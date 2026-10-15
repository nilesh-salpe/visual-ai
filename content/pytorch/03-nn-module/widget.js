(() => {
  const { svg, clear, fmt } = Deck;
  Deck.bind(['pC', 'pL', 'pV', 'pT'], () => {
    const C = Deck.val('pC'), L = Deck.val('pL'), V = Deck.val('pV'), tied = document.getElementById('pT').checked;
    Deck.out('pCo', C.toLocaleString()); Deck.out('pLo', L); Deck.out('pVo', V.toLocaleString());
    const blocks = L * (12 * C * C + 2 * C), emb = V * C, head = tied ? 0 : V * C, tot = blocks + emb + head;
    const f = x => x >= 1e9 ? (x / 1e9).toFixed(2) + 'B' : (x / 1e6).toFixed(1) + 'M';
    Deck.hbars(document.getElementById('pBars'), [{ label: 'blocks (12C² + 2C each)', value: blocks, color: 'var(--a)', text: f(blocks) }, { label: 'token embedding (V × C)', value: emb, color: 'var(--c)', text: f(emb) },
      { label: 'output head', value: head, color: 'var(--b)', text: tied ? 'tied: 0' : f(head) }, { label: 'total', value: tot, color: 'var(--e)', text: f(tot) }], { log: true, min: 1e5 });
    document.getElementById('pOut').innerHTML = `Total ≈ <b>${f(tot)}</b> (position embeddings and biases ignored). Training with AdamW in mixed precision needs ≈ 16 bytes/param = <b>${(16 * tot / 1e9).toFixed(1)} GB</b> of model state. GPT-2 small: C 768, L 12, V 50,257, tied → 124M.`;
  });
})();
