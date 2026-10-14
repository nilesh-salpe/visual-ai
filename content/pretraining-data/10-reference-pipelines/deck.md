---
title: Reference Pipelines
body:
  data-deck: Reference pipelines
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
  - 'extract :: WET or WARC + extractor :: f'
  - 'filter :: rules → classifiers :: a'
  - 'dedup :: exact + MinHash :: b'
  - 'scrub :: PII + safety :: d'
  - 'ablate :: train small models to decide :: e'
  caption: Choices are validated by training small models and comparing benchmarks.
example:
  title: 'Worked example: what changed from C4 to FineWeb-Edu'
  setup: The same source (Common Crawl), four years of pipeline evolution.
  steps:
  - 'C4 (2019 crawl): WET text, line and page rules, three-sentence-span dedup, English ≥ 0.99: about <b>750 GB</b> of text.'
  - 'RefinedWeb (2023): WARC + trafilatura, Gopher-style rules, strict MinHash and exact-substring dedup: <b>5T tokens</b>, beats curated corpora.'
  - 'FineWeb (2024): 96 snapshots, per-snapshot MinHash, ablated C4 filters: <b>15T tokens</b>; FineWeb-Edu adds an LLM-labelled classifier: <b>1.3T tokens</b>.'
  - 'DCLM (2024): a fastText quality classifier as the key ingredient: a 7B model reaches <b>64% MMLU</b> on 2.6T tokens.'
  result: 'Scale grew 20× while selection became more aggressive: the best datasets are both bigger and more selective.'
traps:
  tricks:
  - 'Same skeleton everywhere. :: Learn the stages, then compare choices.'
  - 'Ablate with small models. :: FineWeb and DCLM decide each filter by training ~1B models.'
  - 'Report removal rates. :: Each stage''s kept fraction makes pipelines comparable.'
  traps:
  - 'Copying a pipeline without its ablations. :: Thresholds tuned for English web may fail for code or other languages.'
  - 'Benchmark contamination. :: Classifiers or filters that favour test-like text inflate scores.'
  - 'Ignoring consent trends. :: Re-crawls may now be restricted by robots.txt (deck 04).'
papers:
- t5
- gopher
- refinedweb
- fineweb
- dclm
- dolma
- llama3
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Pretraining Data · 10</div>
    <h1>Reference pipelines</h1>
    <p class="sub">Seven published pipelines side by side, from C4 to Llama 3: what each one does at every stage, and the lessons the field converged on.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Each paper describes its own pipeline with different names and orderings. To design or evaluate one, you need a common map of the choices.</div>
      <div class="c"><b>Core idea</b>Nearly every pipeline follows the same skeleton: <b>extract → language ID → heuristic filters → dedup → (model-based filter) → safety/PII → mix</b>. They differ in extraction (WET vs WARC), how aggressive dedup is, and whether a learned quality filter is used. The trend: learned filters and careful dedup, validated by small-model ablations.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Compare the pipelines

Pick a dataset to see its stages. Cells marked — mean the stage was not described or not used.
{: .lede}

<div class="visual">
  <div class="seg" id="dSeg" style="display:flex;flex-wrap:wrap"><button data-v="c4">C4</button><button data-v="gopher">Gopher</button><button data-v="rw">RefinedWeb</button><button data-v="fw" class="on">FineWeb</button><button data-v="dclm">DCLM</button><button data-v="dolma">Dolma</button><button data-v="llama3">Llama 3</button></div>
  <div class="scroll-x" style="margin-top:12px"><table class="tbl" id="dTbl"></table></div>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why comparing pipelines is hard

::: cards grid3
### [d] Different names
The same step is called "content filtering", "URL filtering" or "safety filtering".

### [b] Different orders
Some dedup before filtering, others after; some dedup per snapshot, others globally.

### [c] Few ablations
Until recently, most choices were not tested individually.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What changed most between C4 and DCLM?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Comparing C4 (2020) and DCLM-Baseline (2024), which ingredient did DCLM find most important?
- [ ] More languages
- [x] A learned (fastText) quality classifier
- [ ] Using WET files
- [ ] Removing all code
> <b>B.</b> DCLM: "model-based filtering is key to assembling a high-quality training set".
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## One skeleton, many choices

::: cards grid2
### [f] Extraction
WET (C4, CCNet) → WARC + trafilatura (RefinedWeb, FineWeb, DCLM) → custom parsers (Llama 3).

### [a] Filtering
Rules (C4, Gopher) → + perplexity (CCNet) → + learned classifiers (DCLM, FineWeb-Edu, Llama 3).

### [b] Deduplication
Spans (C4) → MinHash (Gopher, RefinedWeb, FineWeb) + URL and line levels (Llama 3).

### [e] Validation
Small-model ablations per decision (FineWeb, DCLM) instead of intuition.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Lessons the field converged on

::: cards grid3
### [a] Extract from WARC
Modern extractors beat Common Crawl's WET text (FineWeb ablation).

### [b] Deduplicate carefully
Strict near-dup removal helps; global cross-snapshot dedup can hurt (FineWeb).

### [e] Learn what "good" means
A cheap classifier trained on carefully chosen positives gives the largest gains (DCLM, FineWeb-Edu).

### [c] Mix deliberately
Domain weights and late annealing on high-quality data matter (Llama 3).

### [d] Scrub and respect consent
PII masking, safety filters and robots.txt compliance are part of the pipeline.

### [f] Measure everything
Report kept fractions and ablate each stage with small models.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why open pipelines matter

::: cards grid2
### [a] Reproducible science
Open datasets (RefinedWeb, FineWeb, DCLM, Dolma) let others test data choices directly.

### [e] Data beats tricks
DCLM-Baseline matched Mistral-7B-v0.3 and Llama 3 8B on MMLU (63% and 66%) with 6.6× less compute than Llama 3 8B.

### [b] Transfer to new domains
The same skeleton is reused for code, math and other languages with domain-specific rules.

### [c] Accountability
Documented filters make biases and removals inspectable.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Frontier labs use secret magic data."
> Published pipelines show the same stages; details and scale differ, and open datasets now rival closed ones on many benchmarks.
:::

::: reveal myth
? "The best pipeline keeps the most data."
> FineWeb-Edu kept under 10% of FineWeb and scored much higher on knowledge benchmarks.
:::

::: reveal myth
? "Pipelines are finished once."
> Each new crawl, language or domain needs re-tuned filters and fresh ablations.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Which dataset introduced per-snapshot (rather than global) MinHash dedup after ablations?
- [ ] C4
- [ ] Gopher
- [x] FineWeb
- [ ] Dolma
> <b>FineWeb.</b>
:::

::: reveal
? List the common stages of a pretraining data pipeline.
> Extraction, language ID, heuristic filters, deduplication, model-based quality filtering, PII/safety filtering, mixing.
:::

::: reveal
? How do FineWeb and DCLM decide whether a filter helps?
> They train small models on data with and without the filter and compare downstream benchmark scores.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Published pipelines share one skeleton (extract, filter, dedup, scrub, mix); the field converged on WARC extraction, careful MinHash dedup and learned quality classifiers, all validated by small-model ablations.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>C4, Gopher, RefinedWeb, FineWeb, DCLM, Dolma and Llama 3 all follow the same skeleton: extract text, identify the language, apply heuristic filters, deduplicate, often apply a learned quality filter, scrub personal and unsafe content, and mix. They differ in the details: newer pipelines extract from raw WARC files with tools such as trafilatura, deduplicate with MinHash at several levels while avoiding over-aggressive global deduplication, and select data with cheap classifiers trained on carefully chosen examples. Crucially, FineWeb and DCLM validated each choice by training small models, which is how data work became a measurable science.</p></div>
    <div class="recap"><div><span><b>Problem:</b> many pipelines, different vocabularies.</span></div><div><span><b>Core idea:</b> one skeleton; compare choices per stage.</span></div><div><span><b>Lessons:</b> WARC extraction, careful dedup, learned filters, ablations.</span></div></div>
    <p class="start-hint">You've finished the series. <a href="../../build-it/index.html">See all Build-it notebooks →</a> · Previous: <a href="../09-mixtures-and-repetition/index.html">← 09</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
