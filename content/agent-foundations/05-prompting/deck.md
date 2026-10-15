---
title: Prompting and In-Context Learning
body:
  data-deck: Prompting and in-context learning
  data-home: ../index.html
  data-home-label: Foundations
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
- ../../shared/diagram.js
intro:
  kicker: Visual Agents · Foundations · 05
  h1: Prompting and in-context learning
  sub: 'How a model learns a task from its prompt alone: what in-context examples really teach, the biases that make few-shot prompts unstable, how to structure a
    prompt (role, documents, instructions, examples, query), many-shot prompting, and optimising prompts against an eval set.'
  problem: The same model gives very different results depending on wording, the examples chosen and even their order. In an agent the system prompt, tool descriptions
    and examples are the program, yet they are often edited by hand and never tested.
  core: '<b>In-context learning</b>: the model infers the task from instructions and examples in the prompt, with no weight updates. Examples mostly teach the <b>format,
    the label space and the input distribution</b>, not new facts. Write prompts like a brief for a capable new colleague: <b>role and reasons</b>, long documents
    <b>first</b>, numbered <b>instructions</b>, <b>3 to 5 varied examples</b> in tags, the <b>query last</b>, and a <b>schema</b> for the output. Then treat the prompt
    as code: version it, test it on an eval set, and optimise it.'
  hint: 'Previous: [Planning and task decomposition](../04-planning/index.html) · [All decks](../index.html)'
papers:
- gpt3
- min_demos
- calibrate
- order_sens
- sclar
- manyshot_icl
- dspy
- opro
- claude_prompting
- context_eng
status:
  label: current
  reviewed: '2026-10-15'
  note: Written from primary sources 2026-10-15; prompting guidance from the Claude docs on that date.
---

<!-- slide from="title" -->

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## The same task, very different results

::: cards grid3
### [d] Unstable few-shot prompts
Zhao et al.: the prompt format, the choice of training examples and even their order moved GPT-3 from near chance to near state of the art.

### [b] Systematic biases
Models favour answers that are frequent among the examples (majority label bias), that appear last (recency bias), or are common in pretraining (common token bias).

### [c] Formatting alone
Sclar et al.: semantically equivalent formats (separators, casing, spacing) changed accuracy by up to 76 points for LLaMA-2-13B.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Examples teach the format; instructions teach the goal

::: cards grid2
### [f] In-context learning
GPT-3 showed that large models can perform a new task from a few input-output pairs in the prompt, with no gradient updates, and that larger models use those examples more efficiently.

### [a] What examples carry
Min et al.: replacing the gold labels in demonstrations with random labels cost only 0 to 5% absolute on classification and multiple choice. The label space, the input distribution and the format mattered far more.

### [b] Instructions with reasons
Explain why a rule exists ("read aloud by a text-to-speech engine, so never use ellipses") and say what to do rather than what not to do; the model generalises from the reason (Claude docs).

### [e] Many-shot
With long contexts, hundreds or thousands of examples can override pretraining biases and perform comparably to fine-tuning on some tasks (Agarwal et al. 2024); model-generated rationales can stand in for scarce human ones.
:::

Calibration helps too: Zhao et al. estimate the model's bias from a content-free input such as "N/A" and correct for it, improving GPT-3 and GPT-2 accuracy by up to 30.0% absolute.

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## Anatomy of a prompt

::: diagram 660x280
nodes:
  sys: {at: [10, 10, 250, 44], text: System prompt, sub: role · goal · rules with reasons, color: f, step: 1}
  tl: {at: [10, 62, 250, 44], text: Tool definitions, sub: names · descriptions · schemas, color: f, step: 1}
  dc: {at: [10, 114, 250, 44], text: Long documents, sub: placed near the top, color: c, step: 2}
  ex: {at: [10, 166, 250, 44], text: Instructions and examples, sub: numbered steps · 3–5 tagged examples, color: b, step: 3}
  q: {at: [10, 218, 250, 44], text: Query, sub: last in the prompt, color: a, step: 4}
  m: {at: [330, 211, 130, 56], text: Model, color: e, step: 5}
  out: {at: [500, 211, 150, 56], text: Output, sub: schema-validated, color: e, step: 5}
  ev: {at: [500, 40, 150, 56], text: Eval set, sub: test cases + grader, color: d, step: 6}
edges:
  - {from: sys, to: tl, step: 1}
  - {from: tl, to: dc, step: 2}
  - {from: dc, to: ex, step: 3}
  - {from: ex, to: q, step: 4}
  - {from: q, to: m, step: 5}
  - {from: m, to: out, step: 5}
  - {from: out, to: ev, label: score, step: 6, style: dash}
  - {from: ev, to: sys, label: revise, step: 6, style: back}
steps:
  - 'The stable part first: the role, the goal and rules with their reasons, then tool definitions. Keeping it identical across requests also makes it cacheable.'
  - 'Long documents (20K+ tokens) go near the top, above the instructions and the question: the Claude docs report queries at the end can improve response quality by up to 30% on complex, multi-document inputs.'
  - 'Numbered instructions, then 3 to 5 examples that are relevant, varied and wrapped in tags so they cannot be mistaken for instructions.'
  - The specific question or input comes last.
  - 'For machine-read output, constrain it with a schema (structured outputs, or a tool with an enum of valid labels) rather than hoping for the format.'
  - Every prompt change is scored on an eval set before it ships; failures drive the next revision.
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## A prompt, written out

::: code
[system]
You triage Acme billing tickets.
Each goes to a human queue, and a
wrong queue delays refunds by days,
so answer "unsure" if no label fits.

[user]
<documents>
 <document index="1">
  <source>refunds.md</source>
  <document_content>
  ...
  </document_content>
 </document>
</documents>

<instructions>
1. Read the ticket.
2. Pick one label: refund,
   invoice, fraud or unsure.
3. Quote the sentence that
   decided it.
</instructions>

<examples>
 <example>
  <ticket>Charged twice in May.
  </ticket>
  <label>refund</label>
 </example>
 ... 3 to 5 varied examples,
 balanced across labels,
 in shuffled order ...
</examples>

<ticket>{ticket_text}</ticket>
:::



::: table
| Technique | Use it for | Evidence |
|---|---|---|
| XML tags around documents, examples, inputs | unambiguous structure | Claude docs: tags help parse complex prompts |
| Balanced, shuffled examples | avoiding majority-label and recency bias | Zhao et al. 2021; Lu et al. 2022 (order alone spans near state of the art to chance) |
| Quote first, then answer | grounding answers in long documents | Claude docs; see Hallucination and factuality in Evals |
| Structured outputs or an enum tool | classification and JSON outputs | Claude docs: the replacement for prefilled responses |
| Prefilling the assistant turn [[legacy]] | forcing a format by starting the answer | returns a 400 error on Claude 4.6 models and later |
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

::: table
| Choice | Benefit | Cost |
|---|---|---|
| Zero-shot instructions | short prompt; no examples to maintain | the format and edge cases are left to the model |
| Few-shot (3 to 5 examples) | reliable format, tone and label space | example bias; extra tokens on every call |
| Many-shot (hundreds of examples) | can rival fine-tuning, no training run | long, costly prompts unless cached; curation effort |
| Fine-tuning instead | short prompts; behaviour built in | training pipeline; stale when the task changes (RAG vs fine-tuning deck) |
| Hand-written prompts | fast to start, readable | brittle; no evidence a change helped |
| Optimised prompts (DSPy, OPRO) | measured gains: DSPy beat standard few-shot by over 25% (GPT-3.5); OPRO up to 8% on GSM8K | needs an eval set and a metric; can overfit it |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Example bias | answers drift to the label most frequent or last in the examples | balance labels; shuffle order; calibrate |
| Examples copied too literally | outputs mimic an example's wording or length | vary the examples; state that they are illustrations |
| Format sensitivity | accuracy moves with a separator or casing change | test several formats; report the spread, not the best one |
| Unexplained rules | the model follows the letter and misses the intent | give the reason for each rule |
| Model upgrade regressions | a prompt tuned for one model misbehaves on the next | pin model versions; rerun the eval set on every upgrade |
| Untrusted text in the prompt | retrieved pages or tool results contain instructions | separate data from instructions with tags; treat it as data (Safety and reliability deck) |
:::

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Prompts are code
Keep them in version control with tests; review changes; log the prompt version with every request.

### [c] Evals gate changes
A fixed set of real cases with graders; every prompt or model change runs against it (Evaluating agents deck).

### [b] Cache the stable prefix
System prompt, tools and documents rarely change; keep them first and byte-identical so prompt caching applies.

### [e] Re-tune per model
Guidance changes between model generations (for example, prefill removal); read the provider's current prompting guide when you upgrade.
:::

<!-- slide id="s-papers" from="papers" -->
