---
title: 'Enterprise RAG Assistant: design document'
back: index.html
back_label: Overview deck
---

# An enterprise RAG assistant

> **Design question.** Build an assistant that answers employees' questions from 10 million internal documents, never reveals a document a user cannot open, cites its sources and stays fresh as documents change.

## 1. Goals and non-goals

**Goals:** grounded answers with citations; strict permission enforcement; freshness within minutes; measurable retrieval quality.

**Non-goals:** writing back to source systems; answering from the public web; agentic multi-step research (a later phase).

## 2. Requirements

| Type | Requirement |
|---|---|
| Functional | ask and follow up; answers cite passages; "not found" when sources do not answer; feedback on answers |
| Security | a user only ever sees content they can open in the source system |
| Scale (assumption) | 10M documents × ~2,000 tokens; 50,000 employees × 10 questions/day; peak 3× |
| Freshness (target) | edits searchable in 15 min; revocations enforced in 5 min |
| Latency (target) | first answer token p95 < 3 s |

## 3. Estimates

- **Corpus:** 10M × 2,000 = **20B tokens** → at 400-token chunks, **50M chunks**.
- **Vectors:** 1,024 dimensions × 4 bytes = 4 KB per chunk → **205 GB** raw. HNSW with M = 16 adds up to 32 neighbour ids × 4 bytes = 128 bytes per vector (+6.4 GB). Product quantization at 64 bytes plus an 8-byte id is **3.6 GB**, with re-scoring of top candidates on full vectors.
- **Contextual chunks:** Anthropic estimates **$1.02 per million document tokens** (with their assumptions of 8K-token documents and 800-token chunks) → about **$20,000 one-time** for 20B tokens, plus the cost of changed documents.
- **Queries:** 500K/day → ~5.8 per second average, ~17 at peak.

## 4. Architecture

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

## 5. Components

### 5.1 Connectors and change feed
One connector per source (wiki, drive, ticketing, code). Each emits create, update, delete and permission-change events with document version, content hash and access list.

### 5.2 Ingestion pipeline
Layout-aware parsing (tables kept whole), structure-aware chunking (a few hundred tokens), an LLM-written context sentence per chunk (Contextual Retrieval), metadata (source, title, section, timestamps, access list), embeddings with a pinned model version, and BM25 terms. Unchanged chunks are skipped by content hash.

### 5.3 Indexes
A vector index (HNSW, quantized when memory requires) and a lexical index, both supporting filters on access-list metadata. Indexes are versioned; a new embedding model means building a new index and switching an alias after evaluation.

### 5.4 Query service
Rewrites follow-ups into standalone queries, runs BM25 (top 100) and dense search (top 100) in parallel with the user's group filter, fuses with reciprocal rank fusion (k = 60), and reranks about 150 candidates to 20 with a cross-encoder (Anthropic found retrieving 150 and keeping 20 best among the options they tried).

### 5.5 Answer generation
The model answers only from the 20 passages, cites passage ids, and returns "not found" when they do not contain the answer. Citations are rendered from the source system after a read-time permission check.

## 6. Data model

```
chunk(id, doc_id, doc_version, text, context, embedding_v3, bm25_terms,
      acl_groups[], source, title, section, updated_at, content_hash)
```

## 7. Scaling plan

Quantize or move to SSD-resident graphs as the corpus grows; shard by source with a query router; priority queues so deletes and permission changes overtake bulk imports; scheduled re-embedding backfills.

### 7.1 At web scale: a billion documents, a million queries per second

A frequently reported variant asks for search over a billion documents at a million queries per second. The enterprise design above changes in five ways (all inputs below are assumptions):

| Quantity | Formula | Value |
|---|---|---|
| Vectors | 1B documents × 3 chunks | 3B |
| Index size | 3B × (64-byte PQ code + 64 bytes graph and ids) | ≈ 384 GB in RAM |
| Shards | 3B ÷ 50M vectors per shard | 60 |
| Shard replicas | uncached queries/s ÷ 2,000 queries/s per replica | 1M × 50% miss ÷ 2,000 = 250 per shard → 15,000 shard servers if every query hits every shard |
| Slow queries | 1 − 0.99⁶⁰ | ≈ 45% of queries touch at least one shard in its slowest 1% |
| LLM answers | queries × share answered × 300 tokens ÷ 10,000 tokens/s per 8-GPU replica | 5% of 500K/s → 750 replicas = 6,000 GPUs; for every query: 120,000 GPUs |

Design changes:
1. **Partition to cut fan-out.** Route a query only to shards that can contain its answer (by language, region, tenant or a coarse topic classifier); each halving of fan-out halves the shard servers needed.
2. **Tolerate the tail.** Hedged requests: after the expected latency, send the same shard request to a second replica and take the first answer (Dean and Barroso, The Tail at Scale). Return partial results if a shard misses the deadline.
3. **Cache aggressively.** Result and answer caches keyed by normalised query; a 50% hit rate halves every downstream row.
4. **Keep the index compact.** Product quantization (64 bytes per vector) in RAM, or SSD-resident graph indexes (DiskANN) to cut RAM cost; full text fetched only for the final top-k.
5. **Budget the LLM.** Generate only where it adds value (an answer box for a fraction of queries), cache answers, prefer a small model, and stream.

## 8. Reliability and security

| Risk | Control |
|---|---|
| Leaking restricted content | pre-filter by access list inside the index; read-time permission check; audit log of every answer's sources |
| Stale permissions | event-driven sync, nightly reconciliation, alert on sync lag |
| Prompt injection in documents | retrieved text treated as data; no write tools; output filters |
| Deleted documents still retrievable | deletes from the change feed; reconciliation; tombstones compacted |

## 9. Evaluation

A labelled set of real questions with known supporting documents: **recall@20** (Anthropic reports 1 − recall@20 as the retrieval failure rate), nDCG@10 after reranking, groundedness (every claim supported by a cited passage, checked by a judge and sampled human review), and "not found" accuracy. Online: answer ratings and citation clicks, analysed with A/B tests for changes.

## 10. Alternatives considered

- **Dense-only retrieval:** simpler, but misses exact identifiers; BEIR found BM25 a robust zero-shot baseline.
- **Post-filtering by permission:** leaks text into the pipeline and returns too few results.
- **Long-context only:** if a team's corpus is under about 200,000 tokens, put it in the prompt with prompt caching instead.

## 11. Observability

Retrieval: recall@k on a labelled question set, the share of answers with citations, "not found" rate, permission-filter rejections. Freshness: lag from source edit to searchable, and from revocation to enforcement (targets 15 and 5 minutes). Serving: time to first token, tokens per answer, cache hit rate, cost per question. Feedback: thumbs-down rate and the questions behind it.

## 12. Cost model

- **One-time indexing:** contextual chunking at Anthropic's estimate of $1.02 per million document tokens → about $20,000 for 20B tokens, plus embedding cost, then only changed documents.
- **Per question (assumptions):** 20 retrieved chunks × 400 tokens = 8,000 input tokens plus ~500 output tokens. At 500K questions a day: **4B input and 250M output tokens per day**. Multiply by the model's price per token (or by GPU-hours if self-hosted).
- **Levers:** fewer, better chunks after reranking; prompt caching of the fixed instructions; a smaller model for simple questions; caching answers to repeated questions.
- **Index storage:** 205 GB of full vectors, or 3.6 GB with product quantization plus re-scoring.

## 13. Rollout

Start with one department's sources and an evaluation set of real questions with expected citations; shadow-launch answers to measure recall and faithfulness; enable permissions enforcement and freshness monitoring before broad launch; add sources one connector at a time.

## 14. Risks and open questions

Permission models differ per source system and must be mirrored exactly; stale ACLs are a security incident, not a quality bug; tables and scanned PDFs parse poorly; users will ask questions the corpus cannot answer, so "not found" must be a good answer.

## References

Anthropic, Introducing Contextual Retrieval (2024); Cormack et al. 2009 (RRF); Nogueira & Cho 2019 (cross-encoder reranking); Malkov & Yashunin (HNSW); Subramanya et al. 2019 (DiskANN); Thakur et al. 2021 (BEIR); OWASP Top 10 for LLM Applications 2025. Related decks: indexing pipelines, vector databases, rerankers, identity and access control, agentic RAG.
