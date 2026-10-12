from tool import section, your_turn, myths, check

DECKS = {}

# ---------------------------------------------------------------- 08
DECKS['08-encoder-decoder-attention'] = dict(
    order=[
        ('html', section('s-p1', 1, 'Each output word depends on specific input words', '''    <div class="grid3">
      <div class="card a"><h3>Alignment</h3><p>"Katze" comes from "cat", and "Matte" from "mat". Each target word draws on particular source words.</p></div>
      <div class="card b"><h3>Changing focus</h3><p>The relevant source words change at every step of the output.</p></div>
      <div class="card c"><h3>Different word order</h3><p>Languages order words differently, so the right source word isn't simply "the one at the same position".</p></div>
    </div>
    <div class="takeaway">While writing each target token, the decoder needs flexible access to the relevant parts of the source sentence.</div>''')),
        ('s-prob', 2),
        ('html', your_turn('s-turn', 'Who asks, who answers?',
            'In the attention layer that connects decoder to encoder, where should the queries come from?',
            ['The encoder output', 'The decoder\'s current states', 'Both, alternating by layer', 'Neither: use fixed alignment rules'], 1,
            '<b>B.</b> The decoder is the one looking for information: "which source words do I need right now?" So queries come from the decoder, and the encoder output supplies the <b>keys</b> (what each source word can be matched on) and <b>values</b> (what it contributes).')),
        ('s-wire', 4), ('s-align', 5), ('s-paper', 5),
        ('html', section('s-why', 6, 'Why it works', '''    <div class="grid2">
      <div class="card a"><h3>No bottleneck</h3><p>The source is never squeezed into one vector. Every target position can read all n source vectors.</p></div>
      <div class="card b"><h3>Fresh focus at every position and layer</h3><p>Each target position computes its own weights over the source, and each of the 6 decoder layers can look again with refined queries.</p></div>
      <div class="card c"><h3>Several alignments at once</h3><p>It is multi-head attention, so different heads can track different source relationships.</p></div>
      <div class="card e"><h3>A proven idea, built in</h3><p>It "mimics the typical encoder-decoder attention mechanisms" of earlier seq2seq models (§3.2.3), now as one of three uniform attention uses.</p></div>
    </div>''')),
        ('html', myths('s-myth', [
            ('Encoder-decoder attention is masked like decoder self-attention.', 'It is <b>not</b> masked: every decoder position may attend to <b>all</b> source positions. The source is fully known.'),
            ('Each decoder layer attends to the matching encoder layer (layer 3 to layer 3).', 'All decoder layers attend to the <b>final</b> encoder output (§3.2.3).'),
            ('The attention weights form a hard word-to-word alignment.', 'They are <b>soft</b>: a probability distribution over all source positions, and each head has its own.'),
        ])),
        ('html', check('s-check', [
            ('mcq', 'Which sub-layer of a decoder layer is encoder-decoder attention?', ['First', 'Second', 'Third', 'It sits outside the decoder layers'], 1, '<b>Second</b>: after masked self-attention and before the FFN.'),
            ('open', 'For m target tokens and n source tokens, what is the shape of one head\'s attention-weight matrix?', '<b>m × n</b>: one row per target query, one column per source key.'),
            ('open', 'During generation, does the encoder run again for every new target token?', '<b>No.</b> The source is fixed, so the encoder runs once and its output (the memory) is reused by every decoder pass (deck 12).'),
        ])),
    ],
    line='Queries from the decoder, keys and values from the encoder output: every target position can look at the whole source, in every decoder layer.',
    interview='In encoder-decoder attention, the decoder\'s states provide the queries, and the final encoder output provides the keys and values. Each target position therefore computes a soft alignment over all source positions, in every one of the 6 decoder layers, with multiple heads. It replaces the single fixed context vector of early seq2seq models and is not masked, because the whole source is known.',
)

# ---------------------------------------------------------------- 09
DECKS['09-masked-self-attention'] = dict(
    order=[
        ('html', section('s-p1', 1, 'At inference the model must predict without seeing the future', '''    <div class="grid3">
      <div class="card c"><h3>Generation is left to right</h3><p>When producing token i, tokens i+1, i+2, … don't exist yet.</p></div>
      <div class="card b"><h3>Training should match inference</h3><p>If the model learns to rely on future tokens in training, it fails at test time.</p></div>
      <div class="card a"><h3>But training should be parallel</h3><p>We want to train every target position at the same time (deck 12).</p></div>
    </div>
    <div class="takeaway">How can every position be trained at once while each one only uses what came before it?</div>''')),
        ('s-prob', 2),
        ('html', your_turn('s-turn', 'How would you hide the future?',
            'How can all positions be trained in parallel without any of them seeing future tokens?',
            ['Train one position at a time', 'Set the scores for future positions to −∞ before the softmax', 'Set the attention weights for future positions to 0 after the softmax', 'Reverse the target sentence'], 1,
            '<b>B</b> is what the paper does. Option C sounds close, but zeroing weights <em>after</em> the softmax leaves the rows not summing to 1 (you\'d have to renormalize). Masking with −∞ <em>before</em> the softmax gives exactly 0 weight and a correctly normalized distribution over the visible positions. Option A works but throws away parallelism.')),
        ('s-mask', 4), ('s-num', 5), ('s-paper', 5),
        ('html', section('s-why', 6, 'Why it works', '''    <div class="grid2">
      <div class="card e"><h3>Training sees what inference sees</h3><p>With the mask and the shift-right input, position i depends only on positions &lt; i in the target, exactly the information available when generating.</p></div>
      <div class="card a"><h3>Still fully parallel</h3><p>The mask is just −∞ entries in one n × n matrix, so all positions are still computed in one pass.</p></div>
      <div class="card b"><h3>Exact zeros, proper distribution</h3><p>e<sup>−∞</sup> = 0, so masked positions get exactly 0 weight and each row still sums to 1 over visible positions.</p></div>
      <div class="card c"><h3>Cheap</h3><p>No extra parameters, and only one extra step (Figure 2's optional "Mask") before the softmax.</p></div>
    </div>''')),
        ('html', myths('s-myth', [
            ('The mask is applied to the attention weights after the softmax.', 'It is applied to the <b>scores before the softmax</b>, by setting illegal entries to −∞ (§3.2.3).'),
            ('Masking means the decoder can\'t see the source sentence.', 'Only the decoder\'s <b>self-attention</b> is masked. Encoder-decoder attention sees all source positions.'),
            ('The mask alone stops the model from cheating.', 'You also need the <b>shift-right</b>: without it, position i would still see its own target token. The paper combines both (§3.1).'),
        ])),
        ('html', check('s-check', [
            ('mcq', 'In masked self-attention, position 3 (0-indexed) can attend to which positions?', ['Only 3', '0, 1, 2, 3', '3, 4, 5, …', 'All positions'], 1, '<b>0–3</b>: itself and everything before it.'),
            ('mcq', 'What weight does a masked (−∞) score get after the softmax?', ['A small positive number', 'Exactly 0', '−∞', '1/n'], 1, '<b>Exactly 0</b>, since e<sup>−∞</sup> = 0.'),
            ('open', 'Why is the shift-right needed in addition to the mask?', 'Without it, decoder input position i would hold target token i, the very token it must predict. Shifting right by one (start token first) means position i holds token i−1.'),
        ])),
    ],
    line='Shift the target right and put −∞ above the diagonal: every position trains in parallel, yet only ever sees the past.',
    interview='At inference the decoder generates left to right, so in training a position must not see later tokens. The paper shifts the decoder input right by one and, inside scaled dot-product attention, sets the scores for future positions to −∞ before the softmax, which gives them exactly zero weight. Position i then depends only on positions before i, while all positions are still trained in one parallel pass.',
)

# ---------------------------------------------------------------- 10
DECKS['10-residual-layernorm'] = dict(
    order=[
        ('html', section('s-p1', 1, 'The model is deep: 12 sub-layers in the encoder, 18 in the decoder', '''    <div class="grid3">
      <div class="card a"><h3>Encoder</h3><p>6 layers × 2 sub-layers = 12 transformations in a row.</p></div>
      <div class="card c"><h3>Decoder</h3><p>6 layers × 3 sub-layers = 18 transformations in a row.</p></div>
      <div class="card e"><h3>Depth helps</h3><p>Table 3 (C): N = 2 gives 23.7 dev BLEU, N = 6 gives 25.8.</p></div>
    </div>
    <div class="takeaway">The architecture needs depth, so signals and gradients must pass cleanly through many stacked sub-layers.</div>''')),
        ('s-prob', 2),
        ('html', your_turn('s-turn', 'Make each sub-layer safe to stack',
            'How can each new sub-layer be designed so that, at worst, it does no harm to the signal passing through?',
            ['Initialize all weights to zero', 'Add the input back to the output: x + Sublayer(x)', 'Use fewer layers', 'Use a larger learning rate'], 1,
            '<b>B is a residual connection.</b> The input always has an identity path, so the sub-layer only needs to learn a correction. If that correction is small, the signal passes through nearly unchanged. Zero weights (A) would make all units identical. The paper adds layer normalization after the sum to keep the scale stable.')),
        ('s-wrap', 4), ('s-ln', 5), ('s-paper', 5),
        ('html', section('s-why', 6, 'Why it works', '''    <div class="grid2">
      <div class="card a"><h3>Identity path</h3><p>x reaches the output unchanged, plus a learned correction. Information and gradients have a direct route through the whole stack.</p></div>
      <div class="card e"><h3>Stable scale</h3><p>LayerNorm re-centres and re-scales each token's features after every sub-layer, so activations don't drift with depth.</p></div>
      <div class="card b"><h3>Regularized corrections</h3><p>Dropout on each sub-layer output before the add. Table 3 (D): P<sub>drop</sub> = 0 gives 24.6 BLEU vs 25.8 with 0.1.</p></div>
      <div class="card c"><h3>One width everywhere</h3><p>All sub-layers and embeddings output d<sub>model</sub> = 512, so every residual addition lines up (§3.1).</p></div>
    </div>''')),
        ('html', myths('s-myth', [
            ('Layer normalization normalizes across the batch.', 'It normalizes across the <b>features of one token</b> (its 512 values). Normalizing across the batch is batch normalization, a different technique.'),
            ('The paper applies LayerNorm before each sub-layer.', 'The paper uses <b>LayerNorm(x + Sublayer(x))</b>: normalization comes <b>after</b> the residual addition (§3.1).'),
            ('Residual connections add parameters.', 'The skip path is the <b>identity</b>: no parameters. LayerNorm adds only a gain and bias per feature.'),
        ])),
        ('html', check('s-check', [
            ('mcq', 'What is the output of each sub-layer in the paper?', ['Sublayer(LayerNorm(x))', 'LayerNorm(x + Sublayer(x))', 'x + LayerNorm(Sublayer(x))', 'LayerNorm(Sublayer(x))'], 1, '<b>LayerNorm(x + Sublayer(x))</b> (§3.1), with dropout applied to Sublayer(x) before the addition.'),
            ('mcq', 'Where is residual dropout applied?', ['To the input x', 'To each sub-layer\'s output before it is added and normalized', 'After LayerNorm', 'Only to the attention weights'], 1, '<b>To each sub-layer output before the add &amp; norm</b>, and also to the sums of embeddings and positional encodings (§5.4).'),
            ('open', 'Why must every sub-layer output exactly 512 dimensions?', 'So that x + Sublayer(x) is defined: you can only add vectors of the same size.'),
        ])),
    ],
    line='Wrap every sub-layer as LayerNorm(x + Sublayer(x)): the skip path carries information through, and normalization keeps each token\'s scale stable.',
    interview='Each of the Transformer\'s sub-layers, whether attention or FFN, is wrapped in a residual connection followed by layer normalization: output = LayerNorm(x + Dropout(Sublayer(x))). The identity path lets information and gradients flow through the 12-to-18-sub-layer stacks, so each sub-layer only learns a correction. LayerNorm normalizes each token\'s 512 features to keep activations stable, and all widths are 512 so the additions line up.',
)

# ---------------------------------------------------------------- 11
DECKS['11-position-wise-ffn'] = dict(
    order=[
        ('html', section('s-p1', 1, 'After gathering context, each token needs to compute new features', '''    <div class="grid3">
      <div class="card b"><h3>Attention gathers</h3><p>It decides which tokens to take information from, and how much.</p></div>
      <div class="card a"><h3>Then process it</h3><p>Turning "it + context about the animal" into useful new features is a per-token computation.</p></div>
      <div class="card e"><h3>Non-linearity</h3><p>Rich features need non-linear transformations, layer after layer.</p></div>
    </div>''')),
        ('s-prob', 2),
        ('html', your_turn('s-turn', 'What should process each token?',
            'After attention has mixed context into each token, what should transform each token\'s vector?',
            ['Another attention layer', 'The same small MLP, applied to each position separately', 'A recurrent layer running over the positions', 'Nothing: attention is enough'], 1,
            '<b>B.</b> A position-wise feed-forward network adds a ReLU non-linearity and more capacity per token. Tokens don\'t interact at this step, so it stays fully parallel. Another attention layer (A) mixes tokens again, and an RNN (C) would bring back sequential computation.')),
        ('s-pos', 4), ('s-relu', 5), ('s-paper', 5), ('s-size', 6),
        ('html', myths('s-myth', [
            ('The FFN mixes information between tokens.', 'It is <b>position-wise</b>: each token is transformed on its own. Only the attention sub-layers move information between positions.'),
            ('Each position has its own FFN weights.', 'The weights are <b>shared across positions</b> within a layer, and differ from layer to layer (§3.3).'),
            ('The FFN is a small add-on next to attention.', 'It holds about <b>two-thirds</b> of each encoder layer\'s weights: 2 × 512 × 2048 vs 4 × 512² for attention.'),
        ])),
        ('html', check('s-check', [
            ('mcq', 'What is the FFN\'s inner dimension in the base model?', ['512', '1024', '2048', '4096'], 2, '<b>2048</b> (d<sub>ff</sub>); 4096 in the big model.'),
            ('mcq', 'Which activation does the paper\'s FFN use?', ['Sigmoid', 'tanh', 'ReLU', 'Softmax'], 2, '<b>ReLU</b>: FFN(x) = max(0, xW₁ + b₁)W₂ + b₂.'),
            ('open', 'Why can the FFN be described as "two convolutions with kernel size 1"?', 'A kernel-size-1 convolution applies the <b>same</b> linear map at every position and looks at only that position, which is exactly a shared per-position linear layer.'),
        ])),
    ],
    line='A shared 512 → 2048 → 512 ReLU network transforms each token separately: attention moves information between tokens, and the FFN processes it.',
    interview='Every encoder and decoder layer has a position-wise feed-forward network, FFN(x) = max(0, xW₁ + b₁)W₂ + b₂, with 512 → 2048 → 512 dimensions. The same weights apply at every position, which is equivalent to two kernel-size-1 convolutions, with different weights in each layer. It adds per-token non-linear processing after attention has mixed in context, and holds about two-thirds of each layer\'s parameters. A wider d<sub>ff</sub> improved BLEU in Table 3.',
)

# ---------------------------------------------------------------- 12
DECKS['12-parallel-training-vs-generation'] = dict(
    order=[
        ('s-prob', 1),
        ('html', section('s-lim', 2, 'Two constraints pull in opposite directions', '''    <div class="grid3">
      <div class="card d"><h3>Generation is inherently sequential</h3><p>Token t+1 depends on token t, which doesn't exist until it has been chosen.</p></div>
      <div class="card b"><h3>RNNs copy that structure into training</h3><p>An RNN decoder computes h<sub>t</sub> from h<sub>t−1</sub>, so even with the reference translation available, training takes m dependent steps.</p></div>
      <div class="card c"><h3>Greedy decoding can't recover</h3><p>Choosing only the single most likely token at each step locks in early mistakes.</p></div>
    </div>''')),
        ('html', your_turn('s-turn', 'Use what you know in training',
            'In training you already know the whole reference translation. How can you use that to make training parallel?',
            ['Feed the model its own predictions, one step at a time', 'Feed the reference translation shifted right, with a mask so no position sees the future', 'Predict all target tokens with no decoder input', 'Train only the encoder'], 1,
            '<b>B</b>: teacher forcing plus masking. Every position gets the true previous tokens as input, and the mask hides later ones, so all m predictions come from one forward pass. Option A is sequential again, and C drops the information that each prediction needs.')),
        ('s-train', 4), ('s-gen', 5), ('s-beam', 5), ('s-paper', 5),
        ('html', section('s-why', 6, 'Why it works', '''    <div class="grid2">
      <div class="card e"><h3>The same context in training and at inference</h3><p>Masking plus shift-right means each position conditions only on earlier tokens, just as it will when generating.</p></div>
      <div class="card a"><h3>m loss terms from one pass</h3><p>Every target position contributes to the loss in a single parallel forward and backward pass, so GPUs stay busy.</p></div>
      <div class="card c"><h3>Beam search hedges</h3><p>Keeping 4 hypotheses lets the decoder recover from a locally attractive but globally poor token.</p></div>
      <div class="card b"><h3>Length penalty</h3><p>Summed log-probabilities favour shorter outputs; dividing by lp(Y) with α = 0.6 counters that bias.</p></div>
    </div>''')),
        ('html', myths('s-myth', [
            ('Transformers generate all output tokens at once.', 'Only <b>training</b> is parallel across positions. Generation produces one token per decoder pass (§3: "auto-regressive").'),
            ('Teacher forcing lets the model see the token it is predicting.', 'It sees only the <b>previous</b> reference tokens. Shift-right plus the mask hide the current and future ones.'),
            ('Beam search finds the best possible translation.', 'It is an <b>approximate</b> search that keeps only the 4 best partial hypotheses at each step.'),
        ])),
        ('html', check('s-check', [
            ('mcq', 'Which beam size and length penalty does the paper use for translation?', ['1 and 1.0', '4 and 0.6', '10 and 0.3', '21 and 0.3'], 1, '<b>Beam 4, α = 0.6</b> (§6.1). Beam 21 with α = 0.3 was used for parsing.'),
            ('mcq', 'What is the maximum output length at inference?', ['50 tokens', 'Input length + 50', '2 × input length', 'Unlimited'], 1, '<b>Input length + 50</b>, terminating early when possible.'),
            ('open', 'How many encoder passes and how many decoder passes does it take to generate a 20-token translation?', '<b>1 encoder pass</b> (the source is fixed) and <b>one decoder pass per generated token</b>, about 20 (21 including the end token).'),
        ])),
    ],
    line='Train with the reference shifted right and masked, so all positions train in one pass. Generate one token at a time, with beam search.',
    interview='In training the decoder receives the reference translation shifted right, and masked self-attention stops any position from seeing later tokens, so all m positions are predicted and trained in one parallel pass. At inference the model is auto-regressive: the encoder runs once, then the decoder runs once per output token, feeding each prediction back in. The paper decodes with beam size 4, length penalty α = 0.6, and a maximum length of input + 50.',
)

# ---------------------------------------------------------------- 13
DECKS['13-why-it-works'] = dict(
    order=[
        ('html', section('s-p1', 1, 'Sequence models were slow to train and struggled with long-range structure', '''    <div class="grid3">
      <div class="card d"><h3>Speed</h3><p>Recurrent models need n sequential steps per layer, which limits how much data and how many experiments you can afford.</p></div>
      <div class="card b"><h3>Long-range structure</h3><p>Dependencies between distant words have to cross long paths.</p></div>
      <div class="card c"><h3>Many relationships</h3><p>Reference, syntax and agreement all have to be captured at once.</p></div>
    </div>''')),
        ('s-prob', 2),
        ('html', your_turn('s-turn', 'Patch attention\'s weak spots',
            'Attention alone is order-blind and blurs relationships by averaging. Which two ingredients does the paper add to fix exactly those two problems?',
            ['Positional encoding and multi-head attention', 'Dropout and label smoothing', 'Beam search and checkpoint averaging', 'Byte-pair encoding and a bigger vocabulary'], 0,
            '<b>A.</b> Positional encodings give attention word order (deck 07), and multiple heads counteract the "reduced effective resolution due to averaging" (§2, deck 06). The other options are training or decoding techniques, not fixes to attention itself.')),
        ('s-map', 4),
        ('html', section('s-how', 5, 'How the ingredients fit together in one encoder layer', '''    <div class="visual scroll-x">
      <table class="tbl">
        <tr><th>Step</th><th>Ingredient</th><th>Problem it handles</th><th>Deck</th></tr>
        <tr><td>0</td><td>Embedding × √d<sub>model</sub> + positional encoding</td><td>Order</td><td><a href="../07-positional-encoding/index.html">07</a></td></tr>
        <tr><td>1</td><td>Multi-head self-attention</td><td>Parallel computation, one-hop paths, several relationships</td><td><a href="../03-self-attention/index.html">03</a>–<a href="../06-multi-head-attention/index.html">06</a></td></tr>
        <tr><td>2</td><td>Add &amp; Norm</td><td>Stable signal and gradient flow</td><td><a href="../10-residual-layernorm/index.html">10</a></td></tr>
        <tr><td>3</td><td>Position-wise FFN</td><td>Per-token non-linear processing</td><td><a href="../11-position-wise-ffn/index.html">11</a></td></tr>
        <tr><td>4</td><td>Add &amp; Norm, then repeat × 6</td><td>Depth</td><td><a href="../10-residual-layernorm/index.html">10</a></td></tr>
        <tr><td>Decoder</td><td>+ masked self-attention, + encoder-decoder attention</td><td>Causal generation, reading the source</td><td><a href="../09-masked-self-attention/index.html">09</a>, <a href="../08-encoder-decoder-attention/index.html">08</a></td></tr>
      </table>
    </div>''')),
        ('s-abl', 6), ('s-interp', 6), ('s-paper', 6),
        ('html', myths('s-myth', [
            ('"Attention is all you need" means the model is only attention.', 'The model also depends on <b>position-wise FFNs, residual connections, layer normalization, positional encodings and embeddings</b>. The title means no recurrence and no convolution.'),
            ('In Table 3, bigger is always better.', 'Bigger d<sub>model</sub> and d<sub>ff</sub> helped, but <b>too many heads</b> (h = 32) hurt, and removing dropout hurt (24.6 BLEU).'),
            ('The gains come from one key trick.', 'Table 3 shows <b>many</b> design choices each matter: heads, key size, depth, width, dropout and label smoothing.'),
        ])),
        ('html', check('s-check', [
            ('mcq', 'Table 3 (C): what dev BLEU did N = 2 layers get, against 25.8 for the base model?', ['25.5', '24.9', '23.7', '26.4'], 2, '<b>23.7</b>: depth matters.'),
            ('mcq', 'Learned positional embeddings vs sinusoids (row E)?', ['Much worse', 'Nearly identical (25.7 vs 25.8)', 'Much better', 'Not tested'], 1, '<b>Nearly identical.</b> Sinusoids were kept for possible extrapolation to longer sequences.'),
            ('open', 'Which Table 1 property best explains why long-range dependencies are easier to learn in a Transformer?', '<b>Maximum path length O(1)</b>: any two positions are one attention step apart, compared with O(n) for recurrence.'),
        ])),
    ],
    line='Direct attention for speed and reach, multiple heads for several relationships, positional encoding for order, and residual stacks with FFNs for depth. Table 3 shows each one matters.',
    interview='The Transformer works because each ingredient fixes a specific weakness. Self-attention makes layers fully parallel with O(1) paths between any two tokens. Multiple heads counteract the blurring from averaging. Positional encodings supply the order that attention ignores. Residual connections, layer normalization and position-wise FFNs make a deep stack trainable and expressive. The paper\'s ablations back this up: one head, a smaller d<sub>k</sub>, fewer layers or no dropout all lower BLEU.',
)

# ---------------------------------------------------------------- 14
DECKS['14-experimental-results'] = dict(
    order=[
        ('s-prior', 1),
        ('html', section('s-lim', 2, 'The best systems were ensembles, and they were expensive', '''    <div class="grid3">
      <div class="card d"><h3>Ensembles cost more</h3><p>The best EN-DE result (ConvS2S ensemble, 26.36 BLEU) took 7.7·10¹⁹ training FLOPs; the best EN-FR ensembles took about 10²¹ (Table 2).</p></div>
      <div class="card b"><h3>Small gains</h3><p>On EN-DE, the best single model reached 26.03 (MoE) and the best ensemble only 26.36.</p></div>
      <div class="card c"><h3>Slow to train</h3><p>Recurrent models can't parallelize across positions within a sentence, so every experiment takes longer (deck 01).</p></div>
    </div>''')),
        ('html', your_turn('s-turn', 'Predict the result',
            'The best previous EN-DE result was 26.36 BLEU (an ensemble, 7.7·10¹⁹ FLOPs). What did a single Transformer (big) achieve?',
            ['About 1 BLEU worse, but cheaper', 'About the same BLEU', 'About 2 BLEU better, with about a third of the training FLOPs', '10 BLEU better'], 2,
            '<b>C.</b> 28.4 BLEU (+2.0) with 2.3·10¹⁹ FLOPs, about 0.3× the ConvS2S ensemble\'s cost. Even the <b>base</b> model (27.3 BLEU, 3.3·10¹⁸ FLOPs) beat every earlier model and ensemble.')),
        ('s-table', 4), ('s-cost', 5), ('s-paper', 5),
        ('html', section('s-why', 6, 'Why the results came out this way', '''    <div class="grid2">
      <div class="card e"><h3>Parallel training</h3><p>All positions are processed in each step, so a big model trains in 3.5 days on one 8-GPU machine (decks 01, 12).</p></div>
      <div class="card a"><h3>Short paths</h3><p>Direct connections make long-range dependencies easier to learn (Table 1), which matters for translation quality.</p></div>
      <div class="card b"><h3>Cheap enough to beat ensembles</h3><p>The base model needs 3.3·10¹⁸ FLOPs (12 hours) and still beats ensembles costing up to 10²¹.</p></div>
      <div class="card c"><h3>It generalizes</h3><p>Without task-specific tuning it also did well on English constituency parsing (next slide).</p></div>
    </div>''')),
        ('s-parse', 6),
        ('html', myths('s-myth', [
            ('28.4 BLEU means 28.4% of the translation is correct.', 'BLEU scores n-gram overlap with reference translations on a 0–100 scale. It is a <b>corpus-level similarity score</b>, not a percentage of correct sentences.'),
            ('The training FLOPs in Table 2 were measured.', 'They are <b>estimates</b>: training time × number of GPUs × an assumed sustained TFLOPS per GPU (9.5 for a P100, footnote 5).'),
            ('The Transformer won EN-FR by a large margin.', 'On EN-FR the gain is small: 41.8 vs 41.29 for the ConvS2S ensemble. The big win there is <b>cost</b>: under 1/4 of the previous state of the art\'s training cost (§6.1).'),
        ])),
        ('html', check('s-check', [
            ('mcq', 'What EN-DE BLEU did the base model achieve?', ['25.8', '27.3', '28.4', '41.8'], 1, '<b>27.3</b> on newstest2014 (25.8 is its dev score in Table 3).'),
            ('mcq', 'What hardware did the paper train on?', ['1 TPU pod', '8 NVIDIA P100 GPUs on one machine', '64 K80 GPUs', '16 V100 GPUs'], 1, '<b>One machine with 8 P100 GPUs</b> (§5.2).'),
            ('open', 'Why does this guide report 41.8 for EN-FR when §6.1 says 41.0?', 'The paper is inconsistent: the abstract and Table 2 say <b>41.8</b>, while the §6.1 text says 41.0. The guide uses the table value and notes the mismatch.'),
        ])),
    ],
    line='Better and cheaper: 28.4 BLEU EN-DE (+2.0 over all prior ensembles) and 41.8 EN-FR, for 2.3·10¹⁹ FLOPs on 8 P100 GPUs in 3.5 days.',
    interview='On WMT 2014, the big Transformer reached 28.4 BLEU English-German, more than 2 BLEU above the best previous results including ensembles, and 41.8 English-French, a new single-model state of the art, after 3.5 days of training on 8 P100 GPUs. The paper estimates its training cost at 2.3·10¹⁹ FLOPs, a fraction of what earlier systems used. The base model reached 27.3 in 12 hours. It also transferred to constituency parsing, with 92.7 F1 in the semi-supervised setting.',
)
