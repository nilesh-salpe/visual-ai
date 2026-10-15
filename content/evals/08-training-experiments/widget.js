(() => {
  const { svg, clear, fmt } = Deck;
  Deck.bind(['eS', 'eN', 'eD'], () => {
    const s = Deck.val('eS'), n = Deck.val('eN'), d = Deck.val('eD');
    Deck.out('eSo', s.toFixed(2)); Deck.out('eNo', n); Deck.out('eDo', d.toFixed(1));
    const mdd = 2.80 * s * Math.sqrt(2 / n);
    Deck.hbars(document.getElementById('eBars'), [{ label: 'smallest detectable gap', value: mdd, color: 'var(--d)', text: mdd.toFixed(2) + ' pts' },
      { label: 'observed gap', value: d, color: d > mdd ? 'var(--e)' : 'var(--faint)', text: d.toFixed(1) + ' pts' }], { max: Math.max(mdd, d, 0.5) * 1.15 });
    document.getElementById('eOut').innerHTML = `Seed σ = ${s.toFixed(2)} points, ${n} seed${n > 1 ? 's' : ''} per arm: the difference of means has standard error ${(s * Math.sqrt(2 / n)).toFixed(2)}, so gaps below <b>${mdd.toFixed(2)} points</b> are invisible at 5% significance and 80% power. ` +
      (d > mdd ? `The observed ${d.toFixed(1)}-point gap clears it.` : `The observed ${d.toFixed(1)}-point gap does not: add seeds or switch to a lower-noise metric.`);
  });
})();
