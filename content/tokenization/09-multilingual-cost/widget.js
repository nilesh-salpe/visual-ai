(() => {
  const { svg, clear, fmt } = Deck;

  const L = TOK.ml, en = e => TK.get('ml_English', e).length;
  const bars = (el, enc) => Deck.hbars(el, L.map(l => { const n = TK.get('ml_' + l, enc).length; return { label: `${l} <span style="color:var(--faint)">${TK.esc(TK.text('ml_' + l))}</span>`, value: n, color: l === 'English' ? 'var(--faint)' : n / en(enc) > 2 ? 'var(--d)' : n / en(enc) > 1.3 ? 'var(--b)' : 'var(--e)', text: `${n} tok · ${(n / en(enc)).toFixed(1)}×` }; }), { max: 28 });
  bars(document.getElementById('p1Bars'), 'gpt2');
  Deck.seg('mlEnc', enc => {
    bars(document.getElementById('mlBars'), enc);
    const pr = L.map(l => TK.get('ml_' + l, enc).length / en(enc)), mx = Math.max(...pr), worst = L[pr.indexOf(mx)];
    document.getElementById('mlOut').innerHTML = `${enc}: highest premium is <b>${worst} at ${mx.toFixed(1)}×</b> English.`;
  });
  let cxe = 'cl100k_base';
  const cx = () => { const w = +Deck.val('cxW'); Deck.hbars(document.getElementById('cxBars'), L.map(l => { const n = TK.get('ml_' + l, cxe).length, k = Math.floor(w / n); return { label: l, value: k, color: l === 'English' ? 'var(--a)' : 'var(--c)', text: fmt(k, 0) + ' sentences' }; })); };
  Deck.seg('cxEnc', e => { cxe = e; if (document.getElementById('cxW')) cx(); });
  Deck.bind(['cxW'], cx);

})();
