(() => {
  const { svg, clear, fmt } = Deck;

  (() => {
    const s = document.getElementById('p1Svg');
    svg('rect', { x: 20, y: 40, width: 150, height: 40, rx: 6, class: 'f-a' }, s);
    svg('text', { x: 95, y: 65, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:700', text: 'prefill (P tokens)' }, s);
    for (let i = 0; i < 14; i++) svg('rect', { x: 178 + i * 32, y: 40, width: 28, height: 40, rx: 4, style: 'fill:var(--b)' }, s);
    svg('text', { x: 400, y: 100, 'text-anchor': 'middle', class: 'tm', text: 'decode: one token per step, each step reads all weights + KV cache' }, s);
    svg('line', { x1: 172, x2: 172, y1: 26, y2: 92, style: 'stroke:var(--d);stroke-width:2;stroke-dasharray:4 3' }, s);
    svg('text', { x: 172, y: 20, 'text-anchor': 'middle', class: 't', style: 'fill:var(--d);font-size:11px;font-weight:600', text: 'first token (TTFT)' }, s);
    svg('text', { x: 210, y: 130, class: 'tm', style: 'font-size:11px', text: '↔ TPOT = time between tokens' }, s);
  })();
  const step = b => 18 + 0.12 * b;
  const gp = () => {
    const slo = Deck.val('sloT'), b = Math.round(Math.pow(2, Deck.val('bB')));
    Deck.out('sloTo', slo + ' ms'); Deck.out('bBo', b);
    const bmax = Math.max(0, Math.floor((slo - 18) / 0.12));
    Deck.out('kT', step(b).toFixed(1) + ' ms'); Deck.out('kX', fmt(b / step(b) * 1000, 0));
    Deck.out('kB', bmax ? bmax : 'none'); Deck.out('kG', bmax ? fmt(Math.min(b, bmax) / step(Math.min(b, bmax)) * 1000, 0) : '0');
    document.getElementById('kT').style.color = step(b) <= slo ? 'var(--e)' : 'var(--d)';
    const s = clear(document.getElementById('gpSvg')), L = 60, R = 640, T = 14, B = 220;
    const X = x => L + Math.log2(x) / 8 * (R - L), ymax = 256 / step(256) * 1000 * 1.1, Y = v => B - v / ymax * (B - T);
    if (bmax < 256) svg('rect', { x: X(Math.max(1, bmax)), y: T, width: R - X(Math.max(1, bmax)), height: B - T, style: 'fill:var(--d-soft)' }, s);
    [1, 4, 16, 64, 256].forEach(v => { svg('line', { x1: X(v), x2: X(v), y1: T, y2: B, class: 'ln' }, s); svg('text', { x: X(v), y: B + 16, 'text-anchor': 'middle', class: 'tm tc', text: v }, s); });
    let pts = ''; for (let v = 1; v <= 256; v *= 1.05) pts += `${X(v)},${Y(v / step(v) * 1000)} `;
    svg('polyline', { points: pts, fill: 'none', style: 'stroke:var(--a);stroke-width:3' }, s);
    svg('circle', { cx: X(b), cy: Y(b / step(b) * 1000), r: 7, style: `fill:${step(b) <= slo ? 'var(--a)' : 'var(--d)'};stroke:var(--panel);stroke-width:2` }, s);
    svg('text', { x: (L + R) / 2, y: B + 34, 'text-anchor': 'middle', class: 'tm', text: 'batch size (red zone violates the TPOT SLO)' }, s);
    svg('text', { x: 14, y: (T + B) / 2, 'text-anchor': 'middle', class: 'tm', transform: `rotate(-90 14 ${(T + B) / 2})`, text: 'tokens / s' }, s);
  };
  Deck.bind(['sloT', 'bB'], gp);
  const lat = () => {
    const P = Math.round(Math.pow(2, Deck.val('rP'))), O = Math.round(Math.pow(2, Deck.val('rO'))), sp = +Deck.val('rS'), d = +Deck.val('rD');
    Deck.out('rPo', P.toLocaleString()); Deck.out('rOo', O.toLocaleString());
    const ttft = P / sp, dec = O * d / 1000, tot = ttft + dec;
    const s = clear(document.getElementById('rSvg')), W = 620;
    svg('rect', { x: 20, y: 20, width: Math.max(2, W * ttft / tot), height: 34, rx: 4, class: 'f-a' }, s);
    svg('rect', { x: 20 + W * ttft / tot, y: 20, width: W * dec / tot, height: 34, rx: 4, style: 'fill:var(--b)' }, s);
    svg('text', { x: 20, y: 76, class: 'tm', style: 'font-size:11px', text: `prefill ${(ttft * 1000).toFixed(0)} ms` }, s);
    svg('text', { x: 640, y: 76, 'text-anchor': 'end', class: 'tm', style: 'font-size:11px', text: `decode ${dec.toFixed(2)} s` }, s);
    document.getElementById('rOut').innerHTML = `TTFT ≈ <b>${(ttft * 1000).toFixed(0)} ms</b> · total ≈ <b>${tot.toFixed(2)} s</b> · decode is ${(100 * dec / tot).toFixed(0)}% of the time`;
  };
  Deck.bind(['rP', 'rO', 'rS', 'rD'], lat);

})();
