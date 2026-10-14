---
title: Reward Models
body:
  data-deck: Reward models
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
  - 'prompt + answer A ::  :: f'
  - 'prompt + answer B ::  :: f'
  - 'reward model :: SFT model + scalar head :: b'
  - 'σ(r_A − r_B) :: P(A preferred) :: c'
  - 'loss :: −log σ(r_w − r_l) :: a'
  caption: Only reward differences matter; the RM then scores millions of RL samples automatically.
example:
  title: 'Worked example: one comparison through the loss'
  setup: The RM scores the labeler's chosen answer 2.0 and the rejected one 0.5.
  steps:
  - P(chosen preferred) = σ(2.0 − 0.5) = σ(1.5) = <b>0.818</b>.
  - Loss for this pair = −log 0.818 = <b>0.201</b>.
  - 'If the RM had it backwards (0.5 vs 2.0): loss = −log σ(−1.5) = <b>1.701</b>, a much larger gradient.'
  - A ranking of K = 9 answers contributes C(9, 2) = <b>36</b> such pairs, grouped in one batch element.
  result: Bradley-Terry turns "which is better?" into a smooth loss on reward differences.
traps:
  tricks:
  - 'P(A ≻ B) = σ(r_A − r_B). :: A gap of 1.5 ≈ 82%.'
  - 'Normalize rewards before RL. :: Only differences are identified, so the offset is arbitrary.'
  - 'Group a ranking''s pairs. :: They share responses and are correlated.'
  traps:
  - 'Reading rewards as probabilities. :: They are unbounded scalars.'
  - 'Expecting 100% accuracy. :: Labelers disagree; there is a noise ceiling.'
  - 'Reusing a stale RM. :: As the policy improves, its outputs leave the RM''s training distribution.'
papers:
- instructgpt
- christiano
- llama2
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Post-training · 04</div>
    <h1>Reward models</h1>
    <p class="sub">How human comparisons become a scalar score: the Bradley-Terry model, the pairwise loss, rankings to pairs, and the limits of any learned reward.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>"Helpful, honest, harmless" can't be written as a formula. RL (reinforcement learning) needs a number for every sampled answer, and people can't label millions of samples during training.</div>
      <div class="c"><b>Core idea</b>Collect <b>comparisons</b> between answers, then train a model r(x, y) → scalar so that σ(r_w − r_l) matches how often people prefer y_w over y_l. That model scores RL samples automatically.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Comparisons are easier than scores

Ask five people to score an answer from 1 to 10 and you get five different calibrations. Ask which of two answers is better and they mostly agree. The Bradley-Terry model links reward <b>differences</b> to preference probabilities. Drag the gap.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">r(A) − r(B) <input type="range" id="bD" min="-5" max="5" step="0.1" value="1.5"> <output id="bDo"></output></label></div>
  <svg id="bSvg" viewBox="0 0 660 220" style="margin-top:10px" role="img" aria-label="Bradley-Terry curve"></svg>
  <p class="readout" id="bOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why not use a hand-written reward or direct scores?

::: cards grid3
### [d] No formula for "helpful"
Unlike a game score, quality depends on the request, the audience and subtle correctness. Any hand-written rule is easy to game.

### [b] Absolute ratings are noisy
Labelers disagree on what "7/10" means, and drift over time. Relative judgements are more consistent.

### [c] Humans can't be in the loop
PPO (Proximal Policy Optimization) samples millions of responses. A learned reward model answers instantly; humans label only a fixed dataset per round.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Read a reward model

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

<div class="quiz">
  <p class="qq">A reward model scores answer A at 2.0 and answer B at 0.5. Under Bradley-Terry, what is the predicted probability that a person prefers A?</p>
  <div class="opts">
  <button>A. 0.50</button>
  <button>B. 0.75</button>
  <button data-ok>C. about 0.82</button>
  <button>D. 0.99</button>
  </div>
  <div class="why"><b>C.</b> σ(2.0 − 0.5) = σ(1.5) = 1/(1 + e^−1.5) ≈ 0.82. Only the difference matters: scores of 102.0 and 100.5 predict exactly the same preference.</div>
</div>

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Architecture and loss

<div class="grid3">
  <div class="card a"><h3>Model</h3><p>InstructGPT: start from the SFT (supervised fine-tuning) model "with the final unembedding layer removed" and output one scalar for a (prompt, response) pair. They used 6B reward models; 175B RM training "could be unstable".</p></div>
  <div class="card b"><h3>Loss</h3><p>loss = −E[log σ(r(x, y_w) − r(x, y_l))]: maximize the likelihood of the observed choices under Bradley-Terry. Only differences are learned, so rewards are often normalized before RL.</p></div>
  <div class="card e"><h3>Data</h3><p>For each prompt, sample several model outputs and have labelers rank them. InstructGPT: K = 4 to 9 per prompt; Llama 2: binary comparisons with a strength label, over 1M of them.</p></div>
</div>

<div class="eq">loss(θ) = −1/C(K,2) · E<sub>(x, y_w, y_l)</sub> [ log σ( r<sub>θ</sub>(x, y_w) − r<sub>θ</sub>(x, y_l) ) ]   (InstructGPT eq. 1)</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## From a ranking to training pairs

A labeler ranks K responses. Every ordered pair becomes a comparison: K·(K−1)/2 of them. InstructGPT puts all pairs from one prompt in the <b>same batch element</b>, because they are strongly correlated and treating them as independent samples made the RM overfit.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">K responses ranked <input type="range" id="kK" min="2" max="9" step="1" value="4"> <output id="kKo"></output></label></div>
  <svg id="kSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Pairs from ranking"></svg>
  <p class="readout" id="kOut"></p>
</div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## How good can a reward model get? <span class="ill">simulation</span>

From notebook 04: simulated labelers choose with Bradley-Terry noise around a hidden true reward. Even the true reward function only predicts 81% of their choices, which is the ceiling. A learned RM approaches it as comparisons grow.
{: .lede}

<div class="visual"><div id="aBars"></div></div>

<div class="deep"><h4>Real reward models</h4><p>Real preference data is noisy too: labelers disagree with each other, so held-out RM accuracy well below 100% is expected. Llama 2 trained <b>two</b> reward models, one for helpfulness and one for safety, because the two goals can conflict and a single model had trouble serving both.</p></div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works, and where it breaks

::: cards grid2
### [a] It generalizes the labels
The RM learns features of good answers from tens of thousands of comparisons, then scores answers no labeler has seen.

### [e] Comparisons carry fine signal
Ranking 4–9 samples gives up to 36 comparisons per prompt, focused on the subtle differences between plausible answers.

### [d] It is only a proxy
The RM is accurate where its training data was. Push a policy far from that data and the RM's mistakes get exploited (deck 06).

### [b] It must keep up
As the policy improves, its outputs leave the RM's training distribution. Llama 2 and 3 collect fresh comparisons on the newest model each round.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "A reward model outputs a probability or a 1–10 score."
> It outputs an unbounded scalar, identified only up to a constant: only differences between answers to the same prompt mean anything.
:::

::: reveal myth
? "A good reward model should agree with labelers 100% of the time."
> Labelers disagree among themselves, so even the "true" reward can't predict every label. Accuracy has a noise ceiling.
:::

::: reveal myth
? "Once trained, the reward model can be reused for the whole project."
> It goes stale as the policy improves. Iterated recipes retrain it on comparisons of the current model's outputs.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? How many pairwise comparisons does one ranking of K = 9 responses give?
- [ ] 9
- [ ] 18
- [x] 36
- [ ] 81
> <b>C(9,2) = 36.</b>
:::

<div class="quiz ">
  <p class="qq">Write the reward-model loss and explain why only differences are learned.</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">−log σ(r(x,y_w) − r(x,y_l)). Adding the same constant to every reward leaves every difference, and therefore the loss, unchanged.</div>
</div>

<div class="quiz ">
  <p class="qq">Why did InstructGPT put all pairs from a prompt into one batch element?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">The C(K,2) pairs share responses, so they are highly correlated. Shuffling them as independent samples caused overfitting; grouping them is also cheaper (one forward pass per response).</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">A reward model learns a scalar score from human comparisons via the Bradley-Terry loss −log σ(r_w − r_l), giving RL an automatic but imperfect judge.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Helpfulness has no formula, and humans can't score the millions of samples RL needs. So labs collect comparisons, which are more consistent than absolute ratings, often as rankings of four to nine answers per prompt, and train a model that outputs one scalar per response. The Bradley-Terry model says the probability that one answer is preferred is the sigmoid of the reward difference, so the loss is minus log sigmoid of the winner's score minus the loser's. Only differences are learned. Accuracy is capped by labeler disagreement, the model is only reliable near its training data, and it needs fresh comparisons as the policy improves.</p></div>

<div class="recap"><div><span><b>Problem:</b> no formula for "good answer"; humans can't score every RL sample.</span></div><div><span><b>Core idea:</b> train r(x, y) on comparisons: −log σ(r_w − r_l); only differences matter.</span></div><div><span><b>Limits:</b> label noise caps accuracy; it is a proxy that goes stale as the policy moves.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/post-training/04_reward_model.ipynb" target="_blank" rel="noopener">04 · Train a Bradley-Terry reward model</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/post-training/04_reward_model.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../05-rlhf-ppo/index.html">05 · RLHF with PPO →</a> · Previous: <a href="../03-lora-qlora/index.html">← 03</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Ouyang et al. 2022 (InstructGPT §3.5, eq. 1: K = 4–9 rankings, 6B RM from the SFT model); Touvron et al. 2023 (Llama 2 §3.2.1–3.2.2: helpfulness and safety RMs, 1,418,091 Meta comparisons); Bradley & Terry 1952; Christiano et al. 2017.</p>

<!-- slide id="s-papers" from="papers" -->
