---
title: Many Tokenizations
body:
  data-deck: One text, many tokenizations
  data-home: ../index.html
  data-home-label: Tokenization
styles:
- ../../shared/deck.css
- ../../shared/learn.css
- ../tk.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
- ../data/examples.js
- ../tk.js
glance:
  steps:
  - 'one word :: many valid splits :: f'
  - 'training :: sample a split each time :: a'
  - 'model :: sees varied segmentations :: c'
  - 'inference :: deterministic best split :: e'
  caption: Subword regularization (unigram sampling) and BPE-dropout (skip merges) are training-time only.
example:
  title: 'Worked example: BPE-dropout on one word'
  setup: 'Learned merges in order: e+s, es+t, l+o, lo+w, n+e, ne+w. Dropout probability p = 0.1 per merge application.'
  steps:
  - 'Normal BPE on "newest": n e w e s t → n e w es t → n e w est → ne w est → new est.'
  - With dropout, each merge is skipped with probability 0.1; skipping "ne+w" leaves ne · w · est.
  - 'Probability that all 4 merges apply: 0.9<sup>4</sup> = <b>0.656</b>; so about 34% of the time the model sees a different split.'
  - At inference, use normal BPE (p = 0).
  result: The model learns that "new + est" and "ne + w + est" mean the same, which helped translation by up to +3 BLEU in the paper.
traps:
  tricks:
  - 'Train with noise, test without. :: Both methods use deterministic segmentation at inference.'
  - 'Sampling temperature α. :: Unigram sampling sharpens or flattens the distribution over splits.'
  - 'Biggest wins out of domain. :: And on low-resource pairs.'
  traps:
  - 'Sampling at inference. :: It adds noise to outputs with no benefit.'
  - 'Uniform sampling. :: Kudo found α = 0 (uniform) hurt; LM-guided sampling helps.'
  - 'Assuming LLM pretraining uses it. :: The papers evaluated machine translation; most LLMs tokenize deterministically.'
papers:
- kudo
- bpedrop
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Tokenization for LLMs · 06</div>
    <h1>One text, many tokenizations</h1>
    <p class="sub">The same string can be written as many different token sequences. Subword regularization (Kudo, 2018) and BPE-dropout (BPE = byte-pair encoding) (Provilkov et al., 2020) turn that ambiguity into training noise that makes models more robust.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>With one vocabulary, a sentence can be split many ways, and the model treats each split as a completely different input. A deterministic tokenizer only ever shows it one.</div>
      <div class="c"><b>Core idea</b>During training, <b>sample</b> a different valid segmentation each time a sentence is used: from a unigram LM (language model), or by randomly dropping BPE merges.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Same text, same vocabulary, different ids

From Kudo (2018), Table 1: five ways to encode "Hello World" with the same vocabulary. To the model these are five unrelated id sequences.
{: .lede}

<div class="visual"><div id="helloRows"></div></div>

<div class="cite">Kudo 2018, Table 1 (▁ marks a space). The ids are the paper's.</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## A deterministic tokenizer hides this from the model

::: cards grid3
### [d] One view of each sentence
BPE and Viterbi always pick the same split, so the model never learns that different splits mean the same thing.

### [b] Brittle to noise
Typos, unusual spacing and other domains create splits the model rarely saw. Kudo argues that multiple candidates make a model "robust to noise and segmentation errors".

### [c] Compositionality left implicit
Seeing "books" sometimes as "book" + "s" helps a model learn how words are built (§1).
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Make the model robust to segmentation

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? How could training make a model robust to different segmentations of the same text?
- [ ] Use several tokenizers at inference and vote
- [x] Sample a different valid segmentation every time a sentence is used in training
- [ ] Use a bigger vocabulary
- [ ] Lowercase everything
> <b>B.</b> This is data augmentation for text: the content stays the same and only the segmentation changes. Kudo samples from a unigram LM; BPE-dropout randomly skips merges. Inference still uses one deterministic segmentation.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Two ways to sample segmentations

<div class="grid2">
  <div class="card e"><h3>Subword regularization (Kudo, 2018)</h3><p>Uses the unigram LM, which can score every segmentation. For each parameter update, sample one segmentation from P(x|X), smoothed by α over the l-best candidates (or all of them, with FFBS (forward-filtering backward-sampling)).</p></div>
  <div class="card a"><h3>BPE-dropout (Provilkov et al., 2020)</h3><p>Keeps ordinary BPE but, while segmenting training data, randomly <b>drops</b> some merges, so the same word comes out in different splits. Standard BPE is used at inference.</p></div>
</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Subword regularization: sample from the unigram LM <span class="ill">toy probabilities</span>

<p class="lede">P(x<sub>i</sub>|X) ≅ P(x<sub>i</sub>)<sup>α</sup> / Σ<sub>j</sub> P(x<sub>j</sub>)<sup>α</sup> over the l best segmentations. A small α spreads probability over many splits; a large α concentrates it on the Viterbi split.</p>

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">α <input type="range" id="srA" min="0" max="1" step="0.05" value="0.2"> <output id="srAo"></output></label>
    <label class="ctl">l (candidates) <input type="range" id="srL" min="1" max="12" step="1" value="8"> <output id="srLo"></output></label>
    <button class="btn primary" id="srS">Sample 6 epochs</button>
  </div>
  <div class="grid2" style="margin-top:12px">
    <div><h3>P(segmentation | "tokenizers")</h3><div id="srBars"></div></div>
    <div><h3>What the model sees, epoch by epoch</h3><div id="srSamples"></div></div>
  </div>
</div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## BPE-dropout: randomly skip merges <span class="ill">toy merges</span>

The merges are learned from a toy corpus (low ×5, lower ×2, newest ×6, widest ×3, lowest ×3). With dropout p, each merge application is skipped with probability p. p = 0 is ordinary BPE, and a larger p gives finer, more varied splits.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">dropout p <input type="range" id="bdP" min="0" max="0.6" step="0.05" value="0.1"> <output id="bdPo"></output></label>
    <button class="btn primary" id="bdS">Resample</button>
  </div>
  <div id="bdOut" style="margin-top:12px"></div>
</div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works, and the measured gains

::: cards grid2
### [e] Data augmentation
Each sentence is seen under many segmentations, much like random crops and flips for images, which the paper uses as its own analogy.

### [a] Reversible, so usable on both sides
Segmentation can be undone exactly, so it can be applied to source <em>and</em> target. Table 6 shows both sides together beat either side alone.

### [b] Realistic noise
Sampling guided by the LM beats uniform sampling: α = 0 (uniform) hurt BLEU (Kudo §5.5).

### [c] Results (machine translation)
Subword regularization: about +1 to 2 BLEU on most pairs, and +2 or more out of domain (Kudo). BPE-dropout: up to <b>+3 BLEU</b> over BPE and up to <b>+0.9</b> over subword regularization (Provilkov et al.).
:::

<div class="paper"><b>Scope note:</b> both papers evaluate machine translation. The LLM (large language model) tokenizers covered in this guide (GPT-2/tiktoken, Llama 2, Llama 3) are documented as deterministic BPE, and their papers don't describe stochastic segmentation during pretraining.</div>

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Sampling happens at inference too."
> It is a <b>training-time</b> regularizer. Kudo decodes from the best (or n-best) segmentation, and BPE-dropout uses standard BPE at inference.
:::

::: reveal myth
? "BPE can only ever produce one segmentation."
> Standard BPE is deterministic, but <b>BPE-dropout</b> makes it stochastic by randomly skipping merges during training.
:::

::: reveal myth
? "Fully random segmentation is the best noise."
> Kudo found α = 0 (uniform sampling, ignoring the LM) <b>hurt</b> performance. Noise that resembles real segmentation variation works better.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

<div class="quiz">
  <p class="qq">Which method needs a unigram language model?</p>
  <div class="opts">
  <button>A. BPE-dropout</button>
  <button data-ok>B. Subword regularization (Kudo)</button>
  <button>C. Byte-level BPE</button>
  <button>D. WordPiece</button>
  </div>
  <div class="why"><b>Subword regularization</b> samples from P(x|X), which the unigram LM provides. BPE-dropout works with ordinary BPE.</div>
</div>

::: quiz
? What does a larger α do in Kudo's sampling?
- [ ] Makes sampling more uniform
- [x] Concentrates samples on the Viterbi (best) segmentation
- [ ] Increases vocabulary size
- [ ] Disables sampling
> A larger α moves toward the <b>Viterbi</b> segmentation; a smaller α moves toward uniform.
:::

<div class="quiz ">
  <p class="qq">Why does it matter that segmentation is reversible?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Because the original text can always be recovered, the noise can be applied to the <b>target</b> side as well as the input, which Kudo shows helps (Table 6).</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">A sentence has many valid tokenizations. Sampling them during training, via subword regularization or BPE-dropout, acts as data augmentation and makes models more robust.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>With a fixed vocabulary, the same text can be split many ways, and each split is a different id sequence to the model. Kudo's subword regularization samples a segmentation from a unigram LM, smoothed by α, every time a sentence is used in training. BPE-dropout does the same with ordinary BPE by randomly skipping merges. Both are training-time only and use deterministic segmentation at inference. They gave +1 to 3 BLEU in machine translation, with larger gains out of domain.</p></div>

<div class="recap"><div><span><b>Problem:</b> deterministic tokenization shows one split of each sentence, which makes models brittle to segmentation variation.</span></div><div><span><b>Core idea:</b> sample segmentations during training (unigram LM with α, or BPE with dropped merges).</span></div></div>

<p class="start-hint">Next: <a href="../07-vocabulary-size/index.html">07 · Vocabulary size trade-offs →</a> · Previous: <a href="../05-sentencepiece/index.html">← 05</a> · <a href="../index.html">All decks</a> · <a href="../playground/index.html">Playground</a></p>

<!-- slide id="s-papers" from="papers" -->
