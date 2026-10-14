(() => {
  const { svg, clear, fmt } = Deck;
  let mode = 'gpipe';
  const sim = (orders, p, tf, tb) => {
    const done = {}, ptr = Array(p).fill(0), clock = Array(p).fill(0), boxes = [];
    let prog = true;
    while (prog) { prog = false;
      for (let s = 0; s < p; s++) { if (ptr[s] >= orders[s].length) continue;
        const [op, i] = orders[s][ptr[s]];
        const deps = op === 'F' ? (s > 0 ? [`F${s - 1}_${i}`] : []) : [`F${s}_${i}`].concat(s < p - 1 ? [`B${s + 1}_${i}`] : []);
        if (deps.every(d => d in done)) { const st = Math.max(clock[s], ...deps.map(d => done[d])); const en = st + (op === 'F' ? tf : tb); done[`${op}${s}_${i}`] = en; clock[s] = en; boxes.push([s, st, en, op, i]); ptr[s]++; prog = true; } } }
    return [Math.max(...clock), boxes];
  };
  const orders = (p, m) => {
    if (mode === 'naive') return [...Array(p)].map(() => [['F', 0], ['B', 0]]);
    if (mode === 'gpipe') return [...Array(p)].map(() => [...Array(m)].map((_, i) => ['F', i]).concat([...Array(m)].map((_, i) => ['B', i])));
    return [...Array(p)].map((_, s) => { const w = Math.min(p - s - 1, m), o = [...Array(w)].map((_, i) => ['F', i]); let f = w, b = 0; while (f < m) { o.push(['F', f++], ['B', b++]); } while (b < m) o.push(['B', b++]); return o; });
  };
  const draw = () => {
    const p = Deck.val('pP'), m = mode === 'naive' ? 1 : Deck.val('pM'); Deck.out('pPo', p); Deck.out('pMo', mode === 'naive' ? '1 (whole batch)' : m);
    const [mk, boxes] = sim(orders(p, m), p, 1, 2), s = clear(document.getElementById('pSvg')), W = 590, rh = Math.min(26, 200 / p), sx = W / mk;
    for (let st = 0; st < p; st++) { svg('rect', { x: 60, y: 10 + st * rh, width: W, height: rh - 3, style: 'fill:var(--panel-2)' }, s); svg('text', { x: 52, y: 10 + st * rh + rh / 2 + 2, 'text-anchor': 'end', class: 'tm', style: 'font-size:10px', text: 'GPU ' + (st + 1) }, s); }
    boxes.forEach(([st, a, b, op, i]) => { svg('rect', { x: 60 + a * sx, y: 10 + st * rh, width: Math.max(1, (b - a) * sx - 1), height: rh - 3, rx: 2, style: `fill:${op === 'F' ? 'var(--a)' : 'var(--b)'}` }, s); if ((b - a) * sx > 14) svg('text', { x: 60 + (a + b) / 2 * sx, y: 10 + st * rh + rh / 2 + 3, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:10px', text: i }, s); });
    const ideal = m * 3, bub = (mk - ideal) / ideal;
    const peak = mode === 'gpipe' ? m : mode === 'naive' ? 1 : Math.min(p, m);
    document.getElementById('pOut').innerHTML = `Time ${mk} units vs ideal ${ideal}: bubble <b>${(100 * bub).toFixed(1)}%</b> = (p−1)/m = ${(p - 1)}/${m}. Peak in-flight micro-batches on GPU 1: <b>${peak}</b>.`;
  };
  Deck.seg('pSeg', v => { mode = v; draw(); }); Deck.bind(['pP', 'pM'], draw);
  let vv = 1;
  const bdraw = () => {
    const p = Deck.val('bP'); Deck.out('bPo', p);
    const s = clear(document.getElementById('bSvg')), X = m => 60 + Math.log2(m) / 8 * 570, Y = b => 200 - Math.min(1, b) * 180;
    [0, 0.25, 0.5, 0.75, 1].forEach(v => { svg('line', { x1: 60, x2: 630, y1: Y(v), y2: Y(v), class: 'ln' }, s); svg('text', { x: 52, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm', text: (100 * v) + '%' }, s); });
    svg('line', { x1: 60, x2: 630, y1: Y(0.1), y2: Y(0.1), style: 'stroke:var(--d);stroke-dasharray:5 4' }, s);
    [1, 4, 16, 64, 256].forEach(m => svg('text', { x: X(m), y: 218, 'text-anchor': 'middle', class: 'tm', text: 'm=' + m }, s));
    let pts = ''; for (let e = 0; e <= 8.001; e += 0.05) { const m = Math.pow(2, e); pts += `${X(m)},${Y((p - 1) / (vv * m))} `; }
    svg('polyline', { points: pts, fill: 'none', style: 'stroke:var(--a);stroke-width:3' }, s);
    const need = Math.ceil((p - 1) / (vv * 0.1));
    svg('text', { x: 620, y: 30, 'text-anchor': 'end', class: 't', text: `need m ≥ ${need} micro-batches for ≤ 10% bubble` }, s);
  };
  Deck.bind(['bP'], bdraw); Deck.seg('bV', v => { vv = +v; bdraw(); });
})();
