---
title: Enterprise RAG Assistant
body:
  data-deck: Enterprise RAG assistant
  data-home: ../index.html
  data-home-label: System design
  data-doc: design.html
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
- ../../shared/diagram.js
intro:
  kicker: Visual AI · System design · 02
  h1: An enterprise RAG assistant
  sub: 'A question-answering assistant over a company''s documents: indexing at scale, permission-aware retrieval, hybrid search and reranking, grounded answers with
    citations, freshness and evaluation.'
  problem: Design an assistant that answers employees' questions from 10 million internal documents, never reveals a document a user cannot open, cites its sources
    and stays fresh as documents change.
  core: An offline <b>indexing pipeline</b> (parse, chunk, add context, embed, BM25) keyed by content hash, with <b>access lists on every chunk</b>; an online path
    that rewrites the query, runs <b>hybrid search filtered by the user's groups</b>, fuses with RRF, <b>reranks</b> about 150 candidates to 20, and has the model
    <b>answer with citations</b>. Measure retrieval recall and groundedness continuously.
  hint: '[Read the full design doc →](design.html) · Previous: [Serving a chat assistant](../01-chat-assistant/index.html) · Next: [Autonomous coding agent →](../03-coding-agent/index.html)
    · [All case studies](../index.html)'
papers:
- contextual_retrieval
- rrf
- monobert
- hnsw
- diskann
- owasp_llm
- beir
- pq
- tail_at_scale
---

<!-- slide from="title" -->

<!-- slide id="s-req" chapter="Requirements" tag="1 · Requirements" tagclass="b1" -->
## What the system must do

::: cards grid2
### [f] Functional
Answer questions from internal documents with citations; say "not found" when the documents do not answer; multi-turn follow-ups.

### [d] Hard requirement
Never show or use a document the asking user cannot open in the source system.

### [a] Scale (assumption)
10M documents averaging 2,000 tokens; 50,000 employees asking 10 questions a day; peak 3× average.

### [e] Freshness and latency (target)
Edits searchable within 15 minutes; permission revocations within 5; first answer token p95 under 3 s.
:::

<!-- slide id="s-est" chapter="Estimates" tag="2 · Estimates" tagclass="b2" -->
## Index size and cost <span class="ill">calculator</span>

<div class="visual"><div class="controls"><label class="ctl">documents (M) <input type="range" id="rD" min="1" max="100" step="1" value="10"> <output id="rDo"></output></label><label class="ctl">tokens / document <input type="range" id="rT" min="200" max="10000" step="100" value="2000"> <output id="rTo"></output></label><label class="ctl">chunk tokens <input type="range" id="rC" min="100" max="1000" step="50" value="400"> <output id="rCo"></output></label><label class="ctl">embedding dims <input type="range" id="rM" min="256" max="3072" step="128" value="1024"> <output id="rMo"></output></label><label class="ctl">bytes / dim <input type="range" id="rB" min="1" max="4" step="1" value="4"> <output id="rBo"></output></label></div><div class="bars"><div id="rBars"></div></div><p class="readout" id="rOut"></p></div>

Query load: 50,000 × 10 = 500K questions a day ≈ 5.8 per second on average, about 17 at peak: retrieval capacity is easy; ingestion volume, permissions and quality are the hard parts.

<!-- slide id="s-arch" chapter="Architecture" tag="3 · Architecture" tagclass="b3" -->
## Architecture

::: diagram 660x270
nodes:
  src: {at: [10, 20, 130, 56], text: Sources, sub: wiki · drive · tickets, color: f, step: 1}
  ing: {at: [180, 20, 150, 56], text: Ingestion, sub: parse · chunk · context, color: b, step: 2}
  idx: {at: [370, 20, 140, 56], text: Indexes, sub: vectors + BM25, color: e, step: 3}
  acl: {at: [550, 20, 100, 56], text: ACL sync, sub: groups, color: d, step: 4}
  u: {at: [10, 180, 130, 56], text: Employee, sub: question, color: f, step: 5}
  qs: {at: [180, 180, 150, 56], text: Query service, sub: rewrite · retrieve, color: a, step: 5}
  rr: {at: [370, 180, 140, 56], text: Reranker, sub: 150 → 20, color: c, step: 6}
  llm: {at: [550, 180, 100, 56], text: LLM, sub: answer + cite, color: a, step: 7}
edges:
  - {from: src, to: ing, step: 2}
  - {from: ing, to: idx, step: 3}
  - {from: acl, to: idx, label: permissions, step: 4, style: dash}
  - {from: u, to: qs, step: 5}
  - {from: qs, to: idx, label: filtered search, step: 5, style: dash}
  - {from: qs, to: rr, step: 6}
  - {from: rr, to: llm, step: 7}
steps:
  - Connectors pull documents and their permissions from each source and emit change events.
  - 'Ingestion parses, chunks, adds chunk context and metadata, and embeds.'
  - 'Each chunk lands in a vector index and a lexical (BM25) index, tagged with its access list.'
  - Permission changes are synced into the index so revoked access takes effect quickly.
  - An employee asks; the query service rewrites the question and searches both indexes with a filter on the user's groups.
  - Fused candidates (about 150) are reranked to the best 20.
  - The LLM answers from those passages only and cites them.
:::

<!-- slide id="s-flow" chapter="Walkthrough" tag="4 · Walkthrough" tagclass="b4" -->
## Answering one question

::: diagram 660x270
nodes:
  q: {at: [10, 20, 120, 56], text: Question, color: f, step: 1}
  rw: {at: [160, 20, 140, 56], text: Rewrite, sub: standalone query, color: a, step: 2}
  bm: {at: [330, 20, 140, 56], text: BM25, sub: top 100, color: b, step: 3}
  dn: {at: [330, 130, 140, 56], text: Dense ANN, sub: top 100, color: b, step: 3}
  fu: {at: [500, 70, 150, 56], text: Fuse (RRF), sub: ~150 candidates, color: c, step: 4}
  rr: {at: [500, 200, 150, 56], text: Rerank, sub: keep 20, color: c, step: 5}
  ans: {at: [160, 200, 300, 56], text: Answer with citations, sub: or "not found", color: e, step: 6}
edges:
  - {from: q, to: rw, step: 2}
  - {from: rw, to: bm, step: 3}
  - {from: rw, to: dn, step: 3}
  - {from: bm, to: fu, step: 4}
  - {from: dn, to: fu, step: 4}
  - {from: fu, to: rr, step: 5}
  - {from: rr, to: ans, step: 6}
steps:
  - 'A question arrives, possibly mid-conversation.'
  - An LLM rewrites it into a standalone search query using the conversation.
  - 'Lexical and dense retrieval run in parallel, both filtered by the user''s access groups.'
  - Dense search uses the same filter inside the ANN index.
  - Reciprocal rank fusion (k = 60) merges the two lists.
  - A cross-encoder reranks about 150 candidates and keeps 20.
  - 'The model answers only from those passages, cites them, and says when the answer is not in them.'
:::

<!-- slide id="s-deep" chapter="Deep dive" tag="5 · Deep dive" tagclass="b5" -->
## Deep dive: permissions inside retrieval

::: cards grid2
### [d] Filter before ranking
Every chunk carries its document's access list; the search filters by the user's groups inside the index, so unauthorised text never reaches the reranker or the model.

### [b] Sync permissions fast
Permission changes come from the identity system and source connectors as events; revocations update chunk metadata within minutes, with a nightly reconciliation.

### [c] Re-check at read time
Before showing a citation, check the document's current permission with the source system: a stale index must not leak.

### [a] Restrictive filters
Very selective filters can starve approximate search of candidates: partition indexes by large groups, or fall back to exact search on small filtered sets.
:::

<!-- slide id="s-scale" chapter="Scaling" tag="6 · Scaling" tagclass="b6" -->
## What breaks at 10×

::: table
| Bottleneck | Symptom | Response |
|---|---|---|
| Index memory | HNSW over RAM | product quantization, DiskANN-style SSD graphs, sharding by source |
| Re-embedding | a model upgrade means re-embedding billions of tokens | versioned indexes, blue/green swap, scheduled backfills |
| Ingestion bursts | freshness lags after bulk imports | priority queues for edits and deletes, autoscaled workers |
| Reranker latency | p99 grows with candidate count | cap candidates, GPU batching, time out to fused order |
| Long documents | answer split across chunks | structure-aware chunking, neighbouring-chunk expansion |
:::

<!-- slide id="s-web" chapter="Web scale" tag="6 · Scaling: web scale" tagclass="b6" -->
## At web scale: a billion documents, a million queries a second <span class="ill">calculator</span>

<div class="visual"><div class="controls"><label class="ctl">documents (billions) <input type="range" id="wsD" min="0.1" max="5" step="0.1" value="1"> <output id="wsDo"></output></label><label class="ctl">queries/s <input type="range" id="wsQ" min="10000" max="2000000" step="10000" value="1000000"> <output id="wsQo"></output></label><label class="ctl">cache hit rate <input type="range" id="wsC" min="0" max="90" step="5" value="50"> <output id="wsCo"></output></label><label class="ctl">queries that get an LLM answer <input type="range" id="wsL" min="0" max="100" step="1" value="5"> <output id="wsLo"></output></label></div><div class="bars"><div id="wsBars"></div></div><p class="readout" id="wsOut"></p></div>

Assumptions: 3 chunks per document; vectors compressed with product quantization to 64 bytes plus 64 bytes of graph and ids; 50 million vectors per shard; 2,000 queries/s per shard replica; 300 output tokens per LLM answer at 10,000 tokens/s per 8-GPU replica.

::: cards grid2
### [d] Fan-out sets the tail
A query that touches every shard waits for the slowest. If each shard is slow 1% of the time, a 60-shard query is slow 1 − 0.99⁶⁰ ≈ 45% of the time. Send hedged requests to a second replica after the expected latency, and cut fan-out by partitioning (by tenant, language or topic).

### [a] Index layout
Shard the vectors, replicate each shard for throughput, and keep the compressed index in RAM (or on SSD with DiskANN-style indexes); fetch full text only for the final top-k.

### [b] Cache first
Popular queries repeat: cache retrieval results and generated answers by normalised query, with short TTLs and invalidation on index updates.

### [e] The LLM is the expensive part
Generating an answer for every query at a million per second would need hundreds of thousands of GPUs. Generate for a fraction (an answer box), cache answers, and use a small model where quality allows.
:::

<!-- slide id="s-fail" chapter="Failures" tag="7 · Failures and operations" tagclass="b7" -->
## Failures and operations

::: cards grid2
### [d] Leaked document
Treat as a security incident: audit logs of query, user, chunks and citations make it traceable.

### [b] Stale or deleted content
Deletes processed from the change feed; reconciliation catches missed events.

### [c] Retrieval regressions
A labelled query set (recall@20) and groundedness checks run on every index or model change.

### [a] Prompt injection in documents
Retrieved text is data: instructions inside documents are ignored, and the assistant has no write tools.
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="8 · Trade-offs" tagclass="b8" -->
## Trade-offs and alternatives

::: table
| Decision | Chosen | Alternative | Why |
|---|---|---|---|
| Retrieval | hybrid BM25 + dense, RRF, rerank | dense only | exact identifiers and rare terms need lexical match |
| Chunks | contextual chunks (LLM-written context) | plain chunks or late chunking | Anthropic: failures −49% with BM25, −67% with reranking |
| Permissions | pre-filter in the index + read-time check | filter after retrieval | post-filtering exposes text to the pipeline and returns fewer results |
| Index | HNSW with quantization | flat search | flat is exact but too slow and memory-hungry at 50M chunks |
| Small corpora | retrieval | put everything in the prompt | under ~200K tokens, skip retrieval and use prompt caching |
:::

<!-- slide id="s-sum" chapter="Summary" tag="9 · Summary" tagclass="b9" -->
## Summary

::: cards grid2
### [a] Quality is decided at indexing
Parse well, chunk with context, keep metadata and access lists.

### [d] Permissions inside retrieval
Filter in the index and re-check at read time; never after generation.

### [c] Hybrid, fused, reranked
BM25 + dense, RRF, rerank 150 → 20, answer with citations.

### [e] Read more
Full design document: [design.html](design.html). Related decks: [Indexing](../../agent-retrieval/01-indexing/index.html), [Vector databases](../../agent-retrieval/02-vector-databases/index.html), [Rerankers](../../agent-retrieval/03-rerankers/index.html), [Access control](../../agent-infra/03-access-control/index.html).
:::

<!-- slide id="s-papers" from="papers" -->
