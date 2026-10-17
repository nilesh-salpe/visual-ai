---
title: PagedAttention and Prefix Caching
body:
  data-deck: PagedAttention and prefix caching
  data-home: ../index.html
  data-home-label: Inference
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'sequence :: logical token positions :: f'
  - 'logical blocks :: 16 tokens each :: a'
  - 'block table :: logical → physical :: c'
  - 'physical blocks :: anywhere in GPU memory

    shared blocks ref-counted :: b'
  caption: 'Like virtual memory: contiguous for the sequence, scattered in the GPU.'
example:
  title: 'Worked example: memory wasted per sequence'
  setup: Block size 16 tokens (vLLM's default). A sequence ends at 1,000 tokens; the server's maximum length is 4,096.
  steps:
  - 'Paged: ⌈1,000 / 16⌉ = <b>63 blocks</b>, holding 1,008 slots.'
  - Waste = 1,008 − 1,000 = <b>8 tokens</b> (0.8%), only in the last block.
  - 'Contiguous reservation for the maximum length: 4,096 − 1,000 = <b>3,096 tokens</b> wasted (75.6%).'
  - 'Prefix sharing: 8 parallel samples of the same prompt share its blocks (ref count 8) and copy a block only when they diverge.'
  result: Waste falls from 76% to under 1% here; at most block_size − 1 = 15 tokens per sequence, whatever its length.
traps:
  tricks:
  - 'Internal waste ≤ block_size − 1 tokens. :: Per sequence, independent of length.'
  - 'Copy-on-write. :: Parallel sampling and beam search share prompt blocks until a block is written.'
  - 'Prefix cache = skip prefill. :: A shared system prompt already in cache costs no prefill compute for later requests.'
  traps:
  - 'Blocks too small. :: More table lookups and less efficient memory access in the attention kernel.'
  - 'Prefix match must be exact tokens. :: One different token early in the prompt invalidates everything after it.'
  - 'Cache eviction. :: Under memory pressure, least-recently-used prefixes are evicted; a hot prefix can still miss.'
papers:
- vllm
- sglang
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">LLM Inference &amp; Serving · 05</div>
    <h1>PagedAttention and prefix caching</h1>
    <p class="sub">Managing the KV (key-value) cache like virtual memory (vLLM, SOSP 2023), and reusing the KV of shared prompt prefixes (SGLang's RadixAttention).</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>KV caches grow token by token to unknown final lengths. Reserving contiguous memory wastes most of it, and identical prompt prefixes get stored and recomputed again and again.</div>
      <div class="c"><b>Core idea</b>Store KV in fixed-size <b>blocks</b> mapped by a per-sequence <b>block table</b>, with reference counts and copy-on-write for sharing. Index cached prefixes in a <b>tree</b> so later requests can reuse them.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## The KV cache is dynamic and unpredictable

::: cards grid3
### [a] Grows every step
Each generated token appends K and V to every layer's cache.

### [b] Unknown final length
Nobody knows in advance whether a reply will be 10 tokens or 2,000.

### [c] Lots of sharing
Parallel samples, beam search and common system prompts all start from the same prefix.
:::

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Contiguous reservations waste memory and duplicate shared data

::: cards grid2
### [d] Fragmentation
Reserving max-length buffers leaves most slots unused. Uneven sizes also leave gaps between buffers. The vLLM paper calls this waste from "fragmentation and redundant duplication", and it limits batch size.

### [b] Duplication
Each sample of the same prompt gets its own copy of identical K and V. Every request with the same system prompt recomputes it during prefill.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Borrow an idea from operating systems

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Which operating-system idea fits the "growing, unpredictable, shareable memory" problem best?
- [ ] Swapping whole processes to disk
- [x] Paging: fixed-size pages, a page table per process, copy-on-write for shared pages
- [ ] A bigger contiguous heap
- [ ] Garbage collection
> <b>B.</b> PagedAttention stores each sequence's KV in fixed-size <b>blocks</b> (vLLM's default is 16 tokens) that need not be contiguous. A <b>block table</b> maps logical positions to physical blocks, and shared blocks are reference-counted and copied on write, just like OS pages.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Blocks, block tables, and copy-on-write

::: cards grid3
### [a] Fixed-size blocks
KV for B tokens per block. vLLM sets the default block size to <b>16</b>, as a balance between GPU (graphics processing unit) efficiency and internal fragmentation.

### [b] Block table
Per sequence: logical block i → physical block id. The attention kernel reads K and V through this table.

### [e] Share and copy on write
Forked sequences point at the same blocks (refcount &gt; 1). The first write to a shared, partly filled block copies it.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Watch the allocator <span class="ill">block size 4 for readability</span>

<div class="visual">
  <div class="steps" id="paSteps"></div>
  <div class="grid2" style="margin-top:12px;grid-template-columns:1.3fr 1fr">
    <div><h3>Physical blocks</h3><svg id="paSvg" viewBox="0 0 420 150" role="img" aria-label="Physical KV blocks"></svg></div>
    <div><h3>Block tables</h3><div id="paTables" class="mergelist" style="font-size:13px"></div></div>
  </div>
  <div class="infobox" id="paInfo"></div>
</div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Prefix caching: reuse shared prompts

Many requests begin with the same tokens: a system prompt, few-shot examples, earlier chat turns. Keep their KV after a request finishes, index it in a tree keyed by tokens, and the next request skips prefill for the longest cached prefix. SGLang's <b>RadixAttention</b> uses a radix tree with LRU (least recently used) eviction.
{: .lede}

<div class="visual">
  <div class="steps" id="pcSteps"></div>
  <div id="pcOut" style="margin-top:12px"></div>
  <div class="infobox" id="pcInfo"></div>
</div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works

::: cards grid2
### [e] Near-zero waste
Only the last block of each sequence can be partly empty, so waste is under one block per sequence. Build-it notebook 04 measures <b>0.6%</b> vs <b>48%</b> for contiguous max-length reservation on random lengths.

### [a] Bigger batches
Freed memory holds more sequences. vLLM reported <b>2–4×</b> throughput over FasterTransformer and Orca at the same latency.

### [b] Free sharing
Parallel sampling and beam search share prompt blocks through reference counts.

### [c] Prefix reuse
Shared prefixes skip prefill entirely. SGLang reported up to <b>6.4×</b> higher throughput on structured LLM (large language model) programs.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "PagedAttention makes attention compute faster."
> Its main win is <b>memory</b>: less waste and more sharing allow bigger batches, which raises throughput. The kernel has to read through the block table.
:::

::: reveal myth
? "Bigger blocks are always better."
> Larger blocks are more GPU-efficient but waste more in each sequence's last block. vLLM picked 16 as the balance.
:::

::: reveal myth
? "Prefix caching only helps identical prompts."
> It reuses the <b>longest shared prefix</b>, so different requests with the same system prompt still benefit.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? What is vLLM's default KV block size?
- [ ] 1 token
- [x] 16 tokens
- [ ] 256 tokens
- [ ] one whole sequence
> <b>16 tokens</b>.
:::

<div class="quiz ">
  <p class="qq">Two samples share a prompt whose last block is half full. What happens when sample 2 generates its next token?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">That block is <b>shared</b> (refcount 2) and partly filled, so the allocator copies it on write: sample 2 gets a fresh block, and the old block's refcount drops to 1.</div>
</div>

<div class="quiz">
  <p class="qq">What throughput gain did vLLM report over FasterTransformer and Orca at the same latency?</p>
  <div class="opts">
  <button>A. 1.2×</button>
  <button data-ok>B. 2–4×</button>
  <button>C. 36.9×</button>
  <button>D. 93%</button>
  </div>
  <div class="why"><b>2–4×</b>, with larger gains for longer sequences and larger models.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">PagedAttention manages the KV cache like virtual memory, with blocks, block tables and copy-on-write, and prefix caching reuses the KV of shared prompts.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>KV caches grow token by token to unknown lengths, so contiguous max-length reservations waste most of the memory and duplicate shared prompts. vLLM's PagedAttention stores KV in fixed blocks (16 tokens by default) mapped through a per-sequence block table, with reference counts and copy-on-write so forks share memory. Waste drops to under one block per sequence, batches get bigger, and vLLM reported 2–4× throughput. Prefix caching, such as SGLang's RadixAttention, keeps shared prefixes in a tree so later requests skip their prefill.</p></div>

<div class="recap"><div><span><b>Problem:</b> dynamic KV sizes cause fragmentation, and shared prefixes get duplicated and recomputed.</span></div><div><span><b>Core idea:</b> paged blocks plus block tables plus copy-on-write; a token tree for prefix reuse.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/07_paged_kv_allocator.ipynb" target="_blank" rel="noopener">07 · A paged KV-cache allocator</a> <span style="color:var(--faint)">· 40 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/inference/07_paged_kv_allocator.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/08_prefix_cache.ipynb" target="_blank" rel="noopener">08 · Prefix caching with a token trie (RadixAttention-style)</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/inference/08_prefix_cache.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../03-batching/index.html">03 · Continuous batching →</a> · Previous: <a href="../02-kv-cache/index.html">← 02 · KV cache</a> · <a href="../index.html">All decks</a></p>

<!-- slide id="s-papers" from="papers" -->
