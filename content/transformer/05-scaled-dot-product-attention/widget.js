(() => {
  const { svg, clear } = Deck;

  /* saturation demo */
  let scaled = false, seed = 11;
  const bars = (s, vals, o) => {
    clear(s);
    const n = vals.length, bw = 300 / n, mid = o.signed ? 100 : 180, sc = o.signed ? 80 / o.max : 160 / o.max;
    if (o.signed) svg('line', { x1: 10, x2: 310, y1: mid, y2: mid, class: 'ln' }, s);
    vals.forEach((v, i) => {
      const h = Math.abs(v) * sc, y = o.signed ? (v >= 0 ? mid - h : mid) : mid - h;
      svg('rect', { x: 12 + i * bw, y, width: bw - 6, height: Math.max(1, h), rx: 3, style: `fill:${o.color(v, i)}` }, s);
      svg('text', { x: 12 + i * bw + (bw - 6) / 2, y: o.signed ? (v >= 0 ? y - 4 : y + h + 12) : y - 4, 'text-anchor': 'middle', class: 'tm tc', style: 'font-size:9.5px', text: o.fmt(v) }, s);
    });
  };
  const demo = () => {
    const dk = Math.pow(2, Deck.val('pD')); Deck.out('pDo', dk);
    const r = TX.rng(seed), q = [...Array(dk)].map(() => TX.randn(r)), ks = [...Array(8)].map(() => [...Array(dk)].map(() => TX.randn(r)));
    let sc = ks.map(k => TX.dot(q, k)); if (scaled) sc = sc.map(x => x / Math.sqrt(dk));
    const p = TX.softmax(sc), mx = Math.max(...sc.map(Math.abs), 1);
    bars(document.getElementById('pScores'), sc, { signed: true, max: mx, color: v => v >= 0 ? 'var(--a)' : 'var(--d)', fmt: v => v.toFixed(1) });
    bars(document.getElementById('pSoft'), p, { max: 1, color: (v) => v > .9 ? 'var(--d)' : 'var(--b)', fmt: v => (v * 100).toFixed(0) + '%' });
    const theoryStd = scaled ? 1 : Math.sqrt(dk);
    Deck.out('pStd', `≈ ${theoryStd.toFixed(1)}`);
    const pm = Math.max(...p), g = Math.max(...p.map(x => x * (1 - x)));
    Deck.out('pMax', (pm * 100).toFixed(1) + '%'); Deck.out('pGrad', g.toFixed(3));
    document.getElementById('pMax').style.color = pm > .9 ? 'var(--d)' : 'var(--e)';
    document.getElementById('pGrad').style.color = g < .05 ? 'var(--d)' : 'var(--e)';
  };
  Deck.seg('pScale', v => { scaled = v === '1'; if (document.getElementById('pD')) demo(); });
  document.getElementById('pResample').onclick = () => { seed++; demo(); };
  Deck.bind(['pD'], demo);

  /* equation stepper */
  const r = TX.rng(5), R1 = M => M.map(row => row.map(x => Math.round(x * 10) / 10));
  const Q = R1(TX.randMat(4, 4, r)), K = R1(TX.randMat(4, 4, r)), V = R1(TX.randMat(4, 4, r));
  const S = TX.matMul(Q, TX.T(K)), Ss = S.map(row => row.map(x => x / 2)), A = Ss.map(TX.softmax), O = TX.matMul(A, V);
  const toks = ['t1', 't2', 't3', 't4'];
  const STEPS = [
    ['1 · Q and K', [[Q, 'Q (n × d_k)', 'var(--c)'], [TX.T(K), 'Kᵀ (d_k × n)', 'var(--b)']], 'Each row of Q is one token\'s query, and each column of Kᵀ is one token\'s key.'],
    ['2 · QKᵀ', [[S, 'QKᵀ scores (n × n)', 'var(--b)']], 'Entry (i, j) = q<sub>i</sub>·k<sub>j</sub>: how compatible token i\'s query is with token j\'s key. Every pair in one matrix multiplication.'],
    ['3 · ÷ √d_k', [[Ss, 'QKᵀ / √4 = QKᵀ / 2', 'var(--b)']], 'Scale by 1/√d<sub>k</sub> (here √4 = 2) so the scores keep about unit variance whatever the dimension.'],
    ['4 · softmax', [[A, 'softmax by row: weights A', 'var(--e)']], 'Softmax along each row turns scores into positive weights that <b>sum to 1</b> across the keys: token i\'s attention distribution.'],
    ['5 · × V', [[A, 'A', 'var(--e)'], [V, 'V (n × d_v)', 'var(--a)'], [O, 'output = AV', 'var(--a)']], 'Each output row is a weighted average of the value rows, using that row\'s attention weights. Shape n × d<sub>v</sub>.'],
  ];
  const st = document.getElementById('eqSteps');
  st.innerHTML = STEPS.map((x, i) => `<button data-i="${i}">${x[0]}</button>`).join('');
  const pick = i => {
    Deck.$$('button', st).forEach(b => b.classList.toggle('on', +b.dataset.i === i));
    const s = clear(document.getElementById('eqSvg')), mats = STEPS[i][1];
    let x = 30;
    mats.forEach(([M, lab, c], k) => {
      svg('text', { x, y: 22, class: 't tc', style: `font-weight:700;fill:${c};font-size:12px`, text: lab }, s);
      TX.heat(s, M, { x, y: 50, cell: 40, color: c, neg: true, rows: k === 0 ? toks : null, cols: lab.startsWith('Kᵀ') || lab.includes('n × n') || lab.startsWith('QKᵀ') || lab.startsWith('softmax') || lab === 'A' ? toks : null });
      if (i === 3) A.forEach((row, ri) => svg('text', { x: x + 4 * 40 + 6, y: 50 + ri * 40 + 24, class: 'tm tc', style: 'font-size:10px', text: 'Σ=' + row.reduce((a, b) => a + b, 0).toFixed(2) }, s));
      x += 4 * 40 + (i === 3 ? 70 : 50);
      if (k < mats.length - 1) svg('text', { x: x - 34, y: 140, class: 't', style: 'font-size:20px;fill:var(--muted)', text: i === 4 && k === 1 ? '=' : i === 4 ? '×' : ' ' }, s);
    });
    document.getElementById('eqInfo').innerHTML = STEPS[i][2];
  };
  st.addEventListener('click', e => { const b = e.target.closest('button'); if (b) pick(+b.dataset.i); });
  pick(0);
})();
