(() => {
  const { svg, clear, fmt } = Deck;
  const W = { king: [0.75, 0.8], queen: [0.85, 0.35], man: [0.25, 0.75], woman: [0.35, 0.3], prince: [0.62, 0.9], princess: [0.72, 0.45], cat: [-0.7, -0.4], kitten: [-0.62, -0.62], dog: [-0.45, -0.35], puppy: [-0.38, -0.58], paris: [-0.4, 0.92], london: [-0.1, 0.8] };
  let pick = [];
  const draw = () => {
    const s = clear(document.getElementById('eSvg')), X = x => 330 + x * 280, Y = y => 140 - y * 120;
    svg('line', { x1: 30, x2: 630, y1: Y(0), y2: Y(0), class: 'ln', style: 'opacity:.4' }, s); svg('line', { x1: X(0), x2: X(0), y1: 10, y2: 265, class: 'ln', style: 'opacity:.4' }, s);
    const t = [W.king[0] - W.man[0] + W.woman[0], W.king[1] - W.man[1] + W.woman[1]];
    svg('line', { x1: X(W.king[0]), y1: Y(W.king[1]), x2: X(t[0]), y2: Y(t[1]), style: 'stroke:var(--e);stroke-width:2.5;stroke-dasharray:5 4' }, s);
    svg('circle', { cx: X(t[0]), cy: Y(t[1]), r: 9, style: 'fill:none;stroke:var(--e);stroke-width:2.5' }, s);
    svg('text', { x: X(t[0]) - 4, y: Y(t[1]) + 30, 'text-anchor': 'end', class: 'tm', style: 'fill:var(--e)', text: 'king − man + woman' }, s);
    Object.entries(W).forEach(([w, [x, y]]) => {
      const on = pick.includes(w), c = svg('circle', { cx: X(x), cy: Y(y), r: 8, style: `fill:${on ? 'var(--b)' : 'var(--a)'};cursor:pointer` }, s);
      const tx = svg('text', { x: X(x) + 11, y: Y(y) + 4, class: 't', style: 'cursor:pointer;font-weight:600', text: w }, s);
      [c, tx].forEach(el => el.addEventListener('click', () => { pick = pick.length >= 2 ? [w] : pick.concat(w); draw(); }));
    });
    if (pick.length === 2) { const [a, b] = pick.map(k => W[k]), cos = (a[0] * b[0] + a[1] * b[1]) / Math.hypot(...a) / Math.hypot(...b);
      svg('line', { x1: X(a[0]), y1: Y(a[1]), x2: X(b[0]), y2: Y(b[1]), style: 'stroke:var(--b);stroke-width:2' }, s);
      document.getElementById('eOut').innerHTML = `cos(${pick[0]}, ${pick[1]}) = <b>${cos.toFixed(3)}</b>. ${cos > 0.9 ? 'Very similar contexts.' : cos > 0.5 ? 'Related.' : cos > 0 ? 'Weakly related.' : 'Different regions of the space.'}`; }
    else document.getElementById('eOut').innerHTML = pick.length ? `Picked "${pick[0]}". Click a second word.` : 'Click a word, then another. The dashed line from king lands next to queen.';
  };
  draw();
})();
