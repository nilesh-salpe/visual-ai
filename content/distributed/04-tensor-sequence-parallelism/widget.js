(() => {
  const { svg, clear, fmt } = Deck;
  Deck.seg('tSeg', v => {
    const t = +v, s = clear(document.getElementById('tSvg')), cols = ['var(--a)', 'var(--b)', 'var(--c)', 'var(--e)', 'var(--d)', 'var(--a)', 'var(--b)', 'var(--c)'];
    svg('text', { x: 40, y: 20, class: 'tm', text: 'A (d × 4d): split by columns' }, s); svg('text', { x: 380, y: 20, class: 'tm', text: 'B (4d × d): split by rows' }, s);
    for (let i = 0; i < t; i++) {
      svg('rect', { x: 40 + i * 240 / t, y: 30, width: 240 / t - 3, height: 110, rx: 4, style: `fill:${cols[i]}` }, s);
      svg('rect', { x: 380, y: 30 + i * 110 / t, width: 240, height: 110 / t - 3, rx: 4, style: `fill:${cols[i]}` }, s);
    }
    svg('text', { x: 330, y: 175, 'text-anchor': 'middle', class: 't', text: t === 1 ? 'one GPU, no communication' : `${t} GPUs → partial outputs → 1 all-reduce of n × d values` }, s);
    document.getElementById('tOut').innerHTML = `Each GPU stores and computes 1/${t} of both matrices (${(100 / t).toFixed(t > 4 ? 1 : 0)}%). Colour = which GPU owns which slice.`;
  });
  const SS = [1024, 2048, 8192, 32768, 131072], TS = [1, 2, 4, 8];
  Deck.bind(['aS', 'aT'], () => {
    const s = SS[Deck.val('aS')], t = TS[Deck.val('aT')], h = 12288, a = 96, b = 1; Deck.out('aSo', s.toLocaleString()); Deck.out('aTo', t);
    const sbh = s * b * h, none = sbh * (34 + 5 * a * s / h), tp = sbh * (10 + 24 / t + 5 * a * s / (h * t)), sp = none / t, sel = 34 * sbh / t;
    Deck.hbars(document.getElementById('aBars'), [['no parallelism', none, 'var(--d)'], [`TP only (t=${t})`, tp, 'var(--b)'], [`TP + sequence parallel`, sp, 'var(--a)'], ['+ selective recompute', sel, 'var(--e)']].map(([l, v, c]) => ({ label: l, value: v, color: c, text: (v / 2 ** 30).toFixed(v / 2 ** 30 < 10 ? 2 : 0) + ' GiB' })), { log: true, min: 1e7 });
  });
})();
