---
title: Parallelism for Inference
body:
  data-deck: Parallelism for inference
  data-home: ../index.html
  data-home-label: Inference
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'X (replicated) :: every GPU has the input :: f'
  - 'W₁ split by columns :: each GPU: its share

    + GELU locally :: a'
  - 'W₂ split by rows :: partial outputs :: b'
  - 'all-reduce :: sum partials over NVLink :: d'
  - 'Y (replicated) :: next block :: f'
  caption: 'Megatron MLP: one all-reduce in the forward pass; attention splits by heads the same way.'
example:
  title: 'Worked example: tensor parallelism for a 70B model'
  setup: 70B parameters in BF16 = 140 GB of weights. H100s with 80 GB each, 3.35 TB/s HBM. 80 layers.
  steps:
  - 'One GPU can''t even hold the weights (140 GB > 80 GB). TP = 8: <b>17.5 GB</b> per GPU.'
  - 'Per-token weight read: 41.8 ms if one GPU could hold it, vs <b>5.2 ms</b> with TP = 8, since each GPU reads only its eighth in parallel.'
  - 'Communication: 2 all-reduces per layer × 80 layers = <b>160 all-reduces per token</b>, each only batch × 8,192 × 2 bytes (16 KiB at batch 1).'
  - Those messages are small and latency-bound, so they need NVLink inside one server; across a network they would dominate.
  result: TP cuts per-token latency up to ~8× here, minus communication; it is the standard way to serve models larger than one GPU at low latency.
traps:
  tricks:
  - 'TP lowers latency, PP raises throughput. :: TP splits every layer across GPUs; PP splits the layers into stages (pipeline parallelism).'
  - 'Two all-reduces per transformer block. :: One after attention, one after the MLP (forward pass).'
  - 'Keep TP within the NVLink domain. :: Typically TP ≤ GPUs per server.'
  traps:
  - 'TP across nodes. :: Hundreds of small all-reduces per token over a slower network erase the gain.'
  - 'TP degree > KV heads. :: With 8 KV heads and TP = 16, KV heads must be replicated, wasting cache memory.'
  - 'Expecting linear speedup. :: Communication and fixed per-step costs grow with TP degree.'
papers:
- megatron
- pope
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">LLM Inference &amp; Serving · 08</div>
    <h1>Parallelism for inference</h1>
    <p class="sub">Splitting a model across GPUs (graphics processing units) to serve it: tensor parallelism for latency and fit, pipeline and data parallelism for throughput, expert parallelism for MoE (Mixture of Experts), and why the communication pattern decides where each one runs.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>A large model may not fit in one GPU's memory, and even when it fits, one GPU's memory bandwidth limits how fast each decode step can be.</div>
      <div class="c"><b>Core idea</b><b>Tensor parallelism</b> splits every matmul so each GPU reads only its share of the weights per token, at the cost of one all-reduce per block, which must stay on NVLink.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Fit and speed both hit a single-GPU wall

::: cards grid2
### [d] Fit
A 70B model in BF16 (bfloat16, a 16-bit floating-point format with the exponent range of 32-bit floats) is about 140 GB of weights, more than one 80 GB GPU, before any KV (key-value) cache.

### [b] Speed
At batch 1, one decode step must read all the weights. At 3.35 TB/s (H100 HBM (high-bandwidth memory)), 140 GB takes at least about 42 ms per token.
:::

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Not every split helps latency

::: cards grid3
### [b] Pipeline (layers across GPUs)
Fits the model, but a single request still visits every stage in turn, so per-token latency doesn't improve.

### [c] Data parallel (replicas)
More throughput, but each replica must hold the whole model, and per-request latency is unchanged.

### [d] Naive splits
Splitting carelessly forces communication after every matmul.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Lower per-token latency

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Which kind of parallelism reduces per-token decode latency for a single request?
- [ ] Data parallelism (more replicas)
- [x] Tensor parallelism: split each weight matrix so every GPU reads 1/n of the weights per token
- [ ] Pipeline parallelism across nodes
- [ ] Larger batch size
> <b>B.</b> With TP (tensor parallelism) of degree n, each GPU streams only 1/n of the weights each step, so the memory-bound step time drops roughly n× (minus communication). Pipeline and data parallelism help capacity and throughput, not one request's latency.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Megatron-style tensor parallelism

<div class="visual"><svg id="tpSvg" viewBox="0 0 660 200" role="img" aria-label="Column then row parallel MLP"></svg></div>

<div class="grid3" style="margin-top:12px">
  <div class="card a"><h3>Column-parallel first</h3><p>Split W₁ by output columns. Each GPU computes its slice, and GELU (Gaussian Error Linear Unit) stays local because it's elementwise.</p></div>
  <div class="card b"><h3>Row-parallel second</h3><p>Split W₂ by input rows to match. Each GPU holds a partial sum.</p></div>
  <div class="card e"><h3>One all-reduce</h3><p>Sum the partials once per MLP (and once per attention block). That's two all-reduces per layer.</p></div>
</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## TP degree vs latency and communication <span class="ill">bandwidth-only model</span>

<div class="visual">
  <div class="controls" style="margin-top:0">
    <select id="tM"><option value="16,4096,32">8B-shaped (16 GB, d=4096, 32 layers)</option><option value="140,8192,80" selected>70B-shaped (140 GB, d=8192, 80 layers)</option></select>
    <div class="seg" id="tN"><button data-v="1">TP 1</button><button data-v="2">TP 2</button><button data-v="4">TP 4</button><button data-v="8" class="on">TP 8</button></div>
    <div class="seg" id="tL"><button data-v="450" class="on">NVLink (450 GB/s)</button><button data-v="50">400G network (50 GB/s)</button></div>
  </div>
  <div class="grid4" style="margin-top:14px">
    <div class="stat"><div class="num" id="tW"></div><div class="lbl">weights per GPU</div></div>
    <div class="stat"><div class="num" id="tR"></div><div class="lbl">weight-read time per step (≥)</div></div>
    <div class="stat"><div class="num" id="tC"></div><div class="lbl">all-reduce time per step</div></div>
    <div class="stat"><div class="num" id="tT" style="color:var(--a)"></div><div class="lbl">≈ TPOT (time per output token) lower bound (batch 1)</div></div>
  </div>
</div>

<p class="caption">Per step: read weights ÷ n at 3.35 TB/s (H100 HBM), plus 2 all-reduces per layer of d BF16 values × 2(n−1)/n over the link. Latency per message is ignored, and in practice it makes off-node TP even worse.</p>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why TP lives inside the NVLink domain

::: cards grid2
### [e] Less to read per GPU
Decode is bound by bytes. Splitting weights n ways cuts each GPU's per-step read about n×.

### [d] Small, frequent, blocking messages
Two all-reduces per layer per step sit on the critical path, so they need NVLink-class bandwidth and latency (GPU decks 04 and 05).

### [b] Combine strategies
TP within a node; pipeline across nodes for very large models; data-parallel replicas for throughput.

### [c] MoE: expert parallelism
Experts live on different GPUs and tokens travel by all-to-all. TensorRT-LLM, for example, lists "Wide Expert Parallelism" as a runtime feature.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "More TP always means lower latency."
> Weight reads shrink as 1/n, but all-reduce cost does not. Beyond the NVLink domain, communication can dominate.
:::

::: reveal myth
? "Pipeline parallelism speeds up a single request."
> A request still passes through every stage in order. Pipelining helps fit and throughput, not one request's latency.
:::

::: reveal myth
? "TP needs communication after every matmul."
> The column-then-row (Megatron) arrangement needs <b>one</b> all-reduce per MLP or attention block.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? How many all-reduces per transformer layer does Megatron-style TP need in the forward pass?
- [ ] 0
- [ ] 1
- [x] 2
- [ ] one per matmul
> <b>Two</b>: one after attention, one after the MLP.
:::

<div class="quiz ">
  <p class="qq">Why is GELU between the two MLP matmuls "free" under TP?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">After the column-parallel W₁ each GPU holds complete columns of the hidden activation, and GELU is <b>elementwise</b>, so it runs locally with no communication.</div>
</div>

<div class="quiz ">
  <p class="qq">Roughly what is the minimum per-token decode time for 140 GB of weights on one H100 (3.35 TB/s), and with TP 8?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">140 / 3,350 ≈ <b>42 ms</b>. With TP 8 each GPU reads 17.5 GB, about <b>5.2 ms</b>, plus all-reduce time.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Tensor parallelism splits every weight matrix so each GPU reads 1/n of the weights per token, cutting latency and fitting big models, at the cost of two small all-reduces per layer that must stay on NVLink.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>One GPU may not hold a large model, and at batch 1 a decode step is bounded by reading all the weights: about 42 ms for 140 GB at H100 bandwidth. Tensor parallelism splits each matmul Megatron-style (column-parallel then row-parallel), so each GPU reads 1/n of the weights and only one all-reduce is needed per attention or MLP block. Those all-reduces are small but on the critical path, so TP stays inside the NVLink domain. Pipeline and data parallelism add capacity and throughput, and expert parallelism spreads MoE experts across GPUs.</p></div>

<div class="recap"><div><span><b>Problem:</b> single-GPU memory capacity and bandwidth limit both fit and per-token latency.</span></div><div><span><b>Core idea:</b> column → row TP: 1/n of the weights per GPU, two all-reduces per layer, kept on NVLink.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/12_tensor_parallel.ipynb" target="_blank" rel="noopener">12 · Tensor-parallel linear layers (Megatron-style)</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/inference/12_tensor_parallel.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../09-disaggregated-serving/index.html">09 · Disaggregated serving →</a> · Previous: <a href="../07-quantization/index.html">← 07</a> · <a href="../index.html">All decks</a></p>

<!-- slide id="s-papers" from="papers" -->
