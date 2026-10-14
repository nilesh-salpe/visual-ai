(() => {
  const { svg, clear, fmt } = Deck;

  const rows = (key, opts = {}) => Object.keys(TK.ENC).map(enc => { const el = document.createElement('div'); TK.render(el, TK.get(key, enc), opts); return `<div class="tokrow"><div class="lab">${enc}</div>${el.outerHTML}<div class="cnt">${TK.get(key, enc).length}</div></div>`; }).join('');

  const multi = (keys, opts = { ids: true }) => keys.map(k => `<div style="margin-bottom:10px"><div class="lab" style="font:600 13px 'JetBrains Mono';color:var(--muted);margin-bottom:4px">"${TK.vis(TK.text(k))}"</div>${rows(k, opts)}</div>`).join('');
  document.getElementById('limRows').innerHTML = multi(['straw', 'straw_sp']);
  const Q = {
    spell: [['straw', 'straw_sp', 'straw_cap'], 'The same word splits differently depending on a leading space and capitalization. None of these ids say "three r\'s".'],
    num: [['num', 'arith'], 'GPT-2\'s regex keeps a run of digits together and BPE merges it unevenly (123|45|678). cl100k and o200k pre-split into groups of up to 3 digits from the left (123|456|78). Neither lines up place value across different numbers.'],
    space: [['hello', 'hello_sp', 'Hello', 'HELLO'], '"hello", " hello" and "Hello" are three different ids, and "HELLO" is not even a single token. The model must learn that they are related.'],
    boundary: [['http_full', 'http_colon'], 'A URL in training text tokenizes as <code>http</code> + <code>://</code>. A prompt ending in <code>http:</code> leaves a lone <code>:</code> token, an unusual boundary that misleads the next prediction (see token healing).'],
    glitch: [['magikarp'], '" SolidGoldMagikarp" is a <b>single token</b> in GPT-2\'s tokenizer but splits into ordinary pieces in newer encodings. Tokens like it were nearly absent from the model\'s training data, leaving their embeddings under-trained (Land &amp; Bartolo, 2024).'],
  };
  Deck.seg('qSeg', v => { document.getElementById('qRows').innerHTML = multi(Q[v][0]); document.getElementById('qInfo').innerHTML = Q[v][1]; });
  const full = TK.get('http_full', 'cl100k_base'), colon = TK.get('http_colon', 'cl100k_base');
  const TH = [
    [() => { const a = document.createElement('div'); TK.render(a, colon, { ids: true }); return '<div class="lab" style="font:600 12px Inter;color:var(--muted)">prompt tokens</div>' + a.outerHTML; }, 'The prompt ends with the lone token ":". In training data, ":" is rarely followed by "//" as separate tokens, because URLs were tokenized as "://".'],
    [() => { const a = document.createElement('div'); TK.render(a, colon.slice(0, -1), { ids: true }); return '<div class="lab" style="font:600 12px Inter;color:var(--muted)">prompt after backing up</div>' + a.outerHTML + '<p class="readout" style="margin-top:6px">removed text: <code>:</code></p>'; }, 'Token healing removes the last token from the prompt and remembers its text (":").'],
    [() => { const a = document.createElement('div'); TK.render(a, full, { ids: true }); return '<div class="lab" style="font:600 12px Inter;color:var(--muted)">allowed first token must start with ":". The model can pick "://"</div>' + a.outerHTML; }, 'The first generated token is constrained to start with ":", so the model can choose its natural token "://" and produce a valid URL.'],
  ];
  const ts = document.getElementById('thSteps');
  const pickT = i => { Deck.$$('button', ts).forEach(b => b.classList.toggle('on', +b.dataset.i === i)); document.getElementById('thOut').innerHTML = TH[i][0](); document.getElementById('thInfo').innerHTML = TH[i][1]; };
  ts.addEventListener('click', e => { const b = e.target.closest('button'); if (b) pickT(+b.dataset.i); });
  pickT(0);

})();
