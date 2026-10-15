(() => {
  const { svg, clear, fmt } = Deck;
  Deck.bind(['hP', 'hT'], () => {
    const p = Deck.val('hP') / 100, t = Deck.val('hT') / 100, pen = t / (1 - t);
    Deck.out('hPo', Math.round(p * 100) + '%'); Deck.out('hTo', t.toFixed(2));
    const g = p - (1 - p) * pen;
    Deck.hbars(document.getElementById('hBars'), [
      { label: 'guess, binary grading', value: p, color: 'var(--b)', text: '+' + p.toFixed(2) },
      { label: `guess, penalty ${pen.toFixed(1)} per error`, value: g, color: g > 0 ? 'var(--e)' : 'var(--d)', text: (g >= 0 ? '+' : '') + g.toFixed(2) },
      { label: 'abstain ("I don\'t know")', value: 0, color: 'var(--faint)', text: '0.00' }], { max: 1 });
    document.getElementById('hOut').innerHTML = `At ${Math.round(p * 100)}% confidence a guess is worth <b>${p.toFixed(2)}</b> points under 0/1 grading, so guessing always wins. With a stated target t = ${t.toFixed(2)} (wrong answers cost ${pen.toFixed(1)}), a guess is worth <b>${g.toFixed(2)}</b>: ` +
      (g > 0 ? 'the model should answer.' : 'the model should say it does not know.') + ' Break-even is exactly p = t.';
  });
  Deck.hbars(document.getElementById('sqBars'), [
    { label: 'GPT-4o · declined 1.0%', value: 60.8, color: 'var(--d)', text: '60.8% wrong' },
    { label: 'o1-preview · declined 9.2%', value: 48.1, color: 'var(--d)', text: '48.1% wrong' },
    { label: 'Claude 3.5 Sonnet · declined 35.0%', value: 36.1, color: 'var(--d)', text: '36.1% wrong' },
    { label: 'Claude 3 Haiku · declined 75.3%', value: 19.6, color: 'var(--d)', text: '19.6% wrong' }], { max: 100 });
})();
