(() => {
  const { svg, clear, fmt, bytes } = Deck;

  /* tiers */
  Deck.seg('tierSeg', v => {
    const s = clear(document.getElementById('tierSvg'));
    const nodes = 4, g = 8, nx = 60, gw = 62, nh = 54;
    const gpuX = i => nx + 12 + i * (gw + 9), nodeY = n => 14 + n * 70;
    if (v === 'dp') for (let i = 0; i < g; i++) svg('line', { x1: gpuX(i) + gw / 2, y1: nodeY(0) + 30, x2: gpuX(i) + gw / 2, y2: nodeY(3) + 30, style: 'stroke:var(--b);stroke-width:4;opacity:.75' }, s);
    if (v === 'pp') for (let n = 0; n < nodes - 1; n++) {
      svg('path', { d: `M ${nx + 590} ${nodeY(n) + 30} C ${nx + 640} ${nodeY(n) + 40}, ${nx + 640} ${nodeY(n + 1) + 20}, ${nx + 590} ${nodeY(n + 1) + 30}`, fill: 'none', style: 'stroke:var(--c);stroke-width:4' }, s);
    }
    for (let n = 0; n < nodes; n++) {
      svg('rect', { x: nx, y: nodeY(n), width: 590, height: nh + 6, rx: 10, style: `fill:${v === 'tp' ? 'var(--e-soft)' : 'var(--panel-2)'};stroke:${v === 'tp' ? 'var(--e)' : 'var(--line)'};stroke-width:${v === 'tp' ? 2.5 : 1}` }, s);
      svg('text', { x: 8, y: nodeY(n) + 35, class: 'tm tc', text: 'node ' + n }, s);
      for (let i = 0; i < g; i++) {
        svg('rect', { x: gpuX(i), y: nodeY(n) + 10, width: gw, height: 40, rx: 6, class: 'f-a' }, s);
        svg('text', { x: gpuX(i) + gw / 2, y: nodeY(n) + 35, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11px', text: (v === 'pp' ? 'stage ' + n : v === 'dp' ? 'rank ' + i : 'TP ' + i) }, s);
      }
    }
    const msg = {
      tp: '<span class="ok">TP group = the 8 GPUs of one node.</span> 2 all-reduces per layer, on the critical path, over NVLink at 450 GB/s.',
      dp: '<span style="color:var(--b);font-weight:600">DP group = the same local rank on every node.</span> One gradient all-reduce per step, overlapped with backward, over the network on that GPU\'s rail.',
      pp: '<span style="color:var(--c);font-weight:600">PP: each node is one stage.</span> Activations are sent point-to-point to the next node: small and latency-tolerant when there are enough micro-batches.',
    };
    document.getElementById('tierOut').innerHTML = msg[v];
  });

  /* fat tree */
  let sel = [0, 13];
  const ft = () => {
    const U = Deck.val('ftU'); Deck.out('ftUo', U);
    const s = clear(document.getElementById('ftSvg'));
    const leaves = 4, eps = 16, spX = j => 330 - (U - 1) * 80 + j * 160 * (U > 1 ? 1 : 0) / 1, lfX = l => 90 + l * 160, epX = e => 40 + e * 37.5;
    const spineXs = [...Array(U)].map((_, j) => U === 1 ? 330 : 90 + j * (480 / (U - 1)));
    const la = Math.floor(sel[0] / 4), lb = Math.floor(sel[1] / 4), cross = la !== lb;
    const sp = 0;
    for (let l = 0; l < leaves; l++) spineXs.forEach((x, j) => {
      const on = cross && j === sp && (l === la || l === lb);
      svg('line', { x1: lfX(l), y1: 140, x2: x, y2: 50, style: `stroke:${on ? 'var(--a)' : 'var(--line)'};stroke-width:${on ? 4 : 2}` }, s);
    });
    for (let e = 0; e < eps; e++) {
      const l = Math.floor(e / 4), on = sel.includes(e);
      svg('line', { x1: epX(e), y1: 250, x2: lfX(l), y2: 166, style: `stroke:${on ? 'var(--a)' : 'var(--line)'};stroke-width:${on ? 4 : 1.5}` }, s);
    }
    spineXs.forEach((x, j) => {
      svg('rect', { x: x - 50, y: 26, width: 100, height: 28, rx: 6, style: `fill:${cross && j === sp ? 'var(--a)' : 'var(--c)'}` }, s);
      svg('text', { x, y: 45, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11.5px;font-weight:600', text: 'spine ' + j }, s);
    });
    for (let l = 0; l < leaves; l++) {
      const on = l === la || l === lb;
      svg('rect', { x: lfX(l) - 55, y: 140, width: 110, height: 28, rx: 6, style: `fill:${on ? 'var(--a)' : 'var(--b)'}` }, s);
      svg('text', { x: lfX(l), y: 159, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11.5px;font-weight:600', text: 'leaf ' + l }, s);
    }
    for (let e = 0; e < eps; e++) {
      const on = sel.includes(e);
      const c = svg('circle', { cx: epX(e), cy: 262, r: 11, class: 'ep', 'data-e': e, style: `fill:${on ? 'var(--a)' : 'var(--panel-2)'};stroke:var(--a);stroke-width:2` }, s);
      svg('text', { x: epX(e), y: 266, 'text-anchor': 'middle', class: 'tm tc', style: `font-size:9.5px;pointer-events:none;fill:${on ? '#fff' : 'var(--muted)'}`, text: e }, s);
    }
    svg('text', { x: 330, y: 294, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: 'click endpoints (NICs) to pick a pair' }, s);
    Deck.out('ftHops', cross ? '3 (leaf → spine → leaf)' : '1 (same leaf)');
    document.getElementById('ftHops').style.fontSize = '18px';
    Deck.out('ftOver', `4 : ${U}`);
    Deck.out('ftBW', (400 * U / 4).toFixed(0) + ' Gb/s');
    document.getElementById('ftBW').style.color = U === 4 ? 'var(--e)' : 'var(--d)';
  };
  document.getElementById('ftSvg').addEventListener('click', e => {
    const c = e.target.closest('[data-e]'); if (!c) return;
    sel = [sel[1], +c.dataset.e]; ft();
  });
  Deck.bind(['ftU'], ft);

  /* rails */
  Deck.seg('railSeg', v => {
    const s = clear(document.getElementById('railSvg'));
    const N = 4, R = 4, nodeX = n => 30 + n * 160, gpuX = (n, r) => nodeX(n) + 12 + r * 34, leafX = l => 60 + l * 160;
    const src = [0, 2], dst = [2, 2];
    const rail = v === 'rail';
    const leafOf = (n, r) => rail ? r : n;
    const L1 = leafOf(...src), L2 = leafOf(...dst), cross = L1 !== L2;
    svg('rect', { x: 230, y: 14, width: 200, height: 30, rx: 6, style: `fill:${cross ? 'var(--d)' : 'var(--c)'}` }, s);
    svg('text', { x: 330, y: 34, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:600;font-size:12px', text: 'spine' }, s);
    for (let l = 0; l < 4; l++) {
      const on = l === L1 || l === L2;
      svg('line', { x1: leafX(l) + 50, y1: 110, x2: 330, y2: 44, style: `stroke:${on && cross ? 'var(--d)' : 'var(--line)'};stroke-width:${on && cross ? 4 : 2}` }, s);
    }
    for (let n = 0; n < N; n++) for (let r = 0; r < R; r++) {
      const isPath = (n === src[0] && r === src[1]) || (n === dst[0] && r === dst[1]);
      const l = leafOf(n, r);
      svg('line', { x1: gpuX(n, r) + 14, y1: 210, x2: leafX(l) + 50, y2: 140, style: `stroke:${isPath ? 'var(--a)' : ['var(--a)', 'var(--b)', 'var(--c)', 'var(--e)'][r]};stroke-width:${isPath ? 4 : 1.3};opacity:${isPath ? 1 : .45}` }, s);
    }
    for (let l = 0; l < 4; l++) {
      const on = l === L1 || l === L2;
      svg('rect', { x: leafX(l), y: 110, width: 100, height: 30, rx: 6, style: `fill:${on ? 'var(--a)' : 'var(--b)'}` }, s);
      svg('text', { x: leafX(l) + 50, y: 130, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11.5px;font-weight:600', text: rail ? `leaf · rail ${l}` : `leaf · ToR ${l}` }, s);
    }
    for (let n = 0; n < N; n++) {
      svg('rect', { x: nodeX(n), y: 206, width: 148, height: 70, rx: 8, style: 'fill:var(--panel-2);stroke:var(--line)' }, s);
      svg('text', { x: nodeX(n) + 74, y: 298, 'text-anchor': 'middle', class: 'tm', text: 'node ' + n }, s);
      for (let r = 0; r < R; r++) {
        const on = (n === src[0] && r === src[1]) || (n === dst[0] && r === dst[1]);
        svg('rect', { x: gpuX(n, r), y: 222, width: 28, height: 40, rx: 4, style: `fill:${['var(--a)', 'var(--b)', 'var(--c)', 'var(--e)'][r]};opacity:${on ? 1 : .5};${on ? 'stroke:var(--ink);stroke-width:2.5' : ''}` }, s);
        svg('text', { x: gpuX(n, r) + 14, y: 246, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:10px;font-weight:700', text: 'G' + r }, s);
      }
    }
    document.getElementById('railOut').innerHTML = rail
      ? '<span class="ok">Node 0 · GPU 2 → node 2 · GPU 2: 1 switch hop</span> (both on rail 2). DP/PP traffic never reaches the spine.'
      : '<span class="warn">Node 0 · GPU 2 → node 2 · GPU 2: 3 switch hops</span> (ToR 0 → spine → ToR 2). Every DP flow loads the spine.';
  });

  /* collectives */
  const COL = ['var(--a)', 'var(--b)', 'var(--c)', 'var(--e)'];
  const COLL = {
    ar: { info: '<b>All-reduce</b>: every GPU ends up with the sum (or mean) of all inputs. Used for <b>DP gradient sync</b> and the <b>TP partial-sum</b> after row-parallel matmuls.', before: g => [0, 1, 2, 3].map(c => [g]), after: g => [0, 1, 2, 3].map(() => [0, 1, 2, 3]) },
    rs: { info: '<b>Reduce-scatter</b>: the sum is computed, but each GPU keeps only its 1/N slice. Used for <b>FSDP/ZeRO gradient sharding</b> and sequence-parallel TP.', before: g => [0, 1, 2, 3].map(() => [g]), after: g => [0, 1, 2, 3].map(c => c === g ? [0, 1, 2, 3] : null) },
    ag: { info: '<b>All-gather</b>: each GPU contributes its slice and every GPU ends up with all slices. Used by <b>FSDP to rebuild a layer\'s weights</b> just before computing it.', before: g => [0, 1, 2, 3].map(c => c === g ? [g] : null), after: g => [0, 1, 2, 3].map(c => [c]) },
    bc: { info: '<b>Broadcast</b>: one GPU sends the same data to all. Used for initial weight sync and distributing configuration or random seeds.', before: g => [0, 1, 2, 3].map(() => g === 0 ? [0] : null), after: g => [0, 1, 2, 3].map(() => [0]) },
    a2a: { info: '<b>All-to-all</b>: GPU g sends a <em>different</em> chunk to each GPU (chunk j goes to GPU j). Used for <b>MoE token dispatch and combine</b>, and for Ulysses-style sequence parallelism.', before: g => [0, 1, 2, 3].map(c => [g, c]), after: g => [0, 1, 2, 3].map(c => [c, g]) },
  };
  Deck.seg('collSeg', v => {
    const s = clear(document.getElementById('collSvg')), c = COLL[v];
    const drawSide = (x0, fn, title) => {
      svg('text', { x: x0 + 125, y: 18, 'text-anchor': 'middle', class: 't', style: 'font-weight:700', text: title }, s);
      for (let g = 0; g < 4; g++) {
        const y = 30 + g * 52;
        svg('text', { x: x0, y: y + 27, class: 'tm tc', text: 'GPU' + g }, s);
        fn(g).forEach((cell, k) => {
          const x = x0 + 46 + k * 52;
          if (!cell) { svg('rect', { x, y, width: 46, height: 40, rx: 5, style: 'fill:var(--panel-2);stroke:var(--line);stroke-dasharray:3 3' }, s); return; }
          if (v === 'a2a') {
            svg('rect', { x, y, width: 46, height: 40, rx: 5, style: `fill:${COL[cell[0]]}` }, s);
            svg('text', { x: x + 23, y: y + 25, 'text-anchor': 'middle', class: 't tc', style: 'fill:#fff;font-size:11px;font-weight:600', text: `${cell[0]}→${cell[1]}` }, s);
          } else if (cell.length === 1) {
            svg('rect', { x, y, width: 46, height: 40, rx: 5, style: `fill:${COL[cell[0]]}` }, s);
            svg('text', { x: x + 23, y: y + 25, 'text-anchor': 'middle', class: 't tc', style: 'fill:#fff;font-size:11px;font-weight:600', text: String.fromCharCode(97 + cell[0]) + k }, s);
          } else {
            cell.forEach((src, i) => svg('rect', { x: x + i * 11.5, y, width: 11.5, height: 40, style: `fill:${COL[src]}` }, s));
            svg('text', { x: x + 23, y: y + 25, 'text-anchor': 'middle', class: 't tc', style: 'fill:#fff;font-size:12px;font-weight:700', text: 'Σ' + k }, s);
          }
        });
      }
    };
    drawSide(10, c.before, 'before');
    svg('text', { x: 330, y: 135, 'text-anchor': 'middle', class: 't', style: 'font-size:26px;fill:var(--faint)', text: '⟶' }, s);
    drawSide(350, c.after, 'after');
    document.getElementById('collInfo').innerHTML = c.info;
  });

  /* ring all-reduce */
  const N = 4;
  let st, step, timer = null;
  const reset = () => { st = [...Array(N)].map((_, g) => [...Array(N)].map(() => new Set([g]))); step = 0; drawRing(null); };
  const sendsFor = k => {
    if (k < N - 1) return [...Array(N)].map((_, g) => ({ from: g, to: (g + 1) % N, chunk: ((g - k) % N + N) % N, op: 'add' }));
    const s = k - (N - 1);
    return [...Array(N)].map((_, g) => ({ from: g, to: (g + 1) % N, chunk: ((g + 1 - s) % N + N) % N, op: 'copy' }));
  };
  const drawRing = sends => {
    const s = clear(document.getElementById('ringSvg'));
    const pos = [[150, 60], [510, 60], [510, 200], [150, 200]];
    const cw = 34;
    if (sends) sends.forEach(m => {
      const [x1, y1] = pos[m.from], [x2, y2] = pos[m.to];
      svg('line', { x1: x1 + (x2 > x1 ? 80 : x2 < x1 ? -80 : 0), y1: y1 + (y2 > y1 ? 34 : y2 < y1 ? -34 : 0), x2: x2 + (x2 > x1 ? -80 : x2 < x1 ? 80 : 0), y2: y2 + (y2 > y1 ? -34 : y2 < y1 ? 34 : 0), style: `stroke:${COL[m.chunk]};stroke-width:5`, 'marker-end': 'url(#rarr)' }, s);
    });
    const defs = svg('defs', {}, s), mk = svg('marker', { id: 'rarr', viewBox: '0 0 10 10', refX: 7, refY: 5, markerWidth: 4, markerHeight: 4, orient: 'auto' }, defs);
    svg('path', { d: 'M0,0 L10,5 L0,10 z', style: 'fill:var(--ink)' }, mk);
    pos.forEach(([x, y], g) => {
      svg('rect', { x: x - 76, y: y - 30, width: 152, height: 60, rx: 8, style: 'fill:var(--panel-2);stroke:var(--line)' }, s);
      svg('text', { x: x - 72, y: y - 36, class: 'tm tc', text: 'GPU ' + g }, s);
      for (let c = 0; c < N; c++) {
        const set = st[g][c], cx = x - 70 + c * cw + c * 2;
        const full = set.size === N;
        [...set].sort().forEach((src, i) => svg('rect', { x: cx, y: y - 22 + i * (44 / N), width: cw, height: 44 / N - 1, style: `fill:${COL[c]};opacity:${.35 + .65 * (set.size / N)}` }, s));
        svg('rect', { x: cx, y: y - 22, width: cw, height: 44, rx: 3, style: `fill:none;stroke:${full ? 'var(--ink)' : 'var(--line)'};stroke-width:${full ? 2 : 1}` }, s);
        svg('text', { x: cx + cw / 2, y: y + 5, 'text-anchor': 'middle', class: 't tc', style: 'font-size:11px;font-weight:700;fill:var(--ink)', text: set.size + '/' + N }, s);
      }
    });
    const total = 2 * (N - 1);
    Deck.out('rgPhase', step === 0 ? 'Each GPU holds its own gradients (1/4 = only its contribution)' : step <= N - 1 ? `Reduce-scatter step ${step}/${N - 1}` : step < total ? `All-gather step ${step - (N - 1)}/${N - 1}` : 'Done: every GPU has the full sum (4/4 in every chunk)');
  };
  const doStep = () => {
    if (step >= 2 * (N - 1)) return false;
    const sends = sendsFor(step);
    const snap = st.map(r => r.map(x => new Set(x)));
    sends.forEach(m => {
      const inc = snap[m.from][m.chunk];
      if (m.op === 'add') inc.forEach(v => st[m.to][m.chunk].add(v));
      else st[m.to][m.chunk] = new Set(inc);
    });
    step++;
    drawRing(sends);
    return true;
  };
  document.getElementById('rgStep').onclick = doStep;
  document.getElementById('rgReset').onclick = () => { if (timer) { clearInterval(timer); timer = null; document.getElementById('rgPlay').textContent = 'Play'; } reset(); };
  document.getElementById('rgPlay').onclick = e => {
    if (timer) { clearInterval(timer); timer = null; e.target.textContent = 'Play'; return; }
    if (step >= 2 * (N - 1)) reset();
    e.target.textContent = 'Pause';
    timer = setInterval(() => { if (!doStep()) { clearInterval(timer); timer = null; e.target.textContent = 'Play'; } }, 1100);
  };
  reset();
  Deck.enter('s-ring', () => () => { if (timer) { clearInterval(timer); timer = null; document.getElementById('rgPlay').textContent = 'Play'; } });

  /* cost */
  Deck.bind(['cS', 'cA'], () => {
    const S = Math.pow(10, Deck.val('cS')), a = Deck.val('cA') * 1e-6, B = 50e9;
    Deck.out('cSo', bytes(S)); Deck.out('cAo', Deck.val('cA') + ' µs');
    const ring = n => 2 * (n - 1) * a + 2 * (n - 1) / n * S / B;
    const tree = n => 2 * Math.log2(n) * a + 2 * S / B;
    const s = clear(document.getElementById('costSvg'));
    const L = 70, R = 640, T = 16, Bm = 250, ns = [];
    for (let n = 2; n <= 4096; n *= 1.15) ns.push(n);
    const all = ns.flatMap(n => [ring(n), tree(n)]), lo = Math.min(...all), hi = Math.max(...all);
    const X = n => L + (Math.log2(n) - 1) / 11 * (R - L);
    const Y = t => Bm - (Math.log10(t) - Math.log10(lo * .8)) / (Math.log10(hi * 1.2) - Math.log10(lo * .8)) * (Bm - T);
    [2, 8, 32, 128, 512, 2048].forEach(n => {
      svg('line', { x1: X(n), x2: X(n), y1: T, y2: Bm, class: 'ln' }, s);
      svg('text', { x: X(n), y: Bm + 16, 'text-anchor': 'middle', class: 'tm tc', text: n }, s);
    });
    const tf = t => t < 1e-3 ? (t * 1e6).toFixed(0) + ' µs' : t < 1 ? (t * 1e3).toFixed(1) + ' ms' : t.toFixed(2) + ' s';
    for (let k = 0; k <= 3; k++) {
      const t = Math.pow(10, Math.log10(lo * .8) + k / 3 * (Math.log10(hi * 1.2) - Math.log10(lo * .8)));
      svg('text', { x: L - 6, y: Y(t) + 4, 'text-anchor': 'end', class: 'tm tc', style: 'font-size:10px', text: tf(t) }, s);
    }
    svg('text', { x: (L + R) / 2, y: Bm + 36, 'text-anchor': 'middle', class: 'tm', text: 'number of GPUs (N), 50 GB/s each' }, s);
    svg('polyline', { points: ns.map(n => `${X(n)},${Y(ring(n))}`).join(' '), fill: 'none', style: 'stroke:var(--a);stroke-width:3' }, s);
    svg('polyline', { points: ns.map(n => `${X(n)},${Y(tree(n))}`).join(' '), fill: 'none', style: 'stroke:var(--b);stroke-width:3' }, s);
    svg('text', { x: R, y: Y(ring(4096)) - 8, 'text-anchor': 'end', class: 't', style: 'fill:var(--a);font-weight:600', text: 'ring ' + tf(ring(4096)) }, s);
    svg('text', { x: R, y: Y(tree(4096)) + 18, 'text-anchor': 'end', class: 't', style: 'fill:var(--b);font-weight:600', text: 'tree ' + tf(tree(4096)) }, s);
  });

  /* planner */
  let TP = 8;
  const plan = () => {
    const P = +Deck.val('plM') * 1e9, N = +Deck.val('plN'), PP = Math.pow(2, Deck.val('plPP'));
    Deck.out('plPPo', PP);
    const DP = N / (TP * PP), ok = DP >= 1 && Number.isInteger(DP);
    Deck.out('plDP', ok ? DP.toLocaleString() : '—');
    const mem = ok ? (4 * P / (TP * PP) + 12 * P / (TP * PP * DP)) / 1e9 : NaN;
    Deck.out('plMem', ok ? mem.toFixed(1) + ' GB' : '—');
    document.getElementById('plMem').style.color = mem > 60 ? 'var(--d)' : 'var(--e)';
    const bubble = (PP - 1) / (32 + PP - 1);
    const items = [];
    items.push(!ok ? '<span class="warn">✗ TP × PP exceeds the GPU count</span>' : `<span class="ok">✓</span> ${DP} replicas × ${TP * PP} GPUs each`);
    items.push(TP <= 8 ? '<span class="ok">✓ TP stays inside one node (NVLink)</span>' : '<span class="warn">✗ TP spans nodes: per-layer all-reduce over a 50 GB/s network</span>');
    items.push(PP === 1 ? '<span class="ok">✓ No pipeline bubble</span>' : `${bubble > .1 ? '<span class="warn">!' : '<span class="ok">✓'} Pipeline bubble ≈ ${(bubble * 100).toFixed(0)}%</span> (32 micro-batches)`);
    items.push(mem > 60 ? '<span class="warn">✗ States exceed ~60 GB: little room left for activations</span>' : mem > 40 ? '<span style="color:var(--b);font-weight:600">! Tight: use activation checkpointing</span>' : '<span class="ok">✓ Memory headroom for activations</span>');
    if (ok && TP * PP > N) items.push('<span class="warn">✗ Not enough GPUs</span>');
    document.getElementById('plChecks').innerHTML = items.map(x => `<div>${x}</div>`).join('');
    const s = clear(document.getElementById('plSvg'));
    const stages = Math.min(PP, 32), cols = Math.min(stages, 16), cw = 340 / cols;
    const dotsPer = TP, gpusPerNode = 8;
    for (let st = 0; st < stages; st++) {
      const cx = 10 + (st % cols) * cw, cy = 10 + Math.floor(st / cols) * 105;
      for (let t = 0; t < dotsPer; t++) {
        const gid = st * TP + t, node = Math.floor(gid / gpusPerNode);
        const y = cy + 6 + t * Math.min(12, 90 / dotsPer);
        svg('circle', { cx: cx + cw / 2, cy: y, r: Math.min(5, cw / 3, 90 / dotsPer / 2.4), style: `fill:${['var(--a)', 'var(--b)', 'var(--c)', 'var(--e)'][node % 4]}` }, s);
      }
      if (TP > 8) svg('rect', { x: cx + 2, y: cy, width: cw - 4, height: 98, rx: 4, style: 'fill:none;stroke:var(--d);stroke-dasharray:4 3;stroke-width:1.5' }, s);
      if (cols <= 16) svg('text', { x: cx + cw / 2, y: cy + 112 > 215 ? 215 : cy + 104, 'text-anchor': 'middle', class: 'tm tc', style: 'font-size:9px', text: 's' + st }, s);
    }
    svg('text', { x: 180, y: 218, 'text-anchor': 'middle', class: 'tm', style: 'font-size:10px', text: 'dot colour = which 8-GPU node it lives on' }, s);
  };
  Deck.seg('plTP', v => { TP = +v; if (document.getElementById('plPP')) plan(); });
  Deck.bind(['plM', 'plN', 'plPP'], plan);

  /* MoE */
  let net = 450;
  const moe = () => {
    const k = Deck.val('eS') / 100; Deck.out('eSo', (k * 100).toFixed(0) + '%');
    const n = 8, w = [...Array(n)].map((_, j) => 1 + k * 6 * Math.exp(-j * 1.2));
    const sum = w.reduce((a, b) => a + b, 0);
    const M = [...Array(n)].map((_, i) => w.map((x, j) => x / sum * (1 + 0.15 * Math.sin(i * 3 + j * 7))));
    const col = [...Array(n)].map((_, j) => M.reduce((a, r) => a + r[j], 0));
    const mean = col.reduce((a, b) => a + b, 0) / n, mx = Math.max(...col), imb = mx / mean;
    const s = clear(document.getElementById('eSvg'));
    const c = 32, x0 = 30, y0 = 20, mmax = Math.max(...M.flat());
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) svg('rect', { x: x0 + j * c, y: y0 + i * c, width: c - 2, height: c - 2, rx: 3, style: `fill:var(--a);opacity:${.1 + .9 * M[i][j] / mmax}` }, s);
    col.forEach((v, j) => svg('rect', { x: x0 + j * c, y: y0 + n * c + 6, width: c - 2, height: 6 + 22 * v / mx, rx: 2, style: `fill:${v === mx ? 'var(--d)' : 'var(--faint)'}` }, s));
    for (let i = 0; i < n; i++) svg('text', { x: x0 - 6, y: y0 + i * c + 20, 'text-anchor': 'end', class: 'tm tc', style: 'font-size:10px', text: i }, s);
    Deck.out('eImb', imb.toFixed(2) + '×');
    document.getElementById('eImb').style.color = imb > 1.5 ? 'var(--d)' : 'var(--e)';
    const bytesPer = 8192 * 2 * 7168 * 2, t = bytesPer * imb / (net * 1e9);
    Deck.out('eT', (t * 1000).toFixed(2) + ' ms');
  };
  Deck.seg('eNet', v => { net = +v; if (document.getElementById('eS')) moe(); });
  Deck.bind(['eS'], moe);
})();
