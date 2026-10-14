(() => {
  const { svg, clear, fmt } = Deck;
  Deck.bind(['cP'], () => {
    const p = Deck.val('cP'); Deck.out('cPo', p.toFixed(3));
    const s = clear(document.getElementById('cSvg')), X = v => 60 + v * 570, Y = g => 200 - g * 180;
    [0, 0.5, 1].forEach(v => { svg('line', { x1: 60, x2: 630, y1: Y(v), y2: Y(v), class: 'ln' }, s); svg('text', { x: 52, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm', text: v }, s); });
    const line = (g, st) => { let pt = ''; for (let v = 0.005; v <= 0.996; v += 0.005) pt += `${X(v)},${Y(g(v))} `; svg('polyline', { points: pt, fill: 'none', style: st }, s); };
    line(v => 1 - v, 'stroke:var(--a);stroke-width:3'); line(v => 2 * (1 - v) * v * (1 - v) * 3.3, 'stroke:var(--b);stroke-width:3');
    svg('text', { x: 75, y: 30, class: 't', style: 'fill:var(--a);font-weight:700', text: '|∂L/∂z| cross-entropy = 1 − p' }, s);
    svg('text', { x: 360, y: 30, class: 't', style: 'fill:var(--b);font-weight:700', text: '|∂L/∂z| MSE × 3.3 (to be visible)' }, s);
    svg('line', { x1: X(p), x2: X(p), y1: 20, y2: 200, style: 'stroke:var(--d);stroke-dasharray:4 3' }, s);
    [0, 0.25, 0.5, 0.75, 1].forEach(v => svg('text', { x: X(v), y: 218, 'text-anchor': 'middle', class: 'tm', text: v }, s));
    const ce = 1 - p, mse = 2 * (1 - p) * p * (1 - p);
    document.getElementById('cOut').innerHTML = `Cross-entropy: loss ${(-Math.log(p)).toFixed(2)}, |gradient| <b>${ce.toFixed(3)}</b>. MSE: loss ${((1 - p) ** 2).toFixed(3)}, |gradient| <b>${mse.toFixed(4)}</b> (${(ce / mse).toFixed(0)}× smaller).`;
  });
})();
