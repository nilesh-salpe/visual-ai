---
title: Information Theory for LLMs
body:
  data-deck: Information theory for LLMs
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
  - 'H(p) :: irreducible surprise :: f'
  - '+ KL(p‖q) :: penalty for using q :: d'
  - '= H(p, q) :: the training loss :: a'
  caption: Training lowers KL(p‖q); H(p) is fixed by the data.
example:
  title: 'Worked example: three outcomes'
  setup: Data distribution p = (0.7, 0.2, 0.1); model q = (0.5, 0.3, 0.2).
  steps:
  - H(p) = −Σ p log p ≈ <b>0.802 nats</b> (1.157 bits).
  - H(p, q) = −Σ p log q ≈ <b>0.887 nats</b>.
  - KL(p‖q) = H(p, q) − H(p) ≈ <b>0.085 nats</b>.
  - 'KL(q‖p) ≈ 0.092 nats: different, because KL is not symmetric.'
  result: The model pays 0.085 extra nats per outcome for being wrong; that excess is all that training can remove.
traps:
  tricks:
  - 'H(p, q) = H(p) + KL(p‖q). :: Minimising cross-entropy minimises KL.'
  - 'Forward KL is mass-covering. :: KL(p‖q) spreads q over all of p; reverse KL(q‖p) is mode-seeking.'
  - 'Bits per byte = loss_nats × tokens / (bytes × ln 2). :: Tokenizer-independent.'
  traps:
  - 'Treating KL as a distance. :: It is asymmetric and violates the triangle inequality.'
  - 'q = 0 where p > 0. :: KL becomes infinite; models must never assign exactly zero.'
  - 'Mixing nats and bits. :: 1 nat = 1/ln 2 ≈ 1.443 bits.'
papers:
- shannon
- kl51
- distill
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Math for LLMs · 07</div>
    <h1>Information theory for LLMs</h1>
    <p class="sub">Entropy, cross-entropy and KL divergence: the quantities behind the training loss, distillation, RLHF's KL penalty and bits-per-byte comparisons.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>LLM work constantly asks "how different are these two distributions?": model vs data, student vs teacher, fine-tuned policy vs reference. We need a principled measure.</div>
      <div class="c"><b>Core idea</b><b>Entropy</b> H(p) is average surprise. <b>Cross-entropy</b> H(p, q) is the surprise when you code p's outcomes with model q. Their gap is the <b>KL divergence</b> KL(p‖q) = H(p, q) − H(p) ≥ 0: zero only when q = p, and not symmetric.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## How far apart are two distributions?

Two distributions over three outcomes. Adjust the model q; the readout shows entropy, cross-entropy and KL in both directions.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">q(A) <input type="range" id="kA" min="0.02" max="0.96" step="0.01" value="0.5"> <output id="kAo"></output></label>
    <label class="ctl">q(B) share of rest <input type="range" id="kB" min="0.02" max="0.98" step="0.01" value="0.6"> <output id="kBo"></output></label>
  </div>
  <div id="kBars" style="margin-top:12px"></div>
  <p class="readout" id="kOut"></p>
</div>
<p class="caption">Data distribution p = (0.7, 0.2, 0.1) is fixed.</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why not simpler distances?

::: cards grid3
### [d] Difference of probabilities
Treats 0.01 vs 0.001 like 0.51 vs 0.501, though the first is a 10× difference in surprise.

### [b] Only the top outcome
Ignores how the rest of the probability is spread, which matters for sampling and distillation.

### [c] Needs to match training
We want the measure that maximum likelihood already minimises, so the numbers line up with the loss.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Which is larger?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? For any distributions p and q, how does cross-entropy H(p, q) compare with entropy H(p)?
- [ ] Always smaller
- [x] Always ≥ H(p)
- [ ] Always equal
- [ ] It depends on the vocabulary size
> <b>B.</b> H(p, q) = H(p) + KL(p‖q) and KL ≥ 0 (Gibbs' inequality), with equality only when q = p.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Entropy, cross-entropy, KL

::: cards grid3
### [f] Entropy H(p)
−Σ p log p. Average surprise of the data itself: the floor no model can beat.

### [a] Cross-entropy H(p, q)
−Σ p log q. Average surprise when predicting p's outcomes with q: the LM training loss.

### [d] KL(p‖q)
Σ p log(p/q) = H(p, q) − H(p). The excess caused by q ≠ p.
:::

<div class="eq">H(p, q) = H(p) + KL(p ‖ q),   KL ≥ 0</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Where KL appears in LLM work

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Use</th><th>Which KL</th><th>Effect</th></tr>
  <tr><td>Pretraining / SFT (supervised fine-tuning)</td><td>KL(data ‖ model), via cross-entropy</td><td>model covers everything the data does</td></tr>
  <tr><td>Distillation</td><td>cross-entropy to the teacher's soft targets (temperature T)</td><td>student copies the teacher's full distribution</td></tr>
  <tr><td>RLHF (reinforcement learning from human feedback)</td><td>KL(policy ‖ reference) penalty</td><td>stops the policy drifting too far from the SFT model</td></tr>
  <tr><td>DPO (direct preference optimization)</td><td>implicit KL constraint in its derivation</td><td>same role without explicit RL</td></tr>
</table></div>

::: deep Forward vs reverse KL
Minimising KL(p‖q) (maximum likelihood) forces q to put mass wherever p has mass: mass-covering. Minimising KL(q‖p) lets q ignore parts of p but punishes mass where p has none: mode-seeking. Notebook 04 fits one bump to a two-peaked p both ways.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why these are the right quantities

::: cards grid2
### [a] Compression
Shannon: entropy is the minimum average code length; cross-entropy is the length when coding with q. A better LM is a better compressor.

### [e] Consistency
The training loss, the evaluation metric (perplexity) and regularisers (KL penalties) share one currency.

### [b] Directional on purpose
The asymmetry of KL lets you choose coverage or mode-seeking behaviour.

### [c] Units
Nats with ln, bits with log₂; bits per byte removes tokenizer effects.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "KL divergence is a distance."
> It is not symmetric and does not satisfy the triangle inequality, so it is a divergence, not a metric.
:::

::: reveal myth
? "Cross-entropy loss can go below the entropy of the data."
> Not on the true distribution: H(p, q) ≥ H(p). A training loss below it signals overfitting or leaked test data.
:::

::: reveal myth
? "Entropy measures how good a model is."
> Entropy of the model's own output measures its uncertainty; quality is cross-entropy against real data.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Entropy of a uniform distribution over 8 outcomes?
- [ ] 1 bit
- [x] 3 bits
- [ ] 8 bits
- [ ] 0.125 bits
> log₂ 8 = <b>3 bits</b>.
:::

::: reveal
? Why does minimising cross-entropy also minimise KL(p‖q)?
> H(p, q) = H(p) + KL(p‖q) and H(p) does not depend on the model.
:::

::: reveal
? What does the KL penalty in RLHF prevent?
> The policy drifting far from the reference model, for example to exploit reward-model errors or lose fluency.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Entropy is average surprise, cross-entropy is surprise under a model, and KL = H(p, q) − H(p) ≥ 0 is the asymmetric gap that training, distillation and RLHF penalties control.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Entropy measures the average surprise of a distribution; for data it is the floor no model can beat. Cross-entropy measures the surprise when you predict that data with a model, and it is exactly the language-model training loss. The difference is the KL divergence, which is never negative and is zero only when the model matches the data. So minimising the loss minimises KL from data to model, which is mass-covering. KL is not symmetric: the reverse direction is mode-seeking. The same quantities appear as distillation targets and as the KL penalty that keeps an RLHF policy near its reference.</p></div>
    <div class="recap"><div><span><b>Problem:</b> measure the gap between distributions.</span></div><div><span><b>Core idea:</b> H(p, q) = H(p) + KL(p‖q), KL ≥ 0, asymmetric.</span></div><div><span><b>Uses:</b> loss, distillation, RLHF KL penalty.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/math/04_cross_entropy_kl.ipynb" target="_blank" rel="noopener">04 · Entropy, cross-entropy, KL and perplexity</a> <span style="color:var(--faint)">· 25 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/math/04_cross_entropy_kl.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../08-softmax-logsumexp/index.html">08 · Softmax and log-sum-exp →</a> · Previous: <a href="../06-maximum-likelihood/index.html">← 06</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
