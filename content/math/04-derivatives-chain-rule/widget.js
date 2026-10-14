(() => {
  const { svg, clear, fmt } = Deck;
  Deck.bind(['gW', 'gB'], () => {
    const w = Deck.val('gW'), b = Deck.val('gB'), x = 2, y = 3; Deck.out('gWo', w.toFixed(1)); Deck.out('gBo', b.toFixed(1));
    const m = w * x, z = m + b, e = z - y, L = e * e, dL = 1, de = 2 * e, dz = de, dm = dz, dw = dm * x, db = dz;
    const s = clear(document.getElementById('gSvg'));
    const N = [['w', 40, 50, w], ['x', 40, 150, x], ['×', 180, 100, m], ['b', 250, 200, b], ['+', 320, 130, z], ['− y', 450, 130, e], ['²', 580, 130, L]];
    const E = [[0, 2], [1, 2], [2, 4], [3, 4], [4, 5], [5, 6]];
    E.forEach(([i, j]) => svg('line', { x1: N[i][1], y1: N[i][2], x2: N[j][1], y2: N[j][2], class: 'ln', style: 'stroke-width:2' }, s));
    const G = { 0: dw, 2: dm, 3: db, 4: dz, 5: de, 6: dL };
    N.forEach(([n, cx, cy, v], i) => { svg('circle', { cx, cy, r: 26, style: `fill:${i < 2 || i === 3 ? 'var(--panel-2)' : 'var(--a-soft)'};stroke:var(--a);stroke-width:2` }, s);
      svg('text', { x: cx, y: cy + 5, 'text-anchor': 'middle', class: 't', style: 'font-weight:700', text: n }, s);
      svg('text', { x: cx, y: cy - 32, 'text-anchor': 'middle', class: 'tm', text: v.toFixed(2) }, s);
      if (i in G) svg('text', { x: cx, y: cy + 46, 'text-anchor': 'middle', class: 't', style: 'fill:var(--b);font-weight:700', text: (i === 6 ? 'dL/dL = ' : '∂L = ') + G[i].toFixed(2) }, s); });
    document.getElementById('gOut').innerHTML = `L = <b>${L.toFixed(2)}</b>. ∂L/∂w = 2(wx + b − y)·x = <b>${dw.toFixed(2)}</b>, ∂L/∂b = <b>${db.toFixed(2)}</b>. ${Math.abs(e) < 0.05 ? 'At the minimum: both gradients are zero.' : 'Gradient descent moves w ' + (dw < 0 ? 'up' : 'down') + ' by η × ' + Math.abs(dw).toFixed(2) + ' (against the gradient).'}`;
  });
})();
