---
title: Planning a Pretraining Run
body:
  data-deck: Planning a pretraining run
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
  kicker: Visual AI · System design · 04
  h1: Planning a pretraining run
  sub: 'Turning a training budget into a plan: compute and time estimates, the data pipeline, the parallelism layout, checkpointing against measured failure rates,
    cluster operations and the evaluations that decide what to change.'
  problem: 'Plan the pretraining of a 70B-parameter model on 15 trillion tokens with 4,096 H100 GPUs: how long will it take, how do you lay it out, and how do you
    keep it running?'
  core: Estimate compute with <b>6 × parameters × tokens</b> and time with an assumed <b>MFU</b>; lay out <b>tensor parallelism inside nodes</b>, <b>pipeline parallelism
    across nodes</b> and <b>sharded data parallelism</b> for the rest; set the <b>checkpoint interval from the failure rate</b> (Young/Daly); automate <b>detect →
    drain → restart</b>; de-risk choices with <b>small-scale ablations</b> first.
  hint: '[Read the full design doc →](design.html) · Previous: [Autonomous coding agent](../03-coding-agent/index.html) · [All case studies](../index.html)'
papers:
- bytecheckpoint
- pt_dcp_async
- llama3
- megatron
- zero
- fsdp
- fineweb
- datadecide
- megascale
---

<!-- slide from="title" -->

<!-- slide id="s-req" chapter="Requirements" tag="1 · Requirements" tagclass="b1" -->
## What the run must deliver

::: cards grid2
### [f] Target (assumption)
A 70B dense transformer trained on 15T tokens of a curated mixture, then handed to post-training.

### [a] Resources (assumption)
4,096 H100 GPUs (512 nodes of 8) with a high-bandwidth network, a parallel file system for data and checkpoints.

### [c] Constraints
A fixed calendar budget; failures are routine at this scale; every decision about data and architecture is hard to undo mid-run.

### [e] Success
Hit the planned loss and evals on schedule, with fully reproducible data and code.
:::

<!-- slide id="s-est" chapter="Estimates" tag="2 · Estimates" tagclass="b2" -->
## Compute, time and failures <span class="ill">calculator</span>

<div class="visual"><div class="controls"><label class="ctl">parameters (B) <input type="range" id="tP" min="1" max="405" step="1" value="70"> <output id="tPo"></output></label><label class="ctl">tokens (T) <input type="range" id="tT" min="1" max="30" step="0.5" value="15"> <output id="tTo"></output></label><label class="ctl">GPUs <input type="range" id="tG" min="256" max="16384" step="256" value="4096"> <output id="tGo"></output></label><label class="ctl">MFU % <input type="range" id="tM" min="20" max="60" step="1" value="40"> <output id="tMo"></output></label><label class="ctl">checkpoint save (min) <input type="range" id="tC" min="1" max="30" step="1" value="5"> <output id="tCo"></output></label><label class="ctl">restart time (min) <input type="range" id="tR" min="1" max="60" step="1" value="15"> <output id="tRo"></output></label></div><div class="bars"><div id="tBars"></div></div><p class="readout" id="tOut"></p></div>

Sanity check from the Llama 3 report: 405B parameters on 15.6T tokens is about 3.8 × 10²⁵ FLOPs; it ran on 16,384 H100s at about 41% utilisation.

<!-- slide id="s-arch" chapter="Architecture" tag="3 · Architecture" tagclass="b3" -->
## System overview

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

<!-- slide id="s-flow" chapter="Walkthrough" tag="4 · Walkthrough" tagclass="b4" -->
## Laying out the model

::: cards grid2
### [f] Tensor parallel 8, inside a node
Splits each layer's matrices across the 8 GPUs joined by NVLink, where the frequent all-reduces are cheap.

### [a] Pipeline parallel, across nodes
Splits layers into stages; micro-batches keep stages busy; interleaved schedules shrink the bubble.

### [c] Sharded data parallel for the rest
FSDP / ZeRO shards parameters, gradients and optimizer state across data-parallel ranks: e.g. 4,096 / (8 × 4) = 128 replicas with 4 pipeline stages.

### [e] Context parallel for long context
For long-sequence phases split the sequence across GPUs too; Llama 3 405B moved to context parallel 16 for its long-context stage.
:::

<!-- slide id="s-deep" chapter="Deep dive" tag="5 · Deep dive" tagclass="b5" -->
## Deep dive: checkpointing against failures

::: cards grid2
### [d] Failures are the norm
Llama 3 405B pretraining: 466 interruptions in 54 days, 419 unexpected; only 3 needed significant manual intervention because recovery was automated.

### [b] Interval from the failure rate
Young/Daly: τ* ≈ √(2 δ M) for save time δ and mean time between failures M. At the Llama 3 rate a 4,096-GPU job fails about every 12 hours: with 5-minute saves, checkpoint roughly every 86 minutes.

### [c] Make saves cheap
Asynchronous, sharded checkpoints written in the background shrink δ, which shortens the interval and the work lost.

### [e] Resume exactly
Checkpoint the optimizer state, RNG state and data-loader position too, so a resumed run is the same run.
:::

<!-- slide id="s-deep2" chapter="Recovery" tag="5 · Deep dive: recovery" tagclass="b5" -->
## Deep dive: recovering fast when something breaks

At Llama 3 scale (16,384 GPUs) Meta saw 419 unexpected interruptions in 54 days, about one every 3 hours. Goodput depends less on how rarely jobs fail than on how fast they come back.
{: .lede}

::: table
| Stage | What it costs | How to shrink it |
|---|---|---|
| Detect | minutes if you wait for a collective-communication timeout | heartbeats, per-rank progress counters, GPU health checks; MegaScale-style diagnosis to find the bad node |
| Decide | operator time | automation: cordon the node, pick a hot spare, restart without a human |
| Reload state | a full read of the checkpoint from storage | keep the latest checkpoint in host or peer memory; load only each rank's shard |
| Recompute | everything since the last checkpoint | checkpoint more often; asynchronous saves make that cheap |
:::

::: cards grid2
### [a] Asynchronous checkpoints
PyTorch Distributed Checkpoint `async_save` copies state into CPU buffers, then writes in the background while training continues; the price is CPU memory of about checkpoint size per rank × ranks per host.

### [c] Checkpoint systems at scale
ByteCheckpoint reports an average 54.20× reduction in checkpoint stalls compared with open-source baselines, and reshards checkpoints when the parallelism layout changes.

### [b] Hot spares
Keep a few healthy nodes reserved; on failure, swap one in rather than waiting for a repair or shrinking the job.

### [e] Measure goodput
Track effective training time ÷ wall-clock time, broken down into detection, restart, reload and lost work, so you know which stage to attack.
:::

<!-- slide id="s-scale" chapter="Scaling" tag="6 · Scaling" tagclass="b6" -->
## What breaks at larger scale

::: table
| Bottleneck | Symptom | Response |
|---|---|---|
| Failure rate | more interruptions as GPUs grow | automated detect → drain → requeue, hot spares, faster checkpoints |
| Stragglers | one slow GPU slows every synchronous step | per-rank step-time monitoring, drain slow nodes |
| Network | collectives dominate step time | topology-aware placement, overlap communication with compute |
| Storage | checkpoint writes stall training | asynchronous sharded writes, staged to local NVMe first |
| Loss spikes | divergence late in the run | monitor gradient norms; roll back and skip data; stability measures from the start |
:::

<!-- slide id="s-fail" chapter="Failures" tag="7 · Failures and operations" tagclass="b7" -->
## Failures and operations

::: cards grid2
### [d] Automated recovery
Health checks and job watchdogs detect failures; the scheduler drains bad nodes, requeues the job and resumes from the latest checkpoint on spares.

### [b] Silent data corruption
Bad numerics without a crash: compare loss and gradient statistics across ranks, test suspect GPUs (GPU failures deck).

### [c] Data problems
A bad shard or mixture bug shows up as loss anomalies: versioned shards make rollback precise.

### [a] Observe
Tokens per second, MFU, step time per rank, loss and gradient norm, interruptions by cause, time lost per interruption.
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="8 · Trade-offs" tagclass="b8" -->
## Trade-offs and alternatives

::: table
| Decision | Chosen | Alternative | Why |
|---|---|---|---|
| Data decisions | ablate at small scale first | decide at full scale | DataDecide: 150M-parameter rankings predicted ~80% of 1B comparisons, far cheaper |
| Parallelism | TP 8 + PP + FSDP | FSDP only | a 70B model with long sequences needs model parallelism to fit and to scale |
| Checkpoints | asynchronous, sharded, every ~1.5 h | synchronous, rare | cheaper saves allow more frequent ones and lose less work |
| Scheduling | dedicated reservation with spares | shared queue | restarts must not wait behind other jobs |
| Precision | BF16 with selective FP8 | FP8 everywhere | FP8 speeds GEMMs but adds stability risk; validate at small scale |
:::

<!-- slide id="s-sum" chapter="Summary" tag="9 · Summary" tagclass="b9" -->
## Summary

::: cards grid2
### [a] Estimate first
6 × N × D FLOPs and an honest MFU give the calendar; add failure overhead explicitly.

### [c] Layout follows the network
Tensor parallel inside NVLink domains, pipeline across nodes, sharded data parallel for the rest.

### [d] Plan for failure
Checkpoint interval from the failure rate; automate detect, drain, restart.

### [e] Read more
Full design document: [design.html](design.html). Related decks: [4D parallelism](../../distributed/10-putting-it-together/index.html), [GPU failures](../../gpu/06-gpu-failures/index.html), [Operating a training cluster](../../cluster-scheduling/04-operating-clusters/index.html), [Experiments in LLM training](../../evals/08-training-experiments/index.html).
:::

<!-- slide id="s-papers" from="papers" -->
