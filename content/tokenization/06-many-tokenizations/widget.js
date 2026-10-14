(() => {
  const { svg, clear, fmt } = Deck;

  const H = [['▁Hell/o/▁world', '13586 137 255'], ['▁H/ello/▁world', '320 7363 255'], ['▁He/llo/▁world', '579 10115 255'], ['▁/He/l/l/o/▁world', '7 18085 356 356 137 255'], ['▁H/el/l/o/▁/world', '320 585 356 137 7 12295']];
  document.getElementById('helloRows').innerHTML = H.map(([s, ids]) => { const p = s.split('/'), q = ids.split(' '); const el = document.createElement('div'); TK.render(el, p.map((t, i) => ({ text: t, id: q[i] })), { ids: true }); return `<div class="tokrow"><div class="lab">split</div>${el.outerHTML}<div class="cnt">${p.length}</div></div>`; }).join('');
  const W = 'tokenizers';
  const PROBS = { t: .02, o: .02, k: .01, e: .03, n: .02, i: .02, z: .005, r: .02, s: .03, token: .04, tok: .01, en: .02, izer: .01, izers: .004, iz: .006, er: .02, ers: .01, ize: .01, to: .015, ken: .008 };
  const cands = TK.segmentations(W, PROBS);
  let rnd = Math.random;
  const sr = () => {
    const a = Deck.val('srA'), l = Deck.val('srL'); Deck.out('srAo', a.toFixed(2)); Deck.out('srLo', l);
    const dist = TK.smoothed(cands, a, l);
    Deck.hbars(document.getElementById('srBars'), dist.slice(0, 8).map((d, i) => ({ label: d.pieces.join(' | '), value: d.p, color: i === 0 ? 'var(--e)' : 'var(--a)', text: (d.p * 100).toFixed(0) + '%' })), { max: 1 });
    document.getElementById('srSamples').innerHTML = [1, 2, 3, 4, 5, 6].map(e => { const s = TK.sample(dist, rnd); const el = document.createElement('div'); TK.render(el, s.pieces.map(t => ({ text: t }))); return `<div class="tokrow"><div class="lab">epoch ${e}</div>${el.outerHTML}<div class="cnt">${s.pieces.length}</div></div>`; }).join('');
  };
  document.getElementById('srS').onclick = sr;
  Deck.bind(['srA', 'srL'], sr);
  const merges = TK.bpeTrain([['low', 5], ['lower', 2], ['newest', 6], ['widest', 3], ['lowest', 3]], 14).map(s => [s.a, s.b]);
  const bd = () => {
    const p = Deck.val('bdP'); Deck.out('bdPo', p.toFixed(2));
    document.getElementById('bdOut').innerHTML = ['lowest', 'newest', 'lowest', 'widest', 'lowest', 'newest'].map(w => { const el = document.createElement('div'); const sy = TK.bpeEncode(w, merges, p); TK.render(el, sy.map(t => ({ text: t }))); return `<div class="tokrow"><div class="lab">${w}</div>${el.outerHTML}<div class="cnt">${sy.length}</div></div>`; }).join('');
  };
  document.getElementById('bdS').onclick = bd;
  Deck.bind(['bdP'], bd);

})();
