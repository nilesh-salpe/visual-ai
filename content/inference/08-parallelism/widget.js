(() => {
  const { svg, clear, fmt } = Deck;

  (() => {
    const s = document.getElementById('tpSvg');
    const box = (x, y, w, h, c, t) => { svg('rect', { x, y, width: w, height: h, rx: 6, style: `fill:${c}` }, s); svg('text', { x: x + w / 2, y: y + h / 2 + 4, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11px;font-weight:600', text: t }, s); };
    box(10, 80, 60, 40, 'var(--faint)', 'X');
    for (let g = 0; g < 4; g++) { const y = 10 + g * 46; box(110, y, 110, 36, 'var(--a)', `GPU${g}: X·W₁[:, ${g}]`); box(240, y, 70, 36, 'var(--a)', 'GELU'); box(330, y, 130, 36, 'var(--b)', `·W₂[${g}, :] → partial`); svg('line', { x1: 70, y1: 100, x2: 110, y2: y + 18, class: 's-line', 'stroke-width': 1.5 }, s); svg('line', { x1: 460, y1: y + 18, x2: 500, y2: 100, class: 's-line', 'stroke-width': 1.5 }, s); }
    box(500, 75, 80, 50, 'var(--e)', 'all-reduce Σ'); box(600, 80, 50, 40, 'var(--faint)', 'Y');
    svg('text', { x: 285, y: 196, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: 'no communication until the single all-reduce' }, s);
  })();
  let n = 8, bw = 450;
  const tp = () => {
    const [w, d, L] = Deck.val('tM').split(',').map(Number);
    const read = w / n / 3350 * 1000, comm = n > 1 ? 2 * L * d * 2 * (2 * (n - 1) / n) / (bw * 1e9) * 1000 : 0;
    Deck.out('tW', (w / n).toFixed(1) + ' GB'); Deck.out('tR', read.toFixed(1) + ' ms'); Deck.out('tC', comm.toFixed(2) + ' ms'); Deck.out('tT', (read + comm).toFixed(1) + ' ms');
    document.getElementById('tW').style.color = w / n > 80 ? 'var(--d)' : 'var(--ink)';
  };
  Deck.seg('tN', v => { n = +v; tp(); }); Deck.seg('tL', v => { bw = +v; tp(); }); Deck.bind(['tM'], tp);

})();
