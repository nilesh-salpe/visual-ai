(() => {
  const { svg, clear, fmt } = Deck;
  const N = 4; let step = 0; const done = new Set();
  const cdraw = () => {
    const s = clear(document.getElementById('cSvg')), c = 46, x0 = 112, y0 = 20;
    for (let q = 0; q < N; q++) for (let k = 0; k < N; k++) {
      const future = k > q, has = (q - k + N) % N <= step && !future, now = (q - step + N * 4) % N === k && !future && step < N;
      svg('rect', { x: x0 + k * c, y: y0 + q * c, width: c - 4, height: c - 4, rx: 5, style: `fill:${future ? 'var(--panel-2)' : now ? 'var(--b)' : has ? 'var(--a)' : 'var(--panel)'};stroke:var(--line)` }, s);
    }
    for (let i = 0; i < N; i++) { svg('text', { x: x0 - 8, y: y0 + i * c + 27, 'text-anchor': 'end', class: 'tm', text: 'GPU ' + i + ' (Q' + i + ')' }, s); svg('text', { x: x0 + i * c + 21, y: y0 + N * c + 14, 'text-anchor': 'middle', class: 'tm', text: 'K/V' + i }, s); }
    for (let i = 0; i < N; i++) { const kv = (i - Math.min(step, N - 1) + N * 4) % N; svg('rect', { x: 345 + i * 75, y: 80, width: 65, height: 40, rx: 8, class: 'f-c' }, s); svg('text', { x: 377 + i * 75, y: 98, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11px', text: 'GPU ' + i }, s); svg('text', { x: 377 + i * 75, y: 113, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11px', text: 'holds K/V' + kv }, s); }
    svg('text', { x: 495, y: 150, 'text-anchor': 'middle', class: 'tm', text: 'K/V blocks move one GPU to the right each step' }, s);
    document.getElementById('cOut').innerHTML = step >= N ? 'Done: every GPU has attended to all earlier K/V blocks (teal); masked future blocks were skipped.' : `Step ${step + 1} of ${N}: each GPU computes its queries against the K/V block it currently holds (orange) if it isn't in the future, while passing it on.`;
  };
  document.getElementById('cNext').addEventListener('click', () => { if (step < N) step++; cdraw(); });
  document.getElementById('cReset').addEventListener('click', () => { step = 0; cdraw(); });
  cdraw();
  let bal = 0;
  const ldraw = () => {
    const n = Deck.val('lN'); Deck.out('lNo', n);
    const work = [...Array(n)].map((_, i) => bal ? (i + 1) + (2 * n - i) : (2 * i + 1) + (2 * i + 2));
    Deck.hbars(document.getElementById('lBars'), work.map((w, i) => ({ label: 'GPU ' + i, value: w, color: w === Math.max(...work) ? 'var(--d)' : 'var(--a)', text: w + ' blocks' })), { max: Math.max(...work) * 1.05 });
  };
  Deck.bind(['lN'], ldraw); Deck.seg('lSeg', v => { bal = +v; ldraw(); });
})();
