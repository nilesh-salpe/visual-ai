---
title: 'ReAct: Reasoning and Acting'
body:
  data-deck: 'ReAct: reasoning and acting'
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
  kicker: Visual Agents · Foundations · 03
  h1: 'ReAct: reasoning and acting'
  sub: 'The pattern behind most agents: interleave a reasoning step, an action and an observation, and optionally reflect on failures (Reflexion).'
  problem: Chain-of-thought alone reasons from memory and can hallucinate facts; acting alone (just calling tools) lacks a plan to decide what to do next or how to
    handle surprises.
  core: '<b>ReAct</b> interleaves <b>Thought → Action → Observation</b>: reasoning decides the next action and interprets results; actions gather facts that ground
    the reasoning. <b>Reflexion</b> adds a memory of verbal self-critiques from failed attempts that guides the next attempt.'
  hint: 'Previous: [Tool calling](../02-tool-calling/index.html) · Next: [Planning and task decomposition →](../04-planning/index.html) · [All decks](../index.html)'
papers:
- react
- reflexion
- agentbench
---

<!-- slide from="title" -->

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Reasoning or acting alone

::: cards grid3
### [d] Reason only
Chain-of-thought answers from parametric memory: confident hallucinations, errors propagate.

### [b] Act only
Tool calls without a plan wander and cannot recover from unexpected results.

### [c] No learning across attempts
A failed attempt teaches nothing to the next one.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Interleave thought, action, observation

::: cards grid3
### [a] Thought
Free-text reasoning: what is known, what is missing, what to try next.

### [c] Action
A tool call (search, lookup, click, run code).

### [b] Observation
The tool's result, appended to the trajectory.
:::

Results (Yao et al., 2023): on HotpotQA and FEVER, ReAct with a simple Wikipedia API reduced the hallucination and error propagation of chain-of-thought; on ALFWorld and WebShop it beat imitation and reinforcement learning methods by <b>34</b> and <b>10</b> points absolute success, with one or two in-context examples.

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## The ReAct loop, with reflection

::: diagram 660x300
nodes:
  task: {at: [20, 120, 120, 56], text: Task, color: f, step: 1}
  th: {at: [200, 30, 150, 56], text: Thought, sub: plan next step, color: a, step: 2}
  ac: {at: [420, 30, 150, 56], text: Action, sub: tool call, color: c, step: 3}
  ob: {at: [420, 150, 150, 56], text: Observation, sub: tool result, color: b, step: 4}
  ans: {at: [200, 150, 150, 56], text: Answer, sub: or give up, color: e, step: 5}
  ev: {at: [420, 240, 150, 50], text: Evaluator, sub: 'success? feedback', color: d, step: 6}
  ref: {at: [20, 240, 150, 50], text: Reflection memory, sub: lessons learned, color: d, step: 7}
edges:
  - {from: task, to: th, step: 2}
  - {from: th, to: ac, step: 3}
  - {from: ac, to: ob, step: 4}
  - {from: ob, to: th, label: next thought, step: 4, style: dash}
  - {from: th, to: ans, label: enough info, step: 5}
  - {from: ans, to: ev, step: 6}
  - {from: ev, to: ref, label: failed, step: 7}
  - {from: ref, to: th, label: next trial, step: 7, style: dash}
steps:
  - 'A task arrives (question, game, coding problem).'
  - 'The model writes a thought: what it knows and what to do next.'
  - 'It emits an action, a tool call.'
  - The observation is appended; the next thought interprets it. Repeat.
  - 'When the thought concludes it has enough, it answers.'
  - 'Reflexion: an evaluator (tests, environment reward or the model itself) judges the attempt.'
  - 'On failure, the agent writes a short reflection into episodic memory and retries; Reflexion reached 91% pass@1 on HumanEval versus 80% for GPT-4.'
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## What a trajectory looks like

::: code
Question: Which year was the director of "Inception" born?
Thought 1: I need the director of Inception, then their birth year.
Action 1: search["Inception film director"]
Observation 1: Inception (2010) was written and directed by Christopher Nolan.
Thought 2: Now find Christopher Nolan's birth year.
Action 2: search["Christopher Nolan born"]
Observation 2: Christopher Nolan (born 30 July 1970) ...
Thought 3: The answer is 1970.
Action 3: finish["1970"]
:::

::: cards grid3
### [f] Scratchpad
The full trajectory is the context for the next step, so it grows every iteration.

### [a] Structured actions
Modern APIs carry actions as tool calls; thoughts may be model reasoning or plain text.

### [d] Stop rules
A finish action, a step limit, or repeated identical actions end the loop.
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

::: table
| Choice | Benefit | Cost |
|---|---|---|
| Explicit thoughts between actions | better decisions, interpretable traces | more tokens and latency per step |
| Reflection and retry (Reflexion) | learns from failures within a task | needs a reliable success signal; multiple attempts cost more |
| Few-shot ReAct examples | teaches format and strategy | long prompts; may overfit to example style |
| Full observation text | nothing lost | context bloat; summarise or truncate long observations |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Repetitive loops | same search, same thought | detect repeats; force a different action or stop |
| Thought-action mismatch | reasoning says one thing, action does another | validate actions against the stated plan |
| Observation overload | long pages crowd out the goal | extract only relevant parts; keep the goal at the top |
| Bad reflections | wrong lesson reinforced next trial | ground reflections in evaluator evidence |
| Poor long-term reasoning | loses track over many steps (AgentBench's main failure causes) | plans, notes, sub-tasks (decks 04 and Context 01) |
:::

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Traces
Store full thought/action/observation trajectories for debugging and evaluation.

### [c] Step budgets
Cap iterations and tokens per task; surface "gave up" honestly.

### [b] Success signals
Reflection needs tests or checks you can trust.

### [e] Latency
Each thought adds tokens; use the smallest reasoning effort that works.
:::

<!-- slide id="s-papers" from="papers" -->
