---
title: Where Pretraining Data Comes From
body:
  data-deck: Where pretraining data comes from
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
  - 'crawl :: raw HTML (WARC) :: f'
  - 'extract + language ID :: text per language :: c'
  - 'quality filter :: rules + classifiers :: a'
  - 'deduplicate :: exact + near-duplicate :: b'
  - 'safety + PII :: remove / mask :: d'
  - 'mix :: web + code + math + books :: e'
  caption: Decks 02–10 walk through each stage.
example:
  title: 'Worked example: how much of a crawl survives?'
  setup: RefinedWeb (Penedo et al., 2023) reports what fraction of Common Crawl documents remain after each stage of its pipeline.
  steps:
  - 'URL filtering, text extraction and language identification (English only): <b>48%</b> of documents remain, most lost to language ID.'
  - 'Repetition removal and document/line quality filters: <b>23%</b> remain.'
  - 'Fuzzy (MinHash) and exact deduplication: about <b>10%</b> remain: "nearly 90%" of documents are removed in total.'
  - Even so, RefinedWeb extracted about 5 trillion tokens; FineWeb's 96 snapshots gave 15 trillion.
  result: 'Web data is abundant but mostly unusable as-is: the pipeline, not the crawl, is where data quality is made.'
traps:
  tricks:
  - 'Common Crawl formats. :: WARC = raw responses, WAT = metadata, WET = extracted text.'
  - 'Expect ~90% loss. :: Language, quality and duplicates each remove large shares.'
  - 'Mix matters. :: Llama 3: ~50% general, 25% math/reasoning, 17% code, 8% multilingual.'
  traps:
  - 'Assuming "more web" = better. :: Quality and deduplication beat raw volume.'
  - 'Treating WET text as clean. :: It keeps menus and boilerplate.'
  - 'Forgetting licensing and consent. :: robots.txt and terms of service increasingly restrict AI crawlers (deck 04).'
papers:
- commoncrawl
- refinedweb
- llama3
- dolma
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Pretraining Data · 01</div>
    <h1>Where pretraining data comes from</h1>
    <p class="sub">The sources behind trillion-token training sets, why the open web dominates, and how much of a raw crawl survives the cleaning pipeline.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>A frontier model trains on about 15 trillion tokens. No curated collection is that large, so most of it must come from the web, which is mostly noise.</div>
      <div class="c"><b>Core idea</b>Start from a <b>web crawl</b> (usually Common Crawl), then run a <b>pipeline</b>: extract text, identify language, filter for quality, deduplicate, remove unsafe and personal data, and <b>mix</b> with curated sources (code, books, papers, math). Typically only about 10% of crawled documents survive.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## From a crawl to a training set

Documents remaining after each stage of RefinedWeb's pipeline, as a share of the original Common Crawl documents. Toggle to see a reported final data mix instead.
{: .lede}

<div class="visual">
  <div class="seg" id="fSeg"><button data-v="funnel" class="on">pipeline funnel (RefinedWeb)</button><button data-v="mix">final mix (Llama 3)</button></div>
  <div id="fBars" style="margin-top:12px"></div>
  <p class="readout" id="fOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why not just use curated text?

::: cards grid3
### [d] Too small
Wikipedia, books and papers together are far short of 15T tokens.

### [b] Too narrow
Models need conversational, technical, multilingual and code text in many styles.

### [c] Too static
Curated sets update slowly; a monthly crawl brings 3–5 billion new pages.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What removes the most?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? In RefinedWeb's English pipeline, which single stage removed the largest share of Common Crawl documents?
- [ ] URL blocklist
- [x] Language identification
- [ ] Deduplication
- [ ] Text extraction
> <b>B.</b> About half of all documents were not English. Filtering then removed about half of the rest, and deduplication about half again.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Crawl, clean, mix

::: cards grid2
### [f] Crawl
Common Crawl: a free, open crawl of over 300 billion pages, released as WARC, WAT and WET files.

### [a] Clean
Extract main text, keep target languages, apply quality rules and classifiers.

### [b] Deduplicate
Remove exact and near-duplicate documents and repeated lines.

### [e] Mix
Combine cleaned web text with code, math, books and multilingual data in chosen proportions.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Common Crawl's three file types

<div class="visual scroll-x"><table class="tbl">
  <tr><th>File</th><th>Contents</th><th>Used for</th></tr>
  <tr><td>WARC (Web ARChive)</td><td>raw HTTP responses: full HTML and headers</td><td>custom text extraction (RefinedWeb, FineWeb, Llama 3)</td></tr>
  <tr><td>WAT</td><td>metadata: links, headers</td><td>link graphs, URL analysis</td></tr>
  <tr><td>WET</td><td>plain text extracted by Common Crawl</td><td>quick start (C4, CCNet); keeps boilerplate</td></tr>
</table></div>

::: deep Corpus sizes for scale
Dolma: about 200 TB of raw text curated down to an 11 TB, 3T-token corpus. Llama 3: about 15T multilingual tokens, versus 1.8T for Llama 2.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why the web works despite the noise

::: cards grid2
### [a] Scale
Even a 10% survival rate leaves trillions of tokens.

### [e] Diversity
The web covers nearly every topic, register and language.

### [b] Filtering is cheap
Rules and small classifiers process terabytes on CPUs (Dolma: ~122 CPU-hours per TB for C4-style filtering).

### [c] Evidence
RefinedWeb showed properly filtered and deduplicated web data alone can match or beat curated mixtures.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "LLMs are trained on "the whole internet"."
> They are trained on a heavily filtered, deduplicated slice: typically about a tenth of crawled documents, plus curated sources.
:::

::: reveal myth
? "Common Crawl is clean text."
> It is raw crawl output; its WET text keeps navigation, ads and boilerplate.
:::

::: reveal myth
? "More data is always better."
> Removing low-quality and duplicate data improves models at the same compute (RefinedWeb, FineWeb, DCLM).
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Which Common Crawl file type holds the raw HTML?
- [ ] WET
- [ ] WAT
- [x] WARC
- [ ] robots.txt
> <b>WARC</b>.
:::

::: reveal
? Name the main stages of a pretraining data pipeline.
> Crawl → text extraction → language ID → quality filtering → deduplication → safety/PII filtering → mixing.
:::

::: reveal
? Roughly what fraction of crawled documents survive RefinedWeb's pipeline?
> About 10%: "nearly 90%" are removed.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Pretraining data is mostly filtered web crawl: extract, identify language, filter, deduplicate, scrub and mix, and only about a tenth of crawled documents survive.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Trillion-token training sets can only come from the web, usually Common Crawl, which publishes raw responses as WARC files plus metadata and extracted text. A pipeline turns that into training data: extract the main text from HTML, keep the target languages, apply quality rules and classifiers, remove exact and near duplicates, mask or remove personal and unsafe content, and finally mix the cleaned web text with code, math, books and multilingual data. In RefinedWeb only about ten percent of documents survived, yet that still gave five trillion tokens. Llama 3 trained on about fifteen trillion.</p></div>
    <div class="recap"><div><span><b>Problem:</b> need ~15T tokens; the web is the only source that large.</span></div><div><span><b>Core idea:</b> crawl → clean → dedup → scrub → mix.</span></div><div><span><b>Numbers:</b> ~10% of documents survive; WARC/WAT/WET.</span></div></div>
    <p class="start-hint">Next: <a href="../02-how-a-crawler-works/index.html">02 · How a web crawler works →</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
