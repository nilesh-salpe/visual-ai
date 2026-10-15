---
title: Serving a Chat Assistant
body:
  data-deck: Serving a chat assistant
  data-home: ../index.html
  data-home-label: System design
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
- ../../shared/diagram.js
intro:
  kicker: Visual AI · System design · 01
  h1: Serving a chat assistant to a million daily users
  sub: 'A capacity-driven design for an LLM chat product: requirements and service-level objectives, back-of-envelope sizing of GPUs and KV cache, the serving architecture,
    and how it scales and fails.'
  problem: Design the backend for a chat assistant used by 1 million people a day, answering with a 70B-class model, streaming responses with low latency, within
    a GPU budget.
  core: Size the fleet from <b>peak concurrency × KV cache per sequence</b> and from <b>output tokens per second</b>, whichever is larger. Serve with continuous batching,
    a paged KV cache and <b>prefix caching</b> for the shared system prompt, route with <b>cache affinity</b>, stream tokens, and protect the fleet with quotas, admission
    control and autoscaling.
  hint: '[Read the full design doc →](design.html) · Next: [Enterprise RAG assistant →](../02-enterprise-rag/index.html) · [All case studies](../index.html)'
papers:
- vllm
- vllm_apc
- orca
- sarathi_serve
- distserve
- llama3
- ant_ratelimits
---

<!-- slide from="title" -->

<!-- slide id="s-req" chapter="Requirements" tag="1 · Requirements" tagclass="b1" -->
## What the system must do

::: cards grid2
### [f] Functional
Multi-turn chat with history, streaming responses, a system prompt per product, per-user quotas, conversation storage.

### [a] Scale (assumption)
1M daily active users × 20 requests each = 20M requests a day; peak traffic 3× the daily average.

### [c] Latency targets (assumption)
Time to first token p95 under 1 s; steady streaming of about 40 tokens per second per user.

### [e] Constraints
A 70B-class open model on 8-GPU H100 nodes; cost per request matters; safety checks on input and output.
:::

Prompt shape (assumption): about 1,500 input tokens (a 1,000-token shared system prompt plus history) and 300 output tokens per request.

<!-- slide id="s-est" chapter="Estimates" tag="2 · Estimates" tagclass="b2" -->
## Back-of-envelope sizing <span class="ill">calculator</span>

<div class="visual"><div class="controls"><label class="ctl">daily users (×100k) <input type="range" id="cD" min="1" max="50" step="1" value="10"> <output id="cDo"></output></label><label class="ctl">requests / user / day <input type="range" id="cR" min="1" max="60" step="1" value="20"> <output id="cRo"></output></label><label class="ctl">peak factor <input type="range" id="cP" min="1" max="6" step="0.5" value="3"> <output id="cPo"></output></label><label class="ctl">input tokens <input type="range" id="cI" min="200" max="8000" step="100" value="1500"> <output id="cIo"></output></label><label class="ctl">output tokens <input type="range" id="cO" min="50" max="2000" step="50" value="300"> <output id="cOo"></output></label><label class="ctl">tokens/s per stream <input type="range" id="cS" min="10" max="100" step="5" value="40"> <output id="cSo"></output></label><label class="ctl">measured replica output tokens/s (K) <input type="range" id="cT" min="2" max="60" step="1" value="20"> <output id="cTo"></output></label></div><div class="bars"><div id="cBars"></div></div><p class="readout" id="cOut"></p></div>

::: cards grid3
### [a] Little's law
Concurrent sequences = arrival rate × time each spends generating.

### [c] KV per token
2 × 80 layers × 8 KV heads × 128 × 2 bytes = 320 KB for a 70B-shaped model at 16-bit.

### [e] Take the max
Replicas = max(memory-bound, throughput-bound); measure throughput at your latency target.
:::

<!-- slide id="s-arch" chapter="Architecture" tag="3 · Architecture" tagclass="b3" -->
## Serving architecture

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

<!-- slide id="s-flow" chapter="Walkthrough" tag="4 · Walkthrough" tagclass="b4" -->
## Life of one message

::: diagram 660x230
nodes:
  a: {at: [10, 20, 150, 56], text: Arrive, sub: request + history, color: f, step: 1}
  b: {at: [190, 20, 150, 56], text: Prefix match, sub: system prompt cached, color: e, step: 2}
  c: {at: [370, 20, 140, 56], text: Prefill, sub: uncached tokens, color: a, step: 3}
  d: {at: [540, 20, 110, 56], text: Decode, sub: batched, color: b, step: 4}
  e: {at: [540, 150, 110, 56], text: Stream, sub: token by token, color: c, step: 5}
  f: {at: [300, 150, 210, 56], text: Output checks, sub: on the stream, color: d, step: 6}
  g: {at: [10, 150, 260, 56], text: Store + bill, sub: append turn · tokens, color: f, step: 7}
edges:
  - {from: a, to: b, step: 2}
  - {from: b, to: c, step: 3}
  - {from: c, to: d, step: 4}
  - {from: d, to: e, step: 5}
  - {from: e, to: f, step: 6}
  - {from: f, to: g, step: 7}
steps:
  - A message arrives with the conversation so far.
  - The engine matches the longest cached prefix (the shared system prompt and earlier turns on the same replica).
  - Only the uncached tokens are prefilled; long prompts are chunked so running decodes do not stall.
  - The request joins the running batch; each step generates one token for every active sequence.
  - Tokens stream to the client as they are produced.
  - Output safety checks run over the stream and can stop it.
  - The turn is stored and token usage is metered for quotas and cost.
:::

::: cards grid3
### [e] Prefix caching
The shared system prompt is computed once per replica and reused; vLLM v0.31.0 enables automatic prefix caching by default.

### [a] Continuous batching
Requests join and leave the running batch at every step (Orca), keeping GPUs busy.

### [b] Chunked prefill
Long prompts are split so they do not stall decodes (Sarathi-Serve).
:::

<!-- slide id="s-deep" chapter="Deep dive" tag="5 · Deep dive" tagclass="b5" -->
## Deep dive: the KV cache is the budget

::: cards grid2
### [d] Memory, not FLOPs
At the default assumptions about 5,000 sequences are active at peak, needing about 3 TB of KV cache: more than all the weights in the fleet.

### [a] Shared prefixes
With prefix caching the 1,000-token system prompt is stored once per replica, not per sequence: unique KV per sequence drops from 1,800 to about 800 tokens.

### [c] Paged allocation
PagedAttention allocates KV in fixed blocks (16 tokens by default in vLLM), so fragmentation stays small and memory can be shared.

### [e] Levers
FP8 KV halves memory; grouped-query attention (8 KV heads instead of 64) already cut it 8×; shorter retained history and summarisation cut it further.
:::

<!-- slide id="s-scale" chapter="Scaling" tag="6 · Scaling" tagclass="b6" -->
## What breaks at 10×

::: table
| Bottleneck | Symptom | Response |
|---|---|---|
| KV cache full | requests queue or get preempted and recomputed | more replicas, FP8 KV, shorter history, prefix-aware routing |
| Prefill spikes | time to first token jumps when long prompts arrive | chunked prefill; separate prefill and decode pools (DistServe) |
| Router hot spots | affinity sends popular sessions to the same replica | consistent hashing with spill-over to the least-loaded replica |
| GPU supply | cannot add replicas fast enough for the peak | scheduled pre-scaling, a smaller model tier for overflow, quotas |
| Conversation store | history reads dominate latency | cache recent turns next to the gateway |
:::

<!-- slide id="s-fail" chapter="Failures" tag="7 · Failures and operations" tagclass="b7" -->
## Failures and operations

::: cards grid2
### [d] Replica failure
Health checks remove a replica; in-flight streams are retried on another replica from the stored history (the client sees a short pause).

### [b] Overload
Admission control and per-user quotas; return 429 with retry-after rather than letting latency collapse for everyone.

### [c] Bad deploy
Canary new model or prompt versions on a small share of traffic with automatic rollback on latency or quality regressions.

### [a] Observe
Time to first token, inter-token latency, KV utilisation, preemptions, tokens and cost per request, safety-filter rates.
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="8 · Trade-offs" tagclass="b8" -->
## Trade-offs and alternatives

::: table
| Decision | Chosen | Alternative | Why |
|---|---|---|---|
| Model | one 70B-class model | router across small and large models | simpler first; add routing when cost matters more than consistency |
| Serving | self-hosted vLLM | hosted model API | control and unit cost at high volume vs no operations at low volume |
| Parallelism | tensor parallel 8 per node | TP 4 with FP8 weights | more KV memory per replica vs fewer GPUs per replica |
| Prefill/decode | colocated with chunked prefill | disaggregated pools | simpler; disaggregate when prefill and decode SLOs conflict |
| Streaming | server-sent events | WebSockets | one-way token streams need nothing more |
:::

<!-- slide id="s-sum" chapter="Summary" tag="9 · Summary" tagclass="b9" -->
## Summary

::: cards grid2
### [a] Size from KV and tokens/s
Concurrency × KV per sequence, and output tokens per second: take the larger.

### [c] Cache the shared prefix
Prefix caching plus cache-affinity routing makes the system prompt almost free.

### [b] Protect the fleet
Quotas, admission control and pre-scaling keep latency stable at peak.

### [e] Read more
Full design document: [design.html](design.html). Related decks: [KV cache](../../inference/02-kv-cache/index.html), [vLLM scheduler](../../vllm/04-scheduler/index.html), [LLM gateway](../../agent-infra/01-llm-gateway/index.html).
:::

<!-- slide id="s-papers" from="papers" -->
