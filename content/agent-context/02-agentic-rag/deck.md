---
title: Agentic Retrieval (RAG)
body:
  data-deck: Agentic retrieval (RAG)
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
  kicker: Visual Agents · Context · 02
  h1: Agentic retrieval (RAG)
  sub: From retrieve-once-then-generate to agents that decide when and what to retrieve, check what they found, refine queries, and cite sources.
  problem: Classic RAG retrieves once from the user's question. Multi-hop questions, vague queries and bad retrieval results then lead straight to wrong, confident
    answers.
  core: 'Make retrieval a <b>tool the agent calls repeatedly</b>: plan queries, retrieve, <b>grade</b> relevance, <b>rewrite</b> or broaden the query, fall back to
    other sources, and answer with <b>citations</b>. Self-RAG trains the model to decide when to retrieve and critique; CRAG adds an evaluator and corrective web
    search.'
  hint: 'Previous: [Memory and context management](../01-memory/index.html) · Next: [Model Context Protocol (MCP) →](../03-mcp/index.html) · [All decks](../index.html)'
papers:
- rag_lewis
- selfrag
- crag
- greshake
---

<!-- slide from="title" -->

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## One retrieval is often not enough

::: cards grid3
### [d] Multi-hop questions
The second query depends on the first answer.

### [b] Bad retrieval
Irrelevant chunks are used anyway (CRAG's motivation).

### [c] Unneeded retrieval
Retrieving a fixed number of passages regardless of need hurts versatility (Self-RAG's motivation).
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Retrieval as a tool with feedback

::: cards grid2
### [f] Classic RAG
Lewis et al. (2020): a retriever over an index supplies passages to a generator.

### [a] Agentic loop
The agent decides whether to search, what query to send, and whether results suffice.

### [c] Self-critique
Self-RAG: reflection tokens to retrieve on demand and judge passages and its own output.

### [e] Correction
CRAG: a lightweight evaluator scores retrieval; poor results trigger refinement or web search.
:::

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## Components

::: diagram 660x300
nodes:
  q: {at: [20, 120, 110, 56], text: Question, color: f, step: 1}
  ag: {at: [180, 120, 140, 60], text: Agent, sub: plan queries, color: a, step: 2}
  vs: {at: [380, 10, 130, 50], text: Vector search, sub: semantic, color: c, step: 3}
  kw: {at: [380, 100, 130, 50], text: Keyword search, sub: BM25, color: c, step: 3}
  web: {at: [380, 235, 130, 50], text: Web / APIs, sub: fresh data, color: b, step: 5}
  gr: {at: [560, 160, 90, 56], text: Grader, sub: 'relevant?', color: d, step: 4}
  ans: {at: [180, 240, 140, 50], text: Answer + citations, color: e, step: 6}
edges:
  - {from: q, to: ag, step: 2}
  - {from: ag, to: vs, step: 3}
  - {from: ag, to: kw, step: 3}
  - {from: vs, to: gr, step: 4}
  - {from: kw, to: gr, step: 4}
  - {from: gr, to: ag, label: rewrite / more, step: 4, style: dash}
  - {from: ag, to: web, label: fallback, step: 5, style: dash}
  - {from: ag, to: ans, step: 6}
steps:
  - A question arrives.
  - 'The agent plans one or more queries (rewriting the question, splitting multi-hop questions).'
  - 'It searches indexes: semantic vector search and keyword search, often merged and reranked.'
  - A grader (a model or prompt) checks relevance; weak results lead to rewritten queries or more searches.
  - 'If the index lacks the answer, it falls back to other sources such as web search.'
  - 'It answers, citing the passages used.'
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## The retrieval loop in detail

::: diagram 660x300
nodes:
  p: {at: [20, 20, 160, 50], text: Plan query, sub: rewrite / decompose, color: a, step: 1}
  r: {at: [250, 20, 160, 50], text: Retrieve k, sub: hybrid + rerank, color: c, step: 2}
  g: {at: [480, 20, 160, 50], text: Grade, sub: per passage, color: d, step: 3}
  e: {at: [480, 130, 160, 50], text: 'Enough evidence?', color: b, step: 4}
  w: {at: [250, 130, 160, 50], text: Refine, sub: new query / source, color: c, step: 5}
  a: {at: [480, 230, 160, 50], text: Generate + cite, sub: check support, color: e, step: 6}
edges:
  - {from: p, to: r, step: 2}
  - {from: r, to: g, step: 3}
  - {from: g, to: e, step: 4}
  - {from: e, to: w, label: 'no', step: 5}
  - {from: w, to: r, step: 5}
  - {from: e, to: a, label: 'yes', step: 6}
steps:
  - Turn the question into search queries; split multi-hop questions into steps.
  - Retrieve top-k from hybrid (vector + keyword) search and rerank.
  - Grade each passage for relevance; drop the irrelevant ones.
  - Decide whether the kept evidence answers the question.
  - 'If not, refine: a new query, a different index, or web search; stop after a budget.'
  - Generate the answer from kept passages and check each claim is supported by a cited passage.
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

::: table
| Choice | Benefit | Cost |
|---|---|---|
| Classic one-shot RAG | one retrieval, low latency | fails on multi-hop and bad retrieval |
| Agentic retrieval loop | handles multi-hop, recovers from misses | several model and search calls per question |
| Pre-built index | fast, controlled corpus | staleness; ingestion pipeline to maintain |
| Just-in-time fetching | always fresh, no index | slower; depends on live sources |
| Small chunks | precise matches | lose surrounding context; more chunks to read |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Retrieval miss | answers from memory or says unknown | hybrid search, query rewriting, recall evals |
| Distracting passages | answer swayed by irrelevant text | grading and filtering; fewer, better passages |
| Citation hallucination | cites passages that do not support the claim | verify claim-passage support |
| Indirect prompt injection | retrieved page instructs the agent | treat retrieved text as data; restrict actions (Greshake et al.) |
| Search loops | keeps re-searching similar queries | budget; detect near-duplicate queries |
:::

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Freshness
Re-index on change; show document dates.

### [c] Access control
Retrieval must respect each user's document permissions.

### [b] Evaluate two things
Retrieval recall and answer faithfulness, separately.

### [e] Latency budgets
Each loop adds round trips; cap iterations for interactive use.
:::

<!-- slide id="s-papers" from="papers" -->
