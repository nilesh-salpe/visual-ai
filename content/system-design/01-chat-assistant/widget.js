(() => {
Deck.bind(['cD', 'cR', 'cP', 'cI', 'cO', 'cS', 'cT'], () => {
  const dau = Deck.val('cD') * 1e5, rpu = Deck.val('cR'), pf = Deck.val('cP'), inp = Deck.val('cI'), outT = Deck.val('cO'), spd = Deck.val('cS'), thr = Deck.val('cT') * 1000;
  Deck.out('cDo', (dau / 1e6).toFixed(1) + 'M'); Deck.out('cRo', rpu); Deck.out('cPo', pf + '×'); Deck.out('cIo', inp.toLocaleString()); Deck.out('cOo', outT); Deck.out('cSo', spd); Deck.out('cTo', (thr / 1000) + 'K');
  const rps = dau * rpu / 86400 * pf, conc = rps * outT / spd, kvGB = conc * (inp + outT) * 320 / 1e6;
  const perRep = 0.92 * 640 - 140, repMem = Math.ceil(kvGB / perRep), repThr = Math.ceil(rps * outT / thr), rep = Math.max(repMem, repThr);
  Deck.hbars(document.getElementById('cBars'), [{ label: 'replicas for KV memory', value: repMem, color: 'var(--a)', text: repMem + ' × 8 GPUs' },
    { label: 'replicas for output tokens/s', value: repThr, color: 'var(--c)', text: repThr + ' × 8 GPUs' }], { max: Math.max(repMem, repThr) * 1.1 + 1 });
  document.getElementById('cOut').innerHTML = `Peak ${Math.round(rps).toLocaleString()} requests/s; at ${spd} tokens/s per stream each answer takes ${(outT / spd).toFixed(1)} s, so about <b>${Math.round(conc).toLocaleString()}</b> sequences run at once (Little's law). At 320 KB of KV per token (70B-shaped, 16-bit) that is <b>${(kvGB / 1000).toFixed(2)} TB</b> of KV cache. One 8 × 80 GB replica with 92% of memory usable and 140 GB of weights has about ${Math.round(perRep)} GB for KV. Fleet: <b>${rep} replicas (${rep * 8} GPUs)</b>, set by ${repMem >= repThr ? 'memory' : 'throughput'}. Replica throughput is an input you must measure.`;
});
})();
