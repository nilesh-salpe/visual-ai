---
title: Sharing GPUs
body:
  data-deck: Sharing GPUs
  data-home: ../index.html
  data-home-label: GPU
styles:
- ../../shared/deck.css
- ../../shared/learn.css
css: |-
  .infobox { min-height: 80px; background: var(--panel-2); border-radius: 10px; padding: 12px 14px; font-size: 14px; color: var(--muted); margin-top: 12px; }
    .infobox b { color: var(--ink); }
    .wl { display: flex; flex-wrap: wrap; gap: 8px; }
    .wl label { display: flex; align-items: center; gap: 6px; font-size: 13.5px; border: 1px solid var(--line); border-radius: 8px; padding: 6px 10px; cursor: pointer; background: var(--panel); }
    .wl input { accent-color: var(--a); }
    .mig-btns { display: flex; flex-wrap: wrap; gap: 6px; }
    .mig-btns button { font-family: 'JetBrains Mono', monospace; }
    #spSvg circle { cursor: pointer; }
scripts:
- ../../shared/deck.js
glance:
  steps:
  - 'time-slicing :: take turns, no isolation :: f'
  - 'MPS :: run side by side, soft limits :: b'
  - 'MIG :: hardware partitions, ≤ 7 :: a'
  - 'continuous batching :: one model, many users :: c'
  - 'multi-LoRA :: one base, many adapters :: e'
  caption: From splitting the hardware to sharing the model.
example:
  title: 'Worked example: one H100 for seven small services'
  setup: Seven internal services each need ~8 GB of memory and a small share of compute.
  steps:
  - 'Time-slicing: all seven take turns on the whole GPU; a busy service delays the others, and memory isn''t isolated.'
  - 'MIG: seven 1g.10gb instances, each with its own SMs, L2 slice and ~10 GB of memory: guaranteed isolation and QoS.'
  - 'MPS: processes share SMs concurrently with soft limits: better utilization, weaker isolation.'
  - 'If all seven are LoRA variants of one base model, multi-LoRA serving keeps one copy of the base and batches them together (Punica: 12× throughput).'
  result: Use MIG when tenants need isolation, MPS for cooperating processes, and model-level sharing (batching, multi-LoRA) when they share a model.
traps:
  tricks:
  - 'MIG ≤ 7 instances on H100. :: Fixed profiles; reconfigure only when idle.'
  - 'Share the model, not just the GPU. :: Continuous batching and multi-LoRA beat partitioning for same-model traffic.'
  - 'Gang scheduling. :: Distributed jobs need all their GPUs at once.'
  traps:
  - 'Time-slicing for latency-sensitive work. :: Turns add unpredictable delay.'
  - 'Fragmentation. :: Leftover GPUs that no job can use idle a cluster.'
  - 'Assuming MPS isolates faults. :: A crashing client can affect others.'
papers:
- mig
- orca
- slora
- punica
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">GPU for GenAI · 08</div>
    <h1>Sharing GPUs:<br>from time-slices to multi-tenant serving</h1>
    <p class="sub">An idle H100 still costs money. This deck covers the ways to share one GPU (time-slicing, MPS (NVIDIA Multi-Process Service), MIG (Multi-Instance GPU, hardware partitioning of one GPU)), the ways to share a model across users (continuous batching, multi-LoRA), and the ways to share a cluster (gang scheduling, quotas, preemption).</p>
    <div class="toc" data-auto></div>
    <p class="start-hint">Press <kbd>→</kbd> or <kbd>Space</kbd> to begin.</p>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-why" data-chapter="Why share">
  <div class="inner">
    <div class="label">01 · Why share</div>
    <h2>Most small workloads use a fraction of a GPU</h2>
    <hr>
    <p class="lede">Notebooks, small inference services, embedding models and CI (confidence interval) jobs often use 5–30% of a GPU. If each gets a whole H100, most of the fleet sits idle. Choose the workloads and compare how many GPUs they need with and without packing.</p>
    <div class="visual">
      <div class="wl" id="wl"></div>
      <div class="grid2" style="margin-top:14px;align-items:center">
        <svg id="packSvg" viewBox="0 0 360 200" role="img" aria-label="Bin packing of workloads"></svg>
        <div class="grid2">
          <div class="stat"><div class="num" id="pkWhole" style="color:var(--d)"></div><div class="lbl">GPUs, one per workload</div></div>
          <div class="stat"><div class="num" id="pkShared" style="color:var(--e)"></div><div class="lbl">GPUs with sharing (packed)</div></div>
          <div class="stat"><div class="num" id="pkUtil"></div><div class="lbl">average utilization, unshared</div></div>
          <div class="stat"><div class="num" id="pkSave"></div><div class="lbl">GPUs saved</div></div>
        </div>
      </div>
    </div>
    <p class="caption">Packing uses first-fit by compute share and memory (80 GB). Real packing also has to respect isolation and latency SLOs (service-level objectives), which the rest of this deck covers.</p>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-spec" data-chapter="One GPU">
  <div class="inner">
    <div class="label">02 · One GPU</div>
    <h2>Three ways to split a GPU, each with a different level of isolation</h2>
    <hr>
    <div class="grid2">
      <div class="visual" style="margin-top:0"><svg id="spSvg" viewBox="0 0 360 280" role="img" aria-label="Isolation vs flexibility"></svg></div>
      <div class="visual scroll-x" style="margin-top:0">
        <table class="tbl">
          <tr><th></th><th>Time-slice</th><th>MPS</th><th>MIG</th></tr>
          <tr><td>Runs concurrently</td><td>✗ takes turns</td><td>✓ shares SMs (streaming multiprocessors)</td><td>✓ separate SMs</td></tr>
          <tr><td>Memory isolation</td><td>✗</td><td>~ limit only</td><td>✓ hardware</td></tr>
          <tr><td>Fault isolation</td><td>~</td><td>✗ shared</td><td>✓</td></tr>
          <tr><td>Performance QoS (quality of service)</td><td>✗</td><td>~ thread %</td><td>✓ L2/DRAM (dynamic random-access memory) partitioned</td></tr>
          <tr><td>Granularity</td><td>any</td><td>any %</td><td>fixed profiles, ≤7</td></tr>
          <tr><td>Reconfiguration</td><td>instant</td><td>restart daemon</td><td>GPU must be idle</td></tr>
        </table>
      </div>
    </div>
    <div class="infobox" id="spInfo">Click a point on the chart.</div>
    <div class="takeaway">Use MIG when tenants don't trust each other or need guaranteed QoS, MPS for cooperating processes that each underuse the GPU (for example several inference workers), and time-slicing for dev and notebook clusters where convenience matters most.</div>
  
    <!--x:glance--><div class="glance"><h4>At a glance</h4><svg viewBox="0 0 660 152" role="img" aria-label="From splitting the hardware to sharing the model." class="glance-svg"><defs><marker id="gArr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--muted)"/></marker></defs><rect x="10.0" y="28" width="113.6" height="64" rx="10" style="fill:var(--faint)"/><text x="66.8" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">time-slicing</text><text x="66.8" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">take turns, no</text><text x="66.8" y="123.0" text-anchor="middle" class="tm" style="font-size:11px">isolation</text><rect x="141.6" y="28" width="113.6" height="64" rx="10" style="fill:var(--b)"/><text x="198.4" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">MPS</text><text x="198.4" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">run side by side,</text><text x="198.4" y="123.0" text-anchor="middle" class="tm" style="font-size:11px">soft limits</text><line x1="125.6" y1="60.0" x2="139.6" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/><rect x="273.2" y="28" width="113.6" height="64" rx="10" style="fill:var(--a)"/><text x="330.0" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">MIG</text><text x="330.0" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">hardware</text><text x="330.0" y="123.0" text-anchor="middle" class="tm" style="font-size:11px">partitions, ≤ 7</text><line x1="257.2" y1="60.0" x2="271.2" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/><rect x="404.8" y="28" width="113.6" height="64" rx="10" style="fill:var(--c)"/><text x="461.6" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">continuous batching</text><text x="461.6" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">one model, many</text><text x="461.6" y="123.0" text-anchor="middle" class="tm" style="font-size:11px">users</text><line x1="388.8" y1="60.0" x2="402.8" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/><rect x="536.4" y="28" width="113.6" height="64" rx="10" style="fill:var(--e)"/><text x="593.2" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">multi-LoRA</text><text x="593.2" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">one base, many</text><text x="593.2" y="123.0" text-anchor="middle" class="tm" style="font-size:11px">adapters</text><line x1="520.4" y1="60.0" x2="534.4" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/></svg><p class="caption" style="margin:4px 0 0">From splitting the hardware to sharing the model.</p></div><!--/x:glance-->
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-ts" data-chapter="One GPU">
  <div class="inner">
    <div class="label">03 · One GPU</div>
    <h2>Time-slicing vs MPS: taking turns vs running side by side</h2>
    <hr>
    <p class="lede">With <b>time-slicing</b>, processes take turns owning the whole GPU, and there is a context-switch cost at each turn. With <b>MPS</b>, one shared server context lets kernels from different processes run on <em>different SMs at the same time</em>.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <div class="seg" id="tsMode"><button data-v="ts" class="on">Time-slicing</button><button data-v="mps">MPS</button></div>
        <label class="ctl">Processes <input type="range" id="tsN" min="1" max="4" step="1" value="3"> <output id="tsNo"></output></label>
        <label class="ctl">Each process's SM demand <input type="range" id="tsD" min="10" max="100" step="5" value="30"> <output id="tsDo"></output></label>
      </div>
      <svg id="tsSvg" viewBox="0 0 660 250" style="margin-top:12px" role="img" aria-label="SM occupancy over time"></svg>
      <div class="grid3">
        <div class="stat"><div class="num" id="tsUtil"></div><div class="lbl">SM utilization</div></div>
        <div class="stat"><div class="num" id="tsLat"></div><div class="lbl">each process's slowdown vs running alone</div></div>
        <div class="stat"><div class="num" id="tsMem" style="font:600 15px Inter"></div><div class="lbl">memory</div></div>
      </div>
    </div>
    <p class="caption">Model: each process launches kernels that need the given share of SMs. Time-slicing runs them one at a time with about 5% switch overhead. MPS packs them onto SMs until the GPU is full.</p>
    <div class="takeaway">Time-slicing never makes a GPU busier than one process can make it; it only shares its time. MPS improves utilization when each process is too small to fill the GPU, but a fatal fault in one client can affect the others.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-mig" data-chapter="One GPU">
  <div class="inner">
    <div class="label">04 · One GPU</div>
    <h2>MIG: split an H100 into as many as 7 hardware-isolated GPUs</h2>
    <hr>
    <p class="lede">Multi-Instance GPU divides the chip into <b>7 compute slices</b> and <b>8 memory slices</b> (10 GB each). Each instance gets its own SMs, L2 cache slice and memory controllers. Add profiles to build a layout.</p>
    <div class="visual">
      <div class="mig-btns" id="migBtns"></div>
      <svg id="migSvg" viewBox="0 0 660 200" style="margin-top:14px" role="img" aria-label="MIG layout"></svg>
      <div class="controls"><button class="btn" id="migClear">Clear</button><span class="readout" id="migOut"></span></div>
    </div>
    <p class="caption">H100 80 GB profiles: 1g.10gb · 1g.20gb · 2g.20gb · 3g.40gb · 4g.40gb · 7g.80gb. Click an instance to remove it. Simplified: real MIG also has placement rules about <em>which</em> slice positions each profile may start at.</p>
    <div class="takeaway">MIG is the only option that gives guaranteed QoS and fault isolation, so it suits multi-tenant inference, embeddings and small models. The cost is coarse fixed sizes, a GPU that has to be drained to repartition, and no NVLink peer-to-peer between instances.</div>
    <div class="cite">NVIDIA MIG User Guide (H100 supported profiles).</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-cb" data-chapter="One model">
  <div class="inner">
    <div class="label">05 · One model</div>
    <h2>Continuous batching: one model, many users, no waiting for the slowest</h2>
    <hr>
    <p class="lede">With <b>static batching</b>, a batch of 4 requests holds its slots until its <em>longest</em> output finishes. <b>Continuous (in-flight) batching</b> schedules at every decode step: when one request finishes, the next one takes its slot straight away.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <div class="seg" id="cbMode"><button data-v="static" class="on">Static batching</button><button data-v="cont">Continuous batching</button></div>
        <button class="btn" id="cbNew">New requests</button>
      </div>
      <svg id="cbSvg" viewBox="0 0 660 200" style="margin-top:12px" role="img" aria-label="Batch slot timeline"></svg>
      <div class="grid3">
        <div class="stat"><div class="num" id="cbT"></div><div class="lbl">steps to finish 12 requests</div></div>
        <div class="stat"><div class="num" id="cbU"></div><div class="lbl">slot utilization</div></div>
        <div class="stat"><div class="num" id="cbW"></div><div class="lbl">avg. wait before a request starts</div></div>
      </div>
    </div>
    <div class="takeaway">Continuous batching combined with paged KV (deck 03) is what made vLLM, TGI (Hugging Face's Text Generation Inference server), SGLang and TensorRT-LLM several times faster than naive serving. It is the default way a single model is shared among many users.</div>
    <div class="cite">Yu et al., "Orca: A Distributed Serving System for Transformer-Based Generative Models" (OSDI 2022).</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-lora" data-chapter="One model">
  <div class="inner">
    <div class="label">06 · One model</div>
    <h2>Multi-LoRA: hundreds of fine-tuned variants sharing one base model</h2>
    <hr>
    <p class="lede">A LoRA (Low-Rank Adaptation) adapter for a 70B model is only a few hundred MB. Keep one copy of the base weights and load adapters as needed. Requests for <em>different</em> adapters can still go in the same batch, using custom kernels (Punica's SGMV (segmented gather matrix-vector multiplication), S-LoRA).</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">Fine-tuned variants <input type="range" id="lN" min="1" max="500" step="1" value="50"> <output id="lNo"></output></label>
        <label class="ctl">LoRA rank <input type="range" id="lR" min="3" max="7" step="1" value="4"> <output id="lRo"></output></label>
      </div>
      <div id="lBars" style="margin-top:14px"></div>
      <div class="grid3" style="margin-top:10px">
        <div class="stat"><div class="num" id="lAd"></div><div class="lbl">one adapter (BF16 (bfloat16, a 16-bit floating-point format with the exponent range of 32-bit floats))</div></div>
        <div class="stat"><div class="num" id="lFull" style="color:var(--d)"></div><div class="lbl">H100s for full copies</div></div>
        <div class="stat"><div class="num" id="lMulti" style="color:var(--e)"></div><div class="lbl">H100s with multi-LoRA</div></div>
      </div>
    </div>
    <p class="caption">Llama-3-70B shapes. LoRA is applied to all attention and MLP (multilayer perceptron) projections: r × (d_in + d_out) parameters per matrix × 7 matrices × 80 layers. GPU count covers weights only; add KV cache on top.</p>
    <div class="takeaway">For SaaS-style (SaaS = software as a service) per-customer fine-tunes, multi-LoRA changes the cost from roughly N × (a whole deployment) to one deployment plus small adapters. The trade-off is some kernel overhead and adapter-swap latency for adapters that are rarely used.</div>
  </div>
</section>

<!-- slide id="s-example" from="example" chapter="Example" tag="Worked example" tagclass="b5" -->

<!-- slide raw -->
<section class="slide" id="s-sched" data-chapter="One cluster">
  <div class="inner">
    <div class="label">07 · One cluster</div>
    <h2>Sharing a cluster: gang scheduling, fragmentation and preemption</h2>
    <hr>
    <p class="lede">A distributed training job needs <b>all of its GPUs at once</b> (gang scheduling), preferably on whole nodes within one network pod. Small jobs scattered across nodes leave free GPUs that a large job can't use.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <div class="seg" id="scMode"><button data-v="frag" class="on">Fragmented</button><button data-v="pack">Bin-packed</button><button data-v="pre">Preempt low-priority</button></div>
      </div>
      <svg id="scSvg" viewBox="0 0 660 210" style="margin-top:12px" role="img" aria-label="Cluster allocation"></svg>
      <p class="readout" id="scOut"></p>
    </div>
    <div class="grid3" style="margin-top:12px">
      <div class="card a"><h3>Gang / all-or-nothing</h3><p>Kueue, Volcano, Slurm: either all N pods start or none do, so a half-placed job never holds GPUs while it waits.</p></div>
      <div class="card b"><h3>Topology-aware placement</h3><p>Place by node, then rail or pod. Fill nodes completely before spilling over, so large jobs keep contiguous blocks.</p></div>
      <div class="card c"><h3>Quotas and preemption</h3><p>Teams get guaranteed quotas and can borrow idle capacity. Borrowed, low-priority work is preempted (after a checkpoint) when the owner needs it back.</p></div>
    </div>
  </div>
</section>

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="Tricks and traps" tagclass="b7" -->

<!-- slide raw -->
<section class="slide" id="s-qa" data-chapter="Test yourself">
  <div class="inner">
    <div class="label">08 · Test yourself</div>
    <h2>Questions to test your understanding</h2>
    <hr>
    <details class="qa"><summary>MIG vs MPS vs time-slicing: when would you use each?</summary><div class="ans"><b>MIG</b>: untrusted multi-tenant or SLO-bound inference (hardware partitioning of memory, cache and SMs, fault isolation), with fixed profile sizes, up to 7 instances. <b>MPS</b>: cooperating processes from one team that each underuse the GPU, such as several small inference workers. It gives real concurrency but weak fault isolation. <b>Time-slicing</b>: dev, notebooks and CI, where convenience matters and performance or isolation guarantees don't. You can combine them, for example MPS inside a MIG instance.</div></details>
    <details class="qa"><summary>How would you serve 200 customer fine-tunes of a 70B model?</summary><div class="ans">Train them as <b>LoRA adapters</b> and serve with a <b>multi-LoRA</b> server (vLLM, S-LoRA, LoRAX): one copy of the base weights, with adapters in GPU memory or paged in from host memory based on popularity. Mixed-adapter batches use segmented-GEMM kernels, alongside continuous batching and paged KV. Route by adapter for cache locality. Capacity plan: base model ≈ 140 GB plus about 0.4 GB per rank-16 adapter, plus KV. Full fine-tunes would need about 200 separate deployments.</div></details>
    <details class="qa"><summary>Why can't a 64-GPU job start when the cluster shows 100 free GPUs?</summary><div class="ans"><b>Fragmentation</b> plus <b>gang and topology constraints</b>. The free GPUs are scattered across partly used nodes and pods, and the job needs whole nodes, ideally in one pod, all at the same time. Fixes: bin-packing placement for small jobs, reserving or draining nodes for large jobs, backfill of short jobs that finish in time, priority preemption, and placing small inference and dev work on separate pools (or MIG).</div></details>
    <details class="qa"><summary>What's continuous batching and why is it a big win?</summary><div class="ans">Scheduling happens at <b>each decode step</b> rather than per request. Finished sequences leave and waiting ones join immediately, so slots aren't held by padding until the longest output ends. Throughput goes up several times and queueing latency goes down. It pairs with chunked prefill (splitting long prompts so decode steps aren't blocked) and paged KV (no per-request contiguous allocation).</div></details>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-end" data-chapter="Test yourself">
  <div class="inner">
    <div class="label">09 · Take it with you</div>
    <h2>Four things to remember</h2>
    <hr>
    <div class="recap">
      <div><span><b>Time-slicing shares time, MPS shares SMs, and MIG partitions the hardware.</b> Isolation goes up in that order and flexibility goes down.</span></div>
      <div><span><b>MIG on an H100:</b> 7 compute slices × 8 memory slices of 10 GB, giving profiles 1g.10gb up to 7g.80gb.</span></div>
      <div><span><b>To share one model:</b> continuous batching and paged KV for many users, multi-LoRA for many fine-tunes.</span></div>
      <div><span><b>To share a cluster:</b> gang scheduling, topology-aware packing, quotas with borrowing, and preemption after checkpoint.</span></div>
    </div>
    <p class="start-hint">You've finished the series. <a href="../index.html">← Back to all GPU decks</a> · Previous: <a href="../07-heterogeneous-gpus/index.html">← 07</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
