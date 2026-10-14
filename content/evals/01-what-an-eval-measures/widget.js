(() => {
  const { svg, clear, fmt } = Deck;

  const P = [
    '<b>Capability.</b> What should the number tell you? "Knows chemistry facts", "can solve new maths problems", "fixes real bugs" and "users prefer it" need different evals. A mismatch here makes everything downstream irrelevant.',
    '<b>Questions.</b> Which benchmark, version and split, and how many questions? A few hundred questions give confidence intervals several points wide. Questions may also have leaked into training data (deck 05).',
    '<b>Prompt format.</b> Template, separators, number of few-shot examples, chain of thought or not. Sclar et al.: up to 76 accuracy points between equivalent formats for LLaMA-2-13B.',
    '<b>Decoding.</b> Greedy or sampled, temperature, how many samples. pass@1 measures reliability; pass@k with many samples measures whether the model can ever get it (deck 03).',
    '<b>Scoring.</b> Exact match, log-probability of each option, regex-parsing a generated answer, unit tests, or an LLM judge. Each makes different mistakes (decks 02, 06).',
    '<b>Uncertainty.</b> The score is a sample mean with a standard error. Grouped questions need clustered errors, and model comparisons should be paired (deck 04).',
  ];
  Deck.seg('pSeg', v => { document.getElementById('pInfo').innerHTML = P[+v]; });
  const F = [0.62, 0.48, 0.71, 0.36];
  Deck.seg('fSeg', v => {
    Deck.hbars(document.getElementById('fBars'), F.map((a, i) => ({ label: ['"Question: … Answer:"', '"Q: … A:"', '"QUESTION … ANSWER"', '"question - … answer -"'][i], value: a, color: i === +v ? 'var(--a)' : 'var(--faint)', text: (100 * a).toFixed(0) + '%' })), { max: 1 });
    document.getElementById('fOut').innerHTML = `Selected format: <b>${(100 * F[+v]).toFixed(0)}%</b>. Across formats: mean ${(100 * F.reduce((a, b) => a + b) / 4).toFixed(0)}%, range ${(100 * Math.min(...F)).toFixed(0)}–${(100 * Math.max(...F)).toFixed(0)}%. Reporting only one format hides a ${(100 * (Math.max(...F) - Math.min(...F))).toFixed(0)}-point spread.`;
  });

})();
