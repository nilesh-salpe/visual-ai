---
title: Embeddings
body:
  data-deck: Embeddings
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
  - 'token id :: integer in 0 … V−1 :: f'
  - 'lookup E[id] :: = one-hot × E :: a'
  - 'd-dim vector :: dense, learned :: c'
  - 'network :: attention, MLPs :: b'
  - 'output :: logits = h · Eᵀ (often tied) :: e'
  caption: The same idea embeds positions, images patches, users or products.
example:
  title: 'Worked example: GPT-2 small''s embedding table'
  setup: GPT-2 has a vocabulary of 50,257 tokens; the small model uses d = 768.
  steps:
  - 'Table size: 50,257 × 768 = <b>38.6M</b> parameters, about a third of the 124M-parameter small model.'
  - A one-hot input would be a 50,257-dimensional vector with a single 1; multiplying it by E selects one row, so frameworks just index.
  - 'Gradient: only the rows of tokens present in the batch receive gradient (sparse update).'
  - 'GPT-2 ties the output layer to the same matrix: logits = h · Eᵀ, saving another 38.6M parameters.'
  result: Embeddings are a big, sparse-updated lookup table whose geometry is learned from context.
traps:
  tricks:
  - 'Lookup = one-hot × E. :: Same math, no multiply.'
  - 'Tied embeddings. :: Reuse E for the output projection.'
  - 'Cosine similarity for neighbours. :: Lengths vary with frequency.'
  traps:
  - 'Treating token IDs as numbers. :: Feeding the integer itself implies a meaningless order.'
  - 'Rare tokens. :: Few updates, so their vectors stay close to initialisation.'
  - 'Over-reading analogies. :: king − man + woman ≈ queen is a tendency, not a law.'
papers:
- bengio03
- word2vec
- word2vec_neg
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Neural Networks · 09</div>
    <h1>Embeddings</h1>
    <p class="sub">How discrete tokens become vectors a network can compute with: a learned lookup table, why it beats one-hot vectors, and what geometry the vectors acquire.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Text arrives as integer token IDs. Integers have no useful arithmetic (token 500 is not "close to" 501), and one-hot vectors are huge and say every pair of words is equally different.</div>
      <div class="c"><b>Core idea</b>An <b>embedding table</b> E (V × d) maps token i to row Eᵢ. That is exactly one-hot(i) × E, done as a lookup. The rows are <b>learned</b> by backpropagation, so tokens used in similar contexts end up with similar vectors.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Words as points in space

A toy 2-D embedding learned so that words in similar contexts are close. Click any two words to see their cosine similarity; the arrow shows king − man + woman.
{: .lede}

<div class="visual">
  <svg id="eSvg" viewBox="0 0 660 270" role="img" aria-label="2-D word embeddings"></svg>
  <p class="readout" id="eOut">Click a word, then another.</p>
</div>
<p class="caption">Illustrative coordinates. Real embeddings have hundreds to thousands of dimensions.</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why not integers or one-hot vectors?

::: cards grid3
### [d] Integers
Token IDs have an arbitrary order; arithmetic on them is meaningless.

### [b] One-hot
A V-dimensional vector per token (V ≈ 50K–250K): huge and every pair is equally far apart.

### [c] Hand-made features
Nobody can write down useful features for every token in 100 languages.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What does an embedding lookup equal?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? For token i with one-hot vector eᵢ, what is E[i] (row i of the table)?
- [ ] eᵢ + E
- [x] eᵢ × E (one-hot times the matrix)
- [ ] E × E
- [ ] the integer i
> <b>B.</b> Multiplying a one-hot row vector by E picks out row i. Frameworks implement it as indexing because it is far cheaper.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## A learned lookup table

::: cards grid3
### [a] Table
E has one row of d numbers per token: V × d parameters.

### [c] Lookup
Input token i → E[i]. Equivalent to one-hot × E, the first linear layer of the model.

### [e] Learned geometry
Backprop moves rows so tokens that predict similar contexts get similar vectors (Bengio et al., 2003; word2vec).
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Embedding sizes in practice

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Model</th><th>Vocabulary</th><th>d</th><th>Embedding parameters</th></tr>
  <tr><td>GPT-2 small</td><td>50,257</td><td>768</td><td>38.6M</td></tr>
  <tr><td>GPT-2 XL</td><td>50,257</td><td>1,600</td><td>80.4M</td></tr>
  <tr><td>Llama 2 7B</td><td>32,000</td><td>4,096</td><td>131M (input) + 131M (output)</td></tr>
  <tr><td>Llama 3 8B</td><td>128,256</td><td>4,096</td><td>525M (input) + 525M (output)</td></tr>
</table></div>
<p class="caption">Computed as vocabulary × d. See the <a href="../../tokenization/07-vocabulary-size/index.html">Tokenization deck on vocabulary size</a> for the trade-off.</p>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why learned embeddings work

::: cards grid2
### [a] Distributional signal
Words that appear in similar contexts receive similar gradients, so their vectors converge.

### [e] Generalisation
A model that learned about "cat" transfers some of it to "kitten" because their vectors are close.

### [b] Directions carry meaning
word2vec found offsets like man → woman are roughly consistent across pairs.

### [c] Reusable
Contextual embeddings from the middle of an LLM power retrieval and classification.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Each embedding dimension means something specific."
> Meaning is spread across directions; individual coordinates are rarely interpretable.
:::

::: reveal myth
? "Embeddings are fixed after pretraining."
> They keep updating in fine-tuning, and contextual representations change every layer.
:::

::: reveal myth
? "The embedding layer is a small part of the model."
> For small models with big vocabularies it can be a third or more of the parameters.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Parameters in a 32,000 × 4,096 embedding table?
- [x] 131M
- [ ] 13M
- [ ] 1.3B
- [ ] 32K
> 32,000 × 4,096 ≈ <b>131M</b>.
:::

::: reveal
? Which rows of E get gradient in a training step?
> Only those of tokens that appear in the batch.
:::

::: reveal
? What does weight tying mean?
> Using the same matrix E for the input lookup and (transposed) for the output logits.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Embeddings are a learned V × d lookup table, equivalent to one-hot × E, whose rows acquire meaningful geometry because similar contexts give similar gradients.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Neural networks need vectors, but text arrives as token IDs. An embedding table has one learned row of d numbers per token, and looking up row i is mathematically the same as multiplying a one-hot vector by the table, just much cheaper. Training moves the rows so that tokens used in similar contexts get similar vectors, which lets knowledge transfer between related words; word2vec famously found consistent directions such as man to woman. Tables are large: GPT-2 small's is 50,257 by 768, about 39 million parameters, and many models tie it to the output layer.</p></div>
    <div class="recap"><div><span><b>Problem:</b> token IDs have no geometry.</span></div><div><span><b>Core idea:</b> learned table E; lookup = one-hot × E.</span></div><div><span><b>Facts:</b> V × d parameters; sparse gradients; weight tying.</span></div></div>
    <p class="start-hint">Next: <a href="../10-mlp-to-language-model/index.html">10 · From MLP to language model →</a> · Previous: <a href="../08-regularization/index.html">← 08</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
