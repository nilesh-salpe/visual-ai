---
title: Indexing Pipelines
body:
  data-deck: Indexing pipelines
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
  kicker: Visual Agents · Retrieval · 01
  h1: Indexing pipelines for retrieval
  sub: 'Everything that happens before the first query: parsing, chunking, adding context and metadata, embedding, lexical indexes, and keeping the index fresh as
    documents change.'
  problem: Retrieval quality is mostly decided at indexing time. A chunk that says "revenue grew 3% over the previous quarter" without naming the company cannot be
    found by a query that names it; garbled tables, stale documents and missing permissions break even the best retriever.
  core: 'Run an <b>indexing pipeline</b>: parse → chunk → <b>enrich</b> (context, metadata, access lists) → embed and build a <b>lexical (BM25) index</b> → write,
    with <b>incremental updates</b> keyed by content hash. Anthropic''s <b>Contextual Retrieval</b> prepends 50-100 tokens of chunk-specific context, cutting top-20
    retrieval failures by 35%, by 49% with BM25, and by 67% with reranking.'
  hint: 'Next: [Vector databases →](../02-vector-databases/index.html) · [All decks](../index.html)'
papers:
- contextual_retrieval
- late_chunking
- beir
- mteb
- dpr
---

<!-- slide from="title" -->

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Bad indexes cannot be rescued at query time

::: cards grid2
### [d] Context lost in chunking
Splitting a document cuts each piece off from the title, entity and section it belongs to.

### [b] Parsing
PDF columns, tables, slides and code need different extraction; errors become wrong chunks.

### [c] Freshness
Documents change and get deleted; a stale index answers with old or revoked content.

### [a] Model lock-in
Vectors from different embedding models are not comparable; changing the model means re-embedding everything.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Chunks that carry their context

::: cards grid2
### [f] Chunk sizes
Usually no more than a few hundred tokens per chunk; split on structure (headings, paragraphs, functions) where possible.

### [a] Contextual chunks
An LLM reads the whole document and writes 50-100 tokens situating each chunk; the result is prepended before embedding and BM25 indexing. One-time cost: $1.02 per million document tokens with prompt caching.

### [c] Late chunking
Alternative: run a long-context embedding model over the whole document, then pool token embeddings per chunk, so each chunk vector already reflects its surroundings.

### [e] Hybrid indexes
Keep a dense vector index and a BM25 index. BEIR found BM25 a robust zero-shot baseline; exact terms such as error codes are lexical matches.
:::

When the whole knowledge base is under about 200,000 tokens (about 500 pages), Anthropic suggests skipping retrieval and putting it all in the prompt, with prompt caching.

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## The pipeline

::: diagram 660x300
nodes:
  src: {at: [10, 20, 140, 56], text: Sources, sub: docs · wikis · code, color: f, step: 1}
  ps: {at: [180, 20, 140, 56], text: Parse, sub: text · tables · layout, color: b, step: 2}
  ch: {at: [350, 20, 140, 56], text: Chunk, sub: structure-aware, color: c, step: 3}
  en: {at: [510, 20, 140, 56], text: Enrich, sub: context · metadata · ACL, color: a, step: 4}
  emb: {at: [510, 130, 140, 56], text: Embed, sub: versioned model, color: e, step: 5}
  bm: {at: [350, 130, 140, 56], text: Lexical index, sub: BM25, color: e, step: 5}
  vec: {at: [510, 235, 140, 56], text: Vector index, sub: vector · text · metadata, color: e, step: 6}
  cf: {at: [10, 130, 140, 56], text: Change feed, sub: hash · version · delete, color: d, step: 7}
edges:
  - {from: src, to: ps, step: 2}
  - {from: ps, to: ch, step: 3}
  - {from: ch, to: en, step: 4}
  - {from: en, to: emb, step: 5}
  - {from: en, to: bm, step: 5}
  - {from: emb, to: vec, step: 6}
  - {from: cf, to: ps, label: changed only, step: 7, style: dash}
steps:
  - Connectors pull documents from each source with their permissions and timestamps.
  - 'Parsing turns files into clean text, keeping tables and headings as structure.'
  - 'Chunking splits on structure into pieces of a few hundred tokens, possibly with overlap.'
  - 'Enrichment adds the document title and section, an LLM-written context sentence, metadata for filters, and the access list.'
  - The contextualised chunk is embedded with a pinned model version and also indexed lexically (BM25).
  - Vectors are stored with the chunk text and metadata so results can be filtered and shown.
  - A change feed re-processes only new or changed documents (compare content hashes) and deletes chunks of removed documents.
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Contextualising one chunk

::: diagram 660x300
nodes:
  doc: {at: [10, 20, 160, 56], text: Whole document, sub: cached in prompt, color: f, step: 1}
  ck: {at: [10, 140, 160, 56], text: One chunk, sub: ~ few hundred tokens, color: c, step: 1}
  llm: {at: [230, 80, 170, 60], text: Small LLM, sub: '"situate this chunk"', color: a, step: 2}
  ctx: {at: [460, 20, 190, 56], text: Context, sub: 50-100 tokens, color: b, step: 3}
  out: {at: [460, 140, 190, 56], text: Context + chunk, sub: embed and BM25, color: e, step: 4}
  ver: {at: [230, 230, 170, 56], text: Index record, sub: hash · model · ACL, color: d, step: 5}
edges:
  - {from: doc, to: llm, step: 2}
  - {from: ck, to: llm, step: 2}
  - {from: llm, to: ctx, step: 3}
  - {from: ctx, to: out, label: prepend, step: 4}
  - {from: out, to: ver, label: write, step: 5}
steps:
  - 'Each call sees the whole document and one of its chunks. The document part is the same for all its chunks, so prompt caching makes it cheap.'
  - 'A small, fast model is asked for a short context that situates the chunk within the document, to improve search retrieval.'
  - 'Output: e.g. "This chunk is from ACME''s Q2 2023 filing; the previous quarter''s revenue was $314M."'
  - The context is prepended to the chunk before both embedding and BM25 indexing.
  - 'Store a record with the content hash, embedding model version and access list, so updates and permission changes can be applied incrementally.'
:::



::: code
for doc in changed_documents():          # from the change feed
    for chunk in chunk(parse(doc)):
        h = sha256(chunk.text + doc.acl)
        if index.has(h): continue           # unchanged: skip LLM and embedding cost
        ctx = small_llm(doc.text, chunk.text)  # document prefix is prompt-cached
        text = ctx + "\n" + chunk.text
        index.upsert(h, embed(text, model=EMBED_V3), bm25_terms(text),
                     meta=dict(doc=doc.id, acl=doc.acl, version=doc.version))
    index.delete_missing(doc.id, keep=current_hashes)
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

::: table
| Choice | Benefit | Cost |
|---|---|---|
| Small chunks | precise matches, less noise in context | less context per chunk; more chunks to store |
| Large chunks | more self-contained | embeddings blur several topics; more tokens per result |
| Contextual chunks (LLM-written) | large drop in retrieval failures | one LLM call per chunk at indexing time |
| Late chunking | context without an LLM call | needs a long-context embedding model |
| Dense only | semantic matches, one index | misses exact identifiers and rare terms |
| Streaming updates | fresh results | more complex than nightly rebuilds |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Mixed embedding versions | similarity scores meaningless after a partial migration | version the index; rebuild fully, then swap an alias |
| Deleted documents still found | answers cite removed or revoked content | process deletes from the change feed; periodic reconciliation |
| Tables and figures garbled | numbers attributed to the wrong row | layout-aware parsing; keep tables whole |
| Answer split across chunks | neither half retrieves well | structure-aware splitting, overlap, or returning neighbouring chunks |
| Duplicates | top-k filled with copies of one page | deduplicate by content hash at ingestion |
:::

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Evaluate on your queries
MTEB found no embedding method best on every task: build a labelled set and measure recall@k for each change.

### [c] Blue/green indexes
Build a new index beside the old one, evaluate, then switch traffic by alias.

### [b] Backfill cost
Re-embedding and re-contextualising a large corpus is a planned batch job: budget tokens and time.

### [e] Ingestion lag
Monitor time from document change to searchable; it is a freshness service-level objective.
:::

<!-- slide id="s-papers" from="papers" -->
