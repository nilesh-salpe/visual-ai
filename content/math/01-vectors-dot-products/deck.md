---
title: Vectors and Dot Products
body:
  data-deck: Vectors and dot products
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
  - 'token → vector :: embedding lookup :: f'
  - 'compare two vectors :: a · b = Σ aᵢbᵢ :: a'
  - 'normalise :: cos θ = a·b / (|a||b|) :: c'
  - 'use it :: search, attention, logits :: e'
  caption: 'Dot products appear in every layer: q·k for attention, h·eᵢ for the output logits.'
example:
  title: 'Worked example: similarity and the √d scale'
  setup: Two 2-D vectors a = (3, 4) and b = (4, 3); then random 128-dimensional query and key vectors with mean-0, variance-1 entries.
  steps:
  - a · b = 3·4 + 4·3 = <b>24</b>; |a| = |b| = 5.
  - 'cos θ = 24 / 25 = <b>0.96</b>, so θ ≈ 16.3°: nearly the same direction.'
  - 'For random q, k in d = 128: q·k has mean 0 and variance d, so its standard deviation is √128 ≈ <b>11.3</b>.'
  - Dividing by √d brings that back to about 1, so the softmax over scores is neither flat nor one-hot at initialisation.
  result: The dot product mixes direction and length; cosine isolates direction; attention divides by √d to control scale.
traps:
  tricks:
  - 'a·b = |a||b|cos θ. :: Positive = aligned, 0 = orthogonal, negative = opposed.'
  - 'Normalise once, then matmul. :: All cosines at once, as in vector search.'
  - 'Random high-dimensional vectors are nearly orthogonal. :: Cosine spread ≈ 1/√d.'
  traps:
  - 'Comparing raw dot products across vectors of different lengths. :: Long vectors win regardless of direction.'
  - 'Forgetting the √d. :: Unscaled attention scores have spread √d and saturate the softmax.'
  - 'Treating cosine 0 as "opposite". :: 0 means unrelated (orthogonal); −1 is opposite.'
papers:
- word2vec
- vaswani
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Math for LLMs · 01</div>
    <h1>Vectors and dot products</h1>
    <p class="sub">The single operation behind embeddings, similarity search and attention: multiply matching coordinates and add them up.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>A language model represents every token as a list of thousands of numbers. To use them it must constantly answer one question: how related are these two lists?</div>
      <div class="c"><b>Core idea</b>The <b>dot product</b> a·b = Σ aᵢbᵢ = |a||b|cos θ measures alignment scaled by length. <b>Cosine similarity</b> removes the lengths. Attention scores are dot products of queries and keys, divided by √d to keep their spread near 1.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## How related are two vectors?

Drag the angles of two 2-D vectors and change their lengths. The dot product, cosine and projection update live.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">angle of a <input type="range" id="vA" min="0" max="360" step="1" value="40"> <output id="vAo"></output></label>
    <label class="ctl">angle of b <input type="range" id="vB" min="0" max="360" step="1" value="80"> <output id="vBo"></output></label>
    <label class="ctl">length of b <input type="range" id="vL" min="0.2" max="2" step="0.1" value="1"> <output id="vLo"></output></label>
  </div>
  <svg id="vSvg" viewBox="0 0 660 260" style="margin-top:10px" role="img" aria-label="Two vectors and their dot product"></svg>
  <p class="readout" id="vOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why not compare vectors some other way?

::: cards grid3
### [d] Coordinate by coordinate
Checking whether entries match one by one says nothing about overall alignment in thousands of dimensions.

### [b] Euclidean distance
Useful, but for unit vectors |a − b|² = 2 − 2 a·b, so it is the dot product in disguise.

### [c] It must be fast
A model computes billions of comparisons per step; the dot product is one multiply-add per coordinate and maps perfectly onto matrix hardware.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Which pair is most similar?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? By cosine similarity, which pair is most aligned?
- [x] (1, 0) and (100, 1)
- [ ] (1, 1) and (1, −1)
- [ ] (2, 2) and (−1, −1)
- [ ] (0, 1) and (1, 0)
> <b>A.</b> cos ≈ 0.99995: almost the same direction despite very different lengths. B and D are orthogonal (cosine 0); C points in opposite directions (cosine −1).
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Dot product, length and angle

::: cards grid3
### [a] Dot product
a·b = Σ aᵢbᵢ. Large when the vectors point the same way and are long.

### [c] Length (norm)
|a| = √(a·a). Dividing by it gives a unit vector that keeps only direction.

### [e] Cosine similarity
cos θ = a·b / (|a||b|), between −1 and 1. Used for embedding search and retrieval.
:::

<div class="eq">a · b = Σᵢ aᵢ bᵢ = |a| |b| cos θ</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Where dot products appear in an LLM

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Place</th><th>Dot product of</th><th>Meaning</th></tr>
  <tr><td>Attention scores</td><td>query · key, ÷ √d</td><td>how much token i should look at token j</td></tr>
  <tr><td>Attention output</td><td>weights · values</td><td>weighted average of value vectors</td></tr>
  <tr><td>Every linear layer</td><td>input · each weight column</td><td>one output feature per column</td></tr>
  <tr><td>Output logits</td><td>final hidden state · each token embedding</td><td>score for every possible next token</td></tr>
  <tr><td>Retrieval (RAG)</td><td>query embedding · document embeddings</td><td>which documents to fetch</td></tr>
</table></div>

::: deep Analogies in embedding space
word2vec showed that differences between word vectors carry meaning: the vector king − man + woman lands closest to queen. Notebook 01 reproduces this with toy embeddings.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why the dot product is the right tool

::: cards grid2
### [a] It is a projection
a·b/|b| is the length of a's shadow on b: how much of a lies along b's direction.

### [e] It is linear
Dot products compose into matrix multiplications, which GPUs run at hundreds of TFLOP/s (tera floating-point operations per second).

### [b] High dimensions help
Random directions are nearly orthogonal, so thousands of features can share one vector with little interference.

### [c] Scale is controllable
Dividing by √d or normalising vectors keeps magnitudes in a sensible range.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "A dot product of 0 means the vectors are opposite."
> It means orthogonal: neither aligned nor opposed. Opposite vectors have cosine −1.
:::

::: reveal myth
? "Bigger dot product always means more similar."
> Only for vectors of fixed length; otherwise length dominates. Use cosine to compare directions.
:::

::: reveal myth
? "The √d in attention is a learned parameter."
> It is a fixed constant from the variance argument: d independent unit-variance products sum to variance d.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? cos θ for a = (1, 2, 2) and b = (2, 1, −2)?
- [ ] 1
- [x] 0
- [ ] −1
- [ ] 0.5
> 1·2 + 2·1 + 2·(−2) = 0, so <b>0</b>: orthogonal.
:::

::: reveal
? Why does attention divide q·k by √d?
> For unit-variance entries, q·k has variance d. Dividing by √d keeps the scores' spread near 1 so the softmax does not saturate.
:::

::: reveal
? How do you find the 5 nearest embeddings to a query efficiently?
> Normalise all rows once, compute one matrix-vector product for all cosines, take the top 5 (or use an approximate nearest-neighbour index).
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">The dot product Σ aᵢbᵢ = |a||b|cos θ measures alignment; cosine removes length, and attention divides by √d to keep scores well scaled.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Language models represent tokens as long vectors, and the dot product is how they compare them: multiply matching coordinates and add. It equals the two lengths times the cosine of the angle, so it is large when vectors point the same way. Cosine similarity divides out the lengths and is used for embedding search. Attention scores are dot products of queries and keys; because random vectors in d dimensions give dot products with spread √d, scores are divided by √d before the softmax.</p></div>
    <div class="recap"><div><span><b>Problem:</b> compare thousand-dimensional vectors, billions of times.</span></div><div><span><b>Core idea:</b> a·b = |a||b|cos θ; cosine = direction only.</span></div><div><span><b>In LLMs:</b> attention, linear layers, logits, retrieval.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/math/01_vectors_similarity.ipynb" target="_blank" rel="noopener">01 · Vectors, dot products and similarity</a> <span style="color:var(--faint)">· 25 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/math/01_vectors_similarity.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../02-matrices-linear-layers/index.html">02 · Matrices and linear layers →</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
