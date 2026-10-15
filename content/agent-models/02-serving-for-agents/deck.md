---
title: Serving LLMs for Agent Workloads
body:
  data-deck: Serving LLMs for agent workloads
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
  kicker: Visual Agents · Models · 02
  h1: Serving LLMs for agent workloads
  sub: 'Why agent traffic stresses inference servers differently from chat, and the server-side techniques that help: prefix reuse across turns, constrained decoding
    for tool calls, program-aware scheduling, and smaller models.'
  problem: 'An agent task is a <b>program</b> of many dependent calls sharing a long, growing prefix, separated by tool executions, each ending in strict JSON. Request-level
    schedulers see unrelated requests: they recompute shared prefixes, let one long program block others (head-of-line blocking) and optimise per-request latency
    when the user waits for the whole task.'
  core: 'Serve the program, not the request: <b>reuse KV cache across turns</b> (SGLang''s RadixAttention, up to 6.4× throughput), <b>constrain decoding</b> to the
    tool schema cheaply (XGrammar, near-zero overhead), <b>schedule with program context</b> (Autellix, 4-15× program throughput vs vLLM at the same latency), and
    use <b>smaller or distilled models</b> and speculative decoding where steps are easy.'
  hint: 'Previous: [Training LLMs for agents](../01-training-for-agents/index.html) · [All decks](../index.html)'
papers:
- sglang
- xgrammar
- outlines
- format_freely
- autellix
- parrot
- vllm_apc
---

<!-- slide from="title" -->

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Agent traffic is not chat traffic

::: cards grid2
### [d] Repeated prefixes
Every turn resends system prompt, tools and history; without reuse the server prefills them again.

### [b] Strict outputs
Tool calls must parse; one malformed argument costs a full extra turn.

### [c] Dependent calls
Call n+1 waits for call n and a tool run; latency adds up across the program.

### [a] Head-of-line blocking
Autellix found programs suffer long cumulative waits, blocked at both the request and the program level.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Make the server program-aware

::: cards grid2
### [f] Prefix reuse
Keep KV blocks of earlier turns and match the longest cached prefix (vLLM automatic prefix caching; SGLang's radix tree).

### [a] Constrained decoding
Mask tokens that would break the JSON schema or grammar. XGrammar prechecks context-independent tokens and checks the rest with a persistent stack: up to 100× faster than earlier engines.

### [c] Program-level scheduling
Autellix prioritises calls using each program's completed calls; Parrot's Semantic Variables expose data flow between requests.

### [e] Right-sized models
Distilled or small models for sub-agents and easy steps; speculative decoding for latency at low batch sizes.
:::

The client side of the same problem (prompt caching prices, compaction, budgets) is in the <a href="../../agent-operations/03-cost-and-latency/index.html">cost and latency</a> deck.

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## An agent-aware serving stack

::: diagram 660x300
nodes:
  pr: {at: [10, 120, 140, 56], text: Agent programs, sub: many calls each, color: f, step: 1}
  sc: {at: [190, 120, 140, 56], text: Scheduler, sub: program-aware, color: a, step: 2}
  en: {at: [370, 120, 140, 56], text: Engine, sub: continuous batching, color: b, step: 3}
  rx: {at: [370, 20, 140, 56], text: Prefix cache, sub: radix tree of KV, color: e, step: 3}
  gm: {at: [370, 225, 140, 56], text: Grammar mask, sub: tool JSON schema, color: c, step: 4}
  gp: {at: [550, 120, 100, 56], text: GPUs, color: b, step: 3}
  dr: {at: [550, 20, 100, 56], text: Draft model, sub: speculation, color: d, step: 5}
  tr: {at: [550, 225, 100, 56], text: Tools, sub: run outside, color: f, step: 6}
edges:
  - {from: pr, to: sc, step: 2}
  - {from: sc, to: en, step: 3}
  - {from: en, to: gp, step: 3}
  - {from: rx, to: en, label: reuse, step: 3}
  - {from: gm, to: en, label: allowed tokens, step: 4}
  - {from: dr, to: en, step: 5, style: dash}
  - {from: en, to: tr, label: tool call, step: 6, style: dash}
steps:
  - Many agent programs submit calls; each call belongs to a program with history.
  - 'The scheduler orders calls using program-level information, e.g. how much service each program has received, to avoid head-of-line blocking.'
  - The engine batches calls continuously; the prefix cache supplies KV for the shared history so only new tokens are prefilled.
  - During decoding a grammar mask allows only tokens that keep the tool call valid.
  - 'A small draft model can propose tokens the large model verifies, cutting latency when the batch is small.'
  - The tool call leaves the server; the program's KV waits in cache (or is offloaded) until the next turn.
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## One agent turn on the server

::: diagram 660x240
nodes:
  ar: {at: [10, 20, 150, 56], text: Turn n arrives, sub: history + new tokens, color: f, step: 1}
  mt: {at: [190, 20, 150, 56], text: Prefix match, sub: longest cached prefix, color: e, step: 2}
  pf: {at: [370, 20, 140, 56], text: Prefill, sub: new tokens only, color: a, step: 3}
  dc: {at: [540, 20, 110, 56], text: Decode, sub: masked by grammar, color: c, step: 4}
  tc: {at: [540, 160, 110, 56], text: Tool call, sub: valid JSON, color: c, step: 5}
  kv: {at: [300, 160, 210, 56], text: Keep KV while tool runs, sub: 'pin, TTL or offload to CPU', color: d, step: 6}
  nx: {at: [10, 160, 200, 56], text: Turn n+1, sub: hits the cache, color: e, step: 7}
edges:
  - {from: ar, to: mt, step: 2}
  - {from: mt, to: pf, step: 3}
  - {from: pf, to: dc, step: 4}
  - {from: dc, to: tc, step: 5}
  - {from: tc, to: kv, step: 6}
  - {from: kv, to: nx, step: 7}
steps:
  - 'A new turn arrives: the previous turns plus the latest tool result.'
  - The engine finds the longest prefix whose KV blocks are still cached.
  - Only the uncached suffix (the new tool result and any changed text) is prefilled.
  - Decoding applies the grammar mask so the output follows the tool schema.
  - 'The result is a valid tool call by construction, though not necessarily a correct one.'
  - 'While the tool runs, the program''s KV must survive: kept in GPU memory, given a time-to-live, or offloaded to CPU memory.'
  - 'If it survived, the next turn starts with almost everything cached; if it was evicted, the whole history is prefilled again.'
:::



::: table
| Concern | Chat-style serving | Agent-aware serving |
|---|---|---|
| Unit of scheduling | request | program (task) |
| Latency metric | time to first token per request | end-to-end task completion time |
| KV eviction | least recently used | aware that a program will return after its tool call |
| Output format | free text, validated after | grammar-constrained at decode time |
| Load balancing | least loaded replica | session or prefix affinity, so the cache is on that replica |
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

::: table
| Choice | Benefit | Cost |
|---|---|---|
| Keep KV during tool calls | next turn is nearly free to prefill | GPU memory held by idle programs |
| Evict or offload KV | room for more active requests | recompute or transfer when the program returns |
| Constrained decoding | tool calls always parse | Let Me Speak Freely?: strict format restrictions can degrade reasoning; let the model think before the constrained part |
| Prefix-affinity routing | high cache hit rates | uneven load across replicas |
| Speculative decoding | lower latency at small batch | less benefit at high batch; draft model memory |
| Smaller models for sub-agents | cheaper, faster steps | quality risk on hard steps (route them up) |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Cache thrash | hit rate collapses as concurrent agents exceed KV capacity | admission control, offload tiers, affinity routing |
| Prefix changes | a timestamp or reordered tools at the top kills reuse | stable prefixes; dynamic content at the end |
| Grammar compile stalls | first request with a new schema is slow | cache compiled grammars; precompile known tool schemas |
| Valid but wrong arguments | JSON parses, values are nonsense | schema enums and validation in the tool layer; constrained decoding only fixes syntax |
| Long programs starve short ones | quick tasks wait behind huge ones | program-aware fair scheduling (Autellix) |
:::

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Measure per task
Report task latency, tokens per task and prefix-cache hit rate, not just tokens per second.

### [c] Affinity
Route a session to the replica that holds its cache, with spillover when it is overloaded.

### [b] Capacity for idle KV
Size memory for programs waiting on tools, not only for active decoding.

### [e] Same engine features as hosted APIs
Self-hosting means owning prefix caching, structured outputs and tool parsing yourself (see the vLLM decks).
:::

<!-- slide id="s-papers" from="papers" -->
