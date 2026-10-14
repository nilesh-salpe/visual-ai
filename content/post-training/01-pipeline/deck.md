---
title: The Post-training Pipeline
body:
  data-deck: The post-training pipeline
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
  - 'pretrained model :: next-token on web text :: f'
  - 'SFT :: imitate demonstrations :: a'
  - 'reward model :: learn from comparisons :: b'
  - 'RL (PPO) :: reward − β·KL :: c'
  - 'assistant :: repeat in rounds :: e'
  caption: 'Alternatives: DPO replaces the reward model + RL step; RLVR replaces the reward model with a checker.'
example:
  title: 'Worked example: InstructGPT''s data budget'
  setup: Reported dataset sizes (training prompts) for the three steps.
  steps:
  - 'SFT: about <b>13k</b> prompts with labeler-written demonstrations.'
  - 'Reward model: about <b>33k</b> prompts; each labeler ranking of K = 4–9 outputs gives C(K, 2) = 6–36 comparisons.'
  - 'PPO: about <b>31k</b> prompts from the API (the policy writes the answers itself).'
  - 'Compare pretraining: hundreds of billions of tokens. Post-training is tiny by comparison.'
  result: 'With that small budget, the 1.3B InstructGPT model was preferred to the 175B base GPT-3: post-training shapes behaviour, pretraining supplies knowledge.'
traps:
  tricks:
  - 'Comparisons beat demonstrations for scale. :: Judging is easier than writing; one ranking gives many pairs.'
  - 'Iterate in rounds. :: Collect fresh preferences on the current model (Llama 2: five RLHF versions; Llama 3: six rounds).'
  - 'Pick the optimizer for the signal. :: Pairs → DPO; reward model → PPO or rejection sampling; checker → RLVR.'
  traps:
  - 'Expecting new knowledge from post-training. :: It mostly changes behaviour, not what the model knows.'
  - 'Treating the RM as ground truth. :: It is a proxy; optimize it too hard and it gets gamed (deck 06).'
  - 'Ignoring the alignment tax. :: RLHF can regress benchmarks; InstructGPT mixed pretraining gradients in (PPO-ptx).'
papers:
- instructgpt
- christiano
- stiennon
- llama3
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Post-training · 01</div>
    <h1>The post-training pipeline</h1>
    <p class="sub">How a model that only predicts internet text becomes an assistant: demonstrations (SFT (supervised fine-tuning)), preferences (reward models, RLHF (reinforcement learning from human feedback), DPO (Direct Preference Optimization)) and verifiable rewards (RLVR (reinforcement learning with verifiable rewards)), and how real labs combine them.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Pretraining optimizes "predict the next token of internet text". That makes a model knowledgeable, not helpful: it continues prompts rather than following them, and it has no notion of which answer people prefer.</div>
      <div class="c"><b>Core idea</b>Fine-tune the pretrained model in stages. <b>SFT</b> imitates good demonstrations. <b>Preference optimization</b> (RLHF with a reward model, or DPO) pushes towards answers people prefer. <b>RL (reinforcement learning) with verifiable rewards</b> sharpens tasks whose answers can be checked.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Same knowledge, different behaviour

One prompt, three stages of the same model. The outputs are <b>illustrative</b> (written for this deck), but the pattern is the one InstructGPT documented: a base model continues text, an SFT model answers, and preference tuning makes the answer what people actually want.
{: .lede}

<div class="visual">
  <div class="seg" id="sSeg"><button data-v="0" class="on">Base (pretrained)</button><button data-v="1">After SFT</button><button data-v="2">After preference tuning</button></div>
  <div class="infobox" id="sOut" style="background:var(--panel-2);border-radius:10px;padding:14px 16px;margin-top:12px;font-size:15px;line-height:1.6"></div>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why pretraining alone isn't enough

::: cards grid3
### [d] Wrong objective
The pretraining loss rewards predicting what text comes next on the web, which includes unhelpful, wrong and toxic text. InstructGPT calls this objective "misaligned" with following instructions helpfully and safely.

### [b] Demonstrations are expensive
Writing an ideal answer for every kind of request takes expert time. InstructGPT's SFT set had about 13k prompts; Llama 2 stopped at 27,540 high-quality annotations.

### [c] Imitation has a ceiling
SFT can only copy its demonstrations. To prefer answers better than any single demonstrator would write, you need a signal that <b>compares</b> answers, which is much cheaper than writing them.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## How much does alignment matter?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? InstructGPT compared a 1.3B model with SFT + RLHF against the original 175B GPT-3. Which did human labelers prefer on the API (application programming interface) prompt distribution?
- [ ] 175B GPT-3, by a wide margin
- [ ] They were tied
- [x] The 1.3B InstructGPT model
- [ ] It depended only on prompt length
> <b>C.</b> "Outputs from the 1.3B parameter InstructGPT model are preferred to outputs from the 175B GPT-3, despite having 100x fewer parameters." Post-training changed usefulness more than a 100× increase in parameters did.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## The three InstructGPT steps

::: cards grid3
### [a] 1 · SFT
Labelers write demonstrations of the desired output for prompts; fine-tune the pretrained model on them with ordinary next-token loss. (~13k training prompts.)

### [b] 2 · Reward model
Sample several outputs per prompt, labelers rank them (K = 4 to 9), and train a model to output a scalar score that agrees with the rankings. (~33k prompts.)

### [e] 3 · RL (PPO)
Optimize the SFT model to maximize the reward model's score with PPO (Proximal Policy Optimization), with a KL (Kullback-Leibler divergence) penalty that keeps it close to the SFT model. (~31k prompts.)
:::

<div class="deep"><h4>Where the idea came from</h4><p>Christiano et al. (2017) showed RL from human <b>comparisons</b> could teach Atari and robotics behaviours with feedback on less than 1% of the agent's interactions, and about an hour of human time for some novel behaviours. Stiennon et al. (2020) applied it to summarization; InstructGPT applied it to general instruction following.</p></div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Each stage: data, loss, models in memory

Pick a stage to see what it consumes and what it costs. The later decks cover each one in depth.
{: .lede}

<div class="visual">
  <div class="seg" id="pSeg"><button data-v="pre">Pretraining</button><button data-v="sft" class="on">SFT</button><button data-v="rm">Reward model</button><button data-v="ppo">RLHF (PPO)</button><button data-v="dpo">DPO</button><button data-v="rlvr">RLVR (GRPO)</button></div>
  <div class="grid4" style="margin-top:14px">
    <div class="stat"><div class="num" id="pD" style="font-size:16px"></div><div class="lbl">training data</div></div>
    <div class="stat"><div class="num" id="pL" style="font-size:16px"></div><div class="lbl">loss / signal</div></div>
    <div class="stat"><div class="num" id="pM" style="font-size:16px"></div><div class="lbl">models in memory</div></div>
    <div class="stat"><div class="num" id="pK" style="font-size:16px"></div><div class="lbl">deck</div></div>
  </div>
  <div class="infobox" style="background:var(--panel-2);border-radius:10px;padding:12px 14px;margin-top:10px;font-size:14px;color:var(--muted)" id="pInfo"></div>
</div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## How real recipes combine the pieces

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Model</th><th>Post-training recipe (as reported)</th></tr>
  <tr><td>InstructGPT (2022)</td><td>SFT → reward model → PPO, with a pretraining-loss mix ("PPO-ptx") to reduce regressions</td></tr>
  <tr><td>Llama 2-Chat (2023)</td><td>SFT on 27,540 annotations → two reward models (helpfulness, safety) on over 1M comparisons → five RLHF rounds: rejection-sampling fine-tuning only up to V4, then PPO on top</td></tr>
  <tr><td>Llama 3 (2024)</td><td>Several rounds (six, following Llama 2) of reward modelling → SFT on rejection-sampled data → DPO</td></tr>
  <tr><td>Tülu 3 (2024)</td><td>SFT → DPO → RL with verifiable rewards (the paper that named RLVR)</td></tr>
  <tr><td>DeepSeek-R1 (2025)</td><td>R1-Zero: RL with rule-based rewards directly on the base model, no SFT. R1: a "multi-stage learning framework that integrates rejection sampling, reinforcement learning, and supervised finetuning", starting from cold-start long chain-of-thought data</td></tr>
</table></div>

<div class="deep"><h4>The common pattern</h4><p>Every recipe starts with SFT to teach the format, then uses <b>comparisons or checks on the model's own outputs</b> to improve beyond the demonstrations, and repeats in rounds so new preference data comes from the current model. The choice of optimizer (PPO, rejection sampling, DPO, GRPO (Group Relative Policy Optimization)) is mostly about cost, stability and what signal is available.</p></div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why preferences work so well

::: cards grid2
### [a] Judging is easier than writing
A labeler can reliably pick the better of two answers even when they couldn't write either. Comparisons are cheaper and more consistent than absolute scores.

### [e] Feedback on the model's own outputs
SFT learns from someone else's text. Preference and RL methods learn from what <b>this</b> model actually produces, including its own mistakes.

### [b] Knowledge comes from pretraining
Post-training is small compared with pretraining (thousands to millions of examples vs trillions of tokens). It mostly selects and shapes behaviour the base model can already produce.

### [c] The cost: an "alignment tax"
InstructGPT saw RLHF reduce performance on some public NLP (natural language processing) benchmarks, and mixing pretraining gradients into PPO (PPO-ptx) largely fixed it without hurting preference scores.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Post-training is where the model learns its knowledge."
> Knowledge comes overwhelmingly from pretraining on trillions of tokens. Post-training uses far less data and mainly changes <b>behaviour</b>: format, helpfulness, refusals, reasoning style.
:::

::: reveal myth
? "RLHF means humans give a reward to every answer during training."
> Humans label a fixed set of comparisons once per round. A <b>reward model</b> trained on them scores the millions of samples seen during RL.
:::

::: reveal myth
? "There is one standard recipe."
> InstructGPT used PPO, Llama 3 used rejection sampling + DPO, DeepSeek-R1-Zero used RL with rule-based rewards and no SFT. The building blocks are shared; the mix varies.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? In InstructGPT, what do labelers provide for the reward model?
- [ ] Scores from 1 to 10
- [x] Rankings of 4–9 sampled outputs per prompt
- [ ] Rewritten answers
- [ ] Binary safe/unsafe labels
> <b>Rankings of K = 4–9 outputs</b>, converted into pairwise comparisons.
:::

<div class="quiz ">
  <p class="qq">Why is a KL penalty to the SFT model added during RL?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">The reward model is an imperfect proxy. Without a leash, the policy drifts into outputs where the reward model is wrong (reward hacking). The KL term keeps it near the SFT model, where the reward model was trained.</div>
</div>

<div class="quiz ">
  <p class="qq">Name the three InstructGPT steps and what each trains.</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">SFT trains the policy on demonstrations; reward modelling trains a scalar scorer on rankings; PPO trains the policy to maximize that score minus a KL penalty.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Post-training turns a next-token predictor into an assistant: imitate demonstrations (SFT), then optimize towards what people prefer or what can be verified, repeating in rounds.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>A pretrained model knows a lot but just continues text. Post-training fixes behaviour in stages. Supervised fine-tuning imitates written demonstrations and teaches the chat format. Then preference optimization uses comparisons, which are much cheaper than demonstrations: either train a reward model and optimize against it with RL and a KL penalty, as InstructGPT did, or optimize the same objective directly with DPO. For maths and code, a verifier can replace the reward model. InstructGPT showed a 1.3 billion parameter model after this process was preferred to the 175 billion parameter base GPT-3.</p></div>

<div class="recap"><div><span><b>Problem:</b> next-token pretraining is knowledgeable but not helpful.</span></div><div><span><b>Core idea:</b> SFT on demonstrations, then optimize preferences (RM + PPO, or DPO) or verifiable rewards.</span></div><div><span><b>Practice:</b> labs iterate rounds: InstructGPT PPO, Llama 3 RS (rejection sampling) + DPO, R1 RL with rule-based rewards.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/post-training/01_sft_loss_masking.ipynb" target="_blank" rel="noopener">01 · Supervised fine-tuning: chat templates, loss masking and packing</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/post-training/01_sft_loss_masking.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../02-supervised-fine-tuning/index.html">02 · Supervised fine-tuning →</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Ouyang et al. 2022, "Training language models to follow instructions with human feedback" (InstructGPT §3, Fig. 2); Christiano et al. 2017; Touvron et al. 2023 (Llama 2 §3); Llama Team 2024 (Llama 3 §4); Lambert et al. 2024 (Tülu 3); DeepSeek-AI 2025 (DeepSeek-R1).</p>

<!-- slide id="s-papers" from="papers" -->
