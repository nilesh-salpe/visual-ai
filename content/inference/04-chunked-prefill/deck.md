---
title: Chunked Prefill
body:
  data-deck: Chunked prefill
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
  - 'token budget :: per iteration, e.g. 512 :: f'
  - 'decodes first :: 1 token each, never paused :: b'
  - 'prefill chunk :: fills the remaining budget :: a'
  - 'one forward pass :: mixed batch :: c'
  loop: '3 -> 0 :: next iteration: the next chunk of the same prompt continues'
  caption: Every iteration has a bounded size, so decode latency stays flat while long prompts stream in.
example:
  title: 'Worked example: an 8,000-token prompt arrives'
  setup: '100 sequences are decoding. Token budget per iteration: 512.'
  steps:
  - 'Prefill-first: the next iteration processes 8,000 + 100 = <b>8,100 tokens</b>; every running sequence waits for it (a TPOT spike).'
  - 'Chunked: decodes take 100 tokens of the budget, leaving <b>412</b> for the new prompt.'
  - The prompt is processed in ⌈8,000 / 412⌉ = <b>20 chunks</b>, each iteration at most 512 tokens.
  - Each chunk attends to the KV of earlier chunks, so the result is identical to one big prefill.
  result: 'Running sequences never stall: every iteration is ≤ 512 tokens instead of one 8,100-token iteration. The cost: the new request''s TTFT is spread over 20
    iterations.'
traps:
  tricks:
  - 'Size the budget from the TPOT SLO. :: Pick the largest budget whose iteration time still meets the TPOT target.'
  - 'Decodes piggyback. :: A decode token costs little extra when batched with a compute-heavy prefill chunk.'
  - 'Chunking is exact. :: Later chunks attend to earlier chunks'' cached K and V.'
  traps:
  - 'Chunks too small. :: Low arithmetic intensity, and each chunk re-reads the growing KV of earlier chunks.'
  - 'Expecting less total work. :: Chunking reorganizes prefill, it does not remove FLOPs (and adds a little overhead).'
  - 'Ignoring TTFT. :: Long prompts finish prefill later than with prefill-first; that is the trade being made.'
papers:
- sarathi
- sarathi_serve
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">LLM Inference &amp; Serving · 04</div>
    <h1>Chunked prefill</h1>
    <p class="sub">Splitting long prompts into chunks so they share each iteration with ongoing decodes instead of stalling them (Sarathi-Serve, 2024).</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>When a long prompt arrives, its prefill either stalls every running decode or waits behind them. Either throughput or latency suffers.</div>
      <div class="c"><b>Core idea</b>Give each iteration a <b>token budget</b>: decodes go first (stall-free), and the rest of the budget goes to <b>chunks</b> of waiting prefills.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Prefill and decode compete for the same iterations

::: cards grid2
### [a] Prefill
Hundreds to thousands of tokens in one pass. Compute-heavy and slow per iteration.

### [b] Decode
One token per running request. Fast, but uses little of the GPU (graphics processing unit)'s compute.
:::

<div class="takeaway">Naively interleaving the two makes it hard to get high throughput and low latency at the same time (Sarathi-Serve).</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Two naive policies, two failure modes

<div class="vs">
  <div class="card d"><h3>Prefill-first</h3><p>Run a new prompt's whole prefill as soon as it arrives. Every running decode <b>stalls</b> behind that long iteration, causing TPOT (time per output token) spikes.</p></div>
  <div class="card b"><h3>Decode-first</h3><p>Finish decodes before admitting prefills. New requests wait, which hurts TTFT (time to first token), and decode-only batches underuse compute.</p></div>
</div>

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Avoid both failure modes

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? How can new prompts make progress without stalling running decodes?
- [ ] Only run prefills when no decodes are active
- [x] Split each prefill into chunks and add them to each iteration alongside the decodes, under a token budget
- [ ] Reject long prompts
- [ ] Run prefill on the CPU
> <b>B.</b> With a per-iteration token budget, decodes take their one token each first, and the leftover budget goes to prefill chunks. Iterations stay short and predictable, and prefills still progress every step.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Chunked prefills + stall-free scheduling

::: cards grid3
### [a] Token budget
Each iteration processes at most B tokens in total, which bounds iteration time and therefore TPOT.

### [b] Decodes first
Every running request gets its token, so decodes never stall.

### [e] Prefill chunks fill the rest
Waiting prompts are processed in near-equal chunks. The first output token appears when the last chunk finishes.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Tokens per iteration: prefill-first vs chunked

<div class="visual">
  <label class="ctl">Token budget B <input type="range" id="ckB" min="64" max="1024" step="64" value="256"> <output id="ckBo"></output></label>
  <h3 style="margin-top:10px">Prefill-first (whole prompts at once)</h3><svg id="pfSvg" viewBox="0 0 660 120" role="img" aria-label="Prefill-first iterations"></svg>
  <h3>Chunked (decodes first, then prefill chunks)</h3><svg id="ckSvg" viewBox="0 0 660 120" role="img" aria-label="Chunked iterations"></svg>
  <div class="legend"><span><i style="background:var(--b)"></i>decode tokens</span><span><i style="background:var(--a)"></i>prefill tokens</span><span><i style="background:var(--d)"></i>iteration larger than the budget</span></div>
  <p class="readout" id="ckOut"></p>
</div>

<p class="caption">Same request trace for both, from the rules in Build-it notebook 06. Bar height = tokens processed in that iteration, a proxy for iteration time.</p>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works

::: cards grid2
### [e] Predictable TPOT
Every iteration is bounded by B tokens, so no decode waits behind a huge prefill.

### [a] Better utilization
Decodes ride along with compute-heavy prefill chunks, filling the GPU's otherwise idle compute.

### [b] One knob
A smaller B means smoother TPOT but more iterations to finish a long prompt (higher TTFT), and a larger B the reverse.

### [c] Measured (vs vLLM, under latency SLOs)
Sarathi-Serve: <b>2.6×</b> capacity (Mistral-7B, 1×A100), up to <b>3.7×</b> (Yi-34B, 2×A100), up to <b>5.6×</b> (Falcon-180B with pipeline parallelism).
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Chunking changes the model's output."
> No. Attention over earlier chunks uses the KV cache, so the result is the same as a single prefill pass.
:::

::: reveal myth
? "A bigger budget is always better."
> A bigger B finishes prompts sooner but allows longer iterations, which brings back TPOT spikes. It's a <b>trade-off</b>.
:::

::: reveal myth
? "Chunked prefill only helps long prompts."
> It also raises <b>utilization</b>, because decode-only iterations underuse compute and the chunks fill that gap.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? In stall-free scheduling, what gets the budget first?
- [ ] New prefills
- [x] Running decodes, one token each
- [ ] The longest prompt
- [ ] Whichever arrived last
> <b>Decodes first</b>, so they never stall. Prefill chunks use what's left.
:::

<div class="quiz ">
  <p class="qq">What happens to TTFT and TPOT as the token budget B shrinks?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">TPOT becomes smoother and lower (short iterations), but <b>TTFT rises</b> because long prompts need more iterations to finish prefill.</div>
</div>

<div class="quiz">
  <p class="qq">What serving-capacity gain did Sarathi-Serve report for Mistral-7B on one A100 vs vLLM?</p>
  <div class="opts">
  <button>A. 1.1×</button>
  <button data-ok>B. 2.6×</button>
  <button>C. 6.4×</button>
  <button>D. 36.9×</button>
  </div>
  <div class="why"><b>2.6×</b> under tail-latency constraints.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Chunked prefill bounds every iteration with a token budget: decodes go first and prefill chunks fill the rest, so long prompts never stall streaming users.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Prefill is compute-heavy and decode is light, and naive schedulers either stall decodes behind a long prefill or delay new requests. Sarathi-Serve splits prefills into chunks and gives each iteration a token budget: running decodes get their token first, then waiting prompts get chunks of whatever budget is left. Iterations stay short and predictable, decodes piggyback on compute-heavy chunks, and it reported 2.6× to 5.6× more serving capacity than vLLM under latency SLOs.</p></div>

<div class="recap"><div><span><b>Problem:</b> long prefills stall decodes (TPOT spikes) or wait behind them (TTFT).</span></div><div><span><b>Core idea:</b> a per-iteration token budget: decodes first, prefill chunks after.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/06_chunked_prefill.ipynb" target="_blank" rel="noopener">06 · Chunked prefill with a token budget</a> <span style="color:var(--faint)">· 40 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/inference/06_chunked_prefill.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../06-speculative-decoding/index.html">06 · Speculative decoding →</a> · Previous: <a href="../03-batching/index.html">← 03 · Continuous batching</a> · <a href="../index.html">All decks</a></p>

<!-- slide id="s-papers" from="papers" -->
