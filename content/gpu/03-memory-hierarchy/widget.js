(() => {
  const { svg, clear, fmt, bytes } = Deck;

  /* pyramid */
  const LV = [
    { n: 'Registers', size: '256 KB / SM · ~33 MB total', bw: 'highest (feeds ALUs every cycle)', lat: '~1 cycle', bwv: 100000, c: 'var(--e)', d: 'Private to each thread. 64K × 32-bit registers per SM. Tensor Core operands and accumulators live here. Using too many registers per thread limits occupancy.' },
    { n: 'Shared mem / L1', size: '256 KB / SM · ~33 MB total', bw: '~30 TB/s aggregate', lat: '~20–30 cycles', bwv: 30000, c: 'var(--a)', d: 'On-chip SRAM inside each SM, split between a hardware-managed L1 and a programmer-managed shared memory (up to 228 KB). This is where GEMM and attention tiles live.' },
    { n: 'L2 cache', size: '50 MB', bw: '~10 TB/s (approx.)', lat: '~200 cycles', bwv: 10000, c: 'var(--c)', d: 'Shared by all 132 SMs. Absorbs reuse between neighbouring thread blocks and buffers HBM traffic. Too small to hold a model\'s weights.' },
    { n: 'HBM3', size: '80 GB', bw: '3.35 TB/s', lat: '~500+ cycles', bwv: 3350, c: 'var(--b)', d: 'Stacked DRAM on the GPU package. Holds weights, activations, KV cache and optimizer state. Its bandwidth sets the speed of LLM decode.' },
    { n: 'Peer GPU (NVLink)', size: '7 × 80 GB in node', bw: '450 GB/s per direction', lat: '~µs', bwv: 450, c: 'var(--d)', d: 'Other GPUs\' HBM, reached through NVSwitch. Used by tensor-parallel collectives and peer-to-peer copies.' },
    { n: 'Host DRAM', size: '~2 TB per node', bw: '~64 GB/s (PCIe Gen5 x16)', lat: '~µs', bwv: 64, c: 'var(--faint)', d: 'CPU memory. Used for staging data loading, pinned-memory copies, ZeRO-Offload, and spill-over KV cache.' },
    { n: 'Local NVMe', size: '~30 TB per node', bw: '~7 GB/s per drive', lat: '~10–100 µs', bwv: 7, c: 'var(--faint)', d: 'Checkpoints, dataset shards, ZeRO-Infinity offload. GPUDirect Storage can DMA straight into HBM, skipping the CPU bounce buffer.' },
  ];
  const pyr = document.getElementById('pyr');
  const H = 46, top = 14, cx = 210;
  LV.forEach((l, i) => {
    const w0 = 70 + i * 48, w1 = 70 + (i + 1) * 48, y = top + i * H;
    const g = svg('g', { 'data-i': i }, pyr);
    svg('polygon', { points: `${cx - w0 / 2},${y} ${cx + w0 / 2},${y} ${cx + w1 / 2},${y + H - 4} ${cx - w1 / 2},${y + H - 4}`, style: `fill:${l.c};opacity:${i > 4 ? .55 : .9}` }, g);
    svg('text', { x: cx, y: y + H / 2 + 3, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:600;font-size:12.5px', text: l.n }, g);
  });
  svg('text', { x: 18, y: 30, class: 'tm', text: 'faster' }, pyr);
  svg('text', { x: 18, y: 330, class: 'tm', text: 'bigger' }, pyr);
  svg('line', { x1: 34, y1: 40, x2: 34, y2: 314, class: 's-line', 'stroke-width': 2, 'marker-end': '' }, pyr);
  const pick = i => {
    const l = LV[i];
    Deck.out('lvName', l.n); Deck.out('lvDesc', l.d); Deck.out('lvSize', l.size.split(' · ')[0]);
    Deck.out('lvBW', l.bw.split(' (')[0]); Deck.out('lvLat', l.lat);
    Deck.$$('#pyr g').forEach(g => g.style.opacity = +g.dataset.i === i ? 1 : .55);
    Deck.hbars(document.getElementById('lvBars'), LV.slice(1).map((x, k) => ({ label: x.n, value: x.bwv, color: k + 1 === i ? x.c : 'var(--line)', text: x.bwv >= 1000 ? (x.bwv / 1000).toFixed(x.bwv < 10000 ? 2 : 0) + ' TB/s' : x.bwv + ' GB/s' })), { log: true, min: 3, max: 40000 });
  };
  pyr.addEventListener('click', e => { const g = e.target.closest('g[data-i]'); if (g) pick(+g.dataset.i); });
  pyr.addEventListener('mouseover', e => { const g = e.target.closest('g[data-i]'); if (g) pick(+g.dataset.i); });
  pick(3);

  /* energy */
  Deck.hbars(document.getElementById('enBars'), [
    { label: '8-bit int add', value: 0.03, color: 'var(--e)', text: '0.03 pJ' },
    { label: '32-bit float add', value: 0.9, color: 'var(--e)', text: '0.9 pJ' },
    { label: '32-bit float mult', value: 3.7, color: 'var(--a)', text: '3.7 pJ' },
    { label: '32-bit SRAM read (8 KB)', value: 5, color: 'var(--c)', text: '5 pJ' },
    { label: '32-bit DRAM read', value: 640, color: 'var(--d)', text: '640 pJ' },
  ], { log: true, min: 0.01, max: 1000 });

  /* tiling */
  Deck.bind(['tT', 'tN'], () => {
    const T = Math.pow(2, Deck.val('tT')), N = Math.pow(2, Deck.val('tN'));
    Deck.out('tTo', T + '×' + T); Deck.out('tNo', N.toLocaleString());
    const loads = 2 * N ** 3 / T * 2, flops = 2 * N ** 3, ai = flops / loads;
    Deck.out('tTraffic', bytes(loads)); Deck.out('tAI', ai < 10 ? ai.toFixed(1) : ai.toFixed(0));
    Deck.hbars(document.getElementById('tBars'), [
      { label: 'naive (T=1)', value: 2 * N ** 3 * 2, color: 'var(--d)', text: bytes(2 * N ** 3 * 2) },
      { label: `tiled (T=${T})`, value: loads, color: 'var(--a)', text: bytes(loads) },
    ], { log: true });
    const sram = 2 * T * 64 * 2;
    document.getElementById('tSram').innerHTML = `SRAM per stage (two T×64 BF16 strips): <b>${bytes(sram)}</b> ${sram > 228 * 1024 ? '<span style="color:var(--d)">exceeds 228 KB of shared memory</span>' : '<span style="color:var(--e)">fits</span>'}`;
    const s = clear(document.getElementById('tileSvg'));
    const g = 8, cs = 10, tcell = Math.min(g, Math.max(1, Math.round(T / 32)));
    const mat = (x, y, lab, hl) => {
      for (let i = 0; i < g; i++) for (let j = 0; j < g; j++) svg('rect', { x: x + j * cs, y: y + i * cs, width: cs - 1, height: cs - 1, style: `fill:${hl(i, j) ? 'var(--a)' : 'var(--line)'}` }, s);
      svg('text', { x: x + g * cs / 2, y: y + g * cs + 18, 'text-anchor': 'middle', class: 't', style: 'font-weight:700', text: lab }, s);
    };
    mat(10, 40, 'A', (i) => i < tcell);
    mat(140, 40, 'B', (i, j) => j < tcell);
    mat(270, 40, 'C', (i, j) => i < tcell && j < tcell);
    svg('text', { x: 115, y: 85, class: 't', style: 'font-size:20px', text: '×' }, s);
    svg('text', { x: 245, y: 85, class: 't', style: 'font-size:20px', text: '=' }, s);
    svg('text', { x: 200, y: 190, 'text-anchor': 'middle', class: 'tm', text: 'one output tile reads a row-strip of A and a column-strip of B' }, s);
  });

  /* fusion */
  let fused = false;
  const OPS = ['GEMM out', 'bias', 'GELU', 'dropout', 'residual +'];
  const fuse = () => {
    const S = Math.pow(2, Deck.val('fS')), b = S * 2;
    Deck.out('fSo', fmt(S) + ' el');
    const s = clear(document.getElementById('fuseSvg'));
    svg('rect', { x: 10, y: 150, width: 640, height: 36, rx: 6, class: 'f-panel' }, s);
    svg('text', { x: 330, y: 173, 'text-anchor': 'middle', class: 'tm', text: 'HBM' }, s);
    let traffic, launches;
    if (!fused) {
      OPS.slice(1).forEach((o, i) => {
        const x = 40 + i * 155;
        svg('rect', { x, y: 30, width: 120, height: 44, rx: 8, class: 'f-b' }, s);
        svg('text', { x: x + 60, y: 57, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:600', text: o + ' kernel' }, s);
        svg('line', { x1: x + 35, y1: 148, x2: x + 35, y2: 78, style: 'stroke:var(--d);stroke-width:2.5', 'marker-end': 'url(#ar)' }, s);
        svg('line', { x1: x + 85, y1: 78, x2: x + 85, y2: 148, style: 'stroke:var(--d);stroke-width:2.5', 'marker-end': 'url(#ar)' }, s);
        svg('text', { x: x + 23, y: 118, 'text-anchor': 'end', class: 'tm', style: 'font-size:10px', text: 'read' }, s);
        svg('text', { x: x + 97, y: 118, class: 'tm', style: 'font-size:10px', text: 'write' }, s);
      });
      traffic = 4 * 2 * b + b; launches = 4;
    } else {
      svg('rect', { x: 140, y: 30, width: 380, height: 44, rx: 8, class: 'f-a' }, s);
      svg('text', { x: 330, y: 57, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:600', text: 'bias + GELU + dropout + residual (one kernel)' }, s);
      [[190, 'read x'], [330, 'read residual']].forEach(([x, t]) => {
        svg('line', { x1: x, y1: 148, x2: x, y2: 78, style: 'stroke:var(--e);stroke-width:2.5', 'marker-end': 'url(#ar)' }, s);
        svg('text', { x: x + 8, y: 118, class: 'tm', style: 'font-size:10px', text: t }, s);
      });
      svg('line', { x1: 470, y1: 78, x2: 470, y2: 148, style: 'stroke:var(--e);stroke-width:2.5', 'marker-end': 'url(#ar)' }, s);
      svg('text', { x: 478, y: 118, class: 'tm', style: 'font-size:10px', text: 'write out' }, s);
      traffic = 3 * b; launches = 1;
    }
    const defs = svg('defs', {}, s), m = svg('marker', { id: 'ar', viewBox: '0 0 10 10', refX: 8, refY: 5, markerWidth: 6, markerHeight: 6, orient: 'auto-start-reverse' }, defs);
    svg('path', { d: 'M0,0 L10,5 L0,10 z', style: 'fill:var(--muted)' }, m);
    Deck.out('fBytes', bytes(traffic)); Deck.out('fTime', (traffic / 3.35e12 * 1e6).toFixed(0) + ' µs'); Deck.out('fLaunch', launches);
  };
  Deck.seg('fMode', v => { fused = v === '1'; if (document.getElementById('fS')) fuse(); });
  Deck.bind(['fS'], fuse);

  /* flash attention */
  Deck.bind(['faN'], () => {
    const N = Math.pow(2, Deck.val('faN')), d = 128, Br = 128;
    Deck.out('faNo', N >= 1024 ? N / 1024 + 'K' : N);
    const naiveMem = N * N * 2, flashMem = N * 2 * 4;
    Deck.hbars(document.getElementById('faMem'), [
      { label: 'standard (N×N)', value: naiveMem, color: 'var(--d)', text: bytes(naiveMem) },
      { label: 'Flash (stats only)', value: flashMem, color: 'var(--a)', text: bytes(flashMem) },
    ], { log: true, min: 1e3, max: 1e11 });
    const naiveT = 8 * N * N * 2 + 4 * N * d * 2, flashT = 4 * N * N * d / Br + 4 * N * d * 2;
    Deck.hbars(document.getElementById('faTraffic'), [
      { label: 'standard', value: naiveT, color: 'var(--d)', text: bytes(naiveT) },
      { label: 'Flash', value: flashT, color: 'var(--a)', text: bytes(flashT) + ' · ' + (naiveT / flashT).toFixed(1) + '× less' },
    ]);
  });
  Deck.enter('s-flash', () => {
    const s = clear(document.getElementById('faSvg'));
    const n = 6, c = 34, x0 = 90, y0 = 40;
    svg('text', { x: x0 + n * c / 2, y: 24, 'text-anchor': 'middle', class: 'tm', text: 'Kᵀ / V tiles →' }, s);
    svg('text', { x: 20, y: y0 + n * c / 2, class: 'tm', transform: `rotate(-90 20 ${y0 + n * c / 2})`, 'text-anchor': 'middle', text: 'Q tiles' }, s);
    const cells = [];
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) cells.push(svg('rect', { x: x0 + j * c, y: y0 + i * c, width: c - 3, height: c - 3, rx: 3, style: 'fill:var(--line)' }, s));
    const qBox = svg('rect', { x: 40, y: y0, width: 30, height: c - 3, rx: 3, class: 'f-c' }, s);
    svg('text', { x: 55, y: y0 - 6, 'text-anchor': 'middle', class: 'tm', style: 'font-size:10px', text: 'Q' }, s);
    const sram = svg('rect', { x: 40, y: 262, width: 280, height: 28, rx: 6, style: 'fill:var(--a-soft);stroke:var(--a)' }, s);
    const st = svg('text', { x: 180, y: 281, 'text-anchor': 'middle', class: 't', style: 'font-size:11.5px', text: '' }, s);
    let k = -1, playing = true, acc = 1;
    const btn = document.getElementById('faPlay');
    btn.textContent = 'Pause';
    btn.onclick = () => { playing = !playing; btn.textContent = playing ? 'Pause' : 'Play'; };
    return Deck.loop((t, dt) => {
      if (!playing) return;
      acc += dt; if (acc < 0.35) return; acc = 0;
      k = (k + 1) % (n * n);
      const i = Math.floor(k / n), j = k % n;
      cells.forEach((r, idx) => {
        const ii = Math.floor(idx / n), jj = idx % n;
        r.style.fill = ii < i || (ii === i && jj < j) ? 'var(--a-soft)' : (ii === i && jj === j ? 'var(--a)' : 'var(--line)');
      });
      qBox.setAttribute('y', y0 + i * c);
      st.textContent = `SRAM: Q tile ${i} · K/V tile ${j} · running max m, sum ℓ, output O`;
      Deck.out('faStep', j === n - 1 ? `Row ${i} finished → write O tile ${i} to HBM once` : `update O ← rescale(O) + softmax-part · V${j}`);
    });
  });

  /* ZeRO */
  let stage = 3;
  const zero = () => {
    const P = Math.pow(10, Deck.val('zP')) * 1e9, D = Math.pow(2, Deck.val('zD'));
    Deck.out('zPo', fmt(P, 0)); Deck.out('zDo', D);
    let w = 2 * P, g = 2 * P, o = 12 * P;
    if (stage >= 1) o /= D;
    if (stage >= 2) g /= D;
    if (stage >= 3) w /= D;
    const tot = w + g + o, GB = 1e9, s = clear(document.getElementById('zSvg'));
    const maxv = Math.max(tot, 80 * GB) * 1.05, X = v => 10 + v / maxv * 640;
    let x = 10;
    [[w, 'var(--a)', 'weights'], [g, 'var(--b)', 'grads'], [o, 'var(--c)', 'optimizer']].forEach(([v, c, n]) => {
      const wpx = X(v) - 10;
      svg('rect', { x, y: 30, width: Math.max(.5, wpx), height: 50, style: `fill:${c}` }, s);
      if (wpx > 70) svg('text', { x: x + wpx / 2, y: 60, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:12px', text: `${n} ${(v / GB).toFixed(0)} GB` }, s);
      x += wpx;
    });
    svg('line', { x1: X(80 * GB), x2: X(80 * GB), y1: 16, y2: 96, style: 'stroke:var(--d);stroke-width:2.5;stroke-dasharray:5 4' }, s);
    svg('text', { x: X(80 * GB), y: 12, 'text-anchor': 'middle', class: 't', style: 'fill:var(--d);font-size:11px', text: '80 GB' }, s);
    svg('text', { x: 10, y: 118, class: 'tm', text: `per-GPU state: ${(tot / GB).toFixed(1)} GB` }, s);
    const ok = tot < 80 * GB;
    document.getElementById('zOut').innerHTML = `${['No sharding', 'ZeRO-1', 'ZeRO-2', 'ZeRO-3 / FSDP'][stage]} across ${D} GPUs → <span style="color:${ok ? 'var(--e)' : 'var(--d)'}">${(tot / GB).toFixed(1)} GB per GPU ${ok ? '(fits, with ' + (80 - tot / GB).toFixed(0) + ' GB left for activations)' : '(does not fit)'}</span>`;
  };
  Deck.seg('zS', v => { stage = +v; if (document.getElementById('zP')) zero(); });
  Deck.bind(['zP', 'zD'], zero);

  /* KV */
  let kvBytes = 2;
  const kv = () => {
    const [L, H, d, wGB] = Deck.val('kvM').split(',').map(Number);
    const C = Math.pow(2, Deck.val('kvC')), B = Math.pow(2, Deck.val('kvB'));
    Deck.out('kvCo', C >= 1024 ? C / 1024 + 'K' : C); Deck.out('kvBo', B);
    const per = 2 * L * H * d * kvBytes, tot = per * C * B;
    Deck.out('kvTok', bytes(per)); Deck.out('kvTot', (tot / 1e9).toFixed(tot < 1e10 ? 1 : 0) + ' GB'); Deck.out('kvW', wGB + ' GB');
    const need = (tot / 1e9) + wGB;
    Deck.hbars(document.getElementById('kvBars'), [
      { label: 'weights + KV', value: need, color: 'var(--b)', text: need.toFixed(0) + ' GB' },
      { label: '1× H100 (80 GB)', value: 80, color: need <= 80 ? 'var(--e)' : 'var(--line)', text: '80 GB' },
      { label: '1× H200 (141 GB)', value: 141, color: need <= 141 ? 'var(--e)' : 'var(--line)', text: '141 GB' },
      { label: '1× B200 (192 GB)', value: 192, color: need <= 192 ? 'var(--e)' : 'var(--line)', text: '192 GB' },
      { label: '8× H100 node', value: 640, color: need <= 640 ? 'var(--e)' : 'var(--line)', text: '640 GB' },
    ], { log: true, min: 5, max: Math.max(2000, need * 1.2) });
  };
  Deck.seg('kvT', v => { kvBytes = +v; if (document.getElementById('kvM')) kv(); });
  Deck.bind(['kvM', 'kvC', 'kvB'], kv);

  /* paged */
  let mode = 'c', reqs = [];
  const COLORS = ['var(--a)', 'var(--b)', 'var(--c)', 'var(--e)', 'var(--d)', '#3a8fd8', '#c9a227', '#8a6d3b'];
  const newReqs = () => { reqs = Array.from({ length: 8 }, () => Math.round(80 + Math.random() * Math.random() * 1500)); };
  const paged = () => {
    const s = clear(document.getElementById('pgSvg'));
    const cols = 64, rows = 8, cells = cols * rows, blk = 16; // 512 cells × 16 tokens = 8192 tokens
    const cw = 640 / cols, ch = 26;
    const grid = Array(cells).fill(-1), reserved = Array(cells).fill(false);
    let fit = 0, used = 0, reservedCells = 0;
    const rejected = new Set();
    if (mode === 'c') {
      let pos = 0;
      reqs.forEach((len, r) => {
        const need = 2048 / blk;
        if (pos + need > cells) { rejected.add(r); return; }
        fit++;
        const usedC = Math.ceil(len / blk);
        for (let k = 0; k < need; k++) { reserved[pos + k] = true; if (k < usedC) grid[pos + k] = r; }
        used += len; reservedCells += need; pos += need;
      });
    } else {
      const order = [];
      reqs.forEach((len, r) => { for (let k = 0; k < Math.ceil(len / blk); k++) order.push(r); });
      for (let i = order.length - 1; i > 0; i--) { const j = Math.floor((Math.sin(i * 9301 + 49297) * 0.5 + 0.5) * (i + 1)); [order[i], order[j]] = [order[j], order[i]]; }
      order.slice(0, cells).forEach((r, k) => { grid[k] = r; reserved[k] = true; });
      fit = reqs.length; used = reqs.reduce((a, b) => a + b, 0); reservedCells = Math.min(cells, order.length);
    }
    for (let i = 0; i < cells; i++) {
      const x = 10 + (i % cols) * cw, y = 10 + Math.floor(i / cols) * ch;
      const fill = grid[i] >= 0 ? COLORS[grid[i]] : reserved[i] ? 'var(--d-soft)' : 'var(--panel-2)';
      svg('rect', { x, y, width: cw - 1, height: ch - 2, style: `fill:${fill}${reserved[i] && grid[i] < 0 ? ';stroke:var(--d);stroke-width:.5' : ''}` }, s);
    }
    const usedPct = used / (cells * blk), waste = reservedCells * blk - used;
    Deck.out('pgUsed', (100 * usedPct).toFixed(0) + '%');
    Deck.out('pgFit', `${fit} / ${reqs.length}`);
    Deck.out('pgWaste', (100 * waste / (reservedCells * blk || 1)).toFixed(0) + '%');
    document.getElementById('pgLegend').innerHTML = reqs.map((l, i) => `<span style="${rejected.has(i) ? 'text-decoration:line-through;opacity:.6' : ''}"><i style="background:${COLORS[i]}"></i>req ${i}: ${l} tok${rejected.has(i) ? ' (rejected)' : ''}</span>`).join('') + '<span><i style="background:var(--d-soft);border:1px solid var(--d)"></i>reserved, empty</span>';
  };
  newReqs();
  Deck.seg('pgMode', v => { mode = v; paged(); });
  document.getElementById('pgNew').onclick = () => { newReqs(); paged(); };

  /* offload */
  Deck.bind(['oS'], () => {
    const GB = Math.pow(10, Deck.val('oS'));
    Deck.out('oSo', GB < 10 ? GB.toFixed(1) + ' GB' : GB.toFixed(0) + ' GB');
    const t = bw => { const s = GB / bw; return s < 1 ? (s * 1000).toFixed(s < .01 ? 2 : 0) + ' ms' : s.toFixed(1) + ' s'; };
    const rows = [['HBM3', 3350, 'var(--b)'], ['NVLink 4', 450, 'var(--d)'], ['PCIe Gen5 x16', 64, 'var(--c)'], ['400G NIC', 50, 'var(--c)'], ['NVMe drive', 7, 'var(--faint)']];
    Deck.hbars(document.getElementById('oBars'), rows.map(([n, bw, c]) => ({ label: n, value: GB / bw, color: c, text: t(bw) })), { log: true, min: GB / 6000, max: GB / 5 });
  });
})();
