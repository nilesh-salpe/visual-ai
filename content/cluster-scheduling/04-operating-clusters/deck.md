---
title: Operating a Training Cluster
body:
  data-deck: Operating a training cluster
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
  kicker: Visual LLM · Cluster scheduling · 04
  h1: Operating a training cluster
  sub: 'Keeping thousands of GPUs productive: health checks and draining, automatic requeue and restart from checkpoint, preemption with grace periods, and how labs
    choose between Slurm and Kubernetes.'
  problem: At thousands of GPUs, hardware failures arrive every few hours (see the GPU failures deck). Without automation each failure means a person finds the bad
    node, removes it, and restarts the job by hand while the rest of the cluster sits idle.
  core: 'Close the loop automatically: <b>detect</b> bad nodes (health checks, failed jobs), <b>drain</b> them so no new work lands there, <b>requeue</b> the affected
    job, <b>restart</b> it from the latest <b>checkpoint</b> on healthy nodes, and <b>repair</b> or reboot the node before returning it. Preemption uses the same
    path with a <b>grace period</b> to checkpoint. Choose the scheduler by workload mix: Slurm for large batch training, Kubernetes with Kueue when training shares
    a platform with services.'
  hint: 'Previous: [Kubernetes for GPU workloads](../03-kubernetes-gpus/index.html) · [All decks](../index.html)'
papers:
- slurm_conf
- slurm_preempt
- kueue_waitpods
- jobset
- llama3
---

<!-- slide from="title" -->

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Failures are routine at scale

::: cards grid3
### [d] Frequent interruptions
Llama 3 405B pretraining saw 466 job interruptions in 54 days, 419 unexpected (GPU failures deck).

### [b] One node stops everything
A synchronous job runs at the speed of its slowest or broken rank.

### [c] Manual recovery is slow
Finding, draining and restarting by hand turns minutes of failure into hours of idle GPUs.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Detect, drain, requeue, restart

::: cards grid2
### [f] Detect
Periodic health checks (Slurm HealthCheckProgram every HealthCheckInterval seconds), job-level watchdogs, and GPU error counters.

### [a] Drain
DRAIN prevents additional jobs from running on a node while running work finishes; Slurm also drains nodes that report fewer GPUs than configured.

### [c] Requeue and restart
Slurm requeues batch jobs when JobRequeue=1 (the default) or --requeue; JobSet recreates the whole set; the job resumes from its latest checkpoint.

### [e] Grace for preemption
Slurm sends SIGTERM at once and SIGKILL after GraceTime: enough time to save a checkpoint if the job traps the signal.
:::

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## The automated recovery loop

::: diagram 660x300
nodes:
  job: {at: [10, 120, 130, 56], text: Training job, sub: '1,024 GPUs', color: a, step: 1}
  det: {at: [190, 20, 150, 56], text: Detect, sub: health check · error, color: d, step: 2}
  dr: {at: [390, 20, 130, 56], text: Drain node, sub: no new jobs, color: d, step: 3}
  rq: {at: [210, 220, 150, 56], text: Requeue job, sub: same job id, color: b, step: 4}
  ck: {at: [10, 220, 130, 56], text: Checkpoint store, sub: latest step, color: e, step: 5}
  rp: {at: [560, 20, 90, 56], text: Repair, sub: reboot · RMA, color: c, step: 6}
  pool: {at: [390, 140, 260, 56], text: Healthy nodes, sub: job restarts here, color: e, step: 5}
edges:
  - {from: job, to: det, label: fails, step: 2}
  - {from: det, to: dr, step: 3}
  - {from: det, to: rq, step: 4}
  - {from: rq, to: pool, label: reschedule, step: 5}
  - {from: ck, to: rq, label: resume, step: 5, style: dash}
  - {from: dr, to: rp, step: 6}
  - {from: rp, to: pool, label: return, step: 6, style: dash}
steps:
  - A large job is running when a GPU or node fails.
  - A health check or the job's own watchdog detects the failure.
  - The node is drained so the scheduler sends no new work to it.
  - The job is requeued automatically (it keeps its id and priority).
  - It restarts on healthy nodes and resumes from the latest checkpoint; the work since that checkpoint is lost.
  - 'The bad node is rebooted or repaired, re-checked, and returned to the pool.'
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Preemption without losing work

::: diagram 660x300
nodes:
  hp: {at: [10, 20, 160, 56], text: Urgent job, sub: higher QOS, color: a, step: 1}
  sel: {at: [210, 20, 160, 56], text: Select victims, sub: lowest priority first, color: b, step: 2}
  sig: {at: [410, 20, 240, 56], text: SIGTERM now, sub: end time = now + GraceTime, color: d, step: 3}
  sv: {at: [410, 140, 240, 56], text: Victim saves checkpoint, sub: signal handler, color: e, step: 4}
  kill: {at: [410, 245, 240, 50], text: SIGKILL at grace end, color: d, step: 5}
  rq: {at: [10, 140, 200, 56], text: Victim requeued, sub: needs --requeue, color: c, step: 6}
edges:
  - {from: hp, to: sel, step: 2}
  - {from: sel, to: sig, step: 3}
  - {from: sig, to: sv, step: 4}
  - {from: sv, to: kill, step: 5, style: dash}
  - {from: sv, to: rq, step: 6}
steps:
  - A higher-priority job (by QOS or partition tier) needs GPUs that are busy.
  - The scheduler picks preemptable lower-priority jobs to free enough GPUs.
  - Each victim gets SIGCONT and SIGTERM immediately; its end time becomes now plus GraceTime (default 0).
  - A job that traps SIGTERM writes a checkpoint within the grace period.
  - At the end of the grace period it receives SIGKILL.
  - With PreemptMode=REQUEUE and --requeue (or JobRequeue=1) the victim goes back to the queue and later resumes from that checkpoint; otherwise it is cancelled.
:::



::: code
import signal, sys

def on_sigterm(signum, frame):        # preemption or shutdown: grace period has started
    save_checkpoint(step)              # must finish before GraceTime runs out
    sys.exit(0)                        # the scheduler requeues the job (--requeue)

signal.signal(signal.SIGTERM, on_sigterm)
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Slurm or Kubernetes?

::: table
| Question | Slurm | Kubernetes + Kueue |
|---|---|---|
| All-at-once allocation | built in (a job gets all its nodes together) | Kueue admission + waitForPodsReady |
| Backfill | built-in plugin with time limits | BestEffortFIFO lets fitting jobs pass; no reservation-based backfill like Slurm's |
| Topology | tree, block, ring, torus3d plugins | Kueue topology-aware scheduling (beta), JobSet exclusive placement |
| Services and inference | not its strength | native (deployments, autoscaling) |
| Containers | supported (OCI containers, plugins) | native |
| Typical fit | large batch pretraining on fixed clusters | mixed training + inference platforms, cloud elasticity |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Flapping node | jobs keep landing on a node that fails again | drain on first failure; burn-in tests before returning it |
| Checkpoints too rare | each failure loses hours | pick the interval from MTBF and save cost (Young/Daly, GPU failures deck) |
| Signal not handled | preemption kills the job without saving | trap SIGTERM; set GraceTime long enough to checkpoint |
| Silent data corruption | loss spikes with no crash | numerical checks; isolate and test suspect GPUs |
| Restart storms | many jobs restart at once and overload storage | stagger restarts; scale checkpoint storage |
:::

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Goodput
Measure the share of GPU time spent on useful training steps, not just allocated GPUs.

### [c] Spare capacity
Keep hot-spare nodes so restarts do not wait for repairs.

### [b] Burn-in
Stress-test new and repaired nodes before they join the pool.

### [e] Automate the loop
Detection, drain, requeue and repair should not need a human for routine failures.
:::

<!-- slide id="s-papers" from="papers" -->
