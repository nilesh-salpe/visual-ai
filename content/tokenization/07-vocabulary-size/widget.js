(() => {
  const { svg, clear, fmt } = Deck;

  const cpt = (k, e) => TK.text(k).length / TK.get(k, e).length;
  const V = { gpt2: 50257, cl100k_base: 100277, o200k_base: 200019 };
  Deck.hbars(document.getElementById('enBars'), Object.keys(V).map(e => ({ label: `${e} (${(V[e] / 1000).toFixed(0)}K)`, value: cpt('para', e), color: 'var(--a)', text: cpt('para', e).toFixed(2) + ` (${TK.get('para', e).length} tok)` })), { max: 6 });
  Deck.hbars(document.getElementById('hiBars'), Object.keys(V).map(e => ({ label: `${e} (${(V[e] / 1000).toFixed(0)}K)`, value: cpt('ml_Hindi', e), color: 'var(--b)', text: cpt('ml_Hindi', e).toFixed(2) + ` (${TK.get('ml_Hindi', e).length} tok)` })), { max: 4 });
  document.getElementById('cmpOut').innerHTML = `From 50K to 200K: English improves ${(100 * (cpt('para', 'o200k_base') / cpt('para', 'gpt2') - 1)).toFixed(0)}%, while the Hindi sentence improves ${(cpt('ml_Hindi', 'o200k_base') / cpt('ml_Hindi', 'gpt2')).toFixed(1)}×.`;
  const pts = Object.keys(V).map(e => [Math.log2(V[e]), cpt('para', e)]);
  const interp = lv => { if (lv <= pts[0][0]) return pts[0][1] - (pts[0][0] - lv) * 0.12; for (let i = 1; i < pts.length; i++) if (lv <= pts[i][0]) { const [x0, y0] = pts[i - 1], [x1, y1] = pts[i]; return y0 + (y1 - y0) * (lv - x0) / (x1 - x0); } return pts[pts.length - 1][1]; };
  let tie = 2;
  const vc = () => {
    const lv = Deck.val('vV'), v = Math.round(Math.pow(2, lv)), d = +Deck.val('vD'), T = +Deck.val('vT');
    Deck.out('vVo', fmt(v, 0));
    const p = v * d * tie;
    Deck.out('vPar', fmt(p)); Deck.out('vPct', (100 * p / T).toFixed(1) + '%');
    document.getElementById('vPct').style.color = p / T > .2 ? 'var(--d)' : 'var(--ink)';
    Deck.out('vCtx', '≈ ' + fmt(8192 * interp(lv), 0));
  };
  Deck.seg('vTie', x => { tie = +x; if (document.getElementById('vV')) vc(); });
  Deck.bind(['vV', 'vD', 'vT'], vc);

})();
