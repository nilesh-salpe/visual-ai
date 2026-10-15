---
title: Mixed Precision in PyTorch
body:
  data-deck: Mixed precision in PyTorch
  data-home: ../index.html
  data-home-label: PyTorch
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'FP32 weights :: master copy :: f'
  - 'autocast forward :: matmuls in BF16/FP16 :: a'
  - 'FP32 reductions :: softmax, sum, loss :: c'
  - 'backward :: same dtypes in reverse :: b'
  - 'scaler (FP16 only) :: scale, unscale, skip, adapt :: d'
  caption: 'Theory: Distributed deck 09 and Math deck 10.'
example:
  title: 'Worked example: what autocast changes (measured)'
  setup: Notebook 06 on CPU with torch.autocast("cpu", dtype=torch.bfloat16); defaults reported by PyTorch 2.14.1.
  steps:
  - 'Inside autocast: a @ b and nn.Linear outputs are <b>bfloat16</b>; a.sum() and F.softmax outputs stay <b>float32</b>; the Linear''s weight is still <b>float32</b>.'
  - 'Adding 0.001 ten thousand times: an FP32 total reaches 10.0004; a BF16 total stalls at <b>0.5</b>, because near 0.5 BF16 values are 2⁻⁸ ≈ 0.004 apart and 0.001
    rounds away.'
  - 'GradScaler defaults: initial scale 65,536, growth ×2 every 2,000 clean steps, backoff ×0.5 on overflow.'
  - In the notebook, an injected inf loss leaves the weights unchanged (step skipped) and halves the scale; two clean steps later it doubles again.
  result: Autocast picks precision per op; FP32 is kept exactly where accumulation and range matter.
traps:
  tricks:
  - 'Autocast only the forward + loss. :: Backward follows automatically.'
  - 'Default autocast dtypes. :: CUDA float16, CPU bfloat16; pass dtype=torch.bfloat16 on GPUs that support it.'
  - 'scaler.unscale_(opt) before clipping. :: Otherwise you clip scaled gradients.'
  traps:
  - 'Calling .half() on the model for training. :: Loses the FP32 master weights.'
  - 'Clipping scaled gradients. :: Unscale first.'
  - 'Autocast around the optimizer step. :: Not needed and can change update precision.'
papers:
- pt_amp
- mixedprec
- bf16
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">PyTorch for LLMs · 06</div>
    <h1>Mixed precision in PyTorch</h1>
    <p class="sub">How torch.autocast decides which operations run in BF16 or FP16, why weights and reductions stay in FP32, and how GradScaler protects FP16 training from overflow and underflow.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Low-precision math is much faster on Tensor Cores, but some operations lose too much precision or overflow in 16 bits. Choosing per operation by hand is impractical.</div>
      <div class="c"><b>Core idea</b>Wrap the forward pass in <code>torch.autocast(device_type, dtype)</code>: matmuls and linear layers run in low precision, while reductions, softmax and losses stay in FP32, and the <b>stored weights stay FP32</b>. For FP16, <code>torch.amp.GradScaler</code> multiplies the loss, <b>skips</b> steps with inf/NaN gradients and adapts the scale; BF16 usually needs no scaler.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Where does a BF16 sum stall?

Repeatedly add a small increment to a running total stored in BF16 versus FP32 (BF16 rounding emulated exactly in your browser).
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">increment 10^ <input type="range" id="bX" min="-5" max="-1" step="0.5" value="-3"> <output id="bXo"></output></label><label class="ctl">additions <input type="range" id="bN" min="2" max="5" step="0.5" value="4"> <output id="bNo"></output></label></div>
  <div id="bBars" style="margin-top:12px"></div>
  <p class="readout" id="bOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why not run everything in 16 bits?

::: cards grid3
### [d] Accumulation
Long sums lose small terms (the stall above).

### [b] Range (FP16)
Values above 65,504 overflow and tiny gradients underflow to 0.

### [c] Weight updates
lr × gradient is often smaller than a BF16 weight's spacing; updates vanish without FP32 masters.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What dtype is the weight?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Inside torch.autocast("cuda", dtype=torch.bfloat16), what dtype is a Linear layer's weight parameter?
- [ ] bfloat16
- [ ] float16
- [x] float32 (unchanged)
- [ ] it depends on the input
> <b>C.</b> Autocast casts inputs to each op on the fly (with a cache); it never changes stored parameters.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Autocast + (for FP16) GradScaler

::: cards grid2
### [a] Low-precision ops
matmul, linear, conv, SDPA run in the autocast dtype.

### [c] FP32 ops
Reductions (sum), softmax, log, losses and norms stay in FP32 for accuracy.

### [b] GradScaler
scale(loss).backward(); step(opt) skips if inf/NaN; update() halves or grows the scale.

### [e] BF16 shortcut
BF16 has FP32's exponent range, so most BF16 training uses autocast without a scaler.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## The FP16 recipe in code

<div class="visual"><pre style="margin:0;font:13px/1.55 'JetBrains Mono',monospace;white-space:pre-wrap">scaler = torch.amp.GradScaler("cuda")          # init_scale 65536, growth 2, backoff 0.5, interval 2000&#10;for x, y in loader:&#10;    opt.zero_grad(set_to_none=True)&#10;    with torch.autocast("cuda", dtype=torch.float16):&#10;        loss = model(x, y)&#10;    scaler.scale(loss).backward()&#10;    scaler.unscale_(opt)                                 # so clipping sees true gradients&#10;    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)&#10;    scaler.step(opt)                                     # skipped if any grad is inf/NaN&#10;    scaler.update()&#10;&#10;# BF16: same loop without the scaler lines.</pre></div>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works

::: cards grid2
### [a] Speed where it counts
Matmuls dominate FLOPs and run at Tensor Core rates in BF16/FP16.

### [e] Accuracy where it matters
Reductions and master weights stay in FP32.

### [b] Automatic
Op lists maintained by PyTorch replace error-prone manual casting.

### [c] Self-tuning scale
GradScaler keeps FP16 gradients in range without manual tuning.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Autocast converts the model to half precision."
> Weights stay FP32; ops cast their inputs as they run.
:::

::: reveal myth
? "You always need GradScaler."
> It is for FP16; BF16's 8-bit exponent avoids most underflow.
:::

::: reveal myth
? "A skipped step means training is broken."
> Occasional skips are how dynamic scaling finds the largest safe scale.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? GradScaler's default initial scale?
- [ ] 1
- [ ] 1,024
- [x] 65,536
- [ ] 2³²
> <b>65,536</b> (2¹⁶).
:::

::: reveal
? Why does autocast keep softmax in FP32?
> Exponentials and normalising sums are sensitive to precision and range; FP32 avoids overflow and rounding errors.
:::

::: reveal
? What happens when GradScaler finds inf in the gradients?
> The optimizer step is skipped and the scale is multiplied by the backoff factor (0.5).
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">torch.autocast runs matmuls in BF16/FP16 but keeps reductions, softmax and the weights in FP32; GradScaler adds loss scaling, step skipping and adaptive scale for FP16.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Mixed precision in PyTorch is mostly one context manager. Inside torch autocast, matrix multiplications and linear layers run in bfloat16 or float16, while sums, softmax, losses and normalisations stay in float32, and the stored weights are never changed. The notebook shows why: a total kept in bfloat16 stops growing at one half when you keep adding a thousandth. For float16, a GradScaler multiplies the loss so small gradients survive, skips any step whose gradients overflow, halves its scale when that happens and doubles it after a run of clean steps. Bfloat16 usually needs no scaler.</p></div>
    <div class="recap"><div><span><b>Problem:</b> speed of 16-bit math without its failures.</span></div><div><span><b>Core idea:</b> autocast per-op dtypes; FP32 weights and reductions.</span></div><div><span><b>FP16:</b> GradScaler: scale, skip, adapt.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/06_mixed_precision.ipynb" target="_blank" rel="noopener">06 · Mixed precision: autocast, BF16 and GradScaler</a> <span style="color:var(--faint)">· 25 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/06_mixed_precision.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../07-performance/index.html">07 · Performance: compile, SDPA, memory →</a> · Previous: <a href="../05-data/index.html">← 05</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
