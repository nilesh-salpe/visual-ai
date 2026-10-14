(() => {
  const { svg, clear } = Deck;

  /* ingredient map */
  const ING = [
    ['Direct attention connections', 'var(--b)', [0, 1], '<b>Self-attention</b> connects every pair of positions with O(1) sequential operations and O(1) path length (Table 1), so the whole sequence is processed in parallel and long-range links are one hop.', '03-self-attention'],
    ['Multiple heads', '#3a8fd8', [2], '<b>Multi-head attention</b> counteracts the "reduced effective resolution due to averaging" (§2). Evidence: 1 head is 0.9 BLEU worse than the best setting (Table 3A).', '06-multi-head-attention'],
    ['Positional encoding', '#c9a227', [3], '<b>Sinusoidal PE</b> gives the order-blind attention mechanism information about token positions. Learned embeddings performed the same (Table 3E: 25.7 vs 25.8).', '07-positional-encoding'],
    ['Stacked layers: residual + LN + FFN', 'var(--e)', [4], '<b>N = 6 layers</b>, each LayerNorm(x + Sublayer(x)), with a position-wise FFN for per-token transformation. Depth matters: N = 2 drops to 23.7 BLEU and N = 8 reaches 25.5 (Table 3C); a wider FFN helps (26.2).', '10-residual-layernorm'],
  ];
  const PROB = ['Sequential computation', 'Long paths between distant tokens', 'Averaging blurs relationships', 'No sense of word order', 'Need for depth and per-token processing'];
  let sel = 0;
  const drawMap = () => {
    const s = clear(document.getElementById('mapSvg'));
    PROB.forEach((p, j) => {
      const on = ING[sel][2].includes(j), y = 20 + j * 62;
      TX.box(s, 300, y, 210, 44, on ? 'var(--d)' : 'var(--panel-2)', p, { text: on ? '#fff' : 'var(--muted)', fs: 11.5, stroke: 'var(--line)' });
    });
    ING.forEach(([n, c, targets], i) => {
      const y = 30 + i * 76, on = i === sel;
      targets.forEach(j => svg('line', { x1: 230, y1: y + 22, x2: 298, y2: 42 + j * 62, style: `stroke:${c};stroke-width:${on ? 4 : 1.5};opacity:${on ? 1 : .35}` }, s));
      const g = TX.box(s, 10, y, 220, 44, c, n, { fs: 11.5, attrs: { 'data-i': i } });
      if (!on) g.style.opacity = .55;
    });
    const [, , , txt, deck] = ING[sel];
    document.getElementById('mapInfo').innerHTML = txt + `<br><br><a href="../${deck}/index.html">Open the deck →</a>`;
  };
  document.getElementById('mapSvg').addEventListener('click', e => { const g = e.target.closest('[data-i]'); if (g) { sel = +g.dataset.i; drawMap(); } });
  drawMap();

  /* Table 3 */
  const BASE = { n: 'base', ppl: 4.92, bleu: 25.8 };
  const T3 = {
    A: { rows: [['h = 1, d_k = 512', 5.29, 24.9], ['h = 4, d_k = 128', 5.00, 25.5], ['h = 16, d_k = 32', 4.91, 25.8], ['h = 32, d_k = 16', 5.01, 25.4]], note: 'Computation held constant. One head is 0.9 BLEU worse than the best; too many heads also hurts.' },
    B: { rows: [['d_k = 16', 5.16, 25.1], ['d_k = 32', 5.01, 25.4]], note: 'Smaller keys hurt: "determining compatibility is not easy".' },
    C: { rows: [['N = 2', 6.11, 23.7], ['N = 4', 5.19, 25.3], ['N = 8', 4.88, 25.5], ['d_model = 256', 5.75, 24.5], ['d_model = 1024', 4.66, 26.0], ['d_ff = 1024', 5.12, 25.4], ['d_ff = 4096', 4.75, 26.2]], note: '"Bigger models are better." Depth, width and FFN size all matter.' },
    D: { rows: [['P_drop = 0.0', 5.77, 24.6], ['P_drop = 0.2', 4.95, 25.5], ['ε_ls = 0.0', 4.67, 25.3], ['ε_ls = 0.2', 5.47, 25.7]], note: 'Dropout is very helpful. Label smoothing raises perplexity but improves BLEU (§5.4).' },
    E: { rows: [['learned positional embedding', 4.92, 25.7]], note: 'Nearly identical to sinusoids; sinusoids were kept for possible length extrapolation.' },
    big: { rows: [['big (d_model 1024, d_ff 4096, h 16, P_drop 0.3, 300K steps)', 4.33, 26.4]], note: 'The big configuration: 213M parameters, best dev results in the table.' },
  };
  Deck.seg('aSeg', v => {
    const g = T3[v], rows = [[BASE.n, BASE.ppl, BASE.bleu], ...g.rows];
    Deck.hbars(document.getElementById('aBleu'), rows.map(([n, , b]) => ({ label: n, value: b - 23, color: n === 'base' ? 'var(--faint)' : b > BASE.bleu ? 'var(--e)' : b < BASE.bleu ? 'var(--d)' : 'var(--a)', text: b.toFixed(1) })), { max: 3.6 });
    Deck.hbars(document.getElementById('aPpl'), rows.map(([n, p]) => ({ label: n, value: p - 4, color: n === 'base' ? 'var(--faint)' : p < BASE.ppl ? 'var(--e)' : p > BASE.ppl ? 'var(--d)' : 'var(--a)', text: p.toFixed(2) })), { max: 2.2 });
    document.getElementById('aNote').textContent = g.note;
  });
})();
