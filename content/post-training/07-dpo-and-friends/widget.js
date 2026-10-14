(() => {
  const { svg, clear, fmt } = Deck;

  Deck.seg('pSeg', v => {
    const s = clear(document.getElementById('pSvg')), dpo = v === 'dpo';
    const box = (x, y, w, t, c) => { svg('rect', { x, y, width: w, height: 40, rx: 8, style: `fill:${c}` }, s); svg('text', { x: x + w / 2, y: y + 25, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:600;font-size:12px', text: t }, s); };
    const arrow = (x1, x2, y) => { svg('line', { x1, x2: x2 - 6, y1: y, y2: y, style: 'stroke:var(--muted);stroke-width:2' }, s); svg('path', { d: `M${x2 - 10} ${y - 5} L${x2} ${y} L${x2 - 10} ${y + 5}`, fill: 'none', style: 'stroke:var(--muted);stroke-width:2' }, s); };
    if (!dpo) {
      box(10, 20, 130, 'preference pairs', 'var(--faint)'); arrow(140, 175, 40); box(175, 20, 130, 'train reward model', 'var(--b)'); arrow(305, 340, 40);
      box(340, 20, 140, 'sample from policy', 'var(--c)'); arrow(480, 515, 40); box(515, 20, 130, 'score + PPO step', 'var(--a)');
      svg('path', { d: 'M580 62 V100 H410 V64', fill: 'none', style: 'stroke:var(--muted);stroke-width:2;stroke-dasharray:4 3' }, s);
      svg('text', { x: 495, y: 118, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: 'repeat for thousands of steps' }, s);
      [['policy', 'var(--a)'], ['reference', 'var(--faint)'], ['reward model', 'var(--b)'], ['value model', 'var(--c)']].forEach(([t, c], i) => box(40 + i * 150, 145, 130, t, c));
      document.getElementById('pOut').innerHTML = 'Two training stages, generation inside the loop, and <b>four</b> models in memory.';
    } else {
      box(60, 20, 170, 'preference pairs', 'var(--faint)'); arrow(230, 290, 40); box(290, 20, 300, 'DPO loss on log-ratios (one stage)', 'var(--a)');
      [['policy', 'var(--a)'], ['reference (frozen)', 'var(--faint)']].forEach(([t, c], i) => box(140 + i * 200, 145, 170, t, c));
      document.getElementById('pOut').innerHTML = 'One supervised stage on fixed pairs, no sampling, <b>two</b> models (and the reference only needs log-probs, which can be precomputed).';
    }
  });
  Deck.bind(['gZ'], () => {
    const z = Deck.val('gZ'), w = 1 - 1 / (1 + Math.exp(-z)); Deck.out('gZo', z.toFixed(1));
    const s = clear(document.getElementById('gSvg')), X = v => 60 + (v + 6) / 12 * 560, Y = v => 190 - v * 165;
    [0, 0.5, 1].forEach(v => { svg('line', { x1: 60, x2: 620, y1: Y(v), y2: Y(v), class: 'ln' }, s); svg('text', { x: 52, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm', text: v }, s); });
    let p = ''; for (let v = -6; v <= 6.001; v += 0.05) p += `${X(v)},${Y(1 - 1 / (1 + Math.exp(-v)))} `;
    svg('polyline', { points: p, fill: 'none', style: 'stroke:var(--a);stroke-width:3' }, s);
    svg('circle', { cx: X(z), cy: Y(w), r: 7, style: 'fill:var(--b)' }, s);
    svg('text', { x: 340, y: 214, 'text-anchor': 'middle', class: 'tm', text: 'z = β·[log-ratio(y_w) − log-ratio(y_l)]' }, s);
    document.getElementById('gOut').innerHTML = `Gradient weight 1 − σ(z) = <b>${w.toFixed(2)}</b>. ${z < 0 ? 'The model currently prefers the loser, so this pair gets a strong push.' : z > 3 ? 'Already ranked correctly by a wide margin: almost no update.' : 'Ranked correctly, but with a small margin: a moderate push.'}`;
  });

})();
