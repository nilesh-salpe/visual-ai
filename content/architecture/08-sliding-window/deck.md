---
title: 'Long Context II: Sliding Window and ALiBi'
body:
  data-deck: 'Long context II: sliding window and ALiBi'
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
  - 'token i :: query :: f'
  - 'attend to i−W+1 … i :: window of W keys :: c'
  - 'stack L layers :: reach ≈ L·(W−1)+1 :: a'
  - 'rolling cache :: slot = i mod W :: b'
  caption: Bounded attention per layer; depth relays information further back; memory capped at W per layer.
example:
  title: 'Worked example: Mistral 7B at 32K tokens'
  setup: 32 layers, 8 KV heads of 128, BF16, window W = 4,096.
  steps:
  - 'KV per token: 2 × 32 × 8 × 128 × 2 = <b>128 KiB</b>.'
  - 'Full cache at 32,768 tokens: <b>4 GiB</b>; rolling buffer (4,096 slots): <b>0.5 GiB</b>, 8× less.'
  - 'Theoretical span: 32 × (4,096 − 1) + 1 = <b>131,041</b> tokens (paper: ~131K).'
  - Token 10,000 is written to slot 10,000 mod 4,096 = <b>1,808</b>, overwriting token 5,904.
  result: Constant memory per sequence and attention cost O(T·W), at the price of indirect long-range access.
traps:
  tricks:
  - 'Span ≈ layers × W. :: Exactly L·(W−1)+1 with an inclusive window of W keys.'
  - 'ALiBi slopes: 2^(−8i/n). :: For 8 heads: 1/2 … 1/256.'
  - 'Check sliding_window in the config. :: Mixtral, unlike Mistral 7B, is dense over 32K.'
  traps:
  - 'Assuming nothing beyond W is visible. :: Information hops W per layer, lossily.'
  - 'Calling ALiBi a position embedding. :: It is a bias on attention scores.'
  - 'Off-by-one windows. :: Codebases differ on whether the window includes the current token.'
papers:
- mistral
- longformer
- alibi
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">The Modern LLM · 08</div>
    <h1>Long context II: sliding window and ALiBi</h1>
    <p class="sub">Two other ways to handle long sequences: limit how far each layer looks (sliding-window attention with a rolling KV (key-value) cache), or bias scores by distance (ALiBi (Attention with Linear Biases)).</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Full attention costs O(T²) compute and its KV cache grows with every token. At long T, both memory and time explode, even when most useful context is nearby.</div>
      <div class="c"><b>Core idea</b><b>Sliding window</b>: each token attends only to the last W tokens, and stacked layers relay information further back, so the cache can be a fixed-size ring buffer. <b>ALiBi</b>: no position embeddings; subtract a head-specific slope × distance from every score.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Full attention gets expensive fast

Score computations per layer and KV-cache entries per layer, as the sequence grows. Full causal attention computes about T²/2 scores and caches T entries. A sliding window of W = 4,096 computes at most T·W and caches at most W.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">Sequence length T <input type="range" id="cT" min="10" max="17" step="0.5" value="15"> <output id="cTo"></output></label></div>
  <div id="cBars" style="margin-top:12px"></div>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why not just cut the context?

::: cards grid3
### [d] Truncating loses information
Dropping everything older than W tokens at the input means the model can't use it at all.

### [b] Sparse patterns are fiddly
Hand-designed sparse attention (strided, global tokens) needs custom kernels and careful choices for every pattern.

### [c] Position extrapolation still matters
Even with cheaper attention, the position encoding must behave sensibly at lengths beyond training (deck 07, and ALiBi below).
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## How far can a window see?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Mistral 7B uses a window of W = 4,096 tokens in each of its 32 layers. What is the theoretical attention span at the last layer?
- [ ] 4,096 tokens
- [ ] 8,192 tokens
- [x] About 131K tokens
- [ ] Unlimited
> <b>C.</b> Each layer lets information move up to W tokens further back. After 32 layers that is about 32 × 4,096 ≈ <b>131K</b> tokens (Mistral's figure). Exactly: L·(W−1)+1 = 131,041 with an inclusive window of W keys.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Two ideas

::: cards grid2
### [a] Sliding-window attention (SWA)
Token i attends to positions i−W+1 … i only. Information from further back reaches i indirectly: token i−W saw it in the previous layer. The KV cache needs only the last W entries, stored in a <b>rolling buffer</b> at slot i mod W. Mistral 7B: W = 4,096, 2× faster at 16K with its kernel changes, 8× less cache at 32K.

### [b] ALiBi
Don't add position embeddings at all. Add a <b>linear penalty</b> −m·(i−j) to each query-key score, with a different slope m per head (a geometric sequence, 1/2 … 1/256 for 8 heads). Trained at 1,024 tokens, a 1.3B model extrapolates to 2,048 and matches a sinusoidal model trained at 2,048, while training 11% faster and using 11% less memory.
:::

<div class="deep"><h4>Not every Mistral-family model uses the window</h4><p>Mixtral's paper notes it "supports a fully dense context length of 32k tokens", meaning full attention, unlike Mistral 7B's sliding window. Windowing is a per-model design choice; a model card or config (<code>sliding_window</code>) tells you which.</p></div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Stacked windows: the receptive field grows with depth

Each row is a layer, each column a position (newest on the right). Highlighted cells are positions that can influence the last token's output through the stack. One layer sees W positions; each extra layer reaches W−1 further.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">Window W <input type="range" id="wW" min="2" max="8" step="1" value="4"> <output id="wWo"></output></label>
    <label class="ctl">Layers <input type="range" id="wL" min="1" max="8" step="1" value="4"> <output id="wLo"></output></label>
  </div>
  <svg id="wSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Receptive field across layers"></svg>
  <p class="readout" id="wOut"></p>
</div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## The rolling-buffer KV cache

A cache of W = 4 slots. Token t's key and value are written to slot <b>t mod 4</b>, overwriting the entry from t−4, which the window no longer needs. Press "next token".
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><button class="btn primary" id="rbNext">next token</button><button class="btn" id="rbReset">reset</button></div>
  <svg id="rbSvg" viewBox="0 0 660 170" style="margin-top:10px" role="img" aria-label="Rolling buffer"></svg>
  <p class="readout" id="rbOut"></p>
</div>

<!-- slide id="s-how3" chapter="How" tag="5 · How it works" tagclass="b5" -->
## ALiBi: a distance penalty per head

The bias added to each attention score for one head (rows: query position i, columns: key position j, causal). Darker means a bigger penalty. Heads with a steep slope focus locally; heads with a gentle slope can look far back.
{: .lede}

<div class="visual">
  <div class="seg" id="aSeg"><button data-v="1" class="on">head 1 (m = 1/2)</button><button data-v="3">head 3 (m = 1/8)</button><button data-v="5">head 5 (m = 1/32)</button><button data-v="8">head 8 (m = 1/256)</button></div>
  <svg id="aSvg" viewBox="0 0 660 260" style="margin-top:10px" role="img" aria-label="ALiBi bias matrix"></svg>
</div>

<p class="caption">Slopes for 8 heads: the geometric sequence 1/2¹, 1/2², …, 1/2⁸. For n heads it starts at 2^(−8/n) with the same ratio (Press et al.).</p>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why they work, and their limits

::: cards grid2
### [a] Most attention is local
Many heads mostly look nearby. A window keeps that cheap and lets depth carry longer-range information.

### [e] Memory becomes constant
With a rolling buffer, KV memory per sequence is capped at W entries per layer: 8× smaller at 32K for Mistral 7B, and it never grows during generation.

### [b] ALiBi has no unseen positions
A penalty proportional to distance is defined for any distance, and longer distances just get a larger penalty, which is why it extrapolates.

### [d] Limits
Information older than W must survive several relays, so exact long-range retrieval is harder than with full attention. ALiBi's built-in bias towards recent tokens can also limit how much distant text is used.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "A sliding-window model can't use anything older than W tokens."
> It can, indirectly: information moves up to W further back per layer, so the theoretical span is about L × W. It is lossy, though.
:::

::: reveal myth
? "ALiBi is a kind of position embedding."
> Nothing is added to the embeddings. ALiBi adds a fixed, distance-dependent <b>bias to the attention scores</b>.
:::

::: reveal myth
? "Every Mistral model uses sliding-window attention."
> Mistral 7B does (W = 4,096). Mixtral uses fully dense attention over 32K. Check the config.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? In Mistral's rolling buffer with W = 4,096, where is token 10,000's key stored?
- [ ] slot 10,000
- [x] slot 10,000 mod 4,096 = 1,808
- [ ] slot 0
- [ ] it isn't cached
> <b>Slot i mod W = 1,808</b>, overwriting token 5,904's entry.
:::

<div class="quiz ">
  <p class="qq">What does ALiBi add to the score between query i and key j?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">−m·(i − j), a negative bias growing linearly with distance, with a fixed slope m per head (e.g. 1/2 … 1/256 for 8 heads). No position embeddings at all.</div>
</div>

<div class="quiz ">
  <p class="qq">Why does sliding-window attention make the KV cache constant-size?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">A token never attends further back than W positions, so older keys and values are never needed again and can be overwritten in a ring buffer of W slots.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Sliding windows cap attention cost and KV memory and rely on depth to reach further; ALiBi replaces position embeddings with a per-head distance penalty that extrapolates.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Full attention costs order T squared and its cache grows with every token. Sliding-window attention lets each token attend only to the last W tokens. Information older than that still flows indirectly through the stack, so Mistral 7B, with W of 4,096 over 32 layers, has a theoretical span of about 131K. Because no token looks back further than W, the KV cache can be a ring buffer indexed by position mod W: 8 times less memory at 32K. ALiBi removes position embeddings and subtracts a head-specific slope times the distance from each attention score, which let a model trained at 1,024 tokens work at 2,048.</p></div>

<div class="recap"><div><span><b>Problem:</b> O(T²) scores and an ever-growing KV cache.</span></div><div><span><b>SWA (sliding-window attention):</b> attend to the last W; span ≈ L·W; rolling buffer at i mod W.</span></div><div><span><b>ALiBi:</b> score − m·distance, slopes 1/2…1/256; train short, test long.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/architecture/07_sliding_window.ipynb" target="_blank" rel="noopener">07 · Sliding-window attention and the rolling KV cache</a> <span style="color:var(--faint)">· 40 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/architecture/07_sliding_window.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../09-flash-attention/index.html">09 · FlashAttention internals →</a> · Previous: <a href="../07-rope-scaling/index.html">← 07</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Jiang et al. 2023, "Mistral 7B" (§2, Table 1, Fig. 1–2); Jiang et al. 2024 (Mixtral §2, dense 32K); Beltagy et al. 2020 (Longformer); Press et al. 2022, "Train Short, Test Long: Attention with Linear Biases" (ALiBi, §3).</p>

<!-- slide id="s-papers" from="papers" -->
