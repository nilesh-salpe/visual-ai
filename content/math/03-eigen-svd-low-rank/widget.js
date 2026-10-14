(() => {
  const { svg, clear, fmt } = Deck;
  Deck.bind(['sK', 'sR'], () => {
    const k = Deck.val('sK'), r = Deck.val('sR'); Deck.out('sKo', k); Deck.out('sRo', r);
    const sig = [...Array(64)].map((_, i) => (i < k ? 10 * Math.pow(0.85, i) : 0) + 0.35);
    const tot = sig.reduce((a, v) => a + v * v, 0), kept = sig.slice(0, r).reduce((a, v) => a + v * v, 0);
    const s = clear(document.getElementById('sSvg')), W = 570 / 64, Y = v => 200 - v / 10.4 * 180;
    sig.forEach((v, i) => svg('rect', { x: 60 + i * W, y: Y(v), width: W - 1.5, height: 200 - Y(v), style: `fill:${i < r ? 'var(--a)' : 'var(--faint)'};opacity:${i < r ? 1 : .5}` }, s));
    svg('line', { x1: 60, x2: 630, y1: 200, y2: 200, class: 'ln' }, s);
    svg('text', { x: 345, y: 220, 'text-anchor': 'middle', class: 'tm', text: 'singular values σ₁ ≥ σ₂ ≥ … (index 1 to 64)' }, s);
    document.getElementById('sOut').innerHTML = `Keeping r = ${r}: <b>${(100 * kept / tot).toFixed(1)}%</b> of the energy, relative error ${(100 * Math.sqrt(1 - kept / tot)).toFixed(1)}%, storage ${r} × (64 + 64) = ${r * 128} numbers vs 4,096 (${(100 * r * 128 / 4096).toFixed(0)}%).`;
  });
})();
