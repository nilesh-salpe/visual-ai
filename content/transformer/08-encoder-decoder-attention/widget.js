(() => {
  const { svg, clear } = Deck;

  /* bottleneck */
  let mode = 'fixed';
  const bott = () => {
    const n = Deck.val('bN'); Deck.out('bNo', n);
    const s = clear(document.getElementById('bSvg'));
    TX.arrowDefs(s, 'ba', 'var(--muted)');
    const w = Math.min(46, 300 / n);
    for (let i = 0; i < n; i++) {
      const x = 20 + i * (w + 4);
      svg('rect', { x, y: 150, width: w, height: 30, rx: 5, class: 'f-a' }, s);
      svg('text', { x: x + w / 2, y: 170, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:10px', text: 'h' + (i + 1) }, s);
    }
    svg('text', { x: 20, y: 205, class: 'tm', style: 'font-size:11px', text: 'encoder states (source)' }, s);
    for (let j = 0; j < 4; j++) { svg('rect', { x: 470 + j * 44, y: 150, width: 40, height: 30, rx: 5, class: 'f-c' }, s); svg('text', { x: 490 + j * 44, y: 170, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:10px', text: 'y' + (j + 1) }, s); }
    svg('text', { x: 470, y: 205, class: 'tm', style: 'font-size:11px', text: 'decoder (target)' }, s);
    if (mode === 'fixed') {
      const lx = 20 + (n - 1) * (w + 4) + w / 2;
      TX.arrow(s, lx, 148, 395, 70, 'ba', 'var(--d)', 2);
      svg('rect', { x: 395, y: 45, width: 50, height: 50, rx: 8, style: 'fill:var(--d)' }, s);
      svg('text', { x: 420, y: 75, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:700', text: 'c' }, s);
      for (let j = 0; j < 4; j++) TX.arrow(s, 445, 70, 490 + j * 44, 148, 'ba', 'var(--d)', 1.5);
      svg('text', { x: 420, y: 30, 'text-anchor': 'middle', class: 't', style: 'fill:var(--d);font-size:12px;font-weight:600', text: `${n} words → 1 fixed vector (≈ ${(100 / n).toFixed(0)}% of its capacity per word)` }, s);
    } else {
      for (let i = 0; i < n; i++) for (let j = 0; j < 4; j++) {
        const x1 = 20 + i * (w + 4) + w / 2, x2 = 490 + j * 44;
        svg('path', { d: `M ${x1} 148 Q ${(x1 + x2) / 2} ${40 + j * 8} ${x2} 148`, fill: 'none', style: `stroke:var(--b);stroke-width:${j === 1 ? 1.8 : .8};opacity:${j === 1 ? .9 : .3}` }, s);
      }
      svg('text', { x: 330, y: 24, 'text-anchor': 'middle', class: 't', style: 'fill:var(--e);font-size:12px;font-weight:600', text: 'each target step reads all source states directly, at any length' }, s);
    }
  };
  Deck.seg('bSeg', v => { mode = v; if (document.getElementById('bN')) bott(); });
  Deck.bind(['bN'], bott);

  /* wiring diagram */
  (() => {
    const s = document.getElementById('wSvg');
    TX.arrowDefs(s, 'wa', 'var(--muted)'); TX.arrowDefs(s, 'wk', 'var(--a)'); TX.arrowDefs(s, 'wq', 'var(--c)');
    svg('rect', { x: 10, y: 20, width: 220, height: 260, rx: 12, style: 'fill:var(--a-soft);stroke:var(--a)' }, s);
    svg('text', { x: 120, y: 42, 'text-anchor': 'middle', class: 't', style: 'fill:var(--a);font-weight:700', text: 'Encoder × 6 (runs once)' }, s);
    TX.box(s, 40, 220, 160, 34, 'var(--faint)', 'source + PE');
    TX.box(s, 40, 160, 160, 40, 'var(--a)', 'encoder layers 1…6');
    TX.arrow(s, 120, 220, 120, 202, 'wa');
    TX.box(s, 40, 80, 160, 50, 'var(--a)', 'memory\nn × 512');
    TX.arrow(s, 120, 160, 120, 132, 'wa');
    svg('rect', { x: 290, y: 20, width: 360, height: 260, rx: 12, style: 'fill:var(--c-soft);stroke:var(--c)' }, s);
    svg('text', { x: 470, y: 42, 'text-anchor': 'middle', class: 't', style: 'fill:var(--c);font-weight:700', text: 'One decoder layer (× 6)' }, s);
    TX.box(s, 400, 225, 180, 34, 'var(--b)', 'masked self-attention + Add&Norm');
    TX.box(s, 400, 150, 180, 44, 'var(--b)', 'Encoder-decoder\nattention + Add&Norm');
    TX.box(s, 400, 70, 180, 34, '#3a8fd8', 'Feed-forward + Add&Norm');
    TX.arrow(s, 490, 225, 490, 196, 'wq', 'var(--c)', 2.5);
    svg('text', { x: 498, y: 214, class: 't', style: 'fill:var(--c);font-weight:700;font-size:12px', text: 'Q' }, s);
    TX.arrow(s, 490, 150, 490, 106, 'wa');
    svg('polyline', { points: '200,105 330,105 330,172 396,172', fill: 'none', style: 'stroke:var(--a);stroke-width:3', 'marker-end': 'url(#wk)' }, s);
    svg('text', { x: 338, y: 160, class: 't', style: 'fill:var(--a);font-weight:700;font-size:12px', text: 'K, V' }, s);
    svg('text', { x: 470, y: 272, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: 'the same memory feeds K, V in all 6 decoder layers' }, s);
  })();

  /* alignment */
  const SRC = ['The', 'cat', 'sat', 'on', 'the', 'mat'], TGT = ['Die', 'Katze', 'saß', 'auf', 'der', 'Matte'];
  const A = [
    [.80, .12, .02, .02, .02, .02], [.08, .84, .03, .01, .02, .02], [.02, .10, .82, .03, .01, .02],
    [.01, .02, .06, .85, .04, .02], [.02, .01, .02, .08, .80, .07], [.01, .02, .02, .03, .10, .82],
  ];
  let sel = 1;
  const align = () => {
    const s = clear(document.getElementById('aSvg'));
    const src = TX.tokens(s, SRC, { y: 20, h: 30, width: 380, font: 12, color: () => 'var(--a)', textColor: () => '#fff' });
    const tgt = TX.tokens(s, TGT, { y: 170, h: 30, width: 380, font: 12, click: true, color: i => i === sel ? 'var(--c)' : 'var(--c-soft)', textColor: i => i === sel ? '#fff' : 'var(--c)' });
    A[sel].forEach((w, j) => svg('line', { x1: tgt[sel].x, y1: 168, x2: src[j].x, y2: 52, style: `stroke:var(--b);stroke-width:${1 + 10 * w};opacity:${.2 + .8 * w}` }, s));
    svg('text', { x: 6, y: 112, class: 'tm', style: 'font-size:10.5px', text: 'K, V (source)  ↑   Q (target) ↓' }, s);
    const h = clear(document.getElementById('hSvg'));
    TX.heat(h, A, { x: 70, y: 70, cell: 40, rows: TGT, cols: SRC, rotate: true, fmt: v => (v * 100).toFixed(0), color: 'var(--b)' });
    svg('rect', { x: 69, y: 70 + sel * 40 - 1, width: 6 * 40 + 1, height: 40, style: 'fill:none;stroke:var(--ink);stroke-width:2' }, h);
  };
  document.getElementById('aSvg').addEventListener('click', e => { const g = e.target.closest('[data-tok]'); if (g && g.getAttribute('data-tok') !== null && +g.querySelector('rect').getAttribute('y') > 100) { sel = +g.dataset.tok; align(); } });
  align();
})();
