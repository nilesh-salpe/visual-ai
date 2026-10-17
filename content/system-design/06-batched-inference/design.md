---
title: 'Batched inference service: design document'
back: index.html
back_label: Overview deck
---

# Batched inference service

> **Design question.** Clients call a model synchronously and wait for their own answer. A GPU processes up to 100 inputs per batch, and a batch takes almost as long for 1 input as for 100. Design the service: how requests become batches, how latency and throughput trade off, and what happens under overload and failure.

Reported as an AI-lab design question (candidate reports on prep sites, not official material). The model here is a fixed-shape model such as an embedding, reranking or classification model; section 6.4 covers generative LLMs, where the answer changes.

## 1. Goals and non-goals

**Goals:** high GPU utilisation through batching; per-request latency within a deadline (for example p99 < 200 ms); fair and predictable behaviour under overload; simple synchronous API for clients.

**Non-goals:** asynchronous bulk jobs (see the LLM API platform's batch tier), training, multi-model routing logic (one queue per model is assumed).

## 2. Requirements

| Type | Requirement |
|---|---|
| Functional | `predict(input) → output`, synchronous, one input per call; optional client deadline |
| Scale | peak 10,000 requests/s (*assumption*) |
| Latency | p99 < 200 ms end to end (*target*) |
| GPU cost model | time per batch t(b) = t₀ + c·b with t₀ = 20 ms fixed cost and c = 0.3 ms per input (*assumption; measure your model*), so t(100) = 50 ms |
| Max batch | 100 inputs (GPU memory limit) |

**Clarifying questions:** are inputs similar in size (padding cost); can a client send several inputs at once; are there priorities; is the model one or many; what does the client do on timeout (retry storms).

## 3. Capacity estimates

- **Throughput per GPU:** full batches give b ÷ t(b) = 100 ÷ 50 ms = **2,000 inputs/s**; batch size 1 gives 1 ÷ 20.3 ms ≈ **49/s**: batching is a 40× difference.
- **GPUs at peak:** 10,000 ÷ 2,000 = 5 GPUs at 100% utilisation; run at ≤ 70% for queueing headroom → **8 GPUs**, plus N+1 for failures.
- **Latency budget:** wait to fill a batch + queue wait for a free GPU + t(b) + network. With each of 8 workers receiving 1,250 inputs/s, filling 100 takes 80 ms, so a **maximum delay of 10–20 ms** dispatches partial batches (about 13–25 inputs) earlier: lower latency, lower efficiency. The calculator in the deck simulates this trade-off.
- **Little's law:** requests in the system = arrival rate × time in system = 10,000/s × 0.1 s = 1,000 waiting or running at peak, which sizes thread pools and queue bounds.

## 4. API and data model

```
POST /v1/models/{model}/predict   {"input": ..., "deadline_ms": 200}
→ 200 {"output": ..., "batch_size": 37, "queue_ms": 8, "compute_ms": 31}
→ 503 {"error": "overloaded", "retry_after_ms": 50}      (queue full or deadline unreachable)
→ 504 {"error": "deadline_exceeded"}
```

In memory per request: id, input tensor (or pointer), arrival time, deadline, future. No durable state: a lost request is retried by the client.

## 5. High-level architecture

::: diagram 660x300
nodes:
  cl: {at: [10, 120, 92, 56], text: Clients, sub: sync HTTP, color: f, step: 1}
  fe: {at: [150, 120, 118, 56], text: Front end, sub: validate · deadline, color: a, step: 2}
  q: {at: [292, 120, 118, 56], text: Model queue, sub: bounded · per model, color: b, step: 3}
  bt: {at: [432, 120, 98, 56], text: Batcher, sub: full or timeout, color: c, step: 4}
  g1: {at: [565, 40, 90, 50], text: Worker 1, sub: GPU, color: e, step: 5}
  g2: {at: [565, 120, 90, 50], text: Worker 2, sub: GPU, color: e, step: 5}
  g3: {at: [565, 200, 90, 50], text: Worker N, sub: GPU, color: e, step: 5}
  rs: {at: [250, 240, 250, 50], text: Response router, sub: complete each request's future, color: d, step: 6}
edges:
  - {from: cl, to: fe, label: request, step: 1}
  - {from: fe, to: q, step: 3}
  - {from: q, to: bt, step: 4}
  - {from: bt, to: g1, step: 5}
  - {from: bt, to: g2, step: 5}
  - {from: bt, to: g3, step: 5}
  - {from: g3, to: rs, label: outputs, step: 6, style: dash}
  - {from: rs, to: fe, label: reply, step: 6, style: dash}
steps:
  - 'Clients call synchronously and wait for their own result, with a deadline (for example 200 ms).'
  - 'The front end validates input, attaches the deadline and a future (a promise the request thread waits on), and rejects early if the queue is already too long to meet the deadline.'
  - 'Requests wait in a bounded queue per model. A full queue means overload: reject with 503 or 429 instead of growing latency for everyone.'
  - 'The batcher dispatches when it has the maximum batch (100) or when the oldest request has waited the maximum delay, whichever comes first, to the next idle GPU worker.'
  - Workers run one batched forward pass each (pad or bucket inputs to similar lengths); several workers drain the same queue.
  - Each output is matched back to its request id; the front end completes the future and the client gets its answer.
:::

## 6. Detailed design

### 6.1 The batcher
Dispatch rule: **send when the batch is full (100) or when the oldest waiting request has waited `max_delay`**, whichever comes first, to the next idle worker. Triton's dynamic batcher implements the same idea (`max_queue_delay_microseconds`, optional preferred batch sizes). If a worker is free and the queue is non-empty, sending a partial batch immediately minimises latency; holding for `max_delay` raises batch size. Choose `max_delay` from the latency budget: the deadline minus compute time minus a margin for queueing.

### 6.2 Adaptive batch size
Instead of a fixed maximum, adjust it to the latency target: Clipper uses additive-increase, multiplicative-decrease (AIMD), growing the maximum batch while latency stays under the objective and backing off multiplicatively when it does not.

### 6.3 Overload and back-pressure
- **Bounded queue:** reject (503) when the queue is full; never let the queue grow without bound.
- **Deadline-aware admission:** estimate wait from queue length and recent service time; reject at once if the deadline cannot be met (cheaper than timing out later).
- **Drop expired work:** before forming a batch, remove requests whose deadline already passed or whose client disconnected.
- **Client retries:** require exponential backoff with jitter and honour `retry_after_ms`, or retries amplify overload.

### 6.4 Generative LLMs are different
Fixed batches waste GPU time when outputs have different lengths: the batch runs until its longest sequence finishes. LLM servers use **continuous (iteration-level) batching** (Orca): requests join and leave the batch at every decoding step. The same back-pressure and deadline ideas apply; the batcher moves inside the engine (see the continuous batching deck).

### 6.5 Input shapes
Pad to the longest input in the batch, or bucket requests by length (one queue per length bucket) to limit padding waste; cap input size at the front end.

## 7. Scaling

| Bottleneck | Fix |
|---|---|
| GPU throughput | more workers; larger batches if latency allows; smaller or quantised model |
| Batcher or queue as a single process | shard queues by model or by hash of request id; each shard has its own batcher and workers |
| Many models | one queue per model; scale workers per model by queue depth; co-locate small models on a GPU |
| Front-end connections | stateless front ends behind a load balancer; async I/O |
| Bursts | autoscale on queue depth and p99; keep warm spare workers because model load takes seconds to minutes |

## 8. Reliability

| Failure | Detection | Handling |
|---|---|---|
| Worker crash mid-batch | process exit, heartbeat | fail or requeue the batch's requests if deadlines allow; restart worker |
| Poison input crashes a batch | repeated batch failures | retry the batch split in halves to isolate the bad input; reject it with 400 |
| GPU out of memory on large inputs | allocator error | cap input size; bucket by length; reduce maximum batch |
| Overload | queue depth, rejection rate | bounded queue, deadline-aware rejects, autoscaling |
| Slow worker | per-worker batch latency | take it out of rotation |

## 9. Observability

Per model: arrival rate, queue length and queue time, batch size distribution, compute time per batch, p50/p99 end-to-end latency, rejects and timeouts, GPU utilisation. Batch size and queue time together tell you whether to raise or lower `max_delay`.

## 10. Cost

Cost per million inputs = GPU $/hour ÷ (inputs/s per GPU × 3,600 ÷ 10⁶). Full batches make it 40× cheaper than batch size 1 in this model. The cheapest point is the largest `max_delay` the latency target allows.

## 11. Alternatives and trade-offs

| Choice | Benefit | Cost |
|---|---|---|
| No batching | lowest latency at very low load | 40× lower throughput per GPU here |
| Fixed batch size, wait until full | best efficiency | unbounded latency at low load |
| Full-or-timeout (dynamic batching) | balances both | one more knob to tune |
| Adaptive (AIMD) maximum | tracks the latency objective automatically | needs good latency measurement; can oscillate |
| Client-side batching | fewer requests | pushes complexity to clients; mixes deadlines |

## 12. Rollout

Measure t(b) for the real model at several batch sizes; load test with production-like arrival patterns (bursty, not uniform); start with conservative `max_delay`; ramp traffic; alert on p99 and reject rate.

## 13. Risks and open questions

Bursty arrivals break average-based sizing; input-size skew makes padding expensive; retries from many clients can synchronise into waves.

## References

Crankshaw et al. 2017 (Clipper: adaptive batching with AIMD); NVIDIA Triton Inference Server dynamic batcher (`max_queue_delay_microseconds`, preferred batch sizes); Yu et al. 2022 (Orca, iteration-level scheduling); Dean and Barroso 2013 (The Tail at Scale). Related decks: continuous batching, the inference workload, cost and latency.
