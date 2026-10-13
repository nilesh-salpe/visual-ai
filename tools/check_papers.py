"""Verify every paper record: the link resolves and, for arXiv, the title matches the abstract page.
    python3 tools/check_papers.py [cache_dir]"""
import html, os, re, sys, time, unicodedata, urllib.request
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'decks'))
from papers import PAPERS

cache = sys.argv[1] if len(sys.argv) > 1 else '/tmp/papers_cache'
os.makedirs(cache, exist_ok=True)
norm = lambda s: re.sub(r'[^a-z0-9]+', ' ', unicodedata.normalize('NFKD', html.unescape(s)).encode('ascii', 'ignore').decode().lower()).strip()
bad = 0
for key, p in PAPERS.items():
    url = p['url']
    m = re.match(r'https://arxiv.org/abs/(.+)', url)
    if not m:
        try:
            code = urllib.request.urlopen(urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).status
        except Exception as e:
            code = str(e)
        print(f"{'ok ' if code == 200 else 'BAD'} {key}: {code} (non-arXiv)"); bad += code != 200
        continue
    f = os.path.join(cache, m.group(1).replace('/', '_') + '.html')
    if not os.path.exists(f) or os.path.getsize(f) < 1000:
        for attempt in range(4):
            try:
                data = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read().decode('utf-8', 'replace')
                open(f, 'w').write(data); break
            except Exception:
                time.sleep(5)
    t = re.search(r'<meta name="citation_title" content="([^"]*)"', open(f).read()) if os.path.exists(f) else None
    real = norm(t.group(1)) if t else ''
    mine = norm(re.sub(r'\s*\([^)]*\)\s*$', '', p['title']))
    ok = bool(real) and (real.startswith(mine) or mine.startswith(real) or mine in real)
    bad += not ok
    print(f"{'ok ' if ok else 'BAD'} {key}: {real[:90] if real else 'no title fetched'}")
print(f"{len(PAPERS) - bad}/{len(PAPERS)} papers verified")
sys.exit(1 if bad else 0)
