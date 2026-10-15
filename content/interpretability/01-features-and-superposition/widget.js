(() => {
  const { svg, clear, fmt } = Deck;
  Deck.bind(['sN'], () => {
    const n = Deck.val('sN'); Deck.out('sNo', n);
    const s = clear(document.getElementById('sSvg')), cx = 300, cy = 130, R = 100;
    svg('circle', { cx, cy, r: R, fill: 'none', style: 'stroke:var(--line)' }, s);
    for (let i = 0; i < n; i++) {
      const a = 2 * Math.PI * i / n - Math.PI / 2, x = cx + R * Math.cos(a), y = cy + R * Math.sin(a);
      svg('line', { x1: cx, y1: cy, x2: x, y2: y, style: `stroke:var(--${'abcde'[i % 5]});stroke-width:3` }, s);
      svg('text', { x: cx + (R + 14) * Math.cos(a), y: cy + (R + 14) * Math.sin(a) + 4, 'text-anchor': 'middle', class: 'tm', text: 'f' + (i + 1) }, s);
    }
    const inter = n <= 2 ? 0 : Math.abs(Math.cos(2 * Math.PI / n));
    document.getElementById('sOut').innerHTML = n <= 2 ? `${n} feature${n > 1 ? 's' : ''} in 2 dimensions: orthogonal, no interference.` :
      `${n} features in 2 dimensions, evenly spaced: neighbours are ${(360 / n).toFixed(0)}° apart, so each active feature leaks <b>${inter.toFixed(2)}</b> onto its neighbours. Superposition pays off only if features are rarely active together.`;
  });
})();
