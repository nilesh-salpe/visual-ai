---
title: Multi-Head Attention
body:
  data-deck: Multi-head attention
  data-home: ../index.html
  data-home-label: Transformer
styles:
- ../../shared/deck.css
- ../../shared/learn.css
- ../tx.css
css: |-
  #mhSvg [data-h] { cursor: pointer; }
scripts:
- ../../shared/deck.js
- ../tx.js
glance:
  steps:
  - 'x :: [n, 512] :: f'
  - '8 heads :: each projects to 64 dims :: c'
  - 'attention per head :: in parallel :: a'
  - 'concat :: [n, 512] :: b'
  - 'W_O :: mix heads :: e'
  caption: Same parameter budget as one 512-dim head, split into 8 subspaces.
example:
  title: 'Worked example: the head-count experiment (Table 3)'
  setup: 'Base model on newstest2013 (dev): perplexity 4.92, BLEU 25.8, with h = 8 heads of 64 dims.'
  steps:
  - 'h = 1, d_k = 512: BLEU <b>24.9</b> (−0.9).'
  - 'h = 4, d_k = 128: BLEU <b>25.5</b>.'
  - 'h = 16, d_k = 32: BLEU <b>25.8</b> (same as base).'
  - 'h = 32, d_k = 16: BLEU <b>25.4</b>: too many tiny heads also hurts.'
  result: Several heads beat one big head at the same cost, but there is a sweet spot; later work found many trained heads can be pruned (Michel et al.).
traps:
  tricks:
  - 'Same cost for any h. :: h × d_k = d_model, so parameters and FLOPs stay constant.'
  - 'Heads specialize. :: Some track syntax, some coreference (paper Figures 3–5).'
  - 'Concat then project. :: W_O mixes information across heads.'
  traps:
  - 'More heads always better. :: Table 3: 32 heads did worse than 8 or 16.'
  - 'Each head sees a slice of the input. :: Each head sees the full input, projected to a smaller subspace.'
  - 'Heads are independent forever. :: W_O and later layers combine them.'
papers:
- vaswani
- michel
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Attention Is All You Need · 06</div>
    <h1>Multi-head attention</h1>
    <p class="sub">Eight attention functions run in parallel, each in its own 64-dimensional subspace, and their outputs are concatenated and projected.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>One attention distribution per token has to average over every kind of relationship (who "it" refers to, what describes it, its neighbours), which blurs them together.</div>
      <div class="c"><b>Core idea</b>Project Q, K and V h = 8 times into smaller subspaces (d<sub>k</sub> = 64), attend in each separately, then concatenate and apply W<sup>O</sup>. The total cost is about the same as one full-width head.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## A word relates to other words in several ways at once

To understand "it" in <i>"The animal didn't cross the street because it was tired"</i>, a model needs several different relationships at the same time.
{: .lede}

::: cards grid2
### [a] Reference
What does "it" refer to? → "animal"

### [b] Predicate
What is said about it? → "was tired"

### [c] Local syntax
Neighbouring words such as "because" and "was".

### [e] Long-distance structure
In the paper's Figure 3, "making" links to the distant "more difficult".
:::

<!-- slide id="s-prob" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## One head has to blend different relationships into one average <span class="ill">illustrative weights</span>

To understand "<b>it</b>", a model might want three things at once: what it <span style="color:var(--a);font-weight:600">refers to</span> ("animal"), what is <span style="color:var(--b);font-weight:600">said about it</span> ("tired") and its <span style="color:var(--c);font-weight:600">local syntax</span> ("was"). A single softmax spreads one budget of 100% across all of them.
{: .lede}

<div class="visual">
  <div class="seg" id="pSeg"><button data-v="1" class="on">1 head (averaged)</button><button data-v="3">3 heads (separate)</button></div>
  <svg id="pSvg" viewBox="0 0 660 240" style="margin-top:8px" role="img" aria-label="Single vs multiple heads"></svg>
</div>

<div class="takeaway">The paper puts it this way: "With a single attention head, averaging inhibits this" (§3.2.2). §2 also names the cost of attention's averaging: "reduced effective resolution".</div>

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Several relationships, same budget

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? How would you capture several relationships per token without multiplying the cost?
- [ ] Run h full-width (512-dim) attention layers side by side
- [x] Split the 512 dimensions into h smaller subspaces and run attention in each
- [ ] Use one head with a larger d<sub>k</sub>
- [ ] Add more layers
> <b>B is multi-head attention.</b> 8 heads × 64 dims cost about as much as one 512-dim head, but give 8 separate attention distributions. Option A would cost about 8× more. A single larger head (C) still has only one distribution, and more layers (D) don't give one layer several views.
:::

<!-- slide id="s-arch" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## h = 8 heads in parallel, then concatenate and project

Each head i has its own projections W<sub>i</sub><sup>Q</sup>, W<sub>i</sub><sup>K</sup>, W<sub>i</sub><sup>V</sup> (512 → 64) and runs scaled dot-product attention on its own. The eight 64-dim outputs are concatenated back to 512 and mixed by W<sup>O</sup>. Click a head to see the kind of pattern a head can learn.
{: .lede}

<div class="visual">
  <svg id="mhSvg" viewBox="0 0 660 270" role="img" aria-label="Multi-head attention diagram"></svg>
  <svg id="headSvg" viewBox="0 0 660 150" style="margin-top:4px" role="img" aria-label="Pattern of the selected head"></svg>
  <p class="caption" id="headCap"></p>
</div>

<div class="cite">Head patterns are illustrative. The paper reports that individual heads "clearly learn to perform different tasks", with behaviour related to the syntactic and semantic structure of sentences (§4, Figures 3–5).</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Shapes through one multi-head attention block (base model)

<div class="visual scroll-x">
  <table class="tbl">
    <tr><th>Step</th><th>Operation</th><th>Shape</th></tr>
    <tr><td>1</td><td>Input X (or Q, K, V sources)</td><td>n × 512</td></tr>
    <tr><td>2</td><td>Per head i: Q<sub>i</sub> = XW<sub>i</sub><sup>Q</sup>, K<sub>i</sub> = XW<sub>i</sub><sup>K</sup>, V<sub>i</sub> = XW<sub>i</sub><sup>V</sup></td><td>n × 64, for each of 8 heads</td></tr>
    <tr><td>3</td><td>Scores Q<sub>i</sub>K<sub>i</sub>ᵀ / √64, softmax by row</td><td>n × n, for each of 8 heads</td></tr>
    <tr><td>4</td><td>head<sub>i</sub> = weights × V<sub>i</sub></td><td>n × 64, for each of 8 heads</td></tr>
    <tr><td>5</td><td>Concat(head<sub>1</sub>, …, head<sub>8</sub>)</td><td>n × 512</td></tr>
    <tr><td>6</td><td>× W<sup>O</sup> (512 × 512)</td><td>n × 512</td></tr>
  </table>
</div>

<div class="paper"><b>Parameter check:</b> Q, K, V projections = 3 × 8 × (512 × 64) = 3 × 512² ; W<sup>O</sup> = 512². Total 4 × 512², the same as a single head with full 512-dim projections. That is why the cost is "similar to that of single-head attention with full dimensionality" (§3.2.2).</div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide raw -->
<section class="slide" id="s-paper" data-chapter="How">
  <div class="inner">
    <span class="qtag b5">5 · How it works</span> <span class="ill" style="color:var(--c);border-color:var(--c)">from the paper · §3.2.2</span>
    <h2>The equations</h2>
    <hr>
    <div class="eq">MultiHead(Q, K, V) = Concat(head<sub>1</sub>, …, head<sub>h</sub>) W<sup>O</sup></div>
    <div class="eq">head<sub>i</sub> = Attention(Q W<sub>i</sub><sup>Q</sup>, K W<sub>i</sub><sup>K</sup>, V W<sub>i</sub><sup>V</sup>)</div>
    <div class="paper"><b>Shapes:</b> W<sub>i</sub><sup>Q</sup> ∈ ℝ<sup>d<sub>model</sub>×d<sub>k</sub></sup>, W<sub>i</sub><sup>K</sup> ∈ ℝ<sup>d<sub>model</sub>×d<sub>k</sub></sup>, W<sub>i</sub><sup>V</sup> ∈ ℝ<sup>d<sub>model</sub>×d<sub>v</sub></sup>, W<sup>O</sup> ∈ ℝ<sup>hd<sub>v</sub>×d<sub>model</sub></sup>. With h = 8 and d<sub>k</sub> = d<sub>v</sub> = d<sub>model</sub>/h = 64.</div>
    <div class="paper"><b>Why:</b> "Multi-head attention allows the model to jointly attend to information from different representation subspaces at different positions." Because each head is smaller, the total computational cost is similar to single-head attention with full dimensionality.</div>
  </div>
</section>

<!-- slide id="s-heads" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Same budget, split differently: the paper's head-count experiment

Table 3, row (A) changes h while keeping h · d<sub>k</sub> = 512, so <b>computation stays constant</b>. Pick h to see the per-head width and the measured result on newstest2013 (the EN-DE development set).
{: .lede}

<div class="visual">
  <div class="seg" id="hSeg"><button data-v="1">h = 1</button><button data-v="4">h = 4</button><button data-v="8" class="on">h = 8 (base)</button><button data-v="16">h = 16</button><button data-v="32">h = 32</button></div>
  <svg id="splitSvg" viewBox="0 0 660 70" style="margin-top:12px" role="img" aria-label="512 dims split into heads"></svg>
  <div class="grid2" style="margin-top:10px">
    <div><h3>BLEU (dev), higher is better</h3><div id="bleuBars"></div></div>
    <div><h3>Perplexity (dev), lower is better</h3><div id="pplBars"></div></div>
  </div>
</div>

<div class="takeaway">Single-head attention is 0.9 BLEU worse than the best setting, and quality also drops with too many heads (h = 32, d<sub>k</sub> = 16). The paper's §6.2 says both.</div>

<div class="cite">Table 3 rows (A) and base. Perplexities are per word-piece and are not comparable with per-word perplexities.</div>

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "8 heads cost 8× as much as one head."
> Each head works in 64 dims rather than 512, so total computation is <b>about the same</b> as one full-width head (§3.2.2).
:::

::: reveal myth
? "Each head is assigned a specific job, such as coreference."
> Nothing is assigned. Heads <b>learn</b> their behaviour from data. The paper observes that many end up doing structure-related tasks (Figures 4–5).
:::

::: reveal myth
? "The heads' outputs are averaged together."
> They are <b>concatenated</b> and then mixed by a learned projection W<sup>O</sup>.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? In the base model, what is each head's d<sub>k</sub>?
- [ ] 8
- [ ] 32
- [x] 64
- [ ] 512
> <b>64</b> = d<sub>model</sub> / h = 512 / 8.
:::

<div class="quiz">
  <p class="qq">Table 3 (A): how much worse was single-head attention than the best setting?</p>
  <div class="opts">
  <button>A. 0.1 BLEU</button>
  <button data-ok>B. 0.9 BLEU</button>
  <button>C. 3 BLEU</button>
  <button>D. No difference</button>
  </div>
  <div class="why"><b>0.9 BLEU</b> (24.9 vs 25.8 on the dev set).</div>
</div>

<div class="quiz ">
  <p class="qq">Why might 32 heads (d<sub>k</sub> = 16) do worse than 8?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Each head becomes too narrow to compute good compatibilities. Row (B) shows smaller d<sub>k</sub> hurts, and §6.2 notes "quality also drops off with too many heads".</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Split 512 dimensions into 8 heads of 64, let each head attend in its own subspace, then concatenate and mix with W<sup>O</sup>: several relationships for the price of one.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>One attention head gives a single weighted average per token, which blurs different relationships together. Multi-head attention projects Q, K and V h = 8 times into 64-dimensional subspaces, runs scaled dot-product attention in each in parallel, concatenates the results and applies W<sup>O</sup>. Because each head is smaller, the total cost is similar to one full-width head. In Table 3, one head was 0.9 BLEU worse than eight, and 32 heads also did worse.</p></div>

<div class="recap">
  <div><span><b>Problem:</b> one softmax per token averages different relationships together and loses resolution.</span></div>
  <div><span><b>Core idea:</b> 8 heads × 64 dims attend in parallel, in different subspaces, then Concat → W<sup>O</sup>. Same cost, and measurably better than 1 head (Table 3A).</span></div>
</div>

<p class="start-hint">Next: <a href="../07-positional-encoding/index.html">07 · Positional encoding →</a> · Previous: <a href="../05-scaled-dot-product-attention/index.html">← 05</a> · <a href="../index.html">All concepts</a></p>

<!-- slide id="s-papers" from="papers" -->
