(() => {
Deck.bind(['tP', 'tT', 'tG', 'tM', 'tC', 'tR'], () => {
  const P = Deck.val('tP') * 1e9, T = Deck.val('tT') * 1e12, G = Deck.val('tG'), mfu = Deck.val('tM') / 100, ck = Deck.val('tC'), rs = Deck.val('tR');
  Deck.out('tPo', Deck.val('tP') + 'B'); Deck.out('tTo', Deck.val('tT') + 'T'); Deck.out('tGo', G.toLocaleString()); Deck.out('tMo', Math.round(mfu * 100) + '%'); Deck.out('tCo', ck + ' min'); Deck.out('tRo', rs + ' min');
  const flops = 6 * P * T, days = flops / (G * 989e12 * mfu) / 86400;
  const rate = 419 / (54 * 24 * 16384), mtbfMin = 60 / (rate * G), tau = Math.sqrt(2 * ck * mtbfMin);
  const waste = ck / tau + (tau / 2 + rs) / mtbfMin, total = days / (1 - Math.min(waste, 0.9));
  Deck.hbars(document.getElementById('tBars'), [{ label: 'ideal training time', value: days, color: 'var(--e)', text: days.toFixed(0) + ' days' },
    { label: 'with checkpoints, failures, restarts', value: total, color: 'var(--d)', text: total.toFixed(0) + ' days' }], { max: total * 1.08 });
  document.getElementById('tOut').innerHTML = `6 × ${(P / 1e9)}B × ${(T / 1e12)}T = <b>${flops.toExponential(1)} FLOPs</b>; at ${Math.round(mfu * 100)}% of 989 TFLOPS on ${G.toLocaleString()} H100s that is <b>${days.toFixed(0)} days</b>. At Llama 3's interruption rate (419 unexpected in 54 days on 16,384 GPUs) this job fails about every <b>${(mtbfMin / 60).toFixed(1)} h</b>; Young/Daly gives a checkpoint every <b>${tau.toFixed(0)} min</b>, and checkpoints, lost work and ${rs}-minute restarts cost about <b>${(100 * waste).toFixed(0)}%</b> of the time.`;
});
})();
