(() => {
  const { svg, clear, fmt } = Deck;

  Deck.hbars(document.getElementById('p1Bars'), [['FP32', 4], ['BF16 / FP16', 2], ['FP8 / INT8', 1], ['INT4', .5]].map(([n, b], i) => ({ label: n, value: 70 * b, color: ['var(--faint)', 'var(--a)', 'var(--e)', 'var(--c)'][i], text: (70 * b) + ' GB' })));
  let bits = 4, gran = 'tensor', outl = 0;
  const base = (() => { let s = 11; const r = () => { s = (s * 16807) % 2147483647; return s / 2147483647; }; return [...Array(16)].map(() => { const u = r(), v = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }); })();
  const qz = () => {
    const xs = base.map((v, i) => outl && i === 5 ? 9 : v), qmax = 2 ** (bits - 1) - 1;
    const scaleOf = arr => Math.max(...arr.map(Math.abs)) / qmax;
    const scales = xs.map((_, i) => gran === 'tensor' ? scaleOf(xs) : scaleOf(xs.slice(Math.floor(i / 8) * 8, Math.floor(i / 8) * 8 + 8)));
    const deq = xs.map((v, i) => Math.max(-qmax, Math.min(qmax, Math.round(v / scales[i]))) * scales[i]);
    const s = clear(document.getElementById('qSvg')), L = 30, R = 640, lim = Math.max(...xs.map(Math.abs)) * 1.05, X = v => (L + R) / 2 + v / lim * (R - L) / 2;
    svg('line', { x1: L, x2: R, y1: 100, y2: 100, class: 's-line', 'stroke-width': 2 }, s);
    const sc0 = scales[0];
    for (let k = -qmax; k <= qmax; k++) svg('line', { x1: X(k * sc0), x2: X(k * sc0), y1: 92, y2: 108, style: 'stroke:var(--faint)' }, s);
    xs.forEach((v, i) => { svg('line', { x1: X(v), y1: 60, x2: X(deq[i]), y2: 140, style: 'stroke:var(--d);opacity:.5' }, s); svg('circle', { cx: X(v), cy: 60, r: 5, class: 'f-a' }, s); svg('circle', { cx: X(deq[i]), cy: 140, r: 5, style: 'fill:var(--b)' }, s); });
    svg('text', { x: L, y: 40, class: 'tm', style: 'font-size:11px', text: 'original values' }, s);
    svg('text', { x: L, y: 170, class: 'tm', style: 'font-size:11px', text: `dequantized (${gran === 'tensor' ? 'grid ticks = the single per-tensor step' : 'ticks shown for group 1'})` }, s);
    const err = Math.sqrt(xs.reduce((a, v, i) => a + (v - deq[i]) ** 2, 0) / xs.reduce((a, v) => a + v * v, 0));
    const small = xs.map((v, i) => [v, deq[i]]).filter((_, i) => i !== 5 || !outl);
    const zeroed = small.filter(([v, d]) => d === 0 && v !== 0).length;
    document.getElementById('qRes').innerHTML = `INT${bits}, ${gran === 'tensor' ? 'one scale' : 'one scale per 8 values'}: relative error <b>${(100 * err).toFixed(1)}%</b> · ${zeroed} of ${small.length} non-outlier values rounded to 0`;
  };
  Deck.seg('qBits', v => { bits = +v; qz(); }); Deck.seg('qGran', v => { gran = v; qz(); }); Deck.seg('qOut', v => { outl = +v; qz(); });
  // SmoothQuant live
  const R = (() => { let s = 5; return () => { s = (s * 16807) % 2147483647; return s / 2147483647; }; })();
  const N = () => Math.sqrt(-2 * Math.log(R() + 1e-12)) * Math.cos(2 * Math.PI * R());
  const X = [...Array(64)].map(() => [...Array(128)].map((_, j) => N() * (j === 5 || j === 77 ? 40 : 1)));
  const Wm = [...Array(128)].map(() => [...Array(96)].map(() => N() * 0.05));
  const mm = (A, B) => A.map(r => B[0].map((_, j) => r.reduce((acc, v, k) => acc + v * B[k][j], 0)));
  const ref = mm(X, Wm);
  const w8a8 = (A, B) => {
    const sa = Math.max(...A.flat().map(Math.abs)) / 127, qa = A.map(r => r.map(v => Math.max(-127, Math.min(127, Math.round(v / sa)))));
    const sw = B[0].map((_, j) => Math.max(...B.map(r => Math.abs(r[j]))) / 127), qw = B.map(r => r.map((v, j) => Math.max(-127, Math.min(127, Math.round(v / sw[j])))));
    return mm(qa, qw).map(r => r.map((v, j) => v * sa * sw[j]));
  };
  const rel = Y => Math.sqrt(Y.flat().reduce((a, v, i) => a + (v - ref.flat()[i]) ** 2, 0) / ref.flat().reduce((a, v) => a + v * v, 0));
  const before = rel(w8a8(X, Wm));
  Deck.bind(['smA'], () => {
    const a = Deck.val('smA'); Deck.out('smAo', a.toFixed(2));
    const xmax = X[0].map((_, j) => Math.max(...X.map(r => Math.abs(r[j])))), wmax = Wm.map(r => Math.max(...r.map(Math.abs)));
    const s = xmax.map((m, j) => Math.pow(m, a) / Math.pow(Math.max(wmax[j], 1e-12), 1 - a));
    const Xs = X.map(r => r.map((v, j) => v / s[j])), Ws = Wm.map((r, j) => r.map(v => v * s[j]));
    const after = rel(w8a8(Xs, Ws));
    const sv = clear(document.getElementById('smX')), xm2 = Xs[0].map((_, j) => Math.max(...Xs.map(r => Math.abs(r[j])))), top = Math.max(...xmax);
    for (let j = 0; j < 32; j++) { const jj = j < 16 ? j : 64 + j; svg('rect', { x: 4 + j * 9.8, y: 110 - 100 * xmax[jj === 80 ? 77 : jj] / top, width: 4, height: 100 * xmax[jj === 80 ? 77 : jj] / top, style: 'fill:var(--d);opacity:.5' }, sv); svg('rect', { x: 8.5 + j * 9.8, y: 110 - 100 * xm2[jj === 80 ? 77 : jj] / top, width: 4, height: Math.max(1, 100 * xm2[jj === 80 ? 77 : jj] / top), style: 'fill:var(--e)' }, sv); }
    Deck.hbars(document.getElementById('smBars'), [{ label: 'raw W8A8', value: before, color: 'var(--d)', text: (100 * before).toFixed(2) + '%' }, { label: `smoothed (α=${a.toFixed(2)})`, value: after, color: 'var(--e)', text: (100 * after).toFixed(2) + '%' }], { max: Math.max(before, after) * 1.1 });
  });

})();
