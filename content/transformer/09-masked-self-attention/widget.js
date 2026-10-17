(() => {
  const { svg, clear } = Deck;
  const IN = ['<s>', 'Die', 'Katze', 'saß', 'auf', 'der'];
  const OUT = ['Die', 'Katze', 'saß', 'auf', 'der', 'Matte'];

  /* cheating */
  let masked = false;
  const cheat = () => {
    const i = Deck.val('cI'); Deck.out('cIo', i);
    const s = clear(document.getElementById('cSvg'));
    TX.arrowDefs(s, 'ca', 'var(--muted)');
    svg('text', { x: 10, y: 34, class: 'tm', style: 'font-size:11px', text: 'predict' }, s);
    svg('text', { x: 10, y: 196, class: 'tm', style: 'font-size:11px', text: 'decoder input' }, s);
    const out = TX.tokens(s, OUT, { x0: 100, width: 550, y: 14, h: 30, color: j => j === i ? 'var(--e)' : 'var(--panel-2)', textColor: j => j === i ? '#fff' : 'var(--muted)' });
    const inp = TX.tokens(s, IN, { x0: 100, width: 550, y: 176, h: 30, color: j => j === i ? 'var(--c)' : (j > i && !masked ? 'var(--d-soft)' : 'var(--c-soft)'), textColor: j => j === i ? '#fff' : 'var(--c)' });
    TX.arrow(s, inp[i].x, 174, out[i].x, 48, 'ca', 'var(--e)', 2.5);
    IN.forEach((_, j) => {
      if (j === i) return;
      const future = j > i;
      if (future && masked) return;
      svg('path', { d: `M ${inp[j].x} 174 Q ${(inp[j].x + inp[i].x) / 2} ${future ? 95 : 120} ${inp[i].x + (j < i ? -6 : 6)} 120`, fill: 'none', style: `stroke:${future ? 'var(--d)' : 'var(--c)'};stroke-width:${future && j === i + 1 ? 4 : 2};opacity:${future ? .9 : .6}` }, s);
    });
    const leak = !masked && i < 5;
    document.getElementById('cOut').innerHTML = masked
      ? `<span class="em-e">Position ${i} sees only ${IN.slice(0, i + 1).map(t => `"${t}"`).join(', ')}</span> and must genuinely predict "${OUT[i]}".`
      : leak ? `<span class="em-d">Leak:</span> to predict "${OUT[i]}", position ${i} can read input "${IN[i + 1]}" at position ${i + 1}, which <b>is the answer</b>.`
      : `Last position: nothing to its right, but every earlier position leaks.`;
  };
  Deck.seg('cSeg', v => { masked = v === '1'; if (document.getElementById('cI')) cheat(); });
  Deck.bind(['cI'], cheat);

  /* mask matrix */
  Deck.bind(['mI'], () => {
    const i = Deck.val('mI'); Deck.out('mIo', i);
    const s = clear(document.getElementById('mSvg'));
    const M = IN.map((_, r) => IN.map((_, c) => c <= r ? 1 : -Infinity));
    TX.heat(s, M, { x: 80, y: 70, cell: 40, rows: IN, cols: IN, rotate: true, fmt: () => '✓', color: 'var(--e)', max: 1 });
    svg('rect', { x: 79, y: 70 + i * 40 - 1, width: 6 * 40 + 1, height: 40, style: 'fill:none;stroke:var(--ink);stroke-width:2.5' }, s);
    svg('text', { x: 6, y: 56, class: 'tm', style: 'font-size:10.5px', text: 'query ↓  key →' }, s);
    document.getElementById('mInfo').innerHTML = `<b>Row ${i} (input "${IN[i]}")</b> attends to ${i + 1} position${i ? 's' : ''}: ${IN.slice(0, i + 1).map(t => `"${t}"`).join(', ')}.<br><br>It predicts <b>"${OUT[i]}"</b>. Columns ${i + 1}–5 are set to −∞, so they get weight 0.`;
  });

  /* numeric */
  const r = TX.rng(9), n = 5;
  const S = [...Array(n)].map(() => [...Array(n)].map(() => Math.round(TX.randn(r) * 15) / 10));
  const Mk = S.map((row, i) => row.map((v, j) => j <= i ? v : -Infinity));
  const P = Mk.map(TX.softmax);
  const toks = IN.slice(0, n);
  const NS = [
    [S, 'scores (already ÷ √d_k)', 'var(--b)', true, 'Every query against every key, including future positions above the diagonal.'],
    [Mk, 'masked scores', 'var(--b)', true, 'Every entry above the diagonal (key position j &gt; query position i) is replaced by −∞.'],
    [P, 'softmax weights', 'var(--e)', false, 'e<sup>−∞</sup> = 0, so future positions get exactly zero weight. Each row still sums to 1 over the visible positions.'],
  ];
  const nst = document.getElementById('nSteps');
  const pickN = k => {
    Deck.$$('button', nst).forEach(b => b.classList.toggle('on', +b.dataset.i === k));
    const [M, lab, c, neg, txt] = NS[k], s = clear(document.getElementById('nSvg'));
    svg('text', { x: 220, y: 12, class: 't tc', style: `font-weight:700;fill:${c}`, text: lab }, s);
    TX.heat(s, M, { x: 220, y: 46, cell: 42, rows: toks, cols: toks, color: c, neg, fmt: v => k === 2 ? v.toFixed(2) : v.toFixed(1) });
    if (k === 2) P.forEach((row, i) => svg('text', { x: 220 + n * 42 + 8, y: 46 + i * 42 + 25, class: 'tm tc', style: 'font-size:10.5px', text: 'Σ = ' + row.reduce((a, b) => a + b, 0).toFixed(2) }, s));
    document.getElementById('nInfo').innerHTML = txt;
  };
  nst.addEventListener('click', e => { const b = e.target.closest('button'); if (b) pickN(+b.dataset.i); });
  pickN(0);
})();
