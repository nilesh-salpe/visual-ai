---
title: Data Mixtures and Repetition
body:
  data-deck: Data mixtures and repetition
  data-home: ../index.html
  data-home-label: Pretraining data
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'domain sizes :: unique tokens nᵢ :: f'
  - 'weights :: natural, temperature or learned :: a'
  - 'budget :: total training tokens :: c'
  - 'epochs :: wᵢ·budget / nᵢ :: d'
  - 'cap ~4 epochs :: re-distribute the rest :: e'
  caption: Late in training, small high-quality sets are often up-weighted ("annealing").
example:
  title: 'Worked example: a 15T-token budget'
  setup: 'Notebook 06: web 12T, code 800B, math 150B, books 60B, Wikipedia 20B, low-resource languages 5B unique tokens; budget 15T tokens.'
  steps:
  - 'Natural sampling (T = 1): web gets 92.1%; every domain is seen 1.2 times; low-resource languages get almost nothing.'
  - 'Temperature T = 3: web 50%, code 20%, math 11.6%; but math is repeated 11.6×, Wikipedia 44×, low-resource languages 112×.'
  - 'Capping at 4 epochs and giving the rest to web: web 72%, code 21%, math 4%; nothing exceeds 4 epochs.'
  - 'Reported mixes: Llama 3 ≈ 50% general, 25% math and reasoning, 17% code, 8% multilingual; DoReMi''s learned weights gave +6.5 points and 2.6× fewer steps on
    The Pile.'
  result: The mix is a trade-off between emphasis and repetition; caps keep small domains from being memorised.
traps:
  tricks:
  - 'Epochs = weight × budget ÷ unique tokens. :: Compute it per domain.'
  - '~4 epochs is nearly free. :: Beyond that, value decays quickly; ~40 epochs is about worthless.'
  - 'Proxy models for mixtures. :: DoReMi: 280M proxy chose weights for an 8B model.'
  traps:
  - 'Natural sampling. :: Starves code, math and languages.'
  - 'Unlimited up-weighting. :: Hundreds of epochs on a small set means memorisation.'
  - 'Tuning the mix on the final benchmarks only. :: Risks overfitting the evaluation; use held-out validation domains.'
papers:
- muennighoff
- doremi
- llama3
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Pretraining Data · 09</div>
    <h1>Data mixtures and repetition</h1>
    <p class="sub">How much of each source to train on: domain weights, temperature sampling for small domains and languages, learned mixtures (DoReMi), and how many times data can be repeated before it stops helping.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Cleaned web text dwarfs code, math, books and low-resource languages. Sampling by size starves the small domains; up-weighting them means repeating them many times.</div>
      <div class="c"><b>Core idea</b>Choose <b>sampling weights</b> per domain. <b>Temperature sampling</b> (pᵢ^(1/T)) up-weights small domains; learned methods (<b>DoReMi</b>) pick weights with a small proxy model. Track <b>epochs</b> per domain: Muennighoff et al. found up to about <b>4 epochs</b> of repetition is nearly as good as fresh data, with rapidly diminishing returns after.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Mix six domains

Domain sizes from notebook 06 and a 15T-token budget. Raise the temperature to up-weight small domains, and cap repetition at a chosen number of epochs.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">temperature T <input type="range" id="mT" min="1" max="10" step="0.5" value="3"> <output id="mTo"></output></label><label class="ctl">max epochs <input type="range" id="mC" min="1" max="50" step="1" value="4"> <output id="mCo"></output></label></div>
  <div id="mBars" style="margin-top:12px"></div>
  <p class="readout" id="mOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why the mix is hard

::: cards grid3
### [d] Imbalance
Web text is orders of magnitude larger than code, math or most languages.

### [b] Repetition
Up-weighting a small domain means repeating it; too much leads to memorisation and wasted compute.

### [c] Expensive to tune
Each candidate mix needs a training run to evaluate.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## How much repetition is fine?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? According to Muennighoff et al. (2023), how many epochs over the same data are nearly as good as fresh data?
- [ ] 1
- [x] up to about 4
- [ ] about 40
- [ ] unlimited
> <b>B.</b> Up to about 4 epochs gives negligible change in loss versus unique data; returns then diminish rapidly, and around 40 epochs repetition is almost worthless.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Three ways to set weights

::: cards grid3
### [f] Natural
wᵢ ∝ nᵢ: proportional to size. Simple, but small domains vanish.

### [a] Temperature
wᵢ ∝ (nᵢ/Σn)^(1/T): T > 1 flattens toward uniform; widely used for multilingual data.

### [e] Learned
DoReMi: a small proxy model trained with group DRO (distributionally robust optimization) outputs domain weights for the big run.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Mixes and schedules in practice

::: cards grid3
### [a] Llama 3 mix
About 50% general knowledge, 25% math and reasoning, 17% code, 8% multilingual tokens, chosen with small-model scaling experiments.

### [b] Annealing
At the end of pretraining, Llama 3 trained on small amounts of high-quality code and math with the learning rate decaying, which boosted key benchmarks.

### [c] DoReMi
280M proxy → 8B model (30× larger): +6.5 points few-shot accuracy, baseline reached with 2.6× fewer steps on The Pile.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why mixtures matter

::: cards grid2
### [a] Capabilities follow data
Code and math share drives coding and reasoning ability.

### [e] Repetition has a budget
A few epochs are nearly free; many are wasted compute.

### [b] Small models predict big ones
Mixtures found with proxies transfer to larger runs (DoReMi, Llama 3 experiments).

### [c] Timing matters
Up-weighting high-quality data late in training (annealing) helps more than early.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "The mix just reflects what data exists."
> It is a deliberate choice; natural proportions would be over 90% web.
:::

::: reveal myth
? "Repeating data is always bad."
> Up to about 4 epochs costs almost nothing compared with unique data.
:::

::: reveal myth
? "One mix fits all model sizes."
> Optimal weights depend on scale and goals; teams re-tune with scaling experiments.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? A 50B-token domain gets 2% of a 10T-token budget. Epochs?
- [ ] 0.2
- [ ] 2
- [x] 4
- [ ] 40
> 0.02 × 10T ÷ 50B = <b>4</b>.
:::

::: reveal
? What does a sampling temperature above 1 do?
> Flattens the domain distribution, giving small domains more weight than their size.
:::

::: reveal
? What does DoReMi use to choose domain weights?
> A small proxy model trained with group distributionally robust optimization; its weights are then used to train the large model.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">A data mix is a set of domain weights; temperature or learned weights up-weight small domains, and capping repetition near 4 epochs keeps that emphasis from turning into memorisation.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Pretraining data comes from domains of very different sizes, so sampling by size would make the mix almost all web text. Temperature sampling raises each domain's share to the power one over T, giving small domains more weight; learned methods such as DoReMi choose weights with a small proxy model. Up-weighting a small domain means repeating it: Muennighoff and colleagues found up to about four epochs is nearly as good as fresh data, with rapidly diminishing returns after. Llama 3's final mix was about half general text, a quarter math and reasoning, 17 percent code and 8 percent multilingual.</p></div>
    <div class="recap"><div><span><b>Problem:</b> huge imbalance between domains.</span></div><div><span><b>Core idea:</b> weights (temperature / learned) + epoch caps.</span></div><div><span><b>Numbers:</b> ~4 epochs ≈ free; Llama 3 50/25/17/8.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pretraining-data/06_data_mixture.ipynb" target="_blank" rel="noopener">06 · Data mixtures, sampling temperature and epochs</a> <span style="color:var(--faint)">· 25 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/pretraining-data/06_data_mixture.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../10-reference-pipelines/index.html">10 · Reference pipelines →</a> · Previous: <a href="../08-pii-and-safety/index.html">← 08</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
