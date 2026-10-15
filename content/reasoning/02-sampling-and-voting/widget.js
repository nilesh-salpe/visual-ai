(() => {
  const { svg, clear, fmt } = Deck;
  const rnd = (() => { let s = 7; return () => (s = (s * 16807) % 2147483647) / 2147483647; })();
  Deck.bind(['vP', 'vN', 'vW'], () => {
    const p = Deck.val('vP') / 100, n = Deck.val('vN'), w = Deck.val('vW');
    Deck.out('vPo', Math.round(p * 100) + '%'); Deck.out('vNo', n); Deck.out('vWo', w);
    let hit = 0; const T = 600;
    for (let t = 0; t < T; t++) {
      const c = new Array(w + 1).fill(0);
      for (let i = 0; i < n; i++) { if (rnd() < p) c[0]++; else c[1 + Math.floor(rnd() * w)]++; }
      let best = 0; for (let j = 1; j <= w; j++) if (c[j] > c[best]) best = j;
      if (best === 0 && c[0] > 0) hit++;
    }
    const cov = 1 - Math.pow(1 - p, n), maj = hit / T;
    Deck.hbars(document.getElementById('vBars'), [{ label: 'one sample', value: p, color: 'var(--faint)', text: (100 * p).toFixed(0) + '%' },
      { label: 'majority vote', value: maj, color: 'var(--a)', text: (100 * maj).toFixed(0) + '%' },
      { label: 'coverage (any sample right)', value: cov, color: 'var(--e)', text: (100 * cov).toFixed(0) + '%' }], { max: 1 });
    document.getElementById('vOut').innerHTML = `${n} samples, each right with probability ${Math.round(p * 100)}%, wrong answers spread over ${w} value${w > 1 ? 's' : ''}: majority voting is right about <b>${(100 * maj).toFixed(0)}%</b> of the time (simulated), while some sample is right <b>${(100 * cov).toFixed(0)}%</b> of the time. ${w === 1 ? 'With one dominant wrong answer, voting can be worse than a single sample.' : ''}`;
  });
})();
