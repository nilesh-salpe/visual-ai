(() => {
  const { svg, clear, fmt } = Deck;

  let pair = 0;
  const draw = () => {
    const m = Deck.val('rM'), n = Deck.val('rN'); Deck.out('rMo', m); Deck.out('rNo', n);
    const th = Math.pow(10000, -2 * pair / 16), q0 = Math.atan2(0.6, 1), k0 = Math.atan2(-0.3, 1);
    const qa = q0 + m * th, ka = k0 + n * th, qr = 1.166, kr = 1.044;
    const s = clear(document.getElementById('rSvg'));
    const dial = (cx, ang0, ang, r, color, label, pos) => {
      svg('circle', { cx, cy: 110, r: 80, style: 'fill:none;stroke:var(--line)' }, s);
      svg('line', { x1: cx - 85, x2: cx + 85, y1: 110, y2: 110, class: 'ln' }, s); svg('line', { x1: cx, x2: cx, y1: 25, y2: 195, class: 'ln' }, s);
      svg('line', { x1: cx, y1: 110, x2: cx + 70 * r * Math.cos(ang0), y2: 110 - 70 * r * Math.sin(ang0), style: 'stroke:var(--faint);stroke-width:2;stroke-dasharray:4 3' }, s);
      svg('line', { x1: cx, y1: 110, x2: cx + 70 * r * Math.cos(ang), y2: 110 - 70 * r * Math.sin(ang), style: `stroke:${color};stroke-width:4` }, s);
      svg('circle', { cx: cx + 70 * r * Math.cos(ang), cy: 110 - 70 * r * Math.sin(ang), r: 6, style: `fill:${color}` }, s);
      svg('text', { x: cx, y: 222, 'text-anchor': 'middle', class: 't', text: `${label} at position ${pos}: rotated ${(pos * th).toFixed(2)} rad` }, s);
    };
    dial(150, q0, qa, qr, 'var(--a)', 'q', m); dial(510, k0, ka, kr, 'var(--b)', 'k', n);
    const score = qr * kr * Math.cos(qa - ka);
    svg('text', { x: 330, y: 100, 'text-anchor': 'middle', class: 't', style: 'font-weight:700;font-size:15px', text: `q·k = ${score.toFixed(3)}` }, s);
    svg('text', { x: 330, y: 122, 'text-anchor': 'middle', class: 'tm', text: `m − n = ${m - n}` }, s);
    document.getElementById('rOut').innerHTML = `Pair ${pair}: θ = ${th.toPrecision(3)} rad/token. Angle between q and k = (q₀ − k₀) + (m − n)·θ = <b>${(qa - ka).toFixed(3)} rad</b>. Try "shift both": m and n move, the score doesn't.`;
  };
  Deck.bind(['rM', 'rN'], draw);
  Deck.seg('rPair', v => { pair = +v; draw(); });
  document.getElementById('rShift').addEventListener('click', () => {
    const M = document.getElementById('rM'), N = document.getElementById('rN');
    if (+M.value + 10 > 60 || +N.value + 10 > 60) { M.value = Math.max(0, +M.value - 40); N.value = Math.max(0, +N.value - 40); } else { M.value = +M.value + 10; N.value = +N.value + 10; }
    draw();
  });
  Deck.seg('bSeg', v => {
    const base = +v, d = 128, th = [...Array(64)].map((_, i) => Math.pow(base, -2 * i / d));
    const score = dist => th.reduce((a, t) => a + Math.cos(dist * t), 0) / 64;
    const s = clear(document.getElementById('dSvg')), L0 = 60, R0 = 630, T0 = 14, B0 = 190, X = x => L0 + Math.log10(x) / 5 * (R0 - L0), Y = y => B0 - (y + 0.2) / 1.2 * (B0 - T0);
    [-0.2, 0, 0.5, 1].forEach(v => { svg('line', { x1: L0, x2: R0, y1: Y(v), y2: Y(v), class: 'ln' }, s); svg('text', { x: L0 - 8, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm', text: v }, s); });
    [1, 10, 100, 1000, 10000, 100000].forEach(v => svg('text', { x: X(v), y: B0 + 18, 'text-anchor': 'middle', class: 'tm', text: v >= 1000 ? (v / 1000) + 'K' : v }, s));
    let pts = ''; for (let e = 0; e <= 5; e += 0.01) { const x = Math.pow(10, e); pts += `${X(x)},${Y(score(x))} `; }
    svg('polyline', { points: pts, fill: 'none', style: 'stroke:var(--a);stroke-width:2.5' }, s);
    svg('text', { x: (L0 + R0) / 2, y: B0 + 40, 'text-anchor': 'middle', class: 'tm', text: 'distance m − n (log scale)' }, s);
    svg('text', { x: 14, y: (T0 + B0) / 2, 'text-anchor': 'middle', class: 'tm', transform: `rotate(-90 14 ${(T0 + B0) / 2})`, text: 'score (q = k = 1s)' }, s);
    const at = [100, 1000, 10000].map(x => score(x).toFixed(2));
    document.getElementById('dOut').innerHTML = `Normalized score at distance 100 / 1K / 10K: <b>${at.join(' / ')}</b>. A larger base keeps the score higher for longer, because every pair (except pair 0) turns more slowly.`;
  });

})();
