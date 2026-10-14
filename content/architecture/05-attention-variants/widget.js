(() => {
  const { svg, clear, fmt } = Deck;

  const KV = [1, 2, 4, 8, 16, 32];
  Deck.bind(['kH'], () => {
    const g = KV[Deck.val('kH')], s = clear(document.getElementById('kSvg')), name = g === 1 ? 'MQA' : g === 32 ? 'MHA' : 'GQA';
    Deck.out('kHo', `${g} (${name})`);
    for (let i = 0; i < 32; i++) {
      const x = 14 + i * 20, grp = Math.floor(i / (32 / g)), gx = 14 + (grp + 0.5) * (640 / g) - 8;
      svg('line', { x1: x + 8, y1: 40, x2: gx + 8, y2: 118, style: `stroke:hsl(${grp * 360 / g},55%,55%);stroke-width:1.2;opacity:.7` }, s);
      svg('rect', { x, y: 20, width: 16, height: 20, rx: 3, style: `fill:hsl(${grp * 360 / g},55%,55%)` }, s);
    }
    for (let j = 0; j < g; j++) { const gx = 14 + (j + 0.5) * (640 / g) - 8; svg('rect', { x: gx, y: 118, width: 16, height: 26, rx: 3, style: `fill:hsl(${j * 360 / g},55%,40%)` }, s); }
    svg('text', { x: 4, y: 14, class: 'tm', style: 'font-size:11px', text: '32 query heads' }, s); svg('text', { x: 4, y: 162, class: 'tm', style: 'font-size:11px', text: `${g} K/V head${g > 1 ? 's' : ''} (cached)` }, s);
    const bytes = 2 * 32 * g * 128 * 2;
    document.getElementById('kOut').innerHTML = `${32 / g} query heads per K/V head. KV cache per token (32 layers, head_dim 128, BF16): <b>${Deck.bytes(bytes)}</b>, which is <b>${32 / g}×</b> smaller than MHA. Llama 3 8B uses 8.`;
  });
  const STEPS = [
    ['<b>Compress.</b> c = x·W<sup>DKV</sup>: one d_c-wide latent (512 in DeepSeek-V2) per token per layer. <b>This is what gets cached</b>, instead of 128 heads × (K + V).', ['x', 'c (cached)']],
    ['<b>Expand, naively.</b> Each head\'s key is k_h = c·W<sup>UK</sup>_h and value v_h = c·W<sup>UV</sup>_h. Doing this for every cached token at every step would cost a lot of compute and give back the memory you saved.', ['c (cached)', 'k_h, v_h for all heads']],
    ['<b>Absorb.</b> q_h·k_hᵀ = x·(W<sup>Q</sup>_h W<sup>UK</sup>_hᵀ)·cᵀ. Precompute the product once and the query goes straight into latent space; keys are never materialized. W<sup>UV</sup> is absorbed into the output projection the same way. Notebook 04 checks this is exact.', ['x → latent query', 'score against c directly']],
    ['<b>The RoPE problem.</b> With RoPE the key is R_t·(c_t W<sup>UK</sup>_h), where the rotation R_t depends on the key\'s position. The middle matrix becomes W<sup>Q</sup>_h R_mᵀ R_t W<sup>UK</sup>_hᵀ, which differs for every pair of positions, so it can\'t be precomputed. DeepSeek-V2: "RoPE is incompatible with low-rank KV compression."', ['absorbed matrix', 'depends on m and t ✗']],
    ['<b>Decoupled RoPE.</b> Keep the latent path position-free, and add a small extra slice (d_h<sup>R</sup> = 64) per head for queries plus <b>one RoPE key shared by all heads</b>, cached next to c. Score = content part + RoPE part. Cache per token: d_c + d_h<sup>R</sup> = 576 numbers per layer.', ['c (512) + k^R (64)', 'cached: 576 per layer']],
  ];
  Deck.seg('mSeg', v => {
    const [txt, labels] = STEPS[+v], s = clear(document.getElementById('mSvg'));
    const box = (x, w, label, cls) => { svg('rect', { x, y: 70, width: w, height: 56, rx: 9, class: cls }, s); svg('text', { x: x + w / 2, y: 103, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:600', text: label }, s); };
    box(30, 220, labels[0], 'f-a'); box(410, 220, labels[1], +v === 3 ? 'f-d' : 'f-e');
    svg('line', { x1: 255, x2: 400, y1: 98, y2: 98, style: 'stroke:var(--muted);stroke-width:2.5' }, s);
    svg('path', { d: 'M392 90 L404 98 L392 106', fill: 'none', style: 'stroke:var(--muted);stroke-width:2.5' }, s);
    svg('text', { x: 330, y: 160, 'text-anchor': 'middle', class: 'tm', text: ['W^DKV: d → d_c', 'W^UK, W^UV per head', 'W^Q·W^UKᵀ precomputed', 'R_m, R_t in the middle', 'separate RoPE slice'][+v] }, s);
    document.getElementById('mInfo').innerHTML = txt;
  });
  (() => {
    const rows = [['MHA', 2 * 128 * 128], ['GQA, 8 groups', 2 * 8 * 128], ['MLA (d_c + d_R)', 576], ['MQA', 2 * 128]];
    Deck.hbars(document.getElementById('cBars'), rows.map(([n, v]) => ({ label: n, value: v, color: n.startsWith('MLA') ? 'var(--e)' : n === 'MHA' ? 'var(--d)' : 'var(--a)', text: v.toLocaleString() + ` (${(100 * v / 32768).toFixed(1)}%)` })), { log: true, min: 100 });
  })();

})();
