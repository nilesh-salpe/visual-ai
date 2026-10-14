---
title: What a GPU Is
body:
  data-deck: What a GPU is
  data-home: ../index.html
  data-home-label: GPU
styles:
- ../../shared/deck.css
- ../../shared/learn.css
css: |-
  #dieSvg g[data-info], #chipSvg [data-info] { cursor: pointer; }
    #dieSvg g[data-info]:hover rect, #chipSvg [data-info]:hover { filter: brightness(1.15); }
    .infobox { min-height: 72px; background: var(--panel-2); border-radius: 10px; padding: 12px 14px; font-size: 14px; color: var(--muted); }
    .infobox b { color: var(--ink); }
    .race { display: grid; gap: 10px; margin-top: 8px; }
    .winner { font: 700 15px 'JetBrains Mono', monospace; }
    .stack { display: grid; gap: 8px; }
    .stack .layer { display: grid; grid-template-columns: 180px 1fr; gap: 14px; align-items: center; background: var(--panel-2); border-radius: 10px; padding: 12px 14px; border-left: 4px solid var(--a); }
    .stack .layer b { font-size: 14px; }
    .stack .layer span { font-size: 14px; color: var(--muted); }
    .stack .arrow { text-align: center; color: var(--faint); font-size: 13px; }
    @media (max-width: 640px) { .stack .layer { grid-template-columns: 1fr; gap: 4px; } }
scripts:
- ../../shared/deck.js
glance:
  steps:
  - 'grid :: all blocks of one kernel :: f'
  - 'blocks :: scheduled onto SMs :: c'
  - 'warps of 32 :: one instruction, 32 lanes :: a'
  - 'Tensor Cores :: matrix multiply per SM :: b'
  - 'HBM :: shared memory pool :: e'
  caption: You write one thread; the hardware runs thousands at once in warps of 32 across 132 SMs (streaming multiprocessors).
example:
  title: 'Worked example: wave quantization'
  setup: An H100 SXM has 132 SMs. A matmul is split into 128 × 128 output tiles, and each SM runs one tile at a time.
  steps:
  - 'Output 1,408 × 1,536 → 11 × 12 = <b>132 tiles</b> → exactly 1 wave: every SM busy, 100% use.'
  - Output 1,536 × 1,536 → 12 × 12 = <b>144 tiles</b> → ⌈144/132⌉ = <b>2 waves</b>; the second wave has only 12 tiles.
  - 'Efficiency = 144 tiles / (2 waves × 132 SMs) = <b>55%</b>: 9% more work takes about twice as long.'
  - 'Fixes: choose shapes whose tile count fills whole waves, use smaller tiles, or split K (split-K) to create more tiles.'
  result: GPU time is quantized in waves of 132 tiles; matrix sizes just above a wave boundary are the most wasteful.
traps:
  tricks:
  - 'Warp = 32 threads. :: Branches inside a warp run one after another (divergence).'
  - 'Occupancy hides latency. :: Enough resident warps per SM let the scheduler switch while others wait on memory.'
  - 'Count waves. :: tiles ÷ SMs, rounded up, sets the runtime.'
  traps:
  - 'Counting CUDA cores as speed. :: For AI, Tensor Core throughput and memory bandwidth matter far more.'
  - 'Divergent branches. :: A warp with an if/else pays for both paths.'
  - 'Shapes just past a wave. :: A slightly larger matrix can take ~2× the time.'
papers:
- h100wp
- hopper_bench
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">GPU for GenAI · 01</div>
    <h1>What a GPU is,<br>and how it thinks</h1>
    <p class="sub">A CPU (central processing unit) is built to finish one task quickly. A GPU (graphics processing unit) is built to finish a huge number of tasks at once. This deck covers the chip, its execution model, and the details that matter in practice: warps, occupancy, Tensor Cores and wave quantization.</p>
    <div class="toc" data-auto></div>
    <p class="start-hint">Press <kbd>→</kbd> or <kbd>Space</kbd> to begin.</p>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-die" data-chapter="Two philosophies">
  <div class="inner">
    <div class="label">01 · Two philosophies</div>
    <h2>Same silicon budget, spent on opposite goals</h2>
    <hr>
    <p class="lede">A CPU spends most of its area on making a <em>single</em> thread fast: big caches, branch predictors and out-of-order logic. A GPU spends it on <em>arithmetic units</em>, and keeps just enough control logic to feed them.</p>
    <div class="visual">
      <svg id="dieSvg" viewBox="0 0 760 300" role="img" aria-label="CPU and GPU die area comparison"></svg>
      <div class="infobox" id="dieInfo">Hover or tap a block to see what it does.</div>
      <div class="legend"><span><i style="background:var(--a)"></i>Arithmetic (ALUs)</span><span><i style="background:var(--b)"></i>Control / scheduling</span><span><i style="background:var(--c)"></i>Cache</span><span><i style="background:var(--faint)"></i>Memory interface</span></div>
    </div>
    <p class="caption">Schematic, not to scale. An H100 has 132 active SMs (streaming multiprocessors), each with 128 FP32 (32-bit floating point) lanes and 4 Tensor Cores, which comes to roughly 17,000 FP32 lanes. A server CPU has a few dozen cores, each with a 16-lane SIMD (single instruction, multiple data) unit.</p>
    <div class="takeaway">A CPU minimizes latency: one thread finishes as fast as possible. A GPU maximizes throughput: the most total work per second, even if each thread is slow.</div>
  
    <!--x:glance--><div class="glance"><h4>At a glance</h4><svg viewBox="0 0 660 152" role="img" aria-label="You write one thread; the hardware runs thousands at once in warps of 32 across 132 SMs (streaming multiprocessors)." class="glance-svg"><defs><marker id="gArr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--muted)"/></marker></defs><rect x="10.0" y="28" width="113.6" height="64" rx="10" style="fill:var(--faint)"/><text x="66.8" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">grid</text><text x="66.8" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">all blocks of one</text><text x="66.8" y="123.0" text-anchor="middle" class="tm" style="font-size:11px">kernel</text><rect x="141.6" y="28" width="113.6" height="64" rx="10" style="fill:var(--c)"/><text x="198.4" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">blocks</text><text x="198.4" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">scheduled onto SMs</text><line x1="125.6" y1="60.0" x2="139.6" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/><rect x="273.2" y="28" width="113.6" height="64" rx="10" style="fill:var(--a)"/><text x="330.0" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">warps of 32</text><text x="330.0" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">one instruction,</text><text x="330.0" y="123.0" text-anchor="middle" class="tm" style="font-size:11px">32 lanes</text><line x1="257.2" y1="60.0" x2="271.2" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/><rect x="404.8" y="28" width="113.6" height="64" rx="10" style="fill:var(--b)"/><text x="461.6" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">Tensor Cores</text><text x="461.6" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">matrix multiply</text><text x="461.6" y="123.0" text-anchor="middle" class="tm" style="font-size:11px">per SM</text><line x1="388.8" y1="60.0" x2="402.8" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/><rect x="536.4" y="28" width="113.6" height="64" rx="10" style="fill:var(--e)"/><text x="593.2" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">HBM</text><text x="593.2" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">shared memory pool</text><line x1="520.4" y1="60.0" x2="534.4" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/></svg><p class="caption" style="margin:4px 0 0">You write one thread; the hardware runs thousands at once in warps of 32 across 132 SMs (streaming multiprocessors).</p></div><!--/x:glance-->
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-race" data-chapter="Two philosophies">
  <div class="inner">
    <div class="label">02 · Two philosophies</div>
    <h2>Small jobs go to the CPU. Big parallel jobs go to the GPU.</h2>
    <hr>
    <p class="lede">Every GPU launch has a fixed overhead before any math starts. Drag the slider to change the size of the job and watch where the crossover happens.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">Work size (FLOPs) <input type="range" id="raceN" min="3" max="13" step="0.1" value="6"> <output id="raceNo"></output></label>
      </div>
      <div class="race" id="raceBars"></div>
      <p class="winner" id="raceWin"></p>
    </div>
    <p class="caption">Illustrative model: CPU at about 4 TFLOPS (trillion floating-point operations per second) of FP32 with no launch cost. GPU at about 60 TFLOPS of FP32 (no Tensor Cores) plus about 10 µs of launch and sync overhead. With Tensor Cores the GPU side gets about 15× faster still.</p>
    <div class="takeaway">This is why small kernels hurt. A transformer step that runs thousands of tiny kernels is limited by launch overhead, not math. CUDA (Compute Unified Device Architecture, NVIDIA's programming platform for its graphics processors) Graphs and <code>torch.compile</code> fusion exist to fix exactly that.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-chip" data-chapter="Anatomy">
  <div class="inner">
    <div class="label">03 · Anatomy</div>
    <h2>Inside an H100: GPCs, SMs, L2, and HBM</h2>
    <hr>
    <p class="lede">The basic building block is the <b>Streaming Multiprocessor (SM)</b>. SMs are grouped into GPCs (graphics processing clusters), they share one L2 cache, and they read from HBM (high-bandwidth memory) stacks placed next to the die. Click any part.</p>
    <div class="grid2">
      <div class="visual" style="margin-top:0"><svg id="chipSvg" viewBox="0 0 640 380" role="img" aria-label="H100 chip layout"></svg></div>
      <div class="visual" style="margin-top:0"><svg id="smSvg" viewBox="0 0 400 380" role="img" aria-label="Inside one SM"></svg></div>
    </div>
    <div class="infobox" id="chipInfo" style="margin-top:12px"><b>Full GH100 die:</b> 8 GPCs × 9 TPCs (texture processing clusters) × 2 SMs = 144 SMs. The H100 SXM (NVIDIA's socketed module form factor for data-center graphics processors) product enables <b>132</b>; the rest are fused off to improve manufacturing yield (shown greyed out).</div>
    <div class="cite">NVIDIA H100 Tensor Core GPU Architecture whitepaper (2022). Which SMs are disabled varies from chip to chip; the pattern here is illustrative.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-warps" data-chapter="Programming model">
  <div class="inner">
    <div class="label">04 · Programming model</div>
    <h2>Threads → warps of 32 → blocks → grid</h2>
    <hr>
    <p class="lede">You write code for one <b>thread</b>. Threads are grouped into <b>blocks</b>, and each block runs on a single SM. The hardware runs a block as <b>warps</b> of 32 threads that execute in lockstep. Pick a block size and see what the warps look like.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">Elements N <input type="range" id="wN" min="100" max="20000" step="100" value="10000"> <output id="wNo"></output></label>
        <label class="ctl">Threads / block <input type="range" id="wT" min="1" max="1024" step="1" value="200"> <output id="wTo"></output></label>
      </div>
      <div class="grid4" style="margin:14px 0">
        <div class="stat"><div class="num" id="wBlocks"></div><div class="lbl">blocks in grid</div></div>
        <div class="stat"><div class="num" id="wWarps"></div><div class="lbl">warps per block</div></div>
        <div class="stat"><div class="num" id="wUtil"></div><div class="lbl">lanes doing work in each block</div></div>
        <div class="stat"><div class="num" id="wIdle"></div><div class="lbl">idle lanes in last warp</div></div>
      </div>
      <svg id="warpSvg" viewBox="0 0 660 220" role="img" aria-label="Warps in one block"></svg>
      <div class="legend"><span><i style="background:var(--a)"></i>active lane</span><span><i style="background:var(--line)"></i>idle lane (padding)</span></div>
    </div>
    <div class="takeaway">Always use block sizes that are multiples of 32, such as 128, 256 or 512. With a size like 200, the last warp of every block leaves lanes idle.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-div" data-chapter="Programming model">
  <div class="inner">
    <div class="label">05 · Programming model</div>
    <h2>SIMT: one instruction, 32 lanes, and the cost of <code>if</code></h2>
    <hr>
    <p class="lede">A warp issues one instruction at a time to all 32 lanes. When lanes take different branches, the warp runs <b>each path in turn</b> with the inactive lanes masked off. This is called divergence.</p>
    <div class="visual">
      <div class="seg" id="divSeg">
        <button data-v="none" class="on">No branch</button>
        <button data-v="half">if (i % 2)</button>
        <button data-v="rare">if (i &lt; 4) expensive()</button>
        <button data-v="four">switch (i % 4)</button>
      </div>
      <svg id="divSvg" viewBox="0 0 660 230" style="margin-top:12px" role="img" aria-label="Warp execution passes"></svg>
      <div class="grid3"><div class="stat"><div class="num" id="divPass"></div><div class="lbl">serialized passes</div></div>
        <div class="stat"><div class="num" id="divUtil"></div><div class="lbl">lane utilization</div></div>
        <div class="stat"><div class="num" id="divNote" style="font-size:15px;font-family:Inter"></div><div class="lbl">why</div></div></div>
    </div>
    <div class="takeaway">Dense linear algebra rarely branches, which is one reason it suits GPUs so well. Data-dependent control flow, such as MoE (Mixture of Experts) routing, sampling or sparse ops, is where divergence and imbalance show up.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-hide" data-chapter="Programming model">
  <div class="inner">
    <div class="label">06 · Programming model</div>
    <h2>GPUs hide memory latency by switching warps</h2>
    <hr>
    <p class="lede">A load from HBM takes hundreds of cycles. A CPU covers that wait with big caches and out-of-order execution. A GPU covers it by <b>switching to another warp that is ready to run</b>, which costs no cycles. That only works if enough warps are resident, which is called <b>occupancy</b>.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">Resident warps <input type="range" id="hW" min="1" max="16" step="1" value="3"> <output id="hWo"></output></label>
        <label class="ctl">Memory latency (cycles) <input type="range" id="hL" min="100" max="800" step="20" value="400"> <output id="hLo"></output></label>
      </div>
      <svg id="hideSvg" viewBox="0 0 660 300" style="margin-top:12px" role="img" aria-label="Warp scheduling timeline"></svg>
      <div class="legend"><span><i style="background:var(--a)"></i>issuing math</span><span><i style="background:var(--panel-2);border:1px solid var(--line)"></i>waiting on memory</span><span><i style="background:var(--b)"></i>scheduler busy</span></div>
      <p class="readout" id="hideOut" style="margin-top:8px"></p>
    </div>
    <p class="caption">Model: each warp computes for 40 cycles, then waits <em>L</em> cycles for a load. You need about (40 + L) / 40 warps to keep the scheduler busy. Occupancy is capped by registers (64K 32-bit registers per SM), shared memory per block, and a hard limit of 64 warps per SM.</p>
    <div class="takeaway">"Why does my kernel use 255 registers per thread and run slowly?" Too many registers per thread means fewer resident warps, and with fewer warps the memory stalls are no longer hidden.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-tc" data-chapter="Tensor Cores">
  <div class="inner">
    <div class="label">07 · Tensor Cores</div>
    <h2>Tensor Cores: hardware that does a matrix multiply in one step</h2>
    <hr>
    <p class="lede">A CUDA core does one fused multiply-add per lane per cycle. A Tensor Core does a whole small <b>matrix multiply-accumulate</b>, <code>D = A·B + C</code>, on a tile in a single operation. Almost all of an H100's headline FLOPs (floating-point operations) come from Tensor Cores.</p>
    <div class="grid2">
      <div class="visual" style="margin-top:0">
        <svg id="mmaSvg" viewBox="0 0 380 220" role="img" aria-label="Matrix multiply accumulate"></svg>
        <p class="caption" style="margin-top:4px">Each partition of an SM has one Tensor Core; a warp issues an MMA instruction (Hopper adds <code>wgmma</code> across 4 warps) and the tile math happens in hardware.</p>
      </div>
      <div class="visual" style="margin-top:0">
        <div class="seg" id="tcSeg"><button data-v="dense" class="on">Dense</button><button data-v="sparse">2:4 sparse</button></div>
        <div id="tcBars" style="margin-top:14px"></div>
        <p class="caption">H100 SXM peak throughput in TFLOPS (TOPS (trillion operations per second) for INT8 (8-bit integer)). Log scale.</p>
      </div>
    </div>
    <div class="takeaway">If your work isn't a matmul in BF16 (bfloat16, a 16-bit floating-point format with the exponent range of 32-bit floats) or FP8 (8-bit floating point), you are using about 7% of the chip. That's why everything in a transformer is arranged around GEMMs (general matrix multiplications).</div>
    <div class="cite">NVIDIA H100 datasheet (SXM5): FP64 34, FP64 Tensor 67, FP32 67, TF32 Tensor 495, BF16 Tensor 989, FP8 Tensor 1,979, INT8 Tensor 1,979 (dense). The 2:4 structured sparsity numbers are twice these.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-wave" data-chapter="Tensor Cores">
  <div class="inner">
    <div class="label">08 · Tensor Cores</div>
    <h2>A matmul is split into tiles, and the tiles run in waves across 132 SMs</h2>
    <hr>
    <p class="lede">A GEMM kernel cuts the output matrix into tiles and gives each tile to one SM (one thread block). If the tile count doesn't divide evenly by 132, the last <b>wave</b> leaves most SMs idle.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">M <input type="range" id="qM" min="128" max="4096" step="128" value="1536"> <output id="qMo"></output></label>
        <label class="ctl">N <input type="range" id="qN" min="128" max="4096" step="128" value="1536"> <output id="qNo"></output></label>
        <div class="seg" id="qT"><button data-v="64">tile 64</button><button data-v="128" class="on">tile 128</button><button data-v="256">tile 256</button></div>
      </div>
      <div class="grid4" style="margin:14px 0">
        <div class="stat"><div class="num" id="qTiles"></div><div class="lbl">output tiles</div></div>
        <div class="stat"><div class="num" id="qWaves"></div><div class="lbl">waves over 132 SMs</div></div>
        <div class="stat"><div class="num" id="qLast"></div><div class="lbl">SMs busy in last wave</div></div>
        <div class="stat"><div class="num" id="qEff"></div><div class="lbl">SM utilization</div></div>
      </div>
      <svg id="waveSvg" style="max-width:640px;margin:0 auto" viewBox="0 0 660 330" role="img" aria-label="Output tiles colored by wave"></svg>
      <div class="legend"><span><i style="background:var(--a)"></i>full wave (odd)</span><span><i style="background:var(--c)"></i>full wave (even)</span><span><i style="background:var(--b)"></i>partial last wave</span></div>
    </div>
    <div class="takeaway">Try M = N = 1536: that gives 144 tiles, which is 132 + 12, so the chip runs 2 waves and the second one has 120 SMs idle. Choosing dimensions that are multiples of 64 or 128 and fit the SM count can give speedups of 10–40%.</div>
  </div>
</section>

<!-- slide id="s-example" from="example" chapter="Example" tag="Worked example" tagclass="b5" -->

<!-- slide raw -->
<section class="slide" id="s-stack" data-chapter="Software">
  <div class="inner">
    <div class="label">09 · Software</div>
    <h2>From <code>model(x)</code> to silicon</h2>
    <hr>
    <div class="visual stack">
      <div class="layer"><b>PyTorch / JAX</b><span>The ops in your graph. Eager mode launches each op as its own kernel; <code>torch.compile</code> and XLA fuse ops together.</span></div>
      <div class="arrow">↓ dispatch</div>
      <div class="layer" style="border-color:var(--c)"><b>Kernel libraries</b><span>cuBLAS and CUTLASS (GEMMs), cuDNN, FlashAttention, Triton-generated kernels, and NCCL (NVIDIA Collective Communications Library) for communication.</span></div>
      <div class="arrow">↓ launch &lt;&lt;&lt;grid, block&gt;&gt;&gt;</div>
      <div class="layer" style="border-color:var(--b)"><b>CUDA runtime + driver</b><span>Queues kernels on <b>streams</b>, which run asynchronously. CUDA Graphs record a whole sequence and replay it, avoiding most of the CPU launch overhead.</span></div>
      <div class="arrow">↓ hardware scheduler</div>
      <div class="layer" style="border-color:var(--e)"><b>GPU</b><span>The block scheduler assigns thread blocks to SMs; inside each SM, warp schedulers issue instructions to the CUDA cores and Tensor Cores.</span></div>
    </div>
    <div class="takeaway">The CPU only enqueues work. If the GPU sits idle between kernels in a profile, the CPU is the bottleneck. The usual fixes are bigger kernels, fusion and CUDA Graphs.</div>
  </div>
</section>

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="Tricks and traps" tagclass="b7" -->

<!-- slide raw -->
<section class="slide" id="s-qa" data-chapter="Test yourself">
  <div class="inner">
    <div class="label">10 · Test yourself</div>
    <h2>Questions to test your understanding</h2>
    <hr>
    <details class="qa"><summary>Why does a GPU need tens of thousands of threads in flight?</summary><div class="ans">To <b>hide latency</b>. An HBM access takes hundreds of cycles, and a GPU core has no large caches or out-of-order engine to cover that. Instead, every cycle the warp scheduler picks a warp that is ready to run. With too few resident warps (low occupancy), the units sit idle waiting on memory. By Little's law, the parallelism you need equals latency × throughput.</div></details>
    <details class="qa"><summary>What is a warp, and why does divergence hurt?</summary><div class="ans">A warp is a group of <b>32 threads that execute one instruction together</b> (SIMT (single instruction, multiple threads)). When threads in a warp take different branches, the paths run one after another with lanes masked off, so utilization drops by the number of distinct paths. Fixes: arrange data so the threads in a warp take the same branch, or use branch-free arithmetic.</div></details>
    <details class="qa"><summary>A 1536×1536 GEMM gets fewer TFLOPS than a 2048×2048 one. Why?</summary><div class="ans"><b>Wave quantization.</b> With 128×128 tiles there are 144 output tiles. On 132 SMs that means 2 waves, and the second runs only 12 tiles, so about 45% of SM time is wasted. The 2048 case gives 256 tiles, also 2 waves but much better filled. Small matrices also have low arithmetic intensity. Fixes: pad dimensions, use split-K or stream-K kernels, or choose a different tile size.</div></details>
    <details class="qa"><summary>What's the difference between CUDA cores and Tensor Cores?</summary><div class="ans">CUDA cores are scalar FP32/INT (integer) lanes, each doing one FMA (fused multiply-add) per cycle. Tensor Cores are dedicated matrix-multiply-accumulate units working in BF16, FP16 (16-bit floating point), TF32 (TensorFloat-32), FP8 and, on Blackwell, FP4 (4-bit floating point). On an H100, BF16 Tensor Core throughput (989 TFLOPS dense) is about <b>15× the FP32 CUDA-core peak</b>. Softmax, layernorm and activation functions run on CUDA cores. That's why fusing them, or overlapping them with GEMMs as FlashAttention-3 does, matters so much.</div></details>
    <details class="qa"><summary>What limits occupancy, and is higher occupancy always better?</summary><div class="ans">Three things limit it: <b>registers per thread</b> (64K registers per SM, so 128 registers per thread allows at most 512 threads, or 16 warps), <b>shared memory per block</b> (up to 228 KB per SM on H100), and the cap on threads and blocks per SM (64 warps). Higher occupancy is <b>not always better</b>. Well-tuned GEMM and attention kernels often run at low occupancy with big tiles held in registers, and hide latency through instruction-level parallelism and asynchronous copies (TMA (Tensor Memory Accelerator)) instead.</div></details>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-end" data-chapter="Test yourself">
  <div class="inner">
    <div class="label">11 · Take it with you</div>
    <h2>Four things to remember</h2>
    <hr>
    <div class="recap">
      <div><span><b>A GPU trades per-thread latency for throughput.</b> It has thousands of simple lanes, little cache, and hides latency by switching warps.</span></div>
      <div><span><b>The hierarchy is grid → block (on one SM) → warp (32 threads in lockstep) → thread.</b> Block sizes should be multiples of 32, and divergence is serialized.</span></div>
      <div><span><b>Tensor Cores provide nearly all the FLOPs.</b> The work has to be expressed as BF16 or FP8 matmuls to use them.</span></div>
      <div><span><b>Tile counts and SM counts interact.</b> Wave quantization and launch overhead are the most common causes of "the GPU isn't busy".</span></div>
    </div>
    <p class="start-hint">Next: <a href="../02-why-gpus-for-ai/index.html">02 · Why GPUs for AI →</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
