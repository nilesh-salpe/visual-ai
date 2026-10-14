(() => {
  const { svg, clear, fmt } = Deck;
  const draw = () => {
    const r = Deck.val('lR'), b = Deck.val('lB'); Deck.out('lRo', r); Deck.out('lBo', b);
    const P = s => 1 - Math.pow(1 - Math.pow(s, r), b), s = clear(document.getElementById('lSvg')), X = v => 60 + v * 570, Y = v => 200 - v * 180;
    [0, 0.5, 1].forEach(v => { svg('line', { x1: 60, x2: 630, y1: Y(v), y2: Y(v), class: 'ln' }, s); svg('text', { x: 52, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm', text: (100 * v) + '%' }, s); });
    [0, 0.25, 0.5, 0.75, 1].forEach(v => svg('text', { x: X(v), y: 220, 'text-anchor': 'middle', class: 'tm', text: 's = ' + v }, s));
    let pts = ''; for (let v = 0; v <= 1.0001; v += 0.005) pts += `${X(v)},${Y(P(v))} `;
    svg('polyline', { points: pts, fill: 'none', style: 'stroke:var(--a);stroke-width:3' }, s);
    const t = Math.pow(1 / b, 1 / r); svg('line', { x1: X(t), x2: X(t), y1: 20, y2: 200, style: 'stroke:var(--b);stroke-dasharray:5 4' }, s);
    svg('text', { x: X(t) + 6, y: 32, class: 'tm', style: 'fill:var(--b)', text: `threshold ≈ ${t.toFixed(2)}` }, s);
    document.getElementById('lOut').innerHTML = `${b * r} hashes per document. P(candidate) at s = 0.5: <b>${(100 * P(0.5)).toFixed(1)}%</b>, s = 0.75: <b>${(100 * P(0.75)).toFixed(1)}%</b>, s = 0.8: <b>${(100 * P(0.8)).toFixed(1)}%</b>.`;
  };
  Deck.bind(['lR', 'lB'], draw);
  Deck.seg('lSeg', v => { const [r, b] = v.split(',').map(Number); document.getElementById('lR').value = r; document.getElementById('lB').value = b; draw(); });
})();
