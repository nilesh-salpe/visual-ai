(() => {
  const { svg, clear, fmt } = Deck;

  Deck.seg('wSeg', v => {
    const s = clear(document.getElementById('wSvg')), pre = v === 'pre';
    const box = (x, label, cls) => { svg('rect', { x, y: 70, width: 110, height: 44, rx: 8, class: cls }, s); svg('text', { x: x + 55, y: 97, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:600', text: label }, s); };
    svg('line', { x1: 20, x2: 640, y1: 40, y2: 40, style: 'stroke:var(--a);stroke-width:5' }, s);
    svg('text', { x: 24, y: 28, class: 'tm', text: 'x (residual stream)' }, s);
    if (pre) {
      svg('path', { d: 'M120 40 V92 H150', fill: 'none', style: 'stroke:var(--muted);stroke-width:2' }, s);
      box(150, 'Norm', 'f-c'); box(300, 'F (attn/FFN)', 'f-b');
      svg('line', { x1: 260, x2: 300, y1: 92, y2: 92, style: 'stroke:var(--muted);stroke-width:2' }, s);
      svg('path', { d: 'M410 92 H470 V48', fill: 'none', style: 'stroke:var(--muted);stroke-width:2' }, s);
      svg('circle', { cx: 470, cy: 40, r: 12, style: 'fill:var(--panel);stroke:var(--a);stroke-width:2' }, s); svg('text', { x: 470, y: 45, 'text-anchor': 'middle', class: 't', text: '+' }, s);
      svg('text', { x: 330, y: 160, 'text-anchor': 'middle', class: 'tm', text: 'x ← x + F(Norm(x)): the thick line never passes through a norm' }, s);
    } else {
      svg('path', { d: 'M120 40 V92 H190', fill: 'none', style: 'stroke:var(--muted);stroke-width:2' }, s);
      box(190, 'F (attn/FFN)', 'f-b');
      svg('path', { d: 'M300 92 H380 V48', fill: 'none', style: 'stroke:var(--muted);stroke-width:2' }, s);
      svg('circle', { cx: 380, cy: 40, r: 12, style: 'fill:var(--panel);stroke:var(--a);stroke-width:2' }, s); svg('text', { x: 380, y: 45, 'text-anchor': 'middle', class: 't', text: '+' }, s);
      svg('rect', { x: 440, y: 18, width: 90, height: 44, rx: 8, class: 'f-d' }, s); svg('text', { x: 485, y: 45, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:600', text: 'Norm' }, s);
      svg('text', { x: 330, y: 160, 'text-anchor': 'middle', class: 'tm', text: 'x ← Norm(x + F(x)): the main path is renormalized after every sub-layer' }, s);
    }
    document.getElementById('wOut').innerHTML = pre
      ? 'After L layers: output = x₀ + F₁ + F₂ + … + F_L, then one final norm. Every layer has a direct, un-rescaled route to the output.'
      : 'After L layers the signal from layer 1 has passed through L norms. Each one rescales it, and gradients near the output are large at initialization.';
  });
  (() => {
    const D = [3, 6, 12, 24, 48], post = [190.6, 207.1, 192.0, 166.4, 204.1], pre = [163.2, 147.0, 107.3, 67.4, 56.3];
    const s = document.getElementById('gSvg'), L0 = 70, R0 = 620, T0 = 16, B0 = 200, X = i => L0 + i * (R0 - L0) / 4, Y = v => B0 - v / 240 * (B0 - T0);
    [0, 60, 120, 180, 240].forEach(v => { svg('line', { x1: L0, x2: R0, y1: Y(v), y2: Y(v), class: 'ln' }, s); svg('text', { x: L0 - 8, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm', text: v }, s); });
    D.forEach((d, i) => svg('text', { x: X(i), y: B0 + 18, 'text-anchor': 'middle', class: 'tm', text: 'L=' + d }, s));
    const line = (vals, color, dash) => svg('polyline', { points: vals.map((v, i) => `${X(i)},${Y(v)}`).join(' '), fill: 'none', style: `stroke:${color};stroke-width:3${dash ? ';stroke-dasharray:6 5' : ''}` }, s);
    line(D.map(d => pre[0] * Math.sqrt(3 / d)), 'var(--faint)', true); line(post, 'var(--d)'); line(pre, 'var(--a)');
    [[post, 'var(--d)'], [pre, 'var(--a)']].forEach(([v, c]) => v.forEach((y, i) => svg('circle', { cx: X(i), cy: Y(y), r: 5, style: `fill:${c}` }, s)));
    svg('text', { x: (L0 + R0) / 2, y: B0 + 40, 'text-anchor': 'middle', class: 'tm', text: 'number of blocks (log-spaced)' }, s);
    svg('text', { x: 16, y: (T0 + B0) / 2, 'text-anchor': 'middle', class: 'tm', transform: `rotate(-90 16 ${(T0 + B0) / 2})`, text: '|grad| of last layer' }, s);
  })();
  const base = [1.2, -0.4, 2.1, 0.3, -1.5, 0.9, 1.8, -0.6];
  Deck.bind(['nS', 'nK'], () => {
    const sh = Deck.val('nS'), k = Deck.val('nK'); Deck.out('nSo', sh.toFixed(1)); Deck.out('nKo', k.toFixed(1) + '×');
    const x = base.map(v => (v + sh) * k), n = x.length, mu = x.reduce((a, b) => a + b) / n;
    const sd = Math.sqrt(x.reduce((a, b) => a + (b - mu) ** 2, 0) / n + 1e-6), rms = Math.sqrt(x.reduce((a, b) => a + b * b, 0) / n + 1e-6);
    const ln = x.map(v => (v - mu) / sd), rn = x.map(v => v / rms);
    const s = clear(document.getElementById('nSvg')), groups = [['input x', x, 'var(--faint)'], ['LayerNorm', ln, 'var(--c)'], ['RMSNorm', rn, 'var(--a)']];
    groups.forEach(([name, v, c], gi) => {
      const x0 = 20 + gi * 215, mid = 120, sc = 22;
      svg('text', { x: x0 + 95, y: 16, 'text-anchor': 'middle', class: 't', style: 'font-weight:600', text: name }, s);
      svg('line', { x1: x0, x2: x0 + 190, y1: mid, y2: mid, class: 'ln' }, s);
      v.forEach((val, i) => { const h = Math.max(-95, Math.min(95, val * sc)); svg('rect', { x: x0 + 6 + i * 23, y: h > 0 ? mid - h : mid, width: 17, height: Math.abs(h), rx: 3, style: `fill:${c}` }, s); });
      const m = v.reduce((a, b) => a + b) / n, r = Math.sqrt(v.reduce((a, b) => a + b * b, 0) / n);
      svg('text', { x: x0 + 95, y: 222, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: `mean ${m.toFixed(2)} · rms ${r.toFixed(2)}` }, s);
    });
    document.getElementById('nOut').innerHTML = sh === 0 ? 'Move the shift slider: LayerNorm\'s bars stay put, RMSNorm\'s change. Move scale: neither changes.' : `With a shift of ${sh.toFixed(1)}, RMSNorm output mean = <b>${(rn.reduce((a, b) => a + b) / n).toFixed(2)}</b> (it keeps the offset), while LayerNorm's mean stays <b>0.00</b>.`;
  });

})();
