(() => {
  const { svg, clear, fmt } = Deck;
  Deck.bind(['gA'], () => {
    const a = Deck.val('gA'); Deck.out('gAo', a.toFixed(1));
    const s = clear(document.getElementById('gSvg')), X = v => 300 + v * 55, Y = v => 130 - v * 55;
    svg('line', { x1: 170, y1: 130, x2: 430, y2: 130, style: 'stroke:var(--line)' }, s); svg('line', { x1: 300, y1: 10, x2: 300, y2: 250, style: 'stroke:var(--line)' }, s);
    const pos = [[1.2, 0.9], [1.5, 0.4], [0.9, 1.3]], neg = [[-1.1, -0.8], [-1.4, -0.3], [-0.8, -1.2]];
    pos.forEach(p => svg('circle', { cx: X(p[0]), cy: Y(p[1]), r: 5, style: 'fill:var(--e)' }, s));
    neg.forEach(p => svg('circle', { cx: X(p[0]), cy: Y(p[1]), r: 5, style: 'fill:var(--d)' }, s));
    const mp = [1.2, 0.867], mn = [-1.1, -0.767], v = [mp[0] - mn[0], mp[1] - mn[1]], n = Math.hypot(v[0], v[1]), u = [v[0] / n, v[1] / n];
    const x0 = [-0.6, 0.2], x = [x0[0] + a * u[0], x0[1] + a * u[1]];
    svg('line', { x1: X(mn[0]), y1: Y(mn[1]), x2: X(mp[0]), y2: Y(mp[1]), style: 'stroke:var(--a);stroke-width:2;stroke-dasharray:5 4' }, s);
    svg('line', { x1: X(x0[0]), y1: Y(x0[1]), x2: X(x[0]), y2: Y(x[1]), style: 'stroke:var(--ink);stroke-width:2' }, s);
    svg('circle', { cx: X(x[0]), cy: Y(x[1]), r: 7, style: 'fill:var(--a)' }, s);
    const score = 1 / (1 + Math.exp(-3 * (x[0] * u[0] + x[1] * u[1])));
    document.getElementById('gOut').innerHTML = `Green and red: activations on positive and negative prompts. Dashed: the steering direction (mean positive − mean negative). Adding ${a.toFixed(1)} × the unit direction moves the new prompt\'s activation; a linear probe along the same direction now reads <b>${(100 * score).toFixed(0)}% positive</b>.`;
  });
})();
