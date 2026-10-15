---
title: vLLM Engine Architecture
body:
  data-deck: Engine architecture
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
  - 'API server × A :: HTTP, tokenise, stream :: c'
  - 'ZMQ :: many-to-many :: f'
  - 'EngineCore × DP :: busy loop: schedule + KV :: a'
  - 'GPU worker × N :: N = DP × PP × TP :: b'
  - 'DP coordinator :: only if DP > 1 :: e'
  caption: From the vLLM architecture overview (process count summary).
example:
  title: 'Worked example: counting processes'
  setup: 'The vLLM architecture overview''s formula: total = A + DP + N (+ 1 if DP > 1), where N = DP × PP × TP GPUs and A defaults to DP.'
  steps:
  - '<code>vllm serve … -tp=4</code> on one node: 1 API server + 1 engine core + 4 GPU workers = <b>6 processes</b>.'
  - '<code>vllm serve … -tp=2 -dp=4</code> on 8 GPUs: 4 API servers + 4 engine cores + 8 GPU workers + 1 DP coordinator = <b>17 processes</b>.'
  - Each API server connects to every engine core via ZMQ, so any server can route a request to any data-parallel rank.
  - In the LLM class (offline), the engine core still runs in a background process (SyncMPClient); InprocClient keeps it in-process.
  result: Splitting CPU-heavy I/O from the engine loop keeps the GPU fed; data parallelism replicates the engine, tensor and pipeline parallelism multiply the workers.
traps:
  tricks:
  - 'Processes = A + DP + N (+1). :: A defaults to DP.'
  - 'EngineCore = scheduler + KV manager + executor. :: One per DP rank.'
  - 'Executors. :: uniproc, multiproc (default multi-GPU on one node), Ray (multi-node).'
  traps:
  - 'Under-provisioning CPU cores. :: Each process needs CPU; too few cores slow the engine loop.'
  - 'Treating DP like TP. :: DP replicates the whole engine; TP splits one model across GPUs.'
  - 'Debugging only the API server logs. :: Scheduling issues appear in the engine core.'
papers:
- vllm_arch
- vllm_v1
- vllm_release
- vllm_v029
status: {label: current, reviewed: 2026-10-15, note: "v0.31.0 latest; Model Runner V2 default since v0.29, V1 deprecated"}
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">vLLM · 02</div>
    <h1>Engine architecture</h1>
    <p class="sub">How vLLM V1 splits work across processes (API servers, engine cores, GPU workers, a data-parallel coordinator), why the engine loop is isolated, and how the pieces talk.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Tokenising, detokenising and streaming are CPU work; scheduling must run every few milliseconds; the GPU must never wait. In one Python process these compete for the interpreter.</div>
      <div class="c"><b>Core idea</b>V1 runs an <b>API server</b> process (HTTP, tokenisation, streaming), an isolated <b>EngineCore</b> process per data-parallel rank (a busy loop: schedule → execute → update), and one <b>GPU worker</b> process per GPU. They communicate over ZMQ (and shared memory). For N GPUs: <b>A + DP + N</b> processes, plus a coordinator if DP &gt; 1.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## How many processes?

Pick tensor, pipeline and data parallel sizes. The diagram shows every process vLLM V1 starts, using the formula from the architecture overview. Checked against vLLM v0.31.0.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">TP <input type="range" id="aT" min="1" max="8" step="1" value="4"> <output id="aTo"></output></label><label class="ctl">PP <input type="range" id="aP" min="1" max="4" step="1" value="1"> <output id="aPo"></output></label><label class="ctl">DP <input type="range" id="aD" min="1" max="8" step="1" value="1"> <output id="aDo"></output></label></div>
  <svg id="aSvg" viewBox="0 0 660 240" style="margin-top:10px" role="img" aria-label="Process layout"></svg>
  <p class="readout" id="aOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why not one process?

::: cards grid3
### [d] The GIL
One Python interpreter cannot tokenise, schedule and stream in parallel.

### [b] CPU overhead
At small per-step GPU times, CPU work between steps leaves the GPU idle.

### [c] One process per GPU
Each GPU needs its own process for its CUDA context.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What does an EngineCore do?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Which of these does the EngineCore process NOT do?
- [ ] Run the scheduler
- [ ] Manage KV cache blocks
- [x] Handle HTTP requests and tokenisation
- [ ] Dispatch work to GPU workers
> <b>C.</b> HTTP handling and tokenisation live in the API server process, so the engine core's busy loop only schedules and executes.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Three kinds of processes

::: cards grid3
### [c] API server
HTTP (OpenAI-compatible), input processing, detokenisation, streaming. Count defaults to DP (--api-server-count).

### [a] EngineCore
Busy loop: schedule → execute model → update outputs. Holds the scheduler and KV cache manager. One per DP rank.

### [b] GPU worker
One per GPU: loads its shard of the model, holds its KV cache, runs forward passes (model runner, CUDA graphs). Model Runner V2 has been the default since v0.29 [[current]]; Model Runner V1 is deprecated, targeted for removal in v0.32 [[legacy]].
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Where to find things in the source

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Component</th><th>Module (v0.31.0)</th></tr>
  <tr><td>Async engine used by the server</td><td>vllm/v1/engine/async_llm.py</td></tr>
  <tr><td>Engine core loop</td><td>vllm/v1/engine/core.py (EngineCore, EngineCoreProc)</td></tr>
  <tr><td>Client ↔ core IPC (ZMQ)</td><td>vllm/v1/engine/core_client.py (InprocClient, SyncMPClient, AsyncMPClient)</td></tr>
  <tr><td>Scheduler</td><td>vllm/v1/core/sched/scheduler.py</td></tr>
  <tr><td>KV cache manager, block pool</td><td>vllm/v1/core/kv_cache_manager.py, block_pool.py</td></tr>
  <tr><td>Executors</td><td>vllm/v1/executor/ (uniproc, multiproc, ray)</td></tr>
  <tr><td>Workers and model runners</td><td>vllm/v1/worker/</td></tr>
</table></div>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why this layout works

::: cards grid2
### [a] Overlap
Tokenisation, multimodal loading and streaming run in parallel with the engine loop (V1 blog).

### [e] Simple scaling
DP adds engines; TP/PP add workers under one engine; the formulas stay simple.

### [b] Fault isolation
Front-end and engine failures are separated and observable.

### [c] Many-to-many routing
Any API server can feed any DP engine, balancing load.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "More API servers make generation faster."
> They raise HTTP and tokenisation capacity; generation speed is set by the engine and GPUs.
:::

::: reveal myth
? "Each GPU runs its own scheduler."
> One EngineCore schedules for all GPU workers of its DP rank; workers only execute.
:::

::: reveal myth
? "Data parallelism shares one KV cache."
> Each DP rank has its own engine and KV cache; prefix-cache hits depend on routing to the right rank.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Processes for vllm serve -tp=2 -dp=2 (4 GPUs)?
- [ ] 6
- [ ] 8
- [x] 9
- [ ] 5
> 2 API servers + 2 engine cores + 4 workers + 1 coordinator = <b>9</b>.
:::

::: reveal
? Why is the EngineCore a separate process?
> To isolate the scheduling/execution busy loop from CPU-heavy front-end work, removing interpreter contention and overhead.
:::

::: reveal
? What does the DP coordinator do?
> Load-balances requests across data-parallel engine ranks; it exists only when DP > 1.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">vLLM V1 runs API servers (HTTP, tokenise, stream), one isolated EngineCore per data-parallel rank (schedule + KV + execute) and one worker per GPU: A + DP + N processes, +1 coordinator if DP > 1.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>vLLM version one splits the work across processes so the GPU never waits on Python. API server processes handle HTTP, tokenisation and streaming. Each data-parallel rank has one engine-core process running a busy loop that schedules the next step, manages the KV cache and dispatches work. Each GPU has its own worker process that runs the model. They talk over ZMQ in a many-to-many pattern. The total is the number of API servers plus data-parallel engines plus GPUs, plus a coordinator when data parallelism is on: six processes for tensor parallel four on one node, seventeen for tensor two by data four.</p></div>
    <div class="recap"><div><span><b>Problem:</b> CPU work and scheduling compete with GPU work.</span></div><div><span><b>Core idea:</b> API server / EngineCore / GPU workers over ZMQ.</span></div><div><span><b>Count:</b> A + DP + N (+1 if DP > 1).</span></div></div>
    <p class="start-hint">Next: <a href="../03-kv-cache-manager/index.html">03 · KV cache manager and PagedAttention →</a> · Previous: <a href="../01-what-is-vllm/index.html">← 01</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
