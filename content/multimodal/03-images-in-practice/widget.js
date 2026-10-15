(() => {
  const { svg, clear, fmt } = Deck;
  const tokens = (w, h, L, T) => {
    const cost = (a, b) => Math.ceil(a / 28) * Math.ceil(b / 28);
    const fits = s => Math.max(Math.floor(w * s), Math.floor(h * s)) <= L && cost(Math.floor(w * s), Math.floor(h * s)) <= T;
    if (fits(1)) return [w, h, cost(w, h)];
    let lo = 0, hi = 1; for (let i = 0; i < 50; i++) { const m = (lo + hi) / 2; if (fits(m)) lo = m; else hi = m; }
    const nw = Math.floor(w * lo), nh = Math.floor(h * lo); return [nw, nh, cost(nw, nh)];
  };
  Deck.bind(['iW', 'iH', 'iN'], () => {
    const w = Deck.val('iW'), h = Deck.val('iH'), n = Deck.val('iN');
    Deck.out('iWo', w + ' px'); Deck.out('iHo', h + ' px'); Deck.out('iNo', n);
    const s = tokens(w, h, 1568, 1568), r = tokens(w, h, 2576, 4784);
    Deck.hbars(document.getElementById('iBars'), [{ label: 'standard tier, per image', value: s[2], color: 'var(--e)', text: s[2].toLocaleString() + ' tokens' },
      { label: 'high-resolution tier, per image', value: r[2], color: 'var(--a)', text: r[2].toLocaleString() + ' tokens' }], { max: 5000 });
    document.getElementById('iOut').innerHTML = `${w} × ${h}: standard tier sees ${s[0]} × ${s[1]} → <b>${s[2].toLocaleString()}</b> tokens; high-resolution tier sees ${r[0]} × ${r[1]} → <b>${r[2].toLocaleString()}</b> tokens. With ${n} image${n > 1 ? 's' : ''} kept in context: ${(n * s[2]).toLocaleString()} or ${(n * r[2]).toLocaleString()} tokens.`;
  });
})();
