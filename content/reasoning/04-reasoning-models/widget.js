(() => {
  const { svg, clear, fmt } = Deck;
  Deck.bind(['tA', 'tT', 'tS'], () => {
    const a = Deck.val('tA'), t = Deck.val('tT'), s = Deck.val('tS');
    Deck.out('tAo', a.toLocaleString()); Deck.out('tTo', t.toLocaleString()); Deck.out('tSo', s);
    const base = a / s, think = (a + t) / s;
    Deck.hbars(document.getElementById('tBars'), [{ label: 'answer only', value: base, color: 'var(--e)', text: base.toFixed(1) + ' s' },
      { label: 'thinking + answer', value: think, color: 'var(--d)', text: think.toFixed(1) + ' s' }], { max: think * 1.08 });
    document.getElementById('tOut').innerHTML = `Generation time at ${s} tokens/s: <b>${base.toFixed(1)} s</b> without thinking, <b>${think.toFixed(1)} s</b> with ${t.toLocaleString()} thinking tokens, and <b>${((a + t) / a).toFixed(1)}×</b> the output tokens billed. Worth it only if the extra reasoning changes the answer.`;
  });
})();
