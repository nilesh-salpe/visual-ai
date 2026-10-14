(() => {
  const { svg, clear, fmt } = Deck;

  (() => {
    const M = [['policy π (trained)', 'var(--a)', 'The model being optimized. Samples answers, then gets PPO updates. Needs gradients and optimizer state.'], ['reference π_SFT (frozen)', 'var(--faint)', 'A frozen copy of the SFT model. Its log-probs give the KL penalty that keeps the policy close.'], ['reward model (frozen)', 'var(--b)', 'Scores each complete answer with one scalar. InstructGPT used a 6B RM.'], ['value model (trained)', 'var(--c)', 'Predicts expected reward per token to compute advantages. InstructGPT initialized it from the RM. Also needs gradients and optimizer state.']];
    const s = document.getElementById('fSvg');
    M.forEach(([t, c, info], i) => {
      const x = 20 + (i % 2) * 320, y = 20 + Math.floor(i / 2) * 105, g = svg('g', { style: 'cursor:pointer' }, s);
      svg('rect', { x, y, width: 300, height: 85, rx: 12, style: `fill:${c}` }, g);
      svg('text', { x: x + 150, y: y + 50, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:700;font-size:15px', text: t }, g);
      g.addEventListener('click', () => { document.getElementById('fInfo').innerHTML = `<b>${t}</b>: ${info}`; });
    });
  })();
  let sign = 1;
  const clipDraw = () => {
    const e = Deck.val('cE'); Deck.out('cEo', e.toFixed(2));
    const s = clear(document.getElementById('cSvg')), X = r => 60 + r / 2 * 560, Y = v => 122 - v * 48;
    svg('line', { x1: 60, x2: 620, y1: Y(0), y2: Y(0), class: 'ln' }, s); svg('line', { x1: X(1), x2: X(1), y1: 20, y2: 220, class: 'ln' }, s);
    svg('rect', { x: X(1 - e), y: 22, width: X(1 + e) - X(1 - e), height: 200, style: 'fill:var(--a-soft)' }, s);
    let un = '', cl = '';
    for (let r = 0.01; r <= 2; r += 0.01) { un += `${X(r)},${Y(r * sign)} `; cl += `${X(r)},${Y(Math.min(r * sign, Math.min(Math.max(r, 1 - e), 1 + e) * sign))} `; }
    svg('polyline', { points: un, fill: 'none', style: 'stroke:var(--faint);stroke-width:2;stroke-dasharray:5 4' }, s);
    svg('polyline', { points: cl, fill: 'none', style: 'stroke:var(--a);stroke-width:3.5' }, s);
    [0, 0.5, 1, 1.5, 2].forEach(r => svg('text', { x: X(r), y: 236, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: 'ρ=' + r }, s));
    svg('text', { x: 60, y: 14, class: 'tm', style: 'font-size:11px', text: 'dashed: unclipped ρ·Â   ·   solid: L_CLIP   ·   shaded: 1 ± ε' }, s);
  };
  Deck.bind(['cE'], clipDraw); Deck.seg('cA', v => { sign = +v; clipDraw(); });
  (() => {
    const B = [0.1, 0.25, 0.5, 1, 2, 5], R = [1.995, 1.891, 1.016, 0.465, 0.320, 0.248], K = [3.879, 3.398, 0.989, 0.135, 0.023, 0.005];
    const s = document.getElementById('kSvg'), X = i => 70 + i * 106, Y = v => 200 - v / 4 * 170;
    [0, 1, 2, 3, 4].forEach(v => { svg('line', { x1: 60, x2: 610, y1: Y(v), y2: Y(v), class: 'ln' }, s); svg('text', { x: 52, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm', text: v }, s); });
    B.forEach((b, i) => svg('text', { x: X(i), y: 222, 'text-anchor': 'middle', class: 'tm', text: 'β=' + b }, s));
    [[R, 'var(--a)'], [K, 'var(--d)']].forEach(([v, c]) => { svg('polyline', { points: v.map((y, i) => `${X(i)},${Y(y)}`).join(' '), fill: 'none', style: `stroke:${c};stroke-width:3` }, s); v.forEach((y, i) => svg('circle', { cx: X(i), cy: Y(y), r: 5, style: `fill:${c}` }, s)); });
  })();

})();
