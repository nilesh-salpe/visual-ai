---
title: Automatic Prefix Caching
body:
  data-deck: Automatic prefix caching
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
  - 'prompt tokens :: split into 16-token blocks :: f'
  - 'hash(parent, tokens) :: chained :: a'
  - 'lookup :: longest matching run :: c'
  - 'touch hits :: ref count +1 :: b'
  - 'prefill only the rest :: + last token :: e'
  caption: Partial blocks are never cached; the last token is always recomputed to produce logits.
example:
  title: 'Worked example: a shared system prompt'
  setup: 'Notebook 02: every request = the same 70-token system prompt + a unique 30-token user message; requests processed in order with one cache.'
  steps:
  - 70 tokens = 4 full blocks (64 tokens) + 6 tokens in a partial block. Only the 4 full blocks can be cached.
  - 'The first request misses; each of the next 19 reuses 64 tokens: 19 × 64 / 2,000 = <b>60.8%</b> of all prompt tokens skip prefill (over 50 users: 62.7%).'
  - A 500-token shared prefix saves <b>91.7%</b>; a 2,000-token one 96.6%; a 10-token one 0% (no full block).
  - 'Changing the very first token changes every block hash after it: the whole prefix misses.'
  result: Long, stable prefixes put first in the prompt are where prefix caching pays off.
traps:
  tricks:
  - 'Put shared content first. :: System prompt, tools, documents, then the user turn.'
  - 'Watch vllm:prefix_cache_hits / queries. :: The hit rate.'
  - 'Route DP traffic by prefix. :: Each data-parallel rank has its own cache.'
  traps:
  - 'Timestamps or IDs at the top of the prompt. :: Every request misses.'
  - 'Expecting hits on partial blocks. :: Only full 16-token blocks are cached.'
  - 'Assuming cached = permanent. :: Blocks are evicted LRU under memory pressure.'
papers:
- vllm_apc
- vllm_v1
- sglang
status: {label: current, reviewed: 2026-10-15, note: "v0.31.0 is still the latest release; prefix caching on by default"}
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">vLLM · 05</div>
    <h1>Automatic prefix caching</h1>
    <p class="sub">How vLLM reuses KV cache across requests that share a prefix (system prompts, few-shot examples, multi-turn chats, RAG documents): chained block hashes, cache hits, and eviction.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Many requests start with the same thousands of tokens. Recomputing their KV cache for every request wastes prefill compute and adds time to first token.</div>
      <div class="c"><b>Core idea</b>Hash every <b>full</b> KV block together with the hash of the block before it, so a block hash identifies the <b>entire prefix</b> up to that block. A new prompt reuses the longest run of matching block hashes and only prefills the rest. Freed blocks keep their hashes until <b>LRU eviction</b>. In V1 it is <b>on by default</b> (<code>enable_prefix_caching=True</code>, hash <code>sha256</code>).</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Which blocks hit?

Two prompts, split into 16-token blocks. Edit where the second prompt first differs from the first; blocks before that point (full blocks only) are cache hits.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">shared prefix length <input type="range" id="pS" min="0" max="160" step="1" value="70"> <output id="pSo"></output></label><label class="ctl">prompt length <input type="range" id="pL" min="20" max="200" step="1" value="100"> <output id="pLo"></output></label></div>
  <svg id="pSvg" viewBox="0 0 660 140" style="margin-top:10px" role="img" aria-label="Prefix cache hits"></svg>
  <p class="readout" id="pOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why exact-match hashing on whole prompts isn't enough

::: cards grid3
### [d] Prompts differ at the end
Whole-prompt hashes would almost never match.

### [b] Position matters
The same text at a different position has different KV (positions are encoded in K).

### [c] Memory is finite
Cached blocks must be evictable when space is needed.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Why chain the hashes?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Why does vLLM hash each block together with its parent block's hash?
- [ ] To make hashing faster
- [x] So a block hash identifies the whole prefix before it, not just its own 16 tokens
- [ ] To compress the KV cache
- [ ] Because sha256 requires it
> <b>B.</b> KV values depend on every earlier token. Chaining ensures a hit means the entire prefix matched.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Hash, look up, touch, evict

::: cards grid2
### [a] Hash
hash((parent_hash, block_tokens, extra_keys)) for each full block (sha256 by default; xxhash options exist).

### [c] Look up
Walk the prompt's block hashes from the start; stop at the first miss.

### [b] Touch
Hit blocks get ref count +1 and leave the free queue so they cannot be evicted while in use.

### [e] Evict
Blocks with ref count 0 stay cached in the LRU free queue until reused for new data.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Where prefix caching shines

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Workload</th><th>Shared prefix</th></tr>
  <tr><td>Chat with a long system prompt</td><td>system prompt + tool definitions</td></tr>
  <tr><td>Multi-turn conversations</td><td>all earlier turns</td></tr>
  <tr><td>Few-shot prompting</td><td>the examples</td></tr>
  <tr><td>RAG over a fixed corpus</td><td>documents placed first, if repeated across queries</td></tr>
  <tr><td>Agents</td><td>the growing trajectory: each call extends the previous one</td></tr>
</table></div>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it is nearly free

::: cards grid2
### [a] Built on paging
Blocks and ref counts already exist; caching just keeps hashes on freed blocks.

### [e] Zero overhead on misses
V1 made prefix caching cheap enough to enable by default (V1 blog).

### [b] Big TTFT savings
Skipped prefill tokens directly cut time to first token.

### [c] Composable
Works with chunked prefill, preemption and speculative decoding through the same "computed tokens" counter.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Prefix caching caches responses."
> It caches KV states of prompt prefixes; outputs are still generated fresh.
:::

::: reveal myth
? "Any shared substring is reused."
> Only an identical prefix from the first token, in whole blocks, is reused.
:::

::: reveal myth
? "It must be enabled manually."
> enable_prefix_caching defaults to True in vLLM V1 (v0.31.0).
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? A 70-token shared system prompt with 16-token blocks caches how many tokens?
- [ ] 70
- [x] 64
- [ ] 80
- [ ] 48
> 4 full blocks = <b>64</b>.
:::

::: reveal
? Why is the last prompt token always recomputed?
> The model needs to run at least one token through the network to produce the logits for the next token.
:::

::: reveal
? How should you structure prompts to maximise hits?
> Put stable, shared content (system prompt, tools, documents) first and the variable part last; avoid timestamps or IDs early in the prompt.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">vLLM caches full KV blocks under chained hashes, so any request sharing an exact prefix skips its prefill; it is on by default in V1 and pays off most for long, stable prefixes.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Automatic prefix caching reuses KV cache across requests. vLLM hashes each full sixteen-token block together with the hash of the block before it, so a block's hash stands for the entire prefix up to it. When a request arrives, the scheduler walks its block hashes from the start and reuses every matching block, prefilling only the rest plus the last token. Finished requests leave their blocks in a least-recently-used queue with their hashes intact until the memory is needed. In version one it is on by default. Put stable content like system prompts first.</p></div>
    <div class="recap"><div><span><b>Problem:</b> repeated prefixes waste prefill.</span></div><div><span><b>Core idea:</b> chained block hashes; longest matching run.</span></div><div><span><b>Default:</b> on in V1; sha256.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/vllm/02_prefix_cache.ipynb" target="_blank" rel="noopener">02 · Automatic prefix caching with chained block hashes</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/vllm/02_prefix_cache.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../06-speculative-decoding/index.html">06 · Speculative decoding in vLLM →</a> · Previous: <a href="../04-scheduler/index.html">← 04</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
