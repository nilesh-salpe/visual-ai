(() => {
  const { svg, clear, fmt } = Deck;

  TK.render(document.getElementById('introToks'), TK.get('intro', 'cl100k_base'), { ids: true });
  const KNOWN = new Set("the a an and or but because it is was were be to of in on at for with as by from this that these those i you he she we they not did didn't do does cross street animal tired cat sat mat dog man day time year people way good new first last long great little own other old right big high different small large next early young important few public bad same able handled litres for in range print if else return def class import".split(' '));
  const words = t => t.match(/[\p{L}\p{N}']+|[^\s\p{L}\p{N}]/gu) || [];
  const row = (lab, toksHTML, n) => `<div class="tokrow"><div class="lab">${lab}</div><div>${toksHTML}</div><div class="cnt">${n}</div></div>`;
  const chips = arr => '<div class="toks">' + arr.map((t, i) => `<span class="tok c${i % 6}">${TK.vis(t)}</span>`).join('') + '</div>';
  Deck.seg('limSeg', v => {
    const t = TK.text(v), ch = [...t], ws = words(t), sub = TK.get(v, 'cl100k_base');
    const wHTML = '<div class="toks">' + ws.map((w, i) => KNOWN.has(w.toLowerCase()) || /^[^\p{L}\p{N}]$/u.test(w) ? `<span class="tok c${i % 6}">${TK.vis(w)}</span>` : `<span class="tok" style="background:var(--d-soft);color:var(--d)" title="${TK.esc(w)}">[UNK]</span>`).join('') + '</div>';
    const unk = ws.filter(w => !(KNOWN.has(w.toLowerCase()) || /^[^\p{L}\p{N}]$/u.test(w))).length;
    const el = document.createElement('div'); TK.render(el, sub);
    const cost = n => (n * n / (sub.length * sub.length)).toFixed(1) + '× attention cost';
    document.getElementById('limRows').innerHTML =
      row('characters', chips(ch), ch.length + '<div class="tm" style="font:500 10.5px Inter">' + cost(ch.length) + '</div>') +
      row('words', wHTML, ws.length + `<div style="font:500 10.5px Inter;color:var(--d)">${unk} unknown</div>`) +
      row('subwords', el.outerHTML, sub.length + '<div class="tm" style="font:500 10.5px Inter">1.0× (reference)</div>');
  });
  const CORE = [['w_the', 'common word'], ['w_tok', 'common-ish'], ['w_unbel', 'longer word'], ['w_abw', 'rare compound']];
  Deck.seg('coreEnc', enc => {
    document.getElementById('coreRows').innerHTML = CORE.map(([k, lab]) => { const el = document.createElement('div'); TK.render(el, TK.get(k, enc), { ids: true }); return `<div class="tokrow"><div class="lab">${lab}</div>${el.outerHTML}<div class="cnt">${TK.get(k, enc).length}</div></div>`; }).join('');
  });
  // pipeline
  const T = TK.text('s_rare');
  const PAT = /'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+/gu;
  const chunks = T.match(PAT), toks = TK.get('s_rare', 'cl100k_base');
  const decoded = new TextDecoder().decode(new Uint8Array(toks.flatMap(t => t[1])));
  const STEPS = [
    ['1 · Raw text', () => `<div class="toks"><span class="tok c0">${TK.vis(T)}</span></div>`, 'The input is just a string of Unicode characters.'],
    ['2 · Normalize', () => `<div class="toks"><span class="tok c0">${TK.vis(T.normalize('NFKC'))}</span></div>`, 'Some tokenizers first normalize Unicode (SentencePiece applies NFKC by default; deck 05). Byte-level BPE tokenizers such as tiktoken\'s skip this and keep the raw bytes.'],
    ['3 · Pre-tokenize', () => chips(chunks), 'A regular expression splits the text into chunks: words with their leading space, runs of digits, punctuation. Merges never cross chunk boundaries. This is GPT-2\'s pattern (deck 03).'],
    ['4 · Subword model', () => { const el = document.createElement('div'); TK.render(el, toks); return el.outerHTML; }, 'Inside each chunk, BPE applies its learned merges (deck 02). These are the real cl100k_base tokens. Note that cl100k splits numbers into groups of at most 3 digits.'],
    ['5 · Ids', () => { const el = document.createElement('div'); TK.render(el, toks, { ids: true }); return el.outerHTML; }, 'Each token becomes its integer id, and this list of integers is what the model receives.'],
    ['6 · Decode', () => `<div class="toks"><span class="tok c3">${TK.vis(decoded)}</span></div><p class="readout" style="margin-top:8px">${decoded === T ? '<span class="em-e">✓ identical to the input</span>: concatenating the tokens\' bytes is lossless.' : 'differs'}</p>`, 'Decoding concatenates each token\'s bytes and gives back exactly the original text.'],
  ];
  const ps = document.getElementById('pipeSteps');
  ps.innerHTML = STEPS.map((s, i) => `<button data-i="${i}">${s[0]}</button>`).join('');
  const pick = i => { Deck.$$('button', ps).forEach(b => b.classList.toggle('on', +b.dataset.i === i)); document.getElementById('pipeOut').innerHTML = STEPS[i][1](); document.getElementById('pipeInfo').innerHTML = STEPS[i][2]; };
  ps.addEventListener('click', e => { const b = e.target.closest('button'); if (b) pick(+b.dataset.i); });
  pick(0);

})();
