---
title: Jailbreaks and Adversarial Robustness
body:
  data-deck: Jailbreaks and adversarial robustness
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
  kicker: Visual Agents · Operations · 05
  h1: Jailbreaks and adversarial robustness
  sub: 'How users get a model to do what its safety training forbids: why jailbreaks work, the main automated attack families (optimised suffixes, attacker LLMs,
    many-shot, best-of-N), and the layered defences used in production: safety training, input and output classifiers, monitoring and red teaming.'
  problem: Safety training teaches a model to refuse harmful requests, but attackers rephrase, encode, role-play, pack hundreds of fake dialogues into the context,
    or simply retry random variations until one gets through. Every deployed model faces this, and agents with tools raise the stakes.
  core: 'Treat robustness as a property of the <b>whole system</b>, not of the model alone. Jailbreaks exploit <b>competing objectives</b> (being helpful vs being
    safe) and <b>mismatched generalization</b> (safety training did not cover a format the model still understands). Defend in layers: a <b>safety-trained model</b>,
    <b>input and output classifiers</b> trained from a written policy, <b>monitoring</b> across requests and accounts, and continuous <b>red teaming</b>. Measure
    attack success at a stated attacker budget, together with the false-refusal rate on real traffic.'
  hint: 'Previous: [Experimentation for LLM products](../04-experimentation/index.html) · [All decks](../index.html)'
papers:
- jailbroken
- gcg
- pair
- manyshot_jb
- bon_jb
- const_classifiers
- asl3
- llamaguard
- circuit_breakers
- harmbench
- jailbreakbench
- owasp_llm
status:
  label: current
  reviewed: '2026-10-15'
  note: Written from primary sources 2026-10-15; layered classifier defences are in production (Anthropic ASL-3, Llama Guard).
---

<!-- slide from="title" -->

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Refusals can be talked around

::: cards grid3
### [d] Learned, not enforced
Wei et al.: attacks designed from two failure modes succeeded on every prompt in a curated set of unsafe requests against GPT-4 and Claude v1.3, and on over 96% of all prompts evaluated (2023).

### [b] Automated attacks
GCG finds an adversarial suffix by gradient-guided search on open models that transferred to GPT-3.5 and GPT-4 (up to 84%) and PaLM-2 (66%), much less to Claude (2.1%). PAIR uses an attacker LLM and often needs fewer than 20 queries.

### [c] Retries add up
Best-of-N: resample random variations of a prompt (shuffled, re-capitalised) until one works: 89% on GPT-4o and 78% on Claude 3.5 Sonnet with 10,000 samples, with success following a power law in N.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Why jailbreaks work, and what each family exploits

::: table
| Attack family | Published example | What it exploits | Main defence |
|---|---|---|---|
| Role-play and persuasion | PAIR (attacker LLM refines a scenario) | competing objectives: helpfulness vs safety | safety training; output classifier |
| Encoding and obfuscation | Base64 inputs; random capitalisation (Best-of-N) | mismatched generalization: the model understands a format safety training missed | classifiers that judge meaning, not surface form |
| Optimised suffixes | GCG | brittle refusal behaviour under adversarial tokens | output classifier; adversarial training |
| Many-shot | hundreds of faux dialogues in one prompt (up to 256 tested) | in-context learning, which grows with context length | classifying and modifying the prompt (61% → 2% success in one case) |
| Multi-turn decomposition | splitting a task into individually harmless steps | checks that look at one request at a time | conversation- and account-level monitoring |
:::

A **jailbreak** is the user attacking the model's policy. **Prompt injection** is third-party content (a web page, a tool result) hijacking an agent; it is covered in Safety and reliability. OWASP lists both under prompt injection (LLM01).

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## Layered defence

::: diagram 660x300
nodes:
  u: {at: [10, 120, 90, 56], text: Request, sub: user · account, color: f, step: 1}
  ic: {at: [125, 120, 115, 56], text: Input classifier, sub: policy · intent, color: b, step: 2}
  m: {at: [265, 120, 115, 56], text: Model, sub: safety-trained, color: a, step: 3}
  oc: {at: [405, 120, 115, 56], text: Output classifier, sub: streaming · can halt, color: b, step: 4}
  out: {at: [545, 120, 105, 56], text: Reply, color: e, step: 4}
  mon: {at: [125, 235, 255, 50], text: Account monitoring, sub: patterns across requests · rate limits, color: c, step: 5}
  rt: {at: [125, 20, 255, 56], text: Red teaming, sub: automated attacks + human testers, color: d, step: 6}
edges:
  - {from: u, to: ic, step: 2}
  - {from: ic, to: m, step: 3}
  - {from: m, to: oc, step: 4}
  - {from: oc, to: out, step: 4}
  - {from: ic, to: mon, label: signals, step: 5, style: dash}
  - {from: oc, to: mon, step: 5, style: dash}
  - {from: rt, to: ic, label: new attacks, step: 6, style: dash}
  - {from: rt, to: oc, label: training data, step: 6, style: dash}
steps:
  - A request arrives tied to a user and an account.
  - 'An input classifier screens the prompt against a written policy, judging what is being asked for, not how it is phrased.'
  - 'The model itself is safety-trained to refuse, the first line but not the only one.'
  - An output classifier scores the response as it streams and can stop it mid-generation; blocking harmful output works even when the prompt looked harmless.
  - 'Classifier signals and request patterns feed account-level monitoring and rate limits, which catch repeated attempts and multi-turn decomposition.'
  - 'Red teaming (automated attacks such as PAIR and Best-of-N, plus human testers and bug bounties) finds new attacks; they become training data for the classifiers, which retrain faster than the model.'
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Constitutional classifiers

::: diagram 660x300
nodes:
  co: {at: [10, 20, 150, 56], text: Constitution, sub: allowed · restricted, color: f, step: 1}
  gen: {at: [190, 20, 150, 56], text: Synthetic data, sub: LLM-written examples, color: c, step: 2}
  aug: {at: [370, 20, 140, 56], text: Augment, sub: languages · styles, color: c, step: 2}
  icl: {at: [190, 130, 150, 56], text: Input classifier, sub: whole prompt, color: b, step: 3}
  ocl: {at: [370, 130, 140, 56], text: Output classifier, sub: token by token, color: b, step: 3}
  ev: {at: [190, 235, 320, 50], text: Evaluate, sub: human red teaming · automated attacks · production traffic, color: d, step: 4}
edges:
  - {from: co, to: gen, step: 2}
  - {from: gen, to: aug, step: 2}
  - {from: aug, to: icl, step: 3}
  - {from: aug, to: ocl, step: 3}
  - {from: icl, to: ev, step: 4, style: dash}
  - {from: ocl, to: ev, step: 4}
steps:
  - Write natural-language rules (a constitution) for what is permitted and what is restricted.
  - 'Prompt an LLM to generate many harmful and harmless prompts and completions from the rules, then augment them (translations, known jailbreak styles).'
  - Train an input classifier on whole prompts and a streaming output classifier that scores each token prefix and can halt generation.
  - 'Evaluate with human red teaming and production traffic: over 3,000 estimated hours of red teaming found no universal jailbreak; automated jailbreak success fell from 86% to under 5%; refusals on production traffic rose by 0.38% absolute; inference overhead 23.7%.'
:::

<div class="visual"><div class="controls"><label class="ctl">success per attempt (log₁₀) <input type="range" id="jbP" min="-5" max="-1" step="0.1" value="-3"> <output id="jbPo"></output></label><label class="ctl">classifier catch rate <input type="range" id="jbC" min="0" max="99.9" step="0.1" value="95"> <output id="jbCo"></output></label><label class="ctl">attempts (log₁₀) <input type="range" id="jbN" min="0" max="5" step="0.1" value="3"> <output id="jbNo"></output></label></div><div class="bars"><div id="jbBars"></div></div><p class="readout" id="jbOut"></p></div>

The calculator treats attempts as independent, a simplification: Best-of-N measured a power law, which grows more slowly than independent retries but keeps rising with N.

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

::: table
| Defence | Strength | Cost |
|---|---|---|
| Safety training (refusals) | no extra latency; handles most plain requests | can be argued around; too much causes over-refusal |
| Input and output classifiers [[current]] | robust to many styles; retrain quickly; output check catches harmless-looking prompts | compute overhead (23.7% in the paper); false positives (+0.38% refusals) |
| Adversarial training on known attacks | closes specific holes | attack-specific; may not generalise to new attacks |
| Circuit breakers (representation rerouting) [[research]] | targets the internal representations of harmful output, attack-agnostic | research-stage; Best-of-N still circumvented them |
| Account monitoring and rate limits | catches retries and multi-turn attacks | needs identity; privacy and false-alarm handling |
| Restricting risky features | removes an attack surface (for example very long faux-dialogue prompts) | can block legitimate uses |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Universal jailbreak shared publicly | one template works across many harmful requests | bug bounties, threat intelligence, fast classifier updates |
| Single-attempt evaluation | reported robustness collapses under retries | report attack success at a stated budget N; use HarmBench or JailbreakBench plus your own policy |
| Over-refusal | legitimate users blocked; complaints rise | measure false refusals on real traffic alongside attack success |
| Obfuscated inputs | encodings and odd formatting slip past filters | classify meaning; check outputs, not only inputs |
| Harm split across turns | each turn looks harmless | conversation-level classifiers; account monitoring |
| Jailbroken agent with tools | harmful actions, not just text | least-privilege tools, approvals for risky actions (Safety and reliability deck) |
:::

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Defence in depth
No single layer is enough: Anthropic's AI Safety Level 3 (ASL-3) deployment combines real-time constitutional classifiers, a bug bounty, offline monitoring and threat intelligence.

### [c] Write the policy first
Classifiers, red-team tasks and evals all derive from a written statement of what is allowed and what is not.

### [b] Measure both errors
Attack success at a budget, and false refusals on real traffic; a defence that blocks users is not a win.

### [e] Iterate fast
Classifiers can be retrained in days from new red-team findings; model retraining takes much longer.
:::

<!-- slide id="s-papers" from="papers" -->
