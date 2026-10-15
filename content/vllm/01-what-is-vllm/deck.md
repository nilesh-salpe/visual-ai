---
title: What vLLM Is
body:
  data-deck: What vLLM is and a request's life
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
  - 'HTTP / LLM.generate :: request in :: f'
  - 'API server :: tokenize, validate :: c'
  - 'EngineCore :: schedule each step :: a'
  - 'GPU workers :: forward pass, sample :: b'
  - 'detokenize + stream :: tokens out :: e'
  loop: '3 -> 2 :: once per generated token'
  caption: The concepts behind each box are in the Inference topic; these decks show vLLM's implementation.
example:
  title: 'Worked example: one chat request'
  setup: A client sends a 900-token prompt to <code>vllm serve meta-llama/Llama-3.1-8B-Instruct</code> and asks for up to 200 tokens. Checked against vLLM v0.31.0.
  steps:
  - The <b>API server</b> process applies the chat template, tokenises and sends the request to the engine core over ZMQ.
  - The <b>EngineCore</b> scheduler checks the prefix cache (a shared system prompt may already be cached), allocates 16-token KV blocks and schedules the prompt,
    in chunks if it exceeds the per-step token budget.
  - The <b>GPU worker</b> runs the forward pass for the whole batch (this request's prefill chunk plus other users' decode tokens), samples a token, and the request
    joins the decode set.
  - Each later step adds one token (or several with speculative decoding); the API server detokenises and streams them until 200 tokens or a stop condition, then
    the request's blocks are freed (and stay cached for reuse).
  result: One request touches three kinds of processes and is batched with everyone else at every step.
traps:
  tricks:
  - 'Offline: LLM(model).generate(prompts). :: Batches everything for throughput.'
  - 'Online: vllm serve <model>. :: OpenAI-compatible /v1/chat/completions.'
  - 'Read the Inference topic first. :: KV cache, batching, PagedAttention concepts.'
  traps:
  - 'Benchmarking one request at a time. :: vLLM''s gains come from batching many.'
  - 'Assuming V0 behaviour. :: V1 changed the scheduler, process layout and defaults; the V0 engine was removed entirely in v0.11.0 (October 2025).'
  - 'Pinning advice to old versions. :: Defaults change between releases; check the version you run.'
papers:
- vllm
- vllm_v011
- vllm_v1
- vllm_arch
status: {label: current, reviewed: 2026-10-15, note: "v0.31.0 is still the latest release; V0 engine removed in v0.11.0"}
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">vLLM · 01</div>
    <h1>What vLLM is and a request's life</h1>
    <p class="sub">The open-source LLM inference and serving engine built around PagedAttention: what it does, the two ways to use it, and every stage a request passes through.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Serving an LLM well means batching many users' requests onto a GPU, managing a KV cache that grows with every token, and streaming tokens back quickly. Writing that from scratch is a large systems project.</div>
      <div class="c"><b>Core idea</b>vLLM is a serving engine: you give it a model and requests; it handles <b>batching</b> (continuous, token-budget scheduling), <b>KV memory</b> (paged blocks with prefix caching), <b>execution</b> (CUDA graphs, fused kernels, parallelism) and <b>APIs</b> (a Python <code>LLM</code> class for offline batches and <code>vllm serve</code> for an OpenAI-compatible server).</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Follow a request

Step through the life of one request inside vLLM. Each stage names the process that runs it and the source module. Checked against vLLM v0.31.0.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><button class="btn primary" id="lNext">next stage</button><button class="btn" id="lReset">reset</button></div>
  <svg id="lSvg" viewBox="0 0 660 200" style="margin-top:10px" role="img" aria-label="Request lifecycle"></svg>
  <p class="readout" id="lOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why not serve with a plain model.generate()?

::: cards grid3
### [d] One request at a time
GPUs sit mostly idle during decode without batching many users.

### [b] KV memory waste
Contiguous per-request reservations used only 20.4%–38.2% of KV memory in earlier systems (PagedAttention paper).

### [c] Everything else
Streaming, OpenAI-compatible APIs, metrics, parallelism, quantization, speculative decoding.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Offline or online?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? You need to label 2 million documents with an LLM overnight. Which vLLM entrypoint fits?
- [ ] vllm serve and one HTTP call per document
- [x] The LLM class with all prompts passed to generate()
- [ ] Either is identical
- [ ] Neither: use plain Hugging Face generate
> <b>B.</b> The LLM class submits everything at once so the scheduler can batch maximally; an HTTP server adds overhead you don't need offline.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Four jobs of a serving engine

::: cards grid2
### [a] Batching
A unified scheduler hands out a per-step token budget across prefills and decodes (deck 04).

### [c] KV memory
Paged 16-token blocks, reference counts and automatic prefix caching (decks 03, 05).

### [b] Execution
Model runner with CUDA graphs and torch.compile; tensor, pipeline, data and expert parallelism (decks 02, 07).

### [e] Interfaces
LLM class, vllm serve (OpenAI-compatible), metrics, benchmarking tools (deck 08).
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## The two entrypoints

<div class="visual"><pre style="margin:0;font:13px/1.55 'JetBrains Mono',monospace;white-space:pre-wrap"># offline batch inference&#10;from vllm import LLM, SamplingParams&#10;llm = LLM(model="meta-llama/Llama-3.1-8B-Instruct")&#10;outs = llm.generate(prompts, SamplingParams(temperature=0.7, max_tokens=200))&#10;&#10;# online serving (OpenAI-compatible)&#10;$ vllm serve meta-llama/Llama-3.1-8B-Instruct&#10;$ curl localhost:8000/v1/chat/completions -H "Content-Type: application/json"     -d '{"model": "meta-llama/Llama-3.1-8B-Instruct", "messages": [{"role": "user", "content": "Hi"}]}'</pre></div>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why vLLM became the default open engine

::: cards grid2
### [a] Memory efficiency
PagedAttention gave 2–4× throughput over FasterTransformer and Orca at the same latency (Kwon et al., 2023).

### [e] Lower CPU overhead
The V1 re-architecture isolated the engine loop and reported up to 1.7× higher throughput than V0.

### [b] Breadth
Many model families, quantization formats, hardware back ends and parallelism modes.

### [c] Standard API
OpenAI-compatible endpoints make it a drop-in back end.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "vLLM is a model."
> It is an inference engine; it runs models (mostly from Hugging Face) efficiently.
:::

::: reveal myth
? "vLLM only helps big batches."
> It also reduces per-request latency features (prefix caching, speculative decoding, CUDA graphs), but its biggest wins come from batching.
:::

::: reveal myth
? "PagedAttention is all vLLM does."
> Scheduling, prefix caching, parallelism, quantization and the serving stack matter as much today.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Which process tokenises prompts in vLLM V1 serving?
- [ ] GPU worker
- [ ] EngineCore
- [x] API server
- [ ] DP coordinator
> The <b>API server</b> (input processing), so the engine loop stays free for scheduling.
:::

::: reveal
? Name the two main ways to use vLLM.
> The LLM class for offline batch inference, and vllm serve for an OpenAI-compatible HTTP server.
:::

::: reveal
? What happens to a request's KV blocks when it finishes?
> They are freed back to the pool but keep their hashes, so a later request with the same prefix can reuse them until evicted.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">vLLM is an LLM serving engine: an API server tokenises, the EngineCore schedules a token budget over paged KV blocks each step, GPU workers run the batch, and tokens stream back.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>vLLM is an open-source inference and serving engine. You use it offline through the LLM class, which batches a list of prompts, or online with vllm serve, an OpenAI-compatible server. Inside, an API server process tokenises requests and streams results; an engine-core process runs a loop that schedules every step, deciding how many tokens each request gets and allocating paged KV-cache blocks; GPU worker processes run the batched forward pass and sample tokens. Its origin is PagedAttention, which raised throughput two to four times by eliminating KV memory waste.</p></div>
    <div class="recap"><div><span><b>Problem:</b> efficient multi-user LLM serving is hard.</span></div><div><span><b>Core idea:</b> API server → EngineCore (schedule, KV) → GPU workers.</span></div><div><span><b>Use:</b> LLM class offline; vllm serve online.</span></div></div>
    <p class="start-hint">Next: <a href="../02-engine-architecture/index.html">02 · Engine architecture →</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
