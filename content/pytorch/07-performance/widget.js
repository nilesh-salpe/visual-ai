(() => {
  const { svg, clear, fmt } = Deck;
  Deck.bind(['aT', 'aH', 'aB'], () => {
    const T = Math.pow(2, Deck.val('aT')), H = Deck.val('aH'), B = Deck.val('aB'), D = 128; Deck.out('aTo', T.toLocaleString()); Deck.out('aHo', H); Deck.out('aBo', B);
    const sc = B * H * T * T * 2, qkv = 3 * B * H * T * D * 2, g = x => x >= 2 ** 30 ? (x / 2 ** 30).toFixed(x >= 10 * 2 ** 30 ? 0 : 2) + ' GiB' : (x / 2 ** 20).toFixed(0) + ' MiB';
    Deck.hbars(document.getElementById('aBars'), [{ label: 'score matrix (naive attention)', value: sc, color: sc > 80 * 2 ** 30 ? 'var(--d)' : 'var(--b)', text: g(sc) }, { label: 'q, k, v (all fused attention needs)', value: qkv, color: 'var(--e)', text: g(qkv) }], { log: true, min: 2 ** 18 });
    document.getElementById('aOut').innerHTML = `Scores are <b>${(sc / qkv).toFixed(0)}×</b> q, k, v (= T / (1.5 · D)). ${sc > 80 * 2 ** 30 ? 'Larger than an 80 GB GPU for one layer: only fused attention works.' : ''}`;
  });
})();
