---
title: Initialization
body:
  data-deck: Initialization
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
  - 'h :: variance s² :: f'
  - '× W :: variance × fan_in·Var(w) :: a'
  - 'φ :: × activation factor (½ for ReLU) :: b'
  - 'next layer :: want s² again :: e'
  loop: '3 -> 0 :: every layer'
  caption: Per-layer factor 1 → stable at any depth; 0.9 or 1.1 → vanishes or explodes geometrically.
example:
  title: 'Worked example: 50 ReLU layers of width 256'
  setup: 'Notebook 05: push standard-normal inputs through 50 layers h ← ReLU(hW), W 256 × 256, and measure the activation std.'
  steps:
  - 'Weights with std 1: each layer multiplies the variance by 256 × ½ = 128. After 50 layers the std is <b>6 × 10⁵²</b>.'
  - 'Xavier (Var = 2/512 = 1/256): factor 256 × (1/256) × ½ = ½ per layer. After 50 layers: <b>3.7 × 10⁻⁸</b>.'
  - 'He (Var = 2/256): factor 256 × (2/256) × ½ = 1. After 50 layers: <b>1.24</b>, the same order as at the start.'
  - tanh with std-1 weights keeps std ≈ 1 only because every unit is saturated at ±1, where gradients are ≈ 0.
  result: 'Initialisation is a variance budget: match fan_in·Var(w) to the activation and depth stops being a problem at the start of training.'
traps:
  tricks:
  - 'He: std = √(2/fan_in). :: ReLU family.'
  - 'Xavier: std = √(2/(fan_in + fan_out)). :: tanh / linear.'
  - 'Scale residual branches by ~1/√(2L). :: GPT-2-style init for deep stacks.'
  traps:
  - 'All-zero (or identical) weights. :: Every unit gets the same gradient: symmetry is never broken.'
  - 'Ignoring the activation. :: Xavier is half the right variance for ReLU.'
  - 'Only checking the forward pass. :: Saturation can keep activations bounded while gradients die.'
papers:
- glorot
- he_init
- gpt2
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Neural Networks · 06</div>
    <h1>Initialization</h1>
    <p class="sub">Why the random scale of the starting weights decides whether a deep network trains at all, and how Xavier and He initialisation keep signals at a constant size.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Each layer multiplies activations by a random matrix. If that multiplies their size by even 1.1 or 0.9, after 50 layers the signal has exploded or vanished.</div>
      <div class="c"><b>Core idea</b>Choose Var(w) so each layer <b>preserves variance</b>: fan_in × Var(w) × (activation's factor) = 1. <b>Xavier</b>: Var = 2/(fan_in + fan_out), for tanh-like activations. <b>He</b>: Var = 2/fan_in, for ReLU, which zeroes half its inputs.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Signal size through depth

Activation std after each of 50 layers (log scale) for a random batch, computed live in your browser. Change the weight scale and activation.
{: .lede}

<div class="visual">
  <div class="seg" id="iSeg"><button data-v="naive">std 1</button><button data-v="xavier">Xavier</button><button data-v="he" class="on">He</button></div>
  <div class="seg" id="iAct" style="margin-top:8px"><button data-v="relu" class="on">ReLU</button><button data-v="tanh">tanh</button></div>
  <svg id="iSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Activation scale vs depth"></svg>
  <p class="readout" id="iOut"></p>
</div>
<p class="caption">Width 64, batch 64, a fresh random matrix per layer.</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why scale matters so much

::: cards grid3
### [d] Geometric growth
Variance is multiplied by the same factor every layer: 1.1⁵⁰ ≈ 117, 0.9⁵⁰ ≈ 0.005.

### [b] Gradients follow
The backward pass multiplies by the transposed weights, so the same factor applies to gradients.

### [c] Symmetry
Starting with equal weights makes all units identical forever; randomness is required.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Which variance for ReLU?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Fan-in 1,024 with ReLU. Which weight variance preserves activation variance?
- [ ] 1/1,024
- [x] 2/1,024
- [ ] 1
- [ ] 1/2,048
> <b>B.</b> He: 2/fan_in. ReLU zeroes half its inputs, halving the second moment, so the weights must make up a factor of 2.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## A variance budget per layer

::: cards grid3
### [a] The rule
Var(out) ≈ fan_in · Var(w) · Var(in) · c, where c = 1 for linear/tanh near 0 and ½ for ReLU.

### [c] Xavier / Glorot
Var(w) = 2/(fan_in + fan_out): balances forward and backward for tanh-like units.

### [e] He / Kaiming
Var(w) = 2/fan_in: exactly preserves variance for ReLU, letting very deep ReLU nets train from scratch.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## How transformers are initialised

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Weights</th><th>Typical scheme</th></tr>
  <tr><td>Linear layers</td><td>normal with std ≈ 0.02 (GPT-2) or ∝ 1/√d</td></tr>
  <tr><td>Residual output projections</td><td>scaled by 1/√N, N = number of residual layers (GPT-2)</td></tr>
  <tr><td>Embeddings</td><td>small normal</td></tr>
  <tr><td>Norm gains / biases</td><td>1 / 0</td></tr>
</table></div>
<p class="caption">GPT-2: "We scale the weights of residual layers at initialization by a factor of 1/√N where N is the number of residual layers." Normalisation (next deck) makes transformers much less sensitive than plain deep MLPs.</p>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why variance preservation works

::: cards grid2
### [a] Signals stay in range
Activations neither saturate nor vanish, so every layer starts in a useful regime.

### [e] Gradients stay in range
The same analysis applies backward, so early layers receive meaningful updates.

### [b] Cheap
It only sets the scale of the random draw; no extra computation.

### [c] Complements normalisation
Norm layers fix scale during training; good init makes the first steps sane.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Initialisation only matters for the first few steps."
> A bad start can leave units dead or saturated permanently, or make training diverge immediately.
:::

::: reveal myth
? "Any small random numbers are fine."
> "Small" must be relative to fan-in and activation; too small vanishes just as surely as too large explodes.
:::

::: reveal myth
? "With normalisation layers init is irrelevant."
> It matters less, but residual-branch scaling still affects stability of deep transformers.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? He initialisation std for fan-in 512?
- [ ] 1/512
- [x] √(2/512) ≈ 0.0625
- [ ] √(1/512) ≈ 0.044
- [ ] 0.02
> √(2/512) = <b>0.0625</b>.
:::

::: reveal
? What happens if all weights start equal?
> All hidden units compute the same thing and get the same gradient, so they stay identical: the layer acts like one unit.
:::

::: reveal
? Why does ReLU need twice the weight variance of a linear layer?
> It zeroes half the inputs, halving the second moment of its output.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Initialise so each layer preserves variance (He 2/fan_in for ReLU, Xavier for tanh); otherwise signals and gradients explode or vanish geometrically with depth.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Each layer multiplies activations by a random matrix, so their variance is multiplied by fan-in times the weight variance times a factor from the activation. Repeated fifty times, any factor other than one explodes or vanishes geometrically, and gradients behave the same way. Xavier initialisation sets the variance to two over fan-in plus fan-out for tanh-like units; He initialisation uses two over fan-in for ReLU, which zeroes half its inputs. Weights must also be random to break symmetry. Transformers add tricks such as scaling residual output projections by one over the square root of the depth.</p></div>
    <div class="recap"><div><span><b>Problem:</b> per-layer scale compounds over depth.</span></div><div><span><b>Core idea:</b> fan_in·Var(w)·c = 1: Xavier, He.</span></div><div><span><b>Transformers:</b> std ≈ 0.02, residual scaling 1/√N.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/nn-fundamentals/05_initialization.ipynb" target="_blank" rel="noopener">05 · Initialization: keeping signals alive</a> <span style="color:var(--faint)">· 25 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/nn-fundamentals/05_initialization.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../07-normalization-residuals/index.html">07 · Normalization and residual connections →</a> · Previous: <a href="../05-optimizers/index.html">← 05</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
