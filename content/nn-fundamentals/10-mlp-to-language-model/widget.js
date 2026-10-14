(() => {
  const { svg, clear, fmt } = Deck;
  const TEXT = ("the cat sat on the mat. the dog sat on the log. a cat and a dog met on a mat. the cat saw the dog and the dog saw the cat. on the log sat a frog. the frog sat still. ").repeat(6);
  const CH = [...new Set(TEXT)].sort(), idx = Object.fromEntries(CH.map((c, i) => [c, i])), V = CH.length;
  const C = [...Array(V)].map(() => new Array(V).fill(0.1)); for (let i = 0; i + 1 < TEXT.length; i++) C[idx[TEXT[i]]][idx[TEXT[i + 1]]]++;
  const dist = (c, t) => { const row = C[idx[c] ?? idx[' ']], lg = row.map(v => Math.log(v) / t), m = Math.max(...lg), e = lg.map(v => Math.exp(v - m)), S = e.reduce((a, b) => a + b); return e.map(v => v / S); };
  let seed = 11; const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  const draw = () => {
    const c = (document.getElementById('lC').value || ' ').toLowerCase(), t = Deck.val('lT'); Deck.out('lTo', t.toFixed(1));
    const p = dist(c, t), top = p.map((v, i) => [v, i]).sort((a, b) => b[0] - a[0]).slice(0, 6);
    Deck.hbars(document.getElementById('lBars'), top.map(([v, i]) => ({ label: `"${CH[i] === ' ' ? '␣' : CH[i]}"`, value: v, color: 'var(--a)', text: (100 * v).toFixed(1) + '%' })), { max: 1 });
    document.getElementById('lOut').innerHTML = c in idx ? `Most likely characters after "${c === ' ' ? '␣' : c}". Press "sample" to generate text one character at a time.` : `"${c}" never appears in the text; showing the distribution after a space.`;
  };
  document.getElementById('lC').addEventListener('input', draw); Deck.bind(['lT'], draw);
  document.getElementById('lS').addEventListener('click', () => { const t = Deck.val('lT'); let c = (document.getElementById('lC').value || 't').toLowerCase(), out = c;
    for (let k = 0; k < 80; k++) { const p = dist(c, t); let r = rnd(), j = 0; while (j < V - 1 && (r -= p[j]) > 0) j++; c = CH[j]; out += c; }
    document.getElementById('lOut').innerHTML = `<code>${out.replace(/</g, '&lt;')}</code><br>Only one character of context: locally plausible, globally aimless. Notebook 07's 3-character neural model does much better.`; });
})();
