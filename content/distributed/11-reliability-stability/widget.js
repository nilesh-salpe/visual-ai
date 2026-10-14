(() => {
  const { svg, clear, fmt } = Deck;
  Deck.bind(['yC', 'yM'], () => {
    const C = Deck.val('yC') / 3600, M = Deck.val('yM'), R = 10 / 60; Deck.out('yCo', Deck.val('yC') + ' s'); Deck.out('yMo', M.toFixed(1));
    const good = t => 1 / (1 + C / t + t / (2 * M) + R / M) ;
    const s = clear(document.getElementById('ySvg')), X = t => 60 + Math.log10(t / 0.01) / Math.log10(2400) * 570, Y = g => 200 - g * 180;
    [0, 0.5, 1].forEach(v => { svg('line', { x1: 60, x2: 630, y1: Y(v), y2: Y(v), class: 'ln' }, s); svg('text', { x: 52, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm', text: (100 * v) + '%' }, s); });
    [[1 / 60, '1 min'], [10 / 60, '10 min'], [1, '1 h'], [10, '10 h']].forEach(([t, l]) => svg('text', { x: X(t), y: 218, 'text-anchor': 'middle', class: 'tm', text: l }, s));
    let pts = ''; for (let e = 0; e <= 1; e += 0.005) { const t = 0.01 * Math.pow(2400, e); pts += `${X(t)},${Y(good(t))} `; }
    svg('polyline', { points: pts, fill: 'none', style: 'stroke:var(--a);stroke-width:3' }, s);
    const ty = Math.sqrt(2 * C * M); svg('circle', { cx: X(ty), cy: Y(good(ty)), r: 7, style: 'fill:var(--b)' }, s);
    document.getElementById('yOut').innerHTML = `Young's interval √(2·C·MTBF) = <b>${(ty * 60).toFixed(1)} min</b> → goodput ≈ <b>${(100 * good(ty)).toFixed(1)}%</b> in this model.`;
  });
  const NS = [8, 64, 512, 2048, 8192, 16384];
  Deck.bind(['sN', 'sS'], () => {
    const n = NS[Deck.val('sN')], slow = Deck.val('sS') / 100; Deck.out('sNo', n.toLocaleString()); Deck.out('sSo', (100 * slow).toFixed(0) + '%');
    const z = Math.sqrt(2 * Math.log(n)) - (Math.log(Math.log(n)) + Math.log(4 * Math.PI)) / (2 * Math.sqrt(2 * Math.log(n)));
    const healthy = 1 + 0.02 * z, step = Math.max(healthy, 1 + slow);
    Deck.hbars(document.getElementById('sBars'), [{ label: 'ideal (no variation)', value: 1, color: 'var(--faint)', text: '1.00' }, { label: `max of ${n.toLocaleString()} healthy GPUs`, value: healthy, color: 'var(--a)', text: healthy.toFixed(3) }, { label: 'with the degraded GPU', value: step, color: step > healthy ? 'var(--d)' : 'var(--a)', text: step.toFixed(3) }], { max: 1.6, min: 0.5 });
  });
})();
