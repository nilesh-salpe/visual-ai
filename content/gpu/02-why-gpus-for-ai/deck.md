---
title: Why GPUs for AI
body:
  data-deck: Why GPUs for AI
  data-home: ../index.html
  data-home-label: GPU
styles:
- ../../shared/deck.css
- ../../shared/learn.css
css: |-
  .bits { display: flex; gap: 2px; flex-wrap: wrap; margin: 6px 0 4px; }
    .bits span { width: 18px; height: 26px; border-radius: 3px; display: grid; place-items: center; font: 600 10px 'JetBrains Mono', monospace; color: #fff; }
    .fmtrow { display: grid; grid-template-columns: 120px 1fr; align-items: center; gap: 12px; padding: 6px 0; border-bottom: 1px solid var(--line); cursor: pointer; }
    .fmtrow:last-child { border-bottom: 0; }
    .fmtrow.on b { color: var(--a); }
    .fmtrow b { font: 600 14px 'JetBrains Mono', monospace; }
    .tl { display: flex; height: 34px; border-radius: 8px; overflow: hidden; background: var(--panel-2); margin-top: 6px; }
    .tl div { height: 100%; transition: width .3s; }
scripts:
- ../../shared/deck.js
glance:
  steps:
  - 'model :: N parameters :: f'
  - 'FLOPs :: 2·N per token forward,

    6·N·D to train :: a'
  - 'bytes moved :: weights, activations, KV :: b'
  - 'arithmetic intensity :: FLOPs ÷ bytes :: c'
  - 'roofline :: compute- or memory-bound :: e'
  caption: Compare a kernel's intensity with the ridge point (peak FLOP/s ÷ bandwidth) to know which limit applies.
example:
  title: 'Worked example: estimate a training run on a whiteboard'
  setup: 'Llama 3 405B: N = 405B parameters, D = 15.6T tokens, H100 at 989 TFLOP/s dense BF16, assume 40% MFU (model FLOPs utilization).'
  steps:
  - Total compute ≈ 6 · N · D = 6 × 405B × 15.6T = <b>3.79e+25 FLOPs</b>.
  - GPU-hours = 3.79e+25 ÷ (989 TFLOP/s × 0.4) ÷ 3,600 ≈ <b>26.6M</b> (Meta reported 30.84M including restarts and other overheads).
  - 'On 16,384 GPUs: 26.6M ÷ 16,384 ÷ 24 ≈ <b>68 days</b>.'
  - 'Ridge point of H100: 989 TFLOP/s ÷ 3.35 TB/s ≈ <b>295 FLOPs per byte</b>; below that, a kernel is memory-bound.'
  result: Four numbers (N, D, peak FLOP/s, MFU) give a training budget in 30 seconds.
traps:
  tricks:
  - 'Training ≈ 6·N·D, inference ≈ 2·N per token. :: Forward 2, backward 4.'
  - 'Ridge point = peak ÷ bandwidth. :: ≈ 295 FLOPs/byte on H100 in BF16.'
  - 'Decode intensity ≈ batch size. :: Each weight read serves one token per sequence in the batch.'
  traps:
  - 'Using sparse peak numbers. :: Datasheet 2:4-sparsity figures are 2× the dense ones.'
  - 'Assuming 100% MFU. :: Real large runs reach ~40% (Llama 3: 38–43%).'
  - 'Calling decode compute-bound. :: At small batch it is limited by bandwidth.'
papers:
- kaplan
- palm
- llama3
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">GPU for GenAI · 02</div>
    <h1>Why GPUs for AI:<br>FLOPs, bytes, and the roofline</h1>
    <p class="sub">Neural networks are almost all matrix multiplications, and GPUs (graphics processing units) are built to do those. To reason about performance, keep track of FLOPs (floating-point operations), bytes moved, and the ratio between the two. This deck shows how to do that.</p>
    <div class="toc" data-auto></div>
    <p class="start-hint">Press <kbd>→</kbd> or <kbd>Space</kbd> to begin.</p>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-mm" data-chapter="The workload">
  <div class="inner">
    <div class="label">01 · The workload</div>
    <h2>A transformer forward pass is mostly matmuls: about 2 FLOPs per parameter per token</h2>
    <hr>
    <p class="lede">Every weight is used in one multiply-add per token, which gives roughly <b>2·N FLOPs</b> per token for N parameters. Attention adds work that grows with context length. Pick a model and drag the context slider to see when attention starts to matter.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <div class="seg" id="mmModel"><button data-v="8">Llama 3 8B</button><button data-v="70" class="on">Llama 3 70B</button><button data-v="405">Llama 3 405B</button></div>
        <label class="ctl">Context <input type="range" id="mmCtx" min="9" max="17" step="1" value="13"> <output id="mmCtxo"></output></label>
      </div>
      <div id="mmBars" style="margin-top:16px"></div>
      <p class="readout" id="mmOut" style="margin-top:10px"></p>
    </div>
    <p class="caption">Per-token forward FLOPs. Linear layers (QKV (query, key and value), output projection, MLP (multilayer perceptron)): about 2·N. Attention scores and weighted sum: about 4·L·ctx·d. Training costs about 3× the forward pass (forward + backward), which is where <b>6·N·D</b> comes from.</p>
    <div class="takeaway">At typical context lengths more than 80% of the FLOPs are dense GEMMs (general matrix multiplications), which is exactly the operation Tensor Cores accelerate. Attention FLOPs take over only at very long context.</div>
  
    <!--x:glance--><div class="glance"><h4>At a glance</h4><svg viewBox="0 0 660 166" role="img" aria-label="Compare a kernel&#x27;s intensity with the ridge point (peak FLOP/s ÷ bandwidth) to know which limit applies." class="glance-svg"><defs><marker id="gArr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--muted)"/></marker></defs><rect x="10.0" y="28" width="113.6" height="64" rx="10" style="fill:var(--faint)"/><text x="66.8" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">model</text><text x="66.8" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">N parameters</text><rect x="141.6" y="28" width="113.6" height="64" rx="10" style="fill:var(--a)"/><text x="198.4" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">FLOPs</text><text x="198.4" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">2·N per token</text><text x="198.4" y="123.0" text-anchor="middle" class="tm" style="font-size:11px">forward,</text><text x="198.4" y="137.0" text-anchor="middle" class="tm" style="font-size:11px">6·N·D to train</text><line x1="125.6" y1="60.0" x2="139.6" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/><rect x="273.2" y="28" width="113.6" height="64" rx="10" style="fill:var(--b)"/><text x="330.0" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">bytes moved</text><text x="330.0" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">weights,</text><text x="330.0" y="123.0" text-anchor="middle" class="tm" style="font-size:11px">activations, KV</text><line x1="257.2" y1="60.0" x2="271.2" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/><rect x="404.8" y="28" width="113.6" height="64" rx="10" style="fill:var(--c)"/><text x="461.6" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">arithmetic intensity</text><text x="461.6" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">FLOPs ÷ bytes</text><line x1="388.8" y1="60.0" x2="402.8" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/><rect x="536.4" y="28" width="113.6" height="64" rx="10" style="fill:var(--e)"/><text x="593.2" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">roofline</text><text x="593.2" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">compute- or</text><text x="593.2" y="123.0" text-anchor="middle" class="tm" style="font-size:11px">memory-bound</text><line x1="520.4" y1="60.0" x2="534.4" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/></svg><p class="caption" style="margin:4px 0 0">Compare a kernel's intensity with the ridge point (peak FLOP/s ÷ bandwidth) to know which limit applies.</p></div><!--/x:glance-->
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-6nd" data-chapter="The workload">
  <div class="inner">
    <div class="label">02 · The workload</div>
    <h2>Training cost ≈ 6 · N · D. Work out GPU-days on the whiteboard.</h2>
    <hr>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">Params N <input type="range" id="tN" min="0" max="3.3" step="0.01" value="2.607"> <output id="tNo"></output></label>
        <label class="ctl">Tokens D <input type="range" id="tD" min="11" max="13.5" step="0.01" value="13.19"> <output id="tDo"></output></label>
        <label class="ctl">GPUs <input type="range" id="tG" min="8" max="17" step="1" value="14"> <output id="tGo"></output></label>
        <label class="ctl">MFU <input type="range" id="tM" min="20" max="60" step="1" value="40"> <output id="tMo"></output></label>
        <select id="tGPU"><option value="312">A100 · 312 TF BF16</option><option value="989" selected>H100 · 989 TF BF16</option><option value="2250">B200 · 2250 TF BF16</option></select>
      </div>
      <div class="grid4" style="margin-top:16px">
        <div class="stat"><div class="num" id="tF"></div><div class="lbl">total FLOPs (6·N·D)</div></div>
        <div class="stat"><div class="num" id="tH"></div><div class="lbl">GPU-hours</div></div>
        <div class="stat"><div class="num" id="tDays" style="color:var(--a)"></div><div class="lbl">wall-clock days</div></div>
        <div class="stat"><div class="num" id="tCost"></div><div class="lbl">at $2 / GPU-hour</div></div>
      </div>
    </div>
    <p class="caption">Sanity check against Llama 3 405B: 6 × 405B × 15.6T ≈ <b>3.8 × 10²⁵ FLOPs</b>. On H100s at about 40% MFU (model floating-point-operation utilization, the share of peak compute spent on the model's math) that is roughly 27M GPU-hours. Meta reported 30.84M H100 GPU-hours, which includes restarts and overhead.</p>
    <div class="takeaway">A useful habit: you can estimate any training run from four numbers (N, D, peak FLOPS (floating-point operations per second), MFU) in 30 seconds.</div>
    <div class="cite">Llama Team, "The Llama 3 Herd of Models" (2024); Kaplan et al., "Scaling Laws for Neural Language Models" (2020).</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-ai" data-chapter="Roofline">
  <div class="inner">
    <div class="label">03 · Roofline</div>
    <h2>Arithmetic intensity: FLOPs done per byte moved</h2>
    <hr>
    <p class="lede">An H100 can do about <b>989 TFLOPS (trillion floating-point operations per second)</b> but only read about <b>3.35 TB/s</b> from HBM (high-bandwidth memory). To keep the Tensor Cores busy, a kernel has to do roughly <b>295 FLOPs for every byte</b> it loads. That number is the <em>ridge point</em>.</p>
    <div class="visual">
      <div class="seg" id="aiOp">
        <button data-v="add">x + y</button><button data-v="gelu">GELU</button><button data-v="ln">LayerNorm</button><button data-v="sm">Softmax</button><button data-v="gemm" class="on">GEMM (n×n)</button>
      </div>
      <div class="controls" id="aiNrow"><label class="ctl">n <input type="range" id="aiN" min="4" max="14" step="1" value="10"> <output id="aiNo"></output></label></div>
      <div class="grid3" style="margin-top:14px">
        <div class="stat"><div class="num" id="aiF"></div><div class="lbl">FLOPs</div></div>
        <div class="stat"><div class="num" id="aiB"></div><div class="lbl">bytes moved (BF16 (bfloat16, a 16-bit floating-point format with the exponent range of 32-bit floats))</div></div>
        <div class="stat"><div class="num" id="aiI"></div><div class="lbl">FLOPs / byte</div></div>
      </div>
      <div id="aiBar" style="margin-top:16px"></div>
      <p class="readout" id="aiVerdict" style="margin-top:8px"></p>
    </div>
    <div class="takeaway">For an n×n matmul the intensity is about n/3: it does O(n³) work on O(n²) data. Elementwise ops do about one FLOP per several bytes, so they are always memory-bound. That is why fusing them into neighbouring kernels matters.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-roof" data-chapter="Roofline">
  <div class="inner">
    <div class="label">04 · Roofline</div>
    <h2>The roofline: bandwidth limits the left side, compute limits the right</h2>
    <hr>
    <p class="lede">Attainable FLOPS = <code>min(peak, bandwidth × intensity)</code>. Points to the left of the ridge are <span class="em-d">memory-bound</span> and points to the right are <span class="em-e">compute-bound</span>. Drag the batch slider to move LLM (large language model) decode along the slope.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <div class="seg" id="rfGPU"><button data-v="a100">A100</button><button data-v="h100" class="on">H100</button><button data-v="b200">B200</button></div>
        <label class="ctl">Decode batch <input type="range" id="rfB" min="0" max="10" step="1" value="0"> <output id="rfBo"></output></label>
      </div>
      <svg id="roofSvg" viewBox="0 0 660 380" style="margin-top:10px" role="img" aria-label="Roofline chart"></svg>
      <p class="readout" id="rfOut"></p>
    </div>
    <div class="cite">Peak dense BF16 / HBM bandwidth: A100 SXM 312 TF / 2.04 TB/s · H100 SXM 989 TF / 3.35 TB/s · B200 (HGX) ~2,250 TF / 8 TB/s. Points use BF16 and d = 8192.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-pd" data-chapter="Inference">
  <div class="inner">
    <div class="label">05 · Inference</div>
    <h2>Prefill is limited by compute; decode is limited by memory bandwidth</h2>
    <hr>
    <p class="lede"><b>Prefill</b> runs all prompt tokens through the model at once, which is one big GEMM. <b>Decode</b> generates one token per step, and each step has to read <em>every weight</em> plus the whole KV (key-value) cache from HBM. Example: Llama 3 70B in BF16 on 8×H100 with tensor parallelism (TP=8), batch 1.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">Prompt tokens <input type="range" id="pdP" min="128" max="32768" step="128" value="2048"> <output id="pdPo"></output></label>
        <label class="ctl">Output tokens <input type="range" id="pdO" min="16" max="2048" step="16" value="256"> <output id="pdOo"></output></label>
      </div>
      <div class="tl" id="pdTl"><div style="background:var(--a)"></div><div style="background:var(--b)"></div></div>
      <div class="legend"><span><i style="background:var(--a)"></i>prefill (compute)</span><span><i style="background:var(--b)"></i>decode (memory)</span></div>
      <div class="grid4" style="margin-top:14px">
        <div class="stat"><div class="num" id="pdTTFT"></div><div class="lbl">time to first token (TTFT)</div></div>
        <div class="stat"><div class="num" id="pdTPOT"></div><div class="lbl">time per output token (TPOT)</div></div>
        <div class="stat"><div class="num" id="pdTPS"></div><div class="lbl">tokens / s for this user</div></div>
        <div class="stat"><div class="num" id="pdShare"></div><div class="lbl">of wall time spent decoding</div></div>
      </div>
    </div>
    <p class="caption">Model: prefill FLOPs ≈ 2·N·P at 60% of 8 × 989 TFLOPS. Decode step ≈ (140 GB weights + KV) ÷ (8 × 3.35 TB/s × 80%). At batch 1 the Tensor Cores sit almost idle during decode.</p>
    <div class="takeaway">TTFT depends on compute (prompt length × FLOPs). TPOT depends on bandwidth (bytes ÷ HBM bandwidth). Every discussion of LLM serving uses these two metrics.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-batch" data-chapter="Inference">
  <div class="inner">
    <div class="label">06 · Inference</div>
    <h2>Batching shares one read of the weights across many users</h2>
    <hr>
    <p class="lede">Each decode step reads 140 GB of weights no matter how many sequences are in the batch, so a bigger batch gets more tokens out of each read. KV-cache reads still grow with the batch, and eventually the cache <b>doesn't fit in memory</b>.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">Batch size <input type="range" id="bB" min="0" max="10" step="0.1" value="5"> <output id="bBo"></output></label>
        <label class="ctl">Avg context / seq <input type="range" id="bC" min="10" max="15" step="1" value="12"> <output id="bCo"></output></label>
      </div>
      <svg id="batchSvg" viewBox="0 0 660 300" style="margin-top:10px" role="img" aria-label="Throughput vs batch"></svg>
      <div class="grid4" style="margin-top:10px">
        <div class="stat"><div class="num" id="bTot" style="color:var(--a)"></div><div class="lbl">total tokens / s</div></div>
        <div class="stat"><div class="num" id="bUser" style="color:var(--b)"></div><div class="lbl">tokens / s per user</div></div>
        <div class="stat"><div class="num" id="bBound"></div><div class="lbl">bound by</div></div>
        <div class="stat"><div class="num" id="bMax"></div><div class="lbl">max batch that fits in memory</div></div>
      </div>
    </div>
    <p class="caption">Llama 3 70B BF16 on 8×H100 (640 GB). KV cache = 320 KB per token (80 layers × 8 KV heads × 128 dims × 2 (K and V) × 2 bytes).</p>
    <div class="takeaway">Batching trades per-user latency for total throughput. At long context, KV-cache reads dominate and decode stays memory-bound at any batch size, which is why GQA (grouped-query attention), MLA (multi-head latent attention), KV quantization and paged KV matter.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-prec" data-chapter="Precision">
  <div class="inner">
    <div class="label">07 · Precision</div>
    <h2>Fewer bits per number: twice the FLOPs and half the bytes each time you halve the width</h2>
    <hr>
    <div class="grid2">
      <div class="visual" style="margin-top:0" id="fmtList"></div>
      <div class="visual" style="margin-top:0">
        <h3 id="fmtName"></h3>
        <p class="caption" id="fmtDesc" style="margin-top:0"></p>
        <div class="grid2" style="margin-top:12px">
          <div class="stat"><div class="num" id="fmtMax"></div><div class="lbl">max representable value</div></div>
          <div class="stat"><div class="num" id="fmtMem"></div><div class="lbl">70B weights</div></div>
        </div>
        <div id="fmtBars" style="margin-top:16px"></div>
        <p class="caption">Dense Tensor Core TFLOPS. "—" = not supported in hardware.</p>
      </div>
    </div>
    <div class="takeaway">BF16 keeps FP32 (32-bit floating point)'s exponent range, so training is stable without loss scaling. FP8 (8-bit floating point) and FP4 (4-bit floating point) need <b>scaling factors</b> per tensor or per block (for example the MX (microscaling, block-scaled number formats) formats) because their range is so small.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-mfu" data-chapter="Precision">
  <div class="inner">
    <div class="label">08 · Utilization</div>
    <h2>MFU: the percentage of peak FLOPs that does useful model work</h2>
    <hr>
    <p class="lede"><code>MFU = (6·N · tokens/s) ÷ (peak FLOPS × #GPUs)</code>. Peak is never reached in practice. Each slider below is one source of lost throughput; they multiply together.</p>
    <div class="visual">
      <div class="grid2">
        <div>
          <label class="ctl" style="justify-content:space-between">GEMMs below peak <span><input type="range" id="m1" min="0" max="40" value="20"> <output id="m1o"></output></span></label>
          <label class="ctl" style="justify-content:space-between">Memory-bound kernels <span><input type="range" id="m2" min="0" max="40" value="22"> <output id="m2o"></output></span></label>
          <label class="ctl" style="justify-content:space-between">Exposed communication <span><input type="range" id="m3" min="0" max="40" value="15"> <output id="m3o"></output></span></label>
          <label class="ctl" style="justify-content:space-between">Pipeline bubbles <span><input type="range" id="m4" min="0" max="30" value="8"> <output id="m4o"></output></span></label>
          <label class="ctl" style="justify-content:space-between">Stragglers / restarts <span><input type="range" id="m5" min="0" max="20" value="5"> <output id="m5o"></output></span></label>
        </div>
        <div><svg id="mfuSvg" viewBox="0 0 380 240" role="img" aria-label="MFU waterfall"></svg></div>
      </div>
    </div>
    <p class="caption">MFU counts only the model's FLOPs. <b>HFU (hardware floating-point-operation utilization, which also counts recomputed work)</b> (hardware FLOPs utilization) also counts recomputation from activation checkpointing, so HFU ≥ MFU.</p>
    <div class="takeaway">Large dense pretraining runs typically report about 35–45% MFU. Llama 3 405B reported 38–43% BF16 MFU on 16K H100s.</div>
    <div class="cite">Llama 3 paper, Table 4; Chowdhery et al., "PaLM" (2022), which introduced MFU.</div>
  </div>
</section>

<!-- slide id="s-example" from="example" chapter="Example" tag="Worked example" tagclass="b5" -->

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="Tricks and traps" tagclass="b7" -->

<!-- slide raw -->
<section class="slide" id="s-qa" data-chapter="Test yourself">
  <div class="inner">
    <div class="label">09 · Test yourself</div>
    <h2>Questions to test your understanding</h2>
    <hr>
    <details class="qa"><summary>Estimate the max decode speed of a 70B model on one H100, batch 1.</summary><div class="ans">BF16 weights are 140 GB, which <b>doesn't fit</b> in 80 GB. In FP8 they are about 70 GB, which barely fits. Each token has to read all the weights: 70 GB ÷ 3.35 TB/s ≈ <b>21 ms per token, so at most about 48 tokens/s</b>, and less in practice once KV-cache reads and imperfect bandwidth are included. Compute is nowhere near the limit: 2 × 70e9 FLOPs per token is only about 0.14 ms of H100 compute.</div></details>
    <details class="qa"><summary>Why is prefill compute-bound but decode memory-bound?</summary><div class="ans">Prefill multiplies a [P × d] activation matrix by every weight matrix, so each weight byte is reused P times and the intensity is about P. Decode uses each weight once per sequence in the batch, so the intensity is about the batch size, far below the ~300 FLOPs/byte ridge. Attention in decode is worse still: every sequence reads its own KV cache, so batching doesn't help it.</div></details>
    <details class="qa"><summary>How long does it take to train a 70B model on 15T tokens with 4,096 H100s?</summary><div class="ans">6 × 70e9 × 15e12 = <b>6.3e24 FLOPs</b>. Effective throughput is 4,096 × 989e12 × 0.4 ≈ 1.6e18 FLOPs/s, which gives about 3.9e6 s ≈ <b>45 days</b>. Then mention what this leaves out: failures and restarts, data loading, and evaluation pauses.</div></details>
    <details class="qa"><summary>How would you find out whether a kernel is memory-bound or compute-bound?</summary><div class="ans">Work out its arithmetic intensity (FLOPs ÷ bytes) and compare it with the GPU's ridge point (peak FLOPS ÷ bandwidth). Then confirm with a profiler such as Nsight Compute: if achieved DRAM (dynamic random-access memory) bandwidth is close to peak, it's memory-bound; if Tensor Core utilization is close to peak, it's compute-bound. If neither is high, it's limited by latency or launch overhead.</div></details>
    <details class="qa"><summary>Why are FP8 and FP4 harder to use than BF16?</summary><div class="ans">Their range is tiny: E4M3 tops out at 448 and E2M1 at 6. Outliers in activations overflow, and small gradients round to zero. So you need <b>scaling factors</b> (per tensor, per channel, or per block of 16–32 values as in MXFP8 (8-bit microscaling floating point) and NVFP4 (NVIDIA's block-scaled 4-bit floating point)), higher-precision accumulators, and usually a few sensitive layers (embeddings, the LM (language model) head, normalization) kept in BF16.</div></details>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-end" data-chapter="Test yourself">
  <div class="inner">
    <div class="label">10 · Take it with you</div>
    <h2>Four things to remember</h2>
    <hr>
    <div class="recap">
      <div><span><b>Use 2N FLOPs per token for inference and 6ND for training.</b> Divide by peak × MFU to get time.</span></div>
      <div><span><b>Ridge point = peak FLOPS ÷ bandwidth, about 300 FLOPs/byte on an H100.</b> Below it you are limited by memory bandwidth.</span></div>
      <div><span><b>Prefill is compute-bound (TTFT); decode is bandwidth-bound (TPOT).</b> Batching amortizes the weight reads but not the KV-cache reads.</span></div>
      <div><span><b>Lower precision doubles throughput and halves bytes each step</b>, provided you handle range with scaling factors.</span></div>
    </div>
    <p class="start-hint">Next: <a href="../03-memory-hierarchy/index.html">03 · Memory hierarchy →</a> · Previous: <a href="../01-what-is-a-gpu/index.html">← 01</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
