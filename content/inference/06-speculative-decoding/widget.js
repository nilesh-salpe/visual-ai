(() => {
  const { svg, clear, fmt } = Deck;

  const EX = {
    a: [['the', .40, .50, .31], ['cat', .30, .25, .74], ['sat', .55, .60, .52], ['on', .45, .40, .12]],
    b: [['the', .40, .50, .31], ['dog', .05, .30, .44], ['ran', .20, .30, .10], ['to', .30, .30, .20]],
  };
  Deck.seg('exSeg', v => {
    const rows = EX[v]; let out = [], stop = false;
    const html = rows.map(([tok, p, q, u], i) => {
      if (stop) return `<tr style="opacity:.35"><td>${i + 1}</td><td><code>${tok}</code></td><td>${p}</td><td>${q}</td><td>–</td><td>–</td><td>not checked</td></tr>`;
      const a = Math.min(1, p / q), ok = u < a;
      if (ok) out.push(tok); else { out.push('⟨resample⟩'); stop = true; }
      return `<tr><td>${i + 1}</td><td><code>${tok}</code></td><td>${p}</td><td>${q}</td><td>${a.toFixed(2)}</td><td>${u}</td><td style="color:${ok ? 'var(--e)' : 'var(--d)'};font-weight:700">${ok ? 'accept' : 'reject → sample from norm(max(0, p−q))'}</td></tr>`;
    }).join('');
    if (!stop) out.push('⟨bonus from p⟩');
    document.getElementById('exTbl').innerHTML = '<tr><th>#</th><th>draft x</th><th>p(x)</th><th>q(x)</th><th>min(1, p/q)</th><th>u</th><th>decision</th></tr>' + html;
    document.getElementById('exOut').innerHTML = `This target pass yields <b>${out.length}</b> token${out.length > 1 ? 's' : ''}: ${out.map(t => `<code>${t}</code>`).join(' ')}`;
  });
  const E = (a, g) => (1 - Math.pow(a, g + 1)) / (1 - a), S = (a, g, c) => E(a, g) / (g * c + 1);
  Deck.bind(['sA', 'sG', 'sC'], () => {
    const a = Deck.val('sA'), g = Deck.val('sG'), c = Deck.val('sC');
    Deck.out('sAo', a.toFixed(2)); Deck.out('sGo', g); Deck.out('sCo', c.toFixed(2));
    let best = 1; for (let k = 1; k <= 20; k++) if (S(a, k, c) > S(a, best, c)) best = k;
    Deck.out('sE', E(a, g).toFixed(2)); Deck.out('sS', S(a, g, c).toFixed(2) + '×'); Deck.out('sO', best + ` (${S(a, best, c).toFixed(2)}×)`);
    const s = clear(document.getElementById('sSvg')), L = 50, R = 640, T = 10, B = 190, ymax = Math.max(1 / (1 - a), 2) * 1.05;
    const X = k => L + (k - 1) / 19 * (R - L), Y = v => B - v / ymax * (B - T);
    [1, 5, 10, 15, 20].forEach(k => { svg('line', { x1: X(k), x2: X(k), y1: T, y2: B, class: 'ln' }, s); svg('text', { x: X(k), y: B + 16, 'text-anchor': 'middle', class: 'tm tc', text: k }, s); });
    svg('line', { x1: L, x2: R, y1: Y(1), y2: Y(1), style: 'stroke:var(--faint);stroke-dasharray:4 3' }, s);
    svg('text', { x: R, y: Y(1) - 4, 'text-anchor': 'end', class: 'tm', style: 'font-size:10px', text: 'no speedup' }, s);
    svg('line', { x1: L, x2: R, y1: Y(1 / (1 - a)), y2: Y(1 / (1 - a)), style: 'stroke:var(--d);stroke-dasharray:4 3' }, s);
    svg('text', { x: R, y: Y(1 / (1 - a)) - 4, 'text-anchor': 'end', class: 'tm', style: 'font-size:10px;fill:var(--d)', text: 'cap 1/(1−α)' }, s);
    let pe = '', ps = ''; for (let k = 1; k <= 20; k++) { pe += `${X(k)},${Y(E(a, k))} `; ps += `${X(k)},${Y(S(a, k, c))} `; }
    svg('polyline', { points: pe, fill: 'none', style: 'stroke:var(--a);stroke-width:2;opacity:.6' }, s);
    svg('polyline', { points: ps, fill: 'none', style: 'stroke:var(--e);stroke-width:3' }, s);
    svg('circle', { cx: X(g), cy: Y(S(a, g, c)), r: 7, style: 'fill:var(--e);stroke:var(--panel);stroke-width:2' }, s);
    svg('text', { x: (L + R) / 2, y: B + 34, 'text-anchor': 'middle', class: 'tm', text: 'γ: teal = tokens per target pass, green = wall-clock speedup' }, s);
  });

})();
