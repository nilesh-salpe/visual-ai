(() => {
  const { svg, clear, fmt } = Deck;

  /* ---------- die area ---------- */
  (function die() {
    const s = document.getElementById('dieSvg');
    const info = document.getElementById('dieInfo');
    const block = (g, x, y, w, h, cls, txt) => {
      svg('rect', { x, y, width: w, height: h, rx: 4, class: cls }, g);
      if (txt) svg('text', { x: x + w / 2, y: y + h / 2 + 4, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11px', text: txt }, g);
    };
    const grp = (msg) => { const g = svg('g', { 'data-info': msg }, s); return g; };
    svg('text', { x: 180, y: 20, 'text-anchor': 'middle', class: 't', style: 'font-weight:700', text: 'CPU (e.g. server x86)' }, s);
    svg('text', { x: 570, y: 20, 'text-anchor': 'middle', class: 't', style: 'font-weight:700', text: 'GPU (e.g. H100)' }, s);
    svg('rect', { x: 20, y: 32, width: 320, height: 250, rx: 10, class: 'f-panel s-line', 'stroke-width': 1 }, s);
    svg('rect', { x: 410, y: 32, width: 330, height: 250, rx: 10, class: 'f-panel s-line', 'stroke-width': 1 }, s);
    for (let i = 0; i < 8; i++) {
      const x = 34 + (i % 4) * 76, y = 44 + Math.floor(i / 4) * 78;
      const g = grp('<b>CPU core</b>: a large out-of-order core. Most of its area is the branch predictor, reorder buffer, decoders and private L1/L2 cache (amber and violet). The SIMD ALU (teal) is a small part of the core.');
      block(g, x, y, 68, 34, 'f-b', 'control');
      block(g, x, y + 36, 32, 30, 'f-a', 'ALU');
      block(g, x + 36, y + 36, 32, 30, 'f-c', 'L2');
    }
    const l3 = grp('<b>Shared L3 cache</b>: tens to hundreds of MB, there to keep latency low for a few threads. It often takes up a third of the die.');
    block(l3, 34, 202, 296, 46, 'f-c', 'L3 cache');
    const mc = grp('<b>DDR memory controllers</b>: about 8–12 channels, a few hundred GB/s in total, which is roughly 10× less than HBM.');
    block(mc, 34, 252, 296, 22, '', '');
    mc.lastChild && mc.lastChild.setAttribute('style', 'fill:var(--faint)');
    svg('text', { x: 182, y: 267, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11px', text: 'DDR5 controllers · ~0.3–0.6 TB/s' }, mc);
    // GPU
    const hbmL = grp('<b>HBM stacks</b>: DRAM dies stacked vertically next to the GPU on an interposer. H100 SXM has 5 active stacks, 80 GB at about 3.35 TB/s.');
    for (let i = 0; i < 3; i++) block(hbmL, 418, 44 + i * 78, 26, 70, '', '');
    [...hbmL.querySelectorAll('rect')].forEach(r => r.setAttribute('style', 'fill:var(--faint)'));
    const hbmR = grp(hbmL.getAttribute('data-info'));
    for (let i = 0; i < 3; i++) block(hbmR, 706, 44 + i * 78, 26, 70, '', '');
    [...hbmR.querySelectorAll('rect')].forEach(r => r.setAttribute('style', 'fill:var(--faint)'));
    for (let r = 0; r < 2; r++) for (let c = 0; c < 8; c++) {
      const x = 452 + c * 31, y = (r === 0 ? 44 : 172);
      for (let k = 0; k < 4; k++) {
        const g = grp('<b>Streaming Multiprocessor (SM)</b>: nearly all ALUs and Tensor Cores (teal), with a thin strip of warp schedulers (amber) and a 256 KB L1/shared memory (violet). An H100 has 132 of them.');
        const yy = y + (k % 2) * 52 + (k > 1 ? 0 : 0);
        if (k > 1) continue;
        block(g, x, yy, 27, 6, 'f-b');
        block(g, x, yy + 7, 27, 34, 'f-a');
        block(g, x, yy + 42, 27, 7, 'f-c');
      }
    }
    const l2 = grp('<b>L2 cache</b>: 50 MB shared by all SMs. It is small compared with the work in flight; its job is to buffer HBM traffic, not to hold a working set the way a CPU L3 does.');
    block(l2, 452, 148, 244, 20, 'f-c', 'L2 cache (50 MB)');
    s.addEventListener('mouseover', e => { const g = e.target.closest('[data-info]'); if (g) info.innerHTML = g.dataset.info; });
    s.addEventListener('click', e => { const g = e.target.closest('[data-info]'); if (g) info.innerHTML = g.dataset.info; });
  })();

  /* ---------- race ---------- */
  Deck.bind(['raceN'], () => {
    const N = Math.pow(10, Deck.val('raceN'));
    const cpu = N / 4e12, gpu = 10e-6 + N / 60e12;
    const t = x => x < 1e-3 ? (x * 1e6).toFixed(x < 1e-5 ? 2 : 0) + ' µs' : x < 1 ? (x * 1e3).toFixed(1) + ' ms' : x.toFixed(2) + ' s';
    Deck.out('raceNo', fmt(N) + ' FLOPs');
    Deck.hbars(document.getElementById('raceBars'), [
      { label: 'CPU', value: cpu, color: 'var(--b)', text: t(cpu) },
      { label: 'GPU', value: gpu, color: 'var(--a)', text: t(gpu) },
    ], { max: Math.max(cpu, gpu) });
    const w = document.getElementById('raceWin');
    w.textContent = cpu < gpu ? `CPU wins by ${(gpu / cpu).toFixed(1)}×: the job is too small to pay back the launch overhead`
                              : `GPU wins by ${(cpu / gpu).toFixed(1)}×${N > 1e10 ? ': throughput dominates' : ''}`;
    w.style.color = cpu < gpu ? 'var(--b)' : 'var(--a)';
  });

  /* ---------- chip anatomy ---------- */
  (function chip() {
    const s = document.getElementById('chipSvg'), info = document.getElementById('chipInfo');
    const disabled = new Set([5, 17, 23, 40, 52, 59, 76, 88, 95, 112, 124, 131]);
    const hbmInfo = '<b>HBM3 stack</b>: H100 SXM uses 5 active stacks (a 6th position is not used), each with a 1024-bit interface. Together: <b>80 GB at about 3.35 TB/s</b>. Bandwidth from here is the limit for most LLM inference.';
    [[8, 30], [8, 140], [8, 250], [600, 30], [600, 140], [600, 250]].forEach(([x, y], i) => {
      const r = svg('rect', { x, y, width: 32, height: 100, rx: 4, 'data-info': i === 5 ? '<b>Unused HBM position</b>: GH100 has room for 6 stacks; the SXM5 80 GB part enables 5.' : hbmInfo, style: `fill:var(--faint);opacity:${i === 5 ? .35 : 1}` }, s);
      svg('text', { x: x + 16, y: y + 54, 'text-anchor': 'middle', class: 'tm', style: 'fill:#fff;font-size:10px;pointer-events:none', text: 'HBM' }, s);
    });
    svg('rect', { x: 50, y: 20, width: 540, height: 340, rx: 10, class: 'f-panel s-line' }, s);
    svg('rect', { x: 62, y: 182, width: 516, height: 18, rx: 4, class: 'f-c', 'data-info': '<b>L2 cache: 50 MB</b>, split into two partitions and shared by all SMs. Weights for a single layer often fit here, but a full model does not, so most traffic still goes to HBM.' }, s);
    svg('text', { x: 320, y: 195, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11px;pointer-events:none', text: 'L2 cache · 50 MB' }, s);
    let id = 0;
    for (let g = 0; g < 8; g++) {
      const gx = 62 + (g % 4) * 130, gy = g < 4 ? 30 : 210;
      svg('rect', { x: gx, y: gy, width: 124, height: 142, rx: 6, class: 'f-bg s-line', 'data-info': `<b>GPC ${g}</b> (Graphics Processing Cluster): 9 TPCs × 2 SMs = 18 SMs on the full die.` }, s);
      svg('text', { x: gx + 6, y: gy + 13, class: 'tm', style: 'font-size:10px;pointer-events:none', text: 'GPC ' + g }, s);
      for (let k = 0; k < 18; k++) {
        const x = gx + 6 + (k % 6) * 19.5, y = gy + 20 + Math.floor(k / 6) * 40;
        const off = disabled.has(id);
        const smId = id;
        const r = svg('rect', { x, y, width: 16, height: 36, rx: 2, class: off ? '' : 'f-a', style: off ? 'fill:var(--line)' : '', 'data-sm': smId, 'data-info': off ? `<b>SM ${smId}: disabled</b>. Fused off at manufacturing to improve yield (144 → 132).` : `<b>SM ${smId}</b> in GPC ${g}: 4 partitions, each with a warp scheduler, 32 FP32 lanes, a 64 KB register file and 1 Tensor Core. Shown on the right.` }, s);
        id++;
      }
    }
    const pick = e => {
      const t = e.target.closest('[data-info]'); if (!t) return;
      info.innerHTML = t.dataset.info;
      s.querySelectorAll('[data-sm]').forEach(r => r.setAttribute('stroke', 'none'));
      if (t.dataset.sm) { t.setAttribute('stroke', 'var(--b)'); t.setAttribute('stroke-width', '3'); }
    };
    s.addEventListener('click', pick);
    s.addEventListener('mouseover', pick);

    const m = document.getElementById('smSvg');
    svg('text', { x: 200, y: 18, 'text-anchor': 'middle', class: 't', style: 'font-weight:700', text: 'One SM (Hopper)' }, m);
    for (let p = 0; p < 4; p++) {
      const x = 10 + (p % 2) * 195, y = 30 + Math.floor(p / 2) * 135;
      svg('rect', { x, y, width: 185, height: 128, rx: 6, class: 'f-panel s-line' }, m);
      svg('rect', { x: x + 6, y: y + 6, width: 173, height: 18, rx: 3, class: 'f-b' }, m);
      svg('text', { x: x + 92, y: y + 19, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:10.5px', text: 'Warp scheduler + dispatch' }, m);
      svg('rect', { x: x + 6, y: y + 28, width: 173, height: 16, rx: 3, style: 'fill:var(--c);opacity:.75' }, m);
      svg('text', { x: x + 92, y: y + 40, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:10px', text: 'Register file · 64 KB' }, m);
      for (let i = 0; i < 32; i++) svg('rect', { x: x + 6 + (i % 16) * 7.2, y: y + 50 + Math.floor(i / 16) * 9, width: 6, height: 7, rx: 1, class: 'f-a' }, m);
      svg('text', { x: x + 6, y: y + 87, class: 'tm', style: 'font-size:9.5px', text: '32 FP32 · 16 INT32 · 16 FP64 lanes' }, m);
      svg('rect', { x: x + 124, y: y + 48, width: 55, height: 30, rx: 4, class: 'f-e' }, m);
      svg('text', { x: x + 151, y: y + 64, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:9.5px', text: 'Tensor' }, m);
      svg('text', { x: x + 151, y: y + 76, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:9.5px', text: 'Core' }, m);
      svg('rect', { x: x + 6, y: y + 94, width: 173, height: 26, rx: 3, style: 'fill:var(--faint);opacity:.35' }, m);
      svg('text', { x: x + 92, y: y + 111, 'text-anchor': 'middle', class: 'tm', style: 'font-size:10px', text: 'LD/ST · SFU (exp, sin, rsqrt)' }, m);
    }
    svg('rect', { x: 10, y: 302, width: 380, height: 32, rx: 5, class: 'f-c' }, m);
    svg('text', { x: 200, y: 322, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11.5px', text: '256 KB combined L1 / shared memory (≤228 KB shared)' }, m);
    svg('rect', { x: 10, y: 340, width: 380, height: 26, rx: 5, style: 'fill:var(--b);opacity:.8' }, m);
    svg('text', { x: 200, y: 357, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11px', text: 'TMA: async bulk copies HBM ↔ shared memory' }, m);
  })();

  /* ---------- warps ---------- */
  Deck.bind(['wN', 'wT'], () => {
    const N = Deck.val('wN'), T = Deck.val('wT');
    Deck.out('wNo', N.toLocaleString()); Deck.out('wTo', T);
    const blocks = Math.ceil(N / T), warps = Math.ceil(T / 32), last = T - (warps - 1) * 32;
    Deck.out('wBlocks', blocks.toLocaleString());
    Deck.out('wWarps', warps);
    Deck.out('wUtil', (100 * T / (warps * 32)).toFixed(0) + '%');
    Deck.out('wIdle', 32 - last);
    document.getElementById('wUtil').style.color = T % 32 ? 'var(--d)' : 'var(--e)';
    const s = clear(document.getElementById('warpSvg'));
    const rows = warps, cell = Math.min(18, 200 / rows);
    s.setAttribute('viewBox', `0 0 660 ${Math.max(60, rows * cell + 28)}`);
    svg('text', { x: 0, y: 12, class: 'tm', text: `Block 0: ${warps} warp${warps > 1 ? 's' : ''} × 32 lanes` }, s);
    for (let w = 0; w < rows; w++) {
      if (rows <= 16 || w % Math.ceil(rows / 16) === 0 || w === rows - 1)
        svg('text', { x: 0, y: 22 + w * cell + cell * .75, class: 'tm tc', style: `font-size:${Math.min(11, cell * .8)}px`, text: 'w' + w }, s);
      for (let l = 0; l < 32; l++) {
        const active = w * 32 + l < T;
        svg('rect', { x: 40 + l * 19.4, y: 20 + w * cell, width: 17, height: cell - 2, rx: 2, style: `fill:${active ? 'var(--a)' : 'var(--line)'}` }, s);
      }
    }
  });

  /* ---------- divergence ---------- */
  const DIV = {
    none: { note: 'All lanes run the same path', passes: [{ name: 'y = a*x + b', cyc: 10, act: () => true }] },
    half: { note: 'Odd and even lanes run one after the other', passes: [{ name: 'if-branch (odd i)', cyc: 10, act: i => i % 2 === 1 }, { name: 'else-branch (even i)', cyc: 10, act: i => i % 2 === 0 }] },
    rare: { note: '4 lanes hold up the other 28', passes: [{ name: 'common code', cyc: 10, act: () => true }, { name: 'expensive() for i < 4', cyc: 60, act: i => i < 4 }] },
    four: { note: '4 serialized cases, 8 lanes each', passes: [0, 1, 2, 3].map(k => ({ name: `case ${k}`, cyc: 10, act: i => i % 4 === k })) },
  };
  Deck.seg('divSeg', v => {
    const d = DIV[v], s = clear(document.getElementById('divSvg'));
    const total = d.passes.reduce((a, p) => a + p.cyc, 0);
    let x = 0, used = 0;
    const W = 520;
    svg('text', { x: 0, y: 14, class: 'tm', text: 'lane ↓   time →' }, s);
    d.passes.forEach((p, k) => {
      const w = W * p.cyc / total;
      for (let i = 0; i < 32; i++) {
        const on = p.act(i); if (on) used += p.cyc;
        svg('rect', { x: 120 + x + 1, y: 24 + i * 6, width: Math.max(1, w - 2), height: 5, style: `fill:${on ? 'var(--a)' : 'var(--line)'}` }, s);
      }
      svg('text', { x: 120 + x + w / 2, y: 222, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: p.name }, s);
      x += w;
    });
    for (let i = 0; i < 32; i += 4) svg('text', { x: 100, y: 29 + i * 6, 'text-anchor': 'end', class: 'tm tc', style: 'font-size:9px', text: i }, s);
    Deck.out('divPass', d.passes.length);
    const u = used / (32 * total);
    Deck.out('divUtil', (100 * u).toFixed(0) + '%');
    document.getElementById('divUtil').style.color = u > .9 ? 'var(--e)' : u > .4 ? 'var(--b)' : 'var(--d)';
    Deck.out('divNote', d.note);
  });

  /* ---------- latency hiding ---------- */
  Deck.bind(['hW', 'hL'], () => {
    const W = Deck.val('hW'), L = Deck.val('hL'), C = 40, T = 1600;
    Deck.out('hWo', W); Deck.out('hLo', L);
    const ready = Array(W).fill(0), segs = Array.from({ length: W }, () => []), busy = [];
    let t = 0;
    while (t < T) {
      let k = 0; for (let i = 1; i < W; i++) if (ready[i] < ready[k]) k = i;
      if (ready[k] > t) t = ready[k];
      if (t >= T) break;
      segs[k].push([t, Math.min(T, t + C)]); busy.push([t, Math.min(T, t + C)]);
      ready[k] = t + C + L; t += C;
    }
    const s = clear(document.getElementById('hideSvg'));
    const rowH = Math.min(16, 230 / W), x0 = 60, sc = 590 / T;
    s.setAttribute('viewBox', `0 0 660 ${W * rowH + 70}`);
    for (let i = 0; i < W; i++) {
      const y = 6 + i * rowH;
      svg('text', { x: 0, y: y + rowH * .75, class: 'tm tc', style: `font-size:${Math.min(11, rowH * .8)}px`, text: 'warp ' + i }, s);
      svg('rect', { x: x0, y, width: 590, height: rowH - 3, class: 'f-panel' }, s);
      segs[i].forEach(([a, b]) => svg('rect', { x: x0 + a * sc, y, width: (b - a) * sc, height: rowH - 3, class: 'f-a' }, s));
    }
    const by = 14 + W * rowH;
    svg('text', { x: 0, y: by + 12, class: 'tm', style: 'font-size:11px', text: 'issue' }, s);
    svg('rect', { x: x0, y: by, width: 590, height: 16, class: 'f-panel' }, s);
    busy.forEach(([a, b]) => svg('rect', { x: x0 + a * sc, y: by, width: (b - a) * sc, height: 16, class: 'f-b' }, s));
    svg('text', { x: x0, y: by + 36, class: 'tm tc', style: 'font-size:10px', text: '0' }, s);
    svg('text', { x: x0 + 590, y: by + 36, 'text-anchor': 'end', class: 'tm tc', style: 'font-size:10px', text: T + ' cycles' }, s);
    const u = busy.reduce((a, [p, q]) => a + q - p, 0) / T;
    const need = Math.ceil((C + L) / C);
    document.getElementById('hideOut').innerHTML = `Scheduler busy <span style="color:${u > .9 ? 'var(--e)' : 'var(--d)'}">${(100 * u).toFixed(0)}%</span> of cycles · needs ≈ ${need} warps to saturate`;
  });

  /* ---------- tensor cores ---------- */
  (function mma() {
    const s = document.getElementById('mmaSvg');
    const mat = (x, y, n, cls, lab) => {
      for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) svg('rect', { x: x + j * 14, y: y + i * 14, width: 12, height: 12, rx: 2, class: cls, opacity: .85 }, s);
      svg('text', { x: x + n * 7, y: y + n * 14 + 18, 'text-anchor': 'middle', class: 't', style: 'font-weight:700', text: lab }, s);
    };
    mat(10, 50, 4, 'f-a', 'A'); svg('text', { x: 78, y: 82, class: 't', style: 'font-size:22px', text: '×' }, s);
    mat(100, 50, 4, 'f-c', 'B'); svg('text', { x: 168, y: 82, class: 't', style: 'font-size:22px', text: '+' }, s);
    mat(190, 50, 4, 'f-b', 'C'); svg('text', { x: 258, y: 82, class: 't', style: 'font-size:22px', text: '=' }, s);
    mat(285, 50, 4, 'f-e', 'D');
    svg('text', { x: 190, y: 30, 'text-anchor': 'middle', class: 'tm', text: 'one MMA instruction: many FMAs in one operation' }, s);
    svg('text', { x: 190, y: 180, 'text-anchor': 'middle', class: 'tm', text: 'inputs BF16/FP8, accumulate in FP32' }, s);
  })();
  Deck.seg('tcSeg', v => {
    const m = v === 'sparse' ? 2 : 1;
    Deck.hbars(document.getElementById('tcBars'), [
      { label: 'FP64 (CUDA)', value: 34, color: 'var(--faint)', text: '34' },
      { label: 'FP32 (CUDA)', value: 67, color: 'var(--b)', text: '67' },
      { label: 'TF32 Tensor', value: 495 * m, color: 'var(--c)', text: fmt(495 * m) },
      { label: 'BF16 Tensor', value: 989 * m, color: 'var(--a)', text: fmt(989 * m) },
      { label: 'FP8 Tensor', value: 1979 * m, color: 'var(--e)', text: fmt(1979 * m) },
      { label: 'INT8 Tensor', value: 1979 * m, color: 'var(--e)', text: fmt(1979 * m) },
    ], { log: true, max: 4000, min: 15 });
  });

  /* ---------- wave quantization ---------- */
  let tile = 128;
  const wave = () => {
    const M = Deck.val('qM'), N = Deck.val('qN');
    Deck.out('qMo', M); Deck.out('qNo', N);
    const tm = Math.ceil(M / tile), tn = Math.ceil(N / tile), tiles = tm * tn, SM = 132;
    const waves = Math.ceil(tiles / SM), last = tiles - (waves - 1) * SM, eff = tiles / (waves * SM);
    Deck.out('qTiles', tiles.toLocaleString()); Deck.out('qWaves', waves); Deck.out('qLast', `${last} / 132`);
    Deck.out('qEff', (100 * eff).toFixed(0) + '%');
    document.getElementById('qEff').style.color = eff > .9 ? 'var(--e)' : eff > .7 ? 'var(--b)' : 'var(--d)';
    const s = clear(document.getElementById('waveSvg'));
    const maxSide = 300, c = Math.min(maxSide / tm, 640 / tn);
    s.setAttribute('viewBox', `0 0 660 ${tm * c + 20}`);
    for (let i = 0; i < tm; i++) for (let j = 0; j < tn; j++) {
      const k = i * tn + j, w = Math.floor(k / SM);
      const col = w === waves - 1 && last < SM ? 'var(--b)' : (w % 2 ? 'var(--c)' : 'var(--a)');
      svg('rect', { x: 10 + j * c, y: 10 + i * c, width: Math.max(.5, c - (c > 4 ? 1 : 0)), height: Math.max(.5, c - (c > 4 ? 1 : 0)), style: `fill:${col};opacity:${.55 + .45 * ((w % 3) / 2)}` }, s);
    }
  };
  Deck.seg('qT', v => { tile = +v; if (document.getElementById('qM')) wave(); });
  Deck.bind(['qM', 'qN'], wave);
})();
