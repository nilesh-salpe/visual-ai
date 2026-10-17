---
title: Multi-tenant LLM API platform
body:
  data-deck: Multi-tenant LLM API platform
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
  kicker: Visual AI · System design · 05
  h1: Multi-tenant LLM API platform
  sub: 'The backend of a public LLM API or a ChatGPT-style product: rate limits by tokens, fair scheduling across tenants, priority tiers, routing to model pools
    and LoRA adapters, a discounted batch tier, metering, and the cost model behind it all.'
  problem: Thousands of organisations call several models over one API. Keep time to first token low, stop any tenant from taking all the GPUs, cap free-user cost,
    and bill accurately.
  core: Put a <b>stateless API gateway</b> in front of <b>model pools</b>. Limit each organisation with <b>token buckets</b> on requests, input tokens and output
    tokens; admit by <b>priority class</b>, then by <b>fair share of tokens</b>; route to the right pool and to the replica that <b>caches the prompt prefix</b>;
    fill idle capacity with a <b>discounted batch tier</b>; meter every token for billing.
  hint: '[Read the detailed design document →](design.html) · Previous: [Planning a pretraining run](../04-pretraining-run/index.html) · Next: [Batched inference
    service →](../06-batched-inference/index.html) · [All case studies](../index.html)'
papers:
- ant_ratelimits
- ant_batches
- vtc
- slora
- punica
- vllm
- vllm_router_blog
- routellm
status:
  label: current
  reviewed: '2026-10-17'
  note: Numbers are labelled assumptions or cited (Claude API docs, VTC, S-LoRA) as of 2026-10-17.
---

<!-- slide from="title" -->

<!-- slide id="s-req" chapter="Requirements" tag="1 · Clarify requirements" tagclass="b1" -->
## Clarify before you design

::: cards grid2
### [f] Ask first
How many models and sizes? Streaming? Is conversation state on the server (here: no, clients send history)? How skewed are tenants? What does fair mean: equal, or weighted by tier?

### [a] Functional
Create a response (streaming or not), choose a model, system prompts, prompt caching, batch jobs, usage reporting, limits per key and per organisation.

### [c] Non-functional (targets)
Time to first token p95 under 1 s for paid tiers; 40+ tokens/s per stream; 99.9% monthly availability; isolation: a tenant within its limits keeps its latency target.

### [e] Scale (assumptions)
10,000 organisations; peak 5,000 requests/s; 2,000 input tokens (40% cached) and 400 output tokens per request.
:::

<!-- slide id="s-est" chapter="Estimates" tag="2 · Estimates" tagclass="b2" -->
## Back-of-the-envelope <span class="ill">calculator</span>

<div class="visual"><div class="controls"><label class="ctl">peak requests/s <input type="range" id="eR" min="500" max="20000" step="500" value="5000"> <output id="eRo"></output></label><label class="ctl">output tokens <input type="range" id="eO" min="100" max="2000" step="50" value="400"> <output id="eOo"></output></label><label class="ctl">routed to small model <input type="range" id="eS" min="0" max="90" step="5" value="50"> <output id="eSo"></output></label><label class="ctl">replica throughput (tokens/s) <input type="range" id="eT" min="2" max="30" step="1" value="10"> <output id="eTo"></output></label><label class="ctl">GPU $/hour <input type="range" id="eP" min="1" max="6" step="0.25" value="2"> <output id="ePo"></output></label></div><div class="bars"><div id="eBars"></div></div><p class="readout" id="eOut"></p></div>

Replica throughput at the latency target is the one number that must come from a load test; GPU price is an assumption.

<!-- slide id="s-api" chapter="API" tag="3 · API and data" tagclass="b3" -->
## API and data model

::: code
POST /v1/responses   {"model": "large", "stream": true, "max_tokens": 1024,
                      "system": "...", "messages": [...]}
→ 200 text/event-stream ... final: {"usage": {"input": 812,
        "cache_read": 1200, "output": 391}}
→ 429 {"error": "rate_limit", "limit": "output_tokens_per_minute"}
      retry-after: 7
POST /v1/batches     {"requests": [... up to 100,000 ...]}  → batch id
:::



::: table
| Record | Store | Key |
|---|---|---|
| API key → org, tier, scopes | key-value store, cached at gateways | key hash |
| Org limits (RPM, ITPM, OTPM, budget) | config store | org id |
| Token buckets | in memory, sharded by org | org id + limit |
| Usage events | append-only log → warehouse | request id (idempotent) |
| Batch jobs | object store + job table | batch id |
:::

<!-- slide id="s-hld" chapter="High-level design" tag="4 · High-level design" tagclass="b4" -->
## High-level design

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

<!-- slide id="s-deep1" chapter="Deep dive 1" tag="5 · Deep dive" tagclass="b5" -->
## Deep dive: who runs next when the GPUs are busy <span class="ill">animation</span>

<div class="visual"><div class="seg" id="fSeg"><button data-v="fcfs" class="on">First come, first served</button><button data-v="fair">Fair share of tokens</button></div><svg id="fSvg" viewBox="0 0 660 240" class="anim-lg" role="img" aria-label="Three tenants' requests over time, waiting and being served"></svg><p class="readout" id="fOut"></p></div>

Rate limits cap each tenant, but inside the limits first-come-first-served lets a bulk tenant delay everyone. The Virtual Token Counter (VTC) serves the backlogged tenant that has used the fewest tokens: isolation like a limit, but no idle GPUs while anyone waits. Priority classes (enterprise > paid > free > batch) sit above it.

<!-- slide id="s-deep2" chapter="Deep dive 2" tag="5 · Deep dive" tagclass="b5" -->
## Deep dive: rate limits, routing and the batch tier

::: cards grid2
### [d] Token buckets
Three per organisation, as on the Claude API: requests, input tokens and output tokens per minute, refilled continuously. Reserve max_tokens at admission, refund the rest. Cache reads can be exempt from the input limit, rewarding prompt caching. Gateways hold local allowances so most checks need no network call.

### [c] Routing
Model pool from the request (optionally a router sends easy prompts to the small model); fine-tunes as LoRA adapters on shared base models (S-LoRA, Punica); replica by prefix hash with a load cap, so repeated system prompts hit the prefix cache.

### [b] Free-user caps
Daily token budget, small model by default, lower max_tokens, lowest priority, admitted only into capacity paid tiers are not using.

### [e] Batch tier
Asynchronous jobs at the lowest priority soak up idle GPUs. The Claude API: up to 100,000 requests or 256 MB per batch, done within 24 hours (most within an hour), 50% cheaper.
:::

<!-- slide id="s-scale" chapter="Scaling" tag="6 · Bottlenecks and scaling" tagclass="b6" -->
## Bottlenecks and scaling

::: table
| Bottleneck | Symptom | Fix |
|---|---|---|
| GPU capacity at the daily peak | time to first token rises | autoscale on queue depth and KV-cache use; scheduled pre-scaling; shift work to batch |
| One very large tenant | its share starves others | weighted fair share; a dedicated pool with reserved capacity |
| Rate-limit service | hot shard for a big org | local allowances at gateways; shard by org |
| Long prompts | prefills stall decoding | chunked prefill; prefill/decode disaggregation |
| Thousands of fine-tunes | GPU memory for weights | LoRA adapters on shared bases; cache adapters by popularity |
| Single region | latency and outages | stateless API in several regions; route by latency and capacity |
:::

<!-- slide id="s-ops" chapter="Failures and cost" tag="7 · Failures, monitoring, cost" tagclass="b7" -->
## Failures, monitoring and cost

::: table
| Failure | Detection | Handling |
|---|---|---|
| Replica dies mid-stream | stream error, health check | client retries with the same request id; billing deduplicated by id |
| Overload | queue depth, admission rejects | 429 with retry-after; shed batch then free tiers first; never drop admitted streams |
| Rate-limit service down | error rate | fail open with local caps for paid tiers; fail closed for free |
| Bad deploy | canary SLOs, eval regressions | automatic rollback; tenants can pin model versions |
:::

Monitor per tenant and model: tokens (input, cached, output), time to first token, inter-token latency, 429s by limit, queue time, cost. Cost per million output tokens ≈ GPU $/hour × GPUs per replica ÷ (tokens/s × 3,600 ÷ 10⁶) ÷ utilisation.

<!-- slide id="s-wrap" chapter="Wrap-up" tag="8 · Wrap-up" tagclass="b9" -->
## Wrap-up

::: cards grid2
### [a] Decisions
Token-based limits and fairness (requests differ by 1,000× in cost); stateless API; prefix-aware routing; LoRA for fine-tunes; batch tier for utilisation.

### [b] Trade-offs
Dedicated pools give the strongest isolation at lower utilisation; shared pools with fair scheduling give utilisation with weaker guarantees.

### [c] Next steps
Load-test replica throughput per model; enable fair scheduling in log-only mode first; publish limits and 429 semantics before enforcing.

### [e] Risks and open questions
Pricing of cached tokens; how much capacity to reserve; forecasting throughput of new models. (The Claude API's Priority Tier commitments are no longer sold: offers like this change.)
:::

[Read the detailed design document →](design.html)

<!-- slide id="s-papers" from="papers" -->
