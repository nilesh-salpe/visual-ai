(() => {
  const { svg, clear, fmt } = Deck;
  Deck.bind(['pS', 'pP'], () => {
    const s = Deck.val('pS'), p = Deck.val('pP'); Deck.out('pSo', s + ' px'); Deck.out('pPo', p + ' px');
    const n = Math.floor(s / p) ** 2;
    const g = clear(document.getElementById('pSvg')), side = 220, k = Math.floor(s / p), cell = side / k;
    for (let i = 0; i <= k; i++) {
      svg('line', { x1: 190 + i * cell, y1: 20, x2: 190 + i * cell, y2: 20 + side, style: 'stroke:var(--line)' }, g);
      svg('line', { x1: 190, y1: 20 + i * cell, x2: 190 + side, y2: 20 + i * cell, style: 'stroke:var(--line)' }, g);
    }
    svg('rect', { x: 190, y: 20, width: cell, height: cell, style: 'fill:var(--a);opacity:.5' }, g);
    document.getElementById('pOut').innerHTML = `A ${s} × ${s} image with ${p} × ${p} patches → ${k} × ${k} = <b>${n} tokens</b> (ViT adds one class token). Each token holds ${p} × ${p} × 3 = ${p * p * 3} pixel values. Self-attention cost grows with the square of the token count: ${(n * n / 1e6).toFixed(2)} M pairs.`;
  });
})();
