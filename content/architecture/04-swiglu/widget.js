(() => {
  const { svg, clear, fmt } = Deck;

  (() => {
    const d = 4096, attn = 2 * d * d + 2 * d * 1024, ffn = 3 * d * 14336;
    Deck.hbars(document.getElementById('pBars'), [
      { label: 'attention (GQA)', value: attn, color: 'var(--c)', text: (attn / 1e6).toFixed(1) + 'M (' + (100 * attn / (attn + ffn)).toFixed(0) + '%)' },
      { label: 'FFN (SwiGLU)', value: ffn, color: 'var(--a)', text: (ffn / 1e6).toFixed(1) + 'M (' + (100 * ffn / (attn + ffn)).toFixed(0) + '%)' }], { max: ffn * 1.05 });
  })();
  const silu = z => z / (1 + Math.exp(-z)), gelu = z => 0.5 * z * (1 + Math.tanh(Math.sqrt(2 / Math.PI) * (z + 0.044715 * z ** 3)));
  Deck.bind(['gB'], () => {
    const b = Deck.val('gB'); Deck.out('gBo', b.toFixed(1));
    const s = clear(document.getElementById('aSvg'));
    const panel = (x0, title, fns, ymin, ymax) => {
      const W = 290, X = z => x0 + (z + 4) / 8 * W, Y = y => 190 - (y - ymin) / (ymax - ymin) * 160;
      svg('text', { x: x0 + W / 2, y: 18, 'text-anchor': 'middle', class: 't', style: 'font-weight:600', text: title }, s);
      svg('line', { x1: x0, x2: x0 + W, y1: Y(0), y2: Y(0), class: 'ln' }, s); svg('line', { x1: X(0), x2: X(0), y1: 30, y2: 190, class: 'ln' }, s);
      fns.forEach(([f, c]) => { let p = ''; for (let z = -4; z <= 4.001; z += 0.05) p += `${X(z)},${Y(Math.max(ymin, Math.min(ymax, f(z))))} `; svg('polyline', { points: p, fill: 'none', style: `stroke:${c};stroke-width:2.5` }, s); });
      svg('text', { x: x0 + W / 2, y: 214, 'text-anchor': 'middle', class: 'tm', text: 'pre-activation (z or a)' }, s);
    };
    panel(20, 'activation functions', [[z => Math.max(0, z), 'var(--faint)'], [gelu, 'var(--c)'], [silu, 'var(--a)']], -1, 4);
    panel(350, `gated unit: SiLU(a) × ${b.toFixed(1)}`, [[z => silu(z), 'var(--a)'], [z => silu(z) * b, 'var(--b)']], -4, 4);
  });
  Deck.seg('hSeg', v => {
    const [d, mo, mult] = v.split(',').map(Number), h1 = 4 * d, h2 = Math.floor(2 * h1 / 3), h3 = mult ? Math.floor(mult * h2) : h2, h4 = mo * Math.ceil(h3 / mo);
    Deck.out('h1', h1.toLocaleString()); Deck.out('h2', h2.toLocaleString()); Deck.out('h3', mult ? h3.toLocaleString() : '(none)'); Deck.out('h4', h4.toLocaleString());
    Deck.hbars(document.getElementById('hBars'), [
      { label: 'ReLU FFN params (2·d·4d)', value: 2 * d * h1, color: 'var(--faint)', text: (2 * d * h1 / 1e6).toFixed(0) + 'M' },
      { label: 'SwiGLU params (3·d·hidden)', value: 3 * d * h4, color: 'var(--a)', text: (3 * d * h4 / 1e6).toFixed(0) + 'M' }], { max: 3 * 4096 * 14336 * 1.05 * (d / 4096) ** 2 });
  });
  Deck.hbars(document.getElementById('sBars'), [['ReLU (baseline)', 1.677], ['GELU', 1.679], ['Swish', 1.683], ['GLU (sigmoid)', 1.663], ['Bilinear', 1.648], ['ReGLU', 1.645], ['SwiGLU', 1.636], ['GEGLU', 1.633]].map(([n, v]) => ({ label: n, value: v - 1.6, color: /GLU|Bilinear/.test(n) ? 'var(--a)' : 'var(--faint)', text: v.toFixed(3) })), { max: 0.09 });

})();
