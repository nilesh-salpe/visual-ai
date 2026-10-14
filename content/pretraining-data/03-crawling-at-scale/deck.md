---
title: Crawling at Scale
body:
  data-deck: Crawling at scale
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
  - 'budget :: pages/s × days :: f'
  - 'URL-seen at scale :: disk-backed, batched :: c'
  - 'per-site budget :: resist spam and traps :: d'
  - 'content fingerprints :: simhash / MinHash :: a'
  - 'revisit policy :: freshness :: e'
  caption: 'IRLbot: one server, 6.3 billion pages in 41 days.'
example:
  title: 'Worked example: sizing a monthly crawl'
  setup: Common Crawl adds about 3–5 billion new pages a month. IRLbot sustained 1,789 pages/s on a single server.
  steps:
  - 3 billion pages in 30 days = 3 × 10⁹ ÷ (30 × 86,400 s) ≈ <b>1,157 pages/s</b> on average.
  - That is within a single IRLbot-class server (1,789 pages/s), or a modest cluster with headroom.
  - With 0.5 s downloads and a 10× politeness delay (0.18 pages/s per host), 1,157 pages/s needs at least <b>6,366 hosts</b> active at once.
  - 'IRLbot: 6.3 billion valid HTML pages (7.6 billion connection requests) in 41 days at an average 319 Mb/s.'
  result: Bandwidth is rarely the limit; scheduling across millions of hosts, URL bookkeeping and spam resistance are.
traps:
  tricks:
  - 'pages/s = pages ÷ seconds. :: 1B pages a month ≈ 386 pages/s.'
  - 'Per-site budgets. :: Limit pages per domain by its reputation (IRLbot''s budgets).'
  - 'Simhash for near-duplicates. :: Google: 64-bit fingerprints, ≤ 3 differing bits, 8B pages.'
  traps:
  - 'Infinite URL spaces. :: Calendars, session IDs and faceted search generate endless URLs.'
  - 'Spam farms. :: Highly-branching link spam can absorb most of a breadth-first crawl.'
  - 'Stale pages. :: Without revisits, the crawl ages; with naive revisits, it wastes budget on static pages.'
papers:
- irlbot
- manku07
- commoncrawl
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Pretraining Data · 03</div>
    <h1>Crawling at scale</h1>
    <p class="sub">What changes when a crawl reaches billions of pages: throughput budgets, URL uniqueness on disk, spam farms and crawler traps, near-duplicate detection, and keeping pages fresh.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>At billions of pages, the URL-seen set no longer fits in memory, infinite link spaces and spam sites can swallow the crawl, and pages change after you fetch them.</div>
      <div class="c"><b>Core idea</b>Budget the crawl: <b>pages/s × time</b> sets the size. Store the seen-set on disk with batched checks; give each site a <b>crawl budget</b> so spam farms and traps cannot dominate; fingerprint content to drop <b>near-duplicates</b>; and <b>revisit</b> pages by how often they change.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## How big a crawl can you afford?

Pick a target size and a throughput. The readout gives the crawl duration and how many hosts must be active at once to stay polite.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">pages <input type="range" id="zN" min="8" max="11.5" step="0.1" value="9.5"> <output id="zNo"></output></label>
    <label class="ctl">pages/s per machine <input type="range" id="zR" min="100" max="3000" step="50" value="1800"> <output id="zRo"></output></label>
    <label class="ctl">machines <input type="range" id="zM" min="1" max="200" step="1" value="10"> <output id="zMo"></output></label>
  </div>
  <div class="grid3" style="margin-top:12px">
    <div class="stat"><div class="num" id="zD"></div><div class="lbl">days</div></div>
    <div class="stat"><div class="num" id="zH"></div><div class="lbl">hosts active at once (0.5 s downloads, k = 10)</div></div>
    <div class="stat"><div class="num" id="zB"></div><div class="lbl">bandwidth (at IRLbot's ≈ 22 KB/page)</div></div>
  </div>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## What breaks past a billion pages

::: cards grid3
### [d] Memory
A seen-set of tens of billions of URLs does not fit in RAM; random disk lookups are too slow.

### [b] Adversarial web
Spam farms, auto-generated pages and infinite calendars create unlimited URLs.

### [c] Change
Pages are edited and deleted; a crawl is a snapshot that decays.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What stops spam from taking over?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? A spam farm links to millions of auto-generated pages. What keeps it from consuming the crawl?
- [ ] A faster network
- [x] A per-site crawl budget tied to the site's reputation
- [ ] Following every link breadth-first
- [ ] A bigger seen-set
> <b>B.</b> IRLbot assigned budgets per domain based on incoming links from other sites, so low-reputation spam gets few pages however many links it has.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Four scaling techniques

::: cards grid2
### [c] Disk-backed URL checks
Batch new URLs and check them against a sorted on-disk set sequentially (IRLbot), instead of random lookups.

### [d] Budgets
Pages per site in proportion to reputation; caps on URL depth and parameters to escape traps.

### [a] Content fingerprints
Simhash or MinHash detects near-identical pages under different URLs.

### [e] Revisit scheduling
Re-crawl frequently-changing pages more often; Common Crawl publishes new snapshots regularly.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Real crawler numbers

<div class="visual scroll-x"><table class="tbl">
  <tr><th>System</th><th>Scale</th><th>Notes</th></tr>
  <tr><td>Google prototype (1998)</td><td>24M pages; 100+ pages/s</td><td>4 crawlers × ~300 connections, DNS cache</td></tr>
  <tr><td>Mercator (≈ 2001)</td><td>production crawls</td><td>per-host back-end queues; wait 10× download time</td></tr>
  <tr><td>Google near-dup (2007)</td><td>8B pages</td><td>64-bit simhash, near-duplicate if ≤ 3 bits differ</td></tr>
  <tr><td>IRLbot (2008)</td><td>6.3B pages in 41 days</td><td>single server; 1,789 pages/s; spam-resistant budgets</td></tr>
  <tr><td>Common Crawl (today)</td><td>300B+ pages total</td><td>3–5B new pages a month; CCBot obeys robots.txt and Crawl-delay</td></tr>
</table></div>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why these techniques work

::: cards grid2
### [a] Sequential beats random
Batched, sorted disk access turns billions of random lookups into fast scans.

### [e] Reputation resists spam
Spammers can create pages cheaply but not links from many independent reputable sites.

### [b] Fingerprints are tiny
64 bits per page make near-duplicate checks over billions of pages feasible.

### [c] Not all pages change
Spending revisits where change is likely keeps the snapshot fresh at the same cost.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Crawling the web is mainly a bandwidth problem."
> IRLbot crawled 6.3 billion pages from one server; the hard parts were URL uniqueness, spam and politeness.
:::

::: reveal myth
? "A crawl captures "the web"."
> It captures a budgeted, biased sample at one time; much of the web is behind logins or generated on demand.
:::

::: reveal myth
? "Duplicate URLs are the only duplicates."
> The same content appears under many URLs and sites; content fingerprints are needed too.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? 1 billion pages in 10 days needs roughly how many pages/s?
- [ ] 116
- [x] 1,157
- [ ] 11,574
- [ ] 100,000
> 10⁹ ÷ 864,000 s ≈ <b>1,157</b>.
:::

::: reveal
? What is a crawler trap?
> A site structure that generates unlimited URLs (calendars, session IDs, faceted filters), which can absorb the crawl without new content.
:::

::: reveal
? Why use simhash or MinHash during crawling?
> To detect pages whose content is almost the same as one already stored, even under a different URL.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">At billions of pages the bottlenecks are bookkeeping and adversaries: disk-backed URL checks, per-site budgets, content fingerprints and revisit policies make crawls scale.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Scaling a crawler is less about bandwidth than bookkeeping. One server running IRLbot crawled 6.3 billion pages in 41 days at about 1,800 pages per second. To get there the seen-set lives on disk and is checked in sorted batches, each site gets a crawl budget tied to its reputation so spam farms and infinite calendars cannot take over, and content fingerprints such as Google's 64-bit simhash catch near-identical pages under different URLs. Since pages change, revisits are scheduled by how often they update. Common Crawl applies this at web scale, adding three to five billion pages a month.</p></div>
    <div class="recap"><div><span><b>Problem:</b> memory, spam, traps and change at billions of pages.</span></div><div><span><b>Core idea:</b> disk URL checks, budgets, fingerprints, revisits.</span></div><div><span><b>Numbers:</b> IRLbot 6.3B pages / 41 days; simhash k = 3.</span></div></div>
    <p class="start-hint">Next: <a href="../04-robots-and-consent/index.html">04 · robots.txt and consent →</a> · Previous: <a href="../02-how-a-crawler-works/index.html">← 02</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
