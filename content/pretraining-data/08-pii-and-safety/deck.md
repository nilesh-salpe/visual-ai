---
title: PII and Safety Filtering
body:
  data-deck: PII and safety filtering
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
  - 'URL / domain :: blocklists, PII-heavy domains :: d'
  - 'regex PII :: email, IP, phone :: b'
  - 'few spans :: mask with special token :: a'
  - 'many spans :: drop document :: c'
  - 'toxicity classifier :: drop above threshold :: e'
  caption: 'Precision matters: false positives delete good data, false negatives leak PII.'
example:
  title: 'Worked example: Dolma''s PII policy'
  setup: 'Dolma (Soldaini et al., 2024) found model-based PII detectors too slow for 3T tokens and used regular expressions for three high-precision types: email
    addresses, IP addresses and phone numbers.'
  steps:
  - 'Documents with <b>5 or fewer</b> PII spans: each span is replaced with a special token such as |||EMAIL_ADDRESS|||. This affected <b>0.02%</b> of documents.'
  - 'Documents with more spans (dense PII, e.g. directories) are removed entirely: <b>0.001%</b> of documents.'
  - In ablations, masking versus removal made no measurable difference to model performance.
  - Llama 3 additionally removed whole domains with high volumes of PII or unsafe content, and domains known to contain adult content.
  result: Simple, precise rules applied at scale remove most obvious PII at almost no cost in data.
traps:
  tricks:
  - 'Mask, don''t just delete. :: Keeps the surrounding useful text.'
  - 'Filter domains first. :: Cheap and catches whole problem sites (RefinedWeb: 4.6M-domain blocklist).'
  - 'Measure removal rates. :: Report what fraction each filter removes.'
  traps:
  - 'Assuming regex finds all PII. :: Names and addresses are hard; regex targets high-precision types only.'
  - 'Toxicity filters are biased. :: They can disproportionately remove dialects and minority voices (Dolma, citing prior work).'
  - 'Filtering only at training time. :: Memorisation of rare strings can still occur; dedup and evaluation for leakage also matter.'
papers:
- dolma
- llama3
- refinedweb
- lee_dedup
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Pretraining Data · 08</div>
    <h1>PII and safety filtering</h1>
    <p class="sub">Removing personal information and harmful content from training data: regex masking of emails, IP addresses and phone numbers, domain blocklists, toxicity classifiers, and their trade-offs.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Web text contains people's emails, phone numbers and addresses, plus adult, violent and hateful content. Models can memorise and reproduce such text.</div>
      <div class="c"><b>Core idea</b>Use cheap, high-precision tools at scale: <b>URL/domain blocklists</b> for adult and unsafe sites, <b>regular expressions</b> to <b>mask</b> PII (personally identifiable information) such as emails, IP addresses and phone numbers, and <b>classifiers</b> for toxicity, removing documents where problems are dense.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Mask the PII

Edit the text. Regexes for emails, IPv4 addresses and phone numbers mark spans; with 5 or fewer spans they are masked (Dolma's rule), otherwise the whole document is dropped.
{: .lede}

<div class="visual">
  <textarea id="pTxt" rows="5" style="width:100%;font:13px/1.5 'JetBrains Mono',monospace;padding:10px;border-radius:10px;border:1px solid var(--line);background:var(--panel);color:var(--ink)">For help with the conference, email jane.doe@example.com or call +1 415-555-0132. The registration server at 192.168.10.24 is down until Friday. Slides from last year are on the website.</textarea>
  <div id="pOut" style="margin-top:10px;padding:12px;border-radius:10px;background:var(--panel-2);font:13px/1.6 'JetBrains Mono',monospace"></div>
  <p class="readout" id="pMsg"></p>
</div>
<p class="caption">Illustrative patterns, simpler than production ones. All example values are fictional.</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why this is hard at scale

::: cards grid3
### [d] Volume
Model-based PII detectors are too slow for trillions of tokens (Dolma).

### [b] Ambiguity
A number may be a phone, a product code or a date; a name may be public or private.

### [c] Definitions
There is no single definition of toxicity or quality; annotators and tools disagree.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Mask or drop?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? A page is a staff directory with 200 email addresses. Under Dolma's rule, what happens?
- [ ] Each email is masked
- [x] The document is removed
- [ ] Nothing: emails are public
- [ ] Only the first 5 are masked
> <b>B.</b> More than 5 PII spans means the document is removed. Pages with a few spans keep their text with the spans masked.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Layers of filtering

::: cards grid3
### [d] Domain level
Blocklists of adult, gambling and malicious domains; drop domains dense in PII or unsafe content (RefinedWeb, Llama 3).

### [b] Span level
Regex-detect high-precision PII (emails, IPs, phones) and replace with typed placeholder tokens.

### [a] Document level
Classifiers for toxicity and adult content; remove documents above a threshold or with dense PII.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## What reference pipelines do

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Pipeline</th><th>Safety / PII measures</th></tr>
  <tr><td>C4</td><td>drop pages containing words from a bad-words list</td></tr>
  <tr><td>RefinedWeb</td><td>URL filtering: aggregated blocklist of 4.6M domains plus a URL word score</td></tr>
  <tr><td>Dolma</td><td>regex PII masking (≤ 5 spans) or removal; fastText toxicity classifiers</td></tr>
  <tr><td>Llama 3</td><td>remove PII-heavy, unsafe and adult domains; "dirty word" counting for adult pages missed by blocklists</td></tr>
</table></div>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why layered, simple filters work

::: cards grid2
### [a] Precision first
Regex for well-structured PII rarely deletes good text.

### [e] Cheap to run
Domain lists and regexes cost almost nothing per document.

### [b] Small data loss
Dolma's PII policy touched only 0.02% (masked) and 0.001% (removed) of documents.

### [d] Not sufficient alone
Dedup reduces memorisation; post-training and output filters add further safeguards.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Removing PII from training data makes models private."
> It reduces exposure, but unstructured PII (names, addresses in prose) is hard to detect; memorisation evaluation is still needed.
:::

::: reveal myth
? "Toxicity filters only remove bad content."
> They also remove some benign text, disproportionately from some groups; thresholds involve trade-offs.
:::

::: reveal myth
? "Masking PII hurts model quality."
> Dolma found no measurable effect of masking versus removal on performance.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Which three PII types did Dolma target with regexes?
- [ ] names, addresses, emails
- [x] emails, IP addresses, phone numbers
- [ ] credit cards, names, dates
- [ ] URLs, emails, usernames
> <b>Email addresses, IP addresses and phone numbers.</b>
:::

::: reveal
? Why mask PII spans instead of deleting the document?
> The rest of the document is usually useful text; masking keeps it while removing the personal data.
:::

::: reveal
? What is a risk of toxicity classifiers in data filtering?
> They can remove benign text from dialects or minority groups disproportionately, biasing the corpus.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Remove unsafe and personal data in layers: domain blocklists, regex masking of high-precision PII (emails, IPs, phones), dropping PII-dense documents, and toxicity classifiers, at tiny data cost.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Web text contains personal information and harmful content that models can memorise. Pipelines filter in layers. Whole domains are removed with blocklists of adult or malicious sites and, for Llama 3, domains dense in personal data. Regular expressions find high-precision personal data such as email addresses, IP addresses and phone numbers; Dolma masks them with placeholder tokens when a document has five or fewer and removes the document otherwise, touching only a few hundredths of a percent of documents. Toxicity classifiers remove the most harmful text, though they can be biased against some groups.</p></div>
    <div class="recap"><div><span><b>Problem:</b> PII and harmful content in web text.</span></div><div><span><b>Core idea:</b> domains → regex masking → document drop → classifiers.</span></div><div><span><b>Numbers:</b> Dolma: masked 0.02%, removed 0.001%.</span></div></div>
    <p class="start-hint">Next: <a href="../09-mixtures-and-repetition/index.html">09 · Data mixtures and repetition →</a> · Previous: <a href="../07-deduplication/index.html">← 07</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
