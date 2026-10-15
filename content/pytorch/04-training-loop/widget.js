(() => {
  const { svg, clear, fmt } = Deck;
  let mode = 'mixed';
  const draw = () => {
    const N = Math.pow(10, Deck.val('cN')), f = x => x >= 1e12 ? (x / 1e12).toFixed(2) + ' TB' : (x / 1e9).toFixed(1) + ' GB';
    Deck.out('cNo', N >= 1e9 ? (N / 1e9).toFixed(1) + 'B' : (N / 1e6).toFixed(0) + 'M');
    const rows = mode === 'mixed' ? [['BF16 weights', 2], ['BF16 gradients', 2], ['FP32 master weights', 4], ['AdamW m (FP32)', 4], ['AdamW v (FP32)', 4]] : [['FP32 weights', 4], ['FP32 gradients', 4], ['AdamW m', 4], ['AdamW v', 4]];
    Deck.hbars(document.getElementById('cBars'), rows.map(([l, b]) => ({ label: l, value: b * N, color: /grad/.test(l) ? 'var(--faint)' : /Adam/.test(l) ? 'var(--b)' : 'var(--a)', text: f(b * N) })), { max: 4 * N * 1.05 });
    const ck = rows.filter(r => !/grad/.test(r[0])).reduce((a, r) => a + r[1], 0) * N, tot = rows.reduce((a, r) => a + r[1], 0) * N;
    document.getElementById('cOut').innerHTML = `Training state ≈ <b>${f(tot)}</b> (${rows.reduce((a, r) => a + r[1], 0)} bytes/param). A resumable checkpoint (no gradients) ≈ <b>${f(ck)}</b>; weights alone would be ${f((mode === 'mixed' ? 2 : 4) * N)}.`;
  };
  Deck.bind(['cN'], draw); Deck.seg('cSeg', v => { mode = v; draw(); });
})();
