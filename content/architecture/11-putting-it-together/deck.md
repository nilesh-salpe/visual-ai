---
title: Putting It Together
body:
  data-deck: Putting it together
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
  - 'config.json :: d, layers, heads, KV heads,

    hidden, vocab, rope_theta :: f'
  - 'block recipe :: norms, attention type,

    FFN type, position :: c'
  - 'size :: parameters, KV per token,

    FLOPs per token :: a'
  - 'serving plan :: GPUs, TP degree,

    context × batch :: e'
  caption: From a model card to a hardware estimate in four steps.
example:
  title: 'Worked example: sizing Llama 3 70B from its config'
  setup: Vocabulary 128,256; d = 8,192; 80 layers; 64 query heads, 8 KV heads (head dim 128); FFN 28,672; untied embeddings.
  steps:
  - 'Parameters: <b>70.55B</b> (same formula as notebook 10).'
  - 'Weights: BF16 <b>141 GB</b>; FP8 71 GB → at least 2 × 80 GB GPUs in BF16.'
  - 'KV per token: 2 × 80 × 8 × 128 × 2 = <b>320 KiB</b>; 32 sequences at 8K = 80 GiB.'
  - Forward FLOPs per token ≈ 2 × parameters = <b>141 GFLOP</b>.
  result: Weights pick the minimum GPU count; KV per token decides how many concurrent long-context users fit; FLOPs per token set prefill speed.
traps:
  tricks:
  - 'FLOPs/token ≈ 2N. :: Plus the attention term for long contexts.'
  - 'Memory = weights + KV + activations. :: KV usually decides concurrency.'
  - 'Check rope_theta and rope_scaling. :: They tell you the trained and supported context.'
  traps:
  - 'Parameter count = serving cost. :: KV per token and active (MoE) parameters matter as much.'
  - 'Same size, same architecture. :: Llama 2 7B vs Llama 3 8B differ in KV heads, FFN width, vocabulary and RoPE base.'
  - 'Treating FlashAttention as architecture. :: It is a kernel; outputs are the same.'
papers:
- llama
- llama2
- llama3
- mistral
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">The Modern LLM · 11</div>
    <h1>Putting it together</h1>
    <p class="sub">Build a modern decoder from its parts, compute its size from a config, and practise naming the design choices behind real models.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Knowing each component separately isn't enough. You need to read a model description, reconstruct the block, estimate its size and costs, and explain why each choice was made.</div>
      <div class="c"><b>Core idea</b>A modern LLM (large language model) layer = <b>RMSNorm (root-mean-square normalization) → attention (GQA (grouped-query attention) + RoPE (rotary position embedding), FlashAttention kernel) → residual → RMSNorm → SwiGLU (Swish-gated linear unit) FFN (or MoE (Mixture of Experts)) → residual</b>, stacked L times between a token embedding and a final RMSNorm + output head.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## The whole block on one screen

One Llama 3 layer, with each part labelled by the problem it solves and the deck that explains it. Hover or tap a part.
{: .lede}

<div class="visual">
  <svg id="bSvg" viewBox="0 0 660 330" role="img" aria-label="Modern decoder block"></svg>
  <div class="infobox" id="bInfo" style="background:var(--panel-2);border-radius:10px;padding:12px 14px;margin-top:10px;font-size:14px;color:var(--muted)">Tap a part of the block.</div>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Where people get stuck

::: cards grid3
### [d] Mixing up what is cached
K and V (after RoPE) are cached, Q isn't. With GQA only the K/V heads are cached. With MLA (multi-head latent attention) it's the latent plus the RoPE key.

### [b] Counting parameters wrongly
Forgetting that GQA shrinks Wk and Wv, that SwiGLU has three matrices, or that untied embeddings count twice.

### [c] Confusing kernel and architecture
FlashAttention doesn't change the model; it computes the same function faster. RoPE scaling and sliding windows <b>do</b> change what the model computes.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Name the recipe

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

<div class="quiz">
  <p class="qq">A config says: num_attention_heads 32, num_key_value_heads 8, hidden_act "silu", intermediate_size 14336, rope_theta 1000000, sliding_window 4096. Which features does this model use?</p>
  <div class="opts">
  <button>A. MHA, GELU, learned positions</button>
  <button data-ok>B. GQA, SwiGLU, RoPE (large base), sliding-window attention</button>
  <button>C. MQA, ReLU, ALiBi</button>
  <button>D. MLA, SwiGLU, NTK scaling</button>
  </div>
  <div class="why"><b>B.</b> 8 K/V heads for 32 query heads is GQA; silu with an intermediate size is a SwiGLU FFN; rope_theta is the RoPE base; sliding_window means SWA (sliding-window attention). (A hypothetical config: always read the actual model card.)</div>
</div>

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## The checklist for any model description

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Question</th><th>Where to look</th><th>Typical modern answer</th><th>Deck</th></tr>
  <tr><td>Stack and mask?</td><td>architecture name</td><td>decoder-only, causal (+ document mask for packing)</td><td>06</td></tr>
  <tr><td>Norm placement and type?</td><td><code>rms_norm_eps</code></td><td>pre-norm RMSNorm + final norm</td><td>02</td></tr>
  <tr><td>Position encoding?</td><td><code>rope_theta</code>, <code>rope_scaling</code></td><td>RoPE, base 10K–1M, maybe YaRN (Yet another rotary-position-embedding extension method)/linear scaling</td><td>03, 07</td></tr>
  <tr><td>K/V sharing?</td><td><code>num_key_value_heads</code></td><td>GQA with 8 K/V heads; MLA in DeepSeek</td><td>05</td></tr>
  <tr><td>FFN?</td><td><code>hidden_act</code>, <code>intermediate_size</code></td><td>SwiGLU, hidden ≈ 2.7–3.5·d</td><td>04</td></tr>
  <tr><td>Sparse?</td><td><code>num_local_experts</code>, <code>num_experts_per_tok</code></td><td>dense, or MoE with top-k routing</td><td>10</td></tr>
  <tr><td>Long-context mechanism?</td><td><code>sliding_window</code>, context length</td><td>long-context training; optional SWA</td><td>07, 08</td></tr>
</table></div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Size calculator

Pick a preset or move the sliders. Parameters are counted exactly as in notebook 10 (Llama 2 7B gives 6,738,415,616; Llama 3 8B gives 8,030,261,248). KV (key-value) cache is per token in BF16 (bfloat16, a 16-bit floating-point format with the exponent range of 32-bit floats). Forward FLOPs (floating-point operations) per token ≈ 2 × parameters, ignoring attention over the context.
{: .lede}

<div class="visual">
  <div class="seg" id="zSeg"><button data-v="32000,4096,32,32,32,11008" >Llama 2 7B</button><button data-v="128256,4096,32,32,8,14336" class="on">Llama 3 8B</button><button data-v="32000,4096,32,32,8,14336">Mistral 7B</button><button data-v="128256,8192,80,64,8,28672">Llama 3 70B</button></div>
  <div class="controls">
    <label class="ctl">d <input type="range" id="zD" min="1024" max="16384" step="512" value="4096"> <output id="zDo"></output></label>
    <label class="ctl">layers <input type="range" id="zL" min="8" max="128" step="1" value="32"> <output id="zLo"></output></label>
    <label class="ctl">K/V heads <input type="range" id="zK" min="1" max="64" step="1" value="8"> <output id="zKo"></output></label>
    <label class="ctl">FFN hidden <input type="range" id="zH" min="2048" max="57344" step="256" value="14336"> <output id="zHo"></output></label>
  </div>
  <div class="grid4" style="margin-top:12px">
    <div class="stat"><div class="num" id="zP" style="color:var(--a)"></div><div class="lbl">parameters</div></div>
    <div class="stat"><div class="num" id="zKV"></div><div class="lbl">KV cache / token</div></div>
    <div class="stat"><div class="num" id="zF"></div><div class="lbl">forward FLOPs / token (≈2N)</div></div>
    <div class="stat"><div class="num" id="zW"></div><div class="lbl">BF16 weights</div></div>
  </div>
  <div id="zBars" style="margin-top:12px"></div>
</div>

<p class="caption">Head dimension is fixed at 128 for the calculator (true for all four presets). Query heads = d / 128. Memory units are binary (KB = KiB, GB = GiB).</p>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Follow one token through the stack

<div class="grid3">
  <div class="card a"><h3>1. Embed</h3><p>Token id → row of the embedding table (d numbers). No position vector is added.</p></div>
  <div class="card b"><h3>2. Attention sub-layer</h3><p>RMSNorm → q, k, v projections (fewer K/V heads) → RoPE on q and k → append k, v to the KV cache → attention over the cache with FlashAttention → Wo → add to the stream.</p></div>
  <div class="card c"><h3>3. FFN sub-layer</h3><p>RMSNorm → SwiGLU (or route to top-k experts) → add to the stream.</p></div>
  <div class="card e"><h3>4. Repeat L times</h3><p>The residual stream accumulates every layer's contribution; nothing renormalizes it along the way.</p></div>
  <div class="card a"><h3>5. Output</h3><p>Final RMSNorm → output head (vocab logits) → sample the next token, which becomes the next input.</p></div>
  <div class="card b"><h3>6. Long inputs</h3><p>Positions beyond the trained range need RoPE scaling or long-context training; a sliding window caps the cache.</p></div>
</div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why the pieces fit together

::: cards grid2
### [a] They solve different problems
Stability (pre-norm), cost per op (RMSNorm), position (RoPE), FFN quality (SwiGLU), serving memory (GQA/MLA), memory traffic (FlashAttention), parameters per FLOP (MoE). Each fix is local, so none conflicts with the others.

### [e] The few interactions are known
RoPE plus MLA needs decoupled RoPE. RoPE plus long context needs scaling. MoE plus GQA is fine (Mixtral). Pre-norm needs a final norm.

### [b] Inference shaped the design
The KV cache explains GQA, MLA, sliding windows and why decoder-only won. Active parameters explain MoE. Memory traffic explains FlashAttention.

### [c] What comes next
Training these models at scale (data, scaling laws, parallelism) and aligning them (post-training) are the next topics in this guide.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Parameter count tells you serving cost."
> Serving cost also depends on the KV cache (set by K/V heads, layers and context length) and, for MoE, on <b>active</b> rather than total parameters.
:::

::: reveal myth
? "Two models with the same parameters have the same architecture."
> Llama 2 7B and Llama 3 8B are similar in size but differ in K/V heads (32 vs 8), FFN width (11,008 vs 14,336), vocabulary (32K vs 128K) and RoPE base (10K vs 500K).
:::

::: reveal myth
? "FlashAttention is part of the model architecture."
> It is a <b>kernel</b>. Swapping it for standard attention gives the same outputs, only slower and using more memory.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

<div class="quiz ">
  <p class="qq">Write the two residual updates of a Llama block, naming every component.</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">h = x + Wo·FlashAttn(RoPE(Wq·RMSNorm(x)), RoPE(Wk·RMSNorm(x)), Wv·RMSNorm(x)) with GQA K/V heads; out = h + W_down(SiLU(W_gate·RMSNorm(h)) ⊙ W_up·RMSNorm(h)).</div>
</div>

::: quiz
? Llama 3 8B: about what share of parameters is in the FFNs?
- [ ] ~15%
- [ ] ~40%
- [x] ~70%
- [ ] ~95%
> <b>~70%</b> (5.64B of 8.03B). Attention ~17% thanks to GQA, embeddings + head ~13% because of the 128K vocabulary.
:::

<div class="quiz ">
  <p class="qq">KV cache per token for Llama 3 8B in BF16?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">2 (K and V) × 32 layers × 8 K/V heads × 128 dims × 2 bytes = <b>131,072 bytes = 128 KiB</b>.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">A modern LLM layer is RMSNorm → GQA attention with RoPE → residual → RMSNorm → SwiGLU (or MoE) → residual, computed with FlashAttention, and its size and cache follow directly from the config.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Every modern open LLM is the same template. A token embedding with no position vector; then L identical blocks, each a pre-norm RMSNorm, grouped-query attention with RoPE on queries and keys computed by a FlashAttention kernel, a residual add, another RMSNorm, a SwiGLU feed-forward or a set of routed experts, and another residual add; then a final RMSNorm and the output head. Parameters, KV cache per token and FLOPs follow directly from the config: Llama 3 8B has 8.03 billion parameters, 70% of them in FFNs, and a 128 KiB KV cache per token. Each design choice maps to a specific scaling problem.</p></div>

<div class="recap"><div><span><b>Template:</b> embed → L × [RMSNorm, GQA+RoPE, +, RMSNorm, SwiGLU/MoE, +] → RMSNorm → head.</span></div><div><span><b>Sizes:</b> Llama 3 8B: 8.03B params, ~70% FFN, 128 KiB KV per token.</span></div><div><span><b>Reading configs:</b> num_key_value_heads, rope_theta, intermediate_size, hidden_act, sliding_window, experts.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/architecture/10_llama_block.ipynb" target="_blank" rel="noopener">10 · Build a Llama-style decoder block and count its parameters</a> <span style="color:var(--faint)">· 50 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/architecture/10_llama_block.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">You've finished the series. <a href="../../build-it/index.html">See all Build-it notebooks →</a> · Previous: <a href="../10-mixture-of-experts/index.html">← 10</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Touvron et al. 2023 (LLaMA, Llama 2); Llama Team 2024 (Llama 3 Table 3); Meta-Llama-3-8B config.json; Jiang et al. 2023 (Mistral 7B Table 1); Kaplan et al. 2020 (≈2N FLOPs per token for the forward pass).</p>

<!-- slide id="s-papers" from="papers" -->
