---
title: Tensor and Sequence Parallelism
body:
  data-deck: Tensor and sequence parallelism
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
  - 'X :: full activations :: f'
  - 'A column-split :: each GPU: its hidden units :: c'
  - 'local nonlinearity :: no communication :: a'
  - 'B row-split :: partial outputs :: b'
  - 'all-reduce :: sum partials :: d'
  caption: One all-reduce per block forward, one backward; with sequence parallelism, reduce-scatter + all-gather instead.
example:
  title: 'Worked example: activation memory per layer (GPT-3 175B)'
  setup: 'Korthikanti et al.: activations per layer = s·b·h·(34 + 5as/h) bytes, with s = 2,048, b = 1, h = 12,288, a = 96 heads.'
  steps:
  - 5as/h = 5 × 96 × 2,048 / 12,288 = <b>80</b> (the attention-score term).
  - 'Per layer, no parallelism: 2,048 × 12,288 × (34 + 80) bytes = <b>2.67 GiB</b>; × 96 layers = 256 GiB.'
  - 'Tensor + sequence parallelism over t = 8: ÷ 8 → <b>0.33 GiB</b> per layer.'
  - 'Plus selective recomputation (drop the 5as/h part, recompute it): 34·sbh/8 = <b>0.10 GiB</b> per layer.'
  result: The paper reports 5× less activation memory and MFU rising from 42.1% (full recompute) to 54.2% on a 530B model.
traps:
  tricks:
  - 'Column then row. :: The nonlinearity stays local; one all-reduce per block.'
  - 'Two all-reduces per layer forward. :: One after attention, one after the MLP; two more in backward.'
  - 'TP ≤ GPUs per NVLink domain. :: Usually TP = 8 on HGX servers.'
  traps:
  - 'TP across nodes. :: Per-layer all-reduces over the network dominate step time.'
  - 'TP > KV heads. :: K/V heads get replicated (GQA models).'
  - 'Forgetting replicated activations. :: Plain TP keeps LayerNorm/dropout inputs on every GPU; sequence parallelism shards them.'
papers:
- megatron
- korthikanti
- megatron21
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Distributed Training · 04</div>
    <h1>Tensor and sequence parallelism</h1>
    <p class="sub">Split every weight matrix across the GPUs of a node (Megatron), and shard the activations that tensor parallelism alone would duplicate (sequence parallelism).</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Some layers are too big for one GPU, and even sharded weights must be gathered whole to compute. Splitting the matrices themselves needs communication inside every layer.</div>
      <div class="c"><b>Core idea</b><b>Tensor parallelism</b>: split the first matrix of each block by columns and the second by rows, so each GPU computes its share and one all-reduce per block combines them. <b>Sequence parallelism</b>: split the LayerNorm and dropout regions along the sequence, turning each all-reduce into a reduce-scatter + all-gather.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Split the matrix, not the batch

One MLP block across t GPUs. Pick t: each GPU holds 1/t of each weight matrix and computes 1/t of the hidden units; partial outputs are summed with an all-reduce.
{: .lede}

<div class="visual">
  <div class="seg" id="tSeg"><button data-v="1">t = 1</button><button data-v="2">t = 2</button><button data-v="4" class="on">t = 4</button><button data-v="8">t = 8</button></div>
  <svg id="tSvg" viewBox="0 0 660 200" style="margin-top:10px" role="img" aria-label="Tensor parallel split"></svg>
  <p class="readout" id="tOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## What data parallelism can't do

::: cards grid3
### [d] Layer too big
FSDP still materializes each full layer on every GPU when it computes; giant layers and their activations may not fit.

### [b] Per-GPU work is fixed
DP shortens the step only by splitting the batch, which grows the global batch.

### [c] Activations dominate
At long sequence lengths, activations per layer exceed the weights.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Where is the communication?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? In a Megatron MLP (A split by columns, B split by rows), when do GPUs need to communicate in the forward pass?
- [ ] After A and after B
- [x] Only after B (one all-reduce)
- [ ] Never
- [ ] Before A only
> <b>B.</b> Column-splitting A gives each GPU complete hidden units, so tanh/GELU is local. Row-splitting B gives partial sums of the output, combined with one all-reduce. The backward pass needs one more, for the input gradient.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Megatron tensor parallelism, plus sequence parallelism

::: cards grid2
### [a] Attention
Split by heads: each GPU computes its heads (column-split Q, K, V), then the output projection is row-split and all-reduced.

### [c] MLP
First matrix column-split, second row-split: one all-reduce forward, one backward.

### [b] Sequence parallelism
The regions between blocks (LayerNorm, dropout) are split along the sequence; each all-reduce becomes a reduce-scatter + all-gather of the same total volume.

### [e] Selective recompute
Recompute only the attention-score part (large memory, few FLOPs) in backward instead of whole layers.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Activation memory per layer vs strategy

GPT-3-scale layer (h = 12,288, 96 heads, micro-batch 1). Move the sequence length and tensor-parallel degree.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">Sequence length <input type="range" id="aS" min="0" max="4" step="1" value="1"> <output id="aSo"></output></label>
    <label class="ctl">TP degree t <input type="range" id="aT" min="0" max="3" step="1" value="3"> <output id="aTo"></output></label>
  </div>
  <div id="aBars" style="margin-top:12px"></div>
</div>
<p class="caption">Formula from Korthikanti et al.: s·b·h·(34 + 5as/h) bytes per layer without parallelism. Tensor parallelism alone divides only the parts inside the attention and MLP blocks (the paper's 10 + 24/t + 5as/(ht) form); with sequence parallelism everything divides by t.</p>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works, and its limits

::: cards grid2
### [a] Exact
Splitting matrices and summing partials gives identical results; notebook 03 checks forward and backward against the unsplit layer.

### [e] Cuts per-GPU work and memory
Each GPU reads and computes 1/t of every layer, and with sequence parallelism stores 1/t of the activations.

### [d] Communication every layer
Four collectives per layer per step (two forward, two backward); only NVLink makes them cheap.

### [b] Bounded by the node
TP scales to the NVLink domain (8 GPUs on HGX, up to 72 on NVL72); beyond that use PP, CP and DP.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Tensor parallelism is just model sharding like FSDP."
> FSDP gathers whole layers and each GPU computes all of a layer on its own data; TP keeps layers split and each GPU computes part of every layer on the same data.
:::

::: reveal myth
? "Sequence parallelism adds communication."
> It replaces each all-reduce with a reduce-scatter + all-gather of the same total volume, while sharding activations.
:::

::: reveal myth
? "Bigger t is always better."
> Communication grows and per-GPU matmuls shrink; past the NVLink domain it slows down.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? How many all-reduces does one transformer layer need in the forward pass with Megatron TP?
- [ ] 0
- [ ] 1
- [x] 2
- [ ] 4
> <b>2</b>: one after attention, one after the MLP.
:::

::: reveal
? What does sequence parallelism shard that plain TP replicates?
> Activations in the LayerNorm and dropout regions between the attention and MLP blocks, split along the sequence dimension.
:::

::: reveal
? What does selective recomputation recompute?
> Only the attention-score operations (QKᵀ, softmax, dropout, attention over V): large activations, few FLOPs.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Tensor parallelism splits every matrix inside a node with one all-reduce per block; sequence parallelism and selective recompute shard and shrink the activations.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>When a layer or its activations are too big, split the matrices themselves. Megatron splits the first matrix of each block by columns and the second by rows, so each GPU computes its share of the hidden units and an all-reduce sums the partial outputs, once per block in the forward pass and once in backward. That communication happens in every layer, so tensor parallelism stays inside the fast NVLink domain. Sequence parallelism also shards the activations between blocks along the sequence, and selective recomputation drops only the cheap but huge attention-score activations, cutting activation memory about five times.</p></div>
    <div class="recap"><div><span><b>Problem:</b> layers and activations too big; FSDP still computes whole layers.</span></div><div><span><b>Core idea:</b> column-then-row splits, one all-reduce per block; sequence-parallel activations.</span></div><div><span><b>Placement:</b> inside the NVLink domain (TP ≈ 8).</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/distributed/03_tensor_parallel_training.ipynb" target="_blank" rel="noopener">03 · Tensor-parallel MLP: forward and backward</a> <span style="color:var(--faint)">· 40 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/distributed/03_tensor_parallel_training.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../05-pipeline-parallelism/index.html">05 · Pipeline parallelism →</a> · Previous: <a href="../03-zero-fsdp/index.html">← 03</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
