(() => {
Deck.bind(['jbP', 'jbC', 'jbN'], () => {
  const p = Math.pow(10, Deck.val('jbP')), c = Deck.val('jbC') / 100, N = Math.round(Math.pow(10, Deck.val('jbN')));
  Deck.out('jbPo', (100 * p < 0.1 ? (100 * p).toFixed(3) : (100 * p).toFixed(2)) + '%'); Deck.out('jbCo', (100 * c).toFixed(1) + '%'); Deck.out('jbNo', N.toLocaleString());
  const q = p * (1 - c), b0 = 1 - Math.pow(1 - p, N), b1 = 1 - Math.pow(1 - q, N);
  const med = x => (x > 0 ? Math.ceil(Math.log(0.5) / Math.log(1 - x)) : Infinity);
  Deck.hbars(document.getElementById('jbBars'), [
    { label: 'model only: P(at least one success)', value: b0, color: 'var(--d)', text: (100 * b0).toFixed(1) + '%' },
    { label: 'model + output classifier', value: b1, color: 'var(--e)', text: (100 * b1).toFixed(1) + '%' }], { max: 1 });
  document.getElementById('jbOut').innerHTML = `With ${N.toLocaleString()} attempts at ${(100 * p).toPrecision(2)}% per attempt, the attacker succeeds with probability <b>${(100 * b0).toFixed(1)}%</b>; half of attackers need about ${med(p).toLocaleString()} attempts. A classifier that blocks ${(100 * c).toFixed(1)}% of what slips past the model raises that to about <b>${med(q).toLocaleString()}</b> attempts. ` +
    'Retries make any per-attempt rate add up, so rate limits and account monitoring matter as much as the model.';
});
})();
