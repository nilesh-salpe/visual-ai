(() => {
  const { svg, clear, fmt } = Deck;

  const draw = () => {
    const n = Deck.val('bpeN'); Deck.out('bpeNo', n);
    const corpus = TK.parseCorpus(document.getElementById('bpeCorpus').value);
    const steps = TK.bpeTrain(corpus, 15), cur = steps.slice(0, n), merges = cur.map(s => [s.a, s.b]);
    const vocab = n ? cur[n - 1].vocab : corpus.map(([w, c]) => [[...w, TK.EOW], c]);
    document.getElementById('bpeVocab').innerHTML = vocab.map(([sy, c]) => { const el = document.createElement('div'); TK.render(el, sy.map(s => ({ text: s }))); return `<div class="tokrow"><div class="lab">×${c}</div>${el.outerHTML}<div class="cnt">${sy.length}</div></div>`; }).join('');
    document.getElementById('bpeMerges').innerHTML = steps.map((s, i) => `<div class="${i === n - 1 ? 'on' : ''}" style="opacity:${i < n ? 1 : .35}">${i + 1}. ${TK.esc(s.a)} + ${TK.esc(s.b)} → ${TK.esc(s.a + s.b)} <span style="color:var(--faint)">(${s.count})</span></div>`).join('') || '<i>no pairs left</i>';
    const next = steps[n] ? [...steps[n].counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 6) : [];
    Deck.hbars(document.getElementById('bpePairs'), next.length ? next.map(([k, v], i) => ({ label: TK.esc(k.replace('\u0000', ' + ')), value: v, color: i === 0 ? 'var(--a)' : 'var(--line)', text: v })) : [{ label: '(done)', value: 0, text: '' }]);
    const w = document.getElementById('bpeWord').value.trim() || 'lowest';
    TK.render(document.getElementById('bpeEnc'), TK.bpeEncode(w, merges).map(s => ({ text: s })));
  };
  ['bpeCorpus', 'bpeWord'].forEach(id => document.getElementById(id).addEventListener('input', draw));
  Deck.bind(['bpeN'], draw);
  // Figure 1
  const F1 = [['r', '·'], ['l', 'o'], ['lo', 'w'], ['e', 'r·']];
  let k = 0;
  const f1 = () => {
    const sy = TK.bpeEncode('lower', F1.slice(0, k));
    TK.render(document.getElementById('f1Toks'), sy.map(s => ({ text: s })));
    document.getElementById('f1List').innerHTML = F1.map((m, i) => `<div class="${i === k - 1 ? 'on' : ''}" style="opacity:${i < k ? 1 : .4}">${i + 1}. ${m[0]} + ${m[1]} → ${m[0] + m[1]}</div>`).join('');
    Deck.out('f1Out', k === F1.length ? 'Done: "lower" → low er·' : `${k} of ${F1.length} merges applied`);
  };
  document.getElementById('f1Step').onclick = () => { if (k < F1.length) k++; f1(); };
  document.getElementById('f1Reset').onclick = () => { k = 0; f1(); };
  f1();

})();
