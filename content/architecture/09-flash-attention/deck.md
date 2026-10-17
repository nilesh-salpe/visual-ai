---
title: FlashAttention Internals
body:
  data-deck: FlashAttention internals
  data-home: ../index.html
  data-home-label: Architecture
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'Q block :: loaded once into SRAM :: c'
  - 'stream K, V blocks :: through SRAM :: b'
  - 'online softmax :: running max m, sum ℓ

    rescale partial output :: a'
  - 'write O once :: plus log-sum-exp for backward :: e'
  loop: '2 -> 1 :: for every K/V block'
  caption: The N×N score matrix exists only one tile at a time, on chip.
example:
  title: 'Worked example: what standard attention would store'
  setup: Sequence length N = 8,192, head dimension 128, BF16, one head.
  steps:
  - 'Score matrix S: N² = 67,108,864 elements = <b>128 MiB</b> per head; P is the same again.'
  - 'Q, K, V and O together: 4 × N × d = 4,194,304 elements = <b>8 MiB</b>.'
  - With 32 heads and batch 8, S alone would be <b>32 GiB</b>, written and read back.
  - 'FlashAttention keeps only per-row statistics (m, ℓ or the log-sum-exp): O(N) extra memory.'
  result: 'Same FLOPs (slightly more with recomputation), far fewer bytes moved, and memory linear in N: that is where the speedup comes from.'
traps:
  tricks:
  - 'Online softmax. :: m_new = max(m, block max); ℓ ← ℓ·e^(m−m_new) + Σe^(x−m_new).'
  - 'FA2 loop order. :: Outer loop over query blocks (parallel), inner over K/V blocks.'
  - 'Backward recomputes. :: Store the log-sum-exp per row, recompute S and P on chip.'
  traps:
  - 'Calling it approximate. :: Outputs match standard attention up to floating-point rounding.'
  - 'Calling it O(N). :: Compute is still O(N²); extra memory is O(N).'
  - 'Expecting fewer FLOPs. :: Recomputation adds FLOPs; the gain is memory traffic.'
papers:
- fa1
- fa2
- fa3
- milakov
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">The Modern LLM · 09</div>
    <h1>FlashAttention internals</h1>
    <p class="sub">How computing exact attention in tiles, with an online softmax, avoids writing the N×N matrix to GPU (graphics processing unit) memory. Plus what FlashAttention-2 and -3 changed.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Standard attention writes the N×N score matrix to HBM (high-bandwidth memory), reads it back for the softmax, writes probabilities and reads them again. At long N this memory traffic, not arithmetic, dominates the runtime.</div>
      <div class="c"><b>Core idea</b>Load blocks of Q, K and V into on-chip SRAM (static random-access memory, fast on-chip memory), compute scores, softmax and output for that tile there, and combine tiles with an <b>online softmax</b> (running max and sum, rescaling). The N×N matrix never touches HBM. The result is exact.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Attention is memory-bound

On an A100 (figures from the FlashAttention paper): HBM holds 40–80 GB at 1.5–2.0 TB/s. On-chip SRAM is 192 KB per streaming multiprocessor across 108 SMs, at around 19 TB/s. SRAM is roughly 10× faster and many orders of magnitude smaller. Standard attention runs as several separate passes, each reading from and writing to HBM. See <a href="../../gpu/03-memory-hierarchy/index.html">GPU deck 03</a> for the hierarchy.
{: .lede}

<div class="visual">
  <svg id="pSvg" viewBox="0 0 660 190" role="img" aria-label="Standard attention passes over HBM"></svg>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why earlier speed-ups didn't help

::: cards grid3
### [d] Approximate attention cuts FLOPs
Sparse and low-rank methods reduce computation but trade quality, and the FlashAttention abstract notes they "often do not achieve wall-clock speedup".

### [b] FLOPs aren't the bottleneck
Softmax, masking and dropout are element-wise over N² entries, so they do little arithmetic per byte moved. Their runtime is set by HBM bandwidth.

### [c] Memory grows as N²
Storing S and P for the backward pass needs N² values per head. At N = 65,536 in BF16 (bfloat16, a 16-bit floating-point format with the exponent range of 32-bit floats) that is 8 GiB per head, per layer.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What does FlashAttention save?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? FlashAttention actually does slightly <i>more</i> FLOPs (floating-point operations) than standard attention (it recomputes in the backward pass), yet it is several times faster. What does it reduce?
- [ ] The number of attention heads
- [x] Reads and writes to HBM
- [ ] The precision of the softmax
- [ ] The sequence length
> <b>B.</b> It is IO-aware (IO = input/output, memory reads and writes): tiling keeps S and P in SRAM, so HBM traffic drops. GPT-2 medium (N = 1,024), forward + backward on an A100: standard 66.6 GFLOPs (billion floating-point operations), <b>40.3 GB</b> HBM, 41.7 ms; FlashAttention 75.2 GFLOPs, <b>4.4 GB</b>, <b>7.3 ms</b>.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Three ingredients

<div class="grid3">
  <div class="card a"><h3>Tiling</h3><p>Split Q into row blocks and K, V into column blocks sized to fit in SRAM. For each pair of blocks compute S = QKᵀ/√d, then the partial softmax and partial output, without leaving the chip.</p></div>
  <div class="card b"><h3>Online softmax</h3><p>Softmax needs a row max and sum over <b>all</b> columns. Keep a running max m and sum ℓ per row; when a new block raises the max, rescale the old sum and the old partial output by e<sup>m_old − m_new</sup>. The result is exact.</p></div>
  <div class="card e"><h3>Recompute in the backward pass</h3><p>Don't store P. Save only the per-row softmax statistics (FA2 (FlashAttention-2): just the log-sum-exp) and recompute S and P block by block in the backward pass. Extra FLOPs, far less memory traffic, and memory linear in N.</p></div>
</div>

<div class="deep"><h4>IO complexity (FA1, Theorem 2)</h4><p>With head dimension d and SRAM size M: standard attention needs <b>Θ(Nd + N²)</b> HBM accesses, while FlashAttention needs <b>Θ(N²d²/M)</b>. For typical d (64–128) and M (~100 KB), d² is many times smaller than M. The paper also proves no exact attention algorithm can asymptotically do better for all M.</p></div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Online softmax, step by step

<p class="lede">One row of 12 scores, processed in chunks of 4 as if they arrived from three K blocks. Watch the running max m and running sum ℓ. When the max increases, the old sum is multiplied by e<sup>m_old − m_new</sup>.</p>

<div class="visual">
  <div class="controls" style="margin-top:0"><button class="btn primary" id="osNext">next chunk</button><button class="btn" id="osReset">reset</button></div>
  <svg id="osSvg" viewBox="0 0 660 190" style="margin-top:10px" role="img" aria-label="Online softmax"></svg>
  <p class="readout" id="osOut"></p>
</div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Tiling: which blocks are touched

FlashAttention-2 order: for each Q block (outer loop, run in parallel across thread blocks), stream every K/V block through SRAM (inner loop). Step through and compare the elements moved to and from HBM with standard attention. Turn on causal: blocks entirely above the diagonal are skipped.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><button class="btn primary" id="tlNext">next tile</button><button class="btn" id="tlRun">run all</button><div class="seg" id="tlC"><button data-v="0" class="on">full</button><button data-v="1">causal</button></div></div>
  <svg id="tlSvg" viewBox="0 0 660 240" style="margin-top:10px" role="img" aria-label="Tiled attention"></svg>
  <p class="readout" id="tlOut"></p>
</div>

<p class="caption">N = 8 blocks of 128 rows, d = 64. Forward pass, element counts: standard ≈ 4Nd + 4N², tiled ≈ 2Nd + (N/B_r)·2Nd (the same traffic model as notebook 08).</p>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Measured results, and FA1 → FA2 → FA3

<div class="visual"><div id="fBars"></div><p class="caption">FA1 (FlashAttention-1) Fig. 2: GPT-2 medium attention (N = 1,024, d = 64, 16 heads, batch 64), forward + backward, A100.</p></div>

<div class="visual scroll-x" style="margin-top:12px"><table class="tbl">
  <tr><th></th><th>Key change</th><th>Reported result</th></tr>
  <tr><td>FlashAttention (2022)</td><td>Tiling + online softmax + recompute; IO-aware, exact</td><td>15% faster BERT-large (BERT = Bidirectional Encoder Representations from Transformers) training vs MLPerf 1.1 record; 3× GPT-2 (1K); 2.4× Long Range Arena</td></tr>
  <tr><td>FlashAttention-2 (2023)</td><td>Fewer non-matmul FLOPs; parallelize over sequence (outer loop over Q blocks); split work across warps; rescale the output once at the end</td><td>~2× FA1; 50–73% of peak FLOPs on A100 (FA1: 25–40%); up to 225 TFLOPs (trillion floating-point operations)/s training GPT models</td></tr>
  <tr><td>FlashAttention-3 (2024)</td><td>Hopper features: asynchronous Tensor Cores and TMA (Tensor Memory Accelerator), warp specialization, interleaved matmul + softmax, FP8 (8-bit floating point) with block quantization</td><td>1.5–2.0× on H100; up to 740 TFLOPs/s FP16 (~75%); ~1.2 PFLOPs (quadrillion floating-point operations)/s FP8 with 2.6× lower error than a baseline FP8 attention</td></tr>
</table></div>

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "FlashAttention is an approximation of attention."
> It is <b>exact</b>: the same outputs up to floating-point rounding (notebook 08: max error ~1e-15). Only the order of operations changes.
:::

::: reveal myth
? "FlashAttention makes attention O(N)."
> Compute is still O(N²). What becomes O(N) is the <b>extra memory</b>: no N×N matrix is stored. HBM traffic drops by a large factor but is still quadratic in N.
:::

::: reveal myth
? "It is faster because it does fewer FLOPs."
> It does <b>more</b> FLOPs (75.2 vs 66.6 GFLOPs in Fig. 2) because of recomputation. It is faster because it moves about 9× fewer bytes.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

<div class="quiz">
  <p class="qq">In the online softmax, when a new block has a larger maximum, what happens to the running sum ℓ?</p>
  <div class="opts">
  <button>A. It is reset to 0</button>
  <button data-ok>B. It is multiplied by e^(m_old − m_new)</button>
  <button>C. It is divided by the block size</button>
  <button>D. Nothing</button>
  </div>
  <div class="why"><b>Rescaled by e^(m_old − m_new)</b>, and so is the partial output.</div>
</div>

<div class="quiz ">
  <p class="qq">What does FlashAttention store for the backward pass instead of P?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Only per-row softmax statistics (in FA2, just the log-sum-exp L = m + log ℓ). S and P are recomputed block by block in SRAM during the backward pass.</div>
</div>

<div class="quiz ">
  <p class="qq">Name two changes in FlashAttention-2 compared with FA1.</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Parallelize over the sequence (outer loop over Q blocks, not K/V); fewer non-matmul FLOPs (rescale the output once at the end); better work split across warps; store only the log-sum-exp.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">FlashAttention computes exact attention tile by tile in SRAM with an online softmax, so the N×N matrix never touches HBM: more FLOPs, far fewer bytes, much faster.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Standard attention writes the N by N score matrix to GPU high-bandwidth memory, reads it back for the softmax, writes the probabilities and reads them again, and at long sequences that traffic, not arithmetic, sets the runtime. FlashAttention loads blocks of Q, K and V into on-chip SRAM and computes scores, softmax and output there. It combines blocks with an online softmax that keeps a running max and sum per row and rescales when the max grows. The backward pass recomputes scores from saved statistics instead of storing them. It is exact, uses memory linear in N, and on GPT-2 cut HBM traffic from 40 to 4.4 GB. FlashAttention-2 reordered the loops for parallelism; FlashAttention-3 uses Hopper's asynchrony and FP8.</p></div>

<div class="recap"><div><span><b>Problem:</b> N×N intermediates make attention memory-bound and O(N²) in memory.</span></div><div><span><b>Core idea:</b> tiling + online softmax + recompute: exact, linear memory, ~9× less HBM traffic.</span></div><div><span><b>Versions:</b> FA2: loop order and parallelism (50–73% of peak); FA3: Hopper async + FP8 (740 TFLOPs/s).</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/architecture/08_flash_attention.ipynb" target="_blank" rel="noopener">08 · FlashAttention from scratch: online softmax and tiling</a> <span style="color:var(--faint)">· 50 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/architecture/08_flash_attention.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../10-mixture-of-experts/index.html">10 · Mixture of Experts →</a> · Previous: <a href="../08-sliding-window/index.html">← 08</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Dao et al. 2022, "FlashAttention" (Algorithm 1, Theorem 2, Fig. 2, §2.1 A100 figures); Dao 2023, "FlashAttention-2"; Shah et al. 2024, "FlashAttention-3"; Milakov & Gimelshein 2018, "Online normalizer calculation for softmax".</p>

<!-- slide id="s-papers" from="papers" -->
