---
title: Batched inference service
body:
  data-deck: Batched inference service
  data-home: ../index.html
  data-home-label: System design
  data-doc: design.html
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
- ../../shared/diagram.js
intro:
  kicker: Visual AI · System design · 06
  h1: Batched inference service
  sub: Clients call a model synchronously; a GPU processes up to 100 inputs per batch in almost the time it takes for one. How requests become batches, the latency-throughput
    trade-off, back-pressure and deadlines, and why generative LLMs batch differently.
  problem: Clients send single inputs and wait for their own answer. A GPU runs a batch of up to 100 inputs in about the time it takes for one. Design the service.
  core: Put requests in a <b>bounded queue per model</b> and let a <b>batcher</b> dispatch to the next free GPU when the batch is <b>full or the oldest request has
    waited a maximum delay</b>. Each request waits on a <b>future</b> completed by its output. Size the delay from the <b>latency budget</b>, reject early when a
    <b>deadline</b> cannot be met, and use <b>continuous batching</b> instead for generative LLMs.
  hint: '[Read the detailed design document →](design.html) · Previous: [Multi-tenant LLM API platform](../05-llm-api-platform/index.html) · Next: [Distributing model
    weights →](../07-weight-distribution/index.html) · [All case studies](../index.html)'
papers:
- clipper
- triton_batcher
- orca
- tail_at_scale
status:
  label: current
  reviewed: '2026-10-17'
  note: Batch-cost model and load are labelled assumptions; batcher design from Triton and Clipper, checked 2026-10-17.
---

<!-- slide from="title" -->

<!-- slide id="s-req" chapter="Requirements" tag="1 · Clarify requirements" tagclass="b1" -->
## Clarify before you design

::: cards grid2
### [f] Ask first
Are inputs similar in size? Can one call carry several inputs? Priorities? One model or many? What do clients do on timeout?

### [a] Functional
predict(input) → output, synchronous, one input per call, optional deadline.

### [c] Non-functional (targets)
p99 under 200 ms end to end; graceful behaviour under overload; high GPU utilisation.

### [e] GPU cost model (assumption)
A batch of b inputs takes t(b) = 20 ms + 0.3 ms × b, so t(1) ≈ 20 ms and t(100) = 50 ms: batching is nearly free per input. Measure your own model.
:::

<!-- slide id="s-est" chapter="Estimates" tag="2 · Estimates" tagclass="b2" -->
## Latency vs throughput <span class="ill">simulator</span>

<div class="visual"><div class="controls"><label class="ctl">requests/s <input type="range" id="bL" min="200" max="16000" step="200" value="8000"> <output id="bLo"></output></label><label class="ctl">GPU workers <input type="range" id="bW" min="1" max="12" step="1" value="6"> <output id="bWo"></output></label><label class="ctl">max delay <input type="range" id="bD" min="0" max="60" step="2" value="10"> <output id="bDo"></output></label><label class="ctl">max batch <input type="range" id="bB" min="1" max="100" step="1" value="100"> <output id="bBo"></output></label></div><div class="bars"><div id="bBars"></div></div><p class="readout" id="bOut"></p></div>

Full batches give 100 ÷ 50 ms = 2,000 inputs/s per GPU; batch size 1 gives about 49/s. A discrete-event simulation of 3 seconds of Poisson arrivals.

<!-- slide id="s-api" chapter="API" tag="3 · API and data" tagclass="b3" -->
## API and per-request state

::: code
POST /v1/models/{model}/predict  {"input": ..., "deadline_ms": 200}
→ 200 {"output": ..., "batch_size": 37,
       "queue_ms": 8, "compute_ms": 31}
→ 503 {"error": "overloaded", "retry_after_ms": 50}
→ 504 {"error": "deadline_exceeded"}
:::

In memory per request: id, input, arrival time, deadline and a future the request thread waits on. No durable state: a lost request is simply retried by the client with backoff.

<!-- slide id="s-hld" chapter="High-level design" tag="4 · High-level design" tagclass="b4" -->
## High-level design

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

<!-- slide id="s-deep1" chapter="Deep dive 1" tag="5 · Deep dive" tagclass="b5" -->
## Deep dive: when does a batch leave? <span class="ill">animation</span>

<div class="visual"><div class="seg" id="qSeg"><button data-v="low" class="on">Low traffic</button><button data-v="high">High traffic</button></div><svg id="qSvg" viewBox="0 0 660 160" class="anim-lg" role="img" aria-label="Requests queue up and leave as a batch when full or when the oldest waits too long"></svg></div>

Dispatch when the batch is <b>full</b> or the oldest request has waited <b>max delay</b>, whichever comes first. Triton's dynamic batcher does exactly this (max_queue_delay_microseconds). Clipper goes further and adapts the maximum batch with additive increase, multiplicative decrease to stay under a latency objective.

<!-- slide id="s-deep2" chapter="Deep dive 2" tag="5 · Deep dive" tagclass="b5" -->
## Deep dive: overload, deadlines and LLMs

::: cards grid2
### [d] Bounded queue
Reject with 503 when full. An unbounded queue turns overload into timeouts for everyone.

### [b] Deadline-aware admission
Estimate wait from queue length and recent batch times; reject immediately if the deadline is unreachable, and drop expired or cancelled requests before forming a batch.

### [c] Retries
Clients back off exponentially with jitter and honour retry_after_ms, or retries synchronise into waves.

### [e] Generative LLMs
Outputs differ in length, so a fixed batch runs until its longest sequence ends. LLM servers use continuous (iteration-level) batching: requests join and leave every decoding step (Orca).
:::

<!-- slide id="s-scale" chapter="Scaling" tag="6 · Bottlenecks and scaling" tagclass="b6" -->
## Bottlenecks and scaling

::: table
| Bottleneck | Fix |
|---|---|
| GPU throughput | more workers; larger batches if latency allows; quantised or smaller model |
| One batcher process | shard queues by model or request hash; one batcher per shard |
| Many models | a queue per model; scale workers per model on queue depth; pack small models on one GPU |
| Input-size skew | bucket queues by length to cut padding; cap input size |
| Bursts | autoscale on queue depth and p99; keep warm spares (loading a model takes seconds to minutes) |
:::

<!-- slide id="s-ops" chapter="Failures and cost" tag="7 · Failures, monitoring, cost" tagclass="b7" -->
## Failures, monitoring and cost

::: table
| Failure | Handling |
|---|---|
| Worker crashes mid-batch | requeue its requests if deadlines allow; restart the worker |
| Poison input crashes every batch it is in | retry the batch split in halves to isolate it; reject it with 400 |
| GPU out of memory on large inputs | cap and bucket input sizes; lower the maximum batch |
| Overload | bounded queue, early rejects, autoscaling |
:::

Watch arrival rate, queue time, batch-size distribution, compute time per batch, p99 and rejects. Cost per million inputs = GPU $/hour ÷ (inputs/s per GPU × 3,600 ÷ 10⁶): 40× lower with full batches than with batch size 1 in this model.

<!-- slide id="s-wrap" chapter="Wrap-up" tag="8 · Wrap-up" tagclass="b9" -->
## Wrap-up

::: cards grid2
### [a] Decisions
Bounded per-model queues; full-or-timeout batching; futures for synchronous replies; deadline-aware admission; continuous batching for generative models.

### [b] Trade-off
Max delay is the dial between latency and cost: the longest delay the latency budget allows is the cheapest setting.

### [c] Next steps
Measure t(b) for the real model; load test with bursty arrivals; tune max delay from batch size and queue time; add adaptive (AIMD) batch sizing if load varies a lot.

### [e] Risks
Average-based sizing fails on bursts; padding waste with skewed inputs; client retry storms.
:::

[Read the detailed design document →](design.html)

<!-- slide id="s-papers" from="papers" -->
