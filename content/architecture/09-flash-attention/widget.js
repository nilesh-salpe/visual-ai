(() => {
  const { svg, clear, fmt } = Deck;

  (() => {
    const s = document.getElementById('pSvg'), steps = [['S = QKᵀ', 'read Q, K · write S (N²)'], ['P = softmax(S)', 'read S · write P (N²)'], ['O = PV', 'read P, V · write O']];
    steps.forEach(([a, b], i) => {
      const x = 20 + i * 215;
      svg('rect', { x, y: 30, width: 190, height: 50, rx: 9, class: 'f-a' }, s);
      svg('text', { x: x + 95, y: 61, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:700', text: a }, s);
      svg('text', { x: x + 95, y: 104, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: b }, s);
      svg('path', { d: `M${x + 95} 112 V140`, style: 'stroke:var(--d);stroke-width:2;stroke-dasharray:4 3' }, s);
    });
    svg('rect', { x: 20, y: 140, width: 620, height: 34, rx: 8, style: 'fill:var(--d-soft);stroke:var(--d)' }, s);
    svg('text', { x: 330, y: 162, 'text-anchor': 'middle', class: 't', text: 'HBM: every arrow is a round trip at 1.5–2.0 TB/s (each N² matrix is written, then read)' }, s);
  })();
  const X = [1.2, 0.3, 2.0, -0.5, 3.1, 0.8, 1.9, 2.5, 4.0, -1.0, 0.2, 3.6];
  let os = 0;
  const osDraw = () => {
    const s = clear(document.getElementById('osSvg')); let m = -Infinity, l = 0, msg = [];
    for (let c = 0; c < os; c++) {
      const ch = X.slice(c * 4, c * 4 + 4), mn = Math.max(m, ...ch), corr = isFinite(m) ? Math.exp(m - mn) : 0;
      l = l * corr + ch.reduce((a, x) => a + Math.exp(x - mn), 0);
      msg.push(`chunk ${c + 1}: max ${isFinite(m) ? m.toFixed(1) : '−∞'} → ${mn.toFixed(1)}${c && mn > m ? `, old sum × e^(${m.toFixed(1)}−${mn.toFixed(1)}) = ×${corr.toFixed(3)}` : ''}; ℓ = ${l.toFixed(3)}`);
      m = mn;
    }
    X.forEach((x, i) => {
      const done = i < os * 4, cx = 40 + i * 50;
      svg('rect', { x: cx - 20, y: 20, width: 40, height: 36, rx: 6, style: `fill:${done ? 'var(--a)' : 'var(--panel-2)'}` }, s);
      svg('text', { x: cx, y: 43, 'text-anchor': 'middle', class: 't', style: done ? 'fill:#fff;font-weight:600' : '', text: x.toFixed(1) }, s);
      if (i % 4 === 0) svg('text', { x: cx + 75, y: 74, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: 'chunk ' + (i / 4 + 1) }, s);
    });
    msg.forEach((t, k) => svg('text', { x: 20, y: 110 + k * 24, class: 't', style: 'font-size:12.5px', text: t }, s));
    const trueL = X.reduce((a, x) => a + Math.exp(x - 4.0), 0);
    document.getElementById('osOut').innerHTML = os < 3 ? `After ${os} of 3 chunks: m = ${isFinite(m) ? m.toFixed(1) : '−∞'}, ℓ = ${l.toFixed(3)}.` : `Done. m = ${m.toFixed(1)}, ℓ = ${l.toFixed(4)}; a two-pass softmax gives Σ e^(x − 4.0) = ${trueL.toFixed(4)}, identical. softmax(x)ᵢ = e^(xᵢ − m) / ℓ.`;
  };
  document.getElementById('osNext').addEventListener('click', () => { os = Math.min(3, os + 1); osDraw(); });
  document.getElementById('osReset').addEventListener('click', () => { os = 0; osDraw(); });
  osDraw();
  const NB = 8, Bsz = 128, dd = 64, N = NB * Bsz; let causal = false, tile = 0, timer = null;
  const tiles = () => { const t = []; for (let i = 0; i < NB; i++) for (let j = 0; j < NB; j++) if (!causal || j <= i) t.push([i, j]); return t; };
  const tlDraw = () => {
    const T = tiles(), s = clear(document.getElementById('tlSvg')), c = 24, x0 = 70, y0 = 20;
    for (let i = 0; i < NB; i++) for (let j = 0; j < NB; j++) {
      const k = T.findIndex(([a, b]) => a === i && b === j), done = k >= 0 && k < tile, cur = k === tile - 1, skip = k < 0;
      svg('rect', { x: x0 + j * c, y: y0 + i * c, width: c - 3, height: c - 3, rx: 3, style: `fill:${cur ? 'var(--b)' : done ? 'var(--a)' : skip ? 'var(--panel)' : 'var(--panel-2)'};${skip ? 'stroke:var(--line);stroke-dasharray:2 2' : ''}` }, s);
    }
    svg('text', { x: x0 + NB * c / 2, y: y0 + NB * c + 18, 'text-anchor': 'middle', class: 'tm', text: 'K/V blocks (inner loop) →' }, s);
    svg('text', { x: x0 - 8, y: y0 + NB * c / 2, 'text-anchor': 'end', class: 'tm', text: 'Q ↓' }, s);
    const rowsDone = new Set(T.slice(0, tile).map(([i]) => i)).size;
    const flash = rowsDone * Bsz * dd * 2 + T.slice(0, tile).length * Bsz * dd * 2;
    const std = 4 * N * dd + 4 * N * N * (causal ? 0.5 : 1);
    [['tiles computed', `${tile} / ${T.length}`], ['tiled HBM traffic so far', Deck.fmt(flash) + ' elements'], ['standard, whole pass', Deck.fmt(std) + ' elements'], ['N×N kept in HBM', 'never']].forEach(([a, b], k) => {
      svg('text', { x: 340, y: 50 + k * 34, class: 'tm', text: a }, s); svg('text', { x: 640, y: 50 + k * 34, 'text-anchor': 'end', class: 't', style: 'font-weight:700', text: b }, s);
    });
    document.getElementById('tlOut').innerHTML = tile === T.length ? `Finished: tiled ≈ <b>${Deck.fmt(flash)}</b> vs standard ≈ <b>${Deck.fmt(std)}</b> elements moved (${(std / flash).toFixed(1)}× less)${causal ? `; ${NB * NB - T.length} future blocks skipped` : ''}.` : 'Each orange tile: load Q_i (once per row), K_j and V_j into SRAM, update m, ℓ and Õ for that row block.';
  };
  document.getElementById('tlNext').addEventListener('click', () => { tile = Math.min(tiles().length, tile + 1); tlDraw(); });
  document.getElementById('tlRun').addEventListener('click', () => { clearInterval(timer); timer = setInterval(() => { tile++; if (tile >= tiles().length) { tile = tiles().length; clearInterval(timer); } tlDraw(); }, 70); });
  Deck.seg('tlC', v => { causal = v === '1'; tile = 0; clearInterval(timer); tlDraw(); });
  Deck.hbars(document.getElementById('fBars'), [
    { label: 'GFLOPs, standard', value: 66.6, color: 'var(--faint)', text: '66.6' }, { label: 'GFLOPs, Flash', value: 75.2, color: 'var(--faint)', text: '75.2 (more!)' },
    { label: 'HBM R/W, standard', value: 40.3, color: 'var(--d)', text: '40.3 GB' }, { label: 'HBM R/W, Flash', value: 4.4, color: 'var(--e)', text: '4.4 GB' },
    { label: 'runtime, standard', value: 41.7, color: 'var(--d)', text: '41.7 ms' }, { label: 'runtime, Flash', value: 7.3, color: 'var(--e)', text: '7.3 ms' }], { max: 80 });

})();
