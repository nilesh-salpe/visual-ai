---
title: Deploying vLLM
body:
  data-deck: 'Deploying vLLM: one GPU to many nodes'
  data-home: ../index.html
  data-home-label: vLLM
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
- ../../shared/diagram.js
glance:
  steps:
  - 'fit one replica :: weights + KV cache :: f'
  - 'one node :: TP over NVLink :: a'
  - 'many nodes :: TP inside, PP across :: c'
  - 'replicas :: data parallel or router :: b'
  - 'operate :: Kubernetes, metrics, autoscale :: e'
  caption: Fit a replica first, then copy it for throughput.
example:
  title: 'Worked example: Llama 3.1 405B on 8-GPU H100 nodes'
  setup: '80 GB per GPU, gpu_memory_utilization 0.92 (the v0.31.0 default). KV cache per token: 126 layers × 8 KV heads × 128 dims × 2 (K and V) × 2 bytes ≈ 504 KiB
    in BF16. Activation and CUDA-graph memory are ignored here.'
  steps:
  - 'BF16 weights: 405B × 2 bytes = 810 GB. One node offers 8 × 80 × 0.92 = 589 GB: it does not fit.'
  - 'Two nodes, TP 8 × PP 2: 1,178 GB usable − 810 GB = 368 GB for KV cache, about <b>710K tokens</b> across the replica.'
  - 'FP8 weights: 405 GB fit on one node with 184 GB left, about 355K tokens of BF16 KV (about 710K with an FP8 KV cache): <b>TP 8, one node</b>.'
  - 'Throughput: run several one-node FP8 replicas behind a router rather than one two-node BF16 replica; there is no cross-node traffic on the critical path.'
  result: Quantisation can turn a two-node replica into a one-node replica, which is simpler to run and avoids pipeline traffic between nodes.
traps:
  tricks:
  - 'Read the startup log. :: vLLM prints "GPU KV cache size: N tokens" and "Maximum concurrency for L tokens per request: X×": add GPUs if these are too low.'
  - 'TP inside, PP across. :: The documented default for multi-node: tensor_parallel_size = GPUs per node, pipeline_parallel_size = nodes.'
  - 'No NVLink? Use PP. :: On PCIe-only GPUs (for example L40S) or uneven splits, the docs recommend pipeline parallelism instead of tensor parallelism.'
  traps:
  - 'Cross-node TP over TCP. :: NCCL logs "NET/Socket" instead of "NET/IB/GDRDMA": tensor parallelism across nodes will crawl.'
  - 'An open control network. :: The docs warn inter-node traffic is unencrypted and exploitable for code execution; keep VLLM_HOST_IP on a private network.'
  - 'Counting max_num_seqs once. :: With data parallelism it applies per rank, while queue limits apply to the whole server.'
papers:
- vllm_parallel
- vllm_dp_deploy
- vllm_k8s
- vllm_lws
- vllm_prodstack
- vllm_llmd
- vllm_router_blog
- megatron
- llama3
status:
  label: current
  reviewed: '2026-10-16'
  note: Checked against the vLLM v0.31.0 parallelism, data-parallel and Kubernetes deployment docs.
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">vLLM · 09</div>
    <h1>Deploying vLLM: from one GPU to many nodes</h1>
    <p class="sub">What a vLLM deployment physically looks like: one GPU, tensor parallelism inside a node, tensor × pipeline parallelism across nodes (Ray or multiprocessing), replicas behind a load balancer, data-parallel modes for MoE models, and the Kubernetes stacks (LeaderWorkerSet, production stack, llm-d) that run it.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>A model has to fit in GPU memory with room left for the KV cache, and then serve enough traffic. Some models fit on one GPU, some need a whole node, some need several nodes, and every choice changes how processes, networks and load balancing are laid out.</div>
      <div class="c"><b>Core idea</b>Size <b>one replica</b> first: one GPU if it fits; else <b>tensor parallelism</b> across the GPUs of one NVLink node (or pipeline parallelism if there is no NVLink); else <b>TP = GPUs per node, PP = number of nodes</b>, run with Ray or <code>--nnodes</code>. Then add <b>replicas</b> for throughput: <code>--data-parallel-size</code> behind one endpoint, or independent servers behind a <b>router</b>. On Kubernetes, multi-node replicas are pod groups (LeaderWorkerSet); production stacks add routing, autoscaling and KV-cache offloading.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## One model, many possible layouts

The same model can be served on one GPU, eight GPUs in one server, or sixteen GPUs in two servers, and copied many times for traffic. Each layout changes the processes you run, the network you need and how requests are balanced.
            {: .lede}

::: cards grid3
### [d] Fit
Weights plus a useful KV cache must fit in the GPUs of one replica: 405B parameters in BF16 are 810 GB before any cache.

### [b] Throughput
One replica serves a limited number of concurrent sequences; traffic beyond that needs more replicas.

### [c] Network
Inside a node GPUs talk over NVLink; across nodes over InfiniBand or Ethernet, roughly ten times slower.
:::

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why the obvious setups disappoint

::: cards grid3
### [d] Tensor parallelism over TCP
TP all-reduces in every layer; across nodes without GPUDirect RDMA, NCCL falls back to sockets and throughput collapses.

### [b] One giant replica
Spreading a model that fits on one node over two adds pipeline transfers and failure points without adding much KV capacity per request.

### [c] Round-robin load balancing
Each replica has its own KV cache; spreading a conversation's turns across replicas throws away prefix reuse (Router deck).
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Pick the layout

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? A model needs about 12 GPUs of memory. Each node has 8 H100s with NVLink, and nodes are connected by InfiniBand. What do the vLLM docs recommend for one replica?
- [ ] --tensor-parallel-size 16
- [x] --tensor-parallel-size 8 --pipeline-parallel-size 2
- [ ] --pipeline-parallel-size 16
- [ ] --data-parallel-size 2
> **B.** Set TP to the GPUs per node and PP to the number of nodes: tensor parallelism's per-layer all-reduces stay on NVLink, and only pipeline activations cross the network. TP 16 also works with a fast interconnect, and data parallelism adds replicas, not memory.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Fit a replica, then copy it

::: cards grid2
### [f] Single GPU
If weights and enough KV cache fit, run one GPU per replica: no distributed overhead at all.

### [a] Single node, many GPUs
<code>--tensor-parallel-size</code> = GPUs needed (on NVLink). Without NVLink, or when GPUs do not divide the model evenly, use <code>--pipeline-parallel-size</code> instead. Multiprocessing is the default runtime.

### [c] Multi-node
TP = GPUs per node, PP = number of nodes. Start a Ray cluster (one <code>vllm serve</code> on any node sees all GPUs), or run <code>vllm serve --nnodes 2 --node-rank i --master-addr …</code> on each node, with <code>--headless</code> on workers.

### [e] Replicas
<code>--data-parallel-size N</code> runs N engines behind one endpoint (internal load balancing); <code>--data-parallel-hybrid-lb</code> gives each node its own endpoint; or run independent servers behind an external router. MoE models use data-parallel attention with expert-parallel MoE layers.
:::

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Plan a deployment <span class="ill">interactive</span>

<div class="visual"><div class="controls"><label class="ctl">model size <input type="range" id="dpN" min="0" max="7" step="1" value="5"> <output id="dpNo"></output></label><label class="ctl">weights <input type="range" id="dpQ" min="0" max="2" step="1" value="0"> <output id="dpQo"></output></label><label class="ctl">GPU <input type="range" id="dpG" min="0" max="3" step="1" value="1"> <output id="dpGo"></output></label><label class="ctl">replicas <input type="range" id="dpR" min="1" max="8" step="1" value="2"> <output id="dpRo"></output></label></div><svg id="dpSvg" viewBox="0 0 660 250" role="img" aria-label="GPU layout across nodes, coloured by replica"></svg><pre class="cmd" id="dpCmd"></pre><p class="readout" id="dpOut"></p></div>

Planning assumptions: 8 GPUs per node, 92% of GPU memory usable (the default), and at least a quarter of it kept for KV cache. R = replica, S = pipeline stage. Real sizing also needs activation and CUDA-graph memory: confirm with the "GPU KV cache size" line in the startup log.

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## The whole fleet

::: diagram 660x300
nodes:
  cl: {at: [10, 125, 80, 50], text: Clients, sub: OpenAI API, color: f, step: 1}
  rt: {at: [120, 125, 100, 50], text: Router, sub: or load balancer, color: b, step: 2}
  r1: {at: [255, 20, 175, 60], text: Replica 1 · node A, sub: API server → engine → TP 8, color: a, step: 3}
  r2: {at: [255, 120, 175, 60], text: Replica 2 · node B, sub: API server → engine → TP 8, color: a, step: 3}
  r3: {at: [255, 220, 175, 60], text: Replica 3 · nodes C + D, sub: TP 8 × PP 2 (Ray or --nnodes), color: c, step: 4}
  mx: {at: [470, 20, 180, 60], text: Metrics, sub: /metrics → Prometheus, color: e, step: 5}
  as: {at: [470, 120, 180, 60], text: Autoscaler, sub: queue depth · KV usage, color: e, step: 5}
  st: {at: [470, 220, 180, 60], text: Model storage, sub: same path on every node, color: f, step: 6}
edges:
  - {from: cl, to: rt, step: 2}
  - {from: rt, to: r1, step: 3}
  - {from: rt, to: r2, step: 3}
  - {from: rt, to: r3, step: 4}
  - {from: r1, to: mx, step: 5, style: dash}
  - {from: mx, to: as, step: 5}
  - {from: as, to: r2, label: add / drain, step: 5, style: back}
  - {from: st, to: r3, label: weights, step: 6, style: dash}
steps:
  - Clients call one OpenAI-compatible endpoint.
  - A router or load balancer picks a replica for each request (vLLM Router deck).
  - 'A replica is one copy of the model: here an API server, an engine core and 8 GPU workers with tensor parallelism inside one NVLink node.'
  - 'A model too large for one node becomes one replica spanning two nodes: tensor parallelism inside each node, pipeline parallelism across them.'
  - Every replica exports Prometheus metrics; an autoscaler adds or drains replicas on queue depth and KV-cache usage rather than raw GPU utilisation.
  - 'Every node must see the same environment and model path: container images and pre-downloaded or shared model storage.'
:::



::: table
| Layer | Options in v0.31.0 docs | What it adds |
|---|---|---|
| Multi-node runtime | Ray cluster (`run_cluster.sh`, KubeRay) or multiprocessing (`--nnodes`, `--headless`) | one replica across nodes |
| Replicas | `--data-parallel-size` (internal LB, `--api-server-count`), `--data-parallel-hybrid-lb`, external LB | throughput behind one or many endpoints |
| Kubernetes, multi-node | LeaderWorkerSet: a leader pod and worker pods per replica | gang-placed pod groups |
| Kubernetes, fleet | vLLM production stack (Helm, router, LMCache offloading); llm-d (CNCF Sandbox: prefix-aware routing, P/D, wide EP, SLO-aware autoscaling); KServe | routing, autoscaling, KV management |
:::

::: deep Networking checklist
Cross-node tensor parallelism needs InfiniBand or RoCE with GPUDirect RDMA: run with NCCL_DEBUG=TRACE and look for "NET/IB/GDRDMA", not "NET/Socket". Containers need host IPC or a large /dev/shm and the IPC_LOCK capability. Keep VLLM_HOST_IP on a private network: the docs warn the inter-node traffic is unencrypted and could be exploited to execute code. Pre-download the model to the same path on every node or use shared storage.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why these layouts

::: cards grid2
### [a] Match traffic to links
Tensor parallelism all-reduces in every layer and needs NVLink; pipeline parallelism sends activations only at stage boundaries and tolerates the slower network.

### [c] Replicas scale linearly
Independent replicas share nothing at decode time, so throughput grows with their number; only the router has to be smart.

### [b] Smaller replicas are easier
A one-node replica fails, restarts and autoscales as one unit; a multi-node replica needs gang placement and fails if any node does.

### [e] MoE is different
Data-parallel attention with expert-parallel MoE layers keeps per-GPU KV caches independent while experts are shared; ranks must step together, so a coordinator runs dummy passes on idle ranks.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "More GPUs per replica always means more throughput."
> Past the point where the model and a healthy KV cache fit, extra tensor or pipeline parallelism adds communication; more replicas usually add more throughput.
:::

::: reveal myth
? "Multi-node vLLM needs Ray."
> Ray is the default for multi-node, but v0.31.0 also runs multi-node with multiprocessing: --nnodes, --node-rank, --master-addr and --headless.
:::

::: reveal myth
? "A Kubernetes Service is enough to load-balance vLLM."
> It works, but round-robin ignores each replica's KV cache and queue; the vLLM Router and llm-d route on cache and load (next deck).
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? You have 16 GPUs on 2 nodes with NVLink inside each node. What is the documented default layout for a model that needs all 16?
- [ ] TP 16
- [x] TP 8, PP 2
- [ ] PP 16
- [ ] DP 16
> **B.** Tensor parallelism inside each node, pipeline parallelism across nodes.
:::

::: reveal
? What does --headless do in a multi-node launch?
> It starts the engine and GPU workers on a node without an API server; the head node (or a separate node) serves HTTP.
:::

::: reveal
? How do you check that cross-node NCCL traffic is using RDMA?
> Run with NCCL_DEBUG=TRACE and look for "[send] via NET/IB/GDRDMA"; "NET/Socket" means plain TCP.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Fit one replica with TP inside a node and PP across nodes, then scale throughput with replicas behind a cache-aware router.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>A vLLM replica is one copy of the model. If it fits on one GPU, use one. If not, tensor-parallelise it across the GPUs of one NVLink node, or use pipeline parallelism without NVLink. If it needs several nodes, the documented default is TP = GPUs per node and PP = number of nodes, launched on a Ray cluster or with --nnodes and --headless. Throughput comes from more replicas: --data-parallel-size behind one endpoint (internal, hybrid or external load balancing), or independent servers behind a router. On Kubernetes, LeaderWorkerSet runs multi-node replicas as pod groups, and the production stack or llm-d add routing, autoscaling and KV offloading.</p></div>
    <div class="recap"><div><span><b>Single node:</b> TP across NVLink GPUs; PP without NVLink</span></div><div><span><b>Multi-node:</b> TP = GPUs per node, PP = nodes; Ray or --nnodes</span></div><div><span><b>Throughput:</b> replicas: data parallel or a router</span></div><div><span><b>Kubernetes:</b> LWS pod groups; production stack; llm-d</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/vllm/04_memory_planner.ipynb" target="_blank" rel="noopener">04 · Planning GPU memory: weights, KV cache and concurrency</a> <span style="color:var(--faint)">· 25 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/vllm/04_memory_planner.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../10-router/index.html">10 · vLLM Router →</a> · Previous: <a href="../08-running-and-tuning/index.html">← 08</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
