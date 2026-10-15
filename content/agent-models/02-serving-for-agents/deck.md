---
title: Serving LLMs for Agent Workloads
body:
  data-deck: Serving LLMs for agent workloads
  data-home: ../index.html
  data-home-label: Models
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
papers:
- sglang
- xgrammar
- outlines
- format_freely
- autellix
- parrot
- vllm_apc
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Visual Agents · Models · 02</div>
    <h1>Serving LLMs for agent workloads</h1>
    <p class="sub">Why agent traffic stresses inference servers differently from chat, and the server-side techniques that help: prefix reuse across turns, constrained decoding for tool calls, program-aware scheduling, and smaller models.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>An agent task is a <b>program</b> of many dependent calls sharing a long, growing prefix, separated by tool executions, each ending in strict JSON. Request-level schedulers see unrelated requests: they recompute shared prefixes, let one long program block others (head-of-line blocking) and optimise per-request latency when the user waits for the whole task.</div>
      <div class="c"><b>Core idea</b>Serve the program, not the request: <b>reuse KV cache across turns</b> (SGLang's RadixAttention, up to 6.4× throughput), <b>constrain decoding</b> to the tool schema cheaply (XGrammar, near-zero overhead), <b>schedule with program context</b> (Autellix, 4-15× program throughput vs vLLM at the same latency), and use <b>smaller or distilled models</b> and speculative decoding where steps are easy.</div>
    </div>
    <div class="toc" data-auto></div>
    <p class="start-hint">Previous: <a href="../01-training-for-agents/index.html">Training LLMs for agents</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Agent traffic is not chat traffic

::: cards grid2
### [d] Repeated prefixes
Every turn resends system prompt, tools and history; without reuse the server prefills them again.

### [b] Strict outputs
Tool calls must parse; one malformed argument costs a full extra turn.

### [c] Dependent calls
Call n+1 waits for call n and a tool run; latency adds up across the program.

### [a] Head-of-line blocking
Autellix found programs suffer long cumulative waits, blocked at both the request and the program level.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Make the server program-aware

::: cards grid2
### [f] Prefix reuse
Keep KV blocks of earlier turns and match the longest cached prefix (vLLM automatic prefix caching; SGLang's radix tree).

### [a] Constrained decoding
Mask tokens that would break the JSON schema or grammar. XGrammar prechecks context-independent tokens and checks the rest with a persistent stack: up to 100× faster than earlier engines.

### [c] Program-level scheduling
Autellix prioritises calls using each program's completed calls; Parrot's Semantic Variables expose data flow between requests.

### [e] Right-sized models
Distilled or small models for sub-agents and easy steps; speculative decoding for latency at low batch sizes.
:::

The client side of the same problem (prompt caching prices, compaction, budgets) is in the <a href="../../agent-operations/03-cost-and-latency/index.html">cost and latency</a> deck.

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## An agent-aware serving stack

<div class="visual dgm" data-steps="[&quot;Many agent programs submit calls; each call belongs to a program with history.&quot;, &quot;The scheduler orders calls using program-level information, e.g. how much service each program has received, to avoid head-of-line blocking.&quot;, &quot;The engine batches calls continuously; the prefix cache supplies KV for the shared history so only new tokens are prefilled.&quot;, &quot;During decoding a grammar mask allows only tokens that keep the tool call valid.&quot;, &quot;A small draft model can propose tokens the large model verifies, cutting latency when the batch is small.&quot;, &quot;The tool call leaves the server; the program&#x27;s KV waits in cache (or is offloaded) until the next turn.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 300" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah15" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="152.0" y1="148.0" x2="186.0" y2="148.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah15)"/></g><g data-step="3"><line x1="332.0" y1="148.0" x2="366.0" y2="148.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah15)"/></g><g data-step="3"><line x1="512.0" y1="148.0" x2="546.0" y2="148.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah15)"/></g><g data-step="3"><line x1="440.0" y1="78.0" x2="440.0" y2="116.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah15)"/></g><g data-step="4"><line x1="440.0" y1="223.0" x2="440.0" y2="180.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah15)"/></g><g data-step="5"><line x1="552.0" y1="78.0" x2="491.2" y2="116.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah15)"/></g><g data-step="6"><line x1="485.7" y1="178.0" x2="551.2" y2="221.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah15)"/></g><g data-step="1"><rect x="10" y="120" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="80.0" y="146.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Agent programs</text><text x="80.0" y="162.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">many calls each</text></g><g data-step="2"><rect x="190" y="120" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="260.0" y="146.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Scheduler</text><text x="260.0" y="162.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">program-aware</text></g><g data-step="3"><rect x="370" y="120" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="440.0" y="146.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Engine</text><text x="440.0" y="162.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">continuous batching</text></g><g data-step="3"><rect x="370" y="20" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="440.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Prefix cache</text><text x="440.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">radix tree of KV</text></g><g data-step="4"><rect x="370" y="225" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="440.0" y="251.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Grammar mask</text><text x="440.0" y="267.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">tool JSON schema</text></g><g data-step="3"><rect x="550" y="120" width="100" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="600.0" y="153.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">GPUs</text></g><g data-step="5"><rect x="550" y="20" width="100" height="56" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="600.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Draft model</text><text x="600.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">speculation</text></g><g data-step="6"><rect x="550" y="225" width="100" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="600.0" y="251.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Tools</text><text x="600.0" y="267.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">run outside</text></g><g data-step="3"><text x="440.0" y="92.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">reuse</text></g><g data-step="4"><text x="440.0" y="196.5" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">allowed tokens</text></g><g data-step="6"><text x="518.5" y="194.5" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">tool call</text></g></svg><p class="readout dgcap"></p></div>

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## One agent turn on the server

<div class="visual dgm" data-steps="[&quot;A new turn arrives: the previous turns plus the latest tool result.&quot;, &quot;The engine finds the longest prefix whose KV blocks are still cached.&quot;, &quot;Only the uncached suffix (the new tool result and any changed text) is prefilled.&quot;, &quot;Decoding applies the grammar mask so the output follows the tool schema.&quot;, &quot;The result is a valid tool call by construction, though not necessarily a correct one.&quot;, &quot;While the tool runs, the program&#x27;s KV must survive: kept in GPU memory, given a time-to-live, or offloaded to CPU memory.&quot;, &quot;If it survived, the next turn starts with almost everything cached; if it was evicted, the whole history is prefilled again.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 240" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah16" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="162.0" y1="48.0" x2="186.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah16)"/></g><g data-step="3"><line x1="342.0" y1="48.0" x2="366.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah16)"/></g><g data-step="4"><line x1="512.0" y1="48.0" x2="536.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah16)"/></g><g data-step="5"><line x1="595.0" y1="78.0" x2="595.0" y2="156.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah16)"/></g><g data-step="6"><line x1="538.0" y1="188.0" x2="514.0" y2="188.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah16)"/></g><g data-step="7"><line x1="298.0" y1="188.0" x2="214.0" y2="188.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah16)"/></g><g data-step="1"><rect x="10" y="20" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="85.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Turn n arrives</text><text x="85.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">history + new tokens</text></g><g data-step="2"><rect x="190" y="20" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="265.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Prefix match</text><text x="265.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">longest cached prefix</text></g><g data-step="3"><rect x="370" y="20" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="440.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Prefill</text><text x="440.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">new tokens only</text></g><g data-step="4"><rect x="540" y="20" width="110" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="595.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Decode</text><text x="595.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">masked by grammar</text></g><g data-step="5"><rect x="540" y="160" width="110" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="595.0" y="186.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Tool call</text><text x="595.0" y="202.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">valid JSON</text></g><g data-step="6"><rect x="300" y="160" width="210" height="56" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="405.0" y="186.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Keep KV while tool runs</text><text x="405.0" y="202.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">pin, TTL or offload to CPU</text></g><g data-step="7"><rect x="10" y="160" width="200" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="110.0" y="186.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Turn n+1</text><text x="110.0" y="202.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">hits the cache</text></g></svg><p class="readout dgcap"></p></div>

<div class="visual scroll-x"><table class="tbl"><tr><th>Concern</th><th>Chat-style serving</th><th>Agent-aware serving</th></tr><tr><td>Unit of scheduling</td><td>request</td><td>program (task)</td></tr><tr><td>Latency metric</td><td>time to first token per request</td><td>end-to-end task completion time</td></tr><tr><td>KV eviction</td><td>least recently used</td><td>aware that a program will return after its tool call</td></tr><tr><td>Output format</td><td>free text, validated after</td><td>grammar-constrained at decode time</td></tr><tr><td>Load balancing</td><td>least loaded replica</td><td>session or prefix affinity, so the cache is on that replica</td></tr></table></div>

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

<div class="visual scroll-x"><table class="tbl"><tr><th>Choice</th><th>Benefit</th><th>Cost</th></tr><tr><td>Keep KV during tool calls</td><td>next turn is nearly free to prefill</td><td>GPU memory held by idle programs</td></tr><tr><td>Evict or offload KV</td><td>room for more active requests</td><td>recompute or transfer when the program returns</td></tr><tr><td>Constrained decoding</td><td>tool calls always parse</td><td>Let Me Speak Freely?: strict format restrictions can degrade reasoning; let the model think before the constrained part</td></tr><tr><td>Prefix-affinity routing</td><td>high cache hit rates</td><td>uneven load across replicas</td></tr><tr><td>Speculative decoding</td><td>lower latency at small batch</td><td>less benefit at high batch; draft model memory</td></tr><tr><td>Smaller models for sub-agents</td><td>cheaper, faster steps</td><td>quality risk on hard steps (route them up)</td></tr></table></div>

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

<div class="visual scroll-x"><table class="tbl"><tr><th>Failure</th><th>Symptom</th><th>Mitigation</th></tr><tr><td>Cache thrash</td><td>hit rate collapses as concurrent agents exceed KV capacity</td><td>admission control, offload tiers, affinity routing</td></tr><tr><td>Prefix changes</td><td>a timestamp or reordered tools at the top kills reuse</td><td>stable prefixes; dynamic content at the end</td></tr><tr><td>Grammar compile stalls</td><td>first request with a new schema is slow</td><td>cache compiled grammars; precompile known tool schemas</td></tr><tr><td>Valid but wrong arguments</td><td>JSON parses, values are nonsense</td><td>schema enums and validation in the tool layer; constrained decoding only fixes syntax</td></tr><tr><td>Long programs starve short ones</td><td>quick tasks wait behind huge ones</td><td>program-aware fair scheduling (Autellix)</td></tr></table></div>

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Measure per task
Report task latency, tokens per task and prefix-cache hit rate, not just tokens per second.

### [c] Affinity
Route a session to the replica that holds its cache, with spillover when it is overloaded.

### [b] Capacity for idle KV
Size memory for programs waiting on tools, not only for active decoding.

### [e] Same engine features as hosted APIs
Self-hosting means owning prefix caching, structured outputs and tool parsing yourself (see the vLLM decks).
:::

<!-- slide id="s-papers" from="papers" -->
