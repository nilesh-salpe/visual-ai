---
title: What Changed Since 2017
body:
  data-deck: What changed since 2017
  data-home: ../index.html
  data-home-label: Architecture
styles:
- ../../shared/deck.css
- ../../shared/learn.css
css: |-
  .cfg{font:500 13px/1.75 "JetBrains Mono",monospace;background:var(--panel-2);border-radius:10px;padding:12px 14px;margin:0;overflow-x:auto}.cfg span{cursor:pointer;border-radius:4px;padding:1px 3px}.cfg span:hover{background:var(--a-soft)}.cfg span.on{background:var(--b-soft);outline:1px solid var(--b)}
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'token embedding :: no position vector :: f'
  - 'RMSNorm :: pre-norm :: e'
  - 'GQA attention :: RoPE on q, k

    FlashAttention kernel :: c'
  - 'RMSNorm :: pre-norm :: e'
  - 'SwiGLU FFN :: or MoE experts :: a'
  - 'final norm + head :: logits :: f'
  loop: '4 -> 1 :: × L layers, with a residual add after attention and after the FFN'
  caption: 'A Llama-style decoder: the 2017 skeleton with the seven swaps in place.'
example:
  title: 'Worked example: where Llama 3 8B''s parameters go'
  setup: 'From the published config: vocabulary 128,256; d = 4,096; 32 layers; 32 query heads and 8 KV heads of 128; SwiGLU hidden 14,336; untied embeddings.'
  steps:
  - 'Embeddings + output head: 2 × 128,256 × 4,096 = <b>1.05B</b>.'
  - 'Attention per layer: W_q and W_o (4,096²) + W_k and W_v (4,096 × 1,024) = 41.9M; × 32 = <b>1.34B</b>.'
  - 'SwiGLU per layer: 3 × 4,096 × 14,336 = 176.2M; × 32 = <b>5.64B</b>.'
  - Norm gains add 266,240. Total = <b>8,030,261,248</b>.
  result: 70% FFN, 17% attention (small thanks to GQA), 13% embeddings. Reproducing 8.03B from config.json is a quick check that you understand every component.
traps:
  tricks:
  - 'Read the config, not the name. :: num_key_value_heads, rope_theta, intermediate_size, hidden_act and tie_word_embeddings tell you the recipe.'
  - 'Count per layer. :: Attention ≈ 2d² + 2d·n_kv·d_head; SwiGLU = 3·d·hidden; then × layers + embeddings.'
  - 'Kernel ≠ architecture. :: FlashAttention computes the same function; RoPE scaling and sliding windows change it.'
  traps:
  - 'Assuming every model uses every swap. :: Llama 2 7B has no GQA; Mixtral uses dense attention over 32K; check each model.'
  - 'Forgetting untied embeddings. :: With a 128K vocabulary, input embedding and output head are ~1B parameters together.'
  - 'Crediting the wrong source. :: LLaMA credits pre-norm to GPT-3, SwiGLU to PaLM and rotary embeddings to GPT-Neo.'
papers:
- vaswani
- llama
- llama3
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">The Modern LLM · 01</div>
    <h1>What changed since 2017</h1>
    <p class="sub">The 2017 Transformer and a 2024 Llama block side by side: seven changes, what problem each one solved, and where each is explained in this guide.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>The 2017 Transformer was built for translation on 8 GPUs (graphics processing units). Scaling it to hundreds of billions of parameters, long contexts and millions of users exposed problems in training stability, position handling, FFN (feed-forward network) quality, inference memory and attention speed.</div>
      <div class="c"><b>Core idea</b>Modern LLMs (large language models) keep the 2017 skeleton (attention + FFN + residuals) and swap specific parts: <b>pre-norm RMSNorm (root-mean-square normalization)</b>, <b>RoPE (rotary position embedding)</b>, <b>SwiGLU (Swish-gated linear unit)</b>, <b>GQA (grouped-query attention)/MLA (multi-head latent attention)</b>, a <b>decoder-only</b> stack, <b>long-context</b> tricks and <b>FlashAttention</b>, with <b>MoE (Mixture of Experts)</b> for the largest models.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Same skeleton, different parts

Pick a change to see which part of the block it replaced. Left: one decoder layer as described in 2017. Right: a Llama 3 layer. Both are a stack of identical layers with residual connections. What changed is inside the boxes.
{: .lede}

<div class="visual">
  <div class="seg" id="chSeg" style="flex-wrap:wrap"><button data-v="normpos" class="on">Norm placement</button><button data-v="normtype">Norm type</button><button data-v="pos">Position</button><button data-v="ffn">FFN</button><button data-v="heads">K/V heads</button><button data-v="family">Stack</button><button data-v="kernel">Attention kernel</button></div>
  <svg id="cmpSvg" viewBox="0 0 660 340" style="margin-top:10px" role="img" aria-label="2017 block vs Llama 3 block"></svg>
  <div class="infobox" id="chInfo" style="background:var(--panel-2);border-radius:10px;padding:12px 14px;margin-top:10px;font-size:14px;color:var(--muted)"></div>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## What broke when the 2017 design was scaled up

::: cards grid3
### [d] Training stability
Post-norm (a LayerNorm after each residual add) gives large gradients near the output at initialization. It needs a carefully tuned learning-rate warm-up, and deeper stacks make this worse (Xiong et al., 2020).

### [b] Position handling
Sinusoidal or learned vectors are <b>added</b> to the token embedding, so position is mixed into the content. Attention sees relative distance only indirectly, and learned positions don't exist beyond the trained length.

### [c] Inference memory
Every head keeps its own keys and values. During generation that KV (key-value) cache, not compute, limits batch size and context (Inference deck 02).

### [a] FFN quality per parameter
The ReLU (rectified linear unit) FFN holds about two thirds of a layer's weights. A gated variant (SwiGLU) gets lower perplexity at the same parameter count (Shazeer, 2020).

### [e] Attention is memory-bound
A plain implementation writes the N×N score matrix to GPU memory and reads it back. At long N that traffic, not FLOPs (floating-point operations), sets the runtime (Dao et al., 2022).

### [d] Two stacks for one job
An encoder-decoder needs separate inputs, targets and cross-attention. For "continue this text" a single causal stack is simpler, and it learns from every token.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Which change is mostly about serving cost?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Which of these changes mainly reduces memory at inference time, rather than improving training quality?
- [ ] RMSNorm instead of LayerNorm
- [ ] SwiGLU instead of ReLU
- [x] Grouped-query attention (fewer K/V heads)
- [ ] RoPE instead of sinusoidal embeddings
> <b>C.</b> GQA lets several query heads share one key/value head, so the KV cache shrinks by the sharing factor (8× for Llama 3 with 64 query heads per 8 KV heads in 70B). PaLM reported MQA (multi-query attention) as roughly neutral for quality and training speed but a significant saving at decoding time. The others mainly help training speed, stability or quality.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## The seven swaps, in one table

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Part</th><th>2017</th><th>Modern default</th><th>Problem it solves</th><th>Deck</th></tr>
  <tr><td>Norm placement</td><td>Post-norm: Norm(x + F(x))</td><td><b>Pre-norm</b>: x + F(Norm(x)), plus a final norm</td><td>Stable training without warm-up, even when deep</td><td>02</td></tr>
  <tr><td>Norm type</td><td>LayerNorm (centre + scale)</td><td><b>RMSNorm</b> (scale only)</td><td>Fewer operations, same quality</td><td>02</td></tr>
  <tr><td>Position</td><td>Sinusoidal vector added at the input</td><td><b>RoPE</b>: rotate q and k in every layer</td><td>Attention depends on relative distance; nothing added to the residual stream</td><td>03, 07</td></tr>
  <tr><td>FFN</td><td>ReLU, hidden 4d, 2 matrices</td><td><b>SwiGLU</b>, hidden ≈ ⅔·4d, 3 matrices</td><td>Better perplexity for the same parameters</td><td>04</td></tr>
  <tr><td>K/V heads</td><td>One K/V per query head</td><td><b>GQA</b> (or MQA, or MLA)</td><td>Smaller KV cache, faster decoding</td><td>05</td></tr>
  <tr><td>Stack</td><td>Encoder-decoder</td><td><b>Decoder-only</b>, causal mask</td><td>One stack, every token is a training target, natural fit for chat and KV caching</td><td>06</td></tr>
  <tr><td>Attention kernel</td><td>Materialize the N×N matrix</td><td><b>FlashAttention</b> (tiled, exact)</td><td>Memory linear in N, far less HBM (high-bandwidth memory) traffic</td><td>09</td></tr>
</table></div>

<div class="deep"><h4>Also new, but not in every model</h4><ul><li><b>Long context</b>: RoPE scaling (PI (Position Interpolation), NTK-aware (NTK = neural tangent kernel), YaRN (Yet another rotary-position-embedding extension method)), larger RoPE base, sliding-window attention. Decks 07 and 08.</li><li><b>Mixture of Experts</b>: replace the FFN with many expert FFNs and a router. Mixtral and DeepSeek-V2. Deck 10.</li><li><b>No biases</b> in linear layers and norms (PaLM: "this results in increased training stability for large models"). Llama's config also has <code>attention_bias: false</code>.</li></ul></div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## How the recipe accumulated, model by model

No single paper introduced the modern block. Each model adopted a few changes, and the combination that LLaMA published in 2023 became the default. Only details stated in each paper are listed. A dot means the paper doesn't say.
{: .lede}

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Model</th><th>Norm</th><th>Position</th><th>FFN</th><th>Attention</th><th>Notable</th></tr>
  <tr><td>Transformer (2017)</td><td>post-norm LayerNorm</td><td>sinusoidal, added</td><td>ReLU</td><td>MHA (multi-head attention)</td><td>encoder-decoder</td></tr>
  <tr><td>GPT-2 (2019)</td><td><b>pre-norm</b> + final LN (layer normalization)</td><td>learned, added</td><td>·</td><td>MHA</td><td>decoder-only, 1024 context</td></tr>
  <tr><td>PaLM (2022)</td><td>pre-norm, no biases</td><td><b>RoPE</b></td><td><b>SwiGLU</b></td><td><b>MQA</b></td><td>parallel attention + MLP (multilayer perceptron), 256K vocab</td></tr>
  <tr><td>LLaMA (2023)</td><td>pre-norm <b>RMSNorm</b></td><td>RoPE</td><td>SwiGLU, ⅔·4d</td><td>MHA</td><td>the recipe that stuck</td></tr>
  <tr><td>Llama 2 (2023)</td><td>pre-norm RMSNorm</td><td>RoPE</td><td>SwiGLU</td><td><b>GQA</b> (34B, 70B)</td><td>4K context</td></tr>
  <tr><td>Mistral 7B (2023)</td><td>·</td><td>RoPE</td><td>·</td><td>GQA (8 KV heads)</td><td><b>sliding window</b> 4096</td></tr>
  <tr><td>Mixtral (2024)</td><td>as Mistral 7B</td><td>RoPE</td><td>SwiGLU <b>experts</b></td><td>GQA</td><td><b>MoE</b> 8 experts, top-2; dense 32K context</td></tr>
  <tr><td>DeepSeek-V2 (2024)</td><td>·</td><td>decoupled RoPE</td><td>DeepSeekMoE</td><td><b>MLA</b></td><td>236B total, 21B active</td></tr>
  <tr><td>Llama 3 (2024)</td><td>pre-norm RMSNorm</td><td>RoPE, base <b>500,000</b></td><td>SwiGLU</td><td>GQA, 8 KV heads (all sizes)</td><td>128K vocab, document mask</td></tr>
</table></div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Read a real config.json

These fields are from the published config.json of Meta-Llama-3-8B (a subset; the file also has token ids, dtype and similar). Click any field to see which concept it controls. Being able to read a config like this and explain each line is a quick test of the whole guide.
{: .lede}

<div class="visual">
  <div class="grid2" style="align-items:start">
    <pre class="cfg" id="cfg"></pre>
    <div class="infobox" id="cfgInfo" style="background:var(--panel-2);border-radius:10px;padding:12px 14px;font-size:14px;color:var(--muted)">Click a field on the left.</div>
  </div>
</div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why these changes stuck

::: cards grid2
### [a] They are cheap to adopt
Each swap changes one sub-component and keeps the residual stream and the attention + FFN layout. They compose: you can take all of them at once, as LLaMA did.

### [e] They target scale problems
Pre-norm and RMSNorm address stability and speed at depth. GQA and MLA address serving memory. FlashAttention and RoPE scaling address long sequences. These problems only appeared at scale.

### [b] They were tested in public
Shazeer's GLU (gated linear unit) ablation, Xiong's norm analysis, RoFormer and the GQA uptraining study each report controlled comparisons, and open model families then confirmed the combination.

### [c] Inference shaped training
Several changes (MQA/GQA/MLA, sliding windows, MoE's active parameters) exist mainly because a model is served billions of times after it is trained once.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Modern LLMs use a completely different architecture from the 2017 Transformer."
> The skeleton is the same: token embeddings, a stack of attention + FFN layers with residual connections, and a softmax output. The changes are <b>targeted swaps</b> inside that skeleton.
:::

::: reveal myth
? "Each change was invented by the model that made it famous."
> Mostly not. LLaMA credits pre-normalization to GPT-3, SwiGLU to PaLM (and Shazeer 2020), and rotary embeddings to GPT-Neo (and Su et al. 2021). Its contribution was the combination and the open release.
:::

::: reveal myth
? "These changes are mostly about accuracy."
> Many are about <b>cost</b>: RMSNorm (speed), GQA/MLA (KV memory), FlashAttention (memory traffic), MoE (FLOPs per token). Quality had to stay roughly the same; the cost went down.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? In a pre-norm block, where is the normalization applied?
- [ ] After the residual addition
- [x] To the input of each sub-layer, inside the residual branch
- [ ] Only once, at the end of the network
- [ ] To the attention weights
> <b>B.</b> x + F(Norm(x)). The residual path itself is never normalized, so a final norm is added before the output head.
:::

<div class="quiz ">
  <p class="qq">Llama 3 8B has num_attention_heads 32 and num_key_value_heads 8. What does that mean, and what does it buy?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">It uses <b>GQA</b>: groups of 4 query heads share one key/value head. The KV cache is 4× smaller than with full multi-head attention, which means more concurrent sequences or longer contexts per GPU.</div>
</div>

<div class="quiz ">
  <p class="qq">Name the parts of a Llama block that differ from the 2017 block, and one reason for each.</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Pre-norm (stable without warm-up), RMSNorm (cheaper), RoPE (relative positions; no added vector), SwiGLU (better quality per parameter), GQA (smaller KV cache), decoder-only (one stack, every token trains). FlashAttention is the kernel used to compute the same attention faster.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">A modern LLM is the 2017 Transformer with seven targeted swaps: pre-norm, RMSNorm, RoPE, SwiGLU, shared or compressed K/V heads, a decoder-only stack and an IO-aware (IO = input/output, memory reads and writes) attention kernel.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>The skeleton hasn't changed: attention plus FFN layers with residual connections. What changed are the parts that broke at scale. Normalization moved inside the residual branch and became RMSNorm, for stability and speed. Positions became rotations of q and k (RoPE), so attention depends on relative distance. The FFN became a gated SwiGLU. Query heads now share key/value heads (GQA) to shrink the KV cache. Everything runs as a single causal decoder, computed with FlashAttention. Long-context tricks and Mixture-of-Experts sit on top for the models that need them.</p></div>

<div class="recap"><div><span><b>Problem:</b> the 2017 block had stability, position, memory and speed problems at scale.</span></div><div><span><b>Core idea:</b> keep the skeleton; swap norm, position, FFN, K/V heads, stack type and kernel.</span></div><div><span><b>Read configs:</b> every field in a config.json maps to one of these decisions.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/architecture/10_llama_block.ipynb" target="_blank" rel="noopener">10 · Build a Llama-style decoder block and count its parameters</a> <span style="color:var(--faint)">· 50 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/architecture/10_llama_block.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../02-normalization/index.html">02 · Pre-norm and RMSNorm →</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Vaswani et al. 2017; Radford et al. 2019 (GPT-2 §2.3); Chowdhery et al. 2022 (PaLM §2); Touvron et al. 2023 (LLaMA §2.2; Llama 2 Table 1); Jiang et al. 2023 (Mistral 7B); Jiang et al. 2024 (Mixtral); DeepSeek-AI 2024 (DeepSeek-V2); Llama Team 2024 (Llama 3 §3.2, Table 3); Meta-Llama-3-8B config.json.</p>

<!-- slide id="s-papers" from="papers" -->
