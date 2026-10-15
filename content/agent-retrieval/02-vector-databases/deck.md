---
title: Vector Databases
body:
  data-deck: Vector databases
  data-home: ../index.html
  data-home-label: Retrieval
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
papers:
- hnsw
- pq
- diskann
- faiss
- scann
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Visual Agents · Retrieval · 02</div>
    <h1>Vector databases and ANN indexes</h1>
    <p class="sub">How similarity search over millions to billions of embeddings stays fast: inverted-file partitions, product quantization, HNSW graphs and SSD-resident graphs, plus filtering, updates and sharding.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Exact search compares the query with every stored vector. A billion 768-dimensional float32 vectors are about 3 TB and a full scan per query; even at a few million vectors, brute force is too slow for an agent that searches several times per task.</div>
      <div class="c"><b>Core idea</b><b>Approximate nearest neighbour</b> (ANN) indexes trade a little recall for orders of magnitude in speed and memory: <b>partition</b> (IVF: scan only the closest clusters), <b>compress</b> (PQ: a vector becomes m one-byte codes), or <b>navigate a graph</b> (HNSW: greedy search down a layered small-world graph; DiskANN: a graph on SSD). A vector database wraps an index with storage, filters, updates and replication.</div>
    </div>
    <div class="toc" data-auto></div>
    <p class="start-hint">Previous: <a href="../01-indexing/index.html">Indexing pipelines</a> · Next: <a href="../03-rerankers/index.html">Rerankers →</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Brute force does not scale

::: cards grid3
### [d] Compute
Exact top-k is one dot product per stored vector per query.

### [b] Memory
float32 embeddings cost 4 × dimensions bytes each: 3 KB for 768 dimensions, 12 KB for 3,072.

### [c] Real workloads
Searches come with filters (tenant, date, access list), and data changes continuously.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Partition, compress, or navigate

::: cards grid2
### [f] IVF
Inverted file: cluster vectors with k-means into nlist lists; at query time scan only the nprobe closest lists.

### [a] PQ
Product quantization (Jégou et al. 2011): split a vector into m sub-vectors, replace each by the id of its nearest of 256 centroids; distances come from per-query lookup tables.

### [c] HNSW
Hierarchical navigable small world graph (Malkov and Yashunin): sparse upper layers with long links, dense layer 0; greedy search from the top gives logarithmic scaling.

### [e] DiskANN
A graph on SSD with compressed vectors in RAM: a billion points on one workstation with 64 GB RAM, over 5,000 queries/s, under 3 ms mean latency, 95%+ 1-recall@1.
:::

<div class="visual"><div class="controls" style="margin-top:0"><label class="ctl">vectors (log) <input type="range" id="vN" min="60" max="90" step="1" value="70"> <output id="vNo"></output></label><label class="ctl">dimensions <input type="range" id="vD" min="128" max="3072" step="128" value="768"> <output id="vDo"></output></label><label class="ctl">HNSW M <input type="range" id="vM" min="8" max="64" step="4" value="16"> <output id="vMo"></output></label><label class="ctl">PQ bytes <input type="range" id="vQ" min="8" max="128" step="8" value="64"> <output id="vQo"></output></label></div><div id="vBars" style="margin-top:12px"></div><p class="readout" id="vOut"></p></div>

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## Inside a vector database

<div class="visual dgm" data-steps="[&quot;Writes are appended to a durable log first, so they survive crashes.&quot;, &quot;New data lands in a small growing segment (searched by brute force); full segments are sealed and an ANN index is built for them in the background.&quot;, &quot;A query carries a vector, metadata filters and k; a router fans it out to every shard (or to the one partition a tenant lives in).&quot;, &quot;Each shard searches its indexed segments and its growing segment, applying the filter.&quot;, &quot;The router merges the per-shard top-k; some systems re-score candidates with full-precision vectors.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 280" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah9" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="1"><line x1="152.0" y1="48.0" x2="176.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah9)"/></g><g data-step="2"><line x1="322.0" y1="48.0" x2="346.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah9)"/></g><g data-step="2"><line x1="492.0" y1="48.0" x2="506.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah9)"/></g><g data-step="4"><line x1="553.3" y1="78.0" x2="448.4" y2="196.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah9)"/></g><g data-step="3"><line x1="152.0" y1="228.0" x2="176.0" y2="228.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah9)"/></g><g data-step="4"><line x1="322.0" y1="228.0" x2="346.0" y2="228.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah9)"/></g><g data-step="5"><line x1="492.0" y1="228.0" x2="506.0" y2="228.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah9)"/></g><g data-step="1"><rect x="10" y="20" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="80.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Upserts</text><text x="80.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">vector · metadata</text></g><g data-step="1"><rect x="180" y="20" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="250.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Write log</text><text x="250.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">durable first</text></g><g data-step="2"><rect x="350" y="20" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="420.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Segments</text><text x="420.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">growing → sealed</text></g><g data-step="2"><rect x="510" y="20" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="580.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Index builder</text><text x="580.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">HNSW · IVF-PQ</text></g><g data-step="3"><rect x="10" y="200" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="80.0" y="226.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Query</text><text x="80.0" y="242.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">vector + filter + k</text></g><g data-step="3"><rect x="180" y="200" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="250.0" y="226.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Query router</text><text x="250.0" y="242.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">fan out</text></g><g data-step="4"><rect x="350" y="200" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="420.0" y="226.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Shards</text><text x="420.0" y="242.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">ANN + filter</text></g><g data-step="5"><rect x="510" y="200" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="580.0" y="226.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Merge top-k</text><text x="580.0" y="242.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">optional re-score</text></g><g data-step="2"><text x="499.0" y="43.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">seal</text></g><g data-step="4"><text x="500.9" y="132.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">load index</text></g></svg><p class="readout dgcap"></p></div>

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## HNSW search

<div class="visual dgm" data-steps="[&quot;Each vector&#x27;s top layer is drawn at random with exponentially decaying probability (the paper uses mL = 1/ln M), so upper layers are sparse. Search starts at the entry point on the top layer and moves greedily to the neighbour closest to the query.&quot;, &quot;When no neighbour is closer, drop one layer and continue from the same node: like a skip list.&quot;, &quot;Layer 0 contains every vector; a best-first search keeps ef candidates and returns the closest k.&quot;, &quot;Build parameters: M links per node (2M allowed on layer 0, the paper&#x27;s recommendation) and efConstruction for the candidate list when inserting. Larger means better recall, more memory and slower builds.&quot;, &quot;efSearch trades latency for recall per query; it is the main tuning knob in production.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 280" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah10" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="175.0" y1="72.0" x2="175.0" y2="111.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah10)"/></g><g data-step="3"><line x1="175.0" y1="167.0" x2="175.0" y2="206.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah10)"/></g><g data-step="1"><rect x="10" y="20" width="330" height="50" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="175.0" y="43.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Layer 2</text><text x="175.0" y="59.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">few nodes · long links · entry point</text></g><g data-step="2"><rect x="10" y="115" width="330" height="50" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="175.0" y="138.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Layer 1</text><text x="175.0" y="154.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">more nodes</text></g><g data-step="3"><rect x="10" y="210" width="330" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="175.0" y="236.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Layer 0</text><text x="175.0" y="252.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">every vector · up to 2M links</text></g><g data-step="4"><rect x="400" y="20" width="250" height="50" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="525.0" y="43.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">M</text><text x="525.0" y="59.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">links per node per layer</text></g><g data-step="4"><rect x="400" y="115" width="250" height="50" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="525.0" y="138.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">efConstruction</text><text x="525.0" y="154.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">candidate list when building</text></g><g data-step="5"><rect x="400" y="210" width="250" height="56" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="525.0" y="236.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">efSearch (ef ≥ k)</text><text x="525.0" y="252.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">candidate list when querying</text></g><g data-step="2"><text x="175.0" y="86.5" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">greedy: go to closest</text></g><g data-step="3"><text x="175.0" y="181.5" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">descend</text></g></svg><p class="readout dgcap"></p></div>

<div class="visual scroll-x"><table class="tbl"><tr><th>IVF-PQ knob</th><th>Meaning</th><th>Raise it to</th></tr><tr><td>nlist</td><td>number of k-means clusters</td><td>scan fewer vectors per list (needs more training data)</td></tr><tr><td>nprobe</td><td>clusters scanned per query</td><td>raise recall, at higher latency</td></tr><tr><td>m</td><td>sub-vectors (bytes per vector at 8 bits)</td><td>raise accuracy, at more memory</td></tr><tr><td>re-rank depth</td><td>candidates re-scored with full vectors</td><td>recover precision lost to compression</td></tr></table></div>

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

<div class="visual scroll-x"><table class="tbl"><tr><th>Index</th><th>Strength</th><th>Weakness</th></tr><tr><td>Flat (exact)</td><td>perfect recall, no training</td><td>linear time; fine up to small collections</td></tr><tr><td>IVF-Flat</td><td>simple, fast with good nprobe</td><td>full vectors in memory; clusters drift as data changes</td></tr><tr><td>IVF-PQ</td><td>tens of times less memory</td><td>approximate distances; needs re-ranking for precision</td></tr><tr><td>HNSW</td><td>high recall at low latency, incremental inserts</td><td>graph memory on top of full vectors; deletes degrade it</td></tr><tr><td>DiskANN (SSD graph)</td><td>billion scale on one node</td><td>SSD reads per query; more complex updates</td></tr><tr><td>ScaNN (anisotropic quantization)</td><td>strong inner-product search</td><td>tuned for maximum inner product rather than general metrics</td></tr></table></div>

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

<div class="visual scroll-x"><table class="tbl"><tr><th>Failure</th><th>Symptom</th><th>Mitigation</th></tr><tr><td>Recall silently drops</td><td>no error, just worse answers</td><td>measure recall@k against exact search on a sample regularly</td></tr><tr><td>Selective filters</td><td>fewer than k results, or slow scans</td><td>filter-aware indexes; partition by tenant; fall back to exact search on small filtered sets</td></tr><tr><td>Deletes and updates</td><td>tombstones pile up; graph quality decays</td><td>compaction and periodic rebuilds</td></tr><tr><td>Metric mismatch</td><td>cosine model indexed with L2 on unnormalised vectors</td><td>normalise vectors or use the metric the model was trained for</td></tr><tr><td>Memory blow-up</td><td>HNSW over RAM, swapping</td><td>capacity planning (above); PQ or DiskANN for large sets</td></tr></table></div>

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Tune on a curve
Plot recall@k against p95 latency for several efSearch or nprobe values; pick the knee.

### [c] Hybrid search
Combine with BM25 for exact terms; many databases fuse both in one query.

### [b] Multi-tenancy
A partition or namespace per tenant keeps filters cheap and data separated.

### [e] Library vs database
Faiss is a library of indexes; a database adds durability, replication, filtering and access control around one.
:::

<!-- slide id="s-papers" from="papers" -->
