---
title: The vLLM Scheduler
body:
  data-deck: 'The scheduler: continuous batching and chunked prefill'
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
  - 'token budget :: max_num_batched_tokens :: f'
  - 'running first :: decodes + prefill chunks :: a'
  - 'then waiting :: admit while budget and blocks :: c'
  - 'no blocks? :: preempt newest running :: d'
  - 'execute + update :: computed += scheduled :: e'
  loop: '4 -> 0 :: every step'
  caption: 'Concepts: Inference decks 03–04 (batching, chunked prefill).'
example:
  title: 'Worked example: one step'
  setup: 'Notebook 03''s step function (mirroring vllm/v1/core/sched/scheduler.py): budget 64 tokens; one running request decoding; one new request with a 100-token
    prompt.'
  steps:
  - 'Running first: the decoding request needs 1 token → scheduled 1. Budget left: 63.'
  - 'Waiting next: the new request needs 100 prompt tokens; the budget allows <b>63</b>, so its prefill is chunked: 63 now, 37 next step.'
  - 'Blocks: 63 tokens need ⌈63/16⌉ = 4 new blocks, allocated from the pool.'
  - 'Defaults in v0.31.0 depend on GPU and entrypoint: on H100/H200-class GPUs, max_num_batched_tokens is 16,384 for the LLM class and 8,192 for the server; max_num_seqs
    1,024. Other GPUs: 8,192 / 2,048 and 256.'
  result: Decodes are never starved by prefills, and prefills fill whatever budget is left.
traps:
  tricks:
  - 'Bigger budget = higher throughput. :: But longer steps, so higher inter-token latency.'
  - 'long_prefill_token_threshold. :: Caps one prompt''s chunk per step.'
  - 'Watch vllm:num_preemptions. :: Rising → raise memory or lower concurrency.'
  traps:
  - 'Too large max_num_seqs for the memory. :: Constant preemption and recomputation.'
  - 'Tiny budget with long prompts. :: TTFT (time to first token) grows as prompts trickle in.'
  - 'Assuming strict FCFS. :: The scheduler may skip a blocked request to schedule later ones.'
papers:
- vllm_opt
- sarathi_serve
- orca
- vllm_release
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">vLLM · 04</div>
    <h1>The scheduler: continuous batching and chunked prefill</h1>
    <p class="sub">How vLLM V1 decides what runs each step: one token budget shared by decodes and prefills, running requests first, chunked prefill, a long-prefill threshold, and preemption by recomputation.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Every step mixes requests at different stages: some decoding one token, some with long prompts to prefill, some just arrived. The scheduler must keep the GPU full without stalling anyone.</div>
      <div class="c"><b>Core idea</b>V1 has <b>no prefill or decode phase</b>. Each request has <code>num_computed_tokens</code> and a known token count; each step hands out a <b>token budget</b> (<code>max_num_batched_tokens</code>) so computed tokens catch up. <b>Running</b> requests go first, then <b>waiting</b> ones; long prompts are <b>chunked</b>. If KV blocks run out, the newest running request is <b>preempted</b> and later recomputed.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Fill a step's token budget

Running requests (decoding) and waiting ones (prompts to prefill) compete for one step's budget. Change the budget and the long-prefill threshold and press "step".
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">budget <input type="range" id="sB" min="16" max="512" step="16" value="128"> <output id="sBo"></output></label><label class="ctl">long-prefill threshold <input type="range" id="sL" min="0" max="256" step="16" value="0"> <output id="sLo"></output></label><button class="btn primary" id="sStep">step</button><button class="btn" id="sReset">reset</button></div>
  <div id="sBars" style="margin-top:12px"></div>
  <p class="readout" id="sOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## What older schemes got wrong

::: cards grid3
### [d] Static batches
Wait for the whole batch to finish before admitting new requests.

### [b] Prefill-first phases
Separate prefill steps pause all decoding, causing latency spikes.

### [c] Whole prompts
One long prompt can occupy an entire step.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Who goes first?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Budget 64. One running request is decoding; a new request has a 200-token prompt. What does the step contain?
- [ ] 200 prompt tokens only
- [x] 1 decode token + 63 prompt tokens
- [ ] 64 prompt tokens
- [ ] 1 decode token only
> <b>B.</b> Running requests are scheduled first (1 token), and the remaining 63 tokens start the new request's prefill as a chunk.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## One budget, no phases

::: cards grid2
### [a] Token budget
max_num_scheduled_tokens per step (from max_num_batched_tokens); spent on any mix of prefill chunks and decodes.

### [c] Order
Running requests first (FCFS policy by default, priority optional), then waiting requests while budget and KV blocks last.

### [b] Chunked prefill
On by default in V1 (enable_chunked_prefill=True); long_prefill_token_threshold caps a single request's chunk.

### [d] Preemption
If blocks run out, the newest (or lowest-priority) running request is preempted: blocks freed, computed tokens reset to 0, put back at the front of the waiting queue.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## From the source

The scheduler's own comment (vllm/v1/core/sched/scheduler.py, v0.31.0):

<div class="visual"><pre style="margin:0;font:13px/1.55 'JetBrains Mono',monospace;white-space:pre-wrap"># There's no "decoding phase" nor "prefill phase" in the scheduler.&#10;# Each request just has the num_computed_tokens and&#10;# num_tokens_with_spec. num_tokens_with_spec =&#10;# len(prompt_token_ids) + len(output_token_ids) + len(spec_token_ids).&#10;# At each step, the scheduler tries to assign tokens to the requests&#10;# so that each request's num_computed_tokens can catch up its&#10;# num_tokens_with_spec. This is general enough to cover&#10;# chunked prefills, prefix caching, speculative decoding, ...</pre></div>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why the unified design works

::: cards grid2
### [a] One rule covers everything
Prefill, decode, prefix-cache hits and speculative tokens are all "tokens to catch up".

### [e] Steady latency
Decodes always get their token each step; prefills absorb the rest (Sarathi-Serve's stall-free idea).

### [b] Full GPU
The budget keeps each step large enough to be efficient.

### [c] Graceful overload
Preemption by recomputation frees memory without crashing; the request resumes later.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "vLLM batches requests that arrive together."
> Batches change every step: requests join and leave continuously.
:::

::: reveal myth
? "Preempted requests lose their output."
> They keep generated tokens; only the KV cache is dropped and recomputed (prefix caching may make that cheap).
:::

::: reveal myth
? "Chunked prefill makes prompts slower."
> Per prompt it can add a few steps, but it keeps decode latency smooth and the GPU busy.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Default scheduling policy in v0.31.0?
- [ ] priority
- [x] fcfs
- [ ] shortest-job-first
- [ ] round-robin
> <b>"fcfs"</b> (SchedulerConfig.policy).
:::

::: reveal
? What happens to a preempted request in V1?
> Its KV blocks are freed, num_computed_tokens is reset to 0, and it is put back at the front of the waiting queue to be recomputed later.
:::

::: reveal
? What does long_prefill_token_threshold do?
> Caps how many prompt tokens one request may be given in a single step, so one long prompt cannot monopolise the budget.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">vLLM V1 schedules with one per-step token budget and no phases: running requests first, then waiting ones in chunks, and preemption by recomputation when KV blocks run out.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Every vLLM step, the scheduler hands out a token budget. There is no separate prefill or decode phase: each request simply has tokens it already computed and tokens it knows about, and the scheduler assigns tokens so it catches up. Requests already running go first, which gives every decoding request its next token, then waiting requests fill the rest, with long prompts split into chunks and optionally capped per step. If the KV cache runs out of blocks, the newest running request is preempted: its blocks are freed and it is recomputed later. Budget size trades throughput against inter-token latency.</p></div>
    <div class="recap"><div><span><b>Problem:</b> mixed prefills and decodes every step.</span></div><div><span><b>Core idea:</b> token budget; running first; chunked prefill.</span></div><div><span><b>Overload:</b> preempt newest; recompute later.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/vllm/03_token_budget_scheduler.ipynb" target="_blank" rel="noopener">03 · The unified token-budget scheduler</a> <span style="color:var(--faint)">· 40 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/vllm/03_token_budget_scheduler.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../05-prefix-caching/index.html">05 · Automatic prefix caching →</a> · Previous: <a href="../03-kv-cache-manager/index.html">← 03</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
