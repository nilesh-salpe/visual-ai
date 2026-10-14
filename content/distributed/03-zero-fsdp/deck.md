---
title: ZeRO and FSDP
body:
  data-deck: ZeRO and FSDP
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
  - 'shard everything :: params, grads, Adam state ÷ N :: a'
  - 'all-gather layer weights :: just before forward/backward :: c'
  - 'compute :: on the full layer :: b'
  - 'free + reduce-scatter grads :: each GPU keeps its slice :: e'
  - 'sharded Adam :: update own slice :: f'
  loop: '4 -> 1 :: layer by layer, every step'
  caption: Same math as plain data parallelism; memory per GPU falls ≈ N×.
example:
  title: 'Worked example: a 70B model on 64 GPUs'
  setup: 70B parameters, 16 bytes per parameter of model states, 64 data-parallel GPUs with 80 GB each (activations not included).
  steps:
  - 'Stage 0 (DDP): <b>1,120 GB</b> per GPU.'
  - 'Stage 1 (optimizer state sharded): 4P + 12P/64 = <b>293 GB</b>.'
  - 'Stage 2 (+ gradients): 2P + 14P/64 = <b>155 GB</b>.'
  - 'Stage 3 (+ parameters): 16P/64 = <b>17.5 GB</b>, the only stage that fits in 80 GB.'
  result: ZeRO reports 4× (stage 1) and 8× (stage 2) reductions for large N and N× for stage 3; communication rises from ≈ 2·P to ≈ 3·P elements per step.
traps:
  tricks:
  - 'Stage 1 → 4×, stage 2 → 8×, stage 3 → N×. :: As the DP degree grows (ZeRO paper).'
  - 'Prefetch. :: All-gather layer k+1 while computing layer k.'
  - 'Hybrid sharding. :: Shard within a node, replicate across nodes, to keep all-gathers on NVLink.'
  traps:
  - 'Assuming stage 3 is free. :: It adds a parameter all-gather in backward (≈1.5× DP traffic).'
  - 'Tiny shards at huge N. :: Per-message latency dominates; shard groups are often limited.'
  - 'Forgetting activations. :: ZeRO shards model states, not activations (decks 04 and 08).'
papers:
- zero
- fsdp
- llama3
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Distributed Training · 03</div>
    <h1>ZeRO and FSDP: sharded data parallelism</h1>
    <p class="sub">Data parallelism without the copies: shard optimizer state, gradients and parameters across GPUs, and fetch each layer's weights just in time.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Plain data parallelism stores the full 16 bytes per parameter on every GPU, most of it optimizer state that each GPU only needs a slice of.</div>
      <div class="c"><b>Core idea</b><b>ZeRO</b> (Zero Redundancy Optimizer) partitions optimizer state (stage 1), then gradients (stage 2), then parameters (stage 3) across the data-parallel GPUs. Stage 3 / <b>FSDP</b> all-gathers each layer's weights right before use and reduce-scatters its gradients right after.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Most of the memory is redundant

Memory per GPU for model states, by ZeRO stage. Move the model size and the number of data-parallel GPUs; the dashed line is one 80 GB GPU.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">Parameters <input type="range" id="zP" min="0" max="4" step="1" value="2"> <output id="zPo"></output></label>
    <label class="ctl">Data-parallel GPUs <input type="range" id="zN" min="0" max="6" step="1" value="3"> <output id="zNo"></output></label>
  </div>
  <div id="zBars" style="margin-top:12px"></div>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why not just shard by hand?

::: cards grid3
### [d] Replicated optimizer state
Adam's FP32 master weights, momentum and variance are 12 of the 16 bytes per parameter, copied on every GPU.

### [b] Model parallelism is intrusive
Tensor and pipeline parallelism require changing the model code and its layout.

### [c] Communication must stay modest
Any sharding scheme must not multiply the per-step traffic, or DP stops scaling.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What is sharded first?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Which part of the 16 bytes per parameter does ZeRO stage 1 shard?
- [ ] BF16 weights
- [ ] BF16 gradients
- [x] Optimizer state (FP32 master, momentum, variance)
- [ ] Activations
> <b>C.</b> It is 12 of the 16 bytes and each GPU only needs its own slice to update its own slice of the parameters. That alone gives up to 4× at the same communication volume.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Three stages of sharding

::: cards grid3
### [a] Stage 1: optimizer state
Each GPU keeps Adam state for 1/N of the parameters and updates only that slice; then the updated weights are all-gathered. "4x memory reduction, same communication volume."

### [b] Stage 2: + gradients
Gradients are reduce-scattered instead of all-reduced: each GPU keeps only the averaged slice it updates. "8x memory reduction, same communication volume."

### [e] Stage 3: + parameters (FSDP)
Weights live sharded; each layer is all-gathered just before its forward and backward and freed after. "Memory reduction is linear with DP degree."
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## One FSDP step for one layer

::: cards grid4
### [c] 1 · all-gather
Collect the layer's weight shards from all GPUs into a full copy.

### [a] 2 · forward
Compute the layer, then free the gathered weights (or keep them for backward, trading memory for one less all-gather).

### [b] 3 · backward
All-gather again if freed, compute gradients for the full layer.

### [e] 4 · reduce-scatter
Average gradients across GPUs; each keeps the slice for its shard, then updates it with sharded Adam.
:::

::: deep How Llama 3 tuned it
Llama 3 used FSDP and chose "not reshard after forward computation to avoid an extra all-gather communication during backward passes", and accumulated and reduce-scattered gradients in FP32 for numerical stability.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why sharding is exact and cheap enough

::: cards grid2
### [a] Exact
Every GPU sees the full layer when computing and the averaged gradient when updating; notebook 02 matches single-GPU training exactly.

### [e] Communication only rises modestly
Stages 1–2 keep DP's ≈ 2·P traffic; stage 3 adds one parameter all-gather (≈ 3·P total), overlapped by prefetching.

### [b] No model rewrite
FSDP wraps modules; the model code stays the same, unlike tensor or pipeline parallelism.

### [d] What it doesn't fix
Activations and the per-layer full-weight peak still need memory; very large layers still need tensor parallelism.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "ZeRO is a different optimizer."
> It is the same Adam, partitioned: each GPU updates its slice with identical math.
:::

::: reveal myth
? "Stage 3 triples communication."
> Per step it is about 1.5× plain DP (all-gather in forward and backward plus reduce-scatter), much of it overlapped.
:::

::: reveal myth
? "FSDP replaces tensor parallelism."
> FSDP shards storage, but every GPU still computes whole layers on its own data; huge layers and per-GPU latency still need TP.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Model states per GPU for 7B parameters with ZeRO-3 on 8 GPUs?
- [ ] 112 GB
- [ ] 28 GB
- [x] 14 GB
- [ ] 7 GB
> 16 × 7B / 8 = <b>14 GB</b>.
:::

::: reveal
? Why does stage 2 use reduce-scatter instead of all-reduce for gradients?
> Each GPU only updates its own slice, so it only needs the averaged gradient for that slice; reduce-scatter delivers exactly that at half the all-reduce traffic.
:::

::: reveal
? What does FSDP prefetching overlap?
> The all-gather of the next layer's weights with the computation of the current layer.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">ZeRO/FSDP keeps data parallelism's simplicity but shards optimizer state, gradients and parameters, cutting model-state memory up to N× for modestly more communication.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Plain data parallelism copies 16 bytes per parameter to every GPU, most of it Adam state. ZeRO removes the redundancy in stages: shard the optimizer state, then the gradients, which become a reduce-scatter instead of an all-reduce, then the parameters themselves. With full sharding, which PyTorch implements as FSDP, each layer's weights are all-gathered just before use and freed afterwards, so memory per GPU falls roughly with the number of GPUs. The math is identical to ordinary data parallel training, and the extra parameter all-gathers are hidden by prefetching.</p></div>
    <div class="recap"><div><span><b>Problem:</b> DP replicates 16 B/param; Adam state is 12 of them.</span></div><div><span><b>Core idea:</b> shard optimizer (1), gradients (2), parameters (3); gather just in time.</span></div><div><span><b>Cost:</b> ≈ 1.5× DP traffic for stage 3; activations still separate.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/distributed/02_zero_sharding.ipynb" target="_blank" rel="noopener">02 · ZeRO / FSDP: sharded data parallelism</a> <span style="color:var(--faint)">· 45 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/distributed/02_zero_sharding.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../04-tensor-sequence-parallelism/index.html">04 · Tensor and sequence parallelism →</a> · Previous: <a href="../02-data-parallelism/index.html">← 02</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
