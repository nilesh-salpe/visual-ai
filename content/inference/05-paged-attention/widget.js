(() => {
  const { svg, clear, fmt } = Deck;

  class BM { constructor(n, bs) { this.bs = bs; this.free = [...Array(n).keys()].reverse(); this.ref = Array(n).fill(0); this.t = {}; this.k = {}; this.owner = Array(n).fill(null); }
    al(o) { const b = this.free.pop(); this.ref[b] = 1; this.owner[b] = o; return b; } rel(b) { if (--this.ref[b] === 0) { this.free.push(b); this.owner[b] = null; } }
    add(s) { this.t[s] = []; this.k[s] = 0; }
    app(s, n) { for (let i = 0; i < n; i++) { const t = this.t[s], k = this.k[s]; if (k % this.bs === 0) t.push(this.al(s)); else if (this.ref[t[t.length - 1]] > 1) { const nb = this.al(s); this.rel(t[t.length - 1]); t[t.length - 1] = nb; } this.k[s]++; } }
    fork(p, c) { this.t[c] = this.t[p].slice(); this.k[c] = this.k[p]; this.t[c].forEach(b => this.ref[b]++); }
    freeSeq(s) { this.t[s].forEach(b => this.rel(b)); delete this.t[s]; delete this.k[s]; } }
  const OPS = [
    ['1 · A: 10-token prompt', m => { m.add('A'); m.app('A', 10); }, 'A needs ceil(10/4) = 3 blocks. They needn\'t be contiguous, and the last one is half full.'],
    ['2 · B: 6-token prompt', m => { m.add('B'); m.app('B', 6); }, 'B gets 2 blocks from the free pool, with no reservation for its future length.'],
    ['3 · A generates 3 tokens', m => m.app('A', 3), 'A fills its last block (2 slots), then needs one new block for the 3rd token.'],
    ['4 · Fork A → A′ (parallel sample)', m => m.fork('A', "A'"), 'A′ shares all of A\'s blocks (refcount 2, outlined). No memory is copied.'],
    ['5 · A′ generates 1 token', m => m.app("A'", 1), 'A′ writes into the shared, partly filled last block, so it gets copied on write. The full blocks stay shared.'],
    ['6 · B finishes', m => m.freeSeq('B'), 'B\'s blocks return to the pool immediately for the next request.'],
  ];
  const COL = { A: 'var(--a)', B: 'var(--b)', "A'": 'var(--c)' };
  const ps = document.getElementById('paSteps'); ps.innerHTML = OPS.map((o, i) => `<button data-i="${i}">${o[0]}</button>`).join('');
  const pick = i => {
    Deck.$$('button', ps).forEach(b => b.classList.toggle('on', +b.dataset.i === i));
    const m = new BM(16, 4); OPS.slice(0, i + 1).forEach(o => o[1](m));
    const s = clear(document.getElementById('paSvg'));
    for (let b = 0; b < 16; b++) {
      const x = 10 + (b % 8) * 51, y = 10 + Math.floor(b / 8) * 66, used = m.ref[b] > 0, shared = m.ref[b] > 1;
      let fill = 0; Object.keys(m.t).forEach(sq => { const idx = m.t[sq].indexOf(b); if (idx >= 0) fill = Math.max(fill, Math.min(4, m.k[sq] - idx * 4)); });
      svg('rect', { x, y, width: 46, height: 54, rx: 5, style: `fill:var(--panel-2);stroke:${shared ? 'var(--ink)' : 'var(--line)'};stroke-width:${shared ? 2.5 : 1}` }, s);
      if (used) for (let k = 0; k < fill; k++) svg('rect', { x: x + 4, y: y + 42 - k * 12, width: 38, height: 10, rx: 2, style: `fill:${COL[m.owner[b]] || 'var(--faint)'}` }, s);
      svg('text', { x: x + 23, y: y + 66 > 140 ? y + 64 : y + 64, 'text-anchor': 'middle', class: 'tm tc', style: 'font-size:9px', text: '#' + b + (shared ? ' ×' + m.ref[b] : '') }, s);
    }
    document.getElementById('paTables').innerHTML = Object.keys(m.t).map(sq => `<div><b style="color:${COL[sq]}">${sq}</b> (${m.k[sq]} tok): [${m.t[sq].join(', ')}]</div>`).join('') + `<div style="margin-top:6px;color:var(--muted)">free blocks: ${m.free.length} / 16</div>`;
    document.getElementById('paInfo').innerHTML = OPS[i][2];
  };
  ps.addEventListener('click', e => { const b = e.target.closest('button'); if (b) pick(+b.dataset.i); }); pick(0);
  const SYS = ['<sys>', 'You', 'are', 'a', 'helpful', 'assistant', '.'];
  const REQ = [['User', ':', 'hi'], ['User', ':', 'summarize', 'this'], ['User', ':', 'hi', 'again']];
  const pcs = document.getElementById('pcSteps'); pcs.innerHTML = REQ.map((r, i) => `<button data-i="${i}">Request ${i + 1}</button>`).join('');
  const pc = i => {
    Deck.$$('button', pcs).forEach(b => b.classList.toggle('on', +b.dataset.i === i));
    const cached = new Set(); let html = '';
    for (let k = 0; k <= i; k++) {
      const toks = SYS.concat(REQ[k]); let hit = 0;
      for (let j = 0; j < toks.length; j++) { const key = toks.slice(0, j + 1).join('\u0001'); if (cached.has(key) && hit === j) hit++; }
      if (k === i) html = `<div class="toks">${toks.map((t, j) => `<span class="tok" style="background:${j < hit ? 'var(--e-soft)' : 'var(--b-soft)'};outline:${j < hit ? '1.5px solid var(--e)' : 'none'}">${t}</span>`).join('')}</div>`
        + `<p class="readout" style="margin-top:8px"><span style="color:var(--e)">${hit} cached</span> · <span style="color:var(--b)">${toks.length - hit} to prefill</span></p>`;
      toks.forEach((_, j) => cached.add(toks.slice(0, j + 1).join('\u0001')));
    }
    document.getElementById('pcOut').innerHTML = html;
    document.getElementById('pcInfo').innerHTML = ['The first request has nothing cached, so the whole prompt is prefilled and stays in the cache.', 'The 7-token system prompt plus "User :" (9 tokens) is reused, and only the new suffix is prefilled.', 'Request 3 shares even more with request 1, "… User : hi", so 10 tokens are reused.'][i];
  };
  pcs.addEventListener('click', e => { const b = e.target.closest('button'); if (b) pc(+b.dataset.i); }); pc(0);

})();
