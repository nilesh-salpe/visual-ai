---
title: Rerankers
body:
  data-deck: Rerankers
  data-home: ../index.html
  data-home-label: Retrieval
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
- ../../shared/diagram.js
intro:
  kicker: Visual Agents · Retrieval · 03
  h1: Rerankers
  sub: 'The second stage of retrieval: a slower, more accurate model rereads the query together with each candidate and reorders a short list. Cross-encoders, late
    interaction (ColBERT) and LLM rerankers.'
  problem: First-stage retrieval (BM25 or a bi-encoder) scores query and document <b>independently</b>, so it is fast but misses fine-grained relevance. The top 20
    chunks you hand the LLM often contain near-misses while the best passage sits at rank 60.
  core: '<b>Retrieve many cheaply, rerank few carefully.</b> Fetch around 100-150 candidates, score each with a model that reads query and document <b>together</b>
    (a cross-encoder), keep the best 20. Anthropic''s tests: top-20 failures fell from 2.9% to 1.9% when reranking was added to contextual hybrid search. Variants
    trade accuracy for speed: late interaction (ColBERT) and listwise LLM reranking (RankGPT).'
  hint: 'Previous: [Vector databases](../02-vector-databases/index.html) · [All decks](../index.html)'
papers:
- sbert
- monobert
- colbert
- rankgpt
- rrf
- contextual_retrieval
- cohere_rerank
---

<!-- slide from="title" -->

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Independent scoring misses relevance

::: cards grid3
### [d] One vector per text
A bi-encoder squeezes a passage into one vector before it has seen the query.

### [b] Lexical blind spots
BM25 matches words, not meaning; dense search matches meaning, not exact terms.

### [c] Recall vs precision
Wide top-k improves recall but floods the LLM context with noise and cost.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Two stages: wide recall, then precision

::: cards grid2
### [f] Why not cross-encode everything
Sentence-BERT's example: finding the most similar pair among 10,000 sentences takes ~65 hours with a BERT cross-encoder, ~5 seconds with a bi-encoder.

### [a] Cross-encoder
monoBERT feeds [query; passage] to BERT and outputs a relevance score: +27% relative MRR@10 on MS MARCO (Microsoft Machine Reading Comprehension) when it was published.

### [c] Late interaction
ColBERT keeps one embedding per token, precomputes documents and scores with MaxSim: competitive with BERT rerankers, two orders of magnitude faster.

### [e] LLM reranking
RankGPT asks an LLM for a permutation of passages with a sliding window over BM25's top 100; distilled into a 440M model it beats a 3B supervised reranker on BEIR.
:::

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## A two-stage retrieval service

::: diagram 660x290
nodes:
  q: {at: [10, 120, 100, 56], text: Query, color: f, step: 1}
  bm: {at: [150, 30, 150, 56], text: BM25, sub: top 100, color: b, step: 2}
  dn: {at: [150, 210, 150, 56], text: Dense ANN, sub: top 100, color: b, step: 2}
  fu: {at: [340, 120, 140, 56], text: Fuse, sub: RRF → ~150, color: c, step: 3}
  rr: {at: [520, 30, 130, 56], text: Reranker, sub: cross-encoder, color: a, step: 4}
  top: {at: [520, 210, 130, 56], text: Top 20, sub: to the LLM, color: e, step: 5}
edges:
  - {from: q, to: bm, step: 2}
  - {from: q, to: dn, step: 2}
  - {from: bm, to: fu, step: 3}
  - {from: dn, to: fu, step: 3}
  - {from: fu, to: rr, label: candidates, step: 4}
  - {from: rr, to: top, label: 'reorder, cut', step: 5}
steps:
  - The query (often rewritten by the agent) enters retrieval.
  - 'Lexical and dense retrieval run in parallel, each returning about a hundred candidates.'
  - 'Reciprocal rank fusion merges the lists: score(d) = Σ 1/(60 + rank) over the lists; no score calibration needed.'
  - The reranker reads the query with each candidate and scores it. Anthropic retrieved the top 150 and reranked them.
  - Only the best 20 go into the model's context; Anthropic found 20 better than 5 or 10.
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Three ways to score

::: diagram 660x290
nodes:
  i1: {at: [10, 20, 200, 50], text: q and d apart, sub: bi-encoder, color: f, step: 1}
  m1: {at: [10, 115, 200, 56], text: Two encodings, sub: docs precomputed, color: b, step: 1}
  o1: {at: [10, 220, 200, 56], text: cosine / dot, sub: one vector each, color: b, step: 1}
  i2: {at: [230, 20, 200, 50], text: '[q ; d] together', sub: cross-encoder, color: f, step: 2}
  m2: {at: [230, 115, 200, 56], text: Full attention, sub: every pair at query time, color: a, step: 2}
  o2: {at: [230, 220, 200, 56], text: relevance score, sub: most accurate, color: a, step: 2}
  i3: {at: [450, 20, 200, 50], text: q tokens · d tokens, sub: late interaction, color: f, step: 3}
  m3: {at: [450, 115, 200, 56], text: Token embeddings, sub: docs precomputed, color: c, step: 3}
  o3: {at: [450, 220, 200, 56], text: Σ MaxSim, sub: per query token, color: c, step: 3}
edges:
  - {from: i1, to: m1, step: 1}
  - {from: m1, to: o1, step: 1}
  - {from: i2, to: m2, step: 2}
  - {from: m2, to: o2, step: 2}
  - {from: i3, to: m3, step: 3}
  - {from: m3, to: o3, step: 3}
steps:
  - 'Bi-encoder (first stage): query and document are encoded separately; documents once, offline, so search is a vector lookup (DPR, Sentence-BERT).'
  - 'Cross-encoder (reranker): query and document share one input, so attention compares every query token with every document token. Accurate, but a full model call per pair at query time.'
  - 'Late interaction (ColBERT): token-level embeddings for both, documents precomputed; each query token takes its best-matching document token, and the scores are summed.'
:::



::: table
| Reranker | Input per call | Calls per query |
|---|---|---|
| Cross-encoder (pointwise) | one query-passage pair | one per candidate (batched) |
| LLM listwise (RankGPT) | a window of passages | windows slide from the back of the list to the front |
| Hosted API (e.g. Cohere Rerank) | query + list of documents | one request; scores per document |
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

::: table
| Option | Benefit | Cost |
|---|---|---|
| No reranker | lowest latency | precision limited by the first stage |
| Cross-encoder | large precision gain for a short list | latency grows with candidates × length |
| ColBERT | near cross-encoder quality at lower query cost | stores an embedding per token: much larger index |
| LLM listwise | strong zero-shot, follows instructions | expensive and slow; position bias |
| Deeper candidate list | higher recall going in | more reranker compute per query |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Recall ceiling | the right passage was never retrieved | reranking only reorders: fix the first stage (hybrid, contextual chunks) |
| Truncation | long chunks cut at the model's input limit, answer lost | chunk to fit the reranker; check its maximum length |
| Uncalibrated scores | a fixed score threshold drops good results on some queries | cut by rank, or calibrate per domain |
| Latency spikes | p99 grows with candidate count | cap candidates, batch on GPU, time-out to first-stage order |
| Domain shift | web-trained reranker misjudges code or legal text | evaluate on your data; fine-tune or distil |
:::

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Measure both stages
Track recall@150 for the first stage and nDCG@10 (normalised discounted cumulative gain) after reranking.

### [c] Latency budget
An agent may search several times per task; budget the reranker per call.

### [b] Distil
Use an LLM reranker offline to label data, then train a small cross-encoder for serving, as RankGPT did.

### [e] Structured documents
Format semi-structured records consistently (Cohere recommends YAML strings) so the reranker sees the fields.
:::

<!-- slide id="s-papers" from="papers" -->
