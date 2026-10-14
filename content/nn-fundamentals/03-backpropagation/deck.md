---
title: Backpropagation
body:
  data-deck: Backpropagation
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
  - 'forward :: compute, record parents and op :: a'
  - 'topological order :: every node after its inputs :: c'
  - 'seed :: dL/dL = 1 :: d'
  - 'reverse walk :: grad += upstream × local :: b'
  - '.grad on every weight :: then optimizer step :: e'
  caption: Each op only needs its own backward rule; the graph does the rest.
example:
  title: 'Worked example: one neuron and a squared loss'
  setup: o = tanh(w₁x₁ + w₂x₂ + b) with x₁ = 2, x₂ = 0, w₁ = −3, w₂ = 1, b = 6.8814; loss = (o − 1)².
  steps:
  - 'Forward: w₁x₁ + w₂x₂ + b = −6 + 0 + 6.8814 = 0.8814; o = tanh(0.8814) = <b>0.7071</b>; loss = 0.0858.'
  - 'Backward: dloss/do = 2(o − 1) = -0.5858; tanh′ = 1 − o² = 0.5000, so dloss/dn = -0.2929.'
  - The sum passes that gradient unchanged to each term; the product w₁x₁ gives dloss/dw₁ = x₁ · that = <b>-0.5857</b>, and dloss/dw₂ = x₂ · that = <b>0</b>.
  - Notebook 01 builds exactly this graph with a Value class and checks dloss/dw₁ against a finite difference.
  result: Each node used one local rule; the chain rule happened automatically by walking the graph backwards.
traps:
  tricks:
  - 'Zero the gradients each step. :: Because backward accumulates (+=).'
  - 'A gradient has its tensor''s shape. :: dW for a (d × k) weight is (d × k).'
  - 'Backward ≈ 2× forward FLOPs. :: Two matmuls per linear layer (dX and dW).'
  traps:
  - 'Forgetting to zero grads. :: Gradients from previous steps silently add up.'
  - 'Detaching by accident. :: Converting to NumPy or using .item() cuts the graph.'
  - 'Overwriting instead of accumulating. :: A value used twice must receive both contributions.'
papers:
- rumelhart
- baydin
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Neural Networks · 03</div>
    <h1>Backpropagation</h1>
    <p class="sub">How frameworks like PyTorch compute every gradient automatically: record the operations, then apply each one's local derivative in reverse order. Built from scratch in notebook 01.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>A network is millions of operations. Writing the derivative of the loss with respect to every weight by hand is impossible, and numerical estimates would cost one forward pass per weight.</div>
      <div class="c"><b>Core idea</b>During the forward pass, <b>record a graph</b> of operations and their inputs. Then walk it in <b>reverse topological order</b>, each node passing grad × local derivative to its parents and <b>accumulating</b> (+=) where values are reused. That is reverse-mode automatic differentiation.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Walk the tape forward, then back

The expression L = (tanh(w·x + b) − y)² recorded as a list of operations. Step forward to fill in values, then backward to fill in gradients, one node at a time.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><button class="btn primary" id="bNext">next step</button><button class="btn" id="bReset">reset</button></div>
  <div class="scroll-x" style="margin-top:10px"><table class="tbl" id="bTbl"></table></div>
  <p class="readout" id="bOut"></p>
</div>
<p class="caption">w = 0.5, x = 2, b = −0.3, y = 1.</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why not differentiate some other way?

::: cards grid3
### [d] By hand
Every architecture change would need new derivative code; error-prone at any real size.

### [b] Numerically
Finite differences need one forward pass per parameter: billions per step.

### [c] Symbolically
Expanding the full formula duplicates shared sub-expressions and explodes in size.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What must happen first?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Before calling a node's backward rule, what must be true?
- [ ] Its value must be zero
- [x] Its gradient must be complete: all nodes that use it have already pushed their contribution
- [ ] Its parents must have gradients
- [ ] Nothing
> <b>B.</b> That is why backward runs in reverse topological order: every consumer of a value is processed before the value itself.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Record, order, reverse

::: cards grid3
### [a] Record
Each operation returns a new node that stores its inputs and a small backward function.

### [c] Order
A depth-first search gives a topological order: each node appears after its inputs.

### [b] Reverse and accumulate
Set dL/dL = 1, then for each node in reverse order: parent.grad += node.grad × ∂node/∂parent.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Backward rules you need for an LLM

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Op</th><th>Forward</th><th>Backward (given upstream g)</th></tr>
  <tr><td>add</td><td>c = a + b</td><td>da += g, db += g</td></tr>
  <tr><td>multiply</td><td>c = a·b</td><td>da += g·b, db += g·a</td></tr>
  <tr><td>matmul</td><td>Y = XW</td><td>dX += g·Wᵀ, dW += Xᵀ·g</td></tr>
  <tr><td>ReLU</td><td>y = max(0, x)</td><td>dx += g·1[x > 0]</td></tr>
  <tr><td>softmax + cross-entropy</td><td>L = −log softmax(z)ₜ</td><td>dz += p − onehot(t)</td></tr>
  <tr><td>sum / mean</td><td>s = Σ x</td><td>dx += g (÷ n for mean)</td></tr>
</table></div>

::: deep PyTorch in one sentence
Every tensor operation records a node (`grad_fn`); `loss.backward()` runs exactly this reverse topological walk over tensors, and `optimizer.zero_grad()` resets the accumulated `.grad` fields.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why reverse mode is the right choice

::: cards grid2
### [a] One pass for all weights
One scalar loss, billions of parameters: reverse mode costs about one extra pass; forward mode would cost one pass per parameter.

### [e] Local and composable
New layers only need a forward and a local backward rule.

### [b] Exact
Uses analytic local derivatives, so results match finite differences to rounding error.

### [d] Costs memory
Forward values must be kept for the backward pass, the source of activation memory (Distributed deck 08).
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Backpropagation is how the network learns."
> Backprop only computes gradients; the optimizer (SGD, Adam) uses them to change the weights.
:::

::: reveal myth
? "Autograd approximates derivatives."
> It applies exact local derivatives; only floating-point rounding differs.
:::

::: reveal myth
? "Gradients overwrite each other when a value is reused."
> They add: a value used in two places receives the sum of both contributions.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? c = a·b with a = 3, b = −2 and dL/dc = 5. What is dL/da?
- [x] −10
- [ ] 15
- [ ] −2
- [ ] 5
> g·b = 5 × (−2) = <b>−10</b>.
:::

::: reveal
? Why does backward use reverse topological order?
> So every node's gradient is complete, with contributions from all its consumers, before it is propagated to its own inputs.
:::

::: reveal
? Why do you call zero_grad() every step in PyTorch?
> backward() accumulates into .grad; without zeroing, gradients from earlier steps would add up.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Backpropagation records the forward computation as a graph, then walks it in reverse topological order applying local derivative rules and accumulating gradients.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Automatic differentiation makes training practical. During the forward pass every operation records its inputs and a small backward rule. Calling backward on the loss sets its gradient to one, sorts the graph so each node comes after its inputs, and walks it in reverse: each node multiplies its gradient by its local derivative and adds the result into each input's gradient. Adding matters because values can be reused. This is reverse-mode differentiation: one backward pass gives the gradient for every weight at about twice the forward cost, which is why frameworks like PyTorch can train any architecture you can write.</p></div>
    <div class="recap"><div><span><b>Problem:</b> gradients of one loss w.r.t. billions of weights.</span></div><div><span><b>Core idea:</b> record graph; reverse topological walk; accumulate.</span></div><div><span><b>Practice:</b> zero grads each step; keep activations.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/nn-fundamentals/01_micrograd.ipynb" target="_blank" rel="noopener">01 · Build an autograd engine (micrograd-style)</a> <span style="color:var(--faint)">· 40 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/nn-fundamentals/01_micrograd.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../04-loss-functions/index.html">04 · Loss functions →</a> · Previous: <a href="../02-activation-functions/index.html">← 02</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
