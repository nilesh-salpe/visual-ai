---
title: Floating-Point Numbers
body:
  data-deck: Floating-point numbers
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
  - 'sign :: 1 bit :: d'
  - 'exponent :: range (powers of 2) :: a'
  - 'mantissa :: precision (digits) :: c'
  - 'rounded value :: nearest representable :: e'
  caption: 'Spacing between neighbours grows with magnitude: relative error stays ≈ 2⁻ᵐ.'
example:
  title: 'Worked example: storing 0.1 and adding 10⁻⁴ to 1'
  setup: Round to nearest in each format.
  steps:
  - 0.1 in FP32 = 0.100000001490…; in BF16 = <b>0.10009765625</b>; in FP16 = <b>0.0999755859375</b>.
  - 'Spacing just above 1: FP32 2⁻²³ ≈ 1.2 × 10⁻⁷, FP16 2⁻¹⁰ ≈ 9.8 × 10⁻⁴, BF16 2⁻⁷ ≈ 7.8 × 10⁻³.'
  - '1 + 10⁻⁴: FP32 gives 1.0001000; FP16 and BF16 both round back to <b>1.0</b>: the update vanishes.'
  - 'Range: FP16 overflows above 65,504; BF16 and FP32 reach ≈ 3.4 × 10³⁸.'
  result: This is why training keeps FP32 master weights and accumulators while doing matmuls in 16 or 8 bits (Distributed deck 09).
traps:
  tricks:
  - 'Relative precision ≈ 2⁻ᵐ. :: m = mantissa bits.'
  - 'BF16 = FP32 with the low 16 bits dropped. :: Same exponent, trivial conversion.'
  - 'Sum small numbers first / in FP32. :: Reduces rounding error.'
  traps:
  - 'Comparing floats with ==. :: Use a tolerance.'
  - 'Assuming addition is associative. :: (a + b) + c ≠ a + (b + c), so parallel reductions differ run to run.'
  - 'Catastrophic cancellation. :: Subtracting nearly equal numbers loses most significant digits.'
papers:
- goldberg
- bf16
- mixedprec
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Math for LLMs · 10</div>
    <h1>Floating-point numbers</h1>
    <p class="sub">How computers store real numbers as sign, exponent and mantissa, what precision and range each LLM format gives, and the rounding effects that bite in training.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Models do trillions of arithmetic operations in formats with 32, 16 or even 8 bits. Every number is rounded, small updates can vanish, and large values can overflow.</div>
      <div class="c"><b>Core idea</b>A float is <b>(−1)ˢ × 1.mantissa × 2^(exponent − bias)</b>. <b>Exponent bits</b> set the range; <b>mantissa bits</b> set the precision (relative spacing 2⁻ᵐ). FP32 has 8 + 23, BF16 has 8 + 7 (same range, less precision), FP16 has 5 + 10 (more precision, much less range).</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## What does a number look like in bits?

Type a value and pick a format. The bits split into sign, exponent and mantissa; the readout shows the value actually stored and the rounding error.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">value <input id="fV" type="text" value="0.1" style="width:120px"></label><div class="seg" id="fSeg"><button data-v="fp32">FP32</button><button data-v="bf16" class="on">BF16</button><button data-v="fp16">FP16</button></div></div>
  <svg id="fSvg" viewBox="0 0 660 120" style="margin-top:10px" role="img" aria-label="Floating-point bit layout"></svg>
  <p class="readout" id="fOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why not exact or fixed-point numbers?

::: cards grid3
### [d] Exact rationals
Unbounded size and far too slow for trillions of operations.

### [b] Fixed point
Integers with a fixed scale cannot cover both 10⁻⁸ gradients and 10⁴ activations.

### [c] Bits cost bandwidth
Every byte is memory, bandwidth and silicon; fewer bits per number means faster training and inference.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Which format keeps the tiny gradient?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? A gradient of 10⁻⁶. Which 16-bit format represents it as a normal number?
- [ ] FP16
- [x] BF16
- [ ] both
- [ ] neither
> <b>B.</b> BF16's 8-bit exponent reaches ≈ 10⁻³⁸. FP16's smallest normal is ≈ 6.1 × 10⁻⁵; 10⁻⁶ survives only as a low-precision subnormal (FP16 subnormals go down to ≈ 6 × 10⁻⁸).
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Sign, exponent, mantissa

::: cards grid3
### [d] Sign
1 bit: positive or negative.

### [a] Exponent
Stored with a bias; picks the power of two, so it sets the range. FP32/BF16: 8 bits. FP16: 5 bits.

### [c] Mantissa
Fraction bits after an implicit leading 1; sets relative precision. FP32: 23, FP16: 10, BF16: 7.
:::

<div class="eq">value = (−1)ˢ × (1 + mantissa / 2ᵐ) × 2^(exponent − bias)</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## The formats used for LLMs

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Format</th><th>Exponent + mantissa bits</th><th>Max</th><th>Smallest normal</th><th>Spacing at 1</th><th>Typical use</th></tr>
  <tr><td>FP32</td><td>8 + 23</td><td>3.4 × 10³⁸</td><td>1.2 × 10⁻³⁸</td><td>1.2 × 10⁻⁷</td><td>master weights, optimizer state, reductions</td></tr>
  <tr><td>BF16</td><td>8 + 7</td><td>3.4 × 10³⁸</td><td>1.2 × 10⁻³⁸</td><td>7.8 × 10⁻³</td><td>training matmuls and activations</td></tr>
  <tr><td>FP16</td><td>5 + 10</td><td>65,504</td><td>6.1 × 10⁻⁵</td><td>9.8 × 10⁻⁴</td><td>inference; training with loss scaling</td></tr>
  <tr><td>FP8 E4M3</td><td>4 + 3</td><td>448</td><td>1.6 × 10⁻²</td><td>0.125</td><td>FP8 matmuls (weights, activations)</td></tr>
  <tr><td>FP8 E5M2</td><td>5 + 2</td><td>57,344</td><td>6.1 × 10⁻⁵</td><td>0.25</td><td>gradients in some FP8 recipes</td></tr>
</table></div>
<p class="caption">Values from the IEEE 754 definitions (FP32, FP16), the BF16 definition (FP32 with a 7-bit mantissa) and the FP8 formats of Micikevicius et al. 2022.</p>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why low precision still works

::: cards grid2
### [a] Neural nets are noise-tolerant
Gradients are already noisy estimates; rounding error of 2⁻⁸ relative is small by comparison.

### [e] Range is what breaks training
BF16 keeps FP32's range, so Kalamkar et al. trained many model types without hyper-parameter changes.

### [b] Keep precision where it accumulates
Sums and weight updates stay in FP32, where small contributions would otherwise vanish.

### [c] Speed
Halving the bits roughly doubles Tensor Core throughput and halves memory traffic.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "BF16 is more precise than FP16."
> BF16 has fewer mantissa bits (7 vs 10), so it is less precise; it has far more range.
:::

::: reveal myth
? "Floating-point addition is associative."
> Rounding after each operation makes the order matter, which is why GPU reductions can differ between runs.
:::

::: reveal myth
? "0.1 is stored exactly."
> 0.1 has no finite binary expansion; every format stores the nearest representable value.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? How many mantissa bits does BF16 have?
- [ ] 23
- [ ] 10
- [x] 7
- [ ] 3
> <b>7</b> (plus the implicit leading 1).
:::

::: reveal
? Why does adding a small update to a large weight in BF16 often do nothing?
> The update is smaller than half the spacing between representable numbers near the weight, so the sum rounds back to the weight.
:::

::: reveal
? Which bits decide range and which decide precision?
> Exponent bits decide range; mantissa bits decide relative precision.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">A float is sign × 1.mantissa × 2^exponent: exponent bits give range, mantissa bits give precision; LLMs compute in BF16/FP8 but keep sums and master weights in FP32.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Computers store real numbers as a sign, an exponent that picks a power of two, and a mantissa that gives the significant digits. Exponent bits set the range and mantissa bits set the relative precision, about two to the minus number of mantissa bits. FP32 has eight exponent and twenty-three mantissa bits; BF16 keeps the eight exponent bits but only seven mantissa bits, so it has FP32's range with far less precision; FP16 has more precision but overflows at 65,504. Rounding means small updates can vanish and sums depend on order, so training keeps accumulators and master weights in FP32.</p></div>
    <div class="recap"><div><span><b>Problem:</b> every number is rounded; range and precision are limited.</span></div><div><span><b>Core idea:</b> exponent = range, mantissa = precision.</span></div><div><span><b>Practice:</b> BF16/FP8 compute, FP32 accumulation.</span></div></div>
    <p class="start-hint">You've finished the series. <a href="../../build-it/index.html">See all Build-it notebooks →</a> · Previous: <a href="../09-optimization-basics/index.html">← 09</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
