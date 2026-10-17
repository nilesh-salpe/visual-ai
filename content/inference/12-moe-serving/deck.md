---
title: Serving Large MoE Models
body:
  data-deck: Serving large MoE models
  data-home: ../index.html
  data-home-label: Inference
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
- ../../shared/diagram.js
papers:
- dsv3
- ds_infer
- deepep
- eplb
- vllm_ep
- sglang_ep
- gshard
- mixtral
status:
  label: current
  reviewed: '2026-10-16'
  note: Checked against DeepSeek's V3 report and inference-system write-up, DeepEP, the EP load balancer, vLLM v0.31.0 and SGLang docs (2026-10-16).
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Short answer">
  <div class="inner">
    <div class="kicker">LLM Inference &amp; Serving · 12</div>
    <h1>Serving large Mixture-of-Experts models</h1>
    <p class="sub">How models like DeepSeek-V3 (671B parameters, 37B active) are served across dozens to hundreds of GPUs: data-parallel attention, wide expert parallelism, all-to-all dispatch and combine, redundant experts for load balance, and overlapping communication with computation.</p>
    <div class="ps">
      <div class="p"><b>The question</b>How would you serve a 671B-parameter MoE model with high throughput and low latency?</div>
      <div class="c"><b>Short answer</b>Split by layer type. Attention runs <b>data-parallel</b>: each GPU serves its own requests and keeps their KV cache. Experts are spread across <b>many GPUs</b> (wide expert parallelism), so each GPU stores only a few experts and each expert receives a large batch. Tokens reach their experts and return through <b>two all-to-alls per MoE layer</b>, hidden by overlapping <b>two micro-batches</b>. <b>Copy the busiest experts</b> to balance load, and run prefill and decode as separate units, with decode spread wider.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-draw" chapter="Draw it" tag="1 · Draw it" tagclass="b5" -->
## The picture to draw

::: diagram 660x280
nodes:
  rq: {at: [10, 125, 90, 56], text: Requests, sub: router, color: f, step: 1}
  pf: {at: [135, 30, 175, 60], text: Prefill unit, sub: DP attention · EP32 · 32 GPUs, color: c, step: 2}
  dc: {at: [135, 200, 175, 60], text: Decode unit, sub: DP attention · EP144 · 144 GPUs, color: a, step: 3}
  lb: {at: [355, 25, 295, 50], text: Expert load balancer, sub: 'copy hot experts, re-place about every 10 min', color: d, step: 6}
  ov: {at: [355, 115, 295, 50], text: Two micro-batches, sub: one computes while the other communicates, color: e, step: 5}
  ml: {at: [355, 205, 295, 50], text: Every MoE layer, sub: dispatch (all-to-all) → experts → combine, color: b, step: 4}
edges:
  - {from: rq, to: pf, step: 2}
  - {from: pf, to: dc, label: KV cache, step: 3}
  - {from: dc, to: ml, step: 4}
  - {from: ml, to: ov, step: 5, style: dash}
  - {from: lb, to: pf, label: placement, step: 6, style: dash}
steps:
  - Requests arrive at a router that balances them across data-parallel attention ranks.
  - 'Prefill runs on its own unit: 4 nodes, attention data-parallel, the 256 routed experts plus 32 redundant copies spread over 32 GPUs (9 per GPU).'
  - 'The KV cache moves to a decode unit: 18 nodes, experts spread over 144 GPUs (2 routed experts and the shared expert per GPU). Decode needs the wider spread to give each expert enough tokens.'
  - 'Inside every MoE layer, each token is sent to the GPUs holding its 8 chosen experts (dispatch), processed, and sent back (combine): two all-to-alls per layer.'
  - The batch is split into two micro-batches so one computes while the other communicates.
  - An expert load balancer copies the busiest experts and re-places them using recent load statistics.
:::

The layouts are from DeepSeek's February 2025 inference-system write-up. Its V3 technical report describes a larger decode unit, 40 nodes with experts over 320 GPUs (one expert per GPU, 64 GPUs for redundant and shared experts): the deployment changed, and both are valid answers when you say which.

<!-- slide id="s-how" chapter="How it works" tag="2 · How it works" tagclass="b4" -->
## One MoE layer, step by step <span class="ill">animation</span>

<div class="visual"><div class="seg" id="moeSeg"><button data-v="off" class="on">Without expert copies</button><button data-v="on">With copies of the hot expert</button></div><svg id="moeSvg" class="anim-lg" viewBox="0 0 660 330" role="img" aria-label="Tokens on four GPUs travel to their experts and back; load bars show the busiest GPU"></svg><p class="readout" id="moeOut"></p></div>

Simplified: each token picks one expert here; DeepSeek-V3 picks 8 of 256 routed experts plus a shared expert, and limits each token to experts on at most 4 nodes in training.

<!-- slide id="s-numbers" chapter="Numbers" tag="3 · Numbers to know" tagclass="b6" -->
## Numbers to know <span class="ill">calculator</span>

<div class="visual"><div class="controls"><label class="ctl">expert parallel size <input type="range" id="nEP" min="0" max="7" step="1" value="5"> <output id="nEPo"></output></label><label class="ctl">decode sequences per GPU <input type="range" id="nB" min="1" max="256" step="1" value="64"> <output id="nBo"></output></label><label class="ctl">redundant expert copies <input type="range" id="nR" min="0" max="64" step="8" value="32"> <output id="nRo"></output></label></div><div class="bars"><div id="nBars"></div></div><p class="readout" id="nOut"></p></div>

::: cards grid2
### [a] DeepSeek-V3 shape
256 routed experts + 1 shared per MoE layer, 8 routed chosen per token, 58 MoE layers of 61; 671B parameters, 37B active.

### [c] One expert ≈ 2.55 GB
3 × 7,168 × 2,048 weights per layer × 58 layers ≈ 2.55B parameters, 2.55 GB in FP8. All routed experts: about 654 GB.

### [b] Tokens per expert
tokens per step × 8 ÷ expert instances. Wide EP multiplies the tokens per step: with b sequences on each of EP GPUs, each instance sees b · EP · 8 ÷ (256 + copies).

### [e] Measured throughput
DeepSeek (H800): about 73.7K input tokens/s per node in prefill and 14.8K output tokens/s per node in decode. SGLang (96 H100s): 52.3K and 22.3K per node for 2K-token inputs.
:::

Roofline: with FP8 weights an expert matmul does about 2 FLOPs per weight byte per token, so it reaches H100 FP8 peak (1,979 TFLOP/s over 3.35 TB/s) only with roughly 300 tokens per expert. Attention and communication time are not modelled.

<!-- slide id="s-trade" chapter="Trade-offs" tag="4 · Trade-offs" tagclass="b2" -->
## Trade-offs

::: table
| Choice | Gains | Costs |
|---|---|---|
| Tensor-parallel experts (vLLM's default without `--enable-expert-parallel`) | simple; works on one node | every GPU computes a slice of every expert; small matmuls and all-reduces |
| Expert parallelism, one node (EP 8) | whole experts local; no cross-node traffic | all routed experts must fit in 8 GPUs (about 654 GB for DeepSeek-V3: H200-class); few tokens per expert |
| Wide expert parallelism (EP 32 to 320) | large batch per expert, few experts per GPU, more KV memory free | all-to-all across nodes on every layer; a larger failure domain; needs RDMA kernels (DeepEP) |
| Data-parallel attention | each GPU keeps its requests' KV cache; no KV duplication for MLA | ranks must step together, so idle ranks run dummy passes |
| Redundant experts | balances hot experts; can cut cross-node traffic | extra memory; re-placement moves weights |
| Two micro-batch overlap | hides much of the all-to-all time | needs enough batch to split; more complex scheduling |
:::

<!-- slide id="s-follow" chapter="Follow-ups" tag="5 · Follow-ups" tagclass="b3" -->
## Follow-ups

::: reveal
? <span class="lvl lvl-basic">Basic</span> Why not just tensor-parallelise the experts?
> Every GPU would hold a slice of every expert, so each matmul shrinks and each layer needs an all-reduce. Expert parallelism keeps whole experts local and batches all of an expert's tokens together. SGLang measured 5.2× higher decode throughput with EP 72 than a TP 16 baseline, mostly from 4× larger batches.
:::

::: reveal
? <span class="lvl lvl-basic">Basic</span> MoE activates only 37B of 671B parameters. Why is it still expensive to serve?
> All 671B parameters must sit in GPU memory, and each step reads the weights of every expert that any token chose. Cheap compute per token does not mean cheap memory.
:::

::: reveal
? <span class="lvl lvl-deeper">Deeper</span> Why does decode use a wider expert parallelism than prefill?
> A decode step produces one token per sequence, so a GPU contributes few tokens; gathering tokens from many GPUs gives each expert a useful batch. Prefill already has thousands of tokens per request. DeepSeek: EP 32 for prefill, EP 144 for decode (EP 320 in its V3 report).
:::

::: reveal
? <span class="lvl lvl-deeper">Deeper</span> One expert gets far more tokens than the rest. What happens and what do you do?
> Its GPU becomes the straggler and every other GPU waits each layer. Copy hot experts onto other GPUs and re-place them from recent load statistics: DeepSeek re-places about every 10 minutes; vLLM's --enable-eplb rebalances every 3,000 engine steps over a 1,000-step window by default.
:::

::: reveal
? <span class="lvl lvl-expert">Expert</span> How do you hide the all-to-all communication?
> Split the batch into two micro-batches and alternate: one runs attention and experts while the other dispatches or combines. DeepSeek's decode splits attention into two steps for a 5-stage pipeline. Use low-latency RDMA kernels with CUDA graphs for decode (vLLM deepep_low_latency) and high-throughput kernels for prefill (deepep_high_throughput).
:::

::: reveal
? <span class="lvl lvl-expert">Expert</span> Why data-parallel attention for MLA models?
> MLA stores one compressed latent per token shared by all heads, so splitting heads across GPUs would duplicate that cache on every GPU. Data-parallel attention keeps each request's cache on one GPU (SGLang's "DP attention" removes the duplication).
:::

<!-- slide id="s-wrong" chapter="Wrong answers" tag="6 · Wrong answers to avoid" tagclass="b1" -->
## Wrong answers to avoid

::: reveal myth
? "Only 37B parameters are active, so serving costs like a 37B dense model."
> Memory and weight reads cover all experts in use; DeepSeek-V3's routed experts alone are about 654 GB in FP8.
:::

::: reveal myth
? "Wider expert parallelism is always better."
> Each extra node adds all-to-all traffic and another failure point. DeepSeek itself moved from EP 320 (report) to EP 144 (production write-up) for decode.
:::

::: reveal myth
? "Balanced training means balanced serving."
> Real traffic routes unevenly; vLLM's docs note the token distribution across experts can be highly skewed in practice, which is why EPLB exists.
:::

::: reveal myth
? "Prefill and decode should share one layout."
> They have different bottlenecks: prefill is compute-bound with large batches, decode needs many GPUs' tokens per expert, so DeepSeek runs them as separate units.
:::

<!-- slide id="s-system" chapter="In a system" tag="7 · In a system" tagclass="b9" -->
## In a real system

::: cards grid2
### [a] Fleet size
DeepSeek's V3 and R1 service peaked at 278 nodes (8 H800 each) and averaged 226.75 over one day, about $87K/day at an assumed $2 per GPU-hour.

### [c] Elastic capacity
At night, when traffic is low, DeepSeek shrinks inference and gives the nodes to research and training.

### [b] Precision
FP8 matmuls and FP8 dispatch, BF16 for MLA attention and combine, matching training.

### [e] Open-source path
vLLM: --enable-expert-parallel with --all2all-backend deepep_low_latency or deepep_high_throughput and --enable-eplb; SGLang: DP attention, DeepEP, EPLB and two-batch overlap.
:::

See also: <a href="../09-disaggregated-serving/index.html">Disaggregated serving</a> for the prefill/decode split, and <a href="../../distributed/07-expert-parallelism/index.html">Expert parallelism in training</a>.

<!-- slide id="s-practice" chapter="Practice" tag="8 · Practice" tagclass="b8" -->
## Practice

1. **Explain in 60 seconds** why decode uses wider expert parallelism than prefill.
            2. **Draw** a decode unit: DP attention ranks, the dispatch and combine all-to-alls, experts with one copied hot expert.
            3. **Compute** tokens per expert for EP 144, 64 sequences per GPU, 32 copies: 64 × 144 × 8 ÷ 288 = **256**.

::: quiz
? With EP 8 on one 8-GPU node and 64 decode sequences per GPU, about how many tokens does each DeepSeek-V3 expert see per step?
- [ ] About 2
- [x] About 16
- [ ] About 256
- [ ] About 2,000
> **B.** 64 × 8 GPUs × 8 experts per token ÷ 256 experts = 16: far below the roughly 300 needed for compute-bound FP8 matmuls.
:::

::: quiz
? What does an expert load balancer do?
- [ ] Drops tokens for busy experts
- [x] Copies frequently used experts to more GPUs and re-places them from load statistics
- [ ] Moves attention to the CPU
- [ ] Retrains the router
> **B.** Redundant copies spread the hot experts' tokens so no GPU becomes the straggler.
:::

<p class="start-hint">Next: <a href="../13-kv-cache-fleet/index.html">13 · The KV cache across the fleet →</a> · Previous: <a href="../09-disaggregated-serving/index.html">← 09 · Disaggregated serving</a> · <a href="../index.html">All decks</a></p>

<!-- slide id="s-papers" from="papers" -->
