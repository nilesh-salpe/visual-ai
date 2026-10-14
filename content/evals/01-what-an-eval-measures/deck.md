---
title: What an Eval Measures
body:
  data-deck: What an eval measures
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
  - 'capability :: what should the score mean? :: c'
  - 'questions :: which set, how many :: f'
  - 'prompt :: template, shots :: b'
  - 'decoding :: greedy or sampled, k :: a'
  - 'scoring :: match, log-prob, tests, judge :: e'
  - 'score ± SE :: with uncertainty :: d'
  caption: Report every stage with the number; change any one and the score changes.
example:
  title: 'Worked example: is a 2-point lead real?'
  setup: Model A scores 72% and model B 70% on a 1,000-question benchmark, each in one prompt format.
  steps:
  - '95% CI half-width at ~71%: 1.96 × √(0.71 × 0.29 / 1,000) = <b>±2.8 points</b>.'
  - The 2-point gap is inside either model's interval; a paired test on the same questions is needed (deck 04).
  - Prompt format alone can move scores by tens of points (up to 76 for LLaMA-2-13B in Sclar et al.).
  - Evaluate both models over several equivalent formats and report the mean and spread.
  result: 'Before calling a winner: same protocol, standard errors, a paired comparison, and the format spread.'
traps:
  tricks:
  - 'CI ≈ ±1.96·√(p(1−p)/n). :: ±2.8 points at 70% on 1,000 questions.'
  - 'Report the protocol. :: Version, shots, template, decoding, scoring, n.'
  - 'Measure more than accuracy. :: HELM tracks calibration, robustness, fairness, bias, toxicity and efficiency too.'
  traps:
  - 'Comparing numbers across papers. :: Different harnesses and prompts make them incomparable.'
  - 'One prompt per model. :: Formatting can decide the comparison.'
  - 'Point estimates only. :: Gaps smaller than the error bars are noise.'
papers:
- helm
- sclar
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Evaluating LLMs · 01</div>
    <h1>What an eval measures</h1>
    <p class="sub">An eval score is the result of a task, a prompt, a sampling setup, a scoring rule and a sample of questions. Change any one and the number changes.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Teams ship, rank and choose models based on single eval numbers, yet those numbers depend on many choices that are rarely reported, and accuracy alone hides most of what matters.</div>
      <div class="c"><b>Core idea</b>Treat every score as <b>a measurement with a protocol</b>: what capability, which questions, which prompt and decoding, which scoring rule, how much uncertainty. Measure more than accuracy, and report the setup with the number.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## One model, one benchmark, many scores

Every eval result passes through a pipeline of choices. Click each stage to see the decision it hides and how much it can move the number.
{: .lede}

<div class="visual">
  <div class="seg" id="pSeg" style="flex-wrap:wrap"><button data-v="0" class="on">Capability</button><button data-v="1">Questions</button><button data-v="2">Prompt format</button><button data-v="3">Decoding</button><button data-v="4">Scoring</button><button data-v="5">Uncertainty</button></div>
  <div class="infobox" style="background:var(--panel-2);border-radius:10px;padding:12px 14px;margin-top:10px;font-size:14px;color:var(--muted)" id="pInfo" style="font-size:15px;line-height:1.6"></div>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why a single number misleads

::: cards grid3
### [d] Prompt sensitivity
Sclar et al. found accuracy varying by up to <b>76 points</b> for LLaMA-2-13B across semantically equivalent prompt formats (separators, spacing, casing). A comparison that uses one format per model can be decided by formatting.

### [b] Accuracy isn't everything
A model can be accurate but badly calibrated, brittle to typos, biased or slow. HELM (Holistic Evaluation of Language Models) measures 7 metrics per scenario precisely so the trade-offs stay visible.

### [c] Sampling error
Benchmarks are finite samples of questions. With 1,000 questions at 70% accuracy, the 95% interval is about ±2.8 points, often wider than the gap being celebrated (deck 04).
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Same model, different numbers

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Two papers report different MMLU (Massive Multitask Language Understanding) scores for the same model. Which is the LEAST likely explanation?
- [ ] Different prompt formats or number of few-shot examples
- [ ] Scoring by option log-probability vs by parsing generated text
- [ ] Different random seeds for sampling
- [x] The model's weights changed between runs
> <b>D.</b> Same weights, but every other item is a common source of differences. Prompt format alone can swing results by tens of points (Sclar et al.), and how the answer is extracted and scored differs between evaluation harnesses.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## A score is a measurement protocol

::: cards grid3
### [a] Validity
Does the task measure the capability you care about? Multiple-choice trivia measures recognition, not the ability to write a correct answer from scratch.

### [b] Reliability
Would you get the same number again with other prompts, seeds or a fresh sample of questions? Report standard errors and sensitivity, not just a point estimate.

### [e] Coverage
Measure several properties (accuracy, calibration, robustness, safety, cost) across several scenarios, so a gain in one isn't hiding a loss in another.
:::

<div class="deep"><h4>HELM's design</h4><p>HELM measures <b>7 metrics</b> (accuracy, calibration, robustness, fairness, bias, toxicity and efficiency) on <b>16 core scenarios</b> "to the extent possible (87.5% of the time)", and evaluates <b>30</b> prominent models on <b>42</b> scenarios under standardized conditions. The point is to make the full trade-off visible rather than one leaderboard column.</p></div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Prompt format sensitivity <span class="ill">illustrative</span>

The same 5 questions asked in different, equivalent formats. In this illustration the model's answers change with the format, as Sclar et al. measured at scale. A robust evaluation reports the <b>spread</b> across formats, not one pick.
{: .lede}

<div class="visual">
  <div class="seg" id="fSeg"><button data-v="0" class="on">"Question: … Answer:"</button><button data-v="1">"Q: … A:"</button><button data-v="2">"QUESTION … ANSWER"</button><button data-v="3">"question - … answer -"</button></div>
  <div id="fBars" style="margin-top:12px"></div>
  <p class="readout" id="fOut"></p>
</div>

<p class="caption">Illustrative accuracies for one model on one task. The real reported spread: up to 76 accuracy points for LLaMA-2-13B on some tasks.</p>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## A checklist for reading any eval result

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Question to ask</th><th>Why it matters</th><th>Deck</th></tr>
  <tr><td>Which benchmark version, split and number of questions?</td><td>Sets the sampling error and which questions count</td><td>02, 04</td></tr>
  <tr><td>Zero-shot or few-shot? Which prompt template? Chain of thought?</td><td>Format and shots can move scores by many points</td><td>01</td></tr>
  <tr><td>Greedy or sampled? How many samples? Which k?</td><td>pass@1 and pass@100 answer different questions</td><td>03</td></tr>
  <tr><td>How is the answer extracted and scored?</td><td>Log-prob of options vs parsed generation vs a judge model</td><td>02, 06</td></tr>
  <tr><td>What is the standard error, and was the comparison paired?</td><td>Is the difference real?</td><td>04</td></tr>
  <tr><td>Could the test set be in the training data?</td><td>Memorization inflates scores</td><td>05</td></tr>
</table></div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why the protocol view helps

::: cards grid2
### [a] Comparisons become fair
Same prompts, same scoring and same questions for every model, as in HELM's standardized setup, make differences interpretable.

### [e] Uncertainty becomes visible
With standard errors and format spreads you can tell a real improvement from noise.

### [b] Trade-offs stay honest
Seeing calibration, robustness and cost next to accuracy stops a model from winning on one axis by losing on another.

### [c] Results transfer
A score whose protocol you know can be reproduced and compared with next year's models.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "A benchmark score is a property of the model."
> It is a property of the model <b>plus</b> the prompt, decoding, scoring and question sample. Change those and the score changes, sometimes by a lot.
:::

::: reveal myth
? "Higher accuracy means a better model, full stop."
> Accuracy can trade off against calibration, robustness, safety and cost. HELM reports 7 metrics for exactly this reason.
:::

::: reveal myth
? "If two papers use the same benchmark, their numbers are comparable."
> Only if the protocol matches: version, shots, template, extraction and scoring. Often it doesn't.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? How many metrics does HELM measure for each core scenario?
- [ ] 1 (accuracy)
- [ ] 3
- [x] 7
- [ ] 42
> <b>7</b>: accuracy, calibration, robustness, fairness, bias, toxicity, efficiency.
:::

<div class="quiz ">
  <p class="qq">Name four protocol choices you would want reported with a benchmark score.</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Benchmark version and number of questions; shots and prompt template; decoding (greedy or sampled, number of samples, k); answer extraction and scoring rule; standard error; contamination checks.</div>
</div>

<div class="quiz ">
  <p class="qq">How would you make a prompt-format comparison robust?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Evaluate each model over a set of equivalent formats and report the mean and spread (or the full distribution), rather than one format chosen per model.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">An eval score is a measurement protocol (capability, questions, prompt, decoding, scoring, uncertainty), so report the protocol and more than one metric along with the number.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>A benchmark number depends on the capability the task actually measures, which questions were used, the prompt format, how answers were sampled, how they were scored, and sampling error. Prompt format alone moved LLaMA-2-13B by up to 76 accuracy points between equivalent formats, and 1,000 questions give about plus or minus 2.8 points of uncertainty. HELM's answer is to standardize the setup and measure seven properties, from accuracy and calibration to toxicity and efficiency, across many scenarios. In practice: report the protocol, standard errors and spreads, and look beyond accuracy.</p></div>

<div class="recap"><div><span><b>Problem:</b> single numbers hide prompts, scoring, sampling error and trade-offs.</span></div><div><span><b>Core idea:</b> a score = model + protocol; standardize it and measure several metrics.</span></div><div><span><b>Practice:</b> report setup, standard errors and format spread; check contamination.</span></div></div>

<p class="start-hint">Next: <a href="../02-benchmarks/index.html">02 · Benchmarks and their failure modes →</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Liang et al. 2022, "Holistic Evaluation of Language Models" (HELM: 7 metrics, 16 core scenarios, 42 scenarios, 30 models); Sclar et al. 2023, "Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design" (up to 76 points); Miller 2024, "Adding Error Bars to Evals".</p>

<!-- slide id="s-papers" from="papers" -->
