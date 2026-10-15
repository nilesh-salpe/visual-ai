(() => {
  const { svg, clear, fmt } = Deck;
  const f32 = new Float32Array(1), u32 = new Uint32Array(f32.buffer);
  const bf16 = x => { f32[0] = x; const u = u32[0], r = ((u + 0x7FFF + ((u >>> 16) & 1)) >>> 16) << 16; u32[0] = r >>> 0; return f32[0]; };
  Deck.bind(['bX', 'bN'], () => {
    const x = Math.pow(10, Deck.val('bX')), n = Math.round(Math.pow(10, Deck.val('bN'))); Deck.out('bXo', Deck.val('bX')); Deck.out('bNo', n.toLocaleString());
    let b = 0, s = 0; const xb = bf16(x); f32[0] = x; const xs = f32[0];
    for (let i = 0; i < n; i++) { b = bf16(b + xb); f32[0] = s + xs; s = f32[0]; }
    Deck.hbars(document.getElementById('bBars'), [{ label: 'exact n × x', value: n * x, color: 'var(--faint)', text: (n * x).toPrecision(5) }, { label: 'FP32 running total', value: s, color: 'var(--a)', text: s.toPrecision(5) },
      { label: 'BF16 running total', value: b, color: b < 0.9 * n * x ? 'var(--d)' : 'var(--e)', text: b.toPrecision(5) }], { max: n * x * 1.05 });
    document.getElementById('bOut').innerHTML = b < 0.9 * n * x ? `The BF16 total stalls at <b>${b}</b>: there, adjacent BF16 values are 2⁻⁷ × 2^⌊log₂ ${b.toPrecision(3)}⌋ ≈ ${(Math.pow(2, Math.floor(Math.log2(b)) - 7)).toExponential(2)} apart, more than twice the increment, so each addition rounds back.` : 'The total stays accurate at this size.';
  });
})();
