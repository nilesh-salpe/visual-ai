---
title: From MLP to Language Model
body:
  data-deck: From MLP to language model
  data-home: ../index.html
  data-home-label: NN fundamentals
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'last k tokens :: context window :: f'
  - 'embed + concat :: k × d vector :: c'
  - 'MLP :: hidden features :: a'
  - 'softmax :: p(next | context) :: b'
  - 'sample / train :: generate or cross-entropy :: e'
  loop: '4 -> 0 :: append and repeat'
  caption: 'Transformer: same objective, but attention reads the entire prefix instead of a fixed k.'
example:
  title: 'Worked example: notebook 07''s tiny character model'
  setup: 'A repeated toy text of sentences about cats, dogs and frogs: 18 distinct characters; 90% for training, 10% for validation.'
  steps:
  - 'Uniform guess over 18 characters: ln 18 = <b>2.89</b> nats per character.'
  - 'Counting bigram model (previous character only, smoothed): validation loss <b>1.00</b> nats.'
  - 'Neural model with 3 characters of context (8-dim embeddings, 64 tanh units): <b>0.33</b> nats, perplexity ≈ 1.4.'
  - Sampling at temperature 0.8 from "the" produces text like "the cat on the dog sat and the cat still. the log. the frog."
  result: More context and learned features cut the loss threefold; scaling the same recipe (with attention) gives modern LLMs.
traps:
  tricks:
  - 'LM = next-token classifier. :: Cross-entropy at every position.'
  - 'Teacher forcing. :: Train on true prefixes; all positions in parallel.'
  - 'Generate autoregressively. :: Sample, append, repeat.'
  traps:
  - 'Evaluating on training text. :: Repetitive data makes loss look far better than it is.'
  - 'Fixed context windows. :: The MLP LM cannot use anything older than k tokens.'
  - 'Greedy sampling. :: Repetitive loops; use temperature / top-p (Math deck 05).'
papers:
- bengio03
- vaswani
- gpt2
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Neural Networks · 10</div>
    <h1>From MLP to language model</h1>
    <p class="sub">Everything in this topic assembled: embeddings, an MLP and a softmax over the next character, trained by cross-entropy. Then the step from a fixed context window to the transformer.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>We want a model that, given some text, assigns a probability to every possible next token, and that we can sample from to generate more text.</div>
      <div class="c"><b>Core idea</b>Frame language modelling as <b>classification of the next token</b>. A <b>bigram</b> model just counts pairs. A <b>neural LM</b> (Bengio et al., 2003) embeds the last k tokens, passes them through an MLP and outputs a softmax, trained with cross-entropy. Transformers replace the fixed window with <b>attention</b> over the whole prefix.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## A bigram model in your browser

Character bigram counts from the notebook's toy text. Type a character to see the distribution over the next one, then sample text at a chosen temperature.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">previous character <input id="lC" type="text" maxlength="1" value="t" style="width:40px;text-align:center"></label><label class="ctl">temperature <input type="range" id="lT" min="0.2" max="2" step="0.1" value="1"> <output id="lTo"></output></label><button class="btn primary" id="lS">sample 80 chars</button></div>
  <div id="lBars" style="margin-top:12px"></div>
  <p class="readout" id="lOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## What counting can't do

::: cards grid3
### [d] Tiny context
A bigram sees one previous token; longer n-grams need exponentially many counts.

### [b] No sharing
Counts for "cat sat" say nothing about "dog sat", even though they behave alike.

### [c] Unseen combinations
Any context never seen in training gets no information beyond smoothing.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What does the neural LM add?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Compared with a counting n-gram model, what lets a neural LM generalise to unseen contexts?
- [ ] It memorises more counts
- [x] Learned embeddings: similar tokens get similar vectors, so knowledge transfers
- [ ] It uses no training data
- [ ] It has no softmax
> <b>B.</b> Bengio et al. (2003): because "cat" and "dog" get similar vectors, what the network learns about one context transfers to similar ones.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Language modelling as classification

::: cards grid3
### [a] Inputs
The previous k tokens, each embedded with a shared table and concatenated.

### [c] Network
A hidden layer (or many) computes features of the context.

### [e] Output
Softmax over the vocabulary; train with cross-entropy on the actual next token, at every position.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## From the MLP LM to the transformer

<div class="visual scroll-x"><table class="tbl">
  <tr><th></th><th>Bigram</th><th>MLP LM (2003)</th><th>Transformer LM</th></tr>
  <tr><td>Context</td><td>1 token</td><td>fixed k tokens</td><td>whole prefix (up to the context length)</td></tr>
  <tr><td>How context is combined</td><td>count table</td><td>concatenate embeddings → MLP</td><td>attention layers + MLPs, residual stream</td></tr>
  <tr><td>Parameters</td><td>V²</td><td>V·d + k·d·h + h·V</td><td>embeddings + 12·L·d²</td></tr>
  <tr><td>Training objective</td><td>counts</td><td>cross-entropy</td><td>cross-entropy</td></tr>
</table></div>
<p class="caption">Continue with the <a href="../../transformer/index.html">Transformer</a> and <a href="../../architecture/index.html">Modern LLM architecture</a> topics.</p>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why this recipe scales

::: cards grid2
### [a] Self-supervised
Every token of raw text is a training example; no labels needed.

### [e] One objective
Next-token cross-entropy forces the model to learn grammar, facts and reasoning patterns that help prediction.

### [b] Parallel training
With teacher forcing, all positions of a sequence are trained at once.

### [c] Generation for free
Sampling from the predicted distribution and appending turns the predictor into a generator.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "An LLM is fundamentally different from a next-character MLP."
> The objective and training loop are the same; architecture and scale differ.
:::

::: reveal myth
? "Language models look up answers in their training data."
> They compute a probability distribution from learned parameters; memorisation happens, but generation is computed.
:::

::: reveal myth
? "Lower training loss on a tiny repeated text means a good model."
> It mostly means memorisation; validation on held-out text is what counts.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? A model's validation loss is 0.33 nats per character. Perplexity?
- [ ] 0.33
- [x] ≈ 1.4
- [ ] ≈ 3
- [ ] 18
> e^0.33 ≈ <b>1.39</b>.
:::

::: reveal
? What is teacher forcing?
> During training, feed the true previous tokens (not the model's own samples), so all positions can be trained in parallel.
:::

::: reveal
? What limitation of the MLP LM does attention remove?
> The fixed context window: attention can read any earlier position in the sequence.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">A language model classifies the next token: embeddings plus a network plus a softmax, trained with cross-entropy; transformers replace the fixed window with attention over the whole prefix.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Language modelling is next-token classification. The simplest model counts how often each token follows each other token. Bengio and colleagues' neural model embeds the last few tokens, passes them through a hidden layer and outputs a softmax over the vocabulary, trained with cross-entropy; learned embeddings let it generalise to contexts it never saw. Generation samples a token, appends it and repeats. In notebook 07 this cuts the loss from 1.0 nats for a bigram to 0.33. Transformers keep exactly this objective but use attention to read the whole prefix instead of a fixed window.</p></div>
    <div class="recap"><div><span><b>Problem:</b> p(next token | text so far).</span></div><div><span><b>Core idea:</b> embed → network → softmax; cross-entropy.</span></div><div><span><b>Next:</b> attention over the whole prefix = transformer.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/nn-fundamentals/07_tiny_char_lm.ipynb" target="_blank" rel="noopener">07 · A tiny character-level language model</a> <span style="color:var(--faint)">· 40 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/nn-fundamentals/07_tiny_char_lm.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">You've finished the series. <a href="../../build-it/index.html">See all Build-it notebooks →</a> · Previous: <a href="../09-embeddings/index.html">← 09</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
