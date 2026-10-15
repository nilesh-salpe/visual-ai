---
title: Features and Superposition
body:
  data-deck: Features and superposition
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
  - 'activation vector :: d numbers :: f'
  - 'features :: directions, not neurons :: a'
  - 'sparse features :: more than d of them :: b'
  - 'superposition :: near-orthogonal packing :: c'
  - 'interference :: filtered by ReLU :: d'
  caption: Sparse features can share dimensions; neurons then mix several features.
example:
  title: 'Worked example: five features in two dimensions'
  setup: 'The toy model from Toy Models of Superposition: five features of different importance, embedded in 2 dimensions, followed by a ReLU.'
  steps:
  - 'Dense features (often active together): the model represents the two most important features on orthogonal directions, like PCA, and drops the other three.'
  - 'Sparse features (rarely active together): the model stores all five, as the vertices of a pentagon.'
  - 'Neighbouring pentagon directions are 72° apart: cosine 0.31, so an active feature leaks 0.31 onto its neighbours (interference).'
  - Because features are rarely active together, a ReLU with a small negative bias removes most of that leakage.
  result: 'Sparsity is what makes superposition worth it: occasional interference costs less than dropping features.'
traps:
  tricks:
  - 'Features are directions. :: Analyse projections onto directions, not single neuron values.'
  - 'Sparsity enables superposition. :: Dense features get orthogonal dimensions; sparse ones share.'
  - 'Phase changes. :: As sparsity grows, features switch abruptly from absent to stored in superposition.'
  traps:
  - 'Reading a neuron as a concept. :: Polysemantic neurons respond to several unrelated features.'
  - 'Assuming orthogonality. :: With more features than dimensions, directions must overlap.'
  - 'Equating PCA with features. :: PCA finds at most d dense directions, not the sparse features.'
papers:
- toy_superposition
- induction_heads
- mono_features
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Interpretability · 01</div>
    <h1>Features and superposition</h1>
    <p class="sub">What interpretability looks for inside a network: features as directions in activation space, why single neurons are polysemantic, and how sparse features are packed into fewer dimensions than there are features.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>To understand or audit a model you want to know what its internal activations represent. Looking at individual neurons fails: a single neuron often responds to several unrelated concepts (polysemanticity), so "what does neuron 1,234 do?" has no clean answer.</div>
      <div class="c"><b>Core idea</b>Treat a <b>feature</b> as a <b>direction</b> in activation space rather than a neuron. When features are <b>sparse</b> (rarely active at the same time), a network can store <b>more features than it has dimensions</b> by giving them nearly orthogonal directions: <b>superposition</b>. The cost is <b>interference</b> between features, which nonlinearities filter out. Superposition explains polysemantic neurons and motivates dictionary learning (deck 02).</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## What does this neuron do?

You inspect one neuron of a language model and collect the texts that activate it most. They include academic citations, Korean text, HTTP requests and dialogue. There is no single concept to name.
            {: .lede}

            ::: cards grid3
### [d] Polysemantic neurons
Many neurons respond to several unrelated concepts.

### [b] Too many concepts
A model knows far more concepts than it has neurons in any layer.

### [c] Need a unit of analysis
Auditing a model requires parts that each mean one thing.
:::

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why neurons are the wrong unit

::: cards grid3
### [d] Basis is arbitrary
Nothing forces the network to align concepts with individual neurons; any rotation of a layer's space works as well for the next layer, except where nonlinearities act.

### [b] Dimensions are scarce
A layer with d dimensions has only d orthogonal directions.

### [c] PCA does not help
Principal components are dense directions of maximum variance, at most d of them.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## More features than dimensions?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? A layer has 2 dimensions and the model needs 5 features. When can it represent all 5?
- [ ] Never: 2 dimensions hold 2 features
- [x] When the features are sparse, so they are rarely active at the same time
- [ ] When the features are dense
- [ ] Only with more layers
> **B.** With sparse features, overlapping directions rarely interfere in practice; the toy model then stores all five as a pentagon.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Features as directions, packed in superposition

::: cards grid2
### [f] Feature = direction
A concept is represented by how far the activation vector points along a direction.

### [a] Superposition
With sparse features, the model stores more of them than it has dimensions, as nearly orthogonal directions, accepting interference.

### [c] Sparsity decides
Dense features: only the most important get dimensions. Sparse: more are packed, with phase changes between regimes and polytope geometry.

### [e] Circuits use features
Mechanisms like induction heads ([A][B] ... [A] → [B]) are built from such features; induction heads appear exactly when in-context learning improves sharply during training.
:::

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Packing features into two dimensions <span class="ill">interactive</span>

<div class="visual"><div class="controls"><label class="ctl">features in 2-D <input type="range" id="sN" min="2" max="8" step="1" value="5"> <output id="sNo"></output></label></div><svg id="sSvg" viewBox="0 0 600 260" class="ill-svg"></svg><p class="readout" id="sOut"></p></div>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why networks do this

::: cards grid2
### [a] Capacity
The world has far more useful features than any layer has dimensions.

### [c] Sparsity is natural
Most concepts (a city, a programming language, DNA) are absent from most inputs.

### [b] Nonlinear filtering
ReLU-like nonlinearities suppress small interference terms, making overlap cheap.

### [e] Consequences
Polysemantic neurons, a link to adversarial examples, and the need for dictionary learning to recover features.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Each neuron stands for one concept."
> Superposition spreads features across neurons, so most neurons are polysemantic.
:::

::: reveal myth
? "A model can store at most d features in d dimensions."
> Only if features are dense; sparse features can be packed far beyond d with tolerable interference.
:::

::: reveal myth
? "Interpretability means reading the weights."
> Weights alone are hard to read; most methods study activations on real inputs and test causal effects.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? In the toy model with dense features, what does the network represent?
- [ ] All five features in a pentagon
- [x] Only the two most important features, orthogonally
- [ ] No features
- [ ] Random directions
> **B.** Dense features cannot share directions cheaply, so only the most important get dimensions (like PCA).
:::

::: reveal
? What is polysemanticity, and what explains it?
> A neuron responding to several unrelated concepts; superposition (features stored as overlapping directions) explains it.
:::

::: reveal
? What is an induction head?
> An attention head that completes [A][B] ... [A] → [B] by copying what followed a previous occurrence of the current token; it forms when in-context learning improves sharply in training.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Networks store more features than they have neurons by packing sparse features into overlapping directions.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Interpretability treats features as directions in activation space. Individual neurons are often polysemantic because of superposition: when features are sparse, a network can represent more of them than it has dimensions by giving them nearly orthogonal directions and tolerating interference. In the toy model, five features in two dimensions are dropped down to two when dense, but stored as a pentagon when sparse. This is why later methods look for an overcomplete set of sparse directions instead of reading neurons.</p></div>
    <div class="recap"><div><span><b>Feature:</b> a direction in activation space</span></div><div><span><b>Polysemantic:</b> one neuron, many features</span></div><div><span><b>Superposition:</b> more sparse features than dimensions</span></div><div><span><b>Cost:</b> interference, filtered by nonlinearities</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/interpretability/01_superposition_and_sae.ipynb" target="_blank" rel="noopener">01 · Superposition and sparse autoencoders on a toy model</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/interpretability/01_superposition_and_sae.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../02-sparse-autoencoders/index.html">02 · Sparse autoencoders →</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
