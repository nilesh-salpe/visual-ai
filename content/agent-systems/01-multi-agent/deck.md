---
title: Multi-Agent Systems
body:
  data-deck: Multi-agent systems
  data-home: ../index.html
  data-home-label: Systems
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
papers:
- ma_research
- autogen
- bea
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Visual Agents · Systems · 01</div>
    <h1>Multi-agent systems</h1>
    <p class="sub">When one agent is not enough: a lead agent that plans and spawns parallel subagents with their own context windows, and the coordination, cost and failure modes that come with it.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>A single agent has one context window and works sequentially. Broad tasks (research across many sources, many independent subproblems) overflow its context and take too long.</div>
      <div class="c"><b>Core idea</b>Use an <b>orchestrator-workers</b> design: a <b>lead agent</b> decomposes the task and spawns <b>subagents</b> that work <b>in parallel with separate context windows</b>, then synthesises their results. It adds capacity and speed for breadth-first work, at a large token cost.</div>
    </div>
    <div class="toc" data-auto></div>
    <p class="start-hint">Next: <a href="../02-computer-use/index.html">Computer and browser use →</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## One context, one thread

::: cards grid3
### [d] Context overflow
Dozens of sources and tool results do not fit in one window.

### [b] Sequential
Independent directions are explored one after another.

### [c] Path dependence
One agent's early framing biases everything that follows.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Lead agent + parallel subagents

::: cards grid2
### [a] Orchestrator
Plans, delegates subtasks with clear objectives, and synthesises results.

### [c] Workers
Subagents with fresh context windows, their own tools, working in parallel.

### [e] Measured gain
Anthropic: Claude Opus 4 lead with Claude Sonnet 4 subagents beat single-agent Opus 4 by 90.2% on an internal research eval.

### [d] Measured cost
Agents use about 4× the tokens of chat; multi-agent systems about 15×. Token usage alone explained 80% of BrowseComp performance variance.
:::

Other patterns: sectioning and voting (parallel workflows), evaluator-optimizer pairs, and conversational multi-agent frameworks such as AutoGen.

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## Orchestrator-workers

<div class="visual dgm" data-steps="[&quot;A user query arrives.&quot;, &quot;The lead agent analyses it and plans the approach.&quot;, &quot;It spawns subagents in parallel, each with a task specification and its own context window.&quot;, &quot;Subagents use tools (search, fetch, code) independently.&quot;, &quot;They return condensed findings; the lead synthesises them, saving its plan to memory in case its own context fills up.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 300" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah14" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="122.0" y1="148.0" x2="166.0" y2="148.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah14)"/></g><g data-step="3"><line x1="322.0" y1="113.5" x2="410.2" y2="74.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah14)"/></g><g data-step="3"><line x1="322.0" y1="145.3" x2="396.0" y2="142.7" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah14)"/></g><g data-step="3"><line x1="322.0" y1="177.1" x2="398.3" y2="206.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah14)"/></g><g data-step="4"><line x1="552.0" y1="140.0" x2="586.0" y2="140.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah14)"/></g><g data-step="5"><line x1="418.8" y1="81.1" x2="328.1" y2="121.7" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah14)"/></g><g data-step="5"><line x1="245.0" y1="188.0" x2="245.0" y2="236.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah14)"/></g><g data-step="1"><rect x="20" y="120" width="100" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="70.0" y="146.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">User</text><text x="70.0" y="162.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">query</text></g><g data-step="2"><rect x="170" y="110" width="150" height="76" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="245.0" y="146.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Lead agent</text><text x="245.0" y="162.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">plan · delegate</text></g><g data-step="3"><rect x="400" y="20" width="150" height="50" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="475.0" y="43.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Subagent 1</text><text x="475.0" y="59.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">own context</text></g><g data-step="3"><rect x="400" y="115" width="150" height="50" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="475.0" y="138.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Subagent 2</text><text x="475.0" y="154.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">own context</text></g><g data-step="3"><rect x="400" y="210" width="150" height="50" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="475.0" y="233.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Subagent 3</text><text x="475.0" y="249.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">own context</text></g><g data-step="4"><rect x="590" y="115" width="60" height="50" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="620.0" y="145.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Tools</text></g><g data-step="5"><rect x="170" y="240" width="150" height="50" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="245.0" y="263.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Memory</text><text x="245.0" y="279.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">plan, results</text></g><g data-step="3"><text x="366.1" y="88.8" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">task spec</text></g><g data-step="5"><text x="373.4" y="116.4" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">findings</text></g><g data-step="5"><text x="245.0" y="207.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">save plan</text></g></svg><p class="readout dgcap"></p></div>

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Delegation and synthesis

<div class="visual dgm" data-steps="[&quot;Each subagent gets a precise spec: the objective, the expected output format, which tools to use and where its task ends; vague delegation causes duplicated work.&quot;, &quot;It runs its own agent loop with a clean context.&quot;, &quot;It returns a compact result rather than its full trajectory.&quot;, &quot;The lead merges results, removing duplicates and resolving conflicts.&quot;, &quot;If gaps remain, it spawns further subagents.&quot;, &quot;The final answer cites sources gathered by the subagents.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 300" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah15" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="222.0" y1="65.2" x2="256.0" y2="60.2" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah15)"/></g><g data-step="3"><line x1="422.0" y1="48.0" x2="456.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah15)"/></g><g data-step="4"><line x1="550.0" y1="78.0" x2="550.0" y2="126.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah15)"/></g><g data-step="5"><line x1="458.0" y1="158.0" x2="424.0" y2="158.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah15)"/></g><g data-step="5"><line x1="340.0" y1="128.0" x2="340.0" y2="80.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah15)"/></g><g data-step="6"><line x1="550.0" y1="188.0" x2="550.0" y2="236.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah15)"/></g><g data-step="1"><rect x="20" y="20" width="200" height="120" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="120.0" y="78.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Task spec</text><text x="120.0" y="94.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">objective · output format · tools · boundaries · effort</text></g><g data-step="2"><rect x="260" y="20" width="160" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="340.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Subagent loop</text><text x="340.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">search, read, think</text></g><g data-step="3"><rect x="460" y="20" width="180" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="550.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Condensed result</text><text x="550.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">facts + sources</text></g><g data-step="4"><rect x="460" y="130" width="180" height="56" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="550.0" y="156.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Lead synthesises</text><text x="550.0" y="172.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">dedupe · resolve conflicts</text></g><g data-step="5"><rect x="260" y="130" width="160" height="56" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="340.0" y="156.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">More subagents?</text><text x="340.0" y="172.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">gaps remain</text></g><g data-step="6"><rect x="460" y="240" width="180" height="50" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="550.0" y="263.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Final answer</text><text x="550.0" y="279.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">with citations</text></g><g data-step="5"><text x="441.0" y="153.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">gaps</text></g><g data-step="6"><text x="550.0" y="207.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">done</text></g></svg><p class="readout dgcap"></p></div>

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## When it pays off

<div class="visual scroll-x"><table class="tbl"><tr><th>Dimension</th><th>Single agent</th><th>Multi-agent</th></tr><tr><td>Breadth-first, parallelisable tasks</td><td>slow, context overflows</td><td>faster; separate contexts add capacity</td></tr><tr><td>Tightly coupled tasks (shared state, many dependencies)</td><td>simpler and coherent</td><td>poor fit: coordination overhead (Anthropic notes most coding tasks)</td></tr><tr><td>Token cost</td><td>≈ 4× chat</td><td>≈ 15× chat</td></tr><tr><td>Debuggability</td><td>one trace</td><td>many interacting traces</td></tr><tr><td>Value per task needed</td><td>moderate</td><td>high enough to pay for the tokens</td></tr></table></div>

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

<div class="visual scroll-x"><table class="tbl"><tr><th>Failure</th><th>Symptom</th><th>Mitigation</th></tr><tr><td>Vague delegation</td><td>subagents duplicate each other or miss parts</td><td>explicit objectives, boundaries and output formats</td></tr><tr><td>Runaway spawning</td><td>dozens of subagents for a simple query</td><td>scale effort to query complexity; caps</td></tr><tr><td>Conflicting results</td><td>contradictory findings merged naively</td><td>source quality checks; explicit conflict resolution</td></tr><tr><td>Error amplification</td><td>one bad finding propagates into the synthesis</td><td>citations, verification passes</td></tr><tr><td>Lost lead context</td><td>lead forgets the plan in long runs</td><td>persist plan to memory; compaction</td></tr></table></div>

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Cost controls
Budgets per task and per subagent; 15× tokens must be justified by task value.

### [c] Tracing across agents
Correlate lead and subagent traces to debug emergent behaviour.

### [b] State and resumption
Long runs need checkpoints; restarting from scratch is expensive.

### [e] Rate limits
Parallel subagents hit provider and tool rate limits together.
:::

<!-- slide id="s-papers" from="papers" -->
