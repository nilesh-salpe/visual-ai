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
- ../../shared/diagram.js
intro:
  kicker: Visual Agents · Systems · 01
  h1: Multi-agent systems
  sub: 'When one agent is not enough: a lead agent that plans and spawns parallel subagents with their own context windows, and the coordination, cost and failure
    modes that come with it.'
  problem: A single agent has one context window and works sequentially. Broad tasks (research across many sources, many independent subproblems) overflow its context
    and take too long.
  core: 'Use an <b>orchestrator-workers</b> design: a <b>lead agent</b> decomposes the task and spawns <b>subagents</b> that work <b>in parallel with separate context
    windows</b>, then synthesises their results. It adds capacity and speed for breadth-first work, at a large token cost.'
  hint: 'Next: [Computer and browser use →](../02-computer-use/index.html) · [All decks](../index.html)'
papers:
- ma_research
- autogen
- bea
---

<!-- slide from="title" -->

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

::: diagram 660x300
nodes:
  u: {at: [20, 120, 100, 56], text: User, sub: query, color: f, step: 1}
  lead: {at: [170, 110, 150, 76], text: Lead agent, sub: plan · delegate, color: a, step: 2}
  s1: {at: [400, 20, 150, 50], text: Subagent 1, sub: own context, color: c, step: 3}
  s2: {at: [400, 115, 150, 50], text: Subagent 2, sub: own context, color: c, step: 3}
  s3: {at: [400, 210, 150, 50], text: Subagent 3, sub: own context, color: c, step: 3}
  t: {at: [590, 115, 60, 50], text: Tools, color: b, step: 4}
  mem: {at: [170, 240, 150, 50], text: Memory, sub: 'plan, results', color: e, step: 5}
edges:
  - {from: u, to: lead, step: 2}
  - {from: lead, to: s1, label: task spec, step: 3}
  - {from: lead, to: s2, step: 3}
  - {from: lead, to: s3, step: 3}
  - {from: s2, to: t, step: 4}
  - {from: s1, to: lead, label: findings, step: 5, style: back}
  - {from: lead, to: mem, label: save plan, step: 5, style: dash}
steps:
  - A user query arrives.
  - The lead agent analyses it and plans the approach.
  - 'It spawns subagents in parallel, each with a task specification and its own context window.'
  - 'Subagents use tools (search, fetch, code) independently.'
  - 'They return condensed findings; the lead synthesises them, saving its plan to memory in case its own context fills up.'
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Delegation and synthesis

::: diagram 660x300
nodes:
  spec: {at: [20, 20, 200, 120], text: Task spec, sub: objective · output format · tools · boundaries · effort, color: a, step: 1}
  run: {at: [260, 20, 160, 56], text: Subagent loop, sub: 'search, read, think', color: c, step: 2}
  cond: {at: [460, 20, 180, 56], text: Condensed result, sub: facts + sources, color: e, step: 3}
  syn: {at: [460, 130, 180, 56], text: Lead synthesises, sub: dedupe · resolve conflicts, color: a, step: 4}
  more: {at: [260, 130, 160, 56], text: 'More subagents?', sub: gaps remain, color: d, step: 5}
  cite: {at: [460, 240, 180, 50], text: Final answer, sub: with citations, color: b, step: 6}
edges:
  - {from: spec, to: run, step: 2}
  - {from: run, to: cond, step: 3}
  - {from: cond, to: syn, step: 4}
  - {from: syn, to: more, label: gaps, step: 5}
  - {from: more, to: run, step: 5, style: dash}
  - {from: syn, to: cite, label: done, step: 6}
steps:
  - 'Each subagent gets a precise spec: the objective, the expected output format, which tools to use and where its task ends; vague delegation causes duplicated work.'
  - It runs its own agent loop with a clean context.
  - It returns a compact result rather than its full trajectory.
  - 'The lead merges results, removing duplicates and resolving conflicts.'
  - 'If gaps remain, it spawns further subagents.'
  - The final answer cites sources gathered by the subagents.
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## When it pays off

::: table
| Dimension | Single agent | Multi-agent |
|---|---|---|
| Breadth-first, parallelisable tasks | slow, context overflows | faster; separate contexts add capacity |
| Tightly coupled tasks (shared state, many dependencies) | simpler and coherent | poor fit: coordination overhead (Anthropic notes most coding tasks) |
| Token cost | ≈ 4× chat | ≈ 15× chat |
| Debuggability | one trace | many interacting traces |
| Value per task needed | moderate | high enough to pay for the tokens |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Vague delegation | subagents duplicate each other or miss parts | explicit objectives, boundaries and output formats |
| Runaway spawning | dozens of subagents for a simple query | scale effort to query complexity; caps |
| Conflicting results | contradictory findings merged naively | source quality checks; explicit conflict resolution |
| Error amplification | one bad finding propagates into the synthesis | citations, verification passes |
| Lost lead context | lead forgets the plan in long runs | persist plan to memory; compaction |
:::

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
