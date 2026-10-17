---
title: 'Distributing model weights: design document'
back: index.html
back_label: Overview deck
---

# Distributing model weights to a large GPU fleet

> **Design question.** A new 1 TB model checkpoint must reach 1,000+ GPU workers (128 nodes × 8 GPUs) quickly, for a deploy or to scale out under load. Design the distribution: fan-out from storage, a chain, a tree or peer-to-peer; integrity, failures, and the last hop into GPU memory.

Reported as an AI-lab design question (candidate reports on prep sites, comparing fan-out, pipeline and tree approaches). Numbers marked *assumption* are inputs; formulas show how the answers follow.

## 1. Goals and non-goals

**Goals:** minimise time from "version published" to "all replicas serving"; do not overload the object store or the network core; survive node failures mid-transfer; verify every byte; roll forward and back safely.

**Non-goals:** training checkpoint saves (see the pretraining-run case), cross-region replication strategy beyond one region, model format conversion.

## 2. Requirements

| Type | Requirement |
|---|---|
| Size | 1 TB checkpoint (*assumption*, e.g. ~500B parameters in 16-bit) |
| Fleet | 128 nodes × 8 GPUs (*assumption*) |
| Network | 25 GB/s per node on the storage/front-end network (*assumption*, 200 Gb/s); object store aggregate egress 200 GB/s (*assumption*) |
| Target | all nodes hold the bytes they need within about a minute; serving switches only after verification |
| Integrity | every chunk verified by hash before use |

**Clarifying questions:** does every node need the whole model, or only its shards; is this a planned deploy or an emergency scale-out; what other traffic shares the network; how often do versions change (incremental updates).

## 3. Capacity estimates

| Method | Time formula | 1 TB to 128 nodes |
|---|---|---|
| Fan-out from the object store | max(N·S ÷ E_store, S ÷ B_node) | max(128 TB ÷ 200 GB/s, 40 s) = **640 s** |
| Pipelined chain (64 MB chunks) | S ÷ B + (N − 1) · chunk ÷ B | 40 s + 127 × 2.6 ms ≈ **40 s** |
| Binary tree, store-and-forward | depth × S ÷ B | 7 × 40 s = **280 s** |
| Binary tree, pipelined | S ÷ (B ÷ 2) + depth · chunk ÷ (B ÷ 2) | ≈ **80 s** (each node uploads to two children) |
| Peer-to-peer swarm | ≈ S ÷ B × (1 + overhead) | ≈ **44 s** with 10% overhead (*assumption*) |
| Shard-aware (each node needs half) | multiply S by the fraction needed | halves every row |

**The last hop matters too.** From local RAM (page cache) a GPU loads its 62.5 GB shard (1 TB ÷ 2 nodes per replica ÷ 8 GPUs) over PCIe Gen5 at 64 GB/s in about 1 s; from a single NVMe drive at about 7 GB/s, 500 GB per node takes over a minute. Keep weights in RAM or stripe across drives, and stream directly into GPU memory.

## 4. API and data model

```
POST /models/{name}/versions          → upload manifest + chunks (content-addressed)
GET  /models/{name}/versions/{v}/manifest
     → {"chunks": [{"hash": "sha256:...", "size": 67108864, "shard": "tp3/pp0"}, ...]}
Node agent:  prefetch(name, v, shards=[...])   status → {have: 812/1024, verified: true}
Controller:  rollout(name, v, waves=[1%, 10%, 50%, 100%])   abort()   rollback()
```

| Record | Store | Notes |
|---|---|---|
| Manifest | registry database | version, chunk list with hashes, shard mapping |
| Chunks | object store, key = hash | immutable; dedupe across versions |
| Chunk locations | tracker (in memory, rebuilt from agent heartbeats) | node → chunks held |
| Node state | agent, reported to controller | per version: chunks present, verified, loaded |

## 5. High-level architecture

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

## 6. Detailed design

### 6.1 Why not just read from the object store?
Every node pulling 1 TB means 128 TB through the store's egress: at 200 GB/s that is over 10 minutes, and it competes with everything else using the store. Peer-to-peer turns each node that already has a chunk into a source, so aggregate upload capacity grows with the fleet. Uber's Kraken, a peer-to-peer Docker registry built this way, distributes 20,000 blobs of 100 MB–1 GB in under 30 seconds at peak.

### 6.2 Chain, tree or swarm
- **Chain** (node k forwards chunks to node k+1 as soon as it has them): near-optimal time S ÷ B, but one slow or failed node stalls everyone after it; needs re-linking on failure.
- **Tree**: depth log₂ N, robust to a single failure in one subtree, but each node uploads to several children, dividing its bandwidth.
- **Swarm** (BitTorrent-style): chunks flow along many paths at once, slow nodes are routed around, and failures only remove one source among many. The usual production choice; the cost is a tracker and more connections.

### 6.3 Shard-aware distribution
A replica with tensor parallelism 8 × pipeline parallelism 2 spans 2 nodes; each node serves half the layers and each GPU one-eighth of those. The manifest maps chunks to shards, so each node fetches only its shards: half the bytes, half the time.

### 6.4 Into GPU memory
Streaming loaders read tensors concurrently and copy them straight into GPU memory (vLLM supports the Run:ai Model Streamer, including directly from S3, GCS or Azure storage). ServerlessLLM reports 3.6–8.2× faster checkpoint loading with a loading-optimised format and a multi-tier (SSD, RAM, GPU) loader. For scale-out under load, BlitzScale loads parameters from GPUs that already hold them over the fast compute network and starts serving layer by layer before all parameters arrive, reporting up to 94% lower tail latency than ServerlessLLM.

### 6.5 Integrity and versioning
Content-addressed chunks (SHA-256); verify before marking a chunk present; a version is "ready" on a node only when every needed chunk is verified. Serving switches by flipping a pointer from version v to v+1, in waves; the old version stays on disk until the new one is healthy, so rollback is a pointer flip.

## 7. Scaling

| Bottleneck | Fix |
|---|---|
| Object store egress | seed a few nodes, then peer-to-peer |
| Core network links | rack-aware peer selection: prefer peers in the same rack or switch |
| Tracker load | shard by model version; agents gossip chunk availability |
| Disk write speed | write to RAM first; stripe across NVMe drives |
| Very frequent versions | chunk-level dedupe: only changed chunks move (fine-tunes, adapters) |

## 8. Reliability

| Failure | Handling |
|---|---|
| Peer dies mid-transfer | re-request the chunk from another holder; partial chunks discarded |
| Corrupt chunk | hash mismatch → discard, refetch from a different peer, report the source |
| Seed or store slow | more seeds; peers already holding chunks serve them |
| Bad model version | waves with health and quality checks; automatic rollback by pointer flip |
| Node joins late (autoscaling) | fetches from the whole swarm; BlitzScale-style loading from running GPUs for urgent scale-out |

## 9. Security

Signed manifests; only chunks matching the signed hashes are accepted; mutual TLS between agents; weights encrypted at rest for restricted models; access control on who may publish versions.

## 10. Observability

Per version: bytes moved per source (store vs peers), completion curve across nodes, slowest 1% of nodes, hash failures, time to ready and time to serving. Network: per-link utilisation to spot core congestion.

## 11. Cost

Mostly network and storage egress; peer-to-peer cuts store egress from N × S to a few × S. The bigger cost is idle GPUs while waiting: 1,024 GPUs idle for 10 minutes is 170 GPU-hours per deploy, which pays for the distribution system quickly.

## 12. Alternatives and trade-offs

| Choice | Benefit | Cost |
|---|---|---|
| Everyone reads the store | simplest | store egress bottleneck, slowest |
| Chain | best case S ÷ B | fragile to slow or failed nodes |
| Tree | log N depth, simple | uploads split bandwidth; interior failures cut subtrees |
| Swarm | fast and robust | tracker, many connections, more complex agent |
| Pre-stage on all nodes (keep last versions cached) | instant scale-up | disk and RAM cost on every node |
| Load from running GPUs (BlitzScale) | fastest scale-out | needs a compute network path and coordination with serving |

## 13. Rollout

Ship the agent with peer-to-peer off (store only) to validate integrity checks; enable peer-to-peer within racks, then across; measure completion curves on real deploys; then shard-aware fetching.

## 14. Risks and open questions

Network contention with live traffic during deploys (rate-limit transfer bandwidth); tracker as a dependency; how many old versions to keep cached for fast rollback.

## References

Uber Kraken (peer-to-peer registry: 20K 100 MB–1 GB blobs in under 30 s); Fu et al. 2024 (ServerlessLLM, 3.6–8.2× faster checkpoint loading); Zhang et al. 2025 (BlitzScale, OSDI); vLLM Run:ai Model Streamer documentation. Bandwidth figures for H100 systems from the GPU decks (PCIe Gen5 64 GB/s, NVMe about 7 GB/s). Related decks: inside a GPU server, cluster topology, deploying vLLM.
