---
title: How a Web Crawler Works
body:
  data-deck: How a web crawler works
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
  - 'frontier :: priority + per-host queues :: f'
  - 'robots.txt :: allowed? (cached ≤ 24 h) :: d'
  - 'DNS + fetch :: download page :: c'
  - 'parse :: extract + normalise links :: a'
  - 'seen? :: URL and content fingerprints :: b'
  loop: '4 -> 0 :: add new URLs, repeat'
  caption: 'Politeness lives in the frontier: a host is offered again only after its delay has passed.'
example:
  title: 'Worked example: politeness and throughput'
  setup: Mercator waited 10× the last download time before contacting a host again. Suppose a page takes 0.5 s to download and you want 1,000 pages/s.
  steps:
  - 'One host can then be fetched at most once every 0.5 × (1 + 10) = 5.5 s: <b>0.18 pages/s per host</b>.'
  - To reach 1,000 pages/s you need at least 1,000 ÷ 0.18 ≈ <b>5,500 hosts</b> in flight at once.
  - With 0.5 s per download, 1,000 pages/s also needs about 500 concurrent connections (threads or async requests).
  - Mercator kept about 3 back-end host queues per crawling thread so threads never wait for a polite host.
  result: Politeness caps per-host speed, so throughput comes from parallelism across many hosts, not from hammering one.
traps:
  tricks:
  - 'One queue per host. :: The heap holds when each host may be contacted next.'
  - 'Normalise URLs. :: Lowercase host, drop default port and #fragment.'
  - 'Cache DNS. :: Brin & Page found DNS lookup a major bottleneck.'
  traps:
  - 'Plain FIFO frontier. :: Hits the same host back to back (notebook 01: 0 s gaps).'
  - 'Ignoring robots.txt status codes. :: 5xx means assume complete disallow.'
  - 'Re-fetching duplicates. :: Without a seen-set, link-rich sites dominate the crawl.'
papers:
- najork01
- brin_page
- rfc9309
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Pretraining Data · 02</div>
    <h1>How a web crawler works</h1>
    <p class="sub">The loop at the heart of every crawler: a frontier of URLs to fetch, politeness per host, robots.txt, fetching, link extraction and duplicate checks.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Starting from a few seed URLs, we want to download billions of pages, never twice, without overloading any website, and while honouring its rules.</div>
      <div class="c"><b>Core idea</b>Keep a <b>URL frontier</b>; repeatedly take a URL, check <b>robots.txt</b>, <b>fetch</b> it, extract and <b>normalise</b> its links, and add the unseen ones. Organise the frontier as <b>one queue per host</b> plus a heap of "next allowed contact" times, so each host is visited politely while thousands of others keep the crawler busy.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Threads, hosts and politeness

Throughput is limited by connections (threads) and by politeness (each host fetched at most once per (1 + k) × download time). Move the sliders to see which limit binds.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">connections <input type="range" id="cT" min="1" max="4" step="0.1" value="2.5"> <output id="cTo"></output></label>
    <label class="ctl">hosts in frontier <input type="range" id="cH" min="1" max="5" step="0.1" value="3"> <output id="cHo"></output></label>
    <label class="ctl">delay factor k <input type="range" id="cK" min="0" max="30" step="1" value="10"> <output id="cKo"></output></label>
  </div>
  <div id="cBars" style="margin-top:12px"></div>
  <p class="readout" id="cOut"></p>
</div>
<p class="caption">Average download time 0.5 s. Sliders are logarithmic (10¹–10⁴ connections, 10¹–10⁵ hosts).</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why a simple loop isn't enough

::: cards grid3
### [d] Impolite
A FIFO queue fetches whatever is next, often one site many times in a row, which can overload small servers.

### [b] Duplicates
The same page appears under many URLs (case, ports, fragments, tracking parameters).

### [c] Slow per host
Network round trips dominate; a single connection would crawl a few pages per second.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Where does politeness belong?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Which component should guarantee that a host is not contacted too often?
- [ ] The HTML parser
- [x] The URL frontier (per-host queues with next-allowed times)
- [ ] The DNS resolver
- [ ] The storage layer
> <b>B.</b> The frontier decides what is fetched next, so it is where per-host delays are enforced (Mercator's back-end queues and heap).
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## The crawl loop

::: cards grid3
### [a] Frontier
Front-end queues by priority; back-end FIFO queues, one per host; a heap of next-contact times (Najork & Heydon).

### [c] Fetch
Resolve DNS (cached), check robots.txt (cached ≤ 24 h), download with an identifying User-Agent.

### [e] Process
Extract links, normalise, drop already-seen URLs and pages whose content fingerprint was seen.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Inside Mercator's frontier

::: cards grid4
### [f] 1 · prioritise
New URLs go to front-end FIFO queues by priority.

### [a] 2 · route by host
A router moves URLs into back-end queues, each holding URLs of a single host.

### [c] 3 · wait politely
A heap orders back-end queues by the time their host may next be contacted.

### [e] 4 · fetch and reschedule
After a download, reinsert the queue at now + 10 × download time.
:::

::: deep The original Google crawler
Brin & Page (1998): a URL server sends lists of URLs to several crawlers; each keeps about 300 connections open, and four crawlers together reached over 100 pages per second, with a DNS cache per crawler.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why this design works

::: cards grid2
### [a] Polite by construction
A host cannot be offered again before its delay expires, whatever the link structure.

### [e] Fast in aggregate
Thousands of hosts in flight hide each host's waiting time.

### [b] Priorities
Front-end queues let important or fresh pages go first.

### [c] No wasted fetches
Normalisation and seen-sets keep each page to one download.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "A crawler just follows links recursively."
> Scheduling (priorities, per-host politeness, revisits) is the hard part, not following links.
:::

::: reveal myth
? "Faster crawling means more requests per site."
> Large crawlers get faster by covering more sites in parallel, not by hitting each harder.
:::

::: reveal myth
? "robots.txt is checked once per crawl."
> It is cached (RFC 9309: no more than 24 hours) and re-fetched, and its status code matters.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Download time 1 s, delay factor 10. Maximum fetch rate from one host?
- [ ] 10/s
- [ ] 1/s
- [x] 1 per 11 s
- [ ] 1 per 10 s
> Wait 10 × 1 s after a 1 s download: <b>one page every 11 s</b>.
:::

::: reveal
? What does URL normalisation do and why?
> Maps equivalent URLs (case, default ports, fragments) to one form so the same page is not fetched repeatedly.
:::

::: reveal
? How does a crawler stay fast while being polite?
> Keeps many hosts in flight with many connections, so per-host delays overlap with work on other hosts.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">A crawler loops frontier → robots check → fetch → extract and normalise links → seen-set, with per-host queues and next-contact times that keep it polite while thousands of hosts keep it fast.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>A web crawler starts from seed URLs and repeats a loop: take the next URL from the frontier, check the site's robots.txt, resolve the host and download the page, extract its links, normalise them and add any it has not seen. Politeness is built into the frontier: Mercator kept one queue per host and a heap of times when each host may be contacted again, waiting ten times the last download time. That caps each site at a gentle rate, so throughput comes from crawling thousands of hosts in parallel. Normalisation and fingerprints stop the same page being fetched twice.</p></div>
    <div class="recap"><div><span><b>Problem:</b> billions of pages, fetched once, politely.</span></div><div><span><b>Core idea:</b> per-host queues + heap of next-contact times.</span></div><div><span><b>Throughput:</b> many hosts × many connections.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pretraining-data/01_polite_crawler.ipynb" target="_blank" rel="noopener">01 · A polite crawler on a simulated web</a> <span style="color:var(--faint)">· 40 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/pretraining-data/01_polite_crawler.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../03-crawling-at-scale/index.html">03 · Crawling at scale →</a> · Previous: <a href="../01-where-data-comes-from/index.html">← 01</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
