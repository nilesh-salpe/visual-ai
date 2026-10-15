(() => {
Deck.bind(['kT', 'kN', 'kP', 'kS', 'kM', 'kF'], () => {
  const tasks = Deck.val('kT') * 1000, n = Deck.val('kN'), P = Deck.val('kP') * 1000, T = Deck.val('kS') * 100, mins = Deck.val('kM'), pf = Deck.val('kF');
  Deck.out('kTo', (tasks / 1000) + 'K'); Deck.out('kNo', n); Deck.out('kPo', (P / 1000) + 'K'); Deck.out('kSo', T.toLocaleString()); Deck.out('kMo', mins); Deck.out('kFo', pf + '×');
  let full = 0, cached = 0;
  for (let i = 0; i < n; i++) { const ctx = P + i * T, prev = i ? P + (i - 1) * T : 0; full += ctx; cached += i === 0 ? 1.25 * ctx : 0.1 * prev + 1.25 * (ctx - prev); }
  const sandboxes = Math.ceil(tasks / 1440 * mins * pf);
  Deck.hbars(document.getElementById('kBars'), [{ label: 'input tokens per task (no cache)', value: full, color: 'var(--d)', text: (full / 1e6).toFixed(2) + 'M' },
    { label: 'cost-equivalent with caching', value: cached, color: 'var(--e)', text: (cached / 1e6).toFixed(2) + 'M' }], { max: full * 1.08 });
  document.getElementById('kOut').innerHTML = `${n} steps with a ${(P / 1000)}K-token prefix and ${T.toLocaleString()} tokens added per step: <b>${(full / 1e6).toFixed(2)}M</b> input tokens per task, <b>${(tasks * full / 1e9).toFixed(1)}B</b> a day. Prompt caching (writes 1.25×, reads 0.1×) brings that to about <b>${(100 * cached / full).toFixed(0)}%</b> of the cost. Sandboxes in use at peak: <b>${sandboxes.toLocaleString()}</b> (${mins} minutes per task).`;
});
})();
