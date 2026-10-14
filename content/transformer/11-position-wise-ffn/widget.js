(() => {
  const { svg, clear, fmt } = Deck;

  /* convex hull */
  const VALS = [[120, 60], [300, 40], [360, 200], [150, 220]], COLS = ['var(--a)', 'var(--b)', 'var(--c)', 'var(--e)'];
  let seed = 2;
  const hull = () => {
    const r = TX.rng(seed), w = TX.softmax([...Array(4)].map(() => TX.randn(r) * 1.5));
    const out = [0, 1].map(d => w.reduce((a, wi, i) => a + wi * VALS[i][d], 0));
    const s = clear(document.getElementById('hullSvg'));
    svg('polygon', { points: VALS.map(p => p.join(',')).join(' '), style: 'fill:var(--a-soft);stroke:var(--a);stroke-dasharray:5 4' }, s);
    VALS.forEach((p, i) => {
      svg('line', { x1: p[0], y1: p[1], x2: out[0], y2: out[1], style: `stroke:${COLS[i]};stroke-width:${1 + 8 * w[i]};opacity:.7` }, s);
      svg('circle', { cx: p[0], cy: p[1], r: 9, style: `fill:${COLS[i]}` }, s);
      svg('text', { x: p[0] + (p[0] > 250 ? 14 : -14), y: p[1] + 4, 'text-anchor': p[0] > 250 ? 'start' : 'end', class: 't', style: 'font-size:12px;font-weight:600', text: `v${i + 1} (w = ${(w[i] * 100).toFixed(0)}%)` }, s);
    });
    svg('circle', { cx: out[0], cy: out[1], r: 9, style: 'fill:var(--ink);stroke:var(--panel);stroke-width:3' }, s);
    svg('text', { x: out[0] + 12, y: out[1] - 10, class: 't', style: 'font-weight:700', text: 'output' }, s);
    svg('text', { x: 450, y: 110, class: 't', style: 'font-size:12.5px', text: 'output = Σ wᵢ vᵢ,  wᵢ ≥ 0,  Σ wᵢ = 1' }, s);
    svg('text', { x: 450, y: 134, class: 'tm', style: 'font-size:12px', text: '→ always inside the shaded region' }, s);
    svg('text', { x: 450, y: 158, class: 'tm', style: 'font-size:11px', text: '(2-D picture of 64-dim value vectors)' }, s);
    Deck.out('hullOut', 'weights: ' + w.map(x => (x * 100).toFixed(0) + '%').join(' · '));
  };
  document.getElementById('hullBtn').onclick = () => { seed++; hull(); };
  hull();

  /* position-wise diagram */
  (() => {
    const s = document.getElementById('posSvg');
    TX.arrowDefs(s, 'pa', 'var(--muted)');
    const T = ['Die', 'Katze', 'saß', 'auf', 'der', 'Matte'];
    T.forEach((t, i) => {
      const x = 20 + i * 106;
      TX.box(s, x, 210, 90, 30, 'var(--panel-2)', t, { text: 'var(--ink)', stroke: 'var(--line)' });
      TX.arrow(s, x + 45, 208, x + 45, 182, 'pa');
      TX.box(s, x + 5, 150, 80, 30, 'var(--faint)', '512');
      TX.arrow(s, x + 45, 148, x + 45, 128, 'pa');
      TX.box(s, x, 96, 90, 30, '#3a8fd8', '2048 · ReLU');
      TX.arrow(s, x + 45, 94, x + 45, 74, 'pa');
      TX.box(s, x + 5, 42, 80, 30, 'var(--a)', '512');
    });
    svg('rect', { x: 14, y: 90, width: 632, height: 42, rx: 8, style: 'fill:none;stroke:#3a8fd8;stroke-width:2;stroke-dasharray:6 4' }, s);
    svg('text', { x: 330, y: 22, 'text-anchor': 'middle', class: 't', style: 'font-size:12.5px', text: 'same W₁, b₁, W₂, b₂ at every position · no arrows between positions' }, s);
  })();

  /* toy FFN */
  const r = TX.rng(17), W1 = TX.randMat(4, 8, r, .8), b1 = [...Array(8)].map(() => TX.randn(r) * .3), W2 = TX.randMat(8, 4, r, .6);
  const A = [1.0, -0.4, 0.6, 0.2], B = [-0.5, 0.9, -0.2, 0.7];
  Deck.bind(['fT'], () => {
    const t = Deck.val('fT'); Deck.out('fTo', t.toFixed(2));
    const x = A.map((a, i) => a * (1 - t) + B[i] * t);
    const pre = TX.add(TX.vecMat(x, W1), b1), h = pre.map(v => Math.max(0, v)), y = TX.vecMat(h, W2);
    const s = clear(document.getElementById('ffSvg'));
    TX.arrowDefs(s, 'fa', 'var(--muted)');
    svg('text', { x: 20, y: 20, class: 't', style: 'font-weight:700', text: 'x (4)' }, s);
    TX.vec(s, x, { x: 20, y: 30, cell: 42, vals: true, vertical: true, max: 1.2 });
    TX.arrow(s, 70, 115, 150, 115, 'fa'); svg('text', { x: 110, y: 105, 'text-anchor': 'middle', class: 'tm tc', style: 'font-size:11px', text: 'W₁, b₁' }, s);
    svg('text', { x: 160, y: 20, class: 't', style: 'font-weight:700', text: 'xW₁ + b₁ (8)' }, s);
    TX.vec(s, pre, { x: 160, y: 30, cell: 26, vals: true, vertical: true, max: 2 });
    TX.arrow(s, 196, 115, 276, 115, 'fa'); svg('text', { x: 236, y: 105, 'text-anchor': 'middle', class: 'tm tc', style: 'font-size:11px', text: 'ReLU' }, s);
    svg('text', { x: 286, y: 20, class: 't', style: 'font-weight:700', text: 'hidden (8)' }, s);
    h.forEach((v, i) => {
      svg('rect', { x: 286, y: 30 + i * 26, width: 24, height: 24, rx: 3, style: v > 0 ? `fill:#3a8fd8;opacity:${.25 + .75 * Math.min(1, v / 1.5)}` : 'fill:var(--panel-2);stroke:var(--line);stroke-dasharray:2 2' }, s);
      svg('text', { x: 318, y: 46 + i * 26, class: 'tm tc', style: 'font-size:10px', text: v > 0 ? v.toFixed(2) : 'off' }, s);
    });
    TX.arrow(s, 360, 115, 440, 115, 'fa'); svg('text', { x: 400, y: 105, 'text-anchor': 'middle', class: 'tm tc', style: 'font-size:11px', text: 'W₂' }, s);
    svg('text', { x: 450, y: 20, class: 't', style: 'font-weight:700', text: 'FFN(x) (4)' }, s);
    TX.vec(s, y, { x: 450, y: 30, cell: 42, vals: true, vertical: true, max: 1.5 });
    svg('text', { x: 520, y: 120, class: 'tm', style: 'font-size:11.5px', text: `${h.filter(v => v > 0).length} of 8 hidden units on` }, s);
  });

  /* param bars */
  Deck.hbars(document.getElementById('pBars'), [
    { label: 'Self-attention', value: 4 * 512 * 512, color: 'var(--b)', text: fmt(4 * 512 * 512) + ' · 33%' },
    { label: 'FFN', value: 2 * 512 * 2048, color: '#3a8fd8', text: fmt(2 * 512 * 2048) + ' · 67%' },
  ]);
  Deck.hbars(document.getElementById('dBars'), [
    { label: 'd_ff = 1024', value: 25.4 - 24.5, color: 'var(--line)', text: '25.4' },
    { label: 'd_ff = 2048 (base)', value: 25.8 - 24.5, color: 'var(--a)', text: '25.8' },
    { label: 'd_ff = 4096', value: 26.2 - 24.5, color: 'var(--e)', text: '26.2' },
  ], { max: 2 });
})();
