(() => {
  const { svg, clear } = Deck;

  /* simulation */
  let mode = 0;
  const D = 64, L = 12;
  const r0 = TX.rng(21), Ws = [...Array(L)].map(() => TX.randMat(D, D, r0, 1 / Math.sqrt(D))), x0 = [...Array(D)].map(() => TX.randn(r0));
  const ln = v => { const m = v.reduce((a, b) => a + b, 0) / v.length, sd = Math.sqrt(v.reduce((a, b) => a + (b - m) ** 2, 0) / v.length) || 1; return v.map(x => (x - m) / sd); };
  const cos = (a, b) => TX.dot(a, b) / Math.sqrt(TX.dot(a, a) * TX.dot(b, b));
  const norm = a => Math.sqrt(TX.dot(a, a));
  const sim = () => {
    const g = Deck.val('rG'); Deck.out('rGo', g.toFixed(2));
    const runs = [0, 1, 2].map(m => {
      let x = x0.slice(); const ns = [norm(x)], cs = [1];
      for (let l = 0; l < L; l++) {
        const f = TX.vecMat(x, Ws[l]).map(v => Math.max(0, v * g) * Math.SQRT2);
        x = m === 0 ? f : TX.add(x, f);
        if (m === 2) x = ln(x);
        ns.push(norm(x)); cs.push(cos(x, x0));
      }
      return { ns, cs };
    });
    const plot = (id, key, log) => {
      const s = clear(document.getElementById(id));
      const Lx = 48, W = 262, T = 10, B = 170;
      const all = runs.flatMap(r => r[key]);
      const lo = log ? Math.log10(Math.max(1e-9, Math.min(...all))) : -0.5, hi = log ? Math.log10(Math.max(...all)) : 1;
      const Y = v => B - ((log ? Math.log10(Math.max(1e-9, v)) : v) - lo) / ((hi - lo) || 1) * (B - T);
      const X = l => Lx + l / L * W;
      svg('line', { x1: Lx, x2: Lx + W, y1: B, y2: B, class: 'ln' }, s);
      [0, 6, 12].forEach(l => svg('text', { x: X(l), y: B + 14, 'text-anchor': 'middle', class: 'tm tc', style: 'font-size:10px', text: l }, s));
      svg('text', { x: Lx + W / 2, y: B + 28, 'text-anchor': 'middle', class: 'tm', style: 'font-size:10px', text: 'sub-layer depth' }, s);
      if (!log) [-.5, 0, .5, 1].forEach(v => svg('text', { x: Lx - 4, y: Y(v) + 3, 'text-anchor': 'end', class: 'tm tc', style: 'font-size:9.5px', text: v }, s));
      else [lo, hi].forEach(v => svg('text', { x: Lx - 4, y: Y(10 ** v) + 3, 'text-anchor': 'end', class: 'tm tc', style: 'font-size:9.5px', text: (10 ** v) < 0.01 || (10 ** v) > 999 ? (10 ** v).toExponential(0) : (10 ** v).toPrecision(2) }, s));
      runs.forEach((run, m) => {
        const on = m === mode;
        svg('polyline', { points: run[key].map((v, l) => `${X(l)},${Y(v)}`).join(' '), fill: 'none', style: `stroke:${['var(--d)', 'var(--b)', 'var(--e)'][m]};stroke-width:${on ? 3.5 : 1.2};opacity:${on ? 1 : .35}` }, s);
      });
    };
    plot('nSvg', 'ns', true); plot('cSvg', 'cs', false);
  };
  Deck.seg('rSeg', v => { mode = +v; if (document.getElementById('rG')) sim(); });
  Deck.bind(['rG'], sim);

  /* wrapper diagram */
  (() => {
    const s = document.getElementById('wSvg');
    TX.arrowDefs(s, 'wa', 'var(--muted)'); TX.arrowDefs(s, 'ws', 'var(--a)');
    TX.box(s, 10, 90, 70, 40, 'var(--faint)', 'x');
    TX.arrow(s, 82, 110, 128, 110, 'wa');
    TX.box(s, 132, 85, 150, 50, 'var(--b)', 'Sublayer\n(attention or FFN)');
    TX.arrow(s, 284, 110, 318, 110, 'wa');
    TX.box(s, 322, 92, 80, 36, 'var(--faint)', 'Dropout');
    TX.arrow(s, 404, 110, 440, 110, 'wa');
    svg('circle', { cx: 458, cy: 110, r: 16, style: 'fill:var(--a)' }, s);
    svg('text', { x: 458, y: 116, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:18px;font-weight:700', text: '+' }, s);
    svg('polyline', { points: '45,90 45,40 458,40 458,92', fill: 'none', style: 'stroke:var(--a);stroke-width:3;stroke-dasharray:7 5', 'marker-end': 'url(#ws)' }, s);
    svg('text', { x: 250, y: 32, 'text-anchor': 'middle', class: 't', style: 'fill:var(--a);font-weight:600;font-size:12px', text: 'residual (identity) path: x' }, s);
    TX.arrow(s, 476, 110, 506, 110, 'wa');
    TX.box(s, 510, 88, 100, 44, 'var(--e)', 'LayerNorm');
    TX.arrow(s, 612, 110, 650, 110, 'wa');
    svg('text', { x: 330, y: 185, 'text-anchor': 'middle', class: 't tc', style: 'font-size:13px', text: 'output = LayerNorm( x + Dropout(Sublayer(x)) )      [n × 512 → n × 512]' }, s);
  })();

  /* LN demo */
  let seed = 4;
  const lnDemo = () => {
    const k = Deck.val('lS'), b = Deck.val('lB'); Deck.out('lSo', '×' + k.toFixed(1)); Deck.out('lBo', (b >= 0 ? '+' : '') + b.toFixed(1));
    const r = TX.rng(seed), base = [...Array(8)].map(() => TX.randn(r));
    const x = base.map(v => v * k + b), m = x.reduce((a, c) => a + c, 0) / 8, sd = Math.sqrt(x.reduce((a, c) => a + (c - m) ** 2, 0) / 8), y = x.map(v => (v - m) / sd);
    const s = clear(document.getElementById('lSvg'));
    const panel = (x0, vals, title, sub, color, lim) => {
      svg('text', { x: x0, y: 16, class: 't', style: 'font-weight:700', text: title }, s);
      svg('text', { x: x0, y: 32, class: 'tm tc', style: 'font-size:10.5px', text: sub }, s);
      const mid = 125, sc = 75 / lim;
      svg('line', { x1: x0, x2: x0 + 280, y1: mid, y2: mid, class: 'ln' }, s);
      vals.forEach((v, i) => {
        const h = Math.max(-80, Math.min(80, v * sc));
        svg('rect', { x: x0 + 4 + i * 34, y: h >= 0 ? mid - h : mid, width: 28, height: Math.abs(h) || 1, rx: 3, style: `fill:${v >= 0 ? color : 'var(--d)'}` }, s);
        svg('text', { x: x0 + 18 + i * 34, y: h >= 0 ? mid - h - 4 : mid - h + 12, 'text-anchor': 'middle', class: 'tm tc', style: 'font-size:9.5px', text: v.toFixed(1) }, s);
      });
    };
    panel(10, x, 'input x (one token, 8 of 512 dims)', `μ = ${m.toFixed(2)}   σ = ${sd.toFixed(2)}`, 'var(--faint)', Math.max(3, ...x.map(Math.abs)));
    panel(360, y, '(x − μ) / σ', 'μ = 0.00   σ = 1.00  (then γ, β)', 'var(--e)', 3);
    svg('text', { x: 330, y: 220, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: 'Rescaling or shifting the whole input leaves the normalized vector unchanged.' }, s);
  };
  document.getElementById('lNew').onclick = () => { seed++; lnDemo(); };
  Deck.bind(['lS', 'lB'], lnDemo);
})();
