---
title: Quality Filtering
body:
  data-deck: Quality filtering
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
  - 'document :: extracted text :: f'
  - 'heuristic rules :: C4 + Gopher :: c'
  - 'repetition checks :: duplicate n-grams :: b'
  - 'classifier score :: fastText / small LM :: a'
  - 'keep top fraction :: tuned by ablation :: e'
  caption: Rules remove obvious junk; classifiers decide what counts as good.
example:
  title: 'Worked example: model-based filtering pays off'
  setup: DCLM (Li et al., 2024) compared filters on a 240T-token Common Crawl pool; FineWeb-Edu (Penedo et al., 2024) annotated pages with an LLM.
  steps:
  - 'DCLM: a fastText classifier trained with instruction-style data (OpenHermes 2.5) and top r/ExplainLikeImFive posts as positives gave a <b>3.5-point</b> lift
    on its core benchmark over more conventional choices.'
  - The resulting DCLM-Baseline trained a 7B model to <b>64% 5-shot MMLU</b> with 2.6T tokens.
  - 'FineWeb-Edu: Llama-3-70B-Instruct scored 460,000 pages for educational value (0–5); a classifier trained on those labels (threshold 3, F1 82%) selected <b>1.3T
    tokens</b> from FineWeb''s 15T.'
  - Running that classifier over all 15T tokens took 6,000 H100 GPU-hours.
  result: Heuristics are necessary but not sufficient; a cheap learned notion of "good text" gives the biggest gains.
traps:
  tricks:
  - 'Gopher rules. :: 50–100,000 words; mean word length 3–10; ≥ 2 stop words; symbol ratio ≤ 0.1.'
  - 'C4 rules. :: Lines end in punctuation, ≥ 5 words; ≥ 3 sentences; no "{" or lorem ipsum.'
  - 'fastText classifiers. :: Fast enough for trillions of tokens on CPUs.'
  traps:
  - 'Over-filtering. :: C4''s curly-bracket rule removes all code; strict rules can remove dialects and minority topics.'
  - 'Filtering on your benchmark. :: Classifiers trained toward test-like text inflate scores.'
  - 'Perplexity alone. :: Prefers text similar to the reference corpus (e.g. Wikipedia), not necessarily useful text.'
papers:
- t5
- gopher
- ccnet
- dclm
- fineweb
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Pretraining Data · 06</div>
    <h1>Quality filtering</h1>
    <p class="sub">Deciding which documents are worth training on: transparent heuristic rules (C4, Gopher), perplexity scoring (CCNet), and model-based classifiers (DCLM, FineWeb-Edu, Llama 3).</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>After extraction, much of the web is still spam, keyword lists, machine-generated pages, fragments and code dumps. Training on it wastes compute and teaches bad habits.</div>
      <div class="c"><b>Core idea</b>Apply cheap <b>heuristic rules</b> first (word counts, word length, symbol ratios, punctuation, stop words, repetition), then <b>model-based scoring</b>: a classifier (often fastText) trained to separate high-quality reference text from random web text, keeping the top fraction.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Run the rules

Six sample documents from notebook 04. Toggle rule sets and see which documents survive, with the first rule each one fails.
{: .lede}

<div class="visual">
  <div class="seg" id="qSeg"><button data-v="c4">C4 rules</button><button data-v="gopher" class="on">Gopher rules</button><button data-v="both">both + repetition</button></div>
  <div id="qList" style="margin-top:12px;display:grid;gap:6px"></div>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why rules alone fall short

::: cards grid3
### [d] Blunt
C4 drops any page containing "{", removing all code along with the junk.

### [b] Gameable
Well-formed spam passes word-count and punctuation checks.

### [c] No notion of value
Rules detect broken text, not whether a page is informative.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Which filter catches Latin placeholder text?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? "Lorem ipsum dolor sit amet…" passes length and punctuation checks. Which Gopher rule catches it?
- [ ] word count
- [ ] mean word length
- [x] the stop-word rule (≥ 2 of the, be, to, of, and, that, have, with)
- [ ] bullet lines
> <b>C.</b> It contains no English stop words. C4 removes it directly with its "lorem ipsum" rule.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Three generations of filters

::: cards grid3
### [c] Heuristic rules
C4 (2020) and Gopher (2021): length, characters, punctuation, stop words, repetition. Transparent and cheap.

### [b] Reference-model perplexity
CCNet (2020): score each document by the perplexity of a language model trained on Wikipedia.

### [a] Learned classifiers
DCLM, FineWeb-Edu, Llama 3: classifiers trained on curated or LLM-labelled examples pick the top fraction.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## The rules, verbatim

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Source</th><th>Rule</th></tr>
  <tr><td>C4</td><td>keep lines ending in terminal punctuation with ≥ 5 words; drop pages with &lt; 3 sentences, bad words, "lorem ipsum" or "{"; drop lines with "javascript" or cookie/privacy notices; English with probability ≥ 0.99</td></tr>
  <tr><td>Gopher</td><td>50–100,000 words; mean word length 3–10; symbol-to-word ratio ≤ 0.1 for # and ellipsis; ≤ 90% bullet lines; ≤ 30% lines ending in ellipsis; ≥ 80% words with a letter; ≥ 2 of 8 stop words</td></tr>
  <tr><td>Llama 3</td><td>duplicated n-gram coverage, "dirty word" counts, token-distribution KL divergence; then fastText and DistilRoberta quality classifiers trained on Llama 2 labels</td></tr>
</table></div>
<p class="caption">From Raffel et al. 2020, Rae et al. 2021 and the Llama 3 report.</p>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why filtering improves models

::: cards grid2
### [a] Better tokens per FLOP
Removing junk means each training step learns from more informative text.

### [e] Fewer bad habits
Spam, keyword lists and broken text teach repetition and incoherence.

### [b] Cheap at scale
Rules and fastText run on CPUs over trillions of tokens.

### [c] Ablation-driven
FineWeb and DCLM choose thresholds by training small models and measuring benchmarks.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Quality filtering means keeping text like Wikipedia."
> That is one choice (CCNet, GPT-3-style classifiers); DCLM found instruction-like and ELI5 positives worked better.
:::

::: reveal myth
? "Heuristic filters are obsolete."
> Every modern pipeline still runs them first; classifiers come after.
:::

::: reveal myth
? "Filtering is neutral."
> Definitions of "quality" and "toxicity" encode choices and can remove dialects and minority voices (Dolma discusses this).
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Gopher keeps documents with how many words?
- [ ] 10–1,000
- [x] 50–100,000
- [ ] 100–1,000,000
- [ ] any
> <b>50 to 100,000.</b>
:::

::: reveal
? What did DCLM find works best for quality filtering?
> A fastText classifier with instruction-formatted data (OpenHermes 2.5) and high-scoring ELI5 posts as positives.
:::

::: reveal
? Why can C4's rules hurt a code-capable model?
> Dropping every page with a curly bracket removes nearly all code.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Quality filtering stacks cheap heuristic rules (C4, Gopher) with learned classifiers (fastText, LLM-labelled) that keep the most useful fraction; model-based filtering gives the biggest gains.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>After extraction, much web text is still spam, keyword lists, fragments or code dumps. Pipelines first apply transparent rules: C4 keeps lines ending in punctuation and drops pages with placeholder text or curly brackets; Gopher requires between 50 and 100,000 words, normal word lengths, few symbols and at least two common English stop words, and removes highly repetitive documents. Then a learned filter scores what remains. DCLM's fastText classifier trained on instruction-style examples and FineWeb-Edu's classifier trained on Llama 3 ratings both beat heuristics alone, which is why model-based filtering is now standard.</p></div>
    <div class="recap"><div><span><b>Problem:</b> junk that passes extraction.</span></div><div><span><b>Core idea:</b> rules first, then a learned quality classifier.</span></div><div><span><b>Evidence:</b> DCLM 64% MMLU at 7B; FineWeb-Edu 1.3T tokens.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pretraining-data/04_quality_filters.ipynb" target="_blank" rel="noopener">04 · Heuristic quality filters (C4 and Gopher rules)</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/pretraining-data/04_quality_filters.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../07-deduplication/index.html">07 · Deduplication →</a> · Previous: <a href="../05-text-extraction/index.html">← 05</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
