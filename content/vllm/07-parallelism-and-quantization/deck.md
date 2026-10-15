---
title: Parallelism and Quantization in vLLM
body:
  data-deck: Parallelism and quantization
  data-home: ../index.html
  data-home-label: vLLM
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'fit weights :: TP in node, PP across nodes :: a'
  - 'more KV room :: TP also splits KV heads :: c'
  - 'quantize :: weights (fp8/awq/gptq…) and KV (fp8) :: b'
  - 'scale out :: DP replicas, EP for MoE :: e'
  caption: 'Concepts: Inference deck 08, Distributed decks 04–07.'
example:
  title: 'Worked example: Llama-3.1-70B on 80 GB GPUs'
  setup: 'Notebook 04''s planner: 70.6B parameters, 80 layers, 8 KV heads of dimension 128; gpu_memory_utilization 0.92; 4 GiB activation reserve per GPU.'
  steps:
  - 'KV bytes per token: 2 × 80 × 8 × 128 × 2 = <b>320 KiB</b> in BF16.'
  - 'TP = 1: BF16 weights (≈ 131 GiB) do not fit. TP = 2: room for only ≈ <b>25K</b> KV tokens (3 concurrent 8K requests).'
  - 'TP = 4: ≈ <b>481K</b> KV tokens (58 × 8K requests): splitting weights frees far more room than the extra GPUs alone.'
  - An FP8 KV cache doubles that to ≈ 963K tokens (117 × 8K requests).
  result: Parallelism first makes a model fit, then mostly buys KV space; quantization multiplies both.
traps:
  tricks:
  - 'TP within a node. :: Per-layer all-reduces need NVLink.'
  - 'FP8 KV cache. :: --kv-cache-dtype fp8 halves KV memory on supporting GPUs.'
  - 'MoE: --enable-expert-parallel. :: With TP or DP for the dense parts.'
  traps:
  - 'TP across nodes. :: Use PP between nodes instead.'
  - 'Quantizing blindly. :: Check accuracy on your tasks; methods differ by hardware support.'
  - 'Forgetting DP routing. :: Prefix-cache hits depend on which replica gets a request.'
papers:
- vllm_parallel
- vllm_quant
- megatron
- awq
- gptq
- fp8
status: {label: current, reviewed: 2026-10-15, note: "v0.31.0 is still the latest release"}
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">vLLM · 07</div>
    <h1>Parallelism and quantization</h1>
    <p class="sub">Fitting and scaling models in vLLM: tensor, pipeline, data and expert parallelism flags, weight quantization formats, and FP8 KV caches, with their effect on memory and throughput.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>A 70B model in BF16 needs about 141 GB for weights alone, more than one 80 GB GPU. Even when a model fits, KV-cache space limits how many requests can run at once.</div>
      <div class="c"><b>Core idea</b><b>Tensor parallelism</b> (<code>-tp</code>) splits each layer across GPUs in a node; <b>pipeline parallelism</b> (<code>-pp</code>) splits layers across nodes; <b>data parallelism</b> (<code>-dp</code>) replicates the engine; <b>expert parallelism</b> (<code>--enable-expert-parallel</code>) spreads MoE experts. <b>Quantization</b> (<code>--quantization</code>, e.g. fp8, awq, gptq) shrinks weights; <code>--kv-cache-dtype fp8</code> halves KV memory.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Plan a deployment

Choose a model, TP and KV-cache dtype. The planner (same as notebook 04) shows weights per GPU, KV tokens across the TP group and concurrent 8K-token requests on 80 GB GPUs.
{: .lede}

<div class="visual">
  <div class="seg" id="qSeg"><button data-v="8b" class="on">Llama-3.1-8B</button><button data-v="70b">Llama-3.1-70B</button><button data-v="q7">Qwen2.5-7B</button></div>
  <div class="controls"><label class="ctl">TP <input type="range" id="qT" min="0" max="3" step="1" value="0"> <output id="qTo"></output></label><div class="seg" id="qK"><button data-v="2" class="on">BF16 KV</button><button data-v="1">FP8 KV</button></div><div class="seg" id="qW"><button data-v="2" class="on">BF16 weights</button><button data-v="1">FP8 weights</button></div></div>
  <div id="qBars" style="margin-top:12px"></div>
  <p class="readout" id="qOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why one GPU isn't enough

::: cards grid3
### [d] Weights
70B × 2 bytes ≈ 141 GB in BF16.

### [b] KV cache
Every concurrent token needs KV in every layer; long contexts multiply it.

### [c] Throughput
One replica can only serve so many requests per second.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Which flag adds throughput but not memory?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Your model fits on one GPU but you need 4× the requests per second. Which option is most natural?
- [ ] -tp 4
- [ ] -pp 4
- [x] -dp 4
- [ ] --kv-cache-dtype fp8
> <b>C.</b> Data parallelism runs 4 independent engine replicas. TP/PP help when the model or its KV cache does not fit.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## The knobs

::: cards grid2
### [a] Tensor (-tp)
Shard every layer across GPUs in one node; also shards KV heads, so KV per GPU shrinks.

### [c] Pipeline (-pp)
Split layers into stages, usually across nodes; activations pass stage to stage.

### [e] Data (-dp) and expert parallelism
Replicate engines; for MoE, --enable-expert-parallel places experts on different GPUs.

### [b] Quantization
--quantization (fp8, awq, gptq, compressed-tensors, mxfp4, …) for weights; --kv-cache-dtype fp8 for KV.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Typical commands

<div class="visual"><pre style="margin:0;font:13px/1.55 'JetBrains Mono',monospace;white-space:pre-wrap"># 70B dense model on one 8-GPU node&#10;$ vllm serve meta-llama/Llama-3.1-70B-Instruct -tp 8&#10;&#10;# large model over two nodes: TP inside, PP across&#10;$ vllm serve <model> -tp 8 -pp 2&#10;&#10;# MoE model: experts spread over GPUs&#10;$ vllm serve <moe-model> -tp 8 --enable-expert-parallel&#10;&#10;# more throughput from a model that fits on 2 GPUs&#10;$ vllm serve <model> -tp 2 -dp 4&#10;&#10;# smaller weights and KV cache&#10;$ vllm serve <fp8-checkpoint> --kv-cache-dtype fp8</pre></div>
<p class="caption">Flags are generated from vllm/config (ParallelConfig, CacheConfig) and vllm/engine/arg_utils.py in v0.31.0.</p>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why these choices

::: cards grid2
### [a] Match communication to links
TP's per-layer all-reduces need NVLink; PP sends little between stages.

### [e] KV room is throughput
More KV tokens → more concurrent requests → higher throughput.

### [b] Bytes are time
Decoding is memory-bound; fewer bytes per weight and KV entry mean faster steps.

### [c] Replicas scale linearly
DP adds capacity without changing per-request latency.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "More TP always lowers latency."
> Beyond a point the all-reduce cost dominates; TP mostly buys memory and per-GPU work reduction.
:::

::: reveal myth
? "FP8 KV cache is free accuracy-wise."
> It is usually close, but should be validated on your workload.
:::

::: reveal myth
? "Expert parallelism replaces tensor parallelism."
> EP distributes experts; attention and dense layers still use TP or DP.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? KV bytes per token for Llama-3.1-8B in BF16 (32 layers, 8 KV heads, dim 128)?
- [ ] 32 KiB
- [ ] 64 KiB
- [x] 128 KiB
- [ ] 256 KiB
> 2 × 32 × 8 × 128 × 2 = <b>128 KiB</b>.
:::

::: reveal
? Why does going from TP = 2 to TP = 4 more than double KV capacity for a 70B model?
> Each GPU's weight share halves too, freeing memory beyond the extra GPUs' own capacity.
:::

::: reveal
? Which flag halves KV-cache memory?
> --kv-cache-dtype fp8 (on supporting hardware).
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">vLLM fits and scales models with -tp (in node), -pp (across nodes), -dp (replicas) and expert parallelism, and shrinks memory with weight quantization and an FP8 KV cache; KV room becomes concurrency.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Large models need more than one GPU, and even small ones are limited by KV-cache space. vLLM's tensor parallelism splits every layer, and the KV heads, across GPUs in a node; pipeline parallelism splits layers across nodes; data parallelism runs independent engine replicas for throughput; expert parallelism spreads mixture-of-experts layers. Quantization flags shrink weights with formats like FP8, AWQ or GPTQ, and an FP8 KV cache halves KV memory. In the notebook, a 70B model goes from not fitting, to three concurrent 8K requests at TP two, to fifty-eight at TP four.</p></div>
    <div class="recap"><div><span><b>Problem:</b> weights and KV exceed one GPU.</span></div><div><span><b>Core idea:</b> TP/PP to fit, DP/EP to scale, quantize to shrink.</span></div><div><span><b>Flags:</b> -tp -pp -dp --enable-expert-parallel --kv-cache-dtype.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/vllm/04_memory_planner.ipynb" target="_blank" rel="noopener">04 · Planning GPU memory: weights, KV cache and concurrency</a> <span style="color:var(--faint)">· 25 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/vllm/04_memory_planner.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../08-running-and-tuning/index.html">08 · Running and tuning vLLM →</a> · Previous: <a href="../06-speculative-decoding/index.html">← 06</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
