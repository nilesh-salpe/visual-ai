"""Review status of every deck: which are reviewed, when, and with what label.

    python3 tools/review_status.py                 # table: least recently reviewed first
    python3 tools/review_status.py --stale 90      # only decks never reviewed or reviewed more than 90 days ago
    python3 tools/review_status.py --topic vllm    # one topic
    python3 tools/review_status.py --write         # also write status/index.html (CI does this)

Status lives in each deck's front matter (content/<topic>/<slug>/deck.md):
    status: {label: current | trend | legacy | research, reviewed: YYYY-MM-DD, note: "short reason"}
See .claude/skills/deck-review/SKILL.md for the review procedure.
"""
import argparse, datetime as dt, glob, html, os, re, sys
import yaml

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LABELS = {'current': 'Current practice', 'trend': 'Recent trend', 'legacy': 'Legacy', 'research': 'Research'}


def decks():
    out = []
    for path in sorted(glob.glob(os.path.join(REPO, 'content', '*', '*', 'deck.md'))):
        topic, slug = path.split(os.sep)[-3:-1]
        fm = yaml.safe_load(open(path).read().split('---\n', 2)[1]) or {}
        st = fm.get('status') or {}
        reviewed = st.get('reviewed')
        if isinstance(reviewed, str):
            reviewed = dt.date.fromisoformat(reviewed)
        inline = re.findall(r'\[\[(current|trend|legacy|research)\]\]', open(path).read())
        out.append(dict(topic=topic, slug=slug, title=fm.get('title', slug), label=st.get('label'), reviewed=reviewed, note=st.get('note', ''), inline=inline))
    return out


def age(d, today):
    return (today - d['reviewed']).days if d['reviewed'] else None


def page(rows, today):
    counts = {k: sum(r['label'] == k for r in rows) for k in LABELS}
    never = sum(r['reviewed'] is None for r in rows)
    def badge(lbl):
        return f'<span class="lbl lbl-{lbl}">{LABELS[lbl]}</span>' if lbl else '<span class="status-note">not reviewed</span>'
    trs = ''.join(f'<tr><td><a href="../{r["topic"]}/{r["slug"]}/index.html">{html.escape(r["title"])}</a><div class="status-note">{r["topic"]}</div></td>'
                  f'<td>{badge(r["label"])}</td><td>{r["reviewed"] or "—"}</td><td>{"" if age(r, today) is None else age(r, today)}</td>'
                  f'<td>{len(r["inline"])}</td><td>{html.escape(r["note"])}</td></tr>' for r in rows)
    summary = ' · '.join(f'{LABELS[k]}: {v}' for k, v in counts.items()) + f' · not yet reviewed: {never}'
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Deck Review Status</title>
<link rel="stylesheet" href="../shared/deck.css">
</head>
<body class="doc-page">
<article class="doc">
  <a class="brand" href="../index.html">← Visual AI</a>
  <h1>Review status</h1>
  <p>How current each deck is. <span class="lbl lbl-current">Current practice</span> widely used in production today; <span class="lbl lbl-trend">Recent trend</span> new and gaining adoption;
  <span class="lbl lbl-legacy">Legacy</span> superseded, mostly in older systems; <span class="lbl lbl-research">Research</span> promising but not common in production.
  Decks also carry inline labels next to individual techniques. Least recently reviewed first.</p>
  <p class="status-note">{summary}. Generated {today}.</p>
  <table><tr><th>Deck</th><th>Status</th><th>Reviewed</th><th>Days ago</th><th>Inline labels</th><th>Note</th></tr>{trs}</table>
</article>
</body>
</html>
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stale', type=int, help='only decks never reviewed or reviewed more than N days ago')
    ap.add_argument('--topic')
    ap.add_argument('--write', action='store_true')
    a = ap.parse_args()
    today = dt.date.today()
    rows = sorted(decks(), key=lambda r: (r['reviewed'] is not None, r['reviewed'] or dt.date.min, r['topic'], r['slug']))
    if a.write:
        os.makedirs(os.path.join(REPO, 'status'), exist_ok=True)
        open(os.path.join(REPO, 'status', 'index.html'), 'w').write(page(rows, today))
        print('wrote status/index.html')
    show = [r for r in rows if (not a.topic or r['topic'] == a.topic) and (a.stale is None or r['reviewed'] is None or age(r, today) > a.stale)]
    for r in show:
        print(f"{r['topic'] + '/' + r['slug']:52} {(r['label'] or 'unreviewed'):11} {str(r['reviewed'] or '-'):11} inline={len(r['inline'])}")
    print(f'{len(show)} of {len(rows)} decks shown', file=sys.stderr)


if __name__ == '__main__':
    main()
