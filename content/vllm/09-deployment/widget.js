(() => {
  const { svg, clear, fmt } = Deck;
  const PS = [8, 32, 70, 120, 235, 405, 671, 1000], PREC = [['BF16', 2], ['FP8', 1], ['FP4', 0.5]];
  const GPUS = [['L40S 48 GB, PCIe', 48, false], ['H100 80 GB', 80, true], ['H200 141 GB', 141, true], ['B200 180 GB', 180, true]];
  const s = document.getElementById('dpSvg');
  Deck.bind(['dpN', 'dpQ', 'dpG', 'dpR'], () => {
    const N = PS[Deck.val('dpN')] * 1e9, [pn, pb] = PREC[Deck.val('dpQ')], [gname, mem, nvl] = GPUS[Deck.val('dpG')], R = Deck.val('dpR'), per = 8;
    Deck.out('dpNo', PS[Deck.val('dpN')] + 'B'); Deck.out('dpQo', pn); Deck.out('dpGo', gname); Deck.out('dpRo', R);
    const W = N * pb / 1e9, usable = mem * 0.92;
    let g = 1; while (g * usable * 0.75 < W) g++;          // keep at least a quarter of usable memory for KV cache
    let tp = 1, pp = 1;
    if (g <= per) { const p2 = Math.pow(2, Math.ceil(Math.log2(g))); if (nvl) tp = p2; else pp = g; }
    else { tp = nvl ? per : 1; pp = nvl ? Math.ceil(g / per) : Math.ceil(g / per) * per / 1; if (!nvl) { tp = 1; pp = g; } }
    const gr = tp * pp, total = gr * R, kv = gr * usable - W;
    const nodesPer = Math.ceil(gr / per), perNode = Math.max(1, Math.floor(per / gr));
    const nodes = gr >= per ? nodesPer * R : Math.ceil(R / perNode);
    clear(s);
    const show = Math.min(nodes, 4), cw = 640 / Math.min(show, 2), rows = Math.ceil(show / 2);
    let rep = 0, slot = 0;
    const col = ['var(--a)', 'var(--b)', 'var(--c)', 'var(--e)', 'var(--d)', 'var(--faint)'];
    for (let n = 0; n < show; n++) {
      const x = 10 + (n % 2) * cw, y = 10 + Math.floor(n / 2) * 110;
      svg('rect', { x, y, width: cw - 10, height: 100, rx: 10, style: 'fill:var(--panel);stroke:var(--line)' }, s);
      svg('text', { x: x + 10, y: y + 18, class: 't', style: 'font-weight:700', text: 'node ' + (n + 1) + (nvl ? ' · NVLink' : ' · PCIe') }, s);
      for (let k = 0; k < per; k++) {
        let r = -1, stage = 0;
        if (gr >= per) { r = Math.floor(n / nodesPer); stage = n % nodesPer; if (r >= R || stage * per + k >= gr) r = -1; }
        else { const idx = n * perNode + Math.floor(k / gr); if (Math.floor(k / gr) < perNode && idx < R) r = idx; }
        const gx = x + 10 + (k % 4) * ((cw - 30) / 4), gy = y + 28 + Math.floor(k / 4) * 34;
        svg('rect', { x: gx, y: gy, width: (cw - 30) / 4 - 6, height: 28, rx: 5, style: `fill:${r < 0 ? 'var(--panel-2)' : col[r % 6]};opacity:${r < 0 ? 1 : 0.85}` }, s);
        if (r >= 0) svg('text', { x: gx + ((cw - 30) / 4 - 6) / 2, y: gy + 18, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:700', text: 'R' + (r + 1) + (pp > 1 && tp === per ? '·S' + (stage + 1) : '') }, s);
      }
    }
    if (nodes > show) svg('text', { x: 330, y: 10 + rows * 110 + 6, 'text-anchor': 'middle', class: 't', text: `… ${nodes - show} more node${nodes - show > 1 ? 's' : ''}` }, s);
    const flags = (tp > 1 ? ` -tp ${tp}` : '') + (pp > 1 ? ` -pp ${pp}` : '');
    const multi = gr > per;
    const cmd = multi ? `vllm serve MODEL${flags} --distributed-executor-backend ray   # on a Ray cluster of ${nodesPer} nodes, or --nnodes ${nodesPer} --node-rank i (--headless on workers)`
      : R > 1 && gr * R <= per ? `vllm serve MODEL${flags} --data-parallel-size ${R}   # ${R} replicas on one node, one endpoint`
      : `vllm serve MODEL${flags}   # once per replica (${R}), behind a router`;
    document.getElementById('dpCmd').textContent = cmd;
    document.getElementById('dpOut').innerHTML = `Weights ${W.toFixed(0)} GB; one replica needs <b>${gr} GPU${gr > 1 ? 's' : ''}</b> (${tp > 1 ? 'TP ' + tp : ''}${tp > 1 && pp > 1 ? ' × ' : ''}${pp > 1 ? 'PP ' + pp : ''}${gr === 1 ? 'single GPU' : ''}) with about <b>${kv.toFixed(0)} GB</b> left for KV cache. ${R} replica${R > 1 ? 's' : ''}: <b>${total} GPUs on ${nodes} node${nodes > 1 ? 's' : ''}</b>.` + (!nvl && gr > 1 ? ' No NVLink, so pipeline parallelism instead of tensor parallelism.' : '');
  });
})();
