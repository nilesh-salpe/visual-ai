---
title: Scaled Dot-Product Attention
body:
  data-deck: Scaled dot-product attention
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
  - 'Q·Kᵀ :: raw scores :: c'
  - '÷ √d_k :: keep variance ≈ 1 :: a'
  - 'mask (optional) :: −∞ for future :: d'
  - 'softmax :: row-wise :: b'
  - '× V :: weighted values :: e'
  caption: 'Equation 1: Attention(Q, K, V) = softmax(QKᵀ / √d_k) V.'
example:
  title: 'Worked example: why divide by √d_k?'
  setup: With d_k = 64 and unit-variance components, a dot product has standard deviation √64 = 8.
  steps:
  - 'Unscaled scores [8, 0, −8] → softmax = <b>[0.9997, 0.0003, 0.0000]</b>: almost one-hot, gradients nearly zero.'
  - 'Scaled by 1/8 → [1, 0, −1] → softmax = <b>[0.665, 0.245, 0.090]</b>: soft, trainable.'
  - The largest weight drops from 0.9997 to 0.665.
  - 'The paper: for large d_k dot products grow large, pushing softmax "into regions where it has extremely small gradients".'
  result: Scaling by 1/√d_k keeps scores at unit scale regardless of head size.
traps:
  tricks:
  - 'Var(q·k) = d_k. :: For independent unit-variance components; hence 1/√d_k.'
  - 'Dot-product = matmul. :: Fast on GPUs, unlike additive attention.'
  - 'Mask before softmax. :: Set disallowed scores to −∞ so they get weight 0.'
  traps:
  - 'Dividing by d_k. :: Over-shrinks scores; the paper uses √d_k.'
  - 'Masking after softmax. :: Rows would no longer sum to 1.'
  - 'Thinking scaling changes expressiveness. :: It only changes the softmax temperature at initialization.'
papers:
- vaswani
- luong
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Attention Is All You Need · 05</div>
    <h1>Scaled dot-product attention</h1>
    <p class="sub"><code>Attention(Q, K, V) = softmax(QKᵀ / √d<sub>k</sub>) V</code>: how the scores are computed, scaled, normalized and used to take weighted sums.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Dot products of d<sub>k</sub>-dimensional vectors grow with d<sub>k</sub>. Large scores push the softmax into a near one-hot regime where its gradients are tiny.</div>
      <div class="c"><b>Core idea</b>Divide the scores by √d<sub>k</sub> so their variance stays near 1 whatever the dimension, then apply softmax and take weighted sums of V, all as matrix multiplications.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Attention needs a compatibility score for every query-key pair, and it must be fast

With n tokens, a single head computes <b>n²</b> query-key scores. The base model runs 8 heads in each of its 18 attention sub-layers (6 encoder + 12 decoder), on every training step. Whatever function produces the scores has to be cheap and has to train well.
{: .lede}

::: cards grid3
### [d] n² scores per head
A 50-token sentence means 2,500 scores per head per layer.

### [b] Two known options
<b>Additive</b> attention (a small feed-forward network per pair) and <b>dot-product</b> attention (q·k) (§3.2.1).

### [a] Must map to GPUs
The fastest operation on a GPU (graphics processing unit) is a large matrix multiply.
:::

<!-- slide id="s-why" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why dot products, and why the scaling?

::: cards grid2
### [a] Dot-product attention
Compatibility = q·k. It's fast and memory-efficient "since it can be implemented using highly optimized matrix multiplication code" (§3.2.1). The paper's version is identical to this except for the 1/√d<sub>k</sub> factor.

### [b] Additive attention
Compatibility is computed by a feed-forward network with one hidden layer. Its theoretical complexity is similar, but it is slower in practice.

### [e] Small d<sub>k</sub>
The two mechanisms perform similarly.

### [d] Large d<sub>k</sub>
Additive attention outperforms <em>unscaled</em> dot-product attention. The paper attributes this to large dot products saturating the softmax, so it scales by 1/√d<sub>k</sub>.
:::

<div class="takeaway">Scaling keeps the fast matrix-multiply form of dot-product attention and avoids its large-d<sub>k</sub> problem.</div>

<!-- slide id="s-prob" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Bigger d<sub>k</sub> → bigger dot products → saturated softmax

If the components of q and k are independent with mean 0 and variance 1, then q·k has <b>variance d<sub>k</sub></b>. With d<sub>k</sub> = 64 the scores spread over roughly ±8, the softmax puts nearly all its weight on one key, and its gradients become very small. Drag d<sub>k</sub>.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">d<sub>k</sub> <input type="range" id="pD" min="0" max="10" step="1" value="6"> <output id="pDo"></output></label>
    <div class="seg" id="pScale"><button data-v="0" class="on">Unscaled q·k</button><button data-v="1">Scaled q·k / √d<sub>k</sub></button></div>
    <button class="btn" id="pResample">Resample q, k</button>
  </div>
  <div class="grid2" style="margin-top:12px">
    <div><h3>Scores for 8 keys</h3><svg id="pScores" viewBox="0 0 320 200" role="img" aria-label="Scores"></svg></div>
    <div><h3>Softmax weights</h3><svg id="pSoft" viewBox="0 0 320 200" role="img" aria-label="Softmax weights"></svg></div>
  </div>
  <div class="grid3">
    <div class="stat"><div class="num" id="pStd"></div><div class="lbl">std of scores (theory: √d<sub>k</sub> unscaled, 1 scaled)</div></div>
    <div class="stat"><div class="num" id="pMax"></div><div class="lbl">largest weight</div></div>
    <div class="stat"><div class="num" id="pGrad"></div><div class="lbl">largest softmax gradient term max pᵢ(1−pᵢ)</div></div>
  </div>
</div>

<div class="cite">§3.2.1 and footnote 4. The paper states this as the reason it <em>suspects</em> unscaled dot products underperform for large d<sub>k</sub>. Random q, k are drawn from N(0, 1).</div>

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Fix the saturation, keep the speed

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

<div class="quiz">
  <p class="qq">Dot products of unit-variance vectors have variance d<sub>k</sub>. What is the simplest fix that keeps the matrix-multiply speed?</p>
  <div class="opts">
  <button>A. Switch to additive attention</button>
  <button>B. Divide the scores by d<sub>k</sub></button>
  <button data-ok>C. Divide the scores by √d<sub>k</sub></button>
  <button>D. Clip the scores to [−1, 1]</button>
  </div>
  <div class="why"><b>C.</b> Dividing by √d<sub>k</sub> brings the variance back to exactly 1, whatever d<sub>k</sub> is. Dividing by d<sub>k</sub> (B) shrinks the variance to 1/d<sub>k</sub>, so the softmax becomes nearly uniform. Additive attention (A) is slower in practice, and clipping (D) throws away information and breaks gradients.</div>
</div>

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Use dot products, and divide them by √d<sub>k</sub>

<div class="eq">Attention(Q, K, V) = softmax( QKᵀ / √d<sub>k</sub> ) V</div>

<div class="grid3" style="margin-top:14px">
  <div class="card a"><h3>Dot product</h3><p>Every query-key score in one matrix multiply, QKᵀ.</p></div>
  <div class="card e"><h3>÷ √d<sub>k</sub></h3><p>Brings score variance back to about 1, so the softmax stays responsive.</p></div>
  <div class="card b"><h3>softmax, then × V</h3><p>Row-wise weights, then a weighted sum of values: a second matrix multiply.</p></div>
</div>

{{glance}}

<!-- slide id="s-steps" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Equation 1, one step at a time

<div class="eq">Attention(Q, K, V) = softmax( Q Kᵀ / √d<sub>k</sub> ) · V</div>

<div class="visual">
  <div class="steps" id="eqSteps"></div>
  <svg id="eqSvg" viewBox="0 0 660 250" style="margin-top:10px" role="img" aria-label="Matrices at each step"></svg>
  <div class="infobox" id="eqInfo"></div>
</div>

<p class="caption">Toy example: n = 4 tokens, d<sub>k</sub> = d<sub>v</sub> = 4, random values with a fixed seed. Every number is computed in the page.</p>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide raw -->
<section class="slide" id="s-paper" data-chapter="How">
  <div class="inner">
    <span class="qtag b5">5 · How it works</span> <span class="ill" style="color:var(--c);border-color:var(--c)">from the paper · §3.2.1, Eq. 1, footnote 4</span>
    <h2>The exact statement</h2>
    <hr>
    <div class="eq">Attention(Q, K, V) = softmax( QKᵀ / √d<sub>k</sub> ) V &nbsp;&nbsp; (1)</div>
    <div class="paper"><b>Inputs:</b> queries and keys of dimension d<sub>k</sub>, values of dimension d<sub>v</sub>. Compute the dot products of the query with all keys, divide each by √d<sub>k</sub>, and apply a softmax to obtain the weights on the values.</div>
    <div class="paper"><b>Footnote 4:</b> if the components of q and k are independent random variables with mean 0 and variance 1, then q·k = Σ<sub>i</sub> q<sub>i</sub>k<sub>i</sub> has mean 0 and variance d<sub>k</sub>.</div>
    <div class="paper"><b>Masking (used in the decoder):</b> illegal connections are masked out by setting their softmax inputs to −∞ (§3.2.3; Figure 2's optional "Mask" step). See deck 09.</div>
  </div>
</section>

<!-- slide id="s-wy" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works

::: cards grid2
### [e] Variance stays at 1
If q and k have independent components with mean 0 and variance 1, q·k has variance d<sub>k</sub> (footnote 4). Dividing by √d<sub>k</sub> brings it back to 1 for any d<sub>k</sub>.

### [a] Softmax stays in its sensitive range
Moderate scores give a soft distribution with useful gradients instead of a one-hot one with "extremely small gradients" (§3.2.1).

### [b] Hardware-friendly
Two matrix multiplies and a softmax: "much faster and more space-efficient in practice" than additive attention.

### [c] Room for masking
Forbidden pairs are handled by writing −∞ into the scores before the softmax (deck 09), with no change to the rest of the computation.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "The √d<sub>k</sub> factor is a learned temperature."
> It is a <b>fixed constant</b> (√64 = 8 in the base model). Nothing about it is learned.
:::

::: reveal myth
? "Scaling changes which key gets the most attention."
> Dividing every score by the same positive number keeps their <b>order</b>. Only the sharpness of the softmax changes.
:::

::: reveal myth
? "The softmax is taken over the whole score matrix."
> It is applied <b>row by row</b>: each query gets its own distribution over the keys.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? In the base model (d<sub>k</sub> = 64), what are the scores divided by?
- [ ] 4
- [x] 8
- [ ] 64
- [ ] 512
> <b>8</b> = √64.
:::

<div class="quiz ">
  <p class="qq">With unit-variance components and d<sub>k</sub> = 64, what is the standard deviation of an unscaled dot product q·k?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">√64 = <b>8</b>. Variance is d<sub>k</sub> = 64 (footnote 4), so scores routinely reach ±8 to ±16, enough to saturate a softmax.</div>
</div>

::: quiz
? For n queries and m keys, what is the shape of softmax(QKᵀ/√d<sub>k</sub>)?
- [ ] n × n
- [x] n × m
- [ ] m × d<sub>v</sub>
- [ ] n × d<sub>k</sub>
> <b>n × m</b>: one row of weights over the m keys for each query. Multiplying by V (m × d<sub>v</sub>) gives an n × d<sub>v</sub> output.
:::

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Score with dot products, divide by √d<sub>k</sub> to keep the variance at 1, softmax each row, and take the weighted sum of V: two matrix multiplies and a softmax.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Scaled dot-product attention computes softmax(QKᵀ/√d<sub>k</sub>)V. Dot products are fast because they are a matrix multiply, but with unit-variance components q·k has variance d<sub>k</sub>, so large d<sub>k</sub> pushes the softmax toward one-hot and its gradients vanish. Dividing by √d<sub>k</sub> restores unit variance. The paper notes that unscaled dot-product attention underperforms additive attention at large d<sub>k</sub>; scaling fixes this while keeping the speed.</p></div>

<div class="recap">
  <div><span><b>Problem:</b> raw dot products have variance d<sub>k</sub>, so the softmax saturates and gradients shrink as d<sub>k</sub> grows.</span></div>
  <div><span><b>Core idea:</b> scores = QKᵀ / √d<sub>k</sub>, then a row-wise softmax gives weights, then weights × V gives outputs. That is two matrix multiplications and a softmax.</span></div>
</div>

<p class="start-hint">Next: <a href="../06-multi-head-attention/index.html">06 · Multi-head attention →</a> · Previous: <a href="../04-queries-keys-values/index.html">← 04</a> · <a href="../index.html">All concepts</a></p>

<!-- slide id="s-papers" from="papers" -->
