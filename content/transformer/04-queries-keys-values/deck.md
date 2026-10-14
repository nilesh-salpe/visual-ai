---
title: Queries, Keys and Values
body:
  data-deck: Queries, keys, values
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
  - 'x :: token vector, 512 :: f'
  - 'q = xW_Q :: what I look for :: c'
  - 'k = xW_K :: how I can be found :: b'
  - 'v = xW_V :: what I hand over :: a'
  - 'softmax(qkᵀ/√d_k)·v :: output :: e'
  caption: Three learned projections of the same token give it three separate roles.
example:
  title: 'Worked example: sizes per head (base model)'
  setup: d_model = 512, h = 8 heads, so d_k = d_v = 512 / 8 = 64. A 10-token sentence.
  steps:
  - Per head, W_Q, W_K and W_V are each <b>512 × 64</b>.
  - 'Q, K, V for the sentence: <b>[10, 64]</b> each; scores QKᵀ: <b>[10, 10]</b>.'
  - 'Parameters per head: 3 × 512 × 64 = <b>98,304</b>; across 8 heads plus W_O (512 × 512): <b>1,048,576</b>.'
  - Without separate projections, a token's query and key would be the same vector, forcing symmetric matches.
  result: Separate W_Q and W_K let "what I seek" differ from "what I offer"; W_V decouples matching from content.
traps:
  tricks:
  - 'd_k = d_model / h. :: 64 in the base model.'
  - 'Attention params = 4·d_model². :: Q, K, V and output projections, independent of h.'
  - 'Matrix form. :: softmax(QKᵀ/√d_k)V for all tokens at once.'
  traps:
  - 'Thinking K and V are the same. :: Same input, different learned projections.'
  - 'Using d_model for scaling. :: Divide by √d_k (per-head size), not √d_model.'
  - 'Forgetting W_O. :: Head outputs are concatenated, then projected.'
papers:
- vaswani
- luong
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Attention Is All You Need · 04</div>
    <h1>Queries, keys and values</h1>
    <p class="sub">How query-key compatibility produces attention weights, and how those weights combine value vectors into a context-aware output.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>A token must decide <em>which</em> tokens are relevant and <em>what</em> to take from them. One embedding vector can't serve all three roles well: asking, being matched, and supplying content.</div>
      <div class="c"><b>Core idea</b>Project each token three ways: a query (what I'm looking for), a key (what I can be matched on) and a value (what I contribute). Query·key gives the weights, and the weights combine the values.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-prob" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Searching needs a question, an index and the content itself

Think of a library. You arrive with a <b>question</b>, you compare it with each book's <b>label</b>, and you take <b>content</b> from the books that match. If a token's raw embedding had to be the question, the label and the content all at once, it couldn't specialize for any of those roles.
{: .lede}

<div class="visual"><svg id="libSvg" viewBox="0 0 660 230" role="img" aria-label="Library metaphor for query key value"></svg></div>

<div class="takeaway">"it" should <b>ask</b> for an animate referent, "animal" should be <b>findable</b> as animate, and what "animal" <b>passes on</b> can be different again. These are three different jobs.</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Scoring with the raw embeddings, x<sub>i</sub>·x<sub>j</sub>, doesn't work well

The simplest idea is to score each pair of tokens by the dot product of their embeddings. Below is that score matrix for the toy embeddings used in this deck.
{: .lede}

<div class="grid2" style="align-items:center">
  <div class="visual" style="margin-top:0"><svg id="limSvg" viewBox="0 0 330 270" role="img" aria-label="Raw embedding dot products"></svg></div>
  <div>
    <div class="card d"><h3>Symmetric</h3><p>x<sub>i</sub>·x<sub>j</sub> = x<sub>j</sub>·x<sub>i</sub>. If "it" looks for "animal", "animal" must look for "it" just as strongly.</p></div>
    <div class="card d" style="margin-top:8px"><h3>Each word matches itself best</h3><p>The diagonal dominates: "it" scores 1.02 with itself and only 0.10 with "animal".</p></div>
    <div class="card d" style="margin-top:8px"><h3>One vector, three jobs</h3><p>What a word is matched on and what it passes on are forced to be the same vector.</p></div>
  </div>
</div>

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## How would you separate the roles?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? How can "it" look for animate things without "animal" having to look for pronouns?
- [ ] Keep using x<sub>i</sub>·x<sub>j</sub> but normalize the embeddings
- [x] Use separate learned projections for asking (query) and for being matched (key)
- [ ] Add positional encodings
- [ ] Use a larger embedding size
> <b>B.</b> With q = xW<sup>Q</sup> and k = xW<sup>K</sup>, the score q<sub>i</sub>·k<sub>j</sub> is no longer symmetric, and each projection can specialize. A third projection, v = xW<sup>V</sup>, separates what is passed on from what is matched. Normalizing (A) keeps the symmetry, and (C) and (D) don't separate the roles.
:::

<!-- slide id="s-proj" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Three learned projections of the same token: q = xW<sup>Q</sup>, k = xW<sup>K</sup>, v = xW<sup>V</sup>

Every token's vector x is multiplied by three learned matrices. The toy model below has d<sub>model</sub> = 4 and d<sub>k</sub> = 3; the paper uses 512 and 64. All numbers are computed live. Pick a token.
{: .lede}

<div class="visual">
  <div class="seg" id="tokSeg"><button data-v="0">animal</button><button data-v="1">street</button><button data-v="2" class="on">it</button><button data-v="3">tired</button></div>
  <svg id="projSvg" viewBox="0 0 660 250" style="margin-top:10px" role="img" aria-label="Projection into q k v"></svg>
</div>

<p class="caption">Toy features of x: [animate, place, pronoun, state]. The projection weights are hand-set so the example is readable; in the paper they are learned.</p>

{{glance}}

<!-- slide id="s-match" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Compatibility → weights → weighted sum of values

The query of the selected token is compared with <b>every key</b> by dot product. The scores are scaled by 1/√d<sub>k</sub> and passed through a softmax to give weights that sum to 1. The output is the <b>weighted sum of the values</b>.
{: .lede}

<div class="visual">
  <div class="seg" id="qSeg"><button data-v="0">query: animal</button><button data-v="1">query: street</button><button data-v="2" class="on">query: it</button><button data-v="3">query: tired</button></div>
  <svg id="matchSvg" viewBox="0 0 660 300" style="margin-top:10px" role="img" aria-label="Query key matching"></svg>
</div>

<div class="takeaway">Because q(it) is aligned with k(animal), "it" ends up taking most of its output from v(animal). That is the attention function from §3.2, computed live.</div>

<!-- slide id="s-matrix" chapter="How" tag="5 · How it works" tagclass="b5" -->
## All tokens at once, in matrix form

Stack the token vectors into X (n × d<sub>model</sub>). Then Q = XW<sup>Q</sup>, K = XW<sup>K</sup> and V = XW<sup>V</sup> are three matrix multiplications, and every query is matched against every key in one product, QKᵀ.
{: .lede}

<div class="visual"><svg id="matSvg" viewBox="0 0 660 240" role="img" aria-label="Matrix form of Q K V"></svg></div>

<div class="paper"><b>Shapes in the paper (per head):</b> X: n × 512 · W<sup>Q</sup>, W<sup>K</sup>: 512 × 64 · W<sup>V</sup>: 512 × 64 · Q, K, V: n × 64 · QKᵀ: n × n. Deck 06 shows how 8 such heads run side by side.</div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide raw -->
<section class="slide" id="s-paper" data-chapter="How">
  <div class="inner">
    <span class="qtag b5">5 · How it works</span> <span class="ill" style="color:var(--c);border-color:var(--c)">from the paper · §3.2, §3.2.1</span>
    <h2>The paper's wording</h2>
    <hr>
    <div class="paper"><b>§3.2:</b> "An attention function can be described as mapping a query and a set of key-value pairs to an output, where the query, keys, values, and output are all vectors. The output is computed as a weighted sum of the values, where the weight assigned to each value is computed by a compatibility function of the query with the corresponding key."</div>
    <div class="paper"><b>§3.2.1:</b> the input is queries and keys of dimension d<sub>k</sub> and values of dimension d<sub>v</sub>. In practice the queries are packed into a matrix Q, and the keys and values into matrices K and V.</div>
    <div class="paper"><b>Where Q, K, V come from (§3.2.3):</b> in self-attention, all three come from the same previous layer. In encoder-decoder attention, Q comes from the decoder while K and V come from the encoder output (deck 08).</div>
  </div>
</section>

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why separate Q, K and V work

::: cards grid2
### [c] Asymmetric matching
q<sub>i</sub>·k<sub>j</sub> ≠ q<sub>j</sub>·k<sub>i</sub> in general, so "it → animal" can be strong while "animal → it" is weak.

### [b] Specialized roles
Keys can expose the features worth matching on (animate, place). Queries can ask for exactly those features.

### [a] Content decoupled from matching
Values carry what is passed on, which can differ from what made the match.

### [e] The matching does real work
Table 3 (B): shrinking the key size d<sub>k</sub> to 16 drops dev BLEU (Bilingual Evaluation Understudy, an n-gram overlap score for translation) from 25.8 to 25.1. "Determining compatibility is not easy" (§6.2).
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Q, K and V are three different inputs."
> In <b>self-attention</b> all three are projections of the same input X. Only in encoder-decoder attention do they come from different places (Q from the decoder, K and V from the encoder).
:::

::: reveal myth
? "Keys and values are the same thing."
> They come from the same tokens but use different projections. The <b>key</b> decides how much weight a token gets; the <b>value</b> is what actually gets passed on.
:::

::: reveal myth
? "Attention picks the single best-matching value."
> It outputs a <b>weighted average</b> of all values. Softmax gives every key some weight; in the toy, "it" still takes 15% from "street".
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? In the base model, what is the shape of one head's W<sup>Q</sup>?
- [ ] 64 × 64
- [x] 512 × 64
- [ ] 512 × 512
- [ ] 2048 × 512
> <b>512 × 64</b>: d<sub>model</sub> × d<sub>k</sub>, with d<sub>k</sub> = 512 / 8 heads (§3.2.2).
:::

::: quiz
? In encoder-decoder attention, which come from the encoder output?
- [ ] Queries only
- [x] Keys and values
- [ ] Queries and keys
- [ ] All three
> <b>Keys and values.</b> Queries come from the decoder (§3.2.3).
:::

<div class="quiz ">
  <p class="qq">In the toy, q(it)·k(animal) is the highest score. Why does "it" still give 15% of its weight to "street"?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Softmax never outputs exact zeros for finite scores. Every key gets <b>some</b> weight, in proportion to exp(score / √d<sub>k</sub>).</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Queries ask, keys answer, values deliver. softmax(q·k / √d<sub>k</sub>) decides how much of each value a token takes.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Each token's vector is projected three ways by learned matrices: a query (what it is looking for), a key (what it can be matched on) and a value (what it passes on). Compatibility is the dot product of a query with each key, scaled by 1/√d<sub>k</sub> and softmaxed into weights; the output is the weighted sum of values. Separate projections make matching asymmetric and let content differ from the features used for matching.</p></div>

<div class="recap">
  <div><span><b>Problem:</b> one embedding can't play all three roles: asking, being matched, and supplying content.</span></div>
  <div><span><b>Core idea:</b> learned projections give each token a query, a key and a value. softmax(q·k / √d<sub>k</sub>) weights the values to produce the output.</span></div>
</div>

<p class="start-hint">Next: <a href="../05-scaled-dot-product-attention/index.html">05 · Scaled dot-product attention →</a> · Previous: <a href="../03-self-attention/index.html">← 03</a> · <a href="../index.html">All concepts</a></p>

<!-- slide id="s-papers" from="papers" -->
