(() => {
  const { svg, clear, fmt } = Deck;
  Deck.bind(['pS', 'pL'], () => {
    let sh = Deck.val('pS'); const L = Deck.val('pL'); if (sh > L) sh = L; Deck.out('pSo', sh); Deck.out('pLo', L);
    const s = clear(document.getElementById('pSvg')), nb = Math.ceil(L / 16), w = Math.min(60, 640 / nb - 4), full = Math.floor(L / 16);
    let hits = 0;
    for (let b = 0; b < nb; b++) { const end = Math.min((b + 1) * 16, L), isFull = (b + 1) * 16 <= L, hit = isFull && end <= sh && b === hits; if (hit) hits++;
      svg('rect', { x: 10 + b * (w + 4), y: 20, width: w * (end - b * 16) / 16, height: 50, rx: 5, style: `fill:${hit ? 'var(--e)' : 'var(--b)'};opacity:${isFull ? 1 : .55}` }, s);
      svg('text', { x: 10 + b * (w + 4) + w / 2, y: 50, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11px', text: hit ? 'hit' : isFull ? 'miss' : 'partial' }, s); }
    svg('line', { x1: 10 + sh / 16 * (w + 4), x2: 10 + sh / 16 * (w + 4), y1: 10, y2: 80, style: 'stroke:var(--d);stroke-width:2;stroke-dasharray:4 3' }, s);
    svg('text', { x: 10 + sh / 16 * (w + 4) + 4, y: 100, class: 'tm', style: 'fill:var(--d)', text: 'prompts differ from here' }, s);
    const reused = Math.min(hits * 16, L - 1);
    document.getElementById('pOut').innerHTML = `<b>${reused}</b> of ${L} prompt tokens reused (${hits} full block${hits === 1 ? '' : 's'}); ${L - reused} to prefill. ${sh % 16 && sh < L ? `The ${sh % 16} shared tokens in the partial block after them are recomputed.` : ''}`;
  });
})();
