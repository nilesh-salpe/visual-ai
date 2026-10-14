(() => {
  const { svg, clear, fmt } = Deck;
  Deck.bind(['m11', 'm12', 'm21', 'm22'], () => {
    const a = Deck.val('m11'), b = Deck.val('m12'), c = Deck.val('m21'), d = Deck.val('m22');
    ['m11', 'm12', 'm21', 'm22'].forEach(k => Deck.out(k + 'o', Deck.val(k).toFixed(1)));
    const s = clear(document.getElementById('mSvg')), cx = 330, cy = 150, U = 45, P = (x, y) => [cx + U * (a * x + b * y), cy - U * (c * x + d * y)], Q = (x, y) => [cx + U * x, cy - U * y];
    for (let i = -6; i <= 6; i++) { svg('line', { x1: Q(i, -3)[0], y1: Q(i, -3)[1], x2: Q(i, 3)[0], y2: Q(i, 3)[1], class: 'ln', style: 'opacity:.4' }, s); svg('line', { x1: Q(-7, i)[0], y1: Q(-7, i)[1], x2: Q(7, i)[0], y2: Q(7, i)[1], class: 'ln', style: 'opacity:.4' }, s); }
    svg('polygon', { points: [Q(0, 0), Q(1, 0), Q(1, 1), Q(0, 1)].map(p => p.join(',')).join(' '), style: 'fill:var(--faint);opacity:.25' }, s);
    svg('polygon', { points: [P(0, 0), P(1, 0), P(1, 1), P(0, 1)].map(p => p.join(',')).join(' '), style: 'fill:var(--a);opacity:.35;stroke:var(--a);stroke-width:2' }, s);
    [[P(1, 0), 'var(--b)', 'W·e₁ = (a, c)'], [P(0, 1), 'var(--c)', 'W·e₂ = (b, d)']].forEach(([p, col, t]) => { svg('line', { x1: cx, y1: cy, x2: p[0], y2: p[1], style: `stroke:${col};stroke-width:3.5` }, s); svg('text', { x: p[0] + 6, y: p[1] - 6, class: 't', style: `fill:${col};font-weight:700`, text: t }, s); });
    const det = a * d - b * c;
    document.getElementById('mOut').innerHTML = `Determinant ad − bc = <b>${det.toFixed(2)}</b>: area ×${Math.abs(det).toFixed(2)}${Math.abs(det) < 0.05 ? ' — the square collapses onto a line: the matrix loses a dimension (rank 1)' : det < 0 ? ' and the orientation flips' : ''}.`;
  });
})();
