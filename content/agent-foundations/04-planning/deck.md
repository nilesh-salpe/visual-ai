---
title: Planning and Task Decomposition
body:
  data-deck: Planning and task decomposition
  data-home: ../index.html
  data-home-label: Foundations
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
papers:
- planandsolve
- tot
- hugginggpt
- bea
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Visual Agents · Foundations · 04</div>
    <h1>Planning and task decomposition</h1>
    <p class="sub">How agents handle long tasks: plan first and execute, decompose into subtasks with dependencies, search over alternatives, and replan when reality differs from the plan.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Step-by-step greedy decisions drift on long tasks: the agent forgets the goal, repeats work, or commits early to a dead end it cannot back out of.</div>
      <div class="c"><b>Core idea</b>Make the plan explicit. <b>Plan-and-execute</b>: produce a list (or DAG) of subtasks, then run them. <b>Search</b>: explore alternative partial solutions and evaluate them (Tree of Thoughts). <b>Replan</b> when results contradict the plan. For work you cannot predict, an <b>orchestrator</b> breaks the task down dynamically and delegates.</div>
    </div>
    <div class="toc" data-auto></div>
    <p class="start-hint">Previous: <a href="../03-react-loop/index.html">ReAct: reasoning and acting</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Greedy steps drift

::: cards grid3
### [d] Lost goal
After dozens of steps the original objective is buried in context.

### [b] Dead ends
An early wrong choice cannot be undone without backtracking.

### [c] Missing steps
Zero-shot chain-of-thought skips steps (a failure Plan-and-Solve targets).
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Make the plan explicit

::: cards grid2
### [a] Plan-and-solve
First devise a plan dividing the task into subtasks, then carry them out (Wang et al., 2023).

### [c] Decompose into a DAG
Subtasks with dependencies; independent ones can run in parallel (HuggingGPT plans subtasks and picks a model for each).

### [b] Search
Tree of Thoughts explores several reasoning paths with self-evaluation and backtracking: Game of 24 solved 74% vs 4% with chain-of-thought (GPT-4).

### [e] Replan
Treat the plan as a hypothesis: revise it when observations disagree.
:::

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## Planner, executor, monitor

<div class="visual dgm" data-steps="[&quot;A goal arrives.&quot;, &quot;A planner call decomposes it.&quot;, &quot;The plan is stored explicitly: subtasks, dependencies, status.&quot;, &quot;The executor runs ready subtasks (sequentially or in parallel), each possibly an agent loop.&quot;, &quot;A monitor compares results to expectations; surprises trigger replanning.&quot;, &quot;When all subtasks are done, results are combined into the final output.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 300" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah6" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="142.0" y1="148.0" x2="186.0" y2="148.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah6)"/></g><g data-step="3"><line x1="325.0" y1="118.0" x2="385.7" y2="90.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah6)"/></g><g data-step="4"><line x1="455.0" y1="88.0" x2="455.0" y2="136.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah6)"/></g><g data-step="5"><line x1="455.0" y1="198.0" x2="455.0" y2="236.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah6)"/></g><g data-step="5"><line x1="410.0" y1="238.0" x2="313.3" y2="180.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah6)"/></g><g data-step="6"><line x1="532.0" y1="168.0" x2="566.0" y2="168.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah6)"/></g><g data-step="1"><rect x="20" y="120" width="120" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="80.0" y="153.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Goal</text></g><g data-step="2"><rect x="190" y="120" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="260.0" y="146.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Planner</text><text x="260.0" y="162.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">LLM</text></g><g data-step="3"><rect x="380" y="30" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="455.0" y="56.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Plan</text><text x="455.0" y="72.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">subtasks + deps</text></g><g data-step="4"><rect x="380" y="140" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="455.0" y="166.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Executor</text><text x="455.0" y="182.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">agent loop / workers</text></g><g data-step="5"><rect x="380" y="240" width="150" height="50" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="455.0" y="263.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Monitor</text><text x="455.0" y="279.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">check progress</text></g><g data-step="6"><rect x="570" y="140" width="80" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="610.0" y="173.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Result</text></g><g data-step="3"><text x="355.3" y="99.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">write plan</text></g><g data-step="4"><text x="455.0" y="107.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">next ready step</text></g><g data-step="5"><text x="455.0" y="212.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">results</text></g><g data-step="5"><text x="361.7" y="204.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">replan</text></g><g data-step="6"><text x="549.0" y="163.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">all done</text></g></svg><p class="readout dgcap"></p></div>

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Plan as data; search as a tree

<div class="visual dgm" data-steps="[&quot;Start from the problem state.&quot;, &quot;Generate several candidate thoughts (next steps) and score each with an evaluator prompt.&quot;, &quot;Expand the most promising (breadth- or depth-first); prune dead ends.&quot;, &quot;Keep alternatives so the search can backtrack if the best branch fails.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 260" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah7" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="274.4" y1="58.0" x2="190.0" y2="96.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah7)"/></g><g data-step="2"><line x1="330.0" y1="58.0" x2="330.0" y2="96.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah7)"/></g><g data-step="2"><line x1="385.6" y1="58.0" x2="470.0" y2="96.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah7)"/></g><g data-step="3"><line x1="118.8" y1="148.0" x2="97.2" y2="196.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah7)"/></g><g data-step="3"><line x1="156.2" y1="148.0" x2="206.7" y2="196.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah7)"/></g><g data-step="4"><line x1="530.0" y1="148.0" x2="530.0" y2="196.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah7)"/></g><g data-step="1"><rect x="260" y="10" width="140" height="46" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="330.0" y="38.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">state s0</text></g><g data-step="2"><rect x="60" y="100" width="140" height="46" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="130.0" y="121.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">thought A</text><text x="130.0" y="137.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">value 0.8</text></g><g data-step="2"><rect x="260" y="100" width="140" height="46" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="330.0" y="121.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">thought B</text><text x="330.0" y="137.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">value 0.3</text></g><g data-step="2"><rect x="460" y="100" width="140" height="46" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="530.0" y="121.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">thought C</text><text x="530.0" y="137.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">value 0.6</text></g><g data-step="3"><rect x="20" y="200" width="130" height="46" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="85.0" y="221.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">A → A1</text><text x="85.0" y="237.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">value 0.9</text></g><g data-step="3"><rect x="170" y="200" width="130" height="46" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="235.0" y="221.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">A → A2</text><text x="235.0" y="237.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">dead end</text></g><g data-step="4"><rect x="460" y="200" width="140" height="46" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="530.0" y="221.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">C → C1</text><text x="530.0" y="237.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">kept as backup</text></g></svg><p class="readout dgcap"></p></div>

<div class="visual"><pre style="margin:0;font:13px/1.55 'JetBrains Mono',monospace;white-space:pre-wrap">plan = [&#10;  {"id": 1, "task": "list failing services", "deps": [],     "status": "done"},&#10;  {"id": 2, "task": "fetch logs per service", "deps": [1],   "status": "running"},&#10;  {"id": 3, "task": "summarise root causes",  "deps": [2],   "status": "pending"},&#10;  {"id": 4, "task": "draft incident report",  "deps": [3],   "status": "pending"}]</pre></div>

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

<div class="visual scroll-x"><table class="tbl"><tr><th>Approach</th><th>Benefit</th><th>Cost</th><th>Use when</th></tr><tr><td>Interleaved (ReAct)</td><td>adapts every step</td><td>drifts on long tasks</td><td>short tasks, uncertain environments</td></tr><tr><td>Plan then execute</td><td>goal stays visible; parallelism</td><td>plan may be wrong; needs replanning</td><td>multi-step tasks with clear structure</td></tr><tr><td>Search (ToT)</td><td>better on puzzles with dead ends</td><td>many more model calls</td><td>problems with lookahead and verifiable partial states</td></tr><tr><td>Orchestrator-workers</td><td>dynamic decomposition, parallel workers</td><td>coordination overhead</td><td>subtasks cannot be predicted in advance</td></tr></table></div>

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

<div class="visual scroll-x"><table class="tbl"><tr><th>Failure</th><th>Symptom</th><th>Mitigation</th></tr><tr><td>Plan ignores the environment</td><td>steps assume files or APIs that do not exist</td><td>explore before planning; validate steps</td></tr><tr><td>Stale plan</td><td>executes steps made obsolete by new results</td><td>monitor and replan on surprises</td></tr><tr><td>Over-decomposition</td><td>dozens of trivial subtasks, slow and costly</td><td>plan at the right granularity</td></tr><tr><td>Evaluator errors in search</td><td>prunes the correct branch</td><td>better value prompts; keep backups</td></tr><tr><td>Silent plan abandonment</td><td>agent stops following the plan</td><td>keep plan status in context; check off steps</td></tr></table></div>

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Show the plan
Users can approve or edit a plan before expensive or risky execution.

### [c] Checkpoint state
Long tasks survive restarts if plan status and results are persisted.

### [b] Budget search
Cap branches and depth; search multiplies cost.

### [e] Measure
Track plan quality: completed steps, replans, wasted work.
:::

<!-- slide id="s-papers" from="papers" -->
