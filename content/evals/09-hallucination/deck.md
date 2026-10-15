---
title: Hallucination and Factuality
body:
  data-deck: Hallucination and factuality
  data-home: ../index.html
  data-home-label: Evals
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'rare fact :: seen once in training :: f'
  - 'guess :: plausible but wrong :: d'
  - 'graded 0 or 1 :: guessing beats abstaining :: b'
  - 'measure :: correct · wrong · abstained :: a'
  - 'reduce :: ground · verify · reward abstention :: e'
  caption: Hallucinations start as prediction errors on rare facts and survive because grading rewards guessing.
example:
  title: 'Worked example: grading with a confidence target'
  setup: 'A model is 40% sure of an answer. The benchmark either gives 1 point for a correct answer and 0 otherwise, or states a confidence target t = 0.75 as Kalai
    et al. propose: "answer only if you are more than 75% confident; mistakes cost t/(1 − t) = 3 points".'
  steps:
  - 'Binary grading: guessing earns 0.4 × 1 = 0.4 expected points; "I don''t know" earns 0. Guessing wins at any confidence above zero.'
  - 'With the stated penalty: guessing earns 0.4 × 1 − 0.6 × 3 = <b>−1.4</b>; abstaining earns 0. Abstaining wins.'
  - 'Break-even: p − (1 − p) · t/(1 − t) = 0 gives p = t, so the model should answer exactly when its confidence is above 0.75.'
  - The same rule (answer if p &gt; t) is optimal for every t, so one well-calibrated model can follow whatever target the prompt states.
  result: Binary scoring makes guessing optimal; a stated penalty makes abstaining optimal below the confidence target.
traps:
  tricks:
  - 'Report three numbers. :: Correct, incorrect and not attempted (SimpleQA); accuracy alone hides confident errors.'
  - 'Score long answers by atomic facts. :: FActScore: the share of atomic facts in a generation that a knowledge source supports.'
  - 'Sample disagreement is a free detector. :: Facts the model knows come out the same across samples; invented ones vary (SelfCheckGPT, semantic entropy).'
  traps:
  - 'Treating retrieval as a cure. :: Search-augmented PerplexityAI scored 71.5% on FActScore: 28.5% of its atomic facts were still unsupported.'
  - 'Penalising "I don''t know". :: Binary-graded leaderboards reward guessing, so optimising for them trains models to bluff.'
  - 'Fine-tuning on facts the model does not know. :: Gekhman et al.: such examples are learned slowly and, once learned, linearly increase hallucination.'
papers:
- why_halluc
- halluc_survey
- truthfulqa
- factscore
- simpleqa
- selfcheckgpt
- semantic_entropy
- know_what_they_know
- cove
- ft_new_knowledge
- rag_lewis
- claude_reduce_halluc
status:
  label: current
  reviewed: '2026-10-15'
  note: Written from primary sources 2026-10-15; grounding, verification and abstention-aware grading are current practice.
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Evaluating LLMs · 09</div>
    <h1>Hallucination and factuality</h1>
    <p class="sub">Why language models state plausible falsehoods, how factuality is measured (TruthfulQA, FActScore, SimpleQA), how to detect invented facts from the model's own samples, and what actually reduces them.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Models produce fluent, specific statements that are false, or that the prompt and supplied documents do not support. Readers cannot tell them from correct statements, and most benchmarks score a confident guess higher than "I don't know".</div>
      <div class="c"><b>Core idea</b>Separate two problems: <b>factuality</b> (false about the world) and <b>faithfulness</b> (contradicts the instruction or the supplied context). <b>Measure</b> correct, incorrect and abstained answers separately; <b>detect</b> invented facts by disagreement between samples; <b>reduce</b> them by grounding (retrieval, quotes, citations), verification steps, and grading that <b>rewards abstention</b> instead of guessing.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Fluent, specific and wrong

Kalai et al. asked a state-of-the-art open model for one author's birthday, adding "if you know, just respond with DD-MM". Three attempts gave three different wrong dates: 03-07, 15-06 and 01-01.
            {: .lede}

::: cards grid3
### [d] Looks like a fact
Hallucinations are fluent and specific, so a reader cannot tell them from correct statements.

### [b] Two kinds
<b>Factuality</b>: false about the world (a wrong date, an invented citation). <b>Faithfulness</b>: contradicts the instruction, the supplied context or itself (a summary that adds a claim).

### [c] Worse on rare facts
FActScore for ChatGPT biographies fell from 80% to 16% as the people written about became rarer.
:::

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why it does not go away on its own

::: cards grid3
### [d] Rare facts cannot be learned
A fact seen once is weak evidence. Kalai et al.: after pretraining, the hallucination rate is at least the share of facts that appear exactly once (the singleton rate); if 20% of birthdays appear once, expect at least 20% errors on birthdays.

### [b] Grading rewards guessing
Most benchmarks give 1 for correct and 0 for both wrong and "I don't know", so a guess always scores at least as well as abstaining, and models are tuned to these scores.

### [c] Imitating human errors
TruthfulQA (817 questions, 38 categories): the best 2021 model was truthful on 58% vs 94% for people, and the largest models were generally the least truthful, because they reproduce popular misconceptions.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Which model hallucinates less?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? On SimpleQA, GPT-4o was correct on 38.2% of questions, incorrect on 60.8% and declined 1.0%. Claude 3.5 Sonnet was correct on 28.9%, incorrect on 36.1% and declined 35.0%. Which statement is right?
- [ ] GPT-4o is better because its accuracy is higher
- [x] Accuracy hides the difference: Claude 3.5 Sonnet makes far fewer confident errors and is more accurate on the questions it attempts
- [ ] Claude 3.5 Sonnet knows fewer facts, so it must hallucinate more
- [ ] The two cannot be compared at all
> **B.** Correct-given-attempted was 38.0% for GPT-4o and 44.5% for Claude 3.5 Sonnet. The paper's F-score (harmonic mean of correct and correct-given-attempted) was 38.4 vs 35.0. Which model you want depends on what a wrong answer costs you.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Measure, detect, reduce

::: cards grid2
### [f] Measure
Short answers: grade each as correct, incorrect or not attempted (SimpleQA: 4,326 questions, each with one indisputable answer). Long answers: split into atomic facts and report the share a knowledge source supports (FActScore).

### [a] Detect without labels
Sample the answer several times. SelfCheckGPT checks whether the other samples support each sentence; semantic entropy groups samples by meaning (bidirectional entailment) and measures uncertainty over meanings rather than wordings.

### [c] Ground
Put the source in the context (retrieval), ask for word-for-word quotes before the answer on long documents, and require a citation for every claim, retracting claims without one (Claude documentation).

### [e] Verify and allow abstention
Chain-of-Verification drafts an answer, plans verification questions, answers them independently and revises: Wikidata list precision 0.17 → 0.36 for Llama 65B. Give explicit permission to say "I don't know".
:::

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Guess or abstain? <span class="ill">calculator</span>

<div class="visual"><div class="controls"><label class="ctl">model confidence p <input type="range" id="hP" min="0" max="100" step="5" value="40"> <output id="hPo"></output></label><label class="ctl">confidence target t <input type="range" id="hT" min="0" max="95" step="5" value="75"> <output id="hTo"></output></label></div><div class="bars"><div id="hBars"></div></div><p class="readout" id="hOut"></p></div>

Kalai et al. propose adding the target to the instructions of existing benchmarks ("answer only if you are more than t confident, since mistakes are penalized t/(1 − t) points"), with t = 0.5, 0.75 or 0.9 as natural choices. t = 0 is ordinary binary grading.

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Accuracy hides confident errors <span class="ill">paper table</span>

<div class="visual"><div class="bars"><div id="sqBars"></div></div><p class="readout">SimpleQA (Wei et al. 2024, Table 3): share of questions answered incorrectly, and share not attempted. Correct: GPT-4o 38.2%, o1-preview 42.7%, Claude 3.5 Sonnet 28.9%, Claude 3 Haiku 5.1%. The questions were collected adversarially against GPT-4o.</p></div>



::: deep Calibration: does the model know what it knows?
Large pretrained models are well calibrated on multiple-choice and true/false questions in the right format, and can estimate P(True) for their own sampled answers (Kadavath et al. 2022). Calibration is what makes abstention work: a model can only "answer if p &gt; t" if its p is honest. Kalai et al. show GPT-4's calibration histograms before and after reinforcement learning: the pretrained model is well calibrated, and post-training can move it away from calibration.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why these fixes work

::: cards grid2
### [a] Errors get a cost
Counting abstentions separately, or penalising errors, turns a confident wrong answer from a free guess into a loss.

### [c] Consistency tracks knowledge
A fact stored in the weights comes out the same across samples; an invented detail changes from sample to sample.

### [b] The source does the remembering
With retrieval and quotes, the model copies and cites instead of recalling a rare fact. It can still misread the source, a faithfulness error, so check citations.

### [e] Independent checks
CoVe answers each verification question without seeing the draft, so it does not simply repeat the draft's mistakes.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Retrieval-augmented generation eliminates hallucination."
> It reduces it. In FActScore, search-augmented PerplexityAI scored 71.5% vs 58.3% for ChatGPT, still leaving 28.5% of atomic facts unsupported; the model can also ignore or misread what it retrieved.
:::

::: reveal myth
? "Hallucination is a mysterious flaw that larger models will outgrow."
> Kalai et al. derive it from ordinary statistics: facts seen once cannot be learned reliably, and grading that rewards guessing keeps it after post-training. On TruthfulQA the largest models were generally the least truthful.
:::

::: reveal myth
? "Detecting hallucinations needs access to the model's internals."
> SelfCheckGPT works from sampled text alone: if other samples do not support a sentence, it is probably invented.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Under 0/1 grading, when does a model maximise its expected score by answering instead of abstaining?
- [ ] Only when it is more than 50% confident
- [x] Whenever its confidence is above zero
- [ ] Only when it is more than 90% confident
- [ ] Never
> **B.** A guess earns p ≥ 0 and abstaining earns 0. With a stated penalty of t/(1 − t) per error, answering pays only when p &gt; t.
:::

::: reveal
? What is the difference between a factuality and a faithfulness hallucination?
> Factuality: the claim is false about the world. Faithfulness: the output contradicts the user's instruction, the provided context, or itself (Huang et al.).
:::

::: reveal
? How does SelfCheckGPT detect hallucinations without a knowledge base?
> It samples more responses to the same prompt and checks whether each sentence of the main answer is supported by them; sentences the samples do not support are likely hallucinated.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">A model hallucinates when guessing scores better than saying "I don't know": fix the incentive, ground the answer, and count errors separately from abstentions.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Hallucinations are plausible statements that are false (factuality) or unsupported by the prompt or context (faithfulness). Kalai et al. argue they arise as ordinary prediction errors, at least as often as the share of facts seen only once in training, and persist because binary-graded benchmarks reward guessing. On SimpleQA, GPT-4o attempted almost everything and was wrong on 60.8% of questions, while Claude 3.5 Sonnet declined 35% and was wrong on 36.1%. Measure correct, incorrect and abstained separately, detect invented facts by sample disagreement, and reduce them with retrieval, quotes and citations, verification steps and scoring that rewards abstention.</p></div>
    <div class="recap"><div><span><b>Two kinds:</b> factuality (the world) vs faithfulness (prompt and context)</span></div><div><span><b>Cause:</b> rare facts, plus grading that rewards guessing</span></div><div><span><b>Measure:</b> correct · incorrect · abstained; atomic facts</span></div><div><span><b>Reduce:</b> ground, verify, reward abstention</span></div></div>
    <p class="start-hint">You've finished the series. <a href="../../build-it/index.html">See all Build-it notebooks →</a> · Previous: <a href="../08-training-experiments/index.html">← 08</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
