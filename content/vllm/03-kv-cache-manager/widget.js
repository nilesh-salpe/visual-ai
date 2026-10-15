(() => {
  const { svg, clear, fmt } = Deck;
  const NB = 48, COL = ['var(--a)', 'var(--b)', 'var(--c)', 'var(--e)', 'var(--d)'];
  let owner, queue, reqs, nextId, seed;
  const reset = () => { owner = Array(NB).fill(-1); queue = [...Array(NB).keys()]; reqs = []; nextId = 0; seed = 5; draw('Empty pool: all 48 blocks are in the free queue.'); };
  const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  const alloc = (r, n) => { for (let i = 0; i < n; i++) { if (!queue.length) return false; const b = queue.shift(); owner[b] = r.id; r.blocks.push(b); } return true; };
  const draw = msg => {
    const s = clear(document.getElementById('kSvg')), w = 660 / 16 - 2;
    for (let b = 0; b < NB; b++) { const o = owner[b], x = (b % 16) * (w + 2), y = Math.floor(b / 16) * 46 + 4;
      svg('rect', { x, y, width: w, height: 40, rx: 4, style: `fill:${o < 0 ? 'var(--panel-2)' : COL[o % 5]}` }, s);
      svg('text', { x: x + w / 2, y: y + 25, 'text-anchor': 'middle', class: 't', style: `font-size:10px;${o < 0 ? '' : 'fill:#fff'}`, text: o < 0 ? '' : 'R' + o }, s); }
    svg('text', { x: 4, y: 170, class: 'tm', text: `free queue (front = LRU): ${queue.slice(0, 14).join(', ')}${queue.length > 14 ? ', …' : ''}` }, s);
    document.getElementById('kOut').innerHTML = `${msg} ${reqs.length} active request(s), ${NB - queue.length}/${NB} blocks used.`;
  };
  document.getElementById('kAdd').addEventListener('click', () => { const r = { id: nextId++, tokens: 20 + Math.floor(rnd() * 120), blocks: [] }; const n = Math.ceil(r.tokens / 16);
    if (alloc(r, n)) { reqs.push(r); draw(`R${r.id}: ${r.tokens}-token prompt → ${n} blocks.`); } else { r.blocks.forEach(b => { owner[b] = -1; queue.unshift(b); }); nextId--; draw('<b>Not enough free blocks</b>: the scheduler would wait or preempt.'); } });
  document.getElementById('kGrow').addEventListener('click', () => { let ok = true; reqs.forEach(r => { r.tokens += 16; const need = Math.ceil(r.tokens / 16) - r.blocks.length; if (!alloc(r, need)) ok = false; }); draw(ok ? 'Each request grew by 16 tokens; new blocks were taken from the front of the queue.' : '<b>Out of blocks</b>: vLLM would preempt the newest running request.'); });
  document.getElementById('kFin').addEventListener('click', () => { if (!reqs.length) return; const r = reqs.shift(); [...r.blocks].reverse().forEach(b => { owner[b] = -1; queue.push(b); }); draw(`R${r.id} finished: its ${r.blocks.length} blocks went to the back of the queue in reverse order (still cached until reused).`); });
  document.getElementById('kReset').addEventListener('click', reset);
  reset();
})();
