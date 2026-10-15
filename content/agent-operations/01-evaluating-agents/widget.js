(() => {
  const { svg, clear } = Deck;
  document.querySelectorAll('.dgm').forEach(box => {
    const caps = JSON.parse(box.dataset.steps), els = [...box.querySelectorAll('[data-step]')], max = Math.max(0, ...els.map(e => +e.dataset.step)), cap = box.querySelector('.dgcap');
    let k = max, full = true;
    const show = () => {
      els.forEach(e => { const s = +e.dataset.step; e.style.opacity = s <= k ? 1 : 0.08; e.style.transition = 'opacity .25s'; e.querySelectorAll('rect').forEach(r => r.style.strokeWidth = s === k && k ? 3.5 : 2); });
      cap.innerHTML = k === 0 ? 'Press <b>next step</b> to walk through the design.' : k === max && full ? 'Full design shown. Press <b>reset</b>, then <b>next step</b>, to walk through it one step at a time.' : `<b>Step ${k} of ${max}.</b> ${caps[k - 1] || ''}`;
      full = false;
    };
    box.querySelector('[data-dg=next]').addEventListener('click', () => { k = Math.min(max, k + 1); show(); });
    box.querySelector('[data-dg=all]').addEventListener('click', () => { k = max; full = false; show(); cap.innerHTML = '<b>Full design.</b> ' + caps.map((c, i) => `${i + 1}. ${c}`).join(' '); });
    box.querySelector('[data-dg=reset]').addEventListener('click', () => { k = 0; show(); });
    show();
  });
  const C = (n, k) => { if (k < 0 || k > n) return 0; let r = 1; for (let i = 1; i <= k; i++) r = r * (n - k + i) / i; return r; };
  Deck.bind(['eP', 'eK'], () => {
    const p = Deck.val('eP'), k = Deck.val('eK'); Deck.out('ePo', (100 * p).toFixed(0) + '%'); Deck.out('eKo', k);
    const at = 1 - Math.pow(1 - p, k), hat = Math.pow(p, k);
    Deck.hbars(document.getElementById('eBars'), [{ label: 'success rate per trial', value: p, color: 'var(--faint)', text: (100 * p).toFixed(0) + '%' }, { label: `pass@${k} (any of k succeeds)`, value: at, color: 'var(--a)', text: (100 * at).toFixed(1) + '%' },
      { label: `pass^${k} (all k succeed)`, value: hat, color: 'var(--d)', text: (100 * hat).toFixed(1) + '%' }], { max: 1 });
    document.getElementById('eOut').innerHTML = `With independent trials: pass@k = 1 − (1 − p)^k, pass^k = p^k. A ${(100 * p).toFixed(0)}% agent is consistent across ${k} tries only ${(100 * hat).toFixed(1)}% of the time. τ-bench estimates pass^k from n trials as C(c, k) / C(n, k) for c successes.`;
  });
})();
