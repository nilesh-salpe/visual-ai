---
title: Optimizers
body:
  data-deck: Optimizers
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
  - 'gradient g :: from backprop :: c'
  - 'momentum m :: running mean of g :: a'
  - 'scale v :: running mean of g² :: b'
  - 'update :: −η(m̂/√v̂ + λw) :: e'
  - 'schedule :: η(t): warmup → decay :: f'
  loop: '3 -> 0 :: every step'
  caption: AdamW + warmup + cosine decay is the default recipe for LLM pretraining.
example:
  title: 'Worked example: the Llama recipe'
  setup: 'LLaMA (Touvron et al., 2023): AdamW with β₁ = 0.9, β₂ = 0.95, weight decay 0.1, gradient clipping 1.0, 2,000 warmup steps, cosine decay to 10% of the peak.'
  steps:
  - 'Warmup: η grows linearly from ~0 to the peak over 2,000 steps, while Adam''s v estimates settle.'
  - 'With peak 3 × 10⁻⁴ and 200,000 total steps: η = 1.5 × 10⁻⁴ at step 1,000, 3 × 10⁻⁴ at 2,000, ≈ 1.7 × 10⁻⁴ at 100,000 and 3 × 10⁻⁵ at the end (notebook 04).'
  - Decoupled decay shrinks every weight by η·λ per step, independently of its gradient history.
  - 'Notebook 04: with λ = 0.1, putting the penalty inside Adam''s gradient (L2) gives a final weight norm of 1.38, while AdamW gives 9.81: the two regularise very
    differently.'
  result: Adam's per-parameter scaling, decoupled weight decay and a warmup + decay schedule together make large runs stable.
traps:
  tricks:
  - 'β₂ = 0.95 for LLMs. :: Faster-adapting variance than the 0.999 default.'
  - 'Warm up, then decay. :: Linear warmup, cosine (or linear) decay.'
  - 'Optimizer state = 2 extra values per parameter. :: m and v, in FP32: 8 bytes.'
  traps:
  - 'L2 penalty with Adam. :: Not weight decay; use AdamW.'
  - 'No warmup at a high learning rate. :: Early instability or divergence.'
  - 'Decaying weight decay on norms and biases. :: Usually excluded from decay.'
papers:
- adam
- adamw
- sgdr
- sutskever13
- llama
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Neural Networks · 05</div>
    <h1>Optimizers</h1>
    <p class="sub">From SGD to AdamW: how gradients become weight updates, why weight decay must be decoupled from Adam, and the warmup-plus-cosine schedule used to train LLMs.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Raw gradients are noisy, differently scaled across parameters, and unreliable early in training. Plain gradient steps are slow or unstable on such problems.</div>
      <div class="c"><b>Core idea</b><b>SGD with momentum</b> smooths noisy gradients. <b>Adam</b> also divides by a running RMS (root mean square) of each parameter's gradient. <b>AdamW</b> applies weight decay directly to the weights instead of through the gradient. A <b>learning-rate schedule</b> warms up, then decays.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Shape a learning-rate schedule

Choose warmup length, decay shape and the final fraction of the peak. The curve is the learning rate over a 100,000-step run.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">warmup steps <input type="range" id="sW" min="0" max="20000" step="500" value="2000"> <output id="sWo"></output></label><label class="ctl">final fraction <input type="range" id="sF" min="0" max="1" step="0.05" value="0.1"> <output id="sFo"></output></label></div>
  <div class="seg" id="sSeg" style="margin-top:8px"><button data-v="cos" class="on">cosine</button><button data-v="lin">linear</button><button data-v="const">constant</button></div>
  <svg id="sSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Learning-rate schedule"></svg>
  <p class="readout" id="sOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why plain SGD is not enough for LLMs

::: cards grid3
### [d] Very different scales
Embedding rows, attention weights and norms receive gradients of very different sizes; one learning rate fits none.

### [b] Noise
Mini-batch gradients are noisy; following each one exactly wastes steps.

### [c] Fragile start
Early in training the curvature is high and statistics are unreliable; large steps diverge.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What does weight decay do in AdamW?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? In AdamW, how is weight decay applied?
- [ ] Added to the gradient before computing m and v
- [x] Subtracted from the weights directly, η·λ·w each step
- [ ] Applied only at the end of training
- [ ] Applied to the learning rate
> <b>B.</b> Decoupled: w ← w − η(m̂/(√v̂ + ε) + λw). Putting λw into the gradient instead would be divided by √v̂ and regularise heavily-updated weights less.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Three ingredients

::: cards grid3
### [a] Momentum
m ← β₁m + (1 − β₁)g. Averages noise, accelerates along consistent directions (Sutskever et al., 2013).

### [b] Adaptive scaling
v ← β₂v + (1 − β₂)g². Step ∝ m̂/√v̂: each parameter gets its own effective learning rate (Adam).

### [e] Decoupled decay
w ← w − ηλw separately from the gradient step (AdamW, Loshchilov & Hutter).
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## AdamW, one step

::: cards grid4
### [c] 1 · moments
m = β₁m + (1 − β₁)g, v = β₂v + (1 − β₂)g².

### [a] 2 · bias-correct
m̂ = m/(1 − β₁ᵗ), v̂ = v/(1 − β₂ᵗ): both start at 0.

### [b] 3 · adaptive step
w −= η · m̂/(√v̂ + ε).

### [e] 4 · decay
w −= η · λ · w (skip for norms and biases).
:::

::: deep Memory cost
Adam keeps m and v for every parameter, usually in FP32: 8 bytes per parameter on top of the weights and gradients, which is most of the "16 bytes per parameter" in Distributed deck 03.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why this recipe works

::: cards grid2
### [a] Scale invariance
Adam is invariant to rescaling each gradient coordinate, so badly scaled parameters still learn.

### [e] Regularisation that behaves
Decoupled decay makes the decay strength independent of the learning rate and gradient history.

### [b] Warmup protects the start
Small early steps let Adam's statistics and the network settle before large updates.

### [c] Decay finishes the job
Shrinking η lets the weights settle into a low-loss region; cosine was popularised by SGDR.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Adam needs no learning-rate tuning."
> Its defaults are robust for small problems; LLMs still tune peak η, β₂, warmup and decay.
:::

::: reveal myth
? "Weight decay and L2 regularisation are the same."
> Only for plain SGD. For Adam they differ, which is why AdamW exists.
:::

::: reveal myth
? "Schedules are a minor detail."
> Warmup prevents divergence and the decay phase produces a large share of the final loss improvement.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? How many FP32 optimizer values does Adam store per parameter?
- [ ] 0
- [ ] 1
- [x] 2
- [ ] 4
> <b>2</b>: m and v (plus the step count, shared).
:::

::: reveal
? Why does Adam bias-correct m and v?
> They start at 0, so early averages are biased toward 0; dividing by 1 − βᵗ removes that bias.
:::

::: reveal
? Why warm up the learning rate?
> Early gradients and Adam's variance estimates are unreliable and curvature is high; large early steps can diverge.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">LLMs train with AdamW: momentum plus per-parameter RMS scaling, weight decay applied directly to weights, and a learning rate that warms up and then decays.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Optimizers turn gradients into updates. Momentum keeps a running average of gradients to smooth noise. Adam also keeps a running average of squared gradients and divides by its square root, so each parameter gets its own effective step size, with bias corrections because both averages start at zero. AdamW applies weight decay directly to the weights rather than adding it to the gradient, where Adam's scaling would weaken it. The learning rate follows a schedule: linear warmup while statistics settle, then cosine or linear decay. Llama used beta-two of 0.95, weight decay 0.1 and 2,000 warmup steps.</p></div>
    <div class="recap"><div><span><b>Problem:</b> noisy, badly scaled gradients; fragile start.</span></div><div><span><b>Core idea:</b> momentum + RMS scaling + decoupled decay.</span></div><div><span><b>Schedule:</b> warmup, then cosine to ~10%.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/nn-fundamentals/04_optimizers_schedules.ipynb" target="_blank" rel="noopener">04 · SGD, Adam, AdamW and learning-rate schedules</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/nn-fundamentals/04_optimizers_schedules.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../06-initialization/index.html">06 · Initialization →</a> · Previous: <a href="../04-loss-functions/index.html">← 04</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
