from tool import section, your_turn, myths, check, mcq

DECKS = {}

# ---------------------------------------------------------------- 01
DECKS['01-sequential-bottleneck'] = dict(
    order=[
        ('html', section('s-p1', 1, 'A sequence model must connect distant words and train fast on a lot of data', '''    <p class="lede">Translation is the paper's test bed. A good model has to do three things at once.</p>
    <div class="grid3">
      <div class="card a"><h3>Relate distant words</h3><p>In "The animal didn't cross the street because it was tired", resolving "it" needs a link across 6 words. Long-range dependencies are "a key challenge in many sequence transduction tasks" (§4).</p></div>
      <div class="card b"><h3>Learn from a lot of data</h3><p>WMT 2014 English-German has about 4.5 million sentence pairs; English-French has 36 million sentences (§5.1). Training speed decides what you can afford to try.</p></div>
      <div class="card c"><h3>Use parallel hardware</h3><p>GPUs run thousands of operations at the same time. Training is only fast if the work can be split across positions.</p></div>
    </div>
    <div class="takeaway">The architecture should make any two positions easy to connect, and let all positions be computed at the same time.</div>''')),
        ('s-rnn', 2), ('s-path', 2),
        ('html', your_turn('s-turn', 'How would you fix both problems?',
            'How would you let "it" use "animal" directly, while computing all 10 positions at the same time?',
            ['Give the RNN a bigger hidden state', 'Run the RNN in both directions (bidirectional)', 'Let every position read every other position directly, weighted by relevance', 'Stack more RNN layers'], 2,
            '<b>C is the paper\'s move.</b> A bigger state (A) or more layers (D) keeps the n-step chain. A bidirectional RNN (B) still needs n sequential steps and long paths in each direction. Only direct position-to-position connections give O(1) sequential operations and O(1) path length (Table 1).')),
        ('s-sa', 4),
        ('html', section('s-how', 5, 'A loop of n dependent steps vs a few matrix products', '''    <p class="lede">The difference shows up directly in code. A recurrent layer is a loop where each step needs the previous one. A self-attention layer is a handful of matrix products over all positions at once.</p>
    <div class="vs">
      <div class="visual" style="margin-top:0"><h3>Recurrent layer</h3><pre class="code">h = h0
for t in range(n):        # n dependent steps
    h = f(h, x[t])        # needs h from step t-1
    out[t] = h</pre></div>
      <div class="visual" style="margin-top:0"><h3>Self-attention layer</h3><pre class="code">Q, K, V = X@Wq, X@Wk, X@Wv  # all n positions
S = Q @ K.T / sqrt(d_k)     # n×n scores: 1 matmul
A = softmax(S, axis=-1)     # each row sums to 1
out = A @ V                 # all n outputs at once</pre></div>
    </div>
    <div class="paper">Every output row depends on <b>all</b> inputs, but no output depends on another output, so the whole layer runs in parallel. Decks 03–05 explain each line.</div>''')),
        ('s-cost', 6), ('s-paper', 6),
        ('html', myths('s-myth', [
            ('Self-attention is always cheaper than a recurrent layer.', 'Per layer, self-attention costs O(n²·d) and recurrence O(n·d²). Self-attention is cheaper only when <b>n &lt; d</b>, which the paper notes is usually true for sentence-level translation. For very long sequences it suggests restricting attention to a neighbourhood of size r (§4).'),
            ('The Transformer has no sequential computation at all.', 'Within a layer, all positions run in parallel. But the 6 layers still run one after another, and <b>generation</b> is still one token at a time (deck 12).'),
            ('RNNs can\'t learn long-range dependencies.', 'They can (LSTMs were the state of the art). The paper\'s argument is that <b>longer paths make it harder</b>: shorter paths between positions make long-range dependencies easier to learn (§4).'),
        ])),
        ('html', check('s-check', [
            ('mcq', 'What is the maximum path length between two positions in a recurrent layer (Table 1)?', ['O(1)', 'O(log n)', 'O(n)', 'O(n²)'], 2, '<b>O(n).</b> Information must pass through every hidden state in between. Self-attention: O(1). See "Distant words are many steps apart".'),
            ('open', 'For n = 50 tokens and d = 512, which layer is cheaper per layer, self-attention or recurrent, and by roughly how much?', 'Self-attention: n²·d = 50² × 512 ≈ 1.3M. Recurrent: n·d² = 50 × 512² ≈ 13.1M. Self-attention is about <b>10× cheaper</b>, because n &lt; d.'),
            ('open', 'Why doesn\'t batching many sentences together fix the RNN bottleneck?', 'Batching parallelizes <em>across</em> sentences, but within each sentence the steps stay sequential, and memory limits how large batches can get for long sequences (§1).'),
        ])),
    ],
    line='Recurrence pushes computation and information through n sequential steps. Self-attention puts every pair of positions one hop apart and computes them all at once.',
    interview='RNNs compute h<sub>t</sub> from h<sub>t−1</sub>, so a layer needs O(n) sequential steps and distant tokens are O(n) hops apart. That makes training slow and long-range dependencies hard to learn. Self-attention connects all positions directly: O(1) sequential operations and O(1) path length per layer, at O(n²·d) cost, which is cheaper than recurrence\'s O(n·d²) when n &lt; d, as in sentence-level translation.',
)

# ---------------------------------------------------------------- 02
DECKS['02-transformer-architecture'] = dict(
    order=[
        ('html', section('s-p1', 1, 'Sequence transduction: read one sequence, write another', '''    <p class="lede">Machine translation maps an input sequence (English) to an output sequence (German) of a different length and word order. The standard design in 2017 was an <b>encoder-decoder</b>: the encoder reads the source, and the decoder writes the target one token at a time.</p>
    <div class="grid3">
      <div class="card a"><h3>Encoder</h3><p>Turns the source tokens (x<sub>1</sub>…x<sub>n</sub>) into a sequence of continuous representations z = (z<sub>1</sub>…z<sub>n</sub>) (§3).</p></div>
      <div class="card c"><h3>Decoder</h3><p>Generates the output y<sub>1</sub>…y<sub>m</sub> one symbol at a time, using z and the symbols it has already produced.</p></div>
      <div class="card b"><h3>How positions talk</h3><p>The open question is how information moves between positions inside each stack. Before this paper: recurrence or convolution, usually with attention added between encoder and decoder.</p></div>
    </div>''')),
        ('s-prob', 2),
        ('html', your_turn('s-turn', 'What would the model need?',
            'Suppose you delete recurrence and convolution entirely. What must the model still have in order to work?',
            ['Nothing else: attention alone is enough', 'A way to mix information across positions, a way to encode word order, and per-position processing', 'Larger embeddings', 'A single convolution at the input'], 1,
            '<b>B.</b> Attention mixes information across positions, but it is blind to order and only averages values. The paper adds <b>positional encodings</b> (order), <b>position-wise feed-forward networks</b> (per-token processing), and residual connections with layer normalization (stable stacking). The title is a slogan; the model is more than attention.')),
        ('html', section('s-core', 4, 'Keep the encoder-decoder; build every layer from attention and feed-forward blocks', '''    <p class="lede">The breakthrough is what is <em>left out</em>: no recurrence and no convolution. Six building blocks do all the work.</p>
    <div class="grid3">
      <div class="card" style="border-top:3px solid var(--b)"><h3>Multi-head self-attention</h3><p>Mixes information between all positions in one step. <a href="../03-self-attention/index.html">Decks 03–06</a></p></div>
      <div class="card" style="border-top:3px solid #3a8fd8"><h3>Position-wise FFN</h3><p>Transforms each token on its own. <a href="../11-position-wise-ffn/index.html">Deck 11</a></p></div>
      <div class="card e"><h3>Add &amp; Norm</h3><p>Residual connection + layer normalization around every sub-layer. <a href="../10-residual-layernorm/index.html">Deck 10</a></p></div>
      <div class="card" style="border-top:3px solid #c9a227"><h3>Positional encoding</h3><p>Injects word order into the embeddings. <a href="../07-positional-encoding/index.html">Deck 07</a></p></div>
      <div class="card c"><h3>Encoder-decoder attention</h3><p>Lets the decoder read the source. <a href="../08-encoder-decoder-attention/index.html">Deck 08</a></p></div>
      <div class="card d"><h3>Masked self-attention</h3><p>Stops the decoder seeing future tokens. <a href="../09-masked-self-attention/index.html">Deck 09</a></p></div>
    </div>''')),
        ('s-fig', 5), ('s-flow', 5), ('s-cfg', 5), ('s-paper', 5),
        ('html', section('s-why', 6, 'Why this design works', '''    <div class="grid2">
      <div class="card a"><h3>Constant path length</h3><p>Any two positions are connected by one attention step in every layer, compared with O(n) for recurrence (Table 1). Long-range dependencies become easier to learn.</p></div>
      <div class="card e"><h3>Parallel training</h3><p>All positions in a layer are computed at once. The decoder stays auto-regressive through masking plus the shifted-right input, yet still trains on every position in parallel.</p></div>
      <div class="card b"><h3>Easy to stack</h3><p>Every sub-layer outputs d<sub>model</sub> = 512, so residual connections can add input to output, and N = 6 identical layers stack cleanly. Table 3 (C): N = 2 gives 23.7 BLEU, N = 6 gives 25.8.</p></div>
      <div class="card c"><h3>Evidence</h3><p>New state of the art on WMT 2014 EN-DE (28.4 BLEU) and EN-FR (41.8) at a fraction of the training cost (Table 2, deck 14).</p></div>
    </div>''')),
        ('html', myths('s-myth', [
            ('The original Transformer is a decoder-only model.', 'The 2017 model is an <b>encoder-decoder</b>: a 6-layer encoder and a 6-layer decoder joined by encoder-decoder attention.'),
            ('Encoder and decoder layers are identical.', 'Encoder layers have 2 sub-layers (self-attention, FFN). Decoder layers have <b>3</b>: masked self-attention, encoder-decoder attention, FFN.'),
            ('The encoder output only feeds the first decoder layer.', '<b>Every</b> decoder layer attends to the final encoder output through its encoder-decoder attention sub-layer.'),
        ])),
        ('html', check('s-check', [
            ('mcq', 'How many sub-layers does each decoder layer have?', ['1', '2', '3', '6'], 2, '<b>3</b>: masked multi-head self-attention, multi-head attention over the encoder output, and the position-wise FFN (§3.1).'),
            ('mcq', 'For an n-token source, what shape leaves the base encoder?', ['n × 64', 'n × 512', 'n × 2048', '512 × 512'], 1, '<b>n × 512.</b> Every sub-layer keeps d<sub>model</sub> = 512. See "Follow one sentence through the model".'),
            ('open', 'Why must every sub-layer output exactly d<sub>model</sub> = 512 dimensions?', 'Because each sub-layer is wrapped as LayerNorm(<b>x + Sublayer(x)</b>): you can only add the input to the output if their shapes match (§3.1).'),
        ])),
    ],
    line='An encoder-decoder built only from attention and position-wise feed-forward sub-layers, each wrapped as LayerNorm(x + Sublayer(x)), stacked 6 deep on each side.',
    interview='The Transformer keeps the encoder-decoder structure but drops recurrence and convolution. Each of the 6 encoder layers has multi-head self-attention and a position-wise FFN; each of the 6 decoder layers adds masked self-attention and attention over the encoder output. Every sub-layer is LayerNorm(x + Sublayer(x)) with d<sub>model</sub> = 512, and sinusoidal positional encodings added to the embeddings provide word order.',
)

# ---------------------------------------------------------------- 03
DECKS['03-self-attention'] = dict(
    order=[
        ('s-prob', 1),
        ('html', section('s-lim', 2, 'Existing ways of adding context are slow, local, or absent', '''    <div class="grid3">
      <div class="card d"><h3>Embedding lookup</h3><p>No context at all: "it" gets the same vector in every sentence.</p></div>
      <div class="card b"><h3>Recurrence</h3><p>Context arrives through a chain of hidden states: n sequential steps, and O(n) hops between distant words (<a href="../01-sequential-bottleneck/index.html">deck 01</a>).</p></div>
      <div class="card c"><h3>Convolution</h3><p>Sees a fixed window of k tokens. Linking distant words needs a stack of O(n/k) layers, or O(log<sub>k</sub> n) with dilated convolutions (§4).</p></div>
    </div>
    <div class="takeaway">What's missing: a way for each word to draw on <b>any</b> other word in the sentence directly, chosen by relevance rather than by distance.</div>''')),
        ('html', your_turn('s-turn', 'How should "it" build a context-aware vector?',
            'Given vectors for every word in the sentence, how should "it" build its new, context-aware vector?',
            ['Average all words equally', 'Copy the previous word\'s vector', 'Take a weighted average, with weights reflecting how relevant each word is to "it"', 'Concatenate all the word vectors'], 2,
            '<b>C is self-attention.</b> An equal average (A) loses which word matters. Copying a neighbour (B) only sees local context. Concatenation (D) makes the vector size depend on sentence length. Relevance weights that sum to 1 give a fixed-size, context-specific mix.')),
        ('s-arcs', 4), ('s-matrix', 5), ('s-paper', 5),
        ('html', section('s-why', 6, 'Why it works', '''    <div class="grid2">
      <div class="card a"><h3>Context-dependent by construction</h3><p>The weights are computed from the actual sentence, so the same word gets different outputs in different contexts ("it" → animal vs street).</p></div>
      <div class="card e"><h3>One hop to anything</h3><p>Every token reaches every other token in a single step, so distance doesn't weaken the connection (path length O(1)).</p></div>
      <div class="card b"><h3>All positions in parallel</h3><p>The whole n × n weight matrix comes out of matrix products, with no step-by-step dependency.</p></div>
      <div class="card c"><h3>Learned, not hand-designed</h3><p>What to attend to is learned from data. The trained model's heads end up tracking real linguistic structure, as the next slide shows.</p></div>
    </div>''')),
        ('s-real', 6),
        ('html', myths('s-myth', [
            ('Attention weights show which words are important in the sentence.', 'They are <b>per-query mixing weights</b> in one head of one layer: how much a given token takes from each other token. Different heads and layers attend differently (Figure 5). They are not a global importance score.'),
            ('Self-attention compares the raw word embeddings directly.', 'It compares learned <b>query and key projections</b> of the embeddings and mixes learned <b>value</b> projections (<a href="../04-queries-keys-values/index.html">deck 04</a>).'),
            ('A token cannot attend to itself.', 'It can and usually does: the diagonal of the attention matrix is typically non-zero. The token\'s own value is part of its mix.'),
        ])),
        ('html', check('s-check', [
            ('mcq', 'In encoder self-attention, where do the queries, keys and values come from?', ['Q from the decoder, K and V from the encoder', 'All three from the output of the previous encoder layer', 'Q from the embeddings, K and V from positional encodings', 'They are fixed, not learned'], 1, '<b>All three from the previous encoder layer</b> (§3.2.3), so each position can attend to all positions of that layer.'),
            ('mcq', 'What does each row of the attention matrix sum to?', ['0', '1', 'n', 'd<sub>model</sub>'], 1, '<b>1</b>, because each row comes from a softmax: it is one token\'s distribution over all tokens.'),
            ('open', '"it" has the same embedding in the "tired" and "wide" sentences. How can self-attention give it different outputs?', 'The weights depend on the <b>other tokens in the sentence</b>: "tired" vs "wide" changes how well "animal" and "street" match "it", so the weighted mix and the output change.'),
        ])),
    ],
    line='Each token\'s new representation is a relevance-weighted average of all tokens in the same sequence, so context changes what a word means.',
    interview='Self-attention lets every position look at every other position of the same sequence. For each token it computes weights over all tokens, summing to 1, and outputs the weighted sum of their value vectors, so "it" can draw mostly from "animal". All positions are computed in parallel with matrix products, and any two tokens are one hop apart.',
)

# ---------------------------------------------------------------- 04
DECKS['04-queries-keys-values'] = dict(
    order=[
        ('s-prob', 1),
        ('html', section('s-lim', 2, 'Scoring with the raw embeddings, x<sub>i</sub>·x<sub>j</sub>, doesn\'t work well', '''    <p class="lede">The simplest idea is to score each pair of tokens by the dot product of their embeddings. Below is that score matrix for the toy embeddings used in this deck.</p>
    <div class="grid2" style="align-items:center">
      <div class="visual" style="margin-top:0"><svg id="limSvg" viewBox="0 0 330 270" role="img" aria-label="Raw embedding dot products"></svg></div>
      <div>
        <div class="card d"><h3>Symmetric</h3><p>x<sub>i</sub>·x<sub>j</sub> = x<sub>j</sub>·x<sub>i</sub>. If "it" looks for "animal", "animal" must look for "it" just as strongly.</p></div>
        <div class="card d" style="margin-top:8px"><h3>Each word matches itself best</h3><p>The diagonal dominates: "it" scores 1.02 with itself and only 0.10 with "animal".</p></div>
        <div class="card d" style="margin-top:8px"><h3>One vector, three jobs</h3><p>What a word is matched on and what it passes on are forced to be the same vector.</p></div>
      </div>
    </div>''')),
        ('html', your_turn('s-turn', 'How would you separate the roles?',
            'How can "it" look for animate things without "animal" having to look for pronouns?',
            ['Keep using x<sub>i</sub>·x<sub>j</sub> but normalize the embeddings', 'Use separate learned projections for asking (query) and for being matched (key)', 'Add positional encodings', 'Use a larger embedding size'], 1,
            '<b>B.</b> With q = xW<sup>Q</sup> and k = xW<sup>K</sup>, the score q<sub>i</sub>·k<sub>j</sub> is no longer symmetric, and each projection can specialize. A third projection, v = xW<sup>V</sup>, separates what is passed on from what is matched. Normalizing (A) keeps the symmetry, and (C) and (D) don\'t separate the roles.')),
        ('s-proj', 4), ('s-match', 5), ('s-matrix', 5), ('s-paper', 5),
        ('html', section('s-why', 6, 'Why separate Q, K and V work', '''    <div class="grid2">
      <div class="card c"><h3>Asymmetric matching</h3><p>q<sub>i</sub>·k<sub>j</sub> ≠ q<sub>j</sub>·k<sub>i</sub> in general, so "it → animal" can be strong while "animal → it" is weak.</p></div>
      <div class="card b"><h3>Specialized roles</h3><p>Keys can expose the features worth matching on (animate, place). Queries can ask for exactly those features.</p></div>
      <div class="card a"><h3>Content decoupled from matching</h3><p>Values carry what is passed on, which can differ from what made the match.</p></div>
      <div class="card e"><h3>The matching does real work</h3><p>Table 3 (B): shrinking the key size d<sub>k</sub> to 16 drops dev BLEU from 25.8 to 25.1. "Determining compatibility is not easy" (§6.2).</p></div>
    </div>''')),
        ('html', myths('s-myth', [
            ('Q, K and V are three different inputs.', 'In <b>self-attention</b> all three are projections of the same input X. Only in encoder-decoder attention do they come from different places (Q from the decoder, K and V from the encoder).'),
            ('Keys and values are the same thing.', 'They come from the same tokens but use different projections. The <b>key</b> decides how much weight a token gets; the <b>value</b> is what actually gets passed on.'),
            ('Attention picks the single best-matching value.', 'It outputs a <b>weighted average</b> of all values. Softmax gives every key some weight; in the toy, "it" still takes 15% from "street".'),
        ])),
        ('html', check('s-check', [
            ('mcq', 'In the base model, what is the shape of one head\'s W<sup>Q</sup>?', ['64 × 64', '512 × 64', '512 × 512', '2048 × 512'], 1, '<b>512 × 64</b>: d<sub>model</sub> × d<sub>k</sub>, with d<sub>k</sub> = 512 / 8 heads (§3.2.2).'),
            ('mcq', 'In encoder-decoder attention, which come from the encoder output?', ['Queries only', 'Keys and values', 'Queries and keys', 'All three'], 1, '<b>Keys and values.</b> Queries come from the decoder (§3.2.3).'),
            ('open', 'In the toy, q(it)·k(animal) is the highest score. Why does "it" still give 15% of its weight to "street"?', 'Softmax never outputs exact zeros for finite scores. Every key gets <b>some</b> weight, in proportion to exp(score / √d<sub>k</sub>).'),
        ])),
    ],
    js='''  const s = document.getElementById('limSvg'), T = ['animal', 'street', 'it', 'tired'];
  const X = [[1, 0, 0, 0.2], [0, 1, 0, 0], [0.1, 0.1, 1, 0], [0.3, 0, 0, 1]];
  TX.heat(s, TX.matMul(X, TX.T(X)), { x: 80, y: 50, cell: 48, rows: T, cols: T, color: 'var(--b)', rotate: true });
  Deck.svg('text', { x: 4, y: 262, class: 'tm', style: 'font-size:11px', text: 'score = x_i · x_j (no projections)' }, s);''',
    line='Queries ask, keys answer, values deliver. softmax(q·k / √d<sub>k</sub>) decides how much of each value a token takes.',
    interview='Each token\'s vector is projected three ways by learned matrices: a query (what it is looking for), a key (what it can be matched on) and a value (what it passes on). Compatibility is the dot product of a query with each key, scaled by 1/√d<sub>k</sub> and softmaxed into weights; the output is the weighted sum of values. Separate projections make matching asymmetric and let content differ from the features used for matching.',
)

# ---------------------------------------------------------------- 05
DECKS['05-scaled-dot-product-attention'] = dict(
    order=[
        ('html', section('s-p1', 1, 'Attention needs a compatibility score for every query-key pair, and it must be fast', '''    <p class="lede">With n tokens, a single head computes <b>n²</b> query-key scores. The base model runs 8 heads in each of its 18 attention sub-layers (6 encoder + 12 decoder), on every training step. Whatever function produces the scores has to be cheap and has to train well.</p>
    <div class="grid3">
      <div class="card d"><h3>n² scores per head</h3><p>A 50-token sentence means 2,500 scores per head per layer.</p></div>
      <div class="card b"><h3>Two known options</h3><p><b>Additive</b> attention (a small feed-forward network per pair) and <b>dot-product</b> attention (q·k) (§3.2.1).</p></div>
      <div class="card a"><h3>Must map to GPUs</h3><p>The fastest operation on a GPU is a large matrix multiply.</p></div>
    </div>''')),
        ('s-why', 2), ('s-prob', 2),
        ('html', your_turn('s-turn', 'Fix the saturation, keep the speed',
            'Dot products of unit-variance vectors have variance d<sub>k</sub>. What is the simplest fix that keeps the matrix-multiply speed?',
            ['Switch to additive attention', 'Divide the scores by d<sub>k</sub>', 'Divide the scores by √d<sub>k</sub>', 'Clip the scores to [−1, 1]'], 2,
            '<b>C.</b> Dividing by √d<sub>k</sub> brings the variance back to exactly 1, whatever d<sub>k</sub> is. Dividing by d<sub>k</sub> (B) shrinks the variance to 1/d<sub>k</sub>, so the softmax becomes nearly uniform. Additive attention (A) is slower in practice, and clipping (D) throws away information and breaks gradients.')),
        ('html', section('s-core', 4, 'Use dot products, and divide them by √d<sub>k</sub>', '''    <div class="eq">Attention(Q, K, V) = softmax( QKᵀ / √d<sub>k</sub> ) V</div>
    <div class="grid3" style="margin-top:14px">
      <div class="card a"><h3>Dot product</h3><p>Every query-key score in one matrix multiply, QKᵀ.</p></div>
      <div class="card e"><h3>÷ √d<sub>k</sub></h3><p>Brings score variance back to about 1, so the softmax stays responsive.</p></div>
      <div class="card b"><h3>softmax, then × V</h3><p>Row-wise weights, then a weighted sum of values: a second matrix multiply.</p></div>
    </div>''')),
        ('s-steps', 5), ('s-paper', 5),
        ('html', section('s-wy', 6, 'Why it works', '''    <div class="grid2">
      <div class="card e"><h3>Variance stays at 1</h3><p>If q and k have independent components with mean 0 and variance 1, q·k has variance d<sub>k</sub> (footnote 4). Dividing by √d<sub>k</sub> brings it back to 1 for any d<sub>k</sub>.</p></div>
      <div class="card a"><h3>Softmax stays in its sensitive range</h3><p>Moderate scores give a soft distribution with useful gradients instead of a one-hot one with "extremely small gradients" (§3.2.1).</p></div>
      <div class="card b"><h3>Hardware-friendly</h3><p>Two matrix multiplies and a softmax: "much faster and more space-efficient in practice" than additive attention.</p></div>
      <div class="card c"><h3>Room for masking</h3><p>Forbidden pairs are handled by writing −∞ into the scores before the softmax (deck 09), with no change to the rest of the computation.</p></div>
    </div>''')),
        ('html', myths('s-myth', [
            ('The √d<sub>k</sub> factor is a learned temperature.', 'It is a <b>fixed constant</b> (√64 = 8 in the base model). Nothing about it is learned.'),
            ('Scaling changes which key gets the most attention.', 'Dividing every score by the same positive number keeps their <b>order</b>. Only the sharpness of the softmax changes.'),
            ('The softmax is taken over the whole score matrix.', 'It is applied <b>row by row</b>: each query gets its own distribution over the keys.'),
        ])),
        ('html', check('s-check', [
            ('mcq', 'In the base model (d<sub>k</sub> = 64), what are the scores divided by?', ['4', '8', '64', '512'], 1, '<b>8</b> = √64.'),
            ('open', 'With unit-variance components and d<sub>k</sub> = 64, what is the standard deviation of an unscaled dot product q·k?', '√64 = <b>8</b>. Variance is d<sub>k</sub> = 64 (footnote 4), so scores routinely reach ±8 to ±16, enough to saturate a softmax.'),
            ('mcq', 'For n queries and m keys, what is the shape of softmax(QKᵀ/√d<sub>k</sub>)?', ['n × n', 'n × m', 'm × d<sub>v</sub>', 'n × d<sub>k</sub>'], 1, '<b>n × m</b>: one row of weights over the m keys for each query. Multiplying by V (m × d<sub>v</sub>) gives an n × d<sub>v</sub> output.'),
        ])),
    ],
    line='Score with dot products, divide by √d<sub>k</sub> to keep the variance at 1, softmax each row, and take the weighted sum of V: two matrix multiplies and a softmax.',
    interview='Scaled dot-product attention computes softmax(QKᵀ/√d<sub>k</sub>)V. Dot products are fast because they are a matrix multiply, but with unit-variance components q·k has variance d<sub>k</sub>, so large d<sub>k</sub> pushes the softmax toward one-hot and its gradients vanish. Dividing by √d<sub>k</sub> restores unit variance. The paper notes that unscaled dot-product attention underperforms additive attention at large d<sub>k</sub>; scaling fixes this while keeping the speed.',
)

# ---------------------------------------------------------------- 06
DECKS['06-multi-head-attention'] = dict(
    order=[
        ('html', section('s-p1', 1, 'A word relates to other words in several ways at once', '''    <p class="lede">To understand "it" in <i>"The animal didn't cross the street because it was tired"</i>, a model needs several different relationships at the same time.</p>
    <div class="grid2">
      <div class="card a"><h3>Reference</h3><p>What does "it" refer to? → "animal"</p></div>
      <div class="card b"><h3>Predicate</h3><p>What is said about it? → "was tired"</p></div>
      <div class="card c"><h3>Local syntax</h3><p>Neighbouring words such as "because" and "was".</p></div>
      <div class="card e"><h3>Long-distance structure</h3><p>In the paper\'s Figure 3, "making" links to the distant "more difficult".</p></div>
    </div>''')),
        ('s-prob', 2),
        ('html', your_turn('s-turn', 'Several relationships, same budget',
            'How would you capture several relationships per token without multiplying the cost?',
            ['Run h full-width (512-dim) attention layers side by side', 'Split the 512 dimensions into h smaller subspaces and run attention in each', 'Use one head with a larger d<sub>k</sub>', 'Add more layers'], 1,
            '<b>B is multi-head attention.</b> 8 heads × 64 dims cost about as much as one 512-dim head, but give 8 separate attention distributions. Option A would cost about 8× more. A single larger head (C) still has only one distribution, and more layers (D) don\'t give one layer several views.')),
        ('s-arch', 4),
        ('html', section('s-how', 5, 'Shapes through one multi-head attention block (base model)', '''    <div class="visual scroll-x">
      <table class="tbl">
        <tr><th>Step</th><th>Operation</th><th>Shape</th></tr>
        <tr><td>1</td><td>Input X (or Q, K, V sources)</td><td>n × 512</td></tr>
        <tr><td>2</td><td>Per head i: Q<sub>i</sub> = XW<sub>i</sub><sup>Q</sup>, K<sub>i</sub> = XW<sub>i</sub><sup>K</sup>, V<sub>i</sub> = XW<sub>i</sub><sup>V</sup></td><td>n × 64, for each of 8 heads</td></tr>
        <tr><td>3</td><td>Scores Q<sub>i</sub>K<sub>i</sub>ᵀ / √64, softmax by row</td><td>n × n, for each of 8 heads</td></tr>
        <tr><td>4</td><td>head<sub>i</sub> = weights × V<sub>i</sub></td><td>n × 64, for each of 8 heads</td></tr>
        <tr><td>5</td><td>Concat(head<sub>1</sub>, …, head<sub>8</sub>)</td><td>n × 512</td></tr>
        <tr><td>6</td><td>× W<sup>O</sup> (512 × 512)</td><td>n × 512</td></tr>
      </table>
    </div>
    <div class="paper"><b>Parameter check:</b> Q, K, V projections = 3 × 8 × (512 × 64) = 3 × 512² ; W<sup>O</sup> = 512². Total 4 × 512², the same as a single head with full 512-dim projections. That is why the cost is "similar to that of single-head attention with full dimensionality" (§3.2.2).</div>''')),
        ('s-paper', 5), ('s-heads', 6),
        ('html', myths('s-myth', [
            ('8 heads cost 8× as much as one head.', 'Each head works in 64 dims rather than 512, so total computation is <b>about the same</b> as one full-width head (§3.2.2).'),
            ('Each head is assigned a specific job, such as coreference.', 'Nothing is assigned. Heads <b>learn</b> their behaviour from data. The paper observes that many end up doing structure-related tasks (Figures 4–5).'),
            ('The heads\' outputs are averaged together.', 'They are <b>concatenated</b> and then mixed by a learned projection W<sup>O</sup>.'),
        ])),
        ('html', check('s-check', [
            ('mcq', 'In the base model, what is each head\'s d<sub>k</sub>?', ['8', '32', '64', '512'], 2, '<b>64</b> = d<sub>model</sub> / h = 512 / 8.'),
            ('mcq', 'Table 3 (A): how much worse was single-head attention than the best setting?', ['0.1 BLEU', '0.9 BLEU', '3 BLEU', 'No difference'], 1, '<b>0.9 BLEU</b> (24.9 vs 25.8 on the dev set).'),
            ('open', 'Why might 32 heads (d<sub>k</sub> = 16) do worse than 8?', 'Each head becomes too narrow to compute good compatibilities. Row (B) shows smaller d<sub>k</sub> hurts, and §6.2 notes "quality also drops off with too many heads".'),
        ])),
    ],
    line='Split 512 dimensions into 8 heads of 64, let each head attend in its own subspace, then concatenate and mix with W<sup>O</sup>: several relationships for the price of one.',
    interview='One attention head gives a single weighted average per token, which blurs different relationships together. Multi-head attention projects Q, K and V h = 8 times into 64-dimensional subspaces, runs scaled dot-product attention in each in parallel, concatenates the results and applies W<sup>O</sup>. Because each head is smaller, the total cost is similar to one full-width head. In Table 3, one head was 0.9 BLEU worse than eight, and 32 heads also did worse.',
)

# ---------------------------------------------------------------- 07
DECKS['07-positional-encoding'] = dict(
    order=[
        ('html', section('s-p1', 1, 'Word order carries meaning', '''    <div class="grid3">
      <div class="card d"><h3>Who did what</h3><p>"dog bites man" and "man bites dog" use the same words with opposite meanings.</p></div>
      <div class="card b"><h3>Translation reorders</h3><p>German often moves the verb to the end of a clause, so the model must track where each word sits.</p></div>
      <div class="card c"><h3>Relative position matters</h3><p>"not" changes the word right after it; adjectives modify the noun next to them.</p></div>
    </div>
    <div class="takeaway">Any sequence model must know where each token is, and how far apart two tokens are.</div>''')),
        ('s-prob', 2),
        ('html', your_turn('s-turn', 'How would you add order?',
            'Without recurrence or convolution, how would you give the model information about token order?',
            ['Append the raw position number (0, 1, 2, …) as an extra feature', 'Add a vector that encodes the position to each token\'s embedding', 'Sort the tokens alphabetically', 'Use the decoder\'s causal mask'], 1,
            '<b>B.</b> The paper adds a d<sub>model</sub>-dimensional positional encoding to each embedding. A raw integer (A) grows without bound and sits on a very different scale from the other features. Sorting (C) destroys order. The mask (D) exists only in the decoder and only blocks future positions; it doesn\'t say where a token is.')),
        ('s-add', 4), ('s-heat', 5), ('s-rel', 5), ('s-paper', 6),
        ('html', myths('s-myth', [
            ('The positional encoding is concatenated to the embedding.', 'It is <b>added</b>. PE has the same dimension d<sub>model</sub> as the embedding "so that the two can be summed" (§3.5).'),
            ('Positional encodings are added in every layer.', 'They are added once, "at the bottoms of the encoder and decoder stacks" (§3.5). Residual connections carry them upward.'),
            ('Sinusoids were shown to beat learned position embeddings.', 'The two gave <b>nearly identical</b> results (Table 3 E: 25.7 vs 25.8 BLEU). Sinusoids were chosen because they may extrapolate to longer sequences.'),
        ])),
        ('html', check('s-check', [
            ('mcq', 'What range do the PE wavelengths span?', ['1 to 512', '2π to 10000·2π', '0 to 1', '2π to 512·2π'], 1, '<b>A geometric progression from 2π to 10000·2π</b> (§3.5).'),
            ('open', 'What is the positional encoding at position 0?', 'Every even dimension is sin(0) = <b>0</b> and every odd dimension is cos(0) = <b>1</b>.'),
            ('open', 'Without positional encoding, what happens to the encoder\'s per-token outputs if you shuffle the input words?', 'Each word gets <b>exactly the same output</b>, just in a different row order. Self-attention is permutation-invariant (see the "dog bites man" demo).'),
        ])),
    ],
    line='Add a fixed sinusoidal code PE(pos) to every embedding, so attention can tell positions apart and a fixed offset becomes a fixed rotation.',
    interview='Self-attention is permutation-invariant: shuffle the inputs and each token\'s output is unchanged, so it can\'t use word order. The paper adds positional encodings to the input embeddings: sines and cosines whose wavelengths range geometrically from 2π to 10000·2π. For any fixed offset k, PE(pos+k) is a linear function of PE(pos), which the authors hypothesized makes relative positions easy to learn. Learned position embeddings gave nearly identical results; sinusoids were kept because they may extrapolate to longer sequences.',
)
