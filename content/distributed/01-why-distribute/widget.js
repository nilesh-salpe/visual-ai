(() => {
  const { svg, clear, fmt } = Deck;
  const NS = [1e9, 7e9, 70e9, 405e9, 1e12, 2e12], DS = [1e11, 2e12, 15e12, 30e12], GS = [1, 8, 256, 2048, 16384, 65536];
  const lab = v => v >= 1e12 ? (v / 1e12) + 'T' : (v / 1e9) + 'B';
  Deck.bind(['wN', 'wD', 'wG'], () => {
    const N = NS[Deck.val('wN')], D = DS[Deck.val('wD')], G = GS[Deck.val('wG')];
    Deck.out('wNo', lab(N)); Deck.out('wDo', lab(D) + ' tokens'); Deck.out('wGo', G.toLocaleString());
    Deck.out('wM', (16 * N / 1e12 >= 1 ? (16 * N / 1e12).toFixed(1) + ' TB' : (16 * N / 1e9).toFixed(0) + ' GB') + ` (${(16 * N / 80e9).toFixed(1)}× one GPU)`);
    Deck.out('wF', (6 * N * D).toExponential(1));
    const days = 6 * N * D / (989e12 * 0.4 * G) / 86400;
    Deck.out('wT', days > 3650 ? (days / 365).toFixed(0) + ' years' : days.toFixed(days < 10 ? 1 : 0));
  });
})();
(() => {
  // Axes explorer: one animation per parallelism axis on four GPUs; text panels live in deck.md
  const { svg, clear } = Deck;
  const s = document.getElementById('axSvg');
  if (!s) return;
  const COL = ['var(--a)', 'var(--b)', 'var(--c)', 'var(--e)'];
  const GX = i => 12 + i * 76, GW = 68;
  let mode = 'dp', t0 = 0;
  const T = (x, y, txt, o = {}) => svg('text', { x, y, text: txt, 'text-anchor': o.anchor || 'middle', style: `font:${o.w || 600} ${o.size || 11}px Inter, sans-serif;fill:${o.fill || 'var(--ink)'}` }, s);
  const R = (x, y, w, h, fill, o = {}) => svg('rect', { x, y, width: w, height: h, rx: o.rx ?? 4, style: `fill:${fill};opacity:${o.op ?? 1};stroke:${o.stroke || 'none'};stroke-width:${o.sw || 1}` + (o.dash ? ';stroke-dasharray:4 3' : '') }, s);
  const L = (x1, y1, x2, y2, col, o = {}) => svg('line', { x1, y1, x2, y2, style: `stroke:${col};stroke-width:${o.w || 2}` + (o.dash ? `;stroke-dasharray:5 4;stroke-dashoffset:${o.off || 0}` : '') }, s);
  const C = (x, y, r, fill) => svg('circle', { cx: x, cy: y, r, style: `fill:${fill}` }, s);
  const gpus = (top = 34, h = 180) => { for (let i = 0; i < 4; i++) { R(GX(i), top, GW, h, 'var(--panel)', { stroke: 'var(--line)', rx: 8 }); T(GX(i) + GW / 2, top + 14, 'GPU ' + (i + 1), { size: 10, fill: 'var(--muted)' }); } };
  const caption = txt => T(160, 288, txt, { size: 11, w: 500, fill: 'var(--muted)' });
  const LY = k => 72 + k * 34;   // layer rows

  const draw = {
    dp(t) {
      const p = t % 4; gpus();
      for (let i = 0; i < 4; i++) {
        R(GX(i) + 6, 52, GW - 12, 12, 'var(--f-soft, var(--panel-2))', { stroke: 'var(--line)' }); T(GX(i) + GW / 2, 62, 'batch ' + (i + 1), { size: 9, w: 500 });
        for (let k = 0; k < 4; k++) R(GX(i) + 8, LY(k), GW - 16, 22, COL[k], { op: 0.85 });
        if (p < 2) { const y = p < 1 ? 72 + p * 124 : 196 - (p - 1) * 124; C(GX(i) + GW / 2, y + 11, 6, p < 1 ? 'var(--ink)' : 'var(--d)'); }
      }
      if (p >= 2) { L(GX(0) + GW / 2, 230, GX(3) + GW / 2, 230, 'var(--d)', { w: 3, dash: 1, off: -t * 30 }); T(160, 250, 'all-reduce: average gradients', { size: 10, fill: 'var(--d)' }); }
      T(160, 18, 'Full model on every GPU, different data', { size: 12 });
      caption(p < 1 ? 'forward pass on each GPU\'s own batch' : p < 2 ? 'backward pass computes local gradients' : 'one all-reduce, then identical updates');
    },
    fsdp(t) {
      const p = t % 4, act = p < 2 ? Math.floor(p * 2) : 3 - Math.floor((p - 2) * 2);
      gpus();
      for (let i = 0; i < 4; i++) for (let k = 0; k < 4; k++) for (let j = 0; j < 4; j++) {
        const own = j === i, live = k === act && p < 3;
        R(GX(i) + 8 + j * 13, LY(k), 12, 22, COL[k], { op: own ? 0.9 : live ? 0.55 : 0.08, stroke: own ? 'var(--ink)' : 'none', rx: 2 });
      }
      if (p < 3) T(160, 236, (p < 2 ? 'all-gather layer ' : 're-gather layer ') + (act + 1) + ', use it, free it', { size: 10, fill: 'var(--b)' });
      else { L(GX(0) + GW / 2, 230, GX(3) + GW / 2, 230, 'var(--d)', { w: 3, dash: 1, off: -t * 30 }); T(160, 250, 'reduce-scatter gradients into shards', { size: 10, fill: 'var(--d)' }); }
      T(160, 18, 'Each GPU stores 1/4 of each layer', { size: 12 });
      caption(p < 2 ? 'forward: gather one layer at a time' : p < 3 ? 'backward: gather again, layer by layer' : 'each GPU updates only its own shard');
    },
    tp(t) {
      const p = t % 4, layer = Math.min(3, Math.floor(p));
      gpus();
      for (let i = 0; i < 4; i++) for (let k = 0; k < 4; k++) { R(GX(i) + 8, LY(k), 51, 22, 'none', { stroke: 'var(--line)', dash: 1, rx: 2 }); R(GX(i) + 8 + i * 13, LY(k), 12, 22, COL[k], { op: k <= layer ? 0.95 : 0.35, rx: 2 }); }
      for (let i = 0; i < 4; i++) T(GX(i) + GW / 2, 207, 'slice ' + (i + 1), { size: 9, w: 500, fill: 'var(--muted)' });
      const frac = p - layer, y = LY(layer) + 26;
      if (frac > 0.5) { L(GX(0) + 10, y, GX(3) + GW - 10, y, 'var(--d)', { w: 3, dash: 1, off: -t * 40 }); }
      T(160, 18, 'Each layer split; same input on all', { size: 12 });
      caption(frac > 0.5 ? 'all-reduce after layer ' + (layer + 1) + ' (NVLink)' : 'each GPU computes its slice of layer ' + (layer + 1));
    },
    pp(t) {
      const P = 4, M = 4, S = 2 * (M + P - 1), cur = Math.floor((t % 5) / 4 * S);
      const x0 = 56, w = (310 - x0) / S;
      T(160, 18, '4 stages; micro-batches flow through', { size: 12 });
      for (let st = 0; st < P; st++) {
        const y = 44 + st * 46; T(28, y + 22, 'GPU ' + (st + 1), { size: 10, fill: 'var(--muted)' });
        for (let sl = 0; sl < S; sl++) R(x0 + sl * w + 1, y, w - 2, 34, 'var(--panel)', { stroke: 'var(--line)', rx: 2 });
        for (let j = 0; j < M; j++) {
          const f = st + j, b = (M + P - 1) + (P - 1 - st) + (M - 1 - j);
          if (f <= cur) { R(x0 + f * w + 1, y, w - 2, 34, COL[j], { op: 0.85, rx: 2 }); T(x0 + f * w + w / 2, y + 21, 'F' + (j + 1), { size: 8, fill: '#fff' }); }
          if (b <= cur) { R(x0 + b * w + 1, y, w - 2, 34, COL[j], { op: 0.45, rx: 2 }); T(x0 + b * w + w / 2, y + 21, 'B' + (j + 1), { size: 8 }); }
        }
      }
      L(x0 + (cur + 1) * w, 38, x0 + (cur + 1) * w, 228, 'var(--ink)', { w: 1 });
      T(160, 250, 'empty cells = idle bubble: 3 of 7 slots per GPU here', { size: 10, fill: 'var(--d)' });
      caption('F1–F4 flow down, then B4–B1 flow back');
    },
    cp(t) {
      const step = Math.floor(t % 4);
      T(160, 18, 'The sequence is split into 4 chunks', { size: 12 });
      for (let k = 0; k < 16; k++) R(14 + k * 18.5, 28, 16, 12, COL[Math.floor(k / 4)], { op: 0.9, rx: 2 });
      gpus(52, 170);
      for (let i = 0; i < 4; i++) {
        R(GX(i) + 8, 84, GW - 16, 30, COL[i], { op: 0.9 }); T(GX(i) + GW / 2, 103, 'Q chunk ' + (i + 1), { size: 9, fill: '#fff' });
        const kv = (i - step + 4) % 4;
        R(GX(i) + 8, 140, GW - 16, 30, COL[kv], { op: 0.55 }); T(GX(i) + GW / 2, 159, 'K/V ' + (kv + 1), { size: 9 });
      }
      for (let i = 0; i < 3; i++) L(GX(i) + GW - 8, 155, GX(i + 1) + 8, 155, 'var(--d)', { w: 2, dash: 1, off: -t * 30 });
      L(GX(3) + GW / 2, 222, GX(3) + GW / 2, 234, 'var(--d)', { w: 2 }); L(GX(3) + GW / 2, 234, GX(0) + GW / 2, 234, 'var(--d)', { w: 2, dash: 1, off: -t * 30 }); L(GX(0) + GW / 2, 234, GX(0) + GW / 2, 222, 'var(--d)', { w: 2 });
      T(160, 254, 'ring: pass K/V blocks to the next GPU', { size: 10, fill: 'var(--d)' });
      caption('step ' + (step + 1) + '/4: queries attend to the K/V held now');
    },
    ep(t) {
      const p = t % 4; gpus();
      const route = [5, 2, 7, 0, 3, 6, 1, 4];            // token → expert (2 experts per GPU)
      for (let e = 0; e < 8; e++) { const g = Math.floor(e / 2); R(GX(g) + 6 + (e % 2) * 30, 150, 26, 40, 'var(--c)', { op: p > 1.4 && p < 2.6 ? 0.9 : 0.35 }); T(GX(g) + 19 + (e % 2) * 30, 174, 'E' + (e + 1), { size: 9, fill: '#fff' }); }
      for (let k = 0; k < 8; k++) {
        const home = Math.floor(k / 2), e = route[k], dst = Math.floor(e / 2);
        const hx = GX(home) + 20 + (k % 2) * 28, hy = 70, ex = GX(dst) + 19 + (e % 2) * 30, ey = 140;
        const a = p < 1.4 ? p / 1.4 : p < 2.6 ? 1 : p < 4 ? 1 - (p - 2.6) / 1.4 : 0;
        C(hx + (ex - hx) * a, hy + (ey - hy) * a, 6, COL[home]);
      }
      T(160, 18, '8 experts on 4 GPUs; tokens routed', { size: 12 });
      T(160, 236, p < 1.4 ? 'all-to-all dispatch' : p < 2.6 ? 'experts compute' : 'all-to-all combine', { size: 10, fill: 'var(--d)' });
      caption('tokens go to their expert\'s GPU and back');
    },
  };
  const render = t => { clear(s); draw[mode](t); };
  Deck.seg('axSeg', v => {
    mode = v; t0 = performance.now();
    Deck.$$('.explorer-panel').forEach(el => { el.hidden = el.dataset.axis !== v; });
    render(0);
  });
  Deck.enter('s-axes', () => Deck.loop(() => render((performance.now() - t0) / 1000 * 0.8)));
})();
