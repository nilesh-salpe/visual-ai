---
title: Experimentation for LLM Products
body:
  data-deck: Experimentation for LLM products
  data-home: ../index.html
  data-home-label: Operations
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
- ../../shared/diagram.js
intro:
  kicker: Visual Agents · Operations · 04
  h1: Experimentation for LLM and agent products
  sub: 'Shipping a new model, prompt or tool safely: from offline evals to shadow traffic to online controlled experiments, with guardrail metrics, honest statistics
    (no peeking), sample-ratio checks and variance reduction.'
  problem: 'A change that wins offline can still lower real task success, raise cost or latency, or annoy users: offline sets miss real traffic. And most ideas do
    not work: at Bing, "less than a third move the metrics they were designed to improve" when tested in controlled experiments.'
  core: 'Move every change up a <b>ladder</b>: offline evals, then <b>shadow traffic</b> (run on real requests, show nothing), then an <b>online controlled experiment</b>.
    Randomise <b>users</b> into arms, fix one <b>primary metric</b> (e.g. task success) and <b>guardrails</b> (cost per task, latency, safety, escalations), decide
    the <b>sample size</b> in advance or use <b>always-valid</b> sequential tests, check for <b>sample ratio mismatch</b>, reduce variance with pre-experiment data
    (<b>CUPED</b>), then ramp up. These are proven web-experimentation methods applied to LLM products.'
  hint: 'Previous: [Cost and latency](../03-cost-and-latency/index.html) · [All decks](../index.html)'
papers:
- kohavi_scale
- bing_third
- cuped
- always_valid
- srm
- interleaving
- errorbars
---

<!-- slide from="title" -->

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Offline wins are not online wins

::: cards grid3
### [d] Offline ≠ online
Eval sets are fixed and curated; real traffic has new intents, longer contexts and adversarial users.

### [b] Most ideas fail
At Bing, less than a third of ideas moved the metrics they were designed to improve; teams that skip experiments ship the other two thirds.

### [c] Small effects, noisy outputs
Real gains are often a point or two, and model outputs and costs vary from request to request.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Climb a ladder of evidence

::: cards grid2
### [f] Offline evals
Graded task suites and pass^k (Evaluating agents deck): cheap, repeatable, catch regressions before users see them.

### [a] Shadow traffic
Run the new version on copies of real requests and compare outputs, cost and latency without showing them to users.

### [c] Online controlled experiment
Randomly assign users to control or treatment; compare a pre-chosen primary metric and guardrails.

### [e] Ramp and hold out
Increase exposure stepwise (e.g. 1% → 10% → 50%); keep a small long-term holdout to measure lasting effects.
:::

<div class="visual"><div class="controls"><label class="ctl">baseline task success <input type="range" id="aP" min="5" max="95" step="1" value="50"> <output id="aPo"></output></label><label class="ctl">lift to detect <input type="range" id="aD" min="0.5" max="10" step="0.5" value="2"> <output id="aDo"></output></label></div><div class="bars"><div id="aBars"></div></div><p class="readout" id="aOut"></p></div>

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## The experimentation pipeline

::: diagram 660x300
nodes:
  ch: {at: [10, 120, 120, 56], text: Change, sub: model · prompt · tool, color: f, step: 1}
  'off': {at: [170, 20, 150, 56], text: Offline evals, sub: task suites · pass^k, color: b, step: 2}
  sh: {at: [170, 220, 150, 56], text: Shadow traffic, sub: 'real inputs, hidden', color: b, step: 3}
  as: {at: [370, 120, 140, 56], text: Assignment, sub: hash(user) → arm, color: a, step: 4}
  ar: {at: [550, 40, 100, 56], text: A / B arms, sub: pinned versions, color: c, step: 4}
  lg: {at: [550, 150, 100, 56], text: Logs, sub: events · cost, color: e, step: 5}
  an: {at: [370, 240, 280, 50], text: 'Analysis: SRM check · primary metric · guardrails', color: d, step: 6}
edges:
  - {from: ch, to: 'off', step: 2}
  - {from: ch, to: sh, step: 3}
  - {from: ch, to: as, label: passes, step: 4}
  - {from: as, to: ar, step: 4}
  - {from: ar, to: lg, step: 5}
  - {from: lg, to: an, step: 6}
steps:
  - 'A change: a new model version, prompt, tool, retrieval setting or routing rule.'
  - Offline evals catch regressions on known tasks before any user is exposed.
  - 'Shadow traffic runs the change on real requests and compares outputs, cost and latency without showing results.'
  - 'An assignment service hashes a stable user id into an arm, so each user sees one consistent version.'
  - 'Both arms log the same events: task outcome, tokens and cost, latency, safety flags, escalations to humans.'
  - 'Analysis first checks that the arms received the planned share of users (sample ratio), then tests the primary metric and the guardrails.'
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Honest analysis

::: diagram 660x300
nodes:
  srm: {at: [10, 20, 200, 56], text: Sample ratio check, sub: 'planned 50/50? χ² test', color: d, step: 1}
  pm: {at: [240, 20, 200, 56], text: Primary metric, sub: 'task success, pre-chosen', color: a, step: 2}
  gr: {at: [470, 20, 180, 56], text: Guardrails, sub: cost · latency · safety, color: b, step: 3}
  vr: {at: [240, 130, 200, 56], text: CUPED, sub: pre-period covariate, color: e, step: 4}
  seq: {at: [10, 130, 200, 56], text: Stopping rule, sub: fixed n or always-valid, color: c, step: 5}
  dec: {at: [470, 130, 180, 56], text: Decision, sub: ship · iterate · stop, color: f, step: 6}
  il: {at: [10, 235, 640, 56], text: 'Ranking and retrieval changes: interleave both rankers'' results for the same user', sub: a paired comparison within each user's results, color: c, step: 7}
edges:
  - {from: srm, to: pm, label: ok, step: 2}
  - {from: pm, to: gr, step: 3}
  - {from: vr, to: pm, label: less variance, step: 4, style: dash}
  - {from: seq, to: pm, step: 5, style: dash}
  - {from: gr, to: dec, step: 6}
steps:
  - 'Sample ratio mismatch (SRM): the observed split differs from the planned one. Like a fever, it is a symptom of data-quality problems (bots, logging loss, redirects); results are not trustworthy until it is explained.'
  - 'Test the one primary metric chosen before the experiment; secondary metrics are diagnostics, not decision criteria.'
  - 'Guardrails must not regress: an agent that succeeds 1 point more but costs 30% more per task may be a loss.'
  - CUPED subtracts the part of each user's metric predicted by their pre-experiment behaviour; with correlation ρ the variance shrinks by a factor of 1 − ρ² (about 50% at Bing).
  - 'Decide the sample size in advance, or use always-valid p-values: checking a fixed-horizon test repeatedly and stopping at the first significant result inflates false positives.'
  - 'Ship, iterate or stop based on the primary metric and guardrails together.'
  - 'For search and retrieval, interleaving merges both rankers'' results into one list and credits each click to the ranker that contributed the result: a paired online comparison, validated at scale on Yahoo! and Bing search and arXiv full-text search.'
:::



::: table
| Looks at an A/A test | Share declaring a "winner" |
|---|---|
| 1 (fixed horizon) | 4.6% |
| 5 | 13.2% |
| 20 | 24.8% |
| 50 | 30.8% |
:::



::: colab build-it/evals/05_experiments.ipynb
Compute users per arm for a task-success lift, and simulate how peeking at an A/A test inflates false positives (the table above comes from this notebook).
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

::: table
| Choice | Benefit | Cost |
|---|---|---|
| Randomise by user | consistent experience; independent units | fewer units than requests; slower to reach significance |
| Randomise by request | many units fast | users see both versions; carry-over effects in conversations |
| Fixed-horizon test | simple, standard statistics | no early stopping without inflating errors |
| Always-valid sequential test | monitor continuously and stop early safely | slightly less power at a fixed size |
| Shadow traffic first | catches cost and latency surprises with zero user risk | cannot measure user behaviour or satisfaction |
| LLM-judge metrics online | scores every conversation | judge bias; validate against human labels |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Peeking | many "wins" that vanish on re-test | fixed sample size or always-valid inference |
| Sample ratio mismatch | arms differ in size; results look too good or bad | SRM check on every analysis; find the root cause before reading metrics |
| Proxy metric moves, goal does not | thumbs-up rises while task completion falls | a primary metric tied to the real outcome; guardrails |
| Model version drift | a provider updates the model mid-test | pin model versions and prompts in the experiment config |
| Novelty effects | early lift fades over weeks | run long enough; long-term holdouts |
| Interference between arms | shared caches, rate limits or memory leak effects across arms | separate caches and quotas per arm |
:::

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Config, not code
Model, prompt, tools and routing live in versioned config that the assignment service selects per arm.

### [c] Many experiments at once
Bing ran over 200 concurrent experiments on any given day; that needs a platform for assignment, logging and analysis.

### [b] Cost is a metric
Track tokens and cost per completed task in every experiment, not only quality.

### [e] Review samples
Read real transcripts from both arms: numbers say what changed, transcripts say why.
:::

<!-- slide id="s-papers" from="papers" -->
