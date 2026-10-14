---
title: LLM-as-Judge
body:
  data-deck: LLM-as-judge
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
  - 'answers A, B :: same prompt :: f'
  - 'judge (A, B) :: first order :: c'
  - 'judge (B, A) :: swapped :: c'
  - 'consistent? :: win, else tie :: a'
  - 'length control :: condition on length :: e'
  caption: Swap positions, control for length, give references for hard questions, and never let a model grade itself alone.
example:
  title: 'Worked example: reading MT-Bench''s bias numbers'
  setup: MT-Bench measured position consistency (same verdict after swapping) and a "repetitive list" verbosity attack.
  steps:
  - 'Position consistency, default prompt: GPT-4 <b>65.0%</b>, GPT-3.5 <b>46.2%</b>, Claude-v1 <b>23.8%</b>.'
  - So one in three GPT-4 verdicts flips with the order; with a single query you can't tell which.
  - 'Verbosity attack (padding with rephrased duplicates): Claude-v1 and GPT-3.5 fooled <b>91.3%</b> of the time, GPT-4 <b>8.7%</b>.'
  - Length-controlled AlpacaEval raised agreement with Chatbot Arena from 0.94 to 0.98 (Spearman).
  result: 'Even a strong judge needs the protocol: swap, aggregate, control for length.'
traps:
  tricks:
  - 'Swap and aggregate. :: Win only if preferred in both orders; otherwise tie.'
  - 'Reference-guided grading. :: Give the judge a reference answer for maths and reasoning.'
  - 'Calibrate on a human sample. :: Check agreement before trusting a new judge or task.'
  traps:
  - 'Single-order judging. :: Position bias decides many verdicts.'
  - 'Self-judging. :: Models favour their own outputs.'
  - 'Longer = better. :: Verbosity bias; use length-controlled metrics.'
papers:
- mtbench
- lcalpaca
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Evaluating LLMs · 06</div>
    <h1>LLM-as-judge</h1>
    <p class="sub">Using a strong model to grade open-ended answers: how well it agrees with people, the biases it brings (position, verbosity, self-preference), and how to control them.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Open-ended answers (explanations, essays, chat) have no single correct string, and human grading is slow and expensive. Evaluating every checkpoint on thousands of such answers needs an automatic grader.</div>
      <div class="c"><b>Core idea</b>Ask a strong LLM (large language model) to compare or score answers, then <b>measure and correct its biases</b>: swap answer positions, control for length, avoid letting a model judge itself, and check agreement with human labels.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Agreement with people

::: cards grid3
### [a] As good as another human
MT-Bench (MT = machine translation): strong LLM judges like GPT-4 "match both controlled and crowdsourced human preferences well, achieving over 80% agreement, the same level of agreement between humans".

### [b] Fast and cheap
A judge model can grade thousands of answers per checkpoint, so open-ended quality can be tracked during development.

### [e] Explainable
Judges can be asked to reason before deciding, which makes their verdicts easier to audit.
:::

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Three documented biases

::: cards grid3
### [d] Position bias
Favouring whichever answer is shown first (or second). With the answers swapped, Claude-v1 gave a consistent verdict only 23.8% of the time with the default prompt, GPT-3.5 46.2%, GPT-4 65.0%.

### [b] Verbosity bias
Favouring longer answers. MT-Bench's "repetitive list" attack (padding a list with rephrased duplicates) fooled Claude-v1 and GPT-3.5 91.3% of the time, GPT-4 8.7%.

### [c] Self-enhancement bias
Favouring answers written by the judge itself, or by similar models. A model shouldn't be the only judge of its own outputs.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Catch the bias

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? You ask a judge "Is A or B better?" and it says A. You swap them, asking "Is B or A better?", and it says the first one again (now B). What happened?
- [ ] The judge is consistent
- [x] Position bias: the verdict followed the slot, not the content
- [ ] Verbosity bias
- [ ] The answers are identical
> <b>B.</b> A consistent judge picks the same underlying answer in both orders. Here it picked "whichever came first", so the verdict tells you nothing about A vs B. Count this as a tie, or ask more times.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Using a judge responsibly

::: cards grid2
### [a] Swap and aggregate
Ask both orders; only count a win if the judge picks the same answer twice, otherwise call it a tie (the MT-Bench approach for pairwise comparisons).

### [b] Control for length
Length-controlled AlpacaEval predicts preferences while conditioning on the length difference, which raised its Spearman correlation with Chatbot Arena from 0.94 to 0.98.

### [e] Use references for hard questions
For maths and reasoning, judges can be fooled by wrong answers; giving the judge a reference solution helps.

### [c] Calibrate against humans
Check agreement on a human-labelled sample before trusting a judge on a new task, and re-check when the judge or the task changes.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Position-swap test <span class="ill">simulation</span>

A simulated judge that adds a bias (in log-odds) to whichever answer is shown first. Ask about 500 answer pairs twice, swapping positions. Watch consistency fall as bias grows. Notebook 04 builds this test.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">first-position bias <input type="range" id="jB" min="0" max="3" step="0.1" value="1"> <output id="jBo"></output></label><label class="ctl">judge noise <input type="range" id="jN" min="0.2" max="2" step="0.1" value="1"> <output id="jNo"></output></label></div>
  <div id="jBars" style="margin-top:12px"></div>
</div>

<p class="caption">For reference, MT-Bench (default prompt): consistency GPT-4 65.0%, GPT-3.5 46.2%, Claude-v1 23.8%.</p>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Verbosity bias and length control

<div class="visual"><div id="vBars"></div><p class="caption">MT-Bench Table 3: failure rate of judges under the "repetitive list" attack on 23 answers (padding without new information).</p></div>

<div class="deep"><h4>How length control works</h4><p>Length-controlled AlpacaEval fits a model of the judge's preferences that includes the length difference between the two answers, then reports the win rate predicted with that length term set to zero: "what would the judge prefer if the answers were the same length?" This made the ranking agree better with human votes in Chatbot Arena (Spearman 0.94 → 0.98).</p></div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why judges work, and where they fail

::: cards grid2
### [a] Judging is easier than writing
Comparing two answers is often easier than producing the best one, so a strong model can grade answers from comparable models reasonably well.

### [e] Scales with automation
Cheap enough to grade every checkpoint and every ablation.

### [d] Biases are systematic
Unlike random noise, position, length and self-preference push in consistent directions, so they can change rankings, and models can be tuned to exploit them.

### [b] Weak on hard reasoning
MT-Bench notes "limited reasoning ability": judges can approve wrong maths answers, especially without a reference solution.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "80% agreement means the judge is right 80% of the time."
> It means it agrees with humans as often as humans agree with each other. Both can be wrong, and agreement varies by task.
:::

::: reveal myth
? "Asking once is enough if the judge is strong."
> Even GPT-4 was position-consistent only 65% of the time in MT-Bench. Swap positions and aggregate.
:::

::: reveal myth
? "Longer answers winning means they're more helpful."
> Judges have verbosity bias; length-controlled metrics agree better with human preference.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Which judge resisted MT-Bench's "repetitive list" verbosity attack best?
- [ ] Claude-v1
- [ ] GPT-3.5
- [x] GPT-4
- [ ] All failed equally
> <b>GPT-4</b>: 8.7% failure vs 91.3% for Claude-v1 and GPT-3.5.
:::

<div class="quiz ">
  <p class="qq">Describe a protocol that removes position bias from pairwise judging.</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Ask with both orders. Count a win only when the judge picks the same underlying answer both times; otherwise record a tie (or ask more times).</div>
</div>

<div class="quiz ">
  <p class="qq">What does length-controlled AlpacaEval change, and what was the effect?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">It conditions the judge's preference on the length difference and reports the length-neutral win rate. Correlation with Chatbot Arena rose from 0.94 to 0.98 (Spearman).</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">LLM judges agree with people about as often as people agree with each other, but they are biased by position, length and self-preference, so swap, length-control and calibrate.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Open-ended answers need a grader, and a strong model can do it: MT-Bench found GPT-4's verdicts agree with human preferences over 80 percent of the time, about the same as humans agree with each other. But judges have systematic biases. Swapping the two answers changed GPT-4's verdict a third of the time and Claude-v1's most of the time. Padding answers with repeated content fooled weaker judges over 90 percent of the time. And models may favour their own outputs. So ask in both orders and count disagreements as ties, control for length, as length-controlled AlpacaEval did to raise its correlation with Chatbot Arena from 0.94 to 0.98, give references for hard questions, and check agreement with humans.</p></div>

<div class="recap"><div><span><b>Problem:</b> open-ended answers need scalable grading.</span></div><div><span><b>Core idea:</b> LLM judges ≈ human agreement (>80%), but biased.</span></div><div><span><b>Controls:</b> position swap, length control, references, human calibration, no self-judging.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/evals/04_judges_and_arenas.ipynb" target="_blank" rel="noopener">04 · LLM judges and arena ratings</a> <span style="color:var(--faint)">· 45 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/evals/04_judges_and_arenas.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../07-arenas/index.html">07 · Arenas and ratings →</a> · Previous: <a href="../05-contamination/index.html">← 05</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Zheng et al. 2023, "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena" (>80% agreement; Table 2 position consistency; Table 3 "repetitive list" attack); Dubois et al. 2024, "Length-Controlled AlpacaEval" (Spearman 0.94 → 0.98 with Chatbot Arena).</p>

<!-- slide id="s-papers" from="papers" -->
