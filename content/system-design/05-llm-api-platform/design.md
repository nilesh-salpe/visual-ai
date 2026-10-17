---
title: 'Multi-tenant LLM API platform: design document'
back: index.html
back_label: Overview deck
---

# Multi-tenant LLM API platform

> **Design question.** Design the backend of a public LLM API (or "ChatGPT's backend"): thousands of organisations call several models over HTTP with streaming responses. Keep latency low, stop one tenant from consuming all GPU capacity, cap the cost of free users, and bill everyone accurately.

This document expands the overview deck. Numbers marked *assumption* are inputs to choose for your setting; everything else is computed from them or cited.

## 1. Context, goals and non-goals

**Goals:** one API for several models (a small, a large and fine-tuned variants); streaming responses with a predictable time to first token; isolation between tenants (rate limits, fair scheduling, quotas); accurate usage metering; high GPU utilisation including an asynchronous batch tier.

**Non-goals (v1):** training or fine-tuning jobs (only serving of fine-tunes), multi-region active-active writes for conversation state (the API is stateless), agents and tool execution on the server side.

## 2. Requirements

| Type | Requirement |
|---|---|
| Functional | create a response (streaming or not); choose model; system prompt; prompt caching; batch jobs; usage reporting; per-key and per-org limits |
| Tenancy | 10,000 organisations (*assumption*); tiers: free, paid, enterprise; enterprise may reserve capacity |
| Scale | peak 5,000 requests/s (*assumption*), 2,000 input tokens per request of which 40% cached, 400 output tokens |
| Latency | time to first token p95 < 1 s for paid tiers (*target*); 40+ output tokens/s per stream |
| Availability | 99.9% monthly for the synchronous API (*target*) |
| Isolation | no tenant can push another tenant's p95 latency above target while the other stays within its limits |
| Cost | free users capped per day; batch tier at a discount (the Claude API charges 50% less for Message Batches) |

**Clarifying questions to ask first:** how many models and how big; streaming or not; is conversation state server-side (here: no, clients send full history); expected tenant skew (a few large tenants usually dominate); what does "fair" mean (equal share, or weighted by tier).

## 3. Capacity estimates

| Quantity | Formula | Value |
|---|---|---|
| Output tokens at peak | 5,000 × 400 | **2.0M tokens/s** |
| Uncached input tokens at peak | 5,000 × 2,000 × 60% | **6.0M tokens/s** |
| Streams in flight (Little's law) | 5,000 × (400 ÷ 40 tokens/s) | **50,000 concurrent streams** |
| Large-model replicas | 2.0M × (share to large) ÷ replica throughput | with 50% routed to the small model and 10K output tokens/s per 8-GPU replica (*assumption, measure it*): **100 replicas = 800 GPUs** |
| Small-model replicas | 1.0M ÷ 40K tokens/s per replica (*assumption*) | **25 replicas** |
| GPU cost | GPUs × $/GPU-hour | at $2/GPU-hour (*assumption*): 800 × $2 = $1,600/hour for the large pool |
| Cost per million output tokens (large) | $/hour ÷ (tokens/hour ÷ 10⁶) | $16 ÷ (10K × 3,600 ÷ 10⁶) ≈ **$0.44** per million at full utilisation |

Replica throughput at the latency target is the number that must come from a load test; every other row follows from it. Plan for peak plus headroom (failures, deploys, bursts), and fill the trough with batch jobs.

## 4. API and data model

```
POST /v1/responses
  { "model": "large", "stream": true, "max_tokens": 1024,
    "system": "...", "messages": [...], "metadata": {"user_id": "..."} }
→ 200 text/event-stream  ... deltas ...
  final event: {"usage": {"input": 812, "cache_read": 1200, "cache_write": 0, "output": 391}}
→ 429 {"error": "rate_limit", "limit": "output_tokens_per_minute"}  + retry-after: 7
POST /v1/batches        { "requests": [ {custom_id, params}, ... up to 100,000 ] } → batch id
GET  /v1/batches/{id}   → status; results file when done (within 24 h)
```

| Record | Store | Key | Notes |
|---|---|---|---|
| API key | key-value store, cached at the gateway | key hash | org id, tier, scopes, per-key limits |
| Org limits | config store | org id | RPM, ITPM, OTPM, daily budget, reserved capacity |
| Token buckets | in-memory, sharded by org | org id + limit | counters only; the source of truth for billing is usage events |
| Usage events | append-only log → warehouse | request id | input, cached, output tokens, model, latency, tier |
| Batch jobs | object store + job table | batch id | requests file, per-request status, results file |

## 5. High-level architecture

::: diagram 660x300
nodes:
  cl: {at: [10, 125, 95, 56], text: Tenants, sub: keys · SDKs, color: f, step: 1}
  gw: {at: [128, 125, 115, 56], text: API gateway, sub: auth · validate, color: a, step: 2}
  rl: {at: [128, 15, 115, 56], text: Rate limiter, sub: RPM · ITPM · OTPM, color: d, step: 3}
  ad: {at: [266, 125, 120, 56], text: Admission, sub: priority · fairness, color: b, step: 4}
  rt: {at: [409, 125, 100, 56], text: Router, sub: model · prefix, color: c, step: 5}
  pl: {at: [532, 60, 123, 186], text: Model pools, sub: small · large · LoRA, color: e, step: 6}
  bq: {at: [266, 240, 120, 50], text: Batch queue, sub: fills idle GPUs, color: b, step: 7}
  mt: {at: [409, 240, 100, 50], text: Metering, sub: usage · billing, color: f, step: 8}
edges:
  - {from: cl, to: gw, label: HTTPS, step: 1}
  - {from: gw, to: rl, step: 3, style: dash}
  - {from: gw, to: ad, step: 4}
  - {from: ad, to: rt, step: 5}
  - {from: rt, to: pl, step: 6}
  - {from: bq, to: ad, label: low priority, step: 7, style: dash}
  - {from: pl, to: mt, label: tokens, step: 8, style: dash}
steps:
  - Tenants call one HTTPS API with an API key; responses stream as server-sent events.
  - 'The gateway authenticates the key, validates the request (model, max tokens, context length) and assigns a request id for idempotent retries.'
  - 'A distributed rate limiter checks the organisation''s token buckets for requests, input tokens and output tokens per minute; over the limit returns 429 with retry-after.'
  - 'Admission decides who runs now when capacity is tight: priority classes, then fair share by tokens across tenants, so one tenant cannot fill the queue.'
  - 'The router picks the model pool (or LoRA adapter) and a replica, preferring the replica that already caches this prompt''s prefix.'
  - 'Model pools: replicas of each model with continuous batching and prefix caching; fine-tunes served as LoRA adapters on shared base models.'
  - 'Asynchronous batch jobs wait in a separate queue and are admitted only into spare capacity, at a discount.'
  - 'Every response reports input, cached and output tokens; metering aggregates them per tenant for billing and for the rate limiter.'
:::

## 6. Detailed design

### 6.1 Rate limiting
Three token buckets per organisation and model class, as on the Claude API: **requests per minute, input tokens per minute and output tokens per minute**. Buckets refill continuously rather than resetting each minute. Input tokens are counted at admission from the request; output tokens are reserved as `max_tokens` and refunded with the actual count when the response ends. Cached input tokens can be exempt from the input limit (Claude does not count cache reads toward ITPM for most models), which rewards prompt caching.

Implementation: buckets live in memory on a rate-limit service sharded by org id, with each gateway holding a small local allowance it refills in batches, so most checks need no network call. Over limit → 429 with `retry-after`. Add an **acceleration limit** for sudden ramps of a single org, which protects the fleet from a tenant going from 0 to 100% overnight.

### 6.2 Admission and fair scheduling
Rate limits cap each tenant, but when the whole fleet is busy, first-come-first-served lets a heavy tenant still dominate within its limits. Two layers:
- **Priority classes:** enterprise reserved > paid > free > batch. Lower classes are admitted only when higher queues are below a target.
- **Fair share within a class:** schedule by tokens served, not requests. The Virtual Token Counter (VTC) keeps a counter per client of weighted input and output tokens and always serves the backlogged client with the smallest counter; it is work-conserving (no idle capacity while anyone waits) and bounds the service difference between two backlogged clients (proved 2× tight bound). Weights express tiers.

### 6.3 Routing
1. **Model pool:** from the requested model; optionally a router sends easy requests to the small model when the tenant opted in (see the model-routing deck).
2. **LoRA adapters:** fine-tunes run as adapters on a shared base model (S-LoRA, Punica), so thousands of fine-tunes do not need thousands of replicas.
3. **Replica:** prefix-aware routing (consistent hashing on org + prompt-prefix hash, with a load cap) so repeated system prompts hit the prefix cache; fall back to the least-loaded replica when the preferred one is saturated (see the vLLM Router deck).

### 6.4 Free-user cost caps
Daily token budget per free account; small model by default; lower `max_tokens`; lowest priority class; and shorter retained context. The free tier is admitted only into capacity the paid tiers are not using.

### 6.5 Batch tier
Batch jobs are split into requests and fed into the lowest priority class, so they soak up idle capacity at night and between peaks. The Claude API caps a batch at 100,000 requests or 256 MB, completes within 24 hours (most within an hour) and charges 50% less: the discount pays for flexibility in when the work runs.

### 6.6 Metering and billing
Every response emits a usage event with a request id. Events are idempotent (dedupe by request id), aggregated per org per hour, and reconciled daily against the rate-limiter counters. Billing reads only the event log.

## 7. Scaling

| Bottleneck | Symptom | Fix |
|---|---|---|
| GPU capacity at the daily peak | queueing, time to first token rises | autoscale on queue depth and KV-cache use with scheduled pre-scaling; move work to the batch tier |
| One huge tenant | its share starves others | weighted fair share; reserved capacity for that tenant in a dedicated pool |
| Rate-limit service | hot org shard | local allowances at gateways; shard by org; read replicas for config |
| Long prompts | prefill stalls decodes | chunked prefill; prefill/decode disaggregation for the large model |
| Many fine-tunes | GPU memory for weights | LoRA adapters on shared base models, adapter caching by popularity |
| Regions | latency, region outages | stateless API in several regions; route by latency and capacity |

## 8. Reliability

| Failure | Detection | Handling |
|---|---|---|
| GPU or replica fails mid-stream | health checks; stream error | client retries with the same request id; server deduplicates billing; idempotent non-streaming requests retried transparently |
| Overload | queue depth, admission rejects | 429 with retry-after (or 529 "overloaded" style), shed lowest priority first, never drop admitted streams |
| Rate-limit service down | error rate | fail open for paid tiers with a local per-gateway cap; fail closed for free tier |
| Bad model or deploy | canary error and latency SLOs, eval regressions | automatic rollback; per-model version pinning for tenants |
| Prefix-cache stampede after deploy | time to first token spike | warm caches on new replicas with common system prompts before routing traffic |

## 9. Security and isolation

API keys hashed at rest, scoped per workspace; prompt caches are keyed by org so no tenant can read another's cached prefix; logs redact or sample prompts; data retention per tenant; per-tenant encryption keys for enterprise.

## 10. Observability

Per tenant and model: requests, tokens (input, cached, output), time to first token, inter-token latency, 429s by limit type, queue time, cost. Per replica: batch size, KV-cache use, preemptions. SLO dashboards per tier; alerts on burn rate.

## 11. Cost model

Cost per million output tokens ≈ (GPU $/hour × GPUs per replica) ÷ (output tokens/s per replica × 3,600 ÷ 10⁶) ÷ utilisation. Levers: utilisation (fill troughs with batch), prompt caching (cuts prefill work), routing to smaller models, quantisation (more replicas per GPU budget), and prefill/decode tuning. The overview deck's calculator implements this formula.

## 12. Alternatives and trade-offs

| Choice | Benefit | Cost |
|---|---|---|
| Rate limits only (no fair scheduler) | simple, predictable | idle capacity when one tenant is limited; FCFS unfairness inside limits |
| Token-based fairness (VTC) | isolation with full utilisation | scheduler change inside the serving engine |
| Dedicated pool per big tenant | strongest isolation, predictable latency | lower utilisation; capacity planning per tenant |
| Request-count limits | easy | ignores that a 100K-token request costs far more than a 100-token one |

## 13. Rollout

Shadow traffic on the new gateway and limiter; ramp tenants by tier (internal → free → paid → enterprise); enable fair scheduling first in log-only mode to compare decisions; publish limits and 429 semantics before enforcing.

## 14. Risks and open questions

How to price cached tokens; how much capacity to reserve for enterprise vs share; how to forecast replica throughput for new models before launch; whether to expose priority explicitly (the Claude API's Priority Tier capacity commitments are no longer sold, an example of how such offers change).

## References

Anthropic: rate limits (token buckets, RPM/ITPM/OTPM, cache-aware ITPM, acceleration limits), batch processing (50% cost, 100,000 requests or 256 MB, 24 h), service tiers. Sheng et al. 2024 (VTC, fairness in LLM serving). Sheng et al. 2023 (S-LoRA); Chen et al. 2023 (Punica). Kwon et al. 2023 (vLLM); vLLM Router. Related decks: LLM gateway, model routing, vLLM Router, KV cache across the fleet, cost and latency.
