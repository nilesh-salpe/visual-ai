---
title: Training LLMs for Agents
body:
  data-deck: Training LLMs for agents
  data-home: ../index.html
  data-home-label: Models
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
- ../../shared/diagram.js
intro:
  kicker: Visual Agents · Models · 01
  h1: Training LLMs for tool use and agency
  sub: 'How models learn to call tools, recover from errors and finish long tasks: synthetic tool-use trajectories for fine-tuning, then reinforcement learning in
    environments with checkable rewards.'
  problem: 'Multi-step tool use is rare in pretraining text. Untrained models call the wrong API, invent arguments, stop after one step or never recover from an error.
    Kimi K2''s report: agentic capabilities such as multi-step reasoning, long-term planning and tool use "are rare in natural data and costly to scale".'
  core: 'Two stages. <b>Supervised fine-tuning</b> on tool-use trajectories, mostly <b>synthesised</b>: real and generated tool specs, generated tasks with rubrics,
    simulated or real environments, and a judge that filters the results. Then <b>reinforcement learning</b> with rewards you can check (tests pass, final state correct),
    plus rubric or self-critique rewards for open-ended tasks.'
  hint: 'Next: [Serving LLMs for agent workloads →](../02-serving-for-agents/index.html) · [All decks](../index.html)'
papers:
- toolformer
- gorilla
- toolllm
- kimi_k2
- swe_rl
- r1
---

<!-- slide from="title" -->

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Agency is missing from the training data

::: cards grid3
### [d] Wrong calls
Gorilla's starting point: even GPT-4 generated inaccurate API arguments and hallucinated API usage.

### [b] Short horizons
Chat data rewards one good reply, not a 50-step task that ends in the right state.

### [c] No recovery
Models rarely see examples of reading an error and changing course.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Synthesise trajectories, then reinforce outcomes

::: cards grid2
### [f] Self-labelled calls
Toolformer: the model inserts candidate API calls into text and keeps those that make the next tokens more likely.

### [a] Fine-tuning on APIs
Gorilla fine-tunes on API documentation with a retriever; ToolLLM builds ToolBench from 16,464 real REST APIs with ChatGPT-generated instructions and depth-first-search solution paths.

### [c] Pipelines at scale
Kimi K2: 3,000+ real MCP tools and 20,000+ synthetic tools, thousands of generated agents, tasks with explicit rubrics, simulated multi-turn trajectories filtered by an LLM judge, plus real sandboxes for code.

### [e] RL on outcomes
SWE-RL rewards similarity to the real fix on GitHub history and reaches 41.0% on SWE-bench Verified with a 70B model; RL also improved out-of-domain tasks where an SFT baseline got worse.
:::

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## The training pipeline

::: diagram 660x300
nodes:
  tl: {at: [10, 20, 140, 56], text: Tool specs, sub: real + synthetic, color: f, step: 1}
  tk: {at: [180, 20, 140, 56], text: Tasks, sub: with rubrics, color: b, step: 2}
  en: {at: [350, 20, 140, 56], text: Environments, sub: simulated + sandboxes, color: c, step: 3}
  tj: {at: [510, 20, 140, 56], text: Trajectories, sub: multi-turn, color: c, step: 3}
  jd: {at: [510, 140, 140, 56], text: Judge filter, sub: rubric check, color: d, step: 4}
  sf: {at: [350, 140, 140, 56], text: SFT, sub: imitate good runs, color: a, step: 5}
  rl: {at: [180, 140, 140, 56], text: RL, sub: policy rollouts, color: a, step: 6}
  rw: {at: [180, 245, 140, 50], text: Rewards, sub: tests · state · rubric, color: e, step: 6}
edges:
  - {from: tl, to: tk, step: 2}
  - {from: tk, to: en, step: 3}
  - {from: en, to: tj, step: 3}
  - {from: tj, to: jd, step: 4}
  - {from: jd, to: sf, label: kept, step: 5}
  - {from: sf, to: rl, label: init, step: 6}
  - {from: rl, to: en, label: rollouts, step: 6, style: dash}
  - {from: rw, to: rl, step: 6}
steps:
  - 'Collect tool specifications: real ones (Kimi K2 fetched 3,000+ MCP tools from GitHub) and synthetic ones evolved per domain (20,000+).'
  - 'Generate agents (system prompts, tool sets) and tasks from simple to complex, each with a rubric of success criteria.'
  - 'Run a model through each task in an environment: simulated tools and a simulated user, or real sandboxes where fidelity matters (code with test suites).'
  - A judge scores each trajectory against its rubric; only passing ones are kept.
  - Supervised fine-tuning on the kept trajectories teaches formats and habits.
  - 'Reinforcement learning then lets the policy act in environments and learn from rewards: verifiable ones (tests, final state) and, for open-ended tasks, rubric or self-critique rewards.'
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## One RL step for an agent

::: diagram 660x240
nodes:
  p: {at: [10, 20, 150, 56], text: Task + tools, sub: from the gym, color: f, step: 1}
  ro: {at: [190, 20, 150, 56], text: Rollouts, sub: G attempts each, color: a, step: 2}
  sb: {at: [370, 20, 140, 56], text: Sandbox, sub: executes tool calls, color: c, step: 2}
  rw: {at: [540, 20, 110, 56], text: Reward, sub: end of episode, color: e, step: 3}
  ad: {at: [540, 160, 110, 56], text: Advantage, sub: vs group mean, color: b, step: 4}
  mk: {at: [330, 160, 180, 56], text: Loss mask, sub: model tokens only, color: d, step: 5}
  up: {at: [120, 160, 180, 56], text: Policy update, sub: KL-regularised, color: a, step: 6}
edges:
  - {from: p, to: ro, step: 2}
  - {from: ro, to: sb, label: tool call, step: 2}
  - {from: sb, to: ro, label: observation, step: 2, style: back}
  - {from: sb, to: rw, label: final state, step: 3}
  - {from: rw, to: ad, step: 4}
  - {from: ad, to: mk, step: 5}
  - {from: mk, to: up, step: 6}
steps:
  - Sample a task with its tools and environment.
  - 'Generate several multi-turn attempts; each tool call is executed in a sandbox and the observation appended, like inference.'
  - 'Score each finished episode: do the tests pass, is the database in the expected state, does the answer match.'
  - 'Compare each attempt with the others for the same task (group-relative advantages, as in GRPO used by DeepSeek-R1).'
  - 'Compute the loss only on tokens the model generated; tool outputs in the context are masked out, since the model did not produce them.'
  - 'Update the policy, usually with a penalty for drifting too far from the reference model.'
:::



::: table
| Signal | Example | Risk |
|---|---|---|
| Verifiable reward | unit tests pass; final state matches | reward hacking (editing the tests) |
| Similarity reward | SWE-RL: patch similarity to the real fix | rewards one solution among many valid ones |
| Rubric / LLM judge | Kimi K2 self-critique rubric reward | judge bias; reward models can be gamed |
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

::: table
| Choice | Benefit | Cost |
|---|---|---|
| Real APIs and sandboxes | faithful feedback | slow, flaky, expensive to scale and reset |
| Simulated tools and users | cheap, unlimited, controllable | simulation gap: the model learns the simulator |
| SFT only | stable and simple | imitates the generator's mistakes; weak at recovery |
| RL on outcomes | learns recovery and long-horizon strategy | needs environments, verifiers and lots of compute |
| Distil from a stronger agent | fast way to a capable small model | capped by the teacher; licence limits on outputs |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Reward hacking | model deletes failing tests or special-cases checks | hidden tests, protected files, review of high-reward episodes |
| Overfitting to tool formats | great on the benchmark's tools, poor on new ones | held-out tools and APIs (ToolLLM tested unseen APIs and APIBench) |
| Credit assignment | one reward for 50 steps learns slowly | shorter tasks first, intermediate checks, curricula of moderate difficulty |
| Forgetting general skills | chat and reasoning regress after agent tuning | mixed data; RL rather than narrow SFT (SWE-RL's finding) |
| Unsafe habits | learns to take destructive shortcuts | safety tasks and penalties in the gym |
:::

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Environment infrastructure
Thousands of isolated sandboxes that start fast, reset cleanly and log everything.

### [c] Evaluation beyond the gym
Track agent benchmarks (SWE-bench Verified, τ-bench) and your own tasks, with pass^k for consistency.

### [b] Data provenance
Know which trajectories came from which generator and environment version.

### [e] Fine-tune or prompt?
For most applications, tool descriptions and examples beat training; fine-tune when volume justifies a smaller specialised model.
:::

<!-- slide id="s-papers" from="papers" -->
