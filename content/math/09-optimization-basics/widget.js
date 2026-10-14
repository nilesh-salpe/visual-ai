(() => {
  const { svg, clear, fmt } = Deck;
  Deck.bind(['oL', 'oM', 'oK'], () => {
    const lr = Deck.val('oL'), b = Deck.val('oM'), k = Deck.val('oK'); Deck.out('oLo', lr.toFixed(3)); Deck.out('oMo', b.toFixed(2)); Deck.out('oKo', k);
    const s = clear(document.getElementById('oSvg')), X = x => 330 + x * 270, Y = y => 130 - y * 110;
    for (let c = 1; c <= 6; c++) { const r = c * 0.18; let pts = ''; for (let t = 0; t <= 6.3; t += 0.05) pts += `${X(r * Math.cos(t))},${Y(r * Math.sin(t) / Math.sqrt(k))} `; svg('polyline', { points: pts, fill: 'none', class: 'ln' }, s); }
    let x = -1, y = 1, vx = 0, vy = 0, pts = `${X(x)},${Y(y)} `, n = 0, f0 = 0.5 * (x * x + k * y * y), steps = null;
    for (n = 1; n <= 400; n++) { vx = b * vx + x; vy = b * vy + k * y; x -= lr * vx; y -= lr * vy; if (Math.abs(y) > 50 || Math.abs(x) > 50) break; if (n <= 150) pts += `${X(Math.max(-1.2, Math.min(1.2, x)))},${Y(Math.max(-1.15, Math.min(1.15, y)))} `; if (steps === null && 0.5 * (x * x + k * y * y) < 1e-4 * f0) steps = n; }
    svg('polyline', { points: pts, fill: 'none', style: 'stroke:var(--b);stroke-width:2' }, s);
    svg('circle', { cx: X(-1), cy: Y(1), r: 6, style: 'fill:var(--a)' }, s); svg('circle', { cx: X(0), cy: Y(0), r: 4, style: 'fill:var(--e)' }, s);
    const lim = 2 * (1 + b) / k, div = Math.abs(y) > 50 || Math.abs(x) > 50;
    document.getElementById('oOut').innerHTML = div ? `<b>Diverged</b>: η = ${lr.toFixed(3)} exceeds the stability limit ≈ ${lim.toFixed(3)} for κ = ${k}${b ? ' with this momentum' : ' (2/κ)'}.` : steps ? `Loss reduced 10⁴× in <b>${steps} steps</b> (first 150 drawn). Stability limit ≈ ${lim.toFixed(3)}.` : `Not converged in 400 steps: progress along the flat x direction is slow. Try momentum.`;
  });
})();
