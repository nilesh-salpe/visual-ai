(() => {
  const { svg, clear, fmt } = Deck;
  const TOK = ['The', 'animal', "didn't", 'cross', 'the', 'street', 'because', 'it', 'was', 'tired'];
  const n = TOK.length;

  /* RNN unroll */
  let t = 0, timer = null;
  const drawRNN = () => {
    const s = clear(document.getElementById('rSvg'));
    TX.arrowDefs(s, 'ar1');
    const pos = TX.tokens(s, TOK, { y: 200, h: 28, font: 12 });
    pos.forEach((p, i) => {
      const done = i < t, cur = i === t - 1;
      TX.arrow(s, p.x, 198, p.x, 132, 'ar1', 'var(--line)', 1.5);
      svg('rect', { x: p.x - 26, y: 88, width: 52, height: 42, rx: 8, style: `fill:${done ? 'var(--a)' : 'var(--panel-2)'};stroke:${cur ? 'var(--ink)' : 'var(--line)'};stroke-width:${cur ? 2.5 : 1}` }, s);
      svg('text', { x: p.x, y: 114, 'text-anchor': 'middle', class: 't tc', style: `fill:${done ? '#fff' : 'var(--muted)'};font-size:12px;font-weight:600`, text: 'h' + (i + 1) }, s);
      if (i) TX.arrow(s, pos[i - 1].x + 26, 109, p.x - 28, 109, 'ar1', done ? 'var(--a)' : 'var(--line)', 2);
    });
    svg('text', { x: 10, y: 22, class: 'tm', style: 'font-size:11px', text: '10 hardware lanes:' }, s);
    for (let k = 0; k < n; k++) svg('rect', { x: 120 + k * 52, y: 10, width: 46, height: 18, rx: 3, style: `fill:${t > 0 && k === 0 && t <= n ? 'var(--b)' : 'var(--panel-2)'}` }, s);
    svg('text', { x: 120, y: 48, class: 'tm', style: 'font-size:11px', text: t === 0 ? 'press Play' : t <= n ? `step ${t}: only 1 lane can work; the other 9 are idle` : '' }, s);
    Deck.out('rOut', `sequential steps so far: ${Math.min(t, n)} / ${n}`);
  };
  const stop = () => { if (timer) { clearInterval(timer); timer = null; document.getElementById('rPlay').textContent = 'Play'; } };
  document.getElementById('rPlay').onclick = e => {
    if (timer) return stop();
    if (t >= n) t = 0;
    e.target.textContent = 'Pause';
    timer = setInterval(() => { t++; drawRNN(); if (t >= n) stop(); }, 500);
  };
  document.getElementById('rReset').onclick = () => { stop(); t = 0; drawRNN(); };
  drawRNN();
  Deck.enter('s-rnn', () => stop);

  /* path length */
  let pair = [1, 7];
  const drawPath = () => {
    const k = Deck.val('pK'); Deck.out('pKo', k.toFixed(2));
    const s = clear(document.getElementById('pSvg'));
    TX.arrowDefs(s, 'ar2', 'var(--d)');
    const [a, b] = [Math.min(...pair), Math.max(...pair)];
    const pos = TX.tokens(s, TOK, { y: 140, h: 30, font: 12, click: true, color: i => pair.includes(i) ? 'var(--a)' : 'var(--panel-2)', textColor: i => pair.includes(i) ? '#fff' : 'var(--ink)' });
    for (let i = a; i < b; i++) {
      const strength = Math.pow(k, i - a + 1);
      TX.arrow(s, pos[i].x + 10, 100, pos[i + 1].x - 12, 100, 'ar2', 'var(--d)', 1 + 6 * strength);
      svg('text', { x: (pos[i].x + pos[i + 1].x) / 2, y: 76, 'text-anchor': 'middle', class: 'tm tc', style: 'font-size:10px', text: (strength * 100).toFixed(0) + '%' }, s);
    }
    pos.forEach((p, i) => svg('circle', { cx: p.x, cy: 100, r: 9, style: `fill:${i >= a && i <= b ? 'var(--a)' : 'var(--panel-2)'};stroke:var(--line)` }, s));
    svg('text', { x: 330, y: 30, 'text-anchor': 'middle', class: 't', style: 'font-size:12.5px', text: `"${TOK[a]}" → "${TOK[b]}" must pass through ${b - a} recurrent steps` }, s);
    Deck.out('pHops', b - a);
    Deck.out('pSig', (100 * Math.pow(k, b - a)).toFixed(0) + '%');
  };
  document.getElementById('pSvg').addEventListener('click', e => {
    const g = e.target.closest('[data-tok]'); if (!g) return;
    const i = +g.dataset.tok; if (pair.includes(i)) return;
    pair = [pair[1], i]; drawPath();
  });
  Deck.bind(['pK'], drawPath);

  /* RNN vs self-attention */
  Deck.seg('saSeg', v => {
    const s = clear(document.getElementById('saSvg'));
    TX.arrowDefs(s, 'ar3', 'var(--a)');
    const pos = TX.tokens(s, TOK, { y: 190, h: 30, font: 12 });
    if (v === 'sa') {
      for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {
        const a = pos[i], b = pos[j], h = 14 + (j - i) * 14;
        svg('path', { d: `M ${a.x} 188 Q ${(a.x + b.x) / 2} ${188 - h * 1.5} ${b.x} 188`, fill: 'none', style: `stroke:var(--a);stroke-width:1.2;opacity:${i === 1 || j === 7 ? .9 : .25}` }, s);
      }
      svg('text', { x: 330, y: 16, 'text-anchor': 'middle', class: 't', style: 'font-size:12.5px', text: 'every pair connected directly (1 hop); all 10 outputs computed in the same step' }, s);
    } else {
      pos.forEach((p, i) => { if (i) TX.arrow(s, pos[i - 1].x + 14, 150, p.x - 16, 150, 'ar3', 'var(--a)', 2); svg('circle', { cx: p.x, cy: 150, r: 11, class: 'f-a' }, s); });
      svg('text', { x: 330, y: 110, 'text-anchor': 'middle', class: 't', style: 'font-size:12.5px', text: 'a chain: "animal" reaches "it" only after 6 hops; one position per step' }, s);
    }
    Deck.out('saSeq', v === 'sa' ? 'O(1)' : 'O(n)'); Deck.out('saPath', v === 'sa' ? 'O(1)' : 'O(n)'); Deck.out('saLanes', v === 'sa' ? 'all n' : '1');
    ['saSeq', 'saPath'].forEach(id => document.getElementById(id).style.color = v === 'sa' ? 'var(--e)' : 'var(--d)');
  });

  /* cost */
  Deck.bind(['cN', 'cD', 'cK'], () => {
    const N = Math.round(Math.pow(10, Deck.val('cN'))), d = Math.pow(2, Deck.val('cD')), k = Deck.val('cK');
    Deck.out('cNo', N); Deck.out('cDo', d); Deck.out('cKo', k);
    const sa = N * N * d, rnn = N * d * d, conv = k * N * d * d;
    Deck.hbars(document.getElementById('cBars'), [
      { label: 'Self-attention n²·d', value: sa, color: sa <= rnn ? 'var(--e)' : 'var(--d)', text: fmt(sa) },
      { label: 'Recurrent n·d²', value: rnn, color: 'var(--a)', text: fmt(rnn) },
      { label: 'Convolutional k·n·d²', value: conv, color: 'var(--c)', text: fmt(conv) },
    ], { log: true });
    document.getElementById('cOut').innerHTML = N < d
      ? `<span class="em-e">n (${N}) &lt; d (${d})</span>: self-attention is ${(rnn / sa).toFixed(1)}× cheaper per layer than recurrence, and also fully parallel.`
      : `<span class="em-d">n (${N}) ≥ d (${d})</span>: self-attention costs ${(sa / rnn).toFixed(1)}× more per layer. The paper suggests restricting attention to a neighbourhood r for very long sequences (§4).`;
  });
})();
