---
title: Eigenvalues, SVD and Low Rank
body:
  data-deck: Eigenvalues, SVD and low rank
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
  - 'W :: m × n :: f'
  - 'Vᵀ :: rotate input :: c'
  - 'Σ :: stretch by σ₁ ≥ σ₂ ≥ … :: a'
  - 'U :: rotate output :: b'
  - 'keep top r :: best rank-r approximation :: e'
  caption: 'Eigenvectors are the special case for square symmetric matrices: W v = λ v.'
example:
  title: 'Worked example: LoRA''s parameter savings'
  setup: Adapt one 4,096 × 4,096 projection with a rank-8 LoRA update ΔW = BA, B being 4,096 × 8 and A 8 × 4,096.
  steps:
  - 'Full update: 4,096 × 4,096 = <b>16,777,216</b> parameters.'
  - 'LoRA: 8 × (4,096 + 4,096) = <b>65,536</b> parameters, 0.39% of the full update.'
  - B starts at zero, so at step 0 the model is exactly the pretrained one; after training BA can be merged into W at no inference cost.
  - 'Notebook 02: a 256 × 256 matrix of true rank 16 plus noise is reconstructed to about 1% error at r = 16 using 12.5% of the storage.'
  result: If the important change is low rank, a few thousand times fewer trainable parameters suffice; the LoRA paper reports 10,000× fewer on GPT-3 175B.
traps:
  tricks:
  - 'Rank-r storage = r(m + n). :: Instead of m·n.'
  - 'Error² = sum of the discarded σᵢ². :: Eckart–Young.'
  - 'Energy plot. :: Cumulative σ² shows how many directions matter.'
  traps:
  - 'Confusing eigenvalues with singular values. :: They coincide only for symmetric positive semi-definite matrices.'
  - 'Assuming every matrix is low rank. :: Random matrices spread energy over all directions; pretrained updates are the ones that compress.'
  - 'Merging LoRA before you are done. :: Merge for deployment; keep separate to swap adapters.'
papers:
- lora
- aghajanyan
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Math for LLMs · 03</div>
    <h1>Eigenvalues, SVD and low rank</h1>
    <p class="sub">How any matrix splits into a few important directions, why big weight matrices and their updates are often nearly low rank, and how LoRA exploits it.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>A 4,096 × 4,096 weight matrix has 16.8 million numbers. Fine-tuning all of them for every task is expensive, yet much of a matrix's action is often carried by a few directions.</div>
      <div class="c"><b>Core idea</b>The <b>singular value decomposition</b> (SVD) writes any matrix as W = UΣVᵀ, a sum of rank-1 pieces σᵢuᵢvᵢᵀ ordered by size. Keeping the top r gives the <b>best rank-r approximation</b>. <b>LoRA</b> learns a fine-tuning update directly in that low-rank form, BA.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## How many directions does a matrix really use?

Singular values of a synthetic 64 × 64 matrix with a chosen "true" rank plus noise. Drag r to keep only the top r components and see how much of the matrix (its energy, Σσ²) survives.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">true rank <input type="range" id="sK" min="1" max="32" step="1" value="6"> <output id="sKo"></output></label>
    <label class="ctl">keep r <input type="range" id="sR" min="1" max="64" step="1" value="6"> <output id="sRo"></output></label>
  </div>
  <svg id="sSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Singular value spectrum"></svg>
  <p class="readout" id="sOut"></p>
</div>
<p class="caption">Illustrative spectrum: true components decay slowly, noise adds a small flat floor.</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why not just store or train the full matrix?

::: cards grid3
### [d] Memory
Full fine-tuning stores gradients and Adam state for every weight: 16 bytes per parameter.

### [b] Many tasks, many copies
Each fine-tuned variant of a 7B model is another 14 GB of weights.

### [c] Most of it is redundant
Aghajanyan et al. found fine-tuning works in a tiny subspace: 200 parameters reached 90% of full fine-tuning on one task.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## How big is a rank-r factorisation?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Storing an m × n matrix as a rank-r product (m × r)(r × n) takes how many numbers?
- [ ] m · n
- [ ] r
- [x] r · (m + n)
- [ ] m · n · r
> <b>C.</b> m·r + r·n. For m = n = 4,096 and r = 8, that is 65,536 instead of 16.8M.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## SVD: rotate, stretch, rotate

::: cards grid3
### [c] Vᵀ
An orthonormal change of basis on the input: finds the input directions the matrix cares about.

### [a] Σ
Stretches each direction by a singular value σᵢ ≥ 0, sorted largest first.

### [b] U
Rotates the result into output directions.
:::

<div class="eq">W = U Σ Vᵀ = Σᵢ σᵢ uᵢ vᵢᵀ   ·   best rank r: keep i ≤ r</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## LoRA: learn the update in low-rank form

::: cards grid4
### [f] 1 · freeze W
The pretrained weight stays fixed: no gradients or optimizer state for it.

### [a] 2 · add BA
y = xW + x·(BA)·(α/r), with B (d × r) zero-initialised and A (r × k) random.

### [b] 3 · train B, A
Only r(d + k) parameters get gradients and Adam state.

### [e] 4 · merge or swap
W' = W + BA for deployment, or keep many small adapters for one base model.
:::

::: deep Eigenvalues in one line
For a square matrix, an eigenvector keeps its direction: Wv = λv. For symmetric matrices the eigenvectors are orthogonal and the SVD and eigendecomposition coincide (up to signs). Eigenvalues of the loss Hessian set optimization speed (Optimization basics deck).
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why low rank works so often

::: cards grid2
### [a] Optimal truncation
Eckart–Young: no rank-r matrix is closer to W than the truncated SVD.

### [e] Updates are structured
Task adaptation changes a few directions of a pretrained model's features; LoRA matched full fine-tuning quality with tiny ranks.

### [b] Smaller is cheaper
Fewer trainable parameters means less optimizer memory and tiny checkpoints.

### [c] Same tool, many uses
Compression, PCA (principal component analysis), conditioning analysis and low-rank KV projections all use the SVD.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Low rank means the matrix has few non-zero entries."
> Rank counts independent directions; a low-rank matrix can be completely dense.
:::

::: reveal myth
? "LoRA approximates the pretrained weights."
> It leaves W untouched and constrains only the update ΔW to be low rank.
:::

::: reveal myth
? "Singular values are the same as eigenvalues."
> Singular values are always ≥ 0 and exist for any shape; eigenvalues need a square matrix and can be negative or complex.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Singular values 5, 3, 1, 1. Fraction of energy in the best rank-2 approximation?
- [ ] 8/10
- [x] 34/36
- [ ] 25/36
- [ ] 1/2
> (25 + 9) / (25 + 9 + 1 + 1) = <b>34/36</b> ≈ 94%.
:::

::: reveal
? Why is B initialised to zero in LoRA?
> So BA = 0 at the start and fine-tuning begins exactly at the pretrained model.
:::

::: reveal
? What is the error of the best rank-r approximation in Frobenius norm?
> The square root of the sum of the squared discarded singular values, √(Σᵢ>ᵣ σᵢ²).
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">The SVD splits any matrix into ranked directions; keeping the top r is the best low-rank approximation, and LoRA trains updates in that form for a tiny fraction of the parameters.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Any matrix can be written as a rotation, a stretch along sorted directions, and another rotation: the singular value decomposition. Its pieces are rank-one matrices weighted by singular values, and keeping the largest r gives the closest possible rank-r matrix, with squared error equal to the discarded singular values squared. Storing it costs r times m plus n numbers instead of m times n. LoRA uses this for fine-tuning: it freezes the pretrained weight and learns a low-rank update BA, with B starting at zero, cutting trainable parameters by orders of magnitude.</p></div>
    <div class="recap"><div><span><b>Problem:</b> full matrices and updates are huge.</span></div><div><span><b>Core idea:</b> W = UΣVᵀ; top-r truncation is optimal.</span></div><div><span><b>Use:</b> LoRA: ΔW = BA with r(d + k) parameters.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/math/02_svd_low_rank.ipynb" target="_blank" rel="noopener">02 · SVD and low-rank approximation</a> <span style="color:var(--faint)">· 30 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/math/02_svd_low_rank.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../04-derivatives-chain-rule/index.html">04 · Derivatives and the chain rule →</a> · Previous: <a href="../02-matrices-linear-layers/index.html">← 02</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
