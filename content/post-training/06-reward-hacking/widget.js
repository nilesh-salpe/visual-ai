(() => {
  const { svg, clear, fmt } = Deck;

  const BON = [[1, 0.0, -0.03, 0.0, 0.0], [2, 0.19, 0.81, 0.414, 0.43], [4, 0.64, 1.45, 0.63, 0.632], [8, 1.2, 2.02, 0.704, 0.7], [16, 1.84, 2.51, 0.671, 0.684], [32, 2.5, 2.91, 0.628, 0.614], [64, 3.17, 3.33, 0.507, 0.507], [128, 3.86, 3.68, 0.419, 0.374], [256, 4.55, 4.01, 0.184, 0.22], [512, 5.24, 4.32, 0.025, 0.052], [1024, 5.93, 4.61, -0.109, -0.129]];
  Deck.bind(['hN'], () => {
    const k = Deck.val('hN'), [n, kl, px, gd] = BON[k]; Deck.out('hNo', n);
    const s = clear(document.getElementById('hSvg')), X = d => 60 + d / 2.5 * 560, Y = v => 215 - (v + 0.4) / 5.2 * 195;
    [0, 1, 2, 3, 4, 5].forEach(v => { svg('line', { x1: 60, x2: 620, y1: Y(v), y2: Y(v), class: 'ln' }, s); svg('text', { x: 52, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm', text: v }, s); });
    const line = (i, c, w, dash) => svg('polyline', { points: BON.map(r => `${X(Math.sqrt(r[1]))},${Y(r[i])}`).join(' '), fill: 'none', style: `stroke:${c};stroke-width:${w}${dash ? ';stroke-dasharray:5 4' : ''}` }, s);
    line(4, 'var(--faint)', 2, true); line(2, 'var(--b)', 3); line(3, 'var(--a)', 3);
    svg('line', { x1: X(Math.sqrt(kl)), x2: X(Math.sqrt(kl)), y1: 15, y2: 215, style: 'stroke:var(--ink);stroke-dasharray:3 3' }, s);
    [0, 0.5, 1, 1.5, 2, 2.5].forEach(d => svg('text', { x: X(d), y: 234, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: d }, s));
    svg('text', { x: 340, y: 254, 'text-anchor': 'middle', class: 'tm', text: 'd = √KL from the base policy' }, s);
    document.getElementById('hOut').innerHTML = `n = ${n}: KL = log n − (n−1)/n = <b>${kl.toFixed(2)}</b> nats. Proxy score ${px.toFixed(2)}, gold change <b>${gd >= 0 ? '+' : ''}${gd.toFixed(2)}</b>${k > 3 ? (gd < 0.6 ? ' (past the peak: the extra proxy score is mostly exploitation)' : '') : ''}.`;
  });
  (() => {
    const s = document.getElementById('sSvg'), ns = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024];
    const ev = n => { let seed = 7 + n, h = 0, L = 0; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647; const g = () => Math.sqrt(-2 * Math.log(Math.max(1e-9, rnd()))) * Math.cos(2 * Math.PI * rnd());
      for (let t = 0; t < 200; t++) { let best = -1e9, bh = 0, bl = 0; for (let i = 0; i < n; i++) { const a = g(), b = g(), p = a + b; if (p > best) { best = p; bh = a; bl = b; } } h += bh; L += bl; } return [h / 200, L / 200]; };
    const R = ns.map(ev), X = i => 70 + i * 54, Y = v => 200 - v / 3 * 170;
    [0, 1, 2, 3].forEach(v => { svg('line', { x1: 60, x2: 620, y1: Y(v), y2: Y(v), class: 'ln' }, s); svg('text', { x: 52, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm', text: v }, s); });
    ns.forEach((n, i) => svg('text', { x: X(i), y: 220, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: n }, s));
    [[0, 'var(--a)'], [1, 'var(--d)']].forEach(([j, c]) => svg('polyline', { points: R.map((r, i) => `${X(i)},${Y(r[j])}`).join(' '), fill: 'none', style: `stroke:${c};stroke-width:3` }, s));
  })();

})();
