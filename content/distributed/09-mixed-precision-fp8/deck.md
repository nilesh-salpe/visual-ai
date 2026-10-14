---
title: Mixed Precision and FP8 Training
body:
  data-deck: Mixed precision and FP8 training
  data-home: ../index.html
  data-home-label: Distributed
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'FP32 master weights :: optimizer updates here :: f'
  - 'cast to BF16 / FP8 :: with scales :: c'
  - 'forward + backward :: low-precision matmuls :: a'
  - 'FP32 accumulation :: gradients and reductions :: b'
  - 'unscale + update :: skip on overflow (FP16) :: e'
  loop: '4 -> 0 :: every step'
  caption: Low-precision math, high-precision bookkeeping.
example:
  title: 'Worked example: what each format can hold'
  setup: Largest and smallest normal values (subnormals extend the small end a little).
  steps:
  - 'FP32: max ≈ 3.4 × 10³⁸, smallest normal ≈ 1.2 × 10⁻³⁸, 23 mantissa bits.'
  - 'BF16: same exponent range as FP32, only 7 mantissa bits (≈ 2–3 decimal digits).'
  - 'FP16: max <b>65,504</b>, smallest normal ≈ 6.1 × 10⁻⁵ (subnormals down to ≈ 6 × 10⁻⁸), 10 mantissa bits. A gradient of 10⁻⁸ becomes 0.'
  - 'FP8 E4M3: max <b>448</b>; E5M2: max <b>57,344</b>. With so little range, one scale per tensor is not enough, hence per-tile scaling.'
  result: FP16 needs loss scaling to protect tiny gradients; BF16 trades precision for FP32's range; FP8 needs scales per small block.
traps:
  tricks:
  - 'Master weights in FP32. :: Small updates vanish if added directly to BF16 weights.'
  - 'Dynamic loss scaling. :: Halve on overflow and skip the step; double after N good steps.'
  - 'Accumulate in FP32. :: Llama 3 accumulates and reduce-scatters gradients in FP32.'
  traps:
  - 'FP16 without loss scaling. :: Small gradients flush to zero and training stalls.'
  - 'BF16 weight updates. :: lr × gradient is often below BF16''s resolution at the weight''s magnitude.'
  - 'Per-tensor FP8 scales. :: One outlier forces a scale that crushes the rest; use fine-grained blocks.'
papers:
- mixedprec
- fp8
- dsv3
- llama3
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Distributed Training · 09</div>
    <h1>Mixed precision and FP8 training</h1>
    <p class="sub">Training in 16-bit and 8-bit formats without losing accuracy: FP32 master weights, loss scaling for FP16, why BF16 usually needs none, and the fine-grained scaling FP8 training needs.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Low-precision math is 2–4× faster and halves memory, but small gradients underflow to zero in FP16 and FP8 has very few bits of precision and range.</div>
      <div class="c"><b>Core idea</b>Keep an <b>FP32 master copy</b> of the weights and accumulate in FP32. For FP16, <b>scale the loss</b> so gradients stay representable. BF16 has FP32's range, so it usually needs no scaling. FP8 needs <b>per-block scales</b> (DeepSeek-V3: 1×128 tiles for activations, 128×128 blocks for weights).</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Will this gradient survive?

Pick a gradient magnitude and a loss scale. The number line shows each format's representable range (log scale); a red marker means the value underflows to 0 or overflows to infinity.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">gradient = 10^ <input type="range" id="gE" min="-12" max="6" step="0.5" value="-8"> <output id="gEo"></output></label><label class="ctl">loss scale = 2^ <input type="range" id="gS" min="0" max="24" step="1" value="0"> <output id="gSo"></output></label></div>
  <svg id="gSvg" viewBox="0 0 660 220" style="margin-top:10px" role="img" aria-label="Number format ranges"></svg>
  <p class="readout" id="gOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## What goes wrong in low precision

::: cards grid3
### [d] Underflow
FP16's smallest subnormal is about 6 × 10⁻⁸; many gradients are smaller and become exactly zero.

### [b] Lost updates
Adding a tiny update to a large weight in 16-bit rounds it away; the weight never changes.

### [c] Outliers
With 8 bits, one large value sets the scale for a whole tensor and pushes small values to zero.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Why keep FP32 weights?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? A BF16 weight of 1.0 receives an update of 10⁻⁴. What happens if you add it directly in BF16?
- [ ] It becomes 1.0001
- [x] It stays 1.0: the update is below BF16's resolution near 1
- [ ] It overflows
- [ ] It becomes 0
> <b>B.</b> BF16 has 7 mantissa bits, so values near 1 are spaced 2⁻⁷ ≈ 0.0078 apart; 1 + 10⁻⁴ rounds back to 1. Keeping an FP32 master copy accumulates small updates correctly.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## The mixed-precision recipe

::: cards grid2
### [a] FP32 master weights
The optimizer updates an FP32 copy; a low-precision copy is used for compute (Micikevicius et al., 2018).

### [b] Loss scaling (FP16)
Multiply the loss by S before backward, divide gradients by S before the update; adjust S dynamically.

### [e] BF16 by default
Same range as FP32, so no loss scaling in most LLM training; FP32 accumulation for reductions.

### [c] FP8 with fine-grained scales
DeepSeek-V3: activations scaled per 1×128 tile (per token per 128 channels), weights per 128×128 block, with increased-precision accumulation.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Dynamic loss scaling, step by step

::: cards grid4
### [a] 1 · scale
Multiply the loss by S (e.g. 2¹⁵) before backward.

### [c] 2 · check
If any gradient is inf or NaN, skip the step and halve S.

### [b] 3 · unscale
Otherwise divide gradients by S in FP32 and update the master weights.

### [e] 4 · grow
After N clean steps, double S to keep using the available range.
:::

::: deep What notebook 06 shows
On a toy problem with tiny features, FP16 gradients without scaling mostly flush to zero and training stalls at about a third of the starting loss; with dynamic scaling, training matches FP32. Casting a realistic spread of gradient values to FP16 keeps 37% of them non-zero without scaling and 100% with a 2¹⁵ scale or with BF16.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why low precision is worth the trouble

::: cards grid2
### [a] Speed
Tensor Cores run BF16 at twice FP32-TF32 rates and FP8 at twice BF16 (H100: 989 vs 1,979 TFLOP/s dense).

### [e] Memory and bandwidth
Half the bytes for activations and communication; Micikevicius et al. report nearly 2× less memory.

### [b] Accuracy holds
With master weights, FP32 accumulation and scaling, low-precision training matches FP32; DeepSeek-V3 trained in FP8 at 671B scale.

### [c] Stability tools
FP32 reductions (Llama 3), skipping overflow steps, and fine-grained scales keep training stable.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "BF16 is more accurate than FP16."
> BF16 has more range but less precision (7 vs 10 mantissa bits); it is preferred because range problems are harder to fix than precision.
:::

::: reveal myth
? "Mixed precision means everything is 16-bit."
> Master weights, optimizer states and many reductions stay FP32.
:::

::: reveal myth
? "FP8 training is just FP8 casting."
> It needs fine-grained scaling, higher-precision accumulation and careful choice of which ops stay in BF16.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Largest finite FP16 value?
- [ ] 448
- [ ] 57,344
- [x] 65,504
- [ ] 3.4 × 10³⁸
> <b>65,504</b>.
:::

::: reveal
? Why does BF16 training usually not need loss scaling?
> BF16 has the same 8-bit exponent as FP32, so small gradients don't underflow.
:::

::: reveal
? What scaling granularity did DeepSeek-V3 use for FP8?
> 1×128 tiles for activations (per token per 128 channels) and 128×128 blocks for weights.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Mixed precision computes in BF16/FP8 but keeps FP32 master weights and accumulations; FP16 needs loss scaling, FP8 needs fine-grained scales.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Low-precision math is faster and halves memory and communication, but it loses range and precision. Mixed precision training keeps an FP32 master copy of the weights and accumulates gradients in FP32, while matmuls run in 16 or 8 bits. FP16's narrow range makes small gradients underflow, so the loss is scaled up before backward and the gradients scaled down before the update, with dynamic scaling that halves the scale and skips the step on overflow. BF16 has FP32's exponent range, so it usually needs no scaling. FP8 has so few bits that DeepSeek-V3 scales activations per 1 by 128 tile and weights per 128 by 128 block.</p></div>
    <div class="recap"><div><span><b>Problem:</b> underflow, lost updates and outliers in low precision.</span></div><div><span><b>Core idea:</b> FP32 master weights + accumulation; loss scaling (FP16); fine-grained FP8 scales.</span></div><div><span><b>Default:</b> BF16 compute, FP32 bookkeeping.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/distributed/06_mixed_precision.ipynb" target="_blank" rel="noopener">06 · Mixed precision: FP16, BF16 and loss scaling</a> <span style="color:var(--faint)">· 40 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/distributed/06_mixed_precision.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../10-putting-it-together/index.html">10 · Putting it together: 4D layouts →</a> · Previous: <a href="../08-activation-memory/index.html">← 08</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
