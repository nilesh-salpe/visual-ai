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
- ../../shared/diagram.js
intro:
  kicker: Visual Agents · Infrastructure · 02
  h1: Model and agent routing
  sub: 'Sending each request to the cheapest model or the right specialised agent that can handle it: rule-based routing, learned routers that predict difficulty,
    and cascades that escalate only when needed.'
  problem: One model for everything is either too expensive (a frontier model answering "reset my password") or too weak (a small model failing hard questions). Agent
    systems also have specialists (support, coding, billing) and must pick one per request.
  core: A <b>router</b> looks at each request and chooses a destination. <b>Rules or a classifier</b> route by intent to specialised prompts or agents (Anthropic's
    routing workflow). <b>Learned routers</b> predict whether a weak model is good enough (RouteLLM, Hybrid LLM). <b>Cascades</b> try the cheap model first and escalate
    when a scorer rejects the answer (FrugalGPT).
  hint: 'Previous: [LLM gateway](../01-llm-gateway/index.html) · Next: [Identity and access control →](../03-access-control/index.html) · [All decks](../index.html)'
papers:
- bea
- routellm
- hybridllm
- frugalgpt
---

<!-- slide from="title" -->

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

<div class="visual"><div class="controls"><label class="ctl">easy share <input type="range" id="rP" min="0" max="100" step="5" value="70"> <output id="rPo"></output></label><label class="ctl">small / large price <input type="range" id="rR" min="1" max="60" step="1" value="10"> <output id="rRo"></output></label><label class="ctl">scorer false rejects <input type="range" id="rE" min="0" max="50" step="5" value="10"> <output id="rEo"></output></label></div><div class="bars"><div id="rBars"></div></div><p class="readout" id="rOut"></p></div>

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## Routing in an agent system

::: diagram 660x300
nodes:
  rq: {at: [10, 120, 110, 56], text: Request, color: f, step: 1}
  rt: {at: [170, 110, 150, 76], text: Router, sub: rules · classifier · LLM, color: a, step: 2}
  sm: {at: [420, 10, 230, 50], text: Small model, sub: 'FAQ, extraction, simple steps', color: e, step: 3}
  lg: {at: [420, 100, 230, 50], text: Large model, sub: hard reasoning, color: d, step: 3}
  sa: {at: [420, 190, 230, 50], text: Specialist agents, sub: support · code · billing, color: c, step: 4}
  ev: {at: [170, 240, 150, 50], text: Outcome log, sub: quality · cost, color: b, step: 5}
edges:
  - {from: rq, to: rt, step: 2}
  - {from: rt, to: sm, step: 3}
  - {from: rt, to: lg, step: 3}
  - {from: rt, to: sa, label: by intent, step: 4}
  - {from: rt, to: ev, label: decisions, step: 5, style: dash}
  - {from: ev, to: rt, label: retrain, step: 5, style: back}
steps:
  - A request (or one step of an agent's loop) arrives.
  - 'The router decides: hand-written rules, a trained classifier, or a small LLM asked to classify.'
  - 'Model routing: the same task can go to a cheap or a strong model depending on predicted difficulty.'
  - 'Agent routing: different intents go to different specialised agents with their own prompts and tools.'
  - Log every decision with its outcome; the log becomes training and evaluation data for the router.
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Learned router vs cascade

::: diagram 660x250
nodes:
  q: {at: [10, 20, 110, 56], text: Query, color: f, step: 1}
  cl: {at: [160, 20, 160, 56], text: Router model, sub: P(weak model is enough), color: a, step: 1}
  th: {at: [360, 20, 130, 56], text: Threshold, sub: cost-quality knob, color: d, step: 2}
  w: {at: [530, 20, 120, 56], text: Weak model, color: e, step: 2}
  s1: {at: [10, 170, 110, 56], text: Small model, sub: answers first, color: e, step: 3}
  sc: {at: [160, 170, 160, 56], text: Scorer, sub: judge · confidence, color: b, step: 4}
  ok: {at: [360, 170, 130, 56], text: Accept, sub: return answer, color: e, step: 5}
  big: {at: [530, 170, 120, 56], text: Large model, sub: escalation, color: d, step: 5}
edges:
  - {from: q, to: cl, step: 1}
  - {from: cl, to: th, step: 2}
  - {from: th, to: w, label: above, step: 2}
  - {from: s1, to: sc, label: answer, step: 4}
  - {from: sc, to: ok, label: pass, step: 5}
  - {from: ok, to: big, label: else, step: 5, style: dash}
steps:
  - 'Router: a model (RouteLLM trains several, including a BERT classifier and matrix factorisation, on preference data) predicts from the query whether the weak model''s answer will be good enough.'
  - A threshold on that probability sets the cost-quality trade-off; Hybrid LLM tunes the desired quality level at test time. Below the threshold the strong model gets the query.
  - 'Cascade: always call the cheapest model first.'
  - 'A scorer (a small trained model in FrugalGPT, or an LLM judge, or the model''s own confidence) grades the answer.'
  - 'Accept good answers; escalate the rest to the next, larger model. Cascades pay the small call on every request but see the answer before deciding.'
:::



::: table
| Router input | Router output | Decision cost |
|---|---|---|
| query text only (RouteLLM, Hybrid LLM) | which model to call | one cheap classifier call |
| query + small model's answer (FrugalGPT cascade) | accept or escalate | a full small-model call per request |
| intent label (rules / LLM classifier) | which specialist prompt or agent | a regex or one small LLM call |
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

::: table
| Approach | Benefit | Cost |
|---|---|---|
| Rules / keywords | transparent, zero latency | brittle; misses phrasing it did not foresee |
| Trained classifier | cheap, fast, tunable threshold | needs labelled or preference data; drifts with traffic |
| LLM as router | handles open-ended intents | adds a model call of latency and cost |
| Cascade | decides with the answer in hand | small-model latency added to every escalated request |
| Routing inside an agent loop | cheap model for easy steps | switching models loses the prompt cache, which belongs to one model |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Hard queries sent to the weak model | quality drops quietly on the tail | conservative threshold; monitor quality per route |
| Scorer fooled by fluent wrong answers | confident errors pass the cascade | verifiable checks where possible (tests, schemas); calibrate the scorer |
| Traffic drift | router accuracy decays after a launch | retrain on logged outcomes; shadow-evaluate new routers |
| Specialist mismatch | billing question lands in the coding agent | a fallback "general" route; let agents hand back |
| Format differences | models differ in tool-call behaviour | evaluate every destination on the same tool tasks |
:::

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
