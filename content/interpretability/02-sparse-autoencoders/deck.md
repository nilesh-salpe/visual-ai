---
title: Sparse Autoencoders
body:
  data-deck: Sparse autoencoders
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
  - 'activations :: e.g. middle-layer residual stream :: f'
  - 'encoder :: wide, ReLU or top-k :: a'
  - 'sparse latents :: few active per token :: b'
  - 'decoder :: reconstruct the activations :: c'
  - 'features :: inspect · clamp :: e'
  caption: Reconstruct activations through a wide, sparse bottleneck; each latent is a candidate feature.
example:
  title: 'Worked example: a feature in Claude 3 Sonnet'
  setup: Anthropic trained SAEs with about 1M, 4M and 34M features on Claude 3 Sonnet's middle-layer residual stream.
  steps:
  - Feature 34M/31164353 fires most strongly on references to the Golden Gate Bridge, more weakly on other bridges and tourist attractions.
  - It also fires on images of the bridge, though the SAE was trained only on text activations.
  - Clamping the feature high during the forward pass made the model bring up the bridge in most replies ("Golden Gate Claude", a 24-hour demo).
  - 'The same method surfaced safety-relevant features: code backdoors, bias, deception, power-seeking, sycophancy, dangerous content.'
  result: Activation examples suggest what a feature means; clamping it tests whether the model actually uses it.
traps:
  tricks:
  - 'Two objectives. :: Judge an SAE on reconstruction and sparsity together, plus interpretability.'
  - 'Top-k sparsity. :: k-sparse SAEs fix the number of active latents directly, simplifying tuning (OpenAI).'
  - 'Test by intervention. :: Clamp or ablate a feature and watch the output.'
  traps:
  - 'Dead latents. :: In the 34M-feature SAE about 65% of features never fired on 10⁷ tokens.'
  - 'Existence ≠ behaviour. :: A "deception" feature shows the model represents the concept, not that it lies.'
  - 'Partial reconstruction. :: Anthropic''s SAEs explained at least 65% of activation variance; the rest is unexplained.'
papers:
- mono_features
- sae_cunningham
- scaling_mono
- golden_gate
- sae_openai
- gemma_scope
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Interpretability · 02</div>
    <h1>Sparse autoencoders</h1>
    <p class="sub">Dictionary learning for language models: training a wide, sparse autoencoder on activations to recover interpretable features, from a one-layer transformer to Claude 3 Sonnet and GPT-4, and steering behaviour by clamping features.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>If features are packed in superposition, neither neurons nor principal components give one-concept units. We need a method that finds an overcomplete set of sparse directions, at the scale of production models.</div>
      <div class="c"><b>Core idea</b>Train a <b>sparse autoencoder</b> (SAE) to reconstruct a layer's activations through a much <b>wider</b> hidden layer where only a <b>few latents</b> are active per token (L1 penalty, or keep the top k). Each decoder direction is a candidate <b>feature</b>. Inspect what activates it, then test causality by <b>clamping</b> it during the forward pass.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Finding features in superposition

Superposition means a layer's activation vector is a sparse sum of many feature directions that overlap. Given only activations, can we recover those directions?
            {: .lede}

::: cards grid3
### [d] Overcomplete
There are more features than dimensions, so we need more directions than the layer has.

### [b] Sparse
Only a few features should be active on any token.

### [c] Production scale
Frontier models have millions of features across many layers.
:::

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why simpler decompositions fail

::: cards grid3
### [d] Neurons
Polysemantic: each mixes several features.

### [b] PCA / ICA
At most d directions, chosen for variance or independence rather than sparsity of concepts.

### [c] Supervised probes
Find only the concepts you already thought to label.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What should the hidden layer look like?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? You train an autoencoder on activations of dimension d to find features in superposition. What is the key design choice?
- [ ] A hidden layer narrower than d
- [x] A hidden layer much wider than d with a sparsity penalty, so few latents are active
- [ ] No hidden layer
- [ ] A dense hidden layer of width d
> **B.** Overcomplete and sparse: wide enough to give each feature its own latent, sparse so each input uses only a few.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Dictionary learning at scale

::: cards grid2
### [f] The model
f = ReLU(W_enc(x − b_dec) + b_enc), x̂ = W_dec f + b_dec; loss = reconstruction error + λ‖f‖₁ (or keep only the top k latents).

### [a] Towards Monosemanticity
A one-layer transformer's 512-neuron MLP; SAEs from 512 to 131,072 features trained on 8 billion activations; features for Arabic script, DNA, base64, Hebrew.

### [c] Scaling Monosemanticity
Claude 3 Sonnet, middle-layer residual stream; ~1M, ~4M and ~34M features; fewer than 300 active per token; at least 65% of variance explained; features are multilingual and fire on images too.

### [e] Other labs
OpenAI: k-sparse SAEs with clean scaling laws, a 16M-latent SAE on GPT-4 trained on 40B tokens. DeepMind: Gemma Scope, open JumpReLU SAEs for every layer of Gemma 2 2B and 9B.
:::

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Bigger dictionaries, more dead features <span class="ill">paper numbers</span>

<div class="visual"><div class="bars"><div id="dBars"></div></div><p class="readout">Share of features never active on a sample of 10⁷ tokens at the end of training, for Anthropic's three Claude 3 Sonnet SAEs. Dead latents waste capacity; OpenAI's top-k changes reduced them even at the largest scales they tried.</p></div>

In the notebook, a 16-latent SAE recovers 8 features hidden in 4 dimensions (mean cosine about 0.94) where PCA reaches about 0.82.

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why SAEs work, and what they miss

::: cards grid2
### [a] Matches superposition
An overcomplete sparse code is exactly the structure superposition predicts.

### [c] Unsupervised
Features emerge without labels, including ones nobody thought to look for.

### [b] Causal tests
Clamping or ablating features checks that the model really uses them (Golden Gate Claude).

### [d] Gaps
Reconstruction is partial, many latents can be dead, and features depend on dictionary size and training choices.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "SAE features are the model's true atoms."
> They are one useful decomposition; different sizes split or merge features, and reconstruction is incomplete.
:::

::: reveal myth
? "Finding a deception feature means the model is deceptive."
> Anthropic cautions that knowing about lies differs from lying; existence is not behaviour.
:::

::: reveal myth
? "Bigger SAEs are always better."
> They find finer features but more dead latents and higher cost.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? How does a k-sparse (top-k) SAE control sparsity?
- [ ] With a larger L1 penalty
- [x] By keeping only the k largest latents per input
- [ ] By shrinking the dictionary
- [ ] By using PCA first
> **B.** Exactly k latents stay active, which OpenAI found simplifies tuning and improves the reconstruction-sparsity frontier.
:::

::: reveal
? How would you check that an SAE feature matters to the model?
> Intervene: clamp it high or ablate it during the forward pass and measure the change in outputs.
:::

::: reveal
? Name two numbers that describe Anthropic's Claude 3 Sonnet SAEs.
> Up to ~34M features; fewer than 300 active per token; at least 65% of variance explained; ~65% dead features in the largest (any two).
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">A sparse autoencoder turns a layer's tangled activations into many sparse, mostly interpretable features.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Sparse autoencoders learn an overcomplete dictionary for a layer's activations: a wide hidden layer with few active latents per token. Towards Monosemanticity trained them on a one-layer transformer's 512-neuron MLP, with 512 to 131,072 features, and found features for Arabic script, DNA and base64. Scaling Monosemanticity applied them to Claude 3 Sonnet with up to about 34M features, fewer than 300 active per token, explaining at least 65% of variance; clamping the Golden Gate Bridge feature changed behaviour. OpenAI trained a 16M-latent top-k SAE on GPT-4; DeepMind released open SAEs on every layer of Gemma 2.</p></div>
    <div class="recap"><div><span><b>SAE:</b> wide, sparse autoencoder on activations</span></div><div><span><b>Scale:</b> 1M-34M features on Claude 3 Sonnet; 16M on GPT-4</span></div><div><span><b>Validation:</b> activation examples + clamping</span></div><div><span><b>Caveats:</b> dead latents, partial reconstruction</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/interpretability/01_superposition_and_sae.ipynb" target="_blank" rel="noopener">01 · Superposition and sparse autoencoders on a toy model</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/interpretability/01_superposition_and_sae.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../03-circuits-and-steering/index.html">03 · Circuits, probes and steering →</a> · Previous: <a href="../01-features-and-superposition/index.html">← 01</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
