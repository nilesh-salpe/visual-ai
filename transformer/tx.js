// Shared helpers for the "Attention Is All You Need" decks: math on toy vectors,
// token rows, attention arcs, heatmaps and vector strips. Depends on shared/deck.js.
const TX = (() => {
  const { svg } = Deck;
  const HEADS = ['#0d8487', '#d9731a', '#6a4fd3', '#2e7d32', '#cf3f55', '#3a8fd8', '#c9a227', '#8a6d3b'];

  const softmax = a => {
    const fin = a.filter(isFinite), m = fin.length ? Math.max(...fin) : 0;
    const e = a.map(x => isFinite(x) ? Math.exp(x - m) : 0), s = e.reduce((p, q) => p + q, 0) || 1;
    return e.map(x => x / s);
  };
  const dot = (a, b) => a.reduce((s, x, i) => s + x * b[i], 0);
  const vecMat = (x, W) => W[0].map((_, j) => x.reduce((s, xi, i) => s + xi * W[i][j], 0)); // x[1×n]·W[n×m]
  const matMul = (A, B) => A.map(r => vecMat(r, B));
  const T = A => A[0].map((_, j) => A.map(r => r[j]));
  const add = (a, b) => a.map((x, i) => x + b[i]);
  const scale = (a, k) => a.map(x => x * k);
  const rng = seed => () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  const randn = r => { let u = 0, v = 0; while (!u) u = r(); while (!v) v = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
  const randMat = (rows, cols, r, sd = 1) => [...Array(rows)].map(() => [...Array(cols)].map(() => randn(r) * sd));
  const f2 = x => (Math.abs(x) < 0.005 ? 0 : x).toFixed(2);
  const pe = (pos, i, d) => { const k = Math.floor(i / 2), w = 1 / Math.pow(10000, 2 * k / d); return i % 2 ? Math.cos(pos * w) : Math.sin(pos * w); };

  // Row of token boxes. Returns centers [{x,y,w}]. opts: x0,y,width,h,sel,color(i),textColor,font
  function tokens(s, toks, o = {}) {
    const x0 = o.x0 ?? 10, width = o.width ?? 640, h = o.h ?? 30, y = o.y ?? 10, gap = o.gap ?? 6;
    const w = (width - gap * (toks.length - 1)) / toks.length, out = [];
    toks.forEach((t, i) => {
      const x = x0 + i * (w + gap), on = o.sel === i;
      const g = svg('g', { 'data-tok': i, style: o.click ? 'cursor:pointer' : '' }, s);
      const fill = o.color ? o.color(i) : on ? 'var(--a)' : 'var(--panel-2)';
      svg('rect', { x, y, width: w, height: h, rx: 6, style: `fill:${fill};stroke:${on ? 'var(--ink)' : 'var(--line)'};stroke-width:${on ? 2 : 1}` }, g);
      const fs = Math.min(o.font ?? 13, w / Math.max(3, t.length) * 1.7);
      svg('text', { x: x + w / 2, y: y + h / 2 + fs * .36, 'text-anchor': 'middle', class: 't', style: `font-size:${fs}px;font-weight:600;fill:${o.textColor ? o.textColor(i) : on ? '#fff' : 'var(--ink)'}`, text: t }, g);
      if (o.index) svg('text', { x: x + w / 2, y: y + h + 13, 'text-anchor': 'middle', class: 'tm tc', style: 'font-size:10px', text: i }, g);
      out.push({ x: x + w / 2, y, w, h, left: x });
    });
    return out;
  }

  // Arcs from token `from` to every token j, thickness ∝ weights[j]. Above (y = top) or below.
  function arcs(s, pos, from, weights, o = {}) {
    const color = o.color || 'var(--b)', below = !!o.below, maxW = Math.max(...weights);
    weights.forEach((w, j) => {
      if (w < (o.min ?? 0.01)) return;
      const a = pos[from], b = pos[j];
      const y0 = below ? a.y + a.h : a.y, dir = below ? 1 : -1;
      const hgt = j === from ? 26 : Math.min(o.maxH ?? 120, 18 + Math.abs(a.x - b.x) * .35);
      const d = j === from
        ? `M ${a.x - 8} ${y0} C ${a.x - 22} ${y0 + dir * hgt}, ${a.x + 22} ${y0 + dir * hgt}, ${a.x + 8} ${y0}`
        : `M ${a.x} ${y0} Q ${(a.x + b.x) / 2} ${y0 + dir * hgt * 1.6} ${b.x} ${y0}`;
      svg('path', { d, fill: 'none', style: `stroke:${color};stroke-width:${1 + 9 * w / (o.norm ? maxW : 1)};opacity:${.25 + .75 * w / maxW};stroke-linecap:round` }, s);
    });
  }

  // Heatmap. M rows×cols. o: x,y,cell,rows,cols(labels),color,max,vals(bool),fmt,neg(diverging)
  function heat(s, M, o = {}) {
    const x = o.x ?? 60, y = o.y ?? 30, c = o.cell ?? 34, color = o.color || 'var(--b)';
    const flat = M.flat().filter(isFinite), max = o.max ?? Math.max(...flat.map(Math.abs), 1e-9);
    M.forEach((row, i) => row.forEach((v, j) => {
      const cx = x + j * c, cy = y + i * c;
      if (!isFinite(v)) {
        svg('rect', { x: cx, y: cy, width: c - 2, height: c - 2, rx: 3, style: 'fill:var(--panel-2);stroke:var(--d);stroke-width:1;stroke-dasharray:3 2' }, s);
        if (o.vals !== false) svg('text', { x: cx + c / 2 - 1, y: cy + c / 2 + 4, 'text-anchor': 'middle', class: 'tc', style: `fill:var(--d);font-size:${Math.min(12, c * .36)}px;font-weight:700`, text: '−∞' }, s);
        return;
      }
      const neg = o.neg && v < 0, a = Math.min(1, Math.abs(v) / max);
      svg('rect', { x: cx, y: cy, width: c - 2, height: c - 2, rx: 3, style: `fill:${neg ? 'var(--d)' : color};opacity:${.08 + .92 * a}` }, s);
      if (o.vals !== false && c >= 22) svg('text', { x: cx + c / 2 - 1, y: cy + c / 2 + 4, 'text-anchor': 'middle', class: 'tc', style: `fill:${a > .55 ? '#fff' : 'var(--ink)'};font-size:${Math.min(11, c * .32)}px;font-weight:600`, text: (o.fmt || f2)(v) }, s);
    }));
    (o.rows || []).forEach((t, i) => svg('text', { x: x - 6, y: y + i * c + c / 2 + 4, 'text-anchor': 'end', class: 'tm', style: 'font-size:11.5px', text: t }, s));
    (o.cols || []).forEach((t, j) => svg('text', { x: x + j * c + c / 2 - 1, y: y - 8, 'text-anchor': o.rotate ? 'start' : 'middle', transform: o.rotate ? `rotate(-45 ${x + j * c + c / 2} ${y - 8})` : '', class: 'tm', style: 'font-size:11.5px', text: t }, s));
    return { w: M[0].length * c, h: M.length * c };
  }

  // A vector as a strip of cells (diverging: teal +, red −).
  function vec(s, v, o = {}) {
    const x = o.x ?? 0, y = o.y ?? 0, c = o.cell ?? 18, max = o.max ?? Math.max(...v.map(Math.abs), 1e-9), vertical = !!o.vertical;
    v.forEach((val, i) => {
      const a = Math.min(1, Math.abs(val) / max);
      const cx = vertical ? x : x + i * c, cy = vertical ? y + i * c : y;
      svg('rect', { x: cx, y: cy, width: c - 2, height: c - 2, rx: 2, style: `fill:${val >= 0 ? (o.color || 'var(--a)') : 'var(--d)'};opacity:${.12 + .88 * a}` }, s);
      if (o.vals) svg('text', { x: cx + (c - 2) / 2, y: cy + c / 2 + 3, 'text-anchor': 'middle', class: 'tc', style: `font-size:${Math.min(10, c * .34)}px;fill:${a > .55 ? '#fff' : 'var(--ink)'}`, text: f2(val) }, s);
    });
    if (o.label) svg('text', { x: vertical ? x + c / 2 : x - 6, y: vertical ? y - 6 : y + c / 2 + 3, 'text-anchor': vertical ? 'middle' : 'end', class: 'tm', style: 'font-size:11px', text: o.label }, s);
  }

  function arrowDefs(s, id, color = 'var(--muted)') {
    const defs = svg('defs', {}, s), m = svg('marker', { id, viewBox: '0 0 10 10', refX: 8, refY: 5, markerWidth: 9, markerHeight: 9, markerUnits: 'userSpaceOnUse', orient: 'auto-start-reverse' }, defs);
    svg('path', { d: 'M0,0 L10,5 L0,10 z', style: `fill:${color}` }, m);
  }
  function box(s, x, y, w, h, fill, label, o = {}) {
    const g = svg('g', o.attrs || {}, s);
    svg('rect', { x, y, width: w, height: h, rx: o.rx ?? 7, style: `fill:${fill};${o.stroke ? 'stroke:' + o.stroke + ';' : ''}` }, g);
    if (label) String(label).split('\n').forEach((ln, k, arr) => svg('text', { x: x + w / 2, y: y + h / 2 + 4 + (k - (arr.length - 1) / 2) * 14, 'text-anchor': 'middle', class: 't', style: `fill:${o.text || '#fff'};font-size:${o.fs || 12}px;font-weight:${o.fw || 600}`, text: ln }, g));
    return g;
  }
  const arrow = (s, x1, y1, x2, y2, id = 'ar', color = 'var(--muted)', w = 2) => svg('line', { x1, y1, x2, y2, style: `stroke:${color};stroke-width:${w}`, 'marker-end': `url(#${id})` }, s);

  return { HEADS, softmax, dot, vecMat, matMul, T, add, scale, rng, randn, randMat, f2, pe, tokens, arcs, heat, vec, arrowDefs, box, arrow };
})();

// Quiz / reveal behaviour for "Your turn", "Misconceptions" and "Check yourself" beats.
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.quiz').forEach(q => {
    const btns = [...q.querySelectorAll('.opts button')];
    btns.forEach(b => b.addEventListener('click', () => {
      if (q.classList.contains('done')) return;
      q.classList.add('done');
      btns.forEach(x => { x.disabled = true; if (x.hasAttribute('data-ok')) x.classList.add('right'); });
      if (!b.hasAttribute('data-ok')) b.classList.add('wrong');
    }));
    const r = q.querySelector('.reveal');
    if (r) r.addEventListener('click', () => q.classList.add('done'));
  });
});
