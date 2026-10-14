(() => {
  const { svg, clear, fmt } = Deck;
  const B = [['Ring all-reduce explained', 0, 'title'], ['Home | Blog | About | Log in', 0.79, 'nav'], ['Ring all-reduce explained', 0, 'h1'],
    ['Data-parallel training averages gradients across GPUs. A ring all-reduce does this in two phases, a reduce-scatter and an all-gather.', 0, 'p'],
    ['Each GPU sends about twice the gradient size in total, almost independently of the number of GPUs, which is why the method scales.', 0, 'p'],
    ['Tweet Share', 1, 'div'], ['We use cookies to improve your experience. Privacy policy', 0.24, 'p'], ['Terms © 2024 Example Inc.', 0.2, 'footer']];
  Deck.bind(['xL', 'xW'], () => {
    const L = Deck.val('xL'), W = Deck.val('xW'); Deck.out('xLo', L.toFixed(2)); Deck.out('xWo', W);
    let kept = 0, chars = 0;
    document.getElementById('xList').innerHTML = B.map(([t, ld, tag], i) => {
      const words = t.split(/\s+/).length, boiler = /cookie|privacy policy|terms of use|©/i.test(t), head = i > 0 && i <= 2 && words >= 3;
      const keep = ld < L && !boiler && (words >= W || head) && !(i === 2 && B[0][0] === t && false);
      if (keep) { kept++; chars += t.length; }
      const why = boiler ? 'boilerplate phrase' : ld >= L ? `link density ${ld.toFixed(2)}` : words < W && !head ? `${words} words` : 'kept';
      return `<div style="display:flex;gap:10px;align-items:center;padding:8px 10px;border-radius:8px;background:${keep ? 'var(--a-soft)' : 'var(--panel-2)'};opacity:${keep ? 1 : .6}"><code style="min-width:52px">&lt;${tag}&gt;</code><span style="flex:1">${t}</span><span style="font:600 11px 'JetBrains Mono',monospace;color:${keep ? 'var(--a)' : 'var(--faint)'}">${why}</span></div>`;
    }).join('');
    document.getElementById('xOut').innerHTML = `Kept ${kept} of ${B.length} blocks (${chars} characters). The page title and the &lt;h1&gt; repeat; a later dedup step removes exact repeats.`;
  });
})();
