(() => {
  const { svg, clear, fmt } = Deck;
  // geometry shared by both node diagrams
  const GX = i => 200 + i * 86, GW = 78;
  const SX = j => 230 + j * 165, SW = 135;
  const PX = k => 200 + 2 * k * 86, PW = 164;
  const Y = { sw: 14, gpu: 84, pcie: 176, nic: 226, bus: 274, fab: 300 };
  const C0 = { x: 10, y: 84, w: 160, h: 70 }, C1 = { x: 10, y: 176, w: 160, h: 70 }, NV = { x: 10, y: 268, w: 160, h: 40 };

  function drawNode(s, interactive) {
    const I = msg => interactive ? { 'data-info': msg } : {};
    // NVLink wiring
    for (let i = 0; i < 8; i++) for (let j = 0; j < 4; j++)
      svg('line', { x1: GX(i) + GW / 2, y1: Y.gpu, x2: SX(j) + SW / 2, y2: Y.sw + 30, style: 'stroke:var(--e);stroke-width:1;opacity:.35' }, s);
    // PCIe wiring
    for (let i = 0; i < 8; i++) svg('line', { x1: GX(i) + GW / 2, y1: Y.gpu + 56, x2: GX(i) + GW / 2, y2: Y.pcie, style: 'stroke:var(--c);stroke-width:2;opacity:.6' }, s);
    for (let i = 0; i < 8; i++) svg('line', { x1: GX(i) + GW / 2, y1: Y.pcie + 26, x2: GX(i) + GW / 2, y2: Y.nic, style: 'stroke:var(--c);stroke-width:2;opacity:.6' }, s);
    for (let i = 0; i < 8; i++) svg('line', { x1: GX(i) + GW / 2, y1: Y.nic + 26, x2: GX(i) + GW / 2, y2: Y.fab, style: 'stroke:var(--b);stroke-width:2;opacity:.6' }, s);
    for (let k = 0; k < 4; k++) {
      const cx = PX(k) + 82, by = Y.bus + (k < 2 ? 0 : 10);
      svg('polyline', { points: `${cx},${Y.pcie + 26} ${cx},${by} 182,${by} 182,${k < 2 ? C0.y + 35 : C1.y + 35} ${C0.x + C0.w},${k < 2 ? C0.y + 35 : C1.y + 35}`, fill: 'none', style: 'stroke:var(--c);stroke-width:1.6;opacity:.5' }, s);
    }
    svg('line', { x1: 90, y1: C1.y + C1.h, x2: 90, y2: NV.y, style: 'stroke:var(--c);stroke-width:2;opacity:.6' }, s);
    svg('line', { x1: 60, y1: C0.y + C0.h, x2: 60, y2: C1.y, style: 'stroke:var(--faint);stroke-width:3;stroke-dasharray:4 3' }, s);
    svg('text', { x: 66, y: C0.y + C0.h + 15, class: 'tm', style: 'font-size:10px', text: 'UPI' }, s);

    for (let j = 0; j < 4; j++) {
      const g = svg('g', I(`<b>NVSwitch ${j}</b> (3rd gen): every GPU sends 4–5 of its 18 NVLink links to each of the 4 switches. Together they give a non-blocking all-to-all fabric with in-switch reduction (NVLink SHARP).`), s);
      svg('rect', { x: SX(j), y: Y.sw, width: SW, height: 30, rx: 6, class: 'f-e' }, g);
      svg('text', { x: SX(j) + SW / 2, y: Y.sw + 20, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:600;font-size:12px', text: 'NVSwitch ' + j }, g);
    }
    for (let i = 0; i < 8; i++) {
      const g = svg('g', I(`<b>GPU ${i}: H100 SXM5</b>. 80 GB HBM3 at 3.35 TB/s, 700 W, 18 NVLink 4 links (900 GB/s bidirectional), PCIe Gen5 x16 to its switch.`), s);
      svg('rect', { x: GX(i), y: Y.gpu, width: GW, height: 56, rx: 8, class: 'f-a', 'data-gpu': i }, g);
      svg('text', { x: GX(i) + GW / 2, y: Y.gpu + 25, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:700', text: 'GPU ' + i }, g);
      svg('text', { x: GX(i) + GW / 2, y: Y.gpu + 42, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:10.5px;opacity:.9', text: 'H100 · 80 GB' }, g);
      const n = svg('g', I(`<b>NIC ${i}: ConnectX-7, 400 Gb/s</b> (InfiniBand NDR or Ethernet/RoCE). It is dedicated to GPU ${i} and reads and writes its HBM directly with GPUDirect RDMA.`), s);
      svg('rect', { x: GX(i), y: Y.nic, width: GW, height: 26, rx: 5, class: 'f-b' }, n);
      svg('text', { x: GX(i) + GW / 2, y: Y.nic + 17, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11px;font-weight:600', text: 'NIC ' + i + ' · 400G' }, n);
    }
    for (let k = 0; k < 4; k++) {
      const g = svg('g', I(`<b>PCIe Gen5 switch ${k}</b>: connects GPUs ${2 * k}–${2 * k + 1} and NICs ${2 * k}–${2 * k + 1} (and storage) to CPU ${k < 2 ? 0 : 1}. GPU↔NIC traffic stays inside this switch and never touches the CPU.`), s);
      svg('rect', { x: PX(k) + 4, y: Y.pcie, width: PW - 8, height: 26, rx: 5, class: 'f-c' }, g);
      svg('text', { x: PX(k) + PW / 2, y: Y.pcie + 17, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11px;font-weight:600', text: 'PCIe Gen5 switch ' + k }, g);
    }
    const fab = svg('g', I('<b>Compute fabric</b>: 8 × 400 Gb/s = 3.2 Tb/s per node into a rail-optimized InfiniBand or RoCE network (deck 05). A separate frontend network carries storage and management traffic.'), s);
    svg('rect', { x: 200, y: Y.fab, width: 680, height: 26, rx: 6, style: 'fill:var(--b-soft);stroke:var(--b)' }, fab);
    svg('text', { x: 540, y: Y.fab + 17, 'text-anchor': 'middle', class: 't', style: 'fill:var(--b);font-weight:600;font-size:12px', text: 'compute fabric → other nodes (8 × 400 Gb/s)' }, fab);
    [[C0, 'CPU 0', '56-core Xeon · 1 TB DDR5'], [C1, 'CPU 1', '56-core Xeon · 1 TB DDR5']].forEach(([c, n, d], idx) => {
      const g = svg('g', I(`<b>${n}</b>: a NUMA domain hosting PCIe switches ${idx * 2}–${idx * 2 + 1}. Runs the training process, dataloaders and NCCL proxy threads. Its DDR5 is the "host memory" for pinned buffers and offload.`), s);
      svg('rect', { x: c.x, y: c.y, width: c.w, height: c.h, rx: 8, style: 'fill:var(--faint)' }, g);
      svg('text', { x: c.x + c.w / 2, y: c.y + 30, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:700', text: n }, g);
      svg('text', { x: c.x + c.w / 2, y: c.y + 48, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:10.5px', text: d }, g);
    });
    const nv = svg('g', I('<b>Local NVMe</b> (~30 TB, U.2): a cache for dataset shards and fast local checkpoints. With GPUDirect Storage, the drive can DMA straight into GPU memory.'), s);
    svg('rect', { x: NV.x, y: NV.y, width: NV.w, height: NV.h, rx: 6, style: 'fill:var(--faint);opacity:.7' }, nv);
    svg('text', { x: NV.x + NV.w / 2, y: NV.y + 25, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11.5px;font-weight:600', text: 'NVMe · ~30 TB' }, nv);
    svg('text', { x: 10, y: 340, class: 'tm', style: 'font-size:11px', text: '— NVLink   — PCIe   — network' }, s);
  }

  const map = document.getElementById('mapSvg');
  drawNode(map, true);
  const info = document.getElementById('mapInfo');
  const pick = e => { const g = e.target.closest('[data-info]'); if (g) info.innerHTML = g.dataset.info; };
  map.addEventListener('mouseover', pick); map.addEventListener('click', pick);

  /* data paths */
  const gx = i => GX(i) + GW / 2;
  const PATHS = {
    nvl: { pts: [[gx(0), Y.gpu], [SX(1) + SW / 2, Y.sw + 30], [gx(5), Y.gpu]], bw: 450, c: 'var(--e)', use: 'Tensor-parallel all-reduce, MoE all-to-all within the node',
      info: '<b>GPU 0 → NVSwitch → GPU 5.</b> One hop through a switch, and all 8 GPUs can do this at the same time at full rate (non-blocking). The bandwidth is 18 links × 25 GB/s ≈ 450 GB/s per direction.' },
    rdma: { pts: [[gx(0), Y.gpu + 56], [gx(0), Y.pcie + 13], [gx(0), Y.nic + 13], [gx(0), Y.fab + 13], [880, Y.fab + 13]], bw: 50, c: 'var(--b)', use: 'Data-parallel gradient all-reduce, pipeline sends',
      info: '<b>GPU 0 → PCIe switch → NIC 0 → fabric.</b> With GPUDirect RDMA the NIC DMAs straight from HBM. The CPU is not involved and there is no copy in host memory. The limit is 400 Gb/s ≈ 50 GB/s.' },
    bounce: { pts: [[gx(0), Y.gpu + 56], [gx(0), Y.pcie + 13], [PX(0) + 82, Y.pcie + 26], [PX(0) + 82, Y.bus], [182, Y.bus], [182, C0.y + 35], [C0.x + C0.w / 2, C0.y + 35], [182, C0.y + 35], [182, Y.bus], [PX(0) + 82, Y.bus], [PX(0) + 82, Y.pcie + 26], [gx(0), Y.nic + 13], [gx(0), Y.fab + 13], [880, Y.fab + 13]], bw: 25, c: 'var(--d)', use: 'What happens if GPUDirect RDMA is misconfigured',
      info: '<b>Bounce through host memory:</b> GPU → CPU DRAM (copy) → NIC. The data crosses PCIe twice, uses CPU memory bandwidth and adds latency. Effective throughput drops a lot. Check that <code>nvidia-peermem</code> is loaded, and look at the NCCL logs for "GDR".' },
    h2d: { pts: [[C0.x + C0.w / 2, C0.y + 35], [182, C0.y + 35], [182, Y.bus], [PX(0) + 82, Y.bus], [PX(0) + 82, Y.pcie + 26], [gx(1), Y.pcie + 13], [gx(1), Y.gpu + 56]], bw: 55, c: 'var(--c)', use: 'Input batches, offloaded optimizer state, KV-cache swap-in',
      info: '<b>Host → device copy over PCIe Gen5 x16</b> (~64 GB/s theoretical, about 50–55 GB/s in practice with <em>pinned</em> memory; pageable memory is much slower). Use <code>pin_memory=True</code> and non-blocking copies that overlap with compute.' },
    gds: { pts: [[NV.x + NV.w / 2, NV.y], [90, C1.y + C1.h], [182, C1.y + 35], [182, Y.bus + 10], [PX(2) + 82, Y.bus + 10], [PX(2) + 82, Y.pcie + 26], [gx(4), Y.pcie + 13], [gx(4), Y.gpu + 56]], bw: 14, c: 'var(--faint)', use: 'Checkpoint load, dataset streaming',
      info: '<b>GPUDirect Storage</b>: NVMe → PCIe → GPU HBM by DMA, with no bounce buffer in CPU memory. The limit is drive throughput (~7 GB/s per drive; a few drives in parallel give ~14+ GB/s), not PCIe.' },
  };
  const ps = document.getElementById('pathSvg');
  drawNode(ps, false);
  const overlay = svg('g', {}, ps);
  let cur = 'nvl';
  const renderPath = () => {
    clear(overlay);
    const p = PATHS[cur];
    svg('polyline', { points: p.pts.map(q => q.join(',')).join(' '), fill: 'none', style: `stroke:${p.c};stroke-width:6;stroke-linejoin:round;opacity:.9` }, overlay);
    Deck.out('pBW', p.bw + ' GB/s'); Deck.out('pT', (10 / p.bw < 1 ? (10000 / p.bw).toFixed(0) + ' ms' : (10 / p.bw).toFixed(2) + ' s'));
    Deck.out('pUse', p.use); document.getElementById('pathInfo').innerHTML = p.info;
  };
  Deck.seg('pathSeg', v => { cur = v; renderPath(); });
  Deck.enter('s-paths', () => {
    const dots = [0, 1, 2].map(() => svg('circle', { r: 7, style: 'fill:var(--ink);stroke:var(--panel);stroke-width:2' }, ps));
    const stop = Deck.loop(t => {
      const p = PATHS[cur].pts;
      const seg = []; let L = 0;
      for (let i = 1; i < p.length; i++) { const d = Math.hypot(p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1]); seg.push(d); L += d; }
      dots.forEach((dot, k) => {
        let pos = ((t * 220 + k * L / 3) % L), i = 0;
        while (i < seg.length - 1 && pos > seg[i]) { pos -= seg[i]; i++; }
        const f = seg[i] ? pos / seg[i] : 0;
        dot.setAttribute('cx', p[i][0] + (p[i + 1][0] - p[i][0]) * f);
        dot.setAttribute('cy', p[i][1] + (p[i + 1][1] - p[i][1]) * f);
      });
    });
    return () => { stop(); dots.forEach(d => d.remove()); };
  });

  /* ladder */
  Deck.hbars(document.getElementById('ladBars'), [
    { label: 'HBM3', value: 3350, color: 'var(--b)', text: '3,350 GB/s' },
    { label: 'NVLink 4 (per dir.)', value: 450, color: 'var(--e)', text: '450 GB/s' },
    { label: 'PCIe Gen5 x16', value: 64, color: 'var(--c)', text: '64 GB/s' },
    { label: '400G NIC', value: 50, color: 'var(--b)', text: '50 GB/s' },
    { label: 'NVMe (1 drive)', value: 7, color: 'var(--faint)', text: '~7 GB/s' },
  ], { log: true, min: 3, max: 5000 });
  Deck.bind(['arS'], () => {
    const GB = Math.pow(10, Deck.val('arS'));
    Deck.out('arSo', GB < 10 ? GB.toFixed(1) + ' GB' : GB.toFixed(0) + ' GB');
    const f = 2 * 7 / 8, t = bw => { const s = f * GB / bw; return s < 1 ? (s * 1000).toFixed(0) + ' ms' : s.toFixed(2) + ' s'; };
    Deck.out('arIn', t(450)); Deck.out('arOut', t(50));
  });

  /* topo matrix */
  const topo = document.getElementById('topo');
  const rel = (a, b, nic) => {
    if (!nic) return a === b ? 'X' : 'NV18';
    if (Math.floor(a / 2) === Math.floor(b / 2)) return 'PIX';
    if (Math.floor(a / 4) === Math.floor(b / 4)) return 'NODE';
    return 'SYS';
  };
  let html = '<tr><th></th>' + [...Array(8)].map((_, i) => `<th>GPU${i}</th>`).join('') + [...Array(8)].map((_, i) => `<th>NIC${i}</th>`).join('') + '<th>CPU</th></tr>';
  for (let r = 0; r < 8; r++) {
    html += `<tr><th>GPU${r}</th>`;
    for (let c = 0; c < 8; c++) { const v = rel(r, c, false); html += `<td class="${v === 'NV18' ? 'NV' : 'X'}" data-r="${r}" data-c="G${c}">${v}</td>`; }
    for (let c = 0; c < 8; c++) { const v = rel(r, c, true); html += `<td class="${v}" data-r="${r}" data-c="N${c}">${v}</td>`; }
    html += `<td class="X">${r < 4 ? '0' : '1'}</td></tr>`;
  }
  topo.innerHTML = html;
  const tInfo = document.getElementById('topoInfo');
  const EXPL = {
    NV18: (r, c) => `<b>GPU${r} ↔ GPU${c}: NV18.</b> 18 NVLink 4 links through NVSwitch. Every GPU pair is equidistant, which is why tensor parallelism inside the node doesn't care about rank order.`,
    PIX: (r, c) => `<b>GPU${r} ↔ NIC${c}: PIX.</b> Behind the same PCIe switch. ${r === c ? 'This is the NIC NCCL should use for this GPU.' : 'Close, but this NIC belongs to the neighbouring GPU.'}`,
    NODE: (r, c) => `<b>GPU${r} ↔ NIC${c}: NODE.</b> Same socket, so traffic goes through the CPU root complex. It works, but it competes with other PCIe traffic.`,
    SYS: (r, c) => `<b>GPU${r} ↔ NIC${c}: SYS.</b> Crosses sockets over UPI. Avoid this for RDMA: lower bandwidth, higher latency, and it disturbs the other socket.`,
    X: (r, c) => `<b>GPU${r}</b> itself.`,
  };
  topo.addEventListener('mouseover', e => {
    const td = e.target.closest('td[data-r]'); if (!td) return;
    Deck.$$('td.hl', topo).forEach(x => x.classList.remove('hl')); td.classList.add('hl');
    tInfo.innerHTML = EXPL[td.textContent](td.dataset.r, td.dataset.c.slice(1));
  });

  /* power */
  Deck.bind(['pwSys', 'pwR', 'pwG', 'pwP'], () => {
    const [kw, g] = Deck.val('pwSys').split(',').map(Number), R = Deck.val('pwR'), G = Math.pow(2, Deck.val('pwG')), P = Deck.val('pwP');
    Deck.out('pwRo', R + ' kW'); Deck.out('pwGo', G.toLocaleString()); Deck.out('pwPo', P.toFixed(2));
    const per = Math.floor(R / kw), gpr = per * g;
    Deck.out('pwPer', per || '0 (too hot)'); Deck.out('pwGR', gpr);
    document.getElementById('pwPer').style.color = per ? 'var(--ink)' : 'var(--d)';
    const systems = Math.ceil(G / g), racks = per ? Math.ceil(systems / per) : Infinity;
    Deck.out('pwRacks', isFinite(racks) ? racks.toLocaleString() : '—');
    const mw = systems * kw * P / 1000;
    Deck.out('pwMW', mw < 1 ? (mw * 1000).toFixed(0) + ' kW' : mw.toFixed(1) + ' MW');
    const s = clear(document.getElementById('pwSvg'));
    const shown = Math.min(isFinite(racks) ? racks : 0, 40);
    for (let i = 0; i < shown; i++) {
      const x = 10 + (i % 20) * 32, y = 8 + Math.floor(i / 20) * 54;
      svg('rect', { x, y, width: 26, height: 48, rx: 3, style: 'fill:var(--panel-2);stroke:var(--line)' }, s);
      for (let k = 0; k < Math.min(per, 6); k++) svg('rect', { x: x + 3, y: y + 4 + k * 7, width: 20, height: 5, rx: 1, class: 'f-a' }, s);
    }
    if (racks > 40 && isFinite(racks)) svg('text', { x: 650, y: 115, 'text-anchor': 'end', class: 'tm', text: `showing 40 of ${racks.toLocaleString()} racks` }, s);
  });

  /* scale-up domain */
  Deck.seg('sdSeg', v => {
    const n = +v, s = clear(document.getElementById('sdSvg'));
    const cols = n === 8 ? 8 : 18, rows = Math.ceil(n / cols), cw = 640 / cols, ch = n === 8 ? 70 : 36;
    const top = n === 8 ? 40 : 10;
    svg('rect', { x: 6, y: top + rows * (ch + 8) + 8, width: 648, height: 28, rx: 6, class: 'f-e', opacity: .85 }, s);
    svg('text', { x: 330, y: top + rows * (ch + 8) + 27, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:600', text: n === 8 ? '4 × NVSwitch (on the baseboard)' : '9 NVLink switch trays · 18 NVSwitch chips (in the rack)' }, s);
    for (let i = 0; i < n; i++) {
      const x = 10 + (i % cols) * cw, y = top + Math.floor(i / cols) * (ch + 8);
      svg('line', { x1: x + cw / 2 - 2, y1: y + ch, x2: x + cw / 2 - 2, y2: top + rows * (ch + 8) + 8, style: 'stroke:var(--e);opacity:.4' }, s);
      svg('rect', { x, y, width: cw - 4, height: ch, rx: 4, class: 'f-a' }, s);
      if (n === 8) svg('text', { x: x + cw / 2 - 2, y: y + ch / 2 + 5, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:600', text: 'H100' }, s);
    }
    const h = top + rows * (ch + 8) + 46;
    s.setAttribute('viewBox', `0 0 660 ${h}`);
    Deck.out('sdG', n); Deck.out('sdBW', n === 8 ? '900 GB/s' : '1.8 TB/s');
    Deck.out('sdAgg', n === 8 ? '7.2 TB/s' : '130 TB/s'); Deck.out('sdMem', n === 8 ? '640 GB' : '~13.5 TB');
  });
})();
