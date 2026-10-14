---
title: robots.txt and Consent
body:
  data-deck: robots.txt and consent
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
  - 'fetch /robots.txt :: status code first :: c'
  - 'pick group :: your token, else * :: a'
  - 'match rules :: * and $ wildcards :: b'
  - 'longest match wins :: allow on ties :: e'
  - 'cache ≤ 24 h :: re-check later :: f'
  caption: RFC 9309 (2022) standardised a 1994 convention.
example:
  title: 'Worked example: evaluating one URL'
  setup: 'robots.txt: "User-agent: * / Disallow: /private/ / Allow: /private/public-page.html". Crawler: SomeBot. URL path: /private/public-page.html.'
  steps:
  - No group names SomeBot, so the * group applies.
  - 'Both rules match: Disallow /private/ (9 characters) and Allow /private/public-page.html (25 characters).'
  - 'The longest match wins: <b>allowed</b>. For /private/x only the Disallow matches: <b>disallowed</b>.'
  - If the server answered robots.txt with 503 instead, the crawler must assume complete disallow; with 404, everything is allowed.
  result: 'Specificity, not order, decides: the rule with the most matching characters wins.'
traps:
  tricks:
  - 'Longest match wins. :: Allow wins ties.'
  - 'A specific group replaces *. :: Rules are not inherited from the * group.'
  - 'Status codes. :: 4xx → allowed, 5xx/unreachable → disallow all.'
  traps:
  - 'First-match semantics. :: Order of lines does not matter in RFC 9309.'
  - 'Treating robots.txt as security. :: It is advisory and publicly lists the paths.'
  - 'Assuming Crawl-delay is standard. :: It is a non-standard extension (CCBot obeys it, others may not).'
papers:
- rfc9309
- consent
- commoncrawl
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Pretraining Data · 04</div>
    <h1>robots.txt and consent</h1>
    <p class="sub">How websites tell crawlers what they may fetch, the exact matching rules standardised in RFC 9309, what to do when the file is missing or failing, and the fast-growing restrictions on AI crawlers.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Site owners need a simple way to say "don't crawl this", and crawlers need unambiguous rules. Increasingly, sites also want to opt out of AI training specifically.</div>
      <div class="c"><b>Core idea</b>A site serves <b>/robots.txt</b> with <b>user-agent groups</b> of <b>allow/disallow</b> rules. A crawler picks the group matching its product token (else <code>*</code>), and the <b>longest matching rule wins</b> (allow on ties). 4xx → crawl allowed; 5xx → assume disallow. Cache for at most 24 hours.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Test a robots.txt

Edit the file, the crawler name and the path. The tester follows RFC 9309: group selection, `*` and `$`, longest match, allow on ties. Notebook 02 implements the same logic.
{: .lede}

<div class="visual">
  <textarea id="rTxt" rows="9" style="width:100%;font:13px/1.45 'JetBrains Mono',monospace;padding:10px;border-radius:10px;border:1px solid var(--line);background:var(--panel);color:var(--ink)"></textarea>
  <div class="controls"><label class="ctl">crawler <input id="rUA" type="text" value="SomeBot" style="width:120px"></label><label class="ctl">path <input id="rP" type="text" value="/private/public-page.html" style="width:220px"></label></div>
  <p class="readout" id="rOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why rules need to be precise

::: cards grid3
### [d] Ambiguity
Before RFC 9309, crawlers disagreed on first-match vs longest-match and on wildcards.

### [b] Failure modes
What should a crawler do when robots.txt returns 404, 403 or 500? Different answers mean very different behaviour.

### [c] New purposes
A file written for search indexing now also governs collection for AI training.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Which rule applies?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Rules "Disallow: /docs" and "Allow: /docs/public" in the * group. Is /docs/public/a.html allowed?
- [ ] No: Disallow comes first
- [x] Yes: the Allow match is longer
- [ ] No: Disallow always wins
- [ ] Only for search engines
> <b>B.</b> Both match; /docs/public (12 characters) is longer than /docs (5), so Allow wins. Line order is irrelevant.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## The rules in RFC 9309

::: cards grid2
### [a] Groups
One or more user-agent lines followed by rules. Match your product token case-insensitively; merge duplicate groups; fall back to *.

### [c] Matching
Paths match from the first character; * matches any sequence, $ anchors the end. Most octets wins; allow beats an equivalent disallow.

### [d] Errors
4xx: "unavailable", may crawl anything. 5xx or network failure: "unreachable", assume complete disallow.

### [e] Limits
Follow ≥ 5 redirects; cache ≤ 24 hours; parse at least 500 KiB.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Consent is shifting fast

::: cards grid3
### [d] robots.txt restrictions
Longpre et al. (2024): in one year (2023-04 to 2024-04), about 5%+ of all tokens in C4, RefinedWeb and Dolma, and about 25%+ of tokens from the most critical domains, became restricted by robots.txt.

### [b] Terms of service
A full 45% of C4 is now restricted by terms-of-service crawling clauses.

### [c] Identifying crawlers
Crawlers announce a product token (e.g. CCBot) and can be blocked individually; Common Crawl documents how to block or slow CCBot.
:::

::: deep Why this matters for data
If honoured, these restrictions bias the open web corpus toward sites that do not opt out, affecting its diversity and freshness, as the authors warn.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why the protocol works (and its limits)

::: cards grid2
### [a] Simple and universal
A text file at a fixed path that any crawler can fetch and parse.

### [e] Deterministic
Longest match and explicit tie-breaking give one answer per URL.

### [b] Fails safe on errors
Server errors mean "assume disallow", protecting struggling sites.

### [d] Voluntary
It is not access control: compliance depends on the crawler, and paths are public.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "The first matching rule applies."
> RFC 9309 uses the most specific (longest) match; order does not matter.
:::

::: reveal myth
? "A missing robots.txt means "do not crawl"."
> A 4xx response means the crawler may access everything; only server errors mean disallow.
:::

::: reveal myth
? "robots.txt protects private pages."
> It is advisory and lists the paths publicly; use authentication for real protection.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? robots.txt returns HTTP 503. What should a crawler do?
- [ ] Crawl everything
- [x] Assume complete disallow
- [ ] Ignore it and use the * group
- [ ] Retry once, then crawl
> <b>Assume complete disallow</b> (unreachable).
:::

::: reveal
? For how long may a crawler cache robots.txt?
> It SHOULD NOT use a cached copy for more than 24 hours, unless the file is unreachable.
:::

::: reveal
? Group "User-agent: ExampleBot" has no rule for /private/, while the * group disallows it. Can ExampleBot fetch /private/?
> Yes: the matching ExampleBot group replaces the * group entirely.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">robots.txt groups rules by crawler; the longest matching rule wins (allow on ties), 4xx means allowed and 5xx means disallow, and AI-specific opt-outs are rising fast.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Sites publish crawl rules in robots.txt as groups of allow and disallow lines for named crawlers. RFC 9309 fixes the details: a crawler uses the group naming its product token, otherwise the star group; paths match from the start with star and dollar wildcards; the longest match wins, and allow wins a tie. If fetching robots.txt gives a 4xx error the crawler may access everything, but a server error means assume everything is disallowed. Caches last at most a day. The file is voluntary, and audits show restrictions aimed at AI crawlers grew sharply, about five percent of C4 tokens in one year.</p></div>
    <div class="recap"><div><span><b>Problem:</b> unambiguous, site-controlled crawl rules.</span></div><div><span><b>Core idea:</b> groups; longest match; allow on ties; status codes.</span></div><div><span><b>Trend:</b> ~5%+ of C4 tokens newly restricted in a year.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pretraining-data/02_robots_txt.ipynb" target="_blank" rel="noopener">02 · A robots.txt parser following RFC 9309</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/pretraining-data/02_robots_txt.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../05-text-extraction/index.html">05 · Text extraction →</a> · Previous: <a href="../03-crawling-at-scale/index.html">← 03</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
