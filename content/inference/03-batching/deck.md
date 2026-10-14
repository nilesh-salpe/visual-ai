---
title: Continuous Batching
body:
  data-deck: Batching
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
  - 'waiting queue :: new requests :: f'
  - 'admit :: if a slot and KV memory are free :: a'
  - 'one decode step :: whole batch together :: b'
  - 'evict finished :: free slot and KV now :: e'
  loop: '3 -> 1 :: every iteration: the batch is recomposed'
  caption: Scheduling happens per iteration (one decode step), not per batch.
example:
  title: 'Worked example: slots wasted by static batching'
  setup: Four requests start together and need 10, 20, 50, 200 output tokens.
  steps:
  - 'Static batching keeps the batch together until the longest finishes: 4 slots × 200 steps = <b>800 slot-steps</b> reserved.'
  - Useful work is only 10 + 20 + 50 + 200 = <b>280 slot-steps</b>.
  - Utilization = 280 / 800 = <b>35%</b>; the three short requests also wait for the batch to finish before being returned.
  - Continuous batching refills each slot the iteration after it frees, so with a queue of waiting requests the slots stay ~100% busy.
  result: 'Same hardware, same model: in this example continuous batching does up to <b>2.9×</b> more useful work per step, and short requests return as soon as they
    finish.'
traps:
  tricks:
  - 'Granularity = one decode step. :: Join and leave between iterations; never wait for the batch to drain.'
  - 'Selective batching. :: Batch the matmuls across requests; run attention per request, because each has its own KV length.'
  - 'Throughput ∝ batch while memory-bound. :: Adding sequences reuses the same weight read until compute becomes the limit.'
  traps:
  - 'Padding to the longest sequence. :: Wastes compute and memory; continuous batching with paged KV avoids it.'
  - 'Ignoring KV memory. :: Batch size is capped by free KV memory, not only by a configured maximum; engines preempt when it runs out.'
  - 'Assuming bigger batch is always better. :: TPOT rises with batch; past the SLO, more batch adds no goodput.'
papers:
- orca
- vllm
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">LLM Inference &amp; Serving · 03</div>
    <h1>Continuous batching</h1>
    <p class="sub">Iteration-level scheduling (Orca, OSDI 2022): admit and retire requests at every decode step instead of running fixed batches to completion.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Decode at batch 1 wastes the GPU (graphics processing unit). Static batches, though, hold every slot until the longest request finishes, and new arrivals have to wait.</div>
      <div class="c"><b>Core idea</b>Schedule at the granularity of <b>one iteration</b>: finished requests leave and waiting requests join between every decode step.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## One sequence at a time leaves the GPU idle

A decode step reads all the weights to produce one token per sequence. With one sequence, that read serves one token. Batching lets the same read serve many sequences, which is why servers batch.
{: .lede}

<div class="takeaway">Batching is how decode gets from memory-bound toward compute-bound (GPU deck 02, the roofline).</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Static batching wastes slots and makes requests wait

Static (request-level) batching groups requests and runs the group until its <b>longest</b> member finishes. Short requests sit idle in their slots, and new arrivals can't join a running batch.
{: .lede}

::: cards grid2
### [d] Finished but still occupying a slot
Requests produce different numbers of tokens. Early finishers can't be replaced until the whole batch ends.

### [b] Queueing delay
A request arriving just after a batch starts waits for the whole batch to finish.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Choose the scheduling granularity

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? At what granularity should the scheduler decide which requests run?
- [ ] Per request: run each batch to completion
- [x] Per iteration: re-decide at every decode step
- [ ] Once per minute
- [ ] Per layer
> <b>B.</b> Orca's <b>iteration-level scheduling</b> re-forms the batch at every model iteration. A request that finishes returns immediately and a waiting request takes its slot on the next step.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Iteration-level scheduling + selective batching

::: cards grid2
### [a] Iteration-level scheduling
Between every decode iteration, retire finished sequences and admit new ones, up to the batch or memory limit.

### [c] Selective batching
Requests at different positions have different lengths. Orca batches the operations that don't depend on length (the linear layers) and handles attention per request.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Static vs continuous, simulated

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">Max batch <input type="range" id="cbB" min="2" max="8" step="1" value="4"> <output id="cbBo"></output></label>
    <button class="btn" id="cbNew">New requests</button>
  </div>
  <div class="grid2" style="margin-top:10px">
    <div><h3>Static batching</h3><svg id="stSvg" viewBox="0 0 320 200" role="img" aria-label="Static batching slots"></svg><p class="readout" id="stOut"></p></div>
    <div><h3>Continuous batching</h3><svg id="ctSvg" viewBox="0 0 320 200" role="img" aria-label="Continuous batching slots"></svg><p class="readout" id="ctOut"></p></div>
  </div>
  <div class="legend"><span><i style="background:var(--a)"></i>generating tokens</span><span><i style="background:var(--d-soft);border:1px solid var(--d)"></i>slot held but idle (static)</span></div>
</div>

<p class="caption">Each row is a batch slot over time; each coloured bar is one request. The simulation uses the same rules as Build-it notebook 05.</p>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works

::: cards grid2
### [e] No idle slots
A slot is refilled on the very next iteration, so the batch stays full whenever requests are waiting.

### [a] Less queueing
New requests start within one iteration instead of waiting for a batch to drain.

### [b] Measured
On GPT-3 175B, Orca reported a <b>36.9×</b> throughput improvement over NVIDIA FasterTransformer at the same latency.

### [c] Foundation for what follows
Paged KV (05) and chunked prefill (04) both build on per-iteration scheduling.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Continuous batching just means a bigger batch."
> The batch size limit can be the same. What changes is <b>when</b> membership changes: at every iteration rather than per batch.
:::

::: reveal myth
? "Batched requests must have the same length."
> Iteration-level scheduling mixes requests at different positions. Orca's selective batching handles the length-dependent attention part.
:::

::: reveal myth
? "Batching always increases user latency."
> Each step gets a little slower, but removing queueing usually <b>lowers</b> end-to-end latency, as the simulation shows.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? What problem of static batching does iteration-level scheduling fix?
- [ ] Too much KV memory
- [x] Slots held by finished requests and new requests waiting
- [ ] Low prefill speed
- [ ] Quantization error
> Finished requests <b>free their slots immediately</b> and new ones join at the next iteration.
:::

<div class="quiz">
  <p class="qq">What did Orca report on GPT-3 175B versus FasterTransformer at the same latency?</p>
  <div class="opts">
  <button>A. 2×</button>
  <button>B. 5.6×</button>
  <button data-ok>C. 36.9×</button>
  <button>D. 100×</button>
  </div>
  <div class="why"><b>36.9×</b> throughput (Orca, OSDI '22).</div>
</div>

<div class="quiz ">
  <p class="qq">Why does continuous batching need careful memory management?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Requests join and leave constantly, with KV caches of unpredictable length. That calls for dynamic allocation, which PagedAttention provides (deck 05).</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Continuous batching re-forms the batch at every decode iteration: finished requests leave and new ones join immediately, so slots never sit idle.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Decode needs batching to use the GPU, but static batching runs each batch until its longest request finishes, wasting slots and making new requests wait. Orca introduced iteration-level scheduling: the server re-decides the batch between every decode step, with selective batching for the length-dependent attention. It reported 36.9× throughput over FasterTransformer at the same latency on GPT-3 175B, and it's now standard in LLM (large language model) servers.</p></div>

<div class="recap"><div><span><b>Problem:</b> static batches hold finished requests' slots and make new arrivals wait.</span></div><div><span><b>Core idea:</b> iteration-level scheduling: admit and retire requests at every decode step.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/05_continuous_batching.ipynb" target="_blank" rel="noopener">05 · Continuous (iteration-level) batching</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/inference/05_continuous_batching.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../04-chunked-prefill/index.html">04 · Chunked prefill →</a> · Previous: <a href="../02-kv-cache/index.html">← 02</a> · <a href="../index.html">All decks</a></p>

<!-- slide id="s-papers" from="papers" -->
