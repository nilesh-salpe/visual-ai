---
title: SwiGLU
body:
  data-deck: SwiGLU
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
  - 'x :: normed token vector :: f'
  - 'x·W_gate → SiLU :: how much to let through :: c'
  - 'x·W_up :: what to let through :: b'
  - '⊙ then ·W_down :: back to d :: a'
  caption: 'Three matrices: gate, up, down. The element-wise product is the "gated linear unit".'
example:
  title: 'Worked example: the hidden size and the parameter budget'
  setup: d = 4,096. A ReLU FFN with hidden 4d has 2 matrices; SwiGLU has 3.
  steps:
  - 'ReLU FFN: 2 × 4,096 × 16,384 = <b>134.2M</b> parameters.'
  - 'Equal budget: hidden = ⅔ × 16,384 = 10,922.7 → LLaMA rounds up to a multiple of 256: <b>11,008</b>.'
  - 'SwiGLU params: 3 × 4,096 × 11,008 = <b>135.3M</b> (≈ the same budget).'
  - 'Llama 3 8B multiplies by 1.3 and rounds to 1,024: <b>14,336</b> = 3.5·d, spending more on the FFN.'
  result: The ⅔ rule keeps SwiGLU cost-neutral; odd hidden sizes come from rounding up to hardware-friendly multiples.
traps:
  tricks:
  - 'Hidden ≈ ⅔·4d. :: Then round up to a multiple of 256 (LLaMA) or 1,024 (Llama 3).'
  - 'FFN params = 3·d·hidden. :: About 70% of a dense Llama''s parameters.'
  - 'SiLU = Swish₁ = x·σ(x). :: hidden_act: "silu" in configs means SwiGLU.'
  traps:
  - 'Counting two matrices. :: Gated FFNs have three: gate, up, down.'
  - 'Assuming 4d hidden. :: Real models use ⅔·4d or a tuned multiplier (Llama 3: 3.5·d).'
  - 'Confusing Swish with SwiGLU. :: Swish alone (no gate) performed like ReLU in Shazeer''s table.'
papers:
- glu
- dauphin
- llama
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">The Modern LLM · 04</div>
    <h1>SwiGLU feed-forward layers</h1>
    <p class="sub">Why modern LLMs (large language models) replaced the ReLU (rectified linear unit) FFN (feed-forward network) with a gated unit that has three weight matrices, and how its odd hidden sizes (11,008, 14,336) are derived.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>The FFN holds most of a Transformer's parameters and FLOPs (floating-point operations). The 2017 ReLU FFN is a plain two-layer MLP (multilayer perceptron), and a better design at the same cost improves the whole model.</div>
      <div class="c"><b>Core idea</b>Use a <b>gated linear unit</b>: one projection, passed through Swish/SiLU (Sigmoid Linear Unit), gates another projection element by element. FFN(x) = (SiLU(xW<sub>gate</sub>) ⊙ xW<sub>up</sub>)W<sub>down</sub>. Shrink the hidden size to ⅔·4d to keep the parameter count.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Most of the model is FFN

Count the weights in one Llama 3 8B layer: attention (Wq, Wk, Wv, Wo with GQA (grouped-query attention)) vs the FFN. The FFN is where most parameters and most per-token FLOPs live, so its design matters more than any other sub-layer's.
{: .lede}

<div class="visual"><div id="pBars"></div></div>

<p class="caption">Llama 3 8B: d = 4,096, 8 K/V heads of 128, FFN hidden 14,336. Attention = 2·d² + 2·d·1,024; FFN = 3·d·14,336.</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## What a plain ReLU FFN leaves on the table

::: cards grid3
### [d] Hard zeros
ReLU outputs exactly 0 for all negative inputs, so about half the hidden units are off for any token, and their gradient is zero too.

### [b] No multiplicative interaction
Each hidden unit is a single linear function passed through a fixed nonlinearity. Units can't modulate one another, so the layer can't directly compute "feature A, but only when feature B is present".

### [c] Smoother activations help only a little
GELU (Gaussian Error Linear Unit) and Swish soften ReLU's kink. In Shazeer's ablation they barely move the result: 1.983 and 1.994 log-perplexity vs ReLU's 1.997 at 65K steps.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Same budget, three matrices

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

<div class="quiz">
  <p class="qq">A ReLU FFN with d = 768 and hidden 3,072 has 2 matrices. A SwiGLU (Swish-gated linear unit) FFN has 3. What hidden size keeps the parameter count the same?</p>
  <div class="opts">
  <button>A. 3,072</button>
  <button data-ok>B. 2,048</button>
  <button>C. 1,536</button>
  <button>D. 4,608</button>
  </div>
  <div class="why"><b>B.</b> 2 · 768 · 3,072 = 3 · 768 · h, so h = ⅔ · 3,072 = 2,048. That is exactly what Shazeer used: "we reduce the hidden layer to d_ff = 2048, so as to maintain the same parameter and operation counts as the base model."</div>
</div>

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Gate × value

<div class="grid3">
  <div class="card a"><h3>Gate path</h3><p><code>g = SiLU(x W_gate)</code>, where SiLU(z) = z·σ(z), also called Swish₁. A smooth "how much to let through" signal per hidden unit, slightly negative for negative inputs.</p></div>
  <div class="card b"><h3>Value path</h3><p><code>u = x W_up</code>: a plain linear projection with no nonlinearity. It carries what gets let through, and its sign can be either way.</p></div>
  <div class="card e"><h3>Combine and project</h3><p><code>FFN(x) = (g ⊙ u) W_down</code>. The element-wise product lets one projection modulate another. That multiplicative interaction is what a ReLU FFN lacks.</p></div>
</div>

<div class="eq">FFN<sub>SwiGLU</sub>(x) = (Swish₁(xW) ⊗ xV) W₂   (Shazeer 2020, eq. 6, biases omitted)</div>

<div class="deep"><h4>The GLU family</h4><p>GLU (Dauphin et al. 2017) uses a sigmoid gate: σ(xW) ⊗ xV. Shazeer tries several gates: <b>ReGLU</b> (ReLU), <b>GEGLU</b> (GELU), <b>SwiGLU</b> (Swish) and <b>Bilinear</b> (no nonlinearity at all). All gated versions beat the non-gated baselines in his Table 1; GEGLU and SwiGLU are best. PaLM and LLaMA chose SwiGLU. Llama's code calls the matrices <code>w1</code> (gate), <code>w3</code> (up) and <code>w2</code> (down).</p></div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## The activations, and what the gate does

Left: ReLU, GELU and SiLU as functions of one pre-activation z. Right: one SwiGLU hidden unit, the gate SiLU(a) times the value b, for a fixed value b. Drag b: the unit's output can be positive, negative or near zero depending on <b>both</b> projections.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">Value projection b <input type="range" id="gB" min="-2" max="2" step="0.1" value="1"> <output id="gBo"></output></label></div>
  <svg id="aSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Activation functions and gated unit"></svg>
  <div class="legend"><span><i style="background:var(--faint)"></i>ReLU</span><span><i style="background:var(--c)"></i>GELU</span><span><i style="background:var(--a)"></i>SiLU / Swish₁</span><span><i style="background:var(--b)"></i>SiLU(a) × b</span></div>
</div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Where 11,008 and 14,336 come from

Real models start from ⅔·4d, optionally multiply, then round <b>up</b> to a hardware-friendly multiple. Pick a model to see each step. (This is Meta's code, reproduced and tested in notebook 03.)
{: .lede}

<div class="visual">
  <div class="seg" id="hSeg"><button data-v="4096,256,0" class="on">LLaMA 7B</button><button data-v="5120,256,0">LLaMA 13B</button><button data-v="8192,256,0">LLaMA 65B</button><button data-v="4096,1024,1.3">Llama 3 8B</button></div>
  <div class="grid4" style="margin-top:14px">
    <div class="stat"><div class="num" id="h1"></div><div class="lbl">4d</div></div>
    <div class="stat"><div class="num" id="h2"></div><div class="lbl">int(⅔ · 4d)</div></div>
    <div class="stat"><div class="num" id="h3"></div><div class="lbl">× ffn_dim_multiplier</div></div>
    <div class="stat"><div class="num" id="h4" style="color:var(--e)"></div><div class="lbl">rounded up → hidden</div></div>
  </div>
  <div id="hBars" style="margin-top:12px"></div>
</div>

<p class="caption">Values from Meta's released configs: multiple_of 256 for LLaMA 1, and multiple_of 1024 with ffn_dim_multiplier 1.3 for Llama 3 8B.</p>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works: the evidence, and the honest answer

<div class="visual">
  <div id="sBars"></div>
  <p class="caption">Shazeer 2020, Table 1: held-out log-perplexity on C4 for T5-base after 524,288 steps (lower is better). Every variant has the same parameters and operations.</p>
</div>

<div class="grid2" style="margin-top:12px">
  <div class="card e"><h3>Same cost, consistently better</h3><p>Gated variants win at both training lengths and also on downstream GLUE (General Language Understanding Evaluation benchmark) and SuperGLUE fine-tuning in the same paper. That consistency is why PaLM and LLaMA adopted SwiGLU.</p></div>
  <div class="card b"><h3>Why, exactly? Nobody fully knows</h3><p>The paper's conclusion: "We offer no explanation as to why these architectures seem to work; we attribute their success, as all else, to divine benevolence." The usual intuition is that multiplicative gating adds expressiveness, but this is empirical.</p></div>
</div>

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "SwiGLU makes the FFN bigger."
> At the ⅔·4d hidden size it has the <b>same</b> parameters and FLOPs as the 4d ReLU FFN. Llama 3's 1.3 multiplier is a separate decision to spend more parameters there.
:::

::: reveal myth
? "Swish and SwiGLU are the same thing."
> Swish (SiLU) is the activation function. SwiGLU is the whole <b>gated</b> unit: Swish of one projection times another projection, then a down projection. FFN<sub>Swish</sub> alone scored 1.994, about the same as ReLU.
:::

::: reveal myth
? "Gating was introduced to save compute."
> It costs the same compute. It was introduced for <b>quality</b>: lower perplexity at equal parameters.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? How many weight matrices does a SwiGLU FFN have?
- [ ] 1
- [ ] 2
- [x] 3
- [ ] 4
> <b>3</b>: gate, up and down.
:::

<div class="quiz ">
  <p class="qq">Compute LLaMA-7B's FFN hidden size from d = 4,096 and multiple_of = 256.</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">4d = 16,384 → int(⅔ · 16,384) = 10,922 → round up to a multiple of 256 → <b>11,008</b>.</div>
</div>

<div class="quiz ">
  <p class="qq">Write the SwiGLU FFN and say which part is the gate.</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">(SiLU(xW_gate) ⊙ xW_up)W_down. SiLU(xW_gate) is the gate; xW_up is the value it scales.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">SwiGLU gates one projection with SiLU of another: three matrices at ⅔ the width, same cost as the ReLU FFN, consistently lower perplexity.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>The FFN is most of a Transformer's parameters. The 2017 version is a ReLU MLP with hidden size 4d. SwiGLU computes SiLU of x times W-gate, multiplies that element-wise by x times W-up, and projects back down with W-down. The gate lets one projection modulate the other. Three matrices instead of two means the hidden size drops to two-thirds of 4d to keep parameters equal, which real models round up to hardware-friendly multiples, giving 11,008 for LLaMA-7B and 14,336 for Llama 3 8B. Shazeer's ablation shows lower perplexity at the same cost, and PaLM and LLaMA adopted it, although nobody has a full explanation of why it works.</p></div>

<div class="recap"><div><span><b>Problem:</b> the FFN dominates parameters; the ReLU MLP is not the best use of them.</span></div><div><span><b>Core idea:</b> (SiLU(xW_gate) ⊙ xW_up)W_down; hidden ≈ ⅔·4d keeps cost equal.</span></div><div><span><b>Evidence:</b> Shazeer Table 1: 1.677 → 1.636 log-ppl at the same parameters and operations.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/architecture/03_swiglu.ipynb" target="_blank" rel="noopener">03 · SwiGLU feed-forward layers</a> <span style="color:var(--faint)">· 30 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/architecture/03_swiglu.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../05-attention-variants/index.html">05 · MQA, GQA and MLA →</a> · Previous: <a href="../03-rope/index.html">← 03</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Shazeer 2020, "GLU Variants Improve Transformer" (eq. 5–6, Table 1); Dauphin et al. 2017 (GLU); Touvron et al. 2023 (LLaMA §2.2); Chowdhery et al. 2022 (PaLM §2); Meta llama3 model.py and llama-models sku_list (multiple_of, ffn_dim_multiplier).</p>

<!-- slide id="s-papers" from="papers" -->
