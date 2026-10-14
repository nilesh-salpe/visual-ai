---
title: Parallel Training vs Generation
body:
  data-deck: Training vs generation
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
  - 'training :: whole target known :: a'
  - 'one masked pass :: m predictions in parallel :: e'
  - 'generation :: target unknown :: b'
  - 'm sequential passes :: one token each :: d'
  caption: Teacher forcing makes training parallel; generation stays autoregressive.
example:
  title: 'Worked example: sequential steps for one 20-token translation'
  setup: Target length m = 20; beam size 4 and length penalty α = 0.6 at inference (paper §6.1).
  steps:
  - 'Training: <b>1</b> decoder pass gives 20 predictions and 20 loss terms.'
  - 'Greedy generation: <b>20</b> sequential decoder passes.'
  - 'Beam search with width 4: still 20 sequential steps, but each step scores <b>4</b> hypotheses (4× the work per step).'
  - An RNN decoder would also need 20 sequential steps in training; the Transformer removes them only in training.
  result: Parallelism helps training most; inference speed later needed KV caching and other tricks.
traps:
  tricks:
  - 'Teacher forcing. :: Feed the gold previous tokens during training.'
  - 'Beam 4, α = 0.6. :: The paper''s translation settings; max length = input + 50.'
  - 'Encoder runs once. :: Only the decoder repeats per generated token.'
  traps:
  - '"Transformers generate in parallel." :: Standard decoding is one token per step.'
  - 'Exposure bias. :: Training sees gold prefixes, inference sees its own outputs.'
  - 'Beam = better always. :: Wide beams can favour short or generic outputs without a length penalty.'
papers:
- vaswani
- seq2seq
- gnmt
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Attention Is All You Need · 12</div>
    <h1>Parallel training vs autoregressive generation</h1>
    <p class="sub">Why the Transformer trains on every target position at once, but still has to generate translations one token at a time.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>An RNN (recurrent neural network) is sequential in both training and inference. Fast training needs every position processed at once, but generated tokens only become known one by one.</div>
      <div class="c"><b>Core idea</b>In training, feed the whole reference target (shifted right) and use masking, so all m predictions come from one parallel pass. At inference, generate left to right, using beam search.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-prob" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Count the sequential steps for one target sentence

For a target of m tokens: an RNN decoder needs m dependent steps <em>even in training</em>. A Transformer decoder needs one parallel pass in training, but m passes when generating, because token t+1 can't be computed until token t is chosen.
{: .lede}

<div class="visual">
  <label class="ctl">Target length m <input type="range" id="tM" min="2" max="40" step="1" value="12"> <output id="tMo"></output></label>
  <svg id="tSvg" viewBox="0 0 660 220" style="margin-top:10px" role="img" aria-label="Sequential steps comparison"></svg>
</div>

<div class="takeaway">The Transformer makes <b>training</b> parallel. Generation stays sequential. The paper lists "making generation less sequential" as future work (§7).</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Two constraints pull in opposite directions

::: cards grid3
### [d] Generation is inherently sequential
Token t+1 depends on token t, which doesn't exist until it has been chosen.

### [b] RNNs copy that structure into training
An RNN decoder computes h<sub>t</sub> from h<sub>t−1</sub>, so even with the reference translation available, training takes m dependent steps.

### [c] Greedy decoding can't recover
Choosing only the single most likely token at each step locks in early mistakes.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Use what you know in training

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? In training you already know the whole reference translation. How can you use that to make training parallel?
- [ ] Feed the model its own predictions, one step at a time
- [x] Feed the reference translation shifted right, with a mask so no position sees the future
- [ ] Predict all target tokens with no decoder input
- [ ] Train only the encoder
> <b>B</b>: teacher forcing plus masking. Every position gets the true previous tokens as input, and the mask hides later ones, so all m predictions come from one forward pass. Option A is sequential again, and C drops the information that each prediction needs.
:::

<!-- slide id="s-train" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Training: one forward pass gives m predictions and m loss terms

The decoder input is the reference translation shifted right by one (teacher forcing). Masked self-attention stops each position from seeing later tokens, so every position can be trained <b>at the same time</b>.
{: .lede}

<div class="visual"><svg id="trSvg" viewBox="0 0 660 270" role="img" aria-label="Parallel training"></svg></div>

<p class="caption">Loss: cross-entropy at each position against the next reference token, with label smoothing ε<sub>ls</sub> = 0.1 (§5.4). Batches hold about 25,000 source + 25,000 target tokens.</p>

{{glance}}

<!-- slide id="s-gen" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Generation: one token per decoder pass, fed back in

The encoder runs <b>once</b> on the source. Then the decoder runs repeatedly: each pass reads the tokens generated so far plus the encoder memory, and predicts the next token, which is appended to the input. Step through it.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><button class="btn primary" id="gStep">Next token →</button><button class="btn" id="gReset">Reset</button><span class="readout" id="gOut"></span></div>
  <svg id="gSvg" viewBox="0 0 660 250" style="margin-top:10px" role="img" aria-label="Autoregressive generation"></svg>
</div>

<!-- slide id="s-beam" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Beam search: keep the 4 best partial translations <span class="ill">toy probabilities</span>

Instead of greedily keeping only the single best token at each step, the paper keeps a <b>beam of 4</b> hypotheses, extends each, and keeps the 4 highest-scoring by total log-probability. Finished hypotheses are ranked with a length penalty (α = 0.6).
{: .lede}

<div class="visual">
  <label class="ctl">Decoding step <input type="range" id="bS" min="1" max="7" step="1" value="1"> <output id="bSo"></output></label>
  <div class="grid2" style="margin-top:10px">
    <div><h3>Alive hypotheses (beam = 4)</h3><div id="bAlive"></div></div>
    <div><h3>Finished (ended with &lt;/s&gt;)</h3><div id="bDone"></div></div>
  </div>
</div>

<p class="caption">Toy next-token probabilities, hand-written for illustration. Length penalty lp(Y) = ((5 + |Y|) / 6)<sup>α</sup>, the GNMT (Google's Neural Machine Translation system) form the paper cites [38]; final score = log P(Y) / lp(Y). Maximum output length = input length + 50, with early termination (§6.1).</p>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide raw -->
<section class="slide" id="s-paper" data-chapter="How">
  <div class="inner">
    <span class="qtag b5">5 · How it works</span> <span class="ill" style="color:var(--c);border-color:var(--c)">from the paper · §3, §6.1, §7</span>
    <h2>The paper's wording</h2>
    <hr>
    <div class="paper"><b>§3:</b> "At each step the model is auto-regressive, consuming the previously generated symbols as additional input when generating the next."</div>
    <div class="paper"><b>§6.1:</b> "We used beam search with a beam size of 4 and length penalty α = 0.6 … We set the maximum output length during inference to input length + 50, but terminate early when possible." Base models average the last 5 checkpoints and big models the last 20.</div>
    <div class="paper"><b>§7:</b> "Making generation less sequential is another research goals of ours."</div>
  </div>
</section>

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works

::: cards grid2
### [e] The same context in training and at inference
Masking plus shift-right means each position conditions only on earlier tokens, just as it will when generating.

### [a] m loss terms from one pass
Every target position contributes to the loss in a single parallel forward and backward pass, so GPUs (graphics processing units) stay busy.

### [c] Beam search hedges
Keeping 4 hypotheses lets the decoder recover from a locally attractive but globally poor token.

### [b] Length penalty
Summed log-probabilities favour shorter outputs; dividing by lp(Y) with α = 0.6 counters that bias.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Transformers generate all output tokens at once."
> Only <b>training</b> is parallel across positions. Generation produces one token per decoder pass (§3: "auto-regressive").
:::

::: reveal myth
? "Teacher forcing lets the model see the token it is predicting."
> It sees only the <b>previous</b> reference tokens. Shift-right plus the mask hide the current and future ones.
:::

::: reveal myth
? "Beam search finds the best possible translation."
> It is an <b>approximate</b> search that keeps only the 4 best partial hypotheses at each step.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Which beam size and length penalty does the paper use for translation?
- [ ] 1 and 1.0
- [x] 4 and 0.6
- [ ] 10 and 0.3
- [ ] 21 and 0.3
> <b>Beam 4, α = 0.6</b> (§6.1). Beam 21 with α = 0.3 was used for parsing.
:::

::: quiz
? What is the maximum output length at inference?
- [ ] 50 tokens
- [x] Input length + 50
- [ ] 2 × input length
- [ ] Unlimited
> <b>Input length + 50</b>, terminating early when possible.
:::

<div class="quiz ">
  <p class="qq">How many encoder passes and how many decoder passes does it take to generate a 20-token translation?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why"><b>1 encoder pass</b> (the source is fixed) and <b>one decoder pass per generated token</b>, about 20 (21 including the end token).</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Train with the reference shifted right and masked, so all positions train in one pass. Generate one token at a time, with beam search.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>In training the decoder receives the reference translation shifted right, and masked self-attention stops any position from seeing later tokens, so all m positions are predicted and trained in one parallel pass. At inference the model is auto-regressive: the encoder runs once, then the decoder runs once per output token, feeding each prediction back in. The paper decodes with beam size 4, length penalty α = 0.6, and a maximum length of input + 50.</p></div>

<div class="recap">
  <div><span><b>Problem:</b> fast training needs parallelism, but generated tokens only become known one at a time.</span></div>
  <div><span><b>Core idea:</b> train on all m positions in one masked, teacher-forced pass; generate left to right with beam search (size 4, α = 0.6).</span></div>
</div>

<p class="start-hint">Next: <a href="../13-why-it-works/index.html">13 · Why the Transformer works →</a> · Previous: <a href="../11-position-wise-ffn/index.html">← 11</a> · <a href="../index.html">All concepts</a></p>

<!-- slide id="s-papers" from="papers" -->
