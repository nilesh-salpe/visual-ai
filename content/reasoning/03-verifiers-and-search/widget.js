(() => {
  const { svg, clear, fmt } = Deck;
  const rnd = (() => { let s = 11; return () => (s = (s * 16807) % 2147483647) / 2147483647; })();
  const gauss = () => Math.sqrt(-2 * Math.log(rnd() + 1e-12)) * Math.cos(2 * Math.PI * rnd());
  Deck.bind(['bP', 'bN', 'bS'], () => {
    const p = Deck.val('bP') / 100, n = Deck.val('bN'), s = Deck.val('bS');
    Deck.out('bPo', Math.round(p * 100) + '%'); Deck.out('bNo', n); Deck.out('bSo', s.toFixed(1));
    let hit = 0; const T = 1500;
    for (let t = 0; t < T; t++) { let best = -1e9, ok = false; for (let i = 0; i < n; i++) { const c = rnd() < p; const sc = (c ? 1 : 0) + s * gauss(); if (sc > best) { best = sc; ok = c; } } if (ok) hit++; }
    const cov = 1 - Math.pow(1 - p, n), bon = hit / T;
    Deck.hbars(document.getElementById('bBars'), [{ label: 'one sample', value: p, color: 'var(--faint)', text: (100 * p).toFixed(0) + '%' },
      { label: 'best-of-N with this verifier', value: bon, color: 'var(--a)', text: (100 * bon).toFixed(0) + '%' },
      { label: 'coverage (perfect verifier)', value: cov, color: 'var(--e)', text: (100 * cov).toFixed(0) + '%' }], { max: 1 });
    document.getElementById('bOut').innerHTML = `Verifier score = correct (0 or 1) + noise with standard deviation ${s.toFixed(1)}. Best-of-${n} keeps <b>${(100 * bon).toFixed(0)}%</b> of questions right out of the <b>${(100 * cov).toFixed(0)}%</b> that some sample solves.`;
  });
})();
