(() => {
  const { svg, clear, fmt } = Deck;
  // ---- How it works: one MoE layer on four GPUs
  const s = document.getElementById('moeSvg'), COL = ['var(--a)', 'var(--b)', 'var(--c)', 'var(--e)'];
  const TOK = [[1, 3, 2], [3, 4, 3], [5, 3, 6], [7, 3, 8]];
  const gx = i => 15 + i * 160;
  let red = false, t0 = performance.now();
  const slotC = (g, k) => [gx(g) + 30 + k * 45, 190];
  function plan() {
    const fill = {}, dest = [], load = [0, 0, 0, 0];
    TOK.forEach((row, i) => row.forEach((e, j) => {
      let g = Math.floor((e - 1) / 2), k = (e - 1) % 2;
      if (red && e === 3 && i !== 1) { g = i; k = 2; }
      const key = g + ':' + k, n = fill[key] = (fill[key] || 0) + 1;
      const [cx, cy] = slotC(g, k); dest.push([i, j, cx, cy - 22 + (n - 1) * 11]); load[g]++;
    }));
    return { dest, load };
  }
  function draw(t) {
    const p = t % 6, { dest, load } = plan(); clear(s);
    const phase = p < 1 ? 'attention: each GPU runs its own requests (data parallel)' : p < 2.2 ? 'dispatch: all-to-all sends each token to its expert' : p < 3.8 ? 'experts compute: the layer waits for the busiest GPU' : p < 5 ? 'combine: all-to-all returns results to each token\'s GPU' : 'next layer';
    svg('text', { x: 330, y: 18, 'text-anchor': 'middle', class: 't', style: 'font-weight:700', text: phase }, s);
    for (let i = 0; i < 4; i++) {
      svg('rect', { x: gx(i), y: 30, width: 150, height: 210, rx: 10, style: 'fill:var(--panel);stroke:var(--line)' }, s);
      svg('text', { x: gx(i) + 75, y: 46, 'text-anchor': 'middle', class: 't', style: 'fill:var(--muted)', text: 'GPU ' + (i + 1) }, s);
      svg('rect', { x: gx(i) + 10, y: 54, width: 130, height: 44, rx: 6, style: `fill:${COL[i]};opacity:${p < 1 ? 0.25 : 0.1}` }, s);
      svg('text', { x: gx(i) + 75, y: 112, 'text-anchor': 'middle', class: 't', style: 'fill:var(--muted)', text: 'attention (DP)' }, s);
      for (let k = 0; k < 3; k++) {
        if (k === 2 && !(red && i !== 1)) continue;
        const e = k < 2 ? 2 * i + k + 1 : 3, busy = p >= 2.2 && p < 3.8;
        svg('rect', { x: gx(i) + 10 + k * 45, y: 160, width: 40, height: 62, rx: 6, style: `fill:${k === 2 ? 'var(--d)' : 'var(--c)'};opacity:${busy ? 0.5 : 0.22};stroke:${k === 2 ? 'var(--d)' : 'none'}` }, s);
        svg('text', { x: gx(i) + 30 + k * 45, y: 236, 'text-anchor': 'middle', class: 't', text: 'E' + e + (k === 2 ? ' copy' : '') }, s);
      }
      const w = 130 * Math.min(1, (p < 2.2 ? 0 : Math.min(1, (p - 2.2) / 1.6)) * load[i] / 6);
      svg('rect', { x: gx(i) + 10, y: 258, width: 130, height: 14, rx: 4, style: 'fill:var(--panel-2)' }, s);
      svg('rect', { x: gx(i) + 10, y: 258, width: w, height: 14, rx: 4, style: `fill:${load[i] === Math.max(...load) && !red ? 'var(--d)' : 'var(--e)'}` }, s);
      svg('text', { x: gx(i) + 75, y: 290, 'text-anchor': 'middle', class: 't', text: load[i] + ' tokens' }, s);
    }
    dest.forEach(([i, j, cx, cy]) => {
      const hx = gx(i) + 30 + j * 45, hy = 76;
      const a = p < 1 ? 0 : p < 2.2 ? (p - 1) / 1.2 : p < 3.8 ? 1 : p < 5 ? 1 - (p - 3.8) / 1.2 : 0;
      svg('circle', { cx: hx + (cx - hx) * a, cy: hy + (cy - hy) * a, r: 6, style: `fill:${COL[i]};stroke:#fff;stroke-width:1.5` }, s);
    });
    svg('text', { x: 330, y: 318, 'text-anchor': 'middle', class: 't', style: 'fill:var(--muted)', text: 'expert compute time per layer ∝ busiest GPU' }, s);
  }
  Deck.seg('moeSeg', v => {
    red = v === 'on'; t0 = performance.now(); draw(0);
    const { load } = plan(), mx = Math.max(...load), avg = load.reduce((a, b) => a + b, 0) / 4;
    document.getElementById('moeOut').innerHTML = red
      ? `Copies of the hot expert E3 on GPUs 1, 3 and 4 take their local E3 tokens. Loads ${load.join(', ')}: every GPU finishes together (<b>${Math.round(100 * avg / mx)}%</b> balanced), and fewer tokens cross between GPUs.`
      : `E3 is hot: 5 of 12 tokens choose it. Loads ${load.join(', ')}: the layer takes as long as GPU 2, so the GPUs are only <b>${Math.round(100 * avg / mx)}%</b> balanced and the others wait.`;
  });
  Deck.enter('s-how', () => Deck.loop(() => draw((performance.now() - t0) / 1000)));

  // ---- Numbers: tokens per expert and memory per GPU
  const EPS = [8, 16, 32, 64, 72, 144, 256, 320], EXPERT_GB = 2.554, RIDGE = 1979 / 3.35;
  Deck.bind(['nEP', 'nB', 'nR'], () => {
    const ep = EPS[Deck.val('nEP')], b = Deck.val('nB'), r = Deck.val('nR');
    Deck.out('nEPo', ep); Deck.out('nBo', b); Deck.out('nRo', r);
    const inst = 256 + r, per = Math.ceil(inst / ep), mem = per * EXPERT_GB, tok = b * ep * 8 / inst, util = Math.min(1, 2 * tok / RIDGE);
    Deck.hbars(document.getElementById('nBars'), [
      { label: 'routed experts per GPU', value: per, color: 'var(--c)', text: per + '' },
      { label: 'expert weights per GPU (FP8)', value: mem / 80, color: mem > 80 ? 'var(--d)' : 'var(--a)', text: mem.toFixed(0) + ' GB' },
      { label: 'tokens per expert per step', value: Math.min(1, tok / 300), color: tok < 100 ? 'var(--d)' : 'var(--e)', text: tok.toFixed(0) },
      { label: 'expert matmul: share of FP8 peak (roofline)', value: util, color: 'var(--b)', text: Math.round(100 * util) + '%' }], { max: 1 });
    document.getElementById('nOut').innerHTML = `EP ${ep} with ${b} decode sequences per GPU: each of the ${inst} expert instances sees about <b>${tok.toFixed(0)} tokens</b> per step. ` +
      (mem > 80 ? `Expert weights alone (${mem.toFixed(0)} GB) exceed an 80 GB H100. ` : '') +
      (tok < 150 ? 'Too few tokens: expert matmuls just stream weights from memory. Spread experts wider or batch more.' : 'Enough tokens per expert to approach compute-bound matmuls.');
  });
})();
