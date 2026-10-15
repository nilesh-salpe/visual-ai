(() => {
Deck.bind(['vN', 'vD', 'vM', 'vQ'], () => {
  const N = Math.round(10 ** (Deck.val('vN') / 10)), d = Deck.val('vD'), M = Deck.val('vM'), m = Deck.val('vQ');
  const fmt = b => b >= 1e12 ? (b / 1e12).toFixed(2) + ' TB' : b >= 1e9 ? (b / 1e9).toFixed(1) + ' GB' : (b / 1e6).toFixed(0) + ' MB';
  Deck.out('vNo', N >= 1e9 ? (N / 1e9).toFixed(1) + 'B' : (N / 1e6).toFixed(0) + 'M'); Deck.out('vDo', d); Deck.out('vMo', M); Deck.out('vQo', m + ' B');
  const flat = N * d * 4, hnsw = flat + N * 2 * M * 4, pq = N * m + N * 8;
  Deck.hbars(document.getElementById('vBars'), [{ label: 'flat float32', value: flat, color: 'var(--d)', text: fmt(flat) },
    { label: 'HNSW (float32 + layer-0 links)', value: hnsw, color: 'var(--a)', text: fmt(hnsw) },
    { label: 'IVF-PQ (codes + ids)', value: pq, color: 'var(--e)', text: fmt(pq) }], { max: hnsw * 1.05 });
  document.getElementById('vOut').innerHTML = `${N.toLocaleString()} vectors × ${d} dims × 4 bytes = <b>${fmt(flat)}</b> raw. HNSW adds up to 2M = ${2 * M} neighbour ids of 4 bytes per vector at layer 0 (+${fmt(N * 2 * M * 4)}). PQ stores ${m} one-byte codes per vector (8 bits = 256 centroids per sub-space) plus an 8-byte id: <b>${fmt(pq)}</b>, ${(flat / pq).toFixed(0)}× smaller, at the price of approximate distances (often re-ranked with full vectors).`;
});
})();
