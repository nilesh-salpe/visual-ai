(() => {
  const { svg, clear, fmt } = Deck;
  Deck.bind(['zN', 'zR', 'zM'], () => {
    const N = Math.pow(10, Deck.val('zN')), r = Deck.val('zR'), m = Deck.val('zM'), rate = r * m;
    Deck.out('zNo', N >= 1e9 ? (N / 1e9).toFixed(1) + 'B' : (N / 1e6).toFixed(0) + 'M'); Deck.out('zRo', r.toLocaleString()); Deck.out('zMo', m);
    const days = N / rate / 86400, hosts = rate / (1 / (0.5 * 11)), bw = rate * 22e3 * 8;
    Deck.out('zD', days < 1 ? (days * 24).toFixed(1) + ' h' : days.toFixed(days < 10 ? 1 : 0)); Deck.out('zH', Math.round(hosts).toLocaleString()); Deck.out('zB', bw >= 1e9 ? (bw / 1e9).toFixed(1) + ' Gb/s' : (bw / 1e6).toFixed(0) + ' Mb/s');
  });
})();
