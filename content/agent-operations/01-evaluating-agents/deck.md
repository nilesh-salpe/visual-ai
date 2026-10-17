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
- ../../shared/diagram.js
intro:
  kicker: Visual Agents · Operations · 01
  h1: Evaluating agents
  sub: 'Measuring agents that take many stochastic steps in changing environments: execution-based end-state checks, reliability over repeated trials (pass^k), trajectory
    review, and the benchmarks that set the bar.'
  problem: 'Agents are multi-step and random: the same task can succeed once and fail the next time, many different paths can be correct, and grading by comparing
    text to a reference answer misses what actually happened.'
  core: Grade <b>outcomes in the environment</b> (tests pass, database in the goal state, file exists), run each task <b>several times</b> and report <b>pass^k</b>
    (all k trials succeed) alongside success rate, and review <b>trajectories</b> for how it got there. Build realistic, sandboxed, reproducible environments.
  hint: 'Next: [Safety and reliability →](../02-safety-and-reliability/index.html) · [All decks](../index.html)'
papers:
- taubench
- swebench
- gaia
- osworld
- agentbench
---

<!-- slide from="title" -->

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

<div class="visual"><div class="controls"><label class="ctl">per-trial success <input type="range" id="eP" min="0.05" max="0.99" step="0.01" value="0.6"> <output id="ePo"></output></label><label class="ctl">trials k <input type="range" id="eK" min="1" max="16" step="1" value="8"> <output id="eKo"></output></label></div><div class="bars"><div id="eBars"></div></div><p class="readout" id="eOut"></p></div>

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## An evaluation harness

::: diagram 660x300
nodes:
  ts: {at: [10, 120, 130, 56], text: Task set, sub: goal + initial state, color: f, step: 1}
  env: {at: [180, 120, 140, 56], text: Sandbox env, sub: reset per trial, color: c, step: 2}
  ag: {at: [400, 30, 130, 56], text: Agent, sub: under test, color: a, step: 3}
  us: {at: [570, 30, 85, 56], text: User sim, color: b, step: 3}
  gr: {at: [400, 150, 130, 56], text: Grader, sub: end state / tests, color: d, step: 4}
  tr: {at: [180, 250, 140, 44], text: Trace store, color: e, step: 5}
  rep: {at: [570, 150, 85, 56], text: Report, color: e, step: 6}
edges:
  - {from: ts, to: env, step: 2}
  - {from: env, to: ag, label: observations, step: 3}
  - {from: us, to: ag, label: dialogue, step: 3, style: dash}
  - {from: ag, to: env, label: actions, step: 3, style: back}
  - {from: env, to: gr, label: final state, step: 4}
  - {from: env, to: tr, label: trace, step: 5, style: dash}
  - {from: gr, to: rep, step: 6}
steps:
  - Each task defines a goal and an initial environment state.
  - A sandboxed environment is reset before every trial for reproducibility.
  - The agent acts; benchmarks like τ-bench add an LLM-simulated user the agent must talk to.
  - 'A grader checks the end state (tests, database comparison, evaluation scripts) rather than the text of the answer.'
  - Full trajectories are stored for review and failure analysis.
  - 'Report success rate, pass^k, cost and steps per task.'
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Metrics in detail

::: table
| Metric | Definition | Use |
|---|---|---|
| Success rate | fraction of trials that reach the goal state | capability |
| pass@k | 1 − (1 − p)^k: at least one of k succeeds | best-of-k systems with a verifier |
| pass^k | p^k (estimated C(c, k)/C(n, k)): all k succeed | reliability for user-facing agents |
| Cost and steps per task | tokens, tool calls, wall-clock | efficiency, budgets |
| Policy violations | rule breaks found in trajectories | safety and compliance |
:::

<p class="caption">τ-bench defines pass^k; pass@k is the code-generation metric (see Evals deck 03).</p>

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

::: table
| Choice | Benefit | Cost |
|---|---|---|
| Realistic live environments | closest to production | flaky, non-reproducible |
| Self-hosted snapshots (WebArena, OSWorld) | reproducible | drift from the real world |
| Outcome grading | path-independent, objective | misses unsafe or wasteful paths |
| Trajectory grading (human or LLM judge) | catches process problems | expensive; judge bias |
| More trials per task | reliability estimates (pass^k) | multiplies evaluation cost |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes of evaluations

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Contamination | benchmark solutions in training data | held-out and fresh tasks |
| Flaky environments | scores vary with network or site changes | snapshots; reset per trial |
| Grader bugs | passes wrong solutions or fails right ones | audit graders; human spot checks |
| Single-trial reporting | overstates reliability | report pass^k and confidence intervals |
| Benchmark overfitting | great scores, poor real use | evals built from production traces |
:::

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
