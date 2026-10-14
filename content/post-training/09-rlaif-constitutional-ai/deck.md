---
title: RLAIF and Constitutional AI
body:
  data-deck: RLAIF and Constitutional AI
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
  - 'harmful prompt :: red-team set :: f'
  - 'response :: from a helpful-only model :: c'
  - 'critique + revise :: against a sampled principle :: b'
  - 'SFT on revisions :: SL-CAI :: a'
  - 'AI comparisons → PM → RL :: RL-CAI (RLAIF) :: e'
  caption: Humans write the principles (16 in the paper) and still provide helpfulness labels.
example:
  title: 'Worked example: producing one AI preference label'
  setup: The RL stage needs comparisons. Instead of a human, a feedback model labels them.
  steps:
  - Sample two responses (A, B) to the same prompt from the SL-CAI model.
  - Sample one principle at random from the constitution, e.g. "choose the response that is more helpful while avoiding harm".
  - Ask the feedback model, optionally with chain-of-thought, which response better satisfies it; record the probabilities as a soft label.
  - Repeat across many prompts and principles; train a preference model on these AI labels mixed with human helpfulness labels, then run RL against it.
  result: Each label is cheap to regenerate for every new model, and the criteria are written down rather than implicit in thousands of individual judgements.
traps:
  tricks:
  - 'Two stages. :: Critique-and-revise SFT, then RL from AI preference labels.'
  - 'Sample principles. :: Ensembling over principles gave more robust labels in the paper.'
  - 'Reason before judging. :: Chain-of-thought improved AI feedback quality and transparency.'
  traps:
  - '"No humans involved." :: Humans write the constitution, and helpfulness labels stayed human.'
  - 'Just a system prompt. :: Principles generate training data; behaviour ends up in the weights.'
  - 'Harmless = refuse. :: The goal was harmless but non-evasive: explain objections instead.'
papers:
- cai
- instructgpt
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Post-training · 09</div>
    <h1>RLAIF and Constitutional AI</h1>
    <p class="sub">Using a model, guided by a written set of principles, to produce the feedback that humans used to provide: critique-and-revise for SFT (supervised fine-tuning), and AI (artificial intelligence) preference labels for RL (reinforcement learning).</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Human preference labels are slow and expensive, and for harmful requests they require people to read and judge harmful content. The rules the model is meant to follow are also implicit in thousands of individual labels.</div>
      <div class="c"><b>Core idea</b>Write the rules down as a <b>constitution</b>. In a supervised stage, the model critiques and revises its own answers against principles; in an RL stage, an AI model compares pairs of answers against principles, and RL uses a preference model trained on those <b>AI labels</b> (RLAIF (reinforcement learning from artificial-intelligence feedback)).</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Feedback is the bottleneck

::: cards grid3
### [d] Scale
Every RLHF (reinforcement learning from human feedback) round needs new comparisons on the latest model's outputs. Human labelling limits how often and how widely that can happen.

### [b] Exposure
Labelling harmlessness means people reading and ranking answers to harmful requests.

### [c] Opacity
The intended behaviour lives implicitly in many individual judgements. Nobody can read off "the rules" the model was trained on.
:::

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## The harmless-but-evasive trap

An easy way to be "harmless" is to refuse anything borderline. That is unhelpful and teaches users nothing. The Constitutional AI paper's goal was a "harmless but non-evasive" assistant that "engages with harmful queries by explaining its objections to them".
{: .lede}

<div class="deep"><h4>Why plain preference labels push towards evasion</h4><p>If labelers judging harmlessness in isolation tend to prefer a refusal over any risky-looking answer, the reward model learns that refusing scores well, and RL amplifies it. Writing explicit principles that ask for explanations instead of bare refusals is one way to steer away from that.</p></div>

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What does "RLAIF" replace?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? In the Constitutional AI paper, what does RL from AI Feedback replace?
- [ ] The pretraining data
- [x] Human preference labels for harmlessness
- [ ] The PPO algorithm
- [ ] All human involvement
> <b>B.</b> "We replace human preferences for harmlessness with 'AI feedback'": an AI evaluates responses according to constitutional principles. Humans still write the principles, and the paper still used human feedback for helpfulness.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Two stages

::: cards grid2
### [a] Supervised stage (SL-CAI)
Sample responses to harmful (red-team) prompts from a <b>helpful-only</b> RLHF model; ask it to <b>critique</b> its own response against a randomly chosen principle, then <b>revise</b> it; repeat. Fine-tune the original model on the revised responses.

### [e] RL stage (RL-CAI, i.e. RLAIF)
Sample pairs of responses from the SL-CAI (SL = supervised learning) model; ask a model which one better satisfies a principle; train a preference model on these AI labels; run RL against it, exactly as in RLHF. The paper wrote <b>16 principles</b> and sampled one at random for each comparison label.
:::

<div class="deep"><h4>Chain of thought helps the judge</h4><p>The paper reports that "both the SL and RL methods can leverage chain-of-thought style reasoning to improve the human-judged performance and transparency of AI decision making": asking the feedback model to reason before choosing makes its labels better and easier to inspect.</p></div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Critique and revise, step by step <span class="ill">illustrative example</span>

An invented, low-stakes example of the SL-CAI loop, to show the mechanics. Real constitutions contain many principles; one is sampled for each critique.
{: .lede}

<div class="visual">
  <div class="seg" id="cSeg"><button data-v="0" class="on">1 · prompt + response</button><button data-v="1">2 · principle</button><button data-v="2">3 · critique</button><button data-v="3">4 · revision</button><button data-v="4">5 · training data</button></div>
  <div class="infobox" id="cOut" style="background:var(--panel-2);border-radius:10px;padding:14px 16px;margin-top:12px;font-size:15px;line-height:1.6"></div>
</div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Where AI feedback plugs into the pipeline

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Step</th><th>RLHF</th><th>Constitutional AI (RLAIF)</th></tr>
  <tr><td>Supervised data</td><td>human demonstrations</td><td>model's own responses, critiqued and revised against principles</td></tr>
  <tr><td>Comparisons</td><td>human labelers pick the better response</td><td>a feedback model picks the response that better follows a principle</td></tr>
  <tr><td>Reward / preference model</td><td>trained on human labels</td><td>trained on AI labels (harmlessness) mixed with human labels (helpfulness)</td></tr>
  <tr><td>RL</td><td>PPO (Proximal Policy Optimization) against the RM (reward model)</td><td>same: RL against the preference model</td></tr>
  <tr><td>What humans provide</td><td>many individual judgements</td><td>a short list of written principles, plus helpfulness data</td></tr>
</table></div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works, and what to watch

::: cards grid2
### [a] Judging is easier than generating
A capable model can often tell which of two answers better follows a stated principle even if its own first answer didn't.

### [e] Scalable and inspectable
AI labels are cheap to regenerate for every new model, and the principles are written down, so the target behaviour can be read, debated and changed.

### [b] The feedback model's limits carry over
If the judging model misreads a principle or has blind spots, those errors become training signal, so AI feedback still needs human evaluation.

### [c] Widely reused idea
Model-generated judgements now appear throughout post-training: rejection sampling with reward models, synthetic SFT data, and LLM-as-judge (LLM = large language model) evaluation (Evals topic).
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "RLAIF removes humans from alignment."
> Humans write and choose the principles, and the paper still used human feedback for helpfulness. What changes is who produces each individual label.
:::

::: reveal myth
? "Constitutional AI is just a system prompt with rules."
> The principles are used to <b>generate training data</b>: revised responses for SFT and AI preference labels for a preference model and RL. The behaviour is trained into the weights.
:::

::: reveal myth
? "Being harmless means refusing more."
> The paper aimed for "harmless but non-evasive": engaging with the request and explaining objections rather than refusing blindly.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

<div class="quiz ">
  <p class="qq">Describe the two stages of Constitutional AI.</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">SL-CAI: the model critiques and revises its own responses against sampled principles, and is fine-tuned on the revisions. RL-CAI: a model labels which of two responses better follows a principle; a preference model is trained on those AI labels and used for RL (RLAIF).</div>
</div>

::: quiz
? Which part of the Constitutional AI pipeline still used human preference labels?
- [ ] Harmlessness
- [x] Helpfulness
- [ ] Neither
- [ ] Both
> <b>Helpfulness.</b> AI feedback replaced human labels for harmlessness.
:::

<div class="quiz ">
  <p class="qq">Why might AI feedback make the target behaviour more transparent?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">The behaviour is specified by a short written list of principles that anyone can read, and chain-of-thought judgements show why each label was chosen, instead of being implicit in thousands of individual human labels.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Constitutional AI replaces human harmlessness labels with AI feedback guided by written principles: self-critique and revision for SFT, AI preference labels for RL.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Human feedback is slow, hard to scale, and leaves the intended rules implicit. Constitutional AI writes those rules down as principles. In the supervised stage the model critiques its own responses against a sampled principle and revises them, and is fine-tuned on the revisions. In the RL stage a model compares pairs of responses against principles, a preference model is trained on those AI labels, and RL proceeds as in RLHF. That is RLAIF. The goal was an assistant that is harmless but not evasive, explaining its objections rather than refusing blindly. Humans still write the principles, and the paper kept human labels for helpfulness.</p></div>

<div class="recap"><div><span><b>Problem:</b> human labels are slow, expensive and leave the rules implicit.</span></div><div><span><b>Core idea:</b> principles + AI critique/revision (SL-CAI) + AI preference labels for RL (RLAIF).</span></div><div><span><b>Watch:</b> the judge's blind spots become training signal; humans still set the principles.</span></div></div>

<p class="start-hint">You've finished the series. <a href="../../build-it/index.html">See all Build-it notebooks →</a> · Previous: <a href="../08-rlvr-grpo/index.html">← 08</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Bai et al. 2022, "Constitutional AI: Harmlessness from AI Feedback" (§1, §3 SL-CAI, §4 RL-CAI); Christiano et al. 2017; Ouyang et al. 2022.</p>

<!-- slide id="s-papers" from="papers" -->
