---
title: Heterogeneous GPUs
body:
  data-deck: Heterogeneous GPUs
  data-home: ../index.html
  data-home-label: GPU
styles:
- ../../shared/deck.css
- ../../shared/learn.css
css: |-
  .infobox { min-height: 80px; background: var(--panel-2); border-radius: 10px; padding: 12px 14px; font-size: 14px; color: var(--muted); margin-top: 12px; }
    .infobox b { color: var(--ink); }
    .spec td:first-child { font-weight: 600; }
    .spec td.best { color: var(--e); font-weight: 700; }
scripts:
- ../../shared/deck.js
glance:
  steps:
  - 'mixed fleet :: A100, H100, H200, B200 :: f'
  - 'classify work :: training, prefill, decode, batch :: c'
  - 'match :: compute-heavy → newest

    memory-bound → older :: a'
  - 'balance :: work ∝ speed :: e'
  caption: Mixing hurts synchronous training unless work is balanced; it helps when phases have different needs.
example:
  title: 'Worked example: A100s and H100s in one synchronous job'
  setup: 'Dense BF16 peak: A100 312 TFLOP/s, H100 989 TFLOP/s. Equal per-GPU batches.'
  steps:
  - 'Each step waits for the A100: the H100 finishes in 32% of the step and idles <b>68%</b> of the time.'
  - 'Balance by speed: give each H100 3.2× the work of an A100.'
  - 'In a 1 A100 : 1 H100 pair, the H100 should get <b>76%</b> of the batch.'
  - Pipeline parallelism can instead give faster GPUs more layers.
  result: Heterogeneity is fine when the work split follows each GPU's speed (and memory); equal splits waste the faster GPUs.
traps:
  tricks:
  - 'Split work ∝ throughput. :: Batch share or layer count per GPU type.'
  - 'Prefill on new, decode on old. :: Decode is memory-bound and runs well on older GPUs (Splitwise).'
  - 'Keep TP within one GPU type. :: Mixed types inside a TP group run at the slowest.'
  traps:
  - 'Equal batches on unequal GPUs. :: The fast GPUs idle at every all-reduce.'
  - 'Numerics differences. :: Different kernels and formats (FP8 support) change results slightly.'
  - 'Interconnect mismatch. :: Different NVLink generations can''t share a domain.'
papers:
- splitwise
- distserve
- mooncake
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">GPU for GenAI · 07</div>
    <h1>Heterogeneous GPUs:<br>getting value from a mixed fleet</h1>
    <p class="sub">Real fleets mix A100s, H100s, H200s, B200s and sometimes other vendors. This deck covers why mixing hurts synchronous training, how to rebalance the work, where mixed hardware actually helps (disaggregated inference), and what breaks along the way.</p>
    <div class="toc" data-auto></div>
    <p class="start-hint">Press <kbd>→</kbd> or <kbd>Space</kbd> to begin.</p>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-fleet" data-chapter="The fleet">
  <div class="inner">
    <div class="label">01 · The fleet</div>
    <h2>A new GPU generation every ~2 years, and old ones stay in service for 5+</h2>
    <hr>
    <p class="lede">Supply constraints, depreciation schedules and long contracts mean any large lab runs several generations at once. Pick two GPUs (graphics processing units) to see how different they are.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <select id="gA"></select><span class="ctl">vs</span><select id="gB"></select>
      </div>
      <div class="scroll-x" style="margin-top:12px"><table class="tbl spec" id="specTbl"></table></div>
      <div id="ratioBars" style="margin-top:14px"></div>
    </div>
    <div class="cite">Vendor datasheets, dense (non-sparse) peak values. B200 figures vary by system configuration (HGX vs GB200); treat them as approximate.</div>
  
    <!--x:glance--><div class="glance"><h4>At a glance</h4><svg viewBox="0 0 660 152" role="img" aria-label="Mixing hurts synchronous training unless work is balanced; it helps when phases have different needs." class="glance-svg"><defs><marker id="gArr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--muted)"/></marker></defs><rect x="10.0" y="28" width="146.5" height="64" rx="10" style="fill:var(--faint)"/><text x="83.2" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:13px">mixed fleet</text><text x="83.2" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">A100, H100, H200, B200</text><rect x="174.5" y="28" width="146.5" height="64" rx="10" style="fill:var(--c)"/><text x="247.8" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:13px">classify work</text><text x="247.8" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">training, prefill,</text><text x="247.8" y="123.0" text-anchor="middle" class="tm" style="font-size:11px">decode, batch</text><line x1="158.5" y1="60.0" x2="172.5" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/><rect x="339.0" y="28" width="146.5" height="64" rx="10" style="fill:var(--a)"/><text x="412.2" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:13px">match</text><text x="412.2" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">compute-heavy → newest</text><text x="412.2" y="123.0" text-anchor="middle" class="tm" style="font-size:11px">memory-bound → older</text><line x1="323.0" y1="60.0" x2="337.0" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/><rect x="503.5" y="28" width="146.5" height="64" rx="10" style="fill:var(--e)"/><text x="576.8" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:13px">balance</text><text x="576.8" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">work ∝ speed</text><line x1="487.5" y1="60.0" x2="501.5" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/></svg><p class="caption" style="margin:4px 0 0">Mixing hurts synchronous training unless work is balanced; it helps when phases have different needs.</p></div><!--/x:glance-->
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-slow" data-chapter="Training">
  <div class="inner">
    <div class="label">02 · Training</div>
    <h2>Synchronous training runs at the speed of the slowest GPU</h2>
    <hr>
    <p class="lede">With equal per-GPU batches, every step waits for the slowest rank. Mix A100s into an H100 job and the H100s spend most of each step <b>idle at the all-reduce</b>.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">Share of A100s <input type="range" id="hMix" min="0" max="100" step="12.5" value="25"> <output id="hMixo"></output></label>
        <div class="seg" id="hMode"><button data-v="eq" class="on">Equal batch per GPU</button><button data-v="prop">Batch ∝ GPU speed</button></div>
      </div>
      <svg id="hSvg" viewBox="0 0 660 230" style="margin-top:12px" role="img" aria-label="Per-rank step times"></svg>
      <div class="legend"><span><i style="background:var(--a)"></i>H100 compute</span><span><i style="background:var(--b)"></i>A100 compute</span><span><i style="background:var(--d-soft);border:1px solid var(--d)"></i>idle waiting</span></div>
      <div class="grid3" style="margin-top:8px">
        <div class="stat"><div class="num" id="hThr" style="color:var(--a)"></div><div class="lbl">throughput vs. H100s alone</div></div>
        <div class="stat"><div class="num" id="hIdle" style="color:var(--d)"></div><div class="lbl">H100 time spent idle</div></div>
        <div class="stat"><div class="num" id="hGain"></div><div class="lbl">gain from adding the A100s</div></div>
      </div>
    </div>
    <p class="caption">Model: 8 ranks; an A100 is about 3× slower than an H100 at BF16 (bfloat16, a 16-bit floating-point format with the exponent range of 32-bit floats) GEMMs (312 vs 989 TFLOPS (trillion floating-point operations per second) peak; the measured gap is often 2–3×). With proportional batching, gradients must be averaged <b>weighted by sample count</b>.</p>
    <div class="takeaway">With equal batches, adding slow GPUs can make the job <em>slower</em> than leaving them out. Uneven batches fix the compute imbalance, but memory limits and the communication pattern still differ between the two types.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-pipe" data-chapter="Training">
  <div class="inner">
    <div class="label">03 · Training</div>
    <h2>Pipeline parallel on mixed GPUs: balance the layers by speed</h2>
    <hr>
    <p class="lede">Put 80 layers on 4 pipeline stages: 2 on H100s and 2 on A100s. With an equal split, the A100 stages become the bottleneck and the pipeline stalls. Rebalance by giving faster stages more layers, as long as each stage's <b>memory</b> still fits.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <div class="seg" id="ppMode"><button data-v="eq" class="on">20 / 20 / 20 / 20</button><button data-v="bal">Balanced by speed</button></div>
        <span class="readout" id="ppSplit"></span>
      </div>
      <svg id="ppSvg" viewBox="0 0 660 230" style="margin-top:12px" role="img" aria-label="Pipeline Gantt chart"></svg>
      <div class="grid3" style="margin-top:6px">
        <div class="stat"><div class="num" id="ppT"></div><div class="lbl">time for 8 micro-batches (forward)</div></div>
        <div class="stat"><div class="num" id="ppU"></div><div class="lbl">average stage utilization</div></div>
        <div class="stat"><div class="num" id="ppMem"></div><div class="lbl">largest stage memory (weights + optimizer)</div></div>
      </div>
    </div>
    <p class="caption">Each block is one micro-batch passing through one stage. Grey gaps are idle time. Memory assumes a 70B model at 16 B/param split by layer, sharded 16 ways by DP (data parallelism)/ZeRO (Zero Redundancy Optimizer), against an 80 GB limit per GPU.</p>
    <div class="takeaway">Heterogeneous pipelines are an optimization problem with two constraints: equalize stage time and stay within each stage's memory. Research systems solve it automatically (Metis, HexiScale, Cephalo), but production labs usually avoid mixing GPU types inside one training job.</div>
  </div>
</section>

<!-- slide id="s-example" from="example" chapter="Example" tag="Worked example" tagclass="b5" -->

<!-- slide raw -->
<section class="slide" id="s-disagg" data-chapter="Inference">
  <div class="inner">
    <div class="label">04 · Inference</div>
    <h2>Where mixing helps: prefill and decode on different hardware</h2>
    <hr>
    <p class="lede">Prefill is <b>compute-bound</b> and decode is <b>bandwidth-bound</b> (see deck 02). Disaggregated serving runs them on separate GPU pools, each matched to its phase, and sends the KV (key-value) cache between them.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">Prefill pool <select id="dP"></select></label>
        <label class="ctl">Decode pool <select id="dD"></select></label>
        <div class="seg" id="dLink"><button data-v="50" class="on">KV over 400G network</button><button data-v="450">KV over NVLink</button></div>
      </div>
      <svg id="dSvg" viewBox="0 0 660 150" style="margin-top:12px" role="img" aria-label="Disaggregated serving"></svg>
      <div class="grid4" style="margin-top:8px">
        <div class="stat"><div class="num" id="dTTFT"></div><div class="lbl">prefill time (4K prompt)</div></div>
        <div class="stat"><div class="num" id="dKV"></div><div class="lbl">KV transfer</div></div>
        <div class="stat"><div class="num" id="dTPOT"></div><div class="lbl">time per output token (batch 1)</div></div>
        <div class="stat"><div class="num" id="dNote" style="font:600 14px Inter"></div><div class="lbl">note</div></div>
      </div>
    </div>
    <p class="caption">Model: 70B in FP8 (8-bit floating point) on 8 GPUs per pool. Prefill at 50% of FP8 peak. Decode reads 70 GB of weights per step at 80% of HBM (high-bandwidth memory) bandwidth. FP8 KV ≈ 160 KB/token, so 4K tokens ≈ 0.67 GB.</p>
    <div class="takeaway">Separating the pools also removes <b>interference</b>: a long prefill no longer pauses everyone's decode. Splitwise, DistServe, Mooncake and NVIDIA Dynamo all use this design. The cost is moving the KV cache between pools, which needs fast links or pipelined transfer.</div>
    <div class="cite">Patel et al., "Splitwise" (ISCA 2024); Zhong et al., "DistServe" (OSDI 2024); Qin et al., "Mooncake" (2024).</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-break" data-chapter="Gotchas">
  <div class="inner">
    <div class="label">05 · Gotchas</div>
    <h2>What breaks when you mix GPUs</h2>
    <hr>
    <div class="grid3">
      <div class="card d"><h3>Numerics</h3><p>V100 has no BF16, and A100 has no FP8. A recipe that depends on FP8 Tensor Cores can't run on the older parts, and changing precision changes training dynamics.</p></div>
      <div class="card b"><h3>Kernels</h3><p>FlashAttention-3, <code>wgmma</code> and TMA (Tensor Memory Accelerator) are Hopper-only, and Blackwell adds new instructions. You end up maintaining several code paths and checking that they agree numerically.</p></div>
      <div class="card c"><h3>Communication</h3><p>NCCL (NVIDIA) and RCCL (AMD) don't interoperate in one collective. Mixed-vendor jobs need separate groups joined by a gateway, or they don't work at all.</p></div>
      <div class="card a"><h3>Memory shape</h3><p>40 vs 80 vs 141 vs 192 GB means different shard sizes, batch sizes and KV capacity. One parallelism config no longer fits every GPU.</p></div>
      <div class="card e"><h3>Reproducibility</h3><p>Different kernels and reduction orders give results that differ in the last bits. Bitwise reproducibility across generations is effectively impossible.</p></div>
      <div class="card"><h3>Operations</h3><p>Different drivers, firmware, failure modes and topologies (NVLink-8 vs NVL72 vs PCIe (PCI (Peripheral Component Interconnect) Express, the standard expansion bus)). Scheduling has to understand GPU types.</p></div>
    </div>
    <div class="takeaway">The common pattern in industry: keep each <b>training job on one GPU type</b>, and use the mix at the <b>fleet level</b>, putting each workload on the generation that suits it.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-place" data-chapter="Gotchas">
  <div class="inner">
    <div class="label">06 · Placement</div>
    <h2>Matching workloads to GPU generations</h2>
    <hr>
    <div class="seg" id="wSeg">
      <button data-v="pre" class="on">Frontier pretraining</button><button data-v="rl">RL rollouts</button><button data-v="sft">SFT / small models</button><button data-v="dec">Long-context decode</button><button data-v="eval">Evals &amp; batch</button><button data-v="emb">Embeddings</button>
    </div>
    <div class="visual">
      <div class="grid2" style="align-items:center">
        <div id="wBars"></div>
        <div class="infobox" id="wInfo" style="margin-top:0"></div>
      </div>
    </div>
    <p class="caption">Fit scores are judgement calls meant for discussion, not benchmarks. They weigh compute, bandwidth, memory, interconnect and opportunity cost.</p>
    <div class="takeaway">Old GPUs aren't useless: they handle evals, data processing, embedding and small-model work well. That frees the newest parts for the jobs that need the largest NVLink domain and FP8 or FP4 (4-bit floating point).</div>
  </div>
</section>

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="Tricks and traps" tagclass="b7" -->

<!-- slide raw -->
<section class="slide" id="s-qa" data-chapter="Test yourself">
  <div class="inner">
    <div class="label">07 · Test yourself</div>
    <h2>Questions to test your understanding</h2>
    <hr>
    <details class="qa"><summary>You have 2K H100s and 2K A100s. How do you use them for one model?</summary><div class="ans">Don't run one synchronous job across both. Equal-batch DP would run at A100 speed, and proportional batching makes memory and communication harder. Better options: (1) run <b>pretraining on the H100s</b> and put <b>evals, data processing, RL (reinforcement learning) rollouts or inference on the A100s</b>; (2) if it must be one job, use <b>separate pipeline stages per type</b> with layers balanced by speed, or weighted DP; (3) for serving, use disaggregation: prefill on the H100s, decode on whichever has the best bandwidth per dollar.</div></details>
    <details class="qa"><summary>Why does disaggregated prefill/decode make sense?</summary><div class="ans">The two phases have opposite bottlenecks: prefill is compute-bound (needs TFLOPS) and decode is bandwidth- and capacity-bound (needs HBM bandwidth and KV space). Running them together means long prefills stall decode (bad TPOT (time per output token) tail latency) and each batch is a compromise. Splitting them lets you size and choose hardware per phase and tune TTFT (time to first token) and TPOT SLOs (service-level objectives) independently. The cost is moving the KV cache, which has to go over RDMA (remote direct memory access) or NVLink and be pipelined layer by layer.</div></details>
    <details class="qa"><summary>What changes when you port a training stack from H100 to MI300X?</summary><div class="ans">The software stack changes from CUDA (Compute Unified Device Architecture, NVIDIA's programming platform for its graphics processors) to ROCm (AMD's Radeon Open Compute software stack for its graphics processors)/HIP (AMD's Heterogeneous-computing Interface for Portability) and NCCL to RCCL. Kernels must be ported or come from Triton (FlashAttention has ROCm versions). The parallelism plan changes too: 192 GB of HBM allows larger shards and less TP or PP (pipeline parallelism), and the GPU-to-GPU fabric differs (Infinity Fabric, with a different topology). Budget for numerical validation: loss curves must match the reference within tolerance before you scale up.</div></details>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-end" data-chapter="Test yourself">
  <div class="inner">
    <div class="label">08 · Take it with you</div>
    <h2>Four things to remember</h2>
    <hr>
    <div class="recap">
      <div><span><b>A synchronous job runs at the speed of its slowest GPU.</b> Mixing generations in one job wastes the fast ones unless you rebalance.</span></div>
      <div><span><b>Rebalance by speed:</b> batch per GPU in DP, layers per stage in PP, both subject to memory limits.</span></div>
      <div><span><b>Disaggregated serving is where mixing pays off:</b> prefill on compute-heavy GPUs, decode on bandwidth-heavy ones.</span></div>
      <div><span><b>Use one GPU type per job and mix at the fleet level</b>, putting each workload on the generation that suits it.</span></div>
    </div>
    <p class="start-hint">Next: <a href="../08-sharing-gpus/index.html">08 · Sharing GPUs →</a> · Previous: <a href="../06-gpu-failures/index.html">← 06</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
