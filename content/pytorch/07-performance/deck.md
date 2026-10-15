---
title: 'Performance: Compile, SDPA, Memory'
body:
  data-deck: 'Performance: compile, SDPA, memory'
  data-home: ../index.html
  data-home-label: PyTorch
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'Python model :: eager :: f'
  - 'TorchDynamo :: capture graphs + guards :: c'
  - 'AOTAutograd :: forward + backward graph :: a'
  - 'TorchInductor :: fused Triton / C++ kernels :: e'
  caption: Default backend "inductor"; modes default, reduce-overhead, max-autotune, max-autotune-no-cudagraphs.
example:
  title: 'Worked example: attention memory'
  setup: One layer, 32 heads, head dimension 128, BF16 (2 bytes). Notebook 07 computes the sizes.
  steps:
  - 'T = 1,024: the score matrix (B·H·T·T) is <b>0.06 GiB</b> versus 0.023 GiB for q, k and v together.'
  - 'T = 8,192: scores <b>4 GiB</b> versus 0.19 GiB for q, k, v: 21× larger, per layer, before softmax copies.'
  - 'T = 131,072: scores would be <b>1,024 GiB</b>; q, k, v are 3 GiB. Only fused attention that never materialises the matrix makes this feasible.'
  - The PyTorch 2 paper reports torch.compile speedups of 2.27× (inference) and 1.41× (training), geometric mean over 180+ models on an A100.
  result: Kernel fusion saves memory traffic; fused attention removes the quadratic memory term.
traps:
  tricks:
  - 'mode="reduce-overhead". :: Uses CUDA graphs; good for small batches and decode.'
  - 'torch._dynamo.explain(fn)(x). :: Lists graph breaks and their reasons.'
  - 'torch.cuda.max_memory_allocated(). :: Peak memory; reset with reset_peak_memory_stats().'
  traps:
  - 'Data-dependent Python branches. :: if x.sum() > 0 breaks the graph.'
  - 'Benchmarking the first call. :: It includes compilation; warm up first.'
  - 'Recompilation on changing shapes. :: Mark dynamic dims or pad to buckets.'
papers:
- pytorch2
- pt_compile
- pt_sdpa
- pt_cuda
- fa1
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">PyTorch for LLMs · 07</div>
    <h1>Performance: compile, SDPA and memory</h1>
    <p class="sub">Making PyTorch fast: torch.compile (TorchDynamo + AOTAutograd + TorchInductor), graph breaks, fused attention with scaled_dot_product_attention, and reading GPU memory usage.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Eager PyTorch launches one kernel per operation and writes every intermediate to memory. Attention materialises a T × T matrix. Both waste time and memory at LLM scale.</div>
      <div class="c"><b>Core idea</b><b>torch.compile</b> captures your Python into graphs (<b>TorchDynamo</b>), adds the backward (<b>AOTAutograd</b>) and generates fused kernels (<b>TorchInductor</b>: Triton on GPUs, C++ on CPUs). <b>Graph breaks</b> split graphs and cost speed. <b>SDPA</b> uses fused attention kernels that never store the score matrix. Memory is read with <code>torch.cuda.max_memory_allocated()</code> and the profiler.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## The quadratic memory term

Memory of one attention layer's score matrix (B · H · T · T) versus q, k, v (3 · B · H · T · D), BF16. Fused attention keeps only the latter.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">sequence T = 2^ <input type="range" id="aT" min="9" max="17" step="1" value="13"> <output id="aTo"></output></label><label class="ctl">heads <input type="range" id="aH" min="8" max="128" step="8" value="32"> <output id="aHo"></output></label><label class="ctl">batch <input type="range" id="aB" min="1" max="16" step="1" value="1"> <output id="aBo"></output></label></div>
  <div id="aBars" style="margin-top:12px"></div>
  <p class="readout" id="aOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Where eager PyTorch loses time

::: cards grid3
### [d] Kernel launches
Each elementwise op is its own kernel with launch overhead.

### [b] Memory round trips
Every intermediate is written to HBM and read back.

### [c] Materialised attention
Scores and probabilities of size T × T per head.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Which line breaks the graph?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? In a compiled function, which line causes a graph break?
- [ ] y = torch.relu(x @ w)
- [x] if y.mean() > 0: y = y * 2
- [ ] y = y.view(B, T, -1)
- [ ] y = F.gelu(y) + b
> <b>B.</b> Branching on a tensor's value requires running the graph to know which way to go, so Dynamo splits there.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Three tools

::: cards grid3
### [c] torch.compile
Dynamo captures graphs with guards; Inductor fuses ops and generates Triton/C++ kernels.

### [a] SDPA
F.scaled_dot_product_attention → FlashAttention / efficient / cuDNN kernels: exact attention, linear memory.

### [e] Memory tools
memory_allocated, max_memory_allocated, memory snapshots and torch.profiler show where memory and time go.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Compile modes

<div class="visual scroll-x"><table class="tbl">
  <tr><th>mode</th><th>What it does (PyTorch 2.14.1 docstring)</th></tr>
  <tr><td>"default"</td><td>good balance between performance and overhead</td></tr>
  <tr><td>"reduce-overhead"</td><td>reduces Python overhead with CUDA graphs; useful for small batches; more memory</td></tr>
  <tr><td>"max-autotune"</td><td>Triton or template matmuls and convolutions; CUDA graphs on by default on GPU</td></tr>
  <tr><td>"max-autotune-no-cudagraphs"</td><td>like max-autotune without CUDA graphs</td></tr>
</table></div>

::: deep Graph breaks in practice
Notebook 07: a function with a data-dependent if and a print becomes several graphs; the clean version is one graph. torch._dynamo.explain reports graph_count, graph_break_count and reasons. Use fullgraph=True to turn breaks into errors.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why these help

::: cards grid2
### [a] Fusion
Elementwise chains become one kernel: one read, one write.

### [e] Tiling
FlashAttention computes softmax blockwise in on-chip memory (Architecture deck 09).

### [b] Guards keep it correct
Compiled code is reused only when shapes, dtypes and globals match; otherwise recompile.

### [c] Measurable
Profiler traces and memory stats turn guesses into numbers.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "torch.compile changes results."
> It preserves semantics up to floating-point reordering (notebook 07: max difference below 10⁻⁴).
:::

::: reveal myth
? "Compiling always speeds things up."
> Small CPU workloads may see nothing (notebook 07); gains are largest on GPUs with fusable ops.
:::

::: reveal myth
? "FlashAttention is approximate."
> It computes exact attention with an online softmax.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Default torch.compile backend?
- [ ] "eager"
- [ ] "aot_eager"
- [x] "inductor"
- [ ] "cudagraphs"
> <b>"inductor"</b>.
:::

::: reveal
? Name the three components of torch.compile.
> TorchDynamo (graph capture), AOTAutograd (backward graph), TorchInductor (code generation).
:::

::: reveal
? Score-matrix memory for B = 1, H = 32, T = 8,192 in BF16?
> 32 × 8,192² × 2 bytes = 4 GiB per layer.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">torch.compile captures and fuses your model (Dynamo + AOTAutograd + Inductor), SDPA removes attention's quadratic memory, and memory stats and the profiler tell you what to fix.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Eager PyTorch launches a kernel per operation and writes every intermediate to memory. torch compile captures your Python into graphs with TorchDynamo, builds the backward with AOTAutograd, and generates fused Triton or C++ kernels with TorchInductor; the PyTorch 2 paper measured 2.27 times faster inference and 1.41 times faster training on average. Data-dependent branches cause graph breaks, which explain can find. For attention, scaled dot product attention uses fused kernels that never store the T by T score matrix, which at 8,192 tokens is 4 gibibytes per layer. Memory statistics and the profiler show the rest.</p></div>
    <div class="recap"><div><span><b>Problem:</b> kernel overhead, memory traffic, T² attention.</span></div><div><span><b>Core idea:</b> compile = Dynamo + AOTAutograd + Inductor; SDPA.</span></div><div><span><b>Watch:</b> graph breaks, recompiles, peak memory.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/07_compile_and_sdpa.ipynb" target="_blank" rel="noopener">07 · torch.compile and fused attention</a> <span style="color:var(--faint)">· 30 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/07_compile_and_sdpa.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../08-distributed/index.html">08 · Distributed training in PyTorch →</a> · Previous: <a href="../06-mixed-precision/index.html">← 06</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
