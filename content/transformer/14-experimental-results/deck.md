---
title: Experimental Results
body:
  data-deck: Experimental results
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
  - 'train :: WMT 2014 EN-DE, EN-FR :: f'
  - 'decode :: beam 4, α = 0.6 :: c'
  - 'score :: BLEU on newstest2014 :: a'
  - 'compare cost :: training FLOPs :: e'
  caption: Better BLEU at a fraction of the training cost of earlier systems.
example:
  title: 'Worked example: reproducing the training-cost column'
  setup: The paper estimates FLOPs = GPUs × sustained single-precision TFLOPS × training time, with 9.5 TFLOPS for a P100.
  steps:
  - 'Base: 8 × 9.5 TFLOPS × 12 h = <b>3.3e+18 FLOPs</b> (Table 2: 3.3 × 10¹⁸).'
  - 'Big: 8 × 9.5 TFLOPS × 3.5 days = <b>2.3e+19 FLOPs</b> (Table 2: 2.3 × 10¹⁹).'
  - 'Big model BLEU: 28.4 on EN-DE and 41.8 on EN-FR (Table 2; the text says 41.0 for EN-FR).'
  - The strongest earlier EN-DE ensembles cost 7.7 × 10¹⁹ (ConvS2S) and 1.8 × 10²⁰ (GNMT + RL) FLOPs and scored 26.4 and 26.3 BLEU, below the big model's 28.4.
  result: 'The headline is a cost-quality frontier shift: higher BLEU at much lower training FLOPs.'
traps:
  tricks:
  - 'FLOPs = GPUs × TFLOPS × time. :: The paper''s own estimate method.'
  - '28.4 / 41.8. :: Big model, EN-DE / EN-FR.'
  - 'Checkpoint averaging. :: Last 5 (base) or 20 (big) checkpoints averaged.'
  traps:
  - '41.0 vs 41.8. :: EN-FR differs between the text and Table 2; cite the table.'
  - 'Comparing ensembles with single models. :: Table 2 mixes both; read the labels.'
  - 'Ignoring parsing. :: The paper also shows English constituency parsing generalization (Table 4).'
papers:
- vaswani
- bytenet
- convs2s
- gnmt
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Attention Is All You Need · 14</div>
    <h1>Experimental results</h1>
    <p class="sub">Translation quality (BLEU (Bilingual Evaluation Understudy, an n-gram overlap score for translation)) against training cost (FLOPs (floating-point operations)) on WMT (Workshop on Machine Translation) 2014, plus training time and a transfer test on English constituency parsing. All figures are from the paper.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>The best translation systems of 2016–17 needed large ensembles and 10<sup>19</sup>–10<sup>21</sup> FLOPs of training to reach state-of-the-art BLEU.</div>
      <div class="c"><b>Core idea</b>The Transformer (big) set a new state of the art on EN-DE (28.4 BLEU) and EN-FR (41.8), at a fraction of the training cost: 3.5 days on 8 P100 GPUs (graphics processing units).</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-prior" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Before: better BLEU cost much more compute

Each dot is a published model from Table 2: translation quality (BLEU on newstest2014) against estimated training cost. The best results came from <b>ensembles</b> at 10<sup>20</sup>–10<sup>21</sup> FLOPs. Turn on the Transformer to compare.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <div class="seg" id="lSeg"><button data-v="de" class="on">EN → DE</button><button data-v="fr">EN → FR</button></div>
    <div class="seg" id="tSeg"><button data-v="0" class="on">Prior work only</button><button data-v="1">+ Transformer</button></div>
  </div>
  <svg id="scSvg" viewBox="0 0 660 340" style="margin-top:10px" role="img" aria-label="BLEU vs training FLOPs"></svg>
  <div class="key"><span><i style="background:var(--faint)"></i>single model</span><span><i style="background:var(--c)"></i>ensemble</span><span><i style="background:var(--e)"></i>Transformer</span></div>
</div>

<div class="cite">Table 2. Only models with both a BLEU score and a FLOPs estimate for the selected pair are plotted (ByteNet has no FLOPs entry; Deep-Att has EN-FR only). The paper lists the Transformer's FLOPs once for both language pairs.</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## The best systems were ensembles, and they were expensive

::: cards grid3
### [d] Ensembles cost more
The best EN-DE result (ConvS2S ensemble, 26.36 BLEU) took 7.7·10¹⁹ training FLOPs; the best EN-FR ensembles took about 10²¹ (Table 2).

### [b] Small gains
On EN-DE, the best single model reached 26.03 (MoE (Mixture of Experts)) and the best ensemble only 26.36.

### [c] Slow to train
Recurrent models can't parallelize across positions within a sentence, so every experiment takes longer (deck 01).
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Predict the result

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? The best previous EN-DE result was 26.36 BLEU (an ensemble, 7.7·10¹⁹ FLOPs). What did a single Transformer (big) achieve?
- [ ] About 1 BLEU worse, but cheaper
- [ ] About the same BLEU
- [x] About 2 BLEU better, with about a third of the training FLOPs
- [ ] 10 BLEU better
> <b>C.</b> 28.4 BLEU (+2.0) with 2.3·10¹⁹ FLOPs, about 0.3× the ConvS2S ensemble's cost. Even the <b>base</b> model (27.3 BLEU, 3.3·10¹⁸ FLOPs) beat every earlier model and ensemble.
:::

<!-- slide id="s-table" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Table 2: higher BLEU, lower training cost

<div class="visual scroll-x">
  <table class="tbl">
    <tr><th>Model</th><th>BLEU EN-DE</th><th>BLEU EN-FR</th><th>FLOPs EN-DE</th><th>FLOPs EN-FR</th></tr>
    <tr><td>ByteNet</td><td>23.75</td><td></td><td></td><td></td></tr>
    <tr><td>Deep-Att + PosUnk</td><td></td><td>39.2</td><td></td><td>1.0·10²⁰</td></tr>
    <tr><td>GNMT (Google's Neural Machine Translation system) + RL (reinforcement learning)</td><td>24.6</td><td>39.92</td><td>2.3·10¹⁹</td><td>1.4·10²⁰</td></tr>
    <tr><td>ConvS2S</td><td>25.16</td><td>40.46</td><td>9.6·10¹⁸</td><td>1.5·10²⁰</td></tr>
    <tr><td>MoE</td><td>26.03</td><td>40.56</td><td>2.0·10¹⁹</td><td>1.2·10²⁰</td></tr>
    <tr><td>Deep-Att + PosUnk Ensemble</td><td></td><td>40.4</td><td></td><td>8.0·10²⁰</td></tr>
    <tr><td>GNMT + RL Ensemble</td><td>26.30</td><td>41.16</td><td>1.8·10²⁰</td><td>1.1·10²¹</td></tr>
    <tr><td>ConvS2S Ensemble</td><td>26.36</td><td>41.29</td><td>7.7·10¹⁹</td><td>1.2·10²¹</td></tr>
    <tr style="background:var(--e-soft)"><td><b>Transformer (base)</b></td><td><b>27.3</b></td><td>38.1</td><td colspan="2" style="text-align:center"><b>3.3·10¹⁸</b></td></tr>
    <tr style="background:var(--e-soft)"><td><b>Transformer (big)</b></td><td><b>28.4</b></td><td><b>41.8</b></td><td colspan="2" style="text-align:center">2.3·10¹⁹</td></tr>
  </table>
</div>

<div class="grid3" style="margin-top:14px">
  <div class="stat"><div class="num" style="color:var(--e)">+2.0</div><div class="lbl">BLEU over the best previous EN-DE result, including ensembles (28.4 vs 26.36)</div></div>
  <div class="stat"><div class="num" style="color:var(--e)">27.3</div><div class="lbl">EN-DE BLEU of the <b>base</b> model, already above every earlier model and ensemble</div></div>
  <div class="stat"><div class="num" style="color:var(--e)">&lt; ¼</div><div class="lbl">the training cost of the previous state of the art on EN-FR (big model, §6.1)</div></div>
</div>

<div class="cite">Metric: BLEU on WMT 2014 newstest2014 (case and tokenization as in the paper). On EN-FR the abstract and Table 2 report 41.8, while §6.1's text says 41.0; this deck uses the table value.</div>

{{glance}}

<!-- slide id="s-cost" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Where the training-cost numbers come from

The paper estimates FLOPs as <b>training time × number of GPUs × sustained single-precision throughput per GPU</b>, using 9.5 TFLOPS (trillion floating-point operations per second) for a P100 (footnote 5). You can reproduce the Table 2 values below.
{: .lede}

<div class="visual">
  <div class="seg" id="cSeg"><button data-v="base" class="on">Base model</button><button data-v="big">Big model</button></div>
  <div class="eq" id="cEq"></div>
  <div class="grid3" style="margin-top:8px">
    <div class="stat"><div class="num" id="cT"></div><div class="lbl">wall-clock time</div></div>
    <div class="stat"><div class="num">8 × P100</div><div class="lbl">one machine (§5.2)</div></div>
    <div class="stat"><div class="num" id="cF" style="color:var(--e)"></div><div class="lbl">estimated training FLOPs</div></div>
  </div>
</div>

<div class="cite">§5.2 and §6.1, footnote 5: "We used values of 2.8, 3.7, 6.0 and 9.5 TFLOPS for K80, K40, M40 and P100, respectively."</div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide raw -->
<section class="slide" id="s-paper" data-chapter="How">
  <div class="inner">
    <span class="qtag b5">5 · How it works</span> <span class="ill" style="color:var(--c);border-color:var(--c)">from the paper · Abstract, §6.1</span>
    <h2>The headline claims</h2>
    <hr>
    <div class="paper"><b>Abstract:</b> 28.4 BLEU on WMT 2014 English-to-German, "improving over the existing best results, including ensembles, by over 2 BLEU", and a new single-model state of the art of 41.8 BLEU on English-to-French "after training for 3.5 days on eight GPUs, a small fraction of the training costs of the best models from the literature."</div>
    <div class="paper"><b>Setup (§5):</b> WMT 2014 EN-DE, ~4.5M sentence pairs with a shared BPE (byte-pair encoding) vocabulary of ~37K; EN-FR, 36M sentences with a 32K word-piece vocabulary. Adam (β₁ = 0.9, β₂ = 0.98, ε = 10⁻⁹) with 4,000 warmup steps, then inverse-square-root decay.</div>
    <div class="paper"><b>Decoding (§6.1):</b> beam size 4, length penalty α = 0.6, checkpoint averaging (last 5 for base, last 20 for big).</div>
  </div>
</section>

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why the results came out this way

::: cards grid2
### [e] Parallel training
All positions are processed in each step, so a big model trains in 3.5 days on one 8-GPU machine (decks 01, 12).

### [a] Short paths
Direct connections make long-range dependencies easier to learn (Table 1), which matters for translation quality.

### [b] Cheap enough to beat ensembles
The base model needs 3.3·10¹⁸ FLOPs (12 hours) and still beats ensembles costing up to 10²¹.

### [c] It generalizes
Without task-specific tuning it also did well on English constituency parsing (next slide).
:::

<!-- slide id="s-parse" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Does it generalize? English constituency parsing (Table 4)

A 4-layer Transformer (d<sub>model</sub> = 1024) trained on the WSJ (Wall Street Journal) portion of the Penn Treebank (~40K sentences), and in a semi-supervised setting (~17M sentences), with little task-specific tuning. Metric: F1 on WSJ section 23.
{: .lede}

<div class="visual">
  <div class="seg" id="pSeg"><button data-v="wsj" class="on">WSJ only</button><button data-v="semi">Semi-supervised / other</button></div>
  <div id="pBars" style="margin-top:14px"></div>
</div>

<div class="takeaway">It beat all previously reported models except the Recurrent Neural Network Grammar, and unlike RNN seq2seq models it outperformed the BerkeleyParser even with only the 40K WSJ sentences (§6.3).</div>

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "28.4 BLEU means 28.4% of the translation is correct."
> BLEU scores n-gram overlap with reference translations on a 0–100 scale. It is a <b>corpus-level similarity score</b>, not a percentage of correct sentences.
:::

::: reveal myth
? "The training FLOPs in Table 2 were measured."
> They are <b>estimates</b>: training time × number of GPUs × an assumed sustained TFLOPS per GPU (9.5 for a P100, footnote 5).
:::

::: reveal myth
? "The Transformer won EN-FR by a large margin."
> On EN-FR the gain is small: 41.8 vs 41.29 for the ConvS2S ensemble. The big win there is <b>cost</b>: under 1/4 of the previous state of the art's training cost (§6.1).
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

<div class="quiz">
  <p class="qq">What EN-DE BLEU did the base model achieve?</p>
  <div class="opts">
  <button>A. 25.8</button>
  <button data-ok>B. 27.3</button>
  <button>C. 28.4</button>
  <button>D. 41.8</button>
  </div>
  <div class="why"><b>27.3</b> on newstest2014 (25.8 is its dev score in Table 3).</div>
</div>

::: quiz
? What hardware did the paper train on?
- [ ] 1 TPU pod
- [x] 8 NVIDIA P100 GPUs on one machine
- [ ] 64 K80 GPUs
- [ ] 16 V100 GPUs
> <b>One machine with 8 P100 GPUs</b> (§5.2).
:::

<div class="quiz ">
  <p class="qq">Why does this guide report 41.8 for EN-FR when §6.1 says 41.0?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">The paper is inconsistent: the abstract and Table 2 say <b>41.8</b>, while the §6.1 text says 41.0. The guide uses the table value and notes the mismatch.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Better and cheaper: 28.4 BLEU EN-DE (+2.0 over all prior ensembles) and 41.8 EN-FR, for 2.3·10¹⁹ FLOPs on 8 P100 GPUs in 3.5 days.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>On WMT 2014, the big Transformer reached 28.4 BLEU English-German, more than 2 BLEU above the best previous results including ensembles, and 41.8 English-French, a new single-model state of the art, after 3.5 days of training on 8 P100 GPUs. The paper estimates its training cost at 2.3·10¹⁹ FLOPs, a fraction of what earlier systems used. The base model reached 27.3 in 12 hours. It also transferred to constituency parsing, with 92.7 F1 in the semi-supervised setting.</p></div>

<div class="recap">
  <div><span><b>Problem:</b> state-of-the-art translation needed large ensembles and 10<sup>20</sup>+ FLOPs of training.</span></div>
  <div><span><b>Result:</b> Transformer (big) 28.4 BLEU EN-DE and 41.8 EN-FR at 2.3·10¹⁹ FLOPs (3.5 days, 8 P100s). Base 27.3 EN-DE in 12 hours. Generalizes to parsing (92.7 F1 semi-supervised).</span></div>
</div>

<p class="start-hint">You've finished the guide. <a href="../index.html">← Back to all concepts</a> · Previous: <a href="../13-why-it-works/index.html">← 13</a></p>

<!-- slide id="s-papers" from="papers" -->
