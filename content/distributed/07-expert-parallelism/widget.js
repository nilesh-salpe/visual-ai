(() => {
  const { svg, clear, fmt } = Deck;
  Deck.bind(['eI'], () => {
    const sk = Deck.val('eI'); Deck.out('eIo', sk.toFixed(1));
    const w = [...Array(8)].map((_, i) => Math.exp(sk * (1 - i / 7) * 2)), tot = w.reduce((a, b) => a + b);
    const gpu = [0, 1, 2, 3].map(g => (w[2 * g] + w[2 * g + 1]) / tot);
    Deck.hbars(document.getElementById('eBars'), gpu.map((f, g) => ({ label: `GPU ${g} (experts ${2 * g + 1}, ${2 * g + 2})`, value: f, color: f === Math.max(...gpu) ? 'var(--d)' : 'var(--a)', text: (100 * f).toFixed(0) + '% of tokens' })), { max: 1 });
    document.getElementById('eOut').innerHTML = `The busiest GPU gets ${(100 * Math.max(...gpu)).toFixed(0)}% of the routed tokens vs a fair 25%: the layer takes <b>${(Math.max(...gpu) / 0.25).toFixed(2)}×</b> as long as with perfect balance.`;
  });
})();
