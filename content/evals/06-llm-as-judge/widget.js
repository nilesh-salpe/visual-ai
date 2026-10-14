(() => {
  const { svg, clear, fmt } = Deck;

  const sig = z => 1 / (1 + Math.exp(-z));
  Deck.bind(['jB', 'jN'], () => {
    const b = Deck.val('jB'), nz = Deck.val('jN'); Deck.out('jBo', b.toFixed(1)); Deck.out('jNo', nz.toFixed(1));
    let seed = 99; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647; const g = () => Math.sqrt(-2 * Math.log(Math.max(1e-9, rnd()))) * Math.cos(2 * Math.PI * rnd());
    let cons = 0, first = 0, second = 0; const N = 500;
    for (let i = 0; i < N; i++) {
      const d = g();                                       // true quality difference (a minus b)
      const x = rnd() < sig((d + b) / nz) ? 'A' : 'B';      // order (a, b)
      const y = rnd() < sig((-d + b) / nz) ? 'A' : 'B';     // order (b, a)
      if ((x === 'A') === (y === 'B')) cons++; else if (x === 'A') first++; else second++;
    }
    Deck.hbars(document.getElementById('jBars'), [{ label: 'consistent', value: cons / N, color: 'var(--a)', text: (100 * cons / N).toFixed(0) + '%' }, { label: 'picked first both times', value: first / N, color: 'var(--d)', text: (100 * first / N).toFixed(0) + '%' }, { label: 'picked second both times', value: second / N, color: 'var(--b)', text: (100 * second / N).toFixed(0) + '%' }], { max: 1 });
  });
  Deck.hbars(document.getElementById('vBars'), [['Claude-v1', 0.913], ['GPT-3.5', 0.913], ['GPT-4', 0.087]].map(([l, v]) => ({ label: l, value: v, color: v > 0.5 ? 'var(--d)' : 'var(--a)', text: (100 * v).toFixed(1) + '% fooled' })), { max: 1 });

})();
