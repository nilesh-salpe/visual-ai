---
title: The Inference Workload
body:
  data-deck: The inference workload
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
  - 'request :: arrives, waits in queue :: f'
  - 'prefill :: whole prompt in one pass

    compute-bound :: a'
  - 'first token :: TTFT ends here :: e'
  - 'decode step :: one token per sequence

    memory-bound :: b'
  - 'done :: end-of-sequence or limit :: f'
  loop: '3 -> 3 :: repeat once per output token: each step takes one TPOT'
  caption: Every request has one compute-heavy prefill, then many memory-heavy decode steps.
example:
  title: 'Worked example: latency of one request'
  setup: 'Llama-3-8B (8.03B parameters, BF16) on one H100 SXM. A 2,000-token prompt and a 300-token answer, at batch size 1. Spec sheet: 989 TFLOP/s dense BF16, 3.35
    TB/s HBM (high-bandwidth memory). Assume prefill reaches 40% of peak.'
  steps:
  - Prefill compute ≈ 2 × parameters × prompt tokens = 2 × 8.03B × 2,000 = <b>32.1 TFLOP</b>.
  - TTFT ≈ 32.1 TFLOP ÷ (0.4 × 989 TFLOP/s) ≈ <b>81 ms</b> (plus any queueing).
  - 'Each decode step must read all weights once: 2 bytes × 8.03B = 16.1 GB at 3.35 TB/s ≈ <b>4.8 ms</b>. That is the TPOT floor at batch 1.'
  - Decode total ≈ 299 more tokens × 4.8 ms ≈ <b>1.43 s</b>.
  result: End-to-end ≈ 0.08 + 1.43 ≈ <b>1.51 s</b>, and decode is 95% of it. At batch 1 the GPU does ~3 TFLOP/s during decode, a few percent of peak, which is why
    batching (deck 03) matters.
traps:
  tricks:
  - 'Forward FLOPs ≈ 2 × parameters per token. :: Prefill cost ≈ 2·N·prompt_tokens; good to within the attention term for normal contexts.'
  - 'Decode floor ≈ bytes read ÷ HBM bandwidth. :: At small batch, TPOT ≈ (weight bytes + KV bytes) / bandwidth, not FLOPs / peak.'
  - 'Latency ≈ TTFT + (output − 1) × TPOT. :: Long answers are dominated by decode; long prompts by prefill.'
  - 'Quote goodput, not throughput. :: Requests per second that meet both the TTFT and TPOT SLOs.'
  traps:
  - 'Comparing tokens/s across workloads. :: Prompt-heavy and output-heavy mixes give very different numbers on the same server.'
  - 'Averages instead of percentiles. :: p99 TTFT and TPOT are what break products; means hide them.'
  - 'Forgetting the queue. :: Measured TTFT includes waiting time; under load it can dominate prefill.'
  - 'Counting prompt tokens as generated. :: Input tokens/s and output tokens/s are different metrics with different costs.'
papers:
- pope
- distserve
- splitwise
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">LLM Inference &amp; Serving · 01</div>
    <h1>The inference workload</h1>
    <p class="sub">What happens when a request hits an LLM (large language model) server: the two phases, the metrics users feel and the ones operators pay for, and why a single "tokens per second" number misleads.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Users care about latency, operators care about throughput, and the two pull in opposite directions.</div>
      <div class="c"><b>Core idea</b>Separate the work into <b>prefill</b> (the whole prompt at once) and <b>decode</b> (one token at a time). Measure TTFT (time to first token), TPOT (time per output token), and <b>goodput</b>: throughput that still meets latency targets.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## One request, two very different phases

A chat request has a prompt of P tokens and generates O output tokens. The server first processes the whole prompt in one pass, which is <b>prefill</b>. Then it generates output tokens one at a time, each depending on the last, which is <b>decode</b>.
{: .lede}

<div class="visual"><svg id="p1Svg" viewBox="0 0 660 150" role="img" aria-label="Prefill then decode timeline"></svg></div>

<div class="takeaway">Time to first token comes from prefill. The steady stream of tokens after that comes from decode. They are limited by different resources (see the roofline in GPU (graphics processing unit) deck 02).</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why "tokens per second" isn't enough

::: cards grid3
### [d] Throughput hides latency
A huge batch maximizes tokens/s for the server while each user waits longer per token.

### [b] Averages hide tails
A good mean latency can coexist with a p99 that breaks the product experience.

### [c] Two phases, one number
Prefill speed (prompt tokens/s) and decode speed (output tokens/s) behave differently and need different fixes.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Pick the right metric

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Which metric captures "how much load the server handles while still meeting its latency targets"?
- [ ] Peak tokens per second
- [x] Goodput: requests per second served within the TTFT and TPOT SLOs
- [ ] GPU utilization
- [ ] Average end-to-end latency
> <b>B.</b> DistServe defines <b>goodput</b> as the request rate a system can serve while meeting its time-to-first-token and time-per-output-token targets. Peak tokens/s ignores latency, utilization can be high while users wait, and averages hide tails.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## The four numbers that describe a serving system

::: cards grid2
### [a] TTFT: time to first token
Queueing plus prefill of the prompt. Grows with prompt length. Users feel it as "how long until it starts typing".

### [b] TPOT: time per output token
Time per decode step, also called inter-token latency. Users feel it as streaming speed.

### [c] Throughput
Tokens (or requests) per second across all users. This is what the operator pays for.

### [e] Goodput
Throughput counted only while TTFT and TPOT stay within their SLOs (service-level objectives). It's the metric that matters (DistServe, OSDI '24).
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Batching trades TPOT for throughput <span class="ill">illustrative step-time model</span>

A decode step reads all the weights once whatever the batch size, so batching raises throughput. Each step also gets a little slower as the batch grows. Set a TPOT SLO and find the largest batch that still meets it.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">TPOT SLO <input type="range" id="sloT" min="20" max="80" step="1" value="40"> <output id="sloTo"></output></label>
    <label class="ctl">Batch <input type="range" id="bB" min="0" max="8" step="0.1" value="5"> <output id="bBo"></output></label>
  </div>
  <svg id="gpSvg" viewBox="0 0 660 260" style="margin-top:10px" role="img" aria-label="Throughput vs batch with SLO"></svg>
  <div class="grid4">
    <div class="stat"><div class="num" id="kT"></div><div class="lbl">TPOT at this batch</div></div>
    <div class="stat"><div class="num" id="kX"></div><div class="lbl">throughput (tokens/s)</div></div>
    <div class="stat"><div class="num" id="kB"></div><div class="lbl">largest batch within SLO</div></div>
    <div class="stat"><div class="num" id="kG" style="color:var(--e)"></div><div class="lbl">goodput (tokens/s)</div></div>
  </div>
</div>

<p class="caption">Toy model: step time = 18 ms + 0.12 ms × batch. Real curves come from the roofline: memory-bound at small batch, then compute-bound (GPU deck 02).</p>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## One request's latency, end to end

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">Prompt tokens <input type="range" id="rP" min="7" max="15" step="0.5" value="11"> <output id="rPo"></output></label>
    <label class="ctl">Output tokens <input type="range" id="rO" min="4" max="11" step="0.5" value="8"> <output id="rOo"></output></label>
    <label class="ctl">Prefill speed <select id="rS"><option value="5000">5K tok/s</option><option value="20000" selected>20K tok/s</option><option value="80000">80K tok/s</option></select></label>
    <label class="ctl">TPOT <select id="rD"><option value="15">15 ms</option><option value="30" selected>30 ms</option><option value="60">60 ms</option></select></label>
  </div>
  <svg id="rSvg" viewBox="0 0 660 90" style="margin-top:10px" role="img" aria-label="Latency breakdown"></svg>
  <p class="readout" id="rOut"></p>
</div>

<p class="caption">Illustrative speeds. TTFT ≈ prompt ÷ prefill speed (ignoring queueing), and total ≈ TTFT + output tokens × TPOT.</p>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why splitting the metrics pays off: each one has its own fixes

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Symptom</th><th>Bottleneck</th><th>Techniques (deck)</th></tr>
  <tr><td>Low throughput at small batch</td><td>Decode is memory-bound, so GPU compute sits idle</td><td>Continuous batching (03), quantization (07)</td></tr>
  <tr><td>Can't fit enough requests</td><td>KV-cache (KV = key-value) memory</td><td>GQA (grouped-query attention)/MLA (02), PagedAttention (05), FP8 (8-bit floating point) KV (07)</td></tr>
  <tr><td>TPOT spikes when long prompts arrive</td><td>Prefill interferes with decode</td><td>Chunked prefill (04), disaggregation (09)</td></tr>
  <tr><td>High TTFT on repeated prompts</td><td>Recomputing shared prefixes</td><td>Prefix caching (05)</td></tr>
  <tr><td>TPOT too slow even at batch 1</td><td>Sequential decode</td><td>Speculative decoding (06), tensor parallelism (08)</td></tr>
</table></div>

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Tokens per second tells you how good a server is."
> Not on its own. Without latency targets it rewards huge batches that make each user wait. Use <b>goodput under SLOs</b>.
:::

::: reveal myth
? "A bigger batch is always better."
> Throughput rises, but so does TPOT. Past the SLO limit, extra batch size adds no goodput.
:::

::: reveal myth
? "TTFT and TPOT have the same bottleneck."
> TTFT is mostly <b>prefill compute</b> plus queueing. TPOT is mostly <b>memory bandwidth</b> per decode step. They need different fixes.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

<div class="quiz ">
  <p class="qq">Prompt 2,000 tokens at a prefill speed of 20,000 tokens/s, then 500 output tokens at 30 ms TPOT. Roughly what are TTFT and total latency?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">TTFT ≈ 2,000 / 20,000 = <b>0.1 s</b>. Decode ≈ 500 × 0.03 = 15 s, so the total is about <b>15.1 s</b>. Decode dominates long answers.</div>
</div>

::: quiz
? Which definition of goodput does DistServe use?
- [ ] Peak tokens/s
- [x] Request rate served while meeting TTFT and TPOT SLOs
- [ ] GPU FLOPs utilization
- [ ] Requests per GPU
> <b>Request rate within the latency SLOs</b>.
:::

<div class="quiz ">
  <p class="qq">Why does batching help decode throughput so much?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Each decode step must read <b>all the weights</b> anyway. A larger batch reuses that one read for many sequences, moving decode from memory-bound toward compute-bound.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Serving is two workloads, a compute-bound prefill and a memory-bound decode, judged by TTFT, TPOT and goodput under SLOs.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>An LLM request has a prefill phase that processes the whole prompt in one pass, which sets the time to first token, and a decode phase that generates one token per step, which sets the time per output token. Throughput is what operators pay for, but bigger batches slow each step, so the right metric is goodput: the load you can serve while TTFT and TPOT stay within their SLOs. Each later technique targets one of these bottlenecks.</p></div>

<div class="recap"><div><span><b>Problem:</b> latency and throughput conflict, and a single tokens/s number hides that.</span></div><div><span><b>Core idea:</b> separate prefill and decode, measure TTFT, TPOT and goodput, then fix each bottleneck.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/01_tiny_gpt_forward.ipynb" target="_blank" rel="noopener">01 · A tiny GPT forward pass in NumPy</a> <span style="color:var(--faint)">· 40 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/inference/01_tiny_gpt_forward.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../02-kv-cache/index.html">02 · KV cache →</a> · <a href="../index.html">All decks</a></p>

<!-- slide id="s-papers" from="papers" -->
