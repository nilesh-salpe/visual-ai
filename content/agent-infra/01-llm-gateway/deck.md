---
title: LLM Gateway
body:
  data-deck: LLM gateway
  data-home: ../index.html
  data-home-label: Infrastructure
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
- ../../shared/diagram.js
intro:
  kicker: Visual Agents · Infrastructure · 01
  h1: LLM gateway
  sub: 'One service between your applications and every model provider: a single API, keys and budgets per team, rate limits, retries and fallbacks, caching, and
    one place to see cost and errors.'
  problem: Each team calls several providers directly. API keys are scattered, nobody enforces budgets, a provider returning 429 or 5xx takes the feature down, and
    there is no single view of cost per team or per agent.
  core: Put one <b>proxy</b> in front of all providers. Applications call one endpoint with a <b>virtual key</b>; the gateway authenticates, checks <b>budgets and
    rate limits</b>, serves <b>cache</b> hits, picks a <b>deployment</b>, <b>retries</b> with backoff, <b>falls back</b> to another model or provider, and <b>logs</b>
    tokens and cost for every call.
  hint: 'Next: [Model and agent routing →](../02-model-router/index.html) · [All decks](../index.html)'
papers:
- litellm_routing
- cf_gateway
- ant_ratelimits
- owasp_llm
---

<!-- slide from="title" -->

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Every team wires providers by hand

::: cards grid2
### [d] Scattered credentials
Provider keys live in many services and notebooks; rotating or revoking one is a hunt.

### [b] Provider limits
Anthropic limits each model class in requests, input tokens and output tokens per minute (RPM, ITPM, OTPM) using a token bucket, and answers 429 with a retry-after header when you exceed one.

### [c] No fallback
An outage or rate limit at one provider becomes an outage of your product.

### [a] No cost attribution
Agents make many calls per task; without central metering nobody knows which team or agent spends what.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## One proxy for all model traffic

::: cards grid2
### [f] Unified API
One request format for many providers and self-hosted models; the gateway translates (Anthropic input_schema vs OpenAI parameters for tools, different streaming events).

### [a] Identity, budgets, limits
A virtual key per team, app or agent, mapped to allowed models, a spend budget and rate limits.

### [c] Reliability
Retries with backoff, cooldown of failing deployments, fallback to another model group (LiteLLM: allowed_fails 3, cooldown_time 5 s by default).

### [e] Observability and caching
Log tokens, cost, latency and errors per key; serve repeated requests from cache.
:::

OWASP lists <b>Unbounded Consumption</b> (LLM10:2025) among the top risks of LLM applications; a gateway is the natural place to enforce token and spend caps.

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## Where the gateway sits

::: diagram 660x290
nodes:
  a1: {at: [10, 20, 130, 50], text: Team A app, sub: virtual key, color: f, step: 1}
  a2: {at: [10, 120, 130, 50], text: Team B app, sub: virtual key, color: f, step: 1}
  ag: {at: [10, 220, 130, 50], text: Agent, sub: many calls/task, color: f, step: 1}
  gw: {at: [220, 95, 180, 80], text: LLM gateway, sub: auth · limits · route, color: a, step: 2}
  obs: {at: [220, 230, 180, 50], text: Logs and metrics, sub: tokens · cost · errors, color: e, step: 5}
  p1: {at: [480, 20, 170, 50], text: Provider A, sub: hosted API, color: c, step: 3}
  p2: {at: [480, 120, 170, 50], text: Provider B, sub: hosted API, color: c, step: 4}
  p3: {at: [480, 220, 170, 50], text: Self-hosted, sub: vLLM cluster, color: b, step: 4}
edges:
  - {from: a1, to: gw, step: 2}
  - {from: a2, to: gw, step: 2}
  - {from: ag, to: gw, step: 2}
  - {from: gw, to: p1, label: primary, step: 3}
  - {from: gw, to: p2, label: fallback, step: 4, style: dash}
  - {from: gw, to: p3, label: fallback, step: 4, style: dash}
  - {from: gw, to: obs, step: 5}
steps:
  - 'Applications and agents call one endpoint, each with its own virtual key.'
  - 'The gateway authenticates the key and applies that key''s budget, rate limits and allowed models.'
  - 'It forwards the request to the primary deployment, translating to that provider''s format.'
  - On rate limits or errors it fails over to another provider or to a self-hosted model.
  - 'Every call is logged with tokens, cost, latency and outcome, attributed to the key.'
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## The request pipeline

::: diagram 660x300
nodes:
  au: {at: [10, 15, 140, 50], text: Authenticate, sub: virtual key → policy, color: f, step: 1}
  li: {at: [175, 15, 145, 50], text: Check limits, sub: budget · token bucket, color: d, step: 2}
  ca: {at: [345, 15, 135, 50], text: Cache lookup, sub: exact or semantic, color: e, step: 3}
  pk: {at: [520, 15, 135, 50], text: Pick deployment, sub: routing strategy, color: a, step: 4}
  cl: {at: [520, 140, 135, 56], text: Call provider, sub: stream back, color: c, step: 5}
  rt: {at: [300, 140, 150, 56], text: Retry, sub: backoff · cooldown, color: b, step: 6}
  fb: {at: [40, 140, 160, 56], text: Fallback group, sub: next model, color: b, step: 7}
  lg: {at: [520, 250, 135, 46], text: Meter and log, sub: usage · cost, color: e, step: 8}
edges:
  - {from: au, to: li, step: 2}
  - {from: li, to: ca, step: 3}
  - {from: ca, to: pk, label: miss, step: 4}
  - {from: pk, to: cl, step: 5}
  - {from: cl, to: rt, label: 429 / 5xx, step: 6}
  - {from: rt, to: fb, label: exhausted, step: 7}
  - {from: fb, to: pk, step: 7, style: dash}
  - {from: cl, to: lg, label: done, step: 8}
steps:
  - 'Map the virtual key to its team, allowed models and policies.'
  - Reject early if the key is over budget or over its rate limit (a token bucket per key and per model).
  - 'Return a cached response if an identical (or, with a semantic cache, similar) request was answered recently.'
  - 'Choose a deployment of the requested model group: weighted shuffle, least busy, lowest latency or lowest cost.'
  - Call the provider and stream the response back.
  - 'On 429 or 5xx, honour retry-after, back off and retry; a deployment that keeps failing is put in cooldown.'
  - 'When retries are exhausted, move to the next model group in the fallback list.'
  - 'Record input, cached and output tokens, cost and latency against the key.'
:::



::: code
router_settings:
  routing_strategy: simple-shuffle   # default: weighted pick
  num_retries: 2                     # backoff on rate-limit errors
  allowed_fails: 3                   # then cool the deployment down
  cooldown_time: 5                   # seconds
  fallbacks: [{"claude-sonnet": ["gpt-4o", "local-llama"]}]
:::

::: cards grid2
### [e] Cache-aware limits
For most Claude models only uncached input counts toward ITPM: with 2M ITPM and an 80% cache hit rate you can send about 10M input tokens per minute. A gateway that rewrites prompts can destroy that.

### [d] Not every 429 is retryable
Anthropic's spend-cap 429 (error_code enforced_spend_limit_reached) has no retry-after; retrying fails until access resumes.
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Build, run or buy

::: table
| Option | You gain | You pay |
|---|---|---|
| Direct provider SDKs | no extra hop, newest features first | no central limits, fallbacks or metering |
| Open-source gateway (e.g. LiteLLM) | full control, self-hosted data path | you run it highly available |
| Managed gateway (e.g. Cloudflare AI Gateway) | no operations, analytics built in | prompts flow through a third party |
| Exact-match cache | safe, deterministic | low hit rate on varied prompts |
| Semantic cache | more hits | can return a wrong answer for a similar-looking question |
| Silent cross-model fallback | availability | quality and output format change without notice |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Gateway is a single point of failure | all LLM features down together | stateless replicas across zones; clients may bypass on gateway outage |
| Retry storm | retries multiply load during a provider incident | honour retry-after, exponential backoff with jitter, cooldowns, retry budgets |
| Fallback changes behaviour | tool-call or JSON format breaks on the fallback model | evaluate every fallback model on your tasks; tag responses with the model used |
| Cross-tenant cache hit | one customer sees another's answer | include tenant and permissions in the cache key |
| Broken streaming or caching | proxy buffers streams; reordered prompt prefixes stop prompt-cache hits | pass streams through; never rewrite the cached prefix |
| Sensitive data in logs | prompts with personal data stored in plain text | redact or sample; retention limits; access controls on logs |
:::

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Latency overhead
Measure the added hop; keep the gateway near the callers and connection-pool to providers.

### [c] Budgets per agent
Agents loop: enforce per-task and per-key caps, not just monthly invoices.

### [b] Feature parity
New provider features (caching controls, tool types, batch APIs) must pass through or the gateway becomes a bottleneck.

### [e] Config as code
Version routing and fallback rules; canary changes like any deploy.
:::

<!-- slide id="s-papers" from="papers" -->
