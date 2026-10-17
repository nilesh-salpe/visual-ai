---
title: vLLM Router
body:
  data-deck: vLLM Router
  data-home: ../index.html
  data-home-label: vLLM
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
- ../../shared/diagram.js
glance:
  steps:
  - 'request :: session id · prompt :: f'
  - 'policy :: hash · cache-aware · P2C :: b'
  - 'replica :: holds the prefix :: a'
  - 'P/D :: prefill → decode :: c'
  - 'resilience :: retry · circuit breaker :: e'
  caption: Send each request where its KV cache already is, unless that replica is overloaded.
example:
  title: 'Worked example: a cache-aware routing decision'
  setup: 'Defaults: cache_threshold 0.5, balance_abs_threshold 32, balance_rel_threshold 1.1. Three replicas have 40, 42 and 45 requests in flight. A prompt of 2,000
    characters shares a 1,500-character prefix with something replica 2 served earlier.'
  steps:
  - 'Imbalance test: max − min = 45 − 40 = 5, not above 32, so the system is balanced (both conditions are required).'
  - 'Best match ratio: 1,500 / 2,000 = 0.75 &gt; 0.5, so route to <b>replica 2</b> and reuse its cached prefix.'
  - 'Later the loads are 10, 80 and 30: 80 − 10 = 70 &gt; 32 and 80 &gt; 1.1 × 10, so the system is imbalanced.'
  - Now the request goes to the least-loaded replica (<b>replica 1</b>) even though replica 2 holds the prefix; the radix tree still records it.
  result: Cache affinity wins while load is even; load balance wins once it is not.
traps:
  tricks:
  - 'Send a session header. :: X-Session-ID (then X-User-ID, X-Tenant-ID, …) is the consistent-hash key; without one, requests may not stick.'
  - 'Cache-aware for shared prefixes. :: Repeated system prompts and few-shot examples benefit even across users.'
  - 'Watch the router''s /metrics. :: Per-worker latency, errors and health show hot spots and tripped circuit breakers.'
  traps:
  - 'Treating it as a mature component. :: It is v0.1.x, forked from the SGLang model gateway; flags may change.'
  - 'Hash affinity without capacity. :: A few heavy sessions can overload one replica; consistent hashing does not look at load.'
  - 'Comparing with a broken baseline. :: The blog excluded vLLM''s built-in DP coordinator, which then had a known throughput issue (1/8 of the others).'
papers:
- vllm_router_blog
- vllm_router_repo
- vllm_dp_deploy
- vllm_llmd
- vllm_prodstack
- consistent_hash
- p2c
- sglang
- distserve
status:
  label: trend
  reviewed: '2026-10-16'
  note: Released December 2025; v0.1.16 (October 2026) is still pre-1.0 and may merge into vLLM or the SGLang gateway.
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">vLLM · 10</div>
    <h1>vLLM Router: load balancing a fleet of replicas</h1>
    <p class="sub">Why LLM traffic needs a state-aware load balancer, and how the vLLM Router does it: consistent hashing for session affinity, power of two choices, cache-aware routing, prefill/decode disaggregation, retries and circuit breakers, Kubernetes discovery, and how it compares with llm-d and a plain Kubernetes Service.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>A fleet of vLLM replicas each holds its own KV cache. A generic load balancer spreads a conversation's turns over different replicas, so each turn recomputes the whole history, and it cannot orchestrate prefill/decode disaggregation, where one request visits two kinds of worker.</div>
      <div class="c"><b>Core idea</b>Put a lightweight <b>LLM-aware router</b> in front of the replicas. Route a session to the <b>same replica</b> (consistent hashing on a session or user id) or to the replica with the <b>longest cached prefix</b> (cache-aware), but fall back to the <b>least-loaded</b> replica when load is skewed. For <b>prefill/decode disaggregation</b>, send each request to a prefill worker, then to a decode worker that receives its KV cache. Add <b>retries</b>, <b>circuit breakers</b>, <b>Kubernetes discovery</b> and <b>metrics</b>.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Replicas are not interchangeable

Each vLLM replica keeps its own KV cache and its own queue. Which replica a request reaches decides how much of its prompt must be recomputed and how long it waits.
            {: .lede}

::: cards grid3
### [d] Multi-turn chat
Every turn resends the whole conversation; only the replica that served the last turn has it cached.

### [b] Shared prefixes
System prompts and few-shot examples repeat across users; concentrating them on a few replicas raises the prefix-cache hit rate.

### [c] Two kinds of worker
With prefill/decode disaggregation a request is prefilled on one pool and decoded on another; something must coordinate the hand-off.
:::

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why a generic load balancer falls short

::: cards grid3
### [d] Round robin ignores state
A Kubernetes Service spreads turns evenly and so scatters each conversation over replicas.

### [b] Stickiness ignores load
Pinning a session forever overloads the replica that holds a few long, busy sessions.

### [c] No P/D awareness
Treating prefill and decode pods as identical replicas sends work to the wrong pool.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Which policy?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? A chat product sends each conversation's turns with an X-Session-ID header. Which router policy maximises KV-cache reuse across turns?
- [ ] round_robin
- [ ] random
- [x] consistent_hash
- [ ] power_of_two
> **C.** Consistent hashing maps the same session id to the same replica every time, so each turn finds the previous turn's KV cache. Power of two balances load but ignores where the cache is.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Route on cache and load

::: cards grid2
### [f] consistent_hash
Hash a key (X-Session-ID, then X-User-ID, X-Tenant-ID, request and trace ids, or the OpenAI "user" field) onto a ring with 160 virtual nodes per worker: sticky sessions, and removing a worker only moves its own keys.

### [a] cache_aware
Keep an approximate radix tree of prefixes per worker. While load is balanced, send a request to the worker with the longest prefix match if it covers more than 50% of the prompt, else to the worker with the smallest tree; when load is imbalanced, send it to the least-loaded worker.

### [b] power_of_two
Sample two workers, pick the one with fewer pending requests: near-optimal balance with almost no coordination.

### [c] round_robin and random
Stateless spreading, for stateless or single-turn traffic.
:::

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Policies on multi-turn traffic <span class="ill">simulation</span>

<div class="visual"><div class="controls"><label class="ctl">replicas <input type="range" id="rtW" min="2" max="8" step="1" value="4"> <output id="rtWo"></output></label><label class="ctl">active sessions <input type="range" id="rtS" min="20" max="400" step="20" value="200"> <output id="rtSo"></output></label><label class="ctl">traffic from hot sessions <input type="range" id="rtH" min="0" max="60" step="5" value="20"> <output id="rtHo"></output></label></div><div class="bars"><div id="rtBars"></div></div><p class="readout" id="rtOut"></p></div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Prefill/decode routing and operations

::: diagram 660x290
nodes:
  c: {at: [10, 115, 90, 56], text: Client, color: f, step: 1}
  r: {at: [130, 115, 110, 56], text: vLLM Router, sub: Rust · P/D mode, color: b, step: 1}
  p1: {at: [280, 30, 130, 50], text: Prefill worker, sub: compute-bound, color: a, step: 2}
  p2: {at: [280, 95, 130, 50], text: Prefill worker, color: a, step: 2}
  d1: {at: [470, 30, 180, 50], text: Decode worker, sub: memory-bound, color: c, step: 3}
  d2: {at: [470, 95, 180, 50], text: Decode worker, color: c, step: 3}
  k8: {at: [130, 225, 280, 50], text: Kubernetes API, sub: discover pods by label, color: e, step: 4}
  m: {at: [470, 225, 180, 50], text: /metrics, sub: Prometheus, color: e, step: 5}
edges:
  - {from: c, to: r, step: 1}
  - {from: r, to: p1, label: new request, step: 2}
  - {from: r, to: p2, step: 2}
  - {from: p1, to: d1, label: KV cache (NIXL), step: 3}
  - {from: p2, to: d2, step: 3}
  - {from: k8, to: r, label: workers, step: 4, style: dash}
  - {from: r, to: m, step: 5, style: dash}
steps:
  - The client calls the router's OpenAI-compatible endpoint.
  - 'In P/D mode the router sends a new request to a prefill worker, chosen by the prefill policy.'
  - 'The KV cache moves to a decode worker over the configured connector (NIXL, NCCL with ZMQ discovery, or Mooncake), and the router directs the request state there for token generation.'
  - 'In Kubernetes mode the router watches pods by label selector, adding healthy workers and removing failing ones.'
  - 'It exports per-worker request volume, latency, errors and health on /metrics.'
:::

Resilience is on by default: up to 3 retries with exponential backoff (100 ms initial, 10 s maximum, ×2, 10% jitter) on HTTP 408, 429 and 5xx; a circuit breaker opens after 5 consecutive failures, half-opens after 30 s and closes after 2 successes.

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works, and the evidence

::: cards grid2
### [a] Prefill is the expensive part to repeat
A cache hit skips recomputing the shared prefix, cutting time to first token and freeing compute.

### [c] Thresholds arbitrate
Two simple tests (absolute and relative load gaps) decide when balance overrides affinity.

### [b] Benchmarks (vLLM team, Dec 2025)
Llama 3.1 8B with 8 prefill and 8 decode pods: 25% more requests/s than llm-d and twice a round-robin Kubernetes Service, with TTFT 1,200 ms lower than llm-d. DeepSeek V3 (1 prefill and 1 decode pod, TP 8 each): throughput close to llm-d, TTFT 2,000 ms lower than both.

### [e] One of several options
llm-d reads vLLM KV-cache events for precise prefix-aware routing and reports 3× output throughput vs round robin (Llama 3.1 70B, MI300X); the production stack bundles its own router. Pick by platform.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Sticky sessions solve LLM load balancing."
> They maximise cache reuse but ignore load; hot sessions overload a replica. Cache-aware routing falls back to the least-loaded worker when load is skewed.
:::

::: reveal myth
? "The router does the inference."
> It only forwards requests (or tokenised gRPC requests); the vLLM workers do all model work. Built in Rust to keep its overhead small.
:::

::: reveal myth
? "Any router works with P/D disaggregation."
> P/D needs a router that knows which workers prefill and which decode and how KV transfer is configured (NIXL, NCCL, Mooncake).
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Loads are 10, 80 and 30 requests with the default thresholds (32 absolute, 1.1 relative). What does cache_aware do?
- [ ] Routes to the best prefix match
- [x] Routes to the least-loaded worker
- [ ] Round robin
- [ ] Rejects the request
> **B.** 80 − 10 = 70 &gt; 32 and 80 &gt; 1.1 × 10, so the system is imbalanced and load wins over cache affinity.
:::

::: reveal
? Why does consistent hashing use virtual nodes?
> With 160 points per worker on the ring, keys spread evenly across workers, and removing one worker redistributes only its keys among all the others.
:::

::: reveal
? Name two resilience features of the vLLM Router.
> Retries with exponential backoff and jitter on 408/429/5xx; circuit breakers that remove failing workers; health checks via Kubernetes discovery (any two).
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">An LLM router sends each request to the replica that already holds its context, unless that replica is overloaded, and orchestrates prefill and decode pools.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Each vLLM replica has its own KV cache, so where a request lands decides whether its prefix is reused. The vLLM Router, a Rust load balancer released in December 2025 and forked from the SGLang model gateway, offers consistent hashing on a session or user id (160 virtual nodes per worker), cache-aware routing that follows prefix matches while load is balanced and falls back to the least-loaded worker otherwise, power of two choices, and round robin. It also routes prefill/decode disaggregated deployments, retries with backoff, trips circuit breakers on failing workers, discovers pods in Kubernetes and exports Prometheus metrics. In the team's benchmark it delivered 25% more throughput than llm-d and twice a round-robin Kubernetes Service for Llama 3.1 8B.</p></div>
    <div class="recap"><div><span><b>Problem:</b> per-replica KV caches; P/D needs orchestration</span></div><div><span><b>Policies:</b> consistent hash, cache-aware, power of two, round robin</span></div><div><span><b>P/D:</b> prefill pool → decode pool (NIXL, NCCL, Mooncake)</span></div><div><span><b>Operations:</b> retries, circuit breakers, K8s discovery, metrics</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/vllm/06_router_policies.ipynb" target="_blank" rel="noopener">06 · Routing requests across vLLM replicas</a> <span style="color:var(--faint)">· 40 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/vllm/06_router_policies.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">You've finished the series. <a href="../../build-it/index.html">See all Build-it notebooks →</a> · Previous: <a href="../09-deployment/index.html">← 09</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
