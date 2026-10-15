(() => {
  const { svg, clear, fmt } = Deck;
  Deck.hbars(document.getElementById('dBars'), [
    { label: '~1M features', value: 2, color: 'var(--e)', text: '≈2% dead' },
    { label: '~4M features', value: 35, color: 'var(--b)', text: '≈35% dead' },
    { label: '~34M features', value: 65, color: 'var(--d)', text: '≈65% dead' }], { max: 100 });
})();
