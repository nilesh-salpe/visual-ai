---
title: 'Planning a Pretraining Run: design document'
back: index.html
back_label: Overview deck
---

# Planning a pretraining run

> **Design question.** Plan the pretraining of a 70B-parameter model on 15 trillion tokens with 4,096 H100 GPUs: how long will it take, how do you lay it out, and how do you keep it running?

## 1. Goals and non-goals

**Goals:** a base model that reaches the planned loss and benchmark targets on schedule; reproducible data and code; minimal time lost to failures.

**Non-goals:** post-training (SFT, RL), serving, and choosing model size and token count from scaling laws (taken as given here).

## 2. Requirements and assumptions

| Item | Assumption |
|---|---|
| Model | 70B dense decoder-only transformer, GQA, RoPE |
| Data | 15T tokens of a curated mixture (web, code, multilingual, math, books) |
| Hardware | 4,096 H100 80 GB (512 nodes × 8), NVLink within nodes, high-bandwidth fabric across nodes |
| Throughput | 40% model FLOPs utilisation (MFU) at BF16 dense peak 989 TFLOPS |
| Checkpoint save | 5 minutes blocking time (assumption); restart 15 minutes |

## 3. Estimates

- **Compute:** 6 × 70e9 × 15e12 = **6.3 × 10²⁴ FLOPs**.
- **Throughput:** 4,096 × 989e12 × 0.40 ≈ 1.6 × 10¹⁸ FLOPs/s → **≈ 3.9 × 10⁶ s ≈ 45 days** of pure training.
- **Failure rate:** Llama 3 405B saw 419 unexpected interruptions in 54 days on 16,384 GPUs ≈ 2 × 10⁻⁵ per GPU-hour. On 4,096 GPUs that is ≈ 0.08 per hour → **mean time between failures ≈ 12 hours**.
- **Checkpoint interval (Young/Daly):** τ* ≈ √(2 δ M) = √(2 × 5 × 742) ≈ **86 minutes**.
- **Overhead:** saves (δ/τ ≈ 6%) plus lost work and restarts ((τ/2 + R)/M ≈ 8%) ≈ **14%**, so plan for about **52 days**, before evaluation pauses and data issues. Faster asynchronous checkpoints reduce both terms.

The overview deck's calculator recomputes these for other sizes.

## 4. System overview

::: diagram 660x300
nodes:
  raw: {at: [10, 20, 130, 56], text: Raw data, sub: crawl · code · books, color: f, step: 1}
  dp: {at: [180, 20, 160, 56], text: Data pipeline, sub: filter · dedup · mix, color: b, step: 2}
  tok: {at: [380, 20, 130, 56], text: Tokenised shards, sub: versioned, color: e, step: 3}
  ld: {at: [550, 20, 100, 56], text: Loader, sub: resumable, color: c, step: 4}
  job: {at: [380, 140, 270, 70], text: Training job, sub: 'TP 8 · PP · DP/FSDP on 4,096 GPUs', color: a, step: 5}
  ck: {at: [180, 140, 160, 56], text: Checkpoints, sub: async to storage, color: e, step: 6}
  sch: {at: [10, 140, 130, 56], text: Scheduler, sub: reservation · spares, color: d, step: 7}
  ev: {at: [380, 240, 270, 50], text: Evals and monitoring, sub: loss · benchmarks · spikes, color: c, step: 8}
edges:
  - {from: raw, to: dp, step: 2}
  - {from: dp, to: tok, step: 3}
  - {from: tok, to: ld, step: 4}
  - {from: ld, to: job, step: 5}
  - {from: job, to: ck, label: every τ, step: 6}
  - {from: sch, to: ck, label: restart from, step: 7, style: dash}
  - {from: job, to: ev, step: 8, style: dash}
steps:
  - 'Raw sources: web crawl, code, books and papers, licensed data.'
  - 'The data pipeline extracts text, filters quality, removes duplicates and PII, and sets the mixture.'
  - 'Tokenised shards are written once and versioned, so every run is reproducible.'
  - 'A deterministic, resumable loader streams shards in a fixed order keyed by step.'
  - 'The training job runs tensor parallelism within nodes, pipeline parallelism across nodes and sharded data parallelism across the rest.'
  - Checkpoints are written asynchronously at the interval set by the failure rate.
  - 'The cluster scheduler holds a reservation, keeps hot spares and restarts the job from the latest checkpoint after failures.'
  - 'Training loss, gradient norms and periodic low-noise evals are monitored for spikes and regressions.'
:::

## 5. Components

### 5.1 Data pipeline
Extraction from raw sources (e.g. WARC for web crawl), quality filtering (heuristics and classifiers), deduplication (exact and MinHash near-duplicate), PII and safety filtering, and a mixture of domains set by small-scale ablations. Output: versioned, tokenised shards with manifests. See the web crawling and pretraining data decks.

### 5.2 Data loader
Deterministic order keyed by global step and data-parallel rank, so a resumed run reads exactly the data it would have read; the loader position is part of every checkpoint.

### 5.3 Parallelism layout
Tensor parallelism 8 inside each node (NVLink), pipeline parallelism across nodes (e.g. 4 stages, interleaved schedule), and sharded data parallelism (FSDP/ZeRO) across the remaining 128 data-parallel groups. Context parallelism for long-context phases. For reference, Llama 3 405B used tensor 8, pipeline 16 and data 128 on 16,384 H100s, and context parallel 16 for long context.

### 5.4 Checkpointing
Sharded, asynchronous checkpoints: each rank writes its shard to local NVMe, then to the parallel file system in the background; checkpoint parameters, optimizer state, RNG states and loader position. Keep the last few and periodic milestones.

### 5.5 Cluster operations
A dedicated reservation on the scheduler (e.g. Slurm) with hot spare nodes. Health checks and a job watchdog detect failures; the scheduler drains bad nodes and requeues the job, which resumes from the latest checkpoint on spares. Llama 3 reports that of 466 interruptions only 3 needed significant manual intervention.

### 5.6 Monitoring and evaluation
Per-rank step time (stragglers), MFU, loss and gradient-norm monitoring with spike alerts; periodic evaluation with low-noise metrics (cloze formats, likelihoods) on held-out sets and benchmarks; decisions about data and recipes made with small-scale ablations before and during the run.

## 6. Reliability

| Failure | Detection | Handling |
|---|---|---|
| GPU / node failure | health checks, NCCL errors, watchdog | drain node, requeue, resume from checkpoint on spares |
| Straggler | per-rank step time | drain and replace the slow node |
| Silent data corruption | cross-rank loss/gradient checks | isolate and test suspect GPUs; roll back if corrupted |
| Loss spike | gradient norm, loss | roll back to a checkpoint before the spike; skip the offending data |
| Storage stall | checkpoint write time | asynchronous writes; local staging |

## 6b. Fault tolerance in depth

At 16,384 GPUs, Llama 3 training saw 419 unexpected interruptions in 54 days, roughly one every 3.1 hours. Lost time per failure = detection + decision + restart + reload + recomputation since the last checkpoint. Each term has its own fix:

| Stage | Typical cause of delay | Fix |
|---|---|---|
| Detection | waiting for a collective-communication timeout (often minutes) | heartbeats and per-rank step counters; GPU and NIC health checks; automated localisation of the faulty node (MegaScale built diagnosis tooling for this) |
| Decision | a human in the loop | policy: cordon the node, take a hot spare, restart automatically, page only on repeated failures |
| Restart | scheduling and process start-up, NCCL initialisation | pre-warmed spares; persistent containers; topology-aware placement of the replacement |
| Reload | reading a multi-terabyte checkpoint from shared storage | keep the latest checkpoint in host or peer memory; each rank loads only its shard |
| Recompute | work since the last checkpoint (half an interval on average) | shorter intervals, made affordable by asynchronous saves |

**Asynchronous checkpointing.** PyTorch Distributed Checkpoint `async_save` first copies model and optimiser state into CPU buffers and then writes in the background, so training resumes after the copy; it raises CPU memory by about checkpoint size per rank × ranks per host. Production systems go further: ByteCheckpoint reports an average 54.20× reduction in checkpoint stalls compared with open-source checkpointing and supports resharding when the parallelism layout changes.

**Interval.** With save cost δ and mean time between failures M, the Young/Daly interval τ* ≈ √(2 δ M) (section 3). Cutting the *blocking* part of δ with asynchronous saves shortens τ* and the recomputation term together.

**Goodput accounting.** Track the effective training time ratio (productive time ÷ wall-clock time) and attribute every lost minute to detection, restart, reload or recomputation; the largest bucket is the next thing to automate.

## 7. Risks and de-risking

- **Data mixture wrong:** run small-scale ablations with several seeds and low-noise metrics; DataDecide found 150M-parameter rankings predicted about 80% of 1B comparisons.
- **Instability at scale:** use proven stability measures from the start; test FP8 at small scale before using it.
- **Throughput below plan:** profile a short full-scale run first (communication overlap, pipeline bubble, data loading) and fix before the long run.

## 8. Alternatives considered

- **FSDP only:** simpler, but a 70B model with long sequences needs model parallelism for memory and scaling efficiency.
- **Synchronous rare checkpoints:** lower overhead per save but much more lost work per failure.
- **Shared scheduler queue:** cheaper utilisation, but restarts would wait behind other jobs.

## 9. Data and checkpoint storage

- **Checkpoint size:** 70B parameters × 16 bytes (BF16 weights and gradients are not saved; FP32 master weights and Adam moments plus BF16 weights) ≈ **1.1 TB** per full checkpoint.
- **Write bandwidth:** saving 1.1 TB in the assumed 5 minutes needs ≈ **3.7 GB/s** aggregate to storage; asynchronous saves hide most of it.
- **Retention:** keep the last few checkpoints for restarts plus periodic milestones for evaluation and ablations.
- **Data:** the 15T-token mixture stored as pre-tokenised shards with a manifest (source, version, sampling weight); the data loader records its position in every checkpoint so restarts resume the exact data order.

## 10. Observability

Training: loss, gradient norm, learning rate, tokens/s, MFU per step; loss spikes and NaNs. Fleet: per-node GPU errors (ECC, XID), NIC errors, stragglers (slowest rank per step), temperature. Goodput: productive time ÷ wall-clock time, with lost time attributed to detection, restart, reload and recomputation (section 6b).

## 11. Cost model

GPU-hours = 4,096 GPUs × 52 days × 24 h ≈ **5.1M GPU-hours**. At an assumed $2 per GPU-hour that is about **$10M**; every percentage point of goodput is worth about $100K. Add storage, networking, evaluation runs and the ablations that precede the main run.

## 12. Rollout

Staged: short runs at small scale to validate data, code and loss curves; a full-scale shakedown of a few hours to measure MFU, failure handling and checkpoint save and restore; then the main run with scheduled evaluation checkpoints.

## References

Llama Team 2024 (The Llama 3 Herd of Models: compute, parallelism, interruptions); Shoeybi et al. / Narayanan et al. (Megatron-LM tensor and pipeline parallelism); Rajbhandari et al. 2020 (ZeRO); Zhao et al. 2023 (PyTorch FSDP); Penedo et al. 2024 (FineWeb); Magnusson et al. 2025 (DataDecide); Jiang et al. 2024 (MegaScale). Related decks: distributed training, GPU failures, cluster scheduling, pretraining data, experiments in LLM training.
