(() => {
  const { svg, clear, fmt } = Deck;
  const M = { '8b': { L: 32, kv: 8, d: 128, P: 8.03 }, '70b': { L: 80, kv: 8, d: 128, P: 70.6 }, 'q7': { L: 28, kv: 4, d: 128, P: 7.62 } }, TPS = [1, 2, 4, 8], G = 2 ** 30;
  let m = '8b', kvb = 2, wb = 2;
  const draw = () => {
    const tp = TPS[Deck.val('qT')], mm = M[m]; Deck.out('qTo', tp);
    const w = mm.P * 1e9 * wb / G / tp, budget = 0.92 * 80, kvg = budget - w - 4, perTok = 2 * mm.L * mm.kv * mm.d * kvb / tp, tokens = kvg > 0 ? Math.floor(kvg * G / perTok) : 0;
    Deck.hbars(document.getElementById('qBars'), [{ label: 'usable per GPU (0.92 × 80 GB)', value: budget, color: 'var(--faint)', text: budget.toFixed(1) + ' GiB' }, { label: 'weights per GPU', value: w, color: w > budget ? 'var(--d)' : 'var(--b)', text: w.toFixed(1) + ' GiB' },
      { label: 'KV cache per GPU', value: Math.max(0, kvg), color: 'var(--e)', text: Math.max(0, kvg).toFixed(1) + ' GiB' }], { max: 160 });
    document.getElementById('qOut').innerHTML = kvg <= 0 ? '<b>Does not fit</b>: increase TP or quantize the weights.' : `KV tokens across the TP group: <b>${tokens.toLocaleString()}</b> → <b>${Math.floor(tokens / 8192)}</b> concurrent 8K-token requests (${(perTok * tp / 1024).toFixed(0)} KiB per token in total).`;
  };
  Deck.seg('qSeg', v => { m = v; draw(); }); Deck.seg('qK', v => { kvb = +v; draw(); }); Deck.seg('qW', v => { wb = +v; draw(); }); Deck.bind(['qT'], draw);
})();
