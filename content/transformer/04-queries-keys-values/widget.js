(() => {
  const { svg, clear } = Deck;
  const T = ['animal', 'street', 'it', 'tired'];
  const X = [[1, 0, 0, 0.2], [0, 1, 0, 0], [0.1, 0.1, 1, 0], [0.3, 0, 0, 1]];
  const WQ = [[0, 0, 0.2], [0, 0, 0], [1.5, 0.3, 0], [1.0, 0, 0]];
  const WK = [[1.5, 0, 0], [0, 1.2, 0], [0, 0, 0.5], [0.2, 0, 0.8]];
  const WV = [[1, 0, 0], [0, 1, 0], [0, 0, 0.2], [0, 0, 1]];
  const Q = TX.matMul(X, WQ), K = TX.matMul(X, WK), V = TX.matMul(X, WV);
  const COL = ['var(--a)', 'var(--b)', 'var(--c)', 'var(--e)'];

  /* library metaphor */
  (() => {
    const s = document.getElementById('libSvg');
    TX.arrowDefs(s, 'la');
    TX.box(s, 20, 80, 150, 70, 'var(--c)', 'Query\n"who am I about?"', { fs: 12 });
    svg('text', { x: 95, y: 170, 'text-anchor': 'middle', class: 'tm', text: 'from "it"' }, s);
    [['animal', 'animate', 'var(--a)'], ['street', 'place', 'var(--b)'], ['tired', 'state', 'var(--e)']].forEach(([n, lab, c], i) => {
      const y = 20 + i * 70;
      TX.box(s, 290, y, 120, 50, 'var(--panel-2)', `Key: "${lab}"`, { text: 'var(--ink)', stroke: c });
      TX.box(s, 450, y, 180, 50, c, `Value: content of "${n}"`);
      TX.arrow(s, 172, 115, 286, y + 25, 'la', i === 0 ? 'var(--c)' : 'var(--line)', i === 0 ? 3 : 1.5);
    });
    svg('text', { x: 215, y: 62, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px;paint-order:stroke;stroke:var(--panel);stroke-width:5px;stroke-linejoin:round;', text: 'compare' }, s);
    svg('text', { x: 540, y: 222, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: 'take a blend, mostly from the best match' }, s);
  })();

  /* projections */
  Deck.seg('tokSeg', v => {
    const i = +v, s = clear(document.getElementById('projSvg'));
    TX.arrowDefs(s, 'pa');
    svg('text', { x: 20, y: 24, class: 't', style: 'font-weight:700', text: `x("${T[i]}")` }, s);
    TX.vec(s, X[i], { x: 20, y: 34, cell: 40, vals: true, vertical: true });
    ['animate', 'place', 'pronoun', 'state'].forEach((f, k) => svg('text', { x: 66, y: 58 + k * 40, class: 'tm', style: 'font-size:10.5px', text: f }, s));
    [[WQ, Q, 'W^Q → q', 'query', 'var(--c)'], [WK, K, 'W^K → k', 'key', 'var(--b)'], [WV, V, 'W^V → v', 'value', 'var(--a)']].forEach(([W, R, lab, name, c], r) => {
      const y = 20 + r * 76;
      TX.arrow(s, 130, 100, 228, y + 28, 'pa', c, 2);
      svg('text', { x: 236, y: y + 14, class: 't tc', style: `fill:${c};font-weight:700;font-size:12px`, text: lab }, s);
      TX.heat(s, W, { x: 236, y: y + 20, cell: 13, vals: false, color: c });
      TX.arrow(s, 290, y + 46, 330, y + 46, 'pa', c, 2);
      TX.vec(s, R[i], { x: 340, y: y + 30, cell: 42, vals: true, color: c });
      svg('text', { x: 480, y: y + 56, class: 't', style: `fill:${c};font-weight:600`, text: `${name}("${T[i]}")` }, s);
    });
  });

  /* matching */
  Deck.seg('qSeg', v => {
    const qi = +v, s = clear(document.getElementById('matchSvg'));
    const dk = 3, scores = K.map(k => TX.dot(Q[qi], k)), scaled = scores.map(x => x / Math.sqrt(dk)), w = TX.softmax(scaled);
    const out = [0, 1, 2].map(d => w.reduce((a, wj, j) => a + wj * V[j][d], 0));
    svg('text', { x: 10, y: 18, class: 't', style: 'font-weight:700', text: `q("${T[qi]}")` }, s);
    TX.vec(s, Q[qi], { x: 10, y: 26, cell: 38, vals: true, color: 'var(--c)' });
    const cols = ['key', 'q·k', '÷√3', 'softmax', 'value'];
    cols.forEach((c, k) => svg('text', { x: [70, 230, 300, 380, 520][k], y: 92, class: 'tm', style: 'font-size:11px;font-weight:600', text: c }, s));
    T.forEach((t, j) => {
      const y = 104 + j * 40;
      svg('text', { x: 10, y: y + 18, class: 't', style: 'font-size:12px;font-weight:600', text: t }, s);
      TX.vec(s, K[j], { x: 70, y, cell: 28, vals: true, color: 'var(--b)' });
      svg('text', { x: 230, y: y + 18, class: 't tc', style: 'font-size:12px', text: TX.f2(scores[j]) }, s);
      svg('text', { x: 300, y: y + 18, class: 't tc', style: 'font-size:12px', text: TX.f2(scaled[j]) }, s);
      svg('rect', { x: 380, y: y + 4, width: 110 * w[j], height: 18, rx: 3, style: `fill:${COL[j]}` }, s);
      svg('text', { x: 384 + 110 * w[j], y: y + 18, class: 't tc', style: 'font-size:11.5px;font-weight:700', text: (w[j] * 100).toFixed(0) + '%' }, s);
      TX.vec(s, V[j], { x: 520, y, cell: 28, vals: true, color: 'var(--a)' });
    });
    svg('text', { x: 380, y: 284, class: 't', style: 'font-weight:700', text: 'output = Σ weight × value =' }, s);
    TX.vec(s, out, { x: 556, y: 266, cell: 34, vals: true, color: 'var(--a)' });
  });

  /* matrix form */
  (() => {
    const s = document.getElementById('matSvg');
    const blocks = [[X, 'X', 'n × d_model', 'var(--faint)'], [Q, 'Q = XW^Q', 'n × d_k', 'var(--c)'], [K, 'K = XW^K', 'n × d_k', 'var(--b)'], [V, 'V = XW^V', 'n × d_v', 'var(--a)']];
    blocks.forEach(([M, lab, sh, c], b) => {
      const x = 20 + b * 160;
      svg('text', { x, y: 20, class: 't tc', style: `font-weight:700;fill:${c}`, text: lab }, s);
      TX.heat(s, M, { x, y: 32, cell: 30, vals: true, color: c, neg: true });
      svg('text', { x, y: 170, class: 'tm tc', style: 'font-size:11px', text: sh }, s);
      T.forEach((t, i) => b === 0 && svg('text', { x: x - 4, y: 52 + i * 30, 'text-anchor': 'end', class: 'tm', style: 'font-size:10px', text: '' }, s));
    });
    svg('text', { x: 20, y: 200, class: 't', text: 'rows = tokens (animal, street, it, tired).' }, s); svg('text', { x: 20, y: 218, class: 't', text: 'One matrix product QKᵀ scores every query against every key at once.' }, s);
  })();
})();
(() => {
  const s = document.getElementById('limSvg'), T = ['animal', 'street', 'it', 'tired'];
  const X = [[1, 0, 0, 0.2], [0, 1, 0, 0], [0.1, 0.1, 1, 0], [0.3, 0, 0, 1]];
  TX.heat(s, TX.matMul(X, TX.T(X)), { x: 80, y: 50, cell: 48, rows: T, cols: T, color: 'var(--b)', rotate: true });
  Deck.svg('text', { x: 4, y: 262, class: 'tm', style: 'font-size:11px', text: 'score = x_i · x_j (no projections)' }, s);
})();
