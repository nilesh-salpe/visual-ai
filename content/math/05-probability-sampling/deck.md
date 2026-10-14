---
title: Probability and Sampling
body:
  data-deck: Probability and sampling
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
  - 'context :: x₁ … xₜ₋₁ :: f'
  - 'logits :: one score per token :: c'
  - '÷ temperature :: sharpen / flatten :: b'
  - 'softmax + truncate :: top-k / top-p :: a'
  - 'sample :: next token :: e'
  loop: '4 -> 0 :: append and repeat'
  caption: The same model produces very different text depending on the decoding rule.
example:
  title: 'Worked example: temperature and top-p on four logits'
  setup: Logits (2.0, 1.0, 0.5, −1.0) for tokens A, B, C, D.
  steps:
  - 'T = 1: softmax = (0.609, 0.224, 0.136, 0.030).'
  - 'T = 0.5 (logits doubled): (0.842, 0.114, 0.042, 0.002): almost always A.'
  - 'T = 2 (logits halved): (0.434, 0.263, 0.205, 0.097): much flatter.'
  - 'Top-p with p = 0.9 at T = 1: cumulative A, B, C = 0.970 ≥ 0.9, so D is dropped and A, B, C are renormalised.'
  result: Temperature changes the shape of the whole distribution; top-k and top-p remove the tail, then renormalise.
traps:
  tricks:
  - 'Temperature divides logits. :: T → 0 is greedy; T = 1 is the model''s distribution.'
  - 'Top-p adapts the cut. :: Few tokens when the model is confident, many when it is not.'
  - 'Log-probabilities add. :: Sequence log-prob = Σ log p(xₜ | x₍&lt;t₎).'
  traps:
  - 'Greedy decoding for open-ended text. :: Maximising likelihood gives bland, repetitive output (Holtzman et al.).'
  - 'Multiplying many probabilities. :: Underflows; sum logs instead.'
  - 'Thinking T changes the model. :: It only changes decoding; training is unaffected.'
papers:
- bengio03
- holtzman
- gpt2
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Math for LLMs · 05</div>
    <h1>Probability and sampling</h1>
    <p class="sub">A language model is a conditional probability distribution over the next token. How logits become probabilities, and how temperature, top-k and top-p shape what gets generated.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>The model outputs one score (logit) per vocabulary entry. Generating text requires turning those scores into a distribution and choosing a token, and the choice changes the text dramatically.</div>
      <div class="c"><b>Core idea</b>A language model factorises text with the <b>chain rule of probability</b>: p(x₁…xₙ) = Π p(xₜ | x₍&lt;t₎). Softmax turns logits into p(next | context). <b>Temperature</b> sharpens or flattens it; <b>top-k</b> and <b>top-p (nucleus)</b> sampling cut the unreliable tail.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## From logits to a choice

Five candidate next tokens with fixed logits. Move temperature, top-k and top-p: the bars show the final sampling distribution, and the readout its entropy.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">temperature <input type="range" id="pT" min="0.1" max="3" step="0.1" value="1"> <output id="pTo"></output></label>
    <label class="ctl">top-k <input type="range" id="pK" min="1" max="5" step="1" value="5"> <output id="pKo"></output></label>
    <label class="ctl">top-p <input type="range" id="pP" min="0.1" max="1" step="0.05" value="1"> <output id="pPo"></output></label>
  </div>
  <div id="pBars" style="margin-top:12px"></div>
  <p class="readout" id="pOut"></p>
</div>
<p class="caption">Context: "The cat sat on the …". Logits are illustrative.</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why not always pick the most likely token?

::: cards grid3
### [d] Degeneration
Holtzman et al. found that maximising likelihood when decoding produces bland and strangely repetitive text.

### [b] Human text is not maximal
People routinely choose tokens the model ranks below the top one.

### [c] The tail is unreliable
Pure sampling occasionally picks one of thousands of very unlikely tokens and derails the text.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What does T → 0 do?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? As the sampling temperature approaches 0, what happens?
- [ ] Sampling becomes uniform
- [x] It becomes greedy decoding (always the top token)
- [ ] The model forgets the context
- [ ] Nothing changes
> <b>B.</b> Dividing logits by a tiny T makes the largest logit dominate the softmax completely. Large T flattens toward uniform.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## A distribution over the next token

::: cards grid2
### [a] Chain rule of probability
p(x₁…xₙ) = Π p(xₜ | x₁…xₜ₋₁): a language model only needs next-token conditionals.

### [c] Softmax
p(i) = exp(zᵢ) / Σⱼ exp(zⱼ): positive, sums to 1, preserves the ranking of logits.

### [b] Temperature
Use zᵢ / T. T < 1 sharpens, T > 1 flattens.

### [e] Truncation
Top-k keeps the k best tokens; top-p keeps the smallest set whose probability reaches p. Then renormalise.
:::

<div class="eq">p(xₜ = i | x₍&lt;t₎) = exp(zᵢ / T) / Σⱼ exp(zⱼ / T)</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Probability rules you use constantly

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Rule</th><th>Formula</th><th>Where it shows up</th></tr>
  <tr><td>Conditional probability</td><td>p(a | b) = p(a, b) / p(b)</td><td>next-token prediction</td></tr>
  <tr><td>Chain rule</td><td>p(a, b) = p(a) p(b | a)</td><td>scoring a whole sequence</td></tr>
  <tr><td>Bayes</td><td>p(a | b) = p(b | a) p(a) / p(b)</td><td>reward models, classifiers</td></tr>
  <tr><td>Expectation</td><td>E[f] = Σ p(x) f(x)</td><td>losses, RL objectives</td></tr>
  <tr><td>Logs turn products into sums</td><td>log Π p = Σ log p</td><td>log-likelihood, numerical stability</td></tr>
</table></div>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why this framing works

::: cards grid2
### [a] Any text, one rule
Because of the chain rule, predicting the next token well is enough to model whole documents.

### [e] Trainable
Softmax probabilities are differentiable, so maximum likelihood can train them (next deck).

### [b] Controllable
Decoding knobs trade diversity against reliability without retraining.

### [c] Composable
Log-probabilities let you score, compare and rerank candidate outputs.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Temperature 0 and top-k = 1 are different."
> Both pick the single most likely token (greedy decoding), up to tie-breaking.
:::

::: reveal myth
? "Higher temperature makes the model smarter or more creative."
> It only flattens the distribution: more diverse, but more likely to choose poor tokens.
:::

::: reveal myth
? "Top-p keeps a fixed number of tokens."
> The number varies with the model's confidence: one token when the top probability exceeds p, many when the distribution is flat.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Probabilities 0.5, 0.3, 0.15, 0.05. Which tokens does top-p = 0.8 keep?
- [ ] only the first
- [x] the first two
- [ ] the first three
- [ ] all four
> 0.5 + 0.3 = 0.8 reaches p: <b>the first two</b>.
:::

::: reveal
? How do you compute the probability of a whole sentence under a language model?
> Multiply the next-token probabilities, or better, sum their logs: log p = Σₜ log p(xₜ | x₍&lt;t₎).
:::

::: reveal
? What problem does nucleus sampling solve?
> It avoids both degenerate greedy text and derailment by sampling from an unreliable tail, by keeping only the high-probability nucleus.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">An LLM is a next-token distribution p(xₜ | x₍&lt;t₎) from a softmax over logits; temperature reshapes it and top-k/top-p cut the tail before sampling.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Thanks to the chain rule of probability, a model of whole texts only needs next-token conditionals. The network outputs a logit per vocabulary entry and a softmax turns them into probabilities. Decoding then chooses a token: dividing logits by a temperature below one sharpens the distribution and above one flattens it; top-k keeps the k most likely tokens and top-p keeps the smallest set reaching probability p, then renormalises. Greedy decoding tends to produce bland, repetitive text, which is why sampling with truncation is common.</p></div>
    <div class="recap"><div><span><b>Problem:</b> turn logits into a choice of token.</span></div><div><span><b>Core idea:</b> softmax(z / T), then truncate and sample.</span></div><div><span><b>Rules:</b> chain rule; logs turn products into sums.</span></div></div>
    <p class="start-hint">Next: <a href="../06-maximum-likelihood/index.html">06 · Maximum likelihood and cross-entropy →</a> · Previous: <a href="../04-derivatives-chain-rule/index.html">← 04</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
