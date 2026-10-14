(() => {
  const { svg, clear, fmt } = Deck;
  const rng = seed => () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  const COL = ['var(--a)', 'var(--b)', 'var(--c)', 'var(--e)', 'var(--d)', '#3a8fd8', '#c9a227', '#8a6d3b', '#5f9ea0', '#b05aa8'];

  /* why share */
  const WL = [
    ['Jupyter notebook', 5, 8], ['Embedding service', 15, 6], ['Reranker', 12, 4], ['7B chat (low QPS)', 30, 24],
    ['CI unit tests', 10, 10], ['Eval harness', 35, 30], ['Data filtering model', 20, 12], ['Whisper ASR', 18, 6],
    ['Notebook #2', 4, 8], ['Safety classifier', 10, 5],
  ];
  const wl = document.getElementById('wl');
  wl.innerHTML = WL.map((w, i) => `<label><input type="checkbox" data-i="${i}" ${i < 8 ? 'checked' : ''}><i style="display:inline-block;width:10px;height:10px;border-radius:2px;background:${COL[i]}"></i>${w[0]} · ${w[1]}%</label>`).join('');
  const pack = () => {
    const on = Deck.$$('input', wl).filter(x => x.checked).map(x => +x.dataset.i);
    const bins = [];
    on.forEach(i => {
      const [_, c, m] = WL[i];
      let b = bins.find(b => b.c + c <= 90 && b.m + m <= 80);
      if (!b) { b = { c: 0, m: 0, items: [] }; bins.push(b); }
      b.c += c; b.m += m; b.items.push(i);
    });
    const s = clear(document.getElementById('packSvg'));
    const n = Math.max(1, bins.length), bw = Math.min(70, 340 / n - 8);
    bins.forEach((b, k) => {
      const x = 10 + k * (bw + 8);
      svg('rect', { x, y: 10, width: bw, height: 160, rx: 6, style: 'fill:var(--panel-2);stroke:var(--line)' }, s);
      let y = 170;
      b.items.forEach(i => { const h = WL[i][1] * 1.6; y -= h; svg('rect', { x: x + 3, y, width: bw - 6, height: h - 1, rx: 2, style: `fill:${COL[i]}` }, s); });
      svg('text', { x: x + bw / 2, y: 188, 'text-anchor': 'middle', class: 'tm tc', style: 'font-size:10px', text: b.c + '%' }, s);
    });
    Deck.out('pkWhole', on.length); Deck.out('pkShared', bins.length);
    const avg = on.length ? on.reduce((a, i) => a + WL[i][1], 0) / on.length : 0;
    Deck.out('pkUtil', avg.toFixed(0) + '%'); Deck.out('pkSave', on.length - bins.length);
  };
  wl.addEventListener('change', pack); pack();

  /* spectrum */
  const SP = [
    { n: 'Whole GPU', x: 0.1, y: 0.95, t: '<b>Whole GPU per job</b>: perfect isolation and the simplest option, but utilization is poor for small jobs.' },
    { n: 'MIG', x: 0.35, y: 0.8, t: '<b>MIG</b>: hardware partitions with their own SMs, L2 slice and memory controllers. Guaranteed QoS and fault isolation, but fixed sizes and a drain is needed to reconfigure.' },
    { n: 'vGPU', x: 0.5, y: 0.6, t: '<b>vGPU (virtualization)</b>: the hypervisor shares the GPU among VMs, either time-sliced or backed by MIG. Used in clouds and VDI. Needs a license, and a VM boundary gives security isolation.' },
    { n: 'MPS', x: 0.75, y: 0.35, t: '<b>MPS</b>: one shared context, so kernels from several processes run at the same time. You can cap each client\'s SM share and memory, but fault isolation is weak.' },
    { n: 'Time-slicing', x: 0.9, y: 0.15, t: '<b>Time-slicing</b>: processes (or Kubernetes "replicas" of one GPU) take turns. Any number of tenants, but no memory isolation (one can OOM the others) and no performance guarantees.' },
  ];
  const sp = document.getElementById('spSvg');
  const L = 40, B = 240, W = 300, H = 210;
  svg('line', { x1: L, y1: B, x2: L + W, y2: B, class: 's-line', 'stroke-width': 2 }, sp);
  svg('line', { x1: L, y1: B, x2: L, y2: B - H, class: 's-line', 'stroke-width': 2 }, sp);
  svg('text', { x: L + W / 2, y: B + 26, 'text-anchor': 'middle', class: 'tm', text: 'flexibility / packing density →' }, sp);
  svg('text', { x: 14, y: B - H / 2, 'text-anchor': 'middle', class: 'tm', transform: `rotate(-90 14 ${B - H / 2})`, text: 'isolation →' }, sp);
  SP.forEach((p, i) => {
    const cx = L + p.x * W, cy = B - p.y * H;
    svg('circle', { cx, cy, r: 11, 'data-i': i, style: `fill:${COL[i]};stroke:var(--panel);stroke-width:2` }, sp);
    svg('text', { x: cx + (p.x > .8 ? -15 : 15), y: cy + 4, 'text-anchor': p.x > .8 ? 'end' : 'start', class: 't', style: 'font-weight:600;font-size:12px;pointer-events:none', text: p.n }, sp);
  });
  sp.addEventListener('click', e => { const c = e.target.closest('[data-i]'); if (c) document.getElementById('spInfo').innerHTML = SP[+c.dataset.i].t; });
  sp.addEventListener('mouseover', e => { const c = e.target.closest('[data-i]'); if (c) document.getElementById('spInfo').innerHTML = SP[+c.dataset.i].t; });

  /* time-slicing vs MPS */
  let tsMode = 'ts';
  const ts = () => {
    const n = Deck.val('tsN'), d = Deck.val('tsD') / 100;
    Deck.out('tsNo', n); Deck.out('tsDo', (d * 100).toFixed(0) + '%');
    const s = clear(document.getElementById('tsSvg'));
    const L = 60, W = 590, T = 12, H = 190, slots = 12, sw = W / slots;
    svg('rect', { x: L, y: T, width: W, height: H, style: 'fill:var(--panel-2)' }, s);
    svg('text', { x: L - 6, y: T + 10, 'text-anchor': 'end', class: 'tm', style: 'font-size:10px', text: '100%' }, s);
    svg('text', { x: L - 6, y: T + H, 'text-anchor': 'end', class: 'tm', style: 'font-size:10px', text: '0%' }, s);
    svg('text', { x: 14, y: T + H / 2, 'text-anchor': 'middle', class: 'tm', transform: `rotate(-90 14 ${T + H / 2})`, text: 'SMs in use' }, s);
    svg('text', { x: L + W / 2, y: T + H + 22, 'text-anchor': 'middle', class: 'tm', text: 'time →' }, s);
    let util, slow;
    if (tsMode === 'ts') {
      for (let k = 0; k < slots; k++) {
        const p = k % n, x = L + k * sw;
        svg('rect', { x: x + sw * .05, y: T + H - d * H, width: sw * .9, height: d * H, style: `fill:${COL[p]}` }, s);
        if (n > 1) svg('rect', { x: x + sw * .95, y: T, width: sw * .05, height: H, style: 'fill:var(--d);opacity:.5' }, s);
        svg('text', { x: x + sw / 2, y: T + H - d * H - 6, 'text-anchor': 'middle', class: 'tm tc', style: 'font-size:10px', text: 'P' + p }, s);
      }
      util = d * (n > 1 ? .9 : 1); slow = n / (n > 1 ? .9 : 1);
    } else {
      const total = n * d, scale = Math.min(1, 1 / total);
      for (let k = 0; k < slots; k++) {
        let y = T + H;
        for (let p = 0; p < n; p++) {
          const h = d * scale * H; y -= h;
          svg('rect', { x: L + k * sw + 1, y, width: sw - 2, height: h - 1, style: `fill:${COL[p]}` }, s);
        }
      }
      util = Math.min(1, total); slow = Math.max(1, total);
    }
    Deck.out('tsUtil', (util * 100).toFixed(0) + '%');
    Deck.out('tsLat', slow.toFixed(1) + '×');
    document.getElementById('tsUtil').style.color = util > .7 ? 'var(--e)' : 'var(--d)';
    Deck.out('tsMem', tsMode === 'ts' ? 'Shared, no limits (OOM risk)' : 'Shared, optional per-client limit');
  };
  Deck.seg('tsMode', v => { tsMode = v; if (document.getElementById('tsN')) ts(); });
  Deck.bind(['tsN', 'tsD'], ts);

  /* MIG */
  const PROF = [['1g.10gb', 1, 1], ['1g.20gb', 1, 2], ['2g.20gb', 2, 2], ['3g.40gb', 3, 4], ['4g.40gb', 4, 4], ['7g.80gb', 7, 8]];
  let inst = [[3, 4, 0], [2, 2, 1], [1, 1, 2], [1, 1, 3]].map(([c, m, k]) => ({ name: PROF.find(p => p[1] === c && p[2] === m)[0], c, m, id: k }));
  let nid = 10;
  const mb = document.getElementById('migBtns');
  mb.innerHTML = PROF.map((p, i) => `<button class="btn" data-p="${i}">+ ${p[0]}</button>`).join('');
  const drawMig = msg => {
    const s = clear(document.getElementById('migSvg'));
    const uc = inst.reduce((a, x) => a + x.c, 0), um = inst.reduce((a, x) => a + x.m, 0);
    const cw = 560 / 7, mw = 560 / 8;
    svg('text', { x: 0, y: 40, class: 'tm', style: 'font-size:11px', text: 'compute' }, s);
    svg('text', { x: 0, y: 130, class: 'tm', style: 'font-size:11px', text: 'memory' }, s);
    for (let i = 0; i < 7; i++) svg('rect', { x: 80 + i * cw, y: 14, width: cw - 4, height: 50, rx: 5, style: 'fill:var(--panel-2);stroke:var(--line);stroke-dasharray:3 3' }, s);
    for (let i = 0; i < 8; i++) svg('rect', { x: 80 + i * mw, y: 104, width: mw - 4, height: 50, rx: 5, style: 'fill:var(--panel-2);stroke:var(--line);stroke-dasharray:3 3' }, s);
    let cx = 0, mx = 0;
    inst.forEach((x, k) => {
      const col = COL[k % COL.length];
      const g = svg('g', { 'data-id': x.id, style: 'cursor:pointer' }, s);
      svg('rect', { x: 80 + cx * cw, y: 14, width: x.c * cw - 4, height: 50, rx: 5, style: `fill:${col}` }, g);
      svg('text', { x: 80 + cx * cw + (x.c * cw - 4) / 2, y: 44, 'text-anchor': 'middle', class: 't tc', style: 'fill:#fff;font-size:11px;font-weight:600', text: x.name }, g);
      svg('rect', { x: 80 + mx * mw, y: 104, width: x.m * mw - 4, height: 50, rx: 5, style: `fill:${col};opacity:.8` }, g);
      svg('text', { x: 80 + mx * mw + (x.m * mw - 4) / 2, y: 134, 'text-anchor': 'middle', class: 't tc', style: 'fill:#fff;font-size:11px;font-weight:600', text: x.m * 10 + ' GB' }, g);
      svg('line', { x1: 80 + cx * cw + (x.c * cw - 4) / 2, y1: 64, x2: 80 + mx * mw + (x.m * mw - 4) / 2, y2: 104, style: `stroke:${col};stroke-width:2;opacity:.6` }, g);
      cx += x.c; mx += x.m;
    });
    svg('text', { x: 80, y: 182, class: 'tm tc', style: 'font-size:11px', text: `${inst.length} instance${inst.length === 1 ? '' : 's'} · compute ${uc}/7 · memory ${um * 10}/80 GB` }, s);
    document.getElementById('migOut').innerHTML = msg || (uc === 7 || um === 8 ? '<span style="color:var(--e)">GPU fully partitioned</span>' : `${7 - uc} compute slice(s) and ${(8 - um) * 10} GB free`);
  };
  mb.addEventListener('click', e => {
    const b = e.target.closest('[data-p]'); if (!b) return;
    const [name, c, m] = PROF[+b.dataset.p];
    const uc = inst.reduce((a, x) => a + x.c, 0), um = inst.reduce((a, x) => a + x.m, 0);
    if (uc + c > 7 || um + m > 8) { drawMig(`<span style="color:var(--d)">✗ ${name} doesn't fit: needs ${c} compute + ${m * 10} GB, only ${7 - uc} + ${(8 - um) * 10} GB free</span>`); return; }
    if (inst.length >= 7) { drawMig('<span style="color:var(--d)">✗ Max 7 instances per GPU</span>'); return; }
    inst.push({ name, c, m, id: nid++ }); drawMig();
  });
  document.getElementById('migSvg').addEventListener('click', e => {
    const g = e.target.closest('[data-id]'); if (!g) return;
    inst = inst.filter(x => x.id !== +g.dataset.id); drawMig();
  });
  document.getElementById('migClear').onclick = () => { inst = []; drawMig(); };
  drawMig();

  /* continuous batching */
  let cbMode = 'static', reqs = [], seed = 5;
  const newReqs = () => { const r = rng(seed++); reqs = [...Array(12)].map(() => Math.round(4 + r() * r() * 36)); };
  const cb = () => {
    const slots = 4, sched = [];
    if (cbMode === 'static') {
      for (let b = 0, t = 0; b < reqs.length; b += slots) {
        const batch = reqs.slice(b, b + slots), mx = Math.max(...batch);
        batch.forEach((len, k) => sched.push({ i: b + k, slot: k, start: t, len, pad: mx - len }));
        t += mx;
      }
    } else {
      const free = Array(slots).fill(0);
      reqs.forEach((len, i) => {
        let k = 0; for (let j = 1; j < slots; j++) if (free[j] < free[k]) k = j;
        sched.push({ i, slot: k, start: free[k], len, pad: 0 }); free[k] += len;
      });
    }
    const T = Math.max(...sched.map(x => x.start + x.len + x.pad));
    const s = clear(document.getElementById('cbSvg'));
    const L = 60, W = 590, sc = W / Math.max(T, 1);
    for (let k = 0; k < slots; k++) {
      svg('text', { x: 0, y: 30 + k * 40, class: 'tm tc', style: 'font-size:11px', text: 'slot ' + k }, s);
      svg('rect', { x: L, y: 12 + k * 40, width: W, height: 30, style: 'fill:var(--panel-2)' }, s);
    }
    sched.forEach(x => {
      const y = 12 + x.slot * 40;
      svg('rect', { x: L + x.start * sc + .5, y, width: x.len * sc - 1, height: 30, rx: 3, style: `fill:${COL[x.i % COL.length]}` }, s);
      if (x.len * sc > 18) svg('text', { x: L + (x.start + x.len / 2) * sc, y: y + 19, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:10px;font-weight:600', text: 'r' + x.i }, s);
      if (x.pad) svg('rect', { x: L + (x.start + x.len) * sc, y, width: x.pad * sc, height: 30, style: 'fill:var(--d-soft);stroke:var(--d);stroke-width:.5;stroke-dasharray:3 2' }, s);
    });
    svg('text', { x: L, y: 190, class: 'tm', style: 'font-size:11px', text: cbMode === 'static' ? 'red hatched = slot held by a finished request (padding) until the batch\'s longest request ends' : 'a new request starts the moment a slot frees up' }, s);
    const used = reqs.reduce((a, b) => a + b, 0);
    Deck.out('cbT', T); Deck.out('cbU', (100 * used / (slots * T)).toFixed(0) + '%');
    Deck.out('cbW', (sched.reduce((a, x) => a + x.start, 0) / sched.length).toFixed(1) + ' steps');
  };
  newReqs();
  Deck.seg('cbMode', v => { cbMode = v; cb(); });
  document.getElementById('cbNew').onclick = () => { newReqs(); cb(); };

  /* multi-LoRA */
  Deck.bind(['lN', 'lR'], () => {
    const N = Deck.val('lN'), r = Math.pow(2, Deck.val('lR'));
    Deck.out('lNo', N); Deck.out('lRo', r);
    const d = 8192, kv = 1024, ff = 28672;
    const perLayer = r * ((d + d) + (d + kv) * 2 + (d + d) + (d + ff) * 2 + (ff + d));
    const adB = perLayer * 80 * 2, base = 140e9;
    const full = N * base, multi = base + N * adB;
    Deck.hbars(document.getElementById('lBars'), [
      { label: `${N} full fine-tunes`, value: full, color: 'var(--d)', text: Deck.bytes(full) },
      { label: `1 base + ${N} LoRAs`, value: multi, color: 'var(--e)', text: Deck.bytes(multi) },
    ], { log: true, min: 1e10, max: Math.max(full, 2e11) * 1.5 });
    Deck.out('lAd', Deck.bytes(adB));
    Deck.out('lFull', fmt(Math.ceil(full / 80e9) , 0)); Deck.out('lMulti', Math.ceil(multi / 80e9));
  });

  /* scheduler */
  Deck.seg('scMode', v => {
    const s = clear(document.getElementById('scSvg'));
    const nodes = 6, g = 8;
    const grid = [...Array(nodes)].map(() => Array(g).fill(null));
    const small = [['A', 3], ['B', 2], ['C', 4], ['D', 1], ['E', 2], ['F', 3], ['G', 2], ['H', 3], ['I', 4], ['J', 4]];
    const lowpri = [['L', 8]];
    if (v === 'frag') {
      let n = 0; small.forEach(([id, k]) => { for (let i = 0; i < k; i++) { let slot = grid[n].indexOf(null); grid[n][slot] = id; n = (n + 1) % nodes; } });
      for (let i = 0; i < g; i++) if (!grid[5][i]) { grid[5][i] = 'L'; }
    } else {
      let n = 0, slot = 0;
      [...small].forEach(([id, k]) => { for (let i = 0; i < k; i++) { grid[n][slot++] = id; if (slot === g) { slot = 0; n++; } } });
      if (v === 'pack') { for (let i = 0; i < g; i++) grid[5][i] = 'L'; }
    }
    const big = { id: 'BIG', need: 2 };
    const fullFree = grid.map((r, i) => r.every(x => x === null) ? i : -1).filter(i => i >= 0);
    const placed = fullFree.length >= big.need;
    if (placed) fullFree.slice(0, 2).forEach(n => grid[n].fill('BIG'));
    const colOf = id => id === 'BIG' ? 'var(--e)' : id === 'L' ? 'var(--faint)' : COL['ABCDEFGHIJ'.indexOf(id) % COL.length];
    grid.forEach((row, n) => {
      const x = 10 + n * 108;
      svg('rect', { x, y: 10, width: 100, height: 150, rx: 8, style: 'fill:var(--panel-2);stroke:var(--line)' }, s);
      svg('text', { x: x + 50, y: 176, 'text-anchor': 'middle', class: 'tm tc', style: 'font-size:11px', text: 'node ' + n }, s);
      row.forEach((id, i) => {
        const gx = x + 8 + (i % 2) * 44, gy = 18 + Math.floor(i / 2) * 35;
        svg('rect', { x: gx, y: gy, width: 40, height: 30, rx: 4, style: id ? `fill:${colOf(id)}` : 'fill:var(--panel);stroke:var(--line);stroke-dasharray:3 2' }, s);
        if (id) svg('text', { x: gx + 20, y: gy + 19, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:10px;font-weight:700', text: id === 'BIG' ? '16-GPU' : id }, s);
      });
    });
    const free = grid.flat().filter(x => x === null).length;
    document.getElementById('scOut').innerHTML = {
      frag: `<span style="color:var(--d)">✗ ${free} GPUs free, but the 16-GPU training job (2 whole nodes) can't start:</span> small jobs A–J are spread across every node.`,
      pack: `<span style="color:var(--b)">Bin-packed:</span> small jobs fill nodes 0–3 tightly. ${placed ? '<span style="color:var(--e)">The 16-GPU job fits.</span>' : `Only ${fullFree.length} whole node(s) free, and a low-priority job (L) holds node 5.`}`,
      pre: `<span style="color:var(--e)">✓ Packed and low-priority job L preempted (after checkpoint):</span> the 16-GPU gang starts on 2 whole nodes.`,
    }[v];
  });
})();
