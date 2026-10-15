---
title: Model and Agent Routing
body:
  data-deck: Model and agent routing
  data-home: ../index.html
  data-home-label: Infrastructure
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
papers:
- bea
- routellm
- hybridllm
- frugalgpt
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Visual Agents · Infrastructure · 02</div>
    <h1>Model and agent routing</h1>
    <p class="sub">Sending each request to the cheapest model or the right specialised agent that can handle it: rule-based routing, learned routers that predict difficulty, and cascades that escalate only when needed.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>One model for everything is either too expensive (a frontier model answering "reset my password") or too weak (a small model failing hard questions). Agent systems also have specialists (support, coding, billing) and must pick one per request.</div>
      <div class="c"><b>Core idea</b>A <b>router</b> looks at each request and chooses a destination. <b>Rules or a classifier</b> route by intent to specialised prompts or agents (Anthropic's routing workflow). <b>Learned routers</b> predict whether a weak model is good enough (RouteLLM, Hybrid LLM). <b>Cascades</b> try the cheap model first and escalate when a scorer rejects the answer (FrugalGPT).</div>
    </div>
    <div class="toc" data-auto></div>
    <p class="start-hint">Previous: <a href="../01-llm-gateway/index.html">LLM gateway</a> · Next: <a href="../03-access-control/index.html">Identity and access control →</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## One model does not fit every request

::: cards grid3
### [d] Overpaying
Most traffic is easy; a frontier model on every request burns budget and latency.

### [b] Underpowering
A small model on everything fails the hard tail, which is often the valuable part.

### [c] Specialists
Separate prompts, tools and agents per intent work better than one prompt that does everything.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Choose the destination per request

::: cards grid3
### [a] Intent routing
Classify the input and send it to a specialised follow-up: Anthropic's routing workflow, e.g. easy questions to a small model, hard ones to a larger one.

### [c] Learned routers
Predict from the query alone whether the weak model will do: RouteLLM trains on human preference data (over 2× cheaper in some cases at the same quality); Hybrid LLM makes up to 40% fewer large-model calls with no quality drop.

### [e] Cascades
Call the cheap model, score its answer, escalate if rejected: FrugalGPT matches GPT-4 with up to 98% lower cost on its benchmarks.
:::

<div class="visual"><div class="controls" style="margin-top:0"><label class="ctl">easy share <input type="range" id="rP" min="0" max="100" step="5" value="70"> <output id="rPo"></output></label><label class="ctl">small / large price <input type="range" id="rR" min="1" max="60" step="1" value="10"> <output id="rRo"></output></label><label class="ctl">scorer false rejects <input type="range" id="rE" min="0" max="50" step="5" value="10"> <output id="rEo"></output></label></div><div id="rBars" style="margin-top:12px"></div><p class="readout" id="rOut"></p></div>

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## Routing in an agent system

<div class="visual dgm" data-steps="[&quot;A request (or one step of an agent&#x27;s loop) arrives.&quot;, &quot;The router decides: hand-written rules, a trained classifier, or a small LLM asked to classify.&quot;, &quot;Model routing: the same task can go to a cheap or a strong model depending on predicted difficulty.&quot;, &quot;Agent routing: different intents go to different specialised agents with their own prompts and tools.&quot;, &quot;Log every decision with its outcome; the log becomes training and evaluation data for the router.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 300" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah3" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="122.0" y1="148.0" x2="166.0" y2="148.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah3)"/></g><g data-step="3"><line x1="322.0" y1="118.0" x2="460.6" y2="64.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah3)"/></g><g data-step="3"><line x1="322.0" y1="141.9" x2="416.0" y2="134.4" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah3)"/></g><g data-step="4"><line x1="322.0" y1="165.8" x2="416.0" y2="187.5" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah3)"/></g><g data-step="5"><line x1="245.0" y1="188.0" x2="245.0" y2="236.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah3)"/></g><g data-step="5"><line x1="235.0" y1="238.0" x2="235.0" y2="190.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah3)"/></g><g data-step="1"><rect x="10" y="120" width="110" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="65.0" y="153.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Request</text></g><g data-step="2"><rect x="170" y="110" width="150" height="76" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="245.0" y="146.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Router</text><text x="245.0" y="162.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">rules · classifier · LLM</text></g><g data-step="3"><rect x="420" y="10" width="230" height="50" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="535.0" y="33.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Small model</text><text x="535.0" y="49.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">FAQ, extraction, simple steps</text></g><g data-step="3"><rect x="420" y="100" width="230" height="50" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="535.0" y="123.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Large model</text><text x="535.0" y="139.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">hard reasoning</text></g><g data-step="4"><rect x="420" y="190" width="230" height="50" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="535.0" y="213.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Specialist agents</text><text x="535.0" y="229.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">support · code · billing</text></g><g data-step="5"><rect x="170" y="240" width="150" height="50" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="245.0" y="263.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Outcome log</text><text x="245.0" y="279.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">quality · cost</text></g><g data-step="4"><text x="369.0" y="171.6" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">by intent</text></g><g data-step="5"><text x="245.0" y="207.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">decisions</text></g><g data-step="5"><text x="235.0" y="229.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">retrain</text></g></svg><p class="readout dgcap"></p></div>

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Learned router vs cascade

<div class="visual dgm" data-steps="[&quot;Router: a model (RouteLLM trains several, including a BERT classifier and matrix factorisation, on preference data) predicts from the query whether the weak model&#x27;s answer will be good enough.&quot;, &quot;A threshold on that probability sets the cost-quality trade-off; Hybrid LLM tunes the desired quality level at test time. Below the threshold the strong model gets the query.&quot;, &quot;Cascade: always call the cheapest model first.&quot;, &quot;A scorer (a small trained model in FrugalGPT, or an LLM judge, or the model&#x27;s own confidence) grades the answer.&quot;, &quot;Accept good answers; escalate the rest to the next, larger model. Cascades pay the small call on every request but see the answer before deciding.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 250" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah4" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="1"><line x1="122.0" y1="48.0" x2="156.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah4)"/></g><g data-step="2"><line x1="322.0" y1="48.0" x2="356.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah4)"/></g><g data-step="2"><line x1="492.0" y1="48.0" x2="526.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah4)"/></g><g data-step="4"><line x1="122.0" y1="198.0" x2="156.0" y2="198.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah4)"/></g><g data-step="5"><line x1="322.0" y1="198.0" x2="356.0" y2="198.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah4)"/></g><g data-step="5"><line x1="492.0" y1="198.0" x2="526.0" y2="198.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah4)"/></g><g data-step="1"><rect x="10" y="20" width="110" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="65.0" y="53.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Query</text></g><g data-step="1"><rect x="160" y="20" width="160" height="56" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="240.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Router model</text><text x="240.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">P(weak model is enough)</text></g><g data-step="2"><rect x="360" y="20" width="130" height="56" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="425.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Threshold</text><text x="425.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">cost-quality knob</text></g><g data-step="2"><rect x="530" y="20" width="120" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="590.0" y="53.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Weak model</text></g><g data-step="3"><rect x="10" y="170" width="110" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="65.0" y="196.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Small model</text><text x="65.0" y="212.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">answers first</text></g><g data-step="4"><rect x="160" y="170" width="160" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="240.0" y="196.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Scorer</text><text x="240.0" y="212.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">judge · confidence</text></g><g data-step="5"><rect x="360" y="170" width="130" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="425.0" y="196.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Accept</text><text x="425.0" y="212.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">return answer</text></g><g data-step="5"><rect x="530" y="170" width="120" height="56" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="590.0" y="196.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Large model</text><text x="590.0" y="212.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">escalation</text></g><g data-step="2"><text x="509.0" y="43.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">above</text></g><g data-step="4"><text x="139.0" y="193.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">answer</text></g><g data-step="5"><text x="339.0" y="193.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">pass</text></g><g data-step="5"><text x="509.0" y="193.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">else</text></g></svg><p class="readout dgcap"></p></div>

<div class="visual scroll-x"><table class="tbl"><tr><th>Router input</th><th>Router output</th><th>Decision cost</th></tr><tr><td>query text only (RouteLLM, Hybrid LLM)</td><td>which model to call</td><td>one cheap classifier call</td></tr><tr><td>query + small model's answer (FrugalGPT cascade)</td><td>accept or escalate</td><td>a full small-model call per request</td></tr><tr><td>intent label (rules / LLM classifier)</td><td>which specialist prompt or agent</td><td>a regex or one small LLM call</td></tr></table></div>

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

<div class="visual scroll-x"><table class="tbl"><tr><th>Approach</th><th>Benefit</th><th>Cost</th></tr><tr><td>Rules / keywords</td><td>transparent, zero latency</td><td>brittle; misses phrasing it did not foresee</td></tr><tr><td>Trained classifier</td><td>cheap, fast, tunable threshold</td><td>needs labelled or preference data; drifts with traffic</td></tr><tr><td>LLM as router</td><td>handles open-ended intents</td><td>adds a model call of latency and cost</td></tr><tr><td>Cascade</td><td>decides with the answer in hand</td><td>small-model latency added to every escalated request</td></tr><tr><td>Routing inside an agent loop</td><td>cheap model for easy steps</td><td>switching models loses the prompt cache, which belongs to one model</td></tr></table></div>

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

<div class="visual scroll-x"><table class="tbl"><tr><th>Failure</th><th>Symptom</th><th>Mitigation</th></tr><tr><td>Hard queries sent to the weak model</td><td>quality drops quietly on the tail</td><td>conservative threshold; monitor quality per route</td></tr><tr><td>Scorer fooled by fluent wrong answers</td><td>confident errors pass the cascade</td><td>verifiable checks where possible (tests, schemas); calibrate the scorer</td></tr><tr><td>Traffic drift</td><td>router accuracy decays after a launch</td><td>retrain on logged outcomes; shadow-evaluate new routers</td></tr><tr><td>Specialist mismatch</td><td>billing question lands in the coding agent</td><td>a fallback "general" route; let agents hand back</td></tr><tr><td>Format differences</td><td>models differ in tool-call behaviour</td><td>evaluate every destination on the same tool tasks</td></tr></table></div>

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Measure the curve
Evaluate cost vs quality at several thresholds offline before choosing one.

### [c] Shadow traffic
Run a new router in parallel, compare decisions and outcomes, then switch.

### [b] Default to strong
When the router is unsure or fails, send to the strong model.

### [e] Route at the gateway
Implement routing in the LLM gateway so every app benefits and decisions are logged in one place.
:::

<!-- slide id="s-papers" from="papers" -->
