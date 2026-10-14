---
title: Activation Functions
body:
  data-deck: Activation functions
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
  - 'pre-activation z :: z = xW + b :: f'
  - 'φ(z) :: elementwise nonlinearity :: a'
  - 'backward :: gradient × φ′(z) :: b'
  - 'many layers :: product of φ′ values :: d'
  caption: If |φ′| is small, gradients shrink geometrically with depth.
example:
  title: 'Worked example: gradients through 30 layers'
  setup: 'Notebook 03: 30 layers of width 256, weights scaled to preserve variance, batch of 256 random inputs; ratio of gradient size at the bottom layer to the
    top.'
  steps:
  - 'Sigmoid: σ′(z) = σ(z)(1 − σ(z)) ≤ <b>0.25</b>, so each layer can shrink the gradient 4×. Measured ratio after 30 layers: <b>7 × 10⁻¹⁹</b>.'
  - 'tanh (derivative ≤ 1, gain 1): <b>0.19</b>.'
  - 'ReLU with He scaling (gain 2): <b>4.7</b>; GELU with gain 2: <b>0.61</b>, both healthy.'
  - 'SiLU is sensitive to the scale: gain 2.0 gives 3 × 10⁻⁴, gain 2.25 keeps it near 1.'
  result: Non-saturating activations keep gradients usable through depth, together with the right initialisation (deck 06).
traps:
  tricks:
  - 'ReLU′ = 1 for z > 0. :: Gradients pass straight through active units.'
  - 'GELU(x) = x·Φ(x); SiLU(x) = x·σ(x). :: Smooth, slightly negative for small negative x.'
  - 'SwiGLU = (SiLU(xW) ⊙ xV)W₂. :: The gated MLP in Llama-style models.'
  traps:
  - 'Sigmoid in hidden layers of deep nets. :: Saturation and non-zero mean kill gradients.'
  - 'Dead ReLUs. :: Units stuck at z < 0 get zero gradient forever, often after too-large steps.'
  - 'Assuming the activation choice is cosmetic. :: It interacts with initialisation and depth.'
papers:
- relu
- gelu
- swish
- glu
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Neural Networks · 02</div>
    <h1>Activation functions</h1>
    <p class="sub">The elementwise nonlinearities that make networks more than matrix products: sigmoid and tanh, ReLU, and the smooth GELU and SiLU used in modern LLMs.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Without a nonlinearity a deep network is one linear map. But the wrong nonlinearity makes gradients vanish as they pass back through many layers.</div>
      <div class="c"><b>Core idea</b>Pick a φ whose derivative stays near 1 over the inputs it sees. <b>Sigmoid</b> and <b>tanh</b> saturate (σ' ≤ 1/4). <b>ReLU</b> passes gradient 1 for positive inputs. <b>GELU</b> = x·Φ(x) and <b>SiLU</b> = x·σ(x) are smooth versions used in BERT, GPT-2 and (as the SwiGLU gate) Llama.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Shapes and slopes

Pick an activation. The solid line is φ(z), the dashed line its derivative φ′(z). The shaded band marks where |φ′| < 0.1: inputs there pass almost no gradient back.
{: .lede}

<div class="visual">
  <div class="seg" id="aSeg"><button data-v="sigmoid">sigmoid</button><button data-v="tanh">tanh</button><button data-v="relu" class="on">ReLU</button><button data-v="gelu">GELU</button><button data-v="silu">SiLU</button></div>
  <svg id="aSvg" viewBox="0 0 660 250" style="margin-top:10px" role="img" aria-label="Activation function and derivative"></svg>
  <p class="readout" id="aOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## What goes wrong with the classics

::: cards grid3
### [d] Saturation
For large |z|, sigmoid and tanh are flat: φ′ ≈ 0, so no gradient flows back.

### [b] Small maximum slope
σ′ ≤ 1/4: even at its best, each sigmoid layer cuts the gradient by 4×.

### [c] Non-zero mean
Sigmoid outputs are all positive, which biases the next layer's gradients in one direction (Glorot & Bengio).
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Which keeps gradients alive?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Through 30 layers, which activation preserves gradient size best (with matching initialisation)?
- [ ] sigmoid
- [x] ReLU
- [ ] a step function
- [ ] no activation, but 30 linear layers
> <b>B.</b> ReLU has slope exactly 1 for active units. A step function has zero gradient everywhere it is defined, and purely linear layers collapse into one.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## The modern choices

::: cards grid2
### [a] ReLU
max(0, z). Cheap, non-saturating for z > 0, sparse activations (Nair & Hinton, 2010).

### [c] GELU
z·Φ(z), Φ the Gaussian CDF (cumulative distribution function). Smooth: weights inputs by value instead of gating by sign. BERT, GPT-2.

### [e] SiLU / Swish
z·σ(z), found by automated search (Ramachandran et al.). The gate inside SwiGLU.

### [b] Gated units (GLU family)
Multiply one projection by an activated other: (SiLU(xW) ⊙ xV). Shazeer (2020) found these improve transformers.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Activation by model family

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Model</th><th>MLP activation</th></tr>
  <tr><td>Original Transformer (2017)</td><td>ReLU</td></tr>
  <tr><td>BERT, GPT-2, GPT-3</td><td>GELU</td></tr>
  <tr><td>PaLM, Llama family, Mistral</td><td>SwiGLU (SiLU-gated)</td></tr>
</table></div>
<p class="caption">See <a href="../../architecture/04-swiglu/index.html">Architecture deck 04</a> for SwiGLU in detail.</p>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why the ReLU family works

::: cards grid2
### [a] Slope ≈ 1 where active
Gradients pass through active units unchanged, so deep stacks stay trainable.

### [e] Cheap
max, or a multiply by a sigmoid: negligible next to the matmuls.

### [b] Smoothness helps optimisation
GELU and SiLU have no kink at 0 and let small negative values through, which tends to train slightly better at scale.

### [c] Gating adds expressiveness
Multiplicative interactions in GLU variants give each unit an input-dependent gain.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "ReLU networks are linear."
> They are piecewise linear: every unit switching on or off creates a new region, so a deep ReLU net has a huge number of linear pieces.
:::

::: reveal myth
? "GELU is just a smoothed ReLU with no practical difference."
> Its behaviour near zero matters at scale; GELU and SiLU variants consistently edge out ReLU in transformers.
:::

::: reveal myth
? "Vanishing gradients were solved by ReLU alone."
> ReLU helps, but initialisation, normalisation and residual connections (decks 06–07) are just as important.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Maximum value of the sigmoid's derivative?
- [ ] 1
- [ ] 0.5
- [x] 0.25
- [ ] 0.1
> <b>0.25</b>, at z = 0.
:::

::: reveal
? What is a "dead" ReLU?
> A unit whose pre-activation is negative for all inputs: its output and gradient are 0, so it never recovers.
:::

::: reveal
? Write GELU and SiLU.
> GELU(z) = z·Φ(z) with Φ the standard normal CDF; SiLU(z) = z·σ(z).
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Activations make networks non-linear; saturating ones (sigmoid, tanh) kill gradients through depth, so modern LLMs use ReLU-like GELU and SiLU, usually inside a gated SwiGLU.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>An activation function is applied elementwise between linear layers so the network is not a single linear map. In the backward pass every gradient is multiplied by the activation's slope, so slopes much smaller than one compound through depth. Sigmoid's slope is at most a quarter and saturates for large inputs, which makes gradients vanish. ReLU passes slope one for positive inputs. GELU, z times the Gaussian CDF, and SiLU, z times the sigmoid, are smooth relatives; GPT-2 used GELU and Llama uses SiLU as the gate of its SwiGLU MLP.</p></div>
    <div class="recap"><div><span><b>Problem:</b> need non-linearity without vanishing gradients.</span></div><div><span><b>Core idea:</b> slope ≈ 1 where active: ReLU, GELU, SiLU.</span></div><div><span><b>In LLMs:</b> GELU (GPT-2), SwiGLU (Llama).</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/nn-fundamentals/03_activations_depth.ipynb" target="_blank" rel="noopener">03 · Activations and vanishing gradients</a> <span style="color:var(--faint)">· 25 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/nn-fundamentals/03_activations_depth.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../03-backpropagation/index.html">03 · Backpropagation →</a> · Previous: <a href="../01-perceptron-to-mlp/index.html">← 01</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
