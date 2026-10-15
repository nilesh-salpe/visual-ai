---
title: KV Cache Manager and PagedAttention
body:
  data-deck: KV cache manager and PagedAttention
  data-home: ../index.html
  data-home-label: vLLM
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'GPU KV memory :: pool of blocks :: f'
  - 'block table :: per request :: a'
  - 'allocate on demand :: 1 block per 16 tokens :: c'
  - 'ref counts :: shared prefixes :: b'
  - 'free → LRU queue :: reverse order :: e'
  caption: 'PagedAttention kernels read K and V through the block table. Concept: Inference deck 05.'
example:
  title: 'Worked example: waste with and without paging'
  setup: 'Notebook 01: 1,000 requests with final lengths uniform between 50 and 2,000 tokens; maximum length 2,048.'
  steps:
  - 'Reserving 2,048 contiguous slots per request: <b>49.7%</b> of reserved KV memory is never used.'
  - 'Paging with 16-token blocks: only the unused tail of each request''s last block is wasted: <b>0.75%</b>.'
  - 'Block size trades waste against overhead: 8 → 0.34%, 32 → 1.53%, 128 → 5.95% waste.'
  - The PagedAttention paper measured 20.4%–38.2% of KV memory holding real token states in earlier systems, versus 96.3% in vLLM.
  result: Paging turns KV memory from mostly reserved-but-empty into almost fully used, which directly raises batch size.
traps:
  tricks:
  - 'blocks = ⌈tokens / 16⌉. :: Default block_size 16 (CacheConfig.DEFAULT_BLOCK_SIZE).'
  - 'Ref count > 1 = shared. :: Prefix caching and parallel sampling share blocks.'
  - 'Watch vllm:kv_cache_usage_perc. :: High usage → preemptions.'
  traps:
  - 'Huge block sizes. :: More tail waste per request.'
  - 'Assuming freed = gone. :: Freed blocks keep their hashes until evicted.'
  - 'Ignoring per-layer cost. :: Each logical block exists in every layer.'
papers:
- vllm
- vllm_apc
- vllm_release
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">vLLM · 03</div>
    <h1>KV cache manager and PagedAttention</h1>
    <p class="sub">How vLLM stores the KV cache: a pool of fixed-size blocks, per-request block tables, reference counts for sharing, and an LRU free queue, as implemented in vllm/v1/core.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Each request's KV cache grows token by token to an unknown final length. Reserving a contiguous maximum-length region per request wastes most of the memory.</div>
      <div class="c"><b>Core idea</b>Split GPU KV memory into <b>blocks</b> of 16 tokens (the default <code>block_size</code>). Each request gets a <b>block table</b> mapping its logical blocks to physical ones, allocated on demand. Blocks carry <b>reference counts</b> so prefixes can be shared, and freed blocks enter an <b>LRU free queue</b> (in reverse order, tail first) so cached content survives as long as possible.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Watch the block pool

A pool of 48 blocks of 16 tokens. Add requests (random lengths), let them generate, and finish them. Colours show which request owns each block; freed blocks join the end of the free queue.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><button class="btn primary" id="kAdd">add request</button><button class="btn" id="kGrow">all generate 16 tokens</button><button class="btn" id="kFin">finish oldest</button><button class="btn" id="kReset">reset</button></div>
  <svg id="kSvg" viewBox="0 0 660 200" style="margin-top:10px" role="img" aria-label="KV block pool"></svg>
  <p class="readout" id="kOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why contiguous KV memory fails

::: cards grid3
### [d] Reservation
Unknown output lengths force reserving the maximum per request.

### [b] Fragmentation
Different reservation sizes leave unusable gaps between requests.

### [c] No sharing
Two requests with the same prefix store identical KV twice.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## How many blocks?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? A request has a 1,000-token prompt and has generated 40 tokens. How many 16-token blocks does it hold?
- [ ] 62
- [x] 65
- [ ] 66
- [ ] 1,040
> <b>B.</b> ⌈1,040 / 16⌉ = 65 blocks; the last holds 1,040 − 64·16 = 16 tokens, so it happens to be exactly full.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Blocks, tables, counts, queue

::: cards grid2
### [f] Block pool
All KV memory is pre-allocated at startup as blocks (size from CacheConfig, default 16).

### [a] Block table
Per request, the list of physical block ids for its logical blocks; kernels read KV through it.

### [b] Reference counts
A block may belong to several requests (shared prefix); it is freed when the count reaches 0.

### [e] LRU free queue
A doubly linked list of free blocks; allocation pops the front (least recently used); a request's blocks are freed in reverse order.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## In the source

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Piece</th><th>Where (v0.31.0)</th><th>Detail</th></tr>
  <tr><td>FreeKVCacheBlockQueue</td><td>vllm/v1/core/kv_cache_utils.py</td><td>doubly linked list; O(1) removal from the middle; LRU at the front</td></tr>
  <tr><td>BlockPool</td><td>vllm/v1/core/block_pool.py</td><td>allocates, frees, tracks cached block hashes</td></tr>
  <tr><td>KVCacheManager.allocate_slots</td><td>vllm/v1/core/kv_cache_manager.py</td><td>"touch" cached blocks (ref +1), then pop new blocks for new tokens</td></tr>
  <tr><td>Block size default</td><td>vllm/config/cache.py</td><td>DEFAULT_BLOCK_SIZE = 16; attention back ends may pick another</td></tr>
</table></div>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why paging works

::: cards grid2
### [a] Allocate as you grow
Only the last block is partly empty, so waste is bounded by one block per request.

### [e] Bigger batches
Memory saved becomes room for more concurrent requests.

### [b] Sharing is cheap
A ref-count increment shares a prefix with no copying.

### [c] Eviction keeps value
LRU order with tail-first freeing keeps the most reusable prefixes longest.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "PagedAttention changes the attention math."
> It computes the same attention; it only reads K and V from non-contiguous blocks.
:::

::: reveal myth
? "Smaller blocks are always better."
> They waste less tail space but add table and kernel overhead; 16 is the default balance.
:::

::: reveal myth
? "Blocks are allocated for the maximum length up front."
> They are allocated as tokens are scheduled; that is the point of paging.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? vLLM's default KV block size (CacheConfig.DEFAULT_BLOCK_SIZE)?
- [ ] 8
- [x] 16
- [ ] 32
- [ ] 128
> <b>16</b> tokens.
:::

::: reveal
? Why free a request's blocks in reverse order?
> So the tail blocks become least recently used and are evicted first, keeping the more widely shared head (prefix) blocks cached longer.
:::

::: reveal
? What makes sharing a prefix free?
> Reference counts: a second request just points its block table at the same blocks and increments their counts.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">vLLM pages the KV cache into 16-token blocks with per-request block tables, reference counts for sharing and an LRU free queue, cutting KV waste from about half to under 1% in the notebook.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>The KV cache grows with every generated token to a length nobody knows in advance, so reserving contiguous space per request wastes most of it. vLLM pre-allocates all KV memory as a pool of blocks, sixteen tokens each by default, and gives every request a block table that maps its logical blocks to physical ones, allocated only as tokens are scheduled. Blocks have reference counts, so requests with the same prefix can share them, and freed blocks join a least-recently-used queue, tail first, so cached prefixes survive longest. In notebook one this cut waste from about fifty percent to under one percent.</p></div>
    <div class="recap"><div><span><b>Problem:</b> unknown lengths make contiguous KV wasteful.</span></div><div><span><b>Core idea:</b> blocks + block tables + ref counts + LRU queue.</span></div><div><span><b>Default:</b> block_size 16.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/vllm/01_block_pool.ipynb" target="_blank" rel="noopener">01 · The KV block pool: paging, ref counts and LRU</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/vllm/01_block_pool.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../04-scheduler/index.html">04 · The scheduler: continuous batching and chunked prefill →</a> · Previous: <a href="../02-engine-architecture/index.html">← 02</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
