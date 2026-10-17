---
title: GPU Memory Hierarchy
body:
  data-deck: Memory hierarchy
  data-home: ../index.html
  data-home-label: GPU
styles:
- ../../shared/deck.css
- ../../shared/learn.css
css: |-
  #pyr g { cursor: pointer; }
    #pyr g:hover polygon { filter: brightness(1.1); }
    .lvl-card { min-height: 150px; }
    .lvl-card .grid3 { margin-top: 10px; }
scripts:
- ../../shared/deck.js
glance:
  steps:
  - 'registers :: per thread :: a'
  - 'shared memory / L1 :: 228 KB per SM :: c'
  - 'L2 :: 50 MB, whole GPU :: b'
  - 'HBM :: 80 GB, 3.35 TB/s :: e'
  - 'host DRAM / NVMe :: behind PCIe :: f'
  caption: 'Each step down: bigger, slower, more energy per byte. Fast kernels keep data high in this list.'
example:
  title: 'Worked example: does a 7B model fit for training?'
  setup: 'Mixed-precision training with Adam: BF16 weights (2) + BF16 grads (2) + FP32 master weights (4) + two FP32 Adam moments (8) = 16 bytes per parameter, before
    activations.'
  steps:
  - 7B parameters × 16 bytes = <b>112 GB</b>, more than one 80 GB H100.
  - 'ZeRO-3 (Zero Redundancy Optimizer) across 8 GPUs shards all of it: <b>14 GB</b> per GPU.'
  - '70B parameters: <b>1,120 GB</b> of state → ≥ 14 GPUs just to hold it, before activations.'
  - Activations scale with batch × sequence × layers; activation checkpointing trades recompute for memory.
  result: Capacity, not FLOPs, usually decides the minimum number of GPUs for training.
traps:
  tricks:
  - '16 bytes/param for Adam training. :: Plus activations.'
  - 'Tiling cuts traffic by the tile size. :: Load once into shared memory, reuse T times.'
  - 'Fuse elementwise ops. :: One trip to HBM instead of one per op.'
  traps:
  - 'Counting only weights. :: Gradients and optimizer states are 6× the BF16 weights.'
  - 'Ignoring energy. :: A DRAM access costs far more energy than a multiply (Horowitz).'
  - 'Offloading to host memory freely. :: PCIe is ~50× slower than HBM.'
papers:
- horowitz
- fa1
- zero
- vllm
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">GPU for GenAI · 03</div>
    <h1>The memory hierarchy:<br>where performance is decided</h1>
    <p class="sub">Most GPU (graphics processing unit) performance work is about not moving bytes. This deck goes level by level from registers out to NVMe (Non-Volatile Memory Express, the fast interface for flash storage), then covers the techniques that keep data close to the compute: tiling, fusion, FlashAttention and paged KV (key-value) caches.</p>
    <div class="toc" data-auto></div>
    <p class="start-hint">Press <kbd>→</kbd> or <kbd>Space</kbd> to begin.</p>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-pyr" data-chapter="The levels">
  <div class="inner">
    <div class="label">01 · The levels</div>
    <h2>Each level down is about 10× bigger and much slower</h2>
    <hr>
    <div class="grid2">
      <div class="visual" style="margin-top:0"><svg id="pyr" viewBox="0 0 420 360" role="img" aria-label="Memory pyramid"></svg></div>
      <div class="visual lvl-card" style="margin-top:0">
        <h3 id="lvName"></h3>
        <p class="caption" id="lvDesc" style="margin-top:0"></p>
        <div class="grid3">
          <div class="stat"><div class="num" id="lvSize" style="font-size:22px"></div><div class="lbl">capacity (H100 node)</div></div>
          <div class="stat"><div class="num" id="lvBW" style="font-size:22px"></div><div class="lbl">bandwidth</div></div>
          <div class="stat"><div class="num" id="lvLat" style="font-size:22px"></div><div class="lbl">latency</div></div>
        </div>
        <div id="lvBars" style="margin-top:18px"></div>
        <p class="caption">Bandwidth per GPU, log scale.</p>
      </div>
    </div>
    <div class="cite">H100 SXM figures from NVIDIA's whitepaper and datasheet. On-chip bandwidths and latencies are approximate and come from microbenchmark studies; they vary by access pattern.</div>
  
    <!--x:glance--><div class="glance"><h4>At a glance</h4><svg viewBox="0 0 660 138" role="img" aria-label="Each step down: bigger, slower, more energy per byte. Fast kernels keep data high in this list." class="glance-svg"><defs><marker id="gArr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--muted)"/></marker></defs><rect x="10.0" y="28" width="113.6" height="64" rx="10" style="fill:var(--a)"/><text x="66.8" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">registers</text><text x="66.8" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">per thread</text><rect x="141.6" y="28" width="113.6" height="64" rx="10" style="fill:var(--c)"/><text x="198.4" y="57.5" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">shared memory</text><text x="198.4" y="72.5" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">/ L1</text><text x="198.4" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">228 KB per SM</text><line x1="125.6" y1="60.0" x2="139.6" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/><rect x="273.2" y="28" width="113.6" height="64" rx="10" style="fill:var(--b)"/><text x="330.0" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">L2</text><text x="330.0" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">50 MB, whole GPU</text><line x1="257.2" y1="60.0" x2="271.2" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/><rect x="404.8" y="28" width="113.6" height="64" rx="10" style="fill:var(--e)"/><text x="461.6" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">HBM</text><text x="461.6" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">80 GB, 3.35 TB/s</text><line x1="388.8" y1="60.0" x2="402.8" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/><rect x="536.4" y="28" width="113.6" height="64" rx="10" style="fill:var(--faint)"/><text x="593.2" y="57.5" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">host DRAM /</text><text x="593.2" y="72.5" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">NVMe</text><text x="593.2" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">behind PCIe</text><line x1="520.4" y1="60.0" x2="534.4" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/></svg><p class="caption" style="margin:4px 0 0">Each step down: bigger, slower, more energy per byte. Fast kernels keep data high in this list.</p></div><!--/x:glance-->
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-energy" data-chapter="The levels">
  <div class="inner">
    <div class="label">02 · The levels</div>
    <h2>Fetching a number from DRAM costs ~170× more energy than multiplying it</h2>
    <hr>
    <p class="lede">The gap shows up in energy as well as time. A chip that ships every operand to and from DRAM (dynamic random-access memory) would spend most of its power budget moving data.</p>
    <div class="visual"><div id="enBars"></div></div>
    <p class="caption">Energy per operation, 45 nm process (log scale). Newer nodes shrink every number, but the <em>ratio</em> between arithmetic and off-chip access has stayed huge.</p>
    <div class="takeaway">This is the physics behind every optimization in this deck: reuse data that is already on-chip and avoid round trips to HBM (high-bandwidth memory).</div>
    <div class="cite">M. Horowitz, "Computing's Energy Problem (and what we can do about it)", ISSCC 2014.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-tile" data-chapter="Keep data close">
  <div class="inner">
    <div class="label">03 · Keep data close</div>
    <h2>Tiling: load a block into shared memory once, then use it T times</h2>
    <hr>
    <p class="lede">A naive matmul reads A[i,k] and B[k,j] from memory for every multiply-add. A tiled kernel loads a T×K strip of A and a K×T strip of B into SRAM (static random-access memory, fast on-chip memory), computes a whole T×T output tile from them, and so cuts memory traffic by a factor of T.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">Tile size T <input type="range" id="tT" min="0" max="8" step="1" value="5"> <output id="tTo"></output></label>
        <label class="ctl">Matrix N <input type="range" id="tN" min="10" max="14" step="1" value="13"> <output id="tNo"></output></label>
      </div>
      <div class="grid2" style="margin-top:12px;align-items:center">
        <svg id="tileSvg" viewBox="0 0 400 220" role="img" aria-label="Tiled matmul"></svg>
        <div>
          <div class="grid2">
            <div class="stat"><div class="num" id="tTraffic"></div><div class="lbl">loaded into SMs (streaming multiprocessors)</div></div>
            <div class="stat"><div class="num" id="tAI"></div><div class="lbl">FLOPs (floating-point operations) per byte loaded</div></div>
          </div>
          <div id="tBars" style="margin-top:14px"></div>
          <p class="caption" id="tSram"></p>
        </div>
      </div>
    </div>
    <p class="caption">Model: square output tiles, BF16 (bfloat16, a 16-bit floating-point format with the exponent range of 32-bit floats) values. Real GEMMs (general matrix multiplications) also order their tiles so that neighbouring blocks reuse each other's strips in <b>L2</b>, which cuts HBM traffic further.</p>
    <div class="takeaway">Tile size is limited by SRAM capacity (228 KB of shared memory per SM) and registers. That limit is why kernel writers obsess over tile shapes, and why Hopper added TMA (Tensor Memory Accelerator) to copy tiles asynchronously.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-fuse" data-chapter="Keep data close">
  <div class="inner">
    <div class="label">04 · Keep data close</div>
    <h2>Kernel fusion: one trip to HBM instead of five</h2>
    <hr>
    <p class="lede">After a GEMM, a typical MLP (multilayer perceptron) block runs bias-add → GELU (Gaussian Error Linear Unit) → dropout → residual-add. Run as separate kernels, each one <b>reads the whole tensor from HBM and writes it back</b>. A fused kernel keeps the values in registers.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <div class="seg" id="fMode"><button data-v="0" class="on">Unfused (eager)</button><button data-v="1">Fused</button></div>
        <label class="ctl">Tokens × hidden <input type="range" id="fS" min="20" max="30" step="1" value="25"> <output id="fSo"></output></label>
      </div>
      <svg id="fuseSvg" viewBox="0 0 660 200" style="margin-top:12px" role="img" aria-label="Kernel fusion diagram"></svg>
      <div class="grid3" style="margin-top:8px">
        <div class="stat"><div class="num" id="fBytes"></div><div class="lbl">HBM traffic</div></div>
        <div class="stat"><div class="num" id="fTime"></div><div class="lbl">time at 3.35 TB/s</div></div>
        <div class="stat"><div class="num" id="fLaunch"></div><div class="lbl">kernel launches</div></div>
      </div>
    </div>
    <div class="takeaway">That is what <code>torch.compile</code> (Inductor + Triton), XLA, and hand-written fused kernels do. Fusion doesn't reduce the FLOPs at all; the speedup comes from fewer bytes moved and fewer kernel launches.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-flash" data-chapter="Keep data close">
  <div class="inner">
    <div class="label">05 · Keep data close</div>
    <h2>FlashAttention never writes the N×N attention matrix to HBM</h2>
    <hr>
    <p class="lede">Standard attention writes <code>S = QKᵀ</code> (N×N) to HBM, reads it back for softmax, then writes and reads it again for the weighted sum. FlashAttention streams K/V tiles through SRAM and uses an <b>online softmax</b> (a running max and running sum), so the full matrix never exists in memory.</p>
    <div class="grid2">
      <div class="visual" style="margin-top:0">
        <svg id="faSvg" viewBox="0 0 360 300" role="img" aria-label="FlashAttention tiling animation"></svg>
        <div class="controls"><button class="btn" id="faPlay">Pause</button><span class="caption" style="margin:0" id="faStep"></span></div>
      </div>
      <div class="visual" style="margin-top:0">
        <label class="ctl">Sequence length <input type="range" id="faN" min="10" max="17" step="1" value="13"> <output id="faNo"></output></label>
        <h3 style="margin-top:14px">Memory for scores (per head)</h3>
        <div id="faMem"></div>
        <h3 style="margin-top:14px">HBM traffic for attention (per head)</h3>
        <div id="faTraffic"></div>
        <p class="caption">Model: head dim 128, BF16, 128-row tiles. The standard version runs scale, mask, softmax and dropout as separate kernels.</p>
      </div>
    </div>
    <div class="takeaway">Score memory drops from O(N²) to O(N), and HBM traffic drops several-fold. The FLOPs are the same or slightly <em>higher</em> (there is recomputation in the backward pass), yet it runs 2–4× faster. That is the clearest example of attention being limited by IO (input/output, memory reads and writes) rather than compute.</div>
    <div class="cite">Dao et al., "FlashAttention" (2022); FlashAttention-2 (2023); FlashAttention-3 (2024, Hopper: async TMA + FP8).</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-train" data-chapter="Capacity">
  <div class="inner">
    <div class="label">06 · Capacity</div>
    <h2>Training memory: 16 bytes per parameter before activations</h2>
    <hr>
    <p class="lede">Mixed-precision Adam stores BF16 weights (2 B) + BF16 gradients (2 B) + FP32 (32-bit floating point) master weights, momentum and variance (12 B). <b>ZeRO (Zero Redundancy Optimizer) and FSDP (Fully Sharded Data Parallel)</b> shard these across data-parallel ranks.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">Params <input type="range" id="zP" min="0" max="2.7" step="0.01" value="1.845"> <output id="zPo"></output></label>
        <label class="ctl">DP ranks <input type="range" id="zD" min="0" max="10" step="1" value="6"> <output id="zDo"></output></label>
        <div class="seg" id="zS"><button data-v="0">No sharding</button><button data-v="1">ZeRO-1</button><button data-v="2">ZeRO-2</button><button data-v="3" class="on">ZeRO-3 / FSDP</button></div>
      </div>
      <svg id="zSvg" viewBox="0 0 660 140" style="margin-top:14px" role="img" aria-label="Per-GPU memory"></svg>
      <div class="legend"><span><i style="background:var(--a)"></i>weights (BF16)</span><span><i style="background:var(--b)"></i>gradients (BF16)</span><span><i style="background:var(--c)"></i>optimizer state (FP32 ×3)</span><span><i style="background:var(--d)"></i>80 GB H100 limit</span></div>
      <p class="readout" id="zOut" style="margin-top:8px"></p>
    </div>
    <p class="caption">Not included: activations, which scale with batch × sequence × layers and are often the largest item. They are reduced with activation checkpointing, sequence/context parallelism, or offloading.</p>
    <div class="takeaway">A 70B model needs about 1.1 TB just for weights and optimizer state. That is why training is always sharded, and why FSDP and ZeRO-3 add an all-gather of the weights before every layer.</div>
    <div class="cite">Rajbhandari et al., "ZeRO: Memory Optimizations Toward Training Trillion Parameter Models" (2020).</div>
  </div>
</section>

<!-- slide id="s-example" from="example" chapter="Example" tag="Worked example" tagclass="b5" -->

<!-- slide raw -->
<section class="slide" id="s-kv" data-chapter="Capacity">
  <div class="inner">
    <div class="label">07 · Capacity</div>
    <h2>In inference, the KV cache uses up HBM capacity</h2>
    <hr>
    <p class="lede"><code>KV bytes = 2 × layers × kv_heads × head_dim × bytes × tokens × batch</code>. It grows linearly with context <em>and</em> with the number of concurrent users.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <select id="kvM">
          <option value="32,8,128,16">Llama 3 8B (GQA, 8 KV heads)</option>
          <option value="80,8,128,140" selected>Llama 3 70B (GQA, 8 KV heads)</option>
          <option value="80,64,128,140">70B if it used MHA (64 KV heads)</option>
          <option value="126,8,128,810">Llama 3 405B (GQA, 8 KV heads)</option>
        </select>
        <label class="ctl">Context <input type="range" id="kvC" min="10" max="17" step="1" value="13"> <output id="kvCo"></output></label>
        <label class="ctl">Batch <input type="range" id="kvB" min="0" max="8" step="1" value="5"> <output id="kvBo"></output></label>
        <div class="seg" id="kvT"><button data-v="2" class="on">BF16</button><button data-v="1">FP8</button></div>
      </div>
      <div class="grid3" style="margin-top:14px">
        <div class="stat"><div class="num" id="kvTok"></div><div class="lbl">KV per token</div></div>
        <div class="stat"><div class="num" id="kvTot" style="color:var(--b)"></div><div class="lbl">total KV cache</div></div>
        <div class="stat"><div class="num" id="kvW"></div><div class="lbl">model weights (BF16)</div></div>
      </div>
      <div id="kvBars" style="margin-top:16px"></div>
      <p class="caption">Weights + KV cache compared with GPU memory (log scale).</p>
    </div>
    <div class="takeaway">GQA (8× fewer KV heads than query heads), FP8 (8-bit floating point) KV and MLA (multi-head latent attention) all exist to shrink this number. Every byte saved means more concurrent users, and decode reads less memory per step.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-paged" data-chapter="Capacity">
  <div class="inner">
    <div class="label">08 · Capacity</div>
    <h2>PagedAttention: virtual memory for the KV cache</h2>
    <hr>
    <p class="lede">Early servers reserved one contiguous KV buffer per request, sized for <em>max length</em>. Most requests finish early, so most of that space was never used. vLLM allocates fixed-size <b>blocks</b> on demand, the way an OS (operating system) allocates pages.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <div class="seg" id="pgMode"><button data-v="c" class="on">Contiguous (reserve 2,048)</button><button data-v="p">Paged (16-token blocks)</button></div>
        <button class="btn" id="pgNew">New requests</button>
      </div>
      <svg id="pgSvg" viewBox="0 0 660 230" style="margin-top:12px" role="img" aria-label="KV cache memory map"></svg>
      <div class="legend" id="pgLegend"></div>
      <div class="grid3" style="margin-top:8px">
        <div class="stat"><div class="num" id="pgUsed"></div><div class="lbl">memory holding real tokens</div></div>
        <div class="stat"><div class="num" id="pgFit"></div><div class="lbl">requests that fit</div></div>
        <div class="stat"><div class="num" id="pgWaste"></div><div class="lbl">reserved but unused</div></div>
      </div>
    </div>
    <div class="takeaway">The vLLM paper measured 60–80% KV memory waste in earlier systems, compared with under 4% using paging. Paging also enables <b>prefix sharing</b>: requests with a common system prompt point to the same blocks.</div>
    <div class="cite">Kwon et al., "Efficient Memory Management for Large Language Model Serving with PagedAttention", SOSP 2023.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-off" data-chapter="Beyond the GPU">
  <div class="inner">
    <div class="label">09 · Beyond the GPU</div>
    <h2>Off-GPU memory is huge but sits behind a narrow pipe</h2>
    <hr>
    <p class="lede">Offloading weights, optimizer state or KV cache to CPU (central processing unit) RAM (random-access memory) or NVMe buys capacity, but every byte has to come back through PCIe (PCI (Peripheral Component Interconnect) Express, the standard expansion bus). Drag to see how long it takes to move a given amount of data at each level.</p>
    <div class="visual">
      <label class="ctl">Data to move <input type="range" id="oS" min="0" max="3" step="0.05" value="2.146"> <output id="oSo"></output></label>
      <div id="oBars" style="margin-top:14px"></div>
    </div>
    <p class="caption">Per-GPU, one direction: HBM3 (third-generation high-bandwidth memory) 3.35 TB/s · NVLink 4 450 GB/s · PCIe Gen5 x16 ~64 GB/s · 400 Gb/s NIC (network interface card) 50 GB/s · local NVMe ~7 GB/s per drive.</p>
    <div class="takeaway">Offloading works when the transfer can be <b>overlapped</b> with compute: ZeRO-Offload optimizer steps, prefetching the next layer's weights, or a tiered KV cache for idle chat sessions. It fails when a transfer sits on the critical path of every token.</div>
  </div>
</section>

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="Tricks and traps" tagclass="b7" -->

<!-- slide raw -->
<section class="slide" id="s-qa" data-chapter="Test yourself">
  <div class="inner">
    <div class="label">10 · Test yourself</div>
    <h2>Questions to test your understanding</h2>
    <hr>
    <details class="qa"><summary>Explain why FlashAttention is faster when it does the same FLOPs.</summary><div class="ans">Standard attention is <b>IO-bound</b>: it writes the N×N score matrix to HBM and reads it back several times (for scale, mask, softmax and the matmul with V). FlashAttention tiles Q, K and V into SRAM, computes softmax incrementally (online softmax with a running max and sum), and writes only the N×d output. HBM traffic drops and memory goes from O(N²) to O(N). In the backward pass it recomputes the scores instead of storing them, which is extra FLOPs, and it is still faster.</div></details>
    <details class="qa"><summary>How much KV cache does a 70B model need for 32 users at 8K context?</summary><div class="ans">2 × 80 layers × 8 KV heads × 128 × 2 bytes = <b>320 KB per token</b>. × 8,192 × 32 ≈ <b>86 GB</b>, on top of 140 GB of weights. You need at least 4 × 80 GB GPUs, or FP8 KV to halve it. Without GQA (64 KV heads) it would be 8× larger, about 690 GB.</div></details>
    <details class="qa"><summary>How much memory does it take to train a 7B model with Adam, and how do you fit it?</summary><div class="ans">16 B/param × 7B = <b>112 GB</b> of states, plus activations. That doesn't fit on one 80 GB GPU. Options: ZeRO-2 or 3 / FSDP across 8 GPUs (≈14 GB/GPU of states), activation checkpointing, 8-bit optimizers, or CPU offload of optimizer state. Explain each trade-off: more communication, recompute cost, PCIe bandwidth.</div></details>
    <details class="qa"><summary>What is kernel fusion, and when doesn't it help?</summary><div class="ans">Fusion merges several ops into one kernel so that intermediate values stay in registers or SRAM, which saves HBM round trips and launches. It helps <b>memory-bound chains</b> (elementwise ops, norms, softmax). It helps little for big compute-bound GEMMs, beyond fusing their epilogue. It can hurt if the fused kernel needs too many registers, which lowers occupancy.</div></details>
    <details class="qa"><summary>Why is shared memory faster than L1 or L2 if it's the same SRAM?</summary><div class="ans">On Hopper, L1 and shared memory are the <b>same 256 KB physical SRAM</b> per SM, split by configuration. Shared memory is <b>managed by the programmer</b>, so you place exactly the tile you will reuse there, with no misses or evictions. L2 (50 MB) is shared across all SMs, farther away and slower. Distributed shared memory on H100 also lets SMs in a cluster read each other's shared memory.</div></details>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-end" data-chapter="Test yourself">
  <div class="inner">
    <div class="label">11 · Take it with you</div>
    <h2>Four things to remember</h2>
    <hr>
    <div class="recap">
      <div><span><b>The levels are registers → SMEM/L1 → L2 → HBM → NVLink peers → host DRAM → NVMe.</b> Each step down is bigger and slower; HBM is about 3 TB/s and PCIe about 64 GB/s.</span></div>
      <div><span><b>Most optimizations are about reuse:</b> tiling (GEMM), fusion (elementwise chains) and IO-aware algorithms (FlashAttention).</span></div>
      <div><span><b>Training memory is 16 B/param plus activations,</b> so it is sharded with ZeRO/FSDP. Inference memory is weights + KV cache, managed with paging, GQA and FP8.</span></div>
      <div><span><b>Offloading only pays off when the transfer overlaps with compute.</b> If it's on the critical path, the PCIe link becomes the limit.</span></div>
    </div>
    <p class="start-hint">Next: <a href="../04-inside-gpu-server/index.html">04 · Inside a GPU server →</a> · Previous: <a href="../02-why-gpus-for-ai/index.html">← 02</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
