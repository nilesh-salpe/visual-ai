---
title: Matrices and Linear Layers
body:
  data-deck: Matrices and linear layers
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
  - 'X :: tokens × d_in :: f'
  - '× W :: d_in × d_out :: a'
  - '= Y :: tokens × d_out :: c'
  - 'cost :: 2·m·k·n FLOPs :: b'
  caption: Inner dimensions must match; the outer ones give the result's shape.
example:
  title: 'Worked example: one GPT-3 projection'
  setup: GPT-3 175B uses d_model = 12,288 and 96 layers. Take one query projection Q = XW_Q for a 2,048-token sequence.
  steps:
  - 'Shapes: X is 2,048 × 12,288, W_Q is 12,288 × 12,288, so Q is 2,048 × 12,288; W_Q holds 151M parameters.'
  - 'FLOPs: 2 × 2,048 × 12,288 × 12,288 ≈ <b>0.62 TFLOP</b> for this one matmul.'
  - 'Each layer has about 12·d² weights in its matrices (4d² attention, 8d² MLP): 1.81B per layer, × 96 ≈ <b>174B</b>, nearly all of the 175B.'
  - So a forward pass costs about 2 FLOPs per parameter per token, and training about 6 (forward plus a backward that costs twice as much).
  result: LLM compute is overwhelmingly matrix multiplication; shapes tell you both the parameter count and the cost.
traps:
  tricks:
  - '(m × k)(k × n) = (m × n), 2mkn FLOPs. :: One multiply and one add per term.'
  - 'Parameters ≈ 12·L·d². :: For a standard transformer, ignoring embeddings.'
  - 'Forward ≈ 2N, training ≈ 6N FLOPs per token. :: N = parameters.'
  traps:
  - 'Mixing up row and column conventions. :: PyTorch stores nn.Linear weights as (out, in) and computes xWᵀ.'
  - 'Counting a multiply-add as 1 FLOP. :: Most papers count it as 2.'
  - 'Thinking matrices only scale. :: They rotate, stretch, shear and project, and can lose information (rank).'
papers:
- vaswani
- gpt3
- kaplan
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Math for LLMs · 02</div>
    <h1>Matrices and linear layers</h1>
    <p class="sub">What a matrix does to a vector, why every LLM layer is mostly matrix multiplication, and how to count its shapes and FLOPs.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>A transformer layer has to turn every token's vector into new vectors: queries, keys, values, MLP features. Doing that one number at a time would be hopeless.</div>
      <div class="c"><b>Core idea</b>A matrix W (d_in × d_out) maps a vector x to xW: each output is a dot product of x with one column. A <b>linear layer</b> is y = xW + b. Stacking tokens as rows turns a whole sequence into one <b>matmul</b> costing 2·m·k·n FLOPs (floating-point operations).</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## What does a matrix do to space?

A 2 × 2 matrix moves every point of the plane. Edit its entries and watch the unit square (and the two basis vectors) transform. The determinant is the area scale.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">a <input type="range" id="m11" min="-2" max="2" step="0.1" value="1.5"> <output id="m11o"></output></label>
    <label class="ctl">b <input type="range" id="m12" min="-2" max="2" step="0.1" value="0.5"> <output id="m12o"></output></label>
    <label class="ctl">c <input type="range" id="m21" min="-2" max="2" step="0.1" value="0"> <output id="m21o"></output></label>
    <label class="ctl">d <input type="range" id="m22" min="-2" max="2" step="0.1" value="1"> <output id="m22o"></output></label>
  </div>
  <svg id="mSvg" viewBox="0 0 660 260" style="margin-top:10px" role="img" aria-label="Linear transformation of the unit square"></svg>
  <p class="readout" id="mOut"></p>
</div>
<p class="caption">The matrix [[a, b], [c, d]] sends (1, 0) to (a, c) and (0, 1) to (b, d): its columns are where the basis vectors land.</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why not process each number separately?

::: cards grid3
### [d] Features mix
A useful new feature depends on many input coordinates at once; that is exactly a weighted sum, a dot product.

### [b] Loops are slow
Element-by-element code wastes hardware; Tensor Cores need dense matrix blocks.

### [c] Sequences are batches
Every token gets the same transformation, so stacking tokens as rows turns thousands of vector ops into one matmul.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What shape comes out?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? X has shape (2,048 × 4,096) and W has shape (4,096 × 11,008). What is the shape of XW?
- [ ] 4,096 × 4,096
- [x] 2,048 × 11,008
- [ ] 11,008 × 2,048
- [ ] It is undefined
> <b>B.</b> Inner dimensions (4,096) match and disappear; the result is (rows of X) × (columns of W). This is the MLP up-projection shape of Llama 2 7B.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## A linear layer is a matmul plus a bias

::: cards grid3
### [a] Matrix-vector
y = xW: output j is the dot product of x with column j of W.

### [c] Matrix-matrix
Stack m inputs as rows of X: Y = XW computes all of them at once.

### [e] Bias and composition
y = xW + b. Two linear layers in a row collapse into one, which is why networks put nonlinearities between them.
:::

<div class="eq">Y (m × n) = X (m × k) · W (k × n) + b   ·   cost 2·m·k·n FLOPs</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## The matrices inside one transformer layer

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Matrix</th><th>Shape</th><th>Parameters</th></tr>
  <tr><td>W_Q, W_K, W_V</td><td>d × d each</td><td>3d²</td></tr>
  <tr><td>W_O (attention output)</td><td>d × d</td><td>d²</td></tr>
  <tr><td>MLP up</td><td>d × 4d</td><td>4d²</td></tr>
  <tr><td>MLP down</td><td>4d × d</td><td>4d²</td></tr>
  <tr><td><b>Total</b></td><td></td><td><b>12d²</b></td></tr>
</table></div>
<p class="caption">Original GPT-style layer. Gated MLPs (SwiGLU) use three matrices with a smaller hidden size to keep about the same count; grouped-query attention shrinks W_K and W_V.</p>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why matrices are the workhorse

::: cards grid2
### [a] Expressive
Any linear map between vector spaces is a matrix; with nonlinearities in between, stacks of them approximate almost any function.

### [e] Hardware-friendly
Matmuls reuse each loaded number many times, so they run near peak on GPUs.

### [b] Easy to differentiate
The gradient of XW is another matmul: dW = Xᵀ·dY, dX = dY·Wᵀ.

### [c] Easy to count
Shapes give parameters and FLOPs directly, which is how model and training budgets are planned.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "A matrix just scales a vector."
> It can rotate, stretch along different directions, shear and project; only diagonal matrices scale coordinates independently.
:::

::: reveal myth
? "Stacking linear layers makes a deeper, more powerful model."
> Without nonlinearities, W₁W₂ is just another matrix: the stack is still one linear layer.
:::

::: reveal myth
? "Matmul cost depends only on the parameter count."
> It is 2·m·k·n: proportional to parameters × tokens processed.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? FLOPs for multiplying (1,000 × 500) by (500 × 200)?
- [ ] 10⁸
- [x] 2 × 10⁸
- [ ] 10⁵
- [ ] 5 × 10⁷
> 2 × 1,000 × 500 × 200 = <b>2 × 10⁸</b>.
:::

::: reveal
? Why do networks need nonlinearities between linear layers?
> Because the product of matrices is a matrix: without them the whole stack is a single linear map.
:::

::: reveal
? Roughly how many parameters does a transformer with L layers and width d have?
> About 12·L·d² (plus embeddings).
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">A matrix maps vectors by dot products with its columns; LLM layers are stacks of matmuls whose shapes give parameters (≈12d² per layer) and cost (2mkn FLOPs).</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Each output of a matrix-vector product is a dot product of the input with one column, so a matrix mixes all input features into each output feature. A linear layer is that plus a bias. Stacking tokens as rows makes a whole sequence one matrix multiplication, which costs two FLOPs per multiply-add: 2·m·k·n. A standard transformer layer has about 12d² weights in its attention and MLP matrices, which is why GPT-3 with d = 12,288 and 96 layers has about 175 billion parameters, and why a forward pass costs about 2 FLOPs per parameter per token.</p></div>
    <div class="recap"><div><span><b>Problem:</b> transform every token vector, fast.</span></div><div><span><b>Core idea:</b> Y = XW + b; (m×k)(k×n) costs 2mkn.</span></div><div><span><b>Count:</b> ≈ 12d² per layer; 2N FLOPs per token forward.</span></div></div>
    <p class="start-hint">Next: <a href="../03-eigen-svd-low-rank/index.html">03 · Eigenvalues, SVD and low rank →</a> · Previous: <a href="../01-vectors-dot-products/index.html">← 01</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
