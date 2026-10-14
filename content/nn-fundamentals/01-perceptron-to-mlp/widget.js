(() => {
  const { svg, clear, fmt } = Deck;
  let mode = 'in';
  const PTS = [[0, 0, 0], [0, 1, 1], [1, 0, 1], [1, 1, 0]], H = ([a, b]) => [Math.max(0, a + b), Math.max(0, a + b - 1)];
  const draw = () => {
    const ang = Deck.val('xA') * Math.PI / 180, off = Deck.val('xB'); Deck.out('xAo', Deck.val('xA') + '°'); Deck.out('xBo', off.toFixed(2));
    const s = clear(document.getElementById('xSvg')), lim = mode === 'in' ? [-0.5, 1.5] : [-0.5, 2.5], X = v => 200 + (v - lim[0]) / (lim[1] - lim[0]) * 240 - 120, Y = v => 240 - (v - lim[0]) / (lim[1] - lim[0]) * 220;
    svg('rect', { x: X(lim[0]), y: Y(lim[1]), width: X(lim[1]) - X(lim[0]), height: Y(lim[0]) - Y(lim[1]), style: 'fill:var(--panel-2)' }, s);
    const n = [Math.cos(ang), Math.sin(ang)];
    let correct = 0;
    PTS.forEach(p => { const q = mode === 'in' ? [p[0], p[1]] : H(p), side = n[0] * q[0] + n[1] * q[1] + off > 0 ? 1 : 0; if (side === p[2]) correct++;
      svg('circle', { cx: X(q[0]), cy: Y(q[1]), r: 11, style: `fill:${p[2] ? 'var(--a)' : 'var(--b)'};stroke:${side === p[2] ? 'var(--ink)' : 'var(--d)'};stroke-width:${side === p[2] ? 1.5 : 4}` }, s);
      svg('text', { x: X(q[0]) + 14, y: Y(q[1]) - 10, class: 'tm', style: 'font-size:11px', text: `(${p[0]},${p[1]})` }, s); });
    const t = [-n[1], n[0]], c = [-off * n[0], -off * n[1]], L = 4;
    svg('line', { x1: X(c[0] - L * t[0]), y1: Y(c[1] - L * t[1]), x2: X(c[0] + L * t[0]), y2: Y(c[1] + L * t[1]), style: 'stroke:var(--ink);stroke-width:2.5;stroke-dasharray:6 4' }, s);
    svg('rect', { x: 0, y: 0, width: X(lim[0]), height: 260, style: 'fill:var(--panel)' }, s); svg('rect', { x: X(lim[1]), y: 0, width: 660, height: 260, style: 'fill:var(--panel)' }, s); svg('rect', { x: 0, y: 0, width: X(lim[1]) + 1, height: Y(lim[1]), style: 'fill:var(--panel)' }, s); svg('rect', { x: 0, y: Y(lim[0]), width: X(lim[1]) + 1, height: 40, style: 'fill:var(--panel)' }, s);
    svg('text', { x: 400, y: 60, class: 't', style: 'font-weight:700', text: mode === 'in' ? 'input space' : 'hidden space after ReLU layer' }, s);
    svg('text', { x: 400, y: 95, class: 't', text: `correct: ${correct} / 4` }, s);
    document.getElementById('xOut').innerHTML = mode === 'in' ? (correct === 4 ? 'Impossible: check again!' : `Best possible here is 3 / 4. Red rings mark misclassified points.`) : (correct === 4 ? '<b>All four correct</b>: the hidden layer made XOR linearly separable (for example angle 297°, offset −0.2).' : 'In hidden space a line can get all four right. Try angle 297°, offset −0.2.');
  };
  Deck.bind(['xA', 'xB'], draw); Deck.seg('xSeg', v => { mode = v; draw(); });
})();
