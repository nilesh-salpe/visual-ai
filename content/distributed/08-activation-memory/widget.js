(() => {
  const { svg, clear, fmt } = Deck;
  const SS = [1024, 2048, 8192, 32768, 131072, 524288];
  Deck.bind(['mS'], () => {
    const s = SS[Deck.val('mS')], h = 12288, a = 96; Deck.out('mSo', s.toLocaleString());
    const act = s * h * (34 + 5 * a * s / h), w = 12 * h * h * 2;
    Deck.hbars(document.getElementById('mBars'), [{ label: 'layer weights (BF16)', value: w, color: 'var(--faint)', text: (w / 2 ** 30).toFixed(1) + ' GiB' }, { label: 'layer activations', value: act, color: 'var(--d)', text: (act / 2 ** 30).toFixed(1) + ' GiB' }, { label: 'activations, selective recompute', value: 34 * s * h, color: 'var(--e)', text: (34 * s * h / 2 ** 30).toFixed(1) + ' GiB' }], { log: true, min: 1e8 });
  });
  Deck.bind(['kL', 'kK'], () => {
    const L = Deck.val('kL'); const kk = document.getElementById('kK'); if (+kk.value > L) kk.value = L; const k = +kk.value; Deck.out('kLo', L); Deck.out('kKo', k);
    const s = clear(document.getElementById('kSvg')), X = v => 60 + (v - 1) / (L - 1 || 1) * 570, mx = L + 1, Y = v => 190 - v / mx * 170;
    let pts = ''; for (let v = 1; v <= L; v++) pts += `${X(v)},${Y(L / v + v)} `;
    svg('polyline', { points: pts, fill: 'none', style: 'stroke:var(--a);stroke-width:3' }, s);
    svg('circle', { cx: X(k), cy: Y(L / k + k), r: 7, style: 'fill:var(--b)' }, s);
    const best = Math.round(Math.sqrt(L)); svg('line', { x1: X(best), x2: X(best), y1: 20, y2: 190, style: 'stroke:var(--e);stroke-dasharray:4 3' }, s);
    svg('text', { x: X(best) + 4, y: 30, class: 'tm', text: 'k = √L' }, s); svg('text', { x: 340, y: 212, 'text-anchor': 'middle', class: 'tm', text: 'checkpoint spacing k' }, s);
    document.getElementById('kOut').innerHTML = `Stored activations: L/k + k = <b>${Math.ceil(L / k) + k}</b> of ${L} (${(100 * (Math.ceil(L / k) + k) / L).toFixed(0)}%); recompute: ${k > 1 ? 'about one extra forward pass' : 'none (k = 1 stores everything)'}.`;
  });
})();
