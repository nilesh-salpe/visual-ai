---
title: Reliability and Stability
body:
  data-deck: Reliability and stability
  data-home: ../index.html
  data-home-label: Distributed
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'monitor :: heartbeats, step times, loss :: c'
  - 'detect :: failure, straggler, spike :: d'
  - 'isolate :: drain bad node / skip data :: b'
  - 'restore :: latest checkpoint :: a'
  - 'resume :: lost work ≈ half an interval :: e'
  loop: '4 -> 0 :: hundreds of times per run'
  caption: Goodput = useful training time ÷ wall-clock time.
example:
  title: 'Worked example: what checkpoint speed buys'
  setup: 'Llama 3 405B: 419 interruptions in 54 days → MTBF (mean time between failures) ≈ 3.1 h. Restart cost 10 minutes. Simulated in notebook 08 (5 seeds each).'
  steps:
  - 'Synchronous checkpoint to storage, 5 min: Young''s interval √(2 × 5 min × 3.1 h) ≈ <b>43 min</b> → goodput <b>74.5%</b>.'
  - 'Async checkpoint, 30-second pause: interval ≈ 14 min → goodput <b>88.3%</b>.'
  - 'In-memory checkpoint, 5 seconds (Gemini-style): interval ≈ 5.6 min → goodput <b>92.2%</b>.'
  - Llama 3 reported more than 90% effective training time over its 54-day run.
  result: The checkpoint cost, not the failure rate, is the lever you control; cutting it from minutes to seconds recovers most lost goodput.
traps:
  tricks:
  - 'Interval ≈ √(2·C·MTBF). :: Young''s approximation.'
  - 'Rollback and skip. :: PaLM restarted ~100 steps before a spike and skipped 200–500 batches.'
  - 'Stability knobs. :: z-loss 10⁻⁴·log²Z (PaLM), QK-norm (ViT-22B), FP32 reductions (Llama 3).'
  traps:
  - 'Synchronous saves at scale. :: Every GPU stalls for the whole write.'
  - 'Treating slow nodes as healthy. :: A straggler slows all 16K GPUs every step.'
  - 'Restarting into the same failure. :: Drain and test suspect hardware; skip the data that triggered a spike.'
papers:
- llama3
- megascale
- gemini
- palm_stab
- vit22b
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Distributed Training · 11</div>
    <h1>Reliability and stability</h1>
    <p class="sub">Keeping a months-long, 16,000-GPU run alive: fast checkpoint and restart, straggler detection, and the loss-spike playbook (rollback, skip data, z-loss, QK-norm).</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>At 16K GPUs something fails every few hours, a single slow GPU slows every step, and the loss can suddenly spike and diverge, each threatening weeks of compute.</div>
      <div class="c"><b>Core idea</b>Make every failure <b>cheap</b>: frequent, fast (async or in-memory) checkpoints and automated restart; detect and evict <b>stragglers</b>; and handle <b>instability</b> with rollback-and-skip, FP32 reductions, z-loss and QK normalization.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Goodput vs checkpoint interval

Expected fraction of wall-clock time spent on useful training, from a simple model: overhead ≈ C/τ (saving) + τ/(2·MTBF) (lost work) + R/MTBF (restarts). Move the checkpoint cost and interval.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">checkpoint cost C (s) <input type="range" id="yC" min="1" max="600" step="1" value="300"> <output id="yCo"></output></label><label class="ctl">job MTBF (h) <input type="range" id="yM" min="0.5" max="24" step="0.1" value="3.1"> <output id="yMo"></output></label></div>
  <svg id="ySvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Goodput vs interval"></svg>
  <p class="readout" id="yOut"></p>
</div>
<p class="caption">Analytic approximation with a 10-minute restart; notebook 08 checks it with a Monte Carlo simulation of a 54-day run.</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Three ways a big run loses time

::: cards grid3
### [d] Hard failures
GPU, memory, network and host faults: Llama 3 saw 419 unexpected interruptions in 54 days (~78% hardware). See <a href="../../gpu/06-gpu-failures/index.html">GPU deck 06</a>.

### [b] Stragglers
A GPU that is slow but alive (thermal throttling, a bad link) delays every synchronous step for everyone.

### [c] Instability
Loss spikes and divergence: PaLM saw about 20 spikes in its largest run.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What fixes a loss spike?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? PaLM's largest run hit a loss spike. What did the team do?
- [ ] Lowered the learning rate permanently
- [x] Restarted about 100 steps before the spike and skipped 200–500 batches
- [ ] Ignored it
- [ ] Retrained from scratch
> <b>B.</b> They rolled back to a checkpoint about 100 steps earlier and skipped roughly 200–500 data batches around the spike. The spikes were tied to specific data and model-state combinations rather than "bad data" alone.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Make failures cheap, slow nodes visible, training stable

::: cards grid3
### [a] Fast checkpoint and restart
Async writes, in-memory copies on peer hosts (Gemini: >13× faster recovery), sharded checkpoints and automated restart.

### [b] Detect stragglers
Per-rank step-time and heartbeat monitoring; MegaScale built diagnosis tools and recovered its run 100+ times.

### [e] Stabilize the math
FP32 gradient reductions (Llama 3), z-loss on the softmax normalizer (PaLM), QK normalization against exploding attention logits (ViT-22B), rollback-and-skip.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Stragglers: the slowest GPU sets the pace

Each GPU's step time varies slightly; a synchronous step waits for the slowest. Increase the GPU count and watch the expected slowdown grow, then add one degraded GPU.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">GPUs <input type="range" id="sN" min="0" max="5" step="1" value="3"> <output id="sNo"></output></label><label class="ctl">one GPU slower by <input type="range" id="sS" min="0" max="50" step="5" value="0"> <output id="sSo"></output></label></div>
  <div id="sBars" style="margin-top:12px"></div>
</div>
<p class="caption">Illustrative: each GPU's step time is 1 + noise with 2% standard deviation; the step takes the maximum.</p>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why these measures work

::: cards grid2
### [a] Lost work scales with the interval
Each failure costs about half an interval plus restart; cheaper checkpoints allow shorter intervals.

### [e] Automation beats heroics
Llama 3: only three interruptions needed significant manual intervention; the rest were handled automatically.

### [b] Spikes are often transient
Rolling back and skipping the triggering batches let PaLM continue; architectural fixes like QK-norm prevent some spikes entirely.

### [c] Stable training is possible
DeepSeek-V3 reported no irrecoverable loss spikes and no rollbacks over its whole run.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "With reliable hardware you can skip checkpoints."
> Even very reliable GPUs fail every few hours in aggregate at 16K scale.
:::

::: reveal myth
? "A loss spike means the data is bad."
> PaLM found spikes weren't reproduced by the same data alone; they depend on data and model state together.
:::

::: reveal myth
? "Stragglers only slow their own work."
> In synchronous training every GPU waits for the slowest at each collective.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Young's interval for C = 5 min and MTBF = 3.1 h?
- [ ] ≈ 5 min
- [x] ≈ 43 min
- [ ] ≈ 3 h
- [ ] ≈ 10 h
> √(2 × 0.083 h × 3.1 h) ≈ 0.72 h ≈ <b>43 min</b>.
:::

::: reveal
? Name three stability techniques used in large runs.
> Rollback and skip batches (PaLM), z-loss (PaLM), QK normalization (ViT-22B), FP32 gradient accumulation and reduce-scatter (Llama 3).
:::

::: reveal
? Why do in-memory checkpoints help so much?
> They take seconds instead of minutes, so you can checkpoint far more often and lose less work per failure, and recovery reads from fast memory instead of remote storage.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">At frontier scale failures, stragglers and loss spikes are routine; fast checkpoints, automated recovery, straggler detection and stability tricks keep goodput above 90%.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>A run on sixteen thousand GPUs fails every few hours, a single slow GPU delays every synchronous step, and losses can spike. The goal is to make each event cheap. Checkpoint often and fast, asynchronously or into peer CPU memory, which Gemini reports recovers more than thirteen times faster, and restart automatically; the optimal interval is roughly the square root of two times the checkpoint cost times the mean time between failures. Monitor step times to find and evict stragglers. For instability, roll back and skip the batches around a spike as PaLM did, and use FP32 reductions, z-loss and QK normalization. Llama 3 kept effective training time above 90 percent.</p></div>
    <div class="recap"><div><span><b>Problem:</b> failures every few hours, stragglers, loss spikes.</span></div><div><span><b>Core idea:</b> cheap checkpoints + automated restart; detect stragglers; stabilize the math.</span></div><div><span><b>Numbers:</b> interval ≈ √(2·C·MTBF); Llama 3 >90% effective time.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/distributed/08_checkpoint_failures.ipynb" target="_blank" rel="noopener">08 · Failures, checkpoints and goodput</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/distributed/08_checkpoint_failures.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">You've finished the series. <a href="../../build-it/index.html">See all Build-it notebooks →</a> · Previous: <a href="../10-putting-it-together/index.html">← 10</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
