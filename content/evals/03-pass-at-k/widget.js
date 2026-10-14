(() => {
  const { svg, clear, fmt } = Deck;

  Deck.bind(['pP'], () => {
    const p = Deck.val('pP'); Deck.out('pPo', p.toFixed(2));
    const s = clear(document.getElementById('pSvg')), X = k => 60 + Math.log10(k) / 2 * 560, Y = v => 200 - v * 180;
    [0, 0.5, 1].forEach(v => { svg('line', { x1: 60, x2: 620, y1: Y(v), y2: Y(v), class: 'ln' }, s); svg('text', { x: 52, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm', text: v }, s); });
    [1, 10, 100].forEach(k => svg('text', { x: X(k), y: 218, 'text-anchor': 'middle', class: 'tm', text: 'k=' + k }, s));
    let pts = ''; for (let e = 0; e <= 2.001; e += 0.02) { const k = Math.pow(10, e); pts += `${X(k)},${Y(1 - Math.pow(1 - p, k))} `; }
    svg('polyline', { points: pts, fill: 'none', style: 'stroke:var(--a);stroke-width:3' }, s);
    document.getElementById('pOut').innerHTML = `pass@1 = <b>${p.toFixed(2)}</b>, pass@10 = <b>${(1 - Math.pow(1 - p, 10)).toFixed(2)}</b>, pass@100 = <b>${(1 - Math.pow(1 - p, 100)).toFixed(2)}</b>.`;
  });
  const passk = (n, c, k) => { if (n - c < k) return 1; let pr = 1; for (let i = n - c + 1; i <= n; i++) pr *= 1 - k / i; return 1 - pr; };
  Deck.bind(['cN', 'cC', 'cK'], () => {
    const N = document.getElementById('cN'), Cc = document.getElementById('cC'), K = document.getElementById('cK');
    const n = +N.value; if (+Cc.value > n) Cc.value = n; if (+K.value > n) K.value = n;
    const c = +Cc.value, k = +K.value; Deck.out('cNo', n); Deck.out('cCo', c); Deck.out('cKo', k);
    const u = passk(n, c, k), b = 1 - Math.pow(1 - c / n, k);
    Deck.out('cU', u.toFixed(3)); Deck.out('cB', b.toFixed(3)); Deck.out('c1', (c / n).toFixed(3));
    document.getElementById('cOut').innerHTML = n - c < k ? `n − c = ${n - c} &lt; k = ${k}: every subset of ${k} contains a passing sample, so pass@${k} = 1.` : `pass@${k} = 1 − C(${n - c}, ${k}) / C(${n}, ${k}). The plug-in differs by ${(b - u >= 0 ? '+' : '') + (b - u).toFixed(3)}.`;
  });

})();
