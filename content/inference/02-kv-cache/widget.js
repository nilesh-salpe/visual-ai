(() => {
  const { svg, clear, fmt } = Deck;

  Deck.bind(['nP', 'nN'], () => {
    const p = Deck.val('nP'), n = Deck.val('nN'); Deck.out('nPo', p); Deck.out('nNo', n);
    const naive = n * p + n * (n - 1) / 2, cached = p + n;
    Deck.hbars(document.getElementById('nBars'), [
      { label: 'naive (recompute prefix)', value: naive, color: 'var(--d)', text: fmt(naive) + ' positions' },
      { label: 'KV cache', value: cached, color: 'var(--e)', text: fmt(cached) + ' positions · ' + (naive / cached).toFixed(0) + '× less' },
    ], { log: true, min: 10 });
  });
  let dt = 2;
  const kv = () => {
    const [L, H, d, w] = Deck.val('mM').split(',').map(Number), C = 2 ** Deck.val('mC'), B = 2 ** Deck.val('mB');
    Deck.out('mCo', C >= 1024 ? C / 1024 + 'K' : C); Deck.out('mBo', B);
    const per = 2 * L * H * d * dt, tot = per * C * B;
    Deck.out('mTok', Deck.bytes(per)); Deck.out('mTot', Deck.bytes(tot)); Deck.out('mW', w + ' GB');
    Deck.hbars(document.getElementById('mBars'), [{ label: 'weights', value: w * 1e9, color: 'var(--faint)', text: w + ' GB' }, { label: 'KV cache', value: tot, color: tot > w * 1e9 ? 'var(--d)' : 'var(--b)', text: (tot / 1e9).toFixed(1) + ' GB' }], { log: true, min: 1e8 });
  };
  Deck.seg('mD', v => { dt = +v; if (document.getElementById('mM')) kv(); });
  Deck.bind(['mM', 'mC', 'mB'], kv);
  Deck.seg('gSeg', v => {
    const hk = +v, s = clear(document.getElementById('gSvg')), H = 8;
    for (let h = 0; h < H; h++) {
      const x = 40 + h * 75, g = Math.floor(h / (H / hk)), gx = 40 + (g + .5) * (600 / hk) - 30;
      svg('line', { x1: x + 25, y1: 50, x2: gx + 30, y2: 110, style: `stroke:${['var(--a)', 'var(--b)', 'var(--c)', 'var(--e)', 'var(--d)', '#3a8fd8', '#c9a227', '#8a6d3b'][g]};stroke-width:2;opacity:.7` }, s);
      svg('rect', { x, y: 18, width: 50, height: 32, rx: 6, class: 'f-a' }, s);
      svg('text', { x: x + 25, y: 39, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11px;font-weight:600', text: 'Q' + h }, s);
    }
    for (let g = 0; g < hk; g++) {
      const gx = 40 + (g + .5) * (600 / hk) - 30;
      svg('rect', { x: gx, y: 110, width: 60, height: 34, rx: 6, style: `fill:${['var(--a)', 'var(--b)', 'var(--c)', 'var(--e)', 'var(--d)', '#3a8fd8', '#c9a227', '#8a6d3b'][g]}` }, s);
      svg('text', { x: gx + 30, y: 132, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11px;font-weight:600', text: 'KV' + g }, s);
    }
    document.getElementById('gOut').innerHTML = `${H} query heads share <b>${hk}</b> KV head${hk > 1 ? 's' : ''} → KV cache is <b>${H / hk}×</b> smaller than MHA`;
  });

})();
