(() => {
  const { svg, clear, fmt } = Deck;
  Deck.bind(['aT', 'aP', 'aD'], () => {
    const tp = Deck.val('aT'), pp = Deck.val('aP'), dp = Deck.val('aD'); Deck.out('aTo', tp); Deck.out('aPo', pp); Deck.out('aDo', dp);
    const N = dp * pp * tp, A = dp, coord = dp > 1 ? 1 : 0, total = A + dp + N + coord, s = clear(document.getElementById('aSvg'));
    const row = (y, n, label, col, h = 24) => { const w = Math.min(70, 600 / n - 4); for (let i = 0; i < n; i++) svg('rect', { x: 50 + i * (w + 4), y, width: w, height: h, rx: 5, style: `fill:var(--${col})` }, s); svg('text', { x: 45, y: y + 16, 'text-anchor': 'end', class: 'tm', style: 'font-size:11px', text: label }, s); };
    row(20, A, 'API', 'c'); row(70, dp, 'Engine', 'a'); if (coord) { svg('rect', { x: 560, y: 70, width: 90, height: 24, rx: 5, style: 'fill:var(--e)' }, s); svg('text', { x: 605, y: 86, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11px', text: 'DP coordinator' }, s); }
    row(120, Math.min(N, 64), 'GPU', 'b', 40);
    svg('text', { x: 330, y: 200, 'text-anchor': 'middle', class: 'tm', text: `vllm serve <model> -tp ${tp}${pp > 1 ? ' -pp ' + pp : ''}${dp > 1 ? ' -dp ' + dp : ''}` }, s);
    document.getElementById('aOut').innerHTML = `${A} API server${A > 1 ? 's' : ''} + ${dp} engine core${dp > 1 ? 's' : ''} + ${N} GPU workers${coord ? ' + 1 DP coordinator' : ''} = <b>${total} processes</b> on ${N} GPU${N > 1 ? 's' : ''}.`;
  });
})();
