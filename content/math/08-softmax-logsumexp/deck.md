---
title: Softmax and Log-Sum-Exp
body:
  data-deck: Softmax and log-sum-exp
  data-home: ../index.html
  data-home-label: Math
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'scores z :: any size :: f'
  - 'm = max z :: shift :: c'
  - 'exp(z − m) :: all ≤ 1, no overflow :: a'
  - '÷ Σ :: probabilities :: e'
  caption: 'Online version: update m and the sum as blocks arrive, rescaling the old sum by e^(m_old − m_new).'
example:
  title: 'Worked example: softmax of (1000, 1001, 1002)'
  setup: Naively, e¹⁰⁰⁰ overflows to infinity in FP32 and FP64, and the result is ∞/∞ = NaN (not a number).
  steps:
  - 'Subtract m = 1002: (−2, −1, 0).'
  - 'Exponentiate: (0.1353, 0.3679, 1); sum = 1.5032.'
  - 'Divide: <b>(0.090, 0.245, 0.665)</b>, the same as softmax(0, 1, 2).'
  - 'Online, in two blocks [1000] then [1001, 1002]: after block 1, m = 1000, d = 1. Block 2 raises m to 1002, so d = 1·e⁻² + e⁻¹ + 1 = 1.503: the same sum.'
  result: Shift by the max for safety; rescale the running sum when the max changes to do it in one pass.
traps:
  tricks:
  - 'softmax(z + c) = softmax(z). :: The max-trick is free.'
  - 'log softmax = z − LSE(z). :: Use for losses.'
  - 'Online: d ← d·e^(m − m′) + Σ e^(z − m′). :: The basis of FlashAttention.'
  traps:
  - 'log(softmax(z)). :: Tiny probabilities underflow to 0 and give −∞.'
  - 'Softmax in FP16. :: exp overflows above ≈ 11.09; compute in FP32.'
  - 'Masking with −∞ on a fully masked row. :: Max is −∞ and you get NaN; handle empty rows explicitly.'
papers:
- milakov
- fa1
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Math for LLMs · 08</div>
    <h1>Softmax and log-sum-exp</h1>
    <p class="sub">The function that turns scores into probabilities in every attention head and output layer, why it overflows, and the max-trick and online form that make it safe and fast.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Softmax needs exp of each score. exp overflows FP16 above about 11 and FP32 above about 88.7, and attention logits often exceed those. Computing it also seems to need two passes over the data.</div>
      <div class="c"><b>Core idea</b>Softmax is <b>shift-invariant</b>: subtract the maximum before exponentiating and every exponent is ≤ 0. <b>Log-sum-exp</b> LSE(z) = m + log Σ e^(zᵢ − m) gives stable log-probabilities. The <b>online softmax</b> keeps a running max and a rescaled running sum, so it works block by block in one pass.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## When does softmax break?

Three logits; move the largest one. The naive softmax (exp, then normalise) is computed in a simulated FP16 or FP32; the stable version subtracts the max first.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">largest logit <input type="range" id="xZ" min="0" max="120" step="0.5" value="8"> <output id="xZo"></output></label><div class="seg" id="xSeg"><button data-v="16" class="on">FP16</button><button data-v="32">FP32</button></div></div>
  <div class="grid2" style="margin-top:12px"><div><h4 style="margin:0 0 6px">naive</h4><div id="xN"></div></div><div><h4 style="margin:0 0 6px">stable (subtract max)</h4><div id="xS"></div></div></div>
  <p class="readout" id="xOut"></p>
</div>
<p class="caption">Logits are (z − 2, z − 1, z). exp overflows FP16 above ln 65,504 ≈ 11.09 and FP32 above ≈ 88.72.</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## What goes wrong naively

::: cards grid3
### [d] Overflow
exp of a large logit becomes ∞; ∞/∞ is NaN and poisons the whole step.

### [b] Underflow in logs
log(softmax) of a very unlikely token is log(0) = −∞, making the loss infinite.

### [c] Two passes
The textbook form needs the max and the sum before any output, i.e. extra reads of a long row from memory.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Is the shift allowed?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Why can we subtract max(z) from every logit before the softmax?
- [ ] It is an approximation that is close enough
- [x] The factor e^(−m) appears in numerator and denominator and cancels
- [ ] Because logits are always positive
- [ ] It is not allowed
> <b>B.</b> exp(zᵢ − m) / Σ exp(zⱼ − m) = e^(−m) exp(zᵢ) / (e^(−m) Σ exp(zⱼ)): mathematically identical, numerically safe.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Three stable forms

::: cards grid3
### [a] Stable softmax
exp(z − m) / Σ exp(z − m), with m = max z. All exponents ≤ 0.

### [c] Log-sum-exp
LSE(z) = m + log Σ exp(z − m): the log normaliser, used directly in losses.

### [e] Online softmax
Stream blocks keeping (m, d); when a block raises the max, multiply d by e^(m_old − m_new) (Milakov & Gimelshein, 2018).
:::

<div class="eq">LSE(z) = m + log Σᵢ e^(zᵢ − m),   log softmax(z)ᵢ = zᵢ − LSE(z)</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Online softmax, block by block

Twelve logits read in blocks of three. Step through: the running max m and running sum d update, and d is rescaled whenever m grows.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><button class="btn primary" id="oNext">next block</button><button class="btn" id="oReset">reset</button></div>
  <svg id="oSvg" viewBox="0 0 660 170" style="margin-top:10px" role="img" aria-label="Online softmax"></svg>
  <p class="readout" id="oOut"></p>
</div>

::: deep From online softmax to FlashAttention
FlashAttention applies the same rescaling to the attention output as well as the sum, so it can process keys and values in tiles held in fast on-chip memory without ever writing the full score matrix. See <a href="../../architecture/09-flash-attention/index.html">Architecture deck 09</a>.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it matters in practice

::: cards grid2
### [a] Exactness
The stable and online forms give the same answer as the textbook formula, only without overflow.

### [e] Fewer memory passes
Milakov & Gimelshein measured softmax up to 1.3× faster, and fused softmax + top-k up to 5× faster.

### [b] Enables long context
Tiled attention with online softmax never materialises the n × n score matrix.

### [c] Safe losses
Cross-entropy from logits via LSE stays finite even for probabilities like 10⁻³⁰⁰.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Subtracting the max changes the probabilities slightly."
> It changes nothing mathematically; it only changes the floating-point path.
:::

::: reveal myth
? "Online softmax is an approximation used for speed."
> It is exact; the rescaling exactly corrects for the earlier, smaller max.
:::

::: reveal myth
? "Softmax only appears at the output layer."
> Every attention head applies a softmax to every query's scores.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Above roughly which logit does exp overflow in FP16?
- [ ] 8.3
- [x] 11.09
- [ ] 88.72
- [ ] 709.8
> ln 65,504 ≈ <b>11.09</b>. (88.72 is FP32, 709.8 is FP64.)
:::

::: reveal
? Running state (m = 3, d = 2.5). A new block has max 5. How is d updated?
> d ← 2.5·e^(3 − 5) + Σ e^(z − 5) over the new block; m ← 5.
:::

::: reveal
? Why compute log-softmax as z − LSE(z) rather than log(softmax(z))?
> Very small probabilities underflow to 0 in softmax, giving log 0 = −∞; z − LSE stays finite.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Subtract the max before exponentiating, use log-sum-exp for log-probabilities, and keep a rescaled running max and sum to compute softmax exactly in one pass.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Softmax exponentiates scores and normalises them. Exponentials overflow quickly: above about 11 in FP16 and 89 in FP32. Because softmax does not change when you add a constant to every score, you subtract the maximum first and all exponents become non-positive. Log-sum-exp, the maximum plus the log of the shifted sum, gives stable log-probabilities for the loss. The online softmax processes the scores in blocks, keeping a running maximum and a running sum that is rescaled whenever the maximum grows; it is exact and is what lets FlashAttention work tile by tile.</p></div>
    <div class="recap"><div><span><b>Problem:</b> exp overflows; naive softmax needs two passes.</span></div><div><span><b>Core idea:</b> shift by max; LSE; online (m, d) with rescaling.</span></div><div><span><b>Payoff:</b> stable losses, fused kernels, FlashAttention.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/math/05_stable_softmax.ipynb" target="_blank" rel="noopener">05 · Stable softmax, log-sum-exp and online softmax</a> <span style="color:var(--faint)">· 30 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/math/05_stable_softmax.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../09-optimization-basics/index.html">09 · Optimization basics →</a> · Previous: <a href="../07-information-theory/index.html">← 07</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
