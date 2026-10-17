---
title: 'Serving a Chat Assistant: design document'
back: index.html
back_label: Overview deck
---

# Serving a chat assistant to a million daily users

> **Design question.** Build the backend for a chat assistant used by 1 million people a day, answering with a 70B-class open model, streaming responses with low latency, within a GPU budget.

## 1. Goals and non-goals

**Goals:** multi-turn chat with stored history; streaming answers; predictable latency at the daily peak; cost per request low enough to offer a free tier; input and output safety checks.

**Non-goals (for this version):** fine-tuning per customer, image input, tool use and agents (see the coding-agent case), multi-region active-active.

## 2. Requirements

| Type | Requirement |
|---|---|
| Functional | create and continue conversations; stream tokens; per-product system prompts; per-user quotas; delete conversations |
| Scale (assumption) | 1M daily active users, 20 requests per user per day, peak 3× the daily average |
| Latency (target) | time to first token p95 < 1 s; about 40 tokens/s per stream |
| Availability (target) | 99.9% monthly for the chat API |
| Prompt shape (assumption) | ~1,500 input tokens (1,000-token shared system prompt + history), ~300 output tokens |

## 3. Estimates

- **Requests:** 1M × 20 = 20M per day → 20M / 86,400 ≈ 231 requests/s on average → **≈ 694 requests/s at peak**.
- **Output tokens:** 694 × 300 ≈ **208K tokens/s at peak**.
- **Prefill tokens:** 694 × 1,500 ≈ 1.04M tokens/s at peak; with the 1,000-token system prompt served from the prefix cache, about **350K uncached tokens/s**.
- **Concurrency (Little's law):** each answer streams for 300 / 40 = 7.5 s → 694 × 7.5 ≈ **5,200 sequences in flight**.
- **KV cache:** a 70B-shaped model (80 layers, 8 KV heads, head dimension 128, 16-bit) needs 2 × 80 × 8 × 128 × 2 bytes = **320 KB per token**. At 1,800 tokens per sequence: 576 MB per sequence → ≈ **3.0 TB** at peak without prefix sharing, ≈ **1.3 TB** if the system prompt is shared (800 unique tokens per sequence).
- **Per replica:** 8 × H100 80 GB = 640 GB; with vLLM's default 92% memory utilisation and 140 GB of 16-bit weights, about 449 GB is left for KV and activations.
- **Fleet:** memory-bound ≈ 1.3 TB / 449 GB ≈ 3 replicas with prefix sharing (7 without). Throughput-bound = 208K tokens/s ÷ the replica's **measured** output tokens/s at the latency target. Provision the larger of the two, plus headroom (N+2) for failures and deploys.

The overview deck has a calculator for these formulas. Replica throughput is the one number that must come from a load test of your model, hardware and prompt mix.

## 4. Architecture

::: diagram 660x300
nodes:
  cl: {at: [10, 120, 100, 56], text: Clients, sub: web · mobile · API, color: f, step: 1}
  gw: {at: [150, 120, 130, 56], text: API gateway, sub: auth · quotas, color: a, step: 2}
  cs: {at: [150, 230, 130, 56], text: Conversation svc, sub: history store, color: b, step: 3}
  sf: {at: [150, 10, 130, 56], text: Safety filters, sub: input · output, color: d, step: 4}
  rt: {at: [320, 120, 130, 56], text: Router + LB, sub: tier · affinity, color: c, step: 5}
  ic: {at: [490, 90, 160, 116], text: Inference fleet, sub: vLLM replicas, color: e, step: 6}
  as: {at: [490, 240, 160, 50], text: Autoscaler, sub: queue · KV use, color: b, step: 7}
  ob: {at: [320, 240, 130, 50], text: Telemetry, sub: tokens · latency, color: f, step: 8}
edges:
  - {from: cl, to: gw, label: stream, step: 1}
  - {from: gw, to: cs, step: 3}
  - {from: gw, to: sf, step: 4, style: dash}
  - {from: gw, to: rt, label: prompt, step: 5}
  - {from: rt, to: ic, step: 6}
  - {from: as, to: ic, step: 7, style: dash}
  - {from: ic, to: ob, step: 8, style: dash}
steps:
  - Clients hold a streaming connection (server-sent events) to the API gateway.
  - 'The gateway authenticates, applies per-user quotas and rate limits, and assigns a request id.'
  - 'The conversation service loads the history and assembles the prompt: shared system prompt first, then history, then the new message.'
  - Input safety checks run before inference; output checks run on the stream.
  - 'A router picks the model tier and a replica, preferring the replica that already caches this conversation''s prefix.'
  - 'Inference replicas run continuous batching with a paged KV cache and automatic prefix caching, streaming tokens back.'
  - 'The autoscaler adds replicas on queue depth and KV-cache utilisation, ahead of the daily peak.'
  - 'Telemetry records time to first token, inter-token latency, tokens and cost per request.'
:::

## 5. Components

### 5.1 API gateway
Terminates TLS, authenticates users, enforces per-user and per-organisation quotas with token buckets, assigns request ids and holds the server-sent-events stream. Returns 429 with `retry-after` when a quota or global admission limit is hit.

### 5.2 Conversation service
Stores conversations (relational or key-value store) and assembles prompts in a fixed order: **system prompt, then history, then the new message**, so the prefix is byte-identical across turns and the prefix cache hits. Truncates or summarises old turns beyond a history budget.

### 5.3 Safety filters
A fast classifier on input before inference and on the output stream, able to stop generation mid-stream. Decisions are logged for review.

### 5.4 Router and load balancer
Chooses the model tier and a replica. Uses **session affinity** (consistent hashing on conversation id) so a conversation returns to the replica holding its KV prefix, with spill-over to the least-loaded replica when the preferred one is saturated.

### 5.5 Inference replicas
vLLM replicas with tensor parallelism 8 within a node: continuous batching, PagedAttention (16-token blocks), automatic prefix caching (on by default in v0.31.0) and chunked prefill so long prompts do not stall decoding. Each exposes queue depth and KV utilisation.

### 5.6 Autoscaler
Scales on queue depth and KV-cache utilisation, with scheduled pre-scaling ahead of the known daily peak because GPU replicas take minutes to load weights.

## 6. API sketch

```
POST /v1/conversations/{id}/messages     {"text": "..."}
→ 200 text/event-stream: token events ..., then {"usage": {"input": 1532, "cached": 1000, "output": 287}}
```

## 7. Scaling plan

- **Memory first:** FP8 KV cache halves KV memory; shorter retained history and summarisation reduce tokens per sequence.
- **Prefill vs decode:** if long prompts make time to first token unstable, split into prefill and decode pools (disaggregation) and transfer KV between them.
- **Model tiers:** route simple requests to a smaller model when cost per request matters more than consistency.
- **Regions:** add regions for latency and resilience once single-region capacity is understood.

## 8. Reliability

| Failure | Detection | Handling |
|---|---|---|
| GPU or replica failure | health checks, error rates | remove from pool; retry in-flight requests from stored history on another replica |
| Overload at peak | queue depth, KV utilisation | admission control, quotas, 429 with retry-after, pre-scaling |
| Bad model or prompt deploy | canary metrics (latency, refusals, ratings) | automatic rollback |
| Preemption storms | vLLM preemption counters | lower max concurrent sequences per replica; add capacity |

## 9. Security and privacy

Per-user isolation of conversation data; conversation ids never used as cache keys across users (the prefix cache is shared only for the common system prompt); retention limits and deletion; prompts and outputs in logs redacted or sampled.

## 10. Observability and evaluation

Track time to first token, inter-token latency, tokens per request (input, cached, output), cost per request, KV utilisation, preemptions and safety-filter rates. Quality: offline eval suites before each model or prompt change, then an online A/B test with guardrails (see the experimentation deck).

## 11. Alternatives considered

- **Hosted model API instead of self-hosting:** no GPU operations and fast start; higher unit cost at this volume and less control over latency.
- **WebSockets instead of server-sent events:** unnecessary for one-way token streams.
- **Smaller model only:** cheaper but lower answer quality; better as an overflow or routing tier.

## 12. Rollout

Load-test a single replica to measure throughput at the latency target; launch to internal users; ramp external traffic 1% → 10% → 50% → 100% with canaries; add the routing tier and disaggregation only when metrics show the need.

## 13. Data model

| Record | Store | Key | Notes |
|---|---|---|---|
| Conversation | relational or key-value store | conversation id | owner, product, created, retention policy |
| Message | same store, partitioned by conversation | (conversation id, sequence) | role, text, token counts, safety flags |
| Usage event | append-only log → warehouse | request id | input, cached and output tokens, latency, model, replica |
| Quota counters | in-memory token buckets | user or org id | rebuilt from usage events if lost |

Prompts are assembled from these records in a fixed order (system prompt, history, new message) so that the prefix cache hits across turns.

## 14. Cost model

Fleet cost per hour = replicas × 8 GPUs × GPU price. Cost per request = fleet cost per hour ÷ requests per hour. Example with assumptions: a fleet of 10 replicas (80 GPUs) at $2 per GPU-hour costs $160/hour; at the average 231 requests/s (832K/hour) that is about **$0.0002 per request** (about $0.19 per 1,000), rising off-peak as utilisation falls. The biggest levers: prefix caching (the shared 1,000-token system prompt is two-thirds of each prompt), routing simple requests to a smaller model, FP8 weights and KV cache, and scaling down outside the daily peak.

## 15. Risks and open questions

Replica throughput at the latency target is unknown until load-tested; prompt lengths drift upward as conversations grow; a new model version can change both quality and cost; safety-filter latency adds to time to first token.

## References

Kwon et al. 2023 (PagedAttention / vLLM); vLLM automatic prefix caching design; Yu et al. 2022 (Orca); Agrawal et al. 2024 (Sarathi-Serve); Zhong et al. 2024 (DistServe); Llama 3 model card shapes via the Llama 3 report; Anthropic rate-limit documentation (token buckets, 429 and retry-after). Related decks: KV cache, continuous batching, vLLM scheduler and prefix caching, LLM gateway.
