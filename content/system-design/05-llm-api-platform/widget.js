(() => {
  const { svg, clear } = Deck;
// ---- estimates calculator
Deck.bind(['eR', 'eO', 'eS', 'eT', 'eP'], () => {
  const R = Deck.val('eR'), O = Deck.val('eO'), sm = Deck.val('eS') / 100, T = Deck.val('eT') * 1000, P = Deck.val('eP');
  Deck.out('eRo', R.toLocaleString()); Deck.out('eOo', O); Deck.out('eSo', Math.round(sm * 100) + '%'); Deck.out('eTo', (T / 1000) + 'K'); Deck.out('ePo', '$' + P.toFixed(2));
  const out = R * O, large = out * (1 - sm), reps = Math.ceil(large / T), gpus = reps * 8, perM = P * 8 / (T * 3600 / 1e6);
  const conc = R * O / 40;
  Deck.hbars(document.getElementById('eBars'), [
    { label: 'output tokens/s at peak', value: 1, color: 'var(--a)', text: (out / 1e6).toFixed(2) + 'M' },
    { label: 'concurrent streams (Little\'s law at 40 tok/s)', value: 1, color: 'var(--c)', text: Math.round(conc).toLocaleString() },
    { label: 'large-model GPUs (8 per replica)', value: 1, color: 'var(--d)', text: gpus.toLocaleString() },
    { label: 'cost per million output tokens (large, full use)', value: 1, color: 'var(--e)', text: '$' + perM.toFixed(2) }], { max: 1 });
  document.getElementById('eOut').innerHTML = `${R.toLocaleString()} requests/s × ${O} output tokens = <b>${(out / 1e6).toFixed(2)}M tokens/s</b>. With ${Math.round(sm * 100)}% routed to the small model, the large model needs <b>${reps} replicas (${gpus.toLocaleString()} GPUs)</b> at ${(T / 1000)}K tokens/s each. Cost per million output tokens rises as utilisation falls: fill troughs with batch work.`;
});

// ---- fair scheduling animation: FCFS vs token-fair (VTC-style)
const s = document.getElementById('fSvg'); let mode = 'fcfs', t0 = performance.now();
const ARR = [];   // tenant A: heavy burst of long requests; B and C: light, short
for (let k = 0; k < 14; k++) ARR.push({ t: k * 0.25, who: 0, cost: 3 });
for (let k = 0; k < 6; k++) ARR.push({ t: 0.6 + k * 0.7, who: 1, cost: 1 });
for (let k = 0; k < 5; k++) ARR.push({ t: 1.1 + k * 0.9, who: 2, cost: 1 });
ARR.sort((a, b) => a.t - b.t);
const COL = ['var(--d)', 'var(--a)', 'var(--e)'], NAME = ['tenant A (bulk)', 'tenant B', 'tenant C'];
function simulate() {   // one server, 2 cost units per second
  const done = [], cnt = [0, 0, 0]; let clock = 0; const q = []; let i = 0;
  while (done.length < ARR.length) {
    while (i < ARR.length && ARR[i].t <= clock) q.push({ ...ARR[i++] });
    if (!q.length) { clock = ARR[i].t; continue; }
    let k = 0;
    if (mode === 'fair') { const back = new Set(q.map(r => r.who)); let best = Infinity; q.forEach((r, j) => { if (cnt[r.who] < best) { best = cnt[r.who]; k = j; } }); back.forEach(w => { if (cnt[w] < Math.min(...[...back].map(x => cnt[x]))) cnt[w] = Math.min(...[...back].map(x => cnt[x])); }); }
    const r = q.splice(k, 1)[0]; const start = clock; clock += r.cost / 2; cnt[r.who] += r.cost;
    done.push({ ...r, start, end: clock });
  }
  return done;
}
function draw(now) {
  const d = simulate(), T = Math.max(...d.map(x => x.end)), sx = x => 150 + x / T * 495; now = now % (T + 2);
  clear(s);
  svg('text', { x: 10, y: 20, class: 't', style: 'font-weight:700', text: mode === 'fcfs' ? 'First come, first served' : 'Fair share of tokens (VTC-style)' }, s);
  [0, 1, 2].forEach(w => {
    const y = 45 + w * 55; svg('text', { x: 10, y: y + 22, class: 't', text: NAME[w] }, s);
    d.filter(x => x.who === w).forEach(x => {
      if (x.start > now) return;
      const e = Math.min(x.end, now);
      svg('rect', { x: sx(x.t), y: y + 8, width: Math.max(1, sx(x.start) - sx(x.t)), height: 22, rx: 3, style: 'fill:var(--panel-2)' }, s);
      svg('rect', { x: sx(x.start), y: y + 8, width: Math.max(1, sx(e) - sx(x.start)), height: 22, rx: 3, style: `fill:${COL[w]};opacity:.85` }, s);
    });
  });
  svg('line', { x1: sx(Math.min(now, T)), x2: sx(Math.min(now, T)), y1: 40, y2: 210, style: 'stroke:var(--ink);stroke-width:1.5' }, s);
  svg('text', { x: 150, y: 232, class: 'tm', text: 'grey = waiting in the queue · colour = being served' }, s);
  const avg = w => { const xs = d.filter(x => x.who === w); return xs.reduce((a, x) => a + x.end - x.t, 0) / xs.length; };
  document.getElementById('fOut').innerHTML = `Average latency: tenant A <b>${avg(0).toFixed(1)}</b>, tenant B <b>${avg(1).toFixed(1)}</b>, tenant C <b>${avg(2).toFixed(1)}</b> time units. ` +
    (mode === 'fcfs' ? 'B and C queue behind A\'s burst of long requests.' : 'Light tenants are served first because they have used fewer tokens; A still gets all the spare capacity (work-conserving).');
}
Deck.seg('fSeg', v => { mode = v; t0 = performance.now(); draw(0); });
Deck.enter('s-deep1', () => Deck.loop(() => draw((performance.now() - t0) / 1000 * 1.2)));
})();
