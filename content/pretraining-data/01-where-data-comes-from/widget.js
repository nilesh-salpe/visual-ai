(() => {
  const { svg, clear, fmt } = Deck;
  const FUN = [['Common Crawl', 100], ['after extraction + language ID', 48], ['after quality filtering', 23], ['after deduplication', 10]];
  const MIX = [['general knowledge', 50], ['math and reasoning', 25], ['code', 17], ['multilingual', 8]];
  Deck.seg('fSeg', v => {
    const rows = v === 'funnel' ? FUN : MIX;
    Deck.hbars(document.getElementById('fBars'), rows.map(([l, x], i) => ({ label: l, value: x, color: ['var(--faint)', 'var(--c)', 'var(--a)', 'var(--e)'][i], text: (v === 'funnel' && i === 3 ? '≈ ' : '') + x + '%' })), { max: 100 });
    document.getElementById('fOut').innerHTML = v === 'funnel' ? 'Share of original documents remaining (RefinedWeb). Each of language ID, filtering and dedup roughly halves the data.' : 'Llama 3\'s final pretraining mix by tokens ("roughly", per the paper).';
  });
})();
