(() => {
Deck.bind(['aP', 'aD'], () => {
  const p = Deck.val('aP') / 100, d = Deck.val('aD') / 100, q = Math.min(p + d, 0.999);
  Deck.out('aPo', Math.round(p * 100) + '%'); Deck.out('aDo', (d * 100).toFixed(1) + ' pts');
  const n = Math.ceil(2.80 ** 2 * (p * (1 - p) + q * (1 - q)) / (d * d)), half = Math.ceil(n / 2);
  Deck.hbars(document.getElementById('aBars'), [{ label: 'users per arm', value: n, color: 'var(--a)', text: n.toLocaleString() },
    { label: 'with CUPED (≈50% less variance)', value: half, color: 'var(--e)', text: half.toLocaleString() }], { max: n * 1.08 });
  document.getElementById('aOut').innerHTML = `Detecting a lift from ${Math.round(p * 100)}% to ${(q * 100).toFixed(1)}% task success (two-sided 5%, 80% power) needs about <b>${n.toLocaleString()} users per arm</b>. Halving the lift needs about four times as many. CUPED cut variance by about 50% at Bing, which halves the users or the duration.`;
});
})();
