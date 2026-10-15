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
