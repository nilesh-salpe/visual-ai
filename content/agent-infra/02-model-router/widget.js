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
  Deck.bind(['rP', 'rR', 'rE'], () => {
    const p = Deck.val('rP') / 100, r = Deck.val('rR') / 100, e = Deck.val('rE') / 100;
    Deck.out('rPo', Math.round(p * 100) + '%'); Deck.out('rRo', Math.round(r * 100) + '%'); Deck.out('rEo', Math.round(e * 100) + '%');
    const router = p * r + (1 - p), cascade = r + (1 - p) + p * e;
    Deck.hbars(document.getElementById('rBars'), [{ label: 'always the large model', value: 1, color: 'var(--d)', text: '100%' },
      { label: 'router (predict, then send once)', value: router, color: 'var(--a)', text: (100 * router).toFixed(0) + '%' },
      { label: 'cascade (small first, escalate on reject)', value: cascade, color: 'var(--e)', text: (100 * cascade).toFixed(0) + '%' }], { max: Math.max(1, cascade) * 1.05 });
    document.getElementById('rOut').innerHTML = `If ${Math.round(p * 100)}% of requests are easy and the small model costs ${Math.round(r * 100)}% of the large one, a perfect router costs <b>${(100 * router).toFixed(0)}%</b> of always-large. A cascade pays the small model on every request and escalates the hard ${Math.round((1 - p) * 100)}% plus ${Math.round(e * 100)}% of easy ones its scorer wrongly rejects: <b>${(100 * cascade).toFixed(0)}%</b>, but it never answers a hard request with the small model unless the scorer is fooled. Real routers also misroute; RouteLLM reports over 2× savings in some cases without quality loss.`;
  });
})();
