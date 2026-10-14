---
title: Position-wise Feed-Forward Networks
body:
  data-deck: Position-wise FFN
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
  - 'token vector :: 512 :: f'
  - 'W₁ + b₁ :: expand to 2,048 :: c'
  - 'ReLU :: max(0, ·) :: a'
  - 'W₂ + b₂ :: back to 512 :: e'
  caption: The same two-layer network applied to every position independently.
example:
  title: 'Worked example: where the parameters are'
  setup: 'Base model: d_model = 512, d_ff = 2,048, 6 encoder + 6 decoder layers.'
  steps:
  - 'One FFN: 2 × 512 × 2,048 weights + 2,560 biases = <b>2,099,712</b>.'
  - 'Twelve FFNs (6 encoder + 6 decoder): <b>25.2M</b>.'
  - 'Attention per block: 4 × 512² = 1,048,576; encoder 6 + decoder 12 attention blocks = <b>18.9M</b>.'
  - So the FFNs hold ≈ 39% of the ~65M parameters; embeddings hold much of the rest (~37K × 512).
  result: Attention moves information between positions; the FFN, with most of the layer weights, transforms each position.
traps:
  tricks:
  - 'd_ff = 4·d_model. :: 2,048 for 512.'
  - 'Per position, same weights. :: Like a 1 × 1 convolution.'
  - 'FFN params = 2·d·d_ff. :: About twice the attention params per layer.'
  traps:
  - 'Thinking the FFN mixes positions. :: It never looks at other tokens.'
  - 'Forgetting biases. :: The 2017 FFN has them (modern LLMs usually drop them).'
  - 'Assuming ReLU is still standard. :: Modern LLMs use gated SwiGLU FFNs.'
papers:
- vaswani
- glu
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Attention Is All You Need · 11</div>
    <h1>Position-wise feed-forward networks</h1>
    <p class="sub">After attention mixes information across tokens, a small two-layer network transforms each token's representation on its own.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Attention's output is a weighted <em>average</em> of value vectors. It moves information between tokens but does little non-linear processing of what each token now holds.</div>
      <div class="c"><b>Core idea</b>Apply FFN(x) = max(0, xW₁ + b₁)W₂ + b₂ (512 → 2048 → 512) to every position separately, with the same weights at every position and different weights in each layer.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## After gathering context, each token needs to compute new features

::: cards grid3
### [b] Attention gathers
It decides which tokens to take information from, and how much.

### [a] Then process it
Turning "it + context about the animal" into useful new features is a per-token computation.

### [e] Non-linearity
Rich features need non-linear transformations, layer after layer.
:::

<!-- slide id="s-prob" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## An attention output is always a blend of the values

The softmax weights are positive and sum to 1, so each output is a <b>convex combination</b> of the value vectors: it always lies inside the region they span. Attention <em>routes</em> information between tokens; on its own it doesn't add much new per-token computation. Change the weights below.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><button class="btn primary" id="hullBtn">Random attention weights</button><span class="readout" id="hullOut"></span></div>
  <svg id="hullSvg" viewBox="0 0 660 260" style="margin-top:8px" role="img" aria-label="Convex hull of value vectors"></svg>
</div>

<div class="takeaway">Something has to transform each token's gathered context into new features, non-linearly. That is the job of the FFN sub-layer.</div>

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What should process each token?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? After attention has mixed context into each token, what should transform each token's vector?
- [ ] Another attention layer
- [x] The same small MLP, applied to each position separately
- [ ] A recurrent layer running over the positions
- [ ] Nothing: attention is enough
> <b>B.</b> A position-wise feed-forward network adds a ReLU (rectified linear unit) non-linearity and more capacity per token. Tokens don't interact at this step, so it stays fully parallel. Another attention layer (A) mixes tokens again, and an RNN (C) would bring back sequential computation.
:::

<!-- slide id="s-pos" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## The same small network, applied to every position independently

Each token's 512-dim vector goes through its own copy of one shared MLP (multilayer perceptron): expand to 2048, ReLU, and project back to 512. Tokens don't interact in this step (attention already did that), so all positions run in parallel.
{: .lede}

<div class="visual"><svg id="posSvg" viewBox="0 0 660 260" role="img" aria-label="Position-wise FFN"></svg></div>

<div class="paper"><b>Two equivalent views (§3.3):</b> a fully connected network applied "to each position separately and identically", or "two convolutions with kernel size 1". The weights are shared across positions but differ from layer to layer.</div>

{{glance}}

<!-- slide id="s-relu" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Inside one FFN: expand, ReLU, project back <span class="ill">toy size 4 → 8 → 4</span>

The inner layer is 4× wider (d<sub>ff</sub> = 2048 = 4 × 512). ReLU switches hidden units off (to 0) depending on the input, which is where the non-linearity comes from. Slide between two token representations and watch different units turn on.
{: .lede}

<div class="visual">
  <label class="ctl">Input: token A ← → token B <input type="range" id="fT" min="0" max="1" step="0.02" value="0.3"> <output id="fTo"></output></label>
  <svg id="ffSvg" viewBox="0 0 660 250" style="margin-top:10px" role="img" aria-label="FFN activations"></svg>
</div>

<div class="eq">FFN(x) = max(0, x W₁ + b₁) W₂ + b₂ &nbsp;&nbsp; (2)</div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide raw -->
<section class="slide" id="s-paper" data-chapter="How">
  <div class="inner">
    <span class="qtag b5">5 · How it works</span> <span class="ill" style="color:var(--c);border-color:var(--c)">from the paper · §3.3</span>
    <h2>The paper's wording</h2>
    <hr>
    <div class="paper"><b>§3.3:</b> "In addition to attention sub-layers, each of the layers in our encoder and decoder contains a fully connected feed-forward network, which is applied to each position separately and identically. This consists of two linear transformations with a ReLU activation in between."</div>
    <div class="eq">FFN(x) = max(0, xW₁ + b₁)W₂ + b₂</div>
    <div class="paper">"While the linear transformations are the same across different positions, they use different parameters from layer to layer. Another way of describing this is as two convolutions with kernel size 1. The dimensionality of input and output is d<sub>model</sub> = 512, and the inner-layer has dimensionality d<sub>ff</sub> = 2048."</div>
  </div>
</section>

<!-- slide id="s-size" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Where the parameters are, and what d<sub>ff</sub> buys

<div class="grid2">
  <div class="visual" style="margin-top:0">
    <h3>Weights per encoder layer (base model)</h3>
    <div id="pBars"></div>
    <p class="caption">Attention: W<sup>Q</sup>, W<sup>K</sup>, W<sup>V</sup>, W<sup>O</sup> = 4 × 512 × 512. FFN: W₁ (512 × 2048) + W₂ (2048 × 512). Biases excluded.</p>
  </div>
  <div class="visual" style="margin-top:0">
    <h3>Table 3 (C): changing d<sub>ff</sub></h3>
    <div id="dBars"></div>
    <p class="caption">BLEU (Bilingual Evaluation Understudy, an n-gram overlap score for translation) on newstest2013 (dev), EN-DE. Total parameters: 53 M · 65 M · 90 M.</p>
  </div>
</div>

<div class="takeaway">About two-thirds of each encoder layer's weights are in the FFN, and a wider FFN improved BLEU (25.4 → 25.8 → 26.2).</div>

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "The FFN mixes information between tokens."
> It is <b>position-wise</b>: each token is transformed on its own. Only the attention sub-layers move information between positions.
:::

::: reveal myth
? "Each position has its own FFN weights."
> The weights are <b>shared across positions</b> within a layer, and differ from layer to layer (§3.3).
:::

::: reveal myth
? "The FFN is a small add-on next to attention."
> It holds about <b>two-thirds</b> of each encoder layer's weights: 2 × 512 × 2048 vs 4 × 512² for attention.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? What is the FFN's inner dimension in the base model?
- [ ] 512
- [ ] 1024
- [x] 2048
- [ ] 4096
> <b>2048</b> (d<sub>ff</sub>); 4096 in the big model.
:::

::: quiz
? Which activation does the paper's FFN use?
- [ ] Sigmoid
- [ ] tanh
- [x] ReLU
- [ ] Softmax
> <b>ReLU</b>: FFN(x) = max(0, xW₁ + b₁)W₂ + b₂.
:::

<div class="quiz ">
  <p class="qq">Why can the FFN be described as "two convolutions with kernel size 1"?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">A kernel-size-1 convolution applies the <b>same</b> linear map at every position and looks at only that position, which is exactly a shared per-position linear layer.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">A shared 512 → 2048 → 512 ReLU network transforms each token separately: attention moves information between tokens, and the FFN processes it.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Every encoder and decoder layer has a position-wise feed-forward network, FFN(x) = max(0, xW₁ + b₁)W₂ + b₂, with 512 → 2048 → 512 dimensions. The same weights apply at every position, which is equivalent to two kernel-size-1 convolutions, with different weights in each layer. It adds per-token non-linear processing after attention has mixed in context, and holds about two-thirds of each layer's parameters. A wider d<sub>ff</sub> improved BLEU in Table 3.</p></div>

<div class="recap">
  <div><span><b>Problem:</b> attention outputs are weighted averages of values. They mix tokens but add little per-token non-linear processing.</span></div>
  <div><span><b>Core idea:</b> a shared 512 → 2048 → 512 ReLU MLP applied to each position on its own, holding about 2/3 of each layer's weights.</span></div>
</div>

<p class="start-hint">Next: <a href="../12-parallel-training-vs-generation/index.html">12 · Parallel training vs autoregressive generation →</a> · Previous: <a href="../10-residual-layernorm/index.html">← 10</a> · <a href="../index.html">All concepts</a></p>

<!-- slide id="s-papers" from="papers" -->
