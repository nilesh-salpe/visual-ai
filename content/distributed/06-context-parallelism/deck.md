---
title: Context Parallelism
body:
  data-deck: Context parallelism
  data-home: ../index.html
  data-home-label: Distributed
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'long sequence :: S tokens :: f'
  - 'split into N chunks :: one per GPU :: c'
  - 'local queries :: stay put :: a'
  - 'K/V blocks move :: ring / all-gather / all-to-all :: b'
  - 'online softmax :: exact attention :: e'
  caption: Activation memory per GPU ∝ S/N, so context can grow with GPU count.
example:
  title: 'Worked example: Llama 3 405B at 128K context'
  setup: Sequence 131,072 tokens, CP = 16 (Llama 3's long-context setting), 8 KV heads of dimension 128, BF16.
  steps:
  - 'Tokens per GPU: 131,072 / 16 = <b>8,192</b>.'
  - 'K/V width per token: 2 × 8 × 128 = 2,048 values.'
  - 'K/V each GPU must receive per layer: 15/16 × 131,072 × 2,048 × 2 bytes = <b>480 MiB</b>.'
  - 'Ring: in 15 steps overlapped with computing on the current block. All-gather (Llama 3): at once, simpler with document masks, but the latency is exposed.'
  result: The traffic is the same for ring and all-gather; they differ in overlap and in how easily they handle complex masks.
traps:
  tricks:
  - 'Memory ∝ S / N. :: Context grows with the number of GPUs.'
  - 'Same bytes, different timing. :: Ring overlaps K/V passing with compute; all-gather is one exposed step.'
  - 'Balance causal work. :: Give each GPU one early and one late chunk.'
  traps:
  - 'Contiguous chunks with a causal mask. :: The GPU holding the last chunk does N× the work of the first.'
  - 'Forgetting GQA. :: Fewer KV heads make CP traffic much smaller.'
  - 'Using CP at short context. :: The overhead only pays off when sequences are long.'
papers:
- ringattn
- ulysses
- llama3
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Distributed Training · 06</div>
    <h1>Context parallelism</h1>
    <p class="sub">Training on very long sequences by splitting each sequence across GPUs: ring attention, the all-gather variant Llama 3 uses, and the all-to-all approach of DeepSpeed-Ulysses.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>At 128K tokens, one sequence's activations exceed a GPU's memory, and attention needs every token to see every earlier token.</div>
      <div class="c"><b>Core idea</b>Split the sequence into N chunks, one per GPU. Each GPU keeps its queries; keys and values move: around a <b>ring</b> overlapped with compute (Ring Attention), all at once (<b>all-gather</b>, Llama 3), or by re-sharding heads with <b>all-to-all</b> (Ulysses). With an online softmax the result is exact.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Attention needs the whole past

A causal sequence split across 4 GPUs. Each square is one (query chunk, key chunk) block of the attention matrix; grey blocks are masked out (future). Press "next step" to pass K/V blocks around the ring.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><button class="btn primary" id="cNext">next step</button><button class="btn" id="cReset">reset</button></div>
  <svg id="cSvg" viewBox="0 0 660 250" style="margin-top:10px" role="img" aria-label="Ring attention blocks"></svg>
  <p class="readout" id="cOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why other axes don't help here

::: cards grid3
### [d] TP shards heads, not tokens
Every GPU still holds activations for the whole sequence (sequence parallelism helps only outside attention).

### [b] PP and DP don't split a sequence
One sequence still passes through each stage whole.

### [c] Recompute isn't enough
Even with FlashAttention and recomputation, activations grow linearly with S per layer.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What has to move?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Each GPU holds the queries for its chunk of the sequence. What must it receive from other GPUs to compute causal attention?
- [ ] Nothing
- [ ] The queries of other chunks
- [x] Keys and values of earlier chunks
- [ ] Gradients only
> <b>C.</b> Its queries must attend to the keys and values of every earlier token, which live on other GPUs. Queries stay put; K/V move.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Three ways to move K and V

::: cards grid3
### [a] Ring Attention
K/V blocks rotate one GPU per step; each GPU combines blocks with an online softmax. Communication overlaps compute; context up to N× longer.

### [b] All-gather (Llama 3)
All-gather the K and V tensors, then compute attention for the local queries. Simpler with arbitrary masks like document masks; latency exposed but small vs attention at long S.

### [c] All-to-all (Ulysses)
Re-shard from "split by sequence" to "split by heads" around attention with all-to-all, compute full-sequence attention per head group, then switch back.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Load balancing the causal mask

With contiguous chunks, GPU 0 attends to 1 block and GPU N−1 to N blocks. Reordering chunks (each GPU takes one early and one late piece) evens the work.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">GPUs N <input type="range" id="lN" min="2" max="16" step="1" value="8"> <output id="lNo"></output></label><div class="seg" id="lSeg"><button data-v="0" class="on">contiguous</button><button data-v="1">balanced (zig-zag)</button></div></div>
  <div id="lBars" style="margin-top:12px"></div>
</div>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works

::: cards grid2
### [a] Attention decomposes over key blocks
Online softmax (running max and sum) combines blocks exactly, the same trick as FlashAttention.

### [e] Linear memory scaling
Each GPU holds S/N tokens of activations, so context length can grow with GPUs.

### [b] Overlap
Computing on one K/V block while receiving the next hides most of the ring traffic.

### [d] Limits
Causal imbalance, exposed latency for all-gather, and Ulysses needs heads divisible by the group size.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Context parallelism approximates attention."
> With an online softmax it is exact (notebook 07 matches full causal attention).
:::

::: reveal myth
? "CP is the same as sequence parallelism."
> Megatron sequence parallelism shards activations outside attention within a TP group; CP splits the sequence for attention itself, across its own GPU group.
:::

::: reveal myth
? "Ring is always better than all-gather."
> Same bytes; all-gather is simpler and handles document masks easily, which is why Llama 3 chose it.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? With N GPUs in Ring Attention, how many K/V blocks does each GPU receive per layer?
- [ ] 1
- [ ] N/2
- [x] N − 1
- [ ] N²
> <b>N − 1</b>.
:::

::: reveal
? Why does the causal mask cause load imbalance, and how is it fixed?
> Later chunks attend to more earlier blocks. Assign each GPU one early and one late chunk (zig-zag) to equalize work.
:::

::: reveal
? What does Ulysses use instead of passing K/V around?
> All-to-all re-sharding between sequence-split and head-split layouts around attention.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Context parallelism splits long sequences across GPUs; queries stay, keys and values move (ring, all-gather or all-to-all), and online softmax keeps attention exact.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>At very long contexts a single sequence's activations no longer fit, and attention needs every token to see all earlier tokens. Context parallelism splits the sequence into chunks on different GPUs. Each GPU keeps its queries, and keys and values are exchanged: Ring Attention rotates key-value blocks around a ring while computing, combining them with an online softmax so the result is exact; Llama 3 all-gathers keys and values, which is simpler with document masks; DeepSpeed-Ulysses re-shards by heads with all-to-all. Memory per GPU falls with the number of GPUs, and causal masks need load balancing.</p></div>
    <div class="recap"><div><span><b>Problem:</b> one long sequence exceeds a GPU; attention spans all of it.</span></div><div><span><b>Core idea:</b> split tokens; move K/V (ring, all-gather, all-to-all); online softmax.</span></div><div><span><b>Watch:</b> causal load balance; same bytes, different overlap.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/distributed/07_ring_attention.ipynb" target="_blank" rel="noopener">07 · Context parallelism: ring attention</a> <span style="color:var(--faint)">· 40 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/distributed/07_ring_attention.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../07-expert-parallelism/index.html">07 · Expert parallelism →</a> · Previous: <a href="../05-pipeline-parallelism/index.html">← 05</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
