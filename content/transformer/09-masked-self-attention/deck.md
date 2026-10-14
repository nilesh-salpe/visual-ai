---
title: Masked Self-Attention
body:
  data-deck: Masked self-attention
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
  - 'shift right :: input = <bos> + target[:−1] :: f'
  - 'scores :: all pairs :: c'
  - 'mask j > i :: set to −∞ :: d'
  - 'softmax :: future gets weight 0 :: a'
  - 'predict token i+1 :: from positions ≤ i :: e'
  caption: Training sees the whole target but each position only sees its past.
example:
  title: 'Worked example: one masked row'
  setup: Four target positions. Position 1 (second token) has raw scores [1.0, 2.0, 3.0, 0.5] against positions 0–3.
  steps:
  - 'Mask positions 2 and 3 (future): [1.0, 2.0, −∞, −∞].'
  - softmax = <b>[0.269, 0.731, 0, 0]</b>.
  - 'Without the mask the row would be [0.085, 0.232, 0.631, 0.052]: most weight on a future token, which would let the model copy the answer.'
  - All 4 rows are computed in one pass; the mask makes that equivalent to 4 sequential steps.
  result: Masking turns one parallel pass into m correct next-token predictions.
traps:
  tricks:
  - 'Mask = lower-triangular. :: Position i sees 0…i.'
  - 'Shift right. :: Input at i is target i−1, so the prediction at i is target i.'
  - 'Same mask at inference. :: There, future tokens simply don''t exist yet.'
  traps:
  - 'Masking after softmax. :: Weights must be zeroed before normalization.'
  - 'Masking the encoder. :: The encoder is bidirectional.'
  - 'Off-by-one shifts. :: Without the shift the model sees the token it must predict.'
papers:
- vaswani
- seq2seq
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Attention Is All You Need · 09</div>
    <h1>Masked self-attention</h1>
    <p class="sub">How the decoder is stopped from seeing future target tokens, so a model trained on whole sentences can still generate one token at a time.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>During training the decoder is given the whole target sentence. If position i could attend to position i+1, it would simply copy the answer.</div>
      <div class="c"><b>Core idea</b>Shift the target right by one, and set every score for a future position to −∞ before the softmax. Position i can then use only positions ≤ i.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## At inference the model must predict without seeing the future

::: cards grid3
### [c] Generation is left to right
When producing token i, tokens i+1, i+2, … don't exist yet.

### [b] Training should match inference
If the model learns to rely on future tokens in training, it fails at test time.

### [a] But training should be parallel
We want to train every target position at the same time (deck 12).
:::

<div class="takeaway">How can every position be trained at once while each one only uses what came before it?</div>

<!-- slide id="s-prob" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## If the decoder can see ahead, it learns to copy

The decoder input is the target shifted right (start token first), and position i must predict target token i. Unmasked self-attention lets position i read the input at position i+1, <b>which is the token it is supposed to predict</b>. Training would look perfect, and generation would fail because that future token doesn't exist yet.
{: .lede}

<div class="visual">
  <div class="seg" id="cSeg"><button data-v="0" class="on">No mask</button><button data-v="1">With mask</button></div>
  <label class="ctl" style="margin-top:12px">Position i <input type="range" id="cI" min="0" max="5" step="1" value="1"> <output id="cIo"></output></label>
  <svg id="cSvg" viewBox="0 0 660 230" style="margin-top:6px" role="img" aria-label="Decoder positions and what they can see"></svg>
  <p class="readout" id="cOut"></p>
</div>

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## How would you hide the future?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? How can all positions be trained in parallel without any of them seeing future tokens?
- [ ] Train one position at a time
- [x] Set the scores for future positions to −∞ before the softmax
- [ ] Set the attention weights for future positions to 0 after the softmax
- [ ] Reverse the target sentence
> <b>B</b> is what the paper does. Option C sounds close, but zeroing weights <em>after</em> the softmax leaves the rows not summing to 1 (you'd have to renormalize). Masking with −∞ <em>before</em> the softmax gives exactly 0 weight and a correctly normalized distribution over the visible positions. Option A works but throws away parallelism.
:::

<!-- slide id="s-mask" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Shift right + mask: position i sees only positions ≤ i

The mask is a lower-triangular pattern. Scores above the diagonal are replaced by <b>−∞</b>, so after the softmax their weights are exactly 0. Drag the position to see each row of the mask.
{: .lede}

<div class="visual">
  <label class="ctl">Query position <input type="range" id="mI" min="0" max="5" step="1" value="2"> <output id="mIo"></output></label>
  <div class="grid2" style="margin-top:10px;align-items:center">
    <svg id="mSvg" viewBox="0 0 330 320" role="img" aria-label="Mask matrix"></svg>
    <div class="infobox" id="mInfo" style="margin-top:0"></div>
  </div>
</div>

{{glance}}

<!-- slide id="s-num" chapter="How" tag="5 · How it works" tagclass="b5" -->
## The masked softmax, computed live

The same scaled dot-product attention as deck 05, with one extra step between the scaling and the softmax. Step through it.
{: .lede}

<div class="visual">
  <div class="steps" id="nSteps"><button data-i="0" class="on">1 · scores QKᵀ/√d_k</button><button data-i="1">2 · apply mask (−∞)</button><button data-i="2">3 · softmax by row</button></div>
  <svg id="nSvg" viewBox="0 0 660 260" style="margin-top:10px" role="img" aria-label="Masked softmax matrices"></svg>
  <div class="infobox" id="nInfo"></div>
</div>

<div class="takeaway">Because the mask is just −∞ entries in one matrix, all positions are still computed <b>in parallel</b> during training, and none of them can see the future (deck 12).</div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide raw -->
<section class="slide" id="s-paper" data-chapter="How">
  <div class="inner">
    <span class="qtag b5">5 · How it works</span> <span class="ill" style="color:var(--c);border-color:var(--c)">from the paper · §3.1, §3.2.3, Figure 2</span>
    <h2>The paper's wording</h2>
    <hr>
    <div class="paper"><b>§3.1:</b> "We also modify the self-attention sub-layer in the decoder stack to prevent positions from attending to subsequent positions. This masking, combined with fact that the output embeddings are offset by one position, ensures that the predictions for position i can depend only on the known outputs at positions less than i."</div>
    <div class="paper"><b>§3.2.3:</b> "We need to prevent leftward information flow in the decoder to preserve the auto-regressive property. We implement this inside of scaled dot-product attention by masking out (setting to −∞) all values in the input of the softmax which correspond to illegal connections."</div>
    <div class="paper"><b>Figure 2:</b> the scaled dot-product attention diagram has an optional <b>Mask</b> block between Scale and SoftMax.</div>
  </div>
</section>

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works

::: cards grid2
### [e] Training sees what inference sees
With the mask and the shift-right input, position i depends only on positions &lt; i in the target, exactly the information available when generating.

### [a] Still fully parallel
The mask is just −∞ entries in one n × n matrix, so all positions are still computed in one pass.

### [b] Exact zeros, proper distribution
e<sup>−∞</sup> = 0, so masked positions get exactly 0 weight and each row still sums to 1 over visible positions.

### [c] Cheap
No extra parameters, and only one extra step (Figure 2's optional "Mask") before the softmax.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "The mask is applied to the attention weights after the softmax."
> It is applied to the <b>scores before the softmax</b>, by setting illegal entries to −∞ (§3.2.3).
:::

::: reveal myth
? "Masking means the decoder can't see the source sentence."
> Only the decoder's <b>self-attention</b> is masked. Encoder-decoder attention sees all source positions.
:::

::: reveal myth
? "The mask alone stops the model from cheating."
> You also need the <b>shift-right</b>: without it, position i would still see its own target token. The paper combines both (§3.1).
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? In masked self-attention, position 3 (0-indexed) can attend to which positions?
- [ ] Only 3
- [x] 0, 1, 2, 3
- [ ] 3, 4, 5, …
- [ ] All positions
> <b>0–3</b>: itself and everything before it.
:::

::: quiz
? What weight does a masked (−∞) score get after the softmax?
- [ ] A small positive number
- [x] Exactly 0
- [ ] −∞
- [ ] 1/n
> <b>Exactly 0</b>, since e<sup>−∞</sup> = 0.
:::

<div class="quiz ">
  <p class="qq">Why is the shift-right needed in addition to the mask?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Without it, decoder input position i would hold target token i, the very token it must predict. Shifting right by one (start token first) means position i holds token i−1.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Shift the target right and put −∞ above the diagonal: every position trains in parallel, yet only ever sees the past.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>At inference the decoder generates left to right, so in training a position must not see later tokens. The paper shifts the decoder input right by one and, inside scaled dot-product attention, sets the scores for future positions to −∞ before the softmax, which gives them exactly zero weight. Position i then depends only on positions before i, while all positions are still trained in one parallel pass.</p></div>

<div class="recap">
  <div><span><b>Problem:</b> with the full target visible in training, an unmasked decoder could copy future tokens.</span></div>
  <div><span><b>Core idea:</b> output embeddings offset by one, plus −∞ on future scores, means position i depends only on positions &lt; i in the target, while every position is still trained in parallel.</span></div>
</div>

<p class="start-hint">Next: <a href="../10-residual-layernorm/index.html">10 · Residuals and layer normalization →</a> · Previous: <a href="../08-encoder-decoder-attention/index.html">← 08</a> · <a href="../index.html">All concepts</a></p>

<!-- slide id="s-papers" from="papers" -->
