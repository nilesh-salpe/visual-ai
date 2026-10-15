---
title: Cost and Latency
body:
  data-deck: Cost and latency
  data-home: ../index.html
  data-home-label: Operations
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
papers:
- ant_caching
- ma_research
- bea
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Visual Agents · Operations · 03</div>
    <h1>Cost and latency</h1>
    <p class="sub">Why agent loops are expensive and slow (the context is re-sent every step), and the levers that fix it: prompt caching, compaction, model routing, parallel tool calls, and budgets.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Each iteration re-sends the whole growing context, so total input tokens grow roughly quadratically with the number of steps. Anthropic reports agents use about 4× the tokens of chat and multi-agent systems about 15×.</div>
      <div class="c"><b>Core idea</b>Make the repeated prefix cheap with <b>prompt caching</b> (cache reads at 0.1× the base input price on most Claude models), keep the context small with <b>compaction</b> and concise tool results, send easy steps to <b>smaller models</b>, run independent tool calls <b>in parallel</b>, and enforce <b>budgets</b> per task.</div>
    </div>
    <div class="toc" data-auto></div>
    <p class="start-hint">Previous: <a href="../02-safety-and-reliability/index.html">Safety and reliability</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Loops multiply tokens

::: cards grid3
### [d] Re-sent context
Every model call includes the system prompt, tools and the full history so far.

### [b] Growing history
Each step appends tool results, so step n sends about n × (tokens per step) more.

### [c] Serial latency
Model calls and tool calls run one after another; a 30-step task means 30 round trips.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Make repetition cheap, keep context small

::: cards grid2
### [e] Prompt caching
Reuse the unchanged prefix: 5-minute cache writes cost 1.25× base input, 1-hour writes 2×, reads 0.1× on most Claude models (lower on some newer ones).

### [a] Compaction and lean results
Summarise old history; truncate and summarise large tool outputs.

### [c] Routing
Send easy steps or queries to smaller, cheaper models; reserve the largest for hard ones (Anthropic's routing pattern).

### [b] Parallelism and budgets
Run independent tool calls in parallel; cap steps, tokens and time per task.
:::

<div class="visual"><div class="controls" style="margin-top:0"><label class="ctl">steps <input type="range" id="cS" min="1" max="60" step="1" value="20"> <output id="cSo"></output></label><label class="ctl">prefix tokens <input type="range" id="cP" min="1000" max="50000" step="1000" value="10000"> <output id="cPo"></output></label><label class="ctl">tokens added per step <input type="range" id="cT" min="100" max="10000" step="100" value="1500"> <output id="cTo"></output></label><label class="ctl"><input type="checkbox" id="cC" checked> cache</label></div><div id="cBars" style="margin-top:12px"></div><p class="readout" id="cOut"></p></div>

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## Where time and money go

<div class="visual dgm" data-steps="[&quot;A task enters the loop.&quot;, &quot;A router picks a model by difficulty.&quot;, &quot;Each call reuses the cached prefix (system prompt, tool definitions, earlier history); only new tokens are processed at full price.&quot;, &quot;Independent tool calls run in parallel to cut wall-clock time.&quot;, &quot;When the context nears its limit, compaction summarises it.&quot;, &quot;A budget guard stops runaway tasks.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 300" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah21" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="142.0" y1="148.0" x2="176.0" y2="148.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah21)"/></g><g data-step="3"><line x1="322.0" y1="155.0" x2="376.0" y2="160.3" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah21)"/></g><g data-step="3"><line x1="455.0" y1="88.0" x2="455.0" y2="136.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah21)"/></g><g data-step="4"><line x1="532.0" y1="168.0" x2="576.0" y2="168.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah21)"/></g><g data-step="4"><line x1="578.0" y1="178.0" x2="534.0" y2="178.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah21)"/></g><g data-step="5"><line x1="455.0" y1="198.0" x2="455.0" y2="241.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah21)"/></g><g data-step="6"><line x1="378.0" y1="270.0" x2="324.0" y2="270.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah21)"/></g><g data-step="1"><rect x="20" y="120" width="120" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="80.0" y="153.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Task</text></g><g data-step="2"><rect x="180" y="120" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="250.0" y="146.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Router</text><text x="250.0" y="162.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">small or large model?</text></g><g data-step="3"><rect x="380" y="30" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="455.0" y="56.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Prompt cache</text><text x="455.0" y="72.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">stable prefix</text></g><g data-step="3"><rect x="380" y="140" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="455.0" y="166.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Model call</text><text x="455.0" y="182.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">only new tokens computed</text></g><g data-step="4"><rect x="580" y="140" width="70" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="615.0" y="166.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Tools</text><text x="615.0" y="182.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">parallel</text></g><g data-step="5"><rect x="380" y="245" width="150" height="50" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="455.0" y="268.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Compactor</text><text x="455.0" y="284.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">near the limit</text></g><g data-step="6"><rect x="180" y="245" width="140" height="50" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="250.0" y="268.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Budget guard</text><text x="250.0" y="284.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">steps · tokens · time</text></g><g data-step="3"><text x="455.0" y="107.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">cache hit</text></g></svg><p class="readout dgcap"></p></div>

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Token accounting per step

<div class="visual dgm" data-steps="[&quot;Step 1 sends the prefix P (system prompt, tools, task).&quot;, &quot;Step 2 also sends the T tokens added by step 1 (assistant turn + tool result).&quot;, &quot;Each step adds another T.&quot;, &quot;Step n sends P + (n \u2212 1)T.&quot;, &quot;Summed over n steps, input tokens \u2248 nP + T\u00b7n(n \u2212 1)/2: quadratic in the number of steps.&quot;, &quot;With a cache hit each step, the repeated part is billed at the read price and only the new tokens at full price.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 300" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah22" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="142.0" y1="55.0" x2="156.0" y2="55.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah22)"/></g><g data-step="3"><line x1="302.0" y1="55.0" x2="316.0" y2="55.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah22)"/></g><g data-step="4"><line x1="482.0" y1="55.0" x2="496.0" y2="55.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah22)"/></g><g data-step="5"><line x1="521.2" y1="82.0" x2="393.7" y2="146.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah22)"/></g><g data-step="6"><line x1="330.0" y1="208.0" x2="330.0" y2="236.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah22)"/></g><g data-step="1"><rect x="20" y="30" width="120" height="50" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="80.0" y="53.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">step 1</text><text x="80.0" y="69.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">P</text></g><g data-step="2"><rect x="160" y="30" width="140" height="50" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="230.0" y="53.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">step 2</text><text x="230.0" y="69.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">P + T</text></g><g data-step="3"><rect x="320" y="30" width="160" height="50" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="400.0" y="53.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">step 3</text><text x="400.0" y="69.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">P + 2T</text></g><g data-step="4"><rect x="500" y="30" width="150" height="50" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="575.0" y="53.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">step n</text><text x="575.0" y="69.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">P + (n−1)T</text></g><g data-step="5"><rect x="160" y="150" width="340" height="56" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="330.0" y="176.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">total input ≈ nP + T·n(n−1)/2</text><text x="330.0" y="192.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">grows ~ n² in the history term</text></g><g data-step="6"><rect x="160" y="240" width="340" height="50" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="330.0" y="270.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">cached: prefix at 0.1×, only the new T at full price</text></g></svg><p class="readout dgcap"></p></div>

::: cards grid3
### [e] Stable prefixes
Caching needs an identical prefix: no timestamps or reordered tools at the top.

### [a] Cache lifetime
The default TTL is 5 minutes, measured from the start of the request; a 1-hour TTL costs 2× to write.

### [d] Minimum size
Prompts below a model-specific minimum length are not cached.
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

<div class="visual scroll-x"><table class="tbl"><tr><th>Lever</th><th>Saves</th><th>Costs</th></tr><tr><td>Prompt caching</td><td>most repeated input cost and time to first token</td><td>write premium; needs stable prefixes</td></tr><tr><td>Compaction</td><td>tokens on long tasks</td><td>possible loss of detail</td></tr><tr><td>Smaller model / routing</td><td>price and latency per call</td><td>more steps or lower quality on hard tasks</td></tr><tr><td>Parallel tool calls / subagents</td><td>wall-clock time</td><td>more tokens overall (multi-agent ≈ 15× chat)</td></tr><tr><td>Step budgets</td><td>runaway cost</td><td>some tasks end incomplete</td></tr></table></div>

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

<div class="visual scroll-x"><table class="tbl"><tr><th>Failure</th><th>Symptom</th><th>Mitigation</th></tr><tr><td>Runaway loops</td><td>a task burns thousands of calls</td><td>hard caps; repeated-action detection</td></tr><tr><td>Cache misses from unstable prefixes</td><td>cost does not drop with caching on</td><td>move dynamic content after the cached prefix; deterministic tool order</td></tr><tr><td>Tail latency from slow tools</td><td>p99 dominated by one dependency</td><td>timeouts, parallelism, fallbacks</td></tr><tr><td>Context bloat</td><td>huge tool outputs re-sent every step</td><td>truncate and summarise results</td></tr><tr><td>Silent cost growth</td><td>bill surprises after a prompt change</td><td>track cost per task in monitoring</td></tr></table></div>

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Cost per task, not per call
Budget and report by completed task.

### [c] Latency SLOs
Stream progress; set service-level objectives (SLOs) for time to first action and completion.

### [b] Rate limits
Parallel agents hit token and request limits together; queue and back off.

### [e] Value check
Agents and especially multi-agent systems need tasks valuable enough to pay for their tokens.
:::

<!-- slide id="s-papers" from="papers" -->
