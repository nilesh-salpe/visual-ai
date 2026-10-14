(() => {
  const { svg, clear, fmt } = Deck;
  Deck.bind(['lP'], () => {
    const p = Deck.val('lP'); Deck.out('lPo', p.toFixed(3));
    const s = clear(document.getElementById('lSvg')), X = v => 60 + v * 570, Y = l => 200 - Math.min(l, 7) / 7 * 180;
    [0, 2, 4, 6].forEach(l => { svg('line', { x1: 60, x2: 630, y1: Y(l), y2: Y(l), class: 'ln' }, s); svg('text', { x: 52, y: Y(l) + 4, 'text-anchor': 'end', class: 'tm', text: l }, s); });
    let pts = ''; for (let v = 0.001; v <= 1.0001; v += 0.004) pts += `${X(v)},${Y(-Math.log(v))} `;
    svg('polyline', { points: pts, fill: 'none', style: 'stroke:var(--a);stroke-width:3' }, s);
    svg('circle', { cx: X(p), cy: Y(-Math.log(p)), r: 7, style: 'fill:var(--b)' }, s);
    [0, 0.25, 0.5, 0.75, 1].forEach(v => svg('text', { x: X(v), y: 218, 'text-anchor': 'middle', class: 'tm', text: v }, s));
    document.getElementById('lOut').innerHTML = `Loss −ln p = <b>${(-Math.log(p)).toFixed(3)} nats</b> (${(-Math.log2(p)).toFixed(2)} bits). If every token looked like this, perplexity would be <b>${(1 / p).toFixed(1)}</b>.`;
  });
  const W = ['The', 'capital', 'of', 'France', 'is', 'Paris', '.'], P = [0.02, 0.05, 0.6, 0.15, 0.7, 0.85, 0.5];
  Deck.hbars(document.getElementById('tBars'), W.map((w, i) => ({ label: `"${w}" (p = ${P[i]})`, value: -Math.log(P[i]), color: -Math.log(P[i]) > 2 ? 'var(--d)' : 'var(--a)', text: (-Math.log(P[i])).toFixed(2) + ' nats' })), { max: 4.5 });
  const avg = -P.reduce((a, v) => a + Math.log(v), 0) / P.length;
  document.getElementById('tOut').innerHTML = `Mean loss <b>${avg.toFixed(2)} nats</b> → perplexity <b>${Math.exp(avg).toFixed(1)}</b>. The first two tokens contribute most: openings are genuinely uncertain.`;
})();
