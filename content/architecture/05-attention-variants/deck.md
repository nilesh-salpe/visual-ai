---
title: MQA, GQA and MLA
body:
  data-deck: MQA, GQA and MLA
  data-home: ../index.html
  data-home-label: Architecture
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'query heads :: all n_h kept :: c'
  - 'group them :: g groups :: a'
  - 'shared K/V head :: one per group (GQA)

    or a latent (MLA) :: b'
  - 'KV cache :: shrinks by n_h / g :: e'
  caption: 'MQA: g = 1. GQA: 1 < g < n_h. MHA: g = n_h. MLA compresses all heads into one latent instead.'
example:
  title: 'Worked example: cache per token per layer, DeepSeek-V2 dimensions'
  setup: 128 heads of dimension 128; MLA latent d_c = 512 plus a 64-dim decoupled RoPE key. Numbers are cached elements; multiply by 2 for BF16 bytes.
  steps:
  - 'MHA: 2 × 128 × 128 = <b>32,768</b> elements.'
  - 'GQA, 8 groups: <b>2,048</b> (6.2% of MHA).'
  - 'MLA: <b>576</b> (1.8% of MHA).'
  - 'MQA: <b>256</b> (0.8% of MHA).'
  - 'MLA ≈ 4.5 head-dims: about GQA with 2.25 groups, with quality reported above MHA.'
  result: Sharing (GQA) or compressing (MLA) cuts the cache 16× and 57× here, which converts directly into more concurrent sequences or longer contexts.
traps:
  tricks:
  - 'Cache ∝ KV heads. :: Shrink factor = n_heads / n_kv_heads.'
  - 'Convert MHA → GQA cheaply. :: Mean-pool the K and V heads in each group, then uptrain with ~5% of the pretraining compute.'
  - 'MLA absorbs W_UK into W_Q. :: Keys are never materialized at inference.'
  traps:
  - 'Expecting GQA to cut FLOPs. :: Score FLOPs barely change; the saving is memory and bandwidth.'
  - 'Plain RoPE with MLA. :: The position rotation breaks absorption; MLA needs a decoupled RoPE slice.'
  - 'TP degree above KV heads. :: KV heads then get replicated across GPUs, wasting cache.'
papers:
- mqa
- gqa
- dsv2
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">The Modern LLM · 05</div>
    <h1>MQA, GQA and MLA: fewer keys and values</h1>
    <p class="sub">The modelling side of shrinking the KV (key-value) cache: sharing key/value heads (MQA (multi-query attention), GQA (grouped-query attention)), compressing them into a latent (MLA (multi-head latent attention)), and why MLA needs "decoupled" RoPE (rotary position embedding).</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>During generation every layer stores keys and values for every past token and head. That cache, not compute, limits batch size and context length.</div>
      <div class="c"><b>Core idea</b><b>Share</b> K/V heads across groups of query heads (MQA: 1 group, GQA: g groups), or <b>compress</b> all heads' K/V into one small latent per token and re-expand on the fly (MLA).</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## The cache scales with K/V heads

<p class="lede">The KV cache stores 2 × layers × <b>K/V heads</b> × head_dim numbers per token. With standard multi-head attention (MHA), every query head has its own K and V. This deck is the architecture view; memory sizes in GB and serving effects are in <a href="../../inference/02-kv-cache/index.html">Inference deck 02</a>.</p>

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">K/V heads (32 query heads) <input type="range" id="kH" min="0" max="5" step="1" value="5"> <output id="kHo"></output></label></div>
  <svg id="kSvg" viewBox="0 0 660 170" style="margin-top:10px" role="img" aria-label="Query heads sharing KV heads"></svg>
  <p class="readout" id="kOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why not just use one K/V head?

::: cards grid3
### [d] MQA can lose quality
Multi-query attention (Shazeer 2019) shares <b>one</b> K/V head across all query heads. Ainslie et al.: MQA "can lead to quality degradation and training instability".

### [b] Training a second model is expensive
Pretraining a separate MQA model just for faster inference is costly. Ideally you could convert an existing MHA checkpoint.

### [c] Tensor parallelism wants ≥ 1 K/V head per GPU
With one K/V head and 8-way tensor parallelism, that head is replicated on every GPU (graphics processing unit), which wastes the saving. A few groups split cleanly across GPUs.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Count the groups

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Llama 3 70B has 64 query heads and 8 key/value heads. How many query heads share each K/V head, and how much smaller is the KV cache than MHA?
- [x] 8 each; 8× smaller
- [ ] 64 each; 64× smaller
- [ ] 8 each; 64× smaller
- [ ] They don't share; same size
> <b>A.</b> 64 / 8 = 8 query heads per K/V head. The cache scales with the number of K/V heads, so it is 64 / 8 = <b>8×</b> smaller than MHA with 64 K/V heads.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Share or compress

<div class="grid3">
  <div class="card b"><h3>MQA (2019)</h3><p>All query heads share <b>one</b> K and one V. Smallest cache (2·d_h per layer per token); PaLM used it. Risk: quality loss.</p></div>
  <div class="card a"><h3>GQA (2023)</h3><p>Query heads split into <b>g groups</b>; each group shares one K/V head. g = 1 is MQA; g = heads is MHA. "Quality close to multi-head attention with comparable speed to multi-query." Llama 2 (34B, 70B), Mistral, Llama 3.</p></div>
  <div class="card e"><h3>MLA (2024)</h3><p>Cache one <b>latent vector</b> c (d_c = 512 in DeepSeek-V2) per token and layer, and up-project to every head's K and V when needed. A small extra slice carries RoPE.</p></div>
</div>

<div class="deep"><h4>Converting MHA into GQA</h4><p>Ainslie et al. convert a trained multi-head checkpoint: the key and value projection matrices within each group are <b>mean-pooled</b> into one head (mean pooling worked better than picking one head or random init), then the model is <b>uptrained</b> for about <b>5%</b> of its original pretraining compute. Uptrained GQA reached quality close to MHA with speed close to MQA.</p></div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## MLA step by step

Step through what DeepSeek-V2 computes for one token, and what goes into the cache.
{: .lede}

<div class="visual">
  <div class="seg" id="mSeg"><button data-v="0" class="on">1 · compress</button><button data-v="1">2 · expand (naive)</button><button data-v="2">3 · absorb</button><button data-v="3">4 · RoPE problem</button><button data-v="4">5 · decoupled RoPE</button></div>
  <svg id="mSvg" viewBox="0 0 660 200" style="margin-top:10px" role="img" aria-label="MLA data flow"></svg>
  <div class="infobox" id="mInfo" style="background:var(--panel-2);border-radius:10px;padding:12px 14px;margin-top:10px;font-size:14px;color:var(--muted)"></div>
</div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Cache per token, per layer: the numbers

<p class="lede">DeepSeek-V2's comparison (Table 1) in numbers of elements per token per layer, with its dimensions: n_h = 128 heads, d_h = 128, d_c = 512, RoPE slice d_h<sup>R</sup> = 64.</p>

<div class="visual"><div id="cBars"></div></div>

<div class="deep"><h4>Reading the table</h4><p>MHA: 2·n_h·d_h. GQA: 2·n_g·d_h. MQA: 2·d_h. MLA: d_c + d_h<sup>R</sup> ≈ (9/2)·d_h, "equal to GQA with only 2.25 groups", while the paper reports <b>stronger</b> performance than MHA. Against DeepSeek 67B, DeepSeek-V2 reports a <b>93.3%</b> smaller KV cache and <b>5.76×</b> higher maximum generation throughput (that comparison also includes other changes, such as MoE (Mixture of Experts) and FP8 (8-bit floating point) KV).</p></div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why sharing works, and what each option costs

<div class="visual scroll-x"><table class="tbl">
  <tr><th></th><th>MHA</th><th>GQA</th><th>MQA</th><th>MLA</th></tr>
  <tr><td>KV cache / token / layer</td><td>2·n_h·d_h</td><td>2·g·d_h</td><td>2·d_h</td><td>d_c + d_R</td></tr>
  <tr><td>Quality</td><td>baseline</td><td>close to MHA</td><td>can degrade</td><td>reported ≥ MHA</td></tr>
  <tr><td>Extra compute</td><td>none</td><td>none</td><td>none</td><td>up-projections, absorbed into Q and O at inference</td></tr>
  <tr><td>Works with plain RoPE</td><td>yes</td><td>yes</td><td>yes</td><td>no: needs decoupled RoPE</td></tr>
  <tr><td>Used by</td><td>GPT-3, LLaMA 1</td><td>Llama 2 70B, Mistral, Llama 3</td><td>PaLM</td><td>DeepSeek-V2, V3</td></tr>
</table></div>

<div class="deep"><h4>Why sharing barely hurts</h4><p>Decoding is memory-bound: each step reads the whole KV cache to produce one token per sequence. Query heads still differ, and each one attends to the shared keys in its own way, so the model keeps most of its capacity to look for different things. What it loses is the ability to <b>store</b> different keys per head. GQA's groups and MLA's per-head up-projections recover much of that.</p></div>

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "MQA means attention with a single head."
> There are still many <b>query</b> heads, each attending differently. Only the keys and values are shared.
:::

::: reveal myth
? "GQA mainly saves FLOPs (floating-point operations)."
> The FLOPs for attention scores barely change, because every query head still computes its scores. GQA saves <b>KV-cache memory and memory bandwidth</b>, which is what limits decoding.
:::

<div class="quiz myth">
  <p class="qq">"MLA is just low-rank GQA, and RoPE works the same."</p>
  <button class="reveal">Why is this wrong?</button>
  <div class="why">MLA's trick depends on absorbing W_UK into W_Q, and RoPE's position-dependent rotation sits between them and breaks that. DeepSeek-V2 needs a separate decoupled RoPE slice with a key shared across heads.</div>
</div>

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? GQA with g = 1 is…
- [ ] MHA
- [x] MQA
- [ ] MLA
- [ ] Sliding-window attention
> <b>MQA</b>: one group, so one K/V head shared by every query head.
:::

<div class="quiz ">
  <p class="qq">How do you turn a trained MHA model into a GQA model cheaply?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Mean-pool the K and V projection matrices of the heads in each group into one head, then uptrain for about 5% of the original pretraining compute (Ainslie et al., 2023).</div>
</div>

<div class="quiz ">
  <p class="qq">Why can't MLA simply apply RoPE to its reconstructed keys?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Inference relies on precomputing W_Q·W_UKᵀ so keys never get decompressed. RoPE inserts a rotation that depends on both positions between those matrices, so no single precomputed matrix works. DeepSeek-V2 carries position in a separate small RoPE query/key slice instead.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">The KV cache scales with K/V heads: share them (MQA, GQA) or compress them into a latent (MLA). MLA needs decoupled RoPE to keep its absorption trick.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>During decoding, memory, not compute, is the limit, and the KV cache scales with the number of key/value heads. MQA shares one K/V head across all query heads; it is smallest but can lose quality. GQA uses a few groups, gets quality close to MHA at near-MQA speed, and an existing model can be converted by mean-pooling heads and uptraining for about 5% of the original compute. MLA, from DeepSeek-V2, caches one small latent per token and re-expands it per head; at inference the up-projection is absorbed into the query projection so keys are never materialized. RoPE would break that absorption, so MLA adds a small decoupled RoPE slice.</p></div>

<div class="recap"><div><span><b>Problem:</b> KV cache per token = 2 × layers × K/V heads × head_dim.</span></div><div><span><b>Share:</b> MQA (1 group) and GQA (g groups): cache shrinks by heads/g; convert by mean-pool + 5% uptraining.</span></div><div><span><b>Compress:</b> MLA caches d_c + d_R ≈ 4.5·d_h; absorption + decoupled RoPE.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/architecture/04_mla_absorption.ipynb" target="_blank" rel="noopener">04 · Multi-head latent attention (MLA) and weight absorption</a> <span style="color:var(--faint)">· 45 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/architecture/04_mla_absorption.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../06-decoder-only/index.html">06 · Decoder-only, and why it won →</a> · Previous: <a href="../04-swiglu/index.html">← 04</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Shazeer 2019, "Fast Transformer Decoding: One Write-Head is All You Need"; Ainslie et al. 2023, "GQA" (EMNLP; mean-pooling, 5% uptraining); Chowdhery et al. 2022 (PaLM §2, MQA); Touvron et al. 2023 (Llama 2 Table 1); DeepSeek-AI 2024, DeepSeek-V2 (§2.1, Table 1); Llama 3 §3.2.</p>

<!-- slide id="s-papers" from="papers" -->
