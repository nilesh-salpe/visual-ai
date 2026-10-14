---
title: RLHF with PPO
body:
  data-deck: RLHF with PPO
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
  - 'prompts :: from a dataset :: f'
  - 'policy samples :: current model writes answers :: c'
  - 'score :: RM reward − β·KL to SFT :: b'
  - 'advantages :: value model baseline :: a'
  - 'clipped update :: several epochs per batch :: e'
  loop: '4 -> 1 :: repeat: sample again from the updated policy'
  caption: 'Four models: policy and value (trained), reference and reward model (frozen).'
example:
  title: 'Worked example: what clipping does to one sample'
  setup: A sample with advantage Â = +1. After a few updates the policy gives it 1.5× its old probability (ratio ρ = 1.5). ε = 0.2.
  steps:
  - 'Unclipped term: ρ·Â = <b>1.50</b>.'
  - 'Clipped term: clip(ρ, 1 − ε, 1 + ε)·Â = <b>1.20</b>.'
  - 'PPO takes the minimum: <b>1.20</b>, a flat region, so this sample stops pushing the policy further.'
  - 'With Â = −1 and ρ = 0.5, the clipped term is −0.8 and the minimum is −0.8, again flat: no reward for pushing a bad sample below 0.8×.'
  result: Clipping bounds how far any single sample can move the policy within one batch, which makes several epochs per batch safe.
traps:
  tricks:
  - 'Objective: r − β·log(π/π_SFT). :: Exact optimum π* ∝ π_SFT·e^(r/β).'
  - 'ε = 0.2. :: The PPO paper''s default clip range.'
  - 'PPO-ptx. :: Mix pretraining gradients in to reduce the alignment tax.'
  traps:
  - 'Dropping the KL term. :: The policy then exploits the reward model.'
  - 'Confusing value model and reward model. :: The RM scores full answers; the value model predicts reward per token.'
  - 'Underestimating memory. :: Four models, two with optimizer state, plus generation in the loop.'
papers:
- ppo
- instructgpt
- stiennon
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Post-training · 05</div>
    <h1>RLHF with PPO</h1>
    <p class="sub">Optimizing a language model against a reward model: the KL-penalized (KL = Kullback-Leibler divergence) objective, PPO (Proximal Policy Optimization)'s clipped update, the four models in memory, and the "alignment tax".</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>We have a reward model. We want the policy to produce higher-scoring answers, but naive policy gradients are unstable, and maximizing an imperfect reward model without limits produces garbage that scores well.</div>
      <div class="c"><b>Core idea</b>Maximize <b>r(x, y) − β·KL(π ‖ π_SFT)</b> with <b>PPO</b>: sample answers, score them, and take several small, clipped policy-gradient steps per batch so no update moves the policy too far.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Four models at once

A PPO step for an LLM (large language model) involves four networks. Two are trained, and two are frozen but must still run a forward pass on every sample. For a 7B policy that is a lot of memory before activations.
{: .lede}

<div class="visual">
  <svg id="fSvg" viewBox="0 0 660 230" role="img" aria-label="Four models in PPO"></svg>
  <div class="infobox" style="background:var(--panel-2);border-radius:10px;padding:12px 14px;margin-top:10px;font-size:14px;color:var(--muted)" id="fInfo">Click a model.</div>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## What goes wrong with plain policy gradients

::: cards grid3
### [d] High variance
One scalar reward for a whole answer of hundreds of tokens gives a noisy gradient. A baseline (value function) is needed to tell "better than expected" from "worse".

### [b] Steps that are too big
A single large update can collapse the policy (repeating one phrase, say), and on-policy data from the old policy no longer describes the new one.

### [c] Unlimited optimization
The reward model is wrong somewhere. Without a constraint, the policy finds those spots: odd phrasing, excessive length, flattery.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What does the KL term do?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

<div class="quiz">
  <p class="qq">RLHF (reinforcement learning from human feedback) maximizes r(x,y) − β·log(π_RL(y|x)/π_SFT(y|x)). What happens as β grows large?</p>
  <div class="opts">
  <button>A. The policy ignores the reward model</button>
  <button data-ok>B. The policy stays close to the SFT model and gains less reward</button>
  <button>C. Training becomes faster</button>
  <button>D. The reward model is updated</button>
  </div>
  <div class="why"><b>B.</b> The penalty term, averaged over samples, is β·KL(π‖π_SFT). A large β makes drifting from the SFT (supervised fine-tuning) model expensive, trading reward for staying where the reward model is trustworthy. The exact optimum is π* ∝ π_SFT·exp(r/β).</div>
</div>

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## The objective and the update

<div class="grid2">
  <div class="card a"><h3>What is maximized</h3><p>InstructGPT eq. 2: E[ r<sub>θ</sub>(x,y) − β·log(π<sup>RL</sup>(y|x)/π<sup>SFT</sup>(y|x)) ] + γ·E<sub>pretrain</sub>[log π<sup>RL</sup>(x)]. The KL penalty is applied per token; the γ term (PPO-ptx) mixes in pretraining gradients.</p></div>
  <div class="card b"><h3>How it is maximized (PPO)</h3><p>L<sup>CLIP</sup> = E[ min(ρ·Â, clip(ρ, 1−ε, 1+ε)·Â) ], with ρ the new/old probability ratio and ε = 0.2 in the PPO paper. Several epochs of minibatch updates per batch of samples.</p></div>
</div>

<div class="deep"><h4>Advantages for text</h4><p>The reward model scores the full answer once. The per-token KL penalty gives every token a small reward too. A <b>value model</b> (InstructGPT: initialized from the RM) predicts the expected future reward at each token, and the advantage Â is how much better the actual outcome was than predicted (usually with generalized advantage estimation). GRPO (deck 08) replaces this value model with the average reward of a group of samples.</p></div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## PPO's clip, visualized

<p class="lede">The contribution of one sample to L<sup>CLIP</sup> as the policy changes its probability (ratio ρ = π_new/π_old). For a good sample (Â &gt; 0) the gain stops growing once ρ &gt; 1+ε; for a bad one (Â &lt; 0) the gain from pushing it down stops once ρ &lt; 1−ε. Flat regions have zero gradient.</p>

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">ε <input type="range" id="cE" min="0.05" max="0.5" step="0.05" value="0.2"> <output id="cEo"></output></label><div class="seg" id="cA"><button data-v="1" class="on">Â &gt; 0 (good sample)</button><button data-v="-1">Â &lt; 0 (bad sample)</button></div></div>
  <svg id="cSvg" viewBox="0 0 660 240" style="margin-top:10px" role="img" aria-label="Clipped objective"></svg>
</div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## β is the leash <span class="ill">toy simulation</span>

<p class="lede">Notebook 05 trains a one-step "policy" over 8 responses with PPO at several β. Expected reward and KL from the reference both fall as β rises, and PPO lands on the exact optimum π* ∝ π_ref·e<sup>r/β</sup> each time.</p>

<div class="visual"><svg id="kSvg" viewBox="0 0 660 240" role="img" aria-label="Reward and KL vs beta"></svg>
  <div class="legend"><span><i style="background:var(--a)"></i>E[reward]</span><span><i style="background:var(--d)"></i>KL(π‖π_ref)</span></div></div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why RLHF with PPO worked

::: cards grid2
### [a] Learns from its own samples
Online RL (reinforcement learning) scores what the current policy actually writes, so it fixes the model's own failure modes, not just copies demonstrations.

### [e] Stable enough at scale
Clipping plus the KL leash keep updates small. InstructGPT, Llama 2-Chat (PPO after rejection-sampling rounds) and many others used it.

### [b] The alignment tax, and PPO-ptx
InstructGPT saw regressions on some public NLP (natural language processing) datasets after RLHF. Mixing pretraining gradients into PPO (PPO-ptx) greatly reduced them "without compromising labeler preference scores".

### [d] The costs
Four models, generation inside the training loop, many sensitive hyperparameters (β, ε, learning rates, GAE (generalized advantage estimation) settings). Hence the search for simpler methods (decks 07–08).
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "PPO simply maximizes the reward model's score."
> It maximizes reward <b>minus β·KL</b> to the SFT model. Without that term the policy would exploit the reward model.
:::

::: reveal myth
? "The value model and the reward model are the same thing."
> The RM scores complete answers. The value model predicts expected future reward at each token to compute advantages. InstructGPT initializes the value model from the RM, but trains it separately.
:::

::: reveal myth
? "Clipping limits the size of the gradient."
> It removes the incentive to move a sample's probability ratio beyond 1 ± ε in the helpful direction. Gradients from samples in the flat region are zero; others are unchanged.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Which four models does a typical PPO-based RLHF step use?
- [x] Policy, reference, reward model, value model
- [ ] Policy, teacher, student, critic
- [ ] Encoder, decoder, RM, tokenizer
- [ ] Only the policy
> <b>Policy</b> (trained), <b>reference/SFT</b> (frozen, for KL), <b>reward model</b> (frozen), <b>value model</b> (trained).
:::

<div class="quiz ">
  <p class="qq">What is the closed-form optimum of E[r] − β·KL(π‖π_ref)?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">π*(y) ∝ π_ref(y)·exp(r(y)/β). Higher reward answers are up-weighted exponentially, more strongly the smaller β is. DPO (Direct Preference Optimization) is built on this formula.</div>
</div>

<div class="quiz ">
  <p class="qq">What problem does PPO-ptx address?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">The alignment tax: RLHF degraded some benchmark performance. Mixing pretraining log-likelihood gradients into the update (γ > 0) reduced the regressions while keeping preference scores.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">RLHF maximizes reward-model score minus β·KL to the SFT model, using PPO's clipped updates to stay stable, at the cost of four models and much tuning.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Given a reward model, RLHF samples answers from the current policy, scores them, and updates the policy to raise the score while paying a per-token KL penalty for drifting from the SFT model, because the reward model is only trustworthy near its training data. PPO makes the update stable by clipping the probability ratio between new and old policy, so several gradient steps per batch can't move any answer's probability too far. A value model supplies per-token advantages. The exact optimum of reward minus beta KL is the reference policy times exp of reward over beta. InstructGPT also mixed in pretraining gradients to reduce the alignment tax.</p></div>

<div class="recap"><div><span><b>Problem:</b> optimize against an imperfect RM without instability or exploitation.</span></div><div><span><b>Core idea:</b> max r − β·KL(π‖π_SFT) with PPO's clipped ratio (ε = 0.2).</span></div><div><span><b>Costs:</b> policy, reference, RM and value model in memory; many hyperparameters.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/post-training/05_ppo_toy.ipynb" target="_blank" rel="noopener">05 · PPO with a KL penalty on a toy policy</a> <span style="color:var(--faint)">· 45 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/post-training/05_ppo_toy.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../06-reward-hacking/index.html">06 · Reward hacking and overoptimization →</a> · Previous: <a href="../04-reward-models/index.html">← 04</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Ouyang et al. 2022 (InstructGPT §3.5 eq. 2: per-token KL penalty, PPO-ptx, value function initialized from the RM); Schulman et al. 2017, "Proximal Policy Optimization Algorithms" (eq. 7, ε = 0.2); Stiennon et al. 2020; Touvron et al. 2023 (Llama 2 §3.2.3).</p>

<!-- slide id="s-papers" from="papers" -->
