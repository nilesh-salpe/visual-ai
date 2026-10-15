---
title: Memory and Context Management
body:
  data-deck: Memory and context management
  data-home: ../index.html
  data-home-label: Context
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
papers:
- context_eng
- memgpt
- genagents
- lostmiddle
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Visual Agents · Context · 01</div>
    <h1>Memory and context management</h1>
    <p class="sub">How agents remember: the context window as working memory, compaction and notes for long tasks, and long-term stores with scored retrieval and reflection.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>The context window is finite and gets less reliable as it fills ("context rot"; models miss facts in the middle of long contexts), yet agents run for many steps and users expect them to remember across sessions.</div>
      <div class="c"><b>Core idea</b>Treat context as a scarce <b>attention budget</b>. Keep <b>working memory</b> curated; <b>compact</b> (summarise and restart) near the limit; write <b>structured notes</b> to external storage; retrieve <b>long-term memories</b> by a score such as recency + importance + relevance (Generative Agents) or let the model page memory in and out itself (MemGPT).</div>
    </div>
    <div class="toc" data-auto></div>
    <p class="start-hint">Next: <a href="../02-agentic-rag/index.html">Agentic retrieval (RAG) →</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Context is finite and fragile

::: cards grid3
### [d] Context rot
As tokens increase, recall of information in the context decreases (Anthropic, context engineering).

### [b] Lost in the middle
Performance is often highest when relevant information is at the start or end and degrades in the middle (Liu et al.).

### [c] Sessions end
Nothing persists unless the agent writes it somewhere.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Tiers of memory

::: cards grid2
### [a] Working memory
The context window: system prompt, task, recent steps, retrieved items. Curate it.

### [c] Compaction
Near the limit, summarise the conversation and start a new context with the summary.

### [b] Structured notes
The agent writes progress, decisions and to-dos to files or a store and reads them back later.

### [e] Long-term memory
Episodes, facts and reflections retrieved on demand; MemGPT pages them in and out like OS virtual memory.
:::

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## Memory architecture

<div class="visual dgm" data-steps="[&quot;The agent loop asks for context each step.&quot;, &quot;A context manager decides what goes into the window, compacting history when it nears the limit.&quot;, &quot;Durable notes hold task state outside the window.&quot;, &quot;A long-term store returns the most useful memories for the current query.&quot;, &quot;Periodically, memories are synthesised into higher-level reflections (Generative Agents reflected when summed importance exceeded a threshold, 150 in their implementation).&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 300" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah8" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="152.0" y1="150.0" x2="206.0" y2="150.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah8)"/></g><g data-step="2"><line x1="363.1" y1="118.0" x2="463.7" y2="74.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah8)"/></g><g data-step="3"><line x1="372.0" y1="141.5" x2="426.0" y2="135.8" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah8)"/></g><g data-step="4"><line x1="372.0" y1="168.8" x2="426.0" y2="181.2" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah8)"/></g><g data-step="5"><line x1="530.0" y1="232.0" x2="530.0" y2="246.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah8)"/></g><g data-step="1"><rect x="20" y="120" width="130" height="60" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="85.0" y="148.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Agent</text><text x="85.0" y="164.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">LLM loop</text></g><g data-step="2"><rect x="210" y="120" width="160" height="60" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="290.0" y="148.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Context manager</text><text x="290.0" y="164.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">assemble · compact</text></g><g data-step="2"><rect x="430" y="20" width="200" height="50" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="530.0" y="43.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Working memory</text><text x="530.0" y="59.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">context window</text></g><g data-step="3"><rect x="430" y="100" width="200" height="50" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="530.0" y="123.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Notes / scratch files</text><text x="530.0" y="139.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">progress, to-dos</text></g><g data-step="4"><rect x="430" y="180" width="200" height="50" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="530.0" y="203.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Long-term store</text><text x="530.0" y="219.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">vector + metadata</text></g><g data-step="5"><rect x="430" y="250" width="200" height="44" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="530.0" y="270.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Reflections</text><text x="530.0" y="286.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">periodic summaries</text></g><g data-step="2"><text x="413.4" y="91.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">fits budget</text></g><g data-step="3"><text x="399.0" y="133.6" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">write / read</text></g><g data-step="4"><text x="399.0" y="170.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">retrieve</text></g><g data-step="5"><text x="530.0" y="234.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">synthesise</text></g></svg><p class="readout dgcap"></p></div>

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Scoring and writing memories

<div class="visual dgm" data-steps="[&quot;Each memory record has text, timestamps, an importance rating and an embedding.&quot;, &quot;Three signals (Park et al., 2023): recency (exponential decay, factor 0.995 per sandbox hour), importance (the model rates 1\u201310), relevance (cosine similarity to the query).&quot;, &quot;Each is min-max scaled to [0, 1] and summed with all weights set to 1.&quot;, &quot;The top-ranked memories that fit in the context window go into the prompt.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 250" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah9" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="172.0" y1="200.3" x2="236.0" y2="188.1" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah9)"/></g><g data-step="2"><line x1="192.0" y1="63.6" x2="236.0" y2="52.7" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah9)"/></g><g data-step="2"><line x1="192.0" y1="91.9" x2="236.0" y2="95.4" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah9)"/></g><g data-step="2"><line x1="171.7" y1="112.0" x2="255.7" y2="146.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah9)"/></g><g data-step="3"><line x1="392.6" y1="56.0" x2="456.0" y2="76.9" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah9)"/></g><g data-step="3"><line x1="402.0" y1="104.1" x2="456.0" y2="105.5" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah9)"/></g><g data-step="3"><line x1="402.0" y1="149.2" x2="456.0" y2="134.2" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah9)"/></g><g data-step="4"><line x1="550.0" y1="138.0" x2="550.0" y2="186.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah9)"/></g><g data-step="1"><rect x="20" y="190" width="150" height="50" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="95.0" y="220.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Current query</text></g><g data-step="1"><rect x="20" y="60" width="170" height="50" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="105.0" y="83.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Memory records</text><text x="105.0" y="99.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">text · time · importance</text></g><g data-step="2"><rect x="240" y="10" width="160" height="44" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="320.0" y="30.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Recency</text><text x="320.0" y="46.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">decay 0.995 / game hour</text></g><g data-step="2"><rect x="240" y="80" width="160" height="44" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="320.0" y="100.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Importance</text><text x="320.0" y="116.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">LLM-rated 1–10</text></g><g data-step="2"><rect x="240" y="150" width="160" height="44" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="320.0" y="170.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Relevance</text><text x="320.0" y="186.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">cosine similarity</text></g><g data-step="3"><rect x="460" y="80" width="180" height="56" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="550.0" y="106.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">score = sum</text><text x="550.0" y="122.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">each min-max scaled, weights 1</text></g><g data-step="4"><rect x="460" y="190" width="180" height="50" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="550.0" y="213.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Top memories</text><text x="550.0" y="229.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">that fit the window</text></g><g data-step="4"><text x="550.0" y="157.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">rank</text></g></svg><p class="readout dgcap"></p></div>

::: cards grid3
### [a] Write policy
What to store: decisions, user preferences, outcomes; not every token.

### [c] Compaction trigger
At a set fraction of the window, summarise and restart; keep the goal and open issues verbatim.

### [d] Forget policy
Expire, deduplicate and correct memories; contradictions must be resolved.
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

<div class="visual scroll-x"><table class="tbl"><tr><th>Choice</th><th>Benefit</th><th>Cost</th></tr><tr><td>Keep full history in context</td><td>nothing lost</td><td>context rot, cost grows every step</td></tr><tr><td>Compaction (summarise)</td><td>long tasks fit</td><td>details can be lost in the summary</td></tr><tr><td>Retrieval from a store</td><td>scales to large memories</td><td>retrieval misses; embedding and storage cost</td></tr><tr><td>Agent-managed memory (MemGPT-style)</td><td>model decides what to keep</td><td>extra tool calls; model may manage it badly</td></tr><tr><td>Just-in-time loading</td><td>only identifiers in context, data fetched when needed</td><td>more tool calls, latency</td></tr></table></div>

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

<div class="visual scroll-x"><table class="tbl"><tr><th>Failure</th><th>Symptom</th><th>Mitigation</th></tr><tr><td>Stale or contradictory memories</td><td>acts on outdated preferences</td><td>timestamps, update-in-place, conflict resolution</td></tr><tr><td>Lossy compaction</td><td>forgets a constraint after summarising</td><td>pin critical facts; test summaries</td></tr><tr><td>Memory poisoning</td><td>injected text persists and steers future sessions</td><td>validate what gets written; provenance</td></tr><tr><td>Cross-user leakage</td><td>one user's data appears for another</td><td>strict per-user/tenant isolation</td></tr><tr><td>Needle missed</td><td>fact in context but ignored</td><td>put key facts at the start or end; retrieve fewer, better items</td></tr></table></div>

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Privacy and deletion
Users must be able to see and delete memories; retention policies apply.

### [c] Multi-tenancy
Memory stores keyed and access-controlled per user and organisation.

### [b] Evaluate recall
Test that the right memory is retrieved and used, not just stored.

### [e] Cost
Embeddings, storage and longer prompts all cost money at scale.
:::

<!-- slide id="s-papers" from="papers" -->
