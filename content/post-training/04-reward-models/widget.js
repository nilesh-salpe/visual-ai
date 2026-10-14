(() => {
  const { svg, clear, fmt } = Deck;

  Deck.bind(['bD'], () => {
    const d = Deck.val('bD'), p = 1 / (1 + Math.exp(-d)); Deck.out('bDo', d.toFixed(1));
    const s = clear(document.getElementById('bSvg')), X = v => 60 + (v + 5) / 10 * 560, Y = v => 190 - v * 170;
    [0, 0.5, 1].forEach(v => { svg('line', { x1: 60, x2: 620, y1: Y(v), y2: Y(v), class: 'ln' }, s); svg('text', { x: 52, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm', text: v }, s); });
    let pts = ''; for (let v = -5; v <= 5.001; v += 0.05) pts += `${X(v)},${Y(1 / (1 + Math.exp(-v)))} `;
    svg('polyline', { points: pts, fill: 'none', style: 'stroke:var(--a);stroke-width:3' }, s);
    svg('circle', { cx: X(d), cy: Y(p), r: 7, style: 'fill:var(--b)' }, s);
    svg('text', { x: 340, y: 214, 'text-anchor': 'middle', class: 'tm', text: 'reward difference r(A) − r(B)' }, s);
    document.getElementById('bOut').innerHTML = `P(A preferred) = σ(${d.toFixed(1)}) = <b>${p.toFixed(2)}</b>. Loss if the labeler chose A: −log ${p.toFixed(2)} = ${(-Math.log(p)).toFixed(2)}; if they chose B: ${(-Math.log(1 - p)).toFixed(2)}.`;
  });
  Deck.bind(['kK'], () => {
    const K = Deck.val('kK'), s = clear(document.getElementById('kSvg')); Deck.out('kKo', K);
    const pos = i => [330 + 150 * Math.cos(-Math.PI / 2 + 2 * Math.PI * i / K), 110 + 90 * Math.sin(-Math.PI / 2 + 2 * Math.PI * i / K)];
    for (let i = 0; i < K; i++) for (let j = i + 1; j < K; j++) { const [x1, y1] = pos(i), [x2, y2] = pos(j); svg('line', { x1, y1, x2, y2, style: 'stroke:var(--a);stroke-width:1.5;opacity:.6' }, s); }
    for (let i = 0; i < K; i++) { const [x, y] = pos(i); svg('circle', { cx: x, cy: y, r: 16, style: `fill:hsl(${140 - 140 * i / Math.max(1, K - 1)},55%,45%)` }, s); svg('text', { x, y: y + 5, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:700', text: '#' + (i + 1) }, s); }
    document.getElementById('kOut').innerHTML = `Ranking of ${K} (#1 best): <b>${K * (K - 1) / 2}</b> comparisons, each line a (better, worse) pair. ${K >= 4 ? 'InstructGPT used K = 4–9, so 6 to 36 pairs per prompt.' : ''}`;
  });
  Deck.hbars(document.getElementById('aBars'), [[25, 0.703], [100, 0.758], [400, 0.796], [2000, 0.812]].map(([n, a]) => ({ label: n.toLocaleString() + ' comparisons', value: a - 0.5, color: 'var(--a)', text: (100 * a).toFixed(1) + '%' })).concat([{ label: 'true reward (ceiling)', value: 0.311, color: 'var(--faint)', text: '81.1%' }]), { max: 0.35 });

})();
