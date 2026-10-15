(() => {
  const { svg, clear, fmt } = Deck;
  Deck.hbars(document.getElementById('cBars'), [
    { label: 'PaLM 540B, standard prompting', value: 18, color: 'var(--faint)', text: '18%' },
    { label: 'finetuned GPT-3 175B', value: 33, color: 'var(--b)', text: '33%' },
    { label: 'prior best (finetuned GPT-3 + verifier)', value: 55, color: 'var(--c)', text: '55%' },
    { label: 'PaLM 540B, chain of thought (8 exemplars)', value: 57, color: 'var(--e)', text: '57%' }], { max: 70 });
})();
