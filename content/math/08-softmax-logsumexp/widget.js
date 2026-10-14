(() => {
  const { svg, clear, fmt } = Deck;
  let bits = 16;
  const draw = () => {
    const z = Deck.val('xZ'), L = [z - 2, z - 1, z], lim = bits === 16 ? Math.log(65504) : 88.72; Deck.out('xZo', z.toFixed(1));
    const ex = L.map(v => v > lim ? Infinity : Math.exp(v)), S = ex.reduce((a, b) => a + b), naive = ex.map(v => v / S);
    const sumOver = S > (bits === 16 ? 65504 : 3.4e38);
    const st = L.map(v => Math.exp(v - z)), SS = st.reduce((a, b) => a + b), stable = st.map(v => v / SS);
    const bad = naive.some(v => !isFinite(v) || isNaN(v)) || sumOver;
    Deck.hbars(document.getElementById('xN'), naive.map((v, i) => ({ label: 'z' + (i + 1), value: isFinite(v) && !sumOver ? v : 0, color: bad ? 'var(--d)' : 'var(--a)', text: bad ? 'NaN' : v.toFixed(3) })), { max: 1 });
    Deck.hbars(document.getElementById('xS'), stable.map((v, i) => ({ label: 'z' + (i + 1), value: v, color: 'var(--e)', text: v.toFixed(3) })), { max: 1 });
    document.getElementById('xOut').innerHTML = bad ? `<b>Naive FP${bits} fails</b>: exp(${z.toFixed(1)}) ${z > lim ? 'overflows to ∞' : 'is finite but the sum overflows'}, giving NaN. The stable version is unaffected.` : `Both agree. Naive FP${bits} survives while the largest logit stays below ≈ ${lim.toFixed(2)}${bits === 16 ? ' (and the sum below 65,504)' : ''}.`;
  };
  Deck.bind(['xZ'], draw); Deck.seg('xSeg', v => { bits = +v; draw(); });
  const Z = [1.2, 0.3, 2.5, -0.4, 3.1, 1.0, 0.2, 4.0, 2.2, -1.0, 3.5, 0.7]; let blk = 0, m = -Infinity, d = 0;
  const odraw = () => {
    const s = clear(document.getElementById('oSvg')), w = 48;
    Z.forEach((v, i) => { const done = i < blk * 3, cur = i >= (blk - 1) * 3 && i < blk * 3;
      svg('rect', { x: 40 + i * w, y: 20, width: w - 4, height: 40, rx: 6, style: `fill:${cur ? 'var(--b)' : done ? 'var(--a)' : 'var(--panel-2)'}` }, s);
      svg('text', { x: 40 + i * w + (w - 4) / 2, y: 45, 'text-anchor': 'middle', class: 't', style: done ? 'fill:#fff' : '', text: v.toFixed(1) }, s); });
    svg('text', { x: 40, y: 100, class: 't', text: `running max m = ${isFinite(m) ? m.toFixed(2) : '−∞'}` }, s);
    svg('text', { x: 40, y: 130, class: 't', text: `running sum d = ${d.toFixed(4)}` }, s);
    const full = Z.reduce((a, v) => a + Math.exp(v - Math.max(...Z)), 0);
    svg('text', { x: 360, y: 115, class: 'tm', text: `two-pass reference: m = ${Math.max(...Z)}, d = ${full.toFixed(4)}` }, s);
  };
  document.getElementById('oNext').addEventListener('click', () => {
    if (blk * 3 >= Z.length) return; const b = Z.slice(blk * 3, blk * 3 + 3), m2 = Math.max(m, ...b), old = m;
    d = d * Math.exp(m - m2) + b.reduce((a, v) => a + Math.exp(v - m2), 0); m = m2; blk++; odraw();
    document.getElementById('oOut').innerHTML = blk * 3 >= Z.length ? 'Done: one pass gives exactly the two-pass max and sum.' : (m2 > old && isFinite(old) ? `The max rose from ${old} to ${m2}: the old sum was multiplied by e^(${old} − ${m2}) = ${Math.exp(old - m2).toFixed(4)}.` : 'Max unchanged or first block: just add the new terms.');
  });
  document.getElementById('oReset').addEventListener('click', () => { blk = 0; m = -Infinity; d = 0; odraw(); document.getElementById('oOut').innerHTML = 'Press "next block".'; });
  odraw(); document.getElementById('oOut').innerHTML = 'Press "next block".';
})();
