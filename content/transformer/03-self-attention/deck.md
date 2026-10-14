---
title: Self-Attention
body:
  data-deck: Self-attention
  data-home: ../index.html
  data-home-label: Transformer
styles:
- ../../shared/deck.css
- ../../shared/learn.css
- ../tx.css
scripts:
- ../../shared/deck.js
- ../tx.js
glance:
  steps:
  - 'token vectors :: one per word :: f'
  - 'compare :: score every pair :: c'
  - 'softmax :: weights per row sum to 1 :: a'
  - 'weighted mix :: context-aware vector :: e'
  caption: Each output is a weighted average of all the inputs, with weights computed from the data.
example:
  title: 'Worked example: one row of attention'
  setup: Three tokens; the query token scores the three keys as [2, 1, 0]. Values are v₁ = [1, 0], v₂ = [0, 1], v₃ = [1, 1].
  steps:
  - softmax([2, 1, 0]) = <b>[0.665, 0.245, 0.090]</b>.
  - Output = 0.665·[1,0] + 0.245·[0,1] + 0.090·[1,1] = <b>[0.755, 0.335]</b>.
  - 'Every token does this at once: a 3 × 3 weight matrix times the value matrix.'
  - 'The weights change with every sentence: same word, different context, different output.'
  result: 'Self-attention is a data-dependent weighted average: the weights are the "who to look at", the values are the "what to take".'
traps:
  tricks:
  - 'Rows sum to 1. :: Each output is a convex combination of values.'
  - 'n × n matrix. :: One row per query, one column per key.'
  - 'Permutation-equivariant. :: Shuffle inputs and outputs shuffle the same way; order needs positional encoding.'
  traps:
  - 'Attention weights as explanations. :: They show mixing, not necessarily causal importance.'
  - 'Forgetting values. :: Weights come from Q·K; content comes from V.'
  - 'Assuming symmetric attention. :: Token i attending to j says nothing about j attending to i.'
papers:
- vaswani
- bahdanau
- luong
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Attention Is All You Need · 03</div>
    <h1>Self-attention</h1>
    <p class="sub">How each token builds a context-aware representation by drawing on every other token in the same sequence.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>A word's embedding is the same whatever sentence it's in, but its meaning depends on context. "It" refers to different things in different sentences.</div>
      <div class="c"><b>Core idea</b>Each token computes a weighted average over all tokens in the sequence. The weights express relevance, so the output for "it" draws mostly on the word it refers to.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-prob" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Same word, same vector, different meaning

An embedding table gives "<b>it</b>" one fixed vector. In the first sentence "it" means the <span class="em-a">animal</span>; in the second it means the <span class="em-b">street</span>. Something has to mix in context.
{: .lede}

<div class="visual"><svg id="probSvg" viewBox="0 0 660 260" role="img" aria-label="Same embedding for it in two sentences"></svg></div>

<p class="caption">Example sentences are illustrative and do not come from the paper. Vector values are toy numbers.</p>

<div class="takeaway">For the model to resolve "it", the representation of "it" has to depend on the other words in the sentence.</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Existing ways of adding context are slow, local, or absent

::: cards grid3
### [d] Embedding lookup
No context at all: "it" gets the same vector in every sentence.

### [b] Recurrence
Context arrives through a chain of hidden states: n sequential steps, and O(n) hops between distant words (<a href="../01-sequential-bottleneck/index.html">deck 01</a>).

### [c] Convolution
Sees a fixed window of k tokens. Linking distant words needs a stack of O(n/k) layers, or O(log<sub>k</sub> n) with dilated convolutions (§4).
:::

<div class="takeaway">What's missing: a way for each word to draw on <b>any</b> other word in the sentence directly, chosen by relevance rather than by distance.</div>

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## How should "it" build a context-aware vector?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Given vectors for every word in the sentence, how should "it" build its new, context-aware vector?
- [ ] Average all words equally
- [ ] Copy the previous word's vector
- [x] Take a weighted average, with weights reflecting how relevant each word is to "it"
- [ ] Concatenate all the word vectors
> <b>C is self-attention.</b> An equal average (A) loses which word matters. Copying a neighbour (B) only sees local context. Concatenation (D) makes the vector size depend on sentence length. Relevance weights that sum to 1 give a fixed-size, context-specific mix.
:::

<!-- slide id="s-arcs" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Each token takes a weighted mix of every token in the sentence <span class="ill">illustrative weights</span>

Self-attention relates different positions of a <b>single sequence</b> to compute a new representation of it. Click a token to see where it attends. Arc thickness is the attention weight, and the weights for each token add up to 1.
{: .lede}

<div class="visual">
  <div class="seg" id="vSeg"><button data-v="tired" class="on">…because it was too tired</button><button data-v="wide">…because it was too wide</button></div>
  <svg id="arcSvg" viewBox="0 0 660 230" style="margin-top:8px" role="img" aria-label="Attention arcs"></svg>
  <h3 style="margin-top:6px" id="mixTitle"></h3>
  <div id="mixBars"></div>
</div>

<div class="takeaway">The output for "it" is mostly built from "animal" (or "street"), so the same input word ends up with different, context-aware representations.</div>

{{glance}}

<!-- slide id="s-matrix" chapter="How" tag="5 · How it works" tagclass="b5" -->
## All tokens do this at once: an n × n attention matrix <span class="ill">illustrative weights</span>

Row <i>i</i> is token <i>i</i>'s attention distribution over every token. All rows are computed in parallel with a few matrix multiplications, and nothing waits on a previous step. Hover a row.
{: .lede}

<div class="grid2" style="grid-template-columns:1.3fr 1fr;align-items:center">
  <div class="visual" style="margin-top:0"><svg id="matSvg" viewBox="0 0 470 470" role="img" aria-label="Attention matrix"></svg></div>
  <div><div class="infobox" id="matInfo" style="margin-top:0">Hover a row of the matrix.</div>
    <div class="paper"><b>Each row sums to 1</b> because it comes from a softmax. Deck 05 shows how the weights are computed: softmax(QKᵀ/√d<sub>k</sub>).</div></div>
</div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide raw -->
<section class="slide" id="s-paper" data-chapter="How">
  <div class="inner">
    <span class="qtag b5">5 · How it works</span> <span class="ill" style="color:var(--c);border-color:var(--c)">from the paper · §2, §3.2, §3.2.3</span>
    <h2>The definitions</h2>
    <hr>
    <div class="paper"><b>Self-attention (§2):</b> "sometimes called intra-attention, is an attention mechanism relating different positions of a single sequence in order to compute a representation of the sequence."</div>
    <div class="paper"><b>Attention function (§3.2):</b> maps a query and a set of key-value pairs to an output. The output is a weighted sum of the values, where each weight comes from a compatibility function of the query with the matching key.</div>
    <div class="paper"><b>In the encoder (§3.2.3):</b> all of the keys, values and queries come from the output of the previous encoder layer, so each position can attend to all positions in the previous layer.</div>
    <div class="cite">Next: deck 04 shows where queries, keys and values come from.</div>
  </div>
</section>

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works

::: cards grid2
### [a] Context-dependent by construction
The weights are computed from the actual sentence, so the same word gets different outputs in different contexts ("it" → animal vs street).

### [e] One hop to anything
Every token reaches every other token in a single step, so distance doesn't weaken the connection (path length O(1)).

### [b] All positions in parallel
The whole n × n weight matrix comes out of matrix products, with no step-by-step dependency.

### [c] Learned, not hand-designed
What to attend to is learned from data. The trained model's heads end up tracking real linguistic structure, as the next slide shows.
:::

<!-- slide id="s-real" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## What the trained model actually learned (paper, Figures 3–4)

The paper shows encoder self-attention from <b>layer 5 of 6</b> on real sentences. Some heads link a verb to the words it governs far away; others resolve what a pronoun refers to.
{: .lede}

<div class="visual">
  <div class="seg" id="figSeg"><button data-v="f4" class="on">Fig. 4: "its" (anaphora)</button><button data-v="f3">Fig. 3: "making … more difficult"</button></div>
  <svg id="realSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Attention visualization from the paper"></svg>
  <p class="caption" id="realCap"></p>
</div>

<div class="cite">Schematic redraw of the paper's Figures 3 and 4 (appendix, Attention Visualizations). It shows only the strongest connections described in the captions; exact weights are not reproduced.</div>

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Attention weights show which words are important in the sentence."
> They are <b>per-query mixing weights</b> in one head of one layer: how much a given token takes from each other token. Different heads and layers attend differently (Figure 5). They are not a global importance score.
:::

::: reveal myth
? "Self-attention compares the raw word embeddings directly."
> It compares learned <b>query and key projections</b> of the embeddings and mixes learned <b>value</b> projections (<a href="../04-queries-keys-values/index.html">deck 04</a>).
:::

::: reveal myth
? "A token cannot attend to itself."
> It can and usually does: the diagonal of the attention matrix is typically non-zero. The token's own value is part of its mix.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? In encoder self-attention, where do the queries, keys and values come from?
- [ ] Q from the decoder, K and V from the encoder
- [x] All three from the output of the previous encoder layer
- [ ] Q from the embeddings, K and V from positional encodings
- [ ] They are fixed, not learned
> <b>All three from the previous encoder layer</b> (§3.2.3), so each position can attend to all positions of that layer.
:::

::: quiz
? What does each row of the attention matrix sum to?
- [ ] 0
- [x] 1
- [ ] n
- [ ] d<sub>model</sub>
> <b>1</b>, because each row comes from a softmax: it is one token's distribution over all tokens.
:::

<div class="quiz ">
  <p class="qq">"it" has the same embedding in the "tired" and "wide" sentences. How can self-attention give it different outputs?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">The weights depend on the <b>other tokens in the sentence</b>: "tired" vs "wide" changes how well "animal" and "street" match "it", so the weighted mix and the output change.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Each token's new representation is a relevance-weighted average of all tokens in the same sequence, so context changes what a word means.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Self-attention lets every position look at every other position of the same sequence. For each token it computes weights over all tokens, summing to 1, and outputs the weighted sum of their value vectors, so "it" can draw mostly from "animal". All positions are computed in parallel with matrix products, and any two tokens are one hop apart.</p></div>

<div class="recap">
  <div><span><b>Problem:</b> a fixed embedding can't express that a word's meaning depends on context ("it" → animal or street).</span></div>
  <div><span><b>Core idea:</b> each token's output is a relevance-weighted mix of all tokens in the same sequence, computed for all positions in parallel.</span></div>
</div>

<p class="start-hint">Next: <a href="../04-queries-keys-values/index.html">04 · Queries, keys and values →</a> · Previous: <a href="../02-transformer-architecture/index.html">← 02</a> · <a href="../index.html">All concepts</a></p>

<!-- slide id="s-papers" from="papers" -->
