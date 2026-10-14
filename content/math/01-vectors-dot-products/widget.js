(() => {
  const { svg, clear, fmt } = Deck;
  Deck.bind(['vA', 'vB', 'vL'], () => {
    const A = Deck.val('vA') * Math.PI / 180, B = Deck.val('vB') * Math.PI / 180, lb = Deck.val('vL');
    Deck.out('vAo', Deck.val('vA') + '°'); Deck.out('vBo', Deck.val('vB') + '°'); Deck.out('vLo', lb.toFixed(1));
    const a = [Math.cos(A), Math.sin(A)], b = [lb * Math.cos(B), lb * Math.sin(B)], dot = a[0] * b[0] + a[1] * b[1], cos = dot / lb;
    const s = clear(document.getElementById('vSvg')), cx = 200, cy = 130, R = 90, P = v => [cx + v[0] * R, cy - v[1] * R];
    svg('circle', { cx, cy, r: R, style: 'fill:none;stroke:var(--line);stroke-dasharray:3 4' }, s);
    svg('line', { x1: cx - 120, x2: cx + 120, y1: cy, y2: cy, class: 'ln' }, s); svg('line', { x1: cx, x2: cx, y1: cy - 120, y2: cy + 120, class: 'ln' }, s);
    const pr = [dot * a[0], dot * a[1]];
    svg('line', { x1: P(b)[0], y1: P(b)[1], x2: P(pr)[0], y2: P(pr)[1], style: 'stroke:var(--faint);stroke-dasharray:4 3' }, s);
    svg('line', { x1: cx, y1: cy, x2: P(pr)[0], y2: P(pr)[1], style: 'stroke:var(--e);stroke-width:7;opacity:.5' }, s);
    [[a, 'var(--a)', 'a'], [b, 'var(--b)', 'b']].forEach(([v, c, n]) => { const [x, y] = P(v); svg('line', { x1: cx, y1: cy, x2: x, y2: y, style: `stroke:${c};stroke-width:3.5` }, s); svg('circle', { cx: x, cy: y, r: 5, style: `fill:${c}` }, s); svg('text', { x: x + 8, y: y - 6, class: 't', style: `fill:${c};font-weight:700`, text: n }, s); });
    const bx = 420; [['a · b', dot.toFixed(3)], ['|a| · |b|', lb.toFixed(2)], ['cos θ', cos.toFixed(3)], ['angle θ', (Math.acos(Math.max(-1, Math.min(1, cos))) * 180 / Math.PI).toFixed(0) + '°']].forEach(([k, v], i) => {
      svg('text', { x: bx, y: 70 + i * 40, class: 'tm', text: k }, s); svg('text', { x: bx + 150, y: 70 + i * 40, class: 't', style: 'font-weight:700', text: v }, s); });
    document.getElementById('vOut').innerHTML = cos > 0.7 ? 'Strongly aligned: positive dot product, small angle.' : cos > 0.05 ? 'Partly aligned.' : cos > -0.05 ? '<b>Orthogonal</b>: dot product ≈ 0, unrelated directions.' : 'Pointing apart: negative dot product.';
  });
})();
