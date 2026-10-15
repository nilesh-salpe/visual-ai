(() => {
  const { svg, clear, fmt } = Deck;
  Deck.hbars(document.getElementById('kBars'), [
    { label: 'LLaVA-1.5 (ViT-L/14, 336 px)', value: 576, color: 'var(--a)', text: '576 tokens' },
    { label: 'ViT-B/16 at 224 px', value: 196, color: 'var(--b)', text: '196 tokens' },
    { label: 'Flamingo Perceiver Resampler', value: 64, color: 'var(--c)', text: '64 tokens' },
    { label: 'BLIP-2 Q-Former', value: 32, color: 'var(--e)', text: '32 queries' }], { max: 620 });
})();
