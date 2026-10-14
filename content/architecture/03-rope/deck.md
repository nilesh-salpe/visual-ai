---
title: RoPE
body:
  data-deck: RoPE
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
  - 'q, k vectors :: after W_q and W_k :: f'
  - 'split into pairs :: d/2 two-dim pairs :: c'
  - 'rotate pair i :: by m · θᵢ :: a'
  - 'q′ · k′ :: depends only on m − n :: e'
  caption: Values are not rotated, and nothing is added to the residual stream.
example:
  title: 'Worked example: rotation speeds for d = 128'
  setup: Head dimension 128 (64 pairs). Wavelength = tokens per full turn = 2π / θᵢ.
  steps:
  - 'Pair 0: θ₀ = 1 rad/token → wavelength <b>6.3 tokens</b>.'
  - 'Pair 32: θ = 10000<sup>−0.5</sup> = 0.0100 → wavelength <b>628 tokens</b>.'
  - 'Pair 63 (base 10,000): wavelength <b>54,410 tokens</b>; at position 4,096 it has turned only 0.08 of a circle.'
  - With Llama 3's base 500,000, pair 63's wavelength becomes <b>2,559,196 tokens</b>.
  result: Fast pairs separate nearby tokens, slow pairs far ones. Slow pairs that never complete a turn in training are why long-context extension needs care (deck
    07).
traps:
  tricks:
  - 'θᵢ = base^(−2i/d); wavelength = 2π·base^(2i/d). :: Pair 0 always turns once every ~6.3 tokens.'
  - 'Rotate keys once. :: A key''s rotation depends only on its own position, so it is cached already rotated.'
  - 'Shift invariance. :: Adding the same offset to all positions leaves every score unchanged.'
  traps:
  - 'Rotating values. :: Only q and k are rotated.'
  - 'Mixing pair layouts. :: Interleaved pairs (paper) vs "rotate half" (Llama code) are permutations; weights trained with one don''t work with the other.'
  - 'Assuming RoPE extrapolates. :: Angles beyond the trained range are new to the model; quality drops past the training length.'
papers:
- roformer
- llama
- llama3
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">The Modern LLM · 03</div>
    <h1>Rotary position embeddings (RoPE)</h1>
    <p class="sub">How rotating queries and keys by an angle proportional to position makes attention depend only on the distance between tokens, with no position vector added anywhere.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Attention is order-blind. The 2017 fix adds a position vector to each token embedding, which mixes position into content and lets attention see relative distance only indirectly.</div>
      <div class="c"><b>Core idea</b>Split q and k into 2-D pairs and <b>rotate</b> pair i by angle <b>m·θᵢ</b> at position m, with θᵢ = 10000<sup>−2i/d</sup>. The dot product of two rotated vectors depends only on the angle <b>difference</b>, so q·k depends on <b>m − n</b>.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Attention can't see order by itself

Self-attention scores every pair of tokens with q·k. Shuffle the input tokens and each token gets exactly the same scores, just permuted. "dog bites man" and "man bites dog" would look identical. Position has to be injected somehow.
{: .lede}

::: cards grid2
### [b] The 2017 answer: add a vector
x₀ = embedding(token) + PE(position), once, at the input. Every later layer has to untangle "what" from "where" inside the same vector. Recap: <a href="../../transformer/07-positional-encoding/index.html">Transformer deck 07</a>.

### [a] What attention actually needs
Mostly <b>relative</b> information: "the word two to my left", "the subject of this clause". A score that depends on m − n directly would be ideal, and it should keep working when the whole sequence shifts.
:::

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Limits of added position vectors

<div class="grid3">
  <div class="card d"><h3>Absolute, not relative</h3><p>With x + PE, the score (x_m + p_m)·W·(x_n + p_n) has content-position cross terms. Relative distance appears only through how the network learns to combine them.</p></div>
  <div class="card b"><h3>Added once, diluted later</h3><p>The position signal enters at layer 0 and has to survive every residual update to be useful in layer 40.</p></div>
  <div class="card c"><h3>Learned tables stop at L</h3><p>GPT-2-style learned position embeddings have exactly 1,024 rows. Position 1,025 has no vector at all.</p></div>
</div>

<div class="deep"><h4>Relative position attempts before RoPE</h4><p>Relative-position schemes (Shaw et al. 2018; T5's bucketed biases) add learned terms that depend on m − n to the attention scores. They work, but they need extra tables or bias terms, and RoFormer argues they are awkward to combine with linear-attention variants. RoPE (rotary position embedding) gets relative behaviour from a fixed rotation with <b>no learned parameters</b>.</p></div>

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Rotate both, compare

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Rotate query q by angle mθ and key k by angle nθ in the same plane. Their dot product depends on…
- [ ] m only
- [ ] n only
- [x] m − n only (plus the vectors themselves)
- [ ] m + n
> <b>C.</b> A dot product depends only on the vectors' lengths and the angle between them. Rotating q by mθ and k by nθ changes that angle by (m − n)θ. Shift both positions by the same amount and nothing changes. RoFormer: "the inner product encodes position information only in the relative form."
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## The RoPE recipe

<div class="grid3">
  <div class="card a"><h3>1. Pair up dimensions</h3><p>Split a d-dimensional q (or k) into d/2 pairs: (x₀,x₁), (x₂,x₃), … Treat each pair as a point in a 2-D plane, or as a complex number x₂ᵢ + i·x₂ᵢ₊₁.</p></div>
  <div class="card b"><h3>2. Give each pair a speed</h3><p>θᵢ = base<sup>−2i/d</sup>, base = 10,000 (RoFormer, LLaMA) or 500,000 (Llama 3). Pair 0 turns about once every 6 tokens; the last pair takes tens of thousands of tokens per turn.</p></div>
  <div class="card e"><h3>3. Rotate by position</h3><p>At position m, rotate pair i by m·θᵢ. Do this to q and k in <b>every attention layer</b>, after the projections. Values are not rotated, and nothing is added to the residual stream.</p></div>
</div>

<div class="eq">q′ₘ · k′ₙ = Re[ Σᵢ qᵢ · conj(kᵢ) · e<sup>i(m−n)θᵢ</sup> ]   (pairs written as complex numbers)</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## One pair, two tokens: only the gap matters

The left dial shows one pair of the query at position m; the right shows one pair of the key at position n. The score contribution is their dot product. Drag m and n, then use "shift both" to slide the pair along the sequence without changing the gap.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">Query position m <input type="range" id="rM" min="0" max="60" step="1" value="12"> <output id="rMo"></output></label>
    <label class="ctl">Key position n <input type="range" id="rN" min="0" max="60" step="1" value="9"> <output id="rNo"></output></label>
    <div class="seg" id="rPair"><button data-v="0" class="on">pair 0 (fast)</button><button data-v="2">pair 2</button><button data-v="5">pair 5 (slow)</button></div>
    <button class="btn" id="rShift">shift both +10</button>
  </div>
  <svg id="rSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Rotated query and key"></svg>
  <p class="readout" id="rOut"></p>
</div>

<p class="caption">d = 16 here (8 pairs), base 10,000, so θ₀ = 1 rad/token, θ₂ = 0.1, θ₅ ≈ 0.0032. Real heads use d = 128 (64 pairs).</p>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Many speeds: the frequency spectrum and long-term decay

Each pair rotates at its own speed. Fast pairs separate nearby positions; slow pairs separate far-apart ones. For q = k (all ones) the total score drifts down as the distance grows. RoFormer calls this <b>long-term decay</b>: distant tokens interact more weakly by default.
{: .lede}

<div class="visual">
  <div class="seg" id="bSeg"><button data-v="10000" class="on">base 10,000 (Llama 2)</button><button data-v="500000">base 500,000 (Llama 3)</button></div>
  <svg id="dSvg" viewBox="0 0 660 240" style="margin-top:10px" role="img" aria-label="Score vs distance"></svg>
  <p class="readout" id="dOut"></p>
</div>

<div class="deep"><h4>Wavelengths for d = 128, base 10,000</h4><p>Tokens per full turn of pair i is 2π/θᵢ: pair 0 ≈ <b>6</b>, pair 16 ≈ <b>63</b>, pair 32 ≈ <b>628</b>, pair 48 ≈ <b>6,283</b>, pair 63 ≈ <b>54,410</b> (computed in notebook 02). Pairs whose wavelength exceeds the training length never complete a turn during training. That fact is the key to long-context extension in deck 07.</p></div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why RoPE won

::: cards grid2
### [a] Relative by construction
The score depends on m − n, proven in one line with complex numbers. The model doesn't have to learn to undo absolute positions.

### [e] Zero parameters, nothing added to the stream
A fixed rotation, applied inside attention, in every layer. The residual stream carries content only, and every layer gets fresh position information.

### [b] Plays well with the KV cache
A key's rotation depends only on its own position, so it is rotated once when written to the cache and never touched again. (Relative-bias schemes recompute per pair.)

### [c] Adopted everywhere
GPT-NeoX/GPT-J, PaLM ("better performance on long sequences"), LLaMA, Mistral and most open models since. Its main weakness, behaviour beyond the trained length, has its own family of fixes (deck 07).
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "RoPE adds a position vector to the token embeddings."
> Nothing is added. RoPE <b>multiplies</b> (rotates) q and k inside each attention layer. The residual stream never sees a position vector.
:::

::: reveal myth
? "RoPE is applied to the values too."
> Only <b>queries and keys</b> are rotated, because only their dot product needs position. Values carry content to the output unchanged.
:::

::: reveal myth
? "With RoPE a model works at any length."
> The maths extends to any position, but the model never saw the large angles of slow pairs beyond its training length, so quality collapses without scaling or long-context training (deck 07).
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? For head dimension d = 128 and base 10,000, what is θ for pair i = 0?
- [ ] 10,000
- [x] 1 radian per token
- [ ] 1/128
- [ ] 2π
> <b>B.</b> θ₀ = 10000<sup>0</sup> = 1 rad/token, about one full turn every 6.3 tokens. The fastest pair.
:::

<div class="quiz ">
  <p class="qq">Why does shifting every position by the same amount leave all RoPE attention scores unchanged?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Each score depends on the angle between rotated q and k, which is (m − n)θᵢ for each pair. Adding the same shift to m and n leaves m − n unchanged.</div>
</div>

<div class="quiz ">
  <p class="qq">Llama 3 raised the RoPE base from 10,000 to 500,000. What does that do to the rotation speeds?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Every θᵢ = base<sup>−2i/d</sup> gets smaller except pair 0, so pairs rotate more slowly and wavelengths stretch. More pairs stay distinguishable over long distances, which supports longer contexts.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">RoPE rotates each 2-D slice of q and k by position × frequency, so attention scores depend only on the distance between tokens.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Attention is order-blind, so position has to be injected. The 2017 Transformer added a position vector at the input. RoPE instead splits each query and key into 2-D pairs and rotates pair i by the position times a frequency theta-i, which ranges from about one turn every six tokens down to one turn every fifty thousand. A dot product depends only on the angle between the two vectors, so the score depends only on m minus n: relative position for free, with no parameters, nothing added to the residual stream, and keys that are rotated once when cached. The slow pairs are why extending context needs care.</p></div>

<div class="recap"><div><span><b>Problem:</b> attention is permutation-invariant; added position vectors are absolute and diluted.</span></div><div><span><b>Core idea:</b> rotate q and k pairs by m·θᵢ; q·k depends on m − n.</span></div><div><span><b>Spectrum:</b> θᵢ = base^(−2i/d); fast pairs for local order, slow pairs for long range; base 10K → 500K in Llama 3.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/architecture/02_rope.ipynb" target="_blank" rel="noopener">02 · Rotary position embeddings (RoPE)</a> <span style="color:var(--faint)">· 40 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/architecture/02_rope.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../04-swiglu/index.html">04 · SwiGLU →</a> · Previous: <a href="../02-normalization/index.html">← 02</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Su et al. 2021, "RoFormer: Enhanced Transformer with Rotary Position Embedding" (§3.2–3.4); Touvron et al. 2023 (LLaMA §2.2); Llama Team 2024 (Llama 3 §3.2, RoPE base 500,000); Chowdhery et al. 2022 (PaLM §2). Another visual explainer: murtuzasaifee.github.io/RoPE_Visualization.</p>

<!-- slide id="s-papers" from="papers" -->
