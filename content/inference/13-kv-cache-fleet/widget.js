(() => {
  const { svg, clear, fmt } = Deck;
  // ---- How it works: a tiered KV cache serving a stream of conversations
  const s = document.getElementById('kvSvg');
  const TIERS = [['GPU', 3, 'var(--a)', 0], ['CPU', 5, 'var(--c)', 1], ['SSD', 8, 'var(--b)', 4]];   // name, slots, colour, load cost
  const SEQ = ['A', 'B', 'C', 'D', 'A', 'E', 'B', 'F', 'C', 'A', 'G', 'D'];
  let off = true, step = 0, last = 0, log = [];
  function run(n) {   // replay the first n requests from scratch; return tiers, outcome of the last one
    const t = [[], [], []]; let out = null; const cost = { hit: 0, miss: 0 };
    for (let k = 0; k < n; k++) {
      const x = SEQ[k]; let found = -1;
      for (let i = 0; i < 3; i++) { const j = t[i].indexOf(x); if (j >= 0) { found = i; t[i].splice(j, 1); break; } }
      if (found > 0 && !off) found = -1;
      t[0].unshift(x);
      for (let i = 0; i < 3; i++) while (t[i].length > TIERS[i][1]) { const v = t[i].pop(); if (off && i < 2) t[i + 1].unshift(v); }
      out = { x, found }; found >= 0 ? cost.hit++ : cost.miss++;
    }
    return { t, out, cost };
  }
  function draw() {
    const { t, out, cost } = run(step); clear(s);
    TIERS.forEach(([name, cap, col], i) => {
      const y = 40 + i * 78;
      svg('text', { x: 14, y: y + 30, class: 't', style: 'font-weight:700', text: name }, s);
      for (let k = 0; k < cap; k++) {
        const v = (t[i] || [])[k], x = 70 + k * 64;
        svg('rect', { x, y, width: 56, height: 46, rx: 8, style: `fill:${v ? col : 'var(--panel-2)'};opacity:${v ? 0.85 : 1};stroke:${out && v === out.x && i === 0 ? 'var(--ink)' : 'none'};stroke-width:2.5` }, s);
        if (v) svg('text', { x: x + 28, y: y + 29, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:700', text: v }, s);
      }
      if (i > 0 && !off) svg('text', { x: 72, y: y + 29, class: 't', style: 'fill:var(--muted)', text: 'not used: evicted blocks are dropped' }, s);
    });
    svg('text', { x: 14, y: 22, class: 't', text: 'requests: ' + SEQ.map((x, k) => (k === step - 1 ? '[' + x + ']' : x)).join(' ') }, s);
    const msg = !out ? 'press "next request"' : out.found === 0 ? `prefix ${out.x}: hit in GPU memory, no work` : out.found > 0 ? `prefix ${out.x}: hit in ${TIERS[out.found][0]}, loaded back to the GPU` : `prefix ${out.x}: miss, the whole prefix is recomputed`;
    svg('text', { x: 14, y: 285, class: 't', style: `font-weight:700;fill:${out && out.found < 0 ? 'var(--d)' : 'var(--e)'}`, text: msg }, s);
    document.getElementById('kvOut').innerHTML = `${cost.hit} hits, ${cost.miss} recomputes after ${step} requests. ` + (off ? 'Blocks evicted from the GPU drop to CPU memory and then SSD, so returning conversations (A, B, C, D) are loaded instead of recomputed.' : 'Without offloading, anything pushed out of the 3 GPU slots is gone, so returning conversations pay the full prefill again.');
  }
  Deck.seg('kvSeg', v => { off = v === 'on'; draw(); });
  document.getElementById('kvNext').addEventListener('click', () => { step = step >= SEQ.length ? 0 : step + 1; draw(); });
  Deck.enter('s-how', () => { step = 1; draw(); return Deck.loop(t => { if (t - last > 1.6) { last = t; step = step >= SEQ.length ? 0 : step + 1; draw(); } }); });

  // ---- Numbers: load vs recompute
  const TIER = [['CPU memory (PCIe Gen5)', 64], ['network store (one 50 GB/s NIC per GPU)', 50], ['local NVMe SSD (shared by the node)', 7]];
  Deck.bind(['lL', 'lG', 'lT', 'lM'], () => {
    const L = Deck.val('lL') * 1024, G = Math.pow(2, Deck.val('lG')), [tn, bw] = TIER[Deck.val('lT')], mfu = Deck.val('lM') / 100;
    Deck.out('lLo', (L / 1024) + 'K'); Deck.out('lGo', G); Deck.out('lTo', tn.split(' (')[0]); Deck.out('lMo', Math.round(mfu * 100) + '%');
    const kvGB = L * 327680 / 1e9, flops = 2 * 70e9 * L, recompute = flops / (989e12 * mfu * G);
    const load = Deck.val('lT') === 2 ? kvGB / bw : kvGB / G / bw;
    Deck.hbars(document.getElementById('lBars'), [
      { label: 'recompute the prefix', value: recompute, color: 'var(--d)', text: recompute < 1 ? (recompute * 1000).toFixed(0) + ' ms' : recompute.toFixed(2) + ' s' },
      { label: 'load it from ' + tn.split(' (')[0], value: load, color: load < recompute ? 'var(--e)' : 'var(--b)', text: load < 1 ? (load * 1000).toFixed(0) + ' ms' : load.toFixed(2) + ' s' }], { max: Math.max(recompute, load) * 1.05 });
    document.getElementById('lOut').innerHTML = `A ${(L / 1024)}K-token prefix of a Llama-3-70B-shaped model has <b>${kvGB.toFixed(1)} GB</b> of KV (320 KiB per token). ` +
      (load < recompute ? `Loading it is <b>${(recompute / load).toFixed(0)}× faster</b> than recomputing on ${G} GPU${G > 1 ? 's' : ''}.` : `Here recomputing on ${G} GPUs beats loading from one ${tn.split(' (')[0]}: offload to faster tiers or spread the reads.`);
  });
})();
