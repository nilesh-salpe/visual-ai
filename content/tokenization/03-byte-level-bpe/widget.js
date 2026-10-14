(() => {
  const { svg, clear, fmt } = Deck;

  const charBox = (c) => { const b = [...new TextEncoder().encode(c)]; return `<div class="ch"><b>${TK.esc(c === ' ' ? '·' : c)}</b><span>${b.map(x => x.toString(16).toUpperCase().padStart(2, '0')).join(' ')}</span></div>`; };
  document.getElementById('p1Chars').innerHTML = [...'café 👋 नम 東京 {x}'].map(charBox).join('');
  Deck.hbars(document.getElementById('limBars'), [
    { label: 'Unicode code points (base, before merges)', value: 130000, color: 'var(--d)', text: '130,000+' },
    { label: 'Typical BPE vocabulary', value: 64000, color: 'var(--b)', text: '32K–64K' },
    { label: 'Byte-level base', value: 256, color: 'var(--e)', text: '256' },
  ], { log: true, min: 100, max: 200000 });
  const by = () => {
    const t = document.getElementById('byIn').value, cs = [...t];
    document.getElementById('byOut').innerHTML = cs.map(charBox).join('');
    const nb = new TextEncoder().encode(t).length;
    document.getElementById('byCnt').innerHTML = `${cs.length} characters → <b>${nb} bytes</b>. Byte-level BPE starts from these ${nb} byte symbols and then merges.`;
  };
  document.getElementById('byIn').addEventListener('input', by); by();
  Deck.seg('exSeg', v => {
    document.getElementById('exRows').innerHTML = Object.keys(TK.ENC).map(enc => { const el = document.createElement('div'); TK.render(el, TK.get(v, enc)); return `<div class="tokrow"><div class="lab">${enc}</div>${el.outerHTML}<div class="cnt">${TK.get(v, enc).length}</div></div>`; }).join('');
  });
  const PAT = /'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+/gu;
  const d = TK.text('dog');
  TK.render(document.getElementById('dogChunks'), d.match(PAT).map(t => ({ text: t })));
  TK.render(document.getElementById('dogToks'), TK.get('dog', 'gpt2'), { ids: true });

})();
