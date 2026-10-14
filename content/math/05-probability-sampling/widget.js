(() => {
  const { svg, clear, fmt } = Deck;
  const TOK = ['mat', 'floor', 'sofa', 'roof', 'moon'], Z = [3.0, 2.2, 1.6, 0.4, -1.5];
  Deck.bind(['pT', 'pK', 'pP'], () => {
    const t = Deck.val('pT'), k = Deck.val('pK'), pp = Deck.val('pP'); Deck.out('pTo', t.toFixed(1)); Deck.out('pKo', k); Deck.out('pPo', pp.toFixed(2));
    const mx = Math.max(...Z), e = Z.map(z => Math.exp((z - mx) / t)), S = e.reduce((a, b) => a + b), p = e.map(v => v / S);
    let keep = p.map((_, i) => i < k), cum = 0; p.forEach((v, i) => { if (cum >= pp - 1e-9) keep[i] = false; cum += v; });
    const kept = p.map((v, i) => keep[i] ? v : 0), KS = kept.reduce((a, b) => a + b), q = kept.map(v => v / KS);
    const H = -q.reduce((a, v) => a + (v > 0 ? v * Math.log2(v) : 0), 0);
    Deck.hbars(document.getElementById('pBars'), TOK.map((n, i) => ({ label: `"${n}" (logit ${Z[i]})`, value: q[i], color: keep[i] ? 'var(--a)' : 'var(--faint)', text: keep[i] ? (100 * q[i]).toFixed(1) + '%' : 'cut' })), { max: 1 });
    document.getElementById('pOut').innerHTML = `${keep.filter(Boolean).length} token(s) kept. Entropy of the sampling distribution: <b>${H.toFixed(2)} bits</b> (0 = deterministic, ${Math.log2(5).toFixed(2)} = uniform over 5).`;
  });
})();
