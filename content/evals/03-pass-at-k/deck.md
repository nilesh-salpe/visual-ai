---
title: pass@k and Sampling Metrics
body:
  data-deck: pass@k and sampling metrics
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
  - 'sample n :: per problem, n ≥ k :: f'
  - 'run tests :: count c passing :: b'
  - '1 − C(n−c,k)/C(n,k) :: per problem :: a'
  - 'average :: over problems :: e'
  caption: Unbiased, and it uses all n samples.
example:
  title: 'Worked example: pass@10 from 20 samples'
  setup: n = 20 samples for one problem, c = 2 pass the unit tests, k = 10.
  steps:
  - C(18, 10) = 43,758; C(20, 10) = 184,756.
  - pass@10 = 1 − 43,758 / 184,756 = <b>0.763</b>.
  - 'Plug-in estimate: 1 − (1 − 2/20)<sup>10</sup> = <b>0.651</b>, lower.'
  - pass@1 = c/n = <b>0.10</b>.
  result: Use the unbiased estimator per problem, then average over problems.
traps:
  tricks:
  - 'pass@1 = c/n. :: With many samples it is low-variance.'
  - 'Product form. :: 1 − ∏ (1 − k/i) for i from n − c + 1 to n avoids overflow.'
  - 'n − c < k ⇒ 1. :: Every k-subset contains a pass.'
  traps:
  - 'Plug-in 1 − (1 − c/n)^k. :: Biased low (concave).'
  - 'Reporting pass@100 as user quality. :: Users usually get one attempt.'
  - 'Weak tests. :: Wrong programs that pass weak tests count as solved.'
papers:
- codex
- swebench
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Evaluating LLMs · 03</div>
    <h1>pass@k and sampling metrics</h1>
    <p class="sub">When a model can try several times, what should the score be? pass@k, its unbiased estimator, and how to choose between pass@1 and pass@100.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Generation is stochastic. A model that solves a problem 1 time in 10 looks like a failure with one sample and a success with 100. A single sample per problem is also a very noisy estimate.</div>
      <div class="c"><b>Core idea</b>Sample <b>n</b> solutions per problem, count the <b>c</b> that pass, and estimate pass@k = 1 − C(n−c, k)/C(n, k): the chance that at least one of k attempts passes. Report the k that matches how the model will be used.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## One sample or many?

A problem the model solves with probability p per attempt. With k attempts, the chance that at least one succeeds is 1 − (1−p)<sup>k</sup>. The same model looks very different at k = 1 and k = 100.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">per-attempt success p <input type="range" id="pP" min="0.01" max="0.9" step="0.01" value="0.1"> <output id="pPo"></output></label></div>
  <svg id="pSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="pass@k vs k"></svg>
  <p class="readout" id="pOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Problems with the obvious approaches

::: cards grid3
### [d] Exactly k samples is noisy
Drawing exactly k samples per problem and checking for a pass gives a 0/1 result per problem with high variance.

### [b] Plug-in is biased
Estimating p̂ = c/n and computing 1 − (1−p̂)<sup>k</sup> underestimates pass@k, because the curve is concave in p (notebook 01 measures −0.06 at p = 0.05, n = 20, k = 10).

### [c] Text similarity isn't correctness
BLEU-style (BLEU = Bilingual Evaluation Understudy, an n-gram overlap score for translation) metrics reward code that looks like the reference. HumanEval uses unit tests: functional correctness.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Compute pass@k

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

<div class="quiz">
  <p class="qq">You sample n = 10 solutions and c = 3 pass. What is the unbiased estimate of pass@1?</p>
  <div class="opts">
  <button>A. 0.1</button>
  <button data-ok>B. 0.3</button>
  <button>C. 0.97</button>
  <button>D. 1 − 0.7¹⁰</button>
  </div>
  <div class="why"><b>B.</b> pass@1 = 1 − C(7,1)/C(10,1) = 1 − 7/10 = 0.3 = c/n. With k = 1 the estimator is simply the fraction of samples that pass, averaged over problems.</div>
</div>

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## The unbiased estimator

::: cards grid3
### [a] Sample n ≥ k
For each problem generate n samples (Codex used n = 200) and run the tests; c pass.

### [b] Count subsets
pass@k = 1 − C(n−c, k)/C(n, k): one minus the probability that a random size-k subset of the n samples contains no passing sample. Average over problems.

### [e] Compute stably
Binomials overflow, so use the product form 1 − ∏<sub>i=n−c+1..n</sub>(1 − k/i), as in the paper's numpy snippet. If n − c &lt; k, the answer is 1.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## pass@k calculator

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">n samples <input type="range" id="cN" min="1" max="200" step="1" value="20"> <output id="cNo"></output></label>
    <label class="ctl">c passing <input type="range" id="cC" min="0" max="200" step="1" value="2"> <output id="cCo"></output></label>
    <label class="ctl">k <input type="range" id="cK" min="1" max="100" step="1" value="10"> <output id="cKo"></output></label>
  </div>
  <div class="grid3" style="margin-top:14px">
    <div class="stat"><div class="num" id="cU" style="color:var(--a)"></div><div class="lbl">unbiased pass@k</div></div>
    <div class="stat"><div class="num" id="cB"></div><div class="lbl">plug-in 1 − (1 − c/n)<sup>k</sup></div></div>
    <div class="stat"><div class="num" id="c1"></div><div class="lbl">pass@1 = c/n</div></div>
  </div>
  <p class="readout" id="cOut"></p>
</div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Which k should you report?

::: cards grid2
### [a] pass@1: reliability
What a user gets from one attempt. Estimate it from many samples (n ≫ 1) for low variance; it equals the average per-sample pass rate.

### [b] pass@k, k large: coverage
Whether the model can solve it at all if you can verify attempts. Codex-12B: 28.8% at pass@1, and with 100 samples per problem 70.2% have at least one correct solution.

### [e] Selection matters
pass@k assumes an oracle picks a passing sample. Without one, you need a selection rule (highest likelihood, majority vote, a verifier), and the score falls between pass@1 and pass@k.

### [c] Agentic tasks
On SWE-bench-style (SWE = software engineering) tasks each attempt is expensive and long, so pass@1 with a fixed budget is usually what matters.
:::

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why the estimator is right

::: cards grid2
### [a] It is exact for the sample
Given n samples with c passes, choosing k without replacement fails only if all k come from the n − c failures: probability C(n−c,k)/C(n,k). Averaging over the randomness in c gives exactly the true pass@k.

### [e] It uses every sample
All n samples contribute instead of k, which cuts variance compared with drawing exactly k.

### [b] Notebook evidence
At p = 0.05, n = 20, k = 10: unbiased error ≈ +0.004 (simulation noise), plug-in error −0.061.

### [c] Tests define "pass"
The metric is only as good as the unit tests: weak tests let wrong programs pass.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "pass@100 tells you how good the model is for users."
> Users usually get one attempt. pass@100 measures what a verifier could select from 100 tries, which is a different question.
:::

::: reveal myth
? "1 − (1 − c/n)^k is a fine estimate of pass@k."
> It is biased low because the function is concave. Use 1 − C(n−c,k)/C(n,k).
:::

::: reveal myth
? "pass@1 needs only one sample per problem."
> One sample gives an unbiased but very noisy estimate. Many samples per problem give the same expectation with far lower variance.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

<div class="quiz">
  <p class="qq">n = 5, c = 2, k = 4. pass@4 = ?</p>
  <div class="opts">
  <button>A. 0.4</button>
  <button>B. 0.8</button>
  <button data-ok>C. 1.0</button>
  <button>D. 0.87</button>
  </div>
  <div class="why"><b>1.0</b>: n − c = 3 &lt; k = 4, so every 4-subset contains a pass.</div>
</div>

<div class="quiz ">
  <p class="qq">Why is pass@k averaged over problems rather than computed from the pooled pass rate?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Problems differ in difficulty. pass@k is a per-problem probability; pooling the rate first and then applying 1 − (1−p)^k would mix easy and hard problems incorrectly (and is the biased plug-in).</div>
</div>

<div class="quiz ">
  <p class="qq">When is pass@k with large k the right metric?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">When you can generate many candidates and automatically verify them (unit tests, a checker), so any passing sample can be selected.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">pass@k is the chance that at least one of k attempts passes; estimate it unbiasedly from n ≥ k samples as 1 − C(n−c,k)/C(n,k), and report the k that matches real use.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Code and maths models are stochastic, so the score depends on how many attempts you allow. pass@k is the probability that at least one of k samples passes the tests. The Codex paper estimates it by drawing n samples per problem, counting the c that pass, and computing one minus the number of all-failing k-subsets over all k-subsets, averaged over problems, which is unbiased and uses every sample. The tempting plug-in of c over n into one minus one minus p to the k is biased low. pass@1 measures what a user gets from one try; large k measures what a verifier could find: Codex went from 28.8 percent at one sample to 70.2 percent with 100.</p></div>

<div class="recap"><div><span><b>Problem:</b> stochastic generation: one sample is noisy, many samples need a definition.</span></div><div><span><b>Core idea:</b> pass@k = 1 − C(n−c,k)/C(n,k), product form for stability.</span></div><div><span><b>Practice:</b> pass@1 for reliability, large k only when attempts can be verified.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/evals/01_pass_at_k.ipynb" target="_blank" rel="noopener">01 · pass@k: the unbiased estimator</a> <span style="color:var(--faint)">· 30 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/evals/01_pass_at_k.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../04-error-bars/index.html">04 · Error bars and comparing models →</a> · Previous: <a href="../02-benchmarks/index.html">← 02</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Chen et al. 2021, "Evaluating Large Language Models Trained on Code" (HumanEval, §2.1 unbiased estimator, 28.8% pass@1 and 70.2% with 100 samples); Jimenez et al. 2024 (SWE-bench).</p>

<!-- slide id="s-papers" from="papers" -->
