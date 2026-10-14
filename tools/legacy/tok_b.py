from tool import section, your_turn, myths, check

DECKS = {}
ENC3 = '<div class="seg" id="{id}"><button data-v="gpt2">gpt2</button><button data-v="cl100k_base" class="on">cl100k_base</button><button data-v="o200k_base">o200k_base</button></div>'
ROWS = r'''
  const rows = (key, opts = {}) => Object.keys(TK.ENC).map(enc => { const el = document.createElement('div'); TK.render(el, TK.get(key, enc), opts); return `<div class="tokrow"><div class="lab">${enc}</div>${el.outerHTML}<div class="cnt">${TK.get(key, enc).length}</div></div>`; }).join('');
'''

# =============================================================== 06
DECKS['06-many-tokenizations'] = dict(
    title='Many Tokenizations', h1='One text, many tokenizations',
    sub='The same string can be written as many different token sequences. Subword regularization (Kudo, 2018) and BPE-dropout (Provilkov et al., 2020) turn that ambiguity into training noise that makes models more robust.',
    prob='With one vocabulary, a sentence can be split many ways, and the model treats each split as a completely different input. A deterministic tokenizer only ever shows it one.',
    core='During training, <b>sample</b> a different valid segmentation each time a sentence is used: from a unigram LM, or by randomly dropping BPE merges.',
    slides=[
        section('s-p1', 1, 'Same text, same vocabulary, different ids', '''    <p class="lede">From Kudo (2018), Table 1: five ways to encode "Hello World" with the same vocabulary. To the model these are five unrelated id sequences.</p>
    <div class="visual"><div id="helloRows"></div></div>
    <div class="cite">Kudo 2018, Table 1 (▁ marks a space). The ids are the paper's.</div>'''),
        section('s-lim', 2, 'A deterministic tokenizer hides this from the model', '''    <div class="grid3">
      <div class="card d"><h3>One view of each sentence</h3><p>BPE and Viterbi always pick the same split, so the model never learns that different splits mean the same thing.</p></div>
      <div class="card b"><h3>Brittle to noise</h3><p>Typos, unusual spacing and other domains create splits the model rarely saw. Kudo argues that multiple candidates make a model "robust to noise and segmentation errors".</p></div>
      <div class="card c"><h3>Compositionality left implicit</h3><p>Seeing "books" sometimes as "book" + "s" helps a model learn how words are built (§1).</p></div>
    </div>'''),
        your_turn('s-turn', 'Make the model robust to segmentation',
                  'How could training make a model robust to different segmentations of the same text?',
                  ['Use several tokenizers at inference and vote', 'Sample a different valid segmentation every time a sentence is used in training', 'Use a bigger vocabulary', 'Lowercase everything'], 1,
                  '<b>B.</b> This is data augmentation for text: the content stays the same and only the segmentation changes. Kudo samples from a unigram LM; BPE-dropout randomly skips merges. Inference still uses one deterministic segmentation.'),
        section('s-core', 4, 'Two ways to sample segmentations', '''    <div class="grid2">
      <div class="card e"><h3>Subword regularization (Kudo, 2018)</h3><p>Uses the unigram LM, which can score every segmentation. For each parameter update, sample one segmentation from P(x|X), smoothed by α over the l-best candidates (or all of them, with FFBS).</p></div>
      <div class="card a"><h3>BPE-dropout (Provilkov et al., 2020)</h3><p>Keeps ordinary BPE but, while segmenting training data, randomly <b>drops</b> some merges, so the same word comes out in different splits. Standard BPE is used at inference.</p></div>
    </div>'''),
        section('s-how', 5, 'Subword regularization: sample from the unigram LM <span class="ill">toy probabilities</span>', '''    <p class="lede">P(x<sub>i</sub>|X) ≅ P(x<sub>i</sub>)<sup>α</sup> / Σ<sub>j</sub> P(x<sub>j</sub>)<sup>α</sup> over the l best segmentations. A small α spreads probability over many splits; a large α concentrates it on the Viterbi split.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">α <input type="range" id="srA" min="0" max="1" step="0.05" value="0.2"> <output id="srAo"></output></label>
        <label class="ctl">l (candidates) <input type="range" id="srL" min="1" max="12" step="1" value="8"> <output id="srLo"></output></label>
        <button class="btn primary" id="srS">Sample 6 epochs</button>
      </div>
      <div class="grid2" style="margin-top:12px">
        <div><h3>P(segmentation | "tokenizers")</h3><div id="srBars"></div></div>
        <div><h3>What the model sees, epoch by epoch</h3><div id="srSamples"></div></div>
      </div>
    </div>'''),
        section('s-how2', 5, 'BPE-dropout: randomly skip merges <span class="ill">toy merges</span>', '''    <p class="lede">The merges are learned from a toy corpus (low ×5, lower ×2, newest ×6, widest ×3, lowest ×3). With dropout p, each merge application is skipped with probability p. p = 0 is ordinary BPE, and a larger p gives finer, more varied splits.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">dropout p <input type="range" id="bdP" min="0" max="0.6" step="0.05" value="0.1"> <output id="bdPo"></output></label>
        <button class="btn primary" id="bdS">Resample</button>
      </div>
      <div id="bdOut" style="margin-top:12px"></div>
    </div>'''),
        section('s-why', 6, 'Why it works, and the measured gains', '''    <div class="grid2">
      <div class="card e"><h3>Data augmentation</h3><p>Each sentence is seen under many segmentations, much like random crops and flips for images, which the paper uses as its own analogy.</p></div>
      <div class="card a"><h3>Reversible, so usable on both sides</h3><p>Segmentation can be undone exactly, so it can be applied to source <em>and</em> target. Table 6 shows both sides together beat either side alone.</p></div>
      <div class="card b"><h3>Realistic noise</h3><p>Sampling guided by the LM beats uniform sampling: α = 0 (uniform) hurt BLEU (Kudo §5.5).</p></div>
      <div class="card c"><h3>Results (machine translation)</h3><p>Subword regularization: about +1 to 2 BLEU on most pairs, and +2 or more out of domain (Kudo). BPE-dropout: up to <b>+3 BLEU</b> over BPE and up to <b>+0.9</b> over subword regularization (Provilkov et al.).</p></div>
    </div>
    <div class="paper"><b>Scope note:</b> both papers evaluate machine translation. The LLM tokenizers covered in this guide (GPT-2/tiktoken, Llama 2, Llama 3) are documented as deterministic BPE, and their papers don\'t describe stochastic segmentation during pretraining.</div>'''),
        myths('s-myth', [
            ('Sampling happens at inference too.', 'It is a <b>training-time</b> regularizer. Kudo decodes from the best (or n-best) segmentation, and BPE-dropout uses standard BPE at inference.'),
            ('BPE can only ever produce one segmentation.', 'Standard BPE is deterministic, but <b>BPE-dropout</b> makes it stochastic by randomly skipping merges during training.'),
            ('Fully random segmentation is the best noise.', 'Kudo found α = 0 (uniform sampling, ignoring the LM) <b>hurt</b> performance. Noise that resembles real segmentation variation works better.'),
        ]),
        check('s-check', [
            ('mcq', 'Which method needs a unigram language model?', ['BPE-dropout', 'Subword regularization (Kudo)', 'Byte-level BPE', 'WordPiece'], 1, '<b>Subword regularization</b> samples from P(x|X), which the unigram LM provides. BPE-dropout works with ordinary BPE.'),
            ('mcq', 'What does a larger α do in Kudo\'s sampling?', ['Makes sampling more uniform', 'Concentrates samples on the Viterbi (best) segmentation', 'Increases vocabulary size', 'Disables sampling'], 1, 'A larger α moves toward the <b>Viterbi</b> segmentation; a smaller α moves toward uniform.'),
            ('open', 'Why does it matter that segmentation is reversible?', 'Because the original text can always be recovered, the noise can be applied to the <b>target</b> side as well as the input, which Kudo shows helps (Table 6).'),
        ]),
    ],
    js=r'''
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
''',
    line='A sentence has many valid tokenizations. Sampling them during training, via subword regularization or BPE-dropout, acts as data augmentation and makes models more robust.',
    explain='With a fixed vocabulary, the same text can be split many ways, and each split is a different id sequence to the model. Kudo\'s subword regularization samples a segmentation from a unigram LM, smoothed by α, every time a sentence is used in training. BPE-dropout does the same with ordinary BPE by randomly skipping merges. Both are training-time only and use deterministic segmentation at inference. They gave +1 to 3 BLEU in machine translation, with larger gains out of domain.',
    recap=[('Problem', 'deterministic tokenization shows one split of each sentence, which makes models brittle to segmentation variation.'), ('Core idea', 'sample segmentations during training (unigram LM with α, or BPE with dropped merges).')],
)

# =============================================================== 07
DECKS['07-vocabulary-size'] = dict(
    title='Vocabulary Size', h1='Vocabulary size trade-offs',
    sub='How many tokens should a vocabulary have? Bigger vocabularies make sequences shorter but add parameters, and the benefit depends heavily on the language.',
    prob='The vocabulary size V sets sequence length, embedding and output-layer size, and how well each language is covered, all at once.',
    core='Choose V to balance <b>compression</b> (characters per token) against <b>parameters</b> (V × d), and measure it on the languages you care about.',
    slides=[
        section('s-p1', 1, 'One number, many consequences', '''    <div class="grid2">
      <div class="card a"><h3>Sequence length</h3><p>Fewer, longer tokens mean shorter sequences: less attention compute and more text in the context window.</p></div>
      <div class="card b"><h3>Parameters</h3><p>The input embedding and the output layer each have V × d weights.</p></div>
      <div class="card c"><h3>Coverage</h3><p>Which languages, scripts and domains get compact tokens depends on what the vocabulary was trained on.</p></div>
      <div class="card e"><h3>Training signal</h3><p>Every token in the vocabulary needs enough training examples to learn a good embedding.</p></div>
    </div>'''),
        section('s-lim', 2, 'Both extremes hurt', '''    <div class="vs">
      <div class="card d"><h3>Too small</h3><p>Text is split into many short tokens: longer sequences, more compute per sentence, and less text per context window, especially for languages the vocabulary under-serves (deck 09).</p></div>
      <div class="card b"><h3>Too large</h3><p>Embedding and output matrices grow with V, and rare tokens get few training updates. Under-trained tokens that are nearly absent from training data can make models misbehave ("glitch tokens", Land &amp; Bartolo 2024; deck 10).</p></div>
    </div>'''),
        your_turn('s-turn', 'What did Llama 3 gain?',
                  'Llama 3 moved from Llama 2\'s 32K-token vocabulary to 128K tokens. What benefit does the paper report?',
                  ['Fewer total parameters', 'Better compression (more characters per token), so the model "reads" more text for the same compute', 'A faster softmax', 'No need for BPE any more'], 1,
                  '<b>B.</b> On a sample of English data, characters per token rose from <b>3.17 to 3.94</b>, which "enables the model to \'read\' more text for the same amount of training compute". Adding 28K non-English tokens also improved compression and downstream performance in those languages (Llama 3 paper, §3.2).'),
        section('s-core', 4, 'Compression vs parameters', '''    <div class="eq">embedding params = V × d &nbsp;&nbsp;(×2 if the output layer isn't tied to the input embedding)</div>
    <div class="eq">tokens for a text ≈ characters ÷ (characters per token)</div>
    <div class="takeaway">A larger V raises characters per token, but with diminishing returns once common words are already single tokens. Its cost in parameters grows linearly.</div>'''),
        section('s-how', 5, 'Measured: does a bigger vocabulary compress better?', '''    <p class="lede">Real token counts from three tiktoken encodings (about 50K, 100K and 200K tokens) on this guide's sample texts: a 408-character English paragraph and one short Hindi sentence.</p>
    <div class="visual">
      <div class="grid2">
        <div><h3>English paragraph: characters per token</h3><div id="enBars"></div></div>
        <div><h3>Hindi sentence: characters per token</h3><div id="hiBars"></div></div>
      </div>
      <p class="readout" id="cmpOut" style="margin-top:10px"></p>
    </div>
    <p class="caption">Measured on two small samples, so this illustrates the trend rather than serving as a benchmark. The Hindi sentence is "आज मौसम अच्छा है।" ("The weather is nice today.").</p>'''),
        section('s-how2', 5, 'The parameter bill', '''    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">Vocabulary V <input type="range" id="vV" min="13" max="18" step="0.05" value="17"> <output id="vVo"></output></label>
        <label class="ctl">Model width d <select id="vD"><option>768</option><option>2048</option><option selected>4096</option><option>8192</option></select></label>
        <label class="ctl">Total model <select id="vT"><option value="1e9">1B</option><option value="8e9" selected>8B</option><option value="70e9">70B</option></select></label>
        <div class="seg" id="vTie"><button data-v="1">tied in/out</button><button data-v="2" class="on">separate in/out</button></div>
      </div>
      <div class="grid3" style="margin-top:14px">
        <div class="stat"><div class="num" id="vPar"></div><div class="lbl">embedding + output parameters</div></div>
        <div class="stat"><div class="num" id="vPct"></div><div class="lbl">share of the total model</div></div>
        <div class="stat"><div class="num" id="vCtx"></div><div class="lbl">English characters per 8K-token context (est.)</div></div>
      </div>
    </div>
    <p class="caption">Characters per token are interpolated from the measured English points (gpt2, cl100k, o200k) and are approximate. Parameter counts are exact arithmetic for the chosen V and d.</p>'''),
        section('s-why', 6, 'Why the trade-off resolves the way it does', '''    <div class="grid2">
      <div class="card e"><h3>Compression buys effective data and context</h3><p>Llama 3: 3.17 → 3.94 characters per token on English lets the model "read" more text for the same compute.</p></div>
      <div class="card a"><h3>Parameters are cheap at scale</h3><p>V × d is a large share of a small model but a small share of a large one. That's why large models can afford 100K–200K vocabularies.</p></div>
      <div class="card b"><h3>Where to spend tokens</h3><p>Llama 3 added 28K tokens for non-English languages, which improved their compression with no effect on English tokenization.</p></div>
      <div class="card c"><h3>Diminishing returns in English</h3><p>On the guide's sample, going from 50K to 200K tokens barely changes English, while the Hindi sentence shrinks from 27 tokens to 5.</p></div>
    </div>'''),
        myths('s-myth', [
            ('A bigger vocabulary is free.', 'Each of the embedding and output matrices has V × d weights. At V = 128,000 and d = 4,096 that is about <b>524M parameters</b> per matrix.'),
            ('Doubling the vocabulary halves the token count.', 'Returns diminish fast. On the English sample: 81 tokens (gpt2) → 79 (cl100k_base) → 79 (o200k_base). Most of the gain lands on under-served languages.'),
            ('Vocabulary size only matters for English text.', 'It matters <b>most</b> for other languages and scripts (Llama 3\'s +28K multilingual tokens; deck 09).'),
        ]),
        check('s-check', [
            ('mcq', 'GPT-2 small has d = 768 and V = 50,257. How many input-embedding parameters is that?', ['≈ 3.9M', '≈ 38.6M', '≈ 386M', '≈ 3.9B'], 1, '50,257 × 768 ≈ <b>38.6M</b>.'),
            ('mcq', 'How is Llama 3\'s 128K vocabulary made up?', ['128K SentencePiece unigram pieces', '100K tiktoken tokens + 28K extra non-English tokens', '32K Llama 2 tokens × 4', 'Bytes only'], 1, '<b>100K tokens from tiktoken plus 28K additional tokens</b> for non-English languages (§3.2).'),
            ('open', 'Why does better compression effectively lengthen the context window?', 'The window is measured in <b>tokens</b>. More characters per token means more text fits into the same number of tokens.'),
        ]),
    ],
    js=r'''
  const cpt = (k, e) => TK.text(k).length / TK.get(k, e).length;
  const V = { gpt2: 50257, cl100k_base: 100277, o200k_base: 200019 };
  Deck.hbars(document.getElementById('enBars'), Object.keys(V).map(e => ({ label: `${e} (${(V[e] / 1000).toFixed(0)}K)`, value: cpt('para', e), color: 'var(--a)', text: cpt('para', e).toFixed(2) + ` (${TK.get('para', e).length} tok)` })), { max: 6 });
  Deck.hbars(document.getElementById('hiBars'), Object.keys(V).map(e => ({ label: `${e} (${(V[e] / 1000).toFixed(0)}K)`, value: cpt('ml_Hindi', e), color: 'var(--b)', text: cpt('ml_Hindi', e).toFixed(2) + ` (${TK.get('ml_Hindi', e).length} tok)` })), { max: 4 });
  document.getElementById('cmpOut').innerHTML = `From 50K to 200K: English improves ${(100 * (cpt('para', 'o200k_base') / cpt('para', 'gpt2') - 1)).toFixed(0)}%, while the Hindi sentence improves ${(cpt('ml_Hindi', 'o200k_base') / cpt('ml_Hindi', 'gpt2')).toFixed(1)}×.`;
  const pts = Object.keys(V).map(e => [Math.log2(V[e]), cpt('para', e)]);
  const interp = lv => { if (lv <= pts[0][0]) return pts[0][1] - (pts[0][0] - lv) * 0.12; for (let i = 1; i < pts.length; i++) if (lv <= pts[i][0]) { const [x0, y0] = pts[i - 1], [x1, y1] = pts[i]; return y0 + (y1 - y0) * (lv - x0) / (x1 - x0); } return pts[pts.length - 1][1]; };
  let tie = 2;
  const vc = () => {
    const lv = Deck.val('vV'), v = Math.round(Math.pow(2, lv)), d = +Deck.val('vD'), T = +Deck.val('vT');
    Deck.out('vVo', fmt(v, 0));
    const p = v * d * tie;
    Deck.out('vPar', fmt(p)); Deck.out('vPct', (100 * p / T).toFixed(1) + '%');
    document.getElementById('vPct').style.color = p / T > .2 ? 'var(--d)' : 'var(--ink)';
    Deck.out('vCtx', '≈ ' + fmt(8192 * interp(lv), 0));
  };
  Deck.seg('vTie', x => { tie = +x; if (document.getElementById('vV')) vc(); });
  Deck.bind(['vV', 'vD', 'vT'], vc);
''',
    line='Vocabulary size trades compression against parameters. Large models can afford 100K–200K tokens, and the extra tokens help non-English text far more than English.',
    explain='Vocabulary size V sets how many characters each token covers and how big the embedding and output layers are (V × d each, unless tied). Too small means long sequences, more compute and less text per context window. Too large adds parameters and rarely seen, under-trained tokens. Llama 3 went from 32K to 128K tokens (100K from tiktoken plus 28K multilingual) and improved English compression from 3.17 to 3.94 characters per token. In my measurements, larger vocabularies mostly help under-served languages.',
    recap=[('Problem', 'V controls sequence length, parameter count and language coverage all at once.'), ('Core idea', 'balance characters per token against V × d, and measure on your target languages.')],
)

# =============================================================== 08
DECKS['08-tokenizers-in-llms'] = dict(
    title='Tokenizers in Real LLMs', h1='Tokenizers in real LLMs',
    sub='What GPT-2, GPT-4, GPT-4o, Llama, BERT and T5 actually use: algorithm, vocabulary size, pre-tokenization rules and special tokens. Every row is checked against the model\'s paper or the tokenizer source.',
    prob='Every model family ships its own tokenizer, so token counts, costs and behaviour differ, and ids mean nothing outside their own model.',
    core='A tokenizer is part of the model: a vocabulary (merges or scored pieces), a pre-tokenization rule, normalization, and special tokens, all frozen at training time.',
    slides=[
        section('s-p1', 1, 'Same text, three tokenizers, three answers', '''    <p class="lede">Real output from three OpenAI encodings on one sentence. Token boundaries, counts and ids all differ.</p>
    <div class="visual"><div id="cmpRows"></div></div>
    <p class="caption">Hover any token for its id. Try your own text in the <a href="../playground/index.html">live playground</a>.</p>'''),
        section('s-lim', 2, 'You can\'t swap a tokenizer after training', '''    <div class="grid3">
      <div class="card d"><h3>Ids index the embeddings</h3><p>Id 1234 is a specific learned row in this model's embedding matrix. In another tokenizer, id 1234 is a different string.</p></div>
      <div class="card b"><h3>Rules are baked in</h3><p>How digits, spaces and code are split determines what patterns the model learned to read.</p></div>
      <div class="card c"><h3>Special tokens are reserved</h3><p>End-of-text, padding and chat-role markers are specific ids the model was trained to treat specially.</p></div>
    </div>'''),
        your_turn('s-turn', 'Mismatched ids',
                  'You feed Llama 3 a prompt tokenized with GPT-4\'s cl100k_base ids. What happens?',
                  ['It works fine, since both use BPE', 'Garbage: each id selects an unrelated embedding row', 'Slightly worse quality', 'It runs faster'], 1,
                  '<b>B.</b> Ids are only meaningful with the tokenizer the model was trained with. Even though Llama 3\'s vocabulary includes 100K tokens taken from tiktoken, its id assignments and its extra 28K tokens are its own. Always use the model\'s own tokenizer.'),
        section('s-core', 4, 'What a tokenizer actually consists of', '''    <div class="grid2">
      <div class="card a"><h3>Vocabulary</h3><p>BPE merge ranks (tiktoken: about 100K–200K byte sequences with ranks), or scored pieces (a SentencePiece unigram model).</p></div>
      <div class="card b"><h3>Pre-tokenization</h3><p>A regex or rule that splits text into chunks before subword merging: words with their leading space, digit groups, punctuation.</p></div>
      <div class="card c"><h3>Normalization</h3><p>Optional Unicode normalization (SentencePiece defaults to NFKC). Byte-level BPE keeps raw bytes.</p></div>
      <div class="card e"><h3>Special tokens</h3><p>Reserved ids for document boundaries, padding, fill-in-the-middle or chat structure, never produced from ordinary text.</p></div>
    </div>'''),
        section('s-how', 5, 'The tokenizers of well-known models', '''    <div class="visual scroll-x">
      <table class="tbl">
        <tr><th>Model</th><th>Algorithm</th><th>Vocabulary</th><th>Notable rules</th><th>Source</th></tr>
        <tr><td>GPT-2</td><td>Byte-level BPE</td><td>50,257</td><td>256 bytes + 50,000 merges + &lt;|endoftext|&gt;; no merges across character categories</td><td>GPT-2 §2.2; tiktoken</td></tr>
        <tr><td>GPT-4 (cl100k_base)</td><td>Byte-level BPE</td><td>100,277 ids</td><td>Numbers split into ≤3-digit groups; FIM special tokens</td><td>tiktoken source</td></tr>
        <tr><td>GPT-4o (o200k_base)</td><td>Byte-level BPE</td><td>200,019 ids</td><td>Different regex and merges; ≤3-digit number groups</td><td>tiktoken source</td></tr>
        <tr><td>Llama 1 / 2</td><td>BPE via SentencePiece</td><td>32K</td><td>Numbers split into <b>individual digits</b>; bytes for unknown UTF-8 characters</td><td>Llama 2 §2.2</td></tr>
        <tr><td>Llama 3</td><td>BPE (tiktoken-based)</td><td>128K</td><td>100K tiktoken tokens + 28K non-English tokens</td><td>Llama 3 §3.2</td></tr>
        <tr><td>BERT</td><td>WordPiece</td><td>30,000</td><td>[CLS] starts every sequence; [SEP] separates segments</td><td>BERT §3</td></tr>
        <tr><td>T5</td><td>SentencePiece (wordpieces)</td><td>32,000</td><td>Shared input/output vocabulary; covers EN, DE, FR, RO</td><td>T5 §3.1.3</td></tr>
      </table>
    </div>
    <p class="caption">"ids" counts include special tokens: tiktoken's n_vocab for cl100k_base is 100,277 and for o200k_base 200,019; the rest of the ids are mergeable byte sequences.</p>'''),
        section('s-how2', 5, 'Number handling differs a lot', '''    <p class="lede">"12345678" tokenized for real. GPT-2's pattern keeps a whole run of digits as one chunk and lets BPE merge it however it learned; cl100k and o200k pre-split numbers into groups of at most 3 digits; Llama 1/2 split every digit.</p>
    <div class="visual"><div id="numRows"></div>
      <div class="tokrow"><div class="lab">Llama 1/2 rule</div><div class="toks">''' + ''.join(f'<span class="tok c{i % 6}">{d}</span>' for i, d in enumerate('12345678')) + '''</div><div class="cnt">8</div></div>
    </div>
    <p class="caption">The Llama row applies the documented rule ("split all numbers into individual digits") rather than running the Llama tokenizer.</p>'''),
        section('s-how3', 5, 'Special tokens are reserved ids, not text', '''    <div class="visual scroll-x">
      <table class="tbl">
        <tr><th>Tokenizer</th><th>Special tokens (id)</th></tr>
        <tr><td>gpt2</td><td><code>&lt;|endoftext|&gt;</code> 50256</td></tr>
        <tr><td>cl100k_base</td><td><code>&lt;|endoftext|&gt;</code> 100257 · <code>&lt;|fim_prefix|&gt;</code> 100258 · <code>&lt;|fim_middle|&gt;</code> 100259 · <code>&lt;|fim_suffix|&gt;</code> 100260 · <code>&lt;|endofprompt|&gt;</code> 100276</td></tr>
        <tr><td>o200k_base</td><td><code>&lt;|endoftext|&gt;</code> 199999 · <code>&lt;|endofprompt|&gt;</code> 200018</td></tr>
        <tr><td>BERT</td><td><code>[CLS]</code>, <code>[SEP]</code></td></tr>
        <tr><td>SentencePiece</td><td><code>&lt;unk&gt;</code>, <code>&lt;s&gt;</code>, <code>&lt;/s&gt;</code>, <code>&lt;pad&gt;</code>, plus user-defined ones such as <code>&lt;2ja&gt;</code></td></tr>
      </table>
    </div>
    <div class="paper"><b>Safety detail:</b> by default, tiktoken's <code>encode()</code> <b>raises an error</b> if ordinary text contains a special-token string such as <code>&lt;|endoftext|&gt;</code> (checked with tiktoken 0.14). This stops user-supplied text from silently turning into a control token.</div>'''),
        section('s-why', 6, 'Why tokenizers differ', '''    <div class="grid2">
      <div class="card a"><h3>Different data</h3><p>Tokenizers are trained on their model's data mix. More code and multilingual text in training produces tokens for those.</p></div>
      <div class="card b"><h3>Different goals</h3><p>Splitting digits individually (Llama) or into groups of three (cl100k/o200k) gives numbers a consistent structure. GPT-2's unbounded digit chunks don't.</p></div>
      <div class="card c"><h3>Different eras</h3><p>Vocabularies grew from about 30K (BERT, T5, Llama 2) to 100K–200K (GPT-4, Llama 3, GPT-4o) as models grew and multilingual use mattered more.</p></div>
      <div class="card e"><h3>Tooling</h3><p>SentencePiece (raw text, ▁) and tiktoken (byte-level BPE, regex pre-split) are the two families most LLMs build on.</p></div>
    </div>'''),
        myths('s-myth', [
            ('Token ids are universal across models.', 'They\'re <b>model-specific</b>. The same id maps to different strings in different tokenizers, and even shared merges get different id assignments.'),
            ('Typing "<|endoftext|>" in a prompt ends the document.', 'Special tokens are <b>reserved ids</b>. With tiktoken\'s defaults the literal string raises an error instead of being encoded as the control token.'),
            ('o200k_base is cl100k_base with more tokens added.', 'It is a <b>separate encoding</b>: its own merge ranks and its own pre-tokenization pattern (tiktoken source).'),
        ]),
        check('s-check', [
            ('mcq', 'How do Llama 1 and 2 tokenize numbers?', ['As whole numbers', 'In groups of up to 3 digits', 'As individual digits', 'As words'], 2, '<b>Individual digits</b> (Llama 2 paper §2.2, same as Llama 1).'),
            ('mcq', 'What is &lt;|endoftext|&gt;\'s id in gpt2?', ['0', '50256', '100257', '199999'], 1, '<b>50256</b>, the last id in GPT-2\'s 50,257-entry vocabulary.'),
            ('open', 'Name the four parts that make up a tokenizer.', 'A <b>vocabulary</b> (merges or scored pieces), a <b>pre-tokenization</b> rule, optional <b>normalization</b>, and <b>special tokens</b>.'),
        ]),
    ],
    js=ROWS + r'''
  document.getElementById('cmpRows').innerHTML = rows('compare', { ids: false });
  document.getElementById('numRows').innerHTML = rows('num', { ids: true });
''',
    line='Each LLM\'s tokenizer (vocabulary, pre-tokenization, normalization and special tokens) is part of the model. Ids, counts and number handling differ between models and don\'t transfer.',
    explain='GPT-2 uses byte-level BPE with 50,257 tokens; GPT-4\'s cl100k_base and GPT-4o\'s o200k_base are larger byte-level BPE encodings that split numbers into groups of up to three digits. Llama 1 and 2 use SentencePiece BPE with 32K tokens and individual digits; Llama 3 uses 128K tokens (100K from tiktoken plus 28K multilingual). BERT uses 30,000 WordPieces and T5 32,000 SentencePiece pieces. Special tokens are reserved ids, and ids only make sense with the model\'s own tokenizer.',
    recap=[('Problem', 'tokenizers differ per model, so counts, costs and ids don\'t transfer.'), ('Core idea', 'tokenizer = vocabulary + pre-tokenization + normalization + special tokens, frozen with the model.')],
)

# =============================================================== 09
DECKS['09-multilingual-cost'] = dict(
    title='Multilingual Cost', h1='The multilingual token tax',
    sub='The same sentence can cost very different numbers of tokens depending on its language, which affects price, latency and how much fits in context (Petrov et al., 2023).',
    prob='Tokenizers trained mostly on English text split other languages, especially non-Latin scripts, into many more tokens.',
    core='Measure the <b>tokenization premium</b> (tokens needed relative to English for the same content) and reduce it with multilingual tokenizer training and vocabulary.',
    slides=[
        section('s-p1', 1, 'Same meaning, different bill', '''    <p class="lede">"The weather is nice today." in nine languages, tokenized for real with GPT-2's tokenizer. Many models charge per token, generate one token at a time, and have a fixed token budget.</p>
    <div class="visual"><div id="p1Bars"></div></div>'''),
        section('s-lim', 2, 'Byte-level coverage isn\'t the same as efficiency', '''    <div class="grid3">
      <div class="card d"><h3>English-heavy training</h3><p>Merges are learned from the tokenizer's training data, so frequent English strings become single tokens and rarer scripts stay split into byte-level pieces.</p></div>
      <div class="card b"><h3>Up to 15× more tokens</h3><p>Petrov et al. found the same text translated into different languages can differ in token length by <b>up to 15×</b>.</p></div>
      <div class="card c"><h3>Bytes aren't fair either</h3><p>Even character- and byte-level models show <b>over 4×</b> differences in encoding length for some language pairs, because scripts use different numbers of bytes per character.</p></div>
    </div>'''),
        your_turn('s-turn', 'Predict the most expensive language',
                  'With GPT-2\'s tokenizer, which of these translations of "The weather is nice today." needs the most tokens?',
                  ['Spanish', 'German', 'Hindi', 'Chinese'], 2,
                  '<b>Hindi: 27 tokens</b>, against 6 for English, 10 for Spanish, 11 for German and 11 for Chinese. Devanagari takes 3 bytes per character in UTF-8, and GPT-2\'s merges rarely cover it, so most tokens are single bytes or short byte pieces.'),
        section('s-core', 4, 'The tokenization premium', '''    <div class="eq">premium(L) = tokens(text in L) ÷ tokens(same text in English)</div>
    <div class="grid3" style="margin-top:14px">
      <div class="card d"><h3>Cost</h3><p>Pay-per-token APIs charge the premium directly.</p></div>
      <div class="card b"><h3>Latency</h3><p>Generation is one token per step, so more tokens means slower responses.</p></div>
      <div class="card c"><h3>Context</h3><p>A fixed token window holds less content.</p></div>
    </div>
    <div class="cite">Petrov et al. (NeurIPS 2023) argue these disparities lead to unequal cost, latency and context room, and recommend multilingually fair tokenizers.</div>'''),
        section('s-how', 5, 'Explore the premium by tokenizer', '''    <div class="visual">
      ''' + ENC3.format(id='mlEnc') + '''
      <div id="mlBars" style="margin-top:12px"></div>
      <p class="readout" id="mlOut" style="margin-top:8px"></p>
    </div>
    <p class="caption">Measured on one short sentence per language, so it illustrates the effect rather than measuring it. Petrov et al. use large parallel corpora.</p>'''),
        section('s-how2', 5, 'How much fits in the same context window?', '''    <div class="visual">
      <div class="controls" style="margin-top:0">''' + ENC3.format(id='cxEnc') + '''
        <label class="ctl">Context window <select id="cxW"><option value="4096">4K</option><option value="8192" selected>8K</option><option value="32768">32K</option><option value="131072">128K</option></select></label>
      </div>
      <div id="cxBars" style="margin-top:12px"></div>
    </div>
    <p class="caption">Copies of the sample sentence that fit in the window, estimated as window ÷ tokens per sentence.</p>'''),
        section('s-why', 6, 'Why it happens, and what reduces it', '''    <div class="grid2">
      <div class="card d"><h3>Merges follow the data</h3><p>BPE merges the most frequent pairs in its training data. If most of that data is English, most merges serve English.</p></div>
      <div class="card b"><h3>Scripts cost different numbers of bytes</h3><p>UTF-8 uses 1 byte per ASCII character but 2–3 for many other scripts, so byte-level fallback is uneven.</p></div>
      <div class="card e"><h3>Fix: multilingual vocabulary</h3><p>Llama 3 added 28K non-English tokens, improving compression and downstream performance with no effect on English. In this sample, o200k_base brings every language to 5–6 tokens.</p></div>
      <div class="card a"><h3>Fix: balanced tokenizer training</h3><p>Train the tokenizer on balanced multilingual data and target parity, as Petrov et al. recommend.</p></div>
    </div>'''),
        myths('s-myth', [
            ('Byte-level BPE treats all languages equally.', 'It guarantees <b>coverage</b>, not efficiency. Petrov et al. found even byte-level models differ by over 4× across some language pairs.'),
            ('The premium is only about price.', 'It also means <b>higher latency</b> (more decoding steps) and <b>less usable context</b> for the same content.'),
            ('A language\'s premium is a fixed property of the language.', 'It depends on the <b>tokenizer</b>: the Hindi sample costs 27 tokens with gpt2, 21 with cl100k_base and 5 with o200k_base.'),
        ]),
        check('s-check', [
            ('mcq', 'What maximum disparity did Petrov et al. report?', ['1.5×', '4×', 'Up to 15×', '100×'], 2, '<b>Up to 15×</b> more tokens for the same text in some languages.'),
            ('open', 'Using this guide\'s sample, what is Hindi\'s premium in gpt2 (27 tokens vs 6 for English)?', '27 ÷ 6 = <b>4.5×</b>. With o200k_base it is 5 ÷ 6 ≈ 0.8×, slightly <em>fewer</em> tokens than English on this one sentence.'),
            ('open', 'Give two consequences of a high tokenization premium besides price.', '<b>Higher latency</b> (more tokens to generate) and <b>less content per context window</b>.'),
        ]),
    ],
    js=r'''
  const L = TOK.ml, en = e => TK.get('ml_English', e).length;
  const bars = (el, enc) => Deck.hbars(el, L.map(l => { const n = TK.get('ml_' + l, enc).length; return { label: `${l} <span style="color:var(--faint)">${TK.esc(TK.text('ml_' + l))}</span>`, value: n, color: l === 'English' ? 'var(--faint)' : n / en(enc) > 2 ? 'var(--d)' : n / en(enc) > 1.3 ? 'var(--b)' : 'var(--e)', text: `${n} tok · ${(n / en(enc)).toFixed(1)}×` }; }), { max: 28 });
  bars(document.getElementById('p1Bars'), 'gpt2');
  Deck.seg('mlEnc', enc => {
    bars(document.getElementById('mlBars'), enc);
    const pr = L.map(l => TK.get('ml_' + l, enc).length / en(enc)), mx = Math.max(...pr), worst = L[pr.indexOf(mx)];
    document.getElementById('mlOut').innerHTML = `${enc}: highest premium is <b>${worst} at ${mx.toFixed(1)}×</b> English.`;
  });
  let cxe = 'cl100k_base';
  const cx = () => { const w = +Deck.val('cxW'); Deck.hbars(document.getElementById('cxBars'), L.map(l => { const n = TK.get('ml_' + l, cxe).length, k = Math.floor(w / n); return { label: l, value: k, color: l === 'English' ? 'var(--a)' : 'var(--c)', text: fmt(k, 0) + ' sentences' }; })); };
  Deck.seg('cxEnc', e => { cxe = e; if (document.getElementById('cxW')) cx(); });
  Deck.bind(['cxW'], cx);
''',
    line='The same content can cost several times more tokens outside English. That premium is set by the tokenizer, and it shows up as price, latency and lost context.',
    explain='Tokenizers learn merges from their training data, so English-heavy data gives English compact tokens while other scripts fall back to byte pieces. Petrov et al. found up to 15× differences in token count for the same text, which means higher cost, slower generation and less content per context window. The premium depends on the tokenizer: in this guide\'s Hindi sample it drops from 27 tokens (gpt2) to 5 (o200k_base). Multilingual tokenizer training and vocabulary, like Llama 3\'s extra 28K tokens, reduce it.',
    recap=[('Problem', 'English-centric tokenizers need many more tokens for other languages.'), ('Core idea', 'measure the premium against English and reduce it with multilingual tokenizer data and vocabulary.')],
)

# =============================================================== 10
DECKS['10-tokenization-quirks'] = dict(
    title='Tokenization Quirks', h1='Tokenization quirks in LLMs',
    sub='Letter counting, arithmetic, leading spaces, prompts that end mid-token, and glitch tokens: many odd LLM behaviours become obvious once you look at the tokens.',
    prob='LLMs show surprising failures on tasks that look trivial to people, such as spelling, counting letters, adding numbers, or continuing a prompt that ends in a colon.',
    core='The model sees <b>token ids, not characters</b>. Character-level facts must be learned indirectly, and unusual token boundaries put inputs outside what the model was trained on.',
    slides=[
        section('s-p1', 1, 'Trivial for people, surprisingly hard for models', '''    <div class="grid3">
      <div class="card d"><h3>Spelling and counting letters</h3><p>"How many r's are in strawberry?"</p></div>
      <div class="card b"><h3>Arithmetic</h3><p>Multi-digit numbers arrive in irregular chunks.</p></div>
      <div class="card c"><h3>Prompt endings</h3><p>A trailing space or a cut-off "http:" changes the completion.</p></div>
    </div>'''),
        section('s-lim', 2, 'The model never sees letters', '''    <p class="lede">After tokenization, " strawberry" is a <b>single id</b>. Nothing in that integer says which letters it contains. Any knowledge of its spelling has to be learned indirectly from training data.</p>
    <div class="visual"><div id="limRows"></div></div>'''),
        your_turn('s-turn', 'Why is letter counting hard?',
                  'Why might a model struggle to count the r\'s in "strawberry"?',
                  ['Models can\'t count', 'The model sees one to three tokens, not ten letters', 'The tokenizer deletes the letter r', 'The word never appears in training data'], 1,
                  '<b>B.</b> In cl100k_base, "strawberry" is <code>str|aw|berry</code> (3 tokens) and " strawberry" is a single token. The letters are hidden inside opaque ids, so counting them means recalling each token\'s spelling, which is learned only indirectly.'),
        section('s-core', 4, 'Look at the tokens first', '''    <div class="takeaway">When an LLM fails on something character-level, number-level or boundary-sensitive, check how the input was tokenized before blaming "reasoning".</div>
    <div class="grid2" style="margin-top:14px">
      <div class="card a"><h3>Ids hide characters</h3><p>Spelling, rhyme, letter counts and character edits all need knowledge the ids don't carry.</p></div>
      <div class="card b"><h3>Boundaries carry meaning</h3><p>Training text was tokenized greedily, so an unusual split tells the model something it rarely saw, and that something is misleading.</p></div>
    </div>'''),
        section('s-how', 5, 'Quirk explorer: real tokens', '''    <div class="visual">
      <div class="seg" id="qSeg"><button data-v="spell" class="on">Spelling</button><button data-v="num">Numbers</button><button data-v="space">Spaces &amp; case</button><button data-v="boundary">Prompt boundary</button><button data-v="glitch">Glitch tokens</button></div>
      <div id="qRows" style="margin-top:12px"></div>
      <div class="infobox" id="qInfo"></div>
    </div>'''),
        section('s-how2', 5, 'Token healing: fixing prompt boundaries', '''    <p class="lede">The prompt-boundary problem, from the Guidance project's notebook: in training data URLs are tokenized as <code>http</code> + <code>://</code>. A prompt ending in <code>http:</code> ends with a lone <code>:</code> token, which the model almost never saw followed by <code>//</code>. Their example model then produced <code>http: //www…</code>, an invalid URL with a space.</p>
    <div class="visual">
      <div class="steps" id="thSteps"><button data-i="0" class="on">1 · Prompt "http:"</button><button data-i="1">2 · Back up one token</button><button data-i="2">3 · Constrain the next token</button></div>
      <div id="thOut" style="margin-top:12px"></div>
      <div class="infobox" id="thInfo"></div>
    </div>
    <div class="cite">guidance-ai/guidance, "Prompt boundaries and token healing" notebook. Token healing "automatically backs up the generation process by one token before the end of the prompt", then constrains the first generated token to start with the removed text.</div>'''),
        section('s-why', 6, 'Why each quirk happens', '''    <div class="grid2">
      <div class="card a"><h3>Spelling</h3><p>The ids are opaque, so character knowledge exists only to the extent the model learned each token's spelling.</p></div>
      <div class="card b"><h3>Arithmetic</h3><p>Digits come in irregular chunks (gpt2: 123|45|678; cl100k: 123|456|78), so place value isn't aligned across numbers. Llama 1/2 split every digit, and cl100k/o200k cap groups at 3.</p></div>
      <div class="card c"><h3>Spaces and case</h3><p>"hello", " hello" and "Hello" are different ids with separately learned embeddings. Whitespace is part of the token.</p></div>
      <div class="card e"><h3>Glitch tokens</h3><p>The tokenizer is trained separately from the model, so some vocabulary tokens barely appear in model training. Their embeddings stay under-trained and inputs containing them can trigger strange outputs (Land &amp; Bartolo, 2024).</p></div>
    </div>'''),
        myths('s-myth', [
            ('LLMs read text letter by letter.', 'They read <b>token ids</b>. In cl100k_base, " strawberry" is a single id.'),
            ('A trailing space in a prompt is harmless.', 'In GPT-style tokenizers a space usually starts the <b>next</b> token. A trailing space leaves the model with an unusual lone-space token, which changes what it predicts.'),
            ('Every token in the vocabulary was well trained.', 'Some tokens are <b>under-trained</b>: present in the vocabulary but nearly absent from model training. " SolidGoldMagikarp" is the famous example, a single token in GPT-2\'s tokenizer.'),
        ]),
        check('s-check', [
            ('mcq', 'How does cl100k_base tokenize "12345678"?', ['1|2|3|4|5|6|7|8', '123|456|78', '12345678', '1234|5678'], 1, '<b>123|456|78</b>: its pre-tokenizer splits numbers into groups of at most 3 digits.'),
            ('mcq', 'What does token healing do?', ['Fixes typos in the prompt', 'Removes the last prompt token and constrains the next generated token to start with that text', 'Retrains bad tokens', 'Adds spaces'], 1, 'It <b>backs up one token</b> and constrains generation to start with the removed text, so the model can produce its natural token (e.g. "://").'),
            ('open', 'Why do under-trained ("glitch") tokens exist at all?', 'The tokenizer is built <b>separately</b> from model training, on different data, so some vocabulary entries are rare or absent in the model\'s training data and their embeddings are barely trained (Land &amp; Bartolo, 2024).'),
        ]),
    ],
    js=ROWS + r'''
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
''',
    line='LLMs see token ids, not characters. Spelling, arithmetic, spacing and prompt-boundary quirks, and glitch tokens, all follow from how text was tokenized.',
    explain='A model receives token ids, so character-level facts like spelling or letter counts are hidden inside opaque tokens: in cl100k_base, " strawberry" is one id. Numbers are chunked irregularly, leading spaces and capitalization change ids, and a prompt that ends mid-token (like "http:") puts the model at a boundary it rarely saw, which token healing fixes by backing up a token and constraining the next. Some tokens, such as GPT-2\'s " SolidGoldMagikarp", are under-trained because the tokenizer was built on different data from the model.',
    recap=[('Problem', 'surprising failures on character-, number- and boundary-sensitive inputs.'), ('Core idea', 'the model sees ids, not characters; inspect the tokens and fix boundaries (e.g. token healing).')],
)
