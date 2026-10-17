"""Shared builders for the per-deck additions: at-a-glance diagram, worked example, tricks & traps, key papers.

Every deck spec can carry:
  glance  = dict(steps=[(label, sub, color)], loop=(from_idx, to_idx, label) or None, caption=str)
  example = dict(title=str, setup=str, steps=[html], result=html)      # numbers computed in Python by the spec
  traps   = dict(tricks=[(title, html)], traps=[(title, html)])
  papers  = [dict(title, authors, year, venue, url, summary, number)]
`apply(html_slides, spec)` inserts them into the generated slide list.
"""
from html import escape

COLORS = {'a': 'var(--a)', 'b': 'var(--b)', 'c': 'var(--c)', 'd': 'var(--d)', 'e': 'var(--e)', 'f': 'var(--faint)'}


def _wrap(text, width):
    """Split on explicit newlines, then greedily wrap each part to about `width` characters."""
    lines = []
    for part in text.split('\n'):
        cur = ''
        words = []
        for w in part.split():                         # break over-long identifiers after underscores so they fit the box
            while len(w) > width and '_' in w[1:width]:
                k = w.rindex('_', 1, width) + 1
                words.append(w[:k]); w = w[k:]
            words.append(w)
        for w in words:
            if cur and len(cur) + 1 + len(w) > width:
                lines.append(cur); cur = w
            else:
                cur = (cur + ' ' + w).strip()
        if cur:
            lines.append(cur)
    return lines


def flow(steps, loop=None, caption=''):
    """Static, theme-aware SVG: boxes left to right with arrows; optional loop-back arrow underneath."""
    n = len(steps)
    W, gap, top = 660, 18, 28
    bw = (W - 20 - gap * (n - 1)) / n
    h = 64
    sub_lines = max((len(_wrap(st[1], max(10, int(bw / 6.3)))) for st in steps if st[1]), default=0)
    extra = 14 * max(0, sub_lines - 1)
    out = [f'<svg viewBox="0 0 {W} {top + h + extra + (82 if loop else 46)}" role="img" aria-label="{escape(caption or "diagram")}" class="glance-svg">',
           '<defs><marker id="gArr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--muted)"/></marker></defs>']
    xs = []
    for i, (label, sub, col) in enumerate(steps):
        x = 10 + i * (bw + gap); xs.append(x)
        c = COLORS.get(col, col)
        out.append(f'<rect x="{x:.1f}" y="{top}" width="{bw:.1f}" height="{h}" rx="10" style="fill:{c}"/>')
        fs = 13 if n <= 4 else 12
        lines = _wrap(label, max(6, int((bw - 12) / (fs * 0.6))))     # keep bold labels inside the box (≈0.6 em per character)
        if len(lines) > 3:
            fs = 11; lines = _wrap(label, max(6, int((bw - 10) / (fs * 0.6))))
        for j, ln in enumerate(lines):
            y = top + h / 2 + 5 + (j - (len(lines) - 1) / 2) * (fs + 3)
            out.append(f'<text x="{x + bw / 2:.1f}" y="{y:.1f}" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:{fs}px">{escape(ln)}</text>')
        if sub:
            for j, ln in enumerate(_wrap(sub, max(10, int(bw / 6.3)))):
                out.append(f'<text x="{x + bw / 2:.1f}" y="{top + h + 17 + j * 14:.1f}" text-anchor="middle" class="tm" style="font-size:11px">{escape(ln)}</text>')
        if i:
            out.append(f'<line x1="{xs[i - 1] + bw + 2:.1f}" y1="{top + h / 2}" x2="{x - 2:.1f}" y2="{top + h / 2}" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/>')
    if loop:
        a, b, lbl = loop
        x1, x2, yb = xs[a] + bw / 2, xs[b] + bw / 2, top + h + extra + 54
        if a == b:                                     # self-loop: right edge of the box back to its left edge
            x1, x2 = xs[a] + bw * 0.85, xs[a] + bw * 0.15
        out.append(f'<path d="M{x1:.1f} {top + h + extra + 30} V{yb} H{x2:.1f} V{top + h + extra + 32}" fill="none" style="stroke:var(--muted);stroke-width:2;stroke-dasharray:5 4" marker-end="url(#gArr)"/>')
        out.append(f'<text x="{(x1 + x2) / 2:.1f}" y="{yb + 17}" text-anchor="middle" class="tm" style="font-size:11px">{escape(lbl)}</text>')
    out.append('</svg>')
    return ''.join(out)


def glance_html(g):
    return f'''
    <!--x:glance--><div class="glance"><h4>At a glance</h4>{flow(g["steps"], g.get("loop"), g.get("caption", ""))}{f'<p class="caption" style="margin:4px 0 0">{g["caption"]}</p>' if g.get("caption") else ''}</div><!--/x:glance-->'''


def _section(sid, chapter, tag_cls, tag_text, title, body):
    return f'''<section class="slide" id="{sid}" data-chapter="{chapter}">
  <div class="inner">
    <span class="qtag {tag_cls}">{tag_text}</span>
    <h2>{title}</h2>
    <hr>
{body}
  </div>
</section>'''


def example_slide(ex, chapter='How', tag=('b5', '5 · How it works')):
    steps = ''.join(f'<li>{s}</li>' for s in ex['steps'])
    body = f'''    <p class="lede">{ex["setup"]}</p>
    <div class="example"><h4>Worked example</h4><ol>{steps}</ol><div class="result">{ex["result"]}</div></div>'''
    return _section('s-example', chapter, tag[0], tag[1], ex['title'], body)


def traps_slide(t, tag=('b7', '7 · Tricks and traps')):
    tr = ''.join(f'<li><b>{a}</b> {b}</li>' for a, b in t['tricks'])
    tp = ''.join(f'<li><b>{a}</b> {b}</li>' for a, b in t['traps'])
    body = f'''    <p class="lede">Rules of thumb that make this topic quick to reason about, and the mistakes people most often make with it.</p>
    <div class="tt-grid">
      <div class="tt tricks"><h3>✓ Tricks</h3><ul>{tr}</ul></div>
      <div class="tt traps"><h3>⚠ Traps</h3><ul>{tp}</ul></div>
    </div>'''
    return _section('s-traps', 'Traps', tag[0], tag[1], 'Tricks and traps', body)


def papers_slide(papers):
    items = ''.join(f'''
      <div class="paper-item"><a href="{p["url"]}" target="_blank" rel="noopener">{p["title"]}</a>
        <div class="meta">{p["authors"]} · {p["venue"]} {p["year"]}</div>
        <p>{p["summary"]}</p>{f'<div class="num">Remember: {p["number"]}</div>' if p.get("number") else ''}</div>''' for p in papers)
    body = f'''    <p class="lede">The primary sources behind this deck, each with what it contributed. Links go to the paper (arXiv or the conference page).</p>
    <div class="papers">{items}
    </div>'''
    return _section('s-papers', 'Papers', 'b9', 'Further reading', 'Key papers', body)


def apply(slides, spec):
    """slides: list of section HTML strings (title first, take last). Returns a new list with extras inserted."""
    out = list(slides)
    ids = [s.split('id="', 1)[1].split('"', 1)[0] for s in out]
    if spec.get('glance') and 's-core' in ids:
        i = ids.index('s-core'); s = out[i]
        cut = s.rindex('  </div>\n</section>')
        out[i] = s[:cut] + glance_html(spec['glance']) + '\n' + s[cut:]
    if spec.get('example'):
        last_how = max((k for k, sid in enumerate(ids) if sid.startswith('s-how')), default=ids.index('s-core'))
        out.insert(last_how + 1, example_slide(spec['example'])); ids.insert(last_how + 1, 's-example')
    if spec.get('traps') and 's-myth' in ids:
        k = ids.index('s-myth')
        out.insert(k + 1, traps_slide(spec['traps'])); ids.insert(k + 1, 's-traps')
    if spec.get('papers'):
        out.append(papers_slide(spec['papers'])); ids.append('s-papers')
    return out
