(() => {
  const { svg, clear, fmt } = Deck;
  Deck.bind(['gL', 'gC', 'gV'], () => {
    const L = Deck.val('gL'), C = Deck.val('gC'), V = Deck.val('gV'); Deck.out('gLo', L); Deck.out('gCo', C); Deck.out('gVo', V.toLocaleString());
    const P = L * (12 * C * C + 2 * C) + V * C, f = x => x >= 1e9 ? (x / 1e9).toFixed(2) + 'B' : (x / 1e6).toFixed(1) + 'M';
    const secs = 6 * P * 1e9 / (989e12 * 0.4);
    Deck.out('gP', f(P)); Deck.out('gM', (16 * P / 1e9).toFixed(1) + ' GB'); Deck.out('gT', secs < 3600 ? (secs / 60).toFixed(1) + ' min' : (secs / 3600).toFixed(1) + ' h');
  });
})();
