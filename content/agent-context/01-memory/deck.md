---
title: Memory and Context Management
body:
  data-deck: Memory and context management
  data-home: ../index.html
  data-home-label: Context
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
- ../../shared/diagram.js
intro:
  kicker: Visual Agents · Context · 01
  h1: Memory and context management
  sub: 'How agents remember: the context window as working memory, compaction and notes for long tasks, and long-term stores with scored retrieval and reflection.'
  problem: The context window is finite and gets less reliable as it fills ("context rot"; models miss facts in the middle of long contexts), yet agents run for many
    steps and users expect them to remember across sessions.
  core: Treat context as a scarce <b>attention budget</b>. Keep <b>working memory</b> curated; <b>compact</b> (summarise and restart) near the limit; write <b>structured
    notes</b> to external storage; retrieve <b>long-term memories</b> by a score such as recency + importance + relevance (Generative Agents) or let the model page
    memory in and out itself (MemGPT).
  hint: 'Next: [Agentic retrieval (RAG) →](../02-agentic-rag/index.html) · [All decks](../index.html)'
papers:
- context_eng
- memgpt
- genagents
- lostmiddle
---

<!-- slide from="title" -->

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Context is finite and fragile

::: cards grid3
### [d] Context rot
As tokens increase, recall of information in the context decreases (Anthropic, context engineering).

### [b] Lost in the middle
Performance is often highest when relevant information is at the start or end and degrades in the middle (Liu et al.).

### [c] Sessions end
Nothing persists unless the agent writes it somewhere.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Tiers of memory

::: cards grid2
### [a] Working memory
The context window: system prompt, task, recent steps, retrieved items. Curate it.

### [c] Compaction
Near the limit, summarise the conversation and start a new context with the summary.

### [b] Structured notes
The agent writes progress, decisions and to-dos to files or a store and reads them back later.

### [e] Long-term memory
Episodes, facts and reflections retrieved on demand; MemGPT pages them in and out like OS virtual memory.
:::

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## Memory architecture

::: diagram 660x300
nodes:
  ag: {at: [20, 120, 130, 60], text: Agent, sub: LLM loop, color: a, step: 1}
  cm: {at: [210, 120, 160, 60], text: Context manager, sub: assemble · compact, color: c, step: 2}
  wm: {at: [430, 20, 200, 50], text: Working memory, sub: context window, color: f, step: 2}
  nt: {at: [430, 100, 200, 50], text: Notes / scratch files, sub: 'progress, to-dos', color: e, step: 3}
  lt: {at: [430, 180, 200, 50], text: Long-term store, sub: vector + metadata, color: b, step: 4}
  rf: {at: [430, 250, 200, 44], text: Reflections, sub: periodic summaries, color: d, step: 5}
edges:
  - {from: ag, to: cm, step: 2}
  - {from: cm, to: wm, label: fits budget, step: 2}
  - {from: cm, to: nt, label: write / read, step: 3}
  - {from: cm, to: lt, label: retrieve, step: 4}
  - {from: lt, to: rf, label: synthesise, step: 5}
steps:
  - The agent loop asks for context each step.
  - 'A context manager decides what goes into the window, compacting history when it nears the limit.'
  - Durable notes hold task state outside the window.
  - A long-term store returns the most useful memories for the current query.
  - 'Periodically, memories are synthesised into higher-level reflections (Generative Agents reflected when summed importance exceeded a threshold, 150 in their implementation).'
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Scoring and writing memories

::: diagram 660x250
nodes:
  q: {at: [20, 190, 150, 50], text: Current query, color: f, step: 1}
  m: {at: [20, 60, 170, 50], text: Memory records, sub: text · time · importance, color: e, step: 1}
  r1: {at: [240, 10, 160, 44], text: Recency, sub: decay 0.995 / game hour, color: c, step: 2}
  r2: {at: [240, 80, 160, 44], text: Importance, sub: LLM-rated 1–10, color: b, step: 2}
  r3: {at: [240, 150, 160, 44], text: Relevance, sub: cosine similarity, color: a, step: 2}
  s: {at: [460, 80, 180, 56], text: score = sum, sub: 'each min-max scaled, weights 1', color: d, step: 3}
  top: {at: [460, 190, 180, 50], text: Top memories, sub: that fit the window, color: e, step: 4}
edges:
  - {from: q, to: r3, step: 2}
  - {from: m, to: r1, step: 2}
  - {from: m, to: r2, step: 2}
  - {from: m, to: r3, step: 2}
  - {from: r1, to: s, step: 3}
  - {from: r2, to: s, step: 3}
  - {from: r3, to: s, step: 3}
  - {from: s, to: top, label: rank, step: 4}
steps:
  - 'Each memory record has text, timestamps, an importance rating and an embedding.'
  - 'Three signals (Park et al., 2023): recency (exponential decay, factor 0.995 per sandbox hour), importance (the model rates 1–10), relevance (cosine similarity to the query).'
  - 'Each is min-max scaled to [0, 1] and summed with all weights set to 1.'
  - The top-ranked memories that fit in the context window go into the prompt.
:::

::: cards grid3
### [a] Write policy
What to store: decisions, user preferences, outcomes; not every token.

### [c] Compaction trigger
At a set fraction of the window, summarise and restart; keep the goal and open issues verbatim.

### [d] Forget policy
Expire, deduplicate and correct memories; contradictions must be resolved.
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

::: table
| Choice | Benefit | Cost |
|---|---|---|
| Keep full history in context | nothing lost | context rot, cost grows every step |
| Compaction (summarise) | long tasks fit | details can be lost in the summary |
| Retrieval from a store | scales to large memories | retrieval misses; embedding and storage cost |
| Agent-managed memory (MemGPT-style) | model decides what to keep | extra tool calls; model may manage it badly |
| Just-in-time loading | only identifiers in context, data fetched when needed | more tool calls, latency |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Stale or contradictory memories | acts on outdated preferences | timestamps, update-in-place, conflict resolution |
| Lossy compaction | forgets a constraint after summarising | pin critical facts; test summaries |
| Memory poisoning | injected text persists and steers future sessions | validate what gets written; provenance |
| Cross-user leakage | one user's data appears for another | strict per-user/tenant isolation |
| Needle missed | fact in context but ignored | put key facts at the start or end; retrieve fewer, better items |
:::

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Privacy and deletion
Users must be able to see and delete memories; retention policies apply.

### [c] Multi-tenancy
Memory stores keyed and access-controlled per user and organisation.

### [b] Evaluate recall
Test that the right memory is retrieved and used, not just stored.

### [e] Cost
Embeddings, storage and longer prompts all cost money at scale.
:::

<!-- slide id="s-papers" from="papers" -->
