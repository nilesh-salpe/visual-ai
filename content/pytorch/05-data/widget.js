(() => {
  const { svg, clear, fmt } = Deck;
  let mode = 'pad', seed = 3; const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  const LEN = [...Array(64)].map(() => 20 + Math.floor(rnd() * 380));
  const draw = () => {
    const B = Deck.val('dB'); Deck.out('dBo', B); const lens = LEN.slice(0, B), s = clear(document.getElementById('dSvg')), L = Math.max(...lens), W = 560 / 400, rh = Math.min(28, 220 / B);
    let real = lens.reduce((a, b) => a + b), comp;
    if (mode === 'pad') {
      lens.forEach((l, i) => { svg('rect', { x: 60, y: 10 + i * rh, width: L * W, height: rh - 3, style: 'fill:var(--panel-2)' }, s); svg('rect', { x: 60, y: 10 + i * rh, width: l * W, height: rh - 3, style: 'fill:var(--a)' }, s); });
      comp = B * L;
    } else {
      const rows = Math.ceil(real / L); let used = 0, col = ['var(--a)', 'var(--c)', 'var(--b)', 'var(--e)'];
      lens.forEach((l, k) => { let rem = l; while (rem > 0) { const r = Math.floor(used / L), c = used % L, take = Math.min(rem, L - c);
        svg('rect', { x: 60 + c * W, y: 10 + r * rh, width: take * W - 1, height: rh - 3, style: `fill:${col[k % 4]}` }, s); used += take; rem -= take; } });
      for (let r = 0; r < rows; r++) svg('rect', { x: 60 + (r === rows - 1 ? (used - r * L) : L) * W, y: 10 + r * rh, width: Math.max(0, (r === rows - 1 ? L - (used - r * L) : 0) * W), height: rh - 3, style: 'fill:var(--panel-2)' }, s);
      comp = rows * L;
    }
    document.getElementById('dOut').innerHTML = `${real.toLocaleString()} real tokens, ${comp.toLocaleString()} computed: <b>${(100 * (1 - real / comp)).toFixed(0)}% padding</b>${mode === 'pack' ? ' (only the tail of the last row). Colours = different documents; they need a document mask.' : '.'}`;
  };
  Deck.bind(['dB'], draw); Deck.seg('dSeg', v => { mode = v; draw(); });
})();
