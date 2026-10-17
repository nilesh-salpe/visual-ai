(() => {
  const { svg, clear } = Deck;
// ---- discrete-event simulation of full-or-timeout batching
function sim(lam, W, B, D, t0, c, seed) {
  let r = seed; const rnd = () => (r = (r * 16807) % 2147483647) / 2147483647;
  const T = 3000, arr = []; let t = 0; while (t < T) { t += -Math.log(1 - rnd()) / lam * 1000; arr.push(t); }
  const free = new Array(W).fill(0), lat = [], sizes = []; let i = 0, busy = 0;
  while (i < arr.length) {
    const g = free.indexOf(Math.min(...free));
    const fullAt = i + B - 1 < arr.length ? arr[i + B - 1] : Infinity;      // when the batch would be full
    const close = Math.max(free[g], arr[i], Math.min(fullAt, arr[i] + D));  // full or timeout, never before a worker is free
    let n = 0; while (i + n < arr.length && n < B && arr[i + n] <= close) n++;
    const dur = t0 + c * n, end = close + dur;
    for (let k = 0; k < n; k++) lat.push(end - arr[i + k]);
    sizes.push(n); busy += dur; free[g] = end; i += n;
  }
  lat.sort((a, b) => a - b);
  return { p50: lat[Math.floor(lat.length * 0.5)], p99: lat[Math.floor(lat.length * 0.99)], avgB: sizes.reduce((a, b) => a + b, 0) / sizes.length, util: busy / (W * Math.max(...free)) };
}
Deck.bind(['bL', 'bW', 'bD', 'bB'], () => {
  const lam = Deck.val('bL'), W = Deck.val('bW'), D = Deck.val('bD'), B = Deck.val('bB'), t0 = 20, c = 0.3;
  Deck.out('bLo', lam.toLocaleString() + '/s'); Deck.out('bWo', W); Deck.out('bDo', D + ' ms'); Deck.out('bBo', B);
  const cap = W * B / (t0 + c * B) * 1000;
  if (lam >= cap * 0.98) {
    Deck.hbars(document.getElementById('bBars'), [{ label: 'capacity at full batches', value: cap / lam, color: 'var(--d)', text: Math.round(cap).toLocaleString() + '/s' }], { max: 1 });
    document.getElementById('bOut').innerHTML = `Overloaded: ${W} GPUs can do at most <b>${Math.round(cap).toLocaleString()} inputs/s</b> with batches of ${B}. The queue grows without bound: add GPUs, or reject early.`;
    return;
  }
  const m = sim(lam, W, B, D, t0, c, 7);
  Deck.hbars(document.getElementById('bBars'), [
    { label: 'average batch size', value: m.avgB / B, color: 'var(--c)', text: m.avgB.toFixed(1) },
    { label: 'GPU busy share', value: m.util, color: 'var(--b)', text: Math.round(100 * m.util) + '%' },
    { label: 'p50 latency', value: Math.min(1, m.p50 / 200), color: 'var(--a)', text: m.p50.toFixed(0) + ' ms' },
    { label: 'p99 latency (target 200 ms)', value: Math.min(1, m.p99 / 200), color: m.p99 > 200 ? 'var(--d)' : 'var(--e)', text: m.p99.toFixed(0) + ' ms' }], { max: 1 });
  document.getElementById('bOut').innerHTML = `Batch time t(b) = 20 ms + 0.3 ms × b (assumption). ${W} GPUs at ${lam.toLocaleString()} requests/s with a ${D} ms maximum delay form batches of about <b>${m.avgB.toFixed(0)}</b>; p99 latency <b>${m.p99.toFixed(0)} ms</b>. Longer delays raise batch size and efficiency, and latency with them.`;
});

// ---- animation: requests fill a batch; dispatch on full or timeout
const s = document.getElementById('qSvg'); let t0a = performance.now(), rate = 'low';
function frame(now) {
  clear(s);
  const per = rate === 'low' ? 0.55 : 0.08, B = 8, D = 2.2;            // seconds between arrivals; batch size 8 shown for clarity; max delay 2.2 s
  let t = 0, q = [], batches = [], arrivals = [];
  while (t < now) { arrivals.push(t); t += per; }
  let open = [];
  arrivals.forEach(a => { open.push(a); if (open.length === B) { batches.push({ at: a, n: B, why: 'full' }); open = []; } else if (a - open[0] >= D) { batches.push({ at: open[0] + D, n: open.length, why: 'timeout' }); open = []; } });
  if (open.length && now - open[0] >= D) { batches.push({ at: open[0] + D, n: open.length, why: 'timeout' }); open = []; }
  svg('text', { x: 10, y: 22, class: 't', style: 'font-weight:700', text: 'queue (max batch 8 shown, max delay 2.2 s)' }, s);
  svg('rect', { x: 10, y: 34, width: 330, height: 46, rx: 8, style: 'fill:var(--panel-2)' }, s);
  open.forEach((a, k) => svg('circle', { cx: 32 + k * 40, cy: 57, r: 13, style: 'fill:var(--a)' }, s));
  if (open.length) { const w = Math.min(1, (now - open[0]) / D); svg('rect', { x: 10, y: 88, width: 330 * w, height: 8, rx: 4, style: 'fill:var(--b)' }, s); svg('text', { x: 10, y: 114, class: 'tm', text: 'oldest request waiting: ' + (now - open[0]).toFixed(1) + ' s' }, s); }
  svg('text', { x: 400, y: 22, class: 't', style: 'font-weight:700', text: 'GPU batches sent' }, s);
  batches.slice(-5).forEach((b, k) => {
    const y = 34 + k * 34;
    svg('rect', { x: 400, y, width: 25 * b.n, height: 26, rx: 5, style: `fill:${b.why === 'full' ? 'var(--e)' : 'var(--c)'}` }, s);
    svg('text', { x: 410 + 25 * b.n, y: y + 18, class: 't', text: `${b.n} · ${b.why}` }, s);
  });
  svg('text', { x: 10, y: 150, class: 'tm', text: rate === 'low' ? 'Low traffic: batches leave on the timer, small and fast.' : 'High traffic: batches fill before the timer, large and efficient.' }, s);
}
Deck.seg('qSeg', v => { rate = v; t0a = performance.now(); });
Deck.enter('s-deep1', () => Deck.loop(() => frame(((performance.now() - t0a) / 1000) % 14)));
})();
