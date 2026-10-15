(() => {
Deck.bind(['cS', 'cP', 'cT', 'cC'], () => {
  const S = Deck.val('cS'), P = Deck.val('cP'), T = Deck.val('cT'), cache = document.getElementById('cC').checked;
  Deck.out('cSo', S); Deck.out('cPo', P.toLocaleString()); Deck.out('cTo', T.toLocaleString());
  let full = 0, cached = 0;
  for (let i = 0; i < S; i++) { const ctx = P + i * T; full += ctx; const prev = i ? P + (i - 1) * T : 0; cached += i === 0 ? 1.25 * ctx : 0.1 * prev + 1.25 * (ctx - prev); }
  const eff = cache ? cached : full;
  Deck.hbars(document.getElementById('cBars'), [{ label: 'naive: input tokens re-sent', value: full, color: 'var(--d)', text: Math.round(full).toLocaleString() + ' tokens' },
    { label: 'with prompt caching (cost-equivalent)', value: cached, color: 'var(--e)', text: Math.round(cached).toLocaleString() + ' token-equivalents' }], { max: full * 1.05 });
  document.getElementById('cOut').innerHTML = `${S} steps, ${P.toLocaleString()}-token prefix, +${T.toLocaleString()} tokens per step: last call sends ${(P + (S - 1) * T).toLocaleString()} tokens; total ${Math.round(full).toLocaleString()}. Caching (writes 1.25×, reads 0.1×, 5-minute TTL) cuts input cost to <b>${(100 * cached / full).toFixed(0)}%</b> if each step hits the cache. ${cache ? '' : '(Tick "cache" to compare.)'}`;
});
})();
