(() => {
  const { svg, clear, fmt } = Deck;
  let shape = 'cos';
  const draw = () => {
    const W = Deck.val('sW'), fr = Deck.val('sF'), T = 100000; Deck.out('sWo', W.toLocaleString()); Deck.out('sFo', fr.toFixed(2));
    const lr = t => { if (t < W) return (t + 1) / W; const p = Math.min(1, (t - W) / Math.max(1, T - W)); return shape === 'const' ? 1 : shape === 'lin' ? fr + (1 - fr) * (1 - p) : fr + (1 - fr) * 0.5 * (1 + Math.cos(Math.PI * p)); };
    const s = clear(document.getElementById('sSvg')), X = t => 60 + t / T * 570, Y = v => 200 - v * 175;
    [0, 0.5, 1].forEach(v => { svg('line', { x1: 60, x2: 630, y1: Y(v), y2: Y(v), class: 'ln' }, s); svg('text', { x: 52, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm', text: v === 1 ? 'peak' : v }, s); });
    let pts = ''; for (let t = 0; t <= T; t += 250) pts += `${X(t)},${Y(lr(t))} `;
    svg('polyline', { points: pts, fill: 'none', style: 'stroke:var(--a);stroke-width:3' }, s);
    if (W) svg('rect', { x: 60, y: 20, width: X(W) - 60, height: 180, style: 'fill:var(--b);opacity:.1' }, s);
    [0, 25000, 50000, 75000, 100000].forEach(t => svg('text', { x: X(t), y: 218, 'text-anchor': 'middle', class: 'tm', text: (t / 1000) + 'k' }, s));
    let area = 0; for (let t = 0; t < T; t += 100) area += lr(t) * 100;
    document.getElementById('sOut').innerHTML = `Mid-run (50k) η = <b>${lr(50000).toFixed(3)}</b> × peak; final η = ${lr(T - 1).toFixed(3)} × peak. Average η over the run: ${(area / T).toFixed(2)} × peak.`;
  };
  Deck.bind(['sW', 'sF'], draw); Deck.seg('sSeg', v => { shape = v; draw(); });
})();
