(() => {
  const { svg, clear, fmt } = Deck;
  const DOM = { web: 12000, code: 800, math: 150, books: 60, wikipedia: 20, 'low-resource languages': 5 }, B = 15000;
  Deck.bind(['mT', 'mC'], () => {
    const T = Deck.val('mT'), cap = Deck.val('mC'); Deck.out('mTo', T.toFixed(1)); Deck.out('mCo', cap);
    const tot = Object.values(DOM).reduce((a, b) => a + b), q = {}; Object.entries(DOM).forEach(([k, v]) => { q[k] = Math.pow(v / tot, 1 / T); });
    const z = Object.values(q).reduce((a, b) => a + b); let w = {}; Object.keys(q).forEach(k => { w[k] = q[k] / z; });
    const base = { ...w }, capped = new Set();
    for (let it = 0; it < 10; it++) { const over = Object.keys(w).filter(k => !capped.has(k) && w[k] * B / DOM[k] > cap + 1e-9); if (!over.length) break;
      over.forEach(k => { w[k] = cap * DOM[k] / B; capped.add(k); }); const free = 1 - [...capped].reduce((a, k) => a + w[k], 0), rest = Object.keys(w).filter(k => !capped.has(k)), rz = rest.reduce((a, k) => a + base[k], 0);
      rest.forEach(k => { w[k] = free * base[k] / rz; }); }
    Deck.hbars(document.getElementById('mBars'), Object.keys(DOM).map(k => { const ep = w[k] * B / DOM[k]; return { label: `${k} (${DOM[k] >= 1000 ? DOM[k] / 1000 + 'T' : DOM[k] + 'B'})`, value: w[k], color: capped.has(k) ? 'var(--b)' : 'var(--a)', text: `${(100 * w[k]).toFixed(1)}% · ${ep.toFixed(1)} ep` }; }), { max: 1 });
    document.getElementById('mOut').innerHTML = `Orange = capped at ${cap} epochs, extra budget redistributed. ${cap > 4 ? 'Above ~4 epochs, repeated tokens are worth much less than new ones.' : 'Within the ~4-epoch range where repetition is nearly free.'}`;
  });
})();
