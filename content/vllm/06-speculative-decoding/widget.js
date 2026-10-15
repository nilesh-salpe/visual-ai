(() => {
  const { svg, clear, fmt } = Deck;
  Deck.bind(['eA', 'eK'], () => {
    const a = Deck.val('eA'), k = Deck.val('eK'); Deck.out('eAo', a.toFixed(2)); Deck.out('eKo', k);
    const E = (al, kk) => al >= 1 ? kk + 1 : (1 - Math.pow(al, kk + 1)) / (1 - al);
    const s = clear(document.getElementById('eSvg')), X = v => 60 + v * 570, Y = v => 200 - v / 11 * 180;
    [1, 3, 5, 7, 9, 11].forEach(v => { svg('line', { x1: 60, x2: 630, y1: Y(v), y2: Y(v), class: 'ln', style: 'opacity:.5' }, s); svg('text', { x: 52, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm', text: v }, s); });
    [0, 0.25, 0.5, 0.75, 1].forEach(v => svg('text', { x: X(v), y: 216, 'text-anchor': 'middle', class: 'tm', text: 'α=' + v }, s));
    [1, 2, 4, 8].forEach((kk, i) => { let p = ''; for (let v = 0; v <= 0.981; v += 0.01) p += `${X(v)},${Y(E(v, kk))} `; svg('polyline', { points: p, fill: 'none', style: `stroke:${['var(--faint)', 'var(--c)', 'var(--a)', 'var(--b)'][i]};stroke-width:${kk === k ? 4 : 2}` }, s);
      svg('text', { x: X(0.98) + 4, y: Y(E(0.98, kk)), class: 'tm', style: 'font-size:11px', text: 'k=' + kk }, s); });
    svg('circle', { cx: X(a), cy: Y(E(a, k)), r: 7, style: 'fill:var(--d)' }, s);
    document.getElementById('eOut').innerHTML = `Expected <b>${E(a, k).toFixed(2)}</b> tokens per target pass (upper limit as k → ∞: ${a < 1 ? (1 / (1 - a)).toFixed(2) : '∞'}). Real speed-up is lower: proposer and verification cost extra.`;
  });
})();
