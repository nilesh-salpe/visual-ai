---
title: Why Training Must Be Distributed
body:
  data-deck: Why training must be distributed
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
  - 'one model, one GPU :: too little memory, too slow :: d'
  - 'data parallel :: copy the model, split the batch :: a'
  - 'tensor parallel :: split each matrix :: c'
  - 'pipeline parallel :: split the layers :: b'
  - 'context parallel :: split the sequence :: e'
  caption: Real runs combine all of them (deck 10).
example:
  title: 'Worked example: one GPU vs a 70B model'
  setup: 70B parameters, 15T training tokens, mixed-precision Adam (16 bytes per parameter), H100 at 989 TFLOP/s with 40% MFU (model FLOPs utilization).
  steps:
  - 'Model states: 16 × 70B = <b>1.12 TB</b>, versus 80 GB of HBM (high-bandwidth memory) on one GPU: 14× too much.'
  - 'Compute: 6 × N × D = 6 × 70B × 15T = <b>6.3e+24 FLOPs</b>.'
  - 'On one GPU: 6.3e+24 ÷ (989 TFLOP/s × 0.4) ≈ <b>505 GPU-years</b>.'
  - 'On 16,384 GPUs at the same efficiency: ≈ <b>11 days</b>.'
  result: Memory forces the model to be split; time forces thousands of GPUs. Both must happen without wasting the GPUs on communication.
traps:
  tricks:
  - 'Training FLOPs ≈ 6·N·D. :: Forward 2, backward 4 per parameter per token.'
  - 'Model states ≈ 16 bytes per parameter. :: BF16 weights and grads + FP32 master, m and v.'
  - 'Activations are the third bill. :: They scale with batch × sequence × layers (deck 08).'
  traps:
  - 'Thinking more GPUs only add speed. :: Many techniques exist mainly to make the model fit.'
  - 'Ignoring communication. :: Every split adds traffic; the art is hiding it behind compute.'
  - 'Counting peak FLOPs. :: Plan with realistic MFU (~40% for large runs).'
papers:
- megatron21
- zero
- llama3
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Distributed Training · 01</div>
    <h1>Why training must be distributed</h1>
    <p class="sub">The two walls a single GPU hits when training a large model, memory and time, and the four ways of splitting the work across thousands of GPUs.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>A 70B-parameter model needs over a terabyte just for weights, gradients and optimizer state, and training it on one GPU would take centuries.</div>
      <div class="c"><b>Core idea</b>Split the work along four axes: <b>data</b> (different examples per GPU), <b>tensor</b> (split each matrix), <b>pipeline</b> (split the layers) and <b>context</b> (split the sequence), plus <b>expert</b> parallelism for MoE models.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Two walls: memory and time

Pick a model size and training-token count. The bars show model-state memory per parameter (16 bytes with mixed-precision Adam) against one 80 GB GPU, and how long the run would take.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">Parameters <input type="range" id="wN" min="0" max="5" step="1" value="2"> <output id="wNo"></output></label>
    <label class="ctl">Tokens <input type="range" id="wD" min="0" max="3" step="1" value="2"> <output id="wDo"></output></label>
    <label class="ctl">GPUs <input type="range" id="wG" min="0" max="5" step="1" value="4"> <output id="wGo"></output></label>
  </div>
  <div class="grid3" style="margin-top:14px">
    <div class="stat"><div class="num" id="wM" style="color:var(--d)"></div><div class="lbl">model states (16 B/param)</div></div>
    <div class="stat"><div class="num" id="wF"></div><div class="lbl">training FLOPs (6·N·D)</div></div>
    <div class="stat"><div class="num" id="wT" style="color:var(--a)"></div><div class="lbl">days at 40% MFU on H100s</div></div>
  </div>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why a bigger GPU is not the answer

::: cards grid3
### [d] Memory grows with the model
Weights, gradients and optimizer state alone take 16 bytes per parameter; the largest GPUs hold 80–192 GB.

### [b] Compute grows with model × data
Compute-optimal training scales tokens with parameters, so FLOPs grow roughly with the square of model size.

### [c] One chip improves slowly
A new GPU generation every ~2 years gives a few × more FLOPs; model training compute grew far faster.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Which split helps memory?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Plain data parallelism copies the whole model to every GPU. What does it reduce?
- [ ] Memory per GPU
- [x] Time per step for a fixed global batch
- [ ] Both equally
- [ ] Neither
> <b>B.</b> Each GPU processes a slice of the batch, so the step finishes sooner, but every GPU still holds the full model, gradients and optimizer state. Fitting the model needs sharding (ZeRO/FSDP), tensor or pipeline parallelism.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Four axes of parallelism

::: cards grid2
### [a] Data (DP)
Each GPU gets different examples; gradients are averaged with an all-reduce. Sharded variants (ZeRO, FSDP) also split the model states.

### [c] Tensor (TP)
Split every weight matrix across GPUs; partial results are combined with all-reduces in every layer. Needs NVLink-class bandwidth.

### [b] Pipeline (PP)
Give each GPU a contiguous block of layers; activations flow stage to stage. Costs pipeline "bubbles".

### [e] Context (CP)
Split a long sequence across GPUs; attention exchanges keys and values. MoE models add expert parallelism (EP).
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## What each axis splits, and what it costs

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Axis</th><th>Splits</th><th>Communication</th><th>Typical placement</th><th>Deck</th></tr>
  <tr><td>Data (DDP)</td><td>the batch</td><td>gradient all-reduce once per step</td><td>across nodes</td><td>02</td></tr>
  <tr><td>Sharded data (ZeRO/FSDP)</td><td>batch + model states</td><td>all-gather params, reduce-scatter grads</td><td>across nodes</td><td>03</td></tr>
  <tr><td>Tensor + sequence</td><td>each matrix; activations</td><td>all-reduce (or reduce-scatter + all-gather) every layer</td><td>inside a node (NVLink)</td><td>04</td></tr>
  <tr><td>Pipeline</td><td>the layers</td><td>point-to-point activations per micro-batch</td><td>across nodes</td><td>05</td></tr>
  <tr><td>Context</td><td>the sequence</td><td>K/V exchange in attention</td><td>inside or across nodes</td><td>06</td></tr>
  <tr><td>Expert</td><td>MoE experts</td><td>all-to-all dispatch and combine</td><td>across nodes</td><td>07</td></tr>
</table></div>

::: deep Hardware context
Bandwidth falls about 10× per step away from the GPU (HBM 3,350 · NVLink 450 · network 50 GB/s per direction on H100 systems). The chattiest parallelism goes on the fastest links. See <a href="../../gpu/05-cluster-topology/index.html">GPU deck 05</a> for the network and collectives.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why combining axes works

::: cards grid2
### [a] Each axis has a different cost
TP communicates most and needs NVLink; DP communicates least per FLOP and tolerates the network; PP sits in between.

### [e] Memory and speed are separate knobs
Sharding and TP/PP make it fit; DP and CP add throughput; recomputation trades compute for memory.

### [b] Overlap hides traffic
Gradient all-reduce overlaps the backward pass; pipeline sends overlap compute; ring attention overlaps K/V passing.

### [c] Real systems prove it
Llama 3 405B trained on 16,384 H100s with TP, CP, PP and FSDP-style DP at 38–43% MFU.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Just use more GPUs with data parallelism."
> DP alone keeps a full copy of the model on every GPU; past ~1–2B parameters it no longer fits without sharding or model parallelism.
:::

::: reveal myth
? "Model parallelism is always slower."
> It costs communication, but it is the only way large models fit, and with good placement (TP on NVLink) the overhead is moderate.
:::

::: reveal myth
? "Linear scaling is the default."
> Communication, bubbles and stragglers grow with scale; 40% MFU at 16K GPUs is considered very good.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Model states for a 7B model with mixed-precision Adam?
- [ ] 14 GB
- [ ] 28 GB
- [x] 112 GB
- [ ] 7 GB
> 16 bytes × 7B = <b>112 GB</b>.
:::

::: reveal
? Which parallelism axes reduce memory per GPU, and which mainly add throughput?
> Memory: sharded DP (ZeRO/FSDP), TP, PP, CP (activations). Throughput: plain DP (more examples in parallel) and CP for long sequences.
:::

::: reveal
? Why is tensor parallelism usually kept inside one node?
> It all-reduces activations in every layer, many times per step; only NVLink-class bandwidth makes that cheap.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Large-model training is distributed because the model does not fit and one GPU is far too slow; four axes (data, tensor, pipeline, context) plus experts split the work.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>A 70 billion parameter model needs about 1.1 terabytes for weights, gradients and Adam state and would take decades of GPU time on one H100. So training is split. Data parallelism gives each GPU different examples and averages gradients; sharded data parallelism also splits the model states. Tensor parallelism splits each matrix and needs fast NVLink. Pipeline parallelism splits the layers into stages. Context parallelism splits long sequences, and MoE models add expert parallelism. Real runs combine them so that the chattiest communication rides the fastest links.</p></div>
    <div class="recap"><div><span><b>Problem:</b> memory (16 B/param) and time (6·N·D) both exceed one GPU by orders of magnitude.</span></div><div><span><b>Core idea:</b> split along data, tensor, pipeline, context (and expert) axes.</span></div><div><span><b>Practice:</b> combine axes; put the chattiest on NVLink; overlap communication with compute.</span></div></div>
    <p class="start-hint">Next: <a href="../02-data-parallelism/index.html">02 · Data parallelism →</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
