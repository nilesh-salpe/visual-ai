---
title: 'Long Context I: Stretching RoPE'
body:
  data-deck: 'Long context I: stretching RoPE'
  data-home: ../index.html
  data-home-label: Architecture
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'trained at L :: angles seen: m·θᵢ, m < L :: f'
  - 'target s·L :: pick factor s :: c'
  - 'remap θ :: PI / NTK-aware / YaRN :: a'
  - 'short fine-tune :: hundreds of steps :: b'
  - 'serve s·L :: angles stay in range :: e'
  caption: Or train long directly with a larger RoPE base, as Llama 3 did.
example:
  title: 'Worked example: extending 4K to 32K (s = 8)'
  setup: d = 128, base 10,000, trained length L = 4,096.
  steps:
  - 'PI: every θ ÷ 8. Neighbouring tokens differ by only 1/8 rad in pair 0 (was 1 rad).'
  - 'NTK-aware: new base = 10,000 × 8<sup>128/126</sup> = <b>82,685</b>; pair 0 unchanged, pair 63 slowed by exactly 8.'
  - 'YaRN: pairs with fewer than 1 turn in 4,096 tokens get θ/8; more than 32 turns are left alone; a ramp in between.'
  - 'YaRN logit temperature: √(1/t) = 0.1·ln 8 + 1 = <b>1.208</b>.'
  result: All three keep slow pairs inside the trained angle range; they differ in how much local resolution they keep and how much fine-tuning they need.
traps:
  tricks:
  - 'Find the at-risk pairs. :: Pairs with wavelength 2π/θᵢ > L never completed a turn in training.'
  - 'NTK base: b·s^(d/(d−2)). :: Keeps the fastest pair, slows the slowest by s.'
  - 'YaRN defaults for Llama: α = 1, β = 32. :: Plus temperature 0.1·ln s + 1.'
  traps:
  - 'Skipping fine-tuning. :: PI and YaRN both fine-tune; extrapolation without it fails.'
  - 'Trusting the advertised window. :: Check retrieval and long-document quality at the length you need.'
  - 'Mismatched rope_scaling at inference. :: Serving must apply the same scaling as fine-tuning.'
papers:
- pi
- yarn
- llama3
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">The Modern LLM · 07</div>
    <h1>Long context I: stretching RoPE</h1>
    <p class="sub">Why a model trained on 4K tokens falls apart at 32K, and how Position Interpolation, NTK-aware (NTK = neural tangent kernel) scaling, YaRN (Yet another rotary-position-embedding extension method) and Llama 3's long-context training fix it.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>A RoPE model trained at length L sees angles m·θᵢ only for m < L. Beyond L, the slow pairs reach angles the model has never seen, and attention scores blow up.</div>
      <div class="c"><b>Core idea</b>Remap the rotation frequencies so long positions land on <b>angles seen in training</b>. PI (Position Interpolation) slows every pair by s. NTK-aware raises the base. YaRN slows only the slow pairs and adds a temperature. Then fine-tune briefly, or train long from the start.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Fast pairs have seen every angle; slow pairs haven't

Each RoPE pair turns at its own speed. During training at L = 4,096 (d = 128, base 10,000), a fast pair goes round the circle hundreds of times, so every angle is familiar. A slow pair covers only part of the circle. Pick a pair and an extension factor: green is the arc seen in training, red is new territory at s·L.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">Pair i <input type="range" id="eI" min="0" max="63" step="1" value="50"> <output id="eIo"></output></label>
    <div class="seg" id="eS"><button data-v="2">2×</button><button data-v="4">4×</button><button data-v="8" class="on">8× (32K)</button></div>
  </div>
  <svg id="eSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Trained vs extended angle range"></svg>
  <p class="readout" id="eOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why the obvious options fail

::: cards grid3
### [d] Just run longer (extrapolate)
Unseen angles in the slow pairs produce what PI calls "catastrophically high attention scores". Perplexity shoots up as soon as you pass L.

### [b] Train long from the start
Attention costs grow with sequence length, and most pretraining documents are short anyway. Paying for 128K context on every step is wasteful.

### [c] Squeeze naively
Dividing every position by s keeps angles in range, but neighbouring tokens become s× closer in the fast pairs. Local order gets blurry, which costs short-context quality unless you fine-tune.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What does Position Interpolation do?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? A LLaMA model trained at 2,048 tokens should handle 8,192. What does Position Interpolation (Chen et al. 2023) change?
- [ ] Adds new position embeddings for 2,048–8,192
- [x] Uses position m/4 instead of m, then fine-tunes briefly
- [ ] Drops RoPE beyond 2,048
- [ ] Trains from scratch at 8,192
> <b>B.</b> PI "linearly down-scales the input position indices to match the original context window size". Every angle stays inside the trained range. About 1,000 fine-tuning steps were enough to reach 32,768 tokens on LLaMA 7B–65B, and the authors bound interpolation's error at about 600× smaller than extrapolation's.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Three ways to remap frequencies

::: cards grid3
### [a] PI: slow everything by s
θᵢ → θᵢ / s for every pair. Simple and safe, but it compresses local resolution by s in the fast pairs.

### [b] NTK-aware: change the base
base → base · s<sup>d/(d−2)</sup>. The fastest pair is unchanged, the slowest is slowed by exactly s, and those in between are slowed smoothly. It keeps local order sharp, but most slow pairs still slightly overshoot.

### [e] YaRN: by parts, plus temperature
Count each pair's turns within L: r = L/λᵢ. If r &lt; α (=1): interpolate fully (θ/s). If r &gt; β (=32): leave alone. Blend linearly in between. Scale logits by √(1/t) = 0.1·ln s + 1.
:::

<div class="deep"><h4>Why YaRN adds a temperature</h4><p>Stretching the context spreads attention over many more tokens, so the softmax gets flatter (higher entropy). YaRN scales q and k so the logits are multiplied by (0.1·ln s + 1)²; at s = 8, √(1/t) ≈ 1.208. The coefficient was fit empirically on LLaMA models. YaRN reports needing about <b>10× fewer tokens and 2.5× fewer training steps</b> than previous methods: <b>400 steps</b>, about 0.1% of the original pretraining data, and it was the first method to extend Llama 2's effective context to 128K.</p></div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Slow-down per pair, for each method

For each of the 64 pairs (d = 128, L = 4,096), how much each method slows that pair (θ ÷ θ′). Pairs to the right are slower. The shaded region marks pairs whose wavelength is longer than L: they never complete a turn in training, so they are the ones that must be slowed by s.
{: .lede}

<div class="visual">
  <div class="seg" id="sS"><button data-v="4">s = 4</button><button data-v="8" class="on">s = 8</button><button data-v="32">s = 32</button></div>
  <svg id="sSvg" viewBox="0 0 660 260" style="margin-top:10px" role="img" aria-label="Slow-down factor by pair"></svg>
  <div class="legend"><span><i style="background:var(--faint)"></i>no scaling</span><span><i style="background:var(--d)"></i>PI</span><span><i style="background:var(--b)"></i>NTK-aware</span><span><i style="background:var(--a)"></i>YaRN (α = 1, β = 32)</span></div>
  <p class="readout" id="sOut"></p>
</div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Or train long directly: the Llama 3 recipe

::: cards grid2
### [a] A larger RoPE base from the start
Llama 3 sets the RoPE base to <b>500,000</b> (Llama 2: 10,000) "to better support longer contexts". Every pair except the first rotates more slowly, so more of the spectrum stays distinguishable at long range.

### [e] Grow the context in stages
Pretrain at 8K, then extend in <b>six stages</b> up to 128K using about <b>800B tokens</b>. Each stage continues until short-context performance has fully recovered and needle-in-a-haystack retrieval is solved perfectly at that length.
:::

<div class="visual scroll-x" style="margin-top:12px"><table class="tbl">
  <tr><th>Method</th><th>What changes</th><th>Training cost reported</th><th>Reach reported</th></tr>
  <tr><td>Extrapolation</td><td>nothing</td><td>none</td><td>breaks just past L</td></tr>
  <tr><td>PI (2023)</td><td>positions ÷ s</td><td>~1,000 steps</td><td>32,768 (LLaMA 7B–65B)</td></tr>
  <tr><td>NTK-aware (2023)</td><td>RoPE base × s<sup>d/(d−2)</sup></td><td>none needed: "much better" than PI on non-fine-tuned models</td><td>but worse than PI after fine-tuning, because some pairs go slightly out of bounds (YaRN §3.1)</td></tr>
  <tr><td>YaRN (2023)</td><td>per-pair ramp + temperature</td><td>400 steps, ~0.1% of pretraining data</td><td>128K (Llama 2)</td></tr>
  <tr><td>Llama 3 (2024)</td><td>base 500K + 6-stage continued pretraining</td><td>~800B tokens</td><td>128K</td></tr>
</table></div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why remapping works

::: cards grid2
### [a] Attention only needs familiar angles
The model learned what each angle in each pair means. Keep every (pair, angle) combination inside the trained range and attention behaves normally, even at positions it never saw.

### [e] Fast pairs don't need help
A pair that turned hundreds of times during training has seen every angle, so its behaviour at long range is not new. Leaving it alone (NTK, YaRN) keeps fine local resolution.

### [b] Slow pairs do
Pairs with wavelength longer than L only ever covered part of the circle. They are where unseen angles come from, so they get the full s× slow-down.

### [d] Fine-tuning closes the gap
Any remapping shifts the distribution a little. A short fine-tune at the new length lets the model adapt; the methods differ mostly in how short that can be.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "A 128K context window means the model uses all 128K tokens well."
> The window is what it accepts. How well it retrieves and reasons over distant tokens has to be measured (needle-in-a-haystack, long-document tasks). Llama 3 used both as stage criteria.
:::

::: reveal myth
? "Position Interpolation needs no training."
> PI keeps angles in range but compresses local resolution. The paper fine-tunes for about 1,000 steps.
:::

::: reveal myth
? "Raising the RoPE base is all you need."
> A bigger base changes the frequencies the model was trained on. It has to be trained (or fine-tuned) at long lengths with that base, which is what Llama 3's staged continued pretraining does.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? In YaRN, a pair that completes more than β = 32 turns within the original context is…
- [ ] interpolated by s
- [x] left unchanged
- [ ] removed
- [ ] given a larger temperature
> <b>Left unchanged</b>: it has already seen every angle.
:::

<div class="quiz ">
  <p class="qq">Why does plain extrapolation fail, while PI works after a short fine-tune?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Beyond L, slow RoPE pairs reach angles never seen in training and attention scores blow up. PI divides positions by s so every angle stays inside the trained range; the fine-tune adapts the model to the compressed local spacing.</div>
</div>

<div class="quiz ">
  <p class="qq">What did Llama 3 do instead of a post-hoc scaling trick?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">A larger RoPE base (500,000) plus six stages of continued pretraining from 8K to 128K tokens (about 800B tokens), moving on only once short-context quality recovered and needle-in-a-haystack was solved.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Long context means keeping every RoPE angle inside the range seen in training: slow the slow pairs (PI, NTK, YaRN) or train long with a bigger base (Llama 3).</div>

<div class="explain"><b>Say it in 30 seconds</b><p>A RoPE model trained at length L has seen each pair's angles only up to L times theta. Fast pairs turn many times, so every angle is familiar, but slow pairs cover only part of the circle, and past L they produce unseen angles and exploding attention scores. Position Interpolation divides positions by the extension factor so every angle stays in range, then fine-tunes for about a thousand steps. NTK-aware scaling raises the base so fast pairs stay sharp. YaRN interpolates only the slow pairs, adds an attention temperature, and needs about 400 steps. Llama 3 instead uses a base of 500,000 and six stages of continued pretraining up to 128K.</p></div>

<div class="recap"><div><span><b>Problem:</b> slow RoPE pairs hit unseen angles past the trained length.</span></div><div><span><b>Remap:</b> PI (all ÷ s), NTK-aware (bigger base), YaRN (slow pairs only + temperature).</span></div><div><span><b>Train long:</b> Llama 3: base 500K, 6 stages, 8K → 128K, ~800B tokens.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/architecture/06_rope_scaling.ipynb" target="_blank" rel="noopener">06 · Extending context: PI, NTK-aware and YaRN</a> <span style="color:var(--faint)">· 45 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/architecture/06_rope_scaling.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../08-sliding-window/index.html">08 · Long context II: sliding window and ALiBi →</a> · Previous: <a href="../06-decoder-only/index.html">← 06</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Chen et al. 2023, "Extending Context Window of Large Language Models via Positional Interpolation"; Peng et al. 2023, "YaRN" (eq. 13–22, §4); Su et al. 2021 (RoFormer); Llama Team 2024 (Llama 3 §3.2 RoPE base; §3.4.2 long-context pretraining).</p>

<!-- slide id="s-papers" from="papers" -->
