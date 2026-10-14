"""Web crawling & pretraining data exercise notebooks (pure Python + NumPy; the crawler runs on a simulated in-memory web)."""

NBS = []

# ------------------------------------------------------------------ 01
NBS.append(dict(
    slug='01_polite_crawler', title='01 · A polite crawler on a simulated web', deck='pretraining-data/02-how-a-crawler-works/', deck_name='How a web crawler works', minutes=40,
    goals='URL normalisation, a URL-seen set, and a frontier that enforces per-host politeness with a heap of "next allowed time" (the Mercator design), run on a simulated web so no real site is contacted.',
    setup=r'''
import heapq, random
from urllib.parse import urlsplit, urlunsplit

def make_web(n_hosts=20, pages_per_host=30, links=6, seed=0):
    """A simulated web: {url: [outlinks]} plus a per-host download time in seconds. No network access."""
    r = random.Random(seed); hosts = [f"site{h}.example" for h in range(n_hosts)]
    urls = [f"http://{h}/p{i}" for h in hosts for i in range(pages_per_host)]
    web = {}
    for u in urls:
        host = urlsplit(u).netloc
        same = [x for x in urls if urlsplit(x).netloc == host]
        out = r.sample(same, links // 2) + r.sample(urls, links - links // 2)
        # sprinkle in un-normalised variants that should map to the same page
        web[u] = [o if r.random() < 0.7 else o.replace("http://", "HTTP://").replace(".example", ".example:80") + "#frag" for o in out]
    speed = {h: r.uniform(0.05, 0.5) for h in hosts}
    return web, speed

WEB, SPEED = make_web()
SEEDS = ["http://site0.example/p0", "http://site7.example/p3"]
''',
    tasks=[
        dict(fn='normalize', title='Normalise URLs', md=r'''
            Many strings name the same page. Implement `normalize(url)`: lowercase the scheme and host, drop the default port (`:80` for http, `:443` for https), drop the `#fragment`, and use `/` for an empty path.
            Without this, a crawler fetches the same page many times.''',
             starter=r'''
            def normalize(url):
                # TODO: use urlsplit / urlunsplit
                raise NotImplementedError''',
             test=r'''
            def _test_normalize(f):
                assert f("HTTP://Site1.Example:80/p3#top") == "http://site1.example/p3"
                assert f("https://a.example:443") == "https://a.example/"
                assert f("http://a.example:8080/x?q=1") == "http://a.example:8080/x?q=1", "keep non-default ports and queries"''',
             solution=r'''
            def normalize_solution(url):
                p = urlsplit(url); scheme = p.scheme.lower(); host = (p.hostname or "").lower()
                port = p.port
                netloc = host if port is None or (scheme, port) in (("http", 80), ("https", 443)) else f"{host}:{port}"
                return urlunsplit((scheme, netloc, p.path or "/", p.query, ""))'''),
        dict(fn='PoliteFrontier', title='A frontier with per-host politeness', md=r'''
            Implement a class with `add(url, now)` and `next(now)`:
            * URLs are grouped into one FIFO queue **per host**.
            * A heap holds `(time_host_may_be_contacted, host)`.
            * `next(now)` pops the host with the earliest allowed time; if that time is in the future it returns `(None, wait_until)`; otherwise it returns `(url, host)` from that host's queue. The host goes back on the heap only when `done(host, now, download_time)` is called, with allowed time `now + delay_factor × download_time` (Mercator waited **10×** the last download time).''',
             starter=r'''
            class PoliteFrontier:
                def __init__(self, delay_factor=10.0):
                    self.delay_factor = delay_factor
                    self.queues, self.heap, self.active, self.next_ok = {}, [], set(), {}
                def add(self, url, now=0.0):
                    # TODO: append to the host's queue; if the host is idle (not on the heap, not in flight),
                    # push (max(now, next_ok.get(host, 0)), host) so an idle host still respects its last delay
                    raise NotImplementedError
                def next(self, now):
                    # TODO
                    raise NotImplementedError
                def done(self, host, now, download_time):
                    # TODO: record next_ok[host] = now + delay_factor * download_time; if the host still has URLs, push it back at that time
                    raise NotImplementedError''',
             test=r'''
            def _test_PoliteFrontier(cls):
                fr = cls(delay_factor=10.0)
                for u in ["http://a.example/1", "http://a.example/2", "http://b.example/1"]:
                    fr.add(u, 0.0)
                u1, h1 = fr.next(0.0); u2, h2 = fr.next(0.0)
                assert {h1, h2} == {"a.example", "b.example"}, "two different hosts can be fetched at once"
                got, wait = fr.next(0.0)
                assert got is None, "a.example is in flight: no third URL until done() is called"
                fr.done("a.example", 1.0, 0.2)
                got, wait = fr.next(1.5)
                assert got is None and abs(wait - 3.0) < 1e-9, "next contact allowed at 1.0 + 10 × 0.2 = 3.0"
                got, host = fr.next(3.0)
                assert got == "http://a.example/2" and host == "a.example"''',
             solution=r'''
            class PoliteFrontier_solution:
                def __init__(self, delay_factor=10.0):
                    self.delay_factor = delay_factor
                    self.queues, self.heap, self.active, self.next_ok = {}, [], set(), {}
                def add(self, url, now=0.0):
                    host = urlsplit(url).netloc
                    q = self.queues.setdefault(host, [])
                    if not q and host not in self.active:
                        heapq.heappush(self.heap, (max(now, self.next_ok.get(host, 0.0)), host)); self.active.add(host)
                    q.append(url)
                def next(self, now):
                    while self.heap:
                        t, host = self.heap[0]
                        if t > now:
                            return None, t
                        heapq.heappop(self.heap)
                        if self.queues.get(host):
                            return self.queues[host].pop(0), host
                        self.active.discard(host)
                    return None, None
                def done(self, host, now, download_time):
                    self.next_ok[host] = now + self.delay_factor * download_time
                    if self.queues.get(host):
                        heapq.heappush(self.heap, (self.next_ok[host], host))
                    else:
                        self.active.discard(host)'''),
        dict(fn='crawl', title='Run the crawl', md=r'''
            Simulate a single-threaded event loop: take the next URL (or jump the clock to `wait_until`), "download" it (advance the clock by the host's `SPEED`), call `done`, normalise its outlinks and add the unseen ones. Stop after `max_pages` downloads.
            Return `(pages, elapsed_seconds, violations)`, where a violation is a fetch from a host that starts earlier than `delay_factor ×` that host's previous download time after the previous download ended. A polite crawler has 0. Use your `normalize` and `PoliteFrontier` (or the references).''',
             starter=r'''
            def crawl(max_pages=200, delay_factor=10.0, norm=None, Frontier=None):
                norm = norm or normalize; Frontier = Frontier or PoliteFrontier
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_crawl(f):
                pages, t, viol = f(200, 10.0)
                assert len(pages) == 200 and len(set(pages)) == 200, "every page fetched once (normalisation + seen set)"
                assert all("#" not in p and ":80" not in p for p in pages), "outlinks must be normalised"
                assert viol == 0, f"politeness violated {viol} times"''',
             solution=r'''
            def crawl_solution(max_pages=200, delay_factor=10.0, norm=None, Frontier=None):
                norm = norm or normalize_solution; Frontier = Frontier or PoliteFrontier_solution
                fr, seen, now, pages, last, viol = Frontier(delay_factor), set(), 0.0, [], {}, 0
                for s in SEEDS:
                    s = norm(s); seen.add(s); fr.add(s, now)
                while len(pages) < max_pages:
                    url, info = fr.next(now)
                    if url is None:
                        if info is None: break
                        now = info; continue
                    host = info
                    if host in last and now < last[host][0] + delay_factor * last[host][1] - 1e-9: viol += 1
                    now += SPEED[host]; pages.append(url); last[host] = (now, SPEED[host])
                    fr.done(host, now, SPEED[host])
                    for o in WEB.get(url, []):
                        o = norm(o)
                        if o not in seen:
                            seen.add(o); fr.add(o, now)
                return pages, now, viol'''),
    ],
    explore_md=r'''
        **What a naive FIFO crawler does to servers.** A breadth-first queue with no per-host scheduling fetches whatever comes next, often the same host back to back. Compare the smallest idle gap any host sees between two requests.''',
    explore=r'''
        def min_gap(fetches):
            # smallest idle time between the end of one request to a host and the start of the next one to the same host
            last, gap = {}, float("inf")
            for start, h in fetches:
                if h in last: gap = min(gap, start - last[h])
                last[h] = start + SPEED[h]
            return gap
        # naive FIFO: no politeness at all
        q, seen, now, log = list(SEEDS), set(SEEDS), 0.0, []
        while q and len(log) < 300:
            u = q.pop(0); h = urlsplit(u).netloc; log.append((now, h)); now += SPEED[h]
            for o in WEB[u]:
                o = normalize_solution(o)
                if o not in seen: seen.add(o); q.append(o)
        print(f"naive FIFO : 300 pages in {now:6.1f} s, smallest gap between requests to one host = {min_gap(log):.2f} s")
        fr, seen, now, log = PoliteFrontier_solution(10.0), set(), 0.0, []
        for s0 in SEEDS: seen.add(s0); fr.add(s0, 0.0)
        while len(log) < 300:
            u, info = fr.next(now)
            if u is None: now = info; continue
            log.append((now, info)); now += SPEED[info]; fr.done(info, now, SPEED[info])
            for o in WEB[u]:
                o = normalize_solution(o)
                if o not in seen: seen.add(o); fr.add(o, now)
        print(f"polite (10×): 300 pages in {now:6.1f} s, smallest gap between requests to one host = {min_gap(log):.2f} s")
        print("A real crawler hides the waiting by keeping thousands of hosts in flight across many threads.")''',
    takeaways=r'''
        * Normalise URLs and keep a seen-set, or the crawl wastes most of its budget on duplicates.
        * Politeness is enforced per host: one queue per host and a heap of next-allowed times.
        * Mercator waited 10× the last download time before contacting a host again and kept ~3× as many host queues as threads.''',
))

# ------------------------------------------------------------------ 02
NBS.append(dict(
    slug='02_robots_txt', title='02 · A robots.txt parser following RFC 9309', deck='pretraining-data/04-robots-and-consent/', deck_name='robots.txt and consent', minutes=35,
    goals='parsing robots.txt into user-agent groups, matching paths with `*` and `$`, the longest-match rule (allow wins ties), and the status-code rules for missing or failing robots.txt.',
    setup=r'''
import re
EXAMPLE = """
# example
User-agent: *
Disallow: /private/
Allow: /private/public-page.html

User-agent: ExampleBot
User-agent: OtherBot
Disallow: /tmp
Disallow: /*.pdf$
Allow: /tmp/ok

User-agent: CCBot
Disallow: /
"""
''',
    tasks=[
        dict(fn='parse_robots', title='Parse groups', md=r'''
            Return a dict `{product_token_lowercase: [(kind, path), ...]}` where kind is `'allow'` or `'disallow'`. Consecutive `user-agent` lines share the rules that follow them; a new `user-agent` line after rules starts a new group. Strip `#` comments, ignore case of field names, and ignore rules before the first user-agent line. Empty `Disallow:` lines mean "allow everything" and can be skipped.''',
             starter=r'''
            def parse_robots(text):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_parse_robots(f):
                g = f(EXAMPLE)
                assert set(g) == {"*", "examplebot", "otherbot", "ccbot"}
                assert g["examplebot"] == g["otherbot"], "two user-agent lines share one group"
                assert ("allow", "/private/public-page.html") in g["*"]
                assert g["ccbot"] == [("disallow", "/")]''',
             solution=r'''
            def parse_robots_solution(text):
                groups, current, in_rules = {}, [], False
                for line in text.splitlines():
                    line = line.split("#", 1)[0].strip()
                    if ":" not in line: continue
                    k, v = (x.strip() for x in line.split(":", 1)); k = k.lower()
                    if k == "user-agent":
                        if in_rules: current, in_rules = [], False
                        current.append(v.lower()); groups.setdefault(v.lower(), [])
                    elif k in ("allow", "disallow") and current:
                        in_rules = True
                        if v:
                            for ua in current: groups[ua].append((k, v))
                return groups'''),
        dict(fn='rule_match', title='Path patterns with * and $', md=r'''
            Return the **length of the match** (number of pattern characters, excluding `$`, matched against the path prefix) if `pattern` matches `path`, else `-1`. `*` matches any sequence of characters; a trailing `$` anchors the end. Matching starts at the first character of the path. Hint: translate the pattern to a regular expression.''',
             starter=r'''
            def rule_match(pattern, path):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_rule_match(f):
                assert f("/tmp", "/tmp/a") == 4 and f("/tmp", "/tm") == -1
                assert f("/*.pdf$", "/docs/x.pdf") > 0 and f("/*.pdf$", "/docs/x.pdf?v=1") == -1
                assert f("/", "/anything") == 1''',
             solution=r'''
            def rule_match_solution(pattern, path):
                anchored = pattern.endswith("$"); p = pattern[:-1] if anchored else pattern
                rx = "^" + ".*".join(re.escape(part) for part in p.split("*")) + ("$" if anchored else "")
                return len(p) if re.match(rx, path) else -1'''),
        dict(fn='allowed', title='Is this URL allowed?', md=r'''
            `allowed(groups, agent, path)`: pick the group for the agent's product token (case-insensitive), else the `*` group, else everything is allowed. Among matching rules, the **longest match wins**; if an allow and a disallow match equally long, **allow** wins. `/robots.txt` itself is always allowed.''',
             starter=r'''
            def allowed(groups, agent, path):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_allowed(f):
                g = {"*": [("disallow", "/private/"), ("allow", "/private/public-page.html")],
                     "examplebot": [("disallow", "/tmp"), ("disallow", "/*.pdf$"), ("allow", "/tmp/ok")],
                     "otherbot": [("disallow", "/tmp"), ("disallow", "/*.pdf$"), ("allow", "/tmp/ok")], "ccbot": [("disallow", "/")]}
                assert f(g, "SomeBot", "/private/x") is False and f(g, "SomeBot", "/private/public-page.html") is True, "longer allow beats shorter disallow"
                assert f(g, "examplebot", "/tmp/ok/1") is True and f(g, "ExampleBot", "/tmp/no") is False
                assert f(g, "ExampleBot", "/a/b.pdf") is False and f(g, "ExampleBot", "/private/x") is True, "a specific group replaces the * group entirely"
                assert f(g, "CCBot", "/anything") is False and f(g, "CCBot", "/robots.txt") is True
                assert f({"*": [("disallow", "/a"), ("allow", "/a")]}, "x", "/a") is True, "ties go to allow"''',
             solution=r'''
            def allowed_solution(groups, agent, path):
                if path == "/robots.txt": return True
                rules = groups.get(agent.lower(), groups.get("*"))
                if not rules: return True
                best_len, best_kind = -1, "allow"
                for kind, pat in rules:
                    n = rule_match_solution(pat, path)
                    if n > best_len or (n == best_len and kind == "allow"):
                        best_len, best_kind = n, kind
                return best_len < 0 or best_kind == "allow"'''),
    ],
    explore_md=r'''
        **What to do when robots.txt cannot be fetched (RFC 9309, §2.3.1).** A 4xx status means "unavailable": the crawler MAY access anything. A 5xx or network error means "unreachable": assume **complete disallow**. Caches should not be used for more than 24 hours, and parsers must accept at least 500 KiB.''',
    explore=r'''
        def policy(status):
            if 200 <= status < 300: return "parse and obey the file"
            if 400 <= status < 500: return "unavailable → may crawl everything"
            if 500 <= status < 600: return "unreachable → assume complete disallow"
            return "follow redirects (at least five)"
        for s in [200, 301, 404, 403, 500, 503]: print(s, "→", policy(s))''',
    takeaways=r'''
        * Groups are chosen by product token (case-insensitive); a matching group replaces the `*` group.
        * Longest match wins; on a tie, allow wins; `*` and `$` are the only special characters.
        * 4xx → crawl allowed; 5xx/unreachable → crawl nothing. Crawl-delay is a non-standard extension (Common Crawl's CCBot obeys it).''',
))

# ------------------------------------------------------------------ 03
NBS.append(dict(
    slug='03_text_extraction', title='03 · From HTML to clean text', deck='pretraining-data/05-text-extraction/', deck_name='Text extraction', minutes=30,
    goals='stripping scripts, styles and navigation from HTML, splitting it into text blocks, and dropping boilerplate blocks with link-density and length heuristics, the core idea behind extractors like jusText and trafilatura.',
    setup=r'''
import re, html as _html
PAGE = """<html><head><title>Ring all-reduce explained</title><style>.nav{color:red}</style>
<script>var tracking = "<p>not text</p>";</script></head><body>
<div class="nav"><a href="/">Home</a> | <a href="/blog">Blog</a> | <a href="/about">About</a> | <a href="/login">Log in</a></div>
<h1>Ring all-reduce explained</h1>
<p>Data-parallel training averages gradients across GPUs. A ring all-reduce does this in two phases, a reduce-scatter and an all-gather.</p>
<p>Each GPU sends about twice the gradient size in total, almost independently of the number of GPUs, which is why the method scales.</p>
<div class="share"><a href="/tw">Tweet</a> <a href="/fb">Share</a></div>
<p>We use cookies to improve your experience. <a href="/privacy">Privacy policy</a></p>
<footer><a href="/terms">Terms</a> &copy; 2024 Example Inc.</footer>
</body></html>"""
''',
    tasks=[
        dict(fn='strip_noise', title='Remove scripts, styles and comments', md=r'''
            Remove `<script>…</script>`, `<style>…</style>` and `<!-- … -->` (including their contents, across lines). Return the remaining HTML. Note the script contains a fake `<p>` that must not survive.''',
             starter=r'''
            def strip_noise(html_text):
                # TODO: regex with re.S | re.I
                raise NotImplementedError''',
             test=r'''
            def _test_strip_noise(f):
                out = f(PAGE)
                assert "tracking" not in out and "not text" not in out and ".nav{" not in out
                assert "Ring all-reduce explained" in out''',
             solution=r'''
            def strip_noise_solution(html_text):
                return re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", html_text, flags=re.S | re.I)'''),
        dict(fn='blocks', title='Split into text blocks with link density', md=r'''
            Split the cleaned HTML at block-level tags (`p`, `div`, `h1`–`h6`, `li`, `footer`, `header`, `title`). For each block return `(text, link_density)` where text has tags removed, entities unescaped and whitespace collapsed, and link density = characters inside `<a>…</a>` ÷ all characters. Skip empty blocks.''',
             starter=r'''
            def blocks(clean_html):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_blocks(f):
                b = f(re.sub(r"<script.*?</script>|<style.*?</style>", " ", PAGE, flags=re.S | re.I))
                texts = [t for t, _ in b]
                nav = [d for t, d in b if t.startswith("Home")]
                assert nav and nav[0] > 0.6, "the navigation bar is almost all link text"
                body = [d for t, d in b if t.startswith("Data-parallel")]
                assert body and body[0] == 0
                assert any("©" in t for t in texts), "entities like &copy; must be unescaped"''',
             solution=r'''
            def blocks_solution(clean_html):
                parts = re.split(r"</?(?:p|div|h[1-6]|li|footer|header|title)\b[^>]*>", clean_html, flags=re.I)
                out = []
                for part in parts:
                    link = "".join(re.findall(r"<a\b[^>]*>(.*?)</a>", part, flags=re.S | re.I))
                    text = re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", part))).strip()
                    if not text: continue
                    link_text = re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", link))).strip()
                    out.append((text, len(link_text) / len(text)))
                return out'''),
        dict(fn='extract', title='Keep the main content', md=r'''
            Keep blocks with link density below `max_ld`, at least `min_words` words, and no boilerplate phrase (`cookie`, `privacy policy`, `terms of use`, `©`). Keep the `<h1>`-style headline too: allow blocks of ≥ 3 words if they are the first block after the title. Return the kept texts joined with blank lines.''',
             starter=r'''
            def extract(html_text, max_ld=0.3, min_words=8):
                # TODO: strip_noise → blocks → filter
                raise NotImplementedError''',
             test=r'''
            def _test_extract(f):
                out = f(PAGE)
                assert "reduce-scatter" in out and "twice the gradient" in out, "keep the article paragraphs"
                for junk in ["Log in", "Tweet", "cookies", "Terms"]:
                    assert junk not in out, f"boilerplate '{junk}' should be removed"''',
             solution=r'''
            def extract_solution(html_text, max_ld=0.3, min_words=8):
                bad = ("cookie", "privacy policy", "terms of use", "©")
                b = blocks_solution(strip_noise_solution(html_text)); keep = []
                for i, (t, ld) in enumerate(b):
                    if ld >= max_ld or any(x in t.lower() for x in bad): continue
                    if len(t.split()) >= min_words or (i <= 2 and len(t.split()) >= 3 and i > 0):
                        keep.append(t)
                return "\n\n".join(dict.fromkeys(keep))'''),
    ],
    explore_md=r'''
        **How much of the page is kept?** Compare the number of characters in the raw HTML, the naive tag-stripped text (what WET files roughly give you) and the extracted main content.''',
    explore=r'''
        naive = re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", PAGE)))
        main = extract_solution(PAGE)
        print(f"raw HTML {len(PAGE)} chars → naive text {len(naive)} chars → main content {len(main)} chars")
        print("naive text starts:", naive[:120])''',
    takeaways=r'''
        * Raw HTML is mostly markup, scripts and boilerplate; naive tag stripping keeps menus, buttons and cookie banners.
        * Block-level heuristics (link density, length, boilerplate phrases) recover the main text cheaply.
        * FineWeb found extracting from WARC with trafilatura beat Common Crawl's WET text, which keeps too much boilerplate.''',
))

# ------------------------------------------------------------------ 04
NBS.append(dict(
    slug='04_quality_filters', title='04 · Heuristic quality filters (C4 and Gopher rules)', deck='pretraining-data/06-quality-filtering/', deck_name='Quality filtering', minutes=35,
    goals='the C4 line and page rules and the Gopher (MassiveText) document rules as functions, applied to a small set of sample documents with an explanation of why each one is kept or dropped.',
    setup=r'''
import re
DOCS = {
    "article": "Gradient descent updates the weights in the direction that reduces the loss. The step size is set by the learning rate. If it is too large, training diverges. If it is too small, training is slow. Modern language models use the Adam optimizer with a warmup schedule. This keeps early updates small while statistics settle. Later the learning rate decays, letting the model settle into a good region of the loss surface.",
    "nav": "Home\nProducts\nAbout us\nContact\nLog in\nSign up",
    "spam": "best cheap shoes best cheap shoes best cheap shoes best cheap shoes best cheap shoes best cheap shoes best cheap shoes best cheap shoes best cheap shoes best cheap shoes",
    "code": "function add(a, b) { return a + b; } const x = add(1, 2); console.log(x); if (x > 2) { alert('big'); } // this is a comment line that goes on for a while to be long enough",
    "hashtags": " ".join(["#ai #ml #deep #learning #love #photo #instagood #follow #nofilter #tbt"] * 4) + " this post is about the best day of my life and I have to say that the light was perfect with friends",

    "lorem": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.",
}
STOP = {"the", "be", "to", "of", "and", "that", "have", "with"}
''',
    tasks=[
        dict(fn='c4_clean', title='C4 rules', md=r'''
            From Raffel et al. (2020): keep only lines ending in terminal punctuation (`.`, `!`, `?`, or a closing quote) with at least 5 words; drop the page if fewer than 3 sentences remain, or if it contains "lorem ipsum" or a curly bracket `{`; drop lines containing "javascript".
            Return the cleaned text, or `None` if the page is dropped. (Count sentences as terminal punctuation marks in the kept text.)''',
             starter=r'''
            def c4_clean(text):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_c4_clean(f):
                assert f(DOCS["article"]) is not None
                for k in ["nav", "code", "lorem", "spam"]:
                    assert f(DOCS[k]) is None, f"C4 should drop '{k}'"
                assert f("Enable javascript to view this site. " * 1 + "This sentence has five words here. Another sentence also has words. A third sentence ends now.") is not None''',
             solution=r'''
            def c4_clean_solution(text):
                low = text.lower()
                if "lorem ipsum" in low or "{" in text: return None
                lines = re.split(r"\n|(?<=[.!?\"”])\s+", text)
                keep = [l.strip() for l in lines if l.strip() and l.strip()[-1] in '.!?"”' and len(l.split()) >= 5 and "javascript" not in l.lower()]
                out = " ".join(keep)
                return out if len(re.findall(r'[.!?]["”]?(\s|$)', out)) >= 3 else None'''),
        dict(fn='gopher_ok', title='Gopher document rules', md=r'''
            From Rae et al. (2021): keep a document only if it has 50–100,000 words; mean word length 3–10 characters; symbol-to-word ratio ≤ 0.1 for `#` and for `...`/`…`; ≤ 90% of lines starting with a bullet; ≤ 30% of lines ending in an ellipsis; ≥ 80% of words containing a letter; and at least 2 of the stop words (the, be, to, of, and, that, have, with).
            Return `(ok, reason)` with the first failing rule's name as reason (or `"ok"`).''',
             starter=r'''
            def gopher_ok(text):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_gopher_ok(f):
                assert f(DOCS["article"])[0] is True
                assert f(DOCS["nav"]) == (False, "word_count")
                assert f(DOCS["hashtags"]) == (False, "symbol_ratio")
                assert f(DOCS["lorem"])[1] == "stop_words", "Latin placeholder has no English stop words"''',
             solution=r'''
            def gopher_ok_solution(text):
                words = text.split(); n = len(words)
                if not 50 <= n <= 100_000: return False, "word_count"
                if not 3 <= sum(len(w) for w in words) / n <= 10: return False, "mean_word_length"
                if text.count("#") / n > 0.1 or (text.count("...") + text.count("…")) / n > 0.1: return False, "symbol_ratio"
                lines = [l for l in text.splitlines() if l.strip()] or [text]
                if sum(l.lstrip().startswith(("•", "-", "*")) for l in lines) / len(lines) > 0.9: return False, "bullets"
                if sum(l.rstrip().endswith(("...", "…")) for l in lines) / len(lines) > 0.3: return False, "ellipsis_lines"
                if sum(bool(re.search(r"[A-Za-z]", w)) for w in words) / n < 0.8: return False, "alphabetic"
                if len(STOP & {w.lower().strip(".,;:!?") for w in words}) < 2: return False, "stop_words"
                return True, "ok"'''),
        dict(fn='repetition_ok', title='Repetition: duplicate n-gram fraction', md=r'''
            Gopher also removes documents whose characters are dominated by repeated n-grams. Return the fraction of words that belong to a word **3-gram that occurs more than once** in the document, and `ok = fraction ≤ threshold` (use 0.3 here as a simple stand-in for Gopher's per-n thresholds). Return `(ok, fraction)`.''',
             starter=r'''
            def repetition_ok(text, threshold=0.3):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_repetition_ok(f):
                ok, fr = f(DOCS["spam"]); assert not ok and fr > 0.9
                ok2, fr2 = f(DOCS["article"]); assert ok2 and fr2 < 0.2''',
             solution=r'''
            def repetition_ok_solution(text, threshold=0.3):
                w = text.lower().split(); grams = [tuple(w[i:i + 3]) for i in range(len(w) - 2)]
                from collections import Counter
                c = Counter(grams); covered = set()
                for i, g in enumerate(grams):
                    if c[g] > 1: covered.update(range(i, i + 3))
                fr = len(covered) / max(1, len(w))
                return fr <= threshold, fr'''),
    ],
    explore_md=r'''
        **Verdicts for every sample.** Which rules catch what? Different filters catch different junk, which is why pipelines stack them.''',
    explore=r'''
        for k, d in DOCS.items():
            c4 = c4_clean_solution(d) is not None; g, why = gopher_ok_solution(d); r, fr = repetition_ok_solution(d)
            print(f"{k:9s}: C4 {'keep' if c4 else 'drop'} | Gopher {'keep' if g else 'drop (' + why + ')'} | repetition {fr:.2f} {'ok' if r else 'drop'}")''',
    takeaways=r'''
        * Heuristic filters are cheap, transparent and catch most obvious junk: menus, code, placeholder text, spam.
        * Each rule targets a specific failure; pipelines combine several (Dolma uses all Gopher rules plus C4's punctuation rule).
        * Model-based filters (fastText or small transformers trained on "good" examples) catch subtler low quality; DCLM and FineWeb-Edu show they help most.''',
))

# ------------------------------------------------------------------ 05
NBS.append(dict(
    slug='05_minhash_lsh', title='05 · Near-duplicate detection with MinHash and LSH', deck='pretraining-data/07-deduplication/', deck_name='Deduplication', minutes=40,
    goals='word n-gram shingles and exact Jaccard similarity, MinHash signatures whose agreement estimates Jaccard, and locality-sensitive hashing with b bands of r rows, including its S-shaped detection curve.',
    setup=r'''
import hashlib, itertools
BASE = ("the quick brown fox jumps over the lazy dog while the farmer watches from the old wooden barn "
        "and the sun sets slowly behind the hills casting long shadows across the quiet green fields").split()
def variant(k, seed):
    """BASE with k random word substitutions."""
    r = np.random.default_rng(seed); w = list(BASE)
    for i in r.choice(len(w), size=k, replace=False): w[i] = f"word{r.integers(1e6)}"
    return " ".join(w)
P = (1 << 61) - 1
def h64(s): return int.from_bytes(hashlib.blake2b(s.encode(), digest_size=8).digest(), "big")
''',
    tasks=[
        dict(fn='shingles_jaccard', title='Shingles and Jaccard similarity', md=r'''
            `shingles(text, n)` returns the set of word n-grams (as tuples). `jaccard(a, b)` = |A ∩ B| / |A ∪ B|. Return the two functions as a tuple.''',
             starter=r'''
            def shingles(text, n=5):
                # TODO
                raise NotImplementedError
            def jaccard(A, B):
                # TODO
                raise NotImplementedError
            def shingles_jaccard():
                return shingles, jaccard''',
             test=r'''
            def _test_shingles_jaccard(f):
                sh, jac = f()
                a = sh("a b c d e f", 3)
                assert a == {("a", "b", "c"), ("b", "c", "d"), ("c", "d", "e"), ("d", "e", "f")}
                assert jac(a, a) == 1 and jac(a, set()) == 0
                assert 0.3 < jac(sh(variant(2, 0)), sh(" ".join(BASE))) < 0.9''',
             solution=r'''
            def shingles_s(text, n=5):
                w = text.split(); return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}
            def jaccard_s(A, B):
                return len(A & B) / len(A | B) if A | B else 0.0
            def shingles_jaccard_solution():
                return shingles_s, jaccard_s'''),
        dict(fn='minhash', title='MinHash signatures', md=r'''
            Hash each shingle to a 64-bit integer with `h64`, then apply `k` random affine hash functions $h_i(x) = (a_i x + b_i) \bmod P$ and keep the **minimum** over the set for each i. Return the signature array of length k.
            The probability that two sets agree on one minimum equals their Jaccard similarity (Broder, 1997), so the fraction of agreeing positions estimates it.''',
             starter=r'''
            def minhash(shingle_set, k=128, seed=0):
                r = np.random.default_rng(seed)
                a = r.integers(1, P, size=k, dtype=np.uint64); b = r.integers(0, P, size=k, dtype=np.uint64)
                # TODO: use Python ints for the modular arithmetic (np.uint64 overflows); return np.array of mins
                raise NotImplementedError''',
             test=r'''
            def _test_minhash(f):
                sh = lambda t, n=5: {tuple(t.split()[i:i + n]) for i in range(len(t.split()) - n + 1)}
                jac = lambda X, Y: len(X & Y) / len(X | Y)
                A, B = sh(" ".join(BASE)), sh(variant(3, 1))
                sa, sb = f(A, 256), f(B, 256)
                assert len(sa) == 256
                est, true = np.mean(sa == sb), jac(A, B)
                assert abs(est - true) < 0.1, f"MinHash estimate {est:.2f} should be close to Jaccard {true:.2f}"
                assert np.all(f(A, 64) == f(A, 64)), "deterministic for a fixed seed"''',
             solution=r'''
            def minhash_solution(shingle_set, k=128, seed=0):
                r = np.random.default_rng(seed)
                a = [int(x) for x in r.integers(1, P, size=k, dtype=np.uint64)]; b = [int(x) for x in r.integers(0, P, size=k, dtype=np.uint64)]
                xs = [h64(" ".join(s)) for s in shingle_set]
                return np.array([min((ai * x + bi) % P for x in xs) for ai, bi in zip(a, b)], dtype=object)'''),
        dict(fn='lsh_prob', title='LSH banding: the S-curve', md=r'''
            Split a signature of b·r values into **b bands of r rows**. Two documents become candidates if **all r rows of at least one band** match. With Jaccard s, that happens with probability $P(s) = 1 - (1 - s^r)^b$.
            Return P for the given s, r, b. Check: RefinedWeb's 450 bands × 20 rows give P(0.75) ≈ 0.76 and P(0.8) ≈ 0.994.''',
             starter=r'''
            def lsh_prob(s, r, b):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_lsh_prob(f):
                assert abs(f(0.75, 20, 450) - 0.76) < 0.01 and abs(f(0.8, 20, 450) - 0.994) < 0.002, "RefinedWeb's numbers"
                assert f(0.3, 8, 14) < 0.01 and f(0.9, 8, 14) > 0.99, "FineWeb's 14 bands × 8 rows: steep around 0.75"''',
             solution=r'''
            def lsh_prob_solution(s, r, b):
                return 1 - (1 - s ** r) ** b'''),
    ],
    explore_md=r'''
        **Find near-duplicates in a small corpus with banding.** Build 40 documents (variants of one base text with 0–12 substitutions, plus unrelated random documents), MinHash them, bucket by band, and compare candidates with true Jaccard.''',
    explore=r'''
        sh, jac = shingles_jaccard_solution()
        docs = [variant(k, s) for s, k in enumerate([0, 1, 2, 3, 5, 8, 12] * 3)] + [" ".join(np.random.default_rng(100 + i).choice(["x%d" % j for j in range(500)], 30)) for i in range(19)]
        S = [sh(d) for d in docs]; sig = [minhash_solution(s, 112) for s in S]
        b, r = 14, 8; buckets = {}
        for i, sgn in enumerate(sig):
            for band in range(b):
                buckets.setdefault((band, tuple(sgn[band * r:(band + 1) * r])), []).append(i)
        cand = {tuple(sorted(p)) for ids in buckets.values() for p in itertools.combinations(ids, 2)}
        sims = [jac(S[i], S[j]) for i, j in cand]
        allpairs = [jac(S[i], S[j]) for i, j in itertools.combinations(range(len(S)), 2)]
        print(f"{len(cand)} candidate pairs out of {len(allpairs)}; min Jaccard among candidates {min(sims):.2f}")
        print(f"true pairs with Jaccard ≥ 0.75: {sum(s >= 0.75 for s in allpairs)}, found: {sum(s >= 0.75 for s in sims)}")''',
    takeaways=r'''
        * Near-duplicates are measured by Jaccard similarity of word n-gram sets.
        * MinHash compresses each document to k numbers whose agreement rate estimates Jaccard.
        * LSH banding finds candidate pairs without comparing all pairs; b and r place the S-curve's threshold (≈ (1/b)^(1/r)).''',
))

# ------------------------------------------------------------------ 06
NBS.append(dict(
    slug='06_data_mixture', title='06 · Data mixtures, sampling temperature and epochs', deck='pretraining-data/09-mixtures-and-repetition/', deck_name='Data mixtures and repetition', minutes=25,
    goals='turning domain weights into a token budget, computing how many epochs each domain is repeated, temperature sampling to up-weight small domains (as in multilingual training), and capping repetition.',
    setup=r'''
DOMAINS = {"web": 12_000e9, "code": 800e9, "math": 150e9, "books": 60e9, "wikipedia": 20e9, "low-resource languages": 5e9}
''',
    tasks=[
        dict(fn='epochs', title='Epochs per domain', md=r'''
            Given unique tokens per domain, sampling weights (summing to 1) and a total training budget, return a dict of **epochs** per domain: weight × budget ÷ unique tokens.''',
             starter=r'''
            def epochs(domains, weights, budget):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_epochs(f):
                e = f({"a": 100, "b": 10}, {"a": 0.5, "b": 0.5}, 100)
                assert e == {"a": 0.5, "b": 5.0}''',
             solution=r'''
            def epochs_solution(domains, weights, budget):
                return {k: weights[k] * budget / domains[k] for k in domains}'''),
        dict(fn='temperature_weights', title='Temperature sampling', md=r'''
            Natural sampling uses weights $p_i = n_i / \sum n$. Temperature sampling uses $q_i \propto p_i^{1/T}$: T = 1 is natural, larger T flattens toward uniform (more weight to small domains). Return the normalised weights.''',
             starter=r'''
            def temperature_weights(domains, T):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_temperature_weights(f):
                w1 = f(DOMAINS, 1.0); assert abs(sum(w1.values()) - 1) < 1e-12
                assert abs(w1["web"] - 12000 / sum(v / 1e9 for v in DOMAINS.values())) < 1e-9
                w5 = f(DOMAINS, 5.0)
                assert w5["low-resource languages"] > 10 * w1["low-resource languages"], "higher T boosts small domains"''',
             solution=r'''
            def temperature_weights_solution(domains, T):
                tot = sum(domains.values()); q = {k: (v / tot) ** (1 / T) for k, v in domains.items()}; z = sum(q.values())
                return {k: v / z for k, v in q.items()}'''),
        dict(fn='cap_epochs', title='Cap repetition', md=r'''
            Muennighoff et al. (2023) found that up to about **4 epochs** of repeated data is nearly as good as fresh data, with rapidly diminishing returns after. Given desired weights, cap each domain at `max_epochs` and give the freed budget to uncapped domains in proportion to their weights; repeat until nothing exceeds the cap. Return the new weights.''',
             starter=r'''
            def cap_epochs(domains, weights, budget, max_epochs=4.0):
                # TODO: iterative water-filling
                raise NotImplementedError''',
             test=r'''
            def _test_cap_epochs(f):
                tot = sum(DOMAINS.values()); q = {k: (v / tot) ** 0.2 for k, v in DOMAINS.items()}; w = {k: v / sum(q.values()) for k, v in q.items()}
                budget = 15_000e9
                c = f(DOMAINS, w, budget)
                e = {k: c[k] * budget / DOMAINS[k] for k in DOMAINS}
                assert abs(sum(c.values()) - 1) < 1e-9
                assert max(e.values()) <= 4.0 + 1e-6, f"no domain above 4 epochs, got {max(e.values()):.2f}"
                assert c["web"] > w["web"], "freed budget flows to the big domain"''',
             solution=r'''
            def cap_epochs_solution(domains, weights, budget, max_epochs=4.0):
                w = dict(weights); capped = set()
                while True:
                    over = {k for k in w if k not in capped and w[k] * budget / domains[k] > max_epochs + 1e-12}
                    if not over: return w
                    for k in over:
                        w[k] = max_epochs * domains[k] / budget; capped.add(k)
                    free = 1 - sum(w[k] for k in capped); rest = {k: weights[k] for k in w if k not in capped}; z = sum(rest.values())
                    for k in rest: w[k] = free * rest[k] / z'''),
    ],
    explore_md=r'''
        **A 15T-token run.** Epochs per domain under natural sampling, temperature 3, and temperature 3 with a 4-epoch cap.''',
    explore=r'''
        budget = 15_000e9
        for name, w in [("natural (T=1)", temperature_weights_solution(DOMAINS, 1)), ("T=3", temperature_weights_solution(DOMAINS, 3)),
                        ("T=3, capped at 4 epochs", cap_epochs_solution(DOMAINS, temperature_weights_solution(DOMAINS, 3), budget))]:
            e = epochs_solution(DOMAINS, w, budget)
            print(name + ": " + ", ".join(f"{k} {w[k]:.1%} ({e[k]:.1f} ep)" for k in DOMAINS))''',
    takeaways=r'''
        * A data mix is a set of sampling weights; with a fixed budget, small domains get repeated many times.
        * Temperature sampling up-weights small domains (common for languages); capping epochs (~4) avoids wasted repetition.
        * Llama 3's final mix was roughly 50% general knowledge, 25% math and reasoning, 17% code and 8% multilingual tokens.''',
))
