---
title: Expert Parallelism
body:
  data-deck: Expert parallelism
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
  - 'tokens on GPU r :: after attention :: f'
  - 'router :: top-k experts per token :: c'
  - 'all-to-all dispatch :: tokens → expert GPUs :: b'
  - 'expert FFNs :: local compute :: a'
  - 'all-to-all combine :: results → home GPU :: e'
  caption: Two all-to-alls per MoE layer in forward, two more in backward.
example:
  title: 'Worked example: DeepSeek-V3''s dispatch traffic'
  setup: 'DeepSeek-V3: hidden size 7,168, 8 routed experts per token (of 256), 64-way expert parallelism across 8 nodes, dispatch in FP8 (1 byte). Take 8,192 tokens
    on one GPU.'
  steps:
  - 'Each token is sent to up to 8 experts: 8,192 × 8 × 7,168 bytes = <b>448 MiB</b> dispatched per GPU per MoE layer (forward).'
  - 'Combine sends the expert outputs back: a similar amount again (BF16 in DeepSeek-V3, so about twice the bytes).'
  - DeepSeek-V3 limits each token to at most 4 nodes, so most of this rides NVLink inside a node and less crosses InfiniBand (IB).
  - DualPipe overlaps this all-to-all with compute in the forward and backward passes.
  result: 'MoE trades FLOPs for communication: every MoE layer moves each token''s hidden state to its experts and back.'
traps:
  tricks:
  - 'All-to-all volume ≈ tokens × k × hidden × bytes. :: Per direction, per MoE layer.'
  - 'Limit node fan-out. :: DeepSeek-V3: at most 4 nodes per token.'
  - 'Overlap all-to-all. :: DualPipe overlaps it with computation of another micro-batch.'
  traps:
  - 'Imbalanced routing. :: The busiest GPU sets the step time for everyone.'
  - 'Assuming all-reduce-like scaling. :: All-to-all cost grows with participants and is latency-sensitive.'
  - 'Ignoring expert memory. :: All experts'' weights and optimizer states must live somewhere.'
papers:
- gshard
- switch
- dsv3
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Distributed Training · 07</div>
    <h1>Expert parallelism</h1>
    <p class="sub">Training Mixture-of-Experts models by placing experts on different GPUs: the all-to-all dispatch, load imbalance, and how DeepSeek-V3 limits cross-node traffic.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>An MoE layer with hundreds of experts can't live on one GPU, but tokens must reach whichever experts the router picks, wherever they live.</div>
      <div class="c"><b>Core idea</b>Place different experts on different GPUs (<b>expert parallelism</b>, EP). Each MoE layer does an <b>all-to-all dispatch</b> (send tokens to their experts), local expert compute, and an <b>all-to-all combine</b> (send results back). Balance routing and limit how many nodes each token touches.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Tokens must travel to their experts

4 GPUs, each hosting 2 of 8 experts. Each token's router picks top-2 experts; arrows show where tokens are sent. Drag the imbalance to see how one hot expert slows everyone.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">routing imbalance <input type="range" id="eI" min="0" max="2" step="0.1" value="0.5"> <output id="eIo"></output></label></div>
  <div id="eBars" style="margin-top:12px"></div>
  <p class="readout" id="eOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why other axes don't fit MoE well

::: cards grid3
### [d] Too many experts per GPU
DeepSeek-V3 has 256 routed experts per layer; replicating them all on every GPU would waste memory.

### [b] Data parallelism replicates experts
Each copy would also get only a fraction of the tokens per expert, making expert matmuls tiny.

### [c] Tensor parallelism splits small matrices
Each expert FFN is relatively small (hidden 2,048 in DeepSeek-V3); splitting it further makes it inefficient.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What is the bottleneck?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? In expert parallelism with an all-to-all dispatch, which GPU determines how long the MoE layer takes?
- [ ] The fastest one
- [ ] The average one
- [x] The one hosting the most-loaded experts
- [ ] The router
> <b>C.</b> Every GPU waits for the combine all-to-all, which waits for the busiest experts. That is why load balance matters for speed, not only quality.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Dispatch, compute, combine

::: cards grid3
### [a] Dispatch (all-to-all)
Each GPU sends each token's hidden state to the GPUs hosting its chosen experts.

### [c] Expert compute
Each GPU runs its experts on all tokens it received, as dense, efficient matmuls.

### [e] Combine (all-to-all)
Results go back to each token's home GPU and are weighted by the router; the residual stream continues.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## How DeepSeek-V3 makes it practical

::: cards grid2
### [a] Bounded fan-out
Each token goes to at most 4 nodes, cutting InfiniBand traffic; within a node, NVLink carries the rest.

### [b] DualPipe
A pipeline schedule that overlaps forward and backward computation with the all-to-all communication of other micro-batches.

### [c] Custom kernels
Cross-node all-to-all kernels that use IB and NVLink bandwidth fully while dedicating few SMs (streaming multiprocessors) to communication.

### [e] FP8 dispatch
Activations are dispatched in FP8 to halve the bytes moved; 16-way PP, 64-way EP across 8 nodes and ZeRO-1 DP on 2,048 H800s.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why expert parallelism works

::: cards grid2
### [a] Experts are independent
Each expert only needs its own tokens, so placing experts on different GPUs adds no compute coupling.

### [e] Big matmuls per expert
Gathering every token routed to an expert from all GPUs keeps its matmuls large and efficient.

### [d] Communication heavy
Two all-to-alls per layer forward and two backward; latency- and imbalance-sensitive.

### [b] Proven at scale
GShard: 600B+ parameters on 2,048 TPU v3 in 4 days; DeepSeek-V3: 671B parameters in 2.788M H800 GPU-hours.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "EP is like data parallelism for experts."
> DP replicates; EP partitions experts, and tokens must be moved to them with all-to-all.
:::

::: reveal myth
? "MoE layers are cheap to train because few parameters are active."
> FLOPs per token are low, but the all-to-all traffic and imbalance can dominate step time.
:::

::: reveal myth
? "All-to-all scales like all-reduce."
> Each GPU exchanges data with many peers; latency and the busiest link matter, not just total bytes.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? How many all-to-all operations does one MoE layer need in the forward pass?
- [ ] 0
- [ ] 1
- [x] 2
- [ ] 4
> <b>2</b>: dispatch and combine.
:::

::: reveal
? Why does load balance affect speed in expert parallelism?
> The combine waits for the GPU with the most routed tokens; an overloaded expert slows the whole layer for every GPU.
:::

::: reveal
? Name two techniques DeepSeek-V3 uses to tame all-to-all costs.
> At most 4 nodes per token; DualPipe overlap; custom all-to-all kernels; FP8 dispatch.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Expert parallelism places MoE experts on different GPUs and moves tokens to them with two all-to-alls per layer; balance and overlap decide its speed.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>A Mixture-of-Experts layer has too many experts for one GPU, so expert parallelism spreads them across GPUs. In every MoE layer, an all-to-all dispatch sends each token's hidden state to the GPUs hosting its chosen experts, those GPUs run their experts as dense matmuls, and an all-to-all combine sends the results back. The busiest GPU sets the pace, so routing must be balanced. DeepSeek-V3 makes this practical with 64-way expert parallelism, a limit of four nodes per token, FP8 dispatch, custom kernels and the DualPipe schedule that hides communication behind computation.</p></div>
    <div class="recap"><div><span><b>Problem:</b> hundreds of experts; tokens must reach them anywhere.</span></div><div><span><b>Core idea:</b> partition experts; all-to-all dispatch and combine.</span></div><div><span><b>Practice:</b> balance load, limit fan-out, overlap communication.</span></div></div>
    <p class="start-hint">Next: <a href="../08-activation-memory/index.html">08 · Activation memory and recomputation →</a> · Previous: <a href="../06-context-parallelism/index.html">← 06</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
