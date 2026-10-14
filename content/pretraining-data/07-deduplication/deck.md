---
title: Deduplication
body:
  data-deck: Deduplication
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
  - 'shingles :: word 5-grams :: f'
  - 'MinHash :: k minimum hashes :: a'
  - 'LSH bands :: b bands × r rows :: c'
  - 'candidate pairs :: share a band :: b'
  - 'cluster + keep one :: remove the rest :: e'
  caption: 'P(candidate) = 1 − (1 − sʳ)ᵇ: an S-curve around s ≈ (1/b)^(1/r).'
example:
  title: 'Worked example: choosing b and r'
  setup: Two pipelines' MinHash settings, evaluated with P(s) = 1 − (1 − sʳ)ᵇ for Jaccard similarity s.
  steps:
  - 'RefinedWeb: 9,000 hashes as 450 bands × 20 rows. P(0.75) = <b>76%</b>, P(0.8) = <b>99.5%</b>; threshold ≈ (1/450)^(1/20) = 0.74.'
  - 'FineWeb: 112 hashes as 14 bands × 8 rows, "targeting documents that are at least 75% similar": P(0.75) = <b>77%</b>, P(0.8) = 92%, P(0.5) = 5.3%.'
  - 'Gopher: near-duplicates are documents whose 13-gram Jaccard similarity exceeds 0.8.'
  - Lee et al. (2022) found one 61-word sentence repeated over 60,000 times in C4; deduplicated models emitted memorised text 10× less often.
  result: More bands lower the threshold; more rows per band sharpen it. Pipelines tune both to their notion of "duplicate".
traps:
  tricks:
  - 'Threshold ≈ (1/b)^(1/r). :: Steepness grows with r.'
  - 'Jaccard on word n-grams. :: 5-grams (RefinedWeb, FineWeb) or 13-grams (Gopher).'
  - 'Line-level dedup. :: Llama 3 removed lines appearing more than 6 times per 30M-document bucket.'
  traps:
  - 'Global dedup across all snapshots. :: FineWeb found it kept worse data; per-snapshot dedup worked better.'
  - 'Comparing all pairs. :: n² is impossible at billions of documents; use LSH.'
  - 'Forgetting test sets. :: Remove documents overlapping benchmarks (Gopher''s test-set filtering).'
papers:
- broder97
- lee_dedup
- fineweb
- refinedweb
- gopher
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Pretraining Data · 07</div>
    <h1>Deduplication</h1>
    <p class="sub">Why the web is full of copies, and how pipelines remove exact duplicates, near-duplicates (MinHash with locality-sensitive hashing) and repeated lines and substrings.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>The same text appears thousands of times: mirrored pages, templates, licences, quotes, spam. Training on it wastes compute, encourages memorisation and leaks test data.</div>
      <div class="c"><b>Core idea</b>Remove <b>exact</b> duplicates with hashes (URL, document, line). Find <b>near-duplicates</b> by comparing documents' sets of word n-grams: <b>MinHash</b> compresses each set into a signature whose agreement estimates Jaccard similarity, and <b>LSH banding</b> finds similar pairs without comparing all pairs.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Tune the LSH S-curve

Probability that a pair with Jaccard similarity s becomes a candidate, for b bands of r rows. Presets reproduce RefinedWeb and FineWeb.
{: .lede}

<div class="visual">
  <div class="seg" id="lSeg"><button data-v="20,450">RefinedWeb (450 × 20)</button><button data-v="8,14" class="on">FineWeb (14 × 8)</button><button data-v="5,20">20 × 5</button></div>
  <div class="controls"><label class="ctl">rows per band r <input type="range" id="lR" min="1" max="30" step="1" value="8"> <output id="lRo"></output></label><label class="ctl">bands b <input type="range" id="lB" min="1" max="500" step="1" value="14"> <output id="lBo"></output></label></div>
  <svg id="lSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="LSH S-curve"></svg>
  <p class="readout" id="lOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why simple hashing isn't enough

::: cards grid3
### [d] Near-duplicates
A changed date, ad or footer gives a different hash for essentially the same page.

### [b] All-pairs is impossible
Billions of documents mean ~10¹⁸ pairs.

### [c] Repeated pieces
Boilerplate lines and licences repeat inside otherwise unique documents.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What does MinHash estimate?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? For two documents' shingle sets, the fraction of positions where their MinHash signatures agree estimates…
- [ ] their length ratio
- [x] their Jaccard similarity |A ∩ B| / |A ∪ B|
- [ ] their edit distance
- [ ] their cosine similarity
> <b>B.</b> Broder (1997): the probability that two sets have the same minimum under a random hash equals their Jaccard similarity.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Exact, near, and sub-document

::: cards grid3
### [c] Exact
Hash URLs, documents or lines; keep one per hash. Cheap and lossless.

### [a] Near-duplicate
Shingle → MinHash → LSH bands → candidate pairs → cluster → keep one (Broder; Lee et al.).

### [e] Sub-document
Remove repeated lines (Llama 3, CCNet) or long repeated substrings (suffix arrays, Lee et al.).
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Settings used in practice

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Pipeline</th><th>Near-duplicate method</th><th>Other dedup</th></tr>
  <tr><td>Gopher / MassiveText</td><td>MinHash, 13-gram Jaccard &gt; 0.8</td><td>exact documents; test-set filtering</td></tr>
  <tr><td>RefinedWeb</td><td>MinHash 5-grams, 450 bands × 20</td><td>exact substring; URL dedup across dumps</td></tr>
  <tr><td>FineWeb</td><td>MinHash 5-grams, 14 bands × 8, per snapshot</td><td>(C4-style repeated-line rules among its filters)</td></tr>
  <tr><td>Llama 3</td><td>global MinHash</td><td>URL-level (keep latest); lines seen &gt; 6 times per 30M-doc bucket</td></tr>
  <tr><td>Google crawl (2007)</td><td>64-bit simhash, ≤ 3 bits differ</td><td>—</td></tr>
</table></div>

::: deep FineWeb's surprise
Deduplicating all snapshots against each other removed up to 90% of the oldest snapshots, and the data that survived was worse than what was removed (more ads and keyword lists). Deduplicating each snapshot independently gave 20T tokens that matched RefinedWeb.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why deduplication helps

::: cards grid2
### [a] Less memorisation
Lee et al.: deduplicated models emit memorised text 10× less often.

### [e] Better use of compute
Same or better accuracy in fewer training steps.

### [b] Cleaner evaluation
Train-test overlap affected over 4% of some validation sets before dedup.

### [c] Scales
MinHash + LSH is linear in the number of documents.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Deduplication only removes identical files."
> Most removed data are near-duplicates and repeated passages, found with MinHash, simhash or suffix arrays.
:::

::: reveal myth
? "More aggressive dedup is always better."
> FineWeb found global cross-snapshot dedup hurt; settings must be validated by ablation.
:::

::: reveal myth
? "Duplicates are harmless extra epochs."
> Heavily repeated text drives memorisation and verbatim regurgitation.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? b = 20 bands, r = 5 rows. Approximate similarity threshold of the S-curve?
- [ ] 0.20
- [x] 0.55
- [ ] 0.80
- [ ] 0.95
> (1/20)^(1/5) ≈ <b>0.55</b>.
:::

::: reveal
? Why band MinHash signatures instead of comparing them directly?
> Comparing all pairs is quadratic; banding puts likely-similar documents in the same bucket so only those pairs are compared.
:::

::: reveal
? Name three levels of deduplication in Llama 3's pipeline.
> URL-level, document-level (MinHash) and line-level.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Deduplicate at every level: hashes for exact copies, MinHash + LSH banding (P = 1 − (1 − sʳ)ᵇ) for near-duplicates, and line or substring removal for repeated pieces.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>The web is full of copies, from mirrored pages to licences and spam, and training on them wastes compute and causes memorisation. Exact duplicates are removed by hashing URLs, documents or lines. Near-duplicates are found by representing each document as a set of word n-grams and estimating Jaccard similarity with MinHash, which keeps the minimum of many random hashes. Locality-sensitive hashing splits signatures into bands so only documents sharing a band are compared; the probability of becoming a candidate follows an S-curve set by the number of bands and rows. Deduplicated models memorise far less.</p></div>
    <div class="recap"><div><span><b>Problem:</b> massive exact and near duplication.</span></div><div><span><b>Core idea:</b> hashes; MinHash + LSH; line/substring dedup.</span></div><div><span><b>Tune:</b> threshold ≈ (1/b)^(1/r); ablate settings.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pretraining-data/05_minhash_lsh.ipynb" target="_blank" rel="noopener">05 · Near-duplicate detection with MinHash and LSH</a> <span style="color:var(--faint)">· 40 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/pretraining-data/05_minhash_lsh.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../08-pii-and-safety/index.html">08 · PII and safety filtering →</a> · Previous: <a href="../06-quality-filtering/index.html">← 06</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
