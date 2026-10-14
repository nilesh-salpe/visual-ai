(() => {
  const { svg, clear, fmt } = Deck;

  const W = 'tokenizers';
  const BASE = { t: .02, o: .02, k: .01, e: .03, n: .02, i: .02, z: .005, r: .02, s: .03, token: .04, tok: .01, en: .02, izer: .01, izers: .004, iz: .006, er: .02, ers: .01, ize: .01, to: .015, ken: .008 };
  const p1 = TK.segmentations(W, BASE).filter(s => ['token|izers', 'token|izer|s', 'tok|en|izers', 't|o|k|e|n|i|z|e|r|s'].includes(s.pieces.join('|')));
  document.getElementById('p1Opts').innerHTML = p1.map(s => { const el = document.createElement('div'); TK.render(el, s.pieces.map(t => ({ text: t }))); return `<div class="tokrow"><div class="lab">option</div>${el.outerHTML}<div class="cnt">?</div></div>`; }).join('');
  Deck.bind(['ugP'], () => {
    const lp = Deck.val('ugP'), probs = { ...BASE, token: Math.pow(10, lp) };
    Deck.out('ugPo', probs.token.toExponential(1));
    const segs = TK.segmentations(W, probs).slice(0, 6), best = TK.viterbi(W, probs);
    Deck.hbars(document.getElementById('ugBars'), segs.map(s => ({ label: s.pieces.join(' | '), value: s.logp + 40, color: s.pieces.join('|') === best.pieces.join('|') ? 'var(--e)' : 'var(--line)', text: 'log P = ' + s.logp.toFixed(1) })), { max: 40 });
    document.getElementById('ugBest').innerHTML = `Viterbi best: <b>${best.pieces.join(' | ')}</b> (log P = ${best.logp.toFixed(2)}). Six most probable of ${TK.segmentations(W, probs).length} candidates shown.`;
  });
  const SEED = [['token', 9], ['izers', 7], ['izer', 8], ['er', 6], ['ers', 3], ['tok', 2], ['en', 4], ['ken', 1.5], ['ize', 2.5], ['iz', 1], ['to', 1.2], ['zers', .6], ['oken', .4], ['niz', .3], ['keni', .2]];
  const CHARS = ['t', 'o', 'k', 'e', 'n', 'i', 'z', 'r', 's'];
  let alive = SEED.slice(), round = 0;
  const pr = () => {
    const removed = SEED.filter(s => !alive.includes(s));
    document.getElementById('prChips').innerHTML = '<div class="toks">' +
      alive.map((s, i) => `<span class="tok c${i % 6}" title="loss ${s[1]}">${s[0]} <small style="color:var(--muted)">${s[1]}</small></span>`).join('') +
      removed.map(s => `<span class="tok" style="text-decoration:line-through;opacity:.4">${s[0]}</span>`).join('') +
      CHARS.map(c => `<span class="tok" style="background:var(--panel-2);border:1px solid var(--line)" title="single character: always kept">${c}</span>`).join('') + '</div>';
    Deck.out('prOut', `round ${round}: ${alive.length} multi-character pieces + ${CHARS.length} characters (always kept)`);
  };
  document.getElementById('prStep').onclick = () => { if (alive.length > 3) { alive = alive.slice().sort((a, b) => b[1] - a[1]).slice(0, Math.max(3, Math.ceil(alive.length * .8))); round++; } pr(); };
  document.getElementById('prReset').onclick = () => { alive = SEED.slice(); round = 0; pr(); };
  pr();

})();
