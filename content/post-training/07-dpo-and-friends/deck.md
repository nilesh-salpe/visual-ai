---
title: DPO, KTO and Rejection Sampling
body:
  data-deck: DPO, KTO and rejection sampling
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
  - 'preference pair :: chosen y_w, rejected y_l :: f'
  - 'log-ratios :: log π/π_ref for each :: c'
  - 'margin :: β·(ratio_w − ratio_l) :: a'
  - 'loss :: −log σ(margin) :: e'
  caption: Two models (policy + frozen reference), no reward model, no sampling.
example:
  title: 'Worked example: one DPO step by hand'
  setup: β = 0.1. The reference gives the chosen and rejected answers 0.20 each; the policy now gives 0.30 and 0.10.
  steps:
  - 'Chosen log-ratio: log(0.30/0.20) = 0.405; rejected: log(0.10/0.20) = -0.693.'
  - Margin z = β·(0.405 − (-0.693)) = <b>0.1099</b>.
  - Loss = −log σ(z) = <b>0.6397</b> (it was log 2 = 0.6931 when policy = reference).
  - 'Gradient weight 1 − σ(z) = 0.473: still large, because with β = 0.1 the margin is small.'
  result: 'Implicit rewards: β·log ratio = +0.0405 (chosen) and -0.0693 (rejected). The policy is its own reward model.'
traps:
  tricks:
  - 'Implicit reward = β·log(π/π_ref). :: Z(x) cancels within a pair.'
  - 'Gradient focuses on mistakes. :: Weight 1 − σ(z) is largest when the pair is ranked wrongly.'
  - 'Iterate. :: Fresh pairs from the current model each round (Llama 3: six rounds).'
  traps:
  - 'No reference model. :: DPO needs a frozen reference; it defines the implicit reward.'
  - '"Can''t be hacked." :: It can overfit noisy or narrow pairs.'
  - 'β as a learning rate. :: β is the KL strength; small β allows bigger departures.'
papers:
- dpo
- kto
- llama2
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Post-training · 07</div>
    <h1>DPO, KTO and rejection sampling</h1>
    <p class="sub">Simpler routes to the RLHF (reinforcement learning from human feedback) objective: Direct Preference Optimization turns it into a classification loss, KTO (Kahneman-Tversky Optimization) needs only good/bad labels, and rejection sampling fine-tunes on the best of many samples.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>PPO-based (PPO = Proximal Policy Optimization) RLHF needs four models, generation inside the training loop and delicate tuning. Many teams want the benefit of preference data without running online RL (reinforcement learning).</div>
      <div class="c"><b>Core idea</b><b>DPO (Direct Preference Optimization)</b>: the RLHF optimum π* ∝ π_ref·e<sup>r/β</sup> lets you write the reward as β·log(π/π_ref), so the Bradley-Terry loss can be applied <b>directly to the policy</b>, with no reward model and no sampling.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## RLHF vs DPO, side by side

Both start from an SFT (supervised fine-tuning) model and preference pairs and target the same objective. Compare what each pipeline has to run.
{: .lede}

<div class="visual">
  <div class="seg" id="pSeg"><button data-v="rlhf" class="on">RLHF (RM + PPO)</button><button data-v="dpo">DPO</button></div>
  <svg id="pSvg" viewBox="0 0 660 200" style="margin-top:10px" role="img" aria-label="Pipeline comparison"></svg>
  <p class="readout" id="pOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## What makes PPO-based RLHF heavy

::: cards grid3
### [d] Generation in the loop
Every step samples full answers from the current policy: slow, and awkward to run efficiently next to training.

### [b] Four models
Policy, reference, reward model and value model must all fit, two of them with optimizer state.

### [c] Tuning
β, clipping ε, learning rates for two networks, advantage estimation settings. Instabilities are common.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## The implicit reward

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

<div class="quiz">
  <p class="qq">After DPO training, the policy gives answer y twice the probability the reference gives it (β = 0.1). What implicit reward does DPO assign to y, up to a per-prompt constant?</p>
  <div class="opts">
  <button>A. 0.1</button>
  <button data-ok>B. 0.1 · ln 2 ≈ 0.069</button>
  <button>C. 2</button>
  <button>D. It has no reward</button>
  </div>
  <div class="why"><b>B.</b> DPO's implicit reward is r̂(x,y) = β·log(π_θ(y|x)/π_ref(y|x)) = 0.1·ln 2 ≈ 0.069. "Your language model is secretly a reward model."</div>
</div>

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## The derivation in three lines

<div class="grid3">
  <div class="card a"><h3>1 · Known optimum</h3><p>The KL-regularized (KL = Kullback-Leibler divergence) RLHF objective has the closed-form solution π*(y|x) = π_ref(y|x)·exp(r(x,y)/β) / Z(x).</p></div>
  <div class="card b"><h3>2 · Invert it</h3><p>Solve for the reward: r(x,y) = β·log(π*(y|x)/π_ref(y|x)) + β·log Z(x). Any policy defines a reward this way.</p></div>
  <div class="card e"><h3>3 · Plug into Bradley-Terry</h3><p>In r(y_w) − r(y_l) the β·log Z(x) terms <b>cancel</b>, leaving a loss on the policy alone.</p></div>
</div>

<div class="eq">L<sub>DPO</sub> = −E[ log σ( β·log(π<sub>θ</sub>(y<sub>w</sub>)/π<sub>ref</sub>(y<sub>w</sub>)) − β·log(π<sub>θ</sub>(y<sub>l</sub>)/π<sub>ref</sub>(y<sub>l</sub>)) ) ]</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## What the gradient does

<p class="lede">The DPO gradient for one pair is (1 − σ(z))·β·(∇log π(y_w) − ∇log π(y_l)), where z is the current implicit-reward margin. Pairs the model already ranks correctly with a large margin get almost no weight; pairs it gets wrong get the most. Drag the margin.</p>

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">implicit margin z <input type="range" id="gZ" min="-6" max="6" step="0.1" value="-1"> <output id="gZo"></output></label></div>
  <svg id="gSvg" viewBox="0 0 660 220" style="margin-top:10px" role="img" aria-label="DPO gradient weight"></svg>
  <p class="readout" id="gOut"></p>
</div>

<div class="deep"><h4>Notebook 07 checks the theory</h4><p>On a toy 6-response problem with 20,000 simulated preference pairs, DPO converges to π* ∝ π_ref·e<sup>r/β</sup> (KL(π*‖π) ≈ 0.0008), and its implicit rewards match the hidden true rewards up to a constant: [−0.73, 0.20, −1.24, 1.23, −0.24, 0.78] vs [−0.75, 0.25, −1.25, 1.25, −0.25, 0.75]. With only 200 pairs the KL is 0.19: offline data limits it.</p></div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## The family

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Method</th><th>Signal needed</th><th>Idea</th></tr>
  <tr><td><b>Rejection sampling FT (fine-tuning)</b> (best-of-n + SFT)</td><td>a reward model</td><td>Sample K answers, keep the highest-scoring one, fine-tune on it. Llama 2 used only this up to RLHF-V4, then PPO on top.</td></tr>
  <tr><td><b>DPO</b> (2023)</td><td>preference pairs</td><td>Bradley-Terry loss on the policy's implicit reward β·log(π/π_ref). No RM, no sampling.</td></tr>
  <tr><td><b>KTO</b> (2024)</td><td>a binary desirable / undesirable label per output</td><td>Uses a prospect-theory (Kahneman–Tversky) utility; no pairs needed. Matches or exceeds DPO from 1B to 30B parameters in the paper.</td></tr>
  <tr><td><b>Iterative DPO</b></td><td>fresh pairs each round</td><td>Generate with the current model, label, run DPO, repeat. Llama 3: six rounds of SFT, rejection sampling and DPO.</td></tr>
</table></div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why DPO caught on, and its limits

::: cards grid2
### [a] Simple and stable
A supervised loss on fixed data: two models (policy and frozen reference), no generation, few hyperparameters (mainly β).

### [e] Same target as RLHF
In the ideal case it optimizes "the same objective as existing RLHF algorithms" (the paper), so it is not a weaker objective, just a different optimizer.

### [b] Offline data limits it
It learns only from the pairs it is given. If they don't cover what the current policy does, it can't correct those behaviours, which is why labs iterate with fresh on-policy pairs.

### [d] Still a proxy
The implicit reward is fit to finite, noisy labels. Pushing β small or training long can overfit the pairs, the DPO version of reward hacking.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

<div class="quiz myth">
  <p class="qq">"DPO doesn't need a reference model."</p>
  <button class="reveal">Why is this wrong?</button>
  <div class="why">It does: both log-ratios are taken against a frozen π_ref (usually the SFT model). The reference defines the implicit reward and the KL anchor.</div>
</div>

::: reveal myth
? "DPO has no reward model, so it can't be reward-hacked."
> The policy is its own reward model. It can still overfit noisy or narrow preference data and drift in odd directions.
:::

::: reveal myth
? "β in DPO is a learning rate."
> β is the KL strength from the RLHF objective: a small β allows larger departures from the reference.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

<div class="quiz">
  <p class="qq">Why does the partition function Z(x) disappear from the DPO loss?</p>
  <div class="opts">
  <button>A. It is approximated as 1</button>
  <button data-ok>B. It cancels in the reward difference between y_w and y_l for the same prompt</button>
  <button>C. It is learned separately</button>
  <button>D. β absorbs it</button>
  </div>
  <div class="why"><b>B.</b> Both responses share the same prompt x, so β·log Z(x) cancels in r(y_w) − r(y_l).</div>
</div>

<div class="quiz ">
  <p class="qq">What does KTO need instead of preference pairs?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">A binary label per output: desirable or undesirable. It optimizes a prospect-theory-inspired utility, so data without paired comparisons can be used.</div>
</div>

<div class="quiz ">
  <p class="qq">How did Llama 2 use rejection sampling?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Sample K answers per prompt, take the best by the reward model, fine-tune on those. Only rejection sampling up to RLHF-V4, then PPO applied on top of the rejection-sampling checkpoint.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">DPO rewrites the RLHF objective as a classification loss on β·log(π/π_ref), so preference data trains the policy directly, with no reward model or RL loop.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>PPO-based RLHF needs four models and generation inside training. DPO starts from the known optimum of the KL-regularized objective, the reference policy times exp of reward over beta, and inverts it: any policy implies a reward equal to beta times the log ratio to the reference, plus a per-prompt constant. Plugging that into the Bradley-Terry loss cancels the constant, giving a simple loss on preference pairs that needs only the policy and a frozen reference. Its gradient focuses on pairs the model gets wrong. KTO needs only good-or-bad labels, rejection sampling fine-tunes on the best of several samples, and labs iterate with fresh pairs because DPO only learns from the data it is given.</p></div>

<div class="recap"><div><span><b>Problem:</b> PPO RLHF: four models, generation in the loop, fragile tuning.</span></div><div><span><b>Core idea:</b> implicit reward β·log(π/π_ref); Bradley-Terry loss directly on the policy.</span></div><div><span><b>Family:</b> rejection sampling (best-of-n + SFT), KTO (binary labels), iterative DPO.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/post-training/07_dpo.ipynb" target="_blank" rel="noopener">07 · Direct Preference Optimization (DPO)</a> <span style="color:var(--faint)">· 40 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/post-training/07_dpo.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../08-rlvr-grpo/index.html">08 · RLVR and GRPO →</a> · Previous: <a href="../06-reward-hacking/index.html">← 06</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Rafailov et al. 2023, "Direct Preference Optimization: Your Language Model is Secretly a Reward Model" (§4, eq. 7); Ethayarajh et al. 2024, "KTO: Model Alignment as Prospect Theoretic Optimization"; Touvron et al. 2023 (Llama 2 §3.2.3, rejection sampling); Llama Team 2024 (Llama 3 §4: SFT, RS, DPO in six rounds).</p>

<!-- slide id="s-papers" from="papers" -->
