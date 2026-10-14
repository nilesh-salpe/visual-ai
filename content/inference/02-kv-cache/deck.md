---
title: KV Cache
body:
  data-deck: KV cache
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
  - 'new token :: embedding of the latest token :: f'
  - 'q, k, v :: computed for this token only :: a'
  - 'append k, v :: to every layer''s cache :: b'
  - 'attend :: q · all cached keys

    → weights × cached values :: c'
  - 'next token :: sample, feed back in :: e'
  loop: '4 -> 0 :: one decode step per token; the cache grows by one entry per layer each step'
  caption: The cache turns "recompute the whole prefix" into "compute one token and read the past".
example:
  title: 'Worked example: how big is the cache?'
  setup: 'Llama-3-70B: 80 layers, 8 KV (key-value) heads (GQA), head dimension 128, BF16 (2 bytes). Context 8,192 tokens, batch 32.'
  steps:
  - 'Per token: 2 (K and V) × 80 layers × 8 heads × 128 × 2 bytes = <b>327,680 bytes = 320 KiB</b>.'
  - 'Per sequence at 8,192 tokens: 320 KiB × 8,192 = <b>2.5 GiB</b>.'
  - 'Batch of 32: <b>80 GiB</b>, about as much as the 70B weights in FP8.'
  - 'Without GQA (64 KV heads, one per query head) it would be 8× larger: <b>640 GiB</b>.'
  result: 'Rule: KV bytes per token = 2 × layers × KV heads × head_dim × bytes. For this model, every 1,000 tokens of context costs <b>0.31 GiB</b> per sequence.'
traps:
  tricks:
  - 'KV bytes/token = 2·L·n_kv·d_head·bytes. :: Use KV heads, not query heads.'
  - 'Total = per-token × context × batch. :: Batch and context trade against each other for the same memory.'
  - 'GQA saves n_heads / n_kv. :: Llama-3-70B: 64 query heads / 8 KV heads = 8× smaller cache.'
  - 'Break-even with weights. :: Context × batch where KV = weight bytes tells you when memory, not weights, limits concurrency.'
  traps:
  - 'Using num_attention_heads. :: With GQA the cache scales with num_key_value_heads; using query heads overestimates by the group factor.'
  - 'Dropping the factor 2. :: There are two cached tensors, K and V.'
  - 'Caching queries. :: Past queries are never reused; only K and V are cached.'
  - 'Thinking the cache changes outputs. :: It is exact: identical logits to recomputing everything.'
papers:
- mqa_2
- gqa_2
- dsv2_2
- pope
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">LLM Inference &amp; Serving · 02</div>
    <h1>The KV cache</h1>
    <p class="sub">Why every LLM (large language model) server stores past keys and values, how much memory that takes, and how GQA (grouped-query attention) and MLA (multi-head latent attention) shrink it.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Without caching, generating token t re-runs attention over all t previous tokens, so total work grows quadratically.</div>
      <div class="c"><b>Core idea</b>Store each layer's <b>K and V</b> for every past token. A new token computes only its own q, k and v and attends over the cache. The result is exact, but memory grows with context × batch.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Naive generation redoes almost all of its work

Generating token <i>t</i> needs attention between the new token and all <i>t</i> previous tokens. A naive loop re-runs the full forward pass over the whole prefix for every new token.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">Prompt <input type="range" id="nP" min="16" max="2048" step="16" value="512"> <output id="nPo"></output></label>
    <label class="ctl">New tokens <input type="range" id="nN" min="16" max="2048" step="16" value="512"> <output id="nNo"></output></label>
  </div>
  <div id="nBars" style="margin-top:12px"></div>
</div>

<p class="caption">Token positions processed by the forward pass: naive = Σ (prompt + i) for i &lt; n; cached = prompt + n.</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Recomputing is pure waste

::: cards grid3
### [d] Same K and V every time
Past tokens' keys and values don't change when a new token arrives, because causal masking means earlier positions never see later ones.

### [b] Quadratic total work
Generating n tokens costs about n²/2 token-passes, so long answers get disproportionately slow.

### [c] Latency grows each step
Every step is slower than the one before it, so TPOT (time per output token) keeps rising throughout the answer.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What should be cached?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? To avoid recomputation during decoding, which tensors from past tokens should be stored?
- [ ] The final logits
- [ ] The queries (Q)
- [x] The keys and values (K, V) of every layer
- [ ] The attention weights
> <b>C.</b> A new token needs <em>its own</em> query and <em>everyone's</em> keys and values. Past queries are never used again, and attention weights change with every new token.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Cache K and V per layer; compute only the new token

::: cards grid3
### [a] Prefill
Run the prompt once and store K and V for every layer and position.

### [b] Decode step
Compute q, k and v for the new token only, append k and v to the cache, then attend q over the cache.

### [e] Exact
The logits are identical to full recomputation. The cache trades compute for <b>memory</b>.
:::

<div class="eq">KV bytes = 2 × layers × kv_heads × head_dim × bytes/element × tokens × batch</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## KV-cache memory calculator

<div class="visual">
  <div class="controls" style="margin-top:0">
    <select id="mM"><option value="32,8,128,16">8B-shaped (32 layers, 8 KV heads)</option><option value="80,8,128,140" selected>70B-shaped (80 layers, 8 KV heads)</option><option value="80,64,128,140">70B-shaped without GQA (64 KV heads)</option></select>
    <label class="ctl">Context <input type="range" id="mC" min="10" max="17" step="1" value="13"> <output id="mCo"></output></label>
    <label class="ctl">Batch <input type="range" id="mB" min="0" max="8" step="1" value="5"> <output id="mBo"></output></label>
    <div class="seg" id="mD"><button data-v="2" class="on">BF16</button><button data-v="1">FP8</button></div>
  </div>
  <div class="grid3" style="margin-top:14px">
    <div class="stat"><div class="num" id="mTok"></div><div class="lbl">KV (key-value) per token</div></div>
    <div class="stat"><div class="num" id="mTot" style="color:var(--b)"></div><div class="lbl">total KV cache</div></div>
    <div class="stat"><div class="num" id="mW"></div><div class="lbl">weights (BF16 (bfloat16, a 16-bit floating-point format with the exponent range of 32-bit floats)) for comparison</div></div>
  </div>
  <div id="mBars" style="margin-top:12px"></div>
</div>

<p class="caption">Shapes match Llama-3-8B and 70B (head_dim 128). At long context or large batch the cache exceeds the weights.</p>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Shrinking the cache: MQA, GQA and MLA

The cache scales with the number of <b>key/value heads</b>. Let several query heads share one KV head.
{: .lede}

<div class="visual">
  <div class="seg" id="gSeg"><button data-v="8">MHA (8 KV heads)</button><button data-v="2" class="on">GQA (2 KV heads)</button><button data-v="1">MQA (1 KV head)</button></div>
  <svg id="gSvg" viewBox="0 0 660 170" style="margin-top:10px" role="img" aria-label="Query heads sharing KV heads"></svg>
  <p class="readout" id="gOut"></p>
</div>

<div class="grid2" style="margin-top:12px">
  <div class="card a"><h3>GQA (Ainslie et al., EMNLP 2023)</h3><p>Between MHA (multi-head attention) and MQA (multi-query attention). Quality close to MHA at speeds comparable to MQA, and MHA checkpoints can be "uptrained" with about 5% of the original pre-training compute.</p></div>
  <div class="card c"><h3>MLA (DeepSeek-V2, 2024)</h3><p>Compresses K and V into a latent vector: <b>93.3%</b> smaller KV cache and <b>5.76×</b> max generation throughput compared with DeepSeek 67B.</p></div>
</div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why the KV cache shapes everything else

::: cards grid2
### [e] Compute becomes cheap
Each step does work for one token, so decode is dominated by <b>reading</b> weights and cache.

### [d] Memory becomes the limit
Batch size × context is capped by KV memory, so concurrency depends on the cache's size.

### [b] It drives later techniques
Paging (05), prefix sharing (05), FP8 KV (07), and moving KV between pools (09) all manage this cache.

### [c] Architecture responds
GQA, MQA and MLA are architecture changes made largely to shrink this cache.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Using a KV cache changes the model's outputs."
> It is <b>exact</b>: logits match full recomputation, because causal attention never lets past positions see the future.
:::

::: reveal myth
? "You should cache the queries too."
> Queries are needed only for the <b>current</b> token. Past queries are never reused.
:::

::: reveal myth
? "The KV cache is small compared with the weights."
> At long context it isn't: a 70B-shaped model with GQA needs <b>40 GiB per sequence at 128K tokens</b> in BF16.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

<div class="quiz">
  <p class="qq">KV bytes per token for 80 layers, 8 KV heads, head_dim 128, BF16?</p>
  <div class="opts">
  <button>A. 32 KB</button>
  <button data-ok>B. 320 KB</button>
  <button>C. 3.2 MB</button>
  <button>D. 2.6 MB</button>
  </div>
  <div class="why">2 × 80 × 8 × 128 × 2 = <b>327,680 bytes ≈ 320 KB</b>.</div>
</div>

::: quiz
? 64 query heads sharing 8 KV heads makes the cache how much smaller than MHA?
- [ ] 2×
- [x] 8×
- [ ] 64×
- [ ] No change
> <b>8×</b>: the cache scales with KV heads (64 / 8).
:::

<div class="quiz ">
  <p class="qq">Why can't you avoid the cache by just making attention faster?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Without a cache, every step reprocesses the whole prefix (quadratic total work). A faster kernel speeds up each pass but doesn't remove that redundant work.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">The KV cache stores past keys and values so each decode step computes only one new token. It is exact, but its memory (2 × layers × kv_heads × head_dim × bytes × tokens × batch) becomes the main serving constraint.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Without a cache, generating each token reprocesses the whole prefix, so total work is quadratic. The KV cache stores every layer's keys and values for past tokens; a new token computes its own q, k and v and attends over the cache, giving identical logits. Its size is 2 × layers × KV heads × head_dim × bytes × tokens × batch, about 320 KB per token for a 70B-shaped model, so at long context it limits concurrency. GQA, MQA and MLA shrink it; MLA reported a 93.3% reduction.</p></div>

<div class="recap"><div><span><b>Problem:</b> naive decoding recomputes the whole prefix every step.</span></div><div><span><b>Core idea:</b> cache K and V; exact, linear work per step, memory grows with context × batch; shrink it with GQA or MLA.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/02_kv_cache.ipynb" target="_blank" rel="noopener">02 · KV-cache decoding</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/inference/02_kv_cache.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/03_gqa_mqa.ipynb" target="_blank" rel="noopener">03 · Grouped-query attention (GQA) and multi-query attention (MQA)</a> <span style="color:var(--faint)">· 25 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/inference/03_gqa_mqa.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/04_kv_memory_calculator.ipynb" target="_blank" rel="noopener">04 · KV-cache memory calculator</a> <span style="color:var(--faint)">· 20 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/inference/04_kv_memory_calculator.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../03-batching/index.html">03 · Batching →</a> · Previous: <a href="../01-inference-workload/index.html">← 01</a> · <a href="../index.html">All decks</a></p>

<!-- slide id="s-papers" from="papers" -->
