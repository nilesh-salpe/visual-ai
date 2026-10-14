---
title: BPE From Scratch
body:
  data-deck: BPE from scratch
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
  - 'characters :: words split into symbols

    + end-of-word marker :: f'
  - 'count pairs :: adjacent symbol pairs × word frequency :: c'
  - 'merge the top pair :: add it to the vocabulary :: a'
  - 'repeat :: until vocabulary size :: e'
  loop: '3 -> 1 :: each merge creates a new symbol'
  caption: Training learns an ordered list of merges; encoding replays them in the same order.
example:
  title: 'Worked example: the first merges on Sennrich''s toy corpus'
  setup: 'Word counts: low ×5, lower ×2, newest ×6, widest ×3 (each word split into characters plus an end-of-word marker &lt;/w&gt;).'
  steps:
  - 'Merge 1: <b>e + s</b> → "es" (pair count 9).'
  - 'Merge 2: <b>es + t</b> → "est" (pair count 9).'
  - 'Merge 3: <b>est + &lt;/w&gt;</b> → "est&lt;/w&gt;" (pair count 9).'
  - 'Merge 4: <b>l + o</b> → "lo" (pair count 7).'
  - 'After 4 merges: newest = n · e · w · est&lt;/w&gt;, widest = w · i · d · est&lt;/w&gt;, low = lo · w · &lt;/w&gt;.'
  result: '"es", "est" and "est&lt;/w&gt;" come first because newest (×6) + widest (×3) give each 9 occurrences; then "lo" (low ×5 + lower ×2 = 7). Ties go to the
    first pair found, as in Sennrich''s reference code.'
traps:
  tricks:
  - 'Vocab size = base symbols + merges. :: GPT-2: 256 bytes + 50,000 merges + 1 special = 50,257.'
  - 'Encode by replaying merges in order. :: Not by greedy longest match.'
  - 'Counts are weighted by word frequency. :: A pair in a frequent word counts many times.'
  traps:
  - 'Greedy longest-match encoding. :: That is WordPiece-style, and gives different splits than BPE.'
  - 'Merging across words. :: Classic BPE never merges across word boundaries.'
  - 'Ignoring tie-breaking. :: Different tie rules give different vocabularies.'
papers:
- sennrich
- gpt2
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Tokenization for LLMs · 02</div>
    <h1>Byte-pair encoding, from scratch</h1>
    <p class="sub">The algorithm behind most LLM (large language model) tokenizers: start from characters and repeatedly merge the most frequent adjacent pair (Sennrich, Haddow and Birch, 2016).</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Translation and language modelling are open-vocabulary problems, and a fixed word list can't cover rare words, names and compounds.</div>
      <div class="c"><b>Core idea</b>Learn a vocabulary of frequent character sequences by repeatedly merging the most frequent pair of symbols. Rare words are then spelled with those pieces.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Rare words are everywhere

::: cards grid3
### [a] Names
New people, places and products appear constantly. Many can just be copied or transliterated piece by piece.

### [b] Compounds
German builds words like <b>Abwasserbehandlungsanlage</b> ("sewage water treatment plant"), the paper's own example. It's unlikely to be in any word list, but its parts are common.

### [c] Cognates and loanwords
Words shared across languages often translate through regular character-level patterns.
:::

<div class="takeaway">The paper's observation: many rare words can be translated through units <em>smaller than words</em>.</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Before BPE: shortlists, unknown tokens and back-off dictionaries

::: cards grid3
### [d] Fixed word vocabulary
Models used a shortlist of frequent words; everything else became an unknown token.

### [b] Back-off dictionary
Unknown words were looked up in a separate dictionary after translation, outside the neural model. This was the paper's baseline.

### [c] Characters only
Fully open, but sequences become much longer, which hurts efficiency and makes information travel further.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Which pair merges first?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Training corpus (the one in the paper's Algorithm 1): <code>low ×5, lower ×2, newest ×6, widest ×3</code>, each word split into characters plus an end-of-word marker ·. Which pair does BPE (byte-pair encoding) merge first?
- [ ] l + o
- [x] e + s
- [ ] w + i
- [ ] n + e
> <b>e + s</b>, with 9 occurrences (newest ×6 + widest ×3). s + t and t + · are also 9, and the tie goes to the pair counted first. l + o has 7, n + e has 6, w + i has 3. Then "es + t" and "est + ·" follow. Check it in the trainer two slides on.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Merge the most frequent pair, repeat

<div class="grid2">
  <div class="card a"><h3>1. Start from characters</h3><p>Each word is a sequence of characters plus an end-of-word symbol ·, so the original spacing can be restored.</p></div>
  <div class="card b"><h3>2. Count adjacent pairs</h3><p>Count every pair of neighbouring symbols, weighted by word frequency. Pairs never cross word boundaries.</p></div>
  <div class="card e"><h3>3. Merge the top pair</h3><p>Replace every occurrence of the most frequent pair (A, B) with a new symbol AB and record the merge.</p></div>
  <div class="card c"><h3>4. Repeat</h3><p>Stop after a chosen number of merges. Final vocabulary = initial characters + merges, and the number of merges is "the only hyperparameter".</p></div>
</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Train BPE yourself

Edit the corpus (<code>word:count</code>) and step through merges. The trainer is a direct JavaScript port of the paper's Algorithm 1.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <input class="tk-in" id="bpeCorpus" style="flex:1;min-width:260px" value="low:5, lower:2, newest:6, widest:3">
    <label class="ctl">Merges <input type="range" id="bpeN" min="0" max="15" step="1" value="3"> <output id="bpeNo"></output></label>
  </div>
  <div class="grid2" style="margin-top:12px">
    <div><h3>Corpus after merges</h3><div id="bpeVocab"></div><h3 style="margin-top:12px">Next candidate pairs</h3><div id="bpePairs"></div></div>
    <div><h3>Learned merges, in order</h3><div class="mergelist" id="bpeMerges"></div>
      <h3 style="margin-top:12px">Encode a new word</h3>
      <div class="controls" style="margin-top:4px"><input class="tk-in" id="bpeWord" value="lowest" style="width:160px"></div>
      <div id="bpeEnc" style="margin-top:8px"></div></div>
  </div>
</div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Encoding an unseen word: the paper's Figure 1

At test time, split the word into characters and apply the learned merges <b>in the order they were learned</b>. Figure 1 lists four merges learned from the dictionary {low, lowest, newer, wider}. The unseen word "lower" then comes out as <b>low er·</b>.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><button class="btn primary" id="f1Step">Apply next merge →</button><button class="btn" id="f1Reset">Reset</button><span class="readout" id="f1Out"></span></div>
  <div id="f1Toks" style="margin-top:14px"></div>
  <div class="mergelist" id="f1List" style="margin-top:12px"></div>
</div>

<div class="cite">Sennrich et al. (2016), Figure 1 and §3.2.</div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why BPE works

::: cards grid2
### [a] Frequency decides granularity
Frequent strings are merged early, so common words become single symbols. Rare words remain split into smaller units.

### [e] No shortlist, no back-off
Any word made of known characters can be encoded, so the model handles rare and unseen words itself.

### [b] Compression
It comes from a data-compression algorithm (Gage, 1994): fewer symbols are needed to encode the text.

### [c] Measured gains
On WMT (Workshop on Machine Translation) 15, subword models improved over the back-off dictionary baseline by <b>1.1 BLEU (Bilingual Evaluation Understudy, an n-gram overlap score for translation)</b> (EN→DE) and <b>1.3 BLEU</b> (EN→RU) (abstract).
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "BPE finds the shortest or most likely segmentation of a word."
> It replays merges <b>greedily, in learned order</b>. That is fast and deterministic, but not an optimization over all segmentations (compare the unigram LM (language model) in deck 04).
:::

::: reveal myth
? "You choose the vocabulary size directly."
> In the original algorithm you choose the <b>number of merges</b>; vocabulary = characters + merges. Toolkits such as SentencePiece let you specify the final vocabulary size instead (deck 05).
:::

::: reveal myth
? "BPE merges can join two words."
> Not in the paper: "we do not consider pairs that cross word boundaries". LLM tokenizers enforce this with pre-tokenization (deck 03).
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Using the paper's Figure 1 merges, how is the unseen word "lower" segmented?
- [ ] l o w e r ·
- [x] low er·
- [ ] lower·
- [ ] lo wer·
> <b>low er·</b> (§3.2).
:::

<div class="quiz ">
  <p class="qq">What is the only hyperparameter of the original BPE algorithm?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">The <b>number of merge operations</b>. The final symbol vocabulary is the initial characters plus the merges.</div>
</div>

::: quiz
? What is the end-of-word symbol for?
- [ ] To mark rare words
- [x] To restore the original tokenization after translation
- [ ] To count frequencies
- [ ] To pad sequences
> It lets you <b>restore the original word boundaries</b> after processing (§3.2).
:::

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">BPE starts from characters and repeatedly merges the most frequent adjacent pair. Replaying those merges in order turns any word into known subword units.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Byte-pair encoding, adapted to NLP (natural language processing) by Sennrich et al. (2016), learns a subword vocabulary from data. Every word starts as characters plus an end-of-word marker; you repeatedly count adjacent symbol pairs and merge the most frequent one, and the number of merges is the only hyperparameter. Frequent words end up as single symbols and rare words split into pieces, so there are no unknown words. To encode new text you replay the merges in learned order.</p></div>

<div class="recap"><div><span><b>Problem:</b> a fixed word vocabulary can't cover rare words, names and compounds.</span></div><div><span><b>Core idea:</b> learn merges of frequent symbol pairs; encode any word by replaying them in order.</span></div></div>

<p class="start-hint">Next: <a href="../03-byte-level-bpe/index.html">03 · Byte-level BPE →</a> · Previous: <a href="../01-why-tokenize/index.html">← 01</a> · <a href="../index.html">All decks</a> · <a href="../playground/index.html">Playground</a></p>

<!-- slide id="s-papers" from="papers" -->
