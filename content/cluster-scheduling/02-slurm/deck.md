---
title: Slurm for GPU Clusters
body:
  data-deck: Slurm for GPU clusters
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
  kicker: Visual LLM · Cluster scheduling · 02
  h1: Slurm for GPU clusters
  sub: 'The workload manager behind most supercomputers and many AI training clusters: daemons, partitions and QOS, GPUs as GRES, multifactor priority and fair share,
    backfill, topology-aware placement and preemption. Pinned to Slurm 26.05.'
  problem: A lab needs to share thousands of GPUs between teams, start multi-node training jobs with all their GPUs at once, place them on nearby nodes, account for
    usage, and keep the cluster full.
  core: <b>slurmctld</b> holds the queue and decides; <b>slurmd</b> on every node launches work; <b>slurmdbd</b> stores accounting. Jobs (sbatch, srun) request nodes
    and GPUs (GRES); <b>partitions</b> group nodes like queues, and <b>QOS</b> sets limits and priority. The <b>multifactor</b> plugin ranks jobs, the <b>backfill</b>
    plugin fills gaps, <b>topology</b> plugins keep jobs under few switches, and <b>preemption</b> requeues or cancels lower-priority work.
  hint: 'Previous: [Scheduling a GPU cluster](../01-scheduling-basics/index.html) · Next: [Kubernetes for GPU workloads →](../03-kubernetes-gpus/index.html) · [All
    decks](../index.html)'
papers:
- slurm_overview
- slurm_gres
- slurm_priority
- slurm_fairshare
- slurm_sched
- slurm_topology
- slurm_preempt
- nvidia_schedmd
---

<!-- slide from="title" -->

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Many teams, one cluster

::: cards grid3
### [d] Allocation
Grant users exclusive or shared access to nodes for a period of time.

### [b] Launch
Start, run and monitor parallel work (one process per GPU) on the allocated nodes.

### [c] Arbitration
Queue pending work and settle contention for resources: Slurm's three stated functions.
:::

NVIDIA acquired SchedMD, Slurm's main developer, in December 2025 and said Slurm stays open-source and vendor-neutral; NVIDIA reports Slurm runs on more than half of the top 10 and top 100 TOP500 systems.

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Daemons, partitions, GRES, plugins

::: cards grid2
### [f] Daemons
slurmctld (central manager, optional backup), slurmd (one per compute node), slurmdbd (optional accounting database).

### [a] Partitions and QOS
Partitions are groups of nodes that act as job queues; QOS adds priority, limits and preemption rules.

### [c] GPUs as GRES
--gres=gpu:8 per node or --gpus per job (and --gpus-per-node / --gpus-per-task); Slurm sets CUDA_VISIBLE_DEVICES so concurrent jobs get separate GPUs.

### [e] Plugins
priority/multifactor (ranking), backfill (gap filling), topology/tree or /block (placement), preempt/qos or /partition_prio.
:::

::: code
#!/bin/bash
#SBATCH --job-name=pretrain-7b
#SBATCH --partition=train          # a group of nodes acting as a queue
#SBATCH --nodes=16                 # 16 nodes × 8 GPUs = 128 GPUs, all at once
#SBATCH --gpus-per-node=8
#SBATCH --ntasks-per-node=8        # one process per GPU
#SBATCH --time=48:00:00            # the time limit backfill relies on
#SBATCH --requeue                  # may be requeued after preemption or node failure
#SBATCH --switches=1@01:00:00      # wait up to 1 h for nodes under one leaf switch

srun python train.py --resume-from latest
:::

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## Slurm architecture

::: diagram 660x300
nodes:
  u: {at: [10, 120, 110, 56], text: User, sub: sbatch · srun, color: f, step: 1}
  ctl: {at: [170, 110, 170, 76], text: slurmctld, sub: queue · scheduling, color: a, step: 2}
  bk: {at: [170, 10, 170, 50], text: Backup slurmctld, sub: takes over on failure, color: b, step: 2}
  db: {at: [170, 235, 170, 56], text: slurmdbd, sub: accounting · usage, color: e, step: 3}
  n1: {at: [400, 40, 250, 56], text: slurmd on each node, sub: launches tasks · reports, color: c, step: 4}
  n2: {at: [400, 140, 250, 56], text: GPUs as GRES, sub: CUDA_VISIBLE_DEVICES set, color: c, step: 4}
  hc: {at: [400, 240, 250, 50], text: Health check program, sub: drains bad nodes, color: d, step: 5}
edges:
  - {from: u, to: ctl, label: submit, step: 1}
  - {from: bk, to: ctl, step: 2, style: dash}
  - {from: ctl, to: db, label: usage, step: 3}
  - {from: ctl, to: n1, label: launch, step: 4}
  - {from: n1, to: n2, step: 4}
  - {from: hc, to: n2, step: 5, style: dash}
steps:
  - Users submit batch jobs (sbatch) or launch steps (srun).
  - 'slurmctld keeps the queue, runs the priority, backfill and topology plugins, and decides where jobs run; a backup can take over.'
  - 'slurmdbd records usage per account, which feeds fair share and reporting.'
  - 'slurmd on each node starts the job''s tasks with their GPUs, which Slurm tracks as generic resources (GRES).'
  - A periodic HealthCheckProgram (disabled unless HealthCheckInterval is set) can mark failing nodes DRAIN so no new jobs land on them.
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## How Slurm picks the next job

::: diagram 660x300
nodes:
  f: {at: [10, 20, 200, 56], text: 'Factors in [0, 1]', sub: age · fairshare · size · QOS, color: f, step: 1}
  w: {at: [240, 20, 170, 56], text: Weights, sub: default 0 each, color: b, step: 1}
  p: {at: [440, 20, 210, 56], text: Priority, sub: Σ weight × factor − nice, color: a, step: 2}
  ms: {at: [440, 130, 210, 56], text: Main scheduler, sub: strict order per partition, color: c, step: 3}
  bf: {at: [440, 235, 210, 56], text: Backfill plugin, sub: 'every 30 s, 1 day ahead', color: e, step: 4}
  tp: {at: [240, 130, 150, 56], text: Topology plugin, sub: tree / block / ring, color: d, step: 5}
  fs: {at: [10, 130, 200, 56], text: Fair Tree, sub: rank-based fair share, color: b, step: 6}
edges:
  - {from: f, to: w, step: 2}
  - {from: w, to: p, step: 2}
  - {from: p, to: ms, step: 3}
  - {from: ms, to: bf, label: cannot start, step: 4}
  - {from: tp, to: ms, step: 5, style: dash}
  - {from: fs, to: f, label: fairshare, step: 6, style: dash}
steps:
  - 'Each factor (age, fair-share, job size, partition, QOS, TRES, ...) is a number from 0 to 1.'
  - 'Priority is the weighted sum minus the nice value; every weight defaults to 0, so the site''s configuration decides what counts.'
  - The main scheduler runs on events and every sched_interval (60 s) and starts jobs in strict priority order within a partition.
  - 'The backfill plugin runs every bf_interval (30 s), looks bf_window ahead (1,440 minutes), tests up to bf_max_job_test jobs (100) and starts jobs that do not delay higher-priority reservations.'
  - 'Topology plugins choose nodes: tree finds the lowest switch that fits; block allocates within fixed-size blocks to cut fragmentation; --switches limits leaf switches with a maximum wait.'
  - 'Fair share: since 19.05 the default Fair Tree ranks users by level fairshare S / U through the account tree; usage decays with PriorityDecayHalfLife (7 days).'
:::



::: table
| Preemption setting | Meaning |
|---|---|
| PreemptType=preempt/qos or preempt/partition_prio | who may preempt whom: QOS rules, or partition PriorityTier |
| PreemptMode=REQUEUE | requeue the victim if it allows requeue (--requeue or JobRequeue=1), else cancel |
| PreemptMode=CANCEL / SUSPEND | cancel; or suspend and resume later (SUSPEND needs GANG) |
| GraceTime | SIGCONT and SIGTERM at once, SIGKILL when the grace time ends (default 0) |
| GANG | trap: in Slurm, "gang scheduling" means time-slicing jobs in a partition, not all-at-once placement |
:::



::: colab build-it/cluster-scheduling/02_fair_share_priority.ipynb
Implement decayed usage, the classic fair-share factor 2^(−U/S), multifactor priority and preemption victim selection.
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

::: table
| Choice | Benefit | Cost |
|---|---|---|
| Slurm | mature HPC scheduler: gang allocation, backfill, topology, accounting | static nodes; less native fit for services and containers |
| Exclusive nodes (default for training partitions) | predictable performance | idle GPUs for small jobs |
| GPU sharding (gres/shard) | many small jobs per GPU | no isolation between processes on the GPU |
| Fair Tree vs classic fair share | fairer across account hierarchies | harder to explain to users |
| --switches with a wait | better collective bandwidth | jobs wait longer; set max_switch_wait |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Node with a bad GPU | jobs crash on the same node again and again | health checks drain it; nodes with fewer GPUs than configured are drained |
| Jobs without --requeue | preempted or failed work is cancelled, not retried | set --requeue or JobRequeue=1; checkpoint |
| Unrealistic time limits | backfill reservations wrong | enforce limits; per-partition defaults |
| slurmctld overload | slow squeue, delayed scheduling | limit bf_max_job_test and queue depth; job arrays instead of many jobs |
| Misread "GANG" | time-slicing enabled instead of all-at-once placement | Slurm allocates all of a job's nodes together by default |
:::

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Partitions per workload
Separate partitions or QOS for pretraining, research and interactive use, with preemption rules between them.

### [c] Prolog and epilog
Check GPUs and clean up before and after every job; drain nodes that fail.

### [b] Accounting
slurmdbd usage drives fair share and chargeback; review shares quarterly.

### [e] Topology config
Keep topology.conf (or topology.yaml) in sync with the real network.
:::

<!-- slide id="s-papers" from="papers" -->
