---
title: The Transformer Architecture
body:
  data-deck: Transformer architecture
  data-home: ../index.html
  data-home-label: Transformer
styles:
- ../../shared/deck.css
- ../../shared/learn.css
- ../tx.css
css: |-
  #figSvg [data-k] { cursor: pointer; }
    #figSvg [data-k]:hover rect, #figSvg [data-k]:hover circle { filter: brightness(1.12); }
    .shape { font: 700 22px 'JetBrains Mono', monospace; color: var(--a); }
scripts:
- ../../shared/deck.js
- ../tx.js
glance:
  steps:
  - 'source tokens :: embedding + positions :: f'
  - 'encoder × 6 :: self-attention + FFN :: a'
  - 'decoder × 6 :: masked self-attn,

    cross-attn, FFN :: c'
  - 'linear + softmax :: next-token probabilities :: e'
  caption: 'Every sub-layer: residual connection + layer normalization; d_model = 512 throughout (base).'
example:
  title: 'Worked example: shapes through the base model'
  setup: 'Translate a 10-token source into a 9-token target prefix. Base model: d_model = 512, 8 heads, d_ff = 2,048, N = 6, shared vocabulary of about 37,000 tokens.'
  steps:
  - 'Source embeddings + positional encoding: <b>[10, 512]</b>; every encoder layer keeps [10, 512].'
  - 'Target prefix (shifted right): <b>[9, 512]</b> through 6 decoder layers; cross-attention weights per head are [9, 10].'
  - 'Output projection: [9, 512] × [512, ~37,000] → <b>[9, ~37,000]</b> logits: one next-token distribution per target position.'
  - 'Parameters: base ≈ <b>65M</b>, big (d_model 1,024, 16 heads, d_ff 4,096) ≈ <b>213M</b>.'
  result: The width stays 512 everywhere; only attention patterns and the FFN expansion change what each position holds.
traps:
  tricks:
  - 'Three attentions. :: Encoder self-attention, masked decoder self-attention, encoder-decoder (cross) attention.'
  - 'Width never changes. :: All sub-layers in and out are d_model = 512 so residuals can add.'
  - 'Shared embeddings. :: Input, output embeddings and pre-softmax projection share weights (scaled by √d_model in the input).'
  traps:
  - 'Thinking the encoder sees the target. :: Only the decoder sees the (shifted) target.'
  - 'Forgetting the decoder''s third sub-layer. :: Cross-attention sits between masked self-attention and the FFN.'
  - 'Mixing base and big settings. :: Big doubles d_model and heads and uses dropout 0.3 on EN-DE.'
papers:
- vaswani
- bytenet
- convs2s
- gnmt
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Attention Is All You Need · 02</div>
    <h1>The Transformer architecture</h1>
    <p class="sub">An encoder-decoder built entirely from attention and position-wise feed-forward layers, with no recurrence and no convolution.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Earlier sequence models relied on recurrence or convolution, so the number of operations needed to relate two positions grew with the distance between them.</div>
      <div class="c"><b>Core idea</b>Stack N = 6 identical encoder layers and N = 6 decoder layers built from multi-head attention and feed-forward sub-layers, each wrapped in a residual connection and layer normalization.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Sequence transduction: read one sequence, write another

Machine translation maps an input sequence (English) to an output sequence (German) of a different length and word order. The standard design in 2017 was an <b>encoder-decoder</b>: the encoder reads the source, and the decoder writes the target one token at a time.
{: .lede}

::: cards grid3
### [a] Encoder
Turns the source tokens (x<sub>1</sub>…x<sub>n</sub>) into a sequence of continuous representations z = (z<sub>1</sub>…z<sub>n</sub>) (§3).

### [c] Decoder
Generates the output y<sub>1</sub>…y<sub>m</sub> one symbol at a time, using z and the symbols it has already produced.

### [b] How positions talk
The open question is how information moves between positions inside each stack. Before this paper: recurrence or convolution, usually with attention added between encoder and decoder.
:::

<!-- slide id="s-prob" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## In earlier models, linking two positions cost more the farther apart they were

The paper's §2 compares architectures by how many operations it takes to relate signals from two arbitrary positions. Drag the distance between the two positions.
{: .lede}

<div class="visual">
  <label class="ctl">Distance between positions <input type="range" id="dD" min="1" max="200" step="1" value="40"> <output id="dDo"></output></label>
  <div id="dBars" style="margin-top:14px"></div>
</div>

<p class="caption">From §2: the operations needed "grows in the distance between positions, linearly for ConvS2S and logarithmically for ByteNet"; the Transformer reduces this to a constant. Shown with kernel width k = 3 and an RNN (recurrent neural network)'s one step per position. Constants are illustrative; the growth rates come from the paper.</p>

<div class="takeaway">The constant path comes at a price the paper names: averaging attention-weighted positions reduces effective resolution, "an effect we counteract with Multi-Head Attention" (§2).</div>

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What would the model need?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Suppose you delete recurrence and convolution entirely. What must the model still have in order to work?
- [ ] Nothing else: attention alone is enough
- [x] A way to mix information across positions, a way to encode word order, and per-position processing
- [ ] Larger embeddings
- [ ] A single convolution at the input
> <b>B.</b> Attention mixes information across positions, but it is blind to order and only averages values. The paper adds <b>positional encodings</b> (order), <b>position-wise feed-forward networks</b> (per-token processing), and residual connections with layer normalization (stable stacking). The title is a slogan; the model is more than attention.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Keep the encoder-decoder; build every layer from attention and feed-forward blocks

The breakthrough is what is <em>left out</em>: no recurrence and no convolution. Six building blocks do all the work.
{: .lede}

<div class="grid3">
  <div class="card" style="border-top:3px solid var(--b)"><h3>Multi-head self-attention</h3><p>Mixes information between all positions in one step. <a href="../03-self-attention/index.html">Decks 03–06</a></p></div>
  <div class="card" style="border-top:3px solid #3a8fd8"><h3>Position-wise FFN</h3><p>Transforms each token on its own. <a href="../11-position-wise-ffn/index.html">Deck 11</a></p></div>
  <div class="card e"><h3>Add &amp; Norm</h3><p>Residual connection + layer normalization around every sub-layer. <a href="../10-residual-layernorm/index.html">Deck 10</a></p></div>
  <div class="card" style="border-top:3px solid #c9a227"><h3>Positional encoding</h3><p>Injects word order into the embeddings. <a href="../07-positional-encoding/index.html">Deck 07</a></p></div>
  <div class="card c"><h3>Encoder-decoder attention</h3><p>Lets the decoder read the source. <a href="../08-encoder-decoder-attention/index.html">Deck 08</a></p></div>
  <div class="card d"><h3>Masked self-attention</h3><p>Stops the decoder seeing future tokens. <a href="../09-masked-self-attention/index.html">Deck 09</a></p></div>
</div>

{{glance}}

<!-- slide id="s-fig" chapter="How" tag="5 · How it works" tagclass="b5" -->
## The full model: an encoder stack and a decoder stack (Figure 1)

<div class="grid2" style="grid-template-columns:1.25fr 1fr">
  <div class="visual" style="margin-top:0"><svg id="figSvg" style="max-height:74vh" viewBox="0 0 660 600" role="img" aria-label="Transformer model architecture, after Figure 1"></svg></div>
  <div>
    <div class="infobox" id="figInfo" style="margin-top:0;min-height:220px"><b>Click any block</b> in the diagram to see what it does, its dimensions, and which deck in this guide covers it.</div>
    <div class="key"><span><i style="background:var(--a)"></i>encoder</span><span><i style="background:var(--c)"></i>decoder</span><span><i style="background:var(--b)"></i>attention</span><span><i style="background:#3a8fd8"></i>feed-forward</span><span><i style="background:var(--e)"></i>add &amp; norm</span><span><i style="background:#c9a227"></i>positional encoding</span></div>
  </div>
</div>

<div class="cite">Redrawn after Figure 1 of the paper. Dashed lines are residual connections.</div>

<!-- slide id="s-flow" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Follow one sentence through the model: shapes at every stage

Translating a source sentence of n tokens. While training, the decoder sees the m target tokens, shifted right by one position. Every sub-layer keeps the width at d<sub>model</sub> = 512, which is what lets the residual connections add their input to their output.
{: .lede}

<div class="visual">
  <div class="steps" id="flowSteps"></div>
  <div class="infobox" id="flowInfo" style="min-height:110px"></div>
</div>

<div class="takeaway">The encoder runs once per source sentence and produces a "memory" of n × 512 vectors. Every decoder layer reads that same memory through encoder-decoder attention.</div>

<!-- slide id="s-cfg" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Two sizes: base and big

<div class="visual scroll-x">
  <table class="tbl">
    <tr><th>Hyperparameter</th><th>Base</th><th>Big</th><th>Meaning</th></tr>
    <tr><td>N</td><td>6</td><td>6</td><td>layers in each of the encoder and decoder</td></tr>
    <tr><td>d<sub>model</sub></td><td>512</td><td>1024</td><td>width of every token representation</td></tr>
    <tr><td>d<sub>ff</sub></td><td>2048</td><td>4096</td><td>inner width of the feed-forward network</td></tr>
    <tr><td>h</td><td>8</td><td>16</td><td>attention heads</td></tr>
    <tr><td>d<sub>k</sub> = d<sub>v</sub></td><td>64</td><td>64</td><td>per-head key/value width (d<sub>model</sub>/h)</td></tr>
    <tr><td>P<sub>drop</sub></td><td>0.1</td><td>0.3 (0.1 for EN-FR)</td><td>residual dropout</td></tr>
    <tr><td>ε<sub>ls</sub></td><td>0.1</td><td>0.1</td><td>label smoothing</td></tr>
    <tr><td>Training</td><td>100K steps · 12 h</td><td>300K steps · 3.5 days</td><td>on one machine with 8 NVIDIA P100 GPUs (graphics processing units)</td></tr>
    <tr><td>Parameters</td><td>65 M</td><td>213 M</td><td>Table 3</td></tr>
  </table>
</div>

<div class="cite">Table 3 (base and big rows), §5.2, §6.1. Values left blank in Table 3 equal the base model.</div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide raw -->
<section class="slide" id="s-paper" data-chapter="How">
  <div class="inner">
    <span class="qtag b5">5 · How it works</span> <span class="ill" style="color:var(--c);border-color:var(--c)">from the paper · §3.1, §3.4</span>
    <h2>The paper's own description</h2>
    <hr>
    <div class="paper"><b>Encoder:</b> a stack of N = 6 identical layers, each with two sub-layers: multi-head self-attention, and a simple, position-wise fully connected feed-forward network. Each sub-layer has a residual connection followed by layer normalization, so its output is <code>LayerNorm(x + Sublayer(x))</code>, and all outputs have dimension d<sub>model</sub> = 512.</div>
    <div class="paper"><b>Decoder:</b> also N = 6 layers, with a third sub-layer that performs multi-head attention over the output of the encoder stack. Its self-attention is masked, and together with output embeddings offset by one position, this ensures predictions for position i can depend only on outputs at positions less than i.</div>
    <div class="paper"><b>Embeddings (§3.4):</b> learned embeddings convert tokens to d<sub>model</sub>-dimensional vectors. The two embedding layers and the pre-softmax linear transformation share the same weight matrix, and in the embedding layers those weights are multiplied by √d<sub>model</sub>.</div>
  </div>
</section>

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why this design works

::: cards grid2
### [a] Constant path length
Any two positions are connected by one attention step in every layer, compared with O(n) for recurrence (Table 1). Long-range dependencies become easier to learn.

### [e] Parallel training
All positions in a layer are computed at once. The decoder stays auto-regressive through masking plus the shifted-right input, yet still trains on every position in parallel.

### [b] Easy to stack
Every sub-layer outputs d<sub>model</sub> = 512, so residual connections can add input to output, and N = 6 identical layers stack cleanly. Table 3 (C): N = 2 gives 23.7 BLEU (Bilingual Evaluation Understudy, an n-gram overlap score for translation), N = 6 gives 25.8.

### [c] Evidence
New state of the art on WMT (Workshop on Machine Translation) 2014 EN-DE (28.4 BLEU) and EN-FR (41.8) at a fraction of the training cost (Table 2, deck 14).
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "The original Transformer is a decoder-only model."
> The 2017 model is an <b>encoder-decoder</b>: a 6-layer encoder and a 6-layer decoder joined by encoder-decoder attention.
:::

::: reveal myth
? "Encoder and decoder layers are identical."
> Encoder layers have 2 sub-layers (self-attention, FFN). Decoder layers have <b>3</b>: masked self-attention, encoder-decoder attention, FFN.
:::

::: reveal myth
? "The encoder output only feeds the first decoder layer."
> <b>Every</b> decoder layer attends to the final encoder output through its encoder-decoder attention sub-layer.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? How many sub-layers does each decoder layer have?
- [ ] 1
- [ ] 2
- [x] 3
- [ ] 6
> <b>3</b>: masked multi-head self-attention, multi-head attention over the encoder output, and the position-wise FFN (§3.1).
:::

::: quiz
? For an n-token source, what shape leaves the base encoder?
- [ ] n × 64
- [x] n × 512
- [ ] n × 2048
- [ ] 512 × 512
> <b>n × 512.</b> Every sub-layer keeps d<sub>model</sub> = 512. See "Follow one sentence through the model".
:::

<div class="quiz ">
  <p class="qq">Why must every sub-layer output exactly d<sub>model</sub> = 512 dimensions?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Because each sub-layer is wrapped as LayerNorm(<b>x + Sublayer(x)</b>): you can only add the input to the output if their shapes match (§3.1).</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">An encoder-decoder built only from attention and position-wise feed-forward sub-layers, each wrapped as LayerNorm(x + Sublayer(x)), stacked 6 deep on each side.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>The Transformer keeps the encoder-decoder structure but drops recurrence and convolution. Each of the 6 encoder layers has multi-head self-attention and a position-wise FFN; each of the 6 decoder layers adds masked self-attention and attention over the encoder output. Every sub-layer is LayerNorm(x + Sublayer(x)) with d<sub>model</sub> = 512, and sinusoidal positional encodings added to the embeddings provide word order.</p></div>

<div class="recap">
  <div><span><b>Problem:</b> recurrent and convolutional models needed more operations to relate positions the farther apart they were.</span></div>
  <div><span><b>Core idea:</b> an encoder-decoder made only of attention and position-wise FFN sub-layers, each wrapped as LayerNorm(x + Sublayer(x)), with N = 6 layers on each side, d<sub>model</sub> = 512.</span></div>
</div>

<p class="start-hint">Next: <a href="../03-self-attention/index.html">03 · Self-attention →</a> · Previous: <a href="../01-sequential-bottleneck/index.html">← 01</a> · <a href="../index.html">All concepts</a></p>

<!-- slide id="s-papers" from="papers" -->
