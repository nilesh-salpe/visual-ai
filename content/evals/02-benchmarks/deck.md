---
title: Benchmarks and Their Failure Modes
body:
  data-deck: Benchmarks and their failure modes
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
  - 'format :: recognize / produce / act :: c'
  - 'scoring :: log-prob, match, tests :: b'
  - 'floor and ceiling :: chance, experts, label noise :: a'
  - 'saturation :: scores bunch near the top :: d'
  - 'replace :: harder or fresher set :: e'
  caption: Each benchmark lives until its scores stop separating models.
example:
  title: 'Worked example: how guessing inflates multiple choice'
  setup: A model truly knows 50% of the answers and guesses uniformly on the rest.
  steps:
  - '4 options: 0.5 + 0.5 × 1/4 = <b>62.5%</b>.'
  - '4 options, one distractor eliminated: 0.5 + 0.5 × 1/3 = <b>66.7%</b>.'
  - '10 options (MMLU-Pro): 0.5 + 0.5 × 1/10 = <b>55.0%</b>.'
  - 'Chance-corrected knowledge from a 4-option score s: (s − 0.25) / 0.75; e.g. s = 62.5% → 50%.'
  result: More options lower the floor, so scores reflect knowledge more; part of why MMLU-Pro scores are 16–33% lower.
traps:
  tricks:
  - 'Subtract chance. :: (score − 1/k) / (1 − 1/k) for k options.'
  - 'Know the expert ceiling. :: GPQA: experts 65%, so 100% isn''t the target.'
  - 'Match the format to the use. :: Recognize (MCQ), produce (short answer, code), act (agents).'
  traps:
  - 'MCQ = can produce the answer. :: It measures recognition among options.'
  - 'Small gaps on saturated sets. :: Often inside the error bars or label noise.'
  - 'Ignoring the scoring rule. :: Log-prob vs parsed generation can disagree for the same model.'
papers:
- mmlu
- mmlupro
- gpqa
- swebench
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Evaluating LLMs · 02</div>
    <h1>Benchmarks and their failure modes</h1>
    <p class="sub">Multiple-choice, generative, code and agentic benchmarks: how each is scored, what it really measures, and why benchmarks saturate and get replaced.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Benchmarks are how the field measures progress, but each format has blind spots, and once models approach the ceiling a benchmark stops telling models apart.</div>
      <div class="c"><b>Core idea</b>Pick benchmarks whose <b>format matches the capability</b> (recognize vs produce vs act), check how answers are <b>scored</b>, know the <b>chance and expert baselines</b>, and move to harder or fresher sets as a benchmark <b>saturates</b>.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Four kinds of benchmark

::: cards grid2
### [a] Multiple choice (MMLU, GPQA)
Pick one of the given options. Cheap and unambiguous to score, but measures <b>recognition</b>, and a random guess already scores 1/(number of options).

### [b] Short answer (GSM8K)
Produce a final answer (a number) that is compared with the reference. 8.5K grade-school maths word problems; scoring depends on extracting the answer correctly.

### [e] Code with tests (HumanEval)
164 hand-written programming problems; the generated function must pass unit tests. Functional correctness instead of text similarity.

### [c] Agentic (SWE-bench)
2,294 real GitHub issues: edit a repository so the project's tests pass. Measures multi-step work in a realistic environment; at release the best model, Claude 2, solved 1.96%.
:::

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## How benchmarks fail

::: cards grid3
### [d] Saturation
Once top models score near the ceiling (or near the label-noise limit), differences shrink into the error bars and the benchmark stops ranking models.

### [b] Shortcuts
With 4 options, eliminating two weak distractors gives 50% without knowing the answer. MMLU-Pro (MMLU = Massive Multitask Language Understanding) raised options from 4 to 10 and accuracy dropped by 16–33%.

### [c] Contamination and label errors
Public test sets leak into training data (deck 05), and some "correct" answers are themselves wrong, which caps the achievable score.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Read the baselines

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? GPQA (Graduate-level Google-Proof Q&A benchmark) reports experts at 65%, skilled non-experts with web access at 34%, and GPT-4 at 39%. What makes GPQA useful as a benchmark?
- [ ] It is easy for everyone
- [x] Answers are hard to look up: non-experts barely beat guessing even with 30+ minutes of web search
- [ ] It has many more questions than MMLU
- [ ] It is open-ended
> <b>B.</b> "Google-proof": the large gap between experts (65%) and skilled non-experts with unrestricted web access (34%, near the 25% chance level) means retrieval alone doesn't solve it, so it still separates strong models.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Know the floor, the ceiling and the format

::: cards grid3
### [a] Floor
Chance level: 25% for 4 options, 10% for 10. MMLU's original paper: GPT-3 175B improved over random chance "by almost 20 percentage points on average".

### [b] Ceiling
Expert accuracy and label noise. If experts score 65% (GPQA) or some labels are wrong, 100% is neither expected nor meaningful.

### [e] Format fit
Recognize (multiple choice), produce (short answer, code), or act over many steps (agents). Use the format closest to how the model will be used.
:::

<div class="deep"><h4>Scoring multiple choice</h4><p>Two common ways: compare the model's <b>log-probability</b> of each option (or option letter) and take the highest, or let the model <b>generate</b> an answer and parse the letter. They can give different scores for the same model: the first never fails to produce a valid answer, the second also tests instruction following and can lose points to parsing errors. Harnesses differ here, which is one reason published numbers disagree.</p></div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Chance level vs number of options

Expected accuracy for a model that knows a fraction of the answers and guesses uniformly on the rest. More options lower the floor and make guessing less rewarding, which is part of how MMLU-Pro separates models better.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">Fraction truly known <input type="range" id="kK" min="0" max="1" step="0.05" value="0.5"> <output id="kKo"></output></label>
    <label class="ctl">Distractors eliminated <input type="range" id="kE" min="0" max="2" step="1" value="0"> <output id="kEo"></output></label>
  </div>
  <div id="kBars" style="margin-top:12px"></div>
</div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Benchmarks at a glance

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Benchmark</th><th>Size</th><th>Format / scoring</th><th>Reference points</th></tr>
  <tr><td>MMLU</td><td>57 tasks</td><td>4-option multiple choice</td><td>GPT-3 175B ≈ chance + 20 points at release</td></tr>
  <tr><td>MMLU-Pro</td><td>10 options</td><td>harder, reasoning-focused multiple choice</td><td>16–33% lower accuracy than MMLU</td></tr>
  <tr><td>GPQA</td><td>448 questions</td><td>expert-written multiple choice</td><td>experts 65%, non-experts 34%, GPT-4 39%</td></tr>
  <tr><td>GSM8K (Grade School Math 8K)</td><td>8.5K problems</td><td>maths word problems, final-answer match</td><td>saturating; fresh variants show overfitting (deck 05)</td></tr>
  <tr><td>HumanEval</td><td>164 problems</td><td>Python functions, unit tests, pass@k</td><td>Codex-12B 28.8% pass@1</td></tr>
  <tr><td>SWE-bench (SWE = software engineering)</td><td>2,294 issues</td><td>edit a real repo, project tests must pass</td><td>Claude 2 1.96% at release</td></tr>
</table></div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why benchmarks keep being replaced

::: cards grid2
### [a] Progress compresses scores
Near the ceiling, gaps between models fall inside the error bars, so the benchmark no longer ranks them.

### [e] Harder versions restore spread
More options (MMLU-Pro), expert-only questions (GPQA) and realistic tasks (SWE-bench) re-open the range.

### [b] Fresh sets fight leakage
The longer a test set is public, the more likely it is in training data. New or held-out sets restore trust.

### [c] Usage moves on
As models are used as agents and coders, benchmarks shift from recognizing answers to doing work end to end.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "25% on a 4-option benchmark means the model knows a quarter of the material."
> 25% is what random guessing gets. Knowledge shows up only above the chance floor.
:::

::: reveal myth
? "A model at 90% on a saturated benchmark is clearly better than one at 88%."
> Near the ceiling, a 2-point gap may be within the error bars or caused by label noise and prompt format.
:::

::: reveal myth
? "Multiple-choice accuracy shows the model can produce the answer."
> It shows the model can <b>recognize</b> the answer among options. Producing it unaided is a harder, different skill.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? MMLU-Pro increased the number of options to…
- [ ] 5
- [ ] 8
- [x] 10
- [ ] 26
> <b>10</b>, lowering the chance floor to 10%, and accuracy dropped 16–33%.
:::

<div class="quiz ">
  <p class="qq">Why can log-prob scoring and generation scoring disagree on the same multiple-choice benchmark?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Log-prob scoring always yields a valid choice; generation can produce unparseable or differently formatted answers and also depends on instruction following and the parser.</div>
</div>

<div class="quiz ">
  <p class="qq">What does SWE-bench measure that HumanEval doesn't?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Working in a real repository on real issues: finding the relevant code, making multi-file edits and passing the project's own tests, rather than writing one standalone function.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Choose benchmarks by format (recognize, produce, act), read them against chance and expert baselines, and expect saturation, shortcuts and leakage to retire them.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Benchmarks differ in what they measure. Multiple-choice sets like MMLU test recognition and have a guessing floor; short-answer sets like GSM8K test producing an answer; HumanEval checks code with unit tests; SWE-bench asks a model to resolve real GitHub issues, where the best model at release solved under 2 percent. Scores must be read against chance and expert levels: on GPQA experts score 65 percent and skilled non-experts with web search only 34. As models improve, benchmarks saturate, shortcuts appear and test sets leak, so harder versions like MMLU-Pro, with ten options and 16 to 33 percent lower scores, replace them.</p></div>

<div class="recap"><div><span><b>Problem:</b> each format has blind spots; benchmarks saturate.</span></div><div><span><b>Core idea:</b> match format to capability; know floor, ceiling and scoring.</span></div><div><span><b>Examples:</b> MMLU/MMLU-Pro, GPQA, GSM8K, HumanEval, SWE-bench.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/evals/02_error_bars.ipynb" target="_blank" rel="noopener">02 · Error bars, clustered errors and paired comparisons</a> <span style="color:var(--faint)">· 40 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/evals/02_error_bars.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/evals/03_contamination.ipynb" target="_blank" rel="noopener">03 · Detecting benchmark contamination with n-grams</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/evals/03_contamination.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../03-pass-at-k/index.html">03 · pass@k and sampling metrics →</a> · Previous: <a href="../01-what-an-eval-measures/index.html">← 01</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Hendrycks et al. 2021 (MMLU: 57 tasks); Wang et al. 2024 (MMLU-Pro: 10 options, 16–33% drop); Rein et al. 2023 (GPQA: 448 questions, experts 65%, non-experts 34%, GPT-4 39%); Cobbe et al. 2021 (GSM8K: 8.5K problems); Chen et al. 2021 (HumanEval: 164 problems); Jimenez et al. 2024 (SWE-bench: 2,294 issues, 1.96%).</p>

<!-- slide id="s-papers" from="papers" -->
