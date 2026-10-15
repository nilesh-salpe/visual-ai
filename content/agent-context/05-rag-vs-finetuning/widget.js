(() => {
Deck.bind(['rcN', 'rcQ', 'rcK', 'rcP'], () => {
  const N = Deck.val('rcN') * 10000, Q = Deck.val('rcQ'), K = Deck.val('rcK') * 1000, P = Deck.val('rcP');
  Deck.out('rcNo', N >= 1e6 ? (N / 1e6).toFixed(2) + 'M' : Math.round(N / 1000) + 'K'); Deck.out('rcQo', Q.toLocaleString()); Deck.out('rcKo', K / 1000 + 'K'); Deck.out('rcPo', '$' + P.toFixed(2));
  const ask = 500, rag = (K + ask) * P / 1e6, lc = (N + ask) * P / 1e6, lcc = (0.1 * N + ask) * P / 1e6;
  const fits = N <= 1e6;
  Deck.hbars(document.getElementById('rcBars'), [
    { label: 'RAG: retrieved chunks', value: rag * Q, color: 'var(--a)', text: '$' + Math.round(rag * Q).toLocaleString() + '/day' },
    { label: 'long context, no cache', value: fits ? lc * Q : 0, color: 'var(--d)', text: fits ? '$' + Math.round(lc * Q).toLocaleString() + '/day' : 'does not fit' },
    { label: 'long context, warm cache (0.1×)', value: fits ? lcc * Q : 0, color: 'var(--b)', text: fits ? '$' + Math.round(lcc * Q).toLocaleString() + '/day' : 'does not fit' }], { max: Math.max(rag, fits ? lc : rag) * Q * 1.05 });
  document.getElementById('rcOut').innerHTML = fits
    ? `Per query: RAG <b>$${rag.toFixed(4)}</b>, long context <b>$${lc.toFixed(3)}</b> (${(lc / rag).toFixed(0)}× RAG), or <b>$${lcc.toFixed(4)}</b> if every query hits a warm cache. Input tokens only; cache writes (1.25×) and output are extra.`
    : `A ${(N / 1e6).toFixed(1)}M-token corpus does not fit in a 1M-token context window: retrieval is required.`;
});
})();
