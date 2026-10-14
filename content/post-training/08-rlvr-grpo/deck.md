---
title: RLVR and GRPO
body:
  data-deck: RLVR and GRPO
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
  - 'prompt :: maths, code, format :: f'
  - 'G samples :: from the current policy :: c'
  - 'verifier :: 1 if correct, else 0 :: b'
  - '(r − mean) / std :: group-relative advantage :: a'
  - 'clipped update + KL :: no critic :: e'
  loop: '4 -> 0 :: next batch of prompts'
  caption: The group is its own baseline; a checker replaces the reward model.
example:
  title: 'Worked example: advantages and dead groups'
  setup: GRPO with group size G = 4.
  steps:
  - 'Rewards [1, 0, 0, 1]: mean 0.5, std 0.5 → advantages <b>[+1, −1, −1, +1]</b>.'
  - 'Rewards [1, 0, 0, 0]: mean 0.25, std 0.433 → advantages <b>[+1.73, −0.58, −0.58, −0.58]</b>; a rare success gets a big push.'
  - 'A prompt the model solves 90% of the time: P(all 4 right or all 4 wrong) = 0.9⁴ + 0.1⁴ = <b>65.6%</b> of groups give zero gradient.'
  - 'At 15% success and G = 8: 27.2% dead groups; at G = 32: 0.55%.'
  result: Filter prompts to useful difficulty and use larger groups on hard prompts so most samples carry signal.
traps:
  tricks:
  - 'Â = (r − mean)/std within the group. :: Applied to every token of that sample.'
  - 'Dead groups: p^G + (1 − p)^G. :: Too easy or too hard prompts waste compute.'
  - 'Keep a small KL. :: DeepSeek-R1 used a KL coefficient of 0.001.'
  traps:
  - 'Assuming every sample teaches. :: Equal rewards in a group give zero advantage.'
  - 'Dropping the reference model. :: GRPO drops the critic, not the KL reference.'
  - 'Using RLVR for open-ended tasks. :: Writing quality and safety still need preference signals.'
papers:
- deepseekmath
- r1
- tulu3
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Post-training · 08</div>
    <h1>RL with verifiable rewards and GRPO</h1>
    <p class="sub">How reasoning models are trained: replace the learned reward model with a checker, replace the critic with a group of samples, and let RL (reinforcement learning) discover long chains of thought.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Learned reward models can be gamed and PPO (Proximal Policy Optimization)'s critic costs a whole extra model. For maths and code, correctness can often be checked exactly, so why approximate it?</div>
      <div class="c"><b>Core idea</b><b>RLVR (reinforcement learning with verifiable rewards)</b>: reward = 1 if a checker accepts the answer (plus format rules). <b>GRPO (Group Relative Policy Optimization)</b>: sample a group of G answers per prompt and use (r − mean)/std within the group as each answer's advantage, so no value model is needed.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Some answers can simply be checked

::: cards grid3
### [a] Maths
The final answer, in a required format (for example inside a box), is compared with the reference solution. DeepSeek-R1 calls this an <b>accuracy reward</b>.

### [b] Code
Run the program against test cases; reward the pass rate or all-pass.

### [e] Format and constraints
Did the model put its reasoning between the required tags, answer in the requested language, follow length limits? R1's <b>format reward</b> checks the thinking tags.
:::

<div class="deep"><h4>Why this matters</h4><p>A learned reward model is a proxy with blind spots (deck 06). A checker is exact for what it checks, so there is far less to exploit. Tülu 3 named the approach <b>Reinforcement Learning with Verifiable Rewards (RLVR)</b>; DeepSeek-R1-Zero used rule-based rewards for maths, coding and logic and no neural reward model for them.</p></div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## What PPO-style RLHF costs here

::: cards grid3
### [d] A critic as big as the policy
PPO's value model is usually the same size as the policy, with its own gradients and optimizer state.

### [b] Critics are hard for long outputs
Predicting the expected final reward at every token of a long chain of thought is a hard regression problem, and a bad critic gives bad advantages.

### [c] Reward models drift
A learned RM goes stale and can be hacked; maths answers don't have that problem.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Compute group advantages

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

<div class="quiz">
  <p class="qq">GRPO samples a group of 4 answers to one maths question. Rewards are [1, 0, 0, 1]. What are the advantages?</p>
  <div class="opts">
  <button>A. [1, 0, 0, 1]</button>
  <button>B. [0.5, −0.5, −0.5, 0.5]</button>
  <button data-ok>C. [1, −1, −1, 1]</button>
  <button>D. [0.25, 0.25, 0.25, 0.25]</button>
  </div>
  <div class="why"><b>C.</b> mean = 0.5, std = 0.5, so Â = (r − 0.5)/0.5 = [1, −1, −1, 1]. Every token of a correct answer is pushed up, every token of a wrong one pushed down, relative to this group.</div>
</div>

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## GRPO in one picture

<div class="grid3">
  <div class="card a"><h3>Sample a group</h3><p>For each question, sample G outputs {o₁ … o_G} from the old policy.</p></div>
  <div class="card b"><h3>Normalize within the group</h3><p>Â<sub>i</sub> = (r<sub>i</sub> − mean(r)) / std(r), applied to every token of o<sub>i</sub>. "GRPO foregoes the critic model, instead estimating the baseline from group scores."</p></div>
  <div class="card e"><h3>PPO-style update</h3><p>Clipped probability ratios as in PPO, plus a KL (Kullback-Leibler divergence) penalty to a reference model added to the loss (R1 used a KL coefficient of 0.001).</p></div>
</div>

<div class="deep"><h4>Why a group baseline works</h4><p>A baseline only has to be "what reward would I expect for this prompt?". Several samples for the <b>same</b> prompt estimate that directly, with no network. The cost moves from memory (a critic) to compute (G samples per prompt), which also gives the reward signal more chances to be non-zero.</p></div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## When does a group teach anything?

If every answer in a group is right, or every answer is wrong, all advantages are 0 and the prompt contributes nothing. Probability of a "dead" group = p<sup>G</sup> + (1−p)<sup>G</sup>, where p is the chance of a correct answer. Pick p and G.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">P(correct) p <input type="range" id="dP" min="0.01" max="0.99" step="0.01" value="0.15"> <output id="dPo"></output></label>
    <label class="ctl">group size G <input type="range" id="dG" min="2" max="64" step="1" value="8"> <output id="dGo"></output></label>
  </div>
  <svg id="dSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Dead group probability"></svg>
  <p class="readout" id="dOut"></p>
</div>

<div class="deep"><h4>Practical consequence</h4><p>Prompts the model always solves, or never solves, waste samples. RLVR datasets are therefore filtered towards problems of useful difficulty, and larger G helps on hard prompts. In notebook 08, a toy "base model" with 16% accuracy reaches 0.88 / 0.95 / 0.99 after 150 iterations with G = 2 / 4 / 16.</p></div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## What DeepSeek reported

<div class="visual"><div id="rBars"></div></div>

<div class="grid2" style="margin-top:12px">
  <div class="card a"><h3>R1-Zero: RL without SFT</h3><p>RL with rule-based accuracy and format rewards directly on the base model. AIME (American Invitational Mathematics Examination) 2024 pass@1 went from 15.6% to 77.9%, and responses grew longer as the model learned to think longer. The paper shows an "aha moment" where an intermediate checkpoint learns to stop and re-examine its own solution.</p></div>
  <div class="card b"><h3>R1: fixing R1-Zero's rough edges</h3><p>R1-Zero had "poor readability and language mixing". R1 adds cold-start long chain-of-thought data, a language consistency reward during RL, and a multi-stage pipeline integrating rejection sampling, RL and SFT (supervised fine-tuning).</p></div>
</div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why RLVR + GRPO took off

::: cards grid2
### [a] Hard-to-hack rewards
A checker either accepts the answer or not. The model must actually get it right (or find a loophole in the checker, so checkers need care too).

### [e] Cheaper RL
No critic, no learned RM for these tasks: two models (policy and reference) instead of four.

### [b] Reasoning emerges
Rewarding only final correctness, R1-Zero developed longer reasoning, self-verification and reflection by itself, without demonstrations of how to reason.

### [d] Limits
Only for checkable tasks. Open-ended writing and helpfulness still need preference models, which is why R1 combines RLVR with other stages.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Every sampled answer produces a gradient in GRPO."
> Groups where all answers get the same reward have zero advantages. With 0/1 rewards, too-easy and too-hard prompts teach nothing.
:::

::: reveal myth
? "GRPO doesn't need a reference model."
> It drops the <b>critic</b>, not the reference. A KL penalty to a reference policy is still part of the objective (coefficient 0.001 in R1).
:::

::: reveal myth
? "RLVR replaces preference tuning."
> Only where answers can be verified. General chat quality, tone and safety still rely on preference data or other reward models.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? What replaces the value model in GRPO?
- [ ] A reward model
- [x] The mean and std of rewards in a group of samples for the same prompt
- [ ] A moving average over the dataset
- [ ] Nothing; advantages are raw rewards
> <b>B.</b> The group statistics act as the baseline.
:::

<div class="quiz ">
  <p class="qq">Which two reward types did DeepSeek-R1-Zero use?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Rule-based <b>accuracy</b> rewards (is the final answer correct, e.g. checked inside a box or by test cases) and <b>format</b> rewards (is the reasoning inside the required tags), combined with equal weight.</div>
</div>

<div class="quiz ">
  <p class="qq">With p(correct) = 0.9 and G = 4, what fraction of groups give no signal?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">0.9⁴ + 0.1⁴ = 0.6561 + 0.0001 ≈ <b>66%</b>. Easy prompts mostly waste samples.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">RLVR rewards answers a checker accepts; GRPO uses the spread of rewards within a group of samples as the baseline, dropping the critic. Together they trained today's reasoning models.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>For maths, code and formats, correctness can be checked, so RL with verifiable rewards replaces the learned reward model with a rule: one if the answer is right, plus format checks. GRPO, from DeepSeekMath, removes PPO's value model too: sample a group of answers per prompt and use each answer's reward minus the group mean, divided by the group standard deviation, as its advantage, keeping PPO's clipping and a small KL penalty to a reference. Groups where every answer gets the same reward teach nothing, so prompt difficulty and group size matter. DeepSeek-R1-Zero used this with no SFT and went from 15.6 to 77.9 percent on AIME 2024, learning longer, self-checking reasoning along the way.</p></div>

<div class="recap"><div><span><b>Problem:</b> learned RMs can be hacked; PPO's critic is expensive.</span></div><div><span><b>Core idea:</b> verifier rewards + group-normalized advantages (r − mean)/std, no critic.</span></div><div><span><b>Results:</b> DeepSeekMath MATH 46.8→51.7%; R1-Zero AIME 15.6→77.9% with RL only.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/post-training/08_grpo_rlvr.ipynb" target="_blank" rel="noopener">08 · RL with verifiable rewards and GRPO</a> <span style="color:var(--faint)">· 45 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/post-training/08_grpo_rlvr.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../09-rlaif-constitutional-ai/index.html">09 · RLAIF and Constitutional AI →</a> · Previous: <a href="../07-dpo-and-friends/index.html">← 07</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Shao et al. 2024, "DeepSeekMath" (§4: GRPO, eq. for group-normalized advantage; GSM8K 82.9→88.2%, MATH 46.8→51.7%); DeepSeek-AI 2025, "DeepSeek-R1" (rule-based accuracy and format rewards, KL coefficient 0.001, AIME 2024 15.6%→77.9%, "aha moment", language consistency reward); Lambert et al. 2024 (Tülu 3, RLVR).</p>

<!-- slide id="s-papers" from="papers" -->
