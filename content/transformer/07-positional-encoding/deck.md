---
title: Positional Encoding
body:
  data-deck: Positional encoding
  data-home: ../index.html
  data-home-label: Transformer
styles:
- ../../shared/deck.css
- ../../shared/learn.css
- ../tx.css
css: |-
  canvas { width: 100%; height: auto; display: block; border-radius: 8px; image-rendering: pixelated; }
scripts:
- ../../shared/deck.js
- ../tx.js
glance:
  steps:
  - 'token embedding :: 512 dims :: f'
  - '+ PE(pos) :: sinusoids, one wavelength per pair :: a'
  - 'encoder input :: content + position :: c'
  caption: PE(pos, 2i) = sin(pos / 10000^(2i/d)), PE(pos, 2i+1) = cos(…). Learned embeddings worked about as well (Table 3 row E).
example:
  title: 'Worked example: the range of wavelengths'
  setup: d_model = 512, so there are 256 sine/cosine pairs.
  steps:
  - 'Pair 0: PE(pos, 0) = sin(pos); wavelength <b>2π ≈ 6.3 positions</b>.'
  - 'Pair 255: divisor 10000<sup>510/512</sup> ≈ 9,647; wavelength ≈ <b>60,611</b> positions.'
  - 'At pos = 1: pair 0 gives sin(1) = 0.841; pair 255 gives sin(1/9,647) ≈ 0.00010.'
  - 'For any offset k, PE(pos + k) is a fixed linear function (a rotation) of PE(pos): the paper''s reason to hope for relative-position learning.'
  result: Fast pairs separate neighbours, slow pairs encode coarse position; this idea later became RoPE.
traps:
  tricks:
  - 'Wavelengths 2π … 10000·2π. :: A geometric progression across pairs.'
  - 'Offset = rotation. :: sin/cos pairs make PE(pos + k) linear in PE(pos).'
  - 'Learned ≈ sinusoidal. :: Table 3: 25.7 vs 25.8 BLEU.'
  traps:
  - 'Thinking PE is concatenated. :: It is added, at the input only.'
  - 'Expecting reliable extrapolation. :: The paper only hoped sinusoids might extrapolate; it wasn''t demonstrated.'
  - 'Forgetting attention is order-blind. :: Without PE, word order changes nothing.'
papers:
- vaswani
- shaw
- roformer
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Attention Is All You Need · 07</div>
    <h1>Positional encoding</h1>
    <p class="sub">Why attention needs explicit information about token order, and how fixed sinusoids at different frequencies provide it.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Self-attention treats its input as a set. Shuffle the words and each word gets exactly the same output, so "dog bites man" and "man bites dog" look alike.</div>
      <div class="c"><b>Core idea</b>Add a position-dependent vector PE(pos) to each embedding: sines and cosines whose wavelengths form a geometric progression from 2π to 10000·2π.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Word order carries meaning

::: cards grid3
### [d] Who did what
"dog bites man" and "man bites dog" use the same words with opposite meanings.

### [b] Translation reorders
German often moves the verb to the end of a clause, so the model must track where each word sits.

### [c] Relative position matters
"not" changes the word right after it; adjectives modify the noun next to them.
:::

<div class="takeaway">Any sequence model must know where each token is, and how far apart two tokens are.</div>

<!-- slide id="s-prob" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Without position information, word order doesn't change anything

Self-attention computes softmax(QKᵀ/√d<sub>k</sub>)V. Nothing in that formula depends on <em>where</em> a token is. Reorder the input and every token's output stays the same; only the order of the output rows changes. Below is a live toy self-attention (d = 4).
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <div class="seg" id="oSeg"><button data-v="a" class="on">"dog bites man"</button><button data-v="b">"man bites dog"</button></div>
    <div class="seg" id="peSeg"><button data-v="0" class="on">No positional encoding</button><button data-v="1">+ positional encoding</button></div>
  </div>
  <svg id="permSvg" viewBox="0 0 660 230" style="margin-top:12px" role="img" aria-label="Attention outputs per word"></svg>
  <p class="readout" id="permOut"></p>
</div>

<div class="takeaway">"The model contains no recurrence and no convolution", so the order has to be injected some other way (§3.5).</div>

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## How would you add order?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Without recurrence or convolution, how would you give the model information about token order?
- [ ] Append the raw position number (0, 1, 2, …) as an extra feature
- [x] Add a vector that encodes the position to each token's embedding
- [ ] Sort the tokens alphabetically
- [ ] Use the decoder's causal mask
> <b>B.</b> The paper adds a d<sub>model</sub>-dimensional positional encoding to each embedding. A raw integer (A) grows without bound and sits on a very different scale from the other features. Sorting (C) destroys order. The mask (D) exists only in the decoder and only blocks future positions; it doesn't say where a token is.
:::

<!-- slide id="s-add" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Add a position vector to each word vector

PE has the same dimension as the embeddings (d<sub>model</sub> = 512), so the two can be <b>summed</b>. This happens once, at the bottom of both the encoder and decoder stacks, and dropout is applied to the sum.
{: .lede}

<div class="visual"><svg id="addSvg" viewBox="0 0 660 220" role="img" aria-label="Embedding plus positional encoding"></svg></div>

<div class="eq">PE(pos, 2i) = sin(pos / 10000<sup>2i/d<sub>model</sub></sup>) &nbsp;&nbsp; PE(pos, 2i+1) = cos(pos / 10000<sup>2i/d<sub>model</sub></sup>)</div>

{{glance}}

<!-- slide id="s-heat" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Every dimension is a sinusoid with its own wavelength

Low dimensions oscillate quickly and high dimensions slowly. The wavelengths form a geometric progression <b>from 2π to 10000·2π</b>, so every position gets a unique pattern, a bit like the hands of a clock running at many speeds.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">Position <input type="range" id="hP" min="0" max="99" step="1" value="20"> <output id="hPo"></output></label>
    <label class="ctl">Dimension pair i <input type="range" id="hI" min="0" max="255" step="1" value="8"> <output id="hIo"></output></label>
  </div>
  <div class="grid2" style="margin-top:12px">
    <div><h3>PE matrix: positions 0–99 × dims 0–511</h3><canvas id="peCanvas" width="512" height="100" style="height:200px"></canvas><p class="caption">Teal = +1, red = −1. Row outline = selected position.</p></div>
    <div><h3>Dimension 2i over positions</h3><svg id="waveSvg" viewBox="0 0 320 170" role="img" aria-label="Sinusoid for selected dimension"></svg><p class="caption" id="waveCap"></p></div>
  </div>
</div>

<!-- slide id="s-rel" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Why sinusoids: a fixed offset k is a fixed rotation

For each frequency ω, the pair (sin ωp, cos ωp) is a point on a circle. Moving k positions rotates it by the angle ωk, <b>whatever p is</b>, so PE(pos+k) is a linear function of PE(pos). The authors hypothesized this would make it easy to attend by <b>relative position</b>.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">Position p <input type="range" id="rP" min="0" max="60" step="1" value="5"> <output id="rPo"></output></label>
    <label class="ctl">Offset k <input type="range" id="rK" min="0" max="20" step="1" value="4"> <output id="rKo"></output></label>
  </div>
  <div class="grid2" style="margin-top:10px;align-items:center">
    <svg id="circSvg" viewBox="0 0 320 272" role="img" aria-label="Rotation on a circle"></svg>
    <div><h3>Similarity PE(p)·PE(q), positions 0–63</h3><canvas id="simCanvas" width="64" height="64" style="max-width:280px"></canvas><p class="caption">The dot product depends only on the distance |p − q|: the same pattern along every diagonal.</p></div>
  </div>
</div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide raw -->
<section class="slide" id="s-paper" data-chapter="Why">
  <div class="inner">
    <span class="qtag b6">6 · Why it works</span> <span class="ill" style="color:var(--c);border-color:var(--c)">from the paper · §3.5, Table 3 (E)</span>
    <h2>The choice, and the experiment behind it</h2>
    <hr>
    <div class="paper"><b>§3.5:</b> "We chose this function because we hypothesized it would allow the model to easily learn to attend by relative positions, since for any fixed offset k, PE<sub>pos+k</sub> can be represented as a linear function of PE<sub>pos</sub>."</div>
    <div class="visual scroll-x">
      <table class="tbl">
        <tr><th>Variant (Table 3)</th><th>PPL (dev)</th><th>BLEU (dev)</th></tr>
        <tr><td>Base: sinusoidal positional encoding</td><td>4.92</td><td>25.8</td></tr>
        <tr><td>(E): learned positional embedding instead of sinusoids</td><td>4.92</td><td>25.7</td></tr>
      </table>
    </div>
    <div class="paper"><b>Why keep sinusoids?</b> The two versions produced nearly identical results. The sinusoidal one was chosen because it "may allow the model to extrapolate to sequence lengths longer than the ones encountered during training."</div>
  </div>
</section>

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "The positional encoding is concatenated to the embedding."
> It is <b>added</b>. PE has the same dimension d<sub>model</sub> as the embedding "so that the two can be summed" (§3.5).
:::

::: reveal myth
? "Positional encodings are added in every layer."
> They are added once, "at the bottoms of the encoder and decoder stacks" (§3.5). Residual connections carry them upward.
:::

::: reveal myth
? "Sinusoids were shown to beat learned position embeddings."
> The two gave <b>nearly identical</b> results (Table 3 E: 25.7 vs 25.8 BLEU (Bilingual Evaluation Understudy, an n-gram overlap score for translation)). Sinusoids were chosen because they may extrapolate to longer sequences.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? What range do the PE wavelengths span?
- [ ] 1 to 512
- [x] 2π to 10000·2π
- [ ] 0 to 1
- [ ] 2π to 512·2π
> <b>A geometric progression from 2π to 10000·2π</b> (§3.5).
:::

<div class="quiz ">
  <p class="qq">What is the positional encoding at position 0?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Every even dimension is sin(0) = <b>0</b> and every odd dimension is cos(0) = <b>1</b>.</div>
</div>

<div class="quiz ">
  <p class="qq">Without positional encoding, what happens to the encoder's per-token outputs if you shuffle the input words?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Each word gets <b>exactly the same output</b>, just in a different row order. Self-attention is permutation-invariant (see the "dog bites man" demo).</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Add a fixed sinusoidal code PE(pos) to every embedding, so attention can tell positions apart and a fixed offset becomes a fixed rotation.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Self-attention is permutation-invariant: shuffle the inputs and each token's output is unchanged, so it can't use word order. The paper adds positional encodings to the input embeddings: sines and cosines whose wavelengths range geometrically from 2π to 10000·2π. For any fixed offset k, PE(pos+k) is a linear function of PE(pos), which the authors hypothesized makes relative positions easy to learn. Learned position embeddings gave nearly identical results; sinusoids were kept because they may extrapolate to longer sequences.</p></div>

<div class="recap">
  <div><span><b>Problem:</b> attention is permutation-invariant, so without extra information it can't tell "dog bites man" from "man bites dog".</span></div>
  <div><span><b>Core idea:</b> add fixed sinusoids PE(pos) to the embeddings. Each position gets a unique code, and offsets become rotations. Learned PE scored the same (Table 3E).</span></div>
</div>

<p class="start-hint">Next: <a href="../08-encoder-decoder-attention/index.html">08 · Encoder-decoder attention →</a> · Previous: <a href="../06-multi-head-attention/index.html">← 06</a> · <a href="../index.html">All concepts</a></p>

<!-- slide id="s-papers" from="papers" -->
