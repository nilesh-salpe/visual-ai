---
title: WordPiece and Unigram
body:
  data-deck: WordPiece and unigram LM
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
  - 'big seed vocabulary :: many candidate pieces :: f'
  - 'EM :: estimate piece probabilities :: c'
  - 'prune :: drop pieces that hurt likelihood least :: b'
  - 'Viterbi :: best segmentation per word :: a'
  loop: '2 -> 1 :: until target size'
  caption: Unigram LM goes top-down (prune); BPE and WordPiece go bottom-up (merge).
example:
  title: 'Worked example: scoring segmentations with a unigram LM'
  setup: 'Toy piece probabilities: un 0.10, believ 0.02, able 0.08, unbeliev 0.001, u 0.03, n 0.03, b 0.02.'
  steps:
  - Unigram LM probability of a segmentation = product of piece probabilities.
  - 'un · believ · able: 0.10 × 0.02 × 0.08 = <b>0.00016</b>.'
  - 'unbeliev · able: 0.001 × 0.08 = <b>0.00008</b>.'
  - 'u · n · believ · able: 0.03 × 0.03 × 0.02 × 0.08 = <b>0.0000014</b>. Viterbi picks the first.'
  result: The unigram model keeps a probability for every segmentation, which also lets you sample alternatives (deck 06).
traps:
  tricks:
  - 'Unigram: prune down; BPE: merge up. :: Different directions, similar final sizes.'
  - 'Viterbi finds the best split. :: Dynamic programming over positions.'
  - 'WordPiece marks continuations. :: BERT''s "##" prefix means "joins the previous piece".'
  traps:
  - 'Calling WordPiece = BPE. :: WordPiece picks merges by likelihood gain, not raw frequency.'
  - 'Assuming one valid split. :: Many segmentations exist with the same vocabulary.'
  - 'Forgetting probabilities are learned. :: EM re-estimates them as pieces are pruned.'
papers:
- kudo
- gnmt
- bert
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Tokenization for LLMs · 04</div>
    <h1>WordPiece and the unigram language model</h1>
    <p class="sub">Tokenizers that choose subwords by likelihood instead of raw frequency. The unigram LM (Kudo, 2018) also gives every segmentation a probability.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>BPE (byte-pair encoding) merges greedily by frequency and gives exactly one segmentation, with no score for how good it is.</div>
      <div class="c"><b>Core idea</b>Use a probabilistic model of subwords. WordPiece picks merges by likelihood; the unigram LM starts large, prunes by likelihood, and segments with Viterbi.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## What makes one segmentation better than another?

<p class="lede">"tokenizers" could be token|izers, token|izer|s, tok|en|izers, or t|o|k|e|n|i|z|e|r|s. BPE always returns the same one because it replays fixed merges. It never <em>scores</em> the options.</p>

<div class="visual"><div id="p1Opts"></div></div>

<p class="caption">Candidate segmentations are <span class="ill">illustrative</span>.</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## BPE's limits, as Kudo describes them

::: cards grid3
### [d] Greedy
BPE is "based on a greedy and deterministic symbol replacement". Early merges are fixed and never reconsidered.

### [b] No probabilities
It "can not provide multiple segmentations with probabilities" (Kudo 2018, §3.1).

### [c] Frequency, not fit
Merges are chosen by raw pair counts, not by how well the resulting vocabulary explains the data.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Choose the vocabulary differently

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Instead of merging the most frequent pair, how else could you choose which subwords go into the vocabulary?
- [ ] At random
- [x] Choose subwords that maximize the likelihood of the training text under a language model
- [ ] Alphabetically
- [ ] Keep the longest substrings
> <b>B.</b> This is the idea behind both <b>WordPiece</b> (BPE-like merges, but each merge chosen by likelihood) and the <b>unigram LM</b> (start large and remove the subwords whose loss hurts likelihood least).
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Two likelihood-based tokenizers

::: cards grid2
### [a] WordPiece
Builds the vocabulary incrementally like BPE, but "uses a likelihood instead of frequency" to choose merges (Kudo 2018, footnotes 1–2; Schuster &amp; Nakajima, 2012). BERT (Bidirectional Encoder Representations from Transformers) uses "WordPiece embeddings with a 30,000 token vocabulary".

### [e] Unigram language model
Each subword has a probability p(x), and a segmentation's probability is the product: <b>P(x) = Π p(x<sub>i</sub>)</b>. The best segmentation is found by Viterbi. The vocabulary is learned by starting big and pruning (Kudo, 2018).
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Unigram LM: score every segmentation, pick the best <span class="ill">toy probabilities</span>

With P(x) = Π p(x<sub>i</sub>), each way of splitting "tokenizers" gets a probability. Viterbi finds the most probable one in linear time. Drag the probability of the piece "token" and watch the winner change.
{: .lede}

<div class="visual">
  <label class="ctl">p("token") <input type="range" id="ugP" min="-5" max="-1" step="0.1" value="-1.4"> <output id="ugPo"></output></label>
  <div id="ugBars" style="margin-top:12px"></div>
  <p class="readout" id="ugBest" style="margin-top:8px"></p>
</div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Learning the unigram vocabulary: EM, then prune

The vocabulary itself is unknown, so the unigram method (Kudo §3.2) starts from a large seed vocabulary and repeatedly removes the least useful pieces. Step through the rounds <span class="ill">toy loss values</span>.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><button class="btn primary" id="prStep">Next pruning round →</button><button class="btn" id="prReset">Reset</button><span class="readout" id="prOut"></span></div>
  <div id="prChips" style="margin-top:12px"></div>
</div>

<div class="grid3" style="margin-top:12px">
  <div class="card a"><h3>(a) EM</h3><p>Fix the vocabulary and estimate p(x) with expectation-maximization.</p></div>
  <div class="card b"><h3>(b) Loss</h3><p>For each subword, compute how much the likelihood drops if it is removed.</p></div>
  <div class="card e"><h3>(c) Keep top η%</h3><p>Keep the top η = 80% by loss. Single characters are always kept, so nothing becomes unknown.</p></div>
</div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why likelihood-based tokenizers help

::: cards grid2
### [e] Principled segmentation
Viterbi returns the single most probable split under the model, not just the result of replaying merges.

### [a] Probabilities for alternatives
The unigram LM can output several segmentations with probabilities, which deck 06 uses to sample them during training.

### [b] An entropy-coding view
Kudo frames the unigram model as an entropy encoder: the optimal code length for a symbol s is −log p<sub>s</sub>, so likely pieces get short codes (§3.4).

### [c] No unknowns
All characters stay in the vocabulary, so character-level segmentation is always one of the candidates.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "WordPiece and the unigram LM are the same algorithm."
> WordPiece <b>grows</b> a vocabulary by likelihood-chosen merges, BPE-style. The unigram LM <b>shrinks</b> a large seed vocabulary by pruning, then segments with Viterbi.
:::

::: reveal myth
? "Unigram tokenization picks the longest matching piece first."
> It picks the segmentation with the <b>highest product of probabilities</b>, found by Viterbi, which isn't always the one with the longest pieces.
:::

::: reveal myth
? "Pruning can remove characters and create unknowns."
> Subwords consisting of a single character are <b>always kept</b> (§3.2), so every string stays encodable.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? What vocabulary does BERT use?
- [ ] Byte-level BPE, 50,257
- [x] WordPiece, 30,000 tokens
- [ ] Unigram LM, 32,000
- [ ] Words, 100,000
> <b>WordPiece with a 30,000-token vocabulary</b> (BERT, §3).
:::

<div class="quiz">
  <p class="qq">In the unigram LM, how is the best segmentation found?</p>
  <div class="opts">
  <button>A. Greedy longest match</button>
  <button>B. Replaying merges</button>
  <button data-ok>C. The Viterbi algorithm</button>
  <button>D. Random sampling</button>
  </div>
  <div class="why"><b>Viterbi</b>: x* = argmax P(x) over all candidate segmentations (Eq. 7).</div>
</div>

<div class="quiz ">
  <p class="qq">In one pruning round, what fraction of subwords does Kudo's example keep, and which are always kept?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">The top <b>η = 80%</b> by loss. Single-character subwords are always kept.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Likelihood-based tokenizers score segmentations: WordPiece chooses merges by likelihood, and the unigram LM prunes a big vocabulary with EM and segments with Viterbi.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>BPE merges by raw frequency and replays merges greedily, so it gives one segmentation with no probability. WordPiece, used by BERT with 30,000 tokens, grows the vocabulary like BPE but chooses merges by likelihood. The unigram LM gives each subword a probability, scores a segmentation as the product of its pieces' probabilities, finds the best with Viterbi, and learns the vocabulary by running EM and pruning the 20% of pieces whose removal hurts likelihood least. Single characters are always kept.</p></div>

<div class="recap"><div><span><b>Problem:</b> BPE is greedy and deterministic, with no probabilities.</span></div><div><span><b>Core idea:</b> model subwords probabilistically: WordPiece merges by likelihood; the unigram LM uses EM, pruning and Viterbi.</span></div></div>

<p class="start-hint">Next: <a href="../05-sentencepiece/index.html">05 · SentencePiece →</a> · Previous: <a href="../03-byte-level-bpe/index.html">← 03</a> · <a href="../index.html">All decks</a> · <a href="../playground/index.html">Playground</a></p>

<!-- slide id="s-papers" from="papers" -->
