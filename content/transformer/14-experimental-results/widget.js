(() => {
  const { svg, clear } = Deck;
  // [name, bleuDE, bleuFR, flopsDE, flopsFR, ensemble, transformer]
  const T2 = [
    ['ByteNet', 23.75, null, null, null, 0, 0],
    ['Deep-Att + PosUnk', null, 39.2, null, 1.0e20, 0, 0],
    ['GNMT + RL', 24.6, 39.92, 2.3e19, 1.4e20, 0, 0],
    ['ConvS2S', 25.16, 40.46, 9.6e18, 1.5e20, 0, 0],
    ['MoE', 26.03, 40.56, 2.0e19, 1.2e20, 0, 0],
    ['Deep-Att + PosUnk Ens.', null, 40.4, null, 8.0e20, 1, 0],
    ['GNMT + RL Ens.', 26.30, 41.16, 1.8e20, 1.1e21, 1, 0],
    ['ConvS2S Ens.', 26.36, 41.29, 7.7e19, 1.2e21, 1, 0],
    ['Transformer (base)', 27.3, 38.1, 3.3e18, 3.3e18, 0, 1],
    ['Transformer (big)', 28.4, 41.8, 2.3e19, 2.3e19, 0, 1],
  ];
  let lang = 'de', showT = false;
  const scatter = () => {
    const s = clear(document.getElementById('scSvg'));
    const bi = lang === 'de' ? 1 : 2, fi = lang === 'de' ? 3 : 4;
    const pts = T2.filter(r => r[bi] != null && r[fi] != null && (showT || !r[6]));
    const [ylo, yhi] = lang === 'de' ? [23.5, 29] : [37.5, 42.5];
    const L = 70, R = 640, T = 20, B = 290;
    const X = f => L + (Math.log10(f) - 18) / 3.3 * (R - L), Y = b => B - (b - ylo) / (yhi - ylo) * (B - T);
    for (let e = 18; e <= 21; e++) {
      svg('line', { x1: X(10 ** e), x2: X(10 ** e), y1: T, y2: B, class: 'ln' }, s);
      svg('text', { x: X(10 ** e), y: B + 16, 'text-anchor': 'middle', class: 'tm tc', text: `10^${e}` }, s);
    }
    for (let b = Math.ceil(ylo); b <= yhi; b++) {
      svg('line', { x1: L, x2: R, y1: Y(b), y2: Y(b), class: 'ln', 'stroke-dasharray': '2 4' }, s);
      svg('text', { x: L - 6, y: Y(b) + 4, 'text-anchor': 'end', class: 'tm tc', style: 'font-size:10.5px', text: b }, s);
    }
    svg('text', { x: (L + R) / 2, y: B + 36, 'text-anchor': 'middle', class: 'tm', text: 'training cost (FLOPs, log scale), lower is better' }, s);
    svg('text', { x: 14, y: (T + B) / 2, 'text-anchor': 'middle', class: 'tm', transform: `rotate(-90 14 ${(T + B) / 2})`, text: `BLEU ${lang === 'de' ? 'EN-DE' : 'EN-FR'} (newstest2014), higher is better` }, s);
    pts.forEach(r => {
      const x = X(r[fi]), y = Y(r[bi]), c = r[6] ? 'var(--e)' : r[5] ? 'var(--c)' : 'var(--faint)';
      svg('circle', { cx: x, cy: y, r: r[6] ? 9 : 7, style: `fill:${c};stroke:var(--panel);stroke-width:2` }, s);
      const right = x < 520;
      const dy = r[0].startsWith('GNMT + RL Ens') ? 20 : r[0].startsWith('ConvS2S Ens') ? -10 : r[0].startsWith('Deep-Att + PosUnk Ens') ? 18 : 4;
      svg('text', { x: x + (right ? 12 : -12), y: y + dy, 'text-anchor': right ? 'start' : 'end', class: 't', style: `font-size:11.5px;font-weight:${r[6] ? 700 : 500};fill:${r[6] ? 'var(--e)' : 'var(--ink)'}`, text: `${r[0]} · ${r[bi]}` }, s);
    });
    if (showT) svg('text', { x: L + 8, y: T + 14, class: 't', style: 'fill:var(--e);font-size:12px;font-weight:600', text: '↖ better and cheaper' }, s);
  };
  Deck.seg('lSeg', v => { lang = v; scatter(); });
  Deck.seg('tSeg', v => { showT = v === '1'; scatter(); });

  /* cost derivation */
  Deck.seg('cSeg', v => {
    const base = v === 'base', t = base ? 12 * 3600 : 3.5 * 86400, F = t * 8 * 9.5e12;
    const m = F.toExponential(2).split('e+');
    document.getElementById('cEq').innerHTML = `${base ? '12 hours' : '3.5 days'} = ${t.toLocaleString()} s &nbsp;×&nbsp; 8 GPUs &nbsp;×&nbsp; 9.5·10¹² FLOP/s &nbsp;=&nbsp; <b>${m[0]}·10^${m[1]}</b>`;
    Deck.out('cT', base ? '12 h (100K steps × ~0.4 s)' : '3.5 days (300K steps × 1.0 s)');
    Deck.out('cF', (base ? '3.3·10¹⁸' : '2.3·10¹⁹') + ' ✓ Table 2');
  });

  /* parsing */
  const P4 = {
    wsj: [['Vinyals & Kaiser et al. (2014)', 88.3], ['Petrov et al. (2006)', 90.4], ['Zhu et al. (2013)', 90.4], ['Dyer et al. (2016)', 91.7], ['Transformer (4 layers)', 91.3]],
    semi: [['Zhu et al. (2013), semi-sup.', 91.3], ['Huang & Harper (2009), semi-sup.', 91.3], ['McClosky et al. (2006), semi-sup.', 92.1], ['Vinyals & Kaiser (2014), semi-sup.', 92.1], ['Transformer (4 layers), semi-sup.', 92.7], ['Luong et al. (2015), multi-task', 93.0], ['Dyer et al. (2016), generative', 93.3]],
  };
  Deck.seg('pSeg', v => {
    Deck.hbars(document.getElementById('pBars'), P4[v].map(([n, f]) => ({ label: n, value: f - 87, color: n.startsWith('Transformer') ? 'var(--e)' : 'var(--faint)', text: f.toFixed(1) + ' F1' })), { max: 7 });
  });
})();
