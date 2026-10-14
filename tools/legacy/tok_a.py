from tool import section, your_turn, myths, check

DECKS = {}
ENCSEG = '<div class="seg" id="{id}"><button data-v="gpt2">gpt2</button><button data-v="cl100k_base" class="on">cl100k_base</button><button data-v="o200k_base">o200k_base</button></div>'

# =============================================================== 01
DECKS['01-why-tokenize'] = dict(
    title='Why Tokenize', h1='Why tokenize?',
    sub='A language model can only process numbers. Tokenization decides how text becomes a sequence of integer ids, and that choice affects vocabulary size, sequence length, cost, and what the model can "see".',
    prob='Characters make sequences very long. Whole words leave rare and new words unknown.',
    core='Use <b>subwords</b>: common words stay whole, rare words split into known pieces, so any text fits a fixed vocabulary.',
    slides=[
        section('s-p1', 1, 'A model never sees text, only integer ids', '''    <p class="lede">Before an LLM does anything, the input string is cut into <b>tokens</b>, and each token is replaced by its id in a fixed vocabulary. The model's first layer looks up one embedding row per id. Below is a real tokenization with <code>cl100k_base</code> (GPT-4's encoding).</p>
    <div class="visual">
      <h3>"Tokenization turns text into numbers."</h3>
      <div id="introToks" style="margin-top:10px"></div>
      <p class="caption">Hover a token for its id. <span class="ws">·</span> marks a space, which belongs to the token that follows it.</p>
      <div class="paper" style="margin-top:14px"><b>Next step inside the model:</b> each id selects one row of the embedding matrix (vocabulary size V × model width d). The model's output layer then scores all V ids to predict the next token.</div>
    </div>
    <div class="takeaway">Everything the model learns, it learns over these ids. How text is split decides what each id means.</div>'''),
        section('s-lim', 2, 'The two obvious units both break', '''    <p class="lede">Split by <b>characters</b> and the vocabulary is tiny, but sequences get long, and attention cost grows with the square of the length. Split by <b>words</b> and sequences are short, but any word outside the vocabulary becomes an unknown token. Pick a sentence.</p>
    <div class="visual">
      <div class="seg" id="limSeg"><button data-v="s_animal" class="on">Everyday sentence</button><button data-v="s_rare">Rare word + number</button><button data-v="s_code">Code</button></div>
      <div id="limRows" style="margin-top:12px"></div>
      <p class="caption">Characters and words are split in the browser. The word row uses a <span class="ill">toy</span> vocabulary of about 100 common English words, and anything else becomes [UNK]. The subword row is the real <code>cl100k_base</code> output.</p>
    </div>
    <div class="cite">Sennrich et al. (2016) put the trade-off this way: an increase in text length "reduces efficiency and increases the distances over which neural models need to pass information", while large vocabularies cost time and space.</div>'''),
        your_turn('s-turn', 'Pick the unit',
                  'Which unit gives a fixed, modest vocabulary, reasonably short sequences, and no unknown words?',
                  ['Whole words', 'Single characters', 'Subwords: frequent strings kept whole, rare ones split into known pieces', 'Whole sentences'], 2,
                  '<b>C.</b> Words (A) leave rare words unknown, characters (B) make sequences long, and sentences (D) would need an infinite vocabulary. Subwords sit in between: common words become single tokens, and anything rare is spelled out with smaller pieces that are in the vocabulary.'),
        section('s-core', 4, 'Subwords: common words stay whole, rare words split', '''    <p class="lede">Real tokenizer output. Note the leading space: in these tokenizers a word and the space before it usually form one token.</p>
    <div class="visual">
      ''' + ENCSEG.format(id='coreEnc') + '''
      <div id="coreRows" style="margin-top:12px"></div>
    </div>
    <div class="takeaway">The vocabulary is fixed (about 100K tokens for cl100k_base), yet any word can still be written, from "the" to "Abwasserbehandlungsanlage" (Sennrich et al.'s example of a German compound).</div>'''),
        section('s-how', 5, 'The tokenization pipeline, end to end', '''    <p class="lede">Tokenizers differ in detail, but most follow the same stages. Below, one sentence goes through them with real GPT-2-style pre-tokenization and real <code>cl100k_base</code> tokens.</p>
    <div class="visual">
      <div class="steps" id="pipeSteps"></div>
      <div id="pipeOut" style="margin-top:14px"></div>
      <div class="infobox" id="pipeInfo"></div>
    </div>'''),
        section('s-why', 6, 'Why subwords work', '''    <div class="grid2">
      <div class="card a"><h3>Compression</h3><p>tiktoken's README puts typical BPE compression at about <b>4 bytes per token</b>. On this guide's 408-character English sample, <code>cl100k_base</code> uses 79 tokens, about 5.2 characters per token.</p></div>
      <div class="card b"><h3>Fixed output layer</h3><p>The model predicts one of V ids at every step. A fixed V (50K–200K) keeps that softmax bounded.</p></div>
      <div class="card c"><h3>Open vocabulary</h3><p>Rare words are spelled with smaller pieces, and byte-level tokenizers (deck 03) can encode any string at all.</p></div>
      <div class="card e"><h3>Shorter sequences</h3><p>Fewer tokens means less attention compute (it grows with n²) and more text in a fixed context window (deck 07).</p></div>
    </div>'''),
        myths('s-myth', [
            ('A token is a word.', 'Often it is a <b>piece</b> of a word, and it usually includes the space before it: " strawberry" is one token in cl100k_base, but "strawberry" without the space is three (deck 10).'),
            ('Every model counts tokens the same way.', 'Each model has its own tokenizer. The sentence on the "Characters or words?" slide gets different token counts in gpt2, cl100k_base and o200k_base (deck 08).'),
            ('Tokenization throws information away.', 'Modern BPE tokenizers are <b>reversible and lossless</b> (tiktoken README): concatenating the tokens\' bytes gives back the original text exactly.'),
        ]),
        check('s-check', [
            ('mcq', 'Roughly how many bytes of text does one BPE token cover on average, according to tiktoken\'s README?', ['1', 'About 4', 'About 40', 'One whole sentence'], 1, '<b>About 4 bytes per token</b> in practice. It varies with language and content.'),
            ('open', 'Why not just use characters as tokens?', 'Sequences become several times longer, and attention cost grows with the square of the length, so compute rises and less text fits in the context window.'),
            ('mcq', 'A subword tokenizer meets a word it has never seen. What happens?', ['It outputs [UNK]', 'It splits the word into smaller known pieces', 'It skips the word', 'It raises an error'], 1, '<b>It splits the word into known pieces</b>, down to single characters or bytes if needed.'),
        ]),
    ],
    js=r'''
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
''',
    line='Tokenization maps text to integer ids from a fixed vocabulary. Subwords keep common words whole and spell rare ones in pieces, balancing vocabulary size against sequence length.',
    explain='Models work on integers, so text is split into tokens and each token becomes an id from a fixed vocabulary. Characters give tiny vocabularies but long sequences, and words give short sequences but unknown words. Subword tokenizers keep frequent strings as single tokens and split rare words into known pieces. The pipeline is normalize, pre-tokenize, apply the subword model, then map to ids, and decoding reverses it losslessly.',
    recap=[('Problem', 'characters make sequences long; words leave rare words unknown.'), ('Core idea', 'subword tokens: a fixed vocabulary where any text is spelled with known pieces, about 4 bytes per token.')],
)

# =============================================================== 02
DECKS['02-bpe-from-scratch'] = dict(
    title='BPE From Scratch', h1='Byte-pair encoding, from scratch',
    sub='The algorithm behind most LLM tokenizers: start from characters and repeatedly merge the most frequent adjacent pair (Sennrich, Haddow and Birch, 2016).',
    prob='Translation and language modelling are open-vocabulary problems, and a fixed word list can\'t cover rare words, names and compounds.',
    core='Learn a vocabulary of frequent character sequences by repeatedly merging the most frequent pair of symbols. Rare words are then spelled with those pieces.',
    slides=[
        section('s-p1', 1, 'Rare words are everywhere', '''    <div class="grid3">
      <div class="card a"><h3>Names</h3><p>New people, places and products appear constantly. Many can just be copied or transliterated piece by piece.</p></div>
      <div class="card b"><h3>Compounds</h3><p>German builds words like <b>Abwasserbehandlungsanlage</b> ("sewage water treatment plant"), the paper's own example. It's unlikely to be in any word list, but its parts are common.</p></div>
      <div class="card c"><h3>Cognates and loanwords</h3><p>Words shared across languages often translate through regular character-level patterns.</p></div>
    </div>
    <div class="takeaway">The paper's observation: many rare words can be translated through units <em>smaller than words</em>.</div>'''),
        section('s-lim', 2, 'Before BPE: shortlists, unknown tokens and back-off dictionaries', '''    <div class="grid3">
      <div class="card d"><h3>Fixed word vocabulary</h3><p>Models used a shortlist of frequent words; everything else became an unknown token.</p></div>
      <div class="card b"><h3>Back-off dictionary</h3><p>Unknown words were looked up in a separate dictionary after translation, outside the neural model. This was the paper's baseline.</p></div>
      <div class="card c"><h3>Characters only</h3><p>Fully open, but sequences become much longer, which hurts efficiency and makes information travel further.</p></div>
    </div>'''),
        your_turn('s-turn', 'Which pair merges first?',
                  'Training corpus (the one in the paper\'s Algorithm 1): <code>low ×5, lower ×2, newest ×6, widest ×3</code>, each word split into characters plus an end-of-word marker ·. Which pair does BPE merge first?',
                  ['l + o', 'e + s', 'w + i', 'n + e'], 1,
                  '<b>e + s</b>, with 9 occurrences (newest ×6 + widest ×3). s + t and t + · are also 9, and the tie goes to the pair counted first. l + o has 7, n + e has 6, w + i has 3. Then "es + t" and "est + ·" follow. Check it in the trainer two slides on.'),
        section('s-core', 4, 'Merge the most frequent pair, repeat', '''    <div class="grid2">
      <div class="card a"><h3>1. Start from characters</h3><p>Each word is a sequence of characters plus an end-of-word symbol ·, so the original spacing can be restored.</p></div>
      <div class="card b"><h3>2. Count adjacent pairs</h3><p>Count every pair of neighbouring symbols, weighted by word frequency. Pairs never cross word boundaries.</p></div>
      <div class="card e"><h3>3. Merge the top pair</h3><p>Replace every occurrence of the most frequent pair (A, B) with a new symbol AB and record the merge.</p></div>
      <div class="card c"><h3>4. Repeat</h3><p>Stop after a chosen number of merges. Final vocabulary = initial characters + merges, and the number of merges is "the only hyperparameter".</p></div>
    </div>'''),
        section('s-how', 5, 'Train BPE yourself', '''    <p class="lede">Edit the corpus (<code>word:count</code>) and step through merges. The trainer is a direct JavaScript port of the paper's Algorithm 1.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <input class="tk-in" id="bpeCorpus" style="flex:1;min-width:260px" value="low:5, lower:2, newest:6, widest:3">
        <label class="ctl">Merges <input type="range" id="bpeN" min="0" max="15" step="1" value="3"> <output id="bpeNo"></output></label>
      </div>
      <div class="grid2" style="margin-top:12px">
        <div><h3>Corpus after merges</h3><div id="bpeVocab"></div><h3 style="margin-top:12px">Next candidate pairs</h3><div id="bpePairs"></div></div>
        <div><h3>Learned merges, in order</h3><div class="mergelist" id="bpeMerges"></div>
          <h3 style="margin-top:12px">Encode a new word</h3>
          <div class="controls" style="margin-top:4px"><input class="tk-in" id="bpeWord" value="lowest" style="width:160px"></div>
          <div id="bpeEnc" style="margin-top:8px"></div></div>
      </div>
    </div>'''),
        section('s-how2', 5, 'Encoding an unseen word: the paper\'s Figure 1', '''    <p class="lede">At test time, split the word into characters and apply the learned merges <b>in the order they were learned</b>. Figure 1 lists four merges learned from the dictionary {low, lowest, newer, wider}. The unseen word "lower" then comes out as <b>low er·</b>.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0"><button class="btn primary" id="f1Step">Apply next merge →</button><button class="btn" id="f1Reset">Reset</button><span class="readout" id="f1Out"></span></div>
      <div id="f1Toks" style="margin-top:14px"></div>
      <div class="mergelist" id="f1List" style="margin-top:12px"></div>
    </div>
    <div class="cite">Sennrich et al. (2016), Figure 1 and §3.2.</div>'''),
        section('s-why', 6, 'Why BPE works', '''    <div class="grid2">
      <div class="card a"><h3>Frequency decides granularity</h3><p>Frequent strings are merged early, so common words become single symbols. Rare words remain split into smaller units.</p></div>
      <div class="card e"><h3>No shortlist, no back-off</h3><p>Any word made of known characters can be encoded, so the model handles rare and unseen words itself.</p></div>
      <div class="card b"><h3>Compression</h3><p>It comes from a data-compression algorithm (Gage, 1994): fewer symbols are needed to encode the text.</p></div>
      <div class="card c"><h3>Measured gains</h3><p>On WMT 15, subword models improved over the back-off dictionary baseline by <b>1.1 BLEU</b> (EN→DE) and <b>1.3 BLEU</b> (EN→RU) (abstract).</p></div>
    </div>'''),
        myths('s-myth', [
            ('BPE finds the shortest or most likely segmentation of a word.', 'It replays merges <b>greedily, in learned order</b>. That is fast and deterministic, but not an optimization over all segmentations (compare the unigram LM in deck 04).'),
            ('You choose the vocabulary size directly.', 'In the original algorithm you choose the <b>number of merges</b>; vocabulary = characters + merges. Toolkits such as SentencePiece let you specify the final vocabulary size instead (deck 05).'),
            ('BPE merges can join two words.', 'Not in the paper: "we do not consider pairs that cross word boundaries". LLM tokenizers enforce this with pre-tokenization (deck 03).'),
        ]),
        check('s-check', [
            ('mcq', 'Using the paper\'s Figure 1 merges, how is the unseen word "lower" segmented?', ['l o w e r ·', 'low er·', 'lower·', 'lo wer·'], 1, '<b>low er·</b> (§3.2).'),
            ('open', 'What is the only hyperparameter of the original BPE algorithm?', 'The <b>number of merge operations</b>. The final symbol vocabulary is the initial characters plus the merges.'),
            ('mcq', 'What is the end-of-word symbol for?', ['To mark rare words', 'To restore the original tokenization after translation', 'To count frequencies', 'To pad sequences'], 1, 'It lets you <b>restore the original word boundaries</b> after processing (§3.2).'),
        ]),
    ],
    js=r'''
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
''',
    line='BPE starts from characters and repeatedly merges the most frequent adjacent pair. Replaying those merges in order turns any word into known subword units.',
    explain='Byte-pair encoding, adapted to NLP by Sennrich et al. (2016), learns a subword vocabulary from data. Every word starts as characters plus an end-of-word marker; you repeatedly count adjacent symbol pairs and merge the most frequent one, and the number of merges is the only hyperparameter. Frequent words end up as single symbols and rare words split into pieces, so there are no unknown words. To encode new text you replay the merges in learned order.',
    recap=[('Problem', 'a fixed word vocabulary can\'t cover rare words, names and compounds.'), ('Core idea', 'learn merges of frequent symbol pairs; encode any word by replaying them in order.')],
)

# =============================================================== 03
DECKS['03-byte-level-bpe'] = dict(
    title='Byte-Level BPE', h1='Byte-level BPE',
    sub='How GPT-2 made BPE work on any string at all (emoji, every script, code) with a base vocabulary of only 256 symbols (Radford et al., 2019, §2.2).',
    prob='A general language model should be able to give a probability to, and generate, any string. Character-level BPE either needs a huge base vocabulary or produces unknown tokens.',
    core='Run BPE over the UTF-8 <b>bytes</b> of the text instead of Unicode characters. The base vocabulary is 256 bytes, so nothing is ever unknown.',
    slides=[
        section('s-p1', 1, 'An LLM must handle any string', '''    <p class="lede">The GPT-2 paper sets the requirement: "A general language model (LM) should be able to compute the probability of (and also generate) any string." Real input includes accented letters, emoji, dozens of scripts, code, and stray control characters.</p>
    <div class="visual"><div class="bytes" id="p1Chars"></div></div>
    <div class="takeaway">Lowercasing, word-level tokenization and unknown tokens all <b>restrict which strings the model can represent</b> (§2.2).</div>'''),
        section('s-lim', 2, 'BPE over Unicode characters needs a huge base vocabulary', '''    <p class="lede">Reference BPE implementations of the time worked on Unicode code points. Covering every possible string that way would need "a base vocabulary of over 130,000 before any multi-symbol tokens are added", far larger than the 32,000–64,000-token vocabularies typically used with BPE.</p>
    <div class="visual"><div id="limBars"></div></div>
    <div class="cite">GPT-2 paper §2.2. The alternative, an unknown token for rare characters, gives up the "any string" requirement.</div>'''),
        your_turn('s-turn', 'Cover everything with a small base',
                  'How can BPE cover every possible string while keeping the base vocabulary small?',
                  ['Include all Unicode characters in the base vocabulary', 'Run BPE over the 256 possible UTF-8 byte values', 'Keep ASCII only and map everything else to [UNK]', 'Use whole words'], 1,
                  '<b>B.</b> Every string is a sequence of UTF-8 bytes, and there are only 256 byte values. Starting BPE from bytes makes the base vocabulary 256 and leaves no unknown symbols. Option A needs more than 130,000 base symbols, and C gives up coverage.'),
        section('s-core', 4, 'BPE on bytes: 256 base symbols, then merges', '''    <div class="grid3">
      <div class="card a"><h3>Base = 256 bytes</h3><p>Any text is first encoded as UTF-8, a sequence of bytes 0–255. That's the starting alphabet.</p></div>
      <div class="card b"><h3>Merges on top</h3><p>BPE merges frequent byte sequences into tokens. Common English words become single tokens, and rarer scripts use more, shorter tokens.</p></div>
      <div class="card e"><h3>GPT-2's numbers</h3><p>Vocabulary 50,257 = <b>256 bytes + 50,000 merges + 1 special token</b> (&lt;|endoftext|&gt;), checked with tiktoken.</p></div>
    </div>'''),
        section('s-how', 5, 'From characters to bytes: try it', '''    <p class="lede">Type anything. Each character becomes 1 to 4 UTF-8 bytes. ASCII takes 1 byte, accented Latin letters 2, Devanagari and Japanese 3, and most emoji 4.</p>
    <div class="visual">
      <input class="tk-in" id="byIn" value="héllo 👋 नमस्ते" style="width:100%">
      <div class="bytes" id="byOut" style="margin-top:12px"></div>
      <p class="readout" id="byCnt" style="margin-top:8px"></p>
    </div>'''),
        section('s-how2', 5, 'Real byte-level tokens, including partial characters', '''    <p class="lede">Real output from three tiktoken encodings. A token can end <b>in the middle of a character</b>. Tokens with a dashed red outline hold incomplete UTF-8 bytes, which only become a character when joined with their neighbours.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <div class="seg" id="exSeg"><button data-v="hello_emoji" class="on">héllo 👋</button><button data-v="hindi">नमस्ते दुनिया</button><button data-v="jp">こんにちは世界。</button></div>
      </div>
      <div id="exRows" style="margin-top:12px"></div>
    </div>'''),
        section('s-how3', 5, 'Pre-tokenization: no merges across character categories', '''    <p class="lede">Applied naively, byte-level BPE wasted vocabulary on variants such as <code>dog.</code>, <code>dog!</code> and <code>dog?</code>. GPT-2 therefore stops BPE from merging across character categories. A regular expression first splits text into chunks (letters, numbers, punctuation), with an exception that lets a space attach to the following word.</p>
    <div class="visual">
      <h3>Pre-tokenized chunks (GPT-2 pattern)</h3><div id="dogChunks" style="margin-top:6px"></div>
      <h3 style="margin-top:14px">Final tokens (gpt2)</h3><div id="dogToks" style="margin-top:6px"></div>
    </div>
    <div class="cite">§2.2: "We observed BPE including many versions of common words like dog since they occur in many variations such as dog. dog! dog?" Pattern shown is GPT-2's (tiktoken r50k), minus regex features JavaScript lacks.</div>'''),
        section('s-why', 6, 'Why it works', '''    <div class="grid2">
      <div class="card a"><h3>Nothing is ever unknown</h3><p>Every string is a byte sequence and all 256 bytes are in the vocabulary, so any input can be encoded.</p></div>
      <div class="card e"><h3>Any string gets a probability</h3><p>"Since our approach can assign a probability to any Unicode string," GPT-2 could be evaluated on any dataset "regardless of pre-processing, tokenization, or vocab size" (§2.2).</p></div>
      <div class="card b"><h3>Word-level efficiency where it counts</h3><p>Merges make frequent strings single tokens, combining "the empirical benefits of word-level LMs with the generality of byte-level approaches".</p></div>
      <div class="card c"><h3>Vocabulary spent well</h3><p>The category rule stops near-duplicate tokens like "dog." and "dog!" from using up vocabulary slots.</p></div>
    </div>'''),
        myths('s-myth', [
            ('Byte-level means one token per byte.', 'Bytes are only the <b>base</b>. Merges build multi-byte tokens, so a common English word with its leading space is usually a single token.'),
            ('Every token decodes to valid text.', 'A token can hold a <b>partial</b> UTF-8 character: the 👋 emoji above is split across two tokens. Streaming output has to buffer bytes until a character is complete.'),
            ('The space between words is its own token.', 'In GPT-2-style pre-tokenization a single space attaches to the <b>following</b> word: " dog" is one token.'),
        ]),
        check('s-check', [
            ('mcq', 'How big is the base vocabulary of byte-level BPE?', ['26', '256', '50,257', '130,000+'], 1, '<b>256</b>, one symbol per byte value.'),
            ('mcq', 'What makes up GPT-2\'s 50,257-token vocabulary?', ['50,257 words', '256 bytes + 50,000 merges + 1 special token', '130,000 characters pruned to 50K', '50,000 bytes + 257 merges'], 1, '<b>256 + 50,000 + 1</b>. The special token is &lt;|endoftext|&gt; (id 50256).'),
            ('open', 'Why can a byte-level BPE tokenizer never output an unknown token?', 'Every possible input is a sequence of bytes, and every byte value is a base token, so the worst case is simply one token per byte.'),
        ]),
    ],
    js=r'''
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
''',
    line='Byte-level BPE runs BPE over UTF-8 bytes: a 256-symbol base means any string can be encoded with no unknowns, while merges keep common text compact.',
    explain='GPT-2 wanted a model that could assign a probability to any string. BPE over Unicode characters would need a base vocabulary of more than 130,000 symbols, so GPT-2 runs BPE over UTF-8 bytes instead: 256 base symbols plus 50,000 merges plus one special token gives 50,257. A regex pre-tokenizer stops merges across letters, digits and punctuation, so near-duplicates like "dog." and "dog!" don\'t waste vocabulary. Tokens can hold partial characters, so decoding has to buffer bytes.',
    recap=[('Problem', 'any-string coverage with character BPE needs 130K+ base symbols, or [UNK].'), ('Core idea', 'BPE over bytes: a base of 256, nothing unknown, merges for efficiency, regex pre-tokenization.')],
)

# =============================================================== 04
DECKS['04-wordpiece-unigram'] = dict(
    title='WordPiece and Unigram', h1='WordPiece and the unigram language model',
    sub='Tokenizers that choose subwords by likelihood instead of raw frequency. The unigram LM (Kudo, 2018) also gives every segmentation a probability.',
    prob='BPE merges greedily by frequency and gives exactly one segmentation, with no score for how good it is.',
    core='Use a probabilistic model of subwords. WordPiece picks merges by likelihood; the unigram LM starts large, prunes by likelihood, and segments with Viterbi.',
    slides=[
        section('s-p1', 1, 'What makes one segmentation better than another?', '''    <p class="lede">"tokenizers" could be token|izers, token|izer|s, tok|en|izers, or t|o|k|e|n|i|z|e|r|s. BPE always returns the same one because it replays fixed merges. It never <em>scores</em> the options.</p>
    <div class="visual"><div id="p1Opts"></div></div>
    <p class="caption">Candidate segmentations are <span class="ill">illustrative</span>.</p>'''),
        section('s-lim', 2, 'BPE\'s limits, as Kudo describes them', '''    <div class="grid3">
      <div class="card d"><h3>Greedy</h3><p>BPE is "based on a greedy and deterministic symbol replacement". Early merges are fixed and never reconsidered.</p></div>
      <div class="card b"><h3>No probabilities</h3><p>It "can not provide multiple segmentations with probabilities" (Kudo 2018, §3.1).</p></div>
      <div class="card c"><h3>Frequency, not fit</h3><p>Merges are chosen by raw pair counts, not by how well the resulting vocabulary explains the data.</p></div>
    </div>'''),
        your_turn('s-turn', 'Choose the vocabulary differently',
                  'Instead of merging the most frequent pair, how else could you choose which subwords go into the vocabulary?',
                  ['At random', 'Choose subwords that maximize the likelihood of the training text under a language model', 'Alphabetically', 'Keep the longest substrings'], 1,
                  '<b>B.</b> This is the idea behind both <b>WordPiece</b> (BPE-like merges, but each merge chosen by likelihood) and the <b>unigram LM</b> (start large and remove the subwords whose loss hurts likelihood least).'),
        section('s-core', 4, 'Two likelihood-based tokenizers', '''    <div class="grid2">
      <div class="card a"><h3>WordPiece</h3><p>Builds the vocabulary incrementally like BPE, but "uses a likelihood instead of frequency" to choose merges (Kudo 2018, footnotes 1–2; Schuster &amp; Nakajima, 2012). BERT uses "WordPiece embeddings with a 30,000 token vocabulary".</p></div>
      <div class="card e"><h3>Unigram language model</h3><p>Each subword has a probability p(x), and a segmentation's probability is the product: <b>P(x) = Π p(x<sub>i</sub>)</b>. The best segmentation is found by Viterbi. The vocabulary is learned by starting big and pruning (Kudo, 2018).</p></div>
    </div>'''),
        section('s-how', 5, 'Unigram LM: score every segmentation, pick the best <span class="ill">toy probabilities</span>', '''    <p class="lede">With P(x) = Π p(x<sub>i</sub>), each way of splitting "tokenizers" gets a probability. Viterbi finds the most probable one in linear time. Drag the probability of the piece "token" and watch the winner change.</p>
    <div class="visual">
      <label class="ctl">p("token") <input type="range" id="ugP" min="-5" max="-1" step="0.1" value="-1.4"> <output id="ugPo"></output></label>
      <div id="ugBars" style="margin-top:12px"></div>
      <p class="readout" id="ugBest" style="margin-top:8px"></p>
    </div>'''),
        section('s-how2', 5, 'Learning the unigram vocabulary: EM, then prune', '''    <p class="lede">The vocabulary itself is unknown, so the unigram method (Kudo §3.2) starts from a large seed vocabulary and repeatedly removes the least useful pieces. Step through the rounds <span class="ill">toy loss values</span>.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0"><button class="btn primary" id="prStep">Next pruning round →</button><button class="btn" id="prReset">Reset</button><span class="readout" id="prOut"></span></div>
      <div id="prChips" style="margin-top:12px"></div>
    </div>
    <div class="grid3" style="margin-top:12px">
      <div class="card a"><h3>(a) EM</h3><p>Fix the vocabulary and estimate p(x) with expectation-maximization.</p></div>
      <div class="card b"><h3>(b) Loss</h3><p>For each subword, compute how much the likelihood drops if it is removed.</p></div>
      <div class="card e"><h3>(c) Keep top η%</h3><p>Keep the top η = 80% by loss. Single characters are always kept, so nothing becomes unknown.</p></div>
    </div>'''),
        section('s-why', 6, 'Why likelihood-based tokenizers help', '''    <div class="grid2">
      <div class="card e"><h3>Principled segmentation</h3><p>Viterbi returns the single most probable split under the model, not just the result of replaying merges.</p></div>
      <div class="card a"><h3>Probabilities for alternatives</h3><p>The unigram LM can output several segmentations with probabilities, which deck 06 uses to sample them during training.</p></div>
      <div class="card b"><h3>An entropy-coding view</h3><p>Kudo frames the unigram model as an entropy encoder: the optimal code length for a symbol s is −log p<sub>s</sub>, so likely pieces get short codes (§3.4).</p></div>
      <div class="card c"><h3>No unknowns</h3><p>All characters stay in the vocabulary, so character-level segmentation is always one of the candidates.</p></div>
    </div>'''),
        myths('s-myth', [
            ('WordPiece and the unigram LM are the same algorithm.', 'WordPiece <b>grows</b> a vocabulary by likelihood-chosen merges, BPE-style. The unigram LM <b>shrinks</b> a large seed vocabulary by pruning, then segments with Viterbi.'),
            ('Unigram tokenization picks the longest matching piece first.', 'It picks the segmentation with the <b>highest product of probabilities</b>, found by Viterbi, which isn\'t always the one with the longest pieces.'),
            ('Pruning can remove characters and create unknowns.', 'Subwords consisting of a single character are <b>always kept</b> (§3.2), so every string stays encodable.'),
        ]),
        check('s-check', [
            ('mcq', 'What vocabulary does BERT use?', ['Byte-level BPE, 50,257', 'WordPiece, 30,000 tokens', 'Unigram LM, 32,000', 'Words, 100,000'], 1, '<b>WordPiece with a 30,000-token vocabulary</b> (BERT, §3).'),
            ('mcq', 'In the unigram LM, how is the best segmentation found?', ['Greedy longest match', 'Replaying merges', 'The Viterbi algorithm', 'Random sampling'], 2, '<b>Viterbi</b>: x* = argmax P(x) over all candidate segmentations (Eq. 7).'),
            ('open', 'In one pruning round, what fraction of subwords does Kudo\'s example keep, and which are always kept?', 'The top <b>η = 80%</b> by loss. Single-character subwords are always kept.'),
        ]),
    ],
    js=r'''
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
''',
    line='Likelihood-based tokenizers score segmentations: WordPiece chooses merges by likelihood, and the unigram LM prunes a big vocabulary with EM and segments with Viterbi.',
    explain='BPE merges by raw frequency and replays merges greedily, so it gives one segmentation with no probability. WordPiece, used by BERT with 30,000 tokens, grows the vocabulary like BPE but chooses merges by likelihood. The unigram LM gives each subword a probability, scores a segmentation as the product of its pieces\' probabilities, finds the best with Viterbi, and learns the vocabulary by running EM and pruning the 20% of pieces whose removal hurts likelihood least. Single characters are always kept.',
    recap=[('Problem', 'BPE is greedy and deterministic, with no probabilities.'), ('Core idea', 'model subwords probabilistically: WordPiece merges by likelihood; the unigram LM uses EM, pruning and Viterbi.')],
)

# =============================================================== 05
DECKS['05-sentencepiece'] = dict(
    title='SentencePiece', h1='SentencePiece',
    sub='A language-independent tokenizer and detokenizer that trains directly on raw text, treats whitespace as an ordinary symbol, and round-trips losslessly (Kudo and Richardson, 2018).',
    prob='Existing tools assumed text was already split into words, and relied on hand-written, language-specific rules to tokenize and detokenize.',
    core='Treat the input as a raw Unicode sequence. Escape whitespace as ▁ (U+2581), learn BPE or unigram subwords on top, and decode exactly.',
    slides=[
        section('s-p1', 1, 'Tokenizing and detokenizing raw text is language-dependent', '''    <div class="grid2">
      <div class="visual" style="margin-top:0"><h3>English</h3><p class="caption" style="margin-top:4px">Raw: <code>Hello world.</code><br>Pre-tokenized: <code>[Hello] [world] [.]</code></p><p>The pre-tokenized form has lost the fact that there was <b>no space</b> between "world" and ".", so the detokenizer has to guess with language rules.</p></div>
      <div class="visual" style="margin-top:0"><h3>Japanese</h3><p class="caption" style="margin-top:4px">Raw: <code>こんにちは世界。</code> (Hello world.)<br>Pre-tokenized: <code>[こんにちは] [世界] [。]</code></p><p>There are no spaces at all, so splitting into words needs a separate word segmenter, and detokenizing must <b>not</b> insert spaces.</p></div>
    </div>
    <div class="cite">Examples from the SentencePiece paper, §3.1.</div>'''),
        section('s-lim', 2, 'Hand-written pre- and post-processors don\'t scale across languages', '''    <div class="grid3">
      <div class="card d"><h3>Hand-crafted rules</h3><p>Moses, the standard toolkit at the time, uses language-dependent rules "whose effectiveness for NMT has not been proven".</p></div>
      <div class="card b"><h3>European bias</h3><p>These tools were "mainly designed for European languages where words are segmented with whitespaces".</p></div>
      <div class="card c"><h3>Multilingual pain</h3><p>Every language needs its own pre/post-processor configuration, which makes multilingual models hard to build (§1).</p></div>
    </div>'''),
        your_turn('s-turn', 'Make it reversible in any language',
                  'How can a tokenizer be exactly reversible on raw text in any language, with no language-specific rules?',
                  ['Keep a per-language list of spacing rules', 'Treat whitespace as an ordinary symbol and keep it inside the tokens', 'Delete whitespace before tokenizing', 'Always split on spaces first'], 1,
                  '<b>B.</b> SentencePiece escapes each space as the visible symbol ▁ (U+2581) and tokenizes the whole string as a character sequence. Because the spaces are inside the tokens, detokenizing is just joining the tokens and turning ▁ back into a space.'),
        section('s-core', 4, 'Raw text in, whitespace as a symbol, lossless out', '''    <div class="eq">Decode( Encode( Normalize(text) ) ) = Normalize(text)</div>
    <div class="grid3" style="margin-top:14px">
      <div class="card a"><h3>Raw sentences</h3><p>"SentencePiece can train subword models directly from raw sentences", with no word segmenter needed.</p></div>
      <div class="card b"><h3>▁ for whitespace</h3><p>Spaces are escaped as ▁ (U+2581), so <code>Hello▁world.</code> → <code>[Hello] [▁wor] [ld] [.]</code>.</p></div>
      <div class="card e"><h3>Two algorithms</h3><p>Implements both BPE (Sennrich et al.) and the unigram LM (Kudo), selected as a training option.</p></div>
    </div>'''),
        section('s-how', 5, 'Encode and decode, step by step', '''    <p class="lede">Top: the paper's real example (Figure 1, a model trained with vocabulary size 1000). Bottom: try your own text. Normalization and the ▁ escape are computed exactly; the subword split below them is <span class="ill">illustrative</span>, since no trained model runs in this page.</p>
    <div class="visual">
      <h3>Paper example</h3>
      <div class="tokrow"><div class="lab">input</div><div class="toks"><span class="tok c0">Hello world.</span></div><div class="cnt"></div></div>
      <div class="tokrow"><div class="lab">spm_encode</div><div id="figToks"></div><div class="cnt">5</div></div>
      <div class="tokrow"><div class="lab">spm_decode</div><div class="toks"><span class="tok c3">Hello world.</span></div><div class="cnt">✓</div></div>
      <h3 style="margin-top:16px">Your text</h3>
      <input class="tk-in" id="spIn" value="ＡＢＣ  costs  ½ price." style="width:100%">
      <div id="spRows" style="margin-top:8px"></div>
    </div>'''),
        section('s-how2', 5, 'Four components and id management', '''    <div class="grid2">
      <div class="visual" style="margin-top:0"><h3>Pipeline (§2)</h3><div class="steps" style="margin-top:8px"><button class="on">Normalizer</button><button class="on">Trainer</button><button class="on">Encoder</button><button class="on">Decoder</button></div>
        <p class="caption">The Normalizer maps equivalent Unicode to a canonical form (NFKC by default). The Trainer learns the subword model from the normalized corpus. The Encoder normalizes and tokenizes, and the Decoder turns pieces back into normalized text.</p></div>
      <div class="visual" style="margin-top:0"><h3>Vocabulary and ids (§3.3)</h3>
        <p class="caption" style="margin-top:4px">You set the <b>final vocabulary size</b> (<code>--vocab_size</code>) rather than a number of merges, which works for both BPE and unigram. Ids are reserved for meta symbols: <code>&lt;unk&gt;</code>, <code>&lt;s&gt;</code> (BOS), <code>&lt;/s&gt;</code> (EOS), <code>&lt;pad&gt;</code>, plus custom ones such as language tags <code>&lt;2ja&gt;</code> and <code>&lt;2de&gt;</code>.</p></div>
    </div>'''),
        section('s-why', 6, 'Why it works, and where it is used', '''    <div class="grid2">
      <div class="card e"><h3>Lossless by design</h3><p>Whitespace lives inside the tokens, so detokenization is <code>''.join(tokens).replace('▁', ' ')</code>, with no language rules.</p></div>
      <div class="card a"><h3>Language-independent</h3><p>Chinese, Japanese and Korean need no external word segmenter: the model learns pieces from raw characters.</p></div>
      <div class="card b"><h3>Efficient</h3><p>BPE training uses an O(N log N) heap-based algorithm instead of a naive O(N²) one, and unigram training and segmentation are linear in input size (§3.2).</p></div>
      <div class="card c"><h3>Used by LLMs</h3><p>Llama 1 and 2: BPE via SentencePiece, 32K vocabulary, digits split individually, bytes for unknown UTF-8 characters. T5: SentencePiece with a 32,000-wordpiece vocabulary.</p></div>
    </div>
    <div class="cite">Llama 2 paper §2.2 (Tokenizer); T5 paper §3.1.3.</div>'''),
        myths('s-myth', [
            ('SentencePiece is a new segmentation algorithm.', 'It is a <b>library</b> that implements two existing algorithms, BPE and the unigram LM, with raw-text training and lossless detokenization.'),
            ('▁ is just an underscore.', 'It is <b>U+2581</b> (LOWER ONE EIGHTH BLOCK), chosen so it won\'t collide with real underscores in the text.'),
            ('SentencePiece reproduces the exact raw input.', 'It is lossless with respect to the <b>normalized</b> text. NFKC normalization (the default) can change characters, e.g. fullwidth "ＡＢＣ" becomes "ABC" (§3.4).'),
        ]),
        check('s-check', [
            ('mcq', 'Which symbol does SentencePiece use for whitespace?', ['_ (U+005F)', '▁ (U+2581)', '@@', '·'], 1, '<b>▁, U+2581.</b> subword-nmt instead uses @@ as an intra-word boundary marker.'),
            ('mcq', 'What does lossless tokenization guarantee?', ['Encode(text) = text', 'Decode(Encode(Normalize(text))) = Normalize(text)', 'Every token is a word', 'No normalization happens'], 1, '<b>Decode(Encode(Normalize(text))) = Normalize(text)</b> (§3.1).'),
            ('open', 'Why does treating whitespace as a symbol matter for Japanese and Chinese?', 'These languages have no spaces between words, so a tokenizer that assumes space-split input needs an external segmenter, and detokenizing must not add spaces. SentencePiece needs neither.'),
        ]),
    ],
    js=r'''
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
''',
    line='SentencePiece tokenizes raw text in any language: whitespace becomes ▁, BPE or unigram pieces are learned on top, and decoding is exactly lossless on normalized text.',
    explain='Earlier tokenizers assumed space-separated words and relied on language-specific rules to tokenize and detokenize, which breaks for Japanese or Chinese and complicates multilingual models. SentencePiece trains directly on raw sentences: it normalizes with NFKC, escapes spaces as ▁ (U+2581), and learns BPE or unigram pieces. Because whitespace is inside the tokens, decoding is just joining them and restoring spaces, so Decode(Encode(Normalize(text))) equals Normalize(text). Llama 1 and 2 and T5 use it.',
    recap=[('Problem', 'language-specific pre-/post-processing; text without spaces; detokenization that isn\'t reversible.'), ('Core idea', 'a raw-text tokenizer with ▁ for spaces, BPE or unigram inside, and lossless decoding.')],
)
