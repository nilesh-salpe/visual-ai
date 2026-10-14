---
title: Normalization and Residual Connections
body:
  data-deck: Normalization and residual connections
  data-home: ../index.html
  data-home-label: NN fundamentals
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'x :: residual stream :: f'
  - 'Norm(x) :: fixed scale :: c'
  - 'f(·) :: attention or MLP :: a'
  - 'x + f(Norm(x)) :: add, don''t replace :: e'
  loop: '3 -> 0 :: every block'
  caption: 'The gradient of x + f(x) is I + f′(x): the identity term never vanishes.'
example:
  title: 'Worked example: what the identity path buys'
  setup: 'A stack of L blocks. Plain: x ← f(x). Residual: x ← x + f(x). Backward multiplies by each block''s Jacobian.'
  steps:
  - 'Plain stack: gradient = Πₗ f′ₗ. If each factor has size 0.9, after 100 layers the gradient is 0.9¹⁰⁰ ≈ <b>2.7 × 10⁻⁵</b>.'
  - 'Residual stack: gradient = Πₗ (I + f′ₗ). Expanding the product, one term is the identity itself, so the bottom layer always gets the top gradient directly.'
  - ResNet trained networks of over 100 layers this way; BatchNorm reached the same accuracy with 14× fewer training steps.
  - Pre-norm puts the norm inside the branch (x + f(Norm(x))) so the identity path stays clean; most modern LLMs use pre-norm with RMSNorm.
  result: Normalisation keeps each layer's inputs well scaled; residuals keep a clean path for signals and gradients through any depth.
traps:
  tricks:
  - 'Pre-norm: x + f(Norm(x)). :: Stable for deep stacks.'
  - 'RMSNorm = LayerNorm without mean-centering. :: Cheaper, used by Llama.'
  - 'LayerNorm normalises per token. :: Works with any batch size, unlike BatchNorm.'
  traps:
  - 'BatchNorm in sequence models. :: Statistics depend on the batch and padding.'
  - 'Post-norm at large depth. :: Norm on the residual path can make training unstable without careful warmup.'
  - 'Forgetting the final norm. :: Pre-norm stacks need one before the output head.'
papers:
- resnet
- batchnorm
- layernorm
- rmsnorm
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Neural Networks · 07</div>
    <h1>Normalization and residual connections</h1>
    <p class="sub">The two tricks that let networks hundreds of layers deep train reliably: rescale activations at every layer, and add each layer's output to its input instead of replacing it.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Even with good initialisation, activation scales drift during training, and gradients must pass back through every layer of a very deep stack.</div>
      <div class="c"><b>Core idea</b><b>Normalization</b> rescales each token's (LayerNorm, RMSNorm) or each feature's (BatchNorm) activations to a fixed scale, with learned gains. <b>Residual connections</b> compute x + f(x), so the identity path carries signal and gradient straight through. Transformers combine them as <b>pre-norm</b> blocks: x + f(Norm(x)).</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Plain vs residual vs pre-norm residual

Activation scale through 64 blocks, computed live. Each block's branch is a random linear layer + ReLU whose gain you control. Compare the three wirings.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">branch gain <input type="range" id="rG" min="0.5" max="2.5" step="0.05" value="1.4"> <output id="rGo"></output></label></div>
  <svg id="rSvg" viewBox="0 0 660 240" style="margin-top:10px" role="img" aria-label="Scale through depth"></svg>
  <p class="readout" id="rOut"></p>
</div>
<p class="caption">Width 48. Gain √2 ≈ 1.41 is the He value for ReLU. Branch outputs in the residual stacks are scaled by 1/√2 for symmetry.</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## What initialisation alone can't fix

::: cards grid3
### [d] Drift during training
Weights change, so the carefully balanced scales at step 0 do not stay balanced.

### [b] Products of Jacobians
Without a shortcut, gradients through 100 layers are a product of 100 factors.

### [c] Degradation
He et al. found deeper plain networks had higher training error than shallower ones: an optimisation failure, not overfitting.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Why does x + f(x) help gradients?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? The derivative of x + f(x) with respect to x is I + f′(x). Why does that help a 100-layer stack?
- [ ] It doubles the gradient
- [x] The identity term gives a path where the gradient is not multiplied by any f′
- [ ] It removes the need for backpropagation
- [ ] It makes f linear
> <b>B.</b> Expanding Π(I + f′ₗ) always contains the identity, so the top gradient reaches the bottom unchanged, plus contributions through the branches.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Normalise inside, add outside

::: cards grid2
### [c] BatchNorm
Normalise each feature over the batch (Ioffe & Szegedy, 2015). Great for CNNs (convolutional networks); awkward for variable-length sequences.

### [a] LayerNorm
Normalise each token's vector over its features, then scale and shift (Ba et al., 2016).

### [e] RMSNorm
Divide by the root mean square only, no mean subtraction (Zhang & Sennrich, 2019): cheaper, same quality.

### [b] Residual
x + f(x): each block adds a correction to a running "residual stream" (He et al., 2016).
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Inside one pre-norm transformer block

::: cards grid4
### [f] 1 · stream x
Each token's vector of size d, carried through all layers.

### [c] 2 · attention branch
x ← x + Attention(RMSNorm(x)).

### [a] 3 · MLP branch
x ← x + MLP(RMSNorm(x)).

### [e] 4 · final norm
After the last block, RMSNorm(x), then the output projection to logits.
:::
<p class="caption">See <a href="../../architecture/02-normalization/index.html">Architecture deck 02</a> for pre-norm vs post-norm in detail.</p>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why the combination is so robust

::: cards grid2
### [a] Scale invariance
A normalised layer's output does not depend on the scale of its input, so drift upstream cannot blow it up.

### [e] Identity at init
With small branch outputs, a residual network starts close to the identity function: easy to optimise.

### [b] Higher learning rates
Normalisation allows much larger steps (BatchNorm's 14× fewer steps).

### [c] Residual stream view
Each layer reads from and writes to a shared stream, which is how interpretability work describes transformers.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Normalisation layers just speed up training a little."
> For deep transformers they are often the difference between training and diverging.
:::

::: reveal myth
? "Residual connections add many parameters."
> They add none: just an addition.
:::

::: reveal myth
? "LayerNorm and BatchNorm are the same thing."
> BatchNorm averages over examples for each feature; LayerNorm over features for each example (token).
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? What does RMSNorm drop compared with LayerNorm?
- [ ] the learned gain
- [x] mean subtraction
- [ ] division by a scale
- [ ] everything
> <b>Mean subtraction</b> (and usually the bias).
:::

::: reveal
? Write a pre-norm transformer block.
> x ← x + Attn(Norm(x)); x ← x + MLP(Norm(x)).
:::

::: reveal
? Why is BatchNorm rarely used in LLMs?
> Its statistics depend on the batch, which varies with sequence length, padding and generation one token at a time; LayerNorm/RMSNorm work per token.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Normalisation keeps each layer's inputs at a fixed scale and residual connections give an identity path, so pre-norm blocks x + f(Norm(x)) train at any depth.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Good initialisation balances scales only at the start, and gradients in a deep plain stack are products of many factors. Normalisation layers rescale activations at every layer: BatchNorm over the batch for each feature, LayerNorm over each token's features, and RMSNorm the same without subtracting the mean. Residual connections add each layer's output to its input, so the gradient always includes an identity path and deep networks start near the identity. Modern LLMs use pre-norm blocks, x plus attention of norm x, then x plus MLP of norm x, usually with RMSNorm and a final norm before the output.</p></div>
    <div class="recap"><div><span><b>Problem:</b> scale drift; vanishing gradient products.</span></div><div><span><b>Core idea:</b> normalise inside the branch, add outside.</span></div><div><span><b>In LLMs:</b> pre-norm RMSNorm blocks.</span></div></div>
    <p class="start-hint">Next: <a href="../08-regularization/index.html">08 · Regularization and generalization →</a> · Previous: <a href="../06-initialization/index.html">← 06</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
