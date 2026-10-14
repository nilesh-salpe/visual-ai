"""Per-deck extras for the Tokenization guide. Token counts come from tokenization/data/examples.js (generated
with tiktoken); the BPE example is computed by running BPE below."""
import collections, html, json, os
from papers import PAPERS as P, paper, arxiv

_raw = open(os.path.join(os.path.dirname(__file__), '..', '..', 'tokenization', 'data', 'examples.js')).read()
TOK = json.loads(_raw[_raw.index('{'):_raw.rindex('}') + 1])
n = lambda key, enc: len(TOK['x'][key][enc])

P = dict(P)
P.update(
    kudo=paper('Subword Regularization: Improving Neural Network Translation Models with Multiple Subword Candidates', 'Kudo', 'ACL', 2018, arxiv('1804.10959'),
               'Introduces the unigram language-model tokenizer and trains on sampled segmentations for robustness.', 'consistent gains, especially low-resource and out-of-domain'),
    sentencepiece=paper('SentencePiece: A simple and language independent subword tokenizer and detokenizer for Neural Text Processing', 'Kudo & Richardson', 'EMNLP (demo)', 2018, arxiv('1808.06226'),
                        'Trains subword models directly from raw sentences (whitespace becomes a symbol), making tokenization lossless and language-independent.', ''),
    bpedrop=paper('BPE-Dropout: Simple and Effective Subword Regularization', 'Provilkov et al.', 'ACL', 2020, arxiv('1910.13267'),
                  'Randomly skips BPE merges during training to expose the model to many segmentations; standard BPE at inference.', 'up to +3 BLEU over BPE'),
    petrov=paper('Language Model Tokenizers Introduce Unfairness Between Languages', 'Petrov et al.', 'NeurIPS', 2023, arxiv('2305.15425'),
                 'The same text translated into different languages can need very different numbers of tokens, which changes cost, latency and context.', 'up to 15× more tokens'),
    fim=paper('Efficient Training of Language Models to Fill in the Middle', 'Bavarian et al.', 'arXiv', 2022, arxiv('2207.14255'),
              'Moves a middle span to the end with special sentinel tokens so a left-to-right model learns infilling, without hurting normal generation.', ''),
    byt5=paper('ByT5: Towards a token-free future with pre-trained byte-to-byte models', 'Xue et al.', 'TACL', 2022, arxiv('2105.13626'),
               'A standard Transformer on raw bytes: no tokenizer, more robust to noise and spelling, at the cost of longer sequences.', ''),
)


def _bpe(corpus, merges):
    vocab = {tuple(w.split()): c for w, c in corpus.items()}
    out = []
    for _ in range(merges):
        pairs = collections.Counter()
        for w, c in vocab.items():
            for a, b in zip(w, w[1:]):
                pairs[(a, b)] += c
        top = max(pairs.values())                       # Sennrich's reference code: first pair (in insertion order) with the top count
        best = next((p, c) for p, c in pairs.items() if c == top)
        out.append((best[0], best[1]))
        new = {}
        for w, c in vocab.items():
            i, nw = 0, []
            while i < len(w):
                if i + 1 < len(w) and (w[i], w[i + 1]) == best[0]:
                    nw.append(w[i] + w[i + 1]); i += 2
                else:
                    nw.append(w[i]); i += 1
            new[tuple(nw)] = c
        vocab = new
    return out, vocab


_corpus = {'l o w </w>': 5, 'l o w e r </w>': 2, 'n e w e s t </w>': 6, 'w i d e s t </w>': 3}
_merges, _final = _bpe(_corpus, 4)

EXTRAS = {}

EXTRAS['01-why-tokenize'] = dict(
    glance=dict(steps=[('raw text', 'any string', 'f'), ('normalize', 'optional (e.g. NFKC)', 'f'), ('pre-tokenize', 'split on spaces, punctuation', 'c'),
                       ('subword model', 'BPE, WordPiece, unigram', 'a'), ('ids', 'integers into the embedding table', 'e')],
                caption='Decoding runs the same pipeline backwards: ids → pieces → text.'),
    example=dict(title='Worked example: one sentence, three tokenizers',
                 setup=f'"{TOK["x"]["s_rare"]["text"]}" tokenized with tiktoken.',
                 steps=[f'GPT-2 (50,257 tokens): <b>{n("s_rare", "gpt2")}</b> tokens; cl100k_base (~100K): <b>{n("s_rare", "cl100k_base")}</b>; o200k_base (~200K): <b>{n("s_rare", "o200k_base")}</b>.',
                        f'The rare compound " Abwasserbehandlungsanlage" alone: {n("w_abw", "gpt2")} / {n("w_abw", "cl100k_base")} / {n("w_abw", "o200k_base")} tokens; the common word " unbelievable" is 1 token in all three.',
                        f'Characters as units would need {len(TOK["x"]["s_rare"]["text"])} positions; whole words would need a vocabulary with every compound and number.',
                        'Subwords sit in between: frequent words stay whole, rare ones split into reusable pieces.'],
                 result='Bigger vocabularies compress better, but every entry costs embedding parameters (deck 07).'),
    traps=dict(tricks=[('Rule of thumb for English.', 'A few characters per token; Llama 3 measured 3.94 characters per token.'),
                       ('Leading spaces matter.', '" hello" and "hello" are different tokens.'),
                       ('Everything is ids.', 'The model sees integers; letters exist only inside the embedding.')],
               traps=[('Counting words as tokens.', 'Token counts and word counts differ, by language and tokenizer.'),
                      ('Assuming one tokenizer per language.', 'Each model family has its own; ids aren\'t portable.'),
                      ('Ignoring the tokenizer in evals.', 'Some failures (spelling, arithmetic) start at tokenization.')]),
    papers=[P['sennrich'], P['gpt2'], P['bert']],
)

EXTRAS['02-bpe-from-scratch'] = dict(
    glance=dict(steps=[('characters', 'words split into symbols\n+ end-of-word marker', 'f'), ('count pairs', 'adjacent symbol pairs × word frequency', 'c'),
                       ('merge the top pair', 'add it to the vocabulary', 'a'), ('repeat', 'until vocabulary size', 'e')],
                loop=(3, 1, 'each merge creates a new symbol'), caption='Training learns an ordered list of merges; encoding replays them in the same order.'),
    example=dict(title='Worked example: the first merges on Sennrich\'s toy corpus',
                 setup='Word counts: low ×5, lower ×2, newest ×6, widest ×3 (each word split into characters plus an end-of-word marker &lt;/w&gt;).',
                 steps=[f'Merge {i + 1}: <b>{html.escape(a)} + {html.escape(b)}</b> → "{html.escape(a + b)}" (pair count {c}).' for i, ((a, b), c) in enumerate(_merges)] +
                       [f'After 4 merges: newest = {html.escape(" · ".join([k for k in _final if "".join(k).startswith("new")][0]))}, widest = {html.escape(" · ".join([k for k in _final if "".join(k).startswith("wid")][0]))}, low = {html.escape(" · ".join([k for k in _final if "".join(k) == "low</w>"][0]))}.'],
                 result='"es", "est" and "est&lt;/w&gt;" come first because newest (×6) + widest (×3) give each 9 occurrences; then "lo" (low ×5 + lower ×2 = 7). Ties go to the first pair found, as in Sennrich\'s reference code.'),
    traps=dict(tricks=[('Vocab size = base symbols + merges.', 'GPT-2: 256 bytes + 50,000 merges + 1 special = 50,257.'),
                       ('Encode by replaying merges in order.', 'Not by greedy longest match.'),
                       ('Counts are weighted by word frequency.', 'A pair in a frequent word counts many times.')],
               traps=[('Greedy longest-match encoding.', 'That is WordPiece-style, and gives different splits than BPE.'),
                      ('Merging across words.', 'Classic BPE never merges across word boundaries.'),
                      ('Ignoring tie-breaking.', 'Different tie rules give different vocabularies.')]),
    papers=[P['sennrich'], P['gpt2']],
)

EXTRAS['03-byte-level-bpe'] = dict(
    glance=dict(steps=[('text', 'any Unicode', 'f'), ('UTF-8 bytes', '1–4 bytes per character', 'c'), ('pre-tokenize', 'regex: no merges across categories', 'b'),
                       ('byte-level BPE', '256 base symbols + merges', 'a'), ('ids', 'never unknown', 'e')],
                caption='Any string can be encoded: in the worst case, one token per byte.'),
    example=dict(title='Worked example: bytes behind the tokens',
                 setup='UTF-8 uses 1 byte for ASCII, 2 for most accented Latin and Cyrillic, 3 for most Asian scripts, 4 for emoji.',
                 steps=[f'"héllo 👋" is {len("héllo 👋".encode())} bytes ({len("héllo 👋")} characters): GPT-2 uses <b>{n("hello_emoji", "gpt2")}</b> tokens, o200k_base <b>{n("hello_emoji", "o200k_base")}</b>.',
                        f'"नमस्ते दुनिया" (Hindi) is {len("नमस्ते दुनिया".encode())} bytes: GPT-2 <b>{n("hindi", "gpt2")}</b> tokens, cl100k_base {n("hindi", "cl100k_base")}, o200k_base <b>{n("hindi", "o200k_base")}</b>.',
                        f'"こんにちは世界。" is {len("こんにちは世界。".encode())} bytes: GPT-2 <b>{n("jp", "gpt2")}</b>, o200k_base <b>{n("jp", "o200k_base")}</b>.',
                        'Some tokens hold only part of a character\'s bytes, which is why decoded pieces can look like garbage until joined.'],
                 result='Byte-level BPE guarantees coverage; how efficient it is depends on how much of each script the merges learned.'),
    traps=dict(tricks=[('Base vocabulary = 256.', 'Every byte value; no unknown token needed.'),
                       ('Pre-tokenization regex.', 'Keeps letters, digits and punctuation from merging together.'),
                       ('Count bytes for worst case.', 'Tokens ≤ UTF-8 bytes.')],
               traps=[('Decoding token by token.', 'A token can end mid-character; decode the joined bytes.'),
                      ('"Byte-level means fair."', 'Coverage is universal, efficiency is not (deck 09).'),
                      ('Character counts as cost.', 'Cost is tokens, which track bytes and merges, not characters.')]),
    papers=[P['gpt2'], P['byt5']],
)

EXTRAS['04-wordpiece-unigram'] = dict(
    glance=dict(steps=[('big seed vocabulary', 'many candidate pieces', 'f'), ('EM', 'estimate piece probabilities', 'c'), ('prune', 'drop pieces that hurt likelihood least', 'b'),
                       ('Viterbi', 'best segmentation per word', 'a')], loop=(2, 1, 'until target size'),
                caption='Unigram LM goes top-down (prune); BPE and WordPiece go bottom-up (merge).'),
    example=dict(title='Worked example: scoring segmentations with a unigram LM',
                 setup='Toy piece probabilities: un 0.10, believ 0.02, able 0.08, unbeliev 0.001, u 0.03, n 0.03, b 0.02.',
                 steps=['Unigram LM probability of a segmentation = product of piece probabilities.',
                        f'un · believ · able: 0.10 × 0.02 × 0.08 = <b>{0.10 * 0.02 * 0.08:.5f}</b>.',
                        f'unbeliev · able: 0.001 × 0.08 = <b>{0.001 * 0.08:.5f}</b>.',
                        f'u · n · believ · able: 0.03 × 0.03 × 0.02 × 0.08 = <b>{0.03 * 0.03 * 0.02 * 0.08:.7f}</b>. Viterbi picks the first.'],
                 result='The unigram model keeps a probability for every segmentation, which also lets you sample alternatives (deck 06).'),
    traps=dict(tricks=[('Unigram: prune down; BPE: merge up.', 'Different directions, similar final sizes.'),
                       ('Viterbi finds the best split.', 'Dynamic programming over positions.'),
                       ('WordPiece marks continuations.', 'BERT\'s "##" prefix means "joins the previous piece".')],
               traps=[('Calling WordPiece = BPE.', 'WordPiece picks merges by likelihood gain, not raw frequency.'),
                      ('Assuming one valid split.', 'Many segmentations exist with the same vocabulary.'),
                      ('Forgetting probabilities are learned.', 'EM re-estimates them as pieces are pruned.')]),
    papers=[P['kudo'], P['gnmt'], P['bert']],
)

EXTRAS['05-sentencepiece'] = dict(
    glance=dict(steps=[('raw sentence', 'no pre-tokenizer', 'f'), ('normalize', 'NFKC by default', 'c'), ('spaces → ▁', 'whitespace is a symbol', 'b'),
                       ('BPE or unigram', 'on the whole stream', 'a'), ('decode', 'join, ▁ → space: lossless', 'e')],
                caption='Language-independent: no hand-written rules for where words start.'),
    example=dict(title='Worked example: lossless round trip',
                 setup='Text: "Hello world." with a unigram SentencePiece model.',
                 steps=['Replace spaces with ▁ and prefix one: "▁Hello▁world."',
                        'Segment the stream, e.g. [▁Hello, ▁world, .].',
                        'Decode: concatenate pieces → "▁Hello▁world." → replace ▁ with a space → " Hello world." → strip the leading space.',
                        'No information about spacing was lost, so detokenization needs no language-specific rules (also works for Japanese or Chinese without spaces).'],
                 result='Treating whitespace as an ordinary symbol is what makes SentencePiece reversible across languages. Llama 2 and T5 use it.'),
    traps=dict(tricks=[('▁ marks a word start.', 'It is U+2581, not an underscore.'),
                       ('One library, two algorithms.', 'SentencePiece implements both BPE and unigram LM.'),
                       ('Byte fallback.', 'Unknown characters become UTF-8 byte tokens (as in Llama 2).')],
               traps=[('Calling SentencePiece an algorithm.', 'It is a toolkit and pipeline; BPE or unigram does the segmentation.'),
                      ('Stripping ▁ incorrectly.', 'Leads to doubled or missing spaces on decode.'),
                      ('Forgetting normalization.', 'NFKC changes some characters before tokenization.')]),
    papers=[P['sentencepiece'], P['kudo'], P['t5']],
)

EXTRAS['06-many-tokenizations'] = dict(
    glance=dict(steps=[('one word', 'many valid splits', 'f'), ('training', 'sample a split each time', 'a'), ('model', 'sees varied segmentations', 'c'),
                       ('inference', 'deterministic best split', 'e')],
                caption='Subword regularization (unigram sampling) and BPE-dropout (skip merges) are training-time only.'),
    example=dict(title='Worked example: BPE-dropout on one word',
                 setup='Learned merges in order: e+s, es+t, l+o, lo+w, n+e, ne+w. Dropout probability p = 0.1 per merge application.',
                 steps=['Normal BPE on "newest": n e w e s t → n e w es t → n e w est → ne w est → new est.',
                        'With dropout, each merge is skipped with probability 0.1; skipping "ne+w" leaves ne · w · est.',
                        f'Probability that all 4 merges apply: 0.9<sup>4</sup> = <b>{0.9 ** 4:.3f}</b>; so about {1 - 0.9 ** 4:.0%} of the time the model sees a different split.',
                        'At inference, use normal BPE (p = 0).'],
                 result='The model learns that "new + est" and "ne + w + est" mean the same, which helped translation by up to +3 BLEU in the paper.'),
    traps=dict(tricks=[('Train with noise, test without.', 'Both methods use deterministic segmentation at inference.'),
                       ('Sampling temperature α.', 'Unigram sampling sharpens or flattens the distribution over splits.'),
                       ('Biggest wins out of domain.', 'And on low-resource pairs.')],
               traps=[('Sampling at inference.', 'It adds noise to outputs with no benefit.'),
                      ('Uniform sampling.', 'Kudo found α = 0 (uniform) hurt; LM-guided sampling helps.'),
                      ('Assuming LLM pretraining uses it.', 'The papers evaluated machine translation; most LLMs tokenize deterministically.')]),
    papers=[P['kudo'], P['bpedrop']],
)

EXTRAS['07-vocabulary-size'] = dict(
    glance=dict(steps=[('bigger vocabulary', 'more merges', 'f'), ('fewer tokens', 'per text', 'a'), ('more context, less compute', 'per document', 'e'),
                       ('more parameters', 'embedding + output head', 'd')],
                caption='Compression buys context and effective data; every entry costs 2·d parameters with untied embeddings.'),
    example=dict(title='Worked example: the parameter bill vs the compression gain',
                 setup='Llama 3 moved from 32K to 128,256 tokens with d = 4,096 (8B model, untied input and output matrices).',
                 steps=[f'Embedding + output head at 32,000: 2 × 32,000 × 4,096 = <b>{2 * 32000 * 4096 / 1e9:.2f}B</b>.',
                        f'At 128,256: 2 × 128,256 × 4,096 = <b>{2 * 128256 * 4096 / 1e9:.2f}B</b> (+{2 * (128256 - 32000) * 4096 / 1e9:.2f}B).',
                        f'Compression on English: 3.17 → 3.94 characters per token = <b>{3.94 / 3.17 - 1:.0%}</b> more text per token.',
                        f'The same 8K context now holds ≈ {8192 * 3.94:,.0f} characters instead of {8192 * 3.17:,.0f}.'],
                 result='For large models the extra embedding parameters are a small fraction, and the compression gain applies to every token of training and inference.'),
    traps=dict(tricks=[('Embedding params = V × d (× 2 if untied).', 'GPT-2 small: 50,257 × 768 ≈ 38.6M.'),
                       ('Characters per token.', 'The practical compression metric.'),
                       ('Pad V to a multiple of 64 or 128.', 'Helps matmul efficiency.')],
               traps=[('Huge vocabularies in small models.', 'The embedding can dominate the parameter budget.'),
                      ('Rare-token undertraining.', 'Tokens seen rarely in training get poor embeddings.'),
                      ('Comparing perplexity across vocabularies.', 'Per-token losses aren\'t comparable; use bits per byte or per character.')]),
    papers=[P['llama3'], P['llama2'], P['gpt2']],
)

EXTRAS['08-tokenizers-in-llms'] = dict(
    glance=dict(steps=[('normalizer', 'e.g. NFKC or none', 'f'), ('pre-tokenizer', 'regex split', 'c'), ('model', 'merges or pieces + ids', 'a'),
                       ('special tokens', 'reserved ids', 'b'), ('post-processor', 'add BOS, templates', 'e')],
                caption='All four parts must match the ones used in training.'),
    example=dict(title='Worked example: same text, three tokenizers',
                 setup=f'"{TOK["x"]["compare"]["text"]}"',
                 steps=[f'GPT-2: <b>{n("compare", "gpt2")}</b> tokens; cl100k_base: <b>{n("compare", "cl100k_base")}</b>; o200k_base: <b>{n("compare", "o200k_base")}</b>.',
                        f'Code "{TOK["x"]["s_code"]["text"]}": GPT-2 {n("s_code", "gpt2")} tokens vs cl100k_base {n("s_code", "cl100k_base")}: newer vocabularies merge runs of spaces.',
                        f'"12345678": {n("num", "gpt2")} tokens in all three; Llama 2 instead splits every digit (8 tokens).',
                        '<|endoftext|> is id 50256 in GPT-2 and 100257 in cl100k_base: the same string means different ids.'],
                 result='Token counts, digit handling and special ids differ by tokenizer; a model is only correct with its own.'),
    traps=dict(tricks=[('GPT-2: 50,257 = 256 + 50,000 + 1.', 'Bytes + merges + <|endoftext|>.'),
                       ('Llama 2 splits digits.', 'Every number is one token per digit.'),
                       ('Count with the real tokenizer.', 'Estimates from characters can be far off for code and non-English text.')],
               traps=[('Swapping tokenizers.', 'Ids index the embedding table; a different tokenizer scrambles the input.'),
                      ('Special tokens from user text.', 'Literal "<|endoftext|>" in input must not become the special id.'),
                      ('Assuming same family, same tokenizer.', 'Llama 2 (32K SentencePiece) and Llama 3 (128K tiktoken-based) differ.')]),
    papers=[P['gpt2'], P['llama2'], P['llama3'], P['bert'], P['t5']],
)

_ml = {k[3:]: v for k, v in TOK['x'].items() if k.startswith('ml_')}
EXTRAS['09-multilingual-cost'] = dict(
    glance=dict(steps=[('training data mix', 'mostly English', 'f'), ('merges follow data', 'English pieces get long', 'c'), ('other scripts', 'stay split into bytes', 'b'),
                       ('more tokens', 'cost, latency, less context', 'd')],
                caption='Same meaning, different bill: the tokenization premium.'),
    example=dict(title='Worked example: "The weather is nice today" in nine languages',
                 setup='Token counts for the same sentence, from tiktoken.',
                 steps=[f'English: GPT-2 {len(_ml["English"]["gpt2"])}, o200k_base {len(_ml["English"]["o200k_base"])} tokens.',
                        f'Hindi: GPT-2 <b>{len(_ml["Hindi"]["gpt2"])}</b> ({len(_ml["Hindi"]["gpt2"]) / len(_ml["English"]["gpt2"]):.1f}× English); o200k_base <b>{len(_ml["Hindi"]["o200k_base"])}</b>.',
                        f'Russian: GPT-2 <b>{len(_ml["Russian"]["gpt2"])}</b> ({len(_ml["Russian"]["gpt2"]) / len(_ml["English"]["gpt2"]):.1f}×); o200k_base {len(_ml["Russian"]["o200k_base"])}.',
                        f'Worst premium with GPT-2 here: {max(len(v["gpt2"]) for v in _ml.values()) / len(_ml["English"]["gpt2"]):.1f}×; with o200k_base: {max(len(v["o200k_base"]) for v in _ml.values()) / len(_ml["English"]["o200k_base"]):.1f}×.'],
                 result='A larger, more multilingual vocabulary shrinks the premium a lot; Petrov et al. measured gaps of up to 15× across languages.'),
    traps=dict(tricks=[('Premium = tokens(lang) / tokens(English).', 'For the same meaning.'),
                       ('Same window, less text.', 'A 3× premium means a third of the content fits.'),
                       ('Bigger multilingual vocabularies help.', 'Llama 3 added 28K non-English tokens.')],
               traps=[('"Byte-level is fair."', 'Byte and character models still show over 4× differences.'),
                      ('Per-token pricing as equal.', 'Users of some languages pay several times more for the same content.'),
                      ('Judging by one sentence.', 'Measure on a representative corpus per language.')]),
    papers=[P['petrov'], P['byt5'], P['llama3']],
)

EXTRAS['10-tokenization-quirks'] = dict(
    glance=dict(steps=[('characters', 'what people see', 'f'), ('tokens', 'what the model sees', 'c'), ('quirk', 'spelling, digits, spaces, glitch tokens', 'd'),
                       ('fix', 'spell out, healing, digit splitting', 'e')],
                caption='Look at the tokens first when a model fails at something "trivial".'),
    example=dict(title='Worked example: why "how many r\'s in strawberry?" is hard',
                 setup='Real tiktoken output.',
                 steps=[f'"strawberry" (no leading space): <b>{n("straw", "gpt2")} tokens</b> in GPT-2; " strawberry" (with a space): <b>{n("straw_sp", "gpt2")} token</b>.',
                        'The model never sees the letters r-r-r; it sees one or a few ids and must have memorized their spelling.',
                        f'"1234+5678=6912" is {n("arith", "gpt2")} tokens: digits are grouped irregularly, so column-wise arithmetic is misaligned.',
                        f'" SolidGoldMagikarp" is <b>1</b> token in GPT-2 but {n("magikarp", "cl100k_base")} in cl100k_base: a rarely-trained token can behave strangely ("glitch token").'],
                 result='Spelling, counting, arithmetic and odd behaviours often trace back to tokens, not to reasoning.'),
    traps=dict(tricks=[('Spell it out.', 'Ask for letters separated by spaces to get one token per letter.'),
                       ('Token healing.', 'Back up over the prompt\'s last token so generation can choose the natural boundary.'),
                       ('Digit splitting.', 'One token per digit makes arithmetic regular (Llama 2).')],
               traps=[('Prompt ending in a space.', 'Splits a natural token (" word") and biases the next token.'),
                      ('Case and spacing changes.', '"Hello", "HELLO" and " hello" are different tokens.'),
                      ('Blaming reasoning first.', 'Check the tokens before concluding the model "can\'t count".')]),
    papers=[P['gpt2'], P['fim'], P['byt5']],
)
