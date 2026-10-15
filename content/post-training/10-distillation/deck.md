---
title: Knowledge Distillation
body:
  data-deck: Knowledge distillation
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
  - 'teacher :: large, accurate :: c'
  - 'targets :: logits or sampled text :: b'
  - 'student :: small, fast :: a'
  - 'loss :: KL to the teacher :: f'
  - 'on-policy :: student samples, teacher grades :: e'
  caption: Distillation transfers the teacher's distribution, not only its top answer.
example:
  title: 'Worked example: what a soft target carries'
  setup: For "The capital of Australia is", a teacher gives Canberra 0.90, Sydney 0.08 and Melbourne 0.02 (illustrative numbers). The one-hot label says only "Canberra".
  steps:
  - 'Hard label: the loss is −log q(Canberra). The student learns nothing about Sydney being a closer mistake than an unrelated word.'
  - 'Soft target at T = 1: the cross-entropy −Σ p log q covers all three tokens, so the student is also pushed to give Sydney about 0.08.'
  - 'At T = 4 for both models, the teacher''s probabilities become proportional to p^(1/4): 0.974, 0.532, 0.376, or <b>0.52, 0.28, 0.20</b> after normalising. The
    small probabilities now carry a visible signal.'
  - Hinton et al. multiply the soft-target loss by T² (16 here), because its gradients scale as 1/T²; this keeps it balanced against the hard-label loss.
  result: A soft target gives the student a full distribution per token instead of one label; temperature makes the small probabilities count.
traps:
  tricks:
  - 'Small open models are distilled. :: Gemma 2 (2B, 9B), Llama 3.2 (1B, 3B) and the small Qwen3 models were all trained against a larger teacher.'
  - 'Reverse KL suits generative students. :: MiniLLM: forward KL makes the student overestimate the teacher''s low-probability regions; reverse KL is mode-seeking.'
  - 'On-policy distillation is cheap. :: Thinking Machines reached 70% on AIME 2024 with Qwen3-8B-Base at an estimated 9 to 30 times lower cost than extending off-policy
    SFT.'
  traps:
  - 'Training only on teacher text. :: The student never sees its own mistakes during training, so errors compound at inference (the mismatch GKD addresses).'
  - 'Copying the teacher''s errors. :: Distillation transfers mistakes and biases too; filter the teacher''s outputs (R1 used rejection sampling and checks).'
  - 'Ignoring terms of service. :: Some providers prohibit using outputs to train competing models (for example Anthropic''s commercial terms, section D.4).'
papers:
- distill
- distilbert
- seqkd
- minillm
- gkd
- gemma2
- llama32_blog
- minitron
- r1
- qwen3
- tm_onpolicy
- anthropic_terms
status:
  label: current
  reviewed: '2026-10-15'
  note: Written from primary sources 2026-10-15; logit and on-policy distillation are how current small open models are trained.
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Post-training · 10</div>
    <h1>Knowledge distillation</h1>
    <p class="sub">Training a small model to imitate a large one: soft targets and temperature, sequence-level distillation from teacher outputs, logit distillation in pretraining (Gemma 2, Llama 3.2), on-policy distillation with reverse KL, and distilled reasoning models.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Large models are accurate but slow and costly to serve. A small model trained from scratch on the same data is much weaker, partly because a one-hot next-token label says nothing about which other tokens were nearly right.</div>
      <div class="c"><b>Core idea</b>Use the large model as a <b>teacher</b>. The <b>student</b> learns from the teacher's full probability distribution (<b>soft targets</b>, logit distillation) or from its sampled outputs (<b>sequence-level</b> distillation: fine-tune on teacher text). <b>On-policy</b> distillation lets the student generate and has the teacher score every token it wrote (reverse KL), so the student learns on the states it actually reaches.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Big models are good; small models are what you can afford

Serving cost and latency grow with model size, and many products need a model that runs on one GPU or on a phone. Training a small model from scratch on the same data leaves accuracy on the table.
            {: .lede}

::: cards grid3
### [d] Labels are thin
A next-token label is one-hot: it says which token came next, not which alternatives were plausible.

### [b] Capacity is limited
A small model cannot learn everything in the data, so what it is shown, and how, matters more.

### [c] The teacher already knows
A large model's probabilities encode similarity between answers: "Sydney" is a better wrong answer than an unrelated word. Hinton et al. call this the information in the small probabilities.
:::

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why simply fine-tuning on teacher text is not enough

::: cards grid3
### [d] One sample per prompt
Sampled teacher text shows one continuation; the teacher's other likely answers are lost.

### [b] Train-inference mismatch
A student fine-tuned on teacher text learns on the teacher's states, then generates from its own, where its early mistakes take it off the training distribution (GKD).

### [c] Mode covering
Matching the teacher with forward KL pushes a small student to spread probability over everything the teacher allows, including regions it cannot model well (MiniLLM).
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Distill or run RL?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? DeepSeek trained Qwen2.5-32B two ways: large-scale RL directly on the base model, and SFT on outputs from DeepSeek-R1. Which scored higher on AIME 2024 (pass@1)?
- [ ] RL on the 32B base: the model learns to reason by itself
- [x] Distillation from R1: 72.6% vs 47.0% for RL
- [ ] They tied
- [ ] Neither improved on the base model
> **B.** DeepSeek-R1-Distill-Qwen-32B scored 72.6%, Qwen2.5-32B-Zero (RL) 47.0%. The paper concludes that distilling a stronger model into a smaller one works better than large-scale RL on the small model, though going beyond the teacher still needs stronger base models and RL.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Three ways to learn from a teacher

::: cards grid2
### [f] Soft targets (logit distillation)
Minimise the cross-entropy (equivalently, forward KL) between the teacher's and student's token distributions, both at temperature T, scaled by T², often mixed with the normal label loss. Needs the teacher's logits.

### [b] Sequence-level distillation
Kim and Rush: train on the teacher's generated outputs (beam search in translation, samples for LLMs). Works with only text access; the best student ran 10× faster than its teacher with little loss in BLEU.

### [a] On-policy distillation
The student samples a response; the teacher scores each of its tokens and the student minimises reverse KL(student ‖ teacher) per token (GKD, MiniLLM). Dense, per-token feedback on the student's own mistakes.

### [e] Pruning plus distillation
Cut layers, heads or neurons from a trained model, then recover quality by distilling from the original: Minitron needed up to 40× fewer tokens per model than training from scratch.
:::

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Forward vs reverse KL <span class="ill">interactive</span>

<div class="visual"><div class="controls"><label class="ctl">distance between modes <input type="range" id="kdD" min="0" max="4" step="0.1" value="3.5"> <output id="kdDo"></output></label><label class="ctl">weight of left mode <input type="range" id="kdW" min="0.1" max="0.9" step="0.05" value="0.5"> <output id="kdWo"></output></label></div><svg id="kdSvg" viewBox="0 0 660 290" role="img" aria-label="A two-mode teacher distribution with single-Gaussian student fits under forward and reverse KL"></svg><p class="readout" id="kdOut"></p></div>

A one-dimensional picture of a capacity gap: the student is a single Gaussian, the teacher has two modes. For a language model, "modes" are different plausible continuations.

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Who distils, and how

::: table
| Model | Teacher | How |
|---|---|---|
| Gemma 2 2B, 9B (2024) | larger Gemma 2 model | pretraining on the teacher's token probabilities instead of next-token labels |
| Llama 3.2 1B, 3B (2024) | Llama 3.1 8B and 70B | pruned from 8B; teacher logits as token-level targets during pretraining |
| Minitron 8B, 4B (2024) | Nemotron-4 15B | prune, then retrain with distillation on under 3% of the original data |
| DeepSeek-R1-Distill 1.5B to 70B (2025) | DeepSeek-R1 | SFT on 800K curated samples; no RL stage |
| Qwen3 0.6B to 14B, 30B-A3B (2025) | Qwen3-32B or Qwen3-235B-A22B | off-policy, then on-policy logit distillation |
:::

Gemma 2's ablation: a 2B model trained on 500B tokens scored 67.7 (average of three benchmarks) with distillation from a 7B teacher, versus 60.3 from scratch.

::: deep On-policy distillation, in numbers
Thinking Machines distilled Qwen3-32B into Qwen3-8B-Base for maths reasoning. Off-policy SFT on 400K prompts reached 60% on AIME 2024; the Qwen3 report's RL stage reached 67.6% using 17,920 GPU hours; on-policy distillation reached 70%, at an estimated 9 to 30 times lower cost than extending SFT to 2M prompts. Qwen3 itself reports that strong-to-weak distillation needed about 1/10 of the GPU hours of its four-stage training.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works

::: cards grid2
### [a] More bits per example
A soft target is a whole distribution per token; DistilBERT kept 97% of BERT's language understanding with 40% fewer parameters, running 60% faster.

### [c] Easier targets
The teacher has already resolved noise and ambiguity in the data, so its outputs are cleaner to learn than raw web text.

### [b] Ensembles into one
Hinton et al.: over 80% of the frame-accuracy gain from an ensemble of 10 speech models transferred to a single distilled model.

### [e] Learning from your own mistakes
On-policy distillation grades the states the student actually visits, like RL, but with a dense per-token signal instead of one reward per episode.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Distillation only shrinks a model after training."
> Gemma 2 and Llama 3.2 used teacher probabilities during pretraining itself, as the main training signal for the small models.
:::

::: reveal myth
? "A distilled student cannot get anywhere near its teacher."
> Gaps remain, but they can be small: DeepSeek-R1-Distill-Qwen-32B scored 72.6% on AIME 2024 against 79.8% for R1 itself, and beat OpenAI o1-mini (63.6%).
:::

::: reveal myth
? "You always need the teacher's logits."
> Sequence-level distillation needs only generated text (as in the R1 distills); logits allow richer token-level and on-policy distillation.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Why does Hinton et al.'s soft-target loss get multiplied by T²?
- [ ] To make training faster
- [x] Because the gradients from soft targets scale as 1/T², so the term would otherwise vanish next to the hard-label loss
- [ ] To convert nats to bits
- [ ] It is a regulariser that prevents overfitting
> **B.** Scaling by T² keeps the relative contribution of soft and hard targets roughly unchanged when T changes.
:::

::: reveal
? What is the difference between off-policy and on-policy distillation?
> Off-policy: the student trains on sequences the teacher (or a dataset) produced. On-policy: the student generates its own sequences and the teacher scores each token, so training covers the states the student reaches at inference.
:::

::: reveal
? Why is reverse KL preferred for distilling generative LMs in MiniLLM?
> Forward KL is mode-covering: it penalises the student for missing any teacher mass, so a small student spreads probability into regions the teacher rarely uses. Reverse KL is mode-seeking: the student concentrates on outputs the teacher rates highly.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Distillation trains a small model on what a large model believes, the full distribution or its outputs, so the small model gets far more signal per example than labels alone.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Hinton et al. trained a small model on a large model's softened probabilities: temperature T exposes the small probabilities, and the loss is scaled by T². For language models, sequence-level distillation fine-tunes the student on teacher outputs (DeepSeek-R1-Distill-Qwen-32B reached 72.6% on AIME 2024, versus 47.0% for RL on the same base), while logit distillation trains on the teacher's token probabilities (Gemma 2, Llama 3.2). On-policy distillation lets the student generate and minimises reverse KL to the teacher on its own tokens, which avoids the train-inference mismatch and matched RL results at a fraction of the cost.</p></div>
    <div class="recap"><div><span><b>Soft targets:</b> teacher probabilities at temperature T, loss × T²</span></div><div><span><b>Sequence-level:</b> fine-tune on teacher outputs</span></div><div><span><b>On-policy:</b> student samples, teacher grades each token (reverse KL)</span></div><div><span><b>In practice:</b> how today's small open models are trained</span></div></div>
    <p class="start-hint">You've finished the series. <a href="../../build-it/index.html">See all Build-it notebooks →</a> · Previous: <a href="../09-rlaif-constitutional-ai/index.html">← 09</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
