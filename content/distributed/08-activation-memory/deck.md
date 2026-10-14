---
title: Activation Memory and Recomputation
body:
  data-deck: Activation memory and recomputation
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
  - 'forward :: keep a checkpoint every k layers :: a'
  - 'discard the rest :: memory ≈ L/k + k :: f'
  - 'backward per segment :: recompute from checkpoint :: b'
  - 'gradients :: identical :: e'
  caption: Best k ≈ √L; cost ≈ one extra forward pass.
example:
  title: 'Worked example: activations for a GPT-3-scale model'
  setup: 96 layers, h = 12,288, 96 heads, sequence 2,048, micro-batch 1; per-layer activations s·b·h·(34 + 5as/h) bytes (Korthikanti et al.).
  steps:
  - 'Per layer: <b>2.67 GiB</b>; all 96 layers: <b>256 GiB</b>, more than three 80 GB GPUs.'
  - 'Full recomputation (store only each layer''s input, 2·s·b·h bytes): 4.5 GiB, at the cost of recomputing every layer.'
  - 'Selective (drop only the 5as/h attention part): 76 GiB, recomputing only cheap attention-score ops.'
  - 'With TP = 8 and sequence parallelism on top: 9.6 GiB per GPU.'
  result: Selective recomputation plus sequence parallelism removes most activation memory for a few percent of compute.
traps:
  tricks:
  - 'Activations ∝ sequence × batch × layers. :: Weights don''t grow with them.'
  - 'k ≈ √L. :: Memory ≈ 2√L stored activations.'
  - 'Recompute what is cheap. :: Attention scores: big memory, few FLOPs.'
  traps:
  - 'Full recompute everywhere. :: ~30% slower; selective often suffices.'
  - 'Forgetting the backward peak. :: A segment''s activations are rebuilt during its backward.'
  - 'Mixing checkpointing with RNG. :: Dropout masks must be reproduced exactly during recompute.'
papers:
- chen_ckpt
- korthikanti
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Distributed Training · 08</div>
    <h1>Activation memory and recomputation</h1>
    <p class="sub">Where activation memory comes from in a transformer, and how full, selective and √n checkpointing trade a little extra compute for a lot of memory.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Backward needs every intermediate activation of the forward pass; for long sequences and big batches those activations exceed the weights many times over.</div>
      <div class="c"><b>Core idea</b>Store only some activations (<b>checkpoints</b>) and <b>recompute</b> the rest during backward. Checkpointing every √n layers needs about 2√n stored activations for one extra forward pass; <b>selective</b> recomputation drops just the cheap-to-recompute attention scores.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Activations, not weights, fill the GPU

Memory for one GPT-3-scale layer's activations vs its weights as the sequence grows (micro-batch 1, BF16).
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">sequence length <input type="range" id="mS" min="0" max="5" step="1" value="1"> <output id="mSo"></output></label></div>
  <div id="mBars" style="margin-top:12px"></div>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why you can't just drop activations

::: cards grid3
### [d] Backward needs them
Each layer's gradient uses its inputs and intermediate values from the forward pass.

### [b] Offloading is slow
Copying activations to CPU memory goes over PCIe, about 50× slower than HBM.

### [c] Smaller batches hurt
Shrinking the micro-batch reduces GPU efficiency and, with pipelines, increases bubbles.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What to keep?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? You store activations only every k layers and recompute the rest. Roughly how many activations are stored at peak?
- [ ] L
- [ ] k
- [x] L/k + k
- [ ] L · k
> <b>C.</b> L/k checkpoints, plus the k activations of the segment being recomputed during its backward. Minimized at k = √L.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Three recomputation strategies

::: cards grid3
### [a] Full
Store only each transformer layer's input; recompute the whole layer in backward. Minimum memory, ~30% more time.

### [b] √n checkpointing
Store a checkpoint every √n layers: O(√n) memory for one extra forward (Chen et al.: 48 GB → 7 GB for 1,000 layers at +30%).

### [e] Selective
Recompute only the attention-score operations (large activations, few FLOPs). Korthikanti et al.: MFU 54.2% vs 42.1% with full recompute.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Memory vs compute for a deep stack

A stack of L layers. Choose the checkpoint spacing k: stored activations L/k + k, recompute cost about one extra forward whenever k > 1.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">layers L <input type="range" id="kL" min="4" max="256" step="4" value="64"> <output id="kLo"></output></label><label class="ctl">checkpoint every k <input type="range" id="kK" min="1" max="64" step="1" value="8"> <output id="kKo"></output></label></div>
  <svg id="kSvg" viewBox="0 0 660 220" style="margin-top:10px" role="img" aria-label="Memory vs k"></svg>
  <p class="readout" id="kOut"></p>
</div>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why recomputation is a good trade

::: cards grid2
### [a] GPUs have spare FLOPs
Memory, not compute, usually limits batch and sequence size; spending some FLOPs to save memory pays off.

### [e] Exact
Recomputed activations are identical (with the same dropout RNG), so gradients are unchanged.

### [b] Selective is nearly free
Attention scores are memory-heavy but compute-light, so recomputing just them costs little.

### [c] Composes with everything
Works with TP, SP, PP and FSDP; pipelines also store only stage-boundary activations with recompute.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Recomputation changes the gradients."
> It reproduces the same values (with the same RNG state), so gradients are identical.
:::

::: reveal myth
? "Checkpointing doubles the training time."
> It adds about one extra forward pass, roughly a third more compute for full recompute; selective recompute adds much less.
:::

::: reveal myth
? "FlashAttention makes recomputation unnecessary."
> FlashAttention avoids storing the N×N score matrix; other activations (MLP, LayerNorm) remain.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? With L = 100 layers, roughly how many activations are stored with optimal checkpointing?
- [ ] 10
- [x] 20
- [ ] 50
- [ ] 100
> k = 10 → L/k + k = <b>20</b>.
:::

::: reveal
? What does selective recomputation recompute and why?
> Only the attention-score operations: they create large activations (the 5as/h term) but have few FLOPs, so recomputing them is cheap.
:::

::: reveal
? Why must dropout be handled carefully with recomputation?
> The recomputed forward must use the same random mask; frameworks save and restore the RNG state.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Activation memory scales with sequence, batch and depth; checkpointing (√n), full or selective recomputation trade a little compute for most of that memory.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Backward needs the forward pass's intermediate activations, and for transformers they scale with sequence length, batch and depth, quickly exceeding the weights. Checkpointing stores only some activations and recomputes the rest during backward. Storing a checkpoint every square-root-of-n layers needs about two square-root-of-n activations for one extra forward pass. Full recomputation stores just each layer's input. Selective recomputation, from Korthikanti and colleagues, recomputes only the attention-score operations, which are large but cheap, and together with sequence parallelism removes most activation memory at little cost.</p></div>
    <div class="recap"><div><span><b>Problem:</b> activations grow with s·b·L and dwarf weights.</span></div><div><span><b>Core idea:</b> store checkpoints, recompute the rest: memory ≈ L/k + k.</span></div><div><span><b>Practice:</b> selective recompute + sequence parallelism.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/distributed/05_activation_checkpointing.ipynb" target="_blank" rel="noopener">05 · Activation checkpointing</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/distributed/05_activation_checkpointing.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../09-mixed-precision-fp8/index.html">09 · Mixed precision and FP8 training →</a> · Previous: <a href="../07-expert-parallelism/index.html">← 07</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
