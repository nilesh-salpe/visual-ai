(() => {
  const { svg, clear, fmt } = Deck;
  const erf = x => { const t = 1 / (1 + 0.3275911 * Math.abs(x)), y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x); return x >= 0 ? y : -y; };
  const sig = z => 1 / (1 + Math.exp(-z)), Phi = z => 0.5 * (1 + erf(z / Math.SQRT2)), phi = z => Math.exp(-z * z / 2) / Math.sqrt(2 * Math.PI);
  const A = { sigmoid: [sig, z => sig(z) * (1 - sig(z))], tanh: [Math.tanh, z => 1 - Math.tanh(z) ** 2], relu: [z => Math.max(0, z), z => z > 0 ? 1 : 0],
    gelu: [z => z * Phi(z), z => Phi(z) + z * phi(z)], silu: [z => z * sig(z), z => sig(z) * (1 + z * (1 - sig(z)))] };
  Deck.seg('aSeg', v => {
    const [f, df] = A[v], s = clear(document.getElementById('aSvg')), X = z => 60 + (z + 5) / 10 * 570, Y = y => 125 - y * 45;
    let lo = null; for (let z = -5; z <= 5.001; z += 0.02) { const small = Math.abs(df(z)) < 0.1; if (small && lo === null) lo = z; if ((!small || z > 4.99) && lo !== null) { svg('rect', { x: X(lo), y: 10, width: X(z) - X(lo), height: 220, style: 'fill:var(--d);opacity:.08' }, s); lo = null; } }
    [-2, -1, 0, 1, 2].forEach(t => { svg('line', { x1: 60, x2: 630, y1: Y(t), y2: Y(t), class: 'ln', style: t ? 'opacity:.4' : '' }, s); svg('text', { x: 52, y: Y(t) + 4, 'text-anchor': 'end', class: 'tm', text: t }, s); });
    [-4, -2, 0, 2, 4].forEach(t => svg('text', { x: X(t), y: 245, 'text-anchor': 'middle', class: 'tm', text: t }, s));
    const line = (g, st) => { let p = ''; for (let z = -5; z <= 5.001; z += 0.05) p += `${X(z)},${Y(Math.max(-2.6, Math.min(2.6, g(z))))} `; svg('polyline', { points: p, fill: 'none', style: st }, s); };
    line(f, 'stroke:var(--a);stroke-width:3'); line(df, 'stroke:var(--b);stroke-width:2.5;stroke-dasharray:6 4');
    svg('text', { x: 70, y: 24, class: 't', style: 'fill:var(--a);font-weight:700', text: 'φ(z)' }, s); svg('text', { x: 130, y: 24, class: 't', style: 'fill:var(--b);font-weight:700', text: "φ′(z)" }, s);
    let mx = 0; for (let z = -5; z <= 5; z += 0.01) mx = Math.max(mx, df(z));
    document.getElementById('aOut').innerHTML = `Max slope ≈ <b>${mx.toFixed(2)}</b>. φ′(−3) = ${df(-3).toFixed(3)}, φ′(3) = ${df(3).toFixed(3)}. ${v === 'sigmoid' ? 'Even the best case shrinks gradients 4× per layer.' : v === 'relu' ? 'Exactly 1 for active units, exactly 0 otherwise.' : v === 'tanh' ? 'Slope 1 only near 0; saturates quickly.' : 'Smooth, ≈ 1 for large positive z, small negative dip near −1.'}`;
  });
})();
