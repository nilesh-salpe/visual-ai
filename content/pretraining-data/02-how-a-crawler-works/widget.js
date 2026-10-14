(() => {
  const { svg, clear, fmt } = Deck;
  Deck.bind(['cT', 'cH', 'cK'], () => {
    const T = Math.round(Math.pow(10, Deck.val('cT'))), H = Math.round(Math.pow(10, Deck.val('cH'))), k = Deck.val('cK'), d = 0.5;
    Deck.out('cTo', T.toLocaleString()); Deck.out('cHo', H.toLocaleString()); Deck.out('cKo', k);
    const byConn = T / d, byPolite = H / (d * (1 + k)), rate = Math.min(byConn, byPolite);
    Deck.hbars(document.getElementById('cBars'), [{ label: 'limit from connections (T ÷ d)', value: byConn, color: byConn <= byPolite ? 'var(--d)' : 'var(--faint)', text: byConn.toLocaleString(undefined, { maximumFractionDigits: 0 }) + ' pages/s' },
      { label: 'limit from politeness (H ÷ d(1 + k))', value: byPolite, color: byPolite < byConn ? 'var(--d)' : 'var(--faint)', text: byPolite.toLocaleString(undefined, { maximumFractionDigits: 1 }) + ' pages/s' },
      { label: 'achieved', value: rate, color: 'var(--a)', text: rate.toLocaleString(undefined, { maximumFractionDigits: 1 }) + ' pages/s' }], { log: true, min: 0.05 });
    document.getElementById('cOut').innerHTML = `Bottleneck: <b>${byConn <= byPolite ? 'connections' : 'politeness'}</b>. Each host sees at most one request every ${(d * (1 + k)).toFixed(1)} s. ${byPolite < byConn ? 'Add more hosts to the frontier, not more connections.' : 'Add connections; there are enough hosts.'}`;
  });
})();
