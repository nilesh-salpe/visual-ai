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
- ../../shared/diagram.js
intro:
  kicker: Visual Agents · Foundations · 04
  h1: Planning and task decomposition
  sub: 'How agents handle long tasks: plan first and execute, decompose into subtasks with dependencies, search over alternatives, and replan when reality differs
    from the plan.'
  problem: 'Step-by-step greedy decisions drift on long tasks: the agent forgets the goal, repeats work, or commits early to a dead end it cannot back out of.'
  core: 'Make the plan explicit. <b>Plan-and-execute</b>: produce a list (or DAG) of subtasks, then run them. <b>Search</b>: explore alternative partial solutions
    and evaluate them (Tree of Thoughts). <b>Replan</b> when results contradict the plan. For work you cannot predict, an <b>orchestrator</b> breaks the task down
    dynamically and delegates.'
  hint: 'Previous: [ReAct: reasoning and acting](../03-react-loop/index.html) · Next: [Prompting and in-context learning →](../05-prompting/index.html) · [All decks](../index.html)'
papers:
- planandsolve
- tot
- hugginggpt
- bea
---

<!-- slide from="title" -->

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

::: diagram 660x300
nodes:
  g: {at: [20, 120, 120, 56], text: Goal, color: f, step: 1}
  pl: {at: [170, 120, 140, 56], text: Planner, sub: LLM, color: a, step: 2}
  pq: {at: [360, 30, 150, 56], text: Plan, sub: subtasks + deps, color: e, step: 3}
  ex: {at: [360, 140, 150, 56], text: Executor, sub: agent loop / workers, color: c, step: 4}
  mon: {at: [360, 240, 150, 50], text: Monitor, sub: check progress, color: d, step: 5}
  out: {at: [575, 140, 75, 56], text: Result, color: b, step: 6}
edges:
  - {from: g, to: pl, step: 2}
  - {from: pl, to: pq, label: write plan, step: 3}
  - {from: pq, to: ex, label: next ready step, step: 4}
  - {from: ex, to: mon, label: results, step: 5}
  - {from: mon, to: pl, label: replan, step: 5, style: dash}
  - {from: ex, to: out, label: all done, step: 6}
steps:
  - A goal arrives.
  - A planner call decomposes it.
  - 'The plan is stored explicitly: subtasks, dependencies, status.'
  - 'The executor runs ready subtasks (sequentially or in parallel), each possibly an agent loop.'
  - A monitor compares results to expectations; surprises trigger replanning.
  - 'When all subtasks are done, results are combined into the final output.'
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Plan as data; search as a tree

::: diagram 660x260
nodes:
  root: {at: [260, 10, 140, 46], text: state s0, color: f, step: 1}
  a: {at: [60, 100, 140, 46], text: thought A, sub: value 0.8, color: a, step: 2}
  b: {at: [260, 100, 140, 46], text: thought B, sub: value 0.3, color: d, step: 2}
  c: {at: [460, 100, 140, 46], text: thought C, sub: value 0.6, color: c, step: 2}
  a1: {at: [20, 200, 130, 46], text: A → A1, sub: value 0.9, color: e, step: 3}
  a2: {at: [170, 200, 130, 46], text: A → A2, sub: dead end, color: d, step: 3}
  c1: {at: [460, 200, 140, 46], text: C → C1, sub: kept as backup, color: c, step: 4}
edges:
  - {from: root, to: a, step: 2}
  - {from: root, to: b, step: 2}
  - {from: root, to: c, step: 2}
  - {from: a, to: a1, step: 3}
  - {from: a, to: a2, step: 3}
  - {from: c, to: c1, step: 4}
steps:
  - Start from the problem state.
  - Generate several candidate thoughts (next steps) and score each with an evaluator prompt.
  - Expand the most promising (breadth- or depth-first); prune dead ends.
  - Keep alternatives so the search can backtrack if the best branch fails.
:::



::: code
plan = [
  {"id": 1, "task": "list failing services", "deps": [],     "status": "done"},
  {"id": 2, "task": "fetch logs per service", "deps": [1],   "status": "running"},
  {"id": 3, "task": "summarise root causes",  "deps": [2],   "status": "pending"},
  {"id": 4, "task": "draft incident report",  "deps": [3],   "status": "pending"}]
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

::: table
| Approach | Benefit | Cost | Use when |
|---|---|---|---|
| Interleaved (ReAct) | adapts every step | drifts on long tasks | short tasks, uncertain environments |
| Plan then execute | goal stays visible; parallelism | plan may be wrong; needs replanning | multi-step tasks with clear structure |
| Search (ToT) | better on puzzles with dead ends | many more model calls | problems with lookahead and verifiable partial states |
| Orchestrator-workers | dynamic decomposition, parallel workers | coordination overhead | subtasks cannot be predicted in advance |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Plan ignores the environment | steps assume files or APIs that do not exist | explore before planning; validate steps |
| Stale plan | executes steps made obsolete by new results | monitor and replan on surprises |
| Over-decomposition | dozens of trivial subtasks, slow and costly | plan at the right granularity |
| Evaluator errors in search | prunes the correct branch | better value prompts; keep backups |
| Silent plan abandonment | agent stops following the plan | keep plan status in context; check off steps |
:::

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
