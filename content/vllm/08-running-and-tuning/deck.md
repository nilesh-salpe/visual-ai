---
title: Running and Tuning vLLM
body:
  data-deck: Running and tuning vLLM
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
  - 'vllm serve <model> :: flags :: f'
  - 'clients :: /v1/chat/completions :: c'
  - '/metrics :: Prometheus :: a'
  - 'vllm bench serve :: measure :: b'
  - 'adjust :: memory, concurrency, budget :: e'
  loop: '4 -> 2 :: iterate'
example:
  title: 'Worked example: fixing preemptions'
  setup: 'vLLM''s optimization guide: when KV cache space runs out, requests are preempted and recomputed, logging a warning and raising vllm:num_preemptions.'
  steps:
  - 'Symptom: vllm:num_preemptions climbing, vllm:kv_cache_usage_perc near 1.0, and tail latency spikes.'
  - 'Option 1 (from the guide): increase --gpu-memory-utilization to give the KV cache more of the GPU.'
  - 'Option 2: decrease --max-num-seqs or --max-num-batched-tokens to run fewer requests at once.'
  - 'Option 3: increase --tensor-parallel-size (weights per GPU shrink, KV room grows), or use --kv-cache-dtype fp8. Re-measure with vllm bench serve.'
  result: Preemption is a symptom of KV pressure; trade concurrency, memory share or parallelism against it, and measure.
traps:
  tricks:
  - '--max-model-len below the model maximum. :: Saves startup KV checks and memory if you never need full context.'
  - 'vllm bench serve / throughput / latency. :: Built-in benchmarks.'
  - 'Key metrics. :: kv_cache_usage_perc, num_requests_waiting, num_preemptions, time_to_first_token_seconds, inter_token_latency_seconds.'
  traps:
  - 'gpu-memory-utilization too high with other processes on the GPU. :: Out-of-memory at startup.'
  - 'Tuning on a different workload. :: Benchmark with your real prompt/output lengths.'
  - 'Ignoring max_num_batched_tokens. :: Larger raises throughput but also inter-token latency.'
papers:
- vllm_server
- vllm_opt
- vllm_release
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">vLLM · 08</div>
    <h1>Running and tuning vLLM</h1>
    <p class="sub">Serving with vllm serve: the flags that matter, the OpenAI-compatible endpoints, Prometheus metrics, benchmarking with vllm bench, and what to change when latency, throughput or preemptions look wrong.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Defaults are reasonable but every workload differs: long prompts or short, latency or throughput, many users or few. Tuning blind wastes GPUs or breaks latency targets.</div>
      <div class="c"><b>Core idea</b>Size memory with <code>--gpu-memory-utilization</code> (0.92 by default in v0.31.0), concurrency with <code>--max-num-seqs</code>, step size with <code>--max-num-batched-tokens</code>, and context with <code>--max-model-len</code>. Watch <b>/metrics</b> (KV usage, preemptions, queue, TTFT, inter-token latency), and measure changes with <code>vllm bench serve</code>.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Build a launch command

Pick a goal and constraints; the builder assembles a vllm serve command from flags that exist in v0.31.0 and explains each choice.
{: .lede}

<div class="visual">
  <div class="seg" id="cGoal"><button data-v="lat" class="on">low latency chat</button><button data-v="thr">max throughput</button><button data-v="long">long documents</button></div>
  <div class="controls"><label class="ctl">GPUs <input type="range" id="cG" min="1" max="8" step="1" value="1"> <output id="cGo"></output></label><label class="ctl"><input type="checkbox" id="cF"> FP8 KV cache</label><label class="ctl"><input type="checkbox" id="cS"> speculative (n-gram)</label></div>
  <pre id="cCmd" style="margin:12px 0 0;padding:12px;border-radius:10px;background:var(--panel-2);font:13px/1.55 'JetBrains Mono',monospace;white-space:pre-wrap"></pre>
  <p class="readout" id="cOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why defaults are only a start

::: cards grid3
### [d] Workloads differ
Chat (short prompts, streaming) and batch summarisation (long prompts) want different budgets.

### [b] Hardware differs
v0.31.0 already picks different batching defaults for H100-class, B200-class and other GPUs.

### [c] Targets differ
Latency SLOs (service-level objectives) and cost per token pull in opposite directions.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What to change first?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? vllm:num_requests_waiting keeps growing while vllm:kv_cache_usage_perc stays at 40%. What is the likely limit?
- [ ] KV memory
- [x] max_num_seqs (concurrency cap) or the token budget
- [ ] The tokenizer
- [ ] Network bandwidth
> <b>B.</b> Requests are waiting while KV memory is free, so a scheduling cap is binding: raise max_num_seqs or max_num_batched_tokens (and watch latency).
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Flags, endpoints, metrics

::: cards grid3
### [a] Flags
--gpu-memory-utilization, --max-num-seqs, --max-num-batched-tokens, --max-model-len, -tp/-pp/-dp, --kv-cache-dtype, --speculative-config.

### [c] Endpoints
/v1/chat/completions, /v1/completions, /v1/models, /health, /metrics (OpenAI-compatible server).

### [b] Metrics
vllm:kv_cache_usage_perc, num_requests_running / waiting, num_preemptions, time_to_first_token_seconds, inter_token_latency_seconds, prefix_cache_hits.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Defaults to know (v0.31.0)

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Setting</th><th>Default</th><th>Source</th></tr>
  <tr><td>gpu_memory_utilization</td><td>0.92</td><td>vllm/config/cache.py</td></tr>
  <tr><td>block_size</td><td>16 (back ends may choose another)</td><td>CacheConfig.DEFAULT_BLOCK_SIZE</td></tr>
  <tr><td>enable_prefix_caching</td><td>True</td><td>vllm/config/cache.py</td></tr>
  <tr><td>enable_chunked_prefill</td><td>True</td><td>vllm/config/scheduler.py</td></tr>
  <tr><td>policy</td><td>"fcfs"</td><td>vllm/config/scheduler.py</td></tr>
  <tr><td>max_num_batched_tokens (LLM class / server)</td><td>B200-class ≥ 160 GB: 16,384 / 16,384 · H100/H200-class: 16,384 / 8,192 · others: 8,192 / 2,048</td><td>vllm/engine/arg_utils.py</td></tr>
  <tr><td>max_num_seqs</td><td>1,024 on ≥ 70 GB GPUs (except A100), else 256</td><td>vllm/engine/arg_utils.py</td></tr>
</table></div>
<p class="caption">Defaults change between releases; check `vllm serve --help` for your version.</p>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why measure-then-tune works

::: cards grid2
### [a] Metrics name the bottleneck
KV pressure, scheduling caps and prefill load each show up in distinct metrics.

### [e] Built-in benchmarks
vllm bench serve replays realistic request streams against a running server.

### [b] Few knobs matter most
Memory share, concurrency, budget and parallelism cover most tuning.

### [c] Repeatable
Pin the version and flags; defaults are versioned in code.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Setting gpu_memory_utilization to 1.0 is best."
> It leaves no headroom for activations spikes, other processes or fragmentation; out-of-memory errors follow.
:::

::: reveal myth
? "Higher max_num_seqs always means higher throughput."
> Past the KV capacity it only causes preemption and recomputation.
:::

::: reveal myth
? "Benchmark numbers transfer between workloads."
> Prompt and output length distributions change results dramatically.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Default gpu_memory_utilization in vLLM v0.31.0?
- [ ] 0.8
- [ ] 0.9
- [x] 0.92
- [ ] 0.95
> <b>0.92</b> (CacheConfig).
:::

::: reveal
? Name three actions for frequent preemptions.
> Increase gpu_memory_utilization; decrease max_num_seqs or max_num_batched_tokens; increase tensor_parallel_size (or use an FP8 KV cache).
:::

::: reveal
? Which metric shows how full the KV cache is?
> vllm:kv_cache_usage_perc.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Run vllm serve with memory (0.92 default), concurrency, token-budget and parallelism flags; watch /metrics for KV usage, queueing and preemptions; and measure every change with vllm bench serve.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Running vLLM well is a loop of configure, measure, adjust. The key flags set how much GPU memory vLLM may use, 0.92 by default in this version, how many requests run at once, how many tokens each step may schedule, the maximum context, parallelism, the KV-cache data type and speculative decoding. The server speaks the OpenAI API and exports Prometheus metrics: KV-cache usage, running and waiting requests, preemptions, time to first token and inter-token latency. Preemptions mean KV pressure; waiting requests with free KV mean a scheduling cap. vllm bench serve measures the effect of each change.</p></div>
    <div class="recap"><div><span><b>Problem:</b> one configuration does not fit every workload.</span></div><div><span><b>Core idea:</b> flags → metrics → benchmark → adjust.</span></div><div><span><b>Defaults:</b> mem 0.92, block 16, prefix caching and chunked prefill on.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/vllm/04_memory_planner.ipynb" target="_blank" rel="noopener">04 · Planning GPU memory: weights, KV cache and concurrency</a> <span style="color:var(--faint)">· 25 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/vllm/04_memory_planner.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">You've finished the series. <a href="../../build-it/index.html">See all Build-it notebooks →</a> · Previous: <a href="../07-parallelism-and-quantization/index.html">← 07</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
