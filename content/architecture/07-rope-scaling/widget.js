(() => {
  const { svg, clear, fmt } = Deck;

  const d = 128, base = 1e4, Lc = 4096, TH = [...Array(64)].map((_, i) => Math.pow(base, -2 * i / d));
  let es = 8;
  const arc = () => {
    const i = Deck.val('eI'); Deck.out('eIo', i);
    const th = TH[i], lam = 2 * Math.PI / th, seen = Lc * th, ext = es * Lc * th;
    const s = clear(document.getElementById('eSvg')), cx = 160, cy = 115, r = 85;
    svg('circle', { cx, cy, r, style: 'fill:none;stroke:var(--line);stroke-width:10' }, s);
    const path = (a0, a1, color) => {
      const sweep = Math.min(a1, 2 * Math.PI - 1e-4) - a0; if (sweep <= 0) return;
      const p = a => [cx + r * Math.cos(a), cy - r * Math.sin(a)];
      const [x0, y0] = p(a0), [x1, y1] = p(a0 + sweep);
      svg('path', { d: `M${x0} ${y0} A${r} ${r} 0 ${sweep > Math.PI ? 1 : 0} 0 ${x1} ${y1}`, fill: 'none', style: `stroke:${color};stroke-width:10` }, s);
    };
    if (seen >= 2 * Math.PI) path(0, 2 * Math.PI, 'var(--e)'); else { path(seen, ext, 'var(--d)'); path(0, seen, 'var(--e)'); }
    const turns = seen / (2 * Math.PI);
    svg('text', { x: cx, y: cy + 5, 'text-anchor': 'middle', class: 't', style: 'font-weight:700', text: `pair ${i}` }, s);
    const lines = [`θ = ${th.toPrecision(3)} rad/token`, `wavelength = ${Math.round(lam).toLocaleString()} tokens`, `turns during training (L = 4,096): ${turns >= 10 ? turns.toFixed(0) : turns.toFixed(2)}`, `turns needed at ${es}× (${(es * Lc).toLocaleString()} tokens): ${(turns * es) >= 10 ? (turns * es).toFixed(0) : (turns * es).toFixed(2)}`];
    lines.forEach((t, k) => svg('text', { x: 300, y: 60 + k * 30, class: k > 1 ? 't' : 'tm', text: t }, s));
    document.getElementById('eOut').innerHTML = turns >= 1
      ? 'This pair completed at least one full turn in training: every angle is already familiar, so going longer adds nothing new.'
      : `This pair covered only <b>${(100 * turns).toFixed(0)}%</b> of the circle in training. At ${es}× length it would reach angles it has <b>never seen</b> (red). These slow pairs are the ones that need interpolation.`;
  };
  Deck.bind(['eI'], arc); Deck.seg('eS', v => { es = +v; arc(); });
  Deck.seg('sS', v => {
    const sc = +v, ntkB = base * Math.pow(sc, d / (d - 2));
    const pi = TH.map(t => sc), ntk = TH.map((t, i) => t / Math.pow(ntkB, -2 * i / d));
    const yarn = TH.map(t => { const r = Lc * t / (2 * Math.PI), g = Math.min(1, Math.max(0, (r - 1) / 31)); return t / ((1 - g) * t / sc + g * t); });
    const s = clear(document.getElementById('sSvg')), L0 = 60, R0 = 630, T0 = 14, B0 = 210, X = i => L0 + i / 63 * (R0 - L0), Y = f => B0 - Math.log(f) / Math.log(32) * (B0 - T0);
    const firstSlow = TH.findIndex(t => 2 * Math.PI / t > Lc);
    svg('rect', { x: X(firstSlow), y: T0, width: R0 - X(firstSlow), height: B0 - T0, style: 'fill:var(--d-soft)' }, s);
    svg('text', { x: (X(firstSlow) + R0) / 2, y: T0 + 16, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: 'wavelength > L' }, s);
    [1, 2, 4, 8, 16, 32].forEach(f => { svg('line', { x1: L0, x2: R0, y1: Y(f), y2: Y(f), class: 'ln' }, s); svg('text', { x: L0 - 8, y: Y(f) + 4, 'text-anchor': 'end', class: 'tm', text: f + '×' }, s); });
    [0, 16, 32, 48, 63].forEach(i => svg('text', { x: X(i), y: B0 + 18, 'text-anchor': 'middle', class: 'tm', text: i }, s));
    const line = (vals, c) => svg('polyline', { points: vals.map((f, i) => `${X(i)},${Y(f)}`).join(' '), fill: 'none', style: `stroke:${c};stroke-width:2.5` }, s);
    line(TH.map(() => 1), 'var(--faint)'); line(pi, 'var(--d)'); line(ntk, 'var(--b)'); line(yarn, 'var(--a)');
    svg('text', { x: (L0 + R0) / 2, y: B0 + 40, 'text-anchor': 'middle', class: 'tm', text: 'pair index i (fast → slow)' }, s);
    const over = arr => TH.filter((t, i) => 2 * Math.PI / t > Lc && (sc * Lc - 1) * (t / arr[i]) > Lc * t).length;
    document.getElementById('sOut').innerHTML = `Slow pairs (shaded, ${64 - firstSlow} of 64) still pushed past their trained angle range at ${sc}× length: no scaling <b>${over(TH.map(() => 1))}</b>, PI <b>${over(pi)}</b>, NTK-aware <b>${over(ntk)}</b>, YaRN <b>${over(yarn)}</b>. PI also slows the fastest pair ${sc}×; NTK and YaRN leave it at 1×.`;
  });

})();
