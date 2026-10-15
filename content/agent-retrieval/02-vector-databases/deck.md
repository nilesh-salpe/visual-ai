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
- ../../shared/diagram.js
intro:
  kicker: Visual Agents · Retrieval · 02
  h1: Vector databases and ANN indexes
  sub: 'How similarity search over millions to billions of embeddings stays fast: inverted-file partitions, product quantization, HNSW graphs and SSD-resident graphs,
    plus filtering, updates and sharding.'
  problem: Exact search compares the query with every stored vector. A billion 768-dimensional float32 vectors are about 3 TB and a full scan per query; even at a
    few million vectors, brute force is too slow for an agent that searches several times per task.
  core: '<b>Approximate nearest neighbour</b> (ANN) indexes trade a little recall for orders of magnitude in speed and memory: <b>partition</b> (IVF: scan only the
    closest clusters), <b>compress</b> (PQ: a vector becomes m one-byte codes), or <b>navigate a graph</b> (HNSW: greedy search down a layered small-world graph;
    DiskANN: a graph on SSD). A vector database wraps an index with storage, filters, updates and replication.'
  hint: 'Previous: [Indexing pipelines](../01-indexing/index.html) · Next: [Rerankers →](../03-rerankers/index.html) · [All decks](../index.html)'
papers:
- hnsw
- pq
- diskann
- faiss
- scann
---

<!-- slide from="title" -->

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

<div class="visual"><div class="controls"><label class="ctl">vectors (log) <input type="range" id="vN" min="60" max="90" step="1" value="70"> <output id="vNo"></output></label><label class="ctl">dimensions <input type="range" id="vD" min="128" max="3072" step="128" value="768"> <output id="vDo"></output></label><label class="ctl">HNSW M <input type="range" id="vM" min="8" max="64" step="4" value="16"> <output id="vMo"></output></label><label class="ctl">PQ bytes <input type="range" id="vQ" min="8" max="128" step="8" value="64"> <output id="vQo"></output></label></div><div class="bars"><div id="vBars"></div></div><p class="readout" id="vOut"></p></div>

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## Inside a vector database

::: diagram 660x280
nodes:
  w: {at: [10, 20, 140, 56], text: Upserts, sub: vector · metadata, color: f, step: 1}
  lg: {at: [180, 20, 140, 56], text: Write log, sub: durable first, color: b, step: 1}
  sg: {at: [350, 20, 140, 56], text: Segments, sub: growing → sealed, color: c, step: 2}
  bd: {at: [510, 20, 140, 56], text: Index builder, sub: HNSW · IVF-PQ, color: a, step: 2}
  q: {at: [10, 200, 140, 56], text: Query, sub: vector + filter + k, color: f, step: 3}
  co: {at: [180, 200, 140, 56], text: Query router, sub: fan out, color: b, step: 3}
  sh: {at: [350, 200, 140, 56], text: Shards, sub: ANN + filter, color: e, step: 4}
  mg: {at: [510, 200, 140, 56], text: Merge top-k, sub: optional re-score, color: d, step: 5}
edges:
  - {from: w, to: lg, step: 1}
  - {from: lg, to: sg, step: 2}
  - {from: sg, to: bd, label: seal, step: 2}
  - {from: bd, to: sh, label: load index, step: 4, style: dash}
  - {from: q, to: co, step: 3}
  - {from: co, to: sh, step: 4}
  - {from: sh, to: mg, step: 5}
steps:
  - 'Writes are appended to a durable log first, so they survive crashes.'
  - New data lands in a small growing segment (searched by brute force); full segments are sealed and an ANN index is built for them in the background.
  - 'A query carries a vector, metadata filters and k; a router fans it out to every shard (or to the one partition a tenant lives in).'
  - 'Each shard searches its indexed segments and its growing segment, applying the filter.'
  - The router merges the per-shard top-k; some systems re-score candidates with full-precision vectors.
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## HNSW search

::: diagram 660x280
nodes:
  l2: {at: [10, 20, 330, 50], text: Layer 2, sub: few nodes · long links · entry point, color: b, step: 1}
  l1: {at: [10, 115, 330, 50], text: Layer 1, sub: more nodes, color: c, step: 2}
  l0: {at: [10, 210, 330, 56], text: Layer 0, sub: every vector · up to 2M links, color: e, step: 3}
  pm: {at: [400, 20, 250, 50], text: M, sub: links per node per layer, color: a, step: 4}
  pc: {at: [400, 115, 250, 50], text: efConstruction, sub: candidate list when building, color: a, step: 4}
  ps: {at: [400, 210, 250, 56], text: efSearch (ef ≥ k), sub: candidate list when querying, color: d, step: 5}
edges:
  - {from: l2, to: l1, label: 'greedy: go to closest', step: 2}
  - {from: l1, to: l0, label: descend, step: 3}
steps:
  - 'Each vector''s top layer is drawn at random with exponentially decaying probability (the paper uses mL = 1/ln M), so upper layers are sparse. Search starts at the entry point on the top layer and moves greedily to the neighbour closest to the query.'
  - 'When no neighbour is closer, drop one layer and continue from the same node: like a skip list.'
  - Layer 0 contains every vector; a best-first search keeps ef candidates and returns the closest k.
  - 'Build parameters: M links per node (2M allowed on layer 0, the paper''s recommendation) and efConstruction for the candidate list when inserting. Larger means better recall, more memory and slower builds.'
  - efSearch trades latency for recall per query; it is the main tuning knob in production.
:::



::: table
| IVF-PQ knob | Meaning | Raise it to |
|---|---|---|
| nlist | number of k-means clusters | scan fewer vectors per list (needs more training data) |
| nprobe | clusters scanned per query | raise recall, at higher latency |
| m | sub-vectors (bytes per vector at 8 bits) | raise accuracy, at more memory |
| re-rank depth | candidates re-scored with full vectors | recover precision lost to compression |
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

::: table
| Index | Strength | Weakness |
|---|---|---|
| Flat (exact) | perfect recall, no training | linear time; fine up to small collections |
| IVF-Flat | simple, fast with good nprobe | full vectors in memory; clusters drift as data changes |
| IVF-PQ | tens of times less memory | approximate distances; needs re-ranking for precision |
| HNSW | high recall at low latency, incremental inserts | graph memory on top of full vectors; deletes degrade it |
| DiskANN (SSD graph) | billion scale on one node | SSD reads per query; more complex updates |
| ScaNN (anisotropic quantization) | strong inner-product search | tuned for maximum inner product rather than general metrics |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Recall silently drops | no error, just worse answers | measure recall@k against exact search on a sample regularly |
| Selective filters | fewer than k results, or slow scans | filter-aware indexes; partition by tenant; fall back to exact search on small filtered sets |
| Deletes and updates | tombstones pile up; graph quality decays | compaction and periodic rebuilds |
| Metric mismatch | cosine model indexed with L2 on unnormalised vectors | normalise vectors or use the metric the model was trained for |
| Memory blow-up | HNSW over RAM, swapping | capacity planning (above); PQ or DiskANN for large sets |
:::

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
