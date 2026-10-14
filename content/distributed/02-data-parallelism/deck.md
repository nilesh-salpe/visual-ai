---
title: Data Parallelism
body:
  data-deck: Data parallelism
  data-home: ../index.html
  data-home-label: Distributed
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'replicate model :: same weights everywhere :: f'
  - 'split batch :: each GPU its own examples :: c'
  - 'forward + backward :: local gradients :: a'
  - 'all-reduce gradients :: bucketed, overlapped :: b'
  - 'same update everywhere :: replicas stay identical :: e'
  loop: '4 -> 2 :: every step'
  caption: Mathematically identical to one GPU on the whole batch.
example:
  title: 'Worked example: is the all-reduce hidden?'
  setup: An 8B model (16 GB of BF16 gradients), 8 GPUs in a ring over 400 Gb/s network cards (50 GB/s), 8,192 tokens per GPU per step, H100 at 40% MFU.
  steps:
  - 'Bytes each GPU sends: 2 × (N − 1)/N × 16 GB = <b>28 GB</b>.'
  - 'Time at 50 GB/s: <b>0.56 s</b> (bandwidth only).'
  - 'Compute per step: 6 × 8B × 8,192 tokens ÷ (989 TFLOP/s × 0.4) = <b>0.99 s</b>, of which the backward pass is about two thirds (0.66 s).'
  - With bucketing, most of the all-reduce runs during the backward pass; without it, the GPUs would idle for the whole all-reduce after every step.
  result: 'Communication (0.56 s) is comparable to compute (0.99 s): overlapping it decides whether DP scales.'
traps:
  tricks:
  - 'Ring all-reduce sends ≈ 2·S per GPU. :: Independent of the number of GPUs.'
  - 'Average, not sum. :: Divide by world size (or scale the loss) so the learning rate stays valid.'
  - 'Gradient accumulation. :: Skip synchronization on all but the last micro-batch.'
  traps:
  - 'Global batch grows with GPUs. :: Adding GPUs at a fixed per-GPU batch changes the optimization; retune learning rate.'
  - 'Unbucketed all-reduce. :: Waiting until backward finishes leaves the network idle during compute and the GPUs idle during communication.'
  - 'Non-deterministic data order. :: Each rank must read a different shard; duplicated data silently halves effective data.'
papers:
- ddp
- megatron21
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Distributed Training · 02</div>
    <h1>Data parallelism</h1>
    <p class="sub">The simplest way to use many GPUs: copy the model, split the batch, average the gradients. How the all-reduce works and how PyTorch hides it behind the backward pass.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>One GPU processes the batch too slowly. Giving each GPU part of the batch is easy, but every GPU must end each step with the same, averaged gradient.</div>
      <div class="c"><b>Core idea</b>Each GPU runs forward and backward on its own micro-batch, then a <b>ring all-reduce</b> averages the gradients (each GPU sends ≈ 2× the gradient size). <b>Bucketing</b> starts all-reducing gradients as soon as they are ready, so communication overlaps the backward pass.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Copy the model, split the batch

Four GPUs each process a quarter of the batch. Their gradients differ; before the optimizer step they must be averaged so every copy stays identical. Press play to see one step.
{: .lede}

<div class="visual">
  <div class="seg" id="oSeg"><button data-v="0" class="on">no overlap</button><button data-v="1">bucketed overlap</button></div>
  <svg id="oSvg" viewBox="0 0 660 200" style="margin-top:10px" role="img" aria-label="Compute and communication timeline"></svg>
  <p class="readout" id="oOut"></p>
</div>
<p class="caption">Illustrative timeline: backward produces gradients layer by layer from the last layer; buckets of gradients can be all-reduced while earlier layers are still computing.</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## What makes naive data parallelism slow

::: cards grid3
### [d] Wait, then talk
All-reducing after the backward pass finishes leaves the network idle during compute and the GPUs idle during communication.

### [b] Many tiny messages
All-reducing every parameter tensor separately pays per-message latency thousands of times.

### [c] Full copies everywhere
Every GPU stores the full model, gradients and optimizer state; DP adds no memory headroom.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## How much does each GPU send?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Ring all-reduce over N GPUs on a gradient of S bytes. Roughly how many bytes does each GPU send?
- [ ] S / N
- [ ] S
- [x] ≈ 2·S, whatever N is
- [ ] N · S
> <b>C.</b> Reduce-scatter sends (N−1)/N·S and all-gather another (N−1)/N·S: about 2·S per GPU, nearly independent of N. That is why the bandwidth cost of DP stays flat as you add GPUs.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Average gradients with a ring, overlap it with backward

::: cards grid3
### [a] Ring all-reduce
Reduce-scatter (each GPU ends up owning one summed chunk) then all-gather (everyone receives every chunk). Built into NCCL (NVIDIA Collective Communications Library).

### [b] Bucketing
Group gradients into buckets of a few tens of MB and launch each bucket's all-reduce as soon as it is complete in the backward pass.

### [e] Exact
The averaged gradient equals the full-batch gradient, so DP gives the same model as one big GPU would.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Ring all-reduce, step by step

Four GPUs, each with a gradient split into four chunks. Step through reduce-scatter (sum as you go) and all-gather (copy the finished chunks). Notebook 01 implements exactly this.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><button class="btn primary" id="rNext">next step</button><button class="btn" id="rReset">reset</button></div>
  <svg id="rSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Ring all-reduce"></svg>
  <p class="readout" id="rOut"></p>
</div>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why data parallelism scales so well

::: cards grid2
### [a] Flat bandwidth cost
Each GPU sends ≈ 2·S per step regardless of N, so adding GPUs adds compute without adding per-GPU traffic.

### [e] Communication can hide
Backward pass compute is long; bucketed all-reduce runs underneath it. PyTorch DDP reports near-linear scaling on 256 GPUs.

### [d] Limits
Latency grows with N (2(N−1) steps); the global batch grows with GPUs; and memory per GPU never shrinks.

### [b] Where it lives
In large runs DP is the outermost axis, across nodes, usually sharded (deck 03).
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Data parallelism makes the model fit."
> Every GPU holds the full model, gradients and optimizer state. Only sharding (ZeRO/FSDP) or model parallelism reduces memory.
:::

::: reveal myth
? "All-reduce cost grows with the number of GPUs."
> Bandwidth per GPU stays ≈ 2·S; only the latency term grows.
:::

::: reveal myth
? "DP changes the result."
> Averaging per-GPU gradients is exactly the full-batch gradient (the same model, up to floating-point order).
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Which two collectives make up a ring all-reduce?
- [ ] broadcast + gather
- [x] reduce-scatter + all-gather
- [ ] all-to-all + reduce
- [ ] scatter + broadcast
> <b>Reduce-scatter + all-gather.</b>
:::

::: reveal
? What does gradient bucketing buy?
> It lets all-reduce start during the backward pass (overlap) and amortizes per-message latency over tens of MB.
:::

::: reveal
? Why might you skip gradient synchronization on some micro-batches?
> With gradient accumulation, only the last micro-batch's gradients need averaging; syncing every micro-batch wastes bandwidth.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Data parallelism copies the model, splits the batch and averages gradients with a ring all-reduce (≈ 2·S per GPU), overlapped with the backward pass.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Data parallelism is the simplest way to use many GPUs: each holds the full model, processes its own slice of the batch, and the gradients are averaged before the update so every copy stays identical. The average is computed with a ring all-reduce, a reduce-scatter followed by an all-gather, in which each GPU sends about twice the gradient size regardless of how many GPUs there are. Frameworks like PyTorch DDP group gradients into buckets and start all-reducing them while the backward pass is still running, which hides most of the communication. It does nothing for memory, which is the job of sharding.</p></div>
    <div class="recap"><div><span><b>Problem:</b> one GPU is too slow; replicas must agree on the gradient.</span></div><div><span><b>Core idea:</b> ring all-reduce (≈ 2·S per GPU), bucketed and overlapped with backward.</span></div><div><span><b>Limit:</b> full model copy per GPU; global batch grows with GPU count.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/distributed/01_ring_allreduce.ipynb" target="_blank" rel="noopener">01 · Ring all-reduce from scratch</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/distributed/01_ring_allreduce.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../03-zero-fsdp/index.html">03 · ZeRO and FSDP →</a> · Previous: <a href="../01-why-distribute/index.html">← 01</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
