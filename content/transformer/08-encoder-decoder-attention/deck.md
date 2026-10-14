---
title: Encoder-Decoder Attention
body:
  data-deck: Encoder-decoder attention
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
  - 'decoder state :: queries :: c'
  - 'encoder output :: keys and values :: b'
  - 'attention :: target → source :: a'
  - 'context per target word :: into the FFN :: e'
  caption: Q from the decoder, K and V from the final encoder layer, in every decoder layer.
example:
  title: 'Worked example: cross-attention shapes and cost'
  setup: Source of 10 tokens, target prefix of 9 tokens, 8 heads of 64.
  steps:
  - 'Queries from the decoder: <b>[9, 64]</b> per head; keys and values from the encoder output: <b>[10, 64]</b>.'
  - 'Weights per head: <b>[9, 10]</b>: each target position distributes attention over the 10 source tokens.'
  - All 6 decoder layers attend to the same encoder output, so the encoder runs once per sentence and its K and V can be computed once.
  - Unlike a single summary vector (seq2seq), every source position stays available to every target step.
  result: Cross-attention replaces the fixed-length bottleneck with a learned, per-word lookup into the source.
traps:
  tricks:
  - 'Q from decoder, K/V from encoder. :: The only place the two stacks connect.'
  - 'Compute encoder K/V once. :: Reused for every generated token.'
  - 'No causal mask here. :: The whole source is known.'
  traps:
  - 'Masking the source. :: Only padding is masked in cross-attention.'
  - 'Thinking alignment is hard-coded. :: It is learned, like Bahdanau attention.'
  - 'Forgetting it''s per layer. :: Every decoder layer has its own cross-attention.'
papers:
- vaswani
- bahdanau
- gnmt
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Attention Is All You Need · 08</div>
    <h1>Encoder-decoder attention</h1>
    <p class="sub">How every target position looks at every source position, connecting the sentence being generated to the sentence being translated.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>While writing each target word, the decoder needs the relevant parts of the source. Compressing the whole source into one fixed-size vector creates a bottleneck.</div>
      <div class="c"><b>Core idea</b>In the decoder's second sub-layer, queries come from the decoder and keys and values come from the encoder output, so each target position attends over all source positions.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Each output word depends on specific input words

::: cards grid3
### [a] Alignment
"Katze" comes from "cat", and "Matte" from "mat". Each target word draws on particular source words.

### [b] Changing focus
The relevant source words change at every step of the output.

### [c] Different word order
Languages order words differently, so the right source word isn't simply "the one at the same position".
:::

<div class="takeaway">While writing each target token, the decoder needs flexible access to the relevant parts of the source sentence.</div>

<!-- slide id="s-prob" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## The decoder has to see the source, and one summary vector is too narrow

A basic encoder-decoder squeezes the whole source sentence into one fixed-size vector c. The longer the sentence, the less room each word gets. Attention-based seq2seq models fixed this by letting the decoder look at <em>all</em> encoder states. The Transformer builds this in as one of its three uses of attention.
{: .lede}

<div class="visual">
  <div class="seg" id="bSeg"><button data-v="fixed" class="on">One context vector</button><button data-v="attn">Attend over all source positions</button></div>
  <label class="ctl" style="margin-top:12px">Source length <input type="range" id="bN" min="3" max="12" step="1" value="6"> <output id="bNo"></output></label>
  <svg id="bSvg" viewBox="0 0 660 220" style="margin-top:8px" role="img" aria-label="Bottleneck vs attention"></svg>
</div>

<div class="cite">§3.2.3: this "mimics the typical encoder-decoder attention mechanisms in sequence-to-sequence models", citing Wu et al. 2016, Bahdanau et al. 2014 and Gehring et al. 2017.</div>

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Who asks, who answers?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? In the attention layer that connects decoder to encoder, where should the queries come from?
- [ ] The encoder output
- [x] The decoder's current states
- [ ] Both, alternating by layer
- [ ] Neither: use fixed alignment rules
> <b>B.</b> The decoder is the one looking for information: "which source words do I need right now?" So queries come from the decoder, and the encoder output supplies the <b>keys</b> (what each source word can be matched on) and <b>values</b> (what it contributes).
:::

<!-- slide id="s-wire" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Q from the decoder; K and V from the encoder output

The encoder runs once and produces a memory of n × 512 vectors. In <b>every</b> one of the 6 decoder layers, the second sub-layer projects its own states into queries and projects that same memory into keys and values.
{: .lede}

<div class="visual"><svg id="wSvg" viewBox="0 0 660 300" role="img" aria-label="Encoder-decoder attention wiring"></svg></div>

<div class="key"><span><i style="background:var(--a)"></i>encoder (source)</span><span><i style="background:var(--c)"></i>decoder (target)</span><span><i style="background:var(--b)"></i>attention</span></div>

{{glance}}

<!-- slide id="s-align" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Each target word draws on the source words it translates <span class="ill">illustrative weights</span>

Click a German target word. Its query is matched against the keys of every English source word, and the resulting weights decide which source values it takes in. Together the rows form a soft alignment.
{: .lede}

<div class="visual">
  <div class="grid2" style="grid-template-columns:1.2fr 1fr;align-items:center">
    <svg id="aSvg" viewBox="0 0 400 220" role="img" aria-label="Alignment arcs"></svg>
    <svg id="hSvg" viewBox="0 0 330 300" role="img" aria-label="Alignment matrix"></svg>
  </div>
</div>

<p class="caption">Example sentence pair and weights are illustrative, not taken from a trained model. Rows = target (queries), columns = source (keys and values). Each row sums to 1.</p>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide raw -->
<section class="slide" id="s-paper" data-chapter="How">
  <div class="inner">
    <span class="qtag b5">5 · How it works</span> <span class="ill" style="color:var(--c);border-color:var(--c)">from the paper · §3.2.3</span>
    <h2>The first of three uses of attention</h2>
    <hr>
    <div class="paper"><b>"In 'encoder-decoder attention' layers,</b> the queries come from the previous decoder layer, and the memory keys and values come from the output of the encoder. This allows every position in the decoder to attend over all positions in the input sequence."</div>
    <div class="visual scroll-x">
      <table class="tbl">
        <tr><th>Attention type</th><th>Queries from</th><th>Keys and values from</th><th>Can see</th></tr>
        <tr><td>Encoder self-attention</td><td>previous encoder layer</td><td>previous encoder layer</td><td>all source positions</td></tr>
        <tr><td><b>Encoder-decoder attention</b></td><td><b>previous decoder sub-layer</b></td><td><b>encoder output</b></td><td><b>all source positions</b></td></tr>
        <tr><td>Masked decoder self-attention</td><td>previous decoder layer</td><td>previous decoder layer</td><td>target positions ≤ current</td></tr>
      </table>
    </div>
  </div>
</section>

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works

::: cards grid2
### [a] No bottleneck
The source is never squeezed into one vector. Every target position can read all n source vectors.

### [b] Fresh focus at every position and layer
Each target position computes its own weights over the source, and each of the 6 decoder layers can look again with refined queries.

### [c] Several alignments at once
It is multi-head attention, so different heads can track different source relationships.

### [e] A proven idea, built in
It "mimics the typical encoder-decoder attention mechanisms" of earlier seq2seq models (§3.2.3), now as one of three uniform attention uses.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Encoder-decoder attention is masked like decoder self-attention."
> It is <b>not</b> masked: every decoder position may attend to <b>all</b> source positions. The source is fully known.
:::

::: reveal myth
? "Each decoder layer attends to the matching encoder layer (layer 3 to layer 3)."
> All decoder layers attend to the <b>final</b> encoder output (§3.2.3).
:::

::: reveal myth
? "The attention weights form a hard word-to-word alignment."
> They are <b>soft</b>: a probability distribution over all source positions, and each head has its own.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Which sub-layer of a decoder layer is encoder-decoder attention?
- [ ] First
- [x] Second
- [ ] Third
- [ ] It sits outside the decoder layers
> <b>Second</b>: after masked self-attention and before the FFN (feed-forward network).
:::

<div class="quiz ">
  <p class="qq">For m target tokens and n source tokens, what is the shape of one head's attention-weight matrix?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why"><b>m × n</b>: one row per target query, one column per source key.</div>
</div>

<div class="quiz ">
  <p class="qq">During generation, does the encoder run again for every new target token?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why"><b>No.</b> The source is fixed, so the encoder runs once and its output (the memory) is reused by every decoder pass (deck 12).</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Queries from the decoder, keys and values from the encoder output: every target position can look at the whole source, in every decoder layer.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>In encoder-decoder attention, the decoder's states provide the queries, and the final encoder output provides the keys and values. Each target position therefore computes a soft alignment over all source positions, in every one of the 6 decoder layers, with multiple heads. It replaces the single fixed context vector of early seq2seq models and is not masked, because the whole source is known.</p></div>

<div class="recap">
  <div><span><b>Problem:</b> the decoder needs the relevant source words at every step, and a single context vector is a bottleneck.</span></div>
  <div><span><b>Core idea:</b> Q = decoder states and K, V = encoder memory, in every decoder layer, so each target position attends over the whole source.</span></div>
</div>

<p class="start-hint">Next: <a href="../09-masked-self-attention/index.html">09 · Masked self-attention →</a> · Previous: <a href="../07-positional-encoding/index.html">← 07</a> · <a href="../index.html">All concepts</a></p>

<!-- slide id="s-papers" from="papers" -->
