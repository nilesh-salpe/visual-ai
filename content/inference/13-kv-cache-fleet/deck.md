---
title: KV Cache Across the Fleet
body:
  data-deck: The KV cache across the fleet
  data-home: ../index.html
  data-home-label: Inference
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
- ../../shared/diagram.js
papers:
- vllm_offload
- vllm_disagg
- nixl
- mooncake
- lmcache
- cachedattn
- cp_infer
- ds_infer
- vllm_llmd
- vllm_apc
status:
  label: current
  reviewed: '2026-10-16'
  note: Checked against vLLM v0.31.0 KV offloading and connector docs, Mooncake, LMCache, CachedAttention and DeepSeek (2026-10-16).
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Short answer">
  <div class="inner">
    <div class="kicker">LLM Inference &amp; Serving · 13</div>
    <h1>The KV cache across the fleet</h1>
    <p class="sub">Treating the KV cache as data with a memory hierarchy: spilling to CPU memory, SSD and shared stores, loading instead of recomputing, routing requests to where their prefix lives, moving KV between prefill and decode workers, and splitting very long prompts across GPUs.</p>
    <div class="ps">
      <div class="p"><b>The question</b>Prompts and conversations repeat across requests and replicas. How do you stop recomputing their KV cache at fleet scale?</div>
      <div class="c"><b>Short answer</b>Treat the KV cache as <b>data in a memory hierarchy</b>. Keep hot blocks in GPU memory, copy finished blocks to <b>CPU memory</b>, then <b>SSD or a shared store</b>, and <b>load them back on a hit</b>: for long prefixes, loading is much faster than recomputing. <b>Route</b> each request to where its prefix lives, move KV between prefill and decode workers over <b>RDMA</b> (NIXL, Mooncake), and split very long prompts across GPUs with <b>context parallelism</b>. DeepSeek served 56.3% of its input tokens from an on-disk KV cache.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-draw" chapter="Draw it" tag="1 · Draw it" tagclass="b5" -->
## The picture to draw

::: diagram 660x300
nodes:
  rq: {at: [10, 120, 100, 50], text: Request, sub: prompt prefix, color: f, step: 1}
  rt: {at: [140, 120, 110, 50], text: Router, sub: 'where is my prefix?', color: b, step: 2}
  ix: {at: [140, 230, 110, 56], text: Prefix index, sub: from KV events, color: b, step: 2}
  g: {at: [290, 15, 170, 50], text: GPU memory, sub: 'hot blocks · 3,350 GB/s', color: a, step: 3}
  c: {at: [290, 90, 170, 50], text: CPU memory, sub: PCIe Gen5 · 64 GB/s, color: c, step: 3}
  ss: {at: [290, 165, 170, 50], text: Local NVMe SSD, sub: about 7 GB/s, color: c, step: 4}
  sh: {at: [290, 240, 170, 50], text: Shared store, sub: over the network · 50 GB/s, color: e, step: 4}
  pf: {at: [495, 15, 155, 50], text: Prefill worker, sub: computes new KV, color: a, step: 5}
  dc: {at: [495, 105, 155, 50], text: Decode worker, sub: receives KV, color: a, step: 5}
  cp: {at: [495, 200, 155, 60], text: Long prompt, sub: context parallel, color: d, step: 6}
edges:
  - {from: rq, to: rt, step: 2}
  - {from: ix, to: rt, label: locations, step: 2, style: dash}
  - {from: rt, to: c, label: look up, step: 3}
  - {from: g, to: c, label: evict / load, step: 3}
  - {from: c, to: ss, step: 4}
  - {from: ss, to: sh, step: 4}
  - {from: pf, to: dc, label: KV over RDMA (NIXL), step: 5}
steps:
  - A request arrives; what matters is the prefix it shares with earlier requests.
  - 'The router asks a prefix index (built from the engines'' KV-cache events) which replica or tier already holds that prefix, and sends the request there.'
  - 'KV blocks live in a hierarchy. Finished blocks are copied from GPU memory to pinned CPU memory and loaded back on a hit, instead of being recomputed.'
  - 'Colder blocks spill further: local NVMe and shared storage hold far more, but are slower; loads from them pass through CPU memory.'
  - 'With prefill/decode disaggregation, the prefill worker''s new KV moves to a decode worker over RDMA (NIXL, Mooncake).'
  - A prompt too long for one GPU's prefill is split across GPUs with context parallelism; each holds part of the KV.
:::

<!-- slide id="s-how" chapter="How it works" tag="2 · How it works" tagclass="b4" -->
## A tiered cache at work <span class="ill">animation</span>

<div class="visual"><div class="controls"><div class="seg" id="kvSeg"><button data-v="on" class="on">Offloading on</button><button data-v="off">GPU only</button></div><button class="btn" id="kvNext">next request</button></div><svg id="kvSvg" class="anim-lg" viewBox="0 0 660 300" role="img" aria-label="Prefix blocks moving between GPU, CPU and SSD tiers as requests arrive"></svg><p class="readout" id="kvOut"></p></div>

Each letter is one conversation's prefix. Least recently used blocks move down a tier when the tier above is full; a hit promotes the block back to the GPU. In vLLM v0.31.0 this is the OffloadingConnector: a CPU tier, plus optional filesystem, object-store or peer (NIXL) tiers that always stage through CPU memory.

<!-- slide id="s-numbers" chapter="Numbers" tag="3 · Numbers to know" tagclass="b6" -->
## Numbers to know <span class="ill">calculator</span>

<div class="visual"><div class="controls"><label class="ctl">prefix length (K tokens) <input type="range" id="lL" min="1" max="128" step="1" value="32"> <output id="lLo"></output></label><label class="ctl">GPUs per replica (log₂) <input type="range" id="lG" min="0" max="3" step="1" value="3"> <output id="lGo"></output></label><label class="ctl">where the KV is <input type="range" id="lT" min="0" max="2" step="1" value="0"> <output id="lTo"></output></label><label class="ctl">prefill MFU <input type="range" id="lM" min="20" max="70" step="5" value="50"> <output id="lMo"></output></label></div><div class="bars"><div id="lBars"></div></div><p class="readout" id="lOut"></p></div>

Recompute ≈ 2 × 70B × tokens FLOPs on H100s at 989 TFLOP/s BF16 times the MFU (attention cost ignored, so long prefixes cost even more). Loading divides the KV across the replica's GPUs for CPU and network tiers; a node's SSD is shared. Bandwidths are the H100-system figures from the GPU decks.

::: cards grid2
### [a] KV per token
Llama-3-70B shape (80 layers, 8 KV heads × 128, BF16): 320 KiB. A 32K-token conversation: about 10.7 GB.

### [c] Production hit rates
DeepSeek: 56.3% of 608B input tokens in one day hit its on-disk KV cache. Mooncake (Kimi): 75% more requests handled on real workloads.

### [b] Multi-turn reuse
CachedAttention: up to 87% lower time to first token and 70% lower cost by keeping conversations' KV in host memory and disk. LMCache with vLLM: up to 15× throughput.

### [e] Million-token prefill
Context parallelism: 1M tokens of Llama 3 405B prefilled in 77 s on 128 H100s (16 nodes), 93% parallel efficiency; 128K in 3.8 s.
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="4 · Trade-offs" tagclass="b2" -->
## Trade-offs

::: table
| Choice | Gains | Costs |
|---|---|---|
| GPU-only prefix cache | fastest hits; no extra system | only the GPU memory left after weights; evicted prefixes are recomputed |
| CPU offload | adds host memory as cache capacity; copies overlap with compute | uses host memory and PCIe bandwidth; another layer to run |
| SSD or shared store | huge capacity; survives restarts; shared across replicas | slower loads (staged through CPU); can lose to recompute on short prefixes |
| Prefix-aware routing | hits without moving data | load imbalance (hot prefixes); needs a prefix index or hashing |
| Prefill/decode disaggregation with KV transfer | prefill and decode tuned separately; steadier inter-token latency | KV transfer over RDMA every request; vLLM docs: does not improve throughput by itself |
| Context parallelism for long prompts | near-linear prefill speed-up on long prompts | K/V exchange between GPUs; only worth it for very long prompts |
:::

<!-- slide id="s-follow" chapter="Follow-ups" tag="5 · Follow-ups" tagclass="b3" -->
## Follow-ups

::: reveal
? <span class="lvl lvl-basic">Basic</span> Why is loading cached KV faster than recomputing it?
> Recomputing a prefix costs about 2 × parameters FLOPs per token; loading costs only its KV bytes. For a 70B model, 32K tokens is 10.7 GB of KV: tens of milliseconds over PCIe split across 8 GPUs, versus about a second of 8-GPU compute.
:::

::: reveal
? <span class="lvl lvl-basic">Basic</span> What goes wrong with round-robin load balancing here?
> A conversation's turns land on different replicas, each without the previous turn's cache, so every turn recomputes its history. Route by prefix or session instead (vLLM Router deck).
:::

::: reveal
? <span class="lvl lvl-deeper">Deeper</span> When is SSD offload not worth it?
> When loading takes longer than recomputing: short prefixes, a single drive shared by a whole node (about 7 GB/s), or wide tensor parallelism that makes recompute fast. Measure both; vLLM lets a request cap loads with max_load_tokens.
:::

::: reveal
? <span class="lvl lvl-deeper">Deeper</span> How does KV move from a prefill worker to a decode worker?
> Through a KV connector: vLLM's NixlConnector uses NIXL (UCX over RDMA, or GPUDirect Storage) for asynchronous GPU-to-GPU transfer; Mooncake and LMCache are alternatives. The decode worker reads the blocks from the prefill worker by RDMA (a pull) while the prefill worker holds them under a lease; for multi-turn chat, vLLM can also pull earlier turns' KV back from decode to prefill.
:::

::: reveal
? <span class="lvl lvl-expert">Expert</span> How does a router know where each prefix lives?
> Engines publish KV-cache events (blocks stored and removed); llm-d builds a global index from them for precise prefix-aware routing. The vLLM Router instead keeps an approximate radix tree of prompts it sent to each worker. A stale index only costs a miss and a recompute.
:::

::: reveal
? <span class="lvl lvl-expert">Expert</span> A user sends a 1M-token prompt. What changes?
> One GPU cannot prefill it in time, so split the sequence across GPUs with context parallelism (ring attention passing K/V or Q). Meta prefilled 1M tokens of Llama 3 405B in 77 s on 128 H100s; the resulting KV is spread across those GPUs for decoding.
:::

<!-- slide id="s-wrong" chapter="Wrong answers" tag="6 · Wrong answers to avoid" tagclass="b1" -->
## Wrong answers to avoid

::: reveal myth
? "Prefill/decode disaggregation increases throughput."
> vLLM's docs state it does not improve throughput; it lets you tune time to first token and inter-token latency separately and controls tail latency.
:::

::: reveal myth
? "Keep the whole cache in GPU memory; it is the fastest."
> GPU memory is the scarcest resource. LMCache reports users' stored KV growing far beyond GPU capacity; offloading turns misses into cheap loads.
:::

::: reveal myth
? "Any cache tier beats recomputing."
> A slow tier can be slower than recomputation for short prefixes or highly parallel replicas; check with the bandwidth arithmetic.
:::

::: reveal myth
? "Prefix caching only helps identical requests."
> Blocks are matched by prefix, so any shared start (system prompt, documents, earlier turns) is reused even when the rest differs.
:::

<!-- slide id="s-system" chapter="In a system" tag="7 · In a system" tagclass="b9" -->
## In a real system

::: cards grid2
### [a] DeepSeek
On-disk KV cache across the service: 342B of 608B input tokens in a day were cache hits, priced lower for users ($0.14 vs $0.55 per million tokens for R1).

### [c] Kimi (Mooncake)
Separate prefill and decode clusters around a disaggregated KV cache pool built from CPU memory, DRAM and SSD across the cluster.

### [b] vLLM v0.31.0
OffloadingConnector tiers (CPU, filesystem, object store, peer over NIXL); NixlConnector, MooncakeConnector, LMCacheConnectorV1 for transfer and sharing.

### [e] Kubernetes fleets
llm-d: prefix-aware routing from KV events and tiered offloading (13.9× throughput vs GPU-only at high concurrency on H100).
:::

See also: <a href="../05-paged-attention/index.html">PagedAttention and prefix caching</a> (one server) and the <a href="../../vllm/10-router/index.html">vLLM Router</a>.

<!-- slide id="s-practice" chapter="Practice" tag="8 · Practice" tagclass="b8" -->
## Practice

1. **Explain in 60 seconds** why offloading KV to CPU memory raises throughput for multi-turn chat.
            2. **Draw** the four tiers with their bandwidths, and where a router and a prefix index sit.
            3. **Compute** the KV size of a 16K-token prefix for a 70B model with 320 KiB per token: 16,384 × 327,680 B ≈ **5.4 GB**.

::: quiz
? A 32K-token prefix of a 70B model is cached in CPU memory; the replica has 8 GPUs, each loading its share over PCIe Gen5 (64 GB/s). Roughly how long does the load take?
- [ ] About 2 ms
- [x] About 20 ms
- [ ] About 2 s
- [ ] About 20 s
> **B.** 10.7 GB ÷ 8 GPUs ≈ 1.34 GB each; 1.34 GB ÷ 64 GB/s ≈ 21 ms, versus about a second to recompute.
:::

::: quiz
? Which tier can a GPU read KV from directly in vLLM's OffloadingConnector?
- [ ] Any tier
- [x] Only the CPU primary tier; secondary tiers stage through it
- [ ] Only SSD
- [ ] None: KV is always recomputed
> **B.** Secondary tiers (filesystem, object store, peers) cannot read or write GPU memory directly; transfers go through pinned CPU memory.
:::

<p class="start-hint">Next: <a href="../10-putting-it-together/index.html">10 · Putting it together →</a> · Previous: <a href="../12-moe-serving/index.html">← 12 · Serving large MoE models</a> · <a href="../index.html">All decks</a></p>

<!-- slide id="s-papers" from="papers" -->
