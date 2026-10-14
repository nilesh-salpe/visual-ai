---
title: Residuals and Layer Normalization
body:
  data-deck: Residuals + LayerNorm
  data-home: ../index.html
  data-home-label: Transformer
styles:
- ../../shared/deck.css
- ../../shared/learn.css
- ../tx.css
scripts:
- ../../shared/deck.js
- ../tx.js
glance:
  steps:
  - 'x :: sub-layer input :: f'
  - 'Sublayer(x) :: attention or FFN :: c'
  - 'dropout :: P_drop = 0.1 :: b'
  - 'x + … :: residual :: a'
  - 'LayerNorm :: post-norm (2017) :: e'
  caption: LayerNorm(x + Sublayer(x)) around all 12 encoder and 18 decoder sub-layers.
example:
  title: 'Worked example: LayerNorm on one token'
  setup: A token with 4 features [2.0, -1.0, 0.5, 3.5] (gain 1, bias 0).
  steps:
  - Mean = 1.250; standard deviation = 1.677.
  - Normalized = (x − mean) / std = <b>[0.45, -1.34, -0.45, 1.34]</b>.
  - The result has mean 0 and variance 1 regardless of the input scale, so stacked layers stay in range.
  - It uses only this token's features, so it behaves the same at any batch size (unlike BatchNorm).
  result: Residuals keep a clean path for gradients; LayerNorm keeps each token's scale stable through 30 sub-layers.
traps:
  tricks:
  - 'Sub-layer counts. :: Encoder 6 × 2 = 12; decoder 6 × 3 = 18.'
  - 'Per-token normalization. :: Mean and variance over the 512 features.'
  - 'Modern change. :: Later models moved the norm inside the branch (pre-norm) and used RMSNorm.'
  traps:
  - 'Calling it BatchNorm. :: LayerNorm ignores other examples in the batch.'
  - 'Forgetting dropout. :: Applied to each sub-layer output before the residual add.'
  - 'Assuming post-norm trains easily. :: It needed warm-up (4,000 steps in the paper).'
papers:
- vaswani
- resnet
- layernorm
- xiong
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Attention Is All You Need · 10</div>
    <h1>Residual connections and layer normalization</h1>
    <p class="sub">How every sub-layer is wrapped as <code>LayerNorm(x + Sublayer(x))</code> so information and gradients flow through a stack of 6 + 6 layers.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Stacking many sub-layers makes training hard. Each one transforms the signal, so the original information and the gradients can fade or blow up with depth.</div>
      <div class="c"><b>Core idea</b>Add each sub-layer's output back to its input (a residual, or skip, connection), then normalize each token's vector to zero mean and unit variance across its features.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## The model is deep: 12 sub-layers in the encoder, 18 in the decoder

::: cards grid3
### [a] Encoder
6 layers × 2 sub-layers = 12 transformations in a row.

### [c] Decoder
6 layers × 3 sub-layers = 18 transformations in a row.

### [e] Depth helps
Table 3 (C): N = 2 gives 23.7 dev BLEU (Bilingual Evaluation Understudy, an n-gram overlap score for translation), N = 6 gives 25.8.
:::

<div class="takeaway">The architecture needs depth, so signals and gradients must pass cleanly through many stacked sub-layers.</div>

<!-- slide id="s-prob" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Pass a signal through 12 sub-layers and it drifts <span class="ill">illustrative simulation</span>

The encoder alone has 6 layers × 2 sub-layers. Here a 64-dim vector goes through 12 random sub-layers (linear + ReLU (rectified linear unit)). With no skip path, its size shrinks or explodes (depending on the weight scale) and its resemblance to the input is lost. Turn on each component to see what it fixes.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <div class="seg" id="rSeg"><button data-v="0" class="on">Plain stack</button><button data-v="1">+ residual</button><button data-v="2">+ residual + LayerNorm</button></div>
    <label class="ctl">Weight scale <input type="range" id="rG" min="0.2" max="2" step="0.05" value="0.35"> <output id="rGo"></output></label>
  </div>
  <div class="grid2" style="margin-top:12px">
    <div><h3>Vector norm by depth (log scale)</h3><svg id="nSvg" viewBox="0 0 320 200" role="img" aria-label="Norm across depth"></svg></div>
    <div><h3>Cosine similarity to the input</h3><svg id="cSvg" viewBox="0 0 320 200" role="img" aria-label="Similarity across depth"></svg></div>
  </div>
  <div class="key"><span><i style="background:var(--d)"></i>plain stack</span><span><i style="background:var(--b)"></i>+ residual</span><span><i style="background:var(--e)"></i>+ residual + LayerNorm</span><span>(selected option drawn bold)</span></div>
</div>

<p class="caption">A toy simulation with random weights, made for intuition. It is not an experiment from the paper. The paper adopts residual connections from He et al. (2016) and layer normalization from Ba et al. (2016).</p>

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Make each sub-layer safe to stack

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? How can each new sub-layer be designed so that, at worst, it does no harm to the signal passing through?
- [ ] Initialize all weights to zero
- [x] Add the input back to the output: x + Sublayer(x)
- [ ] Use fewer layers
- [ ] Use a larger learning rate
> <b>B is a residual connection.</b> The input always has an identity path, so the sub-layer only needs to learn a correction. If that correction is small, the signal passes through nearly unchanged. Zero weights (A) would make all units identical. The paper adds layer normalization after the sum to keep the scale stable.
:::

<!-- slide id="s-wrap" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Every sub-layer is wrapped the same way

The input x skips around the sub-layer and is <b>added</b> to its (dropout-regularized) output, and the sum is then layer-normalized. The paper places the normalization <b>after</b> the addition. All widths are d<sub>model</sub> = 512 so the addition works.
{: .lede}

<div class="visual"><svg id="wSvg" viewBox="0 0 660 220" role="img" aria-label="Residual and LayerNorm wrapper"></svg></div>

<div class="grid3" style="margin-top:12px">
  <div class="card a"><h3>Skip path</h3><p>The identity route lets information (and gradients) pass unchanged. The sub-layer only has to learn a <em>correction</em> to x.</p></div>
  <div class="card b"><h3>Dropout 0.1</h3><p>Applied to each sub-layer's output before the addition (§5.4, residual dropout).</p></div>
  <div class="card e"><h3>LayerNorm</h3><p>Re-centres and re-scales each token's 512 features, keeping activations in a stable range from layer to layer.</p></div>
</div>

{{glance}}

<!-- slide id="s-ln" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Layer normalization works on one token's features

For a single token vector: subtract its mean μ, divide by its standard deviation σ, then apply a learned gain γ and bias β. It never looks across other tokens or other examples. Scale or shift the input to see that the normalized output doesn't change.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">Multiply input by <input type="range" id="lS" min="0.2" max="5" step="0.1" value="1"> <output id="lSo"></output></label>
    <label class="ctl">Add to input <input type="range" id="lB" min="-3" max="3" step="0.1" value="0"> <output id="lBo"></output></label>
    <button class="btn" id="lNew">New vector</button>
  </div>
  <svg id="lSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Layer normalization"></svg>
</div>

<div class="eq">LN(x) = γ ⊙ (x − μ) / σ + β, &nbsp; μ = mean over the 512 features of one token</div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide raw -->
<section class="slide" id="s-paper" data-chapter="How">
  <div class="inner">
    <span class="qtag b5">5 · How it works</span> <span class="ill" style="color:var(--c);border-color:var(--c)">from the paper · §3.1, §5.4</span>
    <h2>The paper's wording</h2>
    <hr>
    <div class="paper"><b>§3.1:</b> "We employ a residual connection [11] around each of the two sub-layers, followed by layer normalization [1]. That is, the output of each sub-layer is LayerNorm(x + Sublayer(x)), where Sublayer(x) is the function implemented by the sub-layer itself. To facilitate these residual connections, all sub-layers in the model, as well as the embedding layers, produce outputs of dimension d<sub>model</sub> = 512."</div>
    <div class="paper"><b>§5.4, Residual Dropout:</b> dropout is applied to the output of each sub-layer before it is added to the sub-layer input and normalized, and also to the sums of the embeddings and positional encodings. P<sub>drop</sub> = 0.1 for the base model.</div>
    <div class="paper"><b>Table 3 (D):</b> P<sub>drop</sub> = 0.0 gives 24.6 BLEU (dev) against 25.8 for the base model, so "dropout is very helpful in avoiding over-fitting" (§6.2).</div>
  </div>
</section>

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works

::: cards grid2
### [a] Identity path
x reaches the output unchanged, plus a learned correction. Information and gradients have a direct route through the whole stack.

### [e] Stable scale
LayerNorm re-centres and re-scales each token's features after every sub-layer, so activations don't drift with depth.

### [b] Regularized corrections
Dropout on each sub-layer output before the add. Table 3 (D): P<sub>drop</sub> = 0 gives 24.6 BLEU vs 25.8 with 0.1.

### [c] One width everywhere
All sub-layers and embeddings output d<sub>model</sub> = 512, so every residual addition lines up (§3.1).
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Layer normalization normalizes across the batch."
> It normalizes across the <b>features of one token</b> (its 512 values). Normalizing across the batch is batch normalization, a different technique.
:::

::: reveal myth
? "The paper applies LayerNorm before each sub-layer."
> The paper uses <b>LayerNorm(x + Sublayer(x))</b>: normalization comes <b>after</b> the residual addition (§3.1).
:::

::: reveal myth
? "Residual connections add parameters."
> The skip path is the <b>identity</b>: no parameters. LayerNorm adds only a gain and bias per feature.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? What is the output of each sub-layer in the paper?
- [ ] Sublayer(LayerNorm(x))
- [x] LayerNorm(x + Sublayer(x))
- [ ] x + LayerNorm(Sublayer(x))
- [ ] LayerNorm(Sublayer(x))
> <b>LayerNorm(x + Sublayer(x))</b> (§3.1), with dropout applied to Sublayer(x) before the addition.
:::

::: quiz
? Where is residual dropout applied?
- [ ] To the input x
- [x] To each sub-layer's output before it is added and normalized
- [ ] After LayerNorm
- [ ] Only to the attention weights
> <b>To each sub-layer output before the add &amp; norm</b>, and also to the sums of embeddings and positional encodings (§5.4).
:::

<div class="quiz ">
  <p class="qq">Why must every sub-layer output exactly 512 dimensions?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">So that x + Sublayer(x) is defined: you can only add vectors of the same size.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Wrap every sub-layer as LayerNorm(x + Sublayer(x)): the skip path carries information through, and normalization keeps each token's scale stable.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Each of the Transformer's sub-layers, whether attention or FFN (feed-forward network), is wrapped in a residual connection followed by layer normalization: output = LayerNorm(x + Dropout(Sublayer(x))). The identity path lets information and gradients flow through the 12-to-18-sub-layer stacks, so each sub-layer only learns a correction. LayerNorm normalizes each token's 512 features to keep activations stable, and all widths are 512 so the additions line up.</p></div>

<div class="recap">
  <div><span><b>Problem:</b> deep stacks of transformations make the signal and gradients drift, fade or explode.</span></div>
  <div><span><b>Core idea:</b> output = LayerNorm(x + Dropout(Sublayer(x))). The skip path carries x through unchanged, and LN (layer normalization) keeps each token's features centred and scaled.</span></div>
</div>

<p class="start-hint">Next: <a href="../11-position-wise-ffn/index.html">11 · Position-wise feed-forward networks →</a> · Previous: <a href="../09-masked-self-attention/index.html">← 09</a> · <a href="../index.html">All concepts</a></p>

<!-- slide id="s-papers" from="papers" -->
