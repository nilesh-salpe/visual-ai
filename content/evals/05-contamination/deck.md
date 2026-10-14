---
title: Contamination
body:
  data-deck: Contamination
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
  - 'training corpus :: web-scale :: f'
  - 'test set :: public benchmark :: f'
  - 'n-gram overlap :: 13-grams (GPT-3) :: b'
  - 'clean vs dirty scores :: does overlap matter? :: a'
  - 'fresh test set :: GSM1k-style check :: e'
  caption: Detect, report, validate.
example:
  title: 'Worked example: how much does leakage inflate a score?'
  setup: True skill 55%. Leaked items are answered correctly 95% of the time (memorized).
  steps:
  - '10% leaked: 0.1 × 0.95 + 0.9 × 0.55 = <b>59.0%</b> reported (+4 points).'
  - '20% leaked: <b>63.0%</b> (+8 points).'
  - 'The clean subset still scores ~55%: the gap between full and clean scores is the inflation.'
  - A fresh, equivalent test set would also show ~55%.
  result: Report clean-subset scores next to full ones, and confirm on fresh data when it matters.
traps:
  tricks:
  - 'Inflation = frac × (memorized − true). :: Quick estimate of the effect.'
  - '13-grams. :: Conservative overlap flag, as in GPT-3.'
  - 'Fresh sets reveal overfitting. :: GSM1k: drops of up to 8% for some families.'
  traps:
  - 'Filtered = clean. :: Filters miss paraphrases and can have bugs (GPT-3 had one).'
  - 'Short n-grams. :: Coincidental matches create false positives in real text.'
  - 'Assuming it always matters a lot. :: GPT-3 and GSM1k found it varies by model and dataset; measure it.'
papers:
- gpt3
- gsm1k
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Evaluating LLMs · 05</div>
    <h1>Benchmark contamination</h1>
    <p class="sub">When test questions leak into training data the score partly measures memorization. How to detect overlap, how to report it, and how fresh test sets reveal overfitting.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Pretraining corpora are scraped from the web, and benchmarks are published on the web. Test items (or close variants) can end up in training data, inflating scores in ways that don't reflect real capability.</div>
      <div class="c"><b>Core idea</b><b>Detect</b> overlap (GPT-3 flagged any 13-gram match with the training set), <b>report</b> clean-subset scores next to full ones, and <b>validate</b> on fresh or held-out test sets that can't have leaked.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## How leakage inflates a score <span class="ill">simulation</span>

A model with true skill 55% that answers leaked items correctly 95% of the time (memorized). Move the fraction of the test set that leaked into training.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">leaked fraction <input type="range" id="lF" min="0" max="0.5" step="0.05" value="0.1"> <output id="lFo"></output></label></div>
  <div id="lBars" style="margin-top:12px"></div>
  <p class="readout" id="lOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why it is hard to avoid

::: cards grid3
### [d] Web-scale data
Benchmarks, their solutions and discussions of them are posted online and get scraped along with everything else.

### [b] Filtering is imperfect
GPT-3 tried to remove overlaps with its benchmarks, but "a bug in the filtering caused us to ignore some overlaps, and due to the cost of training it was not feasible to retrain the model."

### [c] Paraphrases escape detection
Exact n-gram matching misses translated, reworded or reformatted copies of test items.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Reading a contamination report

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? A model scores 80% on a benchmark, 81% on the flagged ("dirty") items and 80% on the clean items. What does that suggest?
- [ ] Heavy contamination inflated the score
- [x] Contamination is not driving the score on this benchmark
- [ ] The benchmark is broken
- [ ] The detector failed
> <b>B.</b> If clean-subset performance matches the full score, the overlapping items aren't giving the model an advantage. That is GPT-3's method: compare scores on the clean subset with the full benchmark. GPT-3 found contamination "has a minimal effect" on most datasets, while flagging some where it did matter.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Detect, report, validate

::: cards grid3
### [a] Detect
GPT-3 flagged test examples "that have a 13-gram overlap with anything in the pretraining set (or that overlap with the whole example when it is shorter than 13-grams)". Deliberately conservative.

### [b] Report
Score the full set, the clean subset and the dirty subset. A big gap between clean and full means the score is partly memorization.

### [e] Validate
Build new test sets the model can't have seen: GSM1k mirrors GSM8K (Grade School Math 8K)'s style with fresh problems. Models that overfit GSM8K drop on it.
:::

<div class="deep"><h4>What GSM1k found</h4><p>On fresh, GSM8K-style problems, the authors "observe accuracy drops of up to 8%, with several families of models showing evidence of systematic overfitting across almost all model sizes", while frontier models (they name Gemini, GPT and Claude) "show little to no signs of overfitting". Contamination is not uniform: it depends on how each model's data was collected.</p></div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## n-gram overlap, by hand

A toy test item and a training document. Choose n and see which n-grams of the test item also appear in training. Short n flags coincidences; long n misses partial copies.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">n <input type="range" id="nN" min="2" max="8" step="1" value="5"> <output id="nNo"></output></label></div>
  <div id="nTest" style="display:flex;flex-wrap:wrap;gap:4px;margin-top:12px;font:500 13px 'JetBrains Mono',monospace"></div>
  <p class="caption" style="margin-top:8px">training document: <span id="nTrain" style="font-family:'JetBrains Mono',monospace"></span></p>
  <p class="readout" id="nOut"></p>
</div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Other defences

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Defence</th><th>How it helps</th><th>Limits</th></tr>
  <tr><td>n-gram overlap filtering</td><td>Removes exact copies before training; flags items after</td><td>Misses paraphrases and translations</td></tr>
  <tr><td>Clean-subset reporting</td><td>Shows whether flagged items move the score</td><td>Only as good as the detector</td></tr>
  <tr><td>Fresh / held-out test sets</td><td>Can't have leaked (GSM1k)</td><td>Expensive to build; must match difficulty</td></tr>
  <tr><td>Private or rotating test sets</td><td>Never published, or replaced regularly</td><td>Less reproducible for outsiders</td></tr>
  <tr><td>Canary strings</td><td>A unique marker in benchmark files lets data pipelines filter them and lets models be probed for having seen them</td><td>Depends on pipelines honouring it</td></tr>
</table></div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it matters

::: cards grid2
### [a] Scores stop meaning capability
A memorized answer says nothing about solving a new problem of the same kind, which is what the benchmark is supposed to predict.

### [e] Comparisons become unfair
Models trained on different data are contaminated to different degrees, so rankings mix skill with exposure.

### [b] It compounds over time
The longer a benchmark is public, the more copies, solutions and discussions exist on the web.

### [c] Fresh tests restore trust
A gap between an old benchmark and a fresh equivalent (GSM8K vs GSM1k) is direct evidence of overfitting.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "If the benchmark was filtered from the training data, it is clean."
> Filters miss paraphrases and can have bugs, as GPT-3's did. Report clean-subset results and use fresh sets.
:::

::: reveal myth
? "Contamination always inflates scores a lot."
> GPT-3 found minimal effect on most benchmarks, and GSM1k found frontier models barely affected. It varies by model and dataset, so measure it.
:::

::: reveal myth
? "A shorter n-gram makes detection strictly better."
> Short n-grams match by coincidence in real text, producing false positives. GPT-3 chose 13 to stay conservative.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? What n-gram length did GPT-3 use to flag potential contamination?
- [ ] 3
- [ ] 8
- [x] 13
- [ ] 50
> <b>13-grams</b> (or the whole example if shorter).
:::

<div class="quiz ">
  <p class="qq">How do clean and dirty subset scores tell you whether contamination matters?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">If the clean-subset score matches the full score, overlap isn't driving results. If dirty items score much higher than clean ones, part of the score is memorization.</div>
</div>

<div class="quiz ">
  <p class="qq">What did GSM1k do, and what did it find?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Built fresh GSM8K-style problems. Accuracy dropped by up to 8% for some model families (systematic overfitting), while frontier models showed little to no drop.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Contaminated test items turn benchmarks into memory tests: detect overlap (13-grams), report clean-subset scores, and confirm on fresh test sets.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Benchmarks live on the web, and so does training data, so test items leak. A model that memorized leaked items looks better than it is, and the effect differs between models. GPT-3 flagged any test example sharing a 13-gram with its training data and compared scores on the clean and dirty subsets; it found little effect on most benchmarks, after a filtering bug had left some overlap in. n-gram matching misses paraphrases, so the strongest evidence comes from fresh test sets: on GSM1k, new GSM8K-style problems, some model families dropped by up to 8 percent while frontier models barely changed.</p></div>

<div class="recap"><div><span><b>Problem:</b> web-scale training data includes public test sets.</span></div><div><span><b>Detect & report:</b> 13-gram overlap; full vs clean vs dirty scores.</span></div><div><span><b>Validate:</b> fresh or private test sets; GSM1k drops of up to 8%.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/evals/03_contamination.ipynb" target="_blank" rel="noopener">03 · Detecting benchmark contamination with n-grams</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/evals/03_contamination.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../06-llm-as-judge/index.html">06 · LLM-as-judge →</a> · Previous: <a href="../04-error-bars/index.html">← 04</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Brown et al. 2020, "Language Models are Few-Shot Learners" (GPT-3 §4 and App. C: 13-gram overlap, filtering bug, clean vs dirty analysis); Zhang et al. 2024, "A Careful Examination of Large Language Model Performance on Grade School Arithmetic" (GSM1k: drops of up to 8%).</p>

<!-- slide id="s-papers" from="papers" -->
