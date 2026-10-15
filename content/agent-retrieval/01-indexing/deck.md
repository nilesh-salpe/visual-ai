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
papers:
- contextual_retrieval
- late_chunking
- beir
- mteb
- dpr
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Visual Agents · Retrieval · 01</div>
    <h1>Indexing pipelines for retrieval</h1>
    <p class="sub">Everything that happens before the first query: parsing, chunking, adding context and metadata, embedding, lexical indexes, and keeping the index fresh as documents change.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Retrieval quality is mostly decided at indexing time. A chunk that says "revenue grew 3% over the previous quarter" without naming the company cannot be found by a query that names it; garbled tables, stale documents and missing permissions break even the best retriever.</div>
      <div class="c"><b>Core idea</b>Run an <b>indexing pipeline</b>: parse → chunk → <b>enrich</b> (context, metadata, access lists) → embed and build a <b>lexical (BM25) index</b> → write, with <b>incremental updates</b> keyed by content hash. Anthropic's <b>Contextual Retrieval</b> prepends 50-100 tokens of chunk-specific context, cutting top-20 retrieval failures by 35%, by 49% with BM25, and by 67% with reranking.</div>
    </div>
    <div class="toc" data-auto></div>
    <p class="start-hint">Next: <a href="../02-vector-databases/index.html">Vector databases →</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

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

<div class="visual dgm" data-steps="[&quot;Connectors pull documents from each source with their permissions and timestamps.&quot;, &quot;Parsing turns files into clean text, keeping tables and headings as structure.&quot;, &quot;Chunking splits on structure into pieces of a few hundred tokens, possibly with overlap.&quot;, &quot;Enrichment adds the document title and section, an LLM-written context sentence, metadata for filters, and the access list.&quot;, &quot;The contextualised chunk is embedded with a pinned model version and also indexed lexically (BM25).&quot;, &quot;Vectors are stored with the chunk text and metadata so results can be filtered and shown.&quot;, &quot;A change feed re-processes only new or changed documents (compare content hashes) and deletes chunks of removed documents.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 300" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah7" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="152.0" y1="48.0" x2="176.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah7)"/></g><g data-step="3"><line x1="322.0" y1="48.0" x2="346.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah7)"/></g><g data-step="4"><line x1="492.0" y1="48.0" x2="506.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah7)"/></g><g data-step="5"><line x1="580.0" y1="78.0" x2="580.0" y2="126.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah7)"/></g><g data-step="5"><line x1="536.4" y1="78.0" x2="466.5" y2="126.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah7)"/></g><g data-step="6"><line x1="580.0" y1="188.0" x2="580.0" y2="231.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah7)"/></g><g data-step="7"><line x1="126.4" y1="128.0" x2="200.5" y2="80.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah7)"/></g><g data-step="1"><rect x="10" y="20" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="80.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Sources</text><text x="80.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">docs · wikis · code</text></g><g data-step="2"><rect x="180" y="20" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="250.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Parse</text><text x="250.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">text · tables · layout</text></g><g data-step="3"><rect x="350" y="20" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="420.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Chunk</text><text x="420.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">structure-aware</text></g><g data-step="4"><rect x="510" y="20" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="580.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Enrich</text><text x="580.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">context · metadata · ACL</text></g><g data-step="5"><rect x="510" y="130" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="580.0" y="156.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Embed</text><text x="580.0" y="172.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">versioned model</text></g><g data-step="5"><rect x="350" y="130" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="420.0" y="156.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Lexical index</text><text x="420.0" y="172.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">BM25</text></g><g data-step="6"><rect x="510" y="235" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="580.0" y="261.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Vector index</text><text x="580.0" y="277.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">vector · text · metadata</text></g><g data-step="7"><rect x="10" y="130" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="80.0" y="156.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Change feed</text><text x="80.0" y="172.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">hash · version · delete</text></g><g data-step="7"><text x="163.5" y="99.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">changed only</text></g></svg><p class="readout dgcap"></p></div>

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Contextualising one chunk

<div class="visual dgm" data-steps="[&quot;Each call sees the whole document and one of its chunks. The document part is the same for all its chunks, so prompt caching makes it cheap.&quot;, &quot;A small, fast model is asked for a short context that situates the chunk within the document, to improve search retrieval.&quot;, &quot;Output: e.g. \&quot;This chunk is from ACME&#x27;s Q2 2023 filing; the previous quarter&#x27;s revenue was $314M.\&quot;&quot;, &quot;The context is prepended to the chunk before both embedding and BM25 indexing.&quot;, &quot;Store a record with the content hash, embedding model version and access list, so updates and permission changes can be applied incrementally.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 300" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah8" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="172.0" y1="70.6" x2="226.0" y2="85.5" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah8)"/></g><g data-step="2"><line x1="172.0" y1="146.9" x2="226.0" y2="132.9" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah8)"/></g><g data-step="3"><line x1="402.0" y1="87.5" x2="456.0" y2="73.6" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah8)"/></g><g data-step="4"><line x1="555.0" y1="78.0" x2="555.0" y2="136.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah8)"/></g><g data-step="5"><line x1="475.0" y1="198.0" x2="400.3" y2="226.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah8)"/></g><g data-step="1"><rect x="10" y="20" width="160" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="90.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Whole document</text><text x="90.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">cached in prompt</text></g><g data-step="1"><rect x="10" y="140" width="160" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="90.0" y="166.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">One chunk</text><text x="90.0" y="182.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">~ few hundred tokens</text></g><g data-step="2"><rect x="230" y="80" width="170" height="60" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="315.0" y="108.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Small LLM</text><text x="315.0" y="124.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">&quot;situate this chunk&quot;</text></g><g data-step="3"><rect x="460" y="20" width="190" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="555.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Context</text><text x="555.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">50-100 tokens</text></g><g data-step="4"><rect x="460" y="140" width="190" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="555.0" y="166.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Context + chunk</text><text x="555.0" y="182.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">embed and BM25</text></g><g data-step="5"><rect x="230" y="230" width="170" height="56" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="315.0" y="256.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Index record</text><text x="315.0" y="272.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">hash · model · ACL</text></g><g data-step="4"><text x="555.0" y="102.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">prepend</text></g><g data-step="5"><text x="437.7" y="207.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">write</text></g></svg><p class="readout dgcap"></p></div>

<div class="visual"><pre style="margin:0;font:13px/1.55 'JetBrains Mono',monospace;white-space:pre-wrap">for doc in changed_documents():          # from the change feed&#10;    for chunk in chunk(parse(doc)):&#10;        h = sha256(chunk.text + doc.acl)&#10;        if index.has(h): continue           # unchanged: skip LLM and embedding cost&#10;        ctx = small_llm(doc.text, chunk.text)  # document prefix is prompt-cached&#10;        text = ctx + "\n" + chunk.text&#10;        index.upsert(h, embed(text, model=EMBED_V3), bm25_terms(text),&#10;                     meta=dict(doc=doc.id, acl=doc.acl, version=doc.version))&#10;    index.delete_missing(doc.id, keep=current_hashes)</pre></div>

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

<div class="visual scroll-x"><table class="tbl"><tr><th>Choice</th><th>Benefit</th><th>Cost</th></tr><tr><td>Small chunks</td><td>precise matches, less noise in context</td><td>less context per chunk; more chunks to store</td></tr><tr><td>Large chunks</td><td>more self-contained</td><td>embeddings blur several topics; more tokens per result</td></tr><tr><td>Contextual chunks (LLM-written)</td><td>large drop in retrieval failures</td><td>one LLM call per chunk at indexing time</td></tr><tr><td>Late chunking</td><td>context without an LLM call</td><td>needs a long-context embedding model</td></tr><tr><td>Dense only</td><td>semantic matches, one index</td><td>misses exact identifiers and rare terms</td></tr><tr><td>Streaming updates</td><td>fresh results</td><td>more complex than nightly rebuilds</td></tr></table></div>

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

<div class="visual scroll-x"><table class="tbl"><tr><th>Failure</th><th>Symptom</th><th>Mitigation</th></tr><tr><td>Mixed embedding versions</td><td>similarity scores meaningless after a partial migration</td><td>version the index; rebuild fully, then swap an alias</td></tr><tr><td>Deleted documents still found</td><td>answers cite removed or revoked content</td><td>process deletes from the change feed; periodic reconciliation</td></tr><tr><td>Tables and figures garbled</td><td>numbers attributed to the wrong row</td><td>layout-aware parsing; keep tables whole</td></tr><tr><td>Answer split across chunks</td><td>neither half retrieves well</td><td>structure-aware splitting, overlap, or returning neighbouring chunks</td></tr><tr><td>Duplicates</td><td>top-k filled with copies of one page</td><td>deduplicate by content hash at ingestion</td></tr></table></div>

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
