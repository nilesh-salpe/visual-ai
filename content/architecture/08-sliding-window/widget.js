(() => {
  const { svg, clear, fmt } = Deck;

  Deck.bind(['cT'], () => {
    const T = Math.round(Math.pow(2, Deck.val('cT'))), W = 4096; Deck.out('cTo', T.toLocaleString());
    const full = T * (T + 1) / 2, win = T <= W ? full : W * (W + 1) / 2 + (T - W) * W;
    Deck.hbars(document.getElementById('cBars'), [
      { label: 'scores, full attention', value: full, color: 'var(--d)', text: Deck.fmt(full) },
      { label: 'scores, window 4,096', value: win, color: 'var(--a)', text: Deck.fmt(win) },
      { label: 'KV entries, full', value: T, color: 'var(--d)', text: T.toLocaleString() },
      { label: 'KV entries, rolling buffer', value: Math.min(T, W), color: 'var(--a)', text: Math.min(T, W).toLocaleString() }], { log: true, min: 100 });
  });
  Deck.bind(['wW', 'wL'], () => {
    const W = Deck.val('wW'), L = Deck.val('wL'), N = 40; Deck.out('wWo', W); Deck.out('wLo', L);
    const s = clear(document.getElementById('wSvg')), c = 15, x0 = 30, rowH = 210 / (L + 1);
    for (let l = 0; l <= L; l++) {
      const reach = l === 0 ? 1 : l * (W - 1) + 1, y = 200 - l * rowH;
      for (let p = 0; p < N; p++) {
        const dist = N - 1 - p, on = l === 0 ? dist === 0 : dist < reach;
        svg('rect', { x: x0 + p * c, y: y - c + 2, width: c - 3, height: c - 3, rx: 3, style: `fill:${on ? (l === L ? 'var(--a)' : 'var(--a-soft)') : 'var(--panel-2)'}` }, s);
      }
      svg('text', { x: x0 - 6, y: y - 3, 'text-anchor': 'end', class: 'tm', style: 'font-size:10px', text: l === 0 ? 'out' : 'L' + l }, s);
    }
    const span = L * (W - 1) + 1;
    document.getElementById('wOut').innerHTML = `${L} layer${L > 1 ? 's' : ''} × window ${W}: the last token can be influenced by <b>${span}</b> positions (L·(W−1)+1). Mistral 7B: 32·4,095+1 = <b>131,041</b> ≈ 131K.`;
  });
  let t = 0; const W = 4, slots = Array(W).fill(null);
  const rb = () => {
    const s = clear(document.getElementById('rbSvg'));
    for (let k = 0; k < W; k++) {
      const x = 130 + k * 105, hot = t > 0 && (t - 1) % W === k;
      svg('rect', { x, y: 40, width: 90, height: 60, rx: 9, style: `fill:${hot ? 'var(--b)' : slots[k] === null ? 'var(--panel-2)' : 'var(--a)'}` }, s);
      svg('text', { x: x + 45, y: 76, 'text-anchor': 'middle', class: 't', style: slots[k] === null ? '' : 'fill:#fff;font-weight:700', text: slots[k] === null ? 'empty' : 'k,v of t=' + slots[k] }, s);
      svg('text', { x: x + 45, y: 120, 'text-anchor': 'middle', class: 'tm', text: 'slot ' + k }, s);
    }
    document.getElementById('rbOut').innerHTML = t === 0 ? 'Empty cache. Press "next token".' : `Token t = ${t - 1} written to slot ${(t - 1) % W} = ${t - 1} mod ${W}. The cache holds tokens ${Math.max(0, t - W)}…${t - 1}, exactly the window. A full cache would now hold ${t} entries; this one never exceeds ${W}.`;
  };
  document.getElementById('rbNext').addEventListener('click', () => { slots[t % W] = t; t++; rb(); });
  document.getElementById('rbReset').addEventListener('click', () => { t = 0; slots.fill(null); rb(); });
  rb();
  Deck.seg('aSeg', v => {
    const h = +v, m = Math.pow(2, -h), N = 12, s = clear(document.getElementById('aSvg')), c = 18, x0 = 200, y0 = 14, maxPen = 11 * 0.5;
    for (let i = 0; i < N; i++) for (let j = 0; j < N; j++) {
      if (j > i) { svg('rect', { x: x0 + j * c, y: y0 + i * c, width: c - 2, height: c - 2, rx: 2, style: 'fill:var(--panel-2)' }, s); continue; }
      const pen = m * (i - j);
      svg('rect', { x: x0 + j * c, y: y0 + i * c, width: c - 2, height: c - 2, rx: 2, style: `fill:var(--d);opacity:${(0.06 + 0.94 * pen / maxPen).toFixed(3)}` }, s);
    }
    svg('text', { x: x0 + N * c / 2, y: y0 + N * c + 20, 'text-anchor': 'middle', class: 'tm', text: 'key position j →' }, s);
    svg('text', { x: x0 - 10, y: y0 + N * c / 2, 'text-anchor': 'end', class: 'tm', text: 'query i ↓' }, s);
    svg('text', { x: 460, y: 60, class: 't', text: `slope m = 1/${Math.pow(2, h)}` }, s);
    svg('text', { x: 460, y: 86, class: 'tm', text: `bias at distance 1: −${m.toPrecision(2)}` }, s);
    svg('text', { x: 460, y: 108, class: 'tm', text: `bias at distance 11: −${(11 * m).toPrecision(2)}` }, s);
    svg('text', { x: 460, y: 130, class: 'tm', text: `bias at distance 1,000: −${(1000 * m).toPrecision(3)}` }, s);
  });

})();
