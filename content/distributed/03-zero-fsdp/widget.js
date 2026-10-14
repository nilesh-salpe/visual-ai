(() => {
  const { svg, clear, fmt } = Deck;
  const PS = [1e9, 7e9, 70e9, 405e9, 1e12], NS = [1, 8, 16, 64, 256, 1024, 4096];
  const zb = (P, N, s) => [16 * P, 4 * P + 12 * P / N, 2 * P + 14 * P / N, 16 * P / N][s];
  Deck.bind(['zP', 'zN'], () => {
    const P = PS[Deck.val('zP')], N = NS[Deck.val('zN')]; Deck.out('zPo', P >= 1e12 ? '1T' : (P / 1e9) + 'B'); Deck.out('zNo', N.toLocaleString());
    Deck.hbars(document.getElementById('zBars'), [0, 1, 2, 3].map(s => { const b = zb(P, N, s); return { label: ['stage 0 (DDP)', 'stage 1: + shard optimizer', 'stage 2: + shard grads', 'stage 3 / FSDP: + shard params'][s], value: b, color: b <= 80e9 ? 'var(--e)' : 'var(--d)', text: (b / 1e9 >= 1000 ? (b / 1e12).toFixed(1) + ' TB' : (b / 1e9).toFixed(b < 10e9 ? 1 : 0) + ' GB') + (b <= 80e9 ? ' ✓ fits' : '') }; }), { log: true, min: 1e8 });
  });
})();
