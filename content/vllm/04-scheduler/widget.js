(() => {
  const { svg, clear, fmt } = Deck;
  let reqs, stepNo;
  const reset = () => { reqs = [{ id: 'A', prompt: 300, done: 300, run: true }, { id: 'B', prompt: 120, done: 120, run: true }, { id: 'C', prompt: 700, done: 0, run: false }, { id: 'D', prompt: 60, done: 0, run: false }]; stepNo = 0; draw({}); };
  const draw = (s) => {
    Deck.out('sBo', Deck.val('sB')); Deck.out('sLo', Deck.val('sL') || 'off');
    Deck.hbars(document.getElementById('sBars'), reqs.map(r => ({ label: `${r.id} ${r.done >= r.prompt ? '(decoding)' : r.run ? '(prefilling)' : '(waiting)'}`, value: s[r.id] || 0, color: r.done >= r.prompt ? 'var(--a)' : 'var(--b)', text: (s[r.id] || 0) + ' tokens' })), { max: Deck.val('sB') });
    const used = Object.values(s).reduce((a, b) => a + b, 0);
    document.getElementById('sOut').innerHTML = stepNo ? `Step ${stepNo}: ${used}/${Deck.val('sB')} budget used. Prompt progress: ${reqs.filter(r => r.prompt > 0).map(r => `${r.id} ${Math.min(r.done, r.prompt)}/${r.prompt}`).join(', ')}.` : 'A and B are decoding; C (700-token prompt) and D (60) are waiting. Press step.';
  };
  document.getElementById('sStep').addEventListener('click', () => {
    let budget = Deck.val('sB'); const lp = Deck.val('sL'), s = {};
    const want = r => { let n = r.done >= r.prompt ? 1 : r.prompt - r.done; if (lp > 0) n = Math.min(n, lp); return Math.min(n, budget); };
    reqs.filter(r => r.run).forEach(r => { if (budget <= 0) return; const n = want(r); s[r.id] = n; budget -= n; });
    reqs.filter(r => !r.run).forEach(r => { if (budget <= 0) return; const n = want(r); r.run = true; s[r.id] = n; budget -= n; });
    reqs.forEach(r => { if (s[r.id]) r.done += s[r.id]; }); stepNo++; draw(s);
  });
  document.getElementById('sReset').addEventListener('click', reset);
  reset();
  Deck.bind(['sB', 'sL'], () => draw({}));
})();
