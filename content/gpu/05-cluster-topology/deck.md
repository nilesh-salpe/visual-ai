---
title: GPU Cluster Topology
body:
  data-deck: Cluster topology
  data-home: ../index.html
  data-home-label: GPU
styles:
- ../../shared/deck.css
- ../../shared/learn.css
css: |-
  #ftSvg circle.ep { cursor: pointer; }
    .warn { color: var(--d); font-weight: 600; }
    .ok { color: var(--e); font-weight: 600; }
    .checks div { padding: 6px 0; border-bottom: 1px solid var(--line); font-size: 14px; }
    .checks div:last-child { border-bottom: 0; }
scripts:
- ../../shared/deck.js
glance:
  steps:
  - 'GPU :: in an NVLink domain :: e'
  - 'node :: 8 GPUs, NVSwitch :: a'
  - 'leaf switch :: rail-optimized :: b'
  - 'spine :: fat tree :: c'
  - 'cluster :: 16K GPUs :: f'
  caption: Scale-up inside the node (NVLink), scale-out between nodes (InfiniBand or RoCE).
example:
  title: 'Worked example: one all-reduce of gradients'
  setup: An 8B-parameter model has 16 GB of BF16 gradients. Ring all-reduce over N = 8 participants sends 2(N − 1)/N × S per GPU.
  steps:
  - 'Data per GPU: 2 × 7/8 × 16 GB = <b>28 GB</b>.'
  - 'Inside one node over NVLink (450 GB/s): <b>62 ms</b>.'
  - 'Across 8 nodes over 400 Gb/s NICs (50 GB/s): <b>560 ms</b>.'
  - The bandwidth term barely changes with N (2(N−1)/N → 2), but the latency term grows with N, which is where trees win.
  result: Put the chattiest parallelism (tensor) on NVLink and the bulk all-reduce (data) on the network, overlapped with compute.
traps:
  tricks:
  - 'Ring all-reduce sends ≈ 2S per GPU. :: Independent of N for large N.'
  - 'Place TP inside the node. :: Llama 3 405B: TP = 8, PP = 16, DP = 128 on 16,384 GPUs.'
  - 'Rail-optimized networks. :: GPU i of every node shares a leaf switch.'
  traps:
  - 'Ignoring latency at scale. :: Ring latency grows linearly with N; small messages need trees.'
  - 'TP across nodes. :: Per-layer all-reduces over the network stall every step.'
  - 'Expert parallel imbalance. :: All-to-all waits for the busiest GPU.'
papers:
- megatron21
- llama3
- nccl
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">GPU for GenAI · 05</div>
    <h1>Cluster topology:<br>wiring 16,000 GPUs together</h1>
    <p class="sub">Above about 8 GPUs (graphics processing units), the network is the computer. This deck covers scale-up vs scale-out, fat trees and rails, the collective operations, why ring all-reduce works, and how TP (tensor parallelism), PP (pipeline parallelism), DP (data parallelism) and EP (expert parallelism) are placed onto the network.</p>
    <div class="toc" data-auto></div>
    <p class="start-hint">Press <kbd>→</kbd> or <kbd>Space</kbd> to begin.</p>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-tiers" data-chapter="Two tiers">
  <div class="inner">
    <div class="label">01 · Two tiers</div>
    <h2>Scale-up inside a node, scale-out between nodes</h2>
    <hr>
    <p class="lede">Each node is a fast <b>NVLink island</b> (450 GB/s per GPU per direction). The islands are connected by a <b>network</b> (about 50 GB/s per GPU). Pick a parallelism type to see which links its traffic uses.</p>
    <div class="visual">
      <div class="seg" id="tierSeg"><button data-v="tp" class="on">Tensor parallel</button><button data-v="dp">Data parallel</button><button data-v="pp">Pipeline parallel</button></div>
      <svg id="tierSvg" viewBox="0 0 660 300" style="margin-top:12px" role="img" aria-label="Nodes and traffic"></svg>
      <p class="readout" id="tierOut"></p>
    </div>
    <div class="takeaway">The rule of thumb: the chattiest parallelism goes on the fastest links. TP is synchronous on every layer, so it stays in the node. PP sends activations point-to-point between stages. DP all-reduces gradients once per step and can overlap that with the backward pass.</div>
  
    <!--x:glance--><div class="glance"><h4>At a glance</h4><svg viewBox="0 0 660 152" role="img" aria-label="Scale-up inside the node (NVLink), scale-out between nodes (InfiniBand or RoCE)." class="glance-svg"><defs><marker id="gArr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--muted)"/></marker></defs><rect x="10.0" y="28" width="113.6" height="64" rx="10" style="fill:var(--e)"/><text x="66.8" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">GPU</text><text x="66.8" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">in an NVLink</text><text x="66.8" y="123.0" text-anchor="middle" class="tm" style="font-size:11px">domain</text><rect x="141.6" y="28" width="113.6" height="64" rx="10" style="fill:var(--a)"/><text x="198.4" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">node</text><text x="198.4" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">8 GPUs, NVSwitch</text><line x1="125.6" y1="60.0" x2="139.6" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/><rect x="273.2" y="28" width="113.6" height="64" rx="10" style="fill:var(--b)"/><text x="330.0" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">leaf switch</text><text x="330.0" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">rail-optimized</text><line x1="257.2" y1="60.0" x2="271.2" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/><rect x="404.8" y="28" width="113.6" height="64" rx="10" style="fill:var(--c)"/><text x="461.6" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">spine</text><text x="461.6" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">fat tree</text><line x1="388.8" y1="60.0" x2="402.8" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/><rect x="536.4" y="28" width="113.6" height="64" rx="10" style="fill:var(--faint)"/><text x="593.2" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">cluster</text><text x="593.2" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">16K GPUs</text><line x1="520.4" y1="60.0" x2="534.4" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/></svg><p class="caption" style="margin:4px 0 0">Scale-up inside the node (NVLink), scale-out between nodes (InfiniBand or RoCE (remote direct memory access over Converged Ethernet)).</p></div><!--/x:glance-->
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-fat" data-chapter="Network shape">
  <div class="inner">
    <div class="label">02 · Network shape</div>
    <h2>Leaf-spine (fat tree): every endpoint is a few hops from every other</h2>
    <hr>
    <p class="lede">NICs (network interface cards) connect to <b>leaf</b> switches, and every leaf connects to every <b>spine</b>. If uplink capacity equals downlink capacity, the network is <b>non-blocking</b>: any half of the cluster can talk to the other half at full rate. Click two endpoints, then reduce the uplinks.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">Uplinks per leaf <input type="range" id="ftU" min="1" max="4" step="1" value="4"> <output id="ftUo"></output></label>
      </div>
      <svg id="ftSvg" viewBox="0 0 660 300" style="margin-top:8px" role="img" aria-label="Leaf spine network"></svg>
      <div class="grid3">
        <div class="stat"><div class="num" id="ftHops"></div><div class="lbl">switch hops on selected path</div></div>
        <div class="stat"><div class="num" id="ftOver"></div><div class="lbl">oversubscription (down : up)</div></div>
        <div class="stat"><div class="num" id="ftBW"></div><div class="lbl">per-NIC bandwidth for cross-leaf traffic</div></div>
      </div>
    </div>
    <p class="caption">Real clusters add a third tier (leaf → spine → core) above roughly 2–4K GPUs. Meta's Llama 3 RoCE cluster used full bisection bandwidth inside each 3,072-GPU pod and 1:7 oversubscription between pods. Jobs were placed so that the heavy traffic stayed inside a pod.</p>
    <div class="cite">Llama 3 paper §3.3.1 (network topology).</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-rail" data-chapter="Network shape">
  <div class="inner">
    <div class="label">03 · Network shape</div>
    <h2>Rail-optimized: GPU <i>i</i> of every node shares one leaf switch</h2>
    <hr>
    <p class="lede">With a top-of-rack layout, all of a node's NICs go to the same leaf. In a <b>rail</b> layout, NIC <i>i</i> of every node goes to leaf <i>i</i>. Data-parallel peers (same local rank on different nodes) are then <b>one switch apart</b>.</p>
    <div class="visual">
      <div class="seg" id="railSeg"><button data-v="tor">Top-of-rack</button><button data-v="rail" class="on">Rail-optimized</button></div>
      <svg id="railSvg" viewBox="0 0 660 320" style="margin-top:12px" role="img" aria-label="Rail topology"></svg>
      <p class="readout" id="railOut"></p>
    </div>
    <div class="takeaway">NCCL (NVIDIA Collective Communications Library)'s <b>PXN</b> (PCIe (PCI (Peripheral Component Interconnect) Express, the standard expansion bus) × NVLink) uses this: to reach rail 3 on another node, GPU 0 first moves its data over NVLink to local GPU 3, which then sends it out on its own rail. The NVLink hop is nearly free, and the expensive spine hop is avoided.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-coll" data-chapter="Collectives">
  <div class="inner">
    <div class="label">04 · Collectives</div>
    <h2>The five collectives that distributed training is built from</h2>
    <hr>
    <div class="seg" id="collSeg">
      <button data-v="ar" class="on">All-reduce</button><button data-v="rs">Reduce-scatter</button><button data-v="ag">All-gather</button><button data-v="bc">Broadcast</button><button data-v="a2a">All-to-all</button>
    </div>
    <div class="visual"><svg id="collSvg" viewBox="0 0 660 250" role="img" aria-label="Collective before and after"></svg>
      <div class="infobox" id="collInfo" style="background:var(--panel-2);border-radius:10px;padding:12px 14px;margin-top:10px;font-size:14px;color:var(--muted)"></div>
    </div>
    <div class="takeaway">All-reduce = reduce-scatter + all-gather. FSDP (Fully Sharded Data Parallel) and ZeRO-3 (ZeRO = Zero Redundancy Optimizer) split this in two: they <b>all-gather</b> the weights before each layer and <b>reduce-scatter</b> the gradients after it, so each GPU only keeps its own shard.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-ring" data-chapter="Collectives">
  <div class="inner">
    <div class="label">05 · Collectives</div>
    <h2>Ring all-reduce, step by step</h2>
    <hr>
    <p class="lede">Split the buffer into N chunks. In each step, every GPU sends one chunk to its right-hand neighbour and adds the chunk it receives. After N−1 steps each GPU holds one fully reduced chunk (<b>reduce-scatter</b>). Another N−1 steps circulate those chunks (<b>all-gather</b>).</p>
    <div class="visual">
      <div class="controls" style="margin-top:0"><button class="btn primary" id="rgStep">Step →</button><button class="btn" id="rgPlay">Play</button><button class="btn" id="rgReset">Reset</button><span class="readout" id="rgPhase"></span></div>
      <svg id="ringSvg" viewBox="0 0 660 290" style="margin-top:10px" role="img" aria-label="Ring all-reduce"></svg>
    </div>
    <p class="caption">Each GPU sends 2·(N−1)/N × the buffer size in total, which is <b>nearly independent of N</b>. Every link is busy in every step. That's why ring all-reduce makes full use of bandwidth.</p>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-cost" data-chapter="Collectives">
  <div class="inner">
    <div class="label">06 · Collectives</div>
    <h2>Ring is limited by bandwidth; tree is limited by latency</h2>
    <hr>
    <p class="lede"><code>T_ring ≈ 2(N−1)·α + 2(N−1)/N · S/B</code>. The bandwidth term stays flat as N grows, but the latency term grows <em>linearly</em>. Trees grow only with log N. Change the message size to see which one wins.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">Message size <input type="range" id="cS" min="3" max="10" step="0.1" value="9"> <output id="cSo"></output></label>
        <label class="ctl">Per-hop latency α <input type="range" id="cA" min="1" max="20" step="1" value="5"> <output id="cAo"></output></label>
      </div>
      <svg id="costSvg" viewBox="0 0 660 300" style="margin-top:10px" role="img" aria-label="Collective cost vs N"></svg>
      <div class="legend"><span><i style="background:var(--a)"></i>ring</span><span><i style="background:var(--b)"></i>tree (pipelined, approx.)</span></div>
    </div>
    <div class="takeaway">For large gradient buckets (hundreds of MB), ring is near optimal. For small, latency-sensitive collectives such as MoE (Mixture of Experts) dispatch, decode-time TP all-reduce or many-node all-reduce, trees or in-network reduction (SHARP (Scalable Hierarchical Aggregation and Reduction Protocol, in-network reduction on NVIDIA switches)) win. NCCL picks the algorithm automatically based on size and topology.</div>
  </div>
</section>

<!-- slide id="s-example" from="example" chapter="Example" tag="Worked example" tagclass="b5" -->

<!-- slide raw -->
<section class="slide" id="s-plan" data-chapter="Mapping">
  <div class="inner">
    <div class="label">07 · Mapping</div>
    <h2>Parallelism planner: place TP × PP × DP on the cluster</h2>
    <hr>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <select id="plM"><option value="8">8B model</option><option value="70" selected>70B model</option><option value="405">405B model</option></select>
        <select id="plN"><option>64</option><option>256</option><option selected>1024</option><option>4096</option><option>16384</option></select>
        <span class="ctl">TP</span><div class="seg" id="plTP"><button data-v="1">1</button><button data-v="2">2</button><button data-v="4">4</button><button data-v="8" class="on">8</button><button data-v="16">16</button></div>
        <label class="ctl">PP <input type="range" id="plPP" min="0" max="5" step="1" value="2"> <output id="plPPo"></output></label>
      </div>
      <div class="grid2" style="margin-top:14px">
        <div>
          <div class="grid2">
            <div class="stat"><div class="num" id="plDP"></div><div class="lbl">DP replicas</div></div>
            <div class="stat"><div class="num" id="plMem"></div><div class="lbl">states per GPU (ZeRO-1)</div></div>
          </div>
          <div class="checks" id="plChecks" style="margin-top:12px"></div>
        </div>
        <svg id="plSvg" viewBox="0 0 360 220" role="img" aria-label="One model replica layout"></svg>
      </div>
    </div>
    <p class="caption">One replica is drawn on the right: each column is a pipeline stage, each dot is a TP rank, and its colour shows which 8-GPU node it sits on (a red dashed outline means the TP group spans nodes). Memory = (2 + 2) B/param of weights and grads, plus 12 B/param of optimizer state sharded over DP. Activations are not included. Pipeline bubble assumes 32 micro-batches.</p>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-llama" data-chapter="Mapping">
  <div class="inner">
    <div class="label">08 · Mapping</div>
    <h2>A real example: Llama 3 405B on 16K H100s</h2>
    <hr>
    <div class="visual scroll-x">
      <table class="tbl">
        <tr><th>GPUs</th><th>TP</th><th>CP</th><th>PP</th><th>DP</th><th>Seq len</th><th>BF16 MFU</th></tr>
        <tr><td>8,192</td><td>8</td><td>1</td><td>16</td><td>64</td><td>8,192</td><td>43%</td></tr>
        <tr><td>16,384</td><td>8</td><td>1</td><td>16</td><td>128</td><td>8,192</td><td>41%</td></tr>
        <tr><td>16,384</td><td>8</td><td>16</td><td>16</td><td>8</td><td>131,072</td><td>38%</td></tr>
      </table>
    </div>
    <div class="grid3" style="margin-top:16px">
      <div class="card e"><h3>TP = 8 → inside the node</h3><p>All-reduces on every layer stay on NVLink. TP is never larger than the NVLink domain.</p></div>
      <div class="card c"><h3>PP = 16 → across nodes</h3><p>Only activations are sent point-to-point between stages. Meta modified the schedule to reduce bubbles and balance memory.</p></div>
      <div class="card b"><h3>DP / FSDP outermost</h3><p>Gradient reduce-scatter overlaps with the backward pass. It is the most tolerant of the slower, oversubscribed links.</p></div>
    </div>
    <div class="takeaway">The order (inner to outer) is TP → CP (context parallelism) → PP → DP. The rank layout follows bandwidth needs: the innermost dimension gets the fastest links. CP (context parallel) was added to train on 128K-token sequences.</div>
    <div class="cite">Llama Team, "The Llama 3 Herd of Models" (2024), Table 4 and §3.3.2.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-moe" data-chapter="Mapping">
  <div class="inner">
    <div class="label">09 · Mapping</div>
    <h2>Expert parallelism means all-to-all, and the busiest GPU sets the pace</h2>
    <hr>
    <p class="lede">In MoE layers each token goes to the GPUs that host its top-k experts (dispatch) and comes back (combine). If the router sends a skewed share of tokens to one expert, that GPU receives more data and every other GPU waits for it.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">Router skew <input type="range" id="eS" min="0" max="100" step="1" value="30"> <output id="eSo"></output></label>
        <div class="seg" id="eNet"><button data-v="450" class="on">EP within NVLink</button><button data-v="50">EP across nodes</button></div>
      </div>
      <div class="grid2" style="margin-top:12px;align-items:center">
        <svg id="eSvg" viewBox="0 0 300 300" style="max-width:340px" role="img" aria-label="All-to-all traffic matrix"></svg>
        <div>
          <div class="grid2">
            <div class="stat"><div class="num" id="eImb"></div><div class="lbl">busiest GPU vs average</div></div>
            <div class="stat"><div class="num" id="eT"></div><div class="lbl">dispatch time (busiest GPU)</div></div>
          </div>
          <p class="caption">Rows: source GPU. Columns: GPU hosting the expert. Each GPU sends 8K tokens × top-2 × 7168 hidden × 2 B ≈ 235 MB per MoE layer.</p>
        </div>
      </div>
    </div>
    <div class="takeaway">MoE systems fight this with load-balancing losses (or the auxiliary-loss-free bias used in DeepSeek-V3), capacity limits, node-limited routing (each token goes to at most M nodes), and by putting EP inside the largest available NVLink domain.</div>
  </div>
</section>

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="Tricks and traps" tagclass="b7" -->

<!-- slide raw -->
<section class="slide" id="s-qa" data-chapter="Test yourself">
  <div class="inner">
    <div class="label">10 · Test yourself</div>
    <h2>Questions to test your understanding</h2>
    <hr>
    <details class="qa"><summary>You have 1,024 H100s and a 70B model. How do you lay out the parallelism?</summary><div class="ans">Start with <b>TP=8 inside each node</b> on NVLink, which is enough to shard the layers and keep the GEMMs (general matrix multiplications) efficient. Add PP of 2–4 across nodes only if memory or activations require it, and run enough micro-batches to keep the bubble small. Put the rest into <b>DP with FSDP or ZeRO-1</b>: 1024 / (8 × 2) = 64 replicas. Check memory per GPU, the global batch size (DP × micro-batch × grad accumulation must stay within a good batch size), and that DP communication overlaps with backward. Then say what you would measure: MFU (model floating-point-operation utilization, the share of peak compute spent on the model's math), exposed communication time, and bubble fraction.</div></details>
    <details class="qa"><summary>Why is ring all-reduce bandwidth-optimal, and when is it a bad choice?</summary><div class="ans">Every GPU sends and receives 2(N−1)/N × S, which is the lower bound for all-reduce, and all links are used in every step. But it takes 2(N−1) sequential steps, so the latency term grows linearly. At thousands of GPUs, or for small messages, that dominates. Hierarchical schemes (reduce inside the node, then a ring or tree across nodes), double binary trees, and in-network reduction (SHARP) handle that case.</div></details>
    <details class="qa"><summary>What does "rail-optimized" mean, and why do labs build networks that way?</summary><div class="ans">NIC i of every node connects to leaf (rail) i, so same-rank GPUs across nodes, which are exactly the DP and PP peers, are one switch hop apart. Most training traffic stays inside a rail and never touches the spine. Fewer spine ports are needed and tail latency is lower. Cross-rail traffic is routed over NVLink first (NCCL PXN).</div></details>
    <details class="qa"><summary>InfiniBand vs RoCE: what's the trade-off?</summary><div class="ans"><b>InfiniBand</b> has lossless credit-based flow control, adaptive routing, SHARP in-network reduction and mature NCCL support, and it is a single-vendor ecosystem. <b>RoCE v2</b> runs RDMA (remote direct memory access) over Ethernet, which is cheaper and more widely available, but it needs PFC (priority flow control)/ECN (explicit congestion notification) tuning and congestion control, and ECMP (equal-cost multi-path routing) hash collisions on large flows hurt it. Meta trained Llama 3 on RoCE and other labs use IB (InfiniBand), so both work at scale. The newer Ultra Ethernet specification aims to close the gap.</div></details>
    <details class="qa"><summary>What is an MoE all-to-all bottleneck, and how do you reduce it?</summary><div class="ans">Dispatch and combine move every token's hidden state to its experts' GPUs and back, which is bandwidth-heavy and latency-sensitive, and router skew creates hot GPUs. Mitigations: keep EP within the NVLink domain (8, or 72 on NVL72), limit how many nodes each token can be sent to, add load-balancing terms to the router, overlap communication with computation (for example micro-batch interleaving and DeepEP-style kernels), and compress the dispatch data to FP8 (8-bit floating point).</div></details>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-end" data-chapter="Test yourself">
  <div class="inner">
    <div class="label">11 · Take it with you</div>
    <h2>Four things to remember</h2>
    <hr>
    <div class="recap">
      <div><span><b>There are two tiers:</b> the NVLink island (fast and small) and the network (about 9× slower, very large). Map TP → node, PP and DP → network.</span></div>
      <div><span><b>Fat tree plus rails:</b> non-blocking inside a pod, oversubscribed above it. Same-rank GPUs share a leaf.</span></div>
      <div><span><b>All-reduce = reduce-scatter + all-gather.</b> Ring is bandwidth-optimal at 2(N−1)/N · S, but its latency grows with N.</span></div>
      <div><span><b>MoE all-to-all is limited by the busiest GPU.</b> Keep EP in the NVLink domain and balance the router.</span></div>
    </div>
    <p class="start-hint">Next: <a href="../06-gpu-failures/index.html">06 · GPU failures →</a> · Previous: <a href="../04-inside-gpu-server/index.html">← 04</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
