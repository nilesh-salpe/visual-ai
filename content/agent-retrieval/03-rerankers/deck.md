---
title: Rerankers
body:
  data-deck: Rerankers
  data-home: ../index.html
  data-home-label: Retrieval
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
papers:
- sbert
- monobert
- colbert
- rankgpt
- rrf
- contextual_retrieval
- cohere_rerank
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Visual Agents · Retrieval · 03</div>
    <h1>Rerankers</h1>
    <p class="sub">The second stage of retrieval: a slower, more accurate model rereads the query together with each candidate and reorders a short list. Cross-encoders, late interaction (ColBERT) and LLM rerankers.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>First-stage retrieval (BM25 or a bi-encoder) scores query and document <b>independently</b>, so it is fast but misses fine-grained relevance. The top 20 chunks you hand the LLM often contain near-misses while the best passage sits at rank 60.</div>
      <div class="c"><b>Core idea</b><b>Retrieve many cheaply, rerank few carefully.</b> Fetch around 100-150 candidates, score each with a model that reads query and document <b>together</b> (a cross-encoder), keep the best 20. Anthropic's tests: top-20 failures fell from 2.9% to 1.9% when reranking was added to contextual hybrid search. Variants trade accuracy for speed: late interaction (ColBERT) and listwise LLM reranking (RankGPT).</div>
    </div>
    <div class="toc" data-auto></div>
    <p class="start-hint">Previous: <a href="../02-vector-databases/index.html">Vector databases</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Independent scoring misses relevance

::: cards grid3
### [d] One vector per text
A bi-encoder squeezes a passage into one vector before it has seen the query.

### [b] Lexical blind spots
BM25 matches words, not meaning; dense search matches meaning, not exact terms.

### [c] Recall vs precision
Wide top-k improves recall but floods the LLM context with noise and cost.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Two stages: wide recall, then precision

::: cards grid2
### [f] Why not cross-encode everything
Sentence-BERT's example: finding the most similar pair among 10,000 sentences takes ~65 hours with a BERT cross-encoder, ~5 seconds with a bi-encoder.

### [a] Cross-encoder
monoBERT feeds [query; passage] to BERT and outputs a relevance score: +27% relative MRR@10 on MS MARCO (Microsoft Machine Reading Comprehension) when it was published.

### [c] Late interaction
ColBERT keeps one embedding per token, precomputes documents and scores with MaxSim: competitive with BERT rerankers, two orders of magnitude faster.

### [e] LLM reranking
RankGPT asks an LLM for a permutation of passages with a sliding window over BM25's top 100; distilled into a 440M model it beats a 3B supervised reranker on BEIR.
:::

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## A two-stage retrieval service

<div class="visual dgm" data-steps="[&quot;The query (often rewritten by the agent) enters retrieval.&quot;, &quot;Lexical and dense retrieval run in parallel, each returning about a hundred candidates.&quot;, &quot;Reciprocal rank fusion merges the lists: score(d) = \u03a3 1/(60 + rank) over the lists; no score calibration needed.&quot;, &quot;The reranker reads the query with each candidate and scores it. Anthropic retrieved the top 150 and reranked them.&quot;, &quot;Only the best 20 go into the model&#x27;s context; Anthropic found 20 better than 5 or 10.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 290" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah11" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="112.0" y1="119.6" x2="166.3" y2="90.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah11)"/></g><g data-step="2"><line x1="112.0" y1="176.4" x2="166.3" y2="206.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah11)"/></g><g data-step="3"><line x1="286.7" y1="88.0" x2="344.2" y2="116.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah11)"/></g><g data-step="3"><line x1="286.7" y1="208.0" x2="344.2" y2="180.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah11)"/></g><g data-step="4"><line x1="468.3" y1="118.0" x2="522.8" y2="90.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah11)"/></g><g data-step="5"><line x1="585.0" y1="88.0" x2="585.0" y2="206.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah11)"/></g><g data-step="1"><rect x="10" y="120" width="100" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="60.0" y="153.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Query</text></g><g data-step="2"><rect x="150" y="30" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="225.0" y="56.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">BM25</text><text x="225.0" y="72.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">top 100</text></g><g data-step="2"><rect x="150" y="210" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="225.0" y="236.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Dense ANN</text><text x="225.0" y="252.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">top 100</text></g><g data-step="3"><rect x="340" y="120" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="410.0" y="146.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Fuse</text><text x="410.0" y="162.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">RRF → ~150</text></g><g data-step="4"><rect x="520" y="30" width="130" height="56" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="585.0" y="56.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Reranker</text><text x="585.0" y="72.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">cross-encoder</text></g><g data-step="5"><rect x="520" y="210" width="130" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="585.0" y="236.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Top 20</text><text x="585.0" y="252.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">to the LLM</text></g><g data-step="4"><text x="495.6" y="99.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">candidates</text></g><g data-step="5"><text x="585.0" y="142.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">reorder, cut</text></g></svg><p class="readout dgcap"></p></div>

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Three ways to score

<div class="visual dgm" data-steps="[&quot;Bi-encoder (first stage): query and document are encoded separately; documents once, offline, so search is a vector lookup (DPR, Sentence-BERT).&quot;, &quot;Cross-encoder (reranker): query and document share one input, so attention compares every query token with every document token. Accurate, but a full model call per pair at query time.&quot;, &quot;Late interaction (ColBERT): token-level embeddings for both, documents precomputed; each query token takes its best-matching document token, and the scores are summed.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 290" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah12" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="1"><line x1="110.0" y1="72.0" x2="110.0" y2="111.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah12)"/></g><g data-step="1"><line x1="110.0" y1="173.0" x2="110.0" y2="216.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah12)"/></g><g data-step="2"><line x1="330.0" y1="72.0" x2="330.0" y2="111.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah12)"/></g><g data-step="2"><line x1="330.0" y1="173.0" x2="330.0" y2="216.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah12)"/></g><g data-step="3"><line x1="550.0" y1="72.0" x2="550.0" y2="111.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah12)"/></g><g data-step="3"><line x1="550.0" y1="173.0" x2="550.0" y2="216.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah12)"/></g><g data-step="1"><rect x="10" y="20" width="200" height="50" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="110.0" y="43.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">q and d apart</text><text x="110.0" y="59.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">bi-encoder</text></g><g data-step="1"><rect x="10" y="115" width="200" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="110.0" y="141.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Two encodings</text><text x="110.0" y="157.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">docs precomputed</text></g><g data-step="1"><rect x="10" y="220" width="200" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="110.0" y="246.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">cosine / dot</text><text x="110.0" y="262.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">one vector each</text></g><g data-step="2"><rect x="230" y="20" width="200" height="50" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="330.0" y="43.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">[q ; d] together</text><text x="330.0" y="59.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">cross-encoder</text></g><g data-step="2"><rect x="230" y="115" width="200" height="56" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="330.0" y="141.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Full attention</text><text x="330.0" y="157.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">every pair at query time</text></g><g data-step="2"><rect x="230" y="220" width="200" height="56" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="330.0" y="246.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">relevance score</text><text x="330.0" y="262.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">most accurate</text></g><g data-step="3"><rect x="450" y="20" width="200" height="50" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="550.0" y="43.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">q tokens · d tokens</text><text x="550.0" y="59.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">late interaction</text></g><g data-step="3"><rect x="450" y="115" width="200" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="550.0" y="141.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Token embeddings</text><text x="550.0" y="157.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">docs precomputed</text></g><g data-step="3"><rect x="450" y="220" width="200" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="550.0" y="246.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Σ MaxSim</text><text x="550.0" y="262.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">per query token</text></g></svg><p class="readout dgcap"></p></div>

<div class="visual scroll-x"><table class="tbl"><tr><th>Reranker</th><th>Input per call</th><th>Calls per query</th></tr><tr><td>Cross-encoder (pointwise)</td><td>one query-passage pair</td><td>one per candidate (batched)</td></tr><tr><td>LLM listwise (RankGPT)</td><td>a window of passages</td><td>windows slide from the back of the list to the front</td></tr><tr><td>Hosted API (e.g. Cohere Rerank)</td><td>query + list of documents</td><td>one request; scores per document</td></tr></table></div>

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

<div class="visual scroll-x"><table class="tbl"><tr><th>Option</th><th>Benefit</th><th>Cost</th></tr><tr><td>No reranker</td><td>lowest latency</td><td>precision limited by the first stage</td></tr><tr><td>Cross-encoder</td><td>large precision gain for a short list</td><td>latency grows with candidates × length</td></tr><tr><td>ColBERT</td><td>near cross-encoder quality at lower query cost</td><td>stores an embedding per token: much larger index</td></tr><tr><td>LLM listwise</td><td>strong zero-shot, follows instructions</td><td>expensive and slow; position bias</td></tr><tr><td>Deeper candidate list</td><td>higher recall going in</td><td>more reranker compute per query</td></tr></table></div>

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

<div class="visual scroll-x"><table class="tbl"><tr><th>Failure</th><th>Symptom</th><th>Mitigation</th></tr><tr><td>Recall ceiling</td><td>the right passage was never retrieved</td><td>reranking only reorders: fix the first stage (hybrid, contextual chunks)</td></tr><tr><td>Truncation</td><td>long chunks cut at the model's input limit, answer lost</td><td>chunk to fit the reranker; check its maximum length</td></tr><tr><td>Uncalibrated scores</td><td>a fixed score threshold drops good results on some queries</td><td>cut by rank, or calibrate per domain</td></tr><tr><td>Latency spikes</td><td>p99 grows with candidate count</td><td>cap candidates, batch on GPU, time-out to first-stage order</td></tr><tr><td>Domain shift</td><td>web-trained reranker misjudges code or legal text</td><td>evaluate on your data; fine-tune or distil</td></tr></table></div>

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Measure both stages
Track recall@150 for the first stage and nDCG@10 (normalised discounted cumulative gain) after reranking.

### [c] Latency budget
An agent may search several times per task; budget the reranker per call.

### [b] Distil
Use an LLM reranker offline to label data, then train a small cross-encoder for serving, as RankGPT did.

### [e] Structured documents
Format semi-structured records consistently (Cohere recommends YAML strings) so the reranker sees the fields.
:::

<!-- slide id="s-papers" from="papers" -->
