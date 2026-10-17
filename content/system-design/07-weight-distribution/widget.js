(() => {
  const { svg, clear } = Deck;
// ---- time calculator for each method
Deck.bind(['wS', 'wN', 'wB', 'wE', 'wF'], () => {
  const S = Deck.val('wS'), N = Deck.val('wN'), B = Deck.val('wB'), E = Deck.val('wE'), f = Deck.val('wF') / 100, c = 0.064;
  Deck.out('wSo', S + ' TB'); Deck.out('wNo', N); Deck.out('wBo', B + ' GB/s'); Deck.out('wEo', E + ' GB/s'); Deck.out('wFo', Math.round(f * 100) + '%');
  const s = S * 1000 * f, depth = Math.ceil(Math.log2(N));
  const rows = [['object store fan-out', Math.max(N * s / E, s / B)], ['pipelined chain', s / B + (N - 1) * c / B], ['binary tree, store-and-forward', depth * s / B],
                ['binary tree, pipelined', s / (B / 2) + depth * c / (B / 2)], ['peer-to-peer swarm', s / B * 1.1]];
  const mx = Math.max(...rows.map(r => r[1]));
  Deck.hbars(document.getElementById('wBars'), rows.map(([l, t]) => ({ label: l, value: t / mx, color: t === Math.min(...rows.map(r => r[1])) ? 'var(--e)' : t === mx ? 'var(--d)' : 'var(--a)', text: t < 120 ? t.toFixed(0) + ' s' : (t / 60).toFixed(1) + ' min' })), { max: 1 });
  document.getElementById('wOut').innerHTML = `Each node needs <b>${(s / 1000).toFixed(2)} TB</b>. Store fan-out moves ${(N * s / 1000).toFixed(0)} TB through a ${E} GB/s store; a chain or swarm needs about one node-link time (${(s / B).toFixed(0)} s). The swarm also survives slow and failed nodes, which the chain does not.`;
});

// ---- animation: 16 nodes filling up under each method
const sv = document.getElementById('dSvg'); let mode = 'store', t0 = performance.now();
const N = 16, S = 1, B = 1, E = 3, c = 0.04;     // illustrative units: one node-link time = 1
function finish(k) {   // [start, rate] for node k
  if (mode === 'store') return [0, Math.min(B, E / N)];
  if (mode === 'chain') return [k * c, B];
  if (mode === 'tree') { const d = Math.floor(Math.log2(k + 1)); return [d * c * 2, B / 2]; }
  return [0.05 + (k % 4) * 0.01, B / 1.1];
}
function draw(t) {
  clear(sv);
  const T = mode === 'store' ? S / (E / N) : mode === 'tree' ? S / (B / 2) + 8 * c : S / B * 1.15 + 0.6;
  const now = t % (T + 1.2);
  for (let k = 0; k < N; k++) {
    const [st, r] = finish(k), p = Math.max(0, Math.min(1, (now - st) * r / S));
    const x = 14 + (k % 8) * 80, y = 30 + Math.floor(k / 8) * 80;
    svg('rect', { x, y, width: 70, height: 60, rx: 8, style: 'fill:var(--panel-2);stroke:var(--line)' }, sv);
    svg('rect', { x, y: y + 60 - 60 * p, width: 70, height: 60 * p, rx: 8, style: `fill:${p >= 1 ? 'var(--e)' : 'var(--a)'};opacity:.85` }, sv);
    svg('text', { x: x + 35, y: y + 35, 'text-anchor': 'middle', class: 't', style: 'font-weight:700', text: Math.round(p * 100) + '%' }, sv);
  }
  const names = { store: 'Everyone reads the object store (shared egress)', chain: 'Pipelined chain: node k forwards to k+1', tree: 'Binary tree: each node feeds two children', swarm: 'Peer-to-peer swarm: chunks from many peers' };
  svg('text', { x: 14, y: 20, class: 't', style: 'font-weight:700', text: names[mode] }, sv);
  svg('text', { x: 14, y: 205, class: 'tm', text: 'time ' + now.toFixed(1) + ' (1 = one copy over one node link)' }, sv);
}
Deck.seg('dSeg', v => { mode = v; t0 = performance.now(); });
Deck.enter('s-deep1', () => Deck.loop(() => draw((performance.now() - t0) / 1000 * 0.6)));
})();
