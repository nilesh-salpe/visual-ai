(() => {
  const { svg, clear, fmt } = Deck;
  const F = [['FP32', -44.85, 38.53, 'var(--faint)'], ['BF16', -40.04, 38.53, 'var(--a)'], ['FP16', -7.22, 4.82, 'var(--b)'], ['FP8 E5M2', -4.82, 4.76, 'var(--c)'], ['FP8 E4M3', -2.7, 2.65, 'var(--e)']];
  Deck.bind(['gE', 'gS'], () => {
    const e = Deck.val('gE'), S = Deck.val('gS'); Deck.out('gEo', e); Deck.out('gSo', S);
    const v = e + S * Math.log10(2), s = clear(document.getElementById('gSvg')), X = x => 120 + (x + 46) / 86 * 520;
    F.forEach(([n, lo, hi, c], i) => { const y = 20 + i * 36; svg('text', { x: 110, y: y + 15, 'text-anchor': 'end', class: 't', text: n }, s); svg('rect', { x: X(lo), y, width: X(hi) - X(lo), height: 22, rx: 4, style: `fill:${c};opacity:.85` }, s);
      const ok = v >= lo && v <= hi; svg('circle', { cx: X(Math.max(-46, Math.min(40, v))), cy: y + 11, r: 7, style: `fill:${ok ? 'var(--ink)' : 'var(--d)'};stroke:var(--panel);stroke-width:2` }, s); });
    [-40, -20, 0, 20, 38].forEach(t => svg('text', { x: X(t), y: 205, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: '1e' + t }, s));
    const fp16 = v >= -7.22 && v <= 4.82;
    document.getElementById('gOut').innerHTML = `Scaled value ≈ 10^${v.toFixed(1)}. FP16: <b>${fp16 ? 'representable' : v < -7.22 ? 'underflows to 0' : 'overflows to ∞'}</b>; BF16: <b>${v >= -40.04 ? 'representable' : 'underflows'}</b>.`;
  });
})();
