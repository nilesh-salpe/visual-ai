---
title: Regularization and Generalization
body:
  data-deck: Regularization and generalization
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
  - 'more capacity :: lower train error :: a'
  - 'fits noise :: test error rises :: d'
  - 'regularise :: decay, dropout, data :: e'
  - 'generalise :: small gap :: c'
  caption: LLMs mostly sidestep overfitting by seeing each token about once; fine-tuning on small data is where it bites.
example:
  title: 'Worked example: polynomials on 15 noisy points'
  setup: 'Notebook 06: y = sin(3x) + noise, 15 training points, 500 test points; least-squares polynomials of growing degree.'
  steps:
  - 'Degree 3: test MSE <b>0.073</b>, close to the noise level.'
  - 'Degree 14 passes exactly through all 15 points (train error ≈ 0), but its test MSE is <b>12,756,989</b>: it wiggles wildly between the points.'
  - 'Adding a tiny ridge penalty λ = 10⁻³ (weight decay for linear models) to degree 14: test MSE <b>0.102</b>.'
  - 'Zhang et al. showed standard image networks can fit completely random labels, so for deep nets the story is more subtle: implicit regularisation from SGD, architecture
    and data matter.'
  result: Capacity without constraints memorises noise; a small penalty on weight size restores generalisation.
traps:
  tricks:
  - 'Watch the gap. :: Validation loss rising while training loss falls = overfitting.'
  - 'Dropout scales by 1/(1 − p) in training. :: Nothing changes at inference.'
  - 'More data is the best regulariser. :: LLM pretraining rarely repeats data.'
  traps:
  - 'Tuning on the test set. :: Keep a separate validation split; the test set is for the final number.'
  - 'Dropout at inference. :: Must be turned off (eval mode).'
  - 'Assuming bigger always overfits more. :: Double descent: past the interpolation threshold, larger models can generalise better.'
papers:
- dropout
- zhang17
- belkin
- nakkiran
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Neural Networks · 08</div>
    <h1>Regularization and generalization</h1>
    <p class="sub">Why a model can fit its training data perfectly and still fail on new data, the classic tools that prevent it (weight decay, dropout, early stopping), and the surprises of modern over-parameterised networks.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Training minimises loss on the data you have, but what matters is loss on data you have not seen. Flexible models can memorise noise instead of learning the pattern.</div>
      <div class="c"><b>Core idea</b><b>Generalization gap</b> = test loss − train loss. <b>Weight decay</b> penalises large weights, <b>dropout</b> randomly removes units during training, <b>early stopping</b> stops before memorisation. Large networks can fit even random labels, and test error can fall again past the interpolation point (<b>double descent</b>), so capacity alone does not predict overfitting.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## When does a better fit become worse?

Fit polynomials of increasing degree to 15 noisy points. Toggle a small ridge penalty (weight decay). Fits are precomputed with exact least squares, the same data as notebook 06.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">degree <input type="range" id="gD" min="0" max="14" step="1" value="3"> <output id="gDo"></output></label><div class="seg" id="gSeg"><button data-v="plain" class="on">no penalty</button><button data-v="ridge">ridge λ = 10⁻³</button></div></div>
  <svg id="gSvg" viewBox="0 0 660 250" style="margin-top:10px" role="img" aria-label="Polynomial fit"></svg>
  <p class="readout" id="gOut"></p>
</div>
<p class="caption">Dashed: the true function sin(3x). Dots: training points.</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why training loss can mislead

::: cards grid3
### [d] Noise is learnable
A flexible model can fit the noise in each example, which does not repeat in new data.

### [b] Finite data
Fine-tuning sets are often thousands of examples for billions of parameters.

### [c] Leaky evaluation
Tuning against the test set overfits the benchmark itself (Evals deck 05).
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Which model generalises?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Model A: train loss 0.05, validation 0.90. Model B: train 0.30, validation 0.35. Which is overfitting?
- [x] A
- [ ] B
- [ ] both
- [ ] neither
> <b>A.</b> Its generalisation gap (0.85) is huge: it memorised the training set. B fits less well but its gap is small.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Tools that limit memorisation

::: cards grid2
### [a] Weight decay
Shrink weights every step (L2 / AdamW decay): smooth functions are preferred.

### [c] Dropout
Zero each unit with probability p in training and scale survivors by 1/(1 − p); averages many thinned networks (Srivastava et al., 2014).

### [e] Early stopping
Keep the checkpoint with the best validation loss.

### [b] More (and cleaner) data
The most reliable fix; LLM pretraining relies on it by rarely repeating tokens.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## The modern picture

::: cards grid3
### [d] Random labels
Zhang et al. (2017): standard networks fit completely random labels, so they have enough capacity to memorise; yet on real labels they generalise.

### [a] Double descent
Belkin et al. (2019): test error rises toward the point where the model just interpolates the data, then falls again as it grows larger.

### [e] In deep networks
Nakkiran et al. (2020): double descent appears with model size and with training time; near the threshold, more data can even hurt.
:::

::: deep Where LLMs sit
Pretraining usually sees each token about once, so train and validation loss track each other closely. Overfitting shows up in fine-tuning on small datasets, in many-epoch training, and in benchmark contamination.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why regularisation works

::: cards grid2
### [a] Prefers simple functions
Small weights mean small slopes and gentle curves between data points.

### [e] Robust features
Dropout stops units relying on specific partners, so features work in many combinations.

### [b] Implicit regularisation
SGD noise and architecture choices bias training toward solutions that generalise.

### [c] Data beats tricks
With enough fresh data, memorisation is impossible and the gap closes.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Overfitting means the model is too big."
> Double descent shows bigger can generalise better; it depends on data size, noise and regularisation.
:::

::: reveal myth
? "Dropout is used in all modern LLMs."
> Many large pretraining runs use little or no dropout because data is not repeated; it is more common in fine-tuning.
:::

::: reveal myth
? "Zero training loss is the goal."
> It is evidence of memorisation unless validation loss is also low.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Dropout p = 0.2 in training. By what factor are surviving activations scaled?
- [ ] 0.8
- [x] 1.25
- [ ] 5
- [ ] 1
> 1/(1 − 0.2) = <b>1.25</b>.
:::

::: reveal
? What is the generalisation gap?
> Test (or validation) loss minus training loss.
:::

::: reveal
? Why does LLM pretraining overfit less than fine-tuning?
> Pretraining typically sees each token about once from a huge corpus; fine-tuning repeats small datasets for several epochs.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Generalisation is about unseen data: penalise weight size, drop units, stop early and above all use more data; over-parameterised nets complicate the classic story with double descent.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>A model is trained on one dataset but judged on new data, and the difference between the two losses is the generalisation gap. Flexible models can memorise noise: a degree-fourteen polynomial through fifteen noisy points has zero training error and a huge test error. Weight decay penalises large weights, dropout randomly removes units during training and rescales the rest, and early stopping keeps the best validation checkpoint; more data is the strongest fix. Deep networks complicate this: they can fit random labels, and test error can fall again beyond the interpolation threshold, which is called double descent.</p></div>
    <div class="recap"><div><span><b>Problem:</b> low train loss ≠ low test loss.</span></div><div><span><b>Core idea:</b> weight decay, dropout, early stopping, data.</span></div><div><span><b>Modern view:</b> random-label fitting; double descent.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/nn-fundamentals/06_overfitting_dropout.ipynb" target="_blank" rel="noopener">06 · Overfitting, dropout and weight decay</a> <span style="color:var(--faint)">· 30 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/nn-fundamentals/06_overfitting_dropout.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../09-embeddings/index.html">09 · Embeddings →</a> · Previous: <a href="../07-normalization-residuals/index.html">← 07</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
