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
- ../../shared/diagram.js
intro:
  kicker: Visual Agents · Operations · 03
  h1: Cost and latency
  sub: 'Why agent loops are expensive and slow (the context is re-sent every step), and the levers that fix it: prompt caching, compaction, model routing, parallel
    tool calls, and budgets.'
  problem: Each iteration re-sends the whole growing context, so total input tokens grow roughly quadratically with the number of steps. Anthropic reports agents
    use about 4× the tokens of chat and multi-agent systems about 15×.
  core: Make the repeated prefix cheap with <b>prompt caching</b> (cache reads at 0.1× the base input price on most Claude models), keep the context small with <b>compaction</b>
    and concise tool results, send easy steps to <b>smaller models</b>, run independent tool calls <b>in parallel</b>, and enforce <b>budgets</b> per task.
  hint: 'Previous: [Safety and reliability](../02-safety-and-reliability/index.html) · [All decks](../index.html)'
papers:
- ant_caching
- ma_research
- bea
---

<!-- slide from="title" -->

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

<div class="visual"><div class="controls"><label class="ctl">steps <input type="range" id="cS" min="1" max="60" step="1" value="20"> <output id="cSo"></output></label><label class="ctl">prefix tokens <input type="range" id="cP" min="1000" max="50000" step="1000" value="10000"> <output id="cPo"></output></label><label class="ctl">tokens added per step <input type="range" id="cT" min="100" max="10000" step="100" value="1500"> <output id="cTo"></output></label><label class="ctl"><input type="checkbox" id="cC" checked> cache</label></div><div class="bars"><div id="cBars"></div></div><p class="readout" id="cOut"></p></div>

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## Where time and money go

::: diagram 660x300
nodes:
  req: {at: [20, 120, 120, 56], text: Task, color: f, step: 1}
  rt: {at: [180, 120, 140, 56], text: Router, sub: 'small or large model?', color: b, step: 2}
  pc: {at: [380, 30, 150, 56], text: Prompt cache, sub: stable prefix, color: e, step: 3}
  llm: {at: [380, 140, 150, 56], text: Model call, sub: only new tokens computed, color: a, step: 3}
  tools: {at: [580, 140, 70, 56], text: Tools, sub: parallel, color: c, step: 4}
  cmp: {at: [380, 245, 150, 50], text: Compactor, sub: near the limit, color: d, step: 5}
  bud: {at: [180, 245, 140, 50], text: Budget guard, sub: steps · tokens · time, color: d, step: 6}
edges:
  - {from: req, to: rt, step: 2}
  - {from: rt, to: llm, step: 3}
  - {from: pc, to: llm, label: cache hit, step: 3}
  - {from: llm, to: tools, step: 4}
  - {from: tools, to: llm, step: 4, style: back}
  - {from: llm, to: cmp, step: 5, style: dash}
  - {from: cmp, to: bud, step: 6, style: dash}
steps:
  - A task enters the loop.
  - A router picks a model by difficulty.
  - 'Each call reuses the cached prefix (system prompt, tool definitions, earlier history); only new tokens are processed at full price.'
  - Independent tool calls run in parallel to cut wall-clock time.
  - 'When the context nears its limit, compaction summarises it.'
  - A budget guard stops runaway tasks.
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Token accounting per step

::: diagram 660x300
nodes:
  s1: {at: [20, 30, 120, 50], text: step 1, sub: P, color: f, step: 1}
  s2: {at: [160, 30, 140, 50], text: step 2, sub: P + T, color: f, step: 2}
  s3: {at: [320, 30, 160, 50], text: step 3, sub: P + 2T, color: f, step: 3}
  sn: {at: [500, 30, 150, 50], text: step n, sub: P + (n−1)T, color: d, step: 4}
  sum: {at: [160, 150, 340, 56], text: total input ≈ nP + T·n(n−1)/2, sub: grows ~ n² in the history term, color: d, step: 5}
  c: {at: [160, 240, 340, 50], text: 'cached: prefix at 0.1×, only the new T at full price', color: e, step: 6}
edges:
  - {from: s1, to: s2, step: 2}
  - {from: s2, to: s3, step: 3}
  - {from: s3, to: sn, step: 4, style: dash}
  - {from: sn, to: sum, step: 5}
  - {from: sum, to: c, step: 6}
steps:
  - 'Step 1 sends the prefix P (system prompt, tools, task).'
  - Step 2 also sends the T tokens added by step 1 (assistant turn + tool result).
  - Each step adds another T.
  - Step n sends P + (n − 1)T.
  - 'Summed over n steps, input tokens ≈ nP + T·n(n − 1)/2: quadratic in the number of steps.'
  - 'With a cache hit each step, the repeated part is billed at the read price and only the new tokens at full price.'
:::

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

::: table
| Lever | Saves | Costs |
|---|---|---|
| Prompt caching | most repeated input cost and time to first token | write premium; needs stable prefixes |
| Compaction | tokens on long tasks | possible loss of detail |
| Smaller model / routing | price and latency per call | more steps or lower quality on hard tasks |
| Parallel tool calls / subagents | wall-clock time | more tokens overall (multi-agent ≈ 15× chat) |
| Step budgets | runaway cost | some tasks end incomplete |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Runaway loops | a task burns thousands of calls | hard caps; repeated-action detection |
| Cache misses from unstable prefixes | cost does not drop with caching on | move dynamic content after the cached prefix; deterministic tool order |
| Tail latency from slow tools | p99 dominated by one dependency | timeouts, parallelism, fallbacks |
| Context bloat | huge tool outputs re-sent every step | truncate and summarise results |
| Silent cost growth | bill surprises after a prompt change | track cost per task in monitoring |
:::

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
