---
title: 'Putting It Together: 4D Layouts'
body:
  data-deck: 'Putting it together: 4D layouts'
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
  - 'TP :: inside the node, NVLink :: c'
  - 'CP :: long sequences :: e'
  - 'PP :: across nodes, point-to-point :: b'
  - 'DP / FSDP :: outermost, network :: a'
  caption: Llama 3 orders GPU groups as [TP, CP, PP, DP], fastest-changing first, so TP neighbours share a node.
example:
  title: 'Worked example: Llama 3 405B on 16,384 H100s'
  setup: '126 layers, d = 16,384. Reported 8K-sequence layout: TP 8, CP 1, PP 16, DP 128 (43% → 41% MFU from 8,192 to 16,384 GPUs; 38% at 131K context with CP 16).'
  steps:
  - 'GPUs: 8 × 1 × 16 × 128 = <b>16,384</b>.'
  - 'Parameters per GPU after TP and PP: 405B / (8 × 16) ≈ <b>3.16B</b> → 6.3 GB of BF16 weights.'
  - 'Model states with FSDP over DP 128 on top: 16 × 405B / 16,384 ≈ <b>0.4 GB</b> per GPU (activations extra).'
  - 'At 131K context: CP = 16 and DP = 8 instead (8 × 16 × 16 × 8 = 16,384), trading data parallelism for sequence capacity.'
  result: TP stays within the 8-GPU NVLink node, PP spreads memory across 16 nodes, CP appears only for long context, and DP supplies the rest of the scale.
traps:
  tricks:
  - 'Order axes by bandwidth. :: TP innermost, DP outermost.'
  - 'Product = GPUs. :: TP × CP × PP × DP must equal the cluster (or job) size.'
  - 'Check three numbers. :: Memory per GPU, bubble (p−1)/(v·m), and global batch.'
  traps:
  - 'TP across nodes. :: Per-layer all-reduces over the network collapse MFU.'
  - 'Too much PP for the batch. :: Few micro-batches per pipeline → large bubbles.'
  - 'Ignoring stragglers. :: At 16K GPUs one slow GPU slows every synchronous step (deck 11).'
papers:
- llama3
- megatron21
- megascale
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Distributed Training · 10</div>
    <h1>Putting it together: 4D layouts</h1>
    <p class="sub">How real training runs combine tensor, context, pipeline and data parallelism, and how to reason about a layout from first principles: Llama 3 405B as the worked case.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Each parallelism axis has a different communication pattern, memory effect and scaling limit. Choosing the product TP × CP × PP × DP for a cluster is a constrained puzzle.</div>
      <div class="c"><b>Core idea</b>Nest the axes by bandwidth need: <b>TP</b> inside the node (NVLink), <b>CP</b> when sequences are long, <b>PP</b> across nodes for memory, <b>DP</b> (sharded) outermost for throughput. Check memory fits, the pipeline bubble is small and the batch is large enough.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## A planner for one cluster

Choose degrees for each axis. The planner checks the GPU count, model-state memory per GPU (FSDP over DP on top of TP and PP), the pipeline bubble and the micro-batches available. Presets reproduce the layouts reported for Llama 3 405B.
{: .lede}

<div class="visual">
  <div class="seg" id="qSeg"><button data-v="8,1,16,128,8192" class="on">Llama 3 405B · 8K</button><button data-v="8,16,16,8,131072">Llama 3 405B · 128K</button><button data-v="16,1,8,128,8192">TP 16 (across nodes)</button></div>
  <div class="controls">
    <label class="ctl">TP <select id="qT"><option>1</option><option>2</option><option>4</option><option selected>8</option><option>16</option></select></label>
    <label class="ctl">CP <select id="qC"><option selected>1</option><option>2</option><option>4</option><option>8</option><option>16</option></select></label>
    <label class="ctl">PP <select id="qP"><option>1</option><option>4</option><option>8</option><option selected>16</option><option>32</option></select></label>
    <label class="ctl">DP <select id="qD"><option>8</option><option>16</option><option>32</option><option>64</option><option selected>128</option><option>256</option></select></label>
  </div>
  <div class="grid4" style="margin-top:12px">
    <div class="stat"><div class="num" id="qG"></div><div class="lbl">GPUs</div></div>
    <div class="stat"><div class="num" id="qM"></div><div class="lbl">model states per GPU</div></div>
    <div class="stat"><div class="num" id="qB"></div><div class="lbl">bubble (v = 2, 16M-token batch)</div></div>
    <div class="stat"><div class="num" id="qN"></div><div class="lbl">TP within one 8-GPU node?</div></div>
  </div>
  <p class="readout" id="qOut"></p>
</div>
<p class="caption">Illustrative model: 405B parameters, 16 bytes per parameter fully sharded over TP·PP·DP; micro-batch of one sequence per pipeline; activations not included.</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why one axis is never enough

::: cards grid2
### [d] TP is capped by the node
Beyond 8 GPUs (HGX) its per-layer all-reduces leave NVLink.

### [b] PP is capped by the batch
More stages need more micro-batches to keep the bubble small.

### [c] DP is capped by the batch too
The global batch grows with DP; past a point it hurts convergence.

### [e] CP is only for long context
It adds K/V traffic that only pays off when sequences are long.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Where should TP go?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? You have 8 GPUs per node with NVLink, and a 400 Gb/s network between nodes. Which degree of tensor parallelism is safest?
- [ ] TP = 1
- [x] TP = 8, one node
- [ ] TP = 64 across 8 nodes
- [ ] TP = number of GPUs
> <b>B.</b> TP all-reduces activations in every layer, so it must stay within the NVLink domain: TP = 8 on an 8-GPU node, which is what Llama 3 used.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Nest the axes by bandwidth

::: cards grid2
### [c] TP innermost
Most frequent, latency-sensitive communication: keep it on NVLink.

### [e] CP next
K/V exchange for long sequences; often within or across a few nodes.

### [b] PP across nodes
Point-to-point activations only at stage boundaries.

### [a] DP outermost
One gradient reduction per step, overlapped with backward; sharded (FSDP/ZeRO) for memory.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Reported layouts

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Run</th><th>GPUs</th><th>Layout</th><th>Reported efficiency</th></tr>
  <tr><td>Llama 3 405B, 8K seq</td><td>8,192</td><td>TP 8 · CP 1 · PP 16 · DP 64</td><td>43% BF16 MFU</td></tr>
  <tr><td>Llama 3 405B, 8K seq</td><td>16,384</td><td>TP 8 · CP 1 · PP 16 · DP 128</td><td>41% BF16 MFU</td></tr>
  <tr><td>Llama 3 405B, 131K seq</td><td>16,384</td><td>TP 8 · CP 16 · PP 16 · DP 8</td><td>38% BF16 MFU</td></tr>
  <tr><td>Megatron-LM 1T model</td><td>3,072</td><td>tensor + pipeline + data (PTD-P)</td><td>502 PFLOP/s, 52% of peak</td></tr>
  <tr><td>MegaScale 175B</td><td>12,288</td><td>3D parallelism + many optimizations</td><td>55.2% MFU (1.34× Megatron-LM)</td></tr>
  <tr><td>DeepSeek-V3 (MoE)</td><td>2,048 H800</td><td>PP 16 · EP 64 · ZeRO-1 DP</td><td>2.788M GPU-hours total</td></tr>
</table></div>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why this layout logic works

::: cards grid2
### [a] Communication matches links
The heaviest traffic uses the fastest links, so exposed communication stays small.

### [e] Memory is spread multiplicatively
TP × PP divides weights per GPU; FSDP divides model states further; CP and TP+SP divide activations.

### [b] Scale comes from DP
Once the model fits, DP adds throughput with flat per-GPU bandwidth.

### [d] Efficiency still drops
Llama 3: 43% at 8K GPUs, 41% at 16K; long context 38%. Bubbles, stragglers and exposed communication grow with scale.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "There is one optimal layout."
> It depends on model size, sequence length, batch size, cluster topology and memory; Llama 3 changed its layout for long-context training.
:::

::: reveal myth
? "More model parallelism is always safer."
> Every model-parallel axis adds communication; use as little as needed to fit, and DP for the rest.
:::

::: reveal myth
? "MFU should be near 100%."
> Large runs report 38–55%; the rest is bubbles, communication, recomputation and stragglers.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Llama 3 405B's 16K-GPU 8K-sequence layout?
- [ ] TP 16 · PP 8 · DP 128
- [x] TP 8 · CP 1 · PP 16 · DP 128
- [ ] TP 8 · CP 16 · PP 16 · DP 8
- [ ] DP 16,384
> <b>TP 8 · CP 1 · PP 16 · DP 128.</b> The 128K-context layout used CP 16 and DP 8.
:::

::: reveal
? In what order should the axes be nested, from innermost?
> TP (NVLink), then CP, then PP, with DP outermost, matching communication volume to link bandwidth.
:::

::: reveal
? Name three numbers you check before launching a layout.
> Memory per GPU (states + activations), pipeline bubble, and global batch size; also that TP stays within the NVLink domain.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Real runs nest TP (NVLink) inside CP, PP and sharded DP, choosing degrees so memory fits, bubbles stay small and the batch stays sensible, as Llama 3 405B did on 16,384 GPUs.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>No single parallelism axis scales a frontier run, so they are combined. Tensor parallelism has the heaviest, most frequent communication and stays inside a node on NVLink. Context parallelism is added for long sequences. Pipeline parallelism spreads layers across nodes with only point-to-point traffic. Sharded data parallelism is outermost and supplies the remaining scale. Llama 3 405B used tensor 8, pipeline 16 and data 128 on 16,384 H100s at about 41 percent utilization, and switched to context 16 with data 8 for 128K-token training. Before launching, check memory per GPU, the bubble and the batch size.</p></div>
    <div class="recap"><div><span><b>Problem:</b> each axis has its own cost and limit.</span></div><div><span><b>Core idea:</b> nest by bandwidth: TP ⊂ CP ⊂ PP ⊂ DP.</span></div><div><span><b>Check:</b> memory fit, bubble, batch; Llama 3: 8·1·16·128.</span></div></div>
    <p class="start-hint">Next: <a href="../11-reliability-stability/index.html">11 · Reliability and stability →</a> · Previous: <a href="../09-mixed-precision-fp8/index.html">← 09</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
