(() => {
  const { svg, clear, fmt } = Deck;
  const NS = [1e9, 7e9, 70e9, 405e9, 1e12, 2e12], DS = [1e11, 2e12, 15e12, 30e12], GS = [1, 8, 256, 2048, 16384, 65536];
  const lab = v => v >= 1e12 ? (v / 1e12) + 'T' : (v / 1e9) + 'B';
  Deck.bind(['wN', 'wD', 'wG'], () => {
    const N = NS[Deck.val('wN')], D = DS[Deck.val('wD')], G = GS[Deck.val('wG')];
    Deck.out('wNo', lab(N)); Deck.out('wDo', lab(D) + ' tokens'); Deck.out('wGo', G.toLocaleString());
    Deck.out('wM', (16 * N / 1e12 >= 1 ? (16 * N / 1e12).toFixed(1) + ' TB' : (16 * N / 1e9).toFixed(0) + ' GB') + ` (${(16 * N / 80e9).toFixed(1)}× one GPU)`);
    Deck.out('wF', (6 * N * D).toExponential(1));
    const days = 6 * N * D / (989e12 * 0.4 * G) / 86400;
    Deck.out('wT', days > 3650 ? (days / 365).toFixed(0) + ' years' : days.toFixed(days < 10 ? 1 : 0));
  });
})();
