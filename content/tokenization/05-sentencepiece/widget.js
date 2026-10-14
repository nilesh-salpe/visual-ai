(() => {
  const { svg, clear, fmt } = Deck;

  TK.render(document.getElementById('figToks'), [['151', '▁He'], ['88', 'll'], ['21', 'o'], ['887', '▁world'], ['6', '.']].map(([id, t]) => ({ id, text: t })), { ids: true });
  const sp = () => {
    const raw = document.getElementById('spIn').value, norm = raw.normalize('NFKC'), esc = norm.replace(/ /g, '▁');
    const pieces = esc.match(/▁?[^▁]{1,4}|▁/g) || [];
    const back = pieces.join('').replace(/▁/g, ' ');
    const r = (lab, html, c) => `<div class="tokrow"><div class="lab">${lab}</div>${html}<div class="cnt">${c}</div></div>`;
    const chip = (s, c) => `<div class="toks"><span class="tok ${c}">${TK.esc(s)}</span></div>`;
    const el = document.createElement('div'); TK.render(el, pieces.map(t => ({ text: t })));
    document.getElementById('spRows').innerHTML =
      r('raw', chip(raw, 'c0'), '') +
      r('NFKC', chip(norm, 'c1'), norm === raw ? 'same' : '<span style="color:var(--b)">changed</span>') +
      r('escape ▁', chip(esc, 'c2'), '') +
      r('pieces', el.outerHTML, pieces.length) +
      r('decode', chip(back, 'c3'), back === norm ? '<span style="color:var(--e)">= NFKC ✓</span>' : '✗');
  };
  document.getElementById('spIn').addEventListener('input', sp); sp();

})();
