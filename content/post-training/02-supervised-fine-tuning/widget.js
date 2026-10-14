(() => {
  const { svg, clear, fmt } = Deck;

  const T = [['<bos>', 0], ['<system>', 0], ['you', 0], ['are', 0], ['helpful', 0], ['<eot>', 0], ['<user>', 0], ['what', 0], ['is', 0], ['2+2', 0], ['?', 0], ['<eot>', 0], ['<assistant>', 0], ['2+2', 1], ['is', 1], ['4.', 1], ['<eot>', 1], ['<user>', 0], ['and', 0], ['3+3', 0], ['?', 0], ['<eot>', 0], ['<assistant>', 0], ['6.', 1], ['<eot>', 1]];
  Deck.seg('mSeg', v => {
    const only = v === '1', box = document.getElementById('mToks'); box.innerHTML = '';
    T.forEach(([t, a]) => { const s = document.createElement('span'); const on = only ? a : 1; s.textContent = t; s.style.cssText = `padding:4px 8px;border-radius:6px;background:${on ? 'var(--a)' : 'var(--panel-2)'};color:${on ? '#fff' : 'var(--muted)'}`; box.appendChild(s); });
    const n = only ? T.filter(x => x[1]).length : T.length;
    document.getElementById('mOut').innerHTML = only ? `Loss on <b>${n} of ${T.length}</b> tokens: the two answers and their end-of-turn tokens. Role tokens and user text are context only.` : `Loss on all <b>${T.length}</b> tokens: the model is also trained to predict what the user types and the template itself.`;
  });
  let seed = 3; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const LENS = [...Array(20)].map(() => Math.round(150 + rnd() * 900));
  Deck.seg('kSeg', v => {
    const s = clear(document.getElementById('kSvg')), Lr = 2048, W = 600, x0 = 40;
    let rows;
    if (v === 'pad') { const m = Math.max(...LENS); rows = LENS.map(l => [[l, m]]); }
    else { rows = []; let cur = [], used = 0; LENS.forEach(l => { if (used + l > Lr) { rows.push(cur); cur = []; used = 0; } cur.push([l]); used += l; }); rows.push(cur); }
    const width = v === 'pad' ? Math.max(...LENS) : Lr, rh = Math.min(22, 240 / rows.length);
    let real = 0, total = 0;
    rows.forEach((row, i) => {
      let x = x0; const y = 10 + i * rh;
      row.forEach(([l], j) => { svg('rect', { x, y, width: l / width * W - 1, height: rh - 3, rx: 2, style: `fill:hsl(${(i * 3 + j) * 47 % 360},55%,55%)` }, s); x += l / width * W; real += l; });
      svg('rect', { x, y, width: Math.max(0, x0 + W - x), height: rh - 3, rx: 2, style: 'fill:var(--panel-2)' }, s);
      total += width;
    });
    document.getElementById('kOut').innerHTML = `${rows.length} rows × ${width.toLocaleString()} positions: <b>${(100 * real / total).toFixed(0)}%</b> are real tokens, the rest is padding (grey) that still costs compute.`;
  });

})();
