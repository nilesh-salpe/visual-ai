(() => {
  const { svg, clear, fmt } = Deck;
  const rnd = (() => { let s = 7; return () => { s = (s * 16807) % 2147483647; return s / 2147483647; }; })();
  const gauss = () => { let u = 0; while (!u) u = rnd(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * rnd()); };
  const n = 48, B = 32, L = 64;
  const Ws = [...Array(L)].map(() => [...Array(n)].map(() => [...Array(n)].map(gauss)));
  const X0 = [...Array(B)].map(() => [...Array(n)].map(gauss));
  const mm = (h, W, sd) => h.map(r => { const o = new Array(n).fill(0); for (let i = 0; i < n; i++) { const ri = r[i]; if (!ri) continue; for (let j = 0; j < n; j++) o[j] += ri * W[i][j] * sd; } return o.map(z => Math.max(0, z)); });
  const rms = h => h.map(r => { const s = Math.sqrt(r.reduce((a, v) => a + v * v, 0) / n) || 1; return r.map(v => v / s); });
  const std = h => { let s = 0; h.forEach(r => r.forEach(v => { s += v * v; })); return Math.sqrt(s / (n * B)); };
  Deck.bind(['rG'], () => {
    const g = Deck.val('rG'), sd = g / Math.sqrt(n); Deck.out('rGo', g.toFixed(2));
    const runs = { plain: [], res: [], pre: [] }; let a = X0, b = X0, c = X0;
    for (let l = 0; l < L; l++) {
      a = mm(a, Ws[l], sd); runs.plain.push(std(a));
      const fb = mm(b, Ws[l], sd); b = b.map((r, i) => r.map((v, j) => v + fb[i][j] / Math.SQRT2)); runs.res.push(std(b));
      const fc = mm(rms(c), Ws[l], sd); c = c.map((r, i) => r.map((v, j) => v + fc[i][j] / Math.SQRT2)); runs.pre.push(std(c));
    }
    const s = clear(document.getElementById('rSvg')), X = l => 60 + l / (L - 1) * 570, lg = v => Math.log10(Math.max(1e-12, Math.min(1e12, v))), Y = v => 120 - lg(v) / 12 * 100;
    [-12, -6, 0, 6, 12].forEach(e => { svg('line', { x1: 60, x2: 630, y1: Y(Math.pow(10, e)), y2: Y(Math.pow(10, e)), class: 'ln', style: e ? 'opacity:.4' : '' }, s); svg('text', { x: 52, y: Y(Math.pow(10, e)) + 4, 'text-anchor': 'end', class: 'tm', text: '1e' + e }, s); });
    [['plain', 'var(--d)', 'plain x ← f(x)'], ['res', 'var(--b)', 'residual x ← x + f(x)'], ['pre', 'var(--e)', 'pre-norm x ← x + f(Norm(x))']].forEach(([k, col, lab], i) => {
      svg('polyline', { points: runs[k].map((v, l) => `${X(l)},${Y(v)}`).join(' '), fill: 'none', style: `stroke:${col};stroke-width:3` }, s);
      svg('text', { x: 70 + i * 190, y: 236, class: 't', style: `fill:${col};font-weight:700;font-size:12px`, text: lab }, s); });
    const f = k => runs[k][L - 1].toExponential(1);
    document.getElementById('rOut').innerHTML = `After 64 blocks, std: plain <b>${f('plain')}</b>, residual <b>${f('res')}</b>, pre-norm <b>${f('pre')}</b>. Pre-norm grows only slowly (about √depth) for any gain, because each branch sees a normalised input.`;
  });
})();
