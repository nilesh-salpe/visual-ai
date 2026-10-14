(() => {
  const { svg, clear, fmt } = Deck;

  Deck.bind(['eN', 'eP'], () => {
    const n = Math.round(Math.pow(10, Deck.val('eN'))), p = Deck.val('eP'); Deck.out('eNo', n.toLocaleString()); Deck.out('ePo', (100 * p).toFixed(0) + '%');
    const h = 1.96 * Math.sqrt(p * (1 - p) / n), s = clear(document.getElementById('eSvg')), X = v => 30 + v * 600;
    svg('line', { x1: 30, x2: 630, y1: 60, y2: 60, class: 'ln' }, s);
    [0, 0.25, 0.5, 0.75, 1].forEach(v => svg('text', { x: X(v), y: 100, 'text-anchor': 'middle', class: 'tm', text: (100 * v) + '%' }, s));
    svg('rect', { x: X(Math.max(0, p - h)), y: 46, width: X(Math.min(1, p + h)) - X(Math.max(0, p - h)), height: 28, rx: 5, style: 'fill:var(--a-soft);stroke:var(--a)' }, s);
    svg('circle', { cx: X(p), cy: 60, r: 6, style: 'fill:var(--a)' }, s);
    document.getElementById('eOut').innerHTML = `95% CI: <b>${(100 * p).toFixed(0)}% ± ${(100 * h).toFixed(1)} points</b>. To halve the width you need 4× the questions.`;
  });
  const sig = z => 1 / (1 + Math.exp(-z));
  const simulate = (gap, nq) => {
    let seed = 12345; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647; const g = () => Math.sqrt(-2 * Math.log(Math.max(1e-9, rnd()))) * Math.cos(2 * Math.PI * rnd());
    let hp = 0, hu = 0, gs = 0; const R = 120;
    for (let r = 0; r < R; r++) {
      let sa = 0, sb = 0, sd = 0, sd2 = 0, sa2 = 0, sb2 = 0;
      for (let i = 0; i < nq; i++) {
        const lg = Math.log(0.7 / 0.3) - (1.5 * g() + g()), u = rnd(), ub = rnd() < 0.75 ? u : rnd();
        const a = u < sig(lg) ? 1 : 0, b = ub < sig(lg + gap) ? 1 : 0;
        sa += a; sb += b; sd += b - a; sd2 += (b - a) ** 2;
      }
      const ma = sa / nq, mb = sb / nq, md = sd / nq, vd = (sd2 - nq * md * md) / (nq - 1);
      const vu = (ma * (1 - ma) + mb * (1 - mb)) / (nq - 1);
      if (Math.abs(md) / Math.sqrt(vd / nq) > 1.96) hp++;
      if (Math.abs(md) / Math.sqrt(vu) > 1.96) hu++;
      gs += md;
    }
    return [gs / R, hp / R, hu / R];
  };
  Deck.bind(['sG', 'sN'], () => {
    const gap = Deck.val('sG'), nq = Deck.val('sN'); Deck.out('sGo', gap.toFixed(2)); Deck.out('sNo', nq.toLocaleString());
    const [d, p, u] = simulate(gap, nq);
    Deck.out('sD', (100 * d).toFixed(1)); Deck.out('sP', (100 * p).toFixed(0) + '%'); Deck.out('sU', (100 * u).toFixed(0) + '%');
  });
  Deck.hbars(document.getElementById('cBars'), [['DROP naive', 0.44], ['DROP clustered', 1.34], ['RACE-H naive', 0.46], ['RACE-H clustered', 0.51], ['MGSM naive', 0.86], ['MGSM clustered', 1.62]].map(([l, v]) => ({ label: l, value: v, color: l.includes('clustered') ? 'var(--d)' : 'var(--faint)', text: v.toFixed(2) })), { max: 1.5 });

})();
