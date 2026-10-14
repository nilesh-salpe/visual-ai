(() => {
  const { svg, clear, fmt } = Deck;

  const TRUE = [1.2, 0.8, 0.5, 0.0, -0.3, -1.0], M = 6, SC = 400 / Math.log(10), sig = z => 1 / (1 + Math.exp(-z));
  let seed = 42; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const VOTES = []; for (let t = 0; t < 3000; t++) { const i = Math.floor(rnd() * M), j = (i + 1 + Math.floor(rnd() * (M - 1))) % M; VOTES.push(rnd() < sig(TRUE[i] - TRUE[j]) ? [i, j] : [j, i]); }
  const bt = (() => { const xi = new Array(M).fill(0); for (let s = 0; s < 1500; s++) { const g = new Array(M).fill(0); VOTES.forEach(([w, l]) => { const d = 1 - sig(xi[w] - xi[l]); g[w] += d; g[l] -= d; }); for (let m = 0; m < M; m++) xi[m] += 2 * g[m] / VOTES.length; } const mu = xi.reduce((a, b) => a + b) / M; return xi.map(x => (x - mu) * SC + 1000); })();
  const tmu = TRUE.reduce((a, b) => a + b) / M, truth = TRUE.map(x => (x - tmu) * SC + 1000);
  let order = VOTES.map((_, i) => i);
  const draw = () => {
    const K = Deck.val('aK'); Deck.out('aKo', K);
    const R = new Array(M).fill(1000); order.forEach(ix => { const [w, l] = VOTES[ix]; const e = 1 / (1 + Math.pow(10, (R[l] - R[w]) / 400)); R[w] += K * (1 - e); R[l] -= K * (1 - e); });
    const s = clear(document.getElementById('aSvg')), Y = v => 225 - (v - 700) / 650 * 210;
    [800, 1000, 1200].forEach(v => { svg('line', { x1: 50, x2: 640, y1: Y(v), y2: Y(v), class: 'ln' }, s); svg('text', { x: 44, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm', text: v }, s); });
    for (let m = 0; m < M; m++) {
      const x = 90 + m * 95;
      svg('text', { x, y: 246, 'text-anchor': 'middle', class: 'tm', text: 'model ' + m }, s);
      [[truth[m], 'var(--faint)', -18], [bt[m], 'var(--a)', 0], [R[m], 'var(--d)', 18]].forEach(([v, c, dx]) => svg('rect', { x: x + dx - 7, y: Y(v), width: 14, height: Y(700) - Y(v), rx: 3, style: `fill:${c}` }, s));
    }
  };
  Deck.bind(['aK'], draw);
  document.getElementById('aShuf').addEventListener('click', () => { for (let i = order.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [order[i], order[j]] = [order[j], order[i]]; } draw(); });

})();
