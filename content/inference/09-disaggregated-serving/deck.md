---
title: Disaggregated Serving
body:
  data-deck: Disaggregated serving
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
  - 'request :: prompt :: f'
  - 'prefill pool :: compute-heavy GPUs

    builds KV :: a'
  - 'KV transfer :: network / NVLink :: d'
  - 'decode pool :: memory-heavy GPUs

    streams tokens :: b'
  - 'user :: tokens arrive :: f'
  caption: Each pool gets its own GPUs, parallelism and scale, so prefill bursts don't slow ongoing decodes.
example:
  title: 'Worked example: what does moving the KV cost?'
  setup: 'Llama-3-70B KV cache: 320 KiB per token (deck 02). A 4,000-token prompt.'
  steps:
  - 'KV to move: 4,000 × 320 KiB = <b>1.22 GiB</b> (1.31 GB).'
  - 'Over a 400 Gb/s NIC (network interface card, 50 GB/s): <b>26 ms</b>.'
  - 'Over NVLink at 900 GB/s (H100): <b>1.5 ms</b>.'
  - Transfer can overlap with prefill layer by layer, so much of it can be hidden.
  result: Disaggregation pays when the interference it removes costs more than ~26 ms of transfer per request, which is typical with tight TPOT SLOs and long prompts.
traps:
  tricks:
  - 'Transfer time = KV bytes ÷ link bandwidth. :: Compute it before deciding; GQA and FP8 KV shrink it.'
  - 'Size pools by demand. :: Ratio of prefill GPUs to decode GPUs follows the prompt/output mix.'
  - 'Optimize per phase. :: Different parallelism and even different GPU types per pool (Splitwise).'
  traps:
  - 'Short prompts, small models. :: Little interference to remove; the extra hop may cost more than it saves.'
  - 'Slow links. :: Without fast interconnect the KV transfer dominates TTFT.'
  - 'Pool imbalance. :: A shift in traffic mix leaves one pool idle and the other overloaded.'
papers:
- distserve
- splitwise
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">LLM Inference &amp; Serving · 09</div>
    <h1>Disaggregated prefill and decode</h1>
    <p class="sub">Running prefill and decode on separate GPU (graphics processing unit) pools, each sized and configured for its phase, and moving the KV (key-value) cache between them (DistServe, OSDI 2024; Splitwise, 2024).</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Prefill (compute-heavy) and decode (memory-heavy) interfere when they share GPUs, and one configuration can't be optimal for both.</div>
      <div class="c"><b>Core idea</b><b>Split the phases</b> across machines. Prefill GPUs compute the prompt and its KV, the KV moves to decode GPUs, and each pool gets its own parallelism and scale to maximize <b>goodput</b> under SLOs (service-level objectives).</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Two phases with opposite needs

<div class="vs">
  <div class="card a"><h3>Prefill: "prompt computation"</h3><p>Compute-intensive: many tokens per pass. Sets TTFT (time to first token).</p></div>
  <div class="card b"><h3>Decode: "token generation"</h3><p>Memory-intensive: one token per sequence per step. Sets TPOT (time per output token).</p></div>
</div>

<div class="cite">Splitwise describes these as a compute-intensive prompt phase and a memory-intensive token-generation phase.</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Colocation forces compromises

::: cards grid3
### [d] Interference
A new prompt's prefill shares iterations with ongoing decodes and slows them, or waits behind them (deck 04).

### [b] One configuration for two jobs
The best parallelism and batch size for prefill and for decode differ, but colocation forces a single choice.

### [c] Coupled scaling
You can't add prefill capacity without also adding decode capacity, even if only one is short.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Remove the interference

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? What removes prefill-decode interference entirely while letting each phase be configured separately?
- [ ] A bigger token budget
- [x] Run prefill and decode on different GPUs and transfer the KV cache between them
- [ ] Use only one phase
- [ ] Quantize harder
> <b>B.</b> DistServe "assigns prefill and decoding computation to different GPUs", and Splitwise runs the phases on separate machines, transferring state over the cluster interconnect. Each pool is then tuned for its own SLO.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Prefill pool → KV transfer → decode pool

<div class="visual"><svg id="dSvg" viewBox="0 0 660 150" role="img" aria-label="Disaggregated serving pipeline"></svg></div>

<div class="grid3" style="margin-top:12px">
  <div class="card a"><h3>Prefill pool</h3><p>Sized and parallelized for TTFT, batching prompts for compute efficiency.</p></div>
  <div class="card c"><h3>KV transfer</h3><p>The prompt's KV cache moves to a decode GPU. Placement and interconnect bandwidth decide how much this costs.</p></div>
  <div class="card b"><h3>Decode pool</h3><p>Sized for TPOT and KV capacity, running large continuous batches.</p></div>
</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## What does moving the KV cost?

<div class="visual">
  <div class="controls" style="margin-top:0">
    <select id="xM"><option value="131072">8B-shaped (128 KB/token)</option><option value="327680" selected>70B-shaped (320 KB/token)</option></select>
    <label class="ctl">Prompt tokens <input type="range" id="xP" min="9" max="17" step="0.5" value="12"> <output id="xPo"></output></label>
    <div class="seg" id="xL"><button data-v="450" class="on">NVLink 450 GB/s</button><button data-v="50">400G NIC 50 GB/s</button><button data-v="400">8× NICs 400 GB/s</button></div>
  </div>
  <div class="grid3" style="margin-top:14px">
    <div class="stat"><div class="num" id="xB"></div><div class="lbl">KV to transfer</div></div>
    <div class="stat"><div class="num" id="xT" style="color:var(--c)"></div><div class="lbl">transfer time (bandwidth only)</div></div>
    <div class="stat"><div class="num" id="xF"></div><div class="lbl">vs prefill at 20K tok/s (illustrative)</div></div>
  </div>
</div>

<p class="caption">KV bytes = prompt × per-token KV (BF16 (bfloat16, a 16-bit floating-point format with the exponent range of 32-bit floats)). Transfer can be overlapped layer by layer with prefill. This is a bandwidth estimate, not a measured system.</p>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works, and what it costs

::: cards grid2
### [e] No interference
Long prompts never stall decode iterations, and decode batches never slow prefill.

### [a] Independent tuning
Each pool picks its own parallelism, batch size and GPU count for its own SLO, so goodput goes up.

### [b] Measured
DistServe: <b>7.4×</b> more requests or <b>12.6×</b> tighter SLOs. Splitwise: <b>1.4×</b> throughput at <b>20%</b> lower cost, or <b>2.35×</b> throughput at the same cost and power.

### [d] Cost
KV transfer needs fast interconnect and smart placement, and the pools add operational complexity.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Disaggregation is always better than chunked prefill."
> It adds KV transfer and operational complexity. Chunked prefill (deck 04) also reduces interference on shared GPUs. Which wins depends on workload, scale and interconnect.
:::

::: reveal myth
? "Prefill and decode pools must use the same hardware."
> Splitwise explicitly provisions <b>different machines</b> for each phase, and heterogeneous pools are part of the appeal.
:::

::: reveal myth
? "The KV transfer is negligible."
> For long prompts on large models it is gigabytes per request. It needs NVLink/RDMA-class (RDMA = remote direct memory access) links or overlapping with prefill.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? What does DistServe optimize?
- [ ] Peak FLOPs
- [x] Goodput under TTFT and TPOT SLOs
- [ ] Model size
- [ ] Tokens per watt only
> <b>Goodput</b>: requests served within the TTFT and TPOT SLOs.
:::

<div class="quiz ">
  <p class="qq">Roughly how much KV must move for a 4,096-token prompt on a 70B-shaped model (320 KB/token, BF16)?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">4,096 × 320 KB ≈ <b>1.34 GB</b>, about 3 ms over NVLink at 450 GB/s, or about 27 ms over a single 50 GB/s NIC.</div>
</div>

<div class="quiz">
  <p class="qq">What did Splitwise report at the same cost and power budget?</p>
  <div class="opts">
  <button>A. 1.1×</button>
  <button data-ok>B. 2.35× throughput</button>
  <button>C. 7.4× requests</button>
  <button>D. 36.9×</button>
  </div>
  <div class="why"><b>2.35×</b> more throughput.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Disaggregated serving runs prefill and decode on separate, separately tuned GPU pools and moves the KV cache between them. That removes interference and raises goodput, at the price of fast KV transfer.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Prefill is compute-bound and decode is memory-bound, and sharing GPUs makes them interfere and forces one configuration onto both. DistServe and Splitwise run the phases on different machines: the prefill pool computes the prompt and its KV cache, the KV moves over a fast interconnect, and the decode pool streams tokens. Each pool is sized for its own SLO. DistServe reported 7.4× more requests or 12.6× tighter SLOs, and Splitwise 1.4× throughput at 20% lower cost. The cost is gigabytes of KV transfer for long prompts.</p></div>

<div class="recap"><div><span><b>Problem:</b> prefill and decode interfere and want different configurations.</span></div><div><span><b>Core idea:</b> separate pools plus KV transfer, each pool tuned for goodput.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/06_chunked_prefill.ipynb" target="_blank" rel="noopener">06 · Chunked prefill with a token budget</a> <span style="color:var(--faint)">· 40 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/inference/06_chunked_prefill.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/04_kv_memory_calculator.ipynb" target="_blank" rel="noopener">04 · KV-cache memory calculator</a> <span style="color:var(--faint)">· 20 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/inference/04_kv_memory_calculator.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../12-moe-serving/index.html">12 · Serving large MoE models →</a> · Previous: <a href="../08-parallelism/index.html">← 08 · Parallelism for inference</a> · <a href="../index.html">All decks</a></p>

<!-- slide id="s-papers" from="papers" -->
