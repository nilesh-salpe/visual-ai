---
title: 'Putting It Together: a Tiny GPT'
body:
  data-deck: 'Putting it together: a tiny GPT'
  data-home: ../index.html
  data-home-label: PyTorch
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'tokens :: (B, T) :: f'
  - 'wte + wpe :: std 0.02 init :: c'
  - 'L × block :: RMSNorm, SDPA, MLP :: a'
  - 'norm → logits :: tied head :: b'
  - 'loss / sample :: train or generate :: e'
  loop: '4 -> 0 :: generation appends a token and repeats'
example:
  title: 'Worked example: notebook 09 on a laptop CPU'
  setup: A 2-layer, 64-wide character GPT (vocabulary 28) on a short repetitive text; 300 steps of AdamW (lr 3×10⁻³, β₂ 0.95), batch 16 × 32 characters.
  steps:
  - 'With nn.Embedding''s default std-1 initialisation and a tied head, the first loss was <b>46.5</b>: logits are huge. With GPT-2''s std 0.02 it starts at <b>3.36</b>
    ≈ ln 28 = 3.33, as an untrained model should.'
  - Training loss falls from 3.36 to <b>0.09</b>; validation loss <b>0.08</b> nats per character on this repetitive text.
  - 'Sampling at temperature 0.8 from "the " produces "the quick brown fox jumps over th lazy lazy love lazy dog. dog…": locally right, globally confused, as expected
    from a tiny model.'
  - The same code scaled up (12 layers, C = 768, GPUs, FSDP, torch.compile) is essentially nanoGPT's GPT-2 (124M).
  result: Initialisation scale matters immediately; once it is right, the standard loop trains a working language model in seconds.
traps:
  tricks:
  - 'Check loss at step 0. :: It should be ≈ ln V.'
  - 'Overfit one batch first. :: Loss → 0 proves the plumbing works.'
  - 'model.eval() + torch.no_grad() to sample. :: Faster and dropout-free.'
  traps:
  - 'Default std-1 embeddings with a tied head. :: Initial loss ≫ ln V.'
  - 'Forgetting to crop context. :: Inputs longer than the position table crash or misbehave.'
  - 'Evaluating in train mode. :: Dropout makes validation loss noisy and pessimistic.'
papers:
- nanogpt
- gpt2
- pytorch
status: {label: current, reviewed: 2026-10-15, note: "PyTorch 2.14.1 is still the latest release"}
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">PyTorch for LLMs · 09</div>
    <h1>Putting it together: a tiny GPT</h1>
    <p class="sub">Every piece of this topic in one small, runnable model: embeddings, pre-norm blocks with SDPA, a tied head, AdamW with weight-decay groups, warmup + cosine, clipping, and sampling, nanoGPT style.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Each previous deck showed one piece. To trust them, you need to see them work together: a model that trains, whose loss falls, and that generates text.</div>
      <div class="c"><b>Core idea</b>A GPT = <b>token + position embeddings</b> → <b>L pre-norm blocks</b> → final norm → <b>head tied to the embedding</b>. Train with the standard loop (AdamW, decay groups, warmup + cosine, clipping). Generate by repeatedly sampling from the last position's logits. Initialise embeddings with <b>std 0.02</b>.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Size and train your own GPT

Pick a configuration. The readout gives parameters, the memory to train it with AdamW in mixed precision, and how long 1B tokens take on one H100 at 40% MFU (model FLOPs utilization; 6 FLOPs per parameter per token).
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">layers <input type="range" id="gL" min="1" max="48" step="1" value="12"> <output id="gLo"></output></label>
    <label class="ctl">width <input type="range" id="gC" min="64" max="4096" step="64" value="768"> <output id="gCo"></output></label>
    <label class="ctl">vocabulary <input type="range" id="gV" min="64" max="128000" step="64" value="50304"> <output id="gVo"></output></label>
  </div>
  <div class="grid3" style="margin-top:12px">
    <div class="stat"><div class="num" id="gP"></div><div class="lbl">parameters (tied head)</div></div>
    <div class="stat"><div class="num" id="gM"></div><div class="lbl">AdamW training state (16 B/param)</div></div>
    <div class="stat"><div class="num" id="gT"></div><div class="lbl">per 1B tokens on one H100</div></div>
  </div>
</div>
<p class="caption">H100 SXM dense BF16 peak 989 TFLOP/s. Activations not included.</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why build a tiny one?

::: cards grid3
### [d] Bugs hide at scale
A wrong mask or init wastes thousands of GPU-hours before anyone notices.

### [b] Fast feedback
A tiny model trains in seconds on a CPU.

### [c] Same code path
Every component is the one you will scale.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What should the first loss be?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? An untrained model with vocabulary V = 28 and sensible initialisation. Its first cross-entropy loss is about…
- [ ] 0
- [x] ln 28 ≈ 3.33
- [ ] 28
- [ ] 46
> <b>B.</b> Near-uniform predictions give ln V. Notebook 09 got 46.5 with std-1 embeddings and a tied head, a sign of bad initialisation.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## The whole model

::: cards grid3
### [c] Embeddings
wte (V × C) + wpe (T_max × C), initialised with std 0.02.

### [a] Blocks
L pre-norm blocks: RMSNorm → SDPA attention → residual; RMSNorm → MLP → residual.

### [b] Head
Final RMSNorm, then logits = h @ wteᵀ (tied weights).
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Generation loop

<div class="visual"><pre style="margin:0;font:13px/1.55 'JetBrains Mono',monospace;white-space:pre-wrap">model.eval()&#10;idx = encode("the ")&#10;with torch.no_grad():&#10;    for _ in range(80):&#10;        logits, _ = model(idx[:, -T_max:])              # crop to the context window&#10;        probs = F.softmax(logits[0, -1] / 0.8, dim=-1)   # temperature 0.8&#10;        idx = torch.cat([idx, torch.multinomial(probs, 1)[None]], dim=1)&#10;print(decode(idx[0]))</pre></div>
<p class="caption">Without a KV cache this recomputes the whole prefix every step; serving systems cache keys and values (Inference deck 02).</p>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works

::: cards grid2
### [a] One objective
Next-token cross-entropy over every position trains the whole stack.

### [e] Stable recipe
Pre-norm, small init, AdamW with decay groups, warmup and clipping.

### [b] Tied embeddings
Fewer parameters and a shared notion of token similarity in and out.

### [c] Scales unchanged
More layers, data and GPUs (FSDP, compile) without changing the logic.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "A good tiny model proves the architecture."
> It proves the plumbing; architecture decisions need scaling experiments.
:::

::: reveal myth
? "Low training loss on repetitive text means it learned language."
> It memorised a tiny corpus; validation on varied text is the real test.
:::

::: reveal myth
? "Sampling needs special training."
> Generation reuses the trained next-token distribution; decoding choices are made at inference.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Parameters of a tied-head GPT with L = 12, C = 768, V = 50,304 (ignore positions, norms)?
- [ ] ≈ 85M
- [x] ≈ 124M
- [ ] ≈ 163M
- [ ] ≈ 350M
> 12 × 12 × 768² + 50,304 × 768 ≈ 84.9M + 38.6M ≈ <b>124M</b>.
:::

::: reveal
? Why initialise embeddings with std 0.02 when the head is tied?
> With std 1, logits = h·Eᵀ are huge at initialisation, giving a loss far above ln V and unstable early training.
:::

::: reveal
? What is the first check you run on a new training script?
> The step-0 loss ≈ ln V, then overfit a single batch to near-zero loss.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">A GPT is embeddings, pre-norm SDPA blocks and a tied head trained with the standard AdamW loop; check the step-0 loss (≈ ln V), then scale the same code up.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>This deck assembles the topic into a working model. Token and position embeddings, initialised with a small standard deviation, feed a stack of pre-norm blocks using scaled dot product attention, then a final norm and an output head that reuses the token embedding. The standard loop trains it: AdamW with weight decay only on matrices, warmup and cosine decay, gradient clipping. In notebook nine the default embedding initialisation gave a first loss of 46 instead of about three, a classic bug; with the fix the loss falls to under 0.1 and the model generates text. The same code at GPT-2 size has 124 million parameters.</p></div>
    <div class="recap"><div><span><b>Problem:</b> trust the pieces together.</span></div><div><span><b>Core idea:</b> embeddings → blocks → tied head; standard loop.</span></div><div><span><b>Checks:</b> step-0 loss ≈ ln V; overfit one batch.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/09_tiny_gpt.ipynb" target="_blank" rel="noopener">09 · Train a tiny GPT end to end</a> <span style="color:var(--faint)">· 40 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/09_tiny_gpt.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">You've finished the series. <a href="../../build-it/index.html">See all Build-it notebooks →</a> · Previous: <a href="../08-distributed/index.html">← 08</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
