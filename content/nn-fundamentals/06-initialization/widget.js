(() => {
  const { svg, clear, fmt } = Deck;
  let kind = 'he', act = 'relu';
  const rnd = (() => { let s = 1; return () => { s = (s * 16807) % 2147483647; return s / 2147483647; }; })();
  const gauss = () => { let u = 0, v = 0; while (!u) u = rnd(); v = rnd(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
  const draw = () => {
    const n = 64, B = 64, L = 50, sd = kind === 'naive' ? 1 : kind === 'xavier' ? Math.sqrt(2 / (2 * n)) : Math.sqrt(2 / n);
    let h = [...Array(B)].map(() => [...Array(n)].map(gauss)); const out = [];
    for (let l = 0; l < L; l++) {
      const W = [...Array(n)].map(() => [...Array(n)].map(() => gauss() * sd));
      h = h.map(r => { const o = new Array(n).fill(0); for (let i = 0; i < n; i++) { const ri = r[i]; if (ri === 0) continue; const Wi = W[i]; for (let j = 0; j < n; j++) o[j] += ri * Wi[j]; } return o.map(z => act === 'relu' ? Math.max(0, z) : Math.tanh(z)); });
      let s2 = 0, m = 0; h.forEach(r => r.forEach(v => { m += v; s2 += v * v; })); m /= n * B; out.push(Math.sqrt(Math.max(1e-300, s2 / (n * B) - m * m)));
    }
    const s = clear(document.getElementById('iSvg')), X = l => 60 + l / (L - 1) * 570, lg = v => Math.log10(Math.max(1e-30, Math.min(1e30, v))), Y = v => 115 - lg(v) / 30 * 95;
    [-30, -15, 0, 15, 30].forEach(e => { svg('line', { x1: 60, x2: 630, y1: Y(Math.pow(10, e)), y2: Y(Math.pow(10, e)), class: 'ln', style: e ? 'opacity:.4' : '' }, s); svg('text', { x: 52, y: Y(Math.pow(10, e)) + 4, 'text-anchor': 'end', class: 'tm', text: '1e' + e }, s); });
    svg('polyline', { points: out.map((v, l) => `${X(l)},${Y(v)}`).join(' '), fill: 'none', style: 'stroke:var(--a);stroke-width:3' }, s);
    [1, 10, 20, 30, 40, 50].forEach(l => svg('text', { x: X(l - 1), y: 228, 'text-anchor': 'middle', class: 'tm', text: 'layer ' + l }, s));
    const last = out[L - 1];
    document.getElementById('iOut').innerHTML = `Std after layer 1: ${out[0].toPrecision(3)}, after layer 50: <b>${last.toExponential(2)}</b>. ${act === 'tanh' && kind === 'naive' ? 'tanh units are saturated at ±1: the signal is bounded, but gradients through them are ≈ 0.' : Math.abs(lg(last / out[0])) < 1 ? 'Stable: the variance budget is balanced.' : last < out[0] ? 'Vanishing.' : 'Exploding.'}`;
  };
  Deck.seg('iSeg', v => { kind = v; draw(); }); Deck.seg('iAct', v => { act = v; draw(); });
})();
