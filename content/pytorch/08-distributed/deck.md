---
title: Distributed Training in PyTorch
body:
  data-deck: Distributed training in PyTorch
  data-home: ../index.html
  data-home-label: PyTorch
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'torchrun :: one process per GPU :: f'
  - 'init_process_group :: nccl (GPU) / gloo (CPU) :: c'
  - 'DDP(model) :: replicate, all-reduce grads :: a'
  - 'or fully_shard(block) :: shard params (FSDP2) :: b'
  - 'DistributedSampler :: different data per rank :: e'
  caption: 'Concepts: Distributed decks 02–03.'
example:
  title: 'Worked example: what DDP does for you'
  setup: 'Notebook 08: two CPU processes launched with torchrun and the gloo backend; each holds half of a 16-example batch.'
  steps:
  - 'Manual version: after backward, for every parameter call dist.all_reduce(p.grad, SUM) and divide by the world size.'
  - 'Result: identical to the gradient of the full 16-example batch on one process (checked to 10⁻⁶).'
  - 'DDP version: wrap the model in DistributedDataParallel and run the same forward/backward: same gradients, with all-reduce launched in buckets during backward.'
  - PyTorch 2.14.1 DDP bucket size defaults to 25 MB (the first bucket is 1 MiB, so communication can start early).
  result: DDP is exactly "average the gradients", overlapped with the backward pass and bucketed for efficiency.
traps:
  tricks:
  - 'torchrun --nproc_per_node=8 train.py. :: Single node, 8 GPUs.'
  - 'torch.cuda.set_device(LOCAL_RANK). :: Before creating the model.'
  - 'FSDP2: shard blocks, then the root. :: for b in model.blocks: fully_shard(b); fully_shard(model).'
  traps:
  - 'Same data on every rank. :: Use DistributedSampler (and call set_epoch).'
  - 'Saving from every rank. :: Save on rank 0 (DDP) or use distributed checkpoints (FSDP).'
  - 'Mismatched collectives. :: If ranks call collectives in different orders, the job hangs.'
papers:
- ddp
- pt_torchrun
- pt_fsdp2
- fsdp
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">PyTorch for LLMs · 08</div>
    <h1>Distributed training in PyTorch</h1>
    <p class="sub">The PyTorch APIs behind data parallelism: torchrun, process groups and collectives, DistributedDataParallel and FSDP2's fully_shard, with their key settings.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>You know the theory of data and sharded parallelism (Distributed topic). Now the code: how processes start, find each other, average gradients and shard a model, with as few changes as possible.</div>
      <div class="c"><b>Core idea</b><b>torchrun</b> starts one process per GPU and sets <code>RANK</code>, <code>LOCAL_RANK</code>, <code>WORLD_SIZE</code>; <code>init_process_group("nccl")</code> connects them. <b>DDP</b> wraps the model and all-reduces gradients in buckets during backward. <b>FSDP2</b> calls <code>fully_shard</code> on each block and then the root, sharding parameters as DTensors.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Ranks, local ranks and world size

Choose nodes and GPUs per node. Click a GPU to see the environment torchrun gives its process.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">nodes <input type="range" id="rN" min="1" max="4" step="1" value="2"> <output id="rNo"></output></label><label class="ctl">GPUs per node <input type="range" id="rG" min="1" max="8" step="1" value="4"> <output id="rGo"></output></label></div>
  <svg id="rSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Ranks"></svg>
  <p class="readout" id="rOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## What multi-process training needs

::: cards grid3
### [d] Discovery
Processes on many machines must find each other and agree on ranks.

### [b] Identical replicas
Every rank must start from the same weights and stay in sync.

### [c] Different data
Each rank needs its own shard of each batch.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What does LOCAL_RANK index?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? On a 2-node × 8-GPU job, what is LOCAL_RANK for global rank 11?
- [ ] 11
- [x] 3
- [ ] 1
- [ ] 8
> <b>3</b>: rank 11 is the fourth GPU (index 3) on node 1. LOCAL_RANK picks the GPU within a node; RANK is global.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Launch, connect, wrap

::: cards grid3
### [f] torchrun
Spawns processes, sets RANK, LOCAL_RANK, WORLD_SIZE, MASTER_ADDR, MASTER_PORT; can restart on failure.

### [c] Process group
init_process_group("nccl") on GPUs ("gloo" on CPU); collectives: all_reduce, all_gather, reduce_scatter, broadcast.

### [a] DDP or FSDP2
DDP(model) for replicated models; fully_shard per block for sharded ones.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## FSDP2 in a few lines

<div class="visual"><pre style="margin:0;font:13px/1.55 'JetBrains Mono',monospace;white-space:pre-wrap">from torch.distributed.fsdp import fully_shard, MixedPrecisionPolicy&#10;&#10;mp = MixedPrecisionPolicy(param_dtype=torch.bfloat16, reduce_dtype=torch.float32)&#10;for block in model.blocks:&#10;    fully_shard(block, mp_policy=mp)       # each block: all-gather before use, reduce-scatter grads&#10;fully_shard(model, mp_policy=mp)           # the root (embeddings, head)&#10;opt = torch.optim.AdamW(model.parameters(), lr=3e-4)   # optimizer sees sharded DTensor params</pre></div>

::: deep Mapping from FSDP1
The FSDP2 tutorial maps FULL_SHARD to reshard_after_forward=True (ZeRO-3-like), SHARD_GRAD_OP to reshard_after_forward=False (ZeRO-2-like), and HYBRID_SHARD to a 2-D device mesh.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why the APIs look like this

::: cards grid2
### [a] Same model code
DDP and FSDP2 wrap modules; the model itself is unchanged.

### [e] Overlap
Hooks launch communication during backward (DDP buckets, FSDP prefetch).

### [b] Per-block sharding
Wrapping each block bounds peak memory to one block's full parameters at a time.

### [c] Elastic launch
torchrun can restart failed workers and re-form the group.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "DDP sums gradients."
> It averages them across ranks, so the learning rate means the same as on one GPU with the global batch.
:::

::: reveal myth
? "FSDP needs a different model definition."
> fully_shard wraps existing modules; parameters become sharded DTensors.
:::

::: reveal myth
? "Each process sees all GPUs and picks one."
> Each process should set its device from LOCAL_RANK; otherwise all processes default to GPU 0.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Which backend for multi-GPU NVIDIA training?
- [ ] gloo
- [x] nccl
- [ ] mpi only
- [ ] tcp
> <b>nccl</b>.
:::

::: reveal
? What environment variables does torchrun set for each process?
> RANK, LOCAL_RANK, WORLD_SIZE, MASTER_ADDR, MASTER_PORT (and others).
:::

::: reveal
? How do you apply FSDP2 to a transformer?
> Call fully_shard on each transformer block, then on the root model; create the optimizer afterwards.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">torchrun starts one process per GPU, init_process_group connects them, and DDP (bucketed gradient all-reduce) or FSDP2 (fully_shard per block) turns the same model code into distributed training.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Distributed PyTorch starts with torchrun, which launches one process per GPU and sets each one's global rank, local rank and world size. Each process calls init process group with the nccl backend on GPUs or gloo on CPUs, sets its device from the local rank and reads its own shard of the data. Wrapping the model in DistributedDataParallel averages gradients across ranks with bucketed all-reduces during the backward pass; notebook eight shows this equals the full-batch gradient. For models that do not fit, FSDP2's fully shard is applied to each block and then the root, sharding parameters and gradients.</p></div>
    <div class="recap"><div><span><b>Problem:</b> launch, connect and sync many processes.</span></div><div><span><b>Core idea:</b> torchrun → process group → DDP or fully_shard.</span></div><div><span><b>Defaults:</b> DDP buckets 25 MB; nccl on GPUs.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/08_ddp_torchrun.ipynb" target="_blank" rel="noopener">08 · Distributed: all_reduce and DDP with torchrun</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/08_ddp_torchrun.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../09-putting-it-together/index.html">09 · Putting it together: a tiny GPT →</a> · Previous: <a href="../07-performance/index.html">← 07</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
