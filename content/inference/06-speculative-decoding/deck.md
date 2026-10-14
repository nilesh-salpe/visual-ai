---
title: Speculative Decoding
body:
  data-deck: Speculative decoding
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
  - 'draft γ tokens :: small model, cheap :: b'
  - 'verify in one pass :: target scores all γ + 1 positions :: a'
  - 'accept / reject :: modified rejection sampling :: c'
  - 'emit :: accepted prefix

    + 1 token from the target :: e'
  loop: '3 -> 0 :: repeat from the last accepted token'
  caption: 'Exact: the output distribution is the target model''s.'
example:
  title: 'Worked example: expected speedup'
  setup: Acceptance rate α = 0.8, draft length γ = 4, and a draft that costs c = 0.05 of a target forward pass.
  steps:
  - Expected tokens per target pass = (1 − α<sup>γ+1</sup>) / (1 − α) = (1 − 0.8<sup>5</sup>) / 0.2 = <b>3.36</b>.
  - Cost per iteration = γ·c + 1 = 4 × 0.05 + 1 = <b>1.20</b> target-pass equivalents.
  - Speedup = 3.36 / 1.20 ≈ <b>2.8×</b>.
  - 'With α = 0.5 instead: tokens = 1.94, speedup ≈ 1.6×. Draft quality matters more than draft length.'
  result: Formulas from Leviathan et al. (2023). This assumes the target pass costs the same for 1 or γ + 1 tokens, which holds while decode is memory-bound (small
    batch).
traps:
  tricks:
  - 'E[tokens] = (1 − α^(γ+1)) / (1 − α). :: Speedup = E[tokens] / (γc + 1).'
  - 'Best at small batch. :: Verifying γ + 1 tokens is nearly free only while the target is memory-bound.'
  - 'Every iteration emits ≥ 1 token. :: Even if all drafts are rejected, the target''s own token is kept.'
  traps:
  - 'Assuming it changes outputs. :: With the modified rejection rule the samples are exactly from the target distribution.'
  - 'Using it at large batch. :: When decode is already compute-bound, the extra verification FLOPs reduce or erase the gain.'
  - 'Ignoring draft cost and KV. :: The draft model also needs memory, its own KV cache and time; c is not zero.'
papers:
- leviathan
- chen
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">LLM Inference &amp; Serving · 06</div>
    <h1>Speculative decoding</h1>
    <p class="sub">Draft several tokens with a small model, verify them all in one pass of the large model, and keep exactly the large model's output distribution (Leviathan et al., ICML 2023; Chen et al., 2023).</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Decode produces one token per full read of the model's weights. The GPU (graphics processing unit) waits on memory while its compute sits mostly idle, and tokens can't be generated in parallel because each depends on the last.</div>
      <div class="c"><b>Core idea</b>A cheap <b>draft</b> model proposes γ tokens; the target model <b>scores all of them in one forward pass</b>; a modified rejection rule accepts a prefix of them, so the output distribution is unchanged.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Decode is slow for a reason that has nothing to do with compute

At batch 1, every decode step reads all the weights, about 140 GB for a 70B model in BF16 (bfloat16, a 16-bit floating-point format with the exponent range of 32-bit floats), to produce <b>one</b> token. Scoring several tokens in the same pass costs almost the same, because the memory read is the bottleneck, not the math (GPU deck 02).
{: .lede}

<div class="takeaway">If we knew which tokens to score, we could check several of them for about the price of one step.</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## The obvious shortcuts break something

::: cards grid3
### [d] Just use a small model
Fast, but the quality is the small model's, not the large one's.

### [b] Generate in parallel
Impossible directly: token t+1 depends on token t (autoregression).

### [c] Bigger batches
Help throughput across users, but don't make <em>one</em> user's stream faster.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Faster, without changing the output

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? How can a large model generate faster without changing what it would output?
- [ ] Replace it with a distilled small model
- [x] Let a small model draft several tokens and have the large model verify them all in one parallel pass
- [ ] Skip every other layer
- [ ] Use greedy decoding only
> <b>B.</b> Verification of γ drafted positions happens in <b>one</b> target forward pass. With the modified rejection rule, the accepted tokens are distributed exactly as if the target had sampled them itself.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Draft, verify, accept or reject

<div class="grid2">
  <div class="card a"><h3>1. Draft</h3><p>The draft model q samples γ tokens autoregressively. It's cheap because it's small (often about two orders of magnitude smaller, per Leviathan et al.).</p></div>
  <div class="card b"><h3>2. Verify</h3><p>The target model p scores all γ positions plus one extra in a single forward pass.</p></div>
  <div class="card e"><h3>3. Accept or reject</h3><p>Accept draft x with probability min(1, p(x)/q(x)). On the first rejection, sample a replacement from norm(max(0, p − q)) and stop.</p></div>
  <div class="card c"><h3>4. Bonus token</h3><p>If all γ are accepted, sample one more token from p for free. Each pass yields 1 to γ+1 tokens.</p></div>
</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## One verification step, by hand <span class="ill">illustrative probabilities</span>

<div class="visual">
  <div class="seg" id="exSeg"><button data-v="a" class="on">Example 1</button><button data-v="b">Example 2</button></div>
  <div class="scroll-x" style="margin-top:10px"><table class="tbl" id="exTbl"></table></div>
  <p class="readout" id="exOut" style="margin-top:8px"></p>
</div>

<p class="caption">u is the uniform random number drawn for each draft token. Accept if u &lt; min(1, p/q).</p>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## How many tokens per target pass, and how much faster?

If each draft token is accepted with probability α, the expected tokens per target pass is <b>(1 − α<sup>γ+1</sup>) / (1 − α)</b> (Leviathan et al., eq. 1). With draft cost c relative to the target, the wall-clock improvement is that divided by <b>(γc + 1)</b> (Theorem 3.8).
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">α (acceptance) <input type="range" id="sA" min="0.3" max="0.95" step="0.01" value="0.8"> <output id="sAo"></output></label>
    <label class="ctl">γ (draft length) <input type="range" id="sG" min="1" max="12" step="1" value="4"> <output id="sGo"></output></label>
    <label class="ctl">c (draft cost) <input type="range" id="sC" min="0" max="0.3" step="0.01" value="0.05"> <output id="sCo"></output></label>
  </div>
  <svg id="sSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Speedup vs gamma"></svg>
  <div class="grid3">
    <div class="stat"><div class="num" id="sE"></div><div class="lbl">expected tokens per target pass</div></div>
    <div class="stat"><div class="num" id="sS" style="color:var(--e)"></div><div class="lbl">expected wall-clock speedup</div></div>
    <div class="stat"><div class="num" id="sO"></div><div class="lbl">best γ for this α and c</div></div>
  </div>
</div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works

::: cards grid2
### [e] Exactness
The rejection rule makes the output distribution identical to the target's. Leviathan et al. report <b>identical outputs</b>, and Chen et al. preserve it "within hardware numerics". Build-it notebook 09 checks this by Monte Carlo.

### [a] Spare compute
Decode is memory-bound, so verifying γ+1 positions costs about one step. Accepted drafts are close to free tokens.

### [b] Measured
<b>2–3×</b> on T5-XXL (Leviathan et al.); <b>2–2.5×</b> on Chinchilla 70B (Chen et al.).

### [c] Limit
Even with a free draft (c ≈ 0), the speedup is bounded by 1/(1 − α), so the acceptance rate matters most.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Speculative decoding trades quality for speed."
> The output distribution is <b>exactly</b> the target model's. Only latency changes.
:::

::: reveal myth
? "It only works with greedy decoding."
> The modified rejection sampling works for <b>sampling</b> too, which is the setting both papers address.
:::

::: reveal myth
? "A longer draft (bigger γ) is always faster."
> Each extra draft token costs c and is less likely to be accepted. The best γ depends on α and c.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

<div class="quiz">
  <p class="qq">With α = 0.8 and γ = 4, what is the expected number of tokens per target pass?</p>
  <div class="opts">
  <button>A. 1.8</button>
  <button data-ok>B. 3.36</button>
  <button>C. 4</button>
  <button>D. 5</button>
  </div>
  <div class="why">(1 − 0.8⁵) / 0.2 = <b>3.36</b>.</div>
</div>

<div class="quiz ">
  <p class="qq">What is the maximum possible speedup as γ → ∞ with a free draft model (c = 0)?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why"><b>1 / (1 − α)</b>, e.g. 5× for α = 0.8. Throughput per target pass is capped by the acceptance rate.</div>
</div>

::: quiz
? On rejecting draft x at position i, what is the replacement token sampled from?
- [ ] The draft q
- [ ] The target p
- [x] norm(max(0, p − q))
- [ ] Uniform
> The <b>residual distribution</b> norm(max(0, p − q)), which corrects for what the draft over-proposed.
:::

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Speculative decoding drafts γ tokens with a cheap model and verifies them in one target pass. A modified rejection rule keeps the output exactly the target's, and speedup ≈ (1 − α^(γ+1)) / ((1 − α)(γc + 1)).</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Decode is memory-bound: each step reads all the weights to make one token, so scoring several tokens costs about the same as scoring one. Speculative decoding lets a small draft model propose γ tokens, then the target model scores them all in one pass and accepts each with probability min(1, p/q), resampling from max(0, p − q) on the first rejection. The output distribution is exactly the target's. Expected tokens per pass is (1 − α^(γ+1))/(1 − α), and the papers reported 2–3× speedups.</p></div>

<div class="recap"><div><span><b>Problem:</b> one token per full weight read; autoregression blocks parallel generation.</span></div><div><span><b>Core idea:</b> draft cheaply, verify in parallel, accept or reject exactly; speedup is set by α, γ and c.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/09_speculative_sampling.ipynb" target="_blank" rel="noopener">09 · Speculative sampling</a> <span style="color:var(--faint)">· 45 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/inference/09_speculative_sampling.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../07-quantization/index.html">07 · Quantization →</a> · Previous: <a href="../05-paged-attention/index.html">← 05</a> · <a href="../index.html">All decks</a></p>

<!-- slide id="s-papers" from="papers" -->
