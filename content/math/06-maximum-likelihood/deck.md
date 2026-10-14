---
title: Maximum Likelihood and Cross-Entropy
body:
  data-deck: Maximum likelihood and cross-entropy
  data-home: ../index.html
  data-home-label: Math
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'text :: actual next tokens :: f'
  - 'model :: p(token | context) :: c'
  - '−log p(actual) :: surprise per token :: d'
  - 'average :: loss in nats/token :: a'
  - 'gradient :: p − onehot :: e'
  caption: perplexity = e^loss
example:
  title: 'Worked example: reading loss values'
  setup: Losses in nats (natural log) per token; GPT-2's vocabulary has 50,257 tokens.
  steps:
  - 'A model that guesses uniformly: loss = ln 50,257 ≈ <b>10.82</b> nats, perplexity 50,257.'
  - 'If the actual token always gets probability 0.25: loss = −ln 0.25 ≈ <b>1.386</b>, perplexity 4.'
  - 'A loss of 2.0 nats means perplexity e² ≈ <b>7.39</b>: as uncertain as choosing among about 7 equally likely tokens.'
  - 'One confident mistake, p(actual) = 0.001, costs −ln 0.001 ≈ 6.9 nats: the log punishes confident errors hard.'
  result: Loss is average surprise in nats; perplexity e^loss is the equivalent number of equally likely choices.
traps:
  tricks:
  - '∂L/∂logits = p − y. :: Softmax + cross-entropy has the simplest gradient in deep learning.'
  - 'Perplexity = e^loss. :: Or 2^loss if the loss is in bits.'
  - 'Average per token. :: So losses compare across batch and sequence sizes.'
  traps:
  - 'Comparing perplexities across tokenizers. :: Different vocabularies change the unit; compare bits per byte instead.'
  - 'log(softmax(z)) naively. :: Use log-softmax (Softmax deck) to avoid log 0.'
  - 'Reading loss 0 as the goal. :: Natural text has irreducible uncertainty; held-out loss never reaches 0.'
papers:
- bengio03
- gpt2
- shannon
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Math for LLMs · 06</div>
    <h1>Maximum likelihood and cross-entropy</h1>
    <p class="sub">Why the LLM training loss is the average negative log-probability of the actual next token, what its values mean, and how it relates to perplexity.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>We have a model that outputs next-token probabilities and a mountain of text. We need a single number that says how good the model is and that gradient descent can minimise.</div>
      <div class="c"><b>Core idea</b>Pick parameters that make the observed text most probable: <b>maximum likelihood</b>. Taking logs and averaging gives the <b>cross-entropy loss</b> L = −(1/N) Σ log p(xₜ | x₍&lt;t₎). Its gradient with respect to the logits is simply p − onehot(target).</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## How much should a wrong guess cost?

Move the probability the model gave to the actual next token. The curve is −log p: near-free when the model is confident and right, very expensive when it is confident and wrong.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">p(actual token) <input type="range" id="lP" min="0.001" max="1" step="0.001" value="0.25"> <output id="lPo"></output></label></div>
  <svg id="lSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Negative log likelihood curve"></svg>
  <p class="readout" id="lOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why not simpler losses?

::: cards grid3
### [d] Accuracy
Counting top-1 hits ignores how much probability went to the right token and has zero gradient almost everywhere.

### [b] Squared error on probabilities
Barely penalises assigning 0.001 to the right answer; gradients vanish when the model is confidently wrong.

### [c] Raw likelihood
The product of millions of probabilities underflows to 0; logs turn it into a sum.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Which costs more?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Which prediction gets the larger cross-entropy loss?
- [ ] p(actual) = 0.5
- [ ] p(actual) = 0.9
- [x] p(actual) = 0.01
- [ ] They are equal
> <b>C.</b> −ln 0.01 ≈ 4.6 nats, versus 0.69 for 0.5 and 0.11 for 0.9. Low probability on what actually happened is punished hardest.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Maximise likelihood = minimise cross-entropy

::: cards grid3
### [a] Likelihood
The probability the model assigns to the training text: Πₜ p(xₜ | x₍&lt;t₎).

### [c] Log and average
Maximising it equals minimising the average −log p: the cross-entropy between data and model.

### [e] Simple gradient
For softmax outputs, ∂L/∂zᵢ = pᵢ − 1[i = target]: push the target up, everything else down in proportion.
:::

<div class="eq">L = −(1/N) Σₜ log p_θ(xₜ | x₍&lt;t₎)   ·   ∂L/∂z = p − onehot(xₜ)</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Per-token loss across a sentence

Illustrative per-token probabilities for "The capital of France is Paris ." Easy tokens cost little; surprising ones dominate the average.
{: .lede}

<div class="visual"><div id="tBars"></div><p class="readout" id="tOut"></p></div>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why maximum likelihood is the default

::: cards grid2
### [a] Proper
The loss is minimised exactly when the model's distribution equals the data distribution, so honest probabilities are rewarded.

### [e] Dense signal
Every token of every document gives a gradient, unlike sparse task labels.

### [b] Information-theoretic meaning
Cross-entropy in bits is the code length for compressing the text with the model (Shannon).

### [c] Same loss everywhere
Pretraining, supervised fine-tuning and distillation all use cross-entropy, just with different targets.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Cross-entropy and log-loss are different things."
> For one-hot targets they are the same: −log p(actual).
:::

::: reveal myth
? "Lower perplexity always means a better assistant."
> It means better next-token prediction on that text; helpfulness also depends on post-training.
:::

::: reveal myth
? "The loss should go to zero."
> Text is inherently uncertain; the minimum achievable loss is the data's entropy, well above 0.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Loss of 3.0 nats per token. Perplexity?
- [ ] 3
- [ ] ≈ 8
- [x] ≈ 20
- [ ] ≈ 1,000
> e³ ≈ <b>20.1</b>.
:::

::: reveal
? What is the gradient of softmax + cross-entropy with respect to the logits?
> p − onehot(target): the predicted probabilities minus 1 at the target index.
:::

::: reveal
? Why are perplexities hard to compare between models with different tokenizers?
> Loss is per token, and tokens cover different amounts of text; normalise per byte or per character instead.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">LLMs are trained by maximum likelihood: minimise the average −log p of each actual next token (cross-entropy), whose logit gradient is simply p − onehot.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Maximum likelihood chooses parameters that make the training text as probable as possible. Because that probability is a product over tokens, we take logs and average, giving the cross-entropy loss: the mean negative log-probability of each actual next token, measured in nats. It punishes confident mistakes heavily and is minimised exactly when the model matches the data distribution. With a softmax output its gradient is just the predicted probabilities minus one at the target. Perplexity, e to the loss, is the equivalent number of equally likely choices.</p></div>
    <div class="recap"><div><span><b>Problem:</b> one trainable number for "how good is the model".</span></div><div><span><b>Core idea:</b> L = mean −log p(actual); gradient p − onehot.</span></div><div><span><b>Read it:</b> perplexity = e^loss; uniform = ln V.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/math/04_cross_entropy_kl.ipynb" target="_blank" rel="noopener">04 · Entropy, cross-entropy, KL and perplexity</a> <span style="color:var(--faint)">· 25 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/math/04_cross_entropy_kl.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../07-information-theory/index.html">07 · Information theory for LLMs →</a> · Previous: <a href="../05-probability-sampling/index.html">← 05</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
