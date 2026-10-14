---
title: Supervised Fine-tuning
body:
  data-deck: Supervised fine-tuning
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
  - 'messages :: system, user, assistant :: f'
  - 'chat template :: role tokens + end-of-turn :: c'
  - 'tokens + mask :: assistant tokens = 1 :: a'
  - 'shift labels :: mask → −100 :: b'
  - 'masked loss :: average over trained tokens :: e'
  caption: Ordinary next-token training, applied only to what the assistant should produce.
example:
  title: 'Worked example: what fraction of a chat is trained on?'
  setup: 'The 2-turn chat in notebook 01: system prompt, two user turns, two short assistant answers (toy word-level tokenizer).'
  steps:
  - 'Rendered sequence: <b>29 tokens</b> (bos, role tokens, content, end-of-turn markers).'
  - 'Trained tokens: the two answers plus their end-of-turn tokens = <b>8 tokens (28%)</b>.'
  - Loss = mean of −log p over those 8 positions only; the other 21 are labels of −100.
  - 'Packing 2,000 examples of 20–399 tokens: one example per row → 54% real tokens; packed into 2,048-token rows → 93%.'
  result: Most positions in a chat are context, not targets. Masking keeps the loss focused, and packing keeps the GPU busy.
traps:
  tricks:
  - 'Train the end-of-turn token. :: Otherwise the model never learns to stop.'
  - 'Average over trained tokens only. :: Averaging over all positions shrinks the effective learning rate.'
  - 'Pack + document mask. :: Llama 2 concatenated prompts and answers to fill 4,096-token rows.'
  traps:
  - 'Training on user turns. :: Wastes capacity predicting what users type.'
  - 'More data at any quality. :: Llama 2 preferred 27,540 high-quality examples to millions of third-party ones.'
  - 'Picking checkpoints by validation loss. :: InstructGPT kept training past the minimum because preference scores improved.'
papers:
- instructgpt
- llama2
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Post-training · 02</div>
    <h1>Supervised fine-tuning (SFT)</h1>
    <p class="sub">The first post-training step: chat templates, training only on the assistant's tokens, packing, and why a few thousand high-quality examples beat a million mediocre ones.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>A base model has no notion of "user" and "assistant", doesn't know when an answer ends, and imitates whatever style its prompt resembles.</div>
      <div class="c"><b>Core idea</b>Fine-tune on <b>demonstrations</b> rendered with a <b>chat template</b>, using ordinary next-token loss but <b>only on the assistant's tokens</b> (including its end-of-turn token). Pack examples to avoid wasting compute on padding.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## One conversation, one token sequence

A chat model sees a single flat sequence. The template inserts role markers and end-of-turn tokens. Colour shows what the loss is computed on. Toggle to compare training on everything vs only the assistant's answers.
{: .lede}

<div class="visual">
  <div class="seg" id="mSeg"><button data-v="1" class="on">Loss on assistant tokens only</button><button data-v="0">Loss on every token</button></div>
  <div id="mToks" style="display:flex;flex-wrap:wrap;gap:5px;margin-top:14px;font:500 13px 'JetBrains Mono',monospace"></div>
  <p class="readout" id="mOut"></p>
</div>

<p class="caption">Illustrative template with generic role tokens. Real models define their own (each tokenizer's chat template), but the structure is the same.</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## What a base model gets wrong

::: cards grid3
### [d] No turn structure
It has never seen consistent role markers, so it may keep writing the user's next message, or invent a whole dialogue.

### [b] No stopping point
It doesn't know an answer is finished. Without a trained end-of-turn token it rambles until the length limit.

### [c] Style follows the prompt
Ask casually and you get forum-style text; ask formally and you get a paper. SFT (supervised fine-tuning) pins down one consistent assistant style.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Which tokens should be trained?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? In a two-turn chat (system, user, assistant, user, assistant), where should the SFT loss be computed?
- [ ] On every token
- [ ] Only on the user turns
- [x] On the assistant turns, including each end-of-turn token
- [ ] Only on the final assistant turn
> <b>C.</b> The model should learn to <i>produce</i> answers and to stop, not to predict what users type. Llama 2: "we zero-out the loss on tokens from the user prompt, so as a result, we backpropagate only on answer tokens." Earlier assistant turns are valid targets too.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## SFT in one paragraph

<div class="grid3">
  <div class="card a"><h3>Render</h3><p>Messages → template → token ids, plus a mask marking the assistant's content and closing end-of-turn token as trainable.</p></div>
  <div class="card b"><h3>Shift and mask</h3><p>Inputs = tokens[:-1], labels = tokens[1:]. Set untrained labels to −100, the value standard cross-entropy implementations ignore.</p></div>
  <div class="card e"><h3>Train</h3><p>Average next-token loss over trained positions only. Small learning rate (Llama 2: 2×10⁻⁵), few epochs (Llama 2: 2), sequences up to 4,096 tokens.</p></div>
</div>

<div class="deep"><h4>Epochs and overfitting</h4><p>InstructGPT found its SFT models "overfit on validation loss after 1 epoch", yet "training for more epochs helps both the RM (reward model) score and human preference ratings, despite this overfitting". Validation loss on demonstrations is not the goal; behaviour is. That is one reason labs judge SFT checkpoints with preference models and evals rather than perplexity.</p></div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Packing: stop paying for padding

20 examples of random length go into rows of 2,048 tokens. With one example per row, everything is padded to the longest example. Packing fills each row with whole examples, in order, and pads only the tail.
{: .lede}

<div class="visual">
  <div class="seg" id="kSeg"><button data-v="pad">One example per row</button><button data-v="pack" class="on">Packed</button></div>
  <svg id="kSvg" viewBox="0 0 660 260" style="margin-top:10px" role="img" aria-label="Padding vs packing"></svg>
  <p class="readout" id="kOut"></p>
</div>

<div class="deep"><h4>Packing needs a document mask</h4><p>Llama 2: "we concatenate all the prompts and answers from the training set", with a special token separating segments. Without a document mask (or position resets), tokens in one example can attend to the previous, unrelated example in the same row. See <a href="../../architecture/06-decoder-only/index.html">Architecture deck 06</a>.</p></div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Quality beats quantity

::: cards grid2
### [a] Llama 2: "Quality Is All You Need"
Meta found third-party SFT data had "insufficient diversity and quality". They collected their own and stopped at <b>27,540</b> annotations: a small set of high-quality examples beat millions of mediocre ones.

### [e] InstructGPT: ~13k prompts
Written by a vetted team of labelers, covering generation, open QA, brainstorming, chat, rewriting, summarization and more.

### [b] What makes data good
Correct, consistent in format and style, diverse in task, and at the difficulty you want the model to reach. Errors in demonstrations are imitated faithfully.

### [c] Synthetic data
Modern recipes generate candidate answers with models and keep the best (rejection sampling, deck 07). Llama 3's SFT data combines human-collected prompts with rejection-sampled model responses, plus targeted synthetic data.
:::

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why SFT comes first

::: cards grid2
### [a] It makes RL feasible
RL (reinforcement learning) and preference methods learn from the model's own samples. If the model can't produce a sensible answer at all, there is nothing to compare or reward. SFT puts it in the right region.

### [e] It defines the reference
The SFT model is the reference policy for the KL (Kullback-Leibler divergence) penalty (PPO (Proximal Policy Optimization)) and for DPO (Direct Preference Optimization)'s log-ratios. Later stages stay close to it.

### [b] Cheap and stable
Plain supervised learning: no sampling, no reward model, one model in memory, and with LoRA (Low-Rank Adaptation) it fits on modest hardware (deck 03).

### [c] But it only imitates
It can't exceed its demonstrations or learn from comparisons, and it gives no signal on which of two plausible answers is better.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Training on the whole conversation is just as good."
> Then the model spends capacity predicting user messages, and the loss is diluted by tokens you never want it to generate. Standard practice (Llama 2) masks prompt tokens.
:::

::: reveal myth
? "More SFT data is always better."
> Llama 2 got better results from 27,540 carefully collected examples than from millions of third-party ones. Bad examples are imitated too.
:::

::: reveal myth
? "Lowest validation loss is the best SFT checkpoint."
> InstructGPT trained past the validation-loss minimum because reward-model scores and human preferences kept improving.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

<div class="quiz">
  <p class="qq">Which label value tells a standard cross-entropy loss to skip a position?</p>
  <div class="opts">
  <button>A. 0</button>
  <button>B. −1</button>
  <button data-ok>C. −100</button>
  <button>D. the pad token id</button>
  </div>
  <div class="why"><b>−100</b> (PyTorch's default ignore_index).</div>
</div>

<div class="quiz ">
  <p class="qq">Why must the assistant's end-of-turn token be trained?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Otherwise the model never learns when to stop. It would keep generating past the end of the answer, often inventing the next user turn.</div>
</div>

<div class="quiz ">
  <p class="qq">What does packing save, and what extra mechanism does it need?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">It removes padding, so nearly every position is a real token. It needs a document mask (or position resets) so packed examples don't attend to each other.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">SFT is next-token training on demonstrations, rendered with a chat template and with the loss only on the assistant's tokens, using fewer but better examples.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Supervised fine-tuning is the first post-training step. Each conversation is rendered with a chat template into one token sequence, and the model is trained with ordinary next-token loss, but only on the assistant's tokens and its end-of-turn token, so it learns to answer and to stop rather than to predict users. Examples are packed into full-length rows with a document mask to avoid wasted padding. Quality matters more than quantity: Llama 2 stopped at about 27,500 carefully collected examples. SFT teaches format and style and gives the later preference stages a sensible starting point and reference model.</p></div>

<div class="recap"><div><span><b>Problem:</b> base models don't follow turns, don't stop, and mimic the prompt's style.</span></div><div><span><b>Core idea:</b> chat template + loss on assistant tokens only (+ end-of-turn).</span></div><div><span><b>Practice:</b> pack with a document mask; a small, high-quality dataset; judge by behaviour, not validation loss.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/post-training/01_sft_loss_masking.ipynb" target="_blank" rel="noopener">01 · Supervised fine-tuning: chat templates, loss masking and packing</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/post-training/01_sft_loss_masking.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../03-lora-qlora/index.html">03 · LoRA and QLoRA →</a> · Previous: <a href="../01-pipeline/index.html">← 01</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Ouyang et al. 2022 (InstructGPT §3.5, Appendix); Touvron et al. 2023 (Llama 2 §3.1: "Quality Is All You Need", 27,540 annotations, loss on answer tokens only, packing, hyperparameters).</p>

<!-- slide id="s-papers" from="papers" -->
