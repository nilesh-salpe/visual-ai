---
title: Why the Transformer Works
body:
  data-deck: Why it works
  data-home: ../index.html
  data-home-label: Transformer
styles:
- ../../shared/deck.css
- ../../shared/learn.css
- ../tx.css
css: |-
  #mapSvg [data-i] { cursor: pointer; }
scripts:
- ../../shared/deck.js
- ../tx.js
glance:
  steps:
  - 'self-attention :: path length 1, parallel :: a'
  - 'multi-head :: several relations at once :: c'
  - 'positional encoding :: restores order :: b'
  - 'residual + LayerNorm :: trainable depth :: e'
  - 'FFN :: per-position compute :: f'
  caption: Four ingredients, each patching a specific weakness of plain attention.
example:
  title: 'Worked example: reading the ablations (Table 3, newstest2013)'
  setup: 'Base: perplexity 4.92, BLEU 25.8. Each row changes one setting.'
  steps:
  - 'Single head (h = 1): BLEU <b>24.9</b> → multiple heads matter.'
  - 'Smaller keys (d_k = 16): BLEU <b>25.1</b> → compatibility needs enough dimensions.'
  - 'No label smoothing (ε_ls = 0): perplexity improves to 4.67 but BLEU falls to <b>25.3</b>.'
  - 'Learned instead of sinusoidal positions: BLEU <b>25.7</b> → nearly identical.'
  result: The evidence supports multi-head attention and adequate key size; the specific position encoding mattered little.
traps:
  tricks:
  - 'Read ablations as one-change-at-a-time. :: Compare each row with the base row.'
  - 'Perplexity ≠ BLEU. :: Label smoothing hurts perplexity but helps BLEU.'
  - 'Dev set. :: Table 3 uses newstest2013, not the test set.'
  traps:
  - 'Over-reading small differences. :: A 0.1 BLEU change is within run-to-run noise.'
  - 'Generalizing to LLMs directly. :: These are translation models at 65M parameters.'
  - 'Treating attention maps as proof. :: They are suggestive, not causal explanations.'
papers:
- vaswani
- michel
- shaw
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Attention Is All You Need · 13</div>
    <h1>Why the Transformer works</h1>
    <p class="sub">How four ingredients together address the limits of recurrent sequence models: direct token-to-token connections, multiple heads, positional information, and stacked layers.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Recurrent models are slow to train (sequential), struggle with long-range dependencies (long paths), and capture all relationships through one hidden state.</div>
      <div class="c"><b>Core idea</b>Each ingredient fixes one limit. The paper's ablations (Table 3) measure how much each design choice matters.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Sequence models were slow to train and struggled with long-range structure

::: cards grid3
### [d] Speed
Recurrent models need n sequential steps per layer, which limits how much data and how many experiments you can afford.

### [b] Long-range structure
Dependencies between distant words have to cross long paths.

### [c] Many relationships
Reference, syntax and agreement all have to be captured at once.
:::

<!-- slide id="s-prob" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Three criteria that recurrent layers score poorly on

§4 compares layer types on three criteria. For translation-length sequences (n &lt; d), recurrence loses on all three.
{: .lede}

::: cards grid3
### [d] Parallelism
Sequential operations per layer: <b>RNN (recurrent neural network) O(n)</b> vs self-attention O(1). Training time grows with sequence length.

### [d] Long-range paths
Maximum path length: <b>RNN O(n)</b> vs self-attention O(1). Distant dependencies are harder to learn.

### [b] Compute per layer
<b>RNN O(n·d²)</b> vs self-attention O(n²·d). Self-attention is cheaper when n &lt; d, as in sentence-level translation with BPE (byte-pair encoding).
:::

<div class="takeaway">Attention fixes parallelism and path length, but on its own it brings two new problems: it is <b>order-blind</b>, and averaging <b>blurs</b> distinct relationships. The other ingredients address those.</div>

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Patch attention's weak spots

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Attention alone is order-blind and blurs relationships by averaging. Which two ingredients does the paper add to fix exactly those two problems?
- [x] Positional encoding and multi-head attention
- [ ] Dropout and label smoothing
- [ ] Beam search and checkpoint averaging
- [ ] Byte-pair encoding and a bigger vocabulary
> <b>A.</b> Positional encodings give attention word order (deck 07), and multiple heads counteract the "reduced effective resolution due to averaging" (§2, deck 06). The other options are training or decoding techniques, not fixes to attention itself.
:::

<!-- slide id="s-map" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Four ingredients, each solving a specific problem

Click an ingredient to see which problem it addresses and the evidence in the paper.
{: .lede}

<div class="grid2" style="grid-template-columns:1.3fr 1fr;align-items:center">
  <div class="visual" style="margin-top:0"><svg id="mapSvg" viewBox="0 0 520 330" role="img" aria-label="Ingredients to problems map"></svg></div>
  <div class="infobox" id="mapInfo" style="margin-top:0;min-height:200px"></div>
</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## How the ingredients fit together in one encoder layer

<div class="visual scroll-x">
  <table class="tbl">
    <tr><th>Step</th><th>Ingredient</th><th>Problem it handles</th><th>Deck</th></tr>
    <tr><td>0</td><td>Embedding × √d<sub>model</sub> + positional encoding</td><td>Order</td><td><a href="../07-positional-encoding/index.html">07</a></td></tr>
    <tr><td>1</td><td>Multi-head self-attention</td><td>Parallel computation, one-hop paths, several relationships</td><td><a href="../03-self-attention/index.html">03</a>–<a href="../06-multi-head-attention/index.html">06</a></td></tr>
    <tr><td>2</td><td>Add &amp; Norm</td><td>Stable signal and gradient flow</td><td><a href="../10-residual-layernorm/index.html">10</a></td></tr>
    <tr><td>3</td><td>Position-wise FFN (feed-forward network)</td><td>Per-token non-linear processing</td><td><a href="../11-position-wise-ffn/index.html">11</a></td></tr>
    <tr><td>4</td><td>Add &amp; Norm, then repeat × 6</td><td>Depth</td><td><a href="../10-residual-layernorm/index.html">10</a></td></tr>
    <tr><td>Decoder</td><td>+ masked self-attention, + encoder-decoder attention</td><td>Causal generation, reading the source</td><td><a href="../09-masked-self-attention/index.html">09</a>, <a href="../08-encoder-decoder-attention/index.html">08</a></td></tr>
  </table>
</div>

<!-- slide id="s-abl" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## The evidence: Table 3 model variations

Each row changes one thing relative to the base model and reports BLEU (Bilingual Evaluation Understudy, an n-gram overlap score for translation) and perplexity on the EN-DE development set (newstest2013). Pick a group.
{: .lede}

<div class="visual">
  <div class="seg" id="aSeg"><button data-v="A" class="on">(A) heads</button><button data-v="B">(B) key size</button><button data-v="C">(C) model size</button><button data-v="D">(D) regularization</button><button data-v="E">(E) positions</button><button data-v="big">big</button></div>
  <div class="grid2" style="margin-top:14px">
    <div><h3>BLEU (dev), higher is better</h3><div id="aBleu"></div></div>
    <div><h3>PPL (dev), lower is better</h3><div id="aPpl"></div></div>
  </div>
  <p class="readout" id="aNote" style="margin-top:10px"></p>
</div>

<div class="cite">Table 3, arXiv:1706.03762v7. Beam search as in §6.1 but no checkpoint averaging. Perplexities are per word-piece. Bars are drawn relative to the base model (grey line = base).</div>

<!-- slide id="s-interp" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## A side benefit: you can look inside

Attention weights can be visualized directly. The paper reports that different heads learn different jobs, many related to the structure of the sentence.
{: .lede}

::: cards grid3
### [a] Figure 3
Layer 5 of 6: many heads link "making" to the distant "more difficult", a long-range dependency handled in one hop.

### [c] Figure 4
Two heads apparently doing anaphora resolution: very sharp attention from "its" to "Law" and "application".

### [e] Figure 5
Two heads with different, structure-related patterns over the same sentence: "The heads clearly learned to perform different tasks."
:::

<div class="cite">See deck 03 for a redraw of Figures 3 and 4.</div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide raw -->
<section class="slide" id="s-paper" data-chapter="Why">
  <div class="inner">
    <span class="qtag b6">6 · Why it works</span> <span class="ill" style="color:var(--c);border-color:var(--c)">from the paper · §4, §6.2, §7</span>
    <h2>The paper's own conclusions</h2>
    <hr>
    <div class="paper"><b>§6.2 (A):</b> "While single-head attention is 0.9 BLEU worse than the best setting, quality also drops off with too many heads."</div>
    <div class="paper"><b>§6.2 (B):</b> "Reducing the attention key size d<sub>k</sub> hurts model quality. This suggests that determining compatibility is not easy and that a more sophisticated compatibility function than dot product may be beneficial."</div>
    <div class="paper"><b>§6.2 (C, D, E):</b> "Bigger models are better, and dropout is very helpful in avoiding over-fitting." Replacing sinusoids with learned positional embeddings gives "nearly identical results".</div>
    <div class="paper"><b>§7:</b> the Transformer is "the first sequence transduction model based entirely on attention", and "can be trained significantly faster than architectures based on recurrent or convolutional layers."</div>
  </div>
</section>

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? ""Attention is all you need" means the model is only attention."
> The model also depends on <b>position-wise FFNs, residual connections, layer normalization, positional encodings and embeddings</b>. The title means no recurrence and no convolution.
:::

::: reveal myth
? "In Table 3, bigger is always better."
> Bigger d<sub>model</sub> and d<sub>ff</sub> helped, but <b>too many heads</b> (h = 32) hurt, and removing dropout hurt (24.6 BLEU).
:::

::: reveal myth
? "The gains come from one key trick."
> Table 3 shows <b>many</b> design choices each matter: heads, key size, depth, width, dropout and label smoothing.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

<div class="quiz">
  <p class="qq">Table 3 (C): what dev BLEU did N = 2 layers get, against 25.8 for the base model?</p>
  <div class="opts">
  <button>A. 25.5</button>
  <button>B. 24.9</button>
  <button data-ok>C. 23.7</button>
  <button>D. 26.4</button>
  </div>
  <div class="why"><b>23.7</b>: depth matters.</div>
</div>

::: quiz
? Learned positional embeddings vs sinusoids (row E)?
- [ ] Much worse
- [x] Nearly identical (25.7 vs 25.8)
- [ ] Much better
- [ ] Not tested
> <b>Nearly identical.</b> Sinusoids were kept for possible extrapolation to longer sequences.
:::

<div class="quiz ">
  <p class="qq">Which Table 1 property best explains why long-range dependencies are easier to learn in a Transformer?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why"><b>Maximum path length O(1)</b>: any two positions are one attention step apart, compared with O(n) for recurrence.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Direct attention for speed and reach, multiple heads for several relationships, positional encoding for order, and residual stacks with FFNs for depth. Table 3 shows each one matters.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>The Transformer works because each ingredient fixes a specific weakness. Self-attention makes layers fully parallel with O(1) paths between any two tokens. Multiple heads counteract the blurring from averaging. Positional encodings supply the order that attention ignores. Residual connections, layer normalization and position-wise FFNs make a deep stack trainable and expressive. The paper's ablations back this up: one head, a smaller d<sub>k</sub>, fewer layers or no dropout all lower BLEU.</p></div>

<div class="recap">
  <div><span><b>Problem:</b> recurrence is sequential, uses long paths between distant tokens, and squeezes all relationships into one state.</span></div>
  <div><span><b>Core idea:</b> direct attention (parallel, O(1) paths) + multiple heads (several relationships) + positional encoding (order) + stacked residual layers with FFNs (depth), each backed by the Table 3 ablations.</span></div>
</div>

<p class="start-hint">Next: <a href="../14-experimental-results/index.html">14 · Experimental results →</a> · Previous: <a href="../12-parallel-training-vs-generation/index.html">← 12</a> · <a href="../index.html">All concepts</a></p>

<!-- slide id="s-papers" from="papers" -->
