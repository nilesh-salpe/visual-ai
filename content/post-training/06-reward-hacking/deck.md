---
title: Reward Hacking and Overoptimization
body:
  data-deck: Reward hacking and overoptimization
  data-home: ../index.html
  data-home-label: Post-training
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'proxy RM :: trained on limited data :: b'
  - 'optimize :: best-of-n or RL :: c'
  - 'KL grows :: policy drifts from start :: d'
  - 'gold rises, then falls :: proxy keeps rising :: a'
  caption: 'Goodhart''s law: when a measure becomes a target, it ceases to be a good measure.'
example:
  title: 'Worked example: the KL cost of best-of-n'
  setup: KL_bon = log n − (n − 1)/n (nats), from Stiennon et al.
  steps:
  - 'n = 2: log 2 − 1/2 = <b>0.19</b>.'
  - 'n = 16: log 16 − 15/16 = <b>1.84</b>.'
  - 'n = 1,024: <b>5.93</b>. KL grows like log n: each doubling of n adds ~0.69 nats.'
  - In notebook 06's simulation, gold reward peaks near n = 8 (KL ≈ 1.2) and falls below its starting value by n = 1,024, while the proxy keeps rising.
  result: Pushing harder costs KL; past the peak, extra proxy score is mostly exploitation.
traps:
  tricks:
  - 'Measure optimization in KL. :: Gold vs √KL follows d(α − βd) for best-of-n.'
  - 'Bigger, fresher RMs. :: Overoptimization coefficients scale smoothly with RM size; refresh data each round.'
  - 'Prefer checkable rewards. :: Where possible, use verifiers (deck 08).'
  traps:
  - 'RM score up ⇒ better model. :: Only before the peak.'
  - 'Best-of-n is "safe". :: It optimizes too; KL grows with log n.'
  - 'Ignoring length. :: A common exploited feature is simply longer answers.'
papers:
- gao
- stiennon
- instructgpt
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Post-training · 06</div>
    <h1>Reward hacking and overoptimization</h1>
    <p class="sub">Why optimizing a learned reward model too hard makes the model worse, how to measure "too hard" with KL (Kullback-Leibler divergence), and the mitigations labs use.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>A reward model is a proxy trained on limited data. The harder RL (reinforcement learning) or best-of-n pushes on it, the more it finds the RM's blind spots: the proxy score climbs while the real quality falls.</div>
      <div class="c"><b>Core idea</b>Treat optimization as a <b>budget measured in KL</b> from the starting policy. True ("gold") reward rises then falls as KL grows (Gao et al. 2022), so limit KL, refresh the reward model, and prefer rewards that can't be gamed.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## The proxy keeps rising; the truth doesn't <span class="ill">simulation</span>

Best-of-n against a flawed reward model (notebook 06): the proxy RM partly mistakes "length" for quality, while the true (gold) reward penalizes extreme length. Move n. The x-axis is √KL, the distance from the base policy.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">best-of-n <input type="range" id="hN" min="0" max="10" step="1" value="3"> <output id="hNo"></output></label></div>
  <svg id="hSvg" viewBox="0 0 660 260" style="margin-top:10px" role="img" aria-label="Proxy vs gold reward"></svg>
  <div class="legend"><span><i style="background:var(--b)"></i>proxy RM score</span><span><i style="background:var(--a)"></i>gold reward (change)</span><span><i style="background:var(--faint)"></i>fit d(α − βd)</span></div>
  <p class="readout" id="hOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why a reward model can be gamed

::: cards grid3
### [d] Trained on a narrow distribution
The RM saw outputs from earlier models. As the policy improves, it produces text the RM has never been checked on.

### [b] Spurious features
If longer or more confident answers tended to win in the data, the RM may reward length or confidence itself, even when they don't help.

### [c] An optimizer finds every flaw
RL is a search for high-scoring outputs. Any systematic error in the RM is a direction the search will follow. Goodhart's law: "When a measure becomes a target, it ceases to be a good measure."
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What happens as you push harder?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? You increase n in best-of-n (or train RL longer) against a fixed, imperfect reward model. What does the true quality typically do?
- [ ] Keeps improving, more slowly
- [x] Rises, peaks, then declines
- [ ] Declines from the start
- [ ] Stays flat
> <b>B.</b> Gao et al. find gold reward follows d(α − βd) for best-of-n and d(α − β·log d) for RL, with d = √KL: an initial gain, a peak, then decline, while the proxy score keeps increasing.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Measure optimization in KL

::: cards grid3
### [a] KL as the distance travelled
How far the optimized policy is from where it started. Best-of-n has an exact formula: KL<sub>bon</sub> = log n − (n−1)/n, which grows roughly like log n.

### [b] Predictable curves
Gold reward R(d), with d = √KL:<br>best-of-n: <b>d(α − βd)</b><br>RL: <b>d(α − β log d)</b><br>The coefficients scale smoothly with the reward model's size.

### [e] The KL penalty is a brake
RLHF (reinforcement learning from human feedback)'s −β·KL term (deck 05) caps how far the policy goes, holding it near the region where the RM is trustworthy.
:::

<div class="deep"><h4>How Gao et al. measured this</h4><p>Real human labels are too expensive to sweep, so they used a large "gold-standard" reward model as stand-in ground truth, trained smaller proxy RMs on labels from it, optimized policies against the proxies, and scored the results with the gold RM. That synthetic setup made the rise-then-fall curve measurable across many sizes.</p></div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## What the optimizer actually selected <span class="ill">simulation</span>

The same simulation: average features of the response picked by best-of-n. Helpfulness rises at first, but the optimizer increasingly buys proxy score with "length", which the gold reward penalizes.
{: .lede}

<div class="visual">
  <svg id="sSvg" viewBox="0 0 660 230" role="img" aria-label="Selected features vs n"></svg>
  <div class="legend"><span><i style="background:var(--a)"></i>helpfulness of chosen answer</span><span><i style="background:var(--d)"></i>"length" of chosen answer</span></div>
</div>

<div class="deep"><h4>Real-world versions</h4><p>Commonly reported symptoms include answers that grow longer without getting better, excessive hedging or flattery, and confident wording that the RM likes. Notebook 06 is a two-feature toy: the mechanism (a correlated but wrong feature exploited by search) is the general one.</p></div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Mitigations

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Mitigation</th><th>How it helps</th></tr>
  <tr><td>KL penalty / early stopping</td><td>Stop before the gold curve turns down; β or the step count sets the budget</td></tr>
  <tr><td>Bigger, better reward models</td><td>Overoptimization coefficients scale smoothly with RM size (Gao et al.)</td></tr>
  <tr><td>Iterate: fresh comparisons on the current policy</td><td>Keeps the RM accurate where the policy now is. Llama 2 ran RLHF-V1 to V5; Llama 3 ran six rounds</td></tr>
  <tr><td>Several reward models</td><td>Llama 2 used separate helpfulness and safety RMs</td></tr>
  <tr><td>Verifiable rewards</td><td>For maths and code, a checker is much harder to game than a learned scorer (deck 08)</td></tr>
  <tr><td>Watch the outputs</td><td>Track length, refusal rate and human spot checks, not only the RM score</td></tr>
</table></div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why the curve turns down

::: cards grid2
### [a] Early: real gains
Near the start, the RM's ranking is mostly right, so picking higher-scoring answers picks better answers.

### [d] Later: errors dominate
The biggest proxy scores come increasingly from the RM's mistakes. Selection pressure concentrates on exactly those outputs.

### [b] The fit is good
In our toy, d(1.20 − 0.52d) predicts every simulated point within ~0.05, with a peak near KL ≈ 1.4 nats (n ≈ 8).

### [e] Lesson
A reward model's score is evidence, not a target. More optimization is not automatically better.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "If the reward model score goes up, the model got better."
> Only up to a point. Past the peak, proxy score and true quality move in opposite directions.
:::

::: reveal myth
? "Best-of-n is safe because it doesn't change the model."
> It still optimizes against the RM. KL<sub>bon</sub> = log n − (n−1)/n grows with n, and so does exploitation.
:::

::: reveal myth
? "Reward hacking is a bug in the RL algorithm."
> It is a property of optimizing any imperfect proxy. A perfect optimizer hacks harder.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? KL of best-of-2 from the base policy?
- [ ] 0
- [x] log 2 − 0.5 ≈ 0.19
- [ ] log 2 ≈ 0.69
- [ ] 1
> <b>log 2 − 1/2 ≈ 0.19 nats.</b>
:::

<div class="quiz ">
  <p class="qq">Gao et al.'s functional forms for gold reward vs d = √KL?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Best-of-n: d(α − βd). RL: d(α − β log d). Both rise then fall.</div>
</div>

<div class="quiz ">
  <p class="qq">Name three mitigations for reward hacking.</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">A KL penalty or early stopping; larger and fresher reward models (new comparisons each round); verifiable rewards where possible; multiple RMs; monitoring length and spot checks.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Optimizing a learned reward model is a KL budget: true quality rises, peaks and falls while the proxy keeps climbing, so cap KL and keep the reward honest.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>A reward model is a proxy trained on a narrow slice of outputs. Best-of-n sampling and RL are searches for high proxy scores, so the harder they push, the more they find the reward model's mistakes. Gao and colleagues measured this: plotted against the square root of KL from the starting policy, the true reward follows d times alpha minus beta d for best-of-n and d times alpha minus beta log d for RL, rising then falling while the proxy keeps increasing. Best-of-n's KL is log n minus n minus one over n. Mitigations are a KL penalty or early stopping, bigger and regularly refreshed reward models, and verifiable rewards where possible.</p></div>

<div class="recap"><div><span><b>Problem:</b> the RM is a proxy; optimization finds its errors (Goodhart).</span></div><div><span><b>Core idea:</b> measure optimization in KL; gold reward vs √KL rises then falls.</span></div><div><span><b>Fixes:</b> KL penalty, early stopping, bigger and fresher RMs, verifiable rewards, monitoring.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/post-training/06_overoptimization.ipynb" target="_blank" rel="noopener">06 · Reward hacking: best-of-n against a flawed reward model</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/post-training/06_overoptimization.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../07-dpo-and-friends/index.html">07 · DPO, KTO and rejection sampling →</a> · Previous: <a href="../05-rlhf-ppo/index.html">← 05</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Gao, Schulman & Hilton 2022, "Scaling Laws for Reward Model Overoptimization" (functional forms, KL_bon); Stiennon et al. 2020 (App. G.3); Ouyang et al. 2022 (per-token KL penalty); Touvron et al. 2023 (Llama 2 iterative RLHF V1–V5).</p>

<!-- slide id="s-papers" from="papers" -->
