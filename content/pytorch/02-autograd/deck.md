---
title: Autograd
body:
  data-deck: Autograd
  data-home: ../index.html
  data-home-label: PyTorch
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'leaf tensors :: requires_grad=True :: f'
  - 'forward :: each op records grad_fn :: a'
  - 'loss.backward() :: reverse walk :: b'
  - '.grad += … :: accumulates :: c'
  - 'zero_grad() :: before the next step :: e'
  loop: '4 -> 1 :: every step'
  caption: Theory in NN fundamentals deck 03 (Backpropagation).
example:
  title: 'Worked example: accumulating over micro-batches'
  setup: A batch of 32 examples that does not fit in memory at once; split into k = 4 micro-batches of 8 (notebook 02).
  steps:
  - 'For each micro-batch: loss = mse(model(xᵢ), yᵢ) / 4, then loss.backward(). Do not zero gradients in between.'
  - Because .backward() adds into .grad, after 4 calls each .grad holds the sum of the four scaled gradients.
  - 'That equals the gradient of the mean loss over all 32 examples: the notebook checks every parameter matches to 10⁻⁶.'
  - Forgetting the ÷ 4 gives a gradient 4× too large; forgetting zero_grad() before the next step adds the previous batch's gradient as well.
  result: Accumulation is how large effective batch sizes fit in limited memory, and it relies on .grad adding up.
traps:
  tricks:
  - 'zero_grad(set_to_none=True). :: Default in recent PyTorch; saves memory.'
  - 'Divide by k when accumulating. :: Keeps the gradient equal to the mean.'
  - 'gradcheck in float64. :: Validates custom backward functions.'
  traps:
  - 'In-place ops on saved tensors. :: Raise "modified by an inplace operation" at backward.'
  - 'Calling backward twice. :: The graph is freed after the first call unless retain_graph=True.'
  - 'Using .data. :: Bypasses autograd silently; use detach() or no_grad().'
papers:
- pytorch
- pt_autograd
status: {label: current, reviewed: 2026-10-15, note: "PyTorch 2.14.1 is still the latest release"}
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">PyTorch for LLMs · 02</div>
    <h1>Autograd in PyTorch</h1>
    <p class="sub">How PyTorch records the graph during the forward pass, what .backward() and .grad do, why gradients accumulate, and how no_grad, detach, frozen parameters and custom Functions fit in.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>You need gradients for millions of parameters from arbitrary Python code, sometimes across micro-batches, sometimes with parts frozen, sometimes with custom operations.</div>
      <div class="c"><b>Core idea</b>Every operation on a tensor with <code>requires_grad=True</code> records a <b>grad_fn</b> node. <code>loss.backward()</code> walks the graph in reverse and <b>adds</b> gradients into each leaf's <code>.grad</code>. <code>torch.no_grad()</code> stops recording, <code>detach()</code> cuts a tensor out of the graph, and <code>torch.autograd.Function</code> lets you define your own backward.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Gradients add up

Four micro-batches, each contributing a gradient. Step through backward calls and watch .grad accumulate. Toggle the two classic mistakes.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><button class="btn primary" id="gNext">backward()</button><button class="btn" id="gZero">zero_grad()</button><label class="ctl"><input type="checkbox" id="gDiv" checked> divide loss by k</label></div>
  <div id="gBars" style="margin-top:12px"></div>
  <p class="readout" id="gOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## What a framework must handle

::: cards grid3
### [d] Arbitrary code
Python loops, conditionals and indexing must all be differentiable.

### [b] Memory
The forward pass must keep exactly the tensors the backward pass needs.

### [c] Control
Users need to freeze parts, stop gradients and add custom operations.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What does this print?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? w = torch.ones(3, requires_grad=True); (w * 2).sum().backward(); (w * 2).sum().backward(); print(w.grad)
- [ ] tensor([2., 2., 2.])
- [x] tensor([4., 4., 4.])
- [ ] an error
- [ ] None
> <b>B.</b> Each backward adds 2 to every element of .grad, so two calls give 4. That is why training loops call zero_grad() every step.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## The pieces of autograd

::: cards grid2
### [a] Graph recording
Ops on tensors with requires_grad=True attach a grad_fn (e.g. MulBackward0) linked to their inputs.

### [b] backward()
Starts from a scalar, walks grad_fn nodes in reverse and accumulates into leaf .grad fields.

### [c] Stopping gradients
torch.no_grad() / inference_mode() for evaluation; detach() for a graph-free view; requires_grad_(False) to freeze.

### [e] Custom Functions
Subclass torch.autograd.Function with forward/backward and ctx.save_for_backward; check with gradcheck.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Reading the recorded graph

For <code>y = (torch.tanh(x) * 2).sum()</code>, following <code>y.grad_fn.next_functions</code> prints (notebook 02):

<div class="visual"><pre style="margin:0;font:14px/1.6 'JetBrains Mono',monospace">SumBackward0&#10;  MulBackward0&#10;    TanhBackward0&#10;      AccumulateGrad      ← writes into x.grad</pre></div>

::: deep Memory: what is saved
TanhBackward saves tanh(x) (its output) because d tanh = 1 − tanh²; MulBackward saves the other operand. These saved activations are what makes training memory-hungry and what activation checkpointing recomputes (Distributed deck 08).
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why define-by-run works

::: cards grid2
### [a] Graphs follow the code
The graph is rebuilt every forward pass, so Python control flow just works.

### [e] Accumulation is a feature
Adding into .grad enables micro-batching and shared weights (tied embeddings).

### [b] Precise control
Freezing and detaching make LoRA, distillation targets and EMA models easy.

### [c] Compilable
torch.compile captures the same graph ahead of time for speed (deck 07).
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "backward() replaces the gradient."
> It adds to .grad; you must zero it between optimizer steps.
:::

::: reveal myth
? "no_grad() freezes parameters."
> It only stops recording inside the block; freezing is requires_grad_(False) on the parameters.
:::

::: reveal myth
? "detach() copies the tensor."
> It returns a view sharing the same storage, without graph history.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Which call frees the graph after use by default?
- [ ] loss.item()
- [x] loss.backward()
- [ ] optimizer.step()
- [ ] model.eval()
> <b>loss.backward()</b> (unless retain_graph=True).
:::

::: reveal
? How do you emulate a batch of 64 with micro-batches of 16?
> Call backward on each of 4 micro-batch losses divided by 4, without zeroing between them, then step once.
:::

::: reveal
? What must a custom autograd Function provide?
> A forward that computes the output (saving tensors with ctx.save_for_backward) and a backward returning the gradient for each input.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Autograd records a grad_fn graph during the forward pass; backward() walks it in reverse and adds into .grad, so zero gradients each step and divide by k when accumulating.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>When a tensor requires gradients, every operation on it records a backward node, so the forward pass builds a graph that mirrors your Python code. Calling backward on the loss walks that graph in reverse and adds each parameter's gradient into its dot-grad field. Because gradients add, training loops zero them every step, and gradient accumulation divides each micro-batch loss by the number of micro-batches to reproduce a larger batch exactly. No-grad blocks stop recording, detach removes a tensor from the graph, freezing turns off requires-grad, and custom Functions define their own backward.</p></div>
    <div class="recap"><div><span><b>Problem:</b> gradients from arbitrary Python code.</span></div><div><span><b>Core idea:</b> record grad_fn graph; backward adds into .grad.</span></div><div><span><b>Practice:</b> zero_grad, ÷k accumulation, no_grad, detach, freeze.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/02_autograd.ipynb" target="_blank" rel="noopener">02 · Autograd: graphs, custom functions and accumulation</a> <span style="color:var(--faint)">· 30 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/02_autograd.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../03-nn-module/index.html">03 · nn.Module and a transformer block →</a> · Previous: <a href="../01-tensors/index.html">← 01</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
