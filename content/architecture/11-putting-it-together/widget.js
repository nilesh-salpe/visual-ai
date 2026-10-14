(() => {
  const { svg, clear, fmt } = Deck;

  const PARTS = [
    ['emb', 'token embedding', 290, 'Token id → vector of d numbers. With RoPE there is no position vector here. Llama 3: 128,256 × 4,096 (≈525M parameters).'],
    ['n1', 'RMSNorm', 245, 'Pre-norm: normalize only the input to the sub-layer, dividing by the root mean square. (Deck 02)'],
    ['att', 'GQA attention + RoPE (FlashAttention)', 200, '32 query heads, 8 K/V heads (GQA, deck 05). RoPE rotates q and k (deck 03). Computed with a tiled, exact kernel (deck 09). K and V go into the KV cache.'],
    ['r1', '+ residual', 155, 'Add the attention output to the stream. The stream itself is never normalized.'],
    ['n2', 'RMSNorm', 120, 'Second pre-norm, before the FFN.'],
    ['ffn', 'SwiGLU FFN (or MoE experts)', 75, 'SiLU-gated FFN, 14,336 hidden (deck 04); in MoE models, a router picks the top-k expert FFNs (deck 10). About 70% of the parameters.'],
    ['r2', '+ residual', 30, 'Add the FFN output. Repeat the whole block L times; then a final RMSNorm and the output head.'],
  ];
  (() => {
    const s = document.getElementById('bSvg');
    PARTS.forEach(([k, label, y, info], i) => {
      const g = svg('g', { style: 'cursor:pointer' }, s), wide = k === 'att' || k === 'ffn';
      svg('rect', { x: wide ? 130 : 200, y, width: wide ? 400 : 260, height: 34, rx: 8, class: ['emb', 'r1', 'r2'].includes(k) ? 'f-panel' : k === 'att' ? 'f-c' : k === 'ffn' ? 'f-a' : 'f-e', style: 'stroke:var(--line)' }, g);
      svg('text', { x: 330, y: y + 22, 'text-anchor': 'middle', class: 't', style: ['emb', 'r1', 'r2'].includes(k) ? 'font-weight:600' : 'fill:#fff;font-weight:600', text: label }, g);
      const show = () => { document.getElementById('bInfo').innerHTML = `<b>${label}</b>: ${info}`; };
      g.addEventListener('mouseenter', show); g.addEventListener('click', show);
    });
    svg('text', { x: 560, y: 180, class: 'tm', style: 'font-size:11px', text: '× L layers' }, s);
    svg('line', { x1: 550, x2: 550, y1: 30, y2: 280, style: 'stroke:var(--faint);stroke-dasharray:4 4' }, s);
  })();
  const count = (V, d, L, H, G, h) => { const dh = d / H; return V * d * 2 + L * (2 * d * d + 2 * d * G * dh + 3 * d * h + 2 * d) + d; };
  let vocab = 128256;
  const calc = () => {
    const d = Deck.val('zD'), L = Deck.val('zL'), H = d / 128; let G = Deck.val('zK'); const h = Deck.val('zH');
    if (G > H) G = H; while (H % G) G--;
    Deck.out('zDo', d.toLocaleString()); Deck.out('zLo', L); Deck.out('zKo', G + ` (of ${H} q heads)`); Deck.out('zHo', h.toLocaleString());
    const P = count(vocab, d, L, H, G, h), emb = 2 * vocab * d, attn = L * (2 * d * d + 2 * d * G * 128), ffn = L * 3 * d * h;
    Deck.out('zP', (P / 1e9).toFixed(2) + 'B'); Deck.out('zKV', Deck.bytes(2 * L * G * 128 * 2)); Deck.out('zF', (2 * P / 1e9).toFixed(1) + ' GFLOP'); Deck.out('zW', Deck.bytes(2 * P));
    Deck.hbars(document.getElementById('zBars'), [
      { label: 'FFN', value: ffn, color: 'var(--a)', text: (100 * ffn / P).toFixed(1) + '%' },
      { label: 'attention', value: attn, color: 'var(--c)', text: (100 * attn / P).toFixed(1) + '%' },
      { label: 'embeddings + head', value: emb, color: 'var(--b)', text: (100 * emb / P).toFixed(1) + '%' }], { max: P });
  };
  Deck.seg('zSeg', v => {
    const [V, d, L, H, G, h] = v.split(',').map(Number); vocab = V;
    document.getElementById('zD').value = d; document.getElementById('zL').value = L; document.getElementById('zK').value = G; document.getElementById('zH').value = h; calc();
  });
  Deck.bind(['zD', 'zL', 'zK', 'zH'], calc);

})();
