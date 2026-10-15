---
title: Scheduling a GPU Cluster
body:
  data-deck: Scheduling a GPU cluster
  data-home: ../index.html
  data-home-label: Cluster scheduling
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
- ../../shared/diagram.js
intro:
  kicker: Visual LLM · Cluster scheduling · 01
  h1: Scheduling a GPU cluster
  sub: 'What a cluster scheduler decides and why GPU training makes it hard: queues and priorities, quotas, all-at-once (gang) placement, topology, backfill and preemption.'
  problem: Thousands of GPUs, many teams, and jobs from one GPU for an hour to thousands of GPUs for weeks. Starting jobs in arrival order leaves GPUs idle behind
    big jobs; starting them anywhere scatters a training job across slow links; partial starts deadlock.
  core: A scheduler orders the queue by <b>priority</b> (age, fair share, quality of service), admits jobs within <b>quotas</b>, places each job <b>all at once</b>
    on nodes that are <b>close in the network</b>, fills idle gaps with <b>backfill</b> (short jobs that cannot delay the reserved start of the job at the head),
    and <b>preempts</b> low-priority work when urgent work arrives.
  hint: 'Next: [Slurm for GPU clusters →](../02-slurm/index.html) · [All decks](../index.html)'
papers:
- slurm_sched
- slurm_priority
- kueue_overview
- kueue_waitpods
---

<!-- slide from="title" -->

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## First come, first served wastes GPUs

::: cards grid3
### [d] Head-of-line blocking
A 1,024-GPU job at the front waits for GPUs to drain while small jobs behind it could have run.

### [b] Fragmentation
Free GPUs scattered over half-used nodes cannot host a job that needs whole nodes in one network block (see the GPU sharing deck).

### [c] Partial starts
Two distributed jobs that each get half their GPUs both wait forever.
:::

The GPU decks cover hardware sharing (MIG, time-slicing) and failure rates; this topic is about the scheduler that decides who runs where and when.

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Order, admit, place, fill, preempt

::: cards grid2
### [f] Priority
A score per job: in Slurm a weighted sum of age, fair-share, job size, partition, QOS and more, each normalised to [0, 1].

### [a] Quotas and fair share
Each team gets a share; usage decays over time (Slurm's default half-life is 7 days) so heavy recent users wait longer.

### [c] Gang and topology
All of a job's GPUs start together, on nodes under as few switches as possible.

### [e] Backfill and preemption
Short jobs run in gaps if they cannot delay the reserved job; urgent work can requeue or cancel lower-priority jobs.
:::

::: colab build-it/cluster-scheduling/01_backfill_scheduler.ipynb
Build FIFO and EASY backfill schedulers and measure mean wait and utilisation. On a random 300-job workload backfill cuts mean wait from 496 to 186 hours and raises utilisation from 55% to 95%.
:::

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## What a scheduler does

::: diagram 660x300
nodes:
  sub: {at: [10, 120, 120, 56], text: Submit, sub: GPUs · time limit, color: f, step: 1}
  q: {at: [170, 120, 140, 56], text: Queue, sub: sorted by priority, color: a, step: 2}
  qt: {at: [170, 10, 140, 56], text: Quotas, sub: shares · limits, color: b, step: 3}
  pl: {at: [360, 120, 140, 56], text: Placement, sub: gang · topology, color: c, step: 4}
  bf: {at: [360, 230, 140, 56], text: Backfill, sub: fill gaps, color: e, step: 5}
  pr: {at: [540, 230, 110, 56], text: Preempt, sub: requeue / cancel, color: d, step: 6}
  cl: {at: [540, 120, 110, 56], text: Nodes, sub: run job, color: f, step: 4}
edges:
  - {from: sub, to: q, step: 2}
  - {from: qt, to: q, label: 'admit?', step: 3}
  - {from: q, to: pl, label: head job, step: 4}
  - {from: pl, to: cl, step: 4}
  - {from: q, to: bf, label: later jobs, step: 5, style: dash}
  - {from: bf, to: cl, label: if harmless, step: 5, style: dash}
  - {from: pr, to: cl, label: free GPUs, step: 6}
steps:
  - 'A job asks for resources (GPUs, nodes) and a time limit.'
  - It joins a queue ordered by priority.
  - 'Quotas decide whether the job may run at all now (its team''s share, account limits).'
  - 'The head job is placed only when all its GPUs are free together, preferably within one network block.'
  - 'Backfill starts later jobs in the gaps, if they cannot delay the head job''s reserved start; this relies on honest time limits.'
  - Preemption frees GPUs for urgent work by requeueing or cancelling lower-priority jobs.
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Backfill in one picture

::: diagram 660x270
nodes:
  a: {at: [10, 20, 270, 50], text: 'Job A: 6 GPUs × 10 h', sub: running, color: a, step: 1}
  b: {at: [370, 20, 280, 50], text: 'Job B: 8 GPUs × 5 h', sub: 'head of queue: needs all 8', color: d, step: 2}
  sh: {at: [370, 110, 280, 50], text: Reservation for B at t = 10 h, sub: shadow time, color: d, step: 3}
  c: {at: [10, 110, 270, 50], text: 'Job C: 2 GPUs × 4 h', sub: starts now in the gap, color: e, step: 4}
  dd: {at: [10, 200, 270, 50], text: 'Job D: 2 GPUs × 12 h', sub: 'would delay B: waits', color: b, step: 5}
  ex: {at: [370, 200, 280, 50], text: Extra GPUs at shadow time, sub: long jobs may use only these, color: c, step: 6}
edges:
  - {from: a, to: b, step: 2}
  - {from: b, to: sh, step: 3}
  - {from: c, to: sh, label: ends first, step: 4, style: dash}
  - {from: dd, to: ex, label: extra only, step: 6, style: dash}
steps:
  - 'An 8-GPU cluster: job A holds 6 GPUs for 10 hours.'
  - Job B is at the head of the queue and needs all 8 GPUs.
  - 'B cannot start, so the scheduler reserves its start at the time A ends: the shadow time, t = 10 h.'
  - 'Job C (2 GPUs, 4 h) fits in the 2 idle GPUs and finishes before the shadow time, so it starts now: backfill.'
  - 'Job D (2 GPUs, 12 h) would still be running at t = 10 and take GPUs B needs, so it waits (EASY backfill).'
  - A long job may start early only on GPUs that will still be spare at the shadow time (none here; 2 on a 10-GPU cluster).
:::



::: table
| Policy | Starts a later job when | Risk |
|---|---|---|
| Strict FIFO | every job ahead has started | idle GPUs behind a big job |
| EASY backfill | it cannot delay the head job's reservation | later high-priority jobs may be delayed |
| Conservative backfill | it cannot delay any queued job's reservation | less backfill, more planning cost |
| Greedy (first fit) | it fits now | large jobs starve |
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

::: table
| Choice | Benefit | Cost |
|---|---|---|
| Exclusive whole nodes | no interference; simple topology | idle GPUs when jobs need fewer than a node |
| Shared nodes / fractional GPUs | higher utilisation for small jobs | noisy neighbours; fragmentation for big jobs |
| Strict topology placement | fast collectives | longer waits for a fitting block |
| Aggressive preemption | urgent work starts fast | lost progress unless jobs checkpoint |
| Backfill with padded time limits | safe reservations | fewer gaps filled; users learn to under-request |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Starvation | a large job never starts | reservations (backfill), age factor in priority |
| Partial-allocation deadlock | two jobs each hold half their GPUs | gang admission: all or nothing |
| Bad time limits | backfill disabled in practice; reservations wrong | enforce limits; default limits per partition |
| Quota gaming | many small jobs to grab share | fair share on usage, per-user limits |
| Scattered placement | jobs run slowly across many switches | topology-aware placement with a wait limit |
:::

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Measure the queue
Track wait time by job size, utilisation, and GPU-hours lost to fragmentation and preemption.

### [c] Separate pools
Large pretraining runs often get dedicated reservations; research and inference share the rest.

### [b] Make jobs restartable
Preemption and failures are routine; checkpointing turns them into delays, not lost weeks.

### [e] Explain decisions
Show users why a job is pending (priority, resources, reservation).
:::

<!-- slide id="s-papers" from="papers" -->
