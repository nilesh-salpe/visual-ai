"""Render every slide of every deck in Chrome and report layout defects as JSON lines.

    pip install playwright   (uses the installed Chrome; not run in CI)
    python3 tools/audit_layout.py OUT.jsonl "inference/[0-9][0-9]-*" 1280 390
Checks (on the active slide, after widgets have drawn):
  text_overflow   SVG text wider than the diagram box it sits in
  text_overlap    two SVG text elements overlapping
  label_on_box    an edge label overlapping a box it does not belong to
  line_thru_text  an arrow/line passing through a text element
  svg_outside     SVG text outside the viewBox
  html_overflow   slide content wider than the slide (horizontal spill)
  js_error        uncaught page errors
"""
import glob, json, sys
from playwright.sync_api import sync_playwright

import os
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
JS = r'''() => {
  const out = [], slide = document.querySelector('section.slide.active'); if (!slide) return out;
  const inter = (a, b) => Math.max(0, Math.min(a.x + a.width, b.x + b.width) - Math.max(a.x, b.x)) * Math.max(0, Math.min(a.y + a.height, b.y + b.height) - Math.max(a.y, b.y));
  const segHits = (x1, y1, x2, y2, r) => { for (let t = 0.04; t < 0.96; t += 0.02) { const x = x1 + (x2 - x1) * t, y = y1 + (y2 - y1) * t; if (x > r.x + 1 && x < r.x + r.width - 1 && y > r.y + 1 && y < r.y + r.height - 1) return true; } return false; };
  slide.querySelectorAll('svg').forEach((svg, si) => {
    if (!svg.getBoundingClientRect().width) return;
    const vb = svg.viewBox && svg.viewBox.baseVal && svg.viewBox.baseVal.width ? svg.viewBox.baseVal : null;
    const texts = [...svg.querySelectorAll('text')].filter(t => t.textContent.trim() && getComputedStyle(t).display !== 'none' && +getComputedStyle(t).opacity !== 0 && !t.closest('.dg-off'));
    const boxes = texts.map(t => { try { return t.getBBox(); } catch (e) { return null; } });
    const id = svg.closest('.dgm') ? 'diagram' : svg.classList.contains('glance-svg') ? 'glance' : (svg.id || 'svg' + si);
    texts.forEach((t, i) => {
      const b = boxes[i]; if (!b || !b.width) return;
      const node = t.closest('.dg-node');
      if (node) { const r = node.querySelector('rect').getBBox(); if (b.x < r.x - 1 || b.x + b.width > r.x + r.width + 1) out.push({ k: 'text_overflow', svg: id, text: t.textContent.slice(0, 50), by: +(Math.max(r.x - b.x, b.x + b.width - r.x - r.width)).toFixed(1) }); }
      if (vb && (b.x < vb.x - 2 || b.x + b.width > vb.x + vb.width + 2 || b.y < vb.y - 2 || b.y + b.height > vb.y + vb.height + 2)) out.push({ k: 'svg_outside', svg: id, text: t.textContent.slice(0, 50) });
      for (let j = i + 1; j < texts.length; j++) { const c = boxes[j]; if (!c || !c.width) continue; const a = inter(b, c); if (a > 0.15 * Math.min(b.width * b.height, c.width * c.height)) out.push({ k: 'text_overlap', svg: id, text: t.textContent.slice(0, 40) + ' | ' + texts[j].textContent.slice(0, 40) }); }
      if (t.classList.contains('dg-label')) svg.querySelectorAll('.dg-node:not(.dg-off) rect').forEach(r => { const rb = r.getBBox(); if (inter(b, rb) > 0.25 * b.width * b.height) out.push({ k: 'label_on_box', svg: id, text: t.textContent.slice(0, 40) }); });
    });
    // screen-space checks for widget drawings: rotation-aware overlaps, and lines only where visible (not under a later filled shape)
    const scr = texts.map(t => t.getBoundingClientRect());
    const all = [...svg.querySelectorAll('*')];
    const fills = all.filter(e => (e.tagName === 'rect' || e.tagName === 'circle') && getComputedStyle(e).fill !== 'none' && +getComputedStyle(e).fillOpacity > 0.5 && !e.closest('.dg-off'));
    const hidden = (x, y, lineEl) => fills.some(f => all.indexOf(f) > all.indexOf(lineEl) && (() => { const r = f.getBoundingClientRect(); return x > r.left && x < r.right && y > r.top && y < r.bottom; })());
    if (id !== 'diagram' && id !== 'glance') {
      for (let i = 0; i < out.length; i++) if (out[i].svg === id && out[i].k === 'text_overlap') { out.splice(i, 1); i--; }
      texts.forEach((t, i) => { for (let j = i + 1; j < texts.length; j++) { const a = scr[i], c = scr[j]; const ov = Math.max(0, Math.min(a.right, c.right) - Math.max(a.left, c.left)) * Math.max(0, Math.min(a.bottom, c.bottom) - Math.max(a.top, c.top));
        if (ov > 0.15 * Math.min(a.width * a.height, c.width * c.height)) out.push({ k: 'text_overlap', svg: id, text: t.textContent.slice(0, 40) + ' | ' + texts[j].textContent.slice(0, 40) }); } });
    }
    svg.querySelectorAll('line, polyline').forEach(l => {
      if (l.closest('.dg-off') || getComputedStyle(l).display === 'none' || +getComputedStyle(l).strokeOpacity < 0.3) return;
      const sw = parseFloat(getComputedStyle(l).strokeWidth) || 1; if (getComputedStyle(l).stroke === 'none' || sw <= 1.2) return;   // thin gridlines and axes behind labels are normal chart style
      const M = l.getScreenCTM(); if (!M) return;
      const pts = l.tagName === 'line' ? [[+l.getAttribute('x1'), +l.getAttribute('y1')], [+l.getAttribute('x2'), +l.getAttribute('y2')]] : [...l.points].map(q => [q.x, q.y]);
      const P = pts.map(([x, y]) => [M.a * x + M.c * y + M.e, M.b * x + M.d * y + M.f]);
      texts.forEach((t, i) => { const r = scr[i]; if (!r.width) return;
        for (let s = 0; s + 1 < P.length; s++) { const [x1, y1] = P[s], [x2, y2] = P[s + 1]; if (Math.hypot(x2 - x1, y2 - y1) < 10) continue;
          let hit = false; for (let u = 0.02; u < 0.98; u += 0.01) { const x = x1 + (x2 - x1) * u, y = y1 + (y2 - y1) * u;
            if (x > r.left + 1 && x < r.right - 1 && y > r.top + 2 && y < r.bottom - 2 && !hidden(x, y, l)) { hit = true; break; } }
          if (hit) { out.push({ k: 'line_thru_text', svg: id, text: t.textContent.slice(0, 40) }); break; } } });
    });
  });
  const inner = slide.querySelector('.inner') || slide, R = inner.getBoundingClientRect();
  let spill = 0, what = '';
  inner.querySelectorAll('*').forEach(el => {
    if (el.closest('.scroll-x, .tbl, table, pre, .bigmap, .toc, .hbar .lab') || !el.getClientRects().length) return;
    const r = el.getBoundingClientRect(); if (!r.width) return;
    const d = r.right - R.right; if (d > spill + 0.5) { spill = d; what = (el.className && el.className.baseVal === undefined ? el.className : el.tagName) + ': ' + (el.textContent || '').trim().slice(0, 40); }
  });
  if (spill > 4) out.push({ k: 'html_overflow', by: Math.round(spill), text: what });
  return out;
}'''


def main():
    out, pattern, widths = sys.argv[1], sys.argv[2], [int(w) for w in sys.argv[3:]] or [1280, 390]
    decks = sorted(glob.glob(f'{REPO}/{pattern}/index.html'))
    with sync_playwright() as p, open(out, 'w') as f:
        b = p.chromium.launch(channel='chrome', headless=True)
        for W in widths:
            pg = b.new_page(viewport={'width': W, 'height': 900 if W > 600 else 844})
            errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
            for d in decks:
                rel = d[len(REPO) + 1:-len('/index.html')]
                errs.clear()
                pg.goto('file://' + d + '#1'); pg.wait_for_timeout(250)
                n = pg.evaluate("document.querySelectorAll('section.slide').length")
                for i in range(1, n + 1):
                    pg.evaluate(f"location.hash = '#{i}'"); pg.wait_for_timeout(450)
                    title = pg.evaluate("(document.querySelector('section.slide.active h2, section.slide.active h1')||{}).textContent || ''")[:60]
                    for issue in pg.evaluate(JS):
                        issue.update(deck=rel, slide=i, title=title.strip(), w=W)
                        f.write(json.dumps(issue, ensure_ascii=False) + '\n')
                for e in set(errs):
                    f.write(json.dumps({'k': 'js_error', 'deck': rel, 'w': W, 'text': e}) + '\n')
                f.flush()
            pg.close()
        b.close()


if __name__ == '__main__':
    main()
