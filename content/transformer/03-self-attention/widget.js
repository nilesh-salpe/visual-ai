(() => {
  const { svg, clear } = Deck;
  const base = ['The', 'animal', "didn't", 'cross', 'the', 'street', 'because', 'it', 'was', 'too'];
  const sent = v => [...base, v === 'wide' ? 'wide' : 'tired'];

  // Hand-made, clearly illustrative attention weights (rows normalized).
  const weights = (v, i) => {
    const n = 11, w = Array(n).fill(0.02);
    w[i] += 0.3;
    if (i > 0) w[i - 1] += 0.12;
    if (i < n - 1) w[i + 1] += 0.12;
    const ref = v === 'wide' ? 5 : 1;
    if (i === 7) { w[ref] += 0.75; w[10] += 0.15; }
    if (i === 10) { w[ref] += 0.45; w[7] += 0.2; }
    if (i === 3) { w[1] += 0.25; w[5] += 0.25; }
    if (i === 1) { w[3] += 0.15; }
    if (i === 5) { w[3] += 0.15; }
    const s = w.reduce((a, b) => a + b, 0);
    return w.map(x => x / s);
  };

  /* problem */
  (() => {
    const s = document.getElementById('probSvg');
    TX.arrowDefs(s, 'pa');
    const emb = [0.6, -0.3, 0.8, 0.1, -0.5, 0.4, 0.2, -0.7];
    [['tired', 20, 'var(--a)', 1], ['wide', 130, 'var(--b)', 5]].forEach(([v, y, col, ref]) => {
      const pos = TX.tokens(s, sent(v), { y, h: 30, width: 400, font: 11, color: i => i === 7 ? 'var(--ink)' : i === ref ? col : 'var(--panel-2)', textColor: i => i === 7 || i === ref ? '#fff' : 'var(--ink)' });
      TX.arrow(s, pos[7].x, y + 32, 470, y + 60, 'pa', 'var(--muted)', 1.5);
      TX.vec(s, emb, { x: 480, y: y + 50, cell: 20, label: '' });
      svg('text', { x: 480, y: y + 44, class: 'tm tc', style: 'font-size:11px', text: 'embedding("it")' }, s);
      svg('text', { x: 10, y: y + 52, class: 't', style: `fill:${col};font-size:12px;font-weight:600`, text: `"it" = the ${v === 'wide' ? 'street' : 'animal'}` }, s);
    });
    svg('text', { x: 560, y: 240, 'text-anchor': 'middle', class: 't', style: 'fill:var(--d);font-weight:700', text: 'identical vectors ✗' }, s);
  })();

  /* arcs */
  let variant = 'tired', sel = 7;
  const drawArcs = () => {
    const s = clear(document.getElementById('arcSvg')), toks = sent(variant);
    const w = weights(variant, sel);
    const pos = TX.tokens(s, toks, { y: 180, h: 32, font: 12, sel, click: true, index: true });
    TX.arcs(s, pos, sel, w, { color: variant === 'wide' ? 'var(--b)' : 'var(--a)', maxH: 95, min: 0.03 });
    pos.forEach((p, j) => svg('text', { x: p.x, y: 174, 'text-anchor': 'middle', class: 'tm tc', style: `font-size:10px;font-weight:${w[j] > .15 ? 700 : 400}`, text: (w[j] * 100).toFixed(0) + '%' }, s));
    Deck.out('mixTitle', `new representation of "${toks[sel]}" = Σ weight × (value of token)`);
    const top = w.map((x, j) => [x, j]).sort((a, b) => b[0] - a[0]).slice(0, 5);
    Deck.hbars(document.getElementById('mixBars'), top.map(([x, j]) => ({ label: `"${toks[j]}"`, value: x, color: j === sel ? 'var(--faint)' : (variant === 'wide' ? 'var(--b)' : 'var(--a)'), text: (x * 100).toFixed(0) + '%' })), { max: 1 });
  };
  document.getElementById('arcSvg').addEventListener('click', e => { const g = e.target.closest('[data-tok]'); if (g) { sel = +g.dataset.tok; drawArcs(); } });
  Deck.seg('vSeg', v => { variant = v; drawArcs(); drawMat(); });

  /* matrix */
  function drawMat() {
    const s = clear(document.getElementById('matSvg')), toks = sent(variant);
    const M = toks.map((_, i) => weights(variant, i));
    TX.heat(s, M, { x: 80, y: 80, cell: 34, rows: toks, cols: toks, rotate: true, fmt: v => (v * 100).toFixed(0), color: variant === 'wide' ? 'var(--b)' : 'var(--a)' });
    M.forEach((row, i) => svg('rect', { x: 78, y: 80 + i * 34 - 1, width: 11 * 34 + 2, height: 34, 'data-row': i, style: 'fill:transparent;stroke:transparent' }, s));
    svg('text', { x: 6, y: 66, class: 'tm', style: 'font-size:10.5px', text: 'query ↓  key →' }, s);
    s.onmousemove = e => {
      const r = e.target.closest('[data-row]'); if (!r) return;
      s.querySelectorAll('[data-row]').forEach(x => x.style.stroke = 'transparent');
      r.style.stroke = 'var(--ink)'; r.style.strokeWidth = 2;
      const i = +r.dataset.row, top = M[i].map((x, j) => [x, j]).sort((a, b) => b[0] - a[0]).slice(0, 3);
      document.getElementById('matInfo').innerHTML = `<b>Row "${toks[i]}"</b>: attends most to ${top.map(([x, j]) => `"${toks[j]}" (${(x * 100).toFixed(0)}%)`).join(', ')}. Row sum = ${(M[i].reduce((a, b) => a + b, 0) * 100).toFixed(0)}%.`;
    };
  }

  /* paper figures (schematic) */
  const F4 = ['The', 'Law', 'will', 'never', 'be', 'perfect', ',', 'but', 'its', 'application', 'should', 'be', 'just', '-', 'this', 'is', 'what', 'we', 'are', 'missing', ',', 'in', 'my', 'opinion', '.', '<EOS>'];
  const F3 = ['It', 'is', 'in', 'this', 'spirit', 'that', 'a', 'majority', 'of', 'American', 'governments', 'have', 'passed', 'new', 'laws', 'since', '2009', 'making', 'the', 'registration', 'or', 'voting', 'process', 'more', 'difficult', '.', '<EOS>'];
  Deck.seg('figSeg', v => {
    const s = clear(document.getElementById('realSvg'));
    const toks = v === 'f4' ? F4 : F3, n = toks.length, W = 640, step = W / n;
    const X = i => 12 + i * step + step / 2;
    const src = v === 'f4' ? 8 : 17;
    const links = v === 'f4' ? [[1, TX.HEADS[2], 'head 5'], [9, TX.HEADS[1], 'head 6']] : [[23, TX.HEADS[0], 'several heads'], [24, TX.HEADS[4], 'several heads']];
    links.forEach(([j, c], k) => svg('line', { x1: X(src), y1: 70, x2: X(j), y2: 160, style: `stroke:${c};stroke-width:${v === 'f3' ? 4 - k : 4};opacity:.85` }, s));
    toks.forEach((t, i) => {
      const hl = i === src || links.some(l => l[0] === i);
      [[60, 'end'], [170, 'start']].forEach(([y, anchor]) =>
        svg('text', { x: X(i), y, 'text-anchor': anchor, transform: `rotate(-90 ${X(i)} ${y})`, class: 't', style: `font-size:10.5px;font-weight:${hl ? 700 : 400};fill:${hl ? 'var(--ink)' : 'var(--muted)'}`, text: t }, s));
    });
    s.setAttribute('viewBox', '0 0 660 240');
    document.getElementById('realCap').innerHTML = v === 'f4'
      ? 'Figure 4: two heads in layer 5 of 6 "apparently involved in anaphora resolution". Attention from <b>its</b> is very sharp, pointing to <b>Law</b> (head 5) and <b>application</b> (head 6).'
      : 'Figure 3: many heads attend from <b>making</b> to the distant <b>more difficult</b>, completing the phrase "making … more difficult", a long-distance dependency handled in one hop.';
  });
})();
