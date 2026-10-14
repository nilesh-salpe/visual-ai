(() => {
  const { svg, clear, fmt } = Deck;
  const MODELS = { 8: { N: 8e9, L: 32, d: 4096 }, 70: { N: 70e9, L: 80, d: 8192 }, 405: { N: 405e9, L: 126, d: 16384 } };

  /* matmul share */
  let mdl = 70;
  const mm = () => {
    const m = MODELS[mdl], ctx = Math.pow(2, Deck.val('mmCtx'));
    Deck.out('mmCtxo', ctx >= 1024 ? (ctx / 1024) + 'K' : ctx);
    const lin = 2 * m.N, att = 4 * m.L * ctx * m.d, tot = lin + att;
    Deck.hbars(document.getElementById('mmBars'), [
      { label: 'Linear (GEMM)', value: lin, color: 'var(--a)', text: fmt(lin) + ' · ' + (100 * lin / tot).toFixed(0) + '%' },
      { label: 'Attention', value: att, color: 'var(--b)', text: fmt(att) + ' · ' + (100 * att / tot).toFixed(0) + '%' },
    ], { max: tot });
    Deck.out('mmOut', `≈ ${fmt(tot)} FLOPs per token · ${(2 * m.N / 1e9).toFixed(0)} GFLOPs from weights alone`);
  };
  Deck.seg('mmModel', v => { mdl = +v; if (document.getElementById('mmCtx')) mm(); });
  Deck.bind(['mmCtx'], mm);

  /* 6ND */
  Deck.bind(['tN', 'tD', 'tG', 'tM', 'tGPU'], () => {
    const N = Math.pow(10, Deck.val('tN')) * 1e9, D = Math.pow(10, Deck.val('tD')), G = Math.pow(2, Deck.val('tG')), M = Deck.val('tM') / 100, P = +Deck.val('tGPU') * 1e12;
    Deck.out('tNo', fmt(N, 0)); Deck.out('tDo', fmt(D, 1)); Deck.out('tGo', G.toLocaleString()); Deck.out('tMo', (M * 100) + '%');
    const F = 6 * N * D, gpuSec = F / (P * M), hours = gpuSec / 3600, days = hours / G / 24;
    Deck.out('tF', F.toExponential(1).replace('e+', 'e'));
    Deck.out('tH', fmt(hours));
    Deck.out('tDays', days < 1 ? (days * 24).toFixed(1) + ' h' : days.toFixed(days < 10 ? 1 : 0));
    Deck.out('tCost', '$' + fmt(hours * 2));
  });

  /* intensity */
  const RIDGE = 989e12 / 3.35e12;
  let op = 'gemm';
  const ai = () => {
    const n = Math.pow(2, Deck.val('aiN')), E = 1 << 24;
    let F, B;
    document.getElementById('aiNrow').style.visibility = op === 'gemm' ? 'visible' : 'hidden';
    Deck.out('aiNo', n);
    if (op === 'add') { F = E; B = 3 * 2 * E; }
    else if (op === 'gelu') { F = 8 * E; B = 2 * 2 * E; }
    else if (op === 'ln') { F = 7 * E; B = 2 * 2 * E; }
    else if (op === 'sm') { F = 5 * E; B = 2 * 2 * E; }
    else { F = 2 * n * n * n; B = 3 * 2 * n * n; }
    const I = F / B;
    Deck.out('aiF', fmt(F)); Deck.out('aiB', Deck.bytes(B)); Deck.out('aiI', I < 10 ? I.toFixed(2) : fmt(I));
    Deck.hbars(document.getElementById('aiBar'), [
      { label: 'this op', value: I, color: I < RIDGE ? 'var(--d)' : 'var(--e)', text: (I < 10 ? I.toFixed(2) : fmt(I)) + ' F/B' },
      { label: 'H100 ridge', value: RIDGE, color: 'var(--faint)', text: RIDGE.toFixed(0) + ' F/B' },
    ], { log: true, min: 0.05, max: 5000 });
    const v = document.getElementById('aiVerdict');
    const util = Math.min(1, I / RIDGE);
    v.innerHTML = I < RIDGE ? `<span style="color:var(--d)">Memory-bound</span>: at best ${(util * 100).toFixed(util < .01 ? 2 : 0)}% of peak FLOPS` : `<span style="color:var(--e)">Compute-bound</span>: the Tensor Cores can run at full speed`;
  };
  Deck.seg('aiOp', v => { op = v; if (document.getElementById('aiN')) ai(); });
  Deck.bind(['aiN'], ai);

  /* roofline */
  const GPUS = { a100: { name: 'A100', P: 312, BW: 2.039 }, h100: { name: 'H100', P: 989, BW: 3.35 }, b200: { name: 'B200', P: 2250, BW: 8 } };
  let gpu = 'h100';
  const roof = () => {
    const s = clear(document.getElementById('roofSvg'));
    const L = 70, R = 640, T = 20, Bm = 330;
    const X = i => L + (Math.log10(i) + 1) / 5 * (R - L);           // 0.1 .. 1e4
    const Y = f => Bm - (Math.log10(f) + 1) / 5 * (Bm - T);           // 0.1 .. 1e4 TFLOPS
    for (let k = -1; k <= 4; k++) {
      svg('line', { x1: X(10 ** k), x2: X(10 ** k), y1: T, y2: Bm, class: 'ln' }, s);
      svg('line', { x1: L, x2: R, y1: Y(10 ** k), y2: Y(10 ** k), class: 'ln' }, s);
      svg('text', { x: X(10 ** k), y: Bm + 16, 'text-anchor': 'middle', class: 'tm tc', text: 10 ** k >= 1 ? fmt(10 ** k, 0) : '0.1' }, s);
      svg('text', { x: L - 8, y: Y(10 ** k) + 4, 'text-anchor': 'end', class: 'tm tc', text: 10 ** k >= 1 ? fmt(10 ** k, 0) : '0.1' }, s);
    }
    svg('text', { x: (L + R) / 2, y: Bm + 36, 'text-anchor': 'middle', class: 'tm', text: 'arithmetic intensity (FLOPs / byte)' }, s);
    svg('text', { x: 14, y: (T + Bm) / 2, 'text-anchor': 'middle', class: 'tm', transform: `rotate(-90 14 ${(T + Bm) / 2})`, text: 'attainable TFLOPS' }, s);
    Object.entries(GPUS).forEach(([k, g]) => {
      const ridge = g.P / g.BW, on = k === gpu;
      const pts = `${X(0.1)},${Y(g.BW * 0.1)} ${X(ridge)},${Y(g.P)} ${X(1e4)},${Y(g.P)}`;
      svg('polyline', { points: pts, fill: 'none', style: `stroke:${on ? 'var(--a)' : 'var(--faint)'};stroke-width:${on ? 3 : 1.2};opacity:${on ? 1 : .45}` }, s);
      if (on) {
        svg('line', { x1: X(ridge), x2: X(ridge), y1: Y(g.P), y2: Bm, style: 'stroke:var(--a);stroke-dasharray:4 4' }, s);
        svg('text', { x: X(ridge) + 6, y: Bm - 8, class: 't tc', style: 'fill:var(--a);font-size:11px', text: `ridge ≈ ${ridge.toFixed(0)}` }, s);
        svg('text', { x: L + 10, y: T + 16, class: 't', style: 'fill:var(--a);font-weight:700', text: `${g.name} · ${g.P} TFLOPS · ${g.BW} TB/s` }, s);
      } else svg('text', { x: X(1e4) - 4, y: Y(g.P) + 14, 'text-anchor': 'end', class: 'tm', style: 'font-size:10px', text: g.name }, s);
    });
    const g = GPUS[gpu], att = I => Math.min(g.P, g.BW * I);
    const b = Math.pow(2, Deck.val('rfB')), d = 8192;
    Deck.out('rfBo', b);
    const points = [
      { n: 'x + y', I: 1 / 6, c: 'var(--d)', dx: 10, dy: 16, a: 'start' },
      { n: 'softmax', I: 1.25, c: 'var(--d)', dx: -10, dy: -10, a: 'end' },
      { n: 'attn decode (GQA-8)', I: 8, c: 'var(--c)', dx: -10, dy: -10, a: 'end' },
      { n: `decode GEMM, batch ${b}`, I: b * d / (d + 2 * b), c: 'var(--b)', big: true, dx: 12, dy: 20, a: 'start' },
      { n: 'prefill GEMM (4K tok)', I: 2048, c: 'var(--e)', dx: 0, dy: 24, a: 'middle' },
    ];
    points.forEach(p => {
      const cx = X(p.I), cy = Y(att(p.I));
      svg('circle', { cx, cy, r: p.big ? 8 : 5.5, style: `fill:${p.c};stroke:var(--panel);stroke-width:2` }, s);
      svg('text', { x: cx + p.dx, y: cy + p.dy, 'text-anchor': p.a, class: 't', style: `font-size:11.5px;fill:${p.c};font-weight:600`, text: p.n }, s);
    });
    const dI = b * d / (d + 2 * b), pct = att(dI) / g.P;
    document.getElementById('rfOut').innerHTML = `Decode at batch ${b}: intensity ≈ ${dI.toFixed(1)} → ${att(dI).toFixed(0)} TFLOPS attainable = <span style="color:${pct < .5 ? 'var(--d)' : 'var(--e)'}">${(pct * 100).toFixed(1)}% of peak</span>`;
  };
  Deck.seg('rfGPU', v => { gpu = v; if (document.getElementById('rfB')) roof(); });
  Deck.bind(['rfB'], roof);

  /* prefill vs decode */
  Deck.bind(['pdP', 'pdO'], () => {
    const P = Deck.val('pdP'), O = Deck.val('pdO');
    Deck.out('pdPo', P.toLocaleString()); Deck.out('pdOo', O.toLocaleString());
    const N = 70e9, flops = 8 * 989e12 * 0.6, bw = 8 * 3.35e12 * 0.8, kvTok = 327680;
    const ttft = 2 * N * P / flops;
    let dec = 0;
    for (let i = 0; i < O; i += 16) dec += 16 * (2 * N + kvTok * (P + i)) / bw;
    const tpot = dec / O;
    const tl = document.getElementById('pdTl').children;
    tl[0].style.width = (100 * ttft / (ttft + dec)) + '%';
    tl[1].style.width = (100 * dec / (ttft + dec)) + '%';
    const ms = x => x < 1 ? (x * 1000).toFixed(0) + ' ms' : x.toFixed(2) + ' s';
    Deck.out('pdTTFT', ms(ttft)); Deck.out('pdTPOT', (tpot * 1000).toFixed(1) + ' ms');
    Deck.out('pdTPS', (1 / tpot).toFixed(0)); Deck.out('pdShare', (100 * dec / (ttft + dec)).toFixed(0) + '%');
  });

  /* batching */
  const N70 = 70e9, W = 140e9, BW = 8 * 3.35e12 * 0.8, FL = 8 * 989e12 * 0.6, KV = 327680, CAP = 640e9 * 0.9;
  const step = (B, ctx) => Math.max((W + B * ctx * KV) / BW, 2 * N70 * B / FL);
  Deck.bind(['bB', 'bC'], () => {
    const B = Math.round(Math.pow(2, Deck.val('bB'))), ctx = Math.pow(2, Deck.val('bC'));
    Deck.out('bBo', B); Deck.out('bCo', ctx >= 1024 ? ctx / 1024 + 'K' : ctx);
    const maxB = Math.floor((CAP - W) / (ctx * KV));
    const s = clear(document.getElementById('batchSvg'));
    const L = 70, R = 640, T = 20, Bm = 250;
    const X = b => L + Math.log2(b) / 10 * (R - L);
    let ymax = 0;
    for (let b = 1; b <= 1024; b *= 1.1) ymax = Math.max(ymax, b / step(b, ctx));
    ymax *= 1.1;
    const Y = v => Bm - v / ymax * (Bm - T);
    for (let k = 0; k <= 10; k += 2) {
      svg('line', { x1: X(2 ** k), x2: X(2 ** k), y1: T, y2: Bm, class: 'ln' }, s);
      svg('text', { x: X(2 ** k), y: Bm + 16, 'text-anchor': 'middle', class: 'tm tc', text: 2 ** k }, s);
    }
    const raw = ymax / 4, p10 = Math.pow(10, Math.floor(Math.log10(raw))), m = raw / p10;
    const stepY = (m <= 1 ? 1 : m <= 2 ? 2 : m <= 5 ? 5 : 10) * p10;
    for (let v = 0; v <= ymax; v += stepY) {
      svg('line', { x1: L, x2: R, y1: Y(v), y2: Y(v), class: 'ln', 'stroke-dasharray': '2 4' }, s);
      svg('text', { x: L - 8, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm tc', style: 'font-size:10px', text: fmt(v, 0) }, s);
    }
    svg('text', { x: (L + R) / 2, y: Bm + 36, 'text-anchor': 'middle', class: 'tm', text: 'batch size (concurrent sequences)' }, s);
    svg('text', { x: 14, y: (T + Bm) / 2, 'text-anchor': 'middle', class: 'tm', transform: `rotate(-90 14 ${(T + Bm) / 2})`, text: 'total tokens / s' }, s);
    if (maxB < 1024) {
      const x0 = X(Math.max(1, maxB));
      svg('rect', { x: x0, y: T, width: R - x0, height: Bm - T, style: 'fill:var(--d-soft)' }, s);
      svg('text', { x: Math.min(x0 + 6, R - 175), y: T + 16, class: 't', style: 'fill:var(--d);font-size:11.5px;font-weight:600', text: 'KV cache exceeds 640 GB' }, s);
    }
    let pts = '';
    for (let b = 1; b <= 1024; b *= 1.05) pts += `${X(b)},${Y(b / step(b, ctx))} `;
    svg('polyline', { points: pts, fill: 'none', style: 'stroke:var(--a);stroke-width:3' }, s);
    const tot = B / step(B, ctx), fits = B <= maxB;
    svg('circle', { cx: X(B), cy: Y(tot), r: 7, style: `fill:${fits ? 'var(--a)' : 'var(--d)'};stroke:var(--panel);stroke-width:2` }, s);
    Deck.out('bTot', fmt(tot)); Deck.out('bUser', (1 / step(B, ctx)).toFixed(0));
    const memT = (W + B * ctx * KV) / BW, cmpT = 2 * N70 * B / FL;
    const bound = memT > cmpT ? (B * ctx * KV > W ? 'KV reads' : 'weight reads') : 'compute';
    Deck.out('bBound', bound);
    document.getElementById('bBound').style.color = bound === 'compute' ? 'var(--e)' : 'var(--d)';
    Deck.out('bMax', maxB.toLocaleString());
    document.getElementById('bMax').style.color = fits ? 'var(--ink)' : 'var(--d)';
  });

  /* precision */
  const FMTS = [
    { k: 'FP32', s: 1, e: 8, m: 23, max: '3.4e38', h: '67*', b: '—', desc: 'IEEE single precision. Used for master weights and optimizer state in mixed-precision training, and as the accumulator type. *CUDA cores; TF32 Tensor Core mode: 495.' },
    { k: 'BF16', s: 1, e: 8, m: 7, max: '3.4e38', h: 989, b: 2250, desc: 'Same 8-bit exponent as FP32 with a short mantissa. The default format for training and inference today, with no loss scaling needed.' },
    { k: 'FP16', s: 1, e: 5, m: 10, max: '65,504', h: 989, b: 2250, desc: 'More mantissa bits but only 5 exponent bits. Training in FP16 needs dynamic loss scaling to avoid underflow.' },
    { k: 'FP8 E4M3', s: 1, e: 4, m: 3, max: '448', h: 1979, b: 4500, desc: 'Hopper\'s FP8. Typically used for weights and activations in the forward pass. Needs per-tensor or per-block scale factors.' },
    { k: 'FP8 E5M2', s: 1, e: 5, m: 2, max: '57,344', h: 1979, b: 4500, desc: 'More range, less precision. Often used for gradients in the backward pass.' },
    { k: 'FP4 E2M1', s: 1, e: 2, m: 1, max: '6', h: '—', b: 9000, desc: 'Blackwell\'s FP4, used as NVFP4 or MXFP4 with a shared scale per block of 16 or 32 values. Mostly for inference and, increasingly, low-precision training.' },
  ];
  const list = document.getElementById('fmtList');
  list.innerHTML = FMTS.map((f, i) => `<div class="fmtrow" data-f="${i}"><b>${f.k}</b><div class="bits">${'<span style="background:var(--d)">s</span>'.repeat(f.s)}${'<span style="background:var(--b)">e</span>'.repeat(f.e)}${'<span style="background:var(--a)">m</span>'.repeat(Math.min(f.m, 23))}</div></div>`).join('') +
    '<div class="legend"><span><i style="background:var(--d)"></i>sign</span><span><i style="background:var(--b)"></i>exponent (range)</span><span><i style="background:var(--a)"></i>mantissa (precision)</span></div>';
  const pickFmt = i => {
    const f = FMTS[i], bits = f.s + f.e + f.m;
    Deck.$$('.fmtrow', list).forEach(r => r.classList.toggle('on', +r.dataset.f === i));
    Deck.out('fmtName', `${f.k} · ${bits} bits`);
    Deck.out('fmtDesc', f.desc);
    Deck.out('fmtMax', f.max);
    Deck.out('fmtMem', (70 * bits / 8).toFixed(bits < 8 ? 1 : 0) + ' GB');
    const num = v => typeof v === 'number' ? v : (parseFloat(v) || 0);
    Deck.hbars(document.getElementById('fmtBars'), [
      { label: 'H100', value: num(f.h), color: 'var(--a)', text: String(f.h) },
      { label: 'B200', value: num(f.b), color: 'var(--c)', text: String(f.b) },
    ], { max: 9000 });
  };
  list.addEventListener('click', e => { const r = e.target.closest('.fmtrow'); if (r) pickFmt(+r.dataset.f); });
  pickFmt(1);

  /* MFU waterfall */
  Deck.bind(['m1', 'm2', 'm3', 'm4', 'm5'], () => {
    const names = ['GEMM eff.', 'Mem-bound', 'Comm', 'Bubbles', 'Stalls'];
    const v = [1, 2, 3, 4, 5].map(i => { const x = Deck.val('m' + i); Deck.out('m' + i + 'o', x + '%'); return x / 100; });
    const s = clear(document.getElementById('mfuSvg'));
    const H = 190, top = 20, bw = 50, gap = 8;
    let level = 1;
    const y = f => top + (1 - f) * H;
    svg('rect', { x: 0, y: y(1), width: bw, height: H, class: 'f-faint', style: 'fill:var(--faint)' }, s);
    svg('text', { x: bw / 2, y: top + H + 16, 'text-anchor': 'middle', class: 'tm', style: 'font-size:10px', text: 'Peak' }, s);
    v.forEach((loss, i) => {
      const next = level * (1 - loss), x = (i + 1) * (bw + gap);
      svg('rect', { x, y: y(level), width: bw, height: Math.max(1, (level - next) * H), style: 'fill:var(--d);opacity:.8' }, s);
      svg('text', { x: x + bw / 2, y: top + H + 16, 'text-anchor': 'middle', class: 'tm', style: 'font-size:9.5px', text: names[i] }, s);
      level = next;
    });
    const x = 6 * (bw + gap);
    svg('rect', { x, y: y(level), width: bw, height: level * H, class: 'f-a' }, s);
    svg('text', { x: x + bw / 2, y: y(level) - 6, 'text-anchor': 'middle', class: 't tc', style: 'font-weight:700;fill:var(--a)', text: (level * 100).toFixed(0) + '%' }, s);
    svg('text', { x: x + bw / 2, y: top + H + 16, 'text-anchor': 'middle', class: 't', style: 'font-size:10px;font-weight:700', text: 'MFU' }, s);
    s.setAttribute('viewBox', `0 0 ${x + bw + 4} 240`);
  });
})();
