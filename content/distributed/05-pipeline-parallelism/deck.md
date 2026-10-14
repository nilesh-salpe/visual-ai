---
title: Pipeline Parallelism
body:
  data-deck: Pipeline parallelism
  data-home: ../index.html
  data-home-label: Distributed
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'stage 1 :: layers 1–k :: a'
  - 'stage 2 :: layers k+1–2k :: c'
  - '… :: … :: f'
  - 'stage p :: last layers + loss :: b'
  caption: Activations flow forward, gradients flow back; micro-batches keep every stage busy except while the pipeline fills and drains.
example:
  title: 'Worked example: bubbles for an 8-stage pipeline'
  setup: p = 8 stages; bubble fraction = (p − 1)/m of the ideal time, or (p − 1)/(v·m) with v interleaved chunks per GPU (Megatron; also quoted by Llama 3).
  steps:
  - 'm = 8 micro-batches: (8 − 1)/8 = <b>87.5%</b> extra time.'
  - 'm = 32: <b>21.9%</b>.'
  - 'm = 32 with v = 4 interleaved chunks: 7 / (4 × 32) = <b>5.5%</b>.'
  - GPipe holds activations for all 32 micro-batches at once; 1F1B holds at most p = 8 on the first stage (notebook 04 simulates both).
  result: Many micro-batches and interleaving shrink the bubble; 1F1B keeps the memory bounded while doing so.
traps:
  tricks:
  - 'Bubble = (p − 1)/m. :: Interleaved: (p − 1)/(v·m).'
  - 'GPipe guideline: m ≥ 4p. :: Bubble becomes negligible.'
  - '1F1B memory ≤ p micro-batches. :: Instead of m with GPipe.'
  traps:
  - 'Unbalanced stages. :: The slowest stage sets the pace; embeddings and the loss layer make first and last stages heavy (Llama 3 removes a layer from each).'
  - 'Too few micro-batches. :: A small global batch with deep pipelines wastes most of the time in bubbles.'
  - 'Forgetting point-to-point latency. :: Interleaving multiplies the number of sends by v.'
papers:
- gpipe
- pipedream
- megatron21
- zerobubble
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Distributed Training · 05</div>
    <h1>Pipeline parallelism</h1>
    <p class="sub">Split the layers into stages on different GPUs and stream micro-batches through them: GPipe, 1F1B, interleaved and zero-bubble schedules, and the bubble they all fight.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>A model too deep for one node can be cut into stages, but a single batch flowing through stages leaves every GPU idle most of the time.</div>
      <div class="c"><b>Core idea</b>Split the batch into <b>m micro-batches</b> so stages work on different micro-batches at once. The fill-and-drain <b>bubble</b> costs (p − 1)/m of the ideal time; <b>1F1B</b> bounds activation memory, <b>interleaving</b> divides the bubble by v, and <b>zero-bubble</b> schedules fill the remaining gaps.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## One batch through four stages

Without micro-batching, stage 2 waits for stage 1, and so on: only one GPU works at a time. Switch schedules and watch the idle time (grey).
{: .lede}

<div class="visual">
  <div class="seg" id="pSeg"><button data-v="naive">1 batch</button><button data-v="gpipe" class="on">GPipe</button><button data-v="1f1b">1F1B</button></div>
  <div class="controls"><label class="ctl">stages p <input type="range" id="pP" min="2" max="8" step="1" value="4"> <output id="pPo"></output></label><label class="ctl">micro-batches m <input type="range" id="pM" min="1" max="16" step="1" value="8"> <output id="pMo"></output></label></div>
  <svg id="pSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Pipeline schedule"></svg>
  <p class="readout" id="pOut"></p>
</div>
<p class="caption">Forward = 1 time unit (teal), backward = 2 units (orange). The simulator follows the same dependency rules as notebook 04.</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## The costs of splitting by layers

::: cards grid3
### [d] Fill and drain
The first stage waits for nothing at the start but everything at the end; the last stage the reverse. That idle time is the bubble.

### [b] Activation memory
Each stage keeps activations of every in-flight micro-batch until its backward pass.

### [c] Balance
Stages must take equal time; uneven layers or the loss computation make one stage the bottleneck.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Shrink the bubble

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? With p = 8 stages, how can you cut the bubble from 87.5% to under 6%?
- [ ] Use fewer GPUs
- [x] Use m = 32 micro-batches with 4 interleaved chunks per GPU
- [ ] Make the batch smaller
- [ ] Remove the backward pass
> <b>B.</b> Bubble = (p − 1)/(v·m) = 7/(4 × 32) ≈ 5.5%. More micro-batches and interleaved chunks both shrink it.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Four schedules

::: cards grid2
### [a] GPipe
All forwards, then all backwards. Bubble (p−1)/m; must store activations for all m micro-batches.

### [c] 1F1B (PipeDream)
After a short warm-up, alternate one forward and one backward. Same bubble, but at most p micro-batches in flight.

### [b] Interleaved 1F1B (Megatron)
Each GPU holds v non-adjacent chunks of layers; the bubble shrinks to (p−1)/(v·m) at the cost of more sends.

### [e] Zero bubble
Split backward into input-gradient and weight-gradient parts and schedule the weight part into the gaps: up to 23% faster than 1F1B.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Bubble vs micro-batches

Bubble fraction (p − 1)/(v·m) for a pipeline of p stages. The dashed line is 10%.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">stages p <input type="range" id="bP" min="2" max="32" step="1" value="16"> <output id="bPo"></output></label><div class="seg" id="bV"><button data-v="1" class="on">v = 1</button><button data-v="2">v = 2</button><button data-v="4">v = 4</button></div></div>
  <svg id="bSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Bubble fraction"></svg>
</div>

::: deep Llama 3's pipeline
Llama 3 405B used 16 pipeline stages with an interleaved schedule, removed one transformer layer from the first and last stages (which also hold the embedding and the loss), and used asynchronous point-to-point communication to handle imbalance from document masks.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why pipelines are worth it

::: cards grid2
### [a] Little communication
Only activations at stage boundaries move, point to point, so pipelines work across nodes over the network.

### [e] Memory per GPU ÷ p
Each GPU stores only its stages' weights and optimizer state.

### [d] The price is the bubble
It needs many micro-batches, which needs a large enough global batch.

### [b] Combines with TP and DP
Typical: TP inside the node, PP across a few nodes, DP outermost (Megatron PTD-P: 52% of peak on 3,072 GPUs).
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "1F1B removes the bubble."
> It has the same bubble as GPipe; it reduces activation memory.
:::

::: reveal myth
? "More stages always help."
> More stages increase the bubble ((p−1)/m) unless micro-batches grow too.
:::

::: reveal myth
? "Pipelines change the gradient."
> With synchronous flushes (GPipe, 1F1B) gradients are exactly those of the full batch.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Bubble fraction with p = 4 and m = 12 (no interleaving)?
- [ ] 4%
- [x] 25%
- [ ] 33%
- [ ] 75%
> (4 − 1)/12 = <b>25%</b>.
:::

::: reveal
? What does 1F1B improve over GPipe, and what does it not?
> It bounds in-flight activations to about p micro-batches instead of m; the bubble is unchanged.
:::

::: reveal
? Why is pipeline parallelism usually placed across nodes rather than tensor parallelism?
> It only sends activations between neighbouring stages once per micro-batch, far less traffic than TP's per-layer all-reduces.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Pipeline parallelism splits the layers into stages and streams micro-batches through them; the bubble (p−1)/(v·m) and activation memory decide the schedule.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Pipeline parallelism gives each GPU a contiguous block of layers. One batch would leave every stage idle while others work, so the batch is split into micro-batches that flow through the stages at once. The remaining idle time while the pipeline fills and drains is the bubble, (p minus 1) over m of the ideal time. GPipe runs all forwards then all backwards and stores every micro-batch's activations; 1F1B alternates forwards and backwards to bound memory; interleaved schedules give each GPU several chunks and divide the bubble by v; zero-bubble schedules fill the gaps with weight-gradient work. Because only boundary activations move, pipelines work well across nodes.</p></div>
    <div class="recap"><div><span><b>Problem:</b> deep models across nodes; naive staging leaves GPUs idle.</span></div><div><span><b>Core idea:</b> micro-batches; bubble (p−1)/(v·m); 1F1B bounds memory.</span></div><div><span><b>Practice:</b> balance stages; many micro-batches; interleave or zero-bubble.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/distributed/04_pipeline_schedules.ipynb" target="_blank" rel="noopener">04 · Pipeline schedules: GPipe vs 1F1B</a> <span style="color:var(--faint)">· 45 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/distributed/04_pipeline_schedules.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../06-context-parallelism/index.html">06 · Context parallelism →</a> · Previous: <a href="../04-tensor-sequence-parallelism/index.html">← 04</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
