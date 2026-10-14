---
title: Derivatives and the Chain Rule
body:
  data-deck: Derivatives and the chain rule
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
  - 'forward :: compute and cache values :: a'
  - 'loss :: one scalar :: d'
  - 'backward :: multiply local derivatives :: b'
  - 'sum over paths :: where a value is reused :: c'
  - 'all gradients :: ≈ 2× forward cost :: e'
  caption: 'Reverse mode suits LLMs: one scalar output, billions of inputs.'
example:
  title: 'Worked example: f(x, y) = (x·y + sin x)² at x = 1, y = 2'
  setup: 'Nodes: a = x·y, b = sin x, c = a + b, f = c².'
  steps:
  - 'Forward: a = 2, b = sin 1 ≈ 0.841, c ≈ 2.841, f ≈ <b>8.074</b>.'
  - 'Backward: ∂f/∂c = 2c ≈ 5.683; ∂c/∂a = ∂c/∂b = 1.'
  - 'x reaches f by two paths: through a (∂a/∂x = y = 2) and through b (∂b/∂x = cos 1 ≈ 0.540). So ∂f/∂x = 2c·(2 + 0.540) ≈ <b>14.44</b>.'
  - 'y has one path: ∂f/∂y = 2c·x ≈ <b>5.68</b>. Notebook 03 checks both against finite differences.'
  result: Multiply along each path, add across paths; cache forward values because the backward pass needs them.
traps:
  tricks:
  - 'Gradient has the parameter''s shape. :: Use it to check matrix calculus.'
  - 'Linear layer: dW = Xᵀ·dY, dX = dY·Wᵀ. :: Both are matmuls.'
  - 'Gradient check with central differences. :: (f(x+ε) − f(x−ε)) / 2ε, ε ≈ 10⁻⁵.'
  traps:
  - 'Forgetting a path. :: Reused values (residuals, shared weights) need their gradients summed.'
  - 'Dropping cached activations. :: Backward needs forward values (or recomputation).'
  - 'Using forward mode for training. :: It costs one pass per input; reverse mode costs one pass per output.'
papers:
- rumelhart
- baydin
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Math for LLMs · 04</div>
    <h1>Derivatives and the chain rule</h1>
    <p class="sub">How a model finds which way to nudge billions of weights: local derivatives, the chain rule over a computational graph, and why backpropagation costs only about one extra pass.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Training needs ∂loss/∂w for every one of billions of weights, and the loss depends on each weight through a long chain of operations.</div>
      <div class="c"><b>Core idea</b>Break the computation into simple nodes with known <b>local derivatives</b>. The <b>chain rule</b> says the derivative along a path is the product of local derivatives, summed over paths. Running it from the loss backwards (<b>reverse-mode autodiff</b>, i.e. backprop) yields all gradients in one sweep.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Which way should each input move?

The graph computes L = (w·x + b − y)² for one data point. Move w and b: the forward values flow right, and the gradients (orange) flow back, each the product of local derivatives.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">w <input type="range" id="gW" min="-3" max="3" step="0.1" value="0.5"> <output id="gWo"></output></label>
    <label class="ctl">b <input type="range" id="gB" min="-3" max="3" step="0.1" value="0"> <output id="gBo"></output></label>
  </div>
  <svg id="gSvg" viewBox="0 0 660 260" style="margin-top:10px" role="img" aria-label="Computational graph with gradients"></svg>
  <p class="readout" id="gOut"></p>
</div>
<p class="caption">Fixed data point x = 2, target y = 3.</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why not estimate gradients numerically?

::: cards grid3
### [d] One pass per weight
Finite differences nudge each weight separately: 7 billion weights means 7 billion forward passes per step.

### [b] Inaccurate
Too large an ε gives approximation error, too small gives floating-point cancellation.

### [c] Symbolic is huge
Writing out the derivative formula of a deep network symbolically explodes in size.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## How many paths?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? In f(x, y) = (x·y + sin x)², how many paths connect x to f in the computational graph?
- [ ] 1
- [x] 2
- [ ] 3
- [ ] 0
> <b>B.</b> One through x·y and one through sin x. The chain rule adds the contributions of both paths.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Local derivatives, multiplied and summed

::: cards grid3
### [a] Local derivative
Each node knows its own derivative: d(sin u)/du = cos u, d(u·v)/du = v, d(u²)/du = 2u.

### [b] Chain rule
Along a path, multiply: ∂f/∂x = ∂f/∂c · ∂c/∂a · ∂a/∂x.

### [c] Multiple paths
If x feeds several nodes, add the path contributions. Reverse mode accumulates these sums node by node.
:::

<div class="eq">∂L/∂x = Σ over paths Π (local derivatives along the path)</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Forward mode vs reverse mode

<div class="visual scroll-x"><table class="tbl">
  <tr><th></th><th>Forward mode</th><th>Reverse mode (backprop)</th></tr>
  <tr><td>Direction</td><td>inputs → outputs, carrying ∂/∂x for one input</td><td>output → inputs, carrying ∂L/∂(node)</td></tr>
  <tr><td>Cost for all gradients</td><td>one pass per input</td><td>one pass per output</td></tr>
  <tr><td>Best when</td><td>few inputs, many outputs</td><td>many inputs, one scalar loss</td></tr>
  <tr><td>Memory</td><td>small</td><td>must keep forward values (activations)</td></tr>
</table></div>

::: deep Why the backward pass costs about 2× the forward
For a linear layer Y = XW, backward computes two matmuls of the same size: dX = dY·Wᵀ and dW = Xᵀ·dY. That is why training FLOPs ≈ 3 × forward ≈ 6 per parameter per token.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why backpropagation scales

::: cards grid2
### [a] One sweep for all weights
Reverse mode gets the gradient of one scalar with respect to every input for a small constant multiple of the forward cost.

### [e] Purely local rules
Each operation needs only its own derivative; frameworks compose them automatically (autograd).

### [b] Reuses forward work
Cached activations make each backward step a cheap matmul or elementwise product.

### [d] The price is memory
Keeping activations is what makes long-sequence training memory-bound (Distributed deck 08).
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Backpropagation is a special learning algorithm for neural nets."
> It is just the chain rule applied in reverse order (reverse-mode automatic differentiation); the learning is done by gradient descent.
:::

::: reveal myth
? "Autodiff is numerical differentiation."
> It is exact up to floating-point rounding: it applies analytic local derivatives, with no ε.
:::

::: reveal myth
? "Each weight needs its own backward pass."
> One backward pass produces gradients for all weights at once.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? For L = (wx − y)² with w = 1, x = 2, y = 3, what is ∂L/∂w?
- [x] −4
- [ ] −2
- [ ] 2
- [ ] 4
> wx − y = −1, so ∂L/∂w = 2·(−1)·x = <b>−4</b>.
:::

::: reveal
? What does the backward pass need from the forward pass?
> The intermediate values (activations) at each node, to evaluate local derivatives.
:::

::: reveal
? Why is reverse mode used for training instead of forward mode?
> There is one scalar loss and billions of parameters: reverse mode costs one pass for all of them; forward mode would need one per parameter.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Backprop is the chain rule run backwards: multiply local derivatives along paths, add over paths, and get every gradient for about twice the forward cost.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Training needs the derivative of one scalar loss with respect to billions of weights. Break the computation into nodes with simple local derivatives. The chain rule says the derivative along a path is the product of the local derivatives, and when a value feeds several nodes the paths add. Running this from the loss backwards, reverse-mode automatic differentiation, gives every gradient in one sweep at roughly twice the cost of the forward pass, as long as the forward values are kept. Finite differences are only used to check the result.</p></div>
    <div class="recap"><div><span><b>Problem:</b> gradients for billions of weights.</span></div><div><span><b>Core idea:</b> chain rule: multiply along paths, sum over paths.</span></div><div><span><b>Cost:</b> one backward ≈ 2× forward; needs cached activations.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/math/03_chain_rule_gradcheck.ipynb" target="_blank" rel="noopener">03 · Chain rule by hand and gradient checking</a> <span style="color:var(--faint)">· 30 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/math/03_chain_rule_gradcheck.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../05-probability-sampling/index.html">05 · Probability and sampling →</a> · Previous: <a href="../03-eigen-svd-low-rank/index.html">← 03</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
