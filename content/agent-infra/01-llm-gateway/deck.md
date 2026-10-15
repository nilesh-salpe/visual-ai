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
papers:
- litellm_routing
- cf_gateway
- ant_ratelimits
- owasp_llm
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Visual Agents · Infrastructure · 01</div>
    <h1>LLM gateway</h1>
    <p class="sub">One service between your applications and every model provider: a single API, keys and budgets per team, rate limits, retries and fallbacks, caching, and one place to see cost and errors.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Each team calls several providers directly. API keys are scattered, nobody enforces budgets, a provider returning 429 or 5xx takes the feature down, and there is no single view of cost per team or per agent.</div>
      <div class="c"><b>Core idea</b>Put one <b>proxy</b> in front of all providers. Applications call one endpoint with a <b>virtual key</b>; the gateway authenticates, checks <b>budgets and rate limits</b>, serves <b>cache</b> hits, picks a <b>deployment</b>, <b>retries</b> with backoff, <b>falls back</b> to another model or provider, and <b>logs</b> tokens and cost for every call.</div>
    </div>
    <div class="toc" data-auto></div>
    <p class="start-hint">Next: <a href="../02-model-router/index.html">Model and agent routing →</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

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

<div class="visual dgm" data-steps="[&quot;Applications and agents call one endpoint, each with its own virtual key.&quot;, &quot;The gateway authenticates the key and applies that key&#x27;s budget, rate limits and allowed models.&quot;, &quot;It forwards the request to the primary deployment, translating to that provider&#x27;s format.&quot;, &quot;On rate limits or errors it fails over to another provider or to a self-hosted model.&quot;, &quot;Every call is logged with tokens, cost, latency and outcome, attributed to the key.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 290" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="142.0" y1="70.7" x2="216.0" y2="99.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah1)"/></g><g data-step="2"><line x1="142.0" y1="142.1" x2="216.0" y2="139.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah1)"/></g><g data-step="2"><line x1="132.7" y1="218.0" x2="216.0" y2="179.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah1)"/></g><g data-step="3"><line x1="402.0" y1="102.5" x2="482.8" y2="74.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah1)"/></g><g data-step="4"><line x1="402.0" y1="138.6" x2="476.0" y2="141.5" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah1)"/></g><g data-step="4"><line x1="402.0" y1="174.7" x2="497.8" y2="216.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah1)"/></g><g data-step="5"><line x1="310.0" y1="177.0" x2="310.0" y2="226.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah1)"/></g><g data-step="1"><rect x="10" y="20" width="130" height="50" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="75.0" y="43.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Team A app</text><text x="75.0" y="59.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">virtual key</text></g><g data-step="1"><rect x="10" y="120" width="130" height="50" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="75.0" y="143.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Team B app</text><text x="75.0" y="159.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">virtual key</text></g><g data-step="1"><rect x="10" y="220" width="130" height="50" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="75.0" y="243.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Agent</text><text x="75.0" y="259.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">many calls/task</text></g><g data-step="2"><rect x="220" y="95" width="180" height="80" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="310.0" y="133.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">LLM gateway</text><text x="310.0" y="149.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">auth · limits · route</text></g><g data-step="5"><rect x="220" y="230" width="180" height="50" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="310.0" y="253.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Logs and metrics</text><text x="310.0" y="269.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">tokens · cost · errors</text></g><g data-step="3"><rect x="480" y="20" width="170" height="50" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="565.0" y="43.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Provider A</text><text x="565.0" y="59.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">hosted API</text></g><g data-step="4"><rect x="480" y="120" width="170" height="50" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="565.0" y="143.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Provider B</text><text x="565.0" y="159.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">hosted API</text></g><g data-step="4"><rect x="480" y="220" width="170" height="50" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="565.0" y="243.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Self-hosted</text><text x="565.0" y="259.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">vLLM cluster</text></g><g data-step="3"><text x="442.4" y="83.3" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">primary</text></g><g data-step="4"><text x="439.0" y="135.1" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">fallback</text></g><g data-step="4"><text x="449.9" y="190.3" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">fallback</text></g></svg><p class="readout dgcap"></p></div>

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## The request pipeline

<div class="visual dgm" data-steps="[&quot;Map the virtual key to its team, allowed models and policies.&quot;, &quot;Reject early if the key is over budget or over its rate limit (a token bucket per key and per model).&quot;, &quot;Return a cached response if an identical (or, with a semantic cache, similar) request was answered recently.&quot;, &quot;Choose a deployment of the requested model group: weighted shuffle, least busy, lowest latency or lowest cost.&quot;, &quot;Call the provider and stream the response back.&quot;, &quot;On 429 or 5xx, honour retry-after, back off and retry; a deployment that keeps failing is put in cooldown.&quot;, &quot;When retries are exhausted, move to the next model group in the fallback list.&quot;, &quot;Record input, cached and output tokens, cost and latency against the key.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 300" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="162.0" y1="48.0" x2="171.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah2)"/></g><g data-step="3"><line x1="327.0" y1="48.0" x2="336.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah2)"/></g><g data-step="4"><line x1="492.0" y1="48.0" x2="501.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah2)"/></g><g data-step="5"><line x1="580.0" y1="78.0" x2="580.0" y2="146.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah2)"/></g><g data-step="6"><line x1="503.0" y1="178.0" x2="494.0" y2="178.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah2)"/></g><g data-step="7"><line x1="338.0" y1="178.0" x2="329.0" y2="178.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah2)"/></g><g data-step="7"><line x1="326.2" y1="148.0" x2="501.0" y2="79.1" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah2)"/></g><g data-step="8"><line x1="580.0" y1="208.0" x2="580.0" y2="246.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah2)"/></g><g data-step="1"><rect x="10" y="20" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="85.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Authenticate</text><text x="85.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">virtual key → policy</text></g><g data-step="2"><rect x="175" y="20" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="250.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Check limits</text><text x="250.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">budget · token bucket</text></g><g data-step="3"><rect x="340" y="20" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="415.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Cache lookup</text><text x="415.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">exact or semantic</text></g><g data-step="4"><rect x="505" y="20" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="580.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Pick deployment</text><text x="580.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">routing strategy</text></g><g data-step="5"><rect x="505" y="150" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="580.0" y="176.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Call provider</text><text x="580.0" y="192.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">stream back</text></g><g data-step="6"><rect x="340" y="150" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="415.0" y="176.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Retry</text><text x="415.0" y="192.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">backoff · cooldown</text></g><g data-step="7"><rect x="175" y="150" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="250.0" y="176.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Fallback group</text><text x="250.0" y="192.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">next model</text></g><g data-step="8"><rect x="505" y="250" width="150" height="46" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="580.0" y="271.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Meter and log</text><text x="580.0" y="287.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">usage · cost</text></g><g data-step="4"><text x="496.5" y="43.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">miss</text></g><g data-step="6"><text x="498.5" y="173.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">429 / 5xx</text></g><g data-step="7"><text x="333.5" y="173.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">exhausted</text></g><g data-step="8"><text x="580.0" y="222.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">done</text></g></svg><p class="readout dgcap"></p></div>

<div class="visual"><pre style="margin:0;font:13px/1.55 'JetBrains Mono',monospace;white-space:pre-wrap">router_settings:&#10;  routing_strategy: simple-shuffle   # default: weighted pick&#10;  num_retries: 2                     # backoff on rate-limit errors&#10;  allowed_fails: 3                   # then cool the deployment down&#10;  cooldown_time: 5                   # seconds&#10;  fallbacks: [{"claude-sonnet": ["gpt-4o", "local-llama"]}]</pre></div>

::: cards grid2
### [e] Cache-aware limits
For most Claude models only uncached input counts toward ITPM: with 2M ITPM and an 80% cache hit rate you can send about 10M input tokens per minute. A gateway that rewrites prompts can destroy that.

### [d] Not every 429 is retryable
Anthropic's spend-cap 429 (error_code enforced_spend_limit_reached) has no retry-after; retrying fails until access resumes.
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Build, run or buy

<div class="visual scroll-x"><table class="tbl"><tr><th>Option</th><th>You gain</th><th>You pay</th></tr><tr><td>Direct provider SDKs</td><td>no extra hop, newest features first</td><td>no central limits, fallbacks or metering</td></tr><tr><td>Open-source gateway (e.g. LiteLLM)</td><td>full control, self-hosted data path</td><td>you run it highly available</td></tr><tr><td>Managed gateway (e.g. Cloudflare AI Gateway)</td><td>no operations, analytics built in</td><td>prompts flow through a third party</td></tr><tr><td>Exact-match cache</td><td>safe, deterministic</td><td>low hit rate on varied prompts</td></tr><tr><td>Semantic cache</td><td>more hits</td><td>can return a wrong answer for a similar-looking question</td></tr><tr><td>Silent cross-model fallback</td><td>availability</td><td>quality and output format change without notice</td></tr></table></div>

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

<div class="visual scroll-x"><table class="tbl"><tr><th>Failure</th><th>Symptom</th><th>Mitigation</th></tr><tr><td>Gateway is a single point of failure</td><td>all LLM features down together</td><td>stateless replicas across zones; clients may bypass on gateway outage</td></tr><tr><td>Retry storm</td><td>retries multiply load during a provider incident</td><td>honour retry-after, exponential backoff with jitter, cooldowns, retry budgets</td></tr><tr><td>Fallback changes behaviour</td><td>tool-call or JSON format breaks on the fallback model</td><td>evaluate every fallback model on your tasks; tag responses with the model used</td></tr><tr><td>Cross-tenant cache hit</td><td>one customer sees another's answer</td><td>include tenant and permissions in the cache key</td></tr><tr><td>Broken streaming or caching</td><td>proxy buffers streams; reordered prompt prefixes stop prompt-cache hits</td><td>pass streams through; never rewrite the cached prefix</td></tr><tr><td>Sensitive data in logs</td><td>prompts with personal data stored in plain text</td><td>redact or sample; retention limits; access controls on logs</td></tr></table></div>

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
