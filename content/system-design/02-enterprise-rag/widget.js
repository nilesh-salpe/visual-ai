(() => {
Deck.bind(['rD', 'rT', 'rC', 'rM', 'rB'], () => {
  const docs = Deck.val('rD') * 1e6, tpd = Deck.val('rT'), ch = Deck.val('rC'), dim = Deck.val('rM'), bpd = Deck.val('rB');
  Deck.out('rDo', (docs / 1e6) + 'M'); Deck.out('rTo', tpd.toLocaleString()); Deck.out('rCo', ch); Deck.out('rMo', dim); Deck.out('rBo', bpd);
  const tokens = docs * tpd, chunks = tokens / ch, raw = chunks * dim * bpd / 1e9, hnsw = raw + chunks * 32 * 4 / 1e9, pq = chunks * 72 / 1e9, ctx = tokens / 1e6 * 1.02;
  Deck.hbars(document.getElementById('rBars'), [{ label: 'vectors (raw)', value: raw, color: 'var(--d)', text: raw.toFixed(0) + ' GB' },
    { label: 'HNSW (raw + M=16 links)', value: hnsw, color: 'var(--a)', text: hnsw.toFixed(0) + ' GB' },
    { label: 'IVF-PQ (64 B codes + id)', value: pq, color: 'var(--e)', text: pq.toFixed(1) + ' GB' }], { max: hnsw * 1.08 });
  document.getElementById('rOut').innerHTML = `${(docs / 1e6)}M documents × ${tpd.toLocaleString()} tokens = ${(tokens / 1e9).toFixed(0)}B tokens → <b>${(chunks / 1e6).toFixed(0)}M chunks</b> of ${ch} tokens. One-time contextual-chunk cost at Anthropic\'s estimate of $1.02 per million document tokens: <b>$${Math.round(ctx).toLocaleString()}</b> (their assumptions: 8K-token documents, 800-token chunks).`;
});
})();
