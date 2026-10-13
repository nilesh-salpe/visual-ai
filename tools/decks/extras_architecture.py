"""Per-deck extras for the Modern LLM Architecture guide. Numbers are computed here."""
from math import ceil, log, pi, sqrt
from papers import PAPERS as P

GiB, KiB, MiB = 2 ** 30, 2 ** 10, 2 ** 20


def params(V, d, L, H, G, h, tied=False):
    dh = d // H
    return V * d * (1 if tied else 2) + L * (2 * d * d + 2 * d * G * dh + 3 * d * h + 2 * d) + d


EXTRAS = {}

# 01 ------------------------------------------------------------------
_V, _d, _L, _H, _G, _h = 128256, 4096, 32, 32, 8, 14336
_emb, _att, _ffn = 2 * _V * _d, _L * (2 * _d * _d + 2 * _d * _G * (_d // _H)), _L * 3 * _d * _h
_tot = params(_V, _d, _L, _H, _G, _h)
EXTRAS['01-what-changed'] = dict(
    glance=dict(steps=[('token embedding', 'no position vector', 'f'), ('RMSNorm', 'pre-norm', 'e'), ('GQA attention', 'RoPE on q, k\nFlashAttention kernel', 'c'),
                       ('RMSNorm', 'pre-norm', 'e'), ('SwiGLU FFN', 'or MoE experts', 'a'), ('final norm + head', 'logits', 'f')],
                loop=(4, 1, '× L layers, with a residual add after attention and after the FFN'),
                caption='A Llama-style decoder: the 2017 skeleton with the seven swaps in place.'),
    example=dict(title='Worked example: where Llama 3 8B\'s parameters go',
                 setup='From the published config: vocabulary 128,256; d = 4,096; 32 layers; 32 query heads and 8 KV heads of 128; SwiGLU hidden 14,336; untied embeddings.',
                 steps=[f'Embeddings + output head: 2 × 128,256 × 4,096 = <b>{_emb / 1e9:.2f}B</b>.',
                        f'Attention per layer: W_q and W_o (4,096²) + W_k and W_v (4,096 × 1,024) = {(2 * _d * _d + 2 * _d * 1024) / 1e6:.1f}M; × 32 = <b>{_att / 1e9:.2f}B</b>.',
                        f'SwiGLU per layer: 3 × 4,096 × 14,336 = {3 * _d * _h / 1e6:.1f}M; × 32 = <b>{_ffn / 1e9:.2f}B</b>.',
                        f'Norm gains add {2 * _L * _d + _d:,}. Total = <b>{_tot:,}</b>.'],
                 result=f'{_ffn / _tot:.0%} FFN, {_att / _tot:.0%} attention (small thanks to GQA), {_emb / _tot:.0%} embeddings. Reproducing 8.03B from config.json is a quick check that you understand every component.'),
    traps=dict(tricks=[('Read the config, not the name.', 'num_key_value_heads, rope_theta, intermediate_size, hidden_act and tie_word_embeddings tell you the recipe.'),
                       ('Count per layer.', 'Attention ≈ 2d² + 2d·n_kv·d_head; SwiGLU = 3·d·hidden; then × layers + embeddings.'),
                       ('Kernel ≠ architecture.', 'FlashAttention computes the same function; RoPE scaling and sliding windows change it.')],
               traps=[('Assuming every model uses every swap.', 'Llama 2 7B has no GQA; Mixtral uses dense attention over 32K; check each model.'),
                      ('Forgetting untied embeddings.', 'With a 128K vocabulary, input embedding and output head are ~1B parameters together.'),
                      ('Crediting the wrong source.', 'LLaMA credits pre-norm to GPT-3, SwiGLU to PaLM and rotary embeddings to GPT-Neo.')]),
    papers=[P['vaswani'], P['llama'], P['llama3']],
)

# 02 ------------------------------------------------------------------
_x = [1.2, -0.4, 2.1, 0.3]
_mu = sum(_x) / 4
_sd = sqrt(sum((v - _mu) ** 2 for v in _x) / 4)
_rms = sqrt(sum(v * v for v in _x) / 4)
EXTRAS['02-normalization'] = dict(
    glance=dict(steps=[('x (residual stream)', 'never normalized', 'f'), ('RMSNorm', 'x / rms(x) · g', 'e'), ('sub-layer F', 'attention or FFN', 'c'), ('x + F(·)', 'identity path kept', 'a')],
                loop=(3, 0, 'repeat per sub-layer; one final RMSNorm before the output head'),
                caption='Pre-norm: only the copy going into F is normalized.'),
    example=dict(title='Worked example: LayerNorm vs RMSNorm on one token',
                 setup=f'A token with 4 features x = {_x} (gain 1, bias 0).',
                 steps=[f'LayerNorm: mean = {_mu:.3f}, std = {_sd:.3f} → output = (x − mean)/std = <b>[{", ".join(f"{(v - _mu) / _sd:.2f}" for v in _x)}]</b>.',
                        f'RMSNorm: rms = √(mean(x²)) = {_rms:.3f} → output = x/rms = <b>[{", ".join(f"{v / _rms:.2f}" for v in _x)}]</b>.',
                        f'Add 1 to every feature: LayerNorm\'s output is unchanged; RMSNorm\'s becomes [{", ".join(f"{(v + 1) / sqrt(sum((u + 1) ** 2 for u in _x) / 4):.2f}" for v in _x)}].',
                        'Multiply every feature by 10: both outputs are unchanged (re-scaling invariance).'],
                 result='RMSNorm keeps scale invariance and drops shift invariance, with one reduction (sum of squares) instead of two (mean and variance).'),
    traps=dict(tricks=[('Pre-norm = x + F(Norm(x)).', 'Post-norm = Norm(x + F(x)).'),
                       ('Pre-norm needs a final norm.', 'The residual stream grows with depth and is never normalized on the way.'),
                       ('RMSNorm = x / √(mean(x²) + ε) · g.', 'No mean, no bias.')],
               traps=[('Normalizing across the batch.', 'Layer and RMS norms work per token over features, unlike BatchNorm.'),
                      ('Dropping warm-up with post-norm.', 'Post-norm\'s large gradients near the output at initialization need warm-up.'),
                      ('Treating ε as irrelevant.', 'Configs set it (Llama 3: 1e-5); a mismatch changes outputs when porting weights.')]),
    papers=[P['xiong'], P['rmsnorm'], P['gpt2']],
)

# 03 ------------------------------------------------------------------
_d3 = 128
_th = lambda i, b=10000: b ** (-2 * i / _d3)
EXTRAS['03-rope'] = dict(
    glance=dict(steps=[('q, k vectors', 'after W_q and W_k', 'f'), ('split into pairs', 'd/2 two-dim pairs', 'c'), ('rotate pair i', 'by m · θᵢ', 'a'),
                       ('q′ · k′', 'depends only on m − n', 'e')],
                caption='Values are not rotated, and nothing is added to the residual stream.'),
    example=dict(title='Worked example: rotation speeds for d = 128',
                 setup='Head dimension 128 (64 pairs). Wavelength = tokens per full turn = 2π / θᵢ.',
                 steps=[f'Pair 0: θ₀ = 1 rad/token → wavelength <b>{2 * pi / _th(0):.1f} tokens</b>.',
                        f'Pair 32: θ = 10000<sup>−0.5</sup> = {_th(32):.4f} → wavelength <b>{2 * pi / _th(32):,.0f} tokens</b>.',
                        f'Pair 63 (base 10,000): wavelength <b>{2 * pi / _th(63):,.0f} tokens</b>; at position 4,096 it has turned only {4096 * _th(63) / (2 * pi):.2f} of a circle.',
                        f'With Llama 3\'s base 500,000, pair 63\'s wavelength becomes <b>{2 * pi / _th(63, 500000):,.0f} tokens</b>.'],
                 result='Fast pairs separate nearby tokens, slow pairs far ones. Slow pairs that never complete a turn in training are why long-context extension needs care (deck 07).'),
    traps=dict(tricks=[('θᵢ = base^(−2i/d); wavelength = 2π·base^(2i/d).', 'Pair 0 always turns once every ~6.3 tokens.'),
                       ('Rotate keys once.', 'A key\'s rotation depends only on its own position, so it is cached already rotated.'),
                       ('Shift invariance.', 'Adding the same offset to all positions leaves every score unchanged.')],
               traps=[('Rotating values.', 'Only q and k are rotated.'),
                      ('Mixing pair layouts.', 'Interleaved pairs (paper) vs "rotate half" (Llama code) are permutations; weights trained with one don\'t work with the other.'),
                      ('Assuming RoPE extrapolates.', 'Angles beyond the trained range are new to the model; quality drops past the training length.')]),
    papers=[P['roformer'], P['llama'], P['llama3']],
)

# 04 ------------------------------------------------------------------
def _hid(d, mo=256, mult=None):
    h = int(2 * 4 * d / 3)
    if mult:
        h = int(mult * h)
    return mo * ceil(h / mo)


EXTRAS['04-swiglu'] = dict(
    glance=dict(steps=[('x', 'normed token vector', 'f'), ('x·W_gate → SiLU', 'how much to let through', 'c'), ('x·W_up', 'what to let through', 'b'),
                       ('⊙ then ·W_down', 'back to d', 'a')],
                caption='Three matrices: gate, up, down. The element-wise product is the "gated linear unit".'),
    example=dict(title='Worked example: the hidden size and the parameter budget',
                 setup='d = 4,096. A ReLU FFN with hidden 4d has 2 matrices; SwiGLU has 3.',
                 steps=[f'ReLU FFN: 2 × 4,096 × 16,384 = <b>{2 * 4096 * 16384 / 1e6:.1f}M</b> parameters.',
                        f'Equal budget: hidden = ⅔ × 16,384 = 10,922.7 → LLaMA rounds up to a multiple of 256: <b>{_hid(4096):,}</b>.',
                        f'SwiGLU params: 3 × 4,096 × {_hid(4096):,} = <b>{3 * 4096 * _hid(4096) / 1e6:.1f}M</b> (≈ the same budget).',
                        f'Llama 3 8B multiplies by 1.3 and rounds to 1,024: <b>{_hid(4096, 1024, 1.3):,}</b> = {_hid(4096, 1024, 1.3) / 4096:.1f}·d, spending more on the FFN.'],
                 result='The ⅔ rule keeps SwiGLU cost-neutral; odd hidden sizes come from rounding up to hardware-friendly multiples.'),
    traps=dict(tricks=[('Hidden ≈ ⅔·4d.', 'Then round up to a multiple of 256 (LLaMA) or 1,024 (Llama 3).'),
                       ('FFN params = 3·d·hidden.', 'About 70% of a dense Llama\'s parameters.'),
                       ('SiLU = Swish₁ = x·σ(x).', 'hidden_act: "silu" in configs means SwiGLU.')],
               traps=[('Counting two matrices.', 'Gated FFNs have three: gate, up, down.'),
                      ('Assuming 4d hidden.', 'Real models use ⅔·4d or a tuned multiplier (Llama 3: 3.5·d).'),
                      ('Confusing Swish with SwiGLU.', 'Swish alone (no gate) performed like ReLU in Shazeer\'s table.')]),
    papers=[P['glu'], P['dauphin'], P['llama']],
)

# 05 ------------------------------------------------------------------
_rows = [('MHA', 2 * 128 * 128), ('GQA, 8 groups', 2 * 8 * 128), ('MLA', 512 + 64), ('MQA', 2 * 128)]
EXTRAS['05-attention-variants'] = dict(
    glance=dict(steps=[('query heads', 'all n_h kept', 'c'), ('group them', 'g groups', 'a'), ('shared K/V head', 'one per group (GQA)\nor a latent (MLA)', 'b'),
                       ('KV cache', 'shrinks by n_h / g', 'e')],
                caption='MQA: g = 1. GQA: 1 < g < n_h. MHA: g = n_h. MLA compresses all heads into one latent instead.'),
    example=dict(title='Worked example: cache per token per layer, DeepSeek-V2 dimensions',
                 setup='128 heads of dimension 128; MLA latent d_c = 512 plus a 64-dim decoupled RoPE key. Numbers are cached elements; multiply by 2 for BF16 bytes.',
                 steps=[f'MHA: 2 × 128 × 128 = <b>{_rows[0][1]:,}</b> elements.'] +
                       [f'{n}: <b>{v:,}</b> ({v / _rows[0][1]:.1%} of MHA).' for n, v in _rows[1:]] +
                       ['MLA ≈ 4.5 head-dims: about GQA with 2.25 groups, with quality reported above MHA.'],
                 result=f'Sharing (GQA) or compressing (MLA) cuts the cache {(_rows[0][1] / _rows[1][1]):.0f}× and {(_rows[0][1] / _rows[2][1]):.0f}× here, which converts directly into more concurrent sequences or longer contexts.'),
    traps=dict(tricks=[('Cache ∝ KV heads.', 'Shrink factor = n_heads / n_kv_heads.'),
                       ('Convert MHA → GQA cheaply.', 'Mean-pool the K and V heads in each group, then uptrain with ~5% of the pretraining compute.'),
                       ('MLA absorbs W_UK into W_Q.', 'Keys are never materialized at inference.')],
               traps=[('Expecting GQA to cut FLOPs.', 'Score FLOPs barely change; the saving is memory and bandwidth.'),
                      ('Plain RoPE with MLA.', 'The position rotation breaks absorption; MLA needs a decoupled RoPE slice.'),
                      ('TP degree above KV heads.', 'KV heads then get replicated across GPUs, wasting cache.')]),
    papers=[P['mqa'], P['gqa'], P['dsv2']],
)

# 06 ------------------------------------------------------------------
_T = 2048
EXTRAS['06-decoder-only'] = dict(
    glance=dict(steps=[('tokens 0…T−1', 'one sequence', 'f'), ('causal stack', 'each position sees only the past', 'c'), ('logits at every position', 'predict token t+1', 'a'),
                       ('loss on all T', 'every token is a target', 'e')],
                caption='One stack, one mask, one objective; at serving time past K and V never change, so they can be cached.'),
    example=dict(title='Worked example: training signal per sequence',
                 setup=f'One sequence of {_T:,} tokens.',
                 steps=[f'Causal LM: every position predicts its next token → <b>{_T - 1:,}</b> targets.',
                        f'BERT-style masked LM (15% masked): <b>{round(0.15 * _T)}</b> targets.',
                        f'Encoder-decoder with a 50/50 split: <b>{_T // 2:,}</b> targets, and two stacks.',
                        'Packed with a document mask: same target count, no attention across documents.'],
                 result=f'The causal objective extracts ~{(_T - 1) / round(0.15 * _T):.1f}× more supervised positions per sequence than 15% masking, from raw text with no labels.'),
    traps=dict(tricks=[('Causal mask: j ≤ i.', 'Prefix-LM: bidirectional within the prompt, causal after.'),
                       ('Pack + document mask.', 'Full-length rows with no cross-document attention.'),
                       ('Same mask everywhere.', 'Pretraining, SFT and serving all use the causal mask.')],
               traps=[('Packing without a document mask.', 'Tokens attend into unrelated previous documents.'),
                      ('"Decoders can\'t read the input."', 'The last position sees the whole prompt.'),
                      ('Calling encoder-decoder obsolete.', 'Wang et al. found non-causal objectives win after multitask fine-tuning; encoders still lead retrieval.')]),
    papers=[P['wang22'], P['gpt2'], P['t5'], P['bert']],
)

# 07 ------------------------------------------------------------------
_s, _L7 = 8, 4096
_ntk = 10000 * _s ** (128 / 126)
EXTRAS['07-rope-scaling'] = dict(
    glance=dict(steps=[('trained at L', 'angles seen: m·θᵢ, m < L', 'f'), ('target s·L', 'pick factor s', 'c'), ('remap θ', 'PI / NTK-aware / YaRN', 'a'),
                       ('short fine-tune', 'hundreds of steps', 'b'), ('serve s·L', 'angles stay in range', 'e')],
                caption='Or train long directly with a larger RoPE base, as Llama 3 did.'),
    example=dict(title='Worked example: extending 4K to 32K (s = 8)',
                 setup='d = 128, base 10,000, trained length L = 4,096.',
                 steps=[f'PI: every θ ÷ 8. Neighbouring tokens differ by only 1/8 rad in pair 0 (was 1 rad).',
                        f'NTK-aware: new base = 10,000 × 8<sup>128/126</sup> = <b>{_ntk:,.0f}</b>; pair 0 unchanged, pair 63 slowed by exactly 8.',
                        f'YaRN: pairs with fewer than 1 turn in 4,096 tokens get θ/8; more than 32 turns are left alone; a ramp in between.',
                        f'YaRN logit temperature: √(1/t) = 0.1·ln 8 + 1 = <b>{0.1 * log(8) + 1:.3f}</b>.'],
                 result='All three keep slow pairs inside the trained angle range; they differ in how much local resolution they keep and how much fine-tuning they need.'),
    traps=dict(tricks=[('Find the at-risk pairs.', 'Pairs with wavelength 2π/θᵢ > L never completed a turn in training.'),
                       ('NTK base: b·s^(d/(d−2)).', 'Keeps the fastest pair, slows the slowest by s.'),
                       ('YaRN defaults for Llama: α = 1, β = 32.', 'Plus temperature 0.1·ln s + 1.')],
               traps=[('Skipping fine-tuning.', 'PI and YaRN both fine-tune; extrapolation without it fails.'),
                      ('Trusting the advertised window.', 'Check retrieval and long-document quality at the length you need.'),
                      ('Mismatched rope_scaling at inference.', 'Serving must apply the same scaling as fine-tuning.')]),
    papers=[P['pi'], P['yarn'], P['llama3']],
)

# 08 ------------------------------------------------------------------
_kvtok = 2 * 32 * 8 * 128 * 2
EXTRAS['08-sliding-window'] = dict(
    glance=dict(steps=[('token i', 'query', 'f'), ('attend to i−W+1 … i', 'window of W keys', 'c'), ('stack L layers', 'reach ≈ L·(W−1)+1', 'a'),
                       ('rolling cache', 'slot = i mod W', 'b')],
                caption='Bounded attention per layer; depth relays information further back; memory capped at W per layer.'),
    example=dict(title='Worked example: Mistral 7B at 32K tokens',
                 setup='32 layers, 8 KV heads of 128, BF16, window W = 4,096.',
                 steps=[f'KV per token: 2 × 32 × 8 × 128 × 2 = <b>{_kvtok // KiB} KiB</b>.',
                        f'Full cache at 32,768 tokens: <b>{32768 * _kvtok / GiB:.0f} GiB</b>; rolling buffer (4,096 slots): <b>{4096 * _kvtok / GiB:.1f} GiB</b>, {32768 // 4096}× less.',
                        f'Theoretical span: 32 × (4,096 − 1) + 1 = <b>{32 * 4095 + 1:,}</b> tokens (paper: ~131K).',
                        f'Token 10,000 is written to slot 10,000 mod 4,096 = <b>{10000 % 4096:,}</b>, overwriting token {10000 - 4096:,}.'],
                 result='Constant memory per sequence and attention cost O(T·W), at the price of indirect long-range access.'),
    traps=dict(tricks=[('Span ≈ layers × W.', 'Exactly L·(W−1)+1 with an inclusive window of W keys.'),
                       ('ALiBi slopes: 2^(−8i/n).', 'For 8 heads: 1/2 … 1/256.'),
                       ('Check sliding_window in the config.', 'Mixtral, unlike Mistral 7B, is dense over 32K.')],
               traps=[('Assuming nothing beyond W is visible.', 'Information hops W per layer, lossily.'),
                      ('Calling ALiBi a position embedding.', 'It is a bias on attention scores.'),
                      ('Off-by-one windows.', 'Codebases differ on whether the window includes the current token.')]),
    papers=[P['mistral'], P['longformer'], P['alibi']],
)

# 09 ------------------------------------------------------------------
_N, _dd = 8192, 128
EXTRAS['09-flash-attention'] = dict(
    glance=dict(steps=[('Q block', 'loaded once into SRAM', 'c'), ('stream K, V blocks', 'through SRAM', 'b'), ('online softmax', 'running max m, sum ℓ\nrescale partial output', 'a'),
                       ('write O once', 'plus log-sum-exp for backward', 'e')],
                loop=(2, 1, 'for every K/V block'),
                caption='The N×N score matrix exists only one tile at a time, on chip.'),
    example=dict(title='Worked example: what standard attention would store',
                 setup=f'Sequence length N = {_N:,}, head dimension {_dd}, BF16, one head.',
                 steps=[f'Score matrix S: N² = {_N * _N:,} elements = <b>{_N * _N * 2 / MiB:.0f} MiB</b> per head; P is the same again.',
                        f'Q, K, V and O together: 4 × N × d = {4 * _N * _dd:,} elements = <b>{4 * _N * _dd * 2 / MiB:.0f} MiB</b>.',
                        f'With 32 heads and batch 8, S alone would be <b>{_N * _N * 2 * 32 * 8 / GiB:.0f} GiB</b>, written and read back.',
                        'FlashAttention keeps only per-row statistics (m, ℓ or the log-sum-exp): O(N) extra memory.'],
                 result='Same FLOPs (slightly more with recomputation), far fewer bytes moved, and memory linear in N: that is where the speedup comes from.'),
    traps=dict(tricks=[('Online softmax.', 'm_new = max(m, block max); ℓ ← ℓ·e^(m−m_new) + Σe^(x−m_new).'),
                       ('FA2 loop order.', 'Outer loop over query blocks (parallel), inner over K/V blocks.'),
                       ('Backward recomputes.', 'Store the log-sum-exp per row, recompute S and P on chip.')],
               traps=[('Calling it approximate.', 'Outputs match standard attention up to floating-point rounding.'),
                      ('Calling it O(N).', 'Compute is still O(N²); extra memory is O(N).'),
                      ('Expecting fewer FLOPs.', 'Recomputation adds FLOPs; the gain is memory traffic.')]),
    papers=[P['fa1'], P['fa2'], P['fa3'], P['milakov']],
)

# 10 ------------------------------------------------------------------
_tok, _E, _cf = 4096, 8, 1.25
EXTRAS['10-mixture-of-experts'] = dict(
    glance=dict(steps=[('token', 'after attention', 'f'), ('router', 'logits over N experts', 'c'), ('top-k experts', 'k of N FFNs run', 'a'),
                       ('weighted sum', 'softmax over top-k', 'e')],
                caption='Parameters scale with N; compute per token scales with k.'),
    example=dict(title='Worked example: Mixtral and expert capacity',
                 setup=f'Mixtral: 8 experts, top-2. A batch of {_tok:,} tokens with capacity factor {_cf}.',
                 steps=['Parameters: 47B in total, about 13B active per token (attention and embeddings are shared; 2 of 8 FFNs run).',
                        f'Expert capacity = tokens / experts × capacity factor = {_tok:,} / {_E} × {_cf} = <b>{int(_tok / _E * _cf)}</b> token slots per expert (counting top-1 assignments).',
                        f'If routing sends 30% of tokens to one expert, that is {int(0.3 * _tok):,} tokens for {int(_tok / _E * _cf)} slots: <b>{int(0.3 * _tok) - int(_tok / _E * _cf):,}</b> are dropped from that expert.',
                        'Switch auxiliary loss α·N·Σfᵢ·Pᵢ equals α = 0.01 when perfectly balanced and α·N = 0.08 when collapsed onto one expert.'],
                 result='MoE cuts FLOPs per token but not memory, and only works if routing stays balanced.'),
    traps=dict(tricks=[('Active ≈ shared + k × expert size.', 'Mixtral: ~13B of 47B per token.'),
                       ('Capacity = tokens/N × capacity factor.', 'Overflow tokens skip the expert via the residual.'),
                       ('Aux loss minimum = α.', 'At uniform routing fᵢ = Pᵢ = 1/N.')],
               traps=[('"Runs like a 13B model."', 'Memory must hold all 47B; expert parallelism adds all-to-all traffic.'),
                      ('Expecting topic experts.', 'Mixtral\'s routing follows syntax more than domain.'),
                      ('Ignoring drops.', 'Imbalanced routing silently skips tokens at fixed capacity.')]),
    papers=[P['switch'], P['mixtral'], P['sparse_moe'], P['dsv2']],
)

# 11 ------------------------------------------------------------------
_p70 = params(128256, 8192, 80, 64, 8, 28672)
_kv70 = 2 * 80 * 8 * 128 * 2
EXTRAS['11-putting-it-together'] = dict(
    glance=dict(steps=[('config.json', 'd, layers, heads, KV heads,\nhidden, vocab, rope_theta', 'f'), ('block recipe', 'norms, attention type,\nFFN type, position', 'c'),
                       ('size', 'parameters, KV per token,\nFLOPs per token', 'a'), ('serving plan', 'GPUs, TP degree,\ncontext × batch', 'e')],
                caption='From a model card to a hardware estimate in four steps.'),
    example=dict(title='Worked example: sizing Llama 3 70B from its config',
                 setup='Vocabulary 128,256; d = 8,192; 80 layers; 64 query heads, 8 KV heads (head dim 128); FFN 28,672; untied embeddings.',
                 steps=[f'Parameters: <b>{_p70 / 1e9:.2f}B</b> (same formula as notebook 10).',
                        f'Weights: BF16 <b>{_p70 * 2 / 1e9:.0f} GB</b>; FP8 {_p70 / 1e9:.0f} GB → at least 2 × 80 GB GPUs in BF16.',
                        f'KV per token: 2 × 80 × 8 × 128 × 2 = <b>{_kv70 // KiB} KiB</b>; 32 sequences at 8K = {32 * 8192 * _kv70 / GiB:.0f} GiB.',
                        f'Forward FLOPs per token ≈ 2 × parameters = <b>{2 * _p70 / 1e9:.0f} GFLOP</b>.'],
                 result='Weights pick the minimum GPU count; KV per token decides how many concurrent long-context users fit; FLOPs per token set prefill speed.'),
    traps=dict(tricks=[('FLOPs/token ≈ 2N.', 'Plus the attention term for long contexts.'),
                       ('Memory = weights + KV + activations.', 'KV usually decides concurrency.'),
                       ('Check rope_theta and rope_scaling.', 'They tell you the trained and supported context.')],
               traps=[('Parameter count = serving cost.', 'KV per token and active (MoE) parameters matter as much.'),
                      ('Same size, same architecture.', 'Llama 2 7B vs Llama 3 8B differ in KV heads, FFN width, vocabulary and RoPE base.'),
                      ('Treating FlashAttention as architecture.', 'It is a kernel; outputs are the same.')]),
    papers=[P['llama'], P['llama2'], P['llama3'], P['mistral']],
)
