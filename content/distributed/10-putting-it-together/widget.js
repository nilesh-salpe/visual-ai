(() => {
  const { svg, clear, fmt } = Deck;
  const P = 405e9, L = 126;
  const calc = () => {
    const tp = +Deck.val('qT'), cp = +Deck.val('qC'), pp = +Deck.val('qP'), dp = +Deck.val('qD');
    const g = tp * cp * pp * dp, states = 16 * P / (tp * pp * dp);
    const seq = cp > 1 ? 131072 : 8192, m = Math.max(1, Math.floor(16e6 / seq / dp)), bub = pp > 1 ? (pp - 1) / (2 * m) : 0;
    Deck.out('qG', g.toLocaleString()); Deck.out('qM', (states / 1e9).toFixed(1) + ' GB'); Deck.out('qB', (100 * bub).toFixed(1) + '%'); Deck.out('qN', tp <= 8 ? 'yes' : 'no, crosses nodes');
    document.getElementById('qN').style.color = tp <= 8 ? 'var(--e)' : 'var(--d)'; document.getElementById('qB').style.color = bub < 0.1 ? 'var(--e)' : 'var(--d)';
    document.getElementById('qOut').innerHTML = `${m} micro-batch${m > 1 ? 'es' : ''} per pipeline per step (${seq.toLocaleString()}-token sequences, 16M-token global batch). ${L % pp === 0 || pp === 1 ? '' : `126 layers over ${pp} stages is uneven; Llama 3 removed a layer from the first and last stages.`}`;
  };
  Deck.seg('qSeg', v => { const [t, c, p, d] = v.split(',').map(Number); document.getElementById('qT').value = t; document.getElementById('qC').value = c; document.getElementById('qP').value = p; document.getElementById('qD').value = d; calc(); });
  Deck.bind(['qT', 'qC', 'qP', 'qD'], calc);
})();
