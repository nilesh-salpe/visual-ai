---
title: Inside a GPU Server
body:
  data-deck: Inside a GPU server
  data-home: ../index.html
  data-home-label: GPU
styles:
- ../../shared/deck.css
- ../../shared/learn.css
css: |-
  .node-svg [data-info] { cursor: pointer; }
    .node-svg [data-info]:hover { filter: brightness(1.12); }
    .infobox { min-height: 64px; background: var(--panel-2); border-radius: 10px; padding: 12px 14px; font-size: 14px; color: var(--muted); margin-top: 12px; }
    .infobox b { color: var(--ink); }
    .topo { border-collapse: collapse; font: 500 12px 'JetBrains Mono', monospace; }
    .topo th, .topo td { padding: 5px 6px; text-align: center; border: 1px solid var(--line); }
    .topo th { color: var(--muted); font-weight: 600; background: var(--panel-2); }
    .topo td { cursor: default; }
    .topo td.NV { background: var(--e-soft); color: var(--e); }
    .topo td.PIX { background: var(--a-soft); color: var(--a); }
    .topo td.NODE { background: var(--b-soft); color: var(--b); }
    .topo td.SYS { background: var(--d-soft); color: var(--d); }
    .topo td.X { color: var(--faint); }
    .topo td.hl { outline: 2px solid var(--ink); outline-offset: -2px; }
scripts:
- ../../shared/deck.js
glance:
  steps:
  - 'GPU ↔ HBM :: 3,350 GB/s :: e'
  - 'GPU ↔ GPU :: NVLink 450 GB/s

    per direction :: a'
  - 'GPU ↔ CPU / NIC :: PCIe Gen5 64 GB/s :: b'
  - 'node ↔ node :: NIC 50 GB/s :: c'
  - 'storage :: NVMe ~7 GB/s :: f'
  caption: Bandwidth falls roughly 10× at each step away from the GPU.
example:
  title: 'Worked example: moving 1 GB'
  setup: Per-GPU, per-direction bandwidths from the deck.
  steps:
  - 'HBM: 1 GB ÷ 3,350 GB/s = <b>0.3 ms</b>.'
  - 'NVLink: 1 GB ÷ 450 GB/s = <b>2.2 ms</b>.'
  - 'PCIe Gen5: 1 GB ÷ 64 GB/s = <b>15.6 ms</b>.'
  - 'NIC (400 Gb/s): 1 GB ÷ 50 GB/s = <b>20.0 ms</b>.'
  - 'NVMe: 1 GB ÷ 7 GB/s = <b>142.9 ms</b>.'
  - 'Implication: keep tensor-parallel traffic on NVLink, data-parallel gradients on the network, and checkpoints off the critical path.'
  result: 'The same gigabyte takes 0.3 ms in HBM and 143 ms from NVMe: placement decides speed.'
traps:
  tricks:
  - 'Memorize the ladder. :: HBM 3,350 · NVLink 450 · PCIe 64 · NIC 50 · NVMe 7 GB/s.'
  - 'Check affinity. :: nvidia-smi topo -m shows which NIC and CPU socket sit closest to each GPU.'
  - 'Power sets capacity. :: A DGX H100 draws ~10.2 kW; racks are sized in kilowatts, not GPUs.'
  traps:
  - 'Cross-socket traffic. :: A GPU using a NIC on the other CPU socket pays extra hops.'
  - 'PCIe as GPU-to-GPU path. :: Without NVLink, tensor parallelism is much slower.'
  - 'Ignoring thermals. :: Hot GPUs throttle clocks and become stragglers.'
papers:
- nvl72
- llama3
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">GPU for GenAI · 04</div>
    <h1>Inside a GPU server:<br>8 GPUs, 4 switches, 1 box</h1>
    <p class="sub">The 8-GPU HGX/DGX node is the basic unit of AI (artificial intelligence) infrastructure. This deck shows what is inside it, how data moves between its parts, and which link is the bottleneck for each kind of traffic.</p>
    <div class="toc" data-auto></div>
    <p class="start-hint">Press <kbd>→</kbd> or <kbd>Space</kbd> to begin.</p>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-map" data-chapter="The box">
  <div class="inner">
    <div class="label">01 · The box</div>
    <h2>An HGX H100 node, opened up</h2>
    <hr>
    <p class="lede">Hover or tap any component. Two separate networks run through this box: <span class="em-e">NVLink</span> connects the GPUs (graphics processing units) to each other through NVSwitch, and <span class="em-c">PCIe (PCI (Peripheral Component Interconnect) Express, the standard expansion bus)</span> connects the GPUs to the CPUs (central processing units), NICs (network interface cards) and storage.</p>
    <div class="visual"><svg id="mapSvg" class="node-svg" viewBox="0 0 900 360" role="img" aria-label="HGX H100 node diagram"></svg>
      <div class="infobox" id="mapInfo"><b>DGX H100</b>: 8× H100 SXM (640 GB HBM3 (third-generation high-bandwidth memory) in total), 4× NVSwitch, 8× ConnectX-7 400 Gb/s compute NICs, 2× Xeon CPUs, 2 TB DDR5 (fifth-generation double-data-rate memory), about 30 TB of NVMe (Non-Volatile Memory Express, the fast interface for flash storage), up to about 10.2 kW.</div>
    </div>
    <div class="cite">NVIDIA DGX H100 user guide and datasheet. PCIe switch arrangement simplified; it varies by OEM (HGX boards go into Dell, Supermicro, HPE and other servers).</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-paths" data-chapter="Data paths">
  <div class="inner">
    <div class="label">02 · Data paths</div>
    <h2>Follow the bytes: each kind of traffic takes a different path</h2>
    <hr>
    <div class="seg" id="pathSeg">
      <button data-v="nvl" class="on">GPU ↔ GPU (in node)</button>
      <button data-v="rdma">GPU → remote GPU</button>
      <button data-v="bounce">… without GPUDirect</button>
      <button data-v="h2d">CPU → GPU</button>
      <button data-v="gds">NVMe → GPU (GDS)</button>
    </div>
    <div class="visual"><svg id="pathSvg" class="node-svg" viewBox="0 0 900 360" role="img" aria-label="Animated data path"></svg>
      <div class="grid3" style="margin-top:10px">
        <div class="stat"><div class="num" id="pBW" style="color:var(--a)"></div><div class="lbl">bandwidth per GPU (one direction)</div></div>
        <div class="stat"><div class="num" id="pT"></div><div class="lbl">time to move 10 GB</div></div>
        <div class="stat"><div class="num" id="pUse" style="font:600 15px Inter"></div><div class="lbl">used for</div></div>
      </div>
      <div class="infobox" id="pathInfo"></div>
    </div>
    <div class="takeaway">Inside the node a GPU gets about 450 GB/s per direction; to another node it gets about 50 GB/s. That 9× gap determines how every parallelism strategy is mapped onto the hardware: tensor parallelism stays on NVLink, and only data and pipeline parallelism cross the network.</div>
  
    <!--x:glance--><div class="glance"><h4>At a glance</h4><svg viewBox="0 0 660 152" role="img" aria-label="Bandwidth falls roughly 10× at each step away from the GPU." class="glance-svg"><defs><marker id="gArr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--muted)"/></marker></defs><rect x="10.0" y="28" width="113.6" height="64" rx="10" style="fill:var(--e)"/><text x="66.8" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">GPU ↔ HBM</text><text x="66.8" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">3,350 GB/s</text><rect x="141.6" y="28" width="113.6" height="64" rx="10" style="fill:var(--a)"/><text x="198.4" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">GPU ↔ GPU</text><text x="198.4" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">NVLink 450 GB/s</text><text x="198.4" y="123.0" text-anchor="middle" class="tm" style="font-size:11px">per direction</text><line x1="125.6" y1="60.0" x2="139.6" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/><rect x="273.2" y="28" width="113.6" height="64" rx="10" style="fill:var(--b)"/><text x="330.0" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">GPU ↔ CPU / NIC</text><text x="330.0" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">PCIe Gen5 64 GB/s</text><line x1="257.2" y1="60.0" x2="271.2" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/><rect x="404.8" y="28" width="113.6" height="64" rx="10" style="fill:var(--c)"/><text x="461.6" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">node ↔ node</text><text x="461.6" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">NIC 50 GB/s</text><line x1="388.8" y1="60.0" x2="402.8" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/><rect x="536.4" y="28" width="113.6" height="64" rx="10" style="fill:var(--faint)"/><text x="593.2" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">storage</text><text x="593.2" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">NVMe ~7 GB/s</text><line x1="520.4" y1="60.0" x2="534.4" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/></svg><p class="caption" style="margin:4px 0 0">Bandwidth falls roughly 10× at each step away from the GPU.</p></div><!--/x:glance-->
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-ladder" data-chapter="Data paths">
  <div class="inner">
    <div class="label">03 · Data paths</div>
    <h2>Bandwidth falls off at each step away from the GPU</h2>
    <hr>
    <div class="visual"><div id="ladBars"></div>
      <div class="controls"><label class="ctl">All-reduce size <input type="range" id="arS" min="-1" max="2" step="0.05" value="0.845"> <output id="arSo"></output></label></div>
      <div class="grid2" style="margin-top:10px">
        <div class="stat"><div class="num" id="arIn" style="color:var(--e)"></div><div class="lbl">ring all-reduce, 8 GPUs over NVLink</div></div>
        <div class="stat"><div class="num" id="arOut" style="color:var(--d)"></div><div class="lbl">same, 8 GPUs on 8 nodes over 400G NICs</div></div>
      </div>
    </div>
    <p class="caption">All-reduce time ≈ 2·(n−1)/n × size ÷ per-GPU bandwidth, ignoring latency. Default: 7 GB, the BF16 (bfloat16, a 16-bit floating-point format with the exponent range of 32-bit floats) gradients of a 3.5B model. In-node bandwidth uses 450 GB/s; the NVLink SHARP (Scalable Hierarchical Aggregation and Reduction Protocol, in-network reduction on NVIDIA switches) in-switch reduction on NVSwitch can do better.</p>
    <div class="takeaway">Per GPU and per direction: HBM (high-bandwidth memory) 3,350 · NVLink 450 · PCIe Gen5 64 · NIC 50 · NVMe ~7 GB/s. Memorize these five numbers.</div>
  </div>
</section>

<!-- slide id="s-example" from="example" chapter="Example" tag="Worked example" tagclass="b5" -->

<!-- slide raw -->
<section class="slide" id="s-topo" data-chapter="Affinity">
  <div class="inner">
    <div class="label">04 · Affinity</div>
    <h2><code>nvidia-smi topo -m</code>: which GPUs, NICs and CPUs are close to each other</h2>
    <hr>
    <p class="lede">A node has two CPU sockets (two NUMA (non-uniform memory access) domains). If a dataloader on socket 1 feeds GPU 0, or GPU 0 sends through a NIC on the other socket, traffic crosses the inter-socket link (UPI (Intel's Ultra Path Interconnect between CPU sockets)) and loses bandwidth. Hover any cell.</p>
    <div>
      <div class="visual scroll-x"><table class="topo" id="topo" style="margin:0 auto"></table>
        <div class="infobox" id="topoInfo">Hover a cell.</div></div>
      <div class="visual">
        <table class="tbl" style="margin-top:12px">
          <tr><td><code>NV#</code></td><td>Connected by # NVLinks (NV18 = 18 NVLink 4 links ≈ 900 GB/s bidirectional)</td></tr>
          <tr><td><code>PIX</code></td><td>Same PCIe switch, so the shortest PCIe path. Best GPU↔NIC pairing for GPUDirect RDMA (remote direct memory access).</td></tr>
          <tr><td><code>NODE</code></td><td>Same CPU socket, different PCIe switch: goes through the CPU root complex.</td></tr>
          <tr><td><code>SYS</code></td><td>Crosses sockets over UPI, which is slower and less predictable.</td></tr>
        </table>
      </div>
    </div>
    <div class="takeaway">NCCL (NVIDIA Collective Communications Library) reads this topology and picks the NIC for each GPU, ideally PIX. When jobs are slow, check the pinning: <code>numactl</code> and CPU affinity for dataloaders, and <code>NCCL_IB_HCA</code> or <code>NCCL_TOPO_FILE</code> when auto-detection gets it wrong (common in VMs (virtual machines)).</div>
    <div class="cite">Illustrative matrix for a 2-socket, 8-GPU, 8-NIC node. Run the command on your own hardware.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-power" data-chapter="Power">
  <div class="inner">
    <div class="label">05 · Power</div>
    <h2>Power is the real limit: a cluster's capacity is set by megawatts</h2>
    <hr>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <select id="pwSys">
          <option value="10.2,8">DGX H100 · 8 GPUs · ~10.2 kW</option>
          <option value="14.3,8">DGX B200 · 8 GPUs · ~14.3 kW</option>
          <option value="120,72">GB200 NVL72 rack · 72 GPUs · ~120 kW</option>
        </select>
        <label class="ctl">Rack power budget <input type="range" id="pwR" min="10" max="140" step="5" value="40"> <output id="pwRo"></output></label>
        <label class="ctl">Cluster GPUs <input type="range" id="pwG" min="10" max="17" step="1" value="14"> <output id="pwGo"></output></label>
        <label class="ctl">PUE <input type="range" id="pwP" min="1.05" max="1.6" step="0.05" value="1.2"> <output id="pwPo"></output></label>
      </div>
      <div class="grid4" style="margin-top:16px">
        <div class="stat"><div class="num" id="pwPer"></div><div class="lbl">systems per rack</div></div>
        <div class="stat"><div class="num" id="pwGR"></div><div class="lbl">GPUs per rack</div></div>
        <div class="stat"><div class="num" id="pwRacks"></div><div class="lbl">racks for the cluster</div></div>
        <div class="stat"><div class="num" id="pwMW" style="color:var(--d)"></div><div class="lbl">facility power</div></div>
      </div>
      <svg id="pwSvg" viewBox="0 0 660 120" style="margin-top:12px" role="img" aria-label="Racks"></svg>
    </div>
    <p class="caption">Typical air-cooled data-center racks were designed for about 10–20 kW. A single DGX H100 nearly fills one. Blackwell rack-scale systems need direct liquid cooling. PUE (power usage effectiveness) = facility power ÷ IT (information technology) power.</p>
    <div class="takeaway">"Why don't you just add more GPUs?" Because of power, cooling and floor space. A 16K-GPU H100 cluster draws about 25 MW, which is roughly the consumption of a small town.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-nvl72" data-chapter="Scale-up">
  <div class="inner">
    <div class="label">06 · Scale-up</div>
    <h2>The NVLink domain grows from 8 GPUs to 72</h2>
    <hr>
    <p class="lede">GB200 NVL72 puts 72 Blackwell GPUs and 36 Grace CPUs in one rack, all connected through NVLink switch trays. Every GPU can reach every other GPU at 1.8 TB/s, so the whole rack works like <b>one big GPU</b> for tensor and expert parallelism.</p>
    <div class="visual">
      <div class="seg" id="sdSeg"><button data-v="8" class="on">HGX H100 (8)</button><button data-v="72">GB200 NVL72 (72)</button></div>
      <svg id="sdSvg" viewBox="0 0 660 240" style="margin-top:12px" role="img" aria-label="NVLink domain"></svg>
      <div class="grid4" style="margin-top:8px">
        <div class="stat"><div class="num" id="sdG"></div><div class="lbl">GPUs in one NVLink domain</div></div>
        <div class="stat"><div class="num" id="sdBW"></div><div class="lbl">NVLink per GPU (bidir.)</div></div>
        <div class="stat"><div class="num" id="sdAgg"></div><div class="lbl">aggregate NVLink</div></div>
        <div class="stat"><div class="num" id="sdMem"></div><div class="lbl">HBM in domain</div></div>
      </div>
    </div>
    <div class="takeaway">A bigger scale-up domain means tensor parallelism and MoE (Mixture of Experts) all-to-all traffic can span more GPUs without touching the slower network. Frontier labs care about this because MoE inference is limited by all-to-all bandwidth.</div>
    <div class="cite">NVIDIA GB200 NVL72 product page: 72 GPUs, 130 TB/s aggregate NVLink, ~13.5 TB HBM3e. HGX H100: 900 GB/s per GPU over NVLink 4.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-debug" data-chapter="Scale-up">
  <div class="inner">
    <div class="label">07 · In practice</div>
    <h2>A node is slow. What do you check?</h2>
    <hr>
    <div class="grid2">
      <div class="card a"><h3>1 · Clocks and throttling</h3><p><code>nvidia-smi -q -d PERFORMANCE,CLOCK,POWER,TEMPERATURE</code>: look for thermal or power-cap throttling, or clocks locked low. One hot GPU slows the whole job.</p></div>
      <div class="card b"><h3>2 · Errors</h3><p><code>dmesg | grep -i xid</code>, ECC (error-correcting code) counters and row remapping (<code>nvidia-smi -q -d ECC,ROW_REMAPPER</code>), NVLink error counters.</p></div>
      <div class="card c"><h3>3 · Topology and links</h3><p><code>nvidia-smi topo -m</code>, <code>nvidia-smi nvlink -s</code> (are all links up?), <code>lspci -vv</code> for the negotiated PCIe width and speed (x16 Gen5, not x8 Gen3).</p></div>
      <div class="card e"><h3>4 · Microbenchmarks</h3><p><code>dcgmi diag -r 3</code>, <code>nccl-tests all_reduce_perf</code> (compare busbw with a known-good node), and a GEMM (general matrix multiplication) burn-in to check sustained TFLOPS (trillion floating-point operations per second).</p></div>
    </div>
    <div class="takeaway">Labs run these as <b>preflight checks</b> before admitting a node into a training job, and keep a quarantine pool for nodes that fail. Deck 06 covers this in detail.</div>
  </div>
</section>

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="Tricks and traps" tagclass="b7" -->

<!-- slide raw -->
<section class="slide" id="s-qa" data-chapter="Test yourself">
  <div class="inner">
    <div class="label">08 · Test yourself</div>
    <h2>Questions to test your understanding</h2>
    <hr>
    <details class="qa"><summary>Walk me through what's in an 8×H100 server and how the GPUs talk.</summary><div class="ans">There are 8 SXM GPUs on an HGX baseboard. Each has 18 NVLink 4 links that go to <b>4 NVSwitch chips</b>, so any GPU can reach any other at 900 GB/s bidirectional, all-to-all, without blocking. Separately, PCIe Gen5 switches connect GPUs to <b>one 400G NIC per GPU</b> (ConnectX-7, used with GPUDirect RDMA), to NVMe, and to the 2 CPU sockets. The CPUs handle orchestration and data loading but sit off the hot path.</div></details>
    <details class="qa"><summary>What does GPUDirect RDMA do and why does it matter?</summary><div class="ans">It lets the NIC <b>read and write GPU memory directly</b> over PCIe, with no staging copy in host DRAM (dynamic random-access memory) and no CPU involvement. Without it, every inter-node message is copied GPU → host → NIC, which doubles the PCIe traffic, adds latency and uses CPU memory bandwidth. NCCL depends on it for inter-node collectives. GPUDirect Storage does the same for NVMe and parallel file systems.</div></details>
    <details class="qa"><summary>Why is there one NIC per GPU?</summary><div class="ans">So that each GPU gets <b>its own 400 Gb/s (50 GB/s) path</b> to the network behind a nearby PCIe switch (PIX affinity), which avoids PCIe and UPI contention. It also matches the rail-optimized network design: GPU i in every node connects to the same leaf switch (rail i). See deck 05.</div></details>
    <details class="qa"><summary>Can you train with PCIe H100 cards instead of SXM? What changes?</summary><div class="ans">PCIe H100s have a lower TDP (about 350 W vs 700 W), fewer SMs (streaming multiprocessors) and lower HBM bandwidth, and only an optional NVLink <b>bridge between pairs</b> rather than NVSwitch all-to-all. Tensor parallelism across 8 GPUs would then go over PCIe (~64 GB/s), which is far too slow. They suit inference of models that fit on 1–2 GPUs, but not large-scale training.</div></details>
    <details class="qa"><summary>What's the practical limit on how many H100s you can put in a data hall?</summary><div class="ans"><b>Power and cooling</b>, not floor space. Each DGX H100 draws about 10 kW, so a 16K-GPU cluster is about 20 MW of IT load and about 25 MW of facility load at PUE 1.2. Many existing data centers can't deliver 40+ kW per rack, which is why new AI builds are designed around power and use liquid cooling for Blackwell-class racks.</div></details>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-end" data-chapter="Test yourself">
  <div class="inner">
    <div class="label">09 · Take it with you</div>
    <h2>Four things to remember</h2>
    <hr>
    <div class="recap">
      <div><span><b>There are two fabrics in the box:</b> NVLink/NVSwitch (GPU↔GPU, 900 GB/s bidirectional) and PCIe (GPU↔NIC, NVMe and CPU, ~64 GB/s per direction).</span></div>
      <div><span><b>One 400G NIC per GPU, with GPUDirect RDMA</b>, gives about 50 GB/s per GPU off the node, roughly 9× less than NVLink.</span></div>
      <div><span><b>Topology and NUMA affinity matter.</b> Check them with <code>nvidia-smi topo -m</code>; wrong pinning quietly costs bandwidth.</span></div>
      <div><span><b>Power is the binding constraint.</b> NVL72-style racks make the scale-up domain bigger at about 120 kW per rack.</span></div>
    </div>
    <p class="start-hint">Next: <a href="../05-cluster-topology/index.html">05 · Cluster topology →</a> · Previous: <a href="../03-memory-hierarchy/index.html">← 03</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
