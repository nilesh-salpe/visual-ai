---
title: Text Extraction
body:
  data-deck: Text extraction
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
  - 'raw HTML :: WARC record :: f'
  - 'strip scripts/styles :: no code as text :: c'
  - 'split blocks :: p, div, li, h1… :: a'
  - 'keep prose blocks :: link density, length :: e'
  - 'language ID :: route by language :: b'
  caption: 'FineWeb: extracting from WARC with trafilatura beat Common Crawl''s WET text.'
example:
  title: 'Worked example: one blog page'
  setup: 'Notebook 03''s page: a title, a navigation bar, two article paragraphs, share buttons, a cookie notice and a footer.'
  steps:
  - 'Raw HTML: 835 characters. Naive tag stripping: 488 characters, including the CSS rule, the script''s string, "Home | Blog | About | Log in", "Tweet Share" and
    the cookie notice.'
  - 'Block view: the navigation bar has link density above 0.6 (most of its text is link text); the paragraphs have 0.'
  - 'Keeping blocks with link density < 0.3, ≥ 8 words and no boilerplate phrase leaves the headline and two paragraphs: <b>292 characters</b>.'
  - At web scale, the same menu text would otherwise appear on every page of the site, creating massive duplication.
  result: Good extraction removes most characters of a page and almost none of its content.
traps:
  tricks:
  - 'Link density. :: Characters inside &lt;a&gt; ÷ all characters; menus are near 1.'
  - 'Prefer WARC + extractor. :: Over WET text (FineWeb ablation).'
  - 'Language ID on extracted text. :: Boilerplate in another language confuses it.'
  traps:
  - 'Stripping tags with regex alone. :: Scripts and styles leak in as "text".'
  - 'Dropping code and math blocks. :: Generic extractors can destroy them; Llama 3 built domain-specific extraction.'
  - 'Over-aggressive removal. :: Short legitimate paragraphs (captions, lists) can be lost.'
papers:
- trafilatura
- fineweb
- fasttext_lid
- llama3
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Pretraining Data · 05</div>
    <h1>Text extraction</h1>
    <p class="sub">Turning raw HTML into the main text of a page: removing scripts, menus, buttons and cookie banners, and identifying the language, before any quality filtering.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>A web page is mostly markup and boilerplate. Naive tag stripping keeps navigation, footers, share buttons and consent banners, repeated on every page of a site.</div>
      <div class="c"><b>Core idea</b>Remove <b>non-content markup</b> (scripts, styles), split the page into <b>blocks</b>, and keep blocks that look like prose: low <b>link density</b>, enough words, no boilerplate phrases. Libraries such as <b>trafilatura</b> do this robustly. Then run <b>language identification</b> (for example fastText's 176-language model).</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Which blocks are content?

The page from notebook 03, split into blocks. Move the thresholds and watch which blocks are kept (teal) or dropped (grey).
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">max link density <input type="range" id="xL" min="0.05" max="1" step="0.05" value="0.3"> <output id="xLo"></output></label><label class="ctl">min words <input type="range" id="xW" min="1" max="20" step="1" value="8"> <output id="xWo"></output></label></div>
  <div id="xList" style="margin-top:12px;display:grid;gap:6px"></div>
  <p class="readout" id="xOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why naive extraction fails

::: cards grid3
### [d] Leaked code
Script and style contents appear as text if not removed first.

### [b] Boilerplate repeated
Menus, footers and banners repeat on every page of a site: huge duplicate n-gram counts.

### [c] Lost structure
Tables, lists, code and math need special handling to stay readable.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Which block is boilerplate?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? A block reads "Home | Blog | About | Log in", and every word is a link. Its link density is close to…
- [ ] 0
- [ ] 0.25
- [x] 1
- [ ] undefined
> <b>C.</b> Nearly all its characters are inside &lt;a&gt; tags. Prose paragraphs usually have link density near 0.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Strip, split, score

::: cards grid3
### [c] Strip
Remove &lt;script&gt;, &lt;style&gt;, comments and hidden elements.

### [a] Split
Break into blocks at block-level tags; compute words, link density, position, punctuation.

### [e] Score and keep
Keep prose-like blocks; extractors like jusText and trafilatura combine many such cues with rules or models.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## What the reference pipelines chose

<div class="visual scroll-x"><table class="tbl">
  <tr><th>Dataset</th><th>Extraction</th><th>Language ID</th></tr>
  <tr><td>C4, CCNet</td><td>Common Crawl WET text</td><td>langdetect (C4, English ≥ 0.99); fastText (CCNet)</td></tr>
  <tr><td>RefinedWeb</td><td>WARC + trafilatura</td><td>fastText</td></tr>
  <tr><td>FineWeb</td><td>WARC + trafilatura (WET kept too much boilerplate)</td><td>fastText</td></tr>
  <tr><td>Llama 3</td><td>custom HTML parser; special handling for math and code</td><td>fastText-based, 176 languages</td></tr>
</table></div>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why good extraction pays off

::: cards grid2
### [a] Cleaner tokens
Less boilerplate means more of the token budget goes to content.

### [e] Fewer duplicates
Site-wide menus and footers are the most repeated text on the web.

### [b] Measurable
FineWeb's ablations showed better downstream scores with trafilatura on WARC than with WET.

### [c] Enables later filters
Quality rules and classifiers work far better on clean main text.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Extraction is a solved preprocessing detail."
> It changes downstream benchmark scores measurably and needs special cases for code, math and tables.
:::

::: reveal myth
? "WET files are good enough."
> They are a fine start but keep much more boilerplate than modern extractors.
:::

::: reveal myth
? "Language ID is trivial."
> Short, mixed or boilerplate-heavy text is easily misidentified; run it on extracted text.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? What does link density measure?
- [ ] Number of links
- [x] Fraction of characters inside links
- [ ] Links per word
- [ ] Outgoing links per page
> <b>Fraction of a block's characters inside &lt;a&gt; tags.</b>
:::

::: reveal
? Why remove scripts before stripping tags?
> Script contents (and strings inside them, even fake HTML) would otherwise survive as text.
:::

::: reveal
? What did FineWeb conclude about WET files?
> They retained too much boilerplate and menu text; extracting from WARC with trafilatura worked better.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Text extraction strips markup, splits pages into blocks and keeps prose-like ones (low link density, enough words), then identifies the language; better extraction measurably improves models.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Web pages are mostly markup, scripts and boilerplate, and naive tag stripping keeps menus, buttons and cookie notices that repeat on every page of a site. Extraction first removes scripts and styles, then splits the page into blocks and keeps those that look like prose, using cues such as link density, the share of a block's text that is link text, block length and boilerplate phrases. Libraries such as trafilatura do this robustly, and FineWeb found extracting from raw WARC files beat Common Crawl's own text. A language identifier such as fastText then routes each document by language.</p></div>
    <div class="recap"><div><span><b>Problem:</b> HTML is mostly boilerplate.</span></div><div><span><b>Core idea:</b> strip → split blocks → keep prose-like blocks → language ID.</span></div><div><span><b>Evidence:</b> trafilatura on WARC > WET (FineWeb).</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pretraining-data/03_text_extraction.ipynb" target="_blank" rel="noopener">03 · From HTML to clean text</a> <span style="color:var(--faint)">· 30 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/pretraining-data/03_text_extraction.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../06-quality-filtering/index.html">06 · Quality filtering →</a> · Previous: <a href="../04-robots-and-consent/index.html">← 04</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
