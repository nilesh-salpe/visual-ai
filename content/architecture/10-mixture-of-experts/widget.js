(() => {
  const { svg, clear, fmt } = Deck;

  Deck.hbars(document.getElementById('mBars'), [
    { label: 'Mixtral 8x7B total', value: 47, color: 'var(--faint)', text: '47B' }, { label: 'Mixtral active / token', value: 13, color: 'var(--a)', text: '13B' },
    { label: 'DeepSeek-V2 total', value: 236, color: 'var(--faint)', text: '236B' }, { label: 'DeepSeek-V2 active / token', value: 21, color: 'var(--a)', text: '21B' },
    { label: 'Llama 3 70B (dense)', value: 70, color: 'var(--b)', text: '70B = 70B' }], { max: 240 });
  let seed = 7; const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  const gauss = () => { const u = Math.max(1e-9, rnd()), v = rnd(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
  const LOG = [...Array(6)].map(() => [...Array(8)].map(() => gauss() * 1.4));
  Deck.seg('kSeg', v => {
    const k = +v, s = clear(document.getElementById('rSvg')), load = Array(8).fill(0);
    LOG.forEach((row, t) => {
      const idx = row.map((x, i) => [x, i]).sort((a, b) => b[0] - a[0]).slice(0, k), mx = idx[0][0], ex = idx.map(([x]) => Math.exp(x - mx)), sum = ex.reduce((a, b) => a + b);
      const ty = 30 + t * 36;
      svg('rect', { x: 10, y: ty - 13, width: 210, height: 26, rx: 6, style: 'fill:var(--b)' }, s);
      svg('text', { x: 115, y: ty + 5, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:600;font-size:12px', text: `token ${t + 1} → ` + idx.map(([x, e], j) => `E${e + 1} ${(ex[j] / sum).toFixed(2)}`).join(' · ') }, s);
      idx.forEach(([x, e], j) => { load[e]++; const ey = 22 + e * 27; svg('line', { x1: 220, y1: ty, x2: 420, y2: ey + 10, style: `stroke:var(--a);stroke-width:${1 + 7 * ex[j] / sum};opacity:.85` }, s); });
    });
    for (let e = 0; e < 8; e++) {
      const ey = 22 + e * 27; svg('rect', { x: 420, y: ey, width: 80, height: 21, rx: 5, class: 'f-a' }, s);
      svg('text', { x: 460, y: ey + 15, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:12px', text: 'expert ' + (e + 1) }, s);
      svg('rect', { x: 510, y: ey + 3, width: load[e] * 22, height: 15, rx: 3, style: 'fill:var(--c)' }, s);
      svg('text', { x: 516 + load[e] * 22, y: ey + 15, class: 'tm', style: 'font-size:11px', text: load[e] }, s);
    }
  });
  const TOK = 4096, NE = 8; seed = 11; const BASE = [...Array(TOK)].map(() => [...Array(NE)].map(gauss));
  Deck.bind(['bS'], () => {
    const sk = Deck.val('bS'); Deck.out('bSo', sk.toFixed(1));
    const f = Array(NE).fill(0), P = Array(NE).fill(0), assign = [];
    BASE.forEach(row => {
      const lg = row.map((x, i) => x + sk * (1 - i / (NE - 1))), mx = Math.max(...lg), ex = lg.map(x => Math.exp(x - mx)), sm = ex.reduce((a, b) => a + b);
      ex.forEach((e, i) => P[i] += e / sm / TOK); const a = lg.indexOf(mx); f[a] += 1 / TOK; assign.push(a);
    });
    const cap = Math.floor(TOK / NE * 1.25), used = Array(NE).fill(0); let drop = 0; assign.forEach(a => { if (used[a] < cap) used[a]++; else drop++; });
    Deck.out('bL', (0.01 * NE * f.reduce((a, x, i) => a + x * P[i], 0)).toFixed(4)); Deck.out('bM', (100 * Math.max(...f)).toFixed(0) + '%'); Deck.out('bD', (100 * drop / TOK).toFixed(1) + '%');
    Deck.hbars(document.getElementById('bBars'), f.map((x, i) => ({ label: 'expert ' + (i + 1), value: x, color: x * TOK > cap ? 'var(--d)' : 'var(--a)', text: (100 * x).toFixed(1) + '%' })), { max: 0.5 });
  });

})();
