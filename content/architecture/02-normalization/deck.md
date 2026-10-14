---
title: Pre-norm and RMSNorm
body:
  data-deck: Pre-norm and RMSNorm
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
  - 'x (residual stream) :: never normalized :: f'
  - 'RMSNorm :: x / rms(x) · g :: e'
  - 'sub-layer F :: attention or FFN :: c'
  - 'x + F(·) :: identity path kept :: a'
  loop: '3 -> 0 :: repeat per sub-layer; one final RMSNorm before the output head'
  caption: 'Pre-norm: only the copy going into F is normalized.'
example:
  title: 'Worked example: LayerNorm vs RMSNorm on one token'
  setup: A token with 4 features x = [1.2, -0.4, 2.1, 0.3] (gain 1, bias 0).
  steps:
  - 'LayerNorm: mean = 0.800, std = 0.941 → output = (x − mean)/std = <b>[0.43, -1.28, 1.38, -0.53]</b>.'
  - 'RMSNorm: rms = √(mean(x²)) = 1.235 → output = x/rms = <b>[0.97, -0.32, 1.70, 0.24]</b>.'
  - 'Add 1 to every feature: LayerNorm''s output is unchanged; RMSNorm''s becomes [1.08, 0.30, 1.53, 0.64].'
  - 'Multiply every feature by 10: both outputs are unchanged (re-scaling invariance).'
  result: RMSNorm keeps scale invariance and drops shift invariance, with one reduction (sum of squares) instead of two (mean and variance).
traps:
  tricks:
  - 'Pre-norm = x + F(Norm(x)). :: Post-norm = Norm(x + F(x)).'
  - 'Pre-norm needs a final norm. :: The residual stream grows with depth and is never normalized on the way.'
  - 'RMSNorm = x / √(mean(x²) + ε) · g. :: No mean, no bias.'
  traps:
  - 'Normalizing across the batch. :: Layer and RMS norms work per token over features, unlike BatchNorm.'
  - 'Dropping warm-up with post-norm. :: Post-norm''s large gradients near the output at initialization need warm-up.'
  - 'Treating ε as irrelevant. :: Configs set it (Llama 3: 1e-5); a mismatch changes outputs when porting weights.'
papers:
- xiong
- rmsnorm
- gpt2
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">The Modern LLM · 02</div>
    <h1>Pre-norm and RMSNorm</h1>
    <p class="sub">Where the normalization sits in a residual block decides whether a deep Transformer trains smoothly. And most of what LayerNorm computes turns out to be unnecessary.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Deep post-norm Transformers need a carefully tuned learning-rate warm-up or they diverge, and LayerNorm itself costs time on every token in every layer.</div>
      <div class="c"><b>Core idea</b><b>Pre-norm</b>: normalize the input of each sub-layer, x + F(Norm(x)), so the residual path is a clean identity. <b>RMSNorm (root-mean-square normalization)</b>: skip the mean subtraction and just divide by the root mean square.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Two ways to wire the same block

A Transformer layer is a sub-layer F (attention or FFN (feed-forward network)) plus a residual connection plus a normalization. The 2017 paper puts the norm <b>after</b> the addition. Switch between the two wirings and follow the main path (thick line) from input to output.
{: .lede}

<div class="visual">
  <div class="seg" id="wSeg"><button data-v="post" class="on">Post-norm (2017)</button><button data-v="pre">Pre-norm (GPT-2 onward)</button></div>
  <svg id="wSvg" viewBox="0 0 660 200" style="margin-top:10px" role="img" aria-label="Residual block wiring"></svg>
  <p class="readout" id="wOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## What goes wrong with post-norm

::: cards grid3
### [d] Large gradients near the output
Xiong et al. (2020) show with mean-field analysis that at initialization the gradients of parameters near the output layer are large in post-norm, and they don't shrink as you add layers.

### [b] Warm-up becomes mandatory
With large gradients, a normal learning rate makes the first updates too big. Post-norm models need a warm-up stage: start with a tiny learning rate and ramp up. That is one more sensitive hyperparameter, and it slows training.

### [c] LayerNorm does two jobs
LayerNorm re-centres (subtracts the mean) and re-scales (divides by the standard deviation), then applies a gain and a bias. That is two reductions per token per norm, twice per layer, on every token ever processed.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Where should the norm go?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

<div class="quiz">
  <p class="qq">You want the residual stream to carry each layer's output straight to the end of the network, unchanged. Which wiring achieves that?</p>
  <div class="opts">
  <button>A. Norm(x + F(x))</button>
  <button data-ok>B. x + F(Norm(x))</button>
  <button>C. Norm(x) + F(x)</button>
  <button>D. F(Norm(x + x))</button>
  </div>
  <div class="why"><b>B.</b> In x + F(Norm(x)), the norm only touches the copy that goes into F. The x that is passed along is never rescaled, so after L layers the output is x₀ + F₁ + F₂ + … + F_L: a plain sum with an identity path from every layer to the end.</div>
</div>

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Two independent changes

::: cards grid2
### [a] Pre-norm: move the norm inside the branch
<code>x ← x + Attn(Norm(x))</code><br><code>x ← x + FFN(Norm(x))</code><br>Then add <b>one final norm</b> before the output head, because the residual stream is never normalized along the way. GPT-2 did exactly this: "Layer normalization was moved to the input of each sub-block… and an additional layer normalization was added after the final self-attention block."

### [e] RMSNorm: keep only the re-scaling
<code>RMSNorm(x) = g ⊙ x / √(mean(x²) + ε)</code><br>No mean subtraction, no bias. Zhang & Sennrich hypothesize that LayerNorm's re-centring invariance is "dispensable" and report comparable quality with <b>7–64% less running time</b> across their models. LLaMA uses pre-norm with RMSNorm.
:::

<div class="deep"><h4>Why the final norm matters</h4><p>In pre-norm, each layer <b>adds</b> to the residual stream, so its scale grows with depth (notebook 01 measures this). Each sub-layer still sees normalized input, but the logits would see the raw, growing stream. The final RMSNorm (<code>model.norm</code> in Llama code) fixes the scale once, just before the output head.</p></div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Measured: the last layer's gradient vs depth <span class="ill">toy model, random weights</span>

Stacks of L blocks (FFN sub-layers, Xavier init, LayerNorm), with the gradient norm of the <b>last layer's</b> weights for a squared-error loss. These are the values printed by the experiment in notebook 01, a small-scale reproduction of Xiong et al.'s analysis.
{: .lede}

<div class="visual">
  <svg id="gSvg" viewBox="0 0 660 250" role="img" aria-label="Gradient norm vs depth"></svg>
  <div class="legend"><span><i style="background:var(--d)"></i>post-norm</span><span><i style="background:var(--a)"></i>pre-norm</span><span><i style="background:var(--faint)"></i>pre-norm at L=3 × √(3/L)</span></div>
</div>

<div class="deep"><h4>How to read it</h4><p><b>Post-norm</b> stays between about 165 and 210 however deep the stack: the gradient near the output does not shrink with depth, which is the paper's result for post-LN. With a normal learning rate those large updates destabilize early training, hence warm-up. <b>Pre-norm</b> falls roughly like 1/√L (Xiong et al. prove an O(d√(ln d / L)) scaling), so updates stay modest and warm-up can be dropped. In the paper, pre-LN Transformers trained <b>without warm-up</b> reached comparable results with significantly less training time and hyperparameter tuning.</p></div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## LayerNorm vs RMSNorm on a real vector

Eight features of one token. Shift them all up, or scale them all, and compare what the two norms output. (Gain g = 1, bias = 0.)
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">Shift every feature <input type="range" id="nS" min="-3" max="3" step="0.1" value="0"> <output id="nSo"></output></label>
    <label class="ctl">Scale every feature <input type="range" id="nK" min="0.2" max="5" step="0.1" value="1"> <output id="nKo"></output></label>
  </div>
  <svg id="nSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Input, LayerNorm and RMSNorm outputs"></svg>
  <p class="readout" id="nOut"></p>
</div>

<div class="deep"><h4>What the demo shows</h4><ul><li><b>Scaling</b> the input changes neither output: both norms are re-scaling invariant.</li><li><b>Shifting</b> the input changes RMSNorm's output but not LayerNorm's, because LayerNorm subtracts the mean first. RMSNorm gives up shift invariance, and the paper's experiments suggest models don't need it.</li><li>Cost: LayerNorm needs a mean and a variance per token; RMSNorm needs one sum of squares. On GPUs (graphics processing units) these are memory-bound reductions, so the saving is in passes over the data.</li></ul></div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why pre-norm trains more easily

::: cards grid2
### [a] An identity path to every layer
The output is x₀ plus the sum of every layer's contribution, so each layer receives gradient directly from the loss through the residual stream. That is the same idea as pre-activation ResNets, which GPT-2 cites.

### [e] Gradients well-behaved at initialization
Xiong et al. show pre-LN's gradients are well behaved at init, so the warm-up stage can be removed. Fewer hyperparameters, faster training.

### [b] The cost: a growing stream
Because nothing renormalizes the stream, its magnitude grows with depth. Later layers' contributions are relatively smaller, which is why a final norm is required and why some very deep models add extra tricks.

### [c] RMSNorm: a free speed-up
Same placement, fewer operations. Because it's a drop-in replacement with comparable quality, there is little reason not to use it, and LLaMA, Llama 2 and Llama 3 all do.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "LayerNorm normalizes across the batch, like BatchNorm."
> No. Both LayerNorm and RMSNorm normalize <b>each token's feature vector on its own</b>. Nothing depends on other tokens or other sequences, which is why they work the same in training and at inference with any batch size.
:::

::: reveal myth
? "Pre-norm means you don't need a norm at the end."
> The opposite. Because the residual stream is never normalized, pre-norm models <b>need</b> a final norm before the output head.
:::

::: reveal myth
? "RMSNorm is an approximation of LayerNorm that costs some quality."
> It is a different normalization (no re-centring) that the authors found <b>comparable</b> in quality across tasks, and faster. LLaMA-family models use it.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

<div class="quiz">
  <p class="qq">Which formula is RMSNorm?</p>
  <div class="opts">
  <button>A. (x − μ)/σ · g + b</button>
  <button data-ok>B. x / √(mean(x²) + ε) · g</button>
  <button>C. x / max|x|</button>
  <button>D. (x − μ) / √(mean(x²))</button>
  </div>
  <div class="why"><b>B.</b> Divide by the root mean square and scale by a learned gain. No mean and no bias.</div>
</div>

<div class="quiz ">
  <p class="qq">Why does post-norm usually need a learning-rate warm-up?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">At initialization the gradients of parameters near the output are large (Xiong et al., 2020). A full learning rate on large gradients makes the first updates too big and training unstable; warm-up keeps early steps small.</div>
</div>

<div class="quiz ">
  <p class="qq">Write the two lines of a pre-norm Llama block.</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why"><code>h = x + Attention(RMSNorm(x))</code> and <code>out = h + SwiGLU(RMSNorm(h))</code>. After the last block: <code>RMSNorm</code>, then the output head.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Put the norm inside the residual branch (pre-norm) and drop the mean (RMSNorm): stable deep training without warm-up, at lower cost.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>The 2017 Transformer normalizes after each residual addition. At initialization that makes gradients near the output large regardless of depth, so training needs a learning-rate warm-up. Pre-norm normalizes only the input to each sub-layer, x plus F of Norm x, so the residual stream is a clean sum with an identity path from every layer to the output; gradients are well behaved and warm-up can go. You then need one final norm before the output head. RMSNorm goes further and drops LayerNorm's mean subtraction, dividing only by the root mean square. Quality is comparable and it is cheaper. Llama uses both.</p></div>

<div class="recap"><div><span><b>Problem:</b> post-norm needs warm-up and LayerNorm costs two reductions per token.</span></div><div><span><b>Pre-norm:</b> x + F(Norm(x)) plus a final norm; the gradient no longer stays large near the output.</span></div><div><span><b>RMSNorm:</b> x / rms(x) · g; scale-invariant, not shift-invariant, 7–64% faster in the paper.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/architecture/01_norms_prenorm.ipynb" target="_blank" rel="noopener">01 · RMSNorm and pre-norm blocks</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/architecture/01_norms_prenorm.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../03-rope/index.html">03 · RoPE →</a> · Previous: <a href="../01-what-changed/index.html">← 01</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Xiong et al. 2020, "On Layer Normalization in the Transformer Architecture" (ICML); Zhang & Sennrich 2019, "Root Mean Square Layer Normalization" (NeurIPS); Radford et al. 2019 (GPT-2 §2.3); Touvron et al. 2023 (LLaMA §2.2).</p>

<!-- slide id="s-papers" from="papers" -->
