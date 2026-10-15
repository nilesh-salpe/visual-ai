---
title: Evaluating Agents
body:
  data-deck: Evaluating agents
  data-home: ../index.html
  data-home-label: Operations
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
papers:
- taubench
- swebench
- gaia
- osworld
- agentbench
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Visual Agents · Operations · 01</div>
    <h1>Evaluating agents</h1>
    <p class="sub">Measuring agents that take many stochastic steps in changing environments: execution-based end-state checks, reliability over repeated trials (pass^k), trajectory review, and the benchmarks that set the bar.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Agents are multi-step and random: the same task can succeed once and fail the next time, many different paths can be correct, and grading by comparing text to a reference answer misses what actually happened.</div>
      <div class="c"><b>Core idea</b>Grade <b>outcomes in the environment</b> (tests pass, database in the goal state, file exists), run each task <b>several times</b> and report <b>pass^k</b> (all k trials succeed) alongside success rate, and review <b>trajectories</b> for how it got there. Build realistic, sandboxed, reproducible environments.</div>
    </div>
    <div class="toc" data-auto></div>
    <p class="start-hint">Next: <a href="../02-safety-and-reliability/index.html">Safety and reliability →</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Why agent evaluation is hard

::: cards grid3
### [d] Stochastic
The same agent and task can succeed and fail on different runs.

### [b] Many correct paths
Comparing to one reference trajectory punishes valid alternatives.

### [c] Real environments
Websites, APIs and OS state change; results must be reproducible.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Grade outcomes, measure consistency

::: cards grid2
### [a] Execution-based grading
SWE-bench runs tests; OSWorld runs per-task evaluation scripts; τ-bench compares the final database state to the goal.

### [d] Reliability: pass^k
τ-bench's metric: the chance that all k trials succeed. gpt-4o succeeded on < 50% of tasks and pass^8 was < 25% in retail.

### [c] Human baselines
GAIA: humans 92% vs 15% for GPT-4 with plugins; OSWorld and WebArena report similar gaps at release.

### [e] Trajectory review
Inspect how the agent succeeded: policy violations, wasted steps, risky actions.
:::

<div class="visual"><div class="controls" style="margin-top:0"><label class="ctl">per-trial success <input type="range" id="eP" min="0.05" max="0.99" step="0.01" value="0.6"> <output id="ePo"></output></label><label class="ctl">trials k <input type="range" id="eK" min="1" max="16" step="1" value="8"> <output id="eKo"></output></label></div><div id="eBars" style="margin-top:12px"></div><p class="readout" id="eOut"></p></div>

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## An evaluation harness

<div class="visual dgm" data-steps="[&quot;Each task defines a goal and an initial environment state.&quot;, &quot;A sandboxed environment is reset before every trial for reproducibility.&quot;, &quot;The agent acts; benchmarks like \u03c4-bench add an LLM-simulated user the agent must talk to.&quot;, &quot;A grader checks the end state (tests, database comparison, evaluation scripts) rather than the text of the answer.&quot;, &quot;Full trajectories are stored for review and failure analysis.&quot;, &quot;Report success rate, pass^k, cost and steps per task.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 300" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah18" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="152.0" y1="148.0" x2="196.0" y2="148.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah18)"/></g><g data-step="3"><line x1="338.3" y1="118.0" x2="397.4" y2="90.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah18)"/></g><g data-step="3"><line x1="578.0" y1="58.0" x2="534.0" y2="58.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah18)"/></g><g data-step="3"><line x1="405.9" y1="97.0" x2="346.8" y2="125.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah18)"/></g><g data-step="4"><line x1="352.0" y1="160.2" x2="396.0" y2="167.1" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah18)"/></g><g data-step="5"><line x1="438.4" y1="88.0" x2="298.1" y2="246.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah18)"/></g><g data-step="6"><line x1="532.0" y1="178.0" x2="576.0" y2="178.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah18)"/></g><g data-step="1"><rect x="20" y="120" width="130" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="85.0" y="146.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Task set</text><text x="85.0" y="162.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">goal + initial state</text></g><g data-step="2"><rect x="200" y="120" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="275.0" y="146.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Sandbox env</text><text x="275.0" y="162.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">reset per trial</text></g><g data-step="3"><rect x="400" y="30" width="130" height="56" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="465.0" y="56.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Agent</text><text x="465.0" y="72.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">under test</text></g><g data-step="3"><rect x="580" y="30" width="70" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="615.0" y="63.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">User sim</text></g><g data-step="4"><rect x="400" y="150" width="130" height="56" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="465.0" y="176.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Grader</text><text x="465.0" y="192.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">end state / tests</text></g><g data-step="5"><rect x="200" y="250" width="150" height="44" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="275.0" y="277.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Trace store</text></g><g data-step="6"><rect x="580" y="150" width="70" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="615.0" y="183.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Report</text></g><g data-step="3"><text x="367.9" y="99.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">observations</text></g><g data-step="3"><text x="556.0" y="53.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">dialogue</text></g><g data-step="3"><text x="376.4" y="126.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">actions</text></g><g data-step="4"><text x="374.0" y="158.6" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">final state</text></g><g data-step="5"><text x="368.2" y="162.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">log</text></g></svg><p class="readout dgcap"></p></div>

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Metrics in detail

<div class="visual scroll-x"><table class="tbl"><tr><th>Metric</th><th>Definition</th><th>Use</th></tr><tr><td>Success rate</td><td>fraction of trials that reach the goal state</td><td>capability</td></tr><tr><td>pass@k</td><td>1 − (1 − p)^k: at least one of k succeeds</td><td>best-of-k systems with a verifier</td></tr><tr><td>pass^k</td><td>p^k (estimated C(c, k)/C(n, k)): all k succeed</td><td>reliability for user-facing agents</td></tr><tr><td>Cost and steps per task</td><td>tokens, tool calls, wall-clock</td><td>efficiency, budgets</td></tr><tr><td>Policy violations</td><td>rule breaks found in trajectories</td><td>safety and compliance</td></tr></table></div>

<p class="caption">τ-bench defines pass^k; pass@k is the code-generation metric (see Evals deck 03).</p>

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

<div class="visual scroll-x"><table class="tbl"><tr><th>Choice</th><th>Benefit</th><th>Cost</th></tr><tr><td>Realistic live environments</td><td>closest to production</td><td>flaky, non-reproducible</td></tr><tr><td>Self-hosted snapshots (WebArena, OSWorld)</td><td>reproducible</td><td>drift from the real world</td></tr><tr><td>Outcome grading</td><td>path-independent, objective</td><td>misses unsafe or wasteful paths</td></tr><tr><td>Trajectory grading (human or LLM judge)</td><td>catches process problems</td><td>expensive; judge bias</td></tr><tr><td>More trials per task</td><td>reliability estimates (pass^k)</td><td>multiplies evaluation cost</td></tr></table></div>

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes of evaluations

<div class="visual scroll-x"><table class="tbl"><tr><th>Failure</th><th>Symptom</th><th>Mitigation</th></tr><tr><td>Contamination</td><td>benchmark solutions in training data</td><td>held-out and fresh tasks</td></tr><tr><td>Flaky environments</td><td>scores vary with network or site changes</td><td>snapshots; reset per trial</td></tr><tr><td>Grader bugs</td><td>passes wrong solutions or fails right ones</td><td>audit graders; human spot checks</td></tr><tr><td>Single-trial reporting</td><td>overstates reliability</td><td>report pass^k and confidence intervals</td></tr><tr><td>Benchmark overfitting</td><td>great scores, poor real use</td><td>evals built from production traces</td></tr></table></div>

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Regression suites from real traces
Turn production failures into test tasks.

### [c] Online monitoring
Track success signals, escalations, cost and latency per task live.

### [b] Human review sampling
Regularly read trajectories; metrics miss surprising behaviour.

### [e] Gate releases
Prompt, model or tool changes must pass the eval suite before rollout.
:::

<!-- slide id="s-papers" from="papers" -->
