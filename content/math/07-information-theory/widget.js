(() => {
  const { svg, clear, fmt } = Deck;
  const P = [0.7, 0.2, 0.1];
  Deck.bind(['kA', 'kB'], () => {
    const a = Deck.val('kA'), sb = Deck.val('kB'), Q = [a, (1 - a) * sb, (1 - a) * (1 - sb)];
    Deck.out('kAo', a.toFixed(2)); Deck.out('kBo', sb.toFixed(2));
    const H = -P.reduce((s, p) => s + p * Math.log(p), 0), CE = -P.reduce((s, p, i) => s + p * Math.log(Q[i]), 0), KLpq = CE - H, KLqp = Q.reduce((s, q, i) => s + q * Math.log(q / P[i]), 0);
    Deck.hbars(document.getElementById('kBars'), ['A', 'B', 'C'].flatMap((n, i) => [{ label: `p(${n})`, value: P[i], color: 'var(--faint)', text: P[i].toFixed(2) }, { label: `q(${n})`, value: Q[i], color: 'var(--a)', text: Q[i].toFixed(2) }]), { max: 1 });
    document.getElementById('kOut').innerHTML = `H(p) = ${H.toFixed(3)} · H(p, q) = <b>${CE.toFixed(3)}</b> · KL(p‖q) = <b>${KLpq.toFixed(3)}</b> · KL(q‖p) = ${KLqp.toFixed(3)} nats. ${KLpq < 0.002 ? 'q ≈ p: both KLs vanish.' : 'Note the two KLs differ.'}`;
  });
})();
