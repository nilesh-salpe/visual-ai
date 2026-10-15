---
title: Tensors, Strides and Views
body:
  data-deck: Tensors, strides and views
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
  - 'storage :: flat memory :: f'
  - 'shape + strides :: how to index it :: a'
  - 'view / transpose / expand :: new metadata, same memory :: c'
  - 'contiguous() / reshape :: copy only when needed :: b'
  caption: element [i, j] lives at offset + i·stride[0] + j·stride[1]
example:
  title: 'Worked example: splitting attention heads'
  setup: Activations x of shape (B, T, C) = (2, 5, 12), split into H = 3 heads of D = 4. Notebook 01 runs every line.
  steps:
  - 'Contiguous strides for (2, 5, 12) are (60, 12, 1): one step in the last dimension moves 1 element, one token moves 12.'
  - <code>x.view(2, 5, 3, 4)</code> is free (strides (60, 12, 4, 1)); <code>.transpose(1, 2)</code> gives shape (2, 3, 5, 4) with strides (60, 4, 12, 1), still free
    but now non-contiguous.
  - 'Merging back with <code>.view(2, 5, 12)</code> on the transposed tensor fails: "view size is not compatible with input tensor''s size and stride". <code>.transpose(1,
    2).contiguous().view(…)</code> or <code>.reshape(…)</code> copies once and works.'
  - '<code>expand</code> gives stride 0 along broadcast dimensions: a (4,) bias expanded to (3, 4) has strides (0, 1) and uses no extra memory.'
  result: Shape changes are metadata until a non-contiguous layout forces a copy; know which operations copy.
traps:
  tricks:
  - 'stride[i] = product of later dims. :: For contiguous tensors.'
  - 'Broadcasting aligns from the right. :: Size-1 or missing dims stretch.'
  - 'einsum names the math. :: "bhid,bhjd->bhij" is QKᵀ per head.'
  traps:
  - 'view after transpose. :: Fails; use reshape or contiguous().'
  - 'Editing a view edits the original. :: Views share storage (notebook 01 shows x[0,0] change).'
  - 'Silent broadcasting bugs. :: (B, 1) + (B,) gives (B, B), not (B,).'
papers:
- pytorch
- pt_tensor_views
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">PyTorch for LLMs · 01</div>
    <h1>Tensors, strides and views</h1>
    <p class="sub">What a PyTorch tensor really is (storage, shape, strides, dtype, device), why reshaping attention heads is free, when it is not, and broadcasting and einsum for attention math.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>LLM code constantly reshapes activations: splitting heads, transposing for attention, broadcasting masks. Done wrong it silently copies gigabytes, or fails with "view size is not compatible".</div>
      <div class="c"><b>Core idea</b>A tensor is a <b>view</b> onto flat <b>storage</b> described by <b>shape</b> and <b>strides</b> (elements to skip per dimension). <code>view</code>, <code>transpose</code>, slicing and <code>expand</code> only change that metadata. After a transpose the tensor is <b>non-contiguous</b>, so <code>view</code> fails and you need <code>reshape</code> or <code>.contiguous()</code>.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Same memory, different views

A 3 × 4 tensor stored as 12 numbers. Pick an operation: the grid shows which storage index each element reads, and the readout gives shape, strides and contiguity. Checked against PyTorch 2.14.1.
{: .lede}

<div class="visual">
  <div class="seg" id="tSeg" style="display:flex;flex-wrap:wrap"><button data-v="base" class="on">x (3×4)</button><button data-v="t">x.t()</button><button data-v="slice">x[:, 1:3]</button><button data-v="expand">bias.expand(3, 4)</button><button data-v="cont">x.t().contiguous()</button></div>
  <svg id="tSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Tensor view and storage"></svg>
  <p class="readout" id="tOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why this matters for LLM code

::: cards grid3
### [d] Hidden copies
A stray .contiguous() on a (B, H, T, T) tensor copies gigabytes.

### [b] Confusing errors
"view size is not compatible" appears exactly where heads are merged after a transpose.

### [c] Aliasing
Modifying a view in place modifies the original tensor, including weights.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Does this copy?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? x has shape (B, T, C) and is contiguous. Which operation copies data?
- [ ] x.view(B, T, H, C // H)
- [ ] x.transpose(1, 2)
- [x] x.transpose(1, 2).contiguous()
- [ ] x[:, -1]
> <b>C.</b> view, transpose and slicing only change metadata. contiguous() on a non-contiguous tensor allocates new memory in row-major order.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Storage, shape and strides

::: cards grid3
### [f] Storage
A flat 1-D buffer on a device (CPU, CUDA) with one dtype.

### [a] Shape + strides
Element [i₀, i₁, …] is at offset + Σ iₖ·stride[k]. Contiguous: strides decrease right to left.

### [c] Views
view, transpose/permute, slicing, expand, unsqueeze: new metadata over the same storage.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## The shapes of attention

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Step</th><th>Code</th><th>Shape</th><th>Copies?</th></tr>
  <tr><td>project</td><td><code>q, k, v = qkv(x).split(C, 2)</code></td><td>(B, T, C) each</td><td>no (split = views)</td></tr>
  <tr><td>split heads</td><td><code>q.view(B, T, H, D).transpose(1, 2)</code></td><td>(B, H, T, D)</td><td>no</td></tr>
  <tr><td>scores</td><td><code>q @ k.transpose(-2, -1) / D**0.5</code></td><td>(B, H, T, T)</td><td>new tensor (compute)</td></tr>
  <tr><td>mix values</td><td><code>att @ v</code></td><td>(B, H, T, D)</td><td>new tensor</td></tr>
  <tr><td>merge heads</td><td><code>y.transpose(1, 2).reshape(B, T, C)</code></td><td>(B, T, C)</td><td>yes, one copy</td></tr>
</table></div>
<p class="caption">einsum form of the scores: <code>torch.einsum("bhid,bhjd->bhij", q, k)</code>.</p>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why strided tensors are a good design

::: cards grid2
### [a] Free reshapes
Most layout changes cost nothing, so code can be written in the most readable shape.

### [e] Broadcasting without memory
Stride-0 dimensions let a bias or mask act on a whole batch.

### [b] Kernels choose layouts
Fused kernels accept strided inputs; copies happen only where a kernel needs contiguity.

### [c] Same API on every device
The metadata model is identical on CPU and GPU.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "reshape and view are the same."
> view never copies and fails if strides do not allow it; reshape returns a view when possible and copies otherwise.
:::

::: reveal myth
? "Transpose moves data."
> It swaps two strides; the data moves only if you later call contiguous() or an op that needs contiguity.
:::

::: reveal myth
? "Broadcasting allocates the expanded tensor."
> Expanded dimensions have stride 0; memory is only used when a result is computed.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Strides of a contiguous tensor with shape (2, 3, 4)?
- [ ] (1, 2, 3)
- [x] (12, 4, 1)
- [ ] (4, 3, 2)
- [ ] (24, 12, 4)
> <b>(12, 4, 1)</b>.
:::

::: reveal
? Why does view fail after transpose?
> The transposed strides cannot express the requested shape over the same memory without reordering; reshape or contiguous() is needed.
:::

::: reveal
? Write the attention score computation with einsum.
> torch.einsum("bhid,bhjd->bhij", q, k) / D ** 0.5.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">A tensor is storage plus shape and strides: view, transpose, slicing and expand are free metadata changes, and a copy happens only when a non-contiguous layout must become contiguous.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>A PyTorch tensor is a view onto a flat block of memory, described by its shape and strides, the number of elements to skip per dimension. Operations like view, transpose, slicing and expand only create new metadata over the same storage, which is why splitting attention heads costs nothing. A transpose leaves the tensor non-contiguous, so view can no longer merge dimensions; reshape or contiguous makes one copy. Broadcasting uses stride zero so a bias or mask applies to a whole batch without extra memory, and einsum writes attention math directly.</p></div>
    <div class="recap"><div><span><b>Problem:</b> reshaping without hidden copies or errors.</span></div><div><span><b>Core idea:</b> storage + shape + strides; views share memory.</span></div><div><span><b>Rule:</b> transpose → non-contiguous → reshape/contiguous to merge.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/01_tensors_views.ipynb" target="_blank" rel="noopener">01 · Tensors: shapes, strides, views and einsum</a> <span style="color:var(--faint)">· 30 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/01_tensors_views.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../02-autograd/index.html">02 · Autograd →</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
