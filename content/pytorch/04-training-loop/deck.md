---
title: The Training Loop
body:
  data-deck: The training loop
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
  - 'zero_grad :: clear .grad :: f'
  - 'forward + loss :: :: a'
  - 'backward :: fill .grad :: b'
  - 'clip :: max norm 1.0 :: d'
  - 'opt.step + sched.step :: update, next LR :: e'
  loop: '4 -> 0 :: every step; checkpoint every N steps'
  caption: 'Optimizer theory: NN fundamentals deck 05.'
example:
  title: 'Worked example: what a checkpoint must contain'
  setup: 'Notebook 04: train 40 steps straight, versus 20 steps → checkpoint → reload into fresh objects → 20 more steps.'
  steps:
  - 'Saving model + optimizer + scheduler state_dicts and loading all three: the final weights match the uninterrupted run exactly (max difference <b>0</b>).'
  - 'Saving only the model weights: Adam''s moment estimates and the scheduler position are lost; warmup restarts and the weights end up different (max difference
    ≈ 0.4 in the notebook).'
  - For a 7B model, AdamW's m and v in FP32 are 8 bytes × 7B = 56 GB, twice the FP32 weights themselves.
  - 'PyTorch''s AdamW defaults: lr 10⁻³, betas (0.9, 0.999), eps 10⁻⁸, weight_decay 0.01 (LLM recipes often use 0.1 and β₂ 0.95).'
  result: The optimizer state is part of the model's training state; resume with all of it or the run changes.
traps:
  tricks:
  - 'Parameter groups. :: decay = p.dim() ≥ 2; no decay for biases and norms.'
  - 'LambdaLR(opt, fn). :: fn(step) multiplies the base learning rate.'
  - 'torch.save a dict of state_dicts. :: model, opt, sched, step, RNG.'
  traps:
  - 'sched.step() before opt.step(). :: PyTorch warns and the first LR value is skipped.'
  - 'Saving the whole model object. :: Pickles code paths; save state_dicts instead.'
  - 'Clipping after opt.step(). :: Too late; clip between backward and step.'
papers:
- adamw
- pytorch
- nanogpt
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">PyTorch for LLMs · 04</div>
    <h1>The training loop</h1>
    <p class="sub">The handful of lines every PyTorch training script shares: zero_grad, forward, loss, backward, clipping, optimizer and scheduler steps, parameter groups for weight decay, and checkpoints that resume exactly.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Training runs for days, must be stable, and will be interrupted. The loop has to apply the right update every step and resume after a crash as if nothing happened.</div>
      <div class="c"><b>Core idea</b>Each step: <code>opt.zero_grad(set_to_none=True)</code> → <code>loss = …</code> → <code>loss.backward()</code> → <code>clip_grad_norm_(…, 1.0)</code> → <code>opt.step()</code> → <code>sched.step()</code>. Put biases and norm gains in a no-decay <b>parameter group</b>. A checkpoint stores <b>model, optimizer and scheduler</b> state (plus RNG and data position).</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## What does a checkpoint weigh?

Model, gradients and AdamW state for a given size and precision. The checkpoint you save is model + optimizer (gradients are recomputed).
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">parameters <input type="range" id="cN" min="8" max="11.6" step="0.05" value="9.85"> <output id="cNo"></output></label><div class="seg" id="cSeg"><button data-v="mixed" class="on">BF16 weights + FP32 master</button><button data-v="fp32">all FP32</button></div></div>
  <div id="cBars" style="margin-top:12px"></div>
  <p class="readout" id="cOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## What goes wrong in naive loops

::: cards grid3
### [d] Stale gradients
Forgetting zero_grad adds last step's gradients to this one.

### [b] Loss spikes
One huge gradient can wreck a run without clipping.

### [c] Non-resumable runs
Restarting from weights alone changes the optimisation trajectory.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Where does clipping go?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? In which position should torch.nn.utils.clip_grad_norm_ be called?
- [ ] Before loss.backward()
- [x] Between loss.backward() and opt.step()
- [ ] After opt.step()
- [ ] After sched.step()
> <b>B.</b> Gradients exist only after backward, and they must be clipped before the optimizer uses them.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Six lines, in order

::: cards grid3
### [f] zero_grad
Reset .grad (set_to_none=True frees the memory).

### [a] forward, loss, backward
Compute the loss and fill gradients.

### [e] clip, step, schedule
Clip the global norm, update weights, advance the learning rate.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## The loop in code

<div class="visual"><pre style="margin:0;font:13px/1.55 'JetBrains Mono',monospace;white-space:pre-wrap">decay    = [p for p in model.parameters() if p.dim() >= 2]&#10;no_decay = [p for p in model.parameters() if p.dim() < 2]&#10;opt = torch.optim.AdamW([{"params": decay, "weight_decay": 0.1},&#10;                         {"params": no_decay, "weight_decay": 0.0}], lr=3e-4, betas=(0.9, 0.95))&#10;sched = torch.optim.lr_scheduler.LambdaLR(opt, warmup_then_cosine)&#10;&#10;for step, (x, y) in enumerate(loader):&#10;    opt.zero_grad(set_to_none=True)&#10;    logits, loss = model(x, y)&#10;    loss.backward()&#10;    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)&#10;    opt.step(); sched.step()&#10;    if step % 1000 == 0:&#10;        torch.save({"model": model.state_dict(), "opt": opt.state_dict(),&#10;                    "sched": sched.state_dict(), "step": step}, "ckpt.pt")</pre></div>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why each line is there

::: cards grid2
### [a] zero_grad
Gradients accumulate by design (deck 02).

### [e] Clipping
Bounds the update size when a rare batch produces a huge gradient.

### [b] No decay on norms and biases
Shrinking gains toward 0 fights normalisation for no benefit.

### [c] Full checkpoints
Exact resumption after hardware failures (Distributed deck 11).
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "model.state_dict() is a complete checkpoint."
> Without optimizer and scheduler state, resuming changes the run (notebook 04).
:::

::: reveal myth
? "AdamW's default weight decay is 0."
> In PyTorch it is 0.01; Adam's default is 0.
:::

::: reveal myth
? "Gradient clipping changes the gradient direction."
> Norm clipping rescales all gradients by one factor; the direction is preserved.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? FP32 bytes of AdamW m + v for a 1B-parameter model?
- [ ] 4 GB
- [x] 8 GB
- [ ] 16 GB
- [ ] 2 GB
> 2 × 4 bytes × 1B = <b>8 GB</b>.
:::

::: reveal
? Why exclude LayerNorm/RMSNorm weights from weight decay?
> They are scale parameters; decaying them toward zero fights the normalisation and does not regularise usefully.
:::

::: reveal
? What should a resumable checkpoint store?
> Model, optimizer and scheduler state dicts, the step count, RNG states and the data loader position.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Every step is zero_grad → forward → loss → backward → clip → optimizer step → scheduler step; decay only matrices, and checkpoint model + optimizer + scheduler to resume exactly.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>PyTorch training loops share six lines: zero the gradients, run the forward pass and loss, call backward, clip the gradient norm, step the optimizer and step the learning-rate scheduler. AdamW is usually given two parameter groups so weight decay applies only to weight matrices, not biases or normalisation gains, and a LambdaLR scheduler implements warmup plus cosine decay. A checkpoint must contain the model, optimizer and scheduler states: notebook four shows that resuming from weights alone changes the run, because Adam's moment estimates and the schedule position are lost.</p></div>
    <div class="recap"><div><span><b>Problem:</b> stable, resumable multi-day training.</span></div><div><span><b>Core idea:</b> six lines in a fixed order; decay groups.</span></div><div><span><b>Checkpoint:</b> model + optimizer + scheduler + step + RNG.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/04_training_loop.ipynb" target="_blank" rel="noopener">04 · The training loop: AdamW, schedules, clipping, checkpoints</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/04_training_loop.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../05-data/index.html">05 · Data pipelines for LLMs →</a> · Previous: <a href="../03-nn-module/index.html">← 03</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
