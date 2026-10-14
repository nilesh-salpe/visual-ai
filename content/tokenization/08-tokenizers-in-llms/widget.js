(() => {
  const { svg, clear, fmt } = Deck;

  const rows = (key, opts = {}) => Object.keys(TK.ENC).map(enc => { const el = document.createElement('div'); TK.render(el, TK.get(key, enc), opts); return `<div class="tokrow"><div class="lab">${enc}</div>${el.outerHTML}<div class="cnt">${TK.get(key, enc).length}</div></div>`; }).join('');

  document.getElementById('cmpRows').innerHTML = rows('compare', { ids: false });
  document.getElementById('numRows').innerHTML = rows('num', { ids: true });

})();
