---
title: Sampling, Voting and Coverage
body:
  data-deck: Sampling, voting and coverage
  data-home: ../index.html
  data-home-label: Reasoning
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'one question :: sample N chains :: f'
  - 'final answers :: one per chain :: a'
  - 'select :: vote · verifier · tests :: b'
  - 'answer :: most likely right :: e'
  caption: More samples raise coverage; the selector decides how much of it you keep.
example:
  title: 'Worked example: when does voting help?'
  setup: Each sampled chain is right with probability 0.3.
  steps:
  - 'Wrong chains scatter over 10 different wrong answers: each wrong answer gets about 0.07 of the votes, the right one 0.3, so with 25 samples the majority is right
    most of the time (the notebook measures above 60%).'
  - 'Wrong chains all agree on one wrong answer (a common misconception): that answer gets 0.7 of the votes and wins almost every time.'
  - Voting amplifies whatever answer is most likely, right or wrong.
  - 'With an automatic checker (run the unit tests), any correct sample can be returned: accuracy approaches coverage, 1 − 0.7²⁵ ≈ <b>99.98%</b>.'
  result: Voting needs errors to disagree with each other; verification needs a reliable checker.
traps:
  tricks:
  - 'Coverage = pass@N. :: The share of problems where at least one sample is right.'
  - 'Verify when you can. :: Code and proofs can be checked automatically, so repeated sampling pays off directly.'
  - 'Sample with temperature. :: Greedy decoding returns the same chain every time.'
  traps:
  - 'Voting on free-form answers. :: Majority voting needs answers that can be compared (numbers, options).'
  - 'Expecting voting to scale forever. :: Majority voting and reward models plateau beyond several hundred samples.'
  - 'Ignoring cost. :: N samples cost about N times the tokens.'
papers:
- selfconsistency
- monkeys
- cot
- codex
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Reasoning and test-time compute · 02</div>
    <h1>Sampling, voting and coverage</h1>
    <p class="sub">Spending more inference compute by sampling many reasoning paths: self-consistency (majority voting), coverage that keeps rising with samples, and why picking the right sample is the real bottleneck.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Greedy decoding gives one chain of thought, and one wrong step ruins it. Many problems are solved by some sample when you draw enough of them, but you still have to decide which answer to return.</div>
      <div class="c"><b>Core idea</b>Sample <b>many</b> chains of thought at temperature above zero. <b>Self-consistency</b> returns the most common final answer (majority vote). <b>Coverage</b>, the share of problems solved by any sample, keeps growing roughly log-linearly with the number of samples; turning coverage into accuracy needs a way to <b>select</b>: votes, a verifier, or an automatic check such as unit tests.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## One chain, one chance

Greedy decoding produces a single reasoning path. If any step goes wrong, the answer is wrong, even though a different path would have worked.
            {: .lede}

::: cards grid3
### [d] Fragile paths
Long chains have many places to slip.

### [b] Many valid routes
Hard problems usually admit several ways of reasoning to the same answer.

### [c] Unused compute
Inference typically makes one attempt, even when more attempts would be cheap compared with a bigger model.
:::

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## More samples, but which answer?

::: cards grid3
### [d] No ground truth at inference
For most questions you cannot check an answer automatically.

### [b] Correlated mistakes
If most wrong chains share the same mistake, the wrong answer gets the most votes.

### [c] Plateaus
Large Language Monkeys found majority voting and reward models plateau beyond several hundred samples, while coverage keeps growing.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Coverage or accuracy?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? With 250 samples per issue, DeepSeek-Coder-V2 solved 56% of SWE-bench Lite issues versus 15.9% with one sample. Why could this gain be realised?
- [ ] Because voting picks the best patch
- [x] Because each candidate patch can be checked by running the tests
- [ ] Because the model got larger
- [ ] Because the issues got easier
> **B.** In code, tests act as an automatic verifier, so any correct sample can be selected: coverage becomes accuracy.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Sample, then select

::: cards grid2
### [f] Self-consistency
Sample diverse reasoning paths and return the most consistent final answer: GSM8K +17.9, SVAMP +11.0, AQuA +12.2, StrategyQA +6.4, ARC-Challenge +3.9 points.

### [a] Coverage scales
The share of problems solved by any sample grows with the number of samples over four orders of magnitude, often log-linearly.

### [c] Automatic verifiers
Unit tests, proof checkers and exact-answer checks select a correct sample when one exists.

### [e] Learned verifiers
Without automatic checks, a trained model scores candidates (deck 03).
:::

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Voting vs coverage <span class="ill">simulation</span>

<div class="visual"><div class="controls"><label class="ctl">p(one sample right) <input type="range" id="vP" min="5" max="90" step="5" value="30"> <output id="vPo"></output></label><label class="ctl">samples <input type="range" id="vN" min="1" max="64" step="1" value="16"> <output id="vNo"></output></label><label class="ctl">distinct wrong answers <input type="range" id="vW" min="1" max="20" step="1" value="10"> <output id="vWo"></output></label></div><div class="bars"><div id="vBars"></div></div><p class="readout" id="vOut"></p></div>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why sampling works

::: cards grid2
### [a] Errors disagree
There are many ways to be wrong and usually one way to be right, so wrong answers split the vote.

### [c] Marginalising over paths
Voting approximates the most probable final answer across reasoning paths, not the most probable single path.

### [b] Compute as a dial
More samples trade inference compute for accuracy without changing the model.

### [e] Parallel
Samples are independent, so they can run in parallel; latency grows less than cost.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "More samples always means a better answer."
> Only coverage keeps rising; without a good selector, accuracy plateaus.
:::

::: reveal myth
? "Majority voting fixes systematic errors."
> If the model is consistently wrong, voting makes the wrong answer more certain.
:::

::: reveal myth
? "Sampling is free."
> N samples cost N times the output tokens; batching helps throughput, not cost.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Which selector turns coverage into accuracy most directly?
- [ ] Majority vote
- [ ] Picking the longest answer
- [x] An automatic verifier such as unit tests
- [ ] The first sample
> **C.** A reliable checker accepts any correct sample, so accuracy approaches coverage.
:::

::: reveal
? When does majority voting hurt?
> When wrong samples concentrate on the same wrong answer, so it outvotes the correct one.
:::

::: reveal
? What is coverage?
> The fraction of problems solved by at least one of the generated samples (pass@N).
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Sampling more solutions raises the chance one is right; the hard part is knowing which one.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Instead of one greedy chain of thought, sample many and aggregate. Self-consistency takes the majority answer and improved GSM8K by 17.9 points. Coverage, the share of problems that any sample solves, grows log-linearly over four orders of magnitude of samples: on SWE-bench Lite, DeepSeek-Coder-V2 went from 15.9% with one sample to 56% with 250 when tests could verify the fixes. Without automatic checks, majority voting and reward models plateau after several hundred samples.</p></div>
    <div class="recap"><div><span><b>Self-consistency:</b> majority vote over sampled chains</span></div><div><span><b>Coverage:</b> any sample right; grows with N</span></div><div><span><b>Bottleneck:</b> selecting the right sample</span></div><div><span><b>Checkable tasks:</b> tests and proofs turn coverage into accuracy</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/reasoning/01_test_time_compute.ipynb" target="_blank" rel="noopener">01 · Test-time compute: majority voting, coverage and best-of-N</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/reasoning/01_test_time_compute.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../03-verifiers-and-search/index.html">03 · Verifiers and search →</a> · Previous: <a href="../01-chain-of-thought/index.html">← 01</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
