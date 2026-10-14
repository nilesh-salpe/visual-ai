(() => {
  const { svg, clear, fmt } = Deck;
  let cur = 'bf16';
  const F = { fp32: [8, 23, 127], bf16: [8, 7, 127], fp16: [5, 10, 15] };
  const encode = (v, [E, M, B]) => {
    if (!isFinite(v) || isNaN(v)) return null;
    const s = v < 0 || Object.is(v, -0) ? 1 : 0; let a = Math.abs(v);
    if (a === 0) return { s, e: 0, m: 0, val: 0 };
    let e = Math.floor(Math.log2(a)); if (Math.pow(2, e) > a) e--; if (Math.pow(2, e + 1) <= a) e++;
    let be = e + B, m;
    if (be <= 0) { m = Math.round(a / Math.pow(2, 1 - B) * Math.pow(2, M)); be = 0; if (m >= Math.pow(2, M)) { be = 1; m -= Math.pow(2, M); } }
    else { m = Math.round((a / Math.pow(2, e) - 1) * Math.pow(2, M)); if (m >= Math.pow(2, M)) { m = 0; be++; } }
    if (be >= Math.pow(2, E) - 1) return { s, e: Math.pow(2, E) - 1, m: 0, val: s ? -Infinity : Infinity };
    const val = (s ? -1 : 1) * (be === 0 ? m / Math.pow(2, M) * Math.pow(2, 1 - B) : (1 + m / Math.pow(2, M)) * Math.pow(2, be - B));
    return { s, e: be, m, val };
  };
  const draw = () => {
    const v = parseFloat(document.getElementById('fV').value), [E, M, B] = F[cur], r = encode(v, F[cur]), s = clear(document.getElementById('fSvg'));
    if (!r) { document.getElementById('fOut').innerHTML = 'Enter a number.'; return; }
    const bits = [r.s].concat([...Array(E)].map((_, i) => (r.e >> (E - 1 - i)) & 1)).concat([...Array(M)].map((_, i) => Math.floor(r.m / Math.pow(2, M - 1 - i)) & 1));
    const n = bits.length, w = Math.min(28, 600 / n);
    bits.forEach((b, i) => { const col = i === 0 ? 'var(--d)' : i <= E ? 'var(--a)' : 'var(--c)';
      svg('rect', { x: 30 + i * w, y: 20, width: w - 2, height: 34, rx: 3, style: `fill:${col};opacity:${b ? 1 : .35}` }, s);
      if (w > 12) svg('text', { x: 30 + i * w + (w - 2) / 2, y: 42, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:12px', text: b }, s); });
    svg('text', { x: 30, y: 78, class: 'tm', text: 'sign' }, s); svg('text', { x: 30 + w, y: 78, class: 'tm', style: 'fill:var(--a)', text: `exponent (${E} bits, bias ${B})` }, s); svg('text', { x: 30 + (E + 1) * w, y: 98, class: 'tm', style: 'fill:var(--c)', text: `mantissa (${M} bits)` }, s);
    const err = r.val - v, rel = v ? Math.abs(err / v) : 0;
    document.getElementById('fOut').innerHTML = !isFinite(r.val) ? `<b>Overflow</b>: ${v} is above the ${cur.toUpperCase()} maximum, stored as ∞.` : r.val === 0 && v !== 0 ? `<b>Underflow</b>: ${v} rounds to 0 in ${cur.toUpperCase()}.` : `Stored value: <b>${r.val.toPrecision(12).replace(/0+$/, '').replace(/\.$/, '')}</b> · error ${err.toExponential(2)} (relative ${rel.toExponential(2)}; format precision ≈ 2<sup>−${M + 1}</sup> = ${Math.pow(2, -(M + 1)).toExponential(1)})${r.e === 0 ? ' · subnormal' : ''}.`;
  };
  document.getElementById('fV').addEventListener('input', draw); Deck.seg('fSeg', v => { cur = v; draw(); });
})();
