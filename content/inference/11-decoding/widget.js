(() => {
  const { svg, clear, fmt } = Deck;
  const W = ['mat', 'floor', 'sofa', 'bed', 'chair', 'roof', 'table', 'keyboard', 'moon', 'banana'];
  const P = [0.42, 0.18, 0.12, 0.09, 0.06, 0.04, 0.03, 0.03, 0.02, 0.01];
  Deck.bind(['dT', 'dK', 'dP', 'dM'], () => {
    const T = Deck.val('dT'), k = Deck.val('dK'), tp = Deck.val('dP'), mp = Deck.val('dM');
    Deck.out('dTo', T.toFixed(2)); Deck.out('dKo', k ? k : 'off'); Deck.out('dPo', tp >= 1 ? 'off' : tp.toFixed(2)); Deck.out('dMo', mp ? mp.toFixed(2) : 'off');
    let q;
    if (T < 1e-5) { q = P.map((_, i) => (i === 0 ? 1 : 0)); }
    else { const z = P.map(p => Math.pow(p, 1 / T)); const s = z.reduce((a, b) => a + b, 0); q = z.map(v => v / s); }
    const mx = Math.max(...q);
    let keep = q.map(v => v > 0 && (!mp || v >= mp * mx));
    const order = q.map((v, i) => i).sort((a, b) => q[b] - q[a]);
    if (k) order.forEach((i, r) => { if (r >= k) keep[i] = false; });
    if (tp < 1) { let c = 0, done = false; order.forEach(i => { if (!keep[i]) return; if (done) keep[i] = false; else { c += q[i]; if (c >= tp - 1e-9) done = true; } }); }
    const s = q.reduce((a, v, i) => a + (keep[i] ? v : 0), 0);
    const f = q.map((v, i) => (keep[i] ? v / s : 0));
    Deck.hbars(document.getElementById('dBars'), W.map((w, i) => ({ label: '"' + w + '"', value: f[i], color: keep[i] ? 'var(--a)' : 'var(--faint)', text: keep[i] ? (100 * f[i]).toFixed(1) + '%' : 'cut' })), { max: 1 });
    const n = keep.filter(Boolean).length;
    document.getElementById('dOut').innerHTML = `After "The cat sat on the …": <b>${n}</b> of 10 tokens can be sampled; "mat" has probability <b>${(100 * f[0]).toFixed(0)}%</b>. ` +
      (T < 1e-5 ? 'Temperature 0 is greedy: the argmax always wins.' : n <= 2 ? 'Nearly deterministic: little diversity.' : f[9] > 0 ? 'The unreliable tail ("moon", "banana") is still in play.' : 'The tail is cut; the remaining tokens are plausible.');
  });
})();
