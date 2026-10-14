(() => {
  const { svg, clear, fmt } = Deck;

  Deck.seg('fSeg', v => {
    const P = +v, full = P * 14, lora = P * 2 + 0.004 * P * 12, q = P * (0.5 + 0.127 / 8) + 0.004 * P * 12;
    Deck.hbars(document.getElementById('fBars'), [
      { label: 'full fine-tune', value: full, color: 'var(--d)', text: Math.round(full) + ' GB' },
      { label: 'LoRA (BF16 base)', value: lora, color: 'var(--b)', text: Math.round(lora) + ' GB' },
      { label: 'QLoRA (NF4 base)', value: q, color: 'var(--a)', text: q.toFixed(1) + ' GB' }], { max: 65 * 14 });
  });
  const SHAPES = { q: [4096, 4096], k: [4096, 1024], v: [4096, 1024], o: [4096, 4096], gate: [4096, 14336], up: [4096, 14336], down: [14336, 4096] };
  const SETS = { qv: ['q', 'v'], attn: ['q', 'k', 'v', 'o'], all: Object.keys(SHAPES) };
  let set = 'qv';
  const lc = () => {
    const r = Math.pow(2, Deck.val('lR')); Deck.out('lRo', r);
    const n = 32 * SETS[set].reduce((a, k) => a + r * (SHAPES[k][0] + SHAPES[k][1]), 0);
    Deck.out('lP', n.toLocaleString()); Deck.out('lF', (100 * n / 8.03e9).toPrecision(2) + '%'); Deck.out('lS', Deck.bytes(2 * n));
    const s = clear(document.getElementById('lSvg')), d = 110, w = Math.max(3, r / 256 * d);
    svg('rect', { x: 40, y: 20, width: d, height: d, rx: 4, style: 'fill:var(--panel-2);stroke:var(--line)' }, s); svg('text', { x: 95, y: 80, 'text-anchor': 'middle', class: 't', text: 'W₀ (frozen)' }, s);
    svg('text', { x: 175, y: 82, 'text-anchor': 'middle', class: 't', style: 'font-size:20px', text: '+' }, s);
    svg('rect', { x: 210, y: 20, width: w, height: d, rx: 2, class: 'f-a' }, s); svg('text', { x: 210 + w / 2, y: 145, 'text-anchor': 'middle', class: 'tm', text: 'A' }, s);
    svg('rect', { x: 220 + w, y: 20, width: d, height: w, rx: 2, class: 'f-b' }, s); svg('text', { x: 230 + w + d, y: 20 + w / 2 + 4, class: 'tm', text: 'B' }, s);
    svg('text', { x: 400, y: 60, class: 't', text: `r = ${r}: A is d×${r}, B is ${r}×d` }, s);
    svg('text', { x: 400, y: 86, class: 'tm', text: `adapters on: ${SETS[set].map(k => 'W_' + k).join(', ')}` }, s);
  };
  Deck.bind(['lR'], lc); Deck.seg('lT', v => { set = v; lc(); });
  (() => {
    const NF4 = [-1.0, -0.6962, -0.5251, -0.3949, -0.2844, -0.1848, -0.0911, 0.0, 0.0796, 0.1609, 0.2461, 0.3379, 0.4407, 0.5626, 0.7230, 1.0];
    const s = document.getElementById('qSvg'), X = v => 40 + (v + 1) / 2 * 580;
    let p = ''; for (let v = -1; v <= 1.001; v += 0.01) p += `${X(v)},${150 - 110 * Math.exp(-((v / 0.35) ** 2) / 2)} `;
    svg('polyline', { points: p, fill: 'none', style: 'stroke:var(--faint);stroke-width:2' }, s);
    svg('line', { x1: 40, x2: 620, y1: 150, y2: 150, class: 'ln' }, s);
    NF4.forEach(v => svg('line', { x1: X(v), x2: X(v), y1: 120, y2: 150, style: 'stroke:var(--a);stroke-width:2.5' }, s));
    for (let i = 0; i < 16; i++) { const v = -1 + 2 * i / 15; svg('line', { x1: X(v), x2: X(v), y1: 155, y2: 180, style: 'stroke:var(--b);stroke-width:2.5' }, s); }
    [-1, -0.5, 0, 0.5, 1].forEach(v => svg('text', { x: X(v), y: 196, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: v }, s));
    svg('text', { x: 40, y: 20, class: 'tm', text: 'weights ÷ block absmax (values in [−1, 1])' }, s);
  })();

})();
