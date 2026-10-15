---
title: Experiments in LLM Training
body:
  data-deck: Experiments in LLM training
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
  - 'one change :: against a fixed baseline :: f'
  - 'small proxy :: 150M–1B models :: a'
  - 'several seeds :: per arm :: b'
  - 'low-noise metric :: cloze · likelihood :: c'
  - 'decide :: gap > seed noise :: e'
  caption: 'An ablation is a noisy measurement: design it so the effect can beat the noise.'
example:
  title: 'Worked example: is the new data filter better?'
  setup: Two 7B-architecture runs differ only in a data filter. MMLU (multiple choice) improves by 0.9 points. Meta measured a seed standard deviation of 0.57 points
    for this setup (0.22 for MMLU-Cloze).
  steps:
  - 'One seed per arm: the difference has SE = 0.57 × √2 = 0.81, so the smallest reliably detectable gap is 2.80 × 0.81 = <b>2.3 points</b>.'
  - '0.9 &lt; 2.3: the result is within seed noise. It is not evidence either way.'
  - 'Switch to the cloze format (σ = 0.22): with 3 seeds per arm the detectable gap is 2.80 × 0.22 × √(2/3) = <b>0.50 points</b>.'
  - Re-run 3 seeds per arm; a 0.9-point cloze gain would now be a real signal.
  result: 'Size the experiment before running it: seeds and metric choice decide what you can detect.'
traps:
  tricks:
  - 'Detectable gap ≈ 2.8 · σ · √(2/n). :: n seeds per arm; quadruple the seeds to halve the gap.'
  - 'Prefer continuous metrics at small scale. :: Likelihood or cloze versions of benchmarks have far less noise than accuracy on multiple choice.'
  - 'Check small-to-large agreement. :: Validate that your proxy scale ranks recipes the way the target scale does.'
  traps:
  - 'One seed per arm. :: Many ablation gaps are smaller than seed noise.'
  - 'Benchmarks near chance. :: Small models score around 25% on 4-choice MMLU: the metric carries almost no signal.'
  - 'Picking the best checkpoint or seed. :: Selecting the maximum of noisy scores reports luck as progress.'
papers:
- var_bench
- signal_noise
- datadecide
- random_search
- hyperband
- seed3407
- errorbars
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Evaluating LLMs · 08</div>
    <h1>Experiments in LLM training</h1>
    <p class="sub">How labs decide between data recipes, architectures and hyperparameters with small, cheap runs: seed noise, low-noise metrics, small-to-large agreement, and efficient hyperparameter search.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>A full pretraining run costs too much to try every idea, so decisions are made from small runs. But a small run's benchmark score moves by as much as the effect being tested when only the random seed changes, and the best recipe at 150M parameters is not always the best at 1B.</div>
      <div class="c"><b>Core idea</b>Treat every ablation as a measurement with noise. Change <b>one thing</b>, run <b>several seeds</b> per arm, use <b>low-noise metrics</b> (cloze formats, likelihoods, averaged checkpoints), and only trust differences larger than the <b>seed noise</b>. Choose benchmarks with a high <b>signal-to-noise ratio</b>, check that small-scale rankings <b>agree</b> with larger scale, and search hyperparameters with <b>random search</b> and early stopping rather than grids.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Decisions from small runs

A lab compares two pretraining data filters with one small run each. Filter B wins MMLU by 0.9 points, and B goes into the next large run.
            {: .lede}

::: cards grid3
### [d] Cost
Each full-scale run is too expensive to repeat, so small proxies decide.

### [b] Seed noise
Ten 7B-architecture runs on 210B tokens that differ only in seed vary by 0.57 points on MMLU and 0.80 on ARC-Challenge (standard deviation).

### [c] Scale shift
A recipe that wins at 150M parameters does not always win at 1B.
:::

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Three ways ablations mislead

::: cards grid3
### [d] Gap within noise
One seed per arm cannot separate a 0.9-point effect from a 0.57-point seed standard deviation.

### [b] Metric near chance
Small models score about 25% on 4-choice MMLU for much of training, so the score barely moves with real improvements.

### [c] Cherry-picking
Scanning up to 10,000 seeds on CIFAR-10, Picard found it "surprisingly easy" to find a much better or much worse outlier: report the distribution, not the best run.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Is filter B better?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Filter B beats filter A by 0.9 MMLU points, one run each; the seed standard deviation is 0.57 points. What can you conclude?
- [ ] B is better: 0.9 is larger than 0.57
- [x] Nothing yet: the difference of two runs has SE ≈ 0.81, so 0.9 is within noise
- [ ] A is better
- [ ] B is better because MMLU is a large benchmark
> **B.** The difference of two single runs has standard error σ√2 ≈ 0.81 points; detecting a gap with 80% power at 5% significance needs about 2.8 × 0.81 ≈ 2.3 points. Add seeds or use a lower-noise metric.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Make the effect beat the noise

::: cards grid2
### [f] One change, several seeds
Hold everything else fixed; run 2-3 or more seeds per arm and compare means (paired where possible: same data order, same eval set).

### [a] Low-noise metrics
Cloze formats instead of multiple choice: MMLU-Cloze had seed σ 0.22 vs 0.57 and was far more monotonic during training. Likelihood or perplexity metrics instead of accuracy.

### [c] High signal-to-noise benchmarks
Signal: how far apart models of similar compute score. Noise: how much one run's score jitters across its final checkpoints. Benchmarks with higher SNR give more reliable small-scale decisions (R = 0.79).

### [e] Validate the proxy scale
DataDecide (25 corpora, models to 1B, 3 seeds): rankings at 150M predicted the 1B winner in about 80% of comparisons; no scaling-law method of 8 baselines did better for the same compute.
:::

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## How small a gap can you see? <span class="ill">calculator</span>

<div class="visual"><div class="controls"><label class="ctl">seed σ (points) <input type="range" id="eS" min="0.1" max="1.5" step="0.01" value="0.57"> <output id="eSo"></output></label><label class="ctl">seeds per arm <input type="range" id="eN" min="1" max="10" step="1" value="1"> <output id="eNo"></output></label><label class="ctl">observed gap <input type="range" id="eD" min="0" max="3" step="0.1" value="0.9"> <output id="eDo"></output></label></div><div class="bars"><div id="eBars"></div></div><p class="readout" id="eOut"></p></div>

The statistics are the same as for comparing models on an eval (paired differences, standard errors): see <a href="../04-error-bars/index.html">Error bars and comparing models</a>. Here the noise comes from training, not from the choice of questions.

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Searching hyperparameters

::: cards grid3
### [d] Grid search
Wastes trials: most hyperparameters barely matter, so a grid re-tests the same values of the ones that do.

### [a] Random search
Bergstra and Bengio: randomly chosen trials are more efficient than a grid, because "only a few of the hyper-parameters really matter", and which ones differ by dataset.

### [e] Early stopping (Hyperband)
Start many random configurations cheaply and give more compute only to the promising ones: over an order-of-magnitude speedup over the Bayesian optimisation baselines tested.
:::

Record everything that defines a run (code commit, data version, config, seed) so that any result can be reproduced and compared.

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why this matters

::: cards grid2
### [a] Compute is the budget
Every extra seed or ablation costs compute; sizing experiments decides how many questions the budget can answer.

### [c] Errors compound
A wrong small-scale decision is baked into a large run that costs orders of magnitude more.

### [b] Metrics change with scale
Benchmarks can sit near chance at small scale and become informative only later; continuous metrics made benchmarks over 80% predictable at 1B with 0.01% of the compute in DataDecide.

### [e] Averaging helps
Averaging the scores of a run's final checkpoints raised decision accuracy from 68.9% to 71.3% on a 30-task average (Signal and Noise).
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "A bigger benchmark means no need for multiple seeds."
> More questions shrink question-sampling error, not training noise: the seed changes the model itself. You need both kinds of error under control.
:::

::: reveal myth
? "If the small model wins, the large one will too."
> Usually, not always: about 80% of pairwise comparisons transferred from 150M to 1B in DataDecide. Validate the proxy for your setting.
:::

::: reveal myth
? "Grid search is the safe, thorough choice."
> It spends trials on unimportant hyperparameters; random search covers the important ones better for the same budget.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? You want to halve the smallest gap you can detect. How many seeds per arm do you need, relative to now?
- [ ] Twice as many
- [x] Four times as many
- [ ] The same, with a bigger eval
- [ ] Eight times as many
> **B.** The detectable gap scales with 1/√n, so halving it takes 4× the seeds (or a metric with half the noise).
:::

::: reveal
? Why do cloze formulations help pretraining ablations?
> Small models score near chance on multiple-choice letter formats; cloze scoring of the answer text gives a smoother, more monotonic signal with lower seed variance (MMLU-Cloze σ 0.22 vs 0.57).
:::

::: reveal
? What is signal-to-noise ratio for a benchmark?
> Signal: the spread of scores between models of similar compute (relative dispersion). Noise: the relative standard deviation of one run over its final checkpoints. High SNR predicts reliable small-to-large decisions.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">An ablation is a measurement: if the gap is smaller than the seed noise, you learned nothing.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Labs choose data, architecture and hyperparameters from small runs. Each run's score varies with the seed, by about 0.2 to 0.8 points on common benchmarks at 7B. So run several seeds, prefer low-noise metrics like cloze formats or likelihoods, pick benchmarks with a high signal-to-noise ratio, confirm that the small scale ranks recipes like the target scale (DataDecide: about 80% of comparisons from 150M to 1B), and search hyperparameters randomly with early stopping.</p></div>
    <div class="recap"><div><span><b>Noise floor:</b> seed variance sets the smallest effect you can see</span></div><div><span><b>Metric:</b> cloze and likelihood metrics are less noisy</span></div><div><span><b>Scale:</b> check that small runs rank recipes like large ones</span></div><div><span><b>Search:</b> random search + early stopping beats grids</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/evals/05_experiments.ipynb" target="_blank" rel="noopener">05 · Experiments: seed noise, A/B sample size and the cost of peeking</a> <span style="color:var(--faint)">· 30 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/evals/05_experiments.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../09-hallucination/index.html">09 · Hallucination and factuality →</a> · Previous: <a href="../07-arenas/index.html">← 07</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
