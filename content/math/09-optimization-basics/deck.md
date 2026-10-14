---
title: Optimization Basics
body:
  data-deck: Optimization basics
  data-home: ../index.html
  data-home-label: Math
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'gradient :: direction of steepest ascent :: c'
  - 'step :: w ← w − η g :: a'
  - 'momentum :: v ← βv + g :: b'
  - 'Adam :: ÷ √(running g²) :: e'
  loop: '3 -> 0 :: every step'
  caption: Learning rate × curvature decides stability; the condition number decides speed.
example:
  title: 'Worked example: an ill-conditioned bowl'
  setup: 'f(x, y) = ½(x² + 100·y²): curvatures 1 and 100, condition number κ = 100. Start at (1, 1). (Notebook 06.)'
  steps:
  - 'Stability: η must be below 2/λ_max = 2/100 = <b>0.02</b>; at η = 0.021 the y-coordinate grows every step.'
  - At the best fixed rate η = 2/(1 + κ), plain gradient descent needs <b>346 steps</b> to cut the loss by 10⁶.
  - Momentum with tuned β needs <b>58 steps</b>; at κ = 1,000 it is 3,454 vs 204.
  - Adam with η = 0.05 converges at κ = 100 and at κ = 10,000 with the same settings, because it normalises each coordinate.
  result: The steep direction limits the learning rate; the flat direction then limits progress. Momentum and adaptive methods attack exactly that gap.
traps:
  tricks:
  - 'η < 2/λ_max. :: Above it, GD diverges along the steepest direction.'
  - 'Momentum ≈ √κ speed-up. :: On quadratics (Goh, Distill).'
  - 'Adam defaults: β₁ 0.9, β₂ 0.999, ε 10⁻⁸. :: LLMs often use β₂ ≈ 0.95.'
  traps:
  - 'Too high a learning rate. :: Loss spikes or NaNs; warm up the rate early in training.'
  - 'Fearing local minima. :: In high dimensions saddle points and plateaus are the bigger problem (Dauphin et al.).'
  - 'L2 penalty inside Adam. :: Not the same as weight decay; use decoupled AdamW.'
papers:
- adam
- dauphin
- goh
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Math for LLMs · 09</div>
    <h1>Optimization basics</h1>
    <p class="sub">How gradient descent moves through a loss landscape, why curvature and the learning rate decide whether it converges, and what momentum and Adam fix.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>We can compute gradients of the loss. Now we need to use them to find good weights, in a landscape with billions of dimensions, steep and flat directions, and saddle points.</div>
      <div class="c"><b>Core idea</b><b>Gradient descent</b> steps against the gradient: w ← w − η∇L. On a quadratic it is stable only if η < 2/λ_max, and the flattest direction sets the speed, so ill-conditioning (κ = λ_max/λ_min) slows it. <b>Momentum</b> accumulates velocity; <b>Adam</b> rescales each coordinate by its recent gradient size.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Walking down an elongated valley

Gradient descent on f(x, y) = ½(x² + κy²). Change the learning rate, momentum and condition number κ, and watch the path from the start point (circle).
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">learning rate η <input type="range" id="oL" min="0.001" max="0.03" step="0.001" value="0.015"> <output id="oLo"></output></label>
    <label class="ctl">momentum β <input type="range" id="oM" min="0" max="0.95" step="0.05" value="0"> <output id="oMo"></output></label>
    <label class="ctl">κ <input type="range" id="oK" min="1" max="100" step="1" value="100"> <output id="oKo"></output></label>
  </div>
  <svg id="oSvg" viewBox="0 0 660 260" style="margin-top:10px" role="img" aria-label="Optimization path"></svg>
  <p class="readout" id="oOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why plain gradient descent struggles

::: cards grid3
### [d] Ill-conditioning
The steep direction caps the learning rate at 2/λ_max; along the flat direction progress is then tiny.

### [b] Saddle points
High-dimensional losses have far more saddles than bad local minima, surrounded by slow plateaus.

### [c] Noisy gradients
Mini-batches give noisy estimates (SGD, stochastic gradient descent), so steps jitter.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What happens above the limit?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? For f = ½·100·y², gradient descent uses η = 0.025. What happens to y?
- [ ] It converges slowly
- [ ] It converges in one step
- [x] It oscillates with growing amplitude and diverges
- [ ] It stays fixed
> <b>C.</b> Each step multiplies y by (1 − ηλ) = 1 − 2.5 = −1.5: sign flips and the size grows 1.5× per step. Stability needs |1 − ηλ| < 1, i.e. η < 0.02.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Three update rules

::: cards grid3
### [a] Gradient descent
w ← w − η∇L. Each eigen-direction shrinks by |1 − ηλᵢ| per step.

### [b] Momentum
v ← βv + ∇L, w ← w − ηv. Oscillations cancel across steps; consistent directions accelerate.

### [e] Adam
Running averages of g and g², bias-corrected; step ∝ m̂/(√v̂ + ε). Each coordinate gets its own effective rate.
:::

<div class="eq">stable iff η < 2 / λ_max   ·   speed set by κ = λ_max / λ_min</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## How LLM training uses these ideas

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Practice</th><th>Reason</th></tr>
  <tr><td>AdamW optimizer</td><td>per-coordinate scaling copes with very different gradient sizes across layers; decoupled weight decay</td></tr>
  <tr><td>Learning-rate warmup</td><td>early curvature and Adam's variance estimates are unreliable; start small to avoid divergence</td></tr>
  <tr><td>Decay schedule (cosine or step)</td><td>large steps to make progress, small steps to settle into a low region</td></tr>
  <tr><td>Gradient clipping</td><td>caps rare huge gradients that would overshoot (loss spikes)</td></tr>
  <tr><td>Large batches</td><td>reduce gradient noise, allowing larger stable learning rates up to a point</td></tr>
</table></div>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works despite non-convexity

::: cards grid2
### [a] Locally quadratic
Near any point the loss looks like a quadratic, so curvature analysis predicts stability and speed.

### [e] Saddles are escapable
Noise and momentum push off saddle points along negative-curvature directions.

### [b] Many good minima
Large networks have many equally good solutions; the job is reaching one efficiently.

### [c] Adaptivity helps
Adam's per-parameter scaling partly corrects ill-conditioning without computing the Hessian.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Deep learning gets stuck in bad local minima."
> In high dimensions most critical points are saddles; Dauphin et al. argue plateaus around saddles are the real obstacle.
:::

::: reveal myth
? "A larger learning rate always trains faster."
> Past 2/λ_max the steepest direction diverges; LLM runs use warmup and schedules for this reason.
:::

::: reveal myth
? "Adam needs no tuning."
> Its defaults are robust, but the learning rate, β₂ and warmup still matter at scale.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Curvatures 2 and 50. Largest stable learning rate for plain GD?
- [ ] 1
- [ ] 0.5
- [x] 0.04
- [ ] 0.02
> 2/λ_max = 2/50 = <b>0.04</b>.
:::

::: reveal
? What does the condition number κ control?
> How slowly the flattest direction converges once the learning rate is limited by the steepest: GD needs ~κ steps per e-fold; momentum ~√κ.
:::

::: reveal
? What two running statistics does Adam keep, and why bias-correct them?
> The mean of gradients (m) and of squared gradients (v); both start at 0 so early estimates are biased toward 0, corrected by dividing by 1 − βᵗ.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Gradient descent is stable only for η < 2/λ_max and is slowed by the condition number; momentum and Adam reduce that dependence, with warmup and schedules keeping big runs stable.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Gradient descent steps against the gradient, scaled by a learning rate. Near any point the loss looks like a quadratic bowl, and along each direction the error is multiplied by one minus the learning rate times the curvature, so the step must stay below two over the largest curvature or training diverges. With that cap, the flattest direction moves slowly, so the ratio of largest to smallest curvature, the condition number, sets the speed. Momentum averages steps to cancel oscillations and roughly takes the square root of that ratio; Adam scales each coordinate by its own gradient size.</p></div>
    <div class="recap"><div><span><b>Problem:</b> use gradients to descend a badly conditioned, saddle-filled landscape.</span></div><div><span><b>Core idea:</b> η < 2/λ_max; κ sets speed; momentum, Adam.</span></div><div><span><b>Practice:</b> AdamW, warmup, decay, clipping.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/math/06_gradient_descent.ipynb" target="_blank" rel="noopener">06 · Gradient descent, momentum and Adam</a> <span style="color:var(--faint)">· 30 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/math/06_gradient_descent.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../10-floating-point/index.html">10 · Floating-point numbers →</a> · Previous: <a href="../08-softmax-logsumexp/index.html">← 08</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
