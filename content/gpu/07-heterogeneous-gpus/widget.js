(() => {
  const { svg, clear, fmt } = Deck;
  const G = {
    V100: { bf16: 125, fp8: 0, mem: 32, bw: 0.9, nvl: 300, year: 2017, note: 'FP16 tensor only (no BF16)' },
    A100: { bf16: 312, fp8: 0, mem: 80, bw: 2.04, nvl: 600, year: 2020, note: 'BF16/TF32, no FP8' },
    H100: { bf16: 989, fp8: 1979, mem: 80, bw: 3.35, nvl: 900, year: 2022, note: 'FP8, TMA, wgmma' },
    H200: { bf16: 989, fp8: 1979, mem: 141, bw: 4.8, nvl: 900, year: 2024, note: 'H100 compute, bigger/faster HBM3e' },
    B200: { bf16: 2250, fp8: 4500, mem: 192, bw: 8, nvl: 1800, year: 2025, note: 'FP4, NVLink 5, 2-die' },
    MI300X: { bf16: 1307, fp8: 2615, mem: 192, bw: 5.3, nvl: 896, year: 2023, note: 'AMD · ROCm/RCCL · Infinity Fabric' },
  };
  const names = Object.keys(G);
  ['gA', 'gB'].forEach((id, k) => { const el = document.getElementById(id); el.innerHTML = names.map(n => `<option ${n === (k ? 'H100' : 'A100') ? 'selected' : ''}>${n}</option>`).join(''); });
  Deck.bind(['gA', 'gB'], () => {
    const a = Deck.val('gA'), b = Deck.val('gB'), A = G[a], B = G[b];
    const rows = [['Year', 'year', ''], ['BF16 dense TFLOPS', 'bf16', ''], ['FP8 dense TFLOPS', 'fp8', ''], ['HBM (GB)', 'mem', ''], ['HBM bandwidth (TB/s)', 'bw', ''], ['GPU↔GPU link (GB/s, bidir.)', 'nvl', '']];
    document.getElementById('specTbl').innerHTML = `<tr><th></th><th>${a}</th><th>${b}</th></tr>` + rows.map(([n, k]) => {
      const va = A[k], vb = B[k], fa = va === 0 ? '—' : va, fb = vb === 0 ? '—' : vb;
      const better = k === 'year' ? '' : va > vb ? 'a' : vb > va ? 'b' : '';
      return `<tr><td>${n}</td><td class="${better === 'a' ? 'best' : ''}">${fa}</td><td class="${better === 'b' ? 'best' : ''}">${fb}</td></tr>`;
    }).join('') + `<tr><td>Notes</td><td>${A.note}</td><td>${B.note}</td></tr>`;
    const r = k => B[k] && A[k] ? B[k] / A[k] : 0;
    Deck.hbars(document.getElementById('ratioBars'), [
      { label: `${b} ÷ ${a} · compute`, value: r('bf16'), color: 'var(--a)', text: r('bf16').toFixed(2) + '×' },
      { label: `${b} ÷ ${a} · bandwidth`, value: r('bw'), color: 'var(--b)', text: r('bw').toFixed(2) + '×' },
      { label: `${b} ÷ ${a} · memory`, value: r('mem'), color: 'var(--c)', text: r('mem').toFixed(2) + '×' },
    ], { max: Math.max(4, r('bf16'), r('bw'), r('mem')) });
  });

  /* slowest wins */
  let hMode = 'eq';
  const het = () => {
    const share = Deck.val('hMix') / 100; Deck.out('hMixo', (share * 100).toFixed(1).replace('.0', '') + '%');
    const n = 8, nA = Math.round(share * n), speed = i => i >= n - nA ? 1 / 3 : 1;
    const total = [...Array(n)].reduce((a, _, i) => a + speed(i), 0);
    const batch = i => hMode === 'eq' ? 1 : speed(i) * n / total;
    const t = [...Array(n)].map((_, i) => batch(i) / speed(i));
    const step = Math.max(...t);
    const s = clear(document.getElementById('hSvg'));
    const L = 70, W = 560, sc = W / 3.2;
    t.forEach((v, i) => {
      const y = 10 + i * 26;
      svg('text', { x: 0, y: y + 15, class: 'tm tc', style: 'font-size:11px', text: (speed(i) === 1 ? 'H100 ' : 'A100 ') + i }, s);
      svg('rect', { x: L, y, width: v * sc, height: 20, rx: 3, style: `fill:${speed(i) === 1 ? 'var(--a)' : 'var(--b)'}` }, s);
      if (step - v > 1e-6) svg('rect', { x: L + v * sc, y, width: (step - v) * sc, height: 20, style: 'fill:var(--d-soft);stroke:var(--d);stroke-width:.6' }, s);
      if (hMode === 'prop') svg('text', { x: L + 6, y: y + 14, class: 't', style: 'fill:#fff;font-size:10px;font-weight:600', text: `batch ${(batch(i) * 32).toFixed(0)}` }, s);
    });
    svg('line', { x1: L + step * sc, x2: L + step * sc, y1: 4, y2: 220, style: 'stroke:var(--d);stroke-width:2;stroke-dasharray:4 3' }, s);
    const samples = [...Array(n)].reduce((a, _, i) => a + batch(i), 0), thr = samples / step;
    const nH = n - nA, baseline = nH;
    Deck.out('hThr', (thr / n * 100).toFixed(0) + '% of 8×H100');
    const idle = nH ? [...Array(nH)].reduce((a, _, i) => a + (step - t[i]) / step, 0) / nH : 0;
    Deck.out('hIdle', (idle * 100).toFixed(0) + '%');
    const gain = baseline ? thr / baseline - 1 : 0;
    Deck.out('hGain', nA === 0 ? '—' : nH === 0 ? 'n/a' : (gain >= 0 ? '+' : '') + (gain * 100).toFixed(0) + '%');
    document.getElementById('hGain').style.color = gain < 0 ? 'var(--d)' : 'var(--e)';
  };
  Deck.seg('hMode', v => { hMode = v; if (document.getElementById('hMix')) het(); });
  Deck.bind(['hMix'], het);

  /* pipeline */
  Deck.seg('ppMode', v => {
    const speeds = [1, 1, 1 / 3, 1 / 3];
    let layers = [20, 20, 20, 20];
    if (v === 'bal') {
      const tot = speeds.reduce((a, b) => a + b, 0);
      layers = speeds.map(sp => Math.round(80 * sp / tot));
      layers[0] += 80 - layers.reduce((a, b) => a + b, 0);
    }
    Deck.out('ppSplit', 'layers: ' + layers.join(' / ') + ' (H100, H100, A100, A100)');
    const dur = layers.map((l, i) => l / speeds[i] / 20);
    const m = 8, S = 4, start = [...Array(S)].map(() => Array(m).fill(0)), end = [...Array(S)].map(() => Array(m).fill(0));
    for (let s = 0; s < S; s++) for (let i = 0; i < m; i++) {
      const ready = Math.max(s ? end[s - 1][i] : 0, i ? end[s][i - 1] : 0);
      start[s][i] = ready; end[s][i] = ready + dur[s];
    }
    const T = end[S - 1][m - 1];
    const sv = clear(document.getElementById('ppSvg'));
    const L = 110, W = 470, sc = W / 30;
    for (let s = 0; s < S; s++) {
      const y = 14 + s * 48;
      svg('text', { x: 0, y: y + 22, class: 'tm tc', style: 'font-size:11px', text: `stage ${s} · ${speeds[s] === 1 ? 'H100' : 'A100'}` }, sv);
      svg('rect', { x: L, y, width: T * sc, height: 34, style: 'fill:var(--panel-2)' }, sv);
      for (let i = 0; i < m; i++) {
        svg('rect', { x: L + start[s][i] * sc + .5, y, width: Math.max(1, dur[s] * sc - 1), height: 34, rx: 3, style: `fill:${speeds[s] === 1 ? 'var(--a)' : 'var(--b)'};opacity:${.6 + .4 * (i % 2)}` }, sv);
        if (dur[s] * sc > 16) svg('text', { x: L + start[s][i] * sc + dur[s] * sc / 2, y: y + 22, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:10px;font-weight:600', text: i }, sv);
      }
    }
    svg('text', { x: L + T * sc + 6, y: 120, class: 't tc', style: 'font-size:11px;font-weight:600', text: T.toFixed(1) + ' units' }, sv);
    const busy = dur.reduce((a, d) => a + d * m, 0) / (S * T);
    Deck.out('ppT', T.toFixed(1) + ' units'); Deck.out('ppU', (busy * 100).toFixed(0) + '%');
    const memPer = layers.map(l => 70e9 * 16 * (l / 80) / 16 / 1e9);
    const mx = Math.max(...memPer);
    Deck.out('ppMem', mx.toFixed(0) + ' GB');
    document.getElementById('ppMem').style.color = mx > 80 ? 'var(--d)' : 'var(--e)';
  });

  /* disaggregation */
  ['dP', 'dD'].forEach((id, k) => { const el = document.getElementById(id); el.innerHTML = names.map(n => `<option ${n === (k ? 'H200' : 'H100') ? 'selected' : ''}>${n}</option>`).join(''); });
  let link = 50;
  const dis = () => {
    const P = G[Deck.val('dP')], D = G[Deck.val('dD')];
    const pf = (P.fp8 || P.bf16) * 1e12, pfNote = P.fp8 ? '' : ' (no FP8 → BF16 rate)';
    const ttft = 2 * 70e9 * 4096 / (8 * pf * 0.5);
    const kv = 4096 * 163840 / (link * 1e9);
    const fits = D.mem * 8 >= 70 + 40;
    const tpot = 70e9 / (8 * D.bw * 1e12 * 0.8);
    Deck.out('dTTFT', (ttft * 1000).toFixed(0) + ' ms'); Deck.out('dKV', (kv * 1000).toFixed(1) + ' ms'); Deck.out('dTPOT', (tpot * 1000).toFixed(1) + ' ms');
    Deck.out('dNote', !P.fp8 ? 'Prefill pool lacks FP8' + pfNote : D.bw >= P.bw * 1.3 ? 'Decode pool has the faster HBM ✓' : D.bw < P.bw ? 'Decode pool is slower at decode' : 'Similar pools');
    const s = clear(document.getElementById('dSvg'));
    const box = (x, w, c, t1, t2) => { svg('rect', { x, y: 30, width: w, height: 70, rx: 10, style: `fill:${c}` }, s); svg('text', { x: x + w / 2, y: 60, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:700', text: t1 }, s); svg('text', { x: x + w / 2, y: 80, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11px', text: t2 }, s); };
    svg('text', { x: 10, y: 70, class: 'tm', text: 'prompt →' }, s);
    box(80, 200, 'var(--a)', 'Prefill · 8× ' + Deck.val('dP'), 'compute-bound · ' + fmt((P.fp8 || P.bf16), 0) + ' TF');
    svg('line', { x1: 285, y1: 65, x2: 375, y2: 65, style: `stroke:var(--c);stroke-width:${link > 100 ? 7 : 3}`, 'marker-end': 'url(#dar)' }, s);
    svg('text', { x: 330, y: 55, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: 'KV cache' }, s);
    svg('text', { x: 330, y: 88, 'text-anchor': 'middle', class: 'tm tc', style: 'font-size:10.5px', text: link + ' GB/s' }, s);
    box(380, 200, 'var(--b)', 'Decode · 8× ' + Deck.val('dD'), 'bandwidth-bound · ' + D.bw + ' TB/s');
    svg('text', { x: 590, y: 70, class: 'tm', text: '→ tokens' }, s);
    const defs = svg('defs', {}, s), mk = svg('marker', { id: 'dar', viewBox: '0 0 10 10', refX: 8, refY: 5, markerWidth: 4, markerHeight: 4, orient: 'auto' }, defs);
    svg('path', { d: 'M0,0 L10,5 L0,10 z', style: 'fill:var(--c)' }, mk);
    if (!fits) svg('text', { x: 480, y: 125, 'text-anchor': 'middle', class: 't', style: 'fill:var(--d);font-size:11px', text: 'tight on memory for KV' }, s);
  };
  Deck.seg('dLink', v => { link = +v; if (document.getElementById('dP')) dis(); });
  Deck.bind(['dP', 'dD'], dis);

  /* placement */
  const W = {
    pre: { s: { V100: 5, A100: 25, H100: 75, H200: 80, B200: 100, MI300X: 60 }, t: '<b>Frontier pretraining</b> needs peak FLOPs, FP8/FP4, and the <b>largest NVLink domain</b> for TP/EP. Use the newest homogeneous GPUs in large pods. Every percent of MFU is worth millions of dollars.' },
    rl: { s: { V100: 10, A100: 55, H100: 75, H200: 90, B200: 85, MI300X: 80 }, t: '<b>RL rollouts</b> are mostly <em>generation</em> (decode-heavy, many concurrent sequences). Memory capacity and bandwidth for KV matter more than peak FLOPs, so H200 and MI300X do well and older parts are usable.' },
    sft: { s: { V100: 30, A100: 85, H100: 80, H200: 75, B200: 55, MI300X: 70 }, t: '<b>Fine-tuning small and medium models</b> fits on a single node. An A100 node is cost-effective; using B200s here takes them away from bigger jobs.' },
    dec: { s: { V100: 5, A100: 40, H100: 60, H200: 90, B200: 95, MI300X: 90 }, t: '<b>Long-context decode</b> is limited by HBM bandwidth and KV capacity. Choose by TB/s and GB per dollar, which favours H200, MI300X and B200.' },
    eval: { s: { V100: 45, A100: 85, H100: 60, H200: 55, B200: 35, MI300X: 60 }, t: '<b>Evals and batch inference</b> are throughput jobs that tolerate latency and are easy to preempt. Older GPUs are a good fit, which frees new parts for training.' },
    emb: { s: { V100: 70, A100: 85, H100: 55, H200: 45, B200: 30, MI300X: 50 }, t: '<b>Embedding and reranking</b> models are small and need high QPS. Older GPUs, partitioned with MIG or MPS (deck 08), give the best cost per query.' },
  };
  Deck.seg('wSeg', v => {
    const w = W[v];
    Deck.hbars(document.getElementById('wBars'), names.map(n => ({ label: n, value: w.s[n], color: w.s[n] >= 80 ? 'var(--e)' : w.s[n] >= 50 ? 'var(--a)' : 'var(--faint)', text: w.s[n] + ' / 100' })), { max: 100 });
    document.getElementById('wInfo').innerHTML = w.t;
  });
})();
