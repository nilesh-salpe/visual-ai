---
title: Error Bars and Comparing Models
body:
  data-deck: Error bars and comparing models
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
  - 'per-question scores :: 0/1 or graded :: f'
  - 'mean ± SE :: CLT :: a'
  - 'clusters? :: clustered SE if grouped :: b'
  - 'compare models :: paired differences :: c'
  - 'enough questions? :: power analysis :: e'
  caption: Treat every eval as a sample of questions.
example:
  title: 'Worked example: sizing an eval'
  setup: You want to detect a 2-point improvement. Per-question differences between the two models have standard deviation 0.3.
  steps:
  - 'Two-sided 5% test with 80% power: z = 1.96 + 0.84 = 2.80.'
  - n = (2.80 × 0.3 / 0.02)² = <b>1,766</b> questions.
  - 'For a 1-point gap: <b>7,064</b> (≈ 4×).'
  - 'If questions come in clusters of 10 correlated items, the effective n is closer to the number of clusters: plan for more.'
  result: Small gaps need big evals; paired comparisons need far fewer questions than comparing two separate intervals.
traps:
  tricks:
  - 'n ∝ 1/δ². :: Halving the gap needs four times the questions.'
  - 'Pair whenever possible. :: Same questions for both models → test the differences.'
  - 'Report clusters. :: Give the cluster count with clustered SEs.'
  traps:
  - 'Overlapping CIs ⇒ no difference. :: Not for paired data.'
  - 'Treating grouped questions as independent. :: Clustered SEs can be over 3× naive ones.'
  - 'Chasing noise. :: Picking checkpoints by sub-SE differences selects luck.'
papers:
- errorbars
- arena
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Evaluating LLMs · 04</div>
    <h1>Error bars and comparing models</h1>
    <p class="sub">How much of an eval score is noise: standard errors, clustered questions, paired comparisons between models, and how many questions you need.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Leaderboards rank models by gaps of a point or two, but an eval is a finite sample of questions, and those gaps are often smaller than the sampling error.</div>
      <div class="c"><b>Core idea</b>Report a <b>standard error</b> with every score; use <b>clustered</b> standard errors when questions come in groups; compare models with a <b>paired</b> test on per-question differences; size evals with <b>power analysis</b>.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## How wide is the error bar?

95% confidence interval half-width for an accuracy-style score: 1.96·√(p(1−p)/n). Move the number of questions and the accuracy.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">questions n <input type="range" id="eN" min="1.7" max="4.3" step="0.05" value="3"> <output id="eNo"></output></label>
    <label class="ctl">accuracy <input type="range" id="eP" min="0.05" max="0.95" step="0.05" value="0.7"> <output id="ePo"></output></label>
  </div>
  <svg id="eSvg" viewBox="0 0 660 120" style="margin-top:10px" role="img" aria-label="Confidence interval"></svg>
  <p class="readout" id="eOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Three common statistical mistakes

::: cards grid3
### [d] No error bars
Reporting 71.3 vs 70.1 with no uncertainty invites over-reading a gap that may be noise.

### [b] Ignoring clusters
Ten questions about one passage, or one problem in ten languages, are not ten independent samples. Treating them as independent understates the error.

### [c] Comparing separate intervals
"The intervals overlap, so no difference" throws away the fact that both models answered the <b>same</b> questions, which a paired test exploits.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Is it a real improvement?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Model B scores 2 points higher than model A on the same 1,000 questions. Each score alone has a 95% interval of about ±2.8 points. What is the right next step?
- [ ] Conclude there is no difference because the intervals overlap
- [ ] Conclude B is better because its score is higher
- [x] Test the per-question differences (a paired test)
- [ ] Add more models to the comparison
> <b>C.</b> Both models saw the same questions, so most of the noise (which questions are hard) is shared. The per-question differences have much smaller variance; in notebook 02's simulation, a ~3-point gap is detected 88% of the time with a paired test vs 10% by comparing separate intervals.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Four tools

::: cards grid2
### [a] Standard error (CLT)
SE (standard error) = √( (1/n) · (1/(n−1)) Σ(sᵢ − μ̂)² ); 95% CI (confidence interval) = μ̂ ± 1.96·SE. Miller recommends this over bootstrapping as the default.

### [b] Clustered SE
Sum residuals within each cluster before squaring: SE = (1/n)·√(Σ<sub>c</sub>(Σ<sub>i∈c</sub>(sᵢ − μ̂))²). Report the cluster count next to the question count.

### [e] Paired difference
dᵢ = s<sup>A</sup>ᵢ − s<sup>B</sup>ᵢ; test mean(d) with SE = sd(d)/√n. Uses the shared question difficulty to cancel noise.

### [c] Power analysis
Questions needed to detect a gap δ (5% test, 80% power): n = ((1.96 + 0.84)·σ<sub>d</sub>/δ)². Halving δ needs 4× the questions.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Paired vs unpaired <span class="ill">simulation</span>

Two models answer the same questions, simulated 120 times with notebook 02's model. The gap is real in every run. How often does each comparison notice it?
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">true gap (log-odds) <input type="range" id="sG" min="0" max="0.4" step="0.05" value="0.2"> <output id="sGo"></output></label><label class="ctl">questions <input type="range" id="sN" min="200" max="4000" step="200" value="1000"> <output id="sNo"></output></label></div>
  <div class="grid3" style="margin-top:14px">
    <div class="stat"><div class="num" id="sD"></div><div class="lbl">average gap (points)</div></div>
    <div class="stat"><div class="num" id="sP" style="color:var(--a)"></div><div class="lbl">detected, paired test</div></div>
    <div class="stat"><div class="num" id="sU" style="color:var(--d)"></div><div class="lbl">detected, separate intervals</div></div>
  </div>
</div>

<p class="caption">120 simulated evals per setting, run in your browser. Questions vary in difficulty and the two models tend to fail the same ones (75% shared randomness).</p>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Clusters can triple the error

<div class="visual"><div id="cBars"></div><p class="caption">Miller 2024, Table 4 (Anthropic models on real evals): clustered vs naive standard errors on the same data.</p></div>

<div class="deep"><h4>Why clusters matter</h4><p>Questions sharing a passage (DROP, RACE) or a source problem (MGSM's translations) succeed or fail together. The effective number of independent samples is closer to the number of <b>clusters</b> than the number of questions. Miller: "clustered standard errors can be over 3X larger than naive standard errors". Ratios above: DROP 3.05, MGSM 1.88, RACE-H 1.10.</p></div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why this matters for decisions

::: cards grid2
### [a] Avoid chasing noise
Without error bars, teams "optimize" towards random fluctuations and pick checkpoints by luck.

### [e] Get more from the same eval
Paired tests detect real gaps that unpaired comparisons miss, with no extra questions.

### [b] Design better evals
Power analysis tells you before building an eval whether it can detect the differences you care about.

### [c] Arenas do this too
Chatbot Arena reports confidence intervals on its ratings, so overlapping models can be read as statistically tied (deck 07).
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Overlapping confidence intervals mean no significant difference."
> Not for paired data. Two overlapping intervals can still hide a highly significant paired difference.
:::

::: reveal myth
? "More questions from the same passages give proportionally more precision."
> Correlated questions add less information. Use clustered standard errors and count clusters.
:::

::: reveal myth
? "Bootstrapping is always needed for evals."
> For mean scores the central-limit-theorem standard error is standard and simpler; Miller recommends it as the default.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

<div class="quiz">
  <p class="qq">Roughly what is the 95% CI half-width for 70% accuracy on 1,000 questions?</p>
  <div class="opts">
  <button>A. ±0.3 points</button>
  <button>B. ±1 point</button>
  <button data-ok>C. ±2.8 points</button>
  <button>D. ±10 points</button>
  </div>
  <div class="why">1.96·√(0.7·0.3/1000) ≈ 0.028, so <b>±2.8 points</b>.</div>
</div>

<div class="quiz ">
  <p class="qq">Write the clustered standard error and say when to use it.</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">SE = (1/n)·√(Σ_c (Σ_{i∈c} (s_i − μ̂))²). Use it when questions come in correlated groups (shared passage, translations of one problem, multiple samples per prompt).</div>
</div>

<div class="quiz ">
  <p class="qq">You want to detect a 1-point gap and σ_d = 0.3. How many questions?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">n = ((1.96 + 0.84)·0.3/0.01)² ≈ <b>7,060</b>. Small gaps need large evals.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Every eval score needs an error bar: CLT (central limit theorem) standard errors, clustered when questions are grouped, paired tests for model comparisons, and power analysis to size the eval.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>An eval is a finite sample of questions, so its score has sampling error: at 70 percent on a thousand questions the 95 percent interval is about plus or minus 2.8 points. Report the central-limit-theorem standard error with every score. When questions come in correlated groups, like many questions about one passage, use clustered standard errors, which on real evals can be over three times larger. When comparing two models on the same questions, test the per-question differences: shared difficulty cancels, so a paired test detects gaps that overlapping intervals hide. And use power analysis: detecting half the gap needs four times the questions.</p></div>

<div class="recap"><div><span><b>Problem:</b> leaderboard gaps are often smaller than the sampling error.</span></div><div><span><b>Tools:</b> CLT SE, clustered SE, paired differences, power analysis.</span></div><div><span><b>Numbers:</b> ±2.8 pts at n = 1,000; clustered SE up to 3× naive; n ∝ 1/δ².</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/evals/02_error_bars.ipynb" target="_blank" rel="noopener">02 · Error bars, clustered errors and paired comparisons</a> <span style="color:var(--faint)">· 40 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/evals/02_error_bars.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../05-contamination/index.html">05 · Contamination →</a> · Previous: <a href="../03-pass-at-k/index.html">← 03</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Miller 2024, "Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations" (CLT standard errors, clustered SEs "can be over 3X larger", paired differences, power analysis); Chiang et al. 2024 (Chatbot Arena confidence intervals).</p>

<!-- slide id="s-papers" from="papers" -->
