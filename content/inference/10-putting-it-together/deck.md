---
title: Putting It Together
body:
  data-deck: Putting it together
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
  - 'measure :: TTFT, TPOT, goodput,

    KV use, batch, queue :: a'
  - 'locate :: which phase?

    which resource? :: c'
  - 'fix :: matching technique :: e'
  - 're-measure :: did the SLO metric move? :: b'
  loop: '3 -> 0 :: one bottleneck at a time'
  caption: Diagnose by phase (prefill or decode) and resource (compute, memory bandwidth, memory capacity, network).
example:
  title: 'Worked example: why is the batch stuck at ~100?'
  setup: Llama-3-8B in BF16 on one 80 GB H100, 4,096-token contexts. The batch never grows past ~100 and GPU compute utilization is low.
  steps:
  - 'Weights: 16.06 GB. Leave ~6 GB for activations and the runtime → <b>58 GB</b> for KV.'
  - 'KV per sequence: 2 × 32 layers × 8 KV heads × 128 × 2 bytes × 4,096 = <b>0.50 GiB</b>.'
  - 'Maximum batch ≈ 58 GB / 0.54 GB ≈ <b>107</b> sequences: memory capacity is the bottleneck, not compute.'
  - 'Fixes: FP8 KV halves it → ~215 sequences; paging removes fragmentation; prefix caching shares system prompts; or add GPUs.'
  result: Measure → the KV pool is full → resource = memory capacity in decode → apply KV-shrinking techniques, then re-measure TPOT and goodput.
traps:
  tricks:
  - 'Classify every symptom by phase × resource. :: High TTFT → prefill compute or queueing; high TPOT → decode bandwidth or interference.'
  - 'Read utilization correctly. :: Low compute utilization in decode is normal; low batch with a full KV pool means capacity-bound.'
  - 'Change one thing at a time. :: Many techniques interact (chunk size vs TPOT, quantization vs accuracy).'
  traps:
  - 'Tuning before measuring. :: Adding speculative decoding to a capacity-bound server does little.'
  - 'Optimizing averages. :: Tail latency (p99) is usually what violates SLOs.'
  - 'Benchmarking an unrealistic mix. :: Prompt and output length distributions decide which bottleneck you hit.'
papers:
- vllm
- sglang
- sarathi_serve
- distserve
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">LLM Inference &amp; Serving · 10</div>
    <h1>Putting it together: diagnosing a serving system</h1>
    <p class="sub">How the techniques combine in real engines, and a symptom → cause → fix playbook for the questions you'll actually face.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>A production server has dozens of knobs, and turning the wrong one wastes GPUs (graphics processing units) or breaks SLOs (service-level objectives).</div>
      <div class="c"><b>Core idea</b>Measure first (TTFT (time to first token), TPOT (time per output token), goodput, KV (key-value) utilization, batch size, queue length), identify the bottleneck <b>phase and resource</b>, then apply the matching technique.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Every technique fixes one bottleneck

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Technique</th><th>Fixes</th><th>Main cost</th><th>Deck</th></tr>
  <tr><td>KV cache</td><td>Quadratic recompute</td><td>Memory</td><td>02</td></tr>
  <tr><td>Continuous batching</td><td>Idle slots, queueing</td><td>Dynamic memory management</td><td>03</td></tr>
  <tr><td>Chunked prefill</td><td>Decode stalls from prefill</td><td>Higher TTFT for long prompts</td><td>04</td></tr>
  <tr><td>PagedAttention / prefix cache</td><td>Fragmentation, duplicated prefixes</td><td>Indirection in the kernel</td><td>05</td></tr>
  <tr><td>Speculative decoding</td><td>Sequential decode latency</td><td>Draft compute, depends on α</td><td>06</td></tr>
  <tr><td>Quantization</td><td>Bytes per step, memory fit</td><td>Accuracy risk, calibration</td><td>07</td></tr>
  <tr><td>Tensor parallelism</td><td>Fit, per-token latency</td><td>All-reduce on the critical path</td><td>08</td></tr>
  <tr><td>Disaggregation</td><td>Prefill-decode interference</td><td>KV transfer, complexity</td><td>09</td></tr>
</table></div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Tuning without measuring goes wrong

::: cards grid3
### [d] Wrong knob
Adding GPUs when the problem is queueing, or quantizing when the problem is prefill compute.

### [b] Averages
Tuning mean latency while the p99 TPOT breaks the SLO.

### [c] One phase
Fixing TTFT by enlarging prefill iterations, which spikes everyone's TPOT.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Diagnose this

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? TTFT is high and rising with load. TPOT is fine. KV memory is only 40% used and requests are queueing. What's the most likely fix?
- [ ] Quantize the weights to INT4
- [x] Add prefill capacity or admit more prompts per iteration, e.g. a bigger chunk budget or more prefill GPUs
- [ ] Enable speculative decoding
- [ ] Reduce the batch size
> <b>B.</b> Rising TTFT with fine TPOT and spare KV memory points at <b>prefill throughput or queueing</b>. Speculative decoding and quantization mainly help decode. Smaller batches would make queueing worse.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Measure, locate, fix

::: cards grid2
### [a] Measure
TTFT and TPOT percentiles, goodput at the SLO, running batch size, queue length, KV-cache utilization, prefix-cache hit rate, GPU compute and bandwidth utilization.

### [b] Locate
Which <b>phase</b> (prefill or decode)? Which <b>resource</b> (compute, HBM (high-bandwidth memory) bandwidth, KV capacity, interconnect, scheduler)?

### [e] Fix
Apply the technique matched to that phase and resource (table on the first slide).

### [c] Verify
Re-measure goodput at the SLO, not just mean throughput.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## The playbook: symptom → cause → fix

Decide the cause before revealing.
{: .lede}

<div class="quiz ">
  <p class="qq">TPOT spikes whenever long prompts arrive; TTFT is fine.</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why"><b>Prefill interfering with decode.</b> Use chunked prefill with a token budget (04), or disaggregate (09).</div>
</div>

<div class="quiz ">
  <p class="qq">Batch size stays small although many requests are queued; KV memory is "full".</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why"><b>KV fragmentation or over-reservation, or KV too large.</b> Use paged KV (05), GQA-class (GQA = grouped-query attention) models (02), FP8 (8-bit floating point) KV (07), or shorter maximum context.</div>
</div>

<div class="quiz ">
  <p class="qq">Single-user latency is too slow even at batch 1; GPUs aren't compute-bound.</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why"><b>Memory-bound sequential decode.</b> Use speculative decoding (06), weight quantization (07), or more TP (tensor parallelism) within NVLink (08).</div>
</div>

<div class="quiz ">
  <p class="qq">Many requests share a long system prompt, and TTFT is high.</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why"><b>Recomputing the same prefix.</b> Turn on prefix caching (05).</div>
</div>

<div class="quiz ">
  <p class="qq">After moving to 16-way TP across two nodes, TPOT got worse.</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why"><b>All-reduce over the network is on the critical path.</b> Keep TP within the NVLink domain and use pipeline or data parallelism across nodes (08).</div>
</div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## How the published engines describe themselves

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Engine</th><th>What its source says it does</th><th>Source</th></tr>
  <tr><td>vLLM</td><td>PagedAttention: near-zero KV waste, flexible KV sharing; 2–4× throughput over FasterTransformer and Orca at the same latency</td><td>Kwon et al., SOSP 2023</td></tr>
  <tr><td>SGLang</td><td>RadixAttention for KV-cache reuse; compressed finite-state machines for structured output; up to 6.4× throughput</td><td>Zheng et al., 2023/24</td></tr>
  <tr><td>TensorRT-LLM</td><td>Custom attention, GEMM (general matrix multiplication) and MoE (Mixture of Experts) kernels; prefill-decode disaggregation, wide expert parallelism, speculative decoding; FP8/FP4 (4-bit floating point) quantization; prefix caching, chunked context, CUDA (Compute Unified Device Architecture, NVIDIA's programming platform for its graphics processors) graphs</td><td>NVIDIA/TensorRT-LLM README</td></tr>
</table></div>

<p class="caption">Feature lists are taken from each project's paper or README. This guide doesn't benchmark engines against each other.</p>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why a phase-and-resource view works

::: cards grid2
### [e] The physics is simple
Prefill is compute-bound and decode is bandwidth- and capacity-bound (GPU deck 02 roofline). Almost every symptom maps to one of a few resources.

### [a] Techniques compose
Continuous batching, paged KV, chunked prefill, quantization and speculative decoding stack, because each targets a different bottleneck.

### [b] Goodput keeps you honest
Measuring throughput only within the SLO stops you from "optimizing" by breaking latency.

### [c] Interviews test exactly this
"Our TTFT doubled after launch: what do you check?" is a phase-and-resource question.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "One engine or setting is best for every workload."
> The right configuration depends on prompt and output lengths, sharing, SLOs, model size and interconnect. Measure goodput on <b>your</b> traffic.
:::

::: reveal myth
? "Higher GPU utilization means the server is healthy."
> Utilization can be high while queues grow and SLOs fail. Track <b>goodput and tail latency</b>.
:::

::: reveal myth
? "Optimizations are independent, so stack them all."
> Some trade against each other: bigger chunk budgets raise TPOT, more TP raises communication, speculative decoding uses compute that big batches also want.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? TPOT spikes only when long prompts arrive. Which technique targets that first?
- [ ] Prefix caching
- [x] Chunked prefill
- [ ] INT4 weights
- [ ] More DP replicas
> <b>Chunked prefill</b> (or disaggregation).
:::

<div class="quiz ">
  <p class="qq">Name four metrics you'd check first on a struggling LLM (large language model) server.</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">TTFT and TPOT <b>percentiles</b>, <b>goodput</b> at the SLO, running <b>batch size and queue length</b>, and <b>KV-cache utilization</b>. Prefix-hit rate and GPU bandwidth utilization are good next ones.</div>
</div>

<div class="quiz ">
  <p class="qq">Why might speculative decoding help less at very high batch sizes?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">At large batch, decode moves toward <b>compute-bound</b>, so spare compute for verifying drafts shrinks. Speculative decoding exploits the memory-bound regime.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Diagnose by phase and resource: measure TTFT, TPOT, goodput, batch, queue and KV, find whether prefill or decode is short of compute, bandwidth or memory, then apply the matching technique.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Each serving technique fixes one bottleneck: KV cache for recompute, continuous batching for idle slots, chunked prefill and disaggregation for prefill-decode interference, paging and prefix caching for KV memory, speculative decoding, quantization and tensor parallelism for decode latency. In practice you measure tail TTFT and TPOT, goodput at the SLO, batch size, queue length and KV utilization; decide whether prefill or decode is limited by compute, bandwidth, memory or interconnect; then apply the matching fix and re-measure goodput.</p></div>

<div class="recap"><div><span><b>Problem:</b> many knobs; tuning without measurement breaks SLOs or wastes GPUs.</span></div><div><span><b>Core idea:</b> measure → locate the phase and resource → apply the matching technique → re-check goodput.</span></div></div>

<p class="start-hint">You've finished the series. <a href="../../build-it/index.html">See all Build-it notebooks →</a> · Previous: <a href="../13-kv-cache-fleet/index.html">← 13 · The KV cache across the fleet</a> · <a href="../index.html">All decks</a></p>

<!-- slide id="s-papers" from="papers" -->
