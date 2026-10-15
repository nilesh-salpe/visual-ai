---
title: RAG, Fine-tuning or Long Context
body:
  data-deck: RAG, fine-tuning or long context
  data-home: ../index.html
  data-home-label: Context
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
- ../../shared/diagram.js
intro:
  kicker: Visual Agents · Context · 05
  h1: RAG, fine-tuning or long context?
  sub: 'Three ways to give a model knowledge it lacks: retrieve it per query, train it into the weights, or put everything in the context window. What each is good
    at, what the evidence says, what a query costs, and how production systems combine them.'
  problem: An assistant must answer from a company's documents, which change daily and were never in pretraining. Teams fine-tune "to teach it our data", or paste
    everything into a huge context window, and get stale facts, hallucinations or a large bill.
  core: 'Match the tool to what is missing. Missing <b>knowledge</b> (facts that change, need citations or access control): <b>retrieval</b>. Missing <b>behaviour</b>
    (format, style, tool use, a domain''s way of working): <b>fine-tuning</b>. A <b>bounded set of documents</b> that fits and is asked about repeatedly: <b>long
    context with prompt caching</b>. Production systems combine them: fine-tune for behaviour, retrieve for facts, and route each query to retrieval or long context.'
  hint: 'Previous: [Agent2Agent protocol (A2A)](../04-a2a/index.html) · [All decks](../index.html)'
papers:
- ft_or_rag
- ft_new_knowledge
- selfroute
- ruler
- lostmiddle
- raft
- rag_lewis
- contextual_retrieval
- ant_caching
- claude_context_windows
- lora
status:
  label: current
  reviewed: '2026-10-15'
  note: Written from primary sources 2026-10-15; context limits and caching prices from the Claude docs on that date.
---

<!-- slide from="title" -->

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Three ways to add knowledge

::: cards grid3
### [d] Facts change
Prices, policies and tickets change daily; model weights are a snapshot from the last training run.

### [b] Fine-tuning teaches facts poorly
Ovadia et al.: retrieval beat unsupervised fine-tuning for both known and new facts. On new current-events questions, Mistral 7B scored 0.481 base, 0.504 fine-tuned (0.588 with paraphrased data) and 0.875 with retrieval.

### [c] Long context is not free
Every query pays for every token in the prompt, and accuracy and recall degrade as contexts grow (context rot). In RULER, only about half of 17 models claiming 32K+ context performed satisfactorily at 32K.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Match the tool to what is missing

::: table
| What the model lacks | Use | Why |
|---|---|---|
| Facts that change, must be cited, or depend on who asks | Retrieval (RAG) | update the index, not the model; cite sources; filter by permissions |
| A format, style, tool-use habit or domain behaviour | Fine-tuning (SFT, LoRA) | behaviour generalises from examples; facts are learned slowly and can increase hallucination |
| A bounded set of documents, asked about repeatedly | Long context + prompt caching | no retrieval misses; Anthropic suggests knowledge bases under 200,000 tokens can go straight into the prompt |
| Better use of retrieved documents in one domain | Retrieval-aware fine-tuning (RAFT) | train with distractor documents so the model learns to ignore irrelevant chunks and quote the right one |
:::

Gekhman et al. add a warning for fine-tuning on facts: examples with knowledge the model lacks are learned much more slowly and, once learned, linearly increase its tendency to hallucinate.

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## Combining all three

::: diagram 660x300
nodes:
  q: {at: [10, 120, 110, 56], text: Query, sub: user + permissions, color: f, step: 1}
  rt: {at: [160, 120, 120, 56], text: Router, sub: RAG or full docs, color: b, step: 2}
  up: {at: [160, 20, 120, 56], text: Index, sub: updated on change, color: f, step: 3}
  ix: {at: [330, 20, 140, 56], text: Retriever, sub: hybrid + rerank, color: a, step: 3}
  ch: {at: [510, 20, 140, 56], text: Top-k chunks, sub: with sources, color: a, step: 3}
  lc: {at: [330, 220, 140, 56], text: Document set, sub: cached prefix, color: c, step: 4}
  m: {at: [510, 120, 140, 56], text: Fine-tuned model, sub: format · tools · style, color: e, step: 5}
edges:
  - {from: q, to: rt, step: 2}
  - {from: rt, to: ix, label: open corpus, step: 3}
  - {from: up, to: ix, step: 3, style: dash}
  - {from: ix, to: ch, step: 3}
  - {from: ch, to: m, step: 5}
  - {from: rt, to: lc, label: bounded set, step: 4}
  - {from: lc, to: m, step: 5}
steps:
  - 'A query arrives with the user''s identity, which decides what they may read.'
  - 'A router picks the knowledge path: retrieval for a large or changing corpus, long context for a small, fixed set (for example one contract or one code repository).'
  - 'Retrieval path: an index updated whenever documents change, hybrid search and reranking (Retrieval stack decks), returning the top chunks with their sources.'
  - 'Long-context path: the whole document set goes into the prompt as a stable prefix, so prompt caching makes repeat queries cheap.'
  - 'The model may be fine-tuned, but for behaviour (answer format, citation style, tool use), not to memorise the documents. It answers from the supplied text and cites it.'
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Routing per query: Self-Route

::: diagram 660x270
nodes:
  q: {at: [10, 40, 110, 56], text: Query, color: f, step: 1}
  r: {at: [140, 40, 120, 56], text: Retrieve top-k, sub: 5 × 300 words, color: a, step: 1}
  p: {at: [285, 40, 150, 56], text: Model + chunks, sub: answer or "unanswerable", color: b, step: 2}
  a1: {at: [530, 40, 120, 56], text: Answer (RAG), sub: most queries, color: e, step: 3}
  lc: {at: [285, 190, 150, 56], text: Long-context call, sub: full documents, color: c, step: 4}
  a2: {at: [530, 190, 120, 56], text: Answer (LC), sub: the hard cases, color: e, step: 4}
edges:
  - {from: q, to: r, step: 1}
  - {from: r, to: p, step: 2}
  - {from: p, to: a1, label: answerable, step: 3}
  - {from: p, to: lc, label: unanswerable, step: 4}
  - {from: lc, to: a2, step: 4}
steps:
  - Retrieve the top 5 chunks of 300 words for the query (Li et al. 2024).
  - 'Ask the model to answer from the chunks, or to write "unanswerable" if they are not enough.'
  - 'Most queries stop here. Retrieval and long context gave identical predictions on over 60% of queries, so routing those to retrieval loses nothing.'
  - Only "unanswerable" queries pay for a long-context call. With GPT-4o this used 61% of the tokens for a score of 46.83 vs 47.04 for long context alone; cost fell 65% for Gemini-1.5-Pro and 39% for GPT-4o.
:::

<div class="visual"><div class="controls"><label class="ctl">corpus tokens <input type="range" id="rcN" min="1" max="200" step="1" value="30"> <output id="rcNo"></output></label><label class="ctl">queries per day <input type="range" id="rcQ" min="100" max="50000" step="100" value="5000"> <output id="rcQo"></output></label><label class="ctl">retrieved tokens per query <input type="range" id="rcK" min="1" max="20" step="1" value="4"> <output id="rcKo"></output></label><label class="ctl">input price per million tokens <input type="range" id="rcP" min="0.25" max="15" step="0.25" value="3"> <output id="rcPo"></output></label></div><div class="bars"><div id="rcBars"></div></div><p class="readout" id="rcOut"></p></div>

Prices are assumptions to set yourself. Cache multipliers are from the Claude prompt-caching documentation: reads cost 0.1× the base input price on most models (less on some newer ones), 5-minute cache writes 1.25×.

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

::: table
| Approach | Strengths | Weaknesses |
|---|---|---|
| Retrieval (RAG) | fresh facts, citations, permission filtering, scales to any corpus size, cheap per query | retrieval misses; chunking loses context; more moving parts |
| Fine-tuning | reliable format and behaviour; shorter prompts; can specialise a small, cheap model | facts go stale; new facts learned slowly and can raise hallucination; retraining for every update |
| Long context | no retrieval misses; whole-document reasoning; simple to build | cost and latency grow with every token; recall degrades with length and position; bounded by the window (up to 1M tokens on current Claude models) |
| Long context + caching | repeat queries on a stable prefix are cheap and fast | cache expires (5 minutes or 1 hour); any change before the cached prefix invalidates it |
| Hybrid (route per query) | retrieval cost for easy queries, long-context quality for hard ones | two paths to build, test and monitor |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Fine-tuned on facts | confident answers from last quarter's policy | retrieve facts at query time; fine-tune for behaviour only |
| Retrieval miss | "I can't find that" although the document exists | hybrid search, contextual chunks, reranking; route misses to long context |
| Lost in the middle | facts in the middle of a long prompt are ignored | put key material at the start or end; retrieve to shorten the prompt |
| Distractor chunks | the model answers from a similar but wrong document | reranking; RAFT-style training with distractors; require quotes |
| Cache misses | long-context bill far above estimates | keep the prefix byte-identical; put variable content after the cache breakpoint |
| Permission leaks | a user sees content from documents they cannot open | filter retrieval by the user's permissions; never fine-tune on restricted data |
:::

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Start with retrieval
It is the default for enterprise knowledge: fresh, citable and permission-aware. See the enterprise RAG case study.

### [c] Fine-tune last, for behaviour
When prompts cannot fix format, tone or tool use, fine-tune (often LoRA) on examples of the behaviour, and keep facts in retrieval.

### [b] Long context for bounded tasks
One contract, one repository, one long report: put it all in, cache the prefix, and skip the retrieval pipeline.

### [e] Measure per path
Track answer quality, retrieval recall, tokens and cost separately for each path, and re-test when the model or the corpus changes.
:::

<!-- slide id="s-papers" from="papers" -->
