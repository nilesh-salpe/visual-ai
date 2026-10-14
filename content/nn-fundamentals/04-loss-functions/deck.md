---
title: Loss Functions
body:
  data-deck: Loss functions
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
  - 'prediction :: logits → softmax p :: c'
  - 'target :: one-hot (or smoothed) y :: f'
  - 'loss :: −Σ y log p :: a'
  - 'gradient :: p − y :: e'
  caption: The same loss trains classifiers and every LLM.
example:
  title: 'Worked example: confidently wrong'
  setup: Binary classifier with sigmoid output p = σ(z); true label 1 but the model outputs p = 0.01.
  steps:
  - 'Cross-entropy: loss = −ln 0.01 = <b>4.61</b>; gradient w.r.t. z = p − 1 = <b>−0.99</b>: a strong push.'
  - 'MSE on the probability: loss = (p − 1)² = 0.980; gradient w.r.t. z = 2(p − 1)·p(1 − p) = <b>-0.0196</b>: almost nothing.'
  - So with MSE the worst mistakes learn the slowest, because the sigmoid is saturated.
  - 'Label smoothing ε = 0.1 over K classes: target 1 − ε + ε/K for the true class, ε/K elsewhere. Inception-v3 used ε = 0.1 with K = 1,000 and gained about 0.2%
    top-1 and top-5.'
  result: Cross-entropy undoes the softmax's saturation; that is why it is the default for anything that outputs probabilities.
traps:
  tricks:
  - 'Softmax + CE → gradient p − y. :: No saturation.'
  - 'Regression → MSE (or Huber for outliers). :: Classification → cross-entropy.'
  - 'Average over tokens. :: So the scale is independent of batch and sequence length.'
  traps:
  - 'MSE on probabilities. :: Vanishing gradients when confidently wrong.'
  - 'Computing log(softmax). :: Use log-softmax / fused cross-entropy (Math deck 08).'
  - 'Over-smoothing labels. :: Large ε hurts calibration-sensitive uses like distillation.'
papers:
- inception
- bengio03
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Neural Networks · 04</div>
    <h1>Loss functions</h1>
    <p class="sub">What a loss tells the optimizer: mean squared error for regression, cross-entropy for classification and next-token prediction, and label smoothing.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Training needs one number that is low when the model is right and whose gradient points toward being more right. A poor choice gives weak or misleading gradients.</div>
      <div class="c"><b>Core idea</b><b>MSE</b> (mean squared error) suits real-valued targets. For probabilities use <b>cross-entropy</b> −log p(correct): with a softmax its logit gradient is p − y, which stays large when the model is confidently wrong. <b>Label smoothing</b> mixes the one-hot target with a uniform distribution.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## How hard does each loss push?

The true label is 1. Move the model's predicted probability p. Compare the loss and, more importantly, the gradient with respect to the logit for cross-entropy and for MSE.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">predicted p(correct) <input type="range" id="cP" min="0.005" max="0.995" step="0.005" value="0.05"> <output id="cPo"></output></label></div>
  <svg id="cSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Loss gradients"></svg>
  <p class="readout" id="cOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## What a bad loss does

::: cards grid3
### [d] Weak gradients
MSE through a sigmoid or softmax barely moves confidently wrong predictions.

### [b] Wrong objective
Accuracy is what we care about but it is flat almost everywhere: no gradient.

### [c] Over-confidence
Cross-entropy with hard targets rewards pushing logits to infinity, hurting calibration and generalisation.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Which gradient is bigger?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? True class probability is 0.01. Which loss gives the larger gradient on the logit?
- [ ] MSE on the probability
- [x] Cross-entropy
- [ ] They are equal
- [ ] Neither has a gradient
> <b>B.</b> Cross-entropy: |p − 1| = 0.99. MSE: |2(p − 1)p(1 − p)| ≈ 0.02, about 50× smaller.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Match the loss to the output

::: cards grid3
### [a] Mean squared error
L = mean (ŷ − y)². Real-valued targets; gradient 2(ŷ − y).

### [c] Cross-entropy
L = −Σ yᵢ log pᵢ. Probabilities; with softmax, ∂L/∂z = p − y.

### [e] Label smoothing
Replace the one-hot y with (1 − ε)·y + ε/K. Discourages infinite logits (Szegedy et al., 2016).
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Losses across the LLM lifecycle

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Stage</th><th>Loss</th></tr>
  <tr><td>Pretraining</td><td>cross-entropy on every next token</td></tr>
  <tr><td>SFT (supervised fine-tuning)</td><td>cross-entropy on response tokens only (prompt masked)</td></tr>
  <tr><td>Reward model</td><td>−log σ(r_chosen − r_rejected) (Bradley–Terry)</td></tr>
  <tr><td>Distillation</td><td>cross-entropy to the teacher's softened distribution</td></tr>
  <tr><td>DPO</td><td>−log σ(β · log-ratio difference)</td></tr>
</table></div>
<p class="caption">See the <a href="../../post-training/index.html">Post-training</a> decks for the last three.</p>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why cross-entropy is the default

::: cards grid2
### [a] Maximum likelihood
Minimising it maximises the probability of the data (Math deck 06).

### [e] Clean gradient
p − y: proportional to how wrong the prediction is, never saturating.

### [b] Proper scoring rule
The expected loss is minimised by reporting true probabilities.

### [c] Works per token
Each position gives an independent, cheap training signal.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "MSE and cross-entropy are interchangeable for classification."
> They have the same minimum but very different gradients; MSE learns slowly from confident mistakes.
:::

::: reveal myth
? "Lower loss always means higher accuracy."
> Usually correlated, but loss also rewards calibration; two models can swap order on the two metrics.
:::

::: reveal myth
? "Label smoothing is only for image models."
> The original Transformer used ε = 0.1 too; it is optional for LLM pretraining and usually off.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Gradient of softmax + cross-entropy with respect to the logits?
- [ ] y − p
- [x] p − y
- [ ] log p
- [ ] p(1 − p)
> <b>p − y</b>.
:::

::: reveal
? Why does MSE on a sigmoid output learn slowly from confident mistakes?
> Its gradient contains σ′ = p(1 − p), which is ≈ 0 when p is near 0 or 1.
:::

::: reveal
? Smoothed target for the true class with ε = 0.1 and K = 10?
> 1 − 0.1 + 0.1/10 = 0.91.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Use MSE for real-valued targets and cross-entropy for probabilities: with softmax its gradient p − y never saturates, which is why it trains every LLM.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>A loss turns predictions into one number to minimise, and its gradient decides how the model changes. Mean squared error suits real-valued targets. For probabilities, cross-entropy, minus the log probability of the correct answer, is the right choice: combined with a softmax its gradient on the logits is just the predicted probabilities minus the target, so a confidently wrong prediction gets a strong correction. Squared error on probabilities would multiply in the sigmoid's tiny slope and barely learn. Label smoothing mixes a little uniform probability into the target to discourage over-confidence.</p></div>
    <div class="recap"><div><span><b>Problem:</b> one number with a useful gradient.</span></div><div><span><b>Core idea:</b> cross-entropy for probabilities, gradient p − y.</span></div><div><span><b>Extras:</b> label smoothing; MSE for regression.</span></div></div>
    <p class="start-hint">Next: <a href="../05-optimizers/index.html">05 · Optimizers →</a> · Previous: <a href="../03-backpropagation/index.html">← 03</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
