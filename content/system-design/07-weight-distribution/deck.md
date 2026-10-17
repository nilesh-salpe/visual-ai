---
title: Distributing model weights
body:
  data-deck: Distributing model weights
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
  kicker: Visual AI · System design · 07
  h1: Distributing model weights to a large GPU fleet
  sub: 'Getting a 1 TB checkpoint onto 1,000+ GPUs quickly: why reading from the object store is slow, chain vs tree vs peer-to-peer swarm, shard-aware fetching,
    integrity and versioning, and the last hop into GPU memory.'
  problem: A new 1 TB model version must reach 128 nodes (1,024 GPUs) for a deploy or an urgent scale-out. How do you move the bytes fast and safely?
  core: Split the checkpoint into <b>content-addressed chunks</b>; seed a few nodes from the <b>object store</b>, then let nodes exchange chunks <b>peer-to-peer</b>
    so upload capacity grows with the fleet. Fetch only the <b>shards each node serves</b>, <b>verify every hash</b>, stream into GPU memory, and switch versions
    <b>in waves</b> with instant rollback.
  hint: '[Read the detailed design document →](design.html) · Previous: [Batched inference service](../06-batched-inference/index.html) · [All case studies](../index.html)'
papers:
- kraken
- serverlessllm
- blitzscale
- vllm_runai
status:
  label: current
  reviewed: '2026-10-17'
  note: Fleet and bandwidth figures are labelled assumptions; Kraken, ServerlessLLM, BlitzScale and vLLM sources checked 2026-10-17.
---

<!-- slide from="title" -->

<!-- slide id="s-req" chapter="Requirements" tag="1 · Clarify requirements" tagclass="b1" -->
## Clarify before you design

::: cards grid2
### [f] Ask first
Does every node need the whole model or only its shards? Planned deploy or emergency scale-out? What other traffic shares the network? How often do versions change?

### [a] Functional
Publish a version; every target node ends up with verified copies of the bytes it needs; switch serving to it and back.

### [c] Non-functional (targets)
All nodes ready within about a minute; never use an unverified byte; never overload the object store or the network core.

### [e] Scale (assumptions)
1 TB checkpoint; 128 nodes × 8 GPUs; 25 GB/s per node to storage; object store egress 200 GB/s in total.
:::

<!-- slide id="s-est" chapter="Estimates" tag="2 · Estimates" tagclass="b2" -->
## How long does each method take? <span class="ill">calculator</span>

<div class="visual"><div class="controls"><label class="ctl">model size <input type="range" id="wS" min="0.1" max="4" step="0.1" value="1"> <output id="wSo"></output></label><label class="ctl">nodes <input type="range" id="wN" min="8" max="1024" step="8" value="128"> <output id="wNo"></output></label><label class="ctl">per-node bandwidth <input type="range" id="wB" min="5" max="100" step="5" value="25"> <output id="wBo"></output></label><label class="ctl">object store egress <input type="range" id="wE" min="20" max="1000" step="20" value="200"> <output id="wEo"></output></label><label class="ctl">share each node needs <input type="range" id="wF" min="10" max="100" step="5" value="100"> <output id="wFo"></output></label></div><div class="bars"><div id="wBars"></div></div><p class="readout" id="wOut"></p></div>

Chain: S ÷ B + (N − 1) × chunk ÷ B with 64 MB chunks. Tree: depth = ⌈log₂ N⌉ levels below the seed. Swarm: S ÷ B with 10% overhead (assumption).

<!-- slide id="s-api" chapter="API" tag="3 · API and data" tagclass="b3" -->
## API and data model

::: code
GET /models/{name}/versions/{v}/manifest
→ {"chunks": [{"hash": "sha256:...", "size": 67108864,
               "shard": "tp3/pp0"}, ...]}
agent.prefetch(name, v, shards=[...])
  → {have: 812/1024, verified: true}
controller.rollout(name, v, waves=[1, 10, 50, 100])
controller.rollback()
:::



::: table
| Record | Store |
|---|---|
| Manifest (chunks, hashes, shard map) | registry database |
| Chunks, immutable, key = hash | object store |
| Who holds which chunk | tracker, rebuilt from agent heartbeats |
| Per-node version state | agent, reported to the controller |
:::

<!-- slide id="s-hld" chapter="High-level design" tag="4 · High-level design" tagclass="b4" -->
## High-level design

::: diagram 660x300
nodes:
  ci: {at: [10, 20, 125, 56], text: Model registry, sub: version · manifest, color: f, step: 1}
  os: {at: [10, 125, 125, 56], text: Object store, sub: chunks by hash, color: a, step: 2}
  tr: {at: [175, 20, 120, 56], text: Tracker, sub: who has which chunk, color: b, step: 3}
  sd: {at: [175, 125, 120, 56], text: Seed nodes, sub: first copies, color: c, step: 4}
  n1: {at: [330, 60, 125, 52], text: Node agent, sub: chunks → NVMe/RAM, color: e, step: 5}
  n2: {at: [330, 140, 125, 52], text: Node agent, sub: swaps with peers, color: e, step: 5}
  gp: {at: [500, 100, 155, 60], text: GPUs on the node, sub: load only own shards, color: d, step: 6}
  sw: {at: [330, 235, 325, 50], text: Rollout controller, sub: verify · flip version · roll back, color: b, step: 7}
edges:
  - {from: ci, to: os, label: publish, step: 2}
  - {from: os, to: sd, step: 4}
  - {from: tr, to: n1, step: 5, style: dash}
  - {from: sd, to: n1, step: 5}
  - {from: sd, to: n2, step: 5}
  - {from: n1, to: n2, label: peer, step: 5, style: back}
  - {from: n1, to: gp, step: 6}
  - {from: n2, to: gp, step: 6}
  - {from: sw, to: n2, label: go / abort, step: 7, style: dash}
steps:
  - 'A new model version is registered with a manifest: the list of chunks (for example 64 MB each), their content hashes and which tensor shards they hold.'
  - 'Chunks are uploaded once to an object store, addressed by hash, so identical chunks across versions are stored and moved once.'
  - 'A tracker knows which nodes hold which chunks, so peers can find each other.'
  - A few seed nodes pull from the object store first; after that the store is no longer the bottleneck.
  - 'Agents on every node fetch missing chunks from peers in parallel (a swarm), verify each hash and write to local NVMe or RAM. Each node serves what it has, so upload capacity grows with the fleet.'
  - 'Each GPU loads only the tensor shards it will serve, streamed from local storage into GPU memory.'
  - 'A rollout controller waits for verified copies, switches serving to the new version in waves and can roll back.'
:::

<!-- slide id="s-deep1" chapter="Deep dive 1" tag="5 · Deep dive" tagclass="b5" -->
## Deep dive: store, chain, tree or swarm <span class="ill">animation</span>

<div class="visual"><div class="seg" id="dSeg"><button data-v="store" class="on">Object store</button><button data-v="chain">Chain</button><button data-v="tree">Tree</button><button data-v="swarm">Swarm</button></div><svg id="dSvg" viewBox="0 0 660 215" class="anim-lg" role="img" aria-label="Sixteen nodes filling with model data under four distribution methods"></svg></div>

Fan-out is limited by the store's shared egress. A chain is nearly optimal but stalls behind one slow node. A tree uploads to two children, halving each node's send rate. A swarm pulls chunks from many peers at once and routes around slow ones; Uber's Kraken distributes 20,000 blobs of 100 MB–1 GB in under 30 seconds this way.

<!-- slide id="s-deep2" chapter="Deep dive 2" tag="5 · Deep dive" tagclass="b5" -->
## Deep dive: shards, the last hop and integrity

::: cards grid2
### [a] Shard-aware fetching
A replica with tensor parallelism 8 × pipeline parallelism 2 spans 2 nodes: each node needs only half the layers, each GPU one-eighth of those. The manifest maps chunks to shards.

### [c] Into GPU memory
From RAM, a 62.5 GB shard crosses PCIe Gen5 (64 GB/s) in about a second; from one NVMe drive (about 7 GB/s) 500 GB takes over a minute. Stream tensors concurrently (vLLM supports the Run:ai Model Streamer, even straight from S3). ServerlessLLM reports 3.6–8.2× faster checkpoint loading.

### [b] Urgent scale-out
BlitzScale loads parameters from GPUs that already hold them over the compute network and serves layer by layer before loading finishes: up to 94% lower tail latency than ServerlessLLM.

### [e] Integrity and versions
SHA-256 per chunk, verified before use; a version is ready only when all needed chunks verify; switch by flipping a pointer in waves, so rollback is instant.
:::

<!-- slide id="s-scale" chapter="Scaling" tag="6 · Bottlenecks and scaling" tagclass="b6" -->
## Bottlenecks and scaling

::: table
| Bottleneck | Fix |
|---|---|
| Object store egress | seed a few nodes, then peer-to-peer |
| Core network links | rack-aware peer selection: prefer peers on the same switch |
| Tracker load | shard by version; agents gossip chunk availability |
| Disk write speed | write to RAM first; stripe across NVMe drives |
| Frequent new versions | chunk-level dedupe: only changed chunks move |
:::

<!-- slide id="s-ops" chapter="Failures and cost" tag="7 · Failures, monitoring, cost" tagclass="b7" -->
## Failures, monitoring and cost

::: table
| Failure | Handling |
|---|---|
| Peer dies mid-transfer | re-request the chunk elsewhere; discard partial chunks |
| Corrupt chunk | hash mismatch → discard, refetch from another peer, report the source |
| Bad model version | waves with health and quality checks; automatic rollback by pointer flip |
| Late-joining node | fetch from the whole swarm, or load from running GPUs for urgent scale-out |
:::

Watch bytes from store vs peers, the completion curve across nodes, the slowest 1%, hash failures and time to serving. Idle GPUs are the real cost: 1,024 GPUs waiting 10 minutes is about 170 GPU-hours per deploy.

<!-- slide id="s-wrap" chapter="Wrap-up" tag="8 · Wrap-up" tagclass="b9" -->
## Wrap-up

::: cards grid2
### [a] Decisions
Content-addressed chunks; seed then peer-to-peer swarm; shard-aware fetching; hash verification; versioned waves with pointer-flip rollback.

### [b] Trade-offs
A chain is fastest on paper but fragile; a tree is simple but halves send rate; a swarm is robust at the cost of a tracker and more connections.

### [c] Next steps
Measure completion curves on real deploys; add rack awareness; keep the previous version cached for instant rollback.

### [e] Risks
Transfers competing with live traffic (rate-limit them); tracker as a dependency; disk and RAM for cached versions.
:::

[Read the detailed design document →](design.html)

<!-- slide id="s-papers" from="papers" -->
