(() => {
  const { svg, clear, fmt } = Deck;
  Deck.seg('oSeg', v => {
    const ov = v === '1', s = clear(document.getElementById('oSvg')), X = t => 60 + t * 55;
    svg('text', { x: 10, y: 50, class: 'tm', text: 'compute' }, s); svg('text', { x: 10, y: 120, class: 'tm', text: 'network' }, s);
    svg('rect', { x: X(0), y: 35, width: 55 * 3, height: 26, rx: 4, style: 'fill:var(--a)' }, s); svg('text', { x: X(1.5), y: 53, 'text-anchor': 'middle', class: 't', style: 'fill:#fff', text: 'forward' }, s);
    for (let b = 0; b < 4; b++) svg('rect', { x: X(3 + b * 1.5), y: 35, width: 55 * 1.5 - 3, height: 26, rx: 4, style: 'fill:var(--b)' }, s);
    svg('text', { x: X(6), y: 53, 'text-anchor': 'middle', class: 't', style: 'fill:#fff', text: 'backward (4 buckets)' }, s);
    let end;
    if (ov) { for (let b = 0; b < 4; b++) svg('rect', { x: X(4.5 + b * 1.5), y: 105, width: 55 * 1.5 - 3, height: 26, rx: 4, style: 'fill:var(--c)' }, s); end = 10.5; }
    else { svg('rect', { x: X(9), y: 105, width: 55 * 6 - 3, height: 26, rx: 4, style: 'fill:var(--c)' }, s); end = 15; }
    svg('text', { x: ov ? X(7.5) : X(12), y: 123, 'text-anchor': 'middle', class: 't', style: 'fill:#fff', text: 'all-reduce' }, s);
    svg('line', { x1: X(Math.min(end, 10.8)), x2: X(Math.min(end, 10.8)), y1: 20, y2: 150, style: 'stroke:var(--d);stroke-dasharray:4 3' }, s);
    svg('text', { x: X(Math.min(end, 10.8)), y: 170, 'text-anchor': 'middle', class: 'tm', text: 'step ends' }, s);
    document.getElementById('oOut').innerHTML = ov ? 'Each bucket\'s all-reduce starts as soon as its gradients exist; only the last bucket\'s communication is exposed.' : 'Communication waits for the whole backward pass, then the GPUs sit idle while the network works: the step takes far longer.';
  });
  const N = 4; let st = 0; const val = [...Array(N)].map((_, r) => [...Array(N)].map((_, c) => [r === 0 ? 1 : 0, r === 1 ? 1 : 0, r === 2 ? 1 : 0, r === 3 ? 1 : 0]));
  let chunks;
  const reset = () => { chunks = [...Array(N)].map((_, r) => [...Array(N)].map(() => ({ sum: [r], full: false }))); st = 0; draw(); };
  const draw = () => {
    const s = clear(document.getElementById('rSvg'));
    for (let r = 0; r < N; r++) {
      svg('text', { x: 20, y: 40 + r * 48, class: 't', style: 'font-weight:600', text: 'GPU ' + r }, s);
      for (let c = 0; c < N; c++) {
        const ch = chunks[r][c], x = 100 + c * 130, y = 22 + r * 48, n = ch.sum.length;
        svg('rect', { x, y, width: 120, height: 32, rx: 6, style: `fill:${n === N ? 'var(--e)' : `color-mix(in srgb, var(--a) ${25 + 75 * n / N}%, var(--panel-2))`}` }, s);
        svg('text', { x: x + 60, y: y + 21, 'text-anchor': 'middle', class: 't', style: n > 1 ? 'fill:#fff' : '', text: `chunk ${c}: ${n === N ? 'Σ all' : 'g' + ch.sum.join('+g')}` }, s);
      }
    }
    const phase = st < N - 1 ? `reduce-scatter step ${st + 1} of ${N - 1}` : st < 2 * (N - 1) ? `all-gather step ${st - N + 2} of ${N - 1}` : 'done';
    document.getElementById('rOut').innerHTML = st === 0 ? 'Each GPU starts with only its own gradient g<sub>r</sub> in every chunk.' : st <= N - 1 ? `After ${st} reduce-scatter step(s): GPU r has summed ${st + 1} contributions into chunk (r − ${st} + 1) mod 4.` + (st === N - 1 ? ' Each GPU now owns one fully summed chunk (green).' : '') : st < 2 * (N - 1) ? `All-gather: finished chunks are copied around the ring.` : 'Every GPU has the full summed gradient. Each sent 2 × 3/4 of the gradient.';
  };
  document.getElementById('rNext').addEventListener('click', () => {
    if (st >= 2 * (N - 1)) return;
    if (st < N - 1) { const s0 = st; const msgs = [...Array(N)].map((_, r) => [(r + 1) % N, (r - s0 + N) % N, chunks[r][(r - s0 + N) % N].sum.slice()]); msgs.forEach(([d, k, sm]) => { chunks[d][k].sum = [...new Set(chunks[d][k].sum.concat(sm))].sort(); }); }
    else { const s0 = st - (N - 1); const msgs = [...Array(N)].map((_, r) => [(r + 1) % N, (r + 1 - s0 + N) % N, chunks[r][(r + 1 - s0 + N) % N].sum.slice()]); msgs.forEach(([d, k, sm]) => { chunks[d][k].sum = sm; }); }
    st++; draw();
  });
  document.getElementById('rReset').addEventListener('click', reset);
  reset();
})();
