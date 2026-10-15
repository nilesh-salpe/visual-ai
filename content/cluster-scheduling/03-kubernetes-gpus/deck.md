---
title: Kubernetes for GPU Workloads
body:
  data-deck: Kubernetes for GPU workloads
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
  kicker: Visual LLM · Cluster scheduling · 03
  h1: Kubernetes for GPU workloads
  sub: How Kubernetes exposes GPUs (device plugins, Dynamic Resource Allocation), why the default scheduler is not enough for training, and how Kueue and JobSet add
    queues, quotas, all-or-nothing admission and topology-aware placement. Kubernetes 1.35.
  problem: Kubernetes schedules one pod at a time, has no queue or fair share across teams, and knows nothing about network topology. A 128-GPU training job is 16
    pods that must all start together on nearby nodes, or it deadlocks against another half-started job.
  core: 'Expose GPUs with a <b>device plugin</b> (nvidia.com/gpu, whole GPUs in limits) or <b>DRA</b> (stable in 1.35: claims, device classes, attribute filters,
    sharing). Put <b>Kueue</b> in front of the scheduler: <b>LocalQueues</b> feed <b>ClusterQueues</b> with quotas per <b>ResourceFlavor</b>, cohorts lend unused
    quota, workloads are admitted as a unit, <b>waitForPodsReady</b> evicts and requeues jobs that do not get all pods running, and <b>topology-aware scheduling</b>
    keeps them in one block or rack. <b>JobSet</b> runs a training job as one unit.'
  hint: 'Previous: [Slurm for GPU clusters](../02-slurm/index.html) · Next: [Operating a training cluster →](../04-operating-clusters/index.html) · [All decks](../index.html)'
papers:
- k8s_gpus
- k8s_dra
- kueue_overview
- kueue_cq
- kueue_waitpods
- kueue_tas
- jobset
---

<!-- slide from="title" -->

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Kubernetes was built for services

::: cards grid3
### [d] Pod-by-pod scheduling
The default scheduler places each pod independently; nothing ensures all 16 pods of a job start.

### [b] No queueing or quotas
Pending pods are not ordered by team share or priority across namespaces.

### [c] No topology
Pods can land in different racks or blocks, far apart on the network.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## GPUs as resources, Kueue as the queue

::: cards grid2
### [f] Device plugin
The vendor plugin exposes nvidia.com/gpu; GPUs go in limits (requests default to the limit and must equal it).

### [a] DRA
Dynamic Resource Allocation, stable since 1.35: DeviceClasses, ResourceClaims and ResourceSlices; sharing between pods and expression-based (CEL) device filtering, which device plugins lack.

### [c] Kueue
Decides when a job waits, is admitted to start, or is preempted; quotas per flavor; fair sharing; StrictFIFO or BestEffortFIFO (default).

### [e] JobSet
A group of Jobs managed as one unit (e.g. leader and workers); restarts the whole set on failure, exclusive placement per topology domain, a headless service for stable hostnames.
:::

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## A training job on Kubernetes

::: diagram 660x300
nodes:
  js: {at: [10, 120, 130, 56], text: JobSet, sub: 16 worker pods, color: f, step: 1}
  lq: {at: [180, 120, 130, 56], text: LocalQueue, sub: team namespace, color: b, step: 2}
  cq: {at: [350, 120, 140, 56], text: ClusterQueue, sub: quota per flavor, color: a, step: 3}
  co: {at: [350, 10, 140, 56], text: Cohort, sub: borrow / lend quota, color: b, step: 3}
  ad: {at: [350, 230, 140, 56], text: Admission, sub: all pods or none, color: c, step: 4}
  ks: {at: [540, 230, 110, 56], text: kube-scheduler, sub: binds pods, color: e, step: 5}
  nd: {at: [540, 120, 110, 56], text: GPU nodes, sub: device plugin / DRA, color: e, step: 5}
edges:
  - {from: js, to: lq, label: submitted, step: 2}
  - {from: lq, to: cq, step: 3}
  - {from: co, to: cq, step: 3, style: dash}
  - {from: cq, to: ad, label: 'fits quota?', step: 4}
  - {from: ad, to: ks, label: unsuspend, step: 5}
  - {from: ks, to: nd, step: 5}
steps:
  - 'A team submits a JobSet: one unit containing all the worker pods of a training run. Kueue keeps it suspended.'
  - 'It enters the team''s LocalQueue, in the team''s namespace.'
  - 'The LocalQueue points to a ClusterQueue that holds quotas per ResourceFlavor (e.g. H100 nodes, reserved vs spot). Queues in a cohort can borrow each other''s unused quota.'
  - 'Kueue admits the whole workload only if the quota covers all of it, choosing a flavor (and, with topology-aware scheduling, a topology domain).'
  - Admission unsuspends the job; kube-scheduler then binds the pods to GPU nodes.
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## All-or-nothing and topology

::: diagram 660x300
nodes:
  a1: {at: [10, 20, 200, 56], text: 'Job X: 8 of 16 pods', sub: waiting for the rest, color: d, step: 1}
  a2: {at: [10, 120, 200, 56], text: 'Job Y: 8 of 16 pods', sub: waiting for the rest, color: d, step: 1}
  wp: {at: [260, 70, 180, 56], text: waitForPodsReady, sub: timeout 30 min default, color: a, step: 2}
  ev: {at: [490, 20, 160, 56], text: Evict + requeue Y, sub: backoff 60 s → 1 h, color: b, step: 3}
  x: {at: [490, 120, 160, 56], text: X gets all pods, sub: runs, color: e, step: 4}
  tas: {at: [10, 230, 640, 56], text: Topology-aware scheduling, sub: 'nodes labelled by block and rack · required = one domain · preferred = try, then go up a level', color: c, step: 5}
edges:
  - {from: a1, to: wp, step: 2}
  - {from: a2, to: wp, step: 2}
  - {from: wp, to: ev, label: not all ready, step: 3}
  - {from: ev, to: x, label: frees GPUs, step: 4}
steps:
  - 'Without gang admission, two distributed jobs can each get some pods and wait forever for the rest.'
  - Kueue's waitForPodsReady watches an admitted workload until all its pods are ready; the default timeout is 30 minutes.
  - 'If not all pods are ready in time, the workload is evicted and requeued with exponential backoff (first 60 s, up to 3,600 s).'
  - The freed resources let the other job get all its pods and run.
  - 'Topology-aware scheduling (beta, on by default since Kueue 0.14) uses node labels for block and rack; a required annotation keeps all pods in one domain, a preferred one tries and moves up a level if needed.'
:::



::: code
resources:
  limits:
    nvidia.com/gpu: 8        # whole GPUs, limits only (requests default to the limit)
# pod template annotation for Kueue topology-aware scheduling:
#   kueue.x-k8s.io/podset-required-topology: cloud.provider.com/topology-block
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

::: table
| Choice | Benefit | Cost |
|---|---|---|
| Kubernetes + Kueue | one platform for training, inference and services; cloud-native tooling | more moving parts than Slurm for pure batch |
| Device plugin | simple, widely supported | whole devices per container; no sharing or attribute filters |
| DRA | claims, sharing, CEL filters, per-workload configuration | newer; drivers must support it |
| BestEffortFIFO (default) | small jobs pass blocked big ones | big jobs can wait long |
| Borrowing in cohorts | idle quota gets used | borrowed capacity may be reclaimed by preemption |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Partial placement deadlock | jobs hold some GPUs and wait forever | Kueue admission plus waitForPodsReady |
| Scattered pods | slow all-reduce across racks | topology-aware scheduling, JobSet exclusive placement |
| One failed pod | the rest of the job hangs | JobSet failure policy recreates the whole set; resume from checkpoint |
| Quota mismatch with real capacity | admitted jobs cannot schedule | keep quotas in line with nodes; waitForPodsReady as a backstop |
| Reclaimed borrowed quota | jobs preempted unexpectedly | checkpoint; run long jobs within nominal quota |
:::

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] GPU stack
Drivers, device plugin or DRA driver, and node labels (Node Feature Discovery) on every GPU node.

### [c] Flavors per hardware
One ResourceFlavor per GPU type and capacity type (reserved, spot), with quotas per team.

### [b] Priorities and preemption
WorkloadPriorityClasses and ClusterQueue preemption policies (withinClusterQueue, reclaimWithinCohort) default to Never: set them deliberately.

### [e] Same cluster, many workloads
Kubernetes shines when training shares capacity with inference and services.
:::

<!-- slide id="s-papers" from="papers" -->
