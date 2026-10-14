(() => {
  const { svg, clear } = Deck;
  const TOK = ['The', 'animal', "didn't", 'cross', 'the', 'street', 'because', 'it', 'was', 'too', 'tired'];
  const norm = w => { const s = w.reduce((a, b) => a + b, 0); return w.map(x => x / s); };
  const oneHotish = (n, peaks) => { const w = Array(n).fill(0.01); peaks.forEach(([j, v]) => w[j] += v); return norm(w); };

  /* problem: blend vs separate */
  Deck.seg('pSeg', v => {
    const s = clear(document.getElementById('pSvg'));
    const pos = TX.tokens(s, TOK, { y: 190, h: 30, font: 12, sel: 7 });
    if (v === '1') {
      const w = oneHotish(11, [[1, .3], [10, .3], [8, .3]]);
      TX.arcs(s, pos, 7, w, { color: 'var(--faint)', maxH: 90, norm: true });
      svg('text', { x: 330, y: 22, 'text-anchor': 'middle', class: 't', style: 'font-size:12.5px', text: 'one distribution: ~1/3 each, so no single relationship is sharp' }, s);
    } else {
      [[1, 'var(--a)'], [10, 'var(--b)'], [8, 'var(--c)']].forEach(([j, c]) => TX.arcs(s, pos, 7, oneHotish(11, [[j, .9]]), { color: c, maxH: 90, min: .2 }));
      svg('text', { x: 330, y: 22, 'text-anchor': 'middle', class: 't', style: 'font-size:12.5px', text: 'three heads, each with its own sharp distribution' }, s);
    }
  });

  /* architecture */
  const PAT = [
    ['previous token', i => oneHotish(11, [[Math.max(0, i - 1), 1]])],
    ['next token', i => oneHotish(11, [[Math.min(10, i + 1), 1]])],
    ['pronoun → referent', i => i === 7 ? oneHotish(11, [[1, 1]]) : oneHotish(11, [[i, .6]])],
    ['subject ↔ predicate', i => i === 7 || i === 1 ? oneHotish(11, [[10, 1]]) : oneHotish(11, [[i, .6]])],
    ['verb → its arguments', i => i === 3 || i === 7 ? oneHotish(11, [[1, .5], [5, .5]]) : oneHotish(11, [[3, .5]])],
    ['broad average', () => Array(11).fill(1 / 11)],
    ['itself', i => oneHotish(11, [[i, 1]])],
    ['clause boundary', () => oneHotish(11, [[6, 1]])],
  ];
  let head = 2;
  const drawArch = () => {
    const s = clear(document.getElementById('mhSvg'));
    TX.arrowDefs(s, 'ma');
    TX.box(s, 10, 110, 90, 50, 'var(--faint)', 'X\nn × 512');
    for (let h = 0; h < 8; h++) {
      const y = 8 + h * 32, on = h === head;
      TX.arrow(s, 102, 135, 140, y + 13, 'ma', 'var(--line)', 1.2);
      const g = TX.box(s, 145, y, 160, 26, TX.HEADS[h], `head ${h + 1} · Q,K,V → 64`, { attrs: { 'data-h': h }, fs: 11, stroke: on ? 'var(--ink)' : null });
      if (on) g.firstChild.setAttribute('style', g.firstChild.getAttribute('style') + 'stroke-width:3;');
      svg('rect', { x: 330, y: y + 2, width: 64, height: 22, rx: 3, 'data-h': h, style: `fill:${TX.HEADS[h]};opacity:${on ? 1 : .55}` }, s);
      svg('text', { x: 362, y: y + 17, 'text-anchor': 'middle', class: 't tc', style: 'fill:#fff;font-size:10px;pointer-events:none', text: 'n×64' }, s);
      TX.arrow(s, 307, y + 13, 326, y + 13, 'ma', 'var(--muted)', 1.2);
    }
    svg('text', { x: 225, y: 268, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: 'attention per head' }, s);
    svg('text', { x: 405, y: 268, class: 'tm', style: 'font-size:11px', text: 'concat → n × 512' }, s);
    TX.arrow(s, 398, 135, 440, 135, 'ma', 'var(--muted)', 2);
    TX.box(s, 445, 110, 90, 50, 'var(--b)', 'W^O\n512 × 512');
    TX.arrow(s, 537, 135, 565, 135, 'ma', 'var(--muted)', 2);
    TX.box(s, 570, 110, 80, 50, 'var(--a)', 'output\nn × 512');
    const hs = clear(document.getElementById('headSvg'));
    const pos = TX.tokens(hs, TOK, { y: 110, h: 30, font: 12, sel: 7 });
    TX.arcs(hs, pos, 7, PAT[head][1](7), { color: TX.HEADS[head], maxH: 70, norm: true, min: .03 });
    document.getElementById('headCap').innerHTML = `<b style="color:${TX.HEADS[head]}">Head ${head + 1}</b>: a "${PAT[head][0]}" pattern, shown from the token "it".`;
  };
  document.getElementById('mhSvg').addEventListener('click', e => { const g = e.target.closest('[data-h]'); if (g) { head = +g.dataset.h; drawArch(); } });
  drawArch();

  /* Table 3 (A) */
  const T3A = { 1: [512, 5.29, 24.9], 4: [128, 5.00, 25.5], 8: [64, 4.92, 25.8], 16: [32, 4.91, 25.8], 32: [16, 5.01, 25.4] };
  Deck.seg('hSeg', v => {
    const h = +v, [dk] = T3A[h];
    const s = clear(document.getElementById('splitSvg'));
    const w = 620 / h;
    for (let i = 0; i < h; i++) svg('rect', { x: 20 + i * w, y: 10, width: Math.max(1, w - (h > 16 ? 1 : 3)), height: 30, rx: 3, style: `fill:${TX.HEADS[i % 8]}` }, s);
    svg('text', { x: 330, y: 62, 'text-anchor': 'middle', class: 't tc', style: 'font-size:12px', text: `${h} head${h > 1 ? 's' : ''} × d_k = ${dk}  =  512 dims (constant compute)` }, s);
    const keys = [1, 4, 8, 16, 32];
    Deck.hbars(document.getElementById('bleuBars'), keys.map(k => ({ label: `h = ${k} (d_k ${T3A[k][0]})`, value: T3A[k][2] - 24, color: k === h ? 'var(--a)' : 'var(--line)', text: T3A[k][2].toFixed(1) })), { max: 2 });
    Deck.hbars(document.getElementById('pplBars'), keys.map(k => ({ label: `h = ${k}`, value: T3A[k][1] - 4.8, color: k === h ? 'var(--b)' : 'var(--line)', text: T3A[k][1].toFixed(2) })), { max: .5 });
  });
})();
