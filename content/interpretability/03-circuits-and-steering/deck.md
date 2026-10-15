---
title: Circuits, Probes and Steering
body:
  data-deck: Circuits, probes and steering
  data-home: ../index.html
  data-home-label: Interpretability
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'clean vs corrupted :: two inputs :: f'
  - 'patch :: swap one component''s activation :: a'
  - 'measure :: change in the output :: b'
  - 'circuit :: the components that matter :: c'
  - 'steer :: add a direction :: e'
  caption: Correlation finds candidates; interventions show what the model actually uses.
example:
  title: 'Worked example: a steering vector'
  setup: 'Activation Addition (ActAdd): steer sentiment using one pair of prompts.'
  steps:
  - Run the model on "Love" and on "Hate" and record the activations at a chosen layer.
  - Steering vector = activation("Love") − activation("Hate").
  - On a new prompt, add a multiple of this vector at the same layer during the forward pass.
  - Outputs shift toward positive sentiment; ActAdd reported state-of-the-art negative-to-positive shift and detoxification on LLaMA-3 and OPT while preserving off-target
    performance.
  result: A single contrastive pair can define a direction that changes behaviour, with no training at all.
traps:
  tricks:
  - 'Patch, do not just observe. :: Causal interventions separate used information from mere correlation.'
  - 'Contrast pairs. :: Steering and probing directions come from differences between matched inputs.'
  - 'Judge circuits by faithfulness, completeness, minimality. :: The IOI study used all three criteria.'
  traps:
  - 'Probe accuracy ≠ use. :: A probe can decode information the model never uses.'
  - 'One mechanism per behaviour. :: Models often have parallel paths and shortcuts (attribution graphs found both).'
  - 'Over-steering. :: Large steering coefficients degrade fluency and off-target abilities.'
papers:
- ioi
- rome
- attribution_graphs
- actadd
- repe
- induction_heads
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Interpretability · 03</div>
    <h1>Circuits, probes and steering</h1>
    <p class="sub">From features to mechanisms: causal interventions that locate where a model computes something, circuits like indirect-object identification, attribution graphs in Claude, linear probes, and steering vectors that change behaviour at inference.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Knowing which features exist does not tell you how the model gets from input to output, or whether a representation is actually used. To explain or edit behaviour you need to find the components that cause it.</div>
      <div class="c"><b>Core idea</b>Intervene on activations. <b>Activation patching</b> copies activations from one input into a run on another and measures the effect, locating the components that matter; combined, they form a <b>circuit</b>. <b>Attribution graphs</b> trace feature-to-feature paths through a replacement model. <b>Linear probes</b> test whether information is present. <b>Steering vectors</b> add a direction to activations to change behaviour without training.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## From features to mechanisms

GPT-2 small completes "When Mary and John went to the store, John gave a drink to" with " Mary". Which parts of the network make that happen?
            {: .lede}

::: cards grid3
### [d] Many components
Hundreds of attention heads and MLP layers all contribute something.

### [b] Correlation misleads
A component can carry the right information without the model relying on it.

### [c] Need edits
To fix or steer behaviour you need the causal path, not just a description.
:::

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Limits of looking

::: cards grid3
### [d] Probes find too much
A classifier can decode a property from activations that the model never uses.

### [b] Attention patterns
Where a head attends is not the same as what it contributes.

### [c] Features alone
An SAE dictionary lists parts, not how they connect.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## How do you show a component matters?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? You suspect attention head 9.9 moves the indirect object's name to the output. Which experiment best tests it?
- [ ] Visualise its attention pattern
- [x] Replace its output with its output on a corrupted prompt (patching) and measure the drop in the correct answer's logit
- [ ] Count its parameters
- [ ] Train a probe on its output
> **B.** Activation patching is a causal intervention: if the behaviour breaks when that component's activation is swapped, the model uses it.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Intervene, trace, probe, steer

::: cards grid2
### [f] Patching and circuits
Indirect-object identification in GPT-2 small: 26 attention heads grouped into 7 classes, found with causal interventions and evaluated for faithfulness, completeness and minimality.

### [a] Causal tracing and editing
Factual recall runs through mid-layer feed-forward modules at the subject tokens; ROME edits a fact with a rank-one weight change.

### [c] Attribution graphs
Anthropic traced Claude 3.5 Haiku through a replacement model: Dallas → Texas → Austin as an intermediate step, rhyme words planned before a line is written, shared multilingual features. Satisfying insight on about a quarter of prompts tried.

### [e] Probes and steering
Representation engineering reads and controls population-level directions (honesty, harmlessness, power-seeking); ActAdd steers with one contrast pair.
:::

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Steering along a contrast direction <span class="ill">interactive</span>

<div class="visual"><div class="controls"><label class="ctl">steering coefficient <input type="range" id="gA" min="0" max="3" step="0.1" value="0"> <output id="gAo"></output></label></div><svg id="gSvg" viewBox="0 0 600 260" class="ill-svg"></svg><p class="readout" id="gOut"></p></div>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why interventions matter

::: cards grid2
### [a] Causality
Patching and ablation show necessity and sufficiency, which observation cannot.

### [c] Editing and control
Knowing where a computation happens lets you change it (ROME) or steer it (ActAdd).

### [b] Safety audits
Mechanisms can reveal hidden reasoning or shortcuts that outputs and chains of thought do not show.

### [d] Incomplete
Even the best tools explain only part of behaviour on a fraction of prompts; replacement models are approximations.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "If a probe can read it, the model uses it."
> Probes test presence, not use; patching tests use.
:::

::: reveal myth
? "Each behaviour has one circuit."
> Attribution graphs found shortcut paths alongside multi-step ones.
:::

::: reveal myth
? "Steering requires finetuning."
> ActAdd needs no optimisation: one contrast pair defines the vector.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? What three criteria did the IOI study use to evaluate its circuit?
- [ ] Speed, size, cost
- [x] Faithfulness, completeness, minimality
- [ ] Accuracy, recall, precision
- [ ] Loss, perplexity, entropy
> **B.** Does the circuit reproduce the behaviour, does it include everything that matters, and is every part needed.
:::

::: reveal
? What does ROME change, and where?
> A rank-one update to a mid-layer feed-forward weight matrix, where causal tracing located factual recall.
:::

::: reveal
? How is an ActAdd steering vector built?
> Take the activation difference between two contrasting prompts (e.g. "Love" − "Hate") at a layer and add a multiple of it during the forward pass.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Interpretability becomes useful when it intervenes: patch to find mechanisms, steer to change behaviour.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Activation patching runs the model on one input with some activations copied from another, revealing which components carry the information. The indirect-object identification circuit in GPT-2 small involves 26 attention heads in 7 classes, evaluated for faithfulness, completeness and minimality. Causal tracing located factual recall in mid-layer MLPs at subject tokens, enabling rank-one edits (ROME). Anthropic's attribution graphs found Claude 3.5 Haiku computing "Texas" on the way from Dallas to Austin and planning rhymes ahead, though they gave satisfying insight on about a quarter of prompts. Steering vectors such as ActAdd change behaviour by adding a contrast direction at inference.</p></div>
    <div class="recap"><div><span><b>Patching:</b> swap activations, measure the effect</span></div><div><span><b>Circuits:</b> IOI: 26 heads in 7 classes</span></div><div><span><b>Attribution graphs:</b> multi-hop and planning in Claude 3.5 Haiku</span></div><div><span><b>Steering:</b> add a contrast direction at inference</span></div></div>
    <p class="start-hint">You've finished the series. <a href="../../build-it/index.html">See all Build-it notebooks →</a> · Previous: <a href="../02-sparse-autoencoders/index.html">← 02</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
