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
(() => {
  // web-scale estimates: index size, shards, replicas, fan-out tail, LLM GPUs
  Deck.bind(['wsD', 'wsQ', 'wsC', 'wsL'], () => {
    const D = Deck.val('wsD') * 1e9, Q = Deck.val('wsQ'), hit = Deck.val('wsC') / 100, llm = Deck.val('wsL') / 100;
    Deck.out('wsDo', (D / 1e9).toFixed(1) + 'B'); Deck.out('wsQo', Q.toLocaleString()); Deck.out('wsCo', Math.round(hit * 100) + '%'); Deck.out('wsLo', Math.round(llm * 100) + '%');
    const vecs = D * 3, bytes = vecs * 128, shards = Math.ceil(vecs / 50e6), miss = Q * (1 - hit), reps = Math.ceil(miss / 2000), slowP = 1 - Math.pow(0.99, shards);
    const llmGpus = Math.ceil(Q * (1 - hit) * llm * 300 / 10000) * 8;
    Deck.hbars(document.getElementById('wsBars'), [
      { label: 'index in RAM (compressed)', value: 1, color: 'var(--a)', text: (bytes / 1e12).toFixed(2) + ' TB' },
      { label: 'shards (50M vectors each)', value: 1, color: 'var(--c)', text: shards.toLocaleString() },
      { label: 'shard servers (all shards × replicas)', value: 1, color: 'var(--b)', text: (shards * reps).toLocaleString() },
      { label: 'queries hitting a slow shard (1% each)', value: slowP, color: 'var(--d)', text: Math.round(100 * slowP) + '%' },
      { label: 'GPUs for LLM answers', value: 1, color: 'var(--e)', text: llmGpus.toLocaleString() }], { max: 1 });
    document.getElementById('wsOut').innerHTML = `${(vecs / 1e9).toFixed(1)}B vectors in ${shards} shards. Every uncached query fans out to all shards, so each shard needs ${reps.toLocaleString()} replicas for ${Math.round(miss).toLocaleString()} queries/s: <b>${(shards * reps).toLocaleString()} shard servers</b>. Partitioning so a query touches fewer shards cuts this proportionally. LLM answers for ${Math.round(llm * 100)}% of uncached queries need about <b>${llmGpus.toLocaleString()} GPUs</b>.`;
  });
})();

