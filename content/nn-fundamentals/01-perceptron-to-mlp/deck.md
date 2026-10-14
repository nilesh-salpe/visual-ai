---
title: From Perceptron to MLP
body:
  data-deck: From perceptron to MLP
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
  - 'input x :: raw features :: f'
  - 'hidden h = φ(xW₁ + b₁) :: new features :: a'
  - 'output y = hW₂ + b₂ :: linear read-out :: c'
  - 'loss + backprop :: learn W₁, W₂ :: e'
  caption: 'A transformer''s MLP block is exactly this: up-projection, nonlinearity, down-projection.'
example:
  title: 'Worked example: XOR with two hidden ReLUs'
  setup: Inputs (0,0), (0,1), (1,0), (1,1) with labels 0, 1, 1, 0.
  steps:
  - Any line w·x + b = 0 gets at most 3 of the 4 points right; notebook 02 checks 20,000 random lines and the best is exactly <b>75%</b>.
  - 'Hidden units: h₁ = ReLU(x₁ + x₂), h₂ = ReLU(x₁ + x₂ − 1). The four points map to (0,0), (1,0), (1,0), (2,1).'
  - 'Output y = h₁ − 2h₂ gives 0, 1, 1, 0: <b>XOR solved</b>, because in (h₁, h₂) space a straight line separates the classes.'
  - 'Learning it from a random start: with 2 hidden units gradient descent solved XOR in 9 of 20 runs; with 8 hidden units, 20 of 20 (notebook 02).'
  result: The nonlinearity lets the hidden layer bend the space; extra width makes the solution easier to find, not just possible.
traps:
  tricks:
  - 'Linear layers compose to one linear layer. :: Nonlinearities are what make depth useful.'
  - 'Width helps optimisation. :: Over-parameterised networks find good solutions more reliably.'
  - 'The transformer MLP is a 2-layer MLP. :: d → 4d → d (or a gated SwiGLU variant).'
  traps:
  - 'Reading universal approximation as "one layer is enough in practice". :: It may need exponentially many units; depth is far more efficient.'
  - 'Forgetting the bias. :: Without b, every boundary passes through the origin.'
  - 'Symmetric initialisation. :: Identical hidden units get identical gradients and never differentiate.'
papers:
- rumelhart
- hornik
- cybenko
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Neural Networks · 01</div>
    <h1>From perceptron to MLP</h1>
    <p class="sub">Why a single neuron can only draw a straight line, how one hidden layer with a nonlinearity fixes that, and why depth is the backbone of every LLM block.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>A single linear unit computes w·x + b and thresholds it: one straight boundary. Many simple patterns, starting with XOR, cannot be separated by any straight line.</div>
      <div class="c"><b>Core idea</b>Stack layers: a <b>hidden layer</b> h = φ(xW₁ + b₁) with a <b>nonlinearity</b> φ, then an output layer on h. The hidden layer re-maps the inputs so a straight boundary works in its space. With enough hidden units one layer can approximate any continuous function (<b>universal approximation</b>).</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## One line can't separate XOR

In input space, rotate and shift a straight decision boundary: no setting gets all four XOR points right. Switch to the hidden space of a 2-unit ReLU layer and the same points become separable.
{: .lede}

<div class="visual">
  <div class="seg" id="xSeg"><button data-v="in" class="on">input space (x₁, x₂)</button><button data-v="hid">hidden space (h₁, h₂)</button></div>
  <div class="controls"><label class="ctl">boundary angle <input type="range" id="xA" min="0" max="359" step="1" value="135"> <output id="xAo"></output></label><label class="ctl">offset <input type="range" id="xB" min="-1.5" max="1.5" step="0.05" value="-0.5"> <output id="xBo"></output></label></div>
  <svg id="xSvg" viewBox="0 0 660 260" style="margin-top:10px" role="img" aria-label="XOR decision boundary"></svg>
  <p class="readout" id="xOut"></p>
</div>
<p class="caption">Hidden layer: h₁ = ReLU(x₁ + x₂), h₂ = ReLU(x₁ + x₂ − 1). Teal = label 1, orange = label 0.</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## The limits of a single neuron

::: cards grid3
### [d] One straight boundary
A perceptron thresholds w·x + b, so it can only separate classes with a hyperplane.

### [b] Hand-made features don't scale
You could add x₁·x₂ by hand for XOR, but real tasks need features nobody can design.

### [c] Stacking linear layers doesn't help
W₂(W₁x) = (W₂W₁)x: still one linear map.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What does the hidden layer need?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? You stack two linear layers with no activation in between. Can the result solve XOR?
- [ ] Yes, it has two layers
- [x] No: it is still a single linear map
- [ ] Only with enough hidden units
- [ ] Only with a bias
> <b>B.</b> W₂(W₁x + b₁) + b₂ is again linear in x. A nonlinearity between the layers is what lets the network bend its decision boundary.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## The multilayer perceptron

::: cards grid3
### [a] Hidden layer
h = φ(xW₁ + b₁): each unit is a learned feature, a dot product followed by a nonlinearity.

### [c] Output layer
y = hW₂ + b₂, a linear read-out of the learned features (then softmax for classification).

### [e] Universal approximation
One hidden layer with enough units approximates any continuous function on a bounded domain (Cybenko; Hornik et al., 1989).
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Where MLPs live inside an LLM

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Piece</th><th>Shape</th><th>What it does</th></tr>
  <tr><td>MLP up-projection</td><td>d → 4d (or ≈ 8d/3 ×2 for SwiGLU)</td><td>creates many candidate features per token</td></tr>
  <tr><td>Nonlinearity</td><td>elementwise (GELU, SiLU gate)</td><td>lets features be non-linear functions of the input</td></tr>
  <tr><td>MLP down-projection</td><td>4d → d</td><td>writes the selected features back to the residual stream</td></tr>
  <tr><td>Share of parameters</td><td>8d² of ≈ 12d² per layer</td><td>about two thirds of a standard transformer's weights</td></tr>
</table></div>

::: deep Depth vs width
One wide layer can approximate anything in principle, but some functions need exponentially many units at depth 1 and only polynomially many with more layers. LLMs stack dozens of blocks, each with attention and an MLP.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why hidden layers work

::: cards grid2
### [a] Learned features
Training chooses W₁ so the hidden units become whatever features make the output's job easy.

### [e] Composable
Each layer's features are built from the previous layer's: edges → shapes → objects, or tokens → phrases → meaning.

### [b] Trainable end to end
Backpropagation (deck 03) gives gradients for every layer at once.

### [c] Over-parameterisation helps
Extra hidden units make gradient descent find good solutions far more reliably (notebook 02).
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Neural networks are just big logistic regressions."
> Logistic regression is the last layer; the hidden layers learn the features it uses, which is the whole point.
:::

::: reveal myth
? "Universal approximation means any network can learn anything."
> It says a suitable network exists, not that gradient descent will find it or that it is small.
:::

::: reveal myth
? "Each neuron detects one human-meaningful concept."
> Features are often distributed across many units and units mix several features.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Best accuracy of any linear classifier on XOR?
- [ ] 50%
- [x] 75%
- [ ] 100%
- [ ] 25%
> <b>75%</b>: any line misclassifies at least one of the four points.
:::

::: reveal
? Why must there be a nonlinearity between layers?
> Without it the composition of linear layers is a single linear map, no more expressive than one layer.
:::

::: reveal
? What fraction of a standard transformer layer's weights are in the MLP?
> About two thirds: 8d² of roughly 12d².
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">A hidden layer with a nonlinearity learns new features in which a straight boundary works; stacking such layers is the core of every neural network, including each LLM block's MLP.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>A single neuron computes a weighted sum and thresholds it, so it can only draw one straight boundary, and some patterns such as XOR cannot be separated that way. Adding a hidden layer with a nonlinearity changes that: the hidden units compute new features, and in their space a straight line works. With enough hidden units one layer can approximate any continuous function, but deep stacks do it far more efficiently. Without the nonlinearity, stacked linear layers collapse into one. The MLP inside every transformer block is exactly this: project up, apply a nonlinearity, project down.</p></div>
    <div class="recap"><div><span><b>Problem:</b> one neuron = one straight boundary.</span></div><div><span><b>Core idea:</b> hidden layer + nonlinearity learns features.</span></div><div><span><b>In LLMs:</b> the d → 4d → d MLP in every block.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/nn-fundamentals/02_mlp_numpy.ipynb" target="_blank" rel="noopener">02 · An MLP from scratch: solving XOR</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/nn-fundamentals/02_mlp_numpy.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../02-activation-functions/index.html">02 · Activation functions →</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
