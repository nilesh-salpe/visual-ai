(() => {
  const { svg, clear, fmt } = Deck;
  const OPS = { base: { shape: [3, 4], st: [4, 1], off: 0, store: 12, label: 'x' }, t: { shape: [4, 3], st: [1, 4], off: 0, store: 12, label: 'x.t()' },
    slice: { shape: [3, 2], st: [4, 1], off: 1, store: 12, label: 'x[:, 1:3]' }, expand: { shape: [3, 4], st: [0, 1], off: 0, store: 4, label: 'bias.expand(3, 4)' },
    cont: { shape: [4, 3], st: [3, 1], off: 0, store: 12, label: 'x.t().contiguous()', copy: true } };
  Deck.seg('tSeg', v => {
    const o = OPS[v], s = clear(document.getElementById('tSvg')), [R, C] = o.shape, w = 46;
    for (let i = 0; i < R; i++) for (let j = 0; j < C; j++) {
      const idx = o.off + i * o.st[0] + j * o.st[1];
      svg('rect', { x: 30 + j * w, y: 20 + i * 40, width: w - 4, height: 36, rx: 6, style: `fill:color-mix(in srgb, var(--a) ${20 + 6 * idx}%, var(--panel-2))` }, s);
      svg('text', { x: 30 + j * w + 21, y: 43 + i * 40, 'text-anchor': 'middle', class: 't', style: 'font-weight:700', text: idx }, s); }
    svg('text', { x: 30, y: 200, class: 'tm', text: o.copy ? 'new storage (a copy):' : 'storage (shared with x):' }, s);
    for (let k = 0; k < o.store; k++) { svg('rect', { x: 250 + k * 32, y: 186, width: 30, height: 26, rx: 4, style: `fill:${o.copy ? 'var(--b)' : 'var(--a)'};opacity:${.35 + .05 * k}` }, s); svg('text', { x: 265 + k * 32, y: 204, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11px', text: k }, s); }
    const contiguous = o.st[1] === 1 && (R === 1 || o.st[0] === C) && !o.off;
    document.getElementById('tOut').innerHTML = `<code>${o.label}</code>: shape (${o.shape}), strides (${o.st}), storage offset ${o.off}. Contiguous: <b>${contiguous ? 'yes' : 'no'}</b>${o.st[0] === 0 ? ' (stride 0 = broadcast)' : ''}. Each cell shows the storage index it reads.`;
  });
})();
