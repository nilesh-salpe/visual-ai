---
title: Quantization
body:
  data-deck: Quantization
  data-home: ../index.html
  data-home-label: Inference
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'BF16 weights :: and activations :: f'
  - 'pick granularity :: tensor / channel / group :: c'
  - 'scales + codes :: INT8, INT4, FP8 :: a'
  - 'matmul :: dequantize or low-bit kernel :: b'
  - 'fewer bytes :: faster decode, more KV room :: e'
  caption: Quantization trades a little accuracy for fewer bytes to store and to read.
example:
  title: 'Worked example: memory and decode speed for a 70B model'
  setup: '70B parameters; group-wise INT4 uses one FP16 scale per 128 weights. Decode at batch 1 reads every weight once per token (H100: 3.35 TB/s).'
  steps:
  - 'BF16: 70B × 2 bytes = <b>140 GB</b>; INT8: <b>70 GB</b>; INT4: <b>35 GB</b>.'
  - 'INT4 scale overhead: 16 bits / 128 weights = 0.125 bits per weight → +1.1 GB, so 4.125 effective bits.'
  - 'Time to read the weights once: BF16 42 ms, INT8 21 ms, INT4 11 ms (bandwidth only, as if on one GPU).'
  - Prefill is compute-bound, so weight-only INT4 helps it far less unless the kernel computes in low precision.
  result: Weight-only INT4 cuts the per-token weight read about 3.9× vs BF16. That speeds memory-bound decode and frees memory for KV cache.
traps:
  tricks:
  - 'Effective bits = bits + scale_bits / group_size. :: INT4 with FP16 scales per 128 → 4.125 bits.'
  - 'Weight-only quantization speeds decode. :: Decode is bandwidth-bound; fewer bytes per weight = faster steps.'
  - 'Handle outliers. :: Per-channel scales, SmoothQuant''s migration (α = 0.5 default), or keep outlier dimensions in 16-bit (LLM.int8()).'
  traps:
  - 'Per-tensor activation scales. :: A few outlier channels blow up the scale and crush everything else to zero.'
  - 'Forgetting the scales. :: Group scales add real memory; group size trades accuracy for overhead.'
  - 'Expecting INT4 compute speedups everywhere. :: Without low-bit kernels, weights are dequantized and the matmul runs in 16-bit.'
  - 'Treating KV-cache and weight quantization as the same. :: KV is quantized at runtime per token; errors accumulate differently.'
papers:
- int8
- smoothquant
- gptq
- awq
- fp8
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">LLM Inference &amp; Serving · 07</div>
    <h1>Quantization for inference</h1>
    <p class="sub">Fewer bits per weight, activation and KV (key-value) entry: INT8 (8-bit integer) and INT4 (4-bit integer) scales, the activation-outlier problem and SmoothQuant's fix, weight-only methods (GPTQ, AWQ (Activation-aware Weight Quantization)), and FP8 (8-bit floating point).</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Decode speed and capacity are limited by bytes: weights and KV cache read every step. 16-bit numbers are expensive to move.</div>
      <div class="c"><b>Core idea</b>Store numbers in 8, 4 or fewer bits with <b>scales</b>, chosen per tensor, per channel or per group, and handle <b>outliers</b> so accuracy survives.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Bytes, not FLOPs, set decode speed

At small batch, every decode step streams the weights (and the KV cache) from HBM (high-bandwidth memory). Halve the bytes and you roughly halve that time, and twice as much fits in memory.
{: .lede}

<div class="visual"><div id="p1Bars"></div></div>

<p class="caption">Weight bytes for a 70B-parameter model at different precisions.</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Naive rounding fails on LLM activations

::: cards grid3
### [d] One scale for everything
A per-tensor scale must cover the largest value. Everything else gets only a few effective levels.

### [b] Activation outliers
A few activation channels are far larger than the rest, so per-tensor INT8 on activations loses the small values (the problem SmoothQuant targets).

### [c] Very low bits
Naive 3–4-bit rounding of weights loses accuracy without smarter error handling.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Deal with the outlier channel

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? A few activation channels have huge values, which breaks per-tensor INT8. Which fix keeps the matmul result mathematically the same?
- [ ] Clip the outliers
- [x] Divide each activation channel by a factor and multiply the matching weight row by the same factor
- [ ] Drop the outlier channels
- [ ] Use a per-tensor scale with more care
> <b>B is SmoothQuant.</b> X·W = (X·diag(s)⁻¹)·(diag(s)·W), so dividing activation channel j by s<sub>j</sub> and multiplying weight row j by s<sub>j</sub> moves the difficulty into the weights, which are easier to quantize, with no change to the result.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Scales, granularity, and where the bits go

<div class="eq">q = clip(round(x / s), −qmax, qmax), &nbsp; x̂ = q · s, &nbsp; s = max|x| / qmax</div>

<div class="grid2" style="margin-top:12px">
  <div class="card a"><h3>Granularity</h3><p>Per tensor → per channel → per group: smaller groups mean tighter ranges and less error, at the cost of storing more scales.</p></div>
  <div class="card b"><h3>W8A8 (SmoothQuant)</h3><p>INT8 weights and activations via smoothing: up to <b>1.56×</b> speed and <b>2×</b> less memory with negligible accuracy loss.</p></div>
  <div class="card c"><h3>Weight-only, 3–4 bits</h3><p><b>GPTQ</b>: second-order one-shot quantization; a 175B model in ~4 GPU-hours (GPU = graphics processing unit); 3.25× (A100) and 4.5× (A6000) over FP16 (16-bit floating point). <b>AWQ</b>: protect the ~1% salient weights found from activations; &gt;3× over HF (Hugging Face) FP16.</p></div>
  <div class="card e"><h3>FP8</h3><p>E4M3 and E5M2 floating point, with per-tensor or per-block scales. It matched 16-bit training quality in Micikevicius et al. (2022).</p></div>
</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Rounding on a number line <span class="ill">random values</span>

<div class="visual">
  <div class="controls" style="margin-top:0">
    <div class="seg" id="qBits"><button data-v="8">INT8</button><button data-v="4" class="on">INT4</button></div>
    <div class="seg" id="qGran"><button data-v="tensor" class="on">per-tensor scale</button><button data-v="group">per-group (8) scales</button></div>
    <div class="seg" id="qOut"><button data-v="0" class="on">no outlier</button><button data-v="1">add an outlier</button></div>
  </div>
  <svg id="qSvg" viewBox="0 0 660 200" style="margin-top:10px" role="img" aria-label="Quantization number line"></svg>
  <p class="readout" id="qRes"></p>
</div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## SmoothQuant on live data

<p class="lede">Activations with two outlier channels (×40), as LLMs (large language models) show. The smoothing factor is <b>s<sub>j</sub> = max|X<sub>j</sub>|<sup>α</sup> / max|W<sub>j</sub>|<sup>1−α</sup></b> (paper eq. 4). α = 0.5 is the paper's default, and 0.75 was used for GLM-130B.</p>

<div class="visual">
  <label class="ctl">migration strength α <input type="range" id="smA" min="0" max="1" step="0.05" value="0.5"> <output id="smAo"></output></label>
  <div class="grid2" style="margin-top:10px">
    <div><h3>Per-channel max |X| (first 32 channels)</h3><svg id="smX" viewBox="0 0 320 120" role="img" aria-label="Activation channel ranges"></svg></div>
    <div><h3>W8A8 matmul error</h3><div id="smBars"></div></div>
  </div>
</div>

<p class="caption">Same construction as Build-it notebook 10 (64 × 128 activations, 128 × 96 weights). Errors are computed live in your browser.</p>

<!-- slide id="s-how3" chapter="How" tag="5 · How it works" tagclass="b5" -->
## FP8: two formats

<div class="visual scroll-x"><table class="tbl">
  <tr><th></th><th>E4M3</th><th>E5M2</th></tr>
  <tr><td>Exponent / mantissa bits</td><td>4 / 3</td><td>5 / 2</td></tr>
  <tr><td>Exponent bias</td><td>7</td><td>15</td></tr>
  <tr><td>Max normal</td><td><b>448</b></td><td><b>57,344</b></td></tr>
  <tr><td>Infinities</td><td>none (range extended instead)</td><td>IEEE-style</td></tr>
  <tr><td>Character</td><td>more precision</td><td>more range</td></tr>
</table></div>

<div class="cite">Micikevicius et al., "FP8 Formats for Deep Learning" (2022), Table 1. Build-it notebook 11 enumerates all 127 / 124 finite non-negative values.</div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works

::: cards grid2
### [e] Fewer bytes, faster decode
Decode is memory-bound, so moving fewer bytes per step speeds it up directly and frees memory for more KV.

### [a] Finer scales, smaller ranges
Error is about half a step, and the step is range / levels, so finer granularity means smaller error.

### [b] Outliers moved, not removed
SmoothQuant's transform is exactly equivalent and balances activation and weight ranges.

### [c] Error-aware rounding
GPTQ compensates rounding errors using second-order information, and AWQ protects activation-salient weights.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Quantization always costs a lot of accuracy."
> With good scales and outlier handling, INT8 (SmoothQuant) and 3–4-bit weight-only (GPTQ, AWQ) report small or negligible losses on large models.
:::

::: reveal myth
? "Weight-only INT4 speeds up everything equally."
> It reduces <b>weight bytes</b>, which helps memory-bound decode the most. Compute-bound prefill gains less.
:::

::: reveal myth
? "Per-tensor scales are fine for activations."
> LLM activations have <b>outlier channels</b>, so per-tensor activation INT8 needs SmoothQuant-style smoothing or finer scales.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? What is the maximum normal value of FP8 E4M3?
- [ ] 127
- [ ] 240
- [x] 448
- [ ] 57,344
> <b>448</b> (E5M2: 57,344).
:::

<div class="quiz ">
  <p class="qq">Why is SmoothQuant's transform "free" at inference?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">X·W = (X·diag(s)⁻¹)(diag(s)·W). The weight scaling is folded in <b>offline</b> and the activation division can be fused into the previous layer, so the result is unchanged and nothing is added at runtime.</div>
</div>

<div class="quiz">
  <p class="qq">What fraction of weights does AWQ find to be salient?</p>
  <div class="opts">
  <button>A. 0.01%</button>
  <button data-ok>B. About 1%</button>
  <button>C. About 50%</button>
  <button>D. All</button>
  </div>
  <div class="why">"Protecting only <b>1%</b> salient weights can greatly reduce quantization error".</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Quantization cuts the bytes that bound decode. Scales at the right granularity, outlier handling (SmoothQuant), error-aware weight methods (GPTQ, AWQ) and FP8 keep accuracy while moving 2–4× fewer bytes.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Decode is memory-bound, so storing weights, activations and KV in fewer bits speeds it up and frees memory. Quantization maps values to integers with a scale. Finer scales (per channel, per group) cut error, but LLM activations have outlier channels that break per-tensor INT8. SmoothQuant moves that difficulty into the weights with an exact rescaling, reporting up to 1.56× speed and 2× less memory. GPTQ and AWQ push weights to 3–4 bits. FP8 (E4M3, max 448; E5M2, max 57,344) uses floating point with scales.</p></div>

<div class="recap"><div><span><b>Problem:</b> 16-bit bytes bound decode; naive low-bit rounding breaks on outliers.</span></div><div><span><b>Core idea:</b> scales at the right granularity, outlier migration, error-aware weight quantization, FP8.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/10_quantization.ipynb" target="_blank" rel="noopener">10 · INT8/INT4 quantization and SmoothQuant</a> <span style="color:var(--faint)">· 45 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/inference/10_quantization.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/11_fp8_emulation.ipynb" target="_blank" rel="noopener">11 · FP8 (E4M3 / E5M2) emulation</a> <span style="color:var(--faint)">· 30 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/inference/11_fp8_emulation.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../08-parallelism/index.html">08 · Parallelism for inference →</a> · Previous: <a href="../06-speculative-decoding/index.html">← 06</a> · <a href="../index.html">All decks</a></p>

<!-- slide id="s-papers" from="papers" -->
