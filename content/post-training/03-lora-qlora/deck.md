---
title: LoRA and QLoRA
body:
  data-deck: LoRA and QLoRA
  data-home: ../index.html
  data-home-label: Post-training
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'x :: layer input :: f'
  - 'W₀ x :: frozen (QLoRA: stored in NF4) :: f'
  - '(α/r)·B·A·x :: trainable, rank r

    B starts at 0 :: a'
  - 'sum :: h = W₀x + (α/r)BAx :: e'
  - 'merge after training :: W = W₀ + (α/r)BA :: c'
  caption: No extra layer at inference once merged; or keep one base and swap small adapters.
example:
  title: 'Worked example: LoRA on Llama 3 8B'
  setup: Rank r = 8 on W_q (4,096 × 4,096) and W_v (4,096 × 1,024) in all 32 layers.
  steps:
  - 'Per layer: 8 × (4,096 + 4,096) + 8 × (4,096 + 1,024) = 106,496 parameters.'
  - 'Total trainable: <b>3,407,872</b> = 0.042% of 8.03B.'
  - 'Adapter file in BF16: <b>6.5 MiB</b> vs a 16 GB full checkpoint.'
  - 'QLoRA: base in NF4 ≈ 8.03B × 0.5 bytes = <b>4.0 GB</b> + double-quantized scales (0.13 GB).'
  result: Train a few million parameters, store megabytes per task, and fit the frozen base in a quarter of its BF16 size.
traps:
  tricks:
  - 'Params per matrix = r·(d_in + d_out). :: Tiny compared with d_in·d_out.'
  - 'Scale α/r. :: Set α to the first r you try; changing r then needs little retuning.'
  - 'QLoRA overhead. :: 4 bits + 0.127 bits per parameter with double quantization.'
  traps:
  - 'Forgetting to merge. :: Unmerged adapters add a small extra matmul per layer at inference.'
  - '"QLoRA trains in 4-bit." :: Only the frozen base is 4-bit; compute is BF16 and adapters are 16-bit.'
  - 'Rank as a free win. :: Beyond the needed rank, extra rank only adds parameters.'
papers:
- lora
- qlora
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Post-training · 03</div>
    <h1>LoRA and QLoRA</h1>
    <p class="sub">Fine-tune by training a tiny low-rank update instead of every weight, and keep the frozen base model in 4-bit NormalFloat to fit large models on one GPU (graphics processing unit).</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Full fine-tuning stores gradients and optimizer state for every parameter and produces a full model copy per task: for an 8B model that is roughly 100 GB of training memory and 16 GB per checkpoint.</div>
      <div class="c"><b>Core idea</b><b>LoRA (Low-Rank Adaptation)</b>: freeze W₀ and learn ΔW = BA of rank r (B starts at 0), then merge after training. <b>QLoRA (Quantized Low-Rank Adaptation)</b>: store the frozen base in 4-bit <b>NF4 (4-bit NormalFloat)</b>, dequantize on the fly, train LoRA adapters in 16-bit.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Where the memory goes in full fine-tuning

Rough training memory: BF16 (bfloat16, a 16-bit floating-point format with the exponent range of 32-bit floats) weights (2 bytes per parameter), FP32 (32-bit floating point) gradients (4), and Adam's two FP32 moments (8). Activations are extra. LoRA keeps the last three only for its adapters; QLoRA also shrinks the frozen weights to about 4 bits.
{: .lede}

<div class="visual">
  <div class="seg" id="fSeg"><button data-v="8.03" class="on">8B</button><button data-v="65">65B</button></div>
  <div id="fBars" style="margin-top:12px"></div>
</div>

<p class="caption">Estimates from parameter counts, ignoring activations. QLoRA reports 65B fine-tuning going from more than 780 GB to under 48 GB of GPU memory.</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## The cost of updating everything

::: cards grid3
### [d] Optimizer state for every weight
Adam keeps two extra numbers per parameter, plus a gradient. That state is several times the size of the model itself.

### [b] One full copy per task
Ten fine-tuned variants of an 8B model are ten 16 GB checkpoints to store and to serve separately.

### [c] Adapters add latency
Earlier parameter-efficient methods inserted extra layers ("adapters") that stay in the forward pass at inference time.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## How many trainable parameters?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

<div class="quiz">
  <p class="qq">A 4,096 × 4,096 projection gets a LoRA update of rank r = 8. How many trainable parameters does that add?</p>
  <div class="opts">
  <button>A. 16,777,216</button>
  <button data-ok>B. 65,536</button>
  <button>C. 32,768</button>
  <button>D. 8</button>
  </div>
  <div class="why"><b>B.</b> A is 4,096 × 8 and B is 8 × 4,096: r·(d_in + d_out) = 8 × 8,192 = <b>65,536</b>, which is 0.4% of the 16.8M entries in the full matrix.</div>
</div>

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Low-rank updates

<div class="grid3">
  <div class="card a"><h3>Freeze, then add BA</h3><p>h = W₀x + (α/r)·BAx. W₀ is frozen. A gets a random Gaussian init and B starts at <b>zero</b>, "so ΔW = BA is zero at the beginning of training": you start exactly at the pretrained model.</p></div>
  <div class="card b"><h3>Choose where and how big</h3><p>The paper mostly adapts only W_q and W_v, and finds very small ranks (even r = 1–4) work well there. Many practitioners adapt all linear layers.</p></div>
  <div class="card e"><h3>Merge for free inference</h3><p>After training, W = W₀ + (α/r)BA is one ordinary matrix: "no additional inference latency". You can also keep W₀ shared and swap small adapters per task.</p></div>
</div>

<div class="deep"><h4>Reported results</h4><p>On GPT-3 175B, LoRA "can reduce the number of trainable parameters by 10,000 times and the GPU memory requirement by 3 times", and performs on par or better than full fine-tuning in model quality on RoBERTa, DeBERTa, GPT-2 and GPT-3, with higher training throughput. The α/r scale means changing r doesn't require retuning the learning rate much; the paper simply sets α to the first r tried.</p></div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## LoRA parameter calculator

For Llama 3 8B (32 layers, d = 4,096, GQA (grouped-query attention) with 1,024-wide K/V, FFN (feed-forward network) 14,336), choose the rank and which matrices get adapters.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">rank r <input type="range" id="lR" min="0" max="8" step="1" value="3"> <output id="lRo"></output></label>
    <div class="seg" id="lT"><button data-v="qv" class="on">W_q, W_v (paper default)</button><button data-v="attn">all attention</button><button data-v="all">all linear layers</button></div>
  </div>
  <div class="grid3" style="margin-top:14px">
    <div class="stat"><div class="num" id="lP" style="color:var(--a)"></div><div class="lbl">trainable parameters</div></div>
    <div class="stat"><div class="num" id="lF"></div><div class="lbl">of the 8.03B base</div></div>
    <div class="stat"><div class="num" id="lS"></div><div class="lbl">adapter size (BF16)</div></div>
  </div>
  <svg id="lSvg" viewBox="0 0 660 150" style="margin-top:10px" role="img" aria-label="W0 plus BA"></svg>
</div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## QLoRA: a 4-bit frozen base

The 16 NF4 levels (from the QLoRA paper) vs 16 evenly spaced INT4 (4-bit integer) levels, drawn over a normal distribution like the one pretrained weights follow. NF4 puts more levels where most weights are.
{: .lede}

<div class="visual">
  <svg id="qSvg" viewBox="0 0 660 200" role="img" aria-label="NF4 vs INT4 levels"></svg>
  <div class="legend"><span><i style="background:var(--a)"></i>NF4 levels</span><span><i style="background:var(--b)"></i>INT4 levels (uniform)</span><span><i style="background:var(--faint)"></i>normal density</span></div>
</div>

<div class="deep"><h4>The three QLoRA ingredients</h4><ul><li><b>NF4</b>: blockwise (64 weights per block) absmax-scaled 4-bit codes at normal quantiles. Notebook 03 measures lower error than uniform INT4 on Gaussian weights.</li><li><b>Double quantization</b>: quantize the per-block scales too, cutting their overhead from 0.5 to 0.127 bits per parameter, about 3 GB for a 65B model.</li><li><b>Paged optimizers</b>: page optimizer state between GPU and CPU (central processing unit) memory to survive memory spikes.</li></ul><p>Weights are dequantized to BF16 for each matmul; gradients flow through them to the 16-bit LoRA adapters. The paper: 4-bit QLoRA with NF4 "matches 16-bit full finetuning and 16-bit LoRA finetuning performance on academic benchmarks".</p></div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why a low rank is enough

::: cards grid2
### [a] Updates have low intrinsic rank
The LoRA paper's hypothesis, supported by its experiments: the change needed to adapt a pretrained model lives in a small subspace, even though the weights themselves are full rank.

### [e] Notebook evidence
Fitting a rank-4 update: ranks 1–3 plateau at clear error, rank ≥ 4 fits essentially perfectly. A rank above the true rank adds nothing.

### [b] The trade-off
Low rank limits what can change. For large shifts (new languages, lots of new knowledge), higher ranks, more target matrices, or full fine-tuning can do better.

### [c] Serving many variants
Because adapters are tiny, one base model can serve many fine-tunes by swapping or batching adapters, instead of loading many full copies.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "LoRA makes inference slower."
> Merge W₀ + (α/r)BA after training and the model is exactly as fast as before. That is a main advantage over adapter layers.
:::

::: reveal myth
? "QLoRA trains in 4-bit."
> Only the <b>frozen base weights</b> are stored in 4-bit. They are dequantized to BF16 for compute, and the LoRA adapters and their gradients are 16-bit.
:::

<div class="quiz myth">
  <p class="qq">"A bigger rank is always better."</p>
  <button class="reveal">Why is this wrong?</button>
  <div class="why">Past the rank the task needs, extra rank only adds parameters; the paper found very small ranks sufficient for W_q and W_v.</div>
</div>

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Why is B initialized to zero?
- [ ] To save memory
- [x] So the model starts exactly at the pretrained weights
- [ ] Because A is random and B must be orthogonal
- [ ] To make merging possible
> <b>B.</b> BA = 0 at step 0, so training starts from W₀ exactly.
:::

<div class="quiz ">
  <p class="qq">Name the three techniques QLoRA combines with LoRA.</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">4-bit NormalFloat (NF4) storage of the frozen base, double quantization of the scales, and paged optimizers.</div>
</div>

<div class="quiz ">
  <p class="qq">Adapters for W_q and W_v at r = 8 on Llama 3 8B: how many trainable parameters?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">32 × 8 × [(4,096 + 4,096) + (4,096 + 1,024)] = <b>3,407,872</b>, about 0.04% of 8.03B.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">LoRA trains a rank-r update BA beside a frozen W₀ and merges it afterwards; QLoRA keeps the frozen base in 4-bit NF4 so large models fine-tune on a single GPU.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Full fine-tuning needs gradients and Adam state for every parameter and a full model copy per task. LoRA freezes the pretrained weights and learns a low-rank update, B times A, starting from B equal to zero so training begins at the pretrained model. Because adaptation updates have low intrinsic rank, a small r works, with 10,000 times fewer trainable parameters on GPT-3, and after training the update merges into the weight with no inference cost. QLoRA additionally stores the frozen base in 4-bit NormalFloat, quantizes the scales again, and pages optimizer state, which brings 65 billion parameter fine-tuning from over 780 gigabytes to under 48.</p></div>

<div class="recap"><div><span><b>Problem:</b> full fine-tuning memory ≈ 14 bytes/param plus a full copy per task.</span></div><div><span><b>LoRA:</b> W₀ + (α/r)BA, B = 0 at init, merge after: tiny trainable set, no latency.</span></div><div><span><b>QLoRA:</b> NF4 frozen base + double quantization + paged optimizers; 65B on one 48 GB GPU.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/post-training/02_lora.ipynb" target="_blank" rel="noopener">02 · LoRA from scratch</a> <span style="color:var(--faint)">· 40 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/post-training/02_lora.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/post-training/03_nf4_quantization.ipynb" target="_blank" rel="noopener">03 · QLoRA's NF4 and double quantization</a> <span style="color:var(--faint)">· 30 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/post-training/03_nf4_quantization.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../04-reward-models/index.html">04 · Reward models →</a> · Previous: <a href="../02-supervised-fine-tuning/index.html">← 02</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Hu et al. 2021, "LoRA: Low-Rank Adaptation of Large Language Models" (§4, Fig. 1, §7); Dettmers et al. 2023, "QLoRA: Efficient Finetuning of Quantized LLMs" (§3, Appendix E NF4 values).</p>

<!-- slide id="s-papers" from="papers" -->
