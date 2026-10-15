(() => {
const C = (n, k) => { if (k < 0 || k > n) return 0; let r = 1; for (let i = 1; i <= k; i++) r = r * (n - k + i) / i; return r; };
Deck.bind(['eP', 'eK'], () => {
  const p = Deck.val('eP'), k = Deck.val('eK'); Deck.out('ePo', (100 * p).toFixed(0) + '%'); Deck.out('eKo', k);
  const at = 1 - Math.pow(1 - p, k), hat = Math.pow(p, k);
  Deck.hbars(document.getElementById('eBars'), [{ label: 'success rate per trial', value: p, color: 'var(--faint)', text: (100 * p).toFixed(0) + '%' }, { label: `pass@${k} (any of k succeeds)`, value: at, color: 'var(--a)', text: (100 * at).toFixed(1) + '%' },
    { label: `pass^${k} (all k succeed)`, value: hat, color: 'var(--d)', text: (100 * hat).toFixed(1) + '%' }], { max: 1 });
  document.getElementById('eOut').innerHTML = `With independent trials: pass@k = 1 − (1 − p)^k, pass^k = p^k. A ${(100 * p).toFixed(0)}% agent is consistent across ${k} tries only ${(100 * hat).toFixed(1)}% of the time. τ-bench estimates pass^k from n trials as C(c, k) / C(n, k) for c successes.`;
});
})();
