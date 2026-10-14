(() => {
  const { svg, clear, fmt } = Deck;

  Deck.bind(['kK', 'kE'], () => {
    const k = Deck.val('kK'), e = Deck.val('kE'); Deck.out('kKo', (100 * k).toFixed(0) + '%'); Deck.out('kEo', e);
    const acc = n => k + (1 - k) / Math.max(1, n - e);
    Deck.hbars(document.getElementById('kBars'), [4, 10].map(n => ({ label: `${n} options (chance ${(100 / n).toFixed(0)}%)`, value: acc(n), color: n === 4 ? 'var(--b)' : 'var(--a)', text: (100 * acc(n)).toFixed(1) + '%' })), { max: 1 });
  });

})();
