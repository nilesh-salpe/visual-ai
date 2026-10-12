"""Phase 1 (LLM inference & serving) exercise notebooks."""

TINY_GPT = r'''
def init_params(vocab=64, d_model=32, n_heads=4, n_layers=2, max_len=64, seed=0):
    """A tiny GPT-2-style model with random weights (pre-norm blocks, tied embeddings)."""
    r = np.random.default_rng(seed)
    n = lambda *s: r.normal(0, 0.2, s)
    layers = [dict(ln1_g=1 + n(d_model) * .1, ln1_b=n(d_model) * .1, Wqkv=n(d_model, 3 * d_model), bqkv=n(3 * d_model) * .1,
                   Wo=n(d_model, d_model), bo=n(d_model) * .1, ln2_g=1 + n(d_model) * .1, ln2_b=n(d_model) * .1,
                   W1=n(d_model, 4 * d_model), b1=n(4 * d_model) * .1, W2=n(4 * d_model, d_model), b2=n(d_model) * .1)
              for _ in range(n_layers)]
    return dict(wte=n(vocab, d_model), wpe=n(max_len, d_model), layers=layers,
                lnf_g=1 + n(d_model) * .1, lnf_b=n(d_model) * .1, n_heads=n_heads)

def gelu(x):
    return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x ** 3)))

def softmax(x, axis=-1):
    x = x - x.max(axis=axis, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=axis, keepdims=True)
'''

REF_GPT = r'''
def _ln(x, g, b, eps=1e-5):
    m = x.mean(-1, keepdims=True); v = x.var(-1, keepdims=True)
    return (x - m) / np.sqrt(v + eps) * g + b

def _attn(x, L, H):
    T, d = x.shape; dh = d // H
    q, k, v = np.split(x @ L['Wqkv'] + L['bqkv'], 3, axis=-1)
    q, k, v = [a.reshape(T, H, dh).transpose(1, 0, 2) for a in (q, k, v)]
    s = q @ k.transpose(0, 2, 1) / np.sqrt(dh)
    s = np.where(np.tril(np.ones((T, T), bool)), s, -np.inf)
    o = softmax(s) @ v
    return o.transpose(1, 0, 2).reshape(T, d) @ L['Wo'] + L['bo']

def _gpt(P, tokens):
    T = len(tokens); x = P['wte'][tokens] + P['wpe'][:T]
    for L in P['layers']:
        x = x + _attn(_ln(x, L['ln1_g'], L['ln1_b']), L, P['n_heads'])
        x = x + gelu(_ln(x, L['ln2_g'], L['ln2_b']) @ L['W1'] + L['b1']) @ L['W2'] + L['b2']
    return _ln(x, P['lnf_g'], P['lnf_b']) @ P['wte'].T
'''

NBS = []

# ------------------------------------------------------------------ 01
NBS.append(dict(
    slug='01_tiny_gpt_forward', title='01 · A tiny GPT forward pass in NumPy', deck='inference/01-inference-workload/', deck_name='The inference workload', minutes=40,
    goals='layer norm, causal multi-head self-attention, and a full decoder-only forward pass, which the other notebooks build on.',
    setup=TINY_GPT + REF_GPT + "\nP = init_params()\nprint('tiny GPT ready:', len(P['layers']), 'layers, d_model =', P['wte'].shape[1], ', vocab =', P['wte'].shape[0])",
    tasks=[
        dict(name='ln', fn='layer_norm', title='Layer normalization', md=r'''
            Normalize each row (token) over its features: $\mathrm{LN}(x) = g \odot \frac{x-\mu}{\sqrt{\sigma^2+\epsilon}} + b$, with $\mu,\sigma^2$ taken over the **last** axis.''',
             starter=r'''
            def layer_norm(x, g, b, eps=1e-5):
                """x: [T, d]; g, b: [d]. Returns [T, d]."""
                # TODO: mean and variance over the last axis, normalize, then scale by g and shift by b
                raise NotImplementedError''',
             test=r'''
            def _test_layer_norm(f):
                r = np.random.default_rng(1); x = r.normal(2, 3, (5, 8)); g = r.normal(1, .1, 8); b = r.normal(0, .1, 8)
                y = f(x, g, b)
                assert y.shape == x.shape, f"shape {y.shape} != {x.shape}"
                assert np.allclose(y, _ln(x, g, b), atol=1e-6), "values differ from reference (normalize over the LAST axis, use variance not std inside the sqrt)"''',
             solution=r'''
            def layer_norm_solution(x, g, b, eps=1e-5):
                mu = x.mean(-1, keepdims=True)
                var = x.var(-1, keepdims=True)
                return (x - mu) / np.sqrt(var + eps) * g + b'''),
        dict(name='attn', fn='causal_self_attention', title='Causal multi-head self-attention', md=r'''
            Given the normalized input `x` ([T, d]) and one layer's weights:
            1. `q, k, v = split(x @ Wqkv + bqkv)` into 3 parts of width d.
            2. Reshape each into `H` heads of size `dh = d // H`, giving [H, T, dh].
            3. Scores $= qk^\top/\sqrt{dh}$. **Mask** future positions (column > row) with $-\infty$, softmax over the last axis, then multiply by `v`.
            4. Merge the heads back to [T, d] and apply `@ Wo + bo`.''',
             starter=r'''
            def causal_self_attention(x, layer, n_heads):
                """x: [T, d] (already layer-normed). layer: dict with Wqkv, bqkv, Wo, bo. Returns [T, d]."""
                # TODO: project to q, k, v -> split heads -> masked softmax(q k^T / sqrt(dh)) v -> merge heads -> output projection
                raise NotImplementedError''',
             test=r'''
            def _test_causal_self_attention(f):
                x = np.random.default_rng(2).normal(size=(7, 32)); L = P['layers'][0]
                y = f(x, L, 4)
                assert y.shape == (7, 32), f"shape {y.shape} != (7, 32)"
                assert np.allclose(y, _attn(x, L, 4), atol=1e-6), "values differ from reference: check head split/merge order and the 1/sqrt(dh) scale"
                x2 = x.copy(); x2[-1] += 5.0
                assert np.allclose(f(x2, L, 4)[:-1], y[:-1], atol=1e-9), "not causal: changing the LAST token changed earlier outputs"''',
             solution=r'''
            def causal_self_attention_solution(x, layer, n_heads):
                T, d = x.shape; dh = d // n_heads
                q, k, v = np.split(x @ layer['Wqkv'] + layer['bqkv'], 3, axis=-1)
                q, k, v = [a.reshape(T, n_heads, dh).transpose(1, 0, 2) for a in (q, k, v)]   # [H, T, dh]
                scores = q @ k.transpose(0, 2, 1) / np.sqrt(dh)                              # [H, T, T]
                mask = np.tril(np.ones((T, T), dtype=bool))
                scores = np.where(mask, scores, -np.inf)
                out = softmax(scores, axis=-1) @ v                                             # [H, T, dh]
                return out.transpose(1, 0, 2).reshape(T, d) @ layer['Wo'] + layer['bo']'''),
        dict(name='fwd', fn='gpt_forward', title='The full forward pass', md=r'''
            $x = W_{te}[\text{tokens}] + W_{pe}[0..T)$, then for each layer (pre-norm):
            $x \leftarrow x + \mathrm{Attn}(\mathrm{LN}_1(x))$ and $x \leftarrow x + \mathrm{GELU}(\mathrm{LN}_2(x) W_1 + b_1) W_2 + b_2$.
            Finally apply $\mathrm{LN}_f$ and **tied** output weights: logits $= x\,W_{te}^\top$ ([T, vocab]).
            Use your own `layer_norm` and `causal_self_attention`, or the `_solution` versions if you skipped them.''',
             starter=r'''
            def gpt_forward(params, tokens):
                """tokens: list[int] of length T. Returns logits [T, vocab]."""
                # TODO: embeddings + positions -> for each layer: x += attn(ln1(x)); x += mlp(ln2(x)) -> final ln -> x @ wte.T
                raise NotImplementedError''',
             test=r'''
            def _test_gpt_forward(f):
                toks = [3, 14, 15, 9, 2, 6, 5]
                y = f(P, toks)
                assert y.shape == (7, 64), f"shape {y.shape} != (7, 64)"
                assert np.allclose(y, _gpt(P, toks), atol=1e-5), "logits differ from reference: check pre-norm residuals, GELU MLP, final LN and tied output weights"''',
             solution=r'''
            def gpt_forward_solution(params, tokens):
                T = len(tokens)
                x = params['wte'][tokens] + params['wpe'][:T]
                for L in params['layers']:
                    x = x + causal_self_attention_solution(layer_norm_solution(x, L['ln1_g'], L['ln1_b']), L, params['n_heads'])
                    h = layer_norm_solution(x, L['ln2_g'], L['ln2_b'])
                    x = x + gelu(h @ L['W1'] + L['b1']) @ L['W2'] + L['b2']
                x = layer_norm_solution(x, params['lnf_g'], params['lnf_b'])
                return x @ params['wte'].T'''),
    ],
    explore=r'''
# Greedy generation with the full forward pass: every new token re-runs the whole prefix.
toks = [1, 2, 3]
for _ in range(10):
    toks.append(int(gpt_forward_solution(P, toks)[-1].argmax()))
print('greedy tokens:', toks)
print('note: generating token t recomputes attention over all t previous tokens; notebook 02 removes that waste with a KV cache.')''',
    takeaways='''
    - A decoder-only forward pass is embeddings → N × (pre-norm attention + MLP with residuals) → final norm → logits.
    - The **causal mask** is what makes the model autoregressive: position *t* never sees tokens after *t*.
    - Generating with the full forward pass repeats work for the whole prefix at every step. That's the waste the KV cache removes.''',
))

# ------------------------------------------------------------------ 02
NBS.append(dict(
    slug='02_kv_cache', title='02 · KV-cache decoding', deck='inference/02-kv-cache/', deck_name='KV cache', minutes=35,
    goals='incremental decoding with a key/value cache that gives exactly the same logits as recomputing the whole prefix, but does only one new token of work per step.',
    setup=TINY_GPT + REF_GPT + r'''
P = init_params()

def new_cache(params):
    d = params['wte'].shape[1]
    return [{'k': np.zeros((0, d)), 'v': np.zeros((0, d))} for _ in params['layers']]

def generate_naive(params, prompt, n_new):
    """Greedy decoding WITHOUT a cache: re-runs the full forward pass for every new token."""
    toks = list(prompt)
    for _ in range(n_new):
        toks.append(int(_gpt(params, toks)[-1].argmax()))
    return toks
print('helpers ready: new_cache(P), generate_naive(P, prompt, n), _gpt(P, tokens) = full forward')''',
    tasks=[
        dict(name='step', fn='forward_step', title='One decoding step with a cache', md=r'''
            Process **one** token at position `pos`:
            - $x = W_{te}[\text{token}] + W_{pe}[\text{pos}]$ (shape [d]).
            - For each layer: compute this token's `q, k, v` from $\mathrm{LN}_1(x)$, **append** `k` and `v` to `cache[l]`, then attend with `q` over **all cached** keys and values. No mask is needed, because the cache only holds the past.
            - Finish the block as usual (residual, MLP, residual), apply the final LN, and return logits of shape [vocab].

            `cache[l]['k']` and `cache[l]['v']` have shape [t, d], with heads still concatenated. Split them into heads inside attention.''',
             starter=r'''
            def forward_step(params, token, pos, cache):
                """Returns logits [vocab] for `token` at `pos`, appending this token's k, v to `cache` (mutated in place)."""
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_forward_step(f):
                toks = [5, 9, 1, 33, 7, 21]
                full = _gpt(P, toks)
                cache = new_cache(P)
                for t, tok in enumerate(toks):
                    out = f(P, tok, t, cache)
                    assert out.shape == (64,), f"logits shape {out.shape} != (64,)"
                    assert np.allclose(out, full[t], atol=1e-5), f"step {t}: cached logits differ from the full forward pass"
                assert cache[0]['k'].shape == (6, 32), f"cache should hold 6 keys of width 32, got {cache[0]['k'].shape}"''',
             solution=r'''
            def forward_step_solution(params, token, pos, cache):
                H = params['n_heads']; d = params['wte'].shape[1]; dh = d // H
                x = params['wte'][token] + params['wpe'][pos]
                for L, c in zip(params['layers'], cache):
                    h = _ln(x[None], L['ln1_g'], L['ln1_b'])[0]
                    q, k, v = np.split(h @ L['Wqkv'] + L['bqkv'], 3)
                    c['k'] = np.vstack([c['k'], k]); c['v'] = np.vstack([c['v'], v])
                    t = c['k'].shape[0]
                    Q = q.reshape(H, 1, dh)
                    K = c['k'].reshape(t, H, dh).transpose(1, 0, 2)
                    V = c['v'].reshape(t, H, dh).transpose(1, 0, 2)
                    o = softmax(Q @ K.transpose(0, 2, 1) / np.sqrt(dh)) @ V          # [H, 1, dh]
                    x = x + o.reshape(d) @ L['Wo'] + L['bo']
                    h2 = _ln(x[None], L['ln2_g'], L['ln2_b'])[0]
                    x = x + gelu(h2 @ L['W1'] + L['b1']) @ L['W2'] + L['b2']
                return _ln(x[None], params['lnf_g'], params['lnf_b'])[0] @ params['wte'].T'''),
        dict(name='gen', fn='generate_cached', title='Greedy generation with the cache', md=r'''
            Feed the prompt token by token (this is the **prefill**), then repeatedly take the argmax of the last logits, append it, and feed it back (this is **decode**). The output must equal `generate_naive`.''',
             starter=r'''
            def generate_cached(params, prompt, n_new, step=None):
                """Greedy decoding with a KV cache. `step` defaults to your forward_step."""
                step = step or forward_step
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_generate_cached(f):
                prompt = [4, 8, 15, 16]
                assert f(P, prompt, 12) == generate_naive(P, prompt, 12), "tokens differ from naive greedy decoding"''',
             solution=r'''
            def generate_cached_solution(params, prompt, n_new, step=None):
                step = step or forward_step_solution
                cache, toks = new_cache(params), list(prompt)
                for pos, tok in enumerate(toks):          # prefill
                    logits = step(params, tok, pos, cache)
                for _ in range(n_new):                     # decode
                    nxt = int(logits.argmax()); toks.append(nxt)
                    logits = step(params, nxt, len(toks) - 1, cache)
                return toks'''),
    ],
    explore=r'''
# Work per generated token: naive recomputes the prefix, cached does one token.
P2 = init_params(max_len=512)
prompt = list(range(1, 33))
for n in (32, 96, 192):
    t0 = time.perf_counter(); generate_naive(P2, prompt, n); t_naive = time.perf_counter() - t0
    t0 = time.perf_counter(); generate_cached_solution(P2, prompt, n); t_cache = time.perf_counter() - t0
    naive_rows = sum(len(prompt) + i for i in range(n))     # token rows processed by the naive loop
    print(f"{n:4d} new tokens: naive {t_naive*1e3:7.1f} ms ({naive_rows} token-rows)   cached {t_cache*1e3:7.1f} ms ({len(prompt)+n} token-rows)")''',
    takeaways='''
    - The cache stores each layer's **K and V** for every past token. A new token computes only its own q, k and v and attends over the cache.
    - Logits are **identical** to recomputing everything, so the cache is an exact optimization.
    - The cost moves from compute to **memory**: the cache grows linearly with context length and batch size (notebook 04).''',
))

# ------------------------------------------------------------------ 03
NBS.append(dict(
    slug='03_gqa_mqa', title='03 · Grouped-query attention (GQA) and multi-query attention (MQA)', deck='inference/02-kv-cache/', deck_name='KV cache', minutes=25,
    goals='attention where several query heads share each key/value head (GQA, Ainslie et al. 2023). Multi-head attention and MQA are the two extremes.',
    setup=r'''
def softmax(x, axis=-1):
    x = x - x.max(axis=axis, keepdims=True); e = np.exp(x); return e / e.sum(axis=axis, keepdims=True)

def _ref_gqa(x, Wq, Wk, Wv, Wo, H, Hkv):
    T, d = x.shape; dh = Wq.shape[1] // H
    q = (x @ Wq).reshape(T, H, dh); k = (x @ Wk).reshape(T, Hkv, dh); v = (x @ Wv).reshape(T, Hkv, dh)
    mask = np.tril(np.ones((T, T), bool)); out = np.zeros((T, H, dh))
    for h in range(H):
        g = h // (H // Hkv)                       # the kv head this query head reads
        s = q[:, h] @ k[:, g].T / np.sqrt(dh)
        out[:, h] = softmax(np.where(mask, s, -np.inf)) @ v[:, g]
    return out.reshape(T, H * dh) @ Wo

def make_weights(d=32, H=8, Hkv=2, seed=0):
    r = np.random.default_rng(seed); dh = d // H
    return r.normal(0, .3, (d, H * dh)), r.normal(0, .3, (d, Hkv * dh)), r.normal(0, .3, (d, Hkv * dh)), r.normal(0, .3, (H * dh, d))
print('helpers ready: make_weights(d, H, Hkv)')''',
    tasks=[
        dict(name='gqa', fn='gqa_attention', title='GQA forward pass', md=r'''
            `Wq` projects to `H` query heads; `Wk` and `Wv` project to only `Hkv` key/value heads (`H % Hkv == 0`).
            Query head `h` uses kv head `h // (H // Hkv)`. Apply a causal mask, then merge the heads and apply `@ Wo`.
            Ideally avoid a Python loop over heads: `np.repeat` the kv heads along the head axis.''',
             starter=r'''
            def gqa_attention(x, Wq, Wk, Wv, Wo, n_heads, n_kv_heads):
                """x: [T, d] -> [T, d]. Causal."""
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_gqa_attention(f):
                x = np.random.default_rng(3).normal(size=(6, 32))
                for H, Hkv in [(8, 8), (8, 2), (8, 1)]:
                    W = make_weights(32, H, Hkv, seed=H + Hkv)
                    assert np.allclose(f(x, *W, H, Hkv), _ref_gqa(x, *W, H, Hkv), atol=1e-6), f"mismatch for H={H}, Hkv={Hkv} (query head h must use kv head h // (H // Hkv))"''',
             solution=r'''
            def gqa_attention_solution(x, Wq, Wk, Wv, Wo, n_heads, n_kv_heads):
                T, d = x.shape; dh = Wq.shape[1] // n_heads; rep = n_heads // n_kv_heads
                q = (x @ Wq).reshape(T, n_heads, dh).transpose(1, 0, 2)                      # [H, T, dh]
                k = (x @ Wk).reshape(T, n_kv_heads, dh).transpose(1, 0, 2)                   # [Hkv, T, dh]
                v = (x @ Wv).reshape(T, n_kv_heads, dh).transpose(1, 0, 2)
                k, v = np.repeat(k, rep, axis=0), np.repeat(v, rep, axis=0)                 # share each kv head with `rep` query heads
                s = q @ k.transpose(0, 2, 1) / np.sqrt(dh)
                s = np.where(np.tril(np.ones((T, T), bool)), s, -np.inf)
                return (softmax(s) @ v).transpose(1, 0, 2).reshape(T, n_heads * dh) @ Wo'''),
        dict(name='ratio', fn='kv_cache_reduction', title='How much smaller is the cache?', md=r'''
            Return the factor by which GQA shrinks the KV cache compared with multi-head attention that has the same number of query heads.''',
             starter=r'''
            def kv_cache_reduction(n_heads, n_kv_heads):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_kv_cache_reduction(f):
                assert f(64, 8) == 8, "64 query heads sharing 8 kv heads -> cache is 8x smaller"
                assert f(32, 32) == 1 and f(32, 1) == 32, "MHA -> 1x, MQA -> n_heads x"''',
             solution=r'''
            def kv_cache_reduction_solution(n_heads, n_kv_heads):
                return n_heads // n_kv_heads'''),
    ],
    takeaways='''
    - The KV cache scales with the number of **kv heads**, not query heads. GQA with 8 kv heads for 64 query heads stores 8× less.
    - MHA (`Hkv = H`) and MQA (`Hkv = 1`) are the two ends of one family. GQA can be "uptrained" from an MHA checkpoint with about 5% of the original pre-training compute (Ainslie et al. 2023).''',
))

# ------------------------------------------------------------------ 04
NBS.append(dict(
    slug='04_kv_memory_calculator', title='04 · KV-cache memory calculator', deck='inference/02-kv-cache/', deck_name='KV cache', minutes=20,
    goals='the memory arithmetic every serving interview asks for: bytes per token, total cache size, how many concurrent sequences fit, and paging waste.',
    setup="print('no setup needed beyond numpy')",
    tasks=[
        dict(name='tok', fn='kv_bytes_per_token', title='Bytes per token', md=r'''
            Each layer stores one **K** and one **V** vector per kv head: $2 \times \text{layers} \times \text{kv\_heads} \times \text{head\_dim} \times \text{bytes per element}$.''',
             starter=r'''
            def kv_bytes_per_token(n_layers, n_kv_heads, head_dim, bytes_per_el=2):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_kv_bytes_per_token(f):
                assert f(80, 8, 128, 2) == 327_680, "Llama-3-70B-shaped (80 layers, 8 kv heads, dim 128, BF16) should be 320 KB/token"
                assert f(32, 8, 128, 2) == 131_072, "Llama-3-8B-shaped should be 128 KB/token"
                assert f(80, 64, 128, 1) == 1_310_720, "64 kv heads (no GQA) in FP8"''',
             solution=r'''
            def kv_bytes_per_token_solution(n_layers, n_kv_heads, head_dim, bytes_per_el=2):
                return 2 * n_layers * n_kv_heads * head_dim * bytes_per_el'''),
        dict(name='fit', fn='max_concurrent_seqs', title='How many sequences fit?', md=r'''
            Given GPU memory, model weight memory, a reserve fraction kept free for activations, and a per-sequence context length, return how many sequences' KV caches fit at once: $\lfloor ((1-\text{reserve}) \cdot \text{mem} - \text{weights}) / \text{bytes per sequence} \rfloor$, never below 0.''',
             starter=r'''
            def max_concurrent_seqs(gpu_bytes, weight_bytes, bytes_per_token, seq_len, reserve=0.1):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_max_concurrent_seqs(f):
                GB = 1e9
                assert f(640 * GB, 140 * GB, 327_680, 8192) == 162, "8x80GB, 140GB weights, 70B-shaped KV, 8K context, 10% reserve -> 162"
                assert f(80 * GB, 140 * GB, 327_680, 8192) == 0, "weights don't fit -> 0, not negative"''',
             solution=r'''
            def max_concurrent_seqs_solution(gpu_bytes, weight_bytes, bytes_per_token, seq_len, reserve=0.1):
                free = (1 - reserve) * gpu_bytes - weight_bytes
                return max(0, int(free // (bytes_per_token * seq_len)))'''),
        dict(name='waste', fn='paged_vs_contiguous_waste', title='Paging vs contiguous reservation', md=r'''
            Return a tuple `(contiguous_waste, paged_waste)`, each the fraction of **allocated** token slots that are unused.
            - Contiguous: every sequence reserves `max_len` slots.
            - Paged: every sequence allocates `ceil(len / block_size)` blocks of `block_size` slots. vLLM's default block size is 16.''',
             starter=r'''
            def paged_vs_contiguous_waste(seq_lens, max_len, block_size=16):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_paged_vs_contiguous_waste(f):
                c, p = f([100, 2000, 37], 2048, 16)
                assert abs(c - (1 - 2137 / 6144)) < 1e-9, f"contiguous waste wrong: {c}"
                assert abs(p - (1 - 2137 / ((7 + 125 + 3) * 16))) < 1e-9, f"paged waste wrong: {p}"''',
             solution=r'''
            def paged_vs_contiguous_waste_solution(seq_lens, max_len, block_size=16):
                used = sum(seq_lens)
                contiguous = 1 - used / (max_len * len(seq_lens))
                paged = 1 - used / (sum(math.ceil(n / block_size) for n in seq_lens) * block_size)
                return contiguous, paged'''),
    ],
    explore=r'''
r = np.random.default_rng(0)
lens = list(r.integers(50, 2048, 64))
c, p = paged_vs_contiguous_waste_solution(lens, 2048, 16)
print(f"64 random requests: contiguous reservation wastes {c:.0%} of KV memory, paging wastes {p:.1%}")
bpt = kv_bytes_per_token_solution(80, 8, 128, 2)
for ctx in (2048, 8192, 32768, 131072):
    print(f"context {ctx:>6}: {bpt*ctx/2**30:6.2f} GiB of KV per sequence -> {max_concurrent_seqs_solution(640e9, 140e9, bpt, ctx)} sequences on 8x80 GB")''',
    takeaways='''
    - `KV bytes = 2 × layers × kv_heads × head_dim × bytes × tokens × batch`: memorize it.
    - At long context the KV cache, not the weights, limits concurrency. That's why GQA, FP8 KV and paging matter.
    - Paging wastes less than one block per sequence. Contiguous max-length reservation can waste most of the memory.''',
))

# ------------------------------------------------------------------ 05
NBS.append(dict(
    slug='05_continuous_batching', title='05 · Continuous (iteration-level) batching', deck='inference/03-batching/', deck_name='Batching', minutes=35,
    goals='an iteration-level scheduler (Orca, OSDI 2022) that admits new requests and retires finished ones at every decode step, compared with static batching.',
    setup=r'''
def make_requests(n=40, seed=0, rate=0.5):
    """Requests arrive over time and need different numbers of output tokens."""
    r = np.random.default_rng(seed); t = 0.0; reqs = []
    for i in range(n):
        t += r.exponential(1 / rate)
        reqs.append({'id': i, 'arrival': int(t), 'out_len': int(r.integers(4, 60))})
    return reqs

def simulate_static(requests, max_batch):
    """Static batching: fixed groups (in arrival order) run until their LONGEST member finishes."""
    res, t, reqs = {}, 0, sorted(requests, key=lambda q: (q['arrival'], q['id']))
    for i in range(0, len(reqs), max_batch):
        g = reqs[i:i + max_batch]
        start = max(t, max(q['arrival'] for q in g))
        for q in g: res[q['id']] = (start, start + q['out_len'])
        t = start + max(q['out_len'] for q in g)
    return res

def metrics(requests, res):
    by = {q['id']: q for q in requests}
    span = max(f for _, f in res.values()) - min(q['arrival'] for q in requests)
    lat = [res[i][1] - by[i]['arrival'] for i in res]
    return {'throughput_tok_per_step': round(sum(q['out_len'] for q in requests) / span, 2), 'mean_latency': round(float(np.mean(lat)), 1), 'p90_latency': round(float(np.percentile(lat, 90)), 1)}
print('helpers ready: make_requests(), simulate_static(), metrics()')''',
    tasks=[
        dict(name='cb', fn='simulate_continuous', title='Iteration-level scheduler', md=r'''
            Simulate decode iterations `t = 0, 1, 2, …`, where each iteration produces one token for every running request:
            - At the **start** of iteration `t`, admit waiting requests with `arrival <= t` in FIFO order (by `arrival`, then `id`) while fewer than `max_batch` are running.
            - A request admitted at `t` with `out_len = L` occupies a slot for iterations `t … t+L-1` and **finishes at time `t + L`**. Its slot is free from iteration `t + L` onwards.
            - If nothing is running and nothing has arrived yet, jump ahead to the next arrival.

            Return `(results, batch_sizes)`, where `results[id] = (start, finish)` and `batch_sizes` lists the number of running requests in each iteration that ran.''',
             starter=r'''
            def simulate_continuous(requests, max_batch):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _ref_cont(requests, max_batch):
                q = collections.deque(sorted(requests, key=lambda r: (r['arrival'], r['id'])))
                running, res, sizes, t = [], {}, [], 0
                while q or running:
                    running = [r for r in running if res[r['id']][1] > t]
                    while q and q[0]['arrival'] <= t and len(running) < max_batch:
                        r = q.popleft(); res[r['id']] = (t, t + r['out_len']); running.append(r)
                    if not running:
                        if q: t = q[0]['arrival']
                        continue
                    sizes.append(len(running)); t += 1
                return res, sizes

            def _test_simulate_continuous(f):
                for seed, B in [(0, 4), (1, 8), (2, 1)]:
                    reqs = make_requests(30, seed)
                    res, sizes = f(reqs, B)
                    ref, rsizes = _ref_cont(reqs, B)
                    assert set(res) == set(ref), "every request must appear in results"
                    for q in reqs:
                        s, e = res[q['id']]
                        assert s >= q['arrival'], f"request {q['id']} started before it arrived"
                        assert e - s == q['out_len'], f"request {q['id']}: finish - start must equal out_len"
                    assert max(sizes) <= B, "batch exceeded max_batch"
                    assert res == ref and sizes == rsizes, f"schedule differs from reference (seed={seed}, max_batch={B}): admit FIFO at the START of each iteration, free slots at t + out_len"''',
             solution=r'''
            def simulate_continuous_solution(requests, max_batch):
                queue = collections.deque(sorted(requests, key=lambda r: (r['arrival'], r['id'])))
                running, res, sizes, t = [], {}, [], 0
                while queue or running:
                    running = [r for r in running if res[r['id']][1] > t]            # retire finished
                    while queue and queue[0]['arrival'] <= t and len(running) < max_batch:
                        r = queue.popleft(); res[r['id']] = (t, t + r['out_len']); running.append(r)
                    if not running:
                        if queue: t = queue[0]['arrival']                          # idle: jump to next arrival
                        continue
                    sizes.append(len(running)); t += 1                             # one decode iteration
                return res, sizes'''),
    ],
    explore=r'''
reqs = make_requests(80, seed=3, rate=0.6)
for B in (4, 8, 16):
    s = metrics(reqs, simulate_static(reqs, B))
    c = metrics(reqs, simulate_continuous_solution(reqs, B)[0])
    print(f"max_batch={B:2d}  static: {s}\n              continuous: {c}")''',
    takeaways='''
    - Static batching holds every slot until the batch's longest request finishes, which wastes GPU time and makes new arrivals wait.
    - Iteration-level scheduling refills slots every step. Orca reported **36.9×** throughput over FasterTransformer at the same latency (GPT-3 175B).
    - It is the default in modern servers, and it combines with paged KV (notebook 07) and chunked prefill (notebook 06).''',
))

# ------------------------------------------------------------------ 06
NBS.append(dict(
    slug='06_chunked_prefill', title='06 · Chunked prefill with a token budget', deck='inference/04-chunked-prefill/', deck_name='Chunked prefill', minutes=40,
    goals='a Sarathi-style scheduler (2024) that splits long prompts into chunks so prefills never stall ongoing decodes.',
    setup=r'''
def make_requests(n=20, seed=0):
    r = np.random.default_rng(seed); t = 0; out = []
    for i in range(n):
        t += int(r.integers(0, 4))
        out.append({'id': i, 'arrival': t, 'prompt_len': int(r.choice([64, 128, 512, 1500])), 'out_len': int(r.integers(5, 40))})
    return out

def simulate_prefill_first(requests, budget):
    """Baseline: whenever prompts are waiting, run ALL their prefills in one iteration and stall decodes (no budget)."""
    reqs = sorted(requests, key=lambda r: (r['arrival'], r['id'])); i, t = 0, 0
    st = {r['id']: {'left': r['out_len'], 'last': None, 'gaps': []} for r in reqs}; dec, res, tpi = [], {}, []
    while i < len(reqs) or dec:
        waiting = []
        while i < len(reqs) and reqs[i]['arrival'] <= t: waiting.append(reqs[i]); i += 1
        if waiting:
            tpi.append(sum(r['prompt_len'] for r in waiting))
            for r in waiting:
                s = st[r['id']]; s['left'] -= 1; s['last'] = t; res[r['id']] = {'ttft': t + 1 - r['arrival']}
                if s['left'] == 0: res[r['id']]['finish'] = t + 1
                else: dec.append(r)
        elif dec:
            tpi.append(len(dec))
            for r in list(dec):
                s = st[r['id']]; s['gaps'].append(t - s['last']); s['last'] = t; s['left'] -= 1
                if s['left'] == 0: res[r['id']]['finish'] = t + 1; dec.remove(r)
        elif i < len(reqs): t = reqs[i]['arrival']; continue
        t += 1
    return res, tpi
print('helpers ready: make_requests(), simulate_prefill_first()')''',
    tasks=[
        dict(name='chunk', fn='simulate_chunked', title='Stall-free chunked prefill', md=r'''
            Each iteration `t` has a **token budget** `budget`:
            1. **Decodes first.** Every request already decoding gets 1 token, so decodes never stall.
            2. Fill the remaining budget with **prefill chunks** from requests with `arrival <= t`, in FIFO order (by `arrival`, then `id`). A chunk is `min(prompt tokens left, budget left)`.
            3. When a request's prompt finishes in iteration `t`, its **first output token is produced in that same iteration**: `ttft = t + 1 - arrival`. If `out_len == 1` it finishes at `t + 1`; otherwise it starts decoding at `t + 1`.
            4. A decoding request finishes at `t + 1` in the iteration that produces its last token.
            5. If nothing can run, jump `t` to the next arrival.

            Return `(results, tokens_per_iter)`, where `results[id] = {'ttft': …, 'finish': …}` and `tokens_per_iter` lists the tokens used in each iteration that ran. You can assume `budget` is larger than the number of concurrent decodes.''',
             starter=r'''
            def simulate_chunked(requests, budget):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _ref_chunked(requests, budget):
                reqs = sorted(requests, key=lambda r: (r['arrival'], r['id']))
                pre = {r['id']: r['prompt_len'] for r in reqs}; left = {r['id']: r['out_len'] for r in reqs}
                res, dec, tpi, t, done = {}, [], [], 0, 0
                while done < len(reqs):
                    used = 0
                    for r in list(dec):
                        used += 1; left[r['id']] -= 1
                        if left[r['id']] == 0: res[r['id']]['finish'] = t + 1; dec.remove(r); done += 1
                    for r in reqs:
                        if r['arrival'] > t or pre[r['id']] == 0 or used >= budget: continue
                        c = min(pre[r['id']], budget - used); pre[r['id']] -= c; used += c
                        if pre[r['id']] == 0:
                            res[r['id']] = {'ttft': t + 1 - r['arrival']}; left[r['id']] -= 1
                            if left[r['id']] == 0: res[r['id']]['finish'] = t + 1; done += 1
                            else: dec.append(r)
                    if used == 0:
                        t = min(r['arrival'] for r in reqs if pre[r['id']] > 0); continue
                    tpi.append(used); t += 1
                return res, tpi

            def _test_simulate_chunked(f):
                for seed, B in [(0, 256), (1, 512), (2, 128)]:
                    reqs = make_requests(18, seed)
                    res, tpi = f(reqs, B)
                    ref, rtpi = _ref_chunked(reqs, B)
                    assert max(tpi) <= B, "an iteration exceeded the token budget"
                    assert res == ref, f"ttft/finish differ from reference (seed={seed}, budget={B}): decodes first, then FIFO prefill chunks"
                    assert tpi == rtpi, "tokens_per_iter differs from reference"''',
             solution=r'''
            def simulate_chunked_solution(requests, budget):
                reqs = sorted(requests, key=lambda r: (r['arrival'], r['id']))
                prompt_left = {r['id']: r['prompt_len'] for r in reqs}
                out_left = {r['id']: r['out_len'] for r in reqs}
                res, decoding, tokens_per_iter, t, done = {}, [], [], 0, 0
                while done < len(reqs):
                    used = 0
                    for r in list(decoding):                                   # 1. decodes first: never stall
                        used += 1; out_left[r['id']] -= 1
                        if out_left[r['id']] == 0:
                            res[r['id']]['finish'] = t + 1; decoding.remove(r); done += 1
                    for r in reqs:                                             # 2. FIFO prefill chunks in the leftover budget
                        if r['arrival'] > t or prompt_left[r['id']] == 0 or used >= budget:
                            continue
                        chunk = min(prompt_left[r['id']], budget - used)
                        prompt_left[r['id']] -= chunk; used += chunk
                        if prompt_left[r['id']] == 0:                          # 3. prompt done -> first token now
                            res[r['id']] = {'ttft': t + 1 - r['arrival']}; out_left[r['id']] -= 1
                            if out_left[r['id']] == 0: res[r['id']]['finish'] = t + 1; done += 1
                            else: decoding.append(r)
                    if used == 0:                                              # 5. idle -> jump
                        t = min(r['arrival'] for r in reqs if prompt_left[r['id']] > 0); continue
                    tokens_per_iter.append(used); t += 1
                return res, tokens_per_iter'''),
    ],
    explore=r'''
# Iteration cost grows with the tokens it processes. A decode token has to wait for the whole iteration it is in.
reqs = make_requests(20, seed=4)
base, tpi = simulate_prefill_first(reqs, None)
print(f'prefill-first : largest iteration = {max(tpi):5d} tokens -> a decode token can wait behind a {max(tpi)}-token prefill')
for B in (128, 256, 1024):
    res, tpi = simulate_chunked_solution(reqs, B)
    print(f'chunked B={B:4d}: largest iteration = {max(tpi):5d} tokens | iterations: {len(tpi):3d} | mean TTFT {np.mean([v["ttft"] for v in res.values()]):5.1f} iterations')
print('Smaller budgets keep every iteration (and so every decode step) short, but long prompts need more iterations to finish: the TTFT-vs-TPOT knob.')''',
    takeaways='''
    - Long prefills block decodes in a naive scheduler, so users watching tokens stream see stalls.
    - A per-iteration **token budget** with decodes first and prefill chunks after keeps every iteration short and decodes stall-free.
    - Sarathi-Serve reported **2.6×** serving capacity for Mistral-7B on one A100, and up to **5.6×** for Falcon-180B, compared with vLLM under latency SLOs.''',
))

# ------------------------------------------------------------------ 07
NBS.append(dict(
    slug='07_paged_kv_allocator', title='07 · A paged KV-cache allocator', deck='inference/05-paged-attention/', deck_name='PagedAttention and prefix caching', minutes=40,
    goals='the memory manager behind PagedAttention (vLLM, SOSP 2023): fixed-size blocks, per-sequence block tables, reference counts, and copy-on-write when forked sequences diverge.',
    setup="print('no extra setup')",
    tasks=[
        dict(name='bm', fn='BlockManager', title='BlockManager', md=r'''
            Implement the class with `num_blocks` physical blocks of `block_size` token slots each:
            - `add(seq)`: register an empty sequence.
            - `append(seq, n=1)`: add `n` tokens one at a time. Allocate a new block when the sequence is empty or its last block is full. If the last block is **shared** (refcount > 1) and not full, **copy-on-write**: allocate a fresh block, point the table at it, and decrement the old block's refcount. Raise `MemoryError` when no block is free.
            - `fork(parent, child)`: the child shares all of the parent's blocks (refcounts +1) and gets the same token count.
            - `free(seq)`: decrement refcounts and return blocks that reach 0 to the free pool.
            - `num_free()`, `table(seq)` (list of physical block ids), `num_tokens(seq)`.''',
             starter=r'''
            class BlockManager:
                def __init__(self, num_blocks, block_size=16):
                    # TODO
                    raise NotImplementedError
                def add(self, seq): raise NotImplementedError
                def append(self, seq, n=1): raise NotImplementedError
                def fork(self, parent, child): raise NotImplementedError
                def free(self, seq): raise NotImplementedError
                def num_free(self): raise NotImplementedError
                def table(self, seq): raise NotImplementedError
                def num_tokens(self, seq): raise NotImplementedError''',
             test=r'''
            def _test_BlockManager(C):
                m = C(10, block_size=4)
                m.add('a'); m.append('a', 9)
                assert len(m.table('a')) == 3 and m.num_free() == 7, "9 tokens with block_size 4 need 3 blocks"
                m.fork('a', 'b')
                assert m.table('b') == m.table('a') and m.num_free() == 7, "fork must share blocks, not copy them"
                m.append('b')
                assert m.table('b')[:2] == m.table('a')[:2], "full blocks stay shared after a write"
                assert m.table('b')[2] != m.table('a')[2] and m.num_free() == 6, "writing into a shared partial block must copy-on-write"
                assert m.num_tokens('b') == 10 and m.num_tokens('a') == 9
                m.free('a')
                assert m.num_free() == 7, "freeing 'a' releases only its unshared last block"
                m.free('b')
                assert m.num_free() == 10, "everything returned after freeing both"
                m2 = C(2, block_size=2); m2.add('x'); m2.append('x', 4)
                try:
                    m2.append('x'); raise AssertionError("expected MemoryError when out of blocks")
                except MemoryError:
                    pass''',
             solution=r'''
            class BlockManager_solution:
                def __init__(self, num_blocks, block_size=16):
                    self.bs, self.free_ids = block_size, list(range(num_blocks))[::-1]
                    self.ref, self.tables, self.ntok = [0] * num_blocks, {}, {}
                def _alloc(self):
                    if not self.free_ids: raise MemoryError("out of KV blocks")
                    b = self.free_ids.pop(); self.ref[b] = 1; return b
                def _release(self, b):
                    self.ref[b] -= 1
                    if self.ref[b] == 0: self.free_ids.append(b)
                def add(self, seq): self.tables[seq], self.ntok[seq] = [], 0
                def append(self, seq, n=1):
                    for _ in range(n):
                        t, k = self.tables[seq], self.ntok[seq]
                        if k % self.bs == 0:                                  # empty or last block full
                            t.append(self._alloc())
                        elif self.ref[t[-1]] > 1:                             # shared partial block -> copy-on-write
                            new = self._alloc(); self._release(t[-1]); t[-1] = new
                        self.ntok[seq] = k + 1
                def fork(self, parent, child):
                    self.tables[child] = list(self.tables[parent]); self.ntok[child] = self.ntok[parent]
                    for b in self.tables[child]: self.ref[b] += 1
                def free(self, seq):
                    for b in self.tables.pop(seq): self._release(b)
                    del self.ntok[seq]
                def num_free(self): return len(self.free_ids)
                def table(self, seq): return list(self.tables[seq])
                def num_tokens(self, seq): return self.ntok[seq]'''),
    ],
    explore=r'''
# Parallel sampling: 4 completions share one 600-token prompt.
m = BlockManager_solution(400, 16); m.add('prompt'); m.append('prompt', 600)
for i in range(4):
    m.fork('prompt', f's{i}'); m.append(f's{i}', 100)
used = 400 - m.num_free()
print(f"shared prompt + 4 x 100-token samples use {used} blocks; without sharing it would be {4 * math.ceil(700 / 16)} blocks")''',
    takeaways='''
    - Blocks plus a per-sequence **block table** let the KV cache grow without contiguous reservations, wasting less than one block per sequence.
    - **Reference counts and copy-on-write** let parallel samples and beam candidates share their prompt's KV memory.
    - vLLM's default block size is **16** tokens. It reported **2–4×** throughput over FasterTransformer and Orca at the same latency.''',
))

# ------------------------------------------------------------------ 08
NBS.append(dict(
    slug='08_prefix_cache', title='08 · Prefix caching with a token trie (RadixAttention-style)', deck='inference/05-paged-attention/', deck_name='PagedAttention and prefix caching', minutes=35,
    goals='a cache that reuses the KV of shared prompt prefixes (system prompts, few-shot examples, multi-turn chat) with LRU eviction of leaves, as in SGLang\'s RadixAttention, simplified to one token per node.',
    setup="print('no extra setup')",
    tasks=[
        dict(name='pc', fn='PrefixCache', title='PrefixCache', md=r'''
            Store cached token sequences in a trie (one node per token):
            - `match(tokens)`: return how many leading tokens are already cached, and mark those nodes as used now.
            - `insert(tokens)`: add any missing nodes and mark the whole path as used now. Then, while `size() > capacity`, **evict the least-recently-used leaf** (break ties by lower creation order). Evicting a leaf can turn its parent into a new leaf.
            - `size()`: number of cached tokens (nodes, excluding the root).

            Use a counter that increments on every `match` or `insert` call as the clock.''',
             starter=r'''
            class PrefixCache:
                def __init__(self, capacity):
                    # TODO
                    raise NotImplementedError
                def match(self, tokens): raise NotImplementedError
                def insert(self, tokens): raise NotImplementedError
                def size(self): raise NotImplementedError''',
             test=r'''
            def _test_PrefixCache(C):
                c = C(capacity=12)
                sys = [1, 2, 3, 4, 5]
                c.insert(sys + [10, 11]); c.insert(sys + [20, 21, 22])
                assert c.size() == 10, f"shared prefix stored once: expected 10 nodes, got {c.size()}"
                assert c.match(sys + [20, 21, 99]) == 7, "should match 5 shared + 2 tokens"
                assert c.match([9, 9]) == 0
                c.insert(sys + [30, 31, 32, 33])      # +4 -> 14 > 12: evict 2 LRU leaves from the [10, 11] branch
                assert c.size() == 12, f"capacity not enforced: {c.size()}"
                assert c.match(sys + [10, 11]) == 5, "the least recently used branch [10, 11] should have been evicted"
                assert c.match(sys + [20, 21, 22]) == 8, "recently used branch must survive"''',
             solution=r'''
            class PrefixCache_solution:
                class _N:
                    __slots__ = ('kids', 'parent', 'tok', 'used', 'order')
                    def __init__(s, parent, tok, order): s.kids, s.parent, s.tok, s.used, s.order = {}, parent, tok, 0, order
                def __init__(self, capacity):
                    self.cap, self.clock, self.n, self.created = capacity, 0, 0, 0
                    self.root = self._N(None, None, -1)
                def match(self, tokens):
                    self.clock += 1; node, k = self.root, 0
                    for t in tokens:
                        if t not in node.kids: break
                        node = node.kids[t]; node.used = self.clock; k += 1
                    return k
                def insert(self, tokens):
                    self.clock += 1; node = self.root
                    for t in tokens:
                        if t not in node.kids:
                            self.created += 1; node.kids[t] = self._N(node, t, self.created); self.n += 1
                        node = node.kids[t]; node.used = self.clock
                    while self.n > self.cap:
                        leaves, stack = [], [self.root]
                        while stack:
                            x = stack.pop()
                            if x is not self.root and not x.kids: leaves.append(x)
                            stack.extend(x.kids.values())
                        v = min(leaves, key=lambda x: (x.used, x.order))
                        del v.parent.kids[v.tok]; self.n -= 1
                def size(self): return self.n'''),
    ],
    explore=r'''
# Multi-user chat: every request starts with the same 200-token system prompt.
r = np.random.default_rng(0); sysp = list(range(1000, 1200)); c = PrefixCache_solution(capacity=3000)
hit = total = 0
for _ in range(200):
    req = sysp + list(r.integers(0, 50, int(r.integers(20, 80))))
    hit += c.match(req); total += len(req); c.insert(req)
print(f"prefix-cache hit rate over 200 requests: {hit/total:.0%} of prompt tokens skipped prefill")''',
    takeaways='''
    - Requests often share prefixes (system prompts, few-shot examples, earlier chat turns). Caching their KV skips recomputing them in prefill.
    - A tree keyed by tokens finds the longest cached prefix. LRU eviction of **leaves** keeps shared stems cached the longest.
    - SGLang's RadixAttention (a compressed radix tree) reported up to **6.4×** throughput on structured LLM programs.''',
))

# ------------------------------------------------------------------ 09
NBS.append(dict(
    slug='09_speculative_sampling', title='09 · Speculative sampling', deck='inference/06-speculative-decoding/', deck_name='Speculative decoding', minutes=45,
    goals='draft-and-verify decoding with the modified rejection rule (Leviathan et al. 2023; Chen et al. 2023), proven by a Monte Carlo test to sample from exactly the target distribution, plus the expected-speedup formula.',
    setup=r'''
V = 6
def _norm(p): p = np.asarray(p, float); return p / p.sum()
_T = np.array([_norm(np.random.default_rng(i).random(V) ** 2 + .05) for i in range(V)])          # target: next-token table by last token
_D = np.array([_norm(0.6 * _T[i] + 0.4 * np.random.default_rng(100 + i).random(V)) for i in range(V)])  # draft: a noisy copy

def target_probs(prefix): return _T[prefix[-1]]
def draft_probs(prefix):  return _D[prefix[-1]]
print('toy models ready: vocab', V, '| target_probs(prefix), draft_probs(prefix)')''',
    tasks=[
        dict(name='spec', fn='speculative_step', title='One draft-and-verify step', md=r'''
            1. **Draft** γ tokens autoregressively from `draft_probs`, remembering each draft distribution $q_i$.
            2. **Score** with the target: $p_i$ = `target_probs(prefix + drafts[:i])` for $i = 0 … γ$ (γ+1 distributions; on a GPU this is **one** batched forward pass).
            3. For each draft $x_i$: **accept** with probability $\min(1, p_i(x_i)/q_i(x_i))$. On the first rejection, sample a replacement from $\mathrm{norm}(\max(0, p_i - q_i))$ and stop.
            4. If all γ are accepted, also sample a **bonus** token from $p_γ$.

            Return `(new_tokens, n_accepted)`. Use `rng.random()` and `rng.choice(V, p=…)`.''',
             starter=r'''
            def speculative_step(prefix, target_fn, draft_fn, gamma, rng):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_speculative_step(f):
                rng = np.random.default_rng(0); N = 30000; prefix = [2]
                first, pairs = np.zeros(V), np.zeros((V, V))
                for _ in range(N):
                    toks, acc = f(prefix, target_probs, draft_probs, 3, rng)
                    assert 1 <= len(toks) <= 4 and len(toks) == acc + 1, "must return accepted drafts + exactly one extra token"
                    if len(toks) < 2:
                        toks = toks + f(prefix + toks, target_probs, draft_probs, 3, rng)[0]
                    first[toks[0]] += 1; pairs[toks[0], toks[1]] += 1
                assert np.abs(first / N - _T[2]).max() < 0.015, "first-token distribution does not match the TARGET model"
                joint = _T[2][:, None] * _T
                assert np.abs(pairs / N - joint).max() < 0.012, "two-token joint distribution does not match the target"''',
             solution=r'''
            def speculative_step_solution(prefix, target_fn, draft_fn, gamma, rng):
                ctx, drafts, qs = list(prefix), [], []
                for _ in range(gamma):                                        # 1. draft
                    q = draft_fn(ctx); x = int(rng.choice(len(q), p=q))
                    drafts.append(x); qs.append(q); ctx.append(x)
                ps = [target_fn(list(prefix) + drafts[:i]) for i in range(gamma + 1)]   # 2. verify (one batched pass)
                out = []
                for i, x in enumerate(drafts):                                # 3. accept / reject
                    if rng.random() < min(1.0, ps[i][x] / qs[i][x]):
                        out.append(x)
                    else:
                        resid = np.maximum(ps[i] - qs[i], 0); resid /= resid.sum()
                        out.append(int(rng.choice(len(resid), p=resid)))
                        return out, i
                out.append(int(rng.choice(len(ps[gamma]), p=ps[gamma])))      # 4. bonus token
                return out, gamma'''),
        dict(name='theory', fn='expected_tokens', title='Expected tokens per target pass', md=r'''
            With acceptance rate α (Leviathan et al. eq. 1), each target forward pass yields on average
            $$E[\#\text{tokens}] = \frac{1-\alpha^{\gamma+1}}{1-\alpha}$$
            For a fixed draft distribution $q$ and target distribution $p$, $\alpha = \sum_x \min(p(x), q(x))$.
            Implement `expected_tokens(alpha, gamma)`. The tests also check it against your sampler.''',
             starter=r'''
            def expected_tokens(alpha, gamma):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_expected_tokens(f):
                assert abs(f(0.8, 4) - (1 - 0.8 ** 5) / 0.2) < 1e-9
                assert abs(f(0.0, 5) - 1.0) < 1e-9, "alpha = 0 -> 1 token per pass"
                p, q = _T[0], _D[0]; a = np.minimum(p, q).sum()
                rng = np.random.default_rng(1); n = 20000; tot = 0
                for _ in range(n):                       # simulate accept/reject only: draft x ~ q, accept w.p. min(1, p/q)
                    k = 0
                    while k < 4:
                        x = rng.choice(V, p=q)
                        if rng.random() < min(1, p[x] / q[x]): k += 1
                        else: break
                    tot += k + 1
                mean = tot / n
                assert abs(mean - f(a, 4)) / f(a, 4) < 0.03, f"simulated {mean:.3f} tokens/pass vs formula {f(a, 4):.3f}"''',
             solution=r'''
            def expected_tokens_solution(alpha, gamma):
                return (1 - alpha ** (gamma + 1)) / (1 - alpha) if alpha < 1 else gamma + 1'''),
    ],
    explore=r'''
# Wall-clock speedup (Leviathan et al. Theorem 3.8): E[tokens] / (gamma*c + 1), where c = draft cost / target cost
for alpha in (0.6, 0.8, 0.9):
    best = max(range(1, 16), key=lambda g: expected_tokens_solution(alpha, g) / (g * 0.05 + 1))
    print(f"alpha={alpha}: best gamma={best:2d}  ->  speedup {expected_tokens_solution(alpha, best) / (best * 0.05 + 1):.2f}x  (c = 0.05)")''',
    takeaways='''
    - Decode is memory-bound. Verifying γ drafted tokens costs about the same as one target step, so accepted drafts are nearly free tokens.
    - The modified rejection rule makes the output distribution **identical** to sampling from the target model. Your Monte Carlo test proves it on a toy model.
    - Speedup depends on the acceptance rate α and the draft cost c. The papers reported **2–3×** (T5-XXL) and **2–2.5×** (Chinchilla 70B).''',
))

# ------------------------------------------------------------------ 10
NBS.append(dict(
    slug='10_quantization', title='10 · INT8/INT4 quantization and SmoothQuant', deck='inference/07-quantization/', deck_name='Quantization', minutes=45,
    goals='symmetric quantization (per-tensor, per-channel, per-group), a W8A8 matmul, and SmoothQuant\'s outlier migration (Xiao et al., ICML 2023), with error measurements.',
    setup=r'''
def rel_err(a, b): return float(np.linalg.norm(a - b) / np.linalg.norm(b))
rng0 = np.random.default_rng(0)
X = rng0.normal(0, 1, (64, 128)); X[:, [5, 77]] *= 40          # activations with two outlier channels (as observed in LLMs)
W = rng0.normal(0, 0.05, (128, 96))
print('X: activations [64 x 128] with outlier channels 5 and 77;  W: weights [128 x 96]')''',
    tasks=[
        dict(name='q', fn='quantize_sym', title='Symmetric quantize/dequantize', md=r'''
            `scale = max|x| / (2^{bits-1} − 1)`, `q = clip(round(x / scale), −qmax, qmax)`.
            With `axis=None` use one scale for the whole tensor. Otherwise reduce over `axis` with `keepdims=True` (e.g. `axis=0` on W[in, out] gives one scale per **output channel**).
            Return `(q, scale)`; dequantize with `q * scale`.''',
             starter=r'''
            def quantize_sym(x, bits=8, axis=None):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_quantize_sym(f):
                q, s = f(W, 8)
                assert np.abs(q).max() <= 127 and np.allclose(q, np.round(q)), "int8 values must be integers in [-127, 127]"
                assert np.abs(q * s - W).max() <= np.max(s) / 2 + 1e-12, "error must be at most half a step"
                q4, s4 = f(W, 4, axis=0)
                assert np.shape(s4) == (1, 96), f"per-output-channel scales should have shape (1, 96), got {np.shape(s4)}"
                assert np.abs(q4).max() <= 7
                Wm = W.copy(); Wm[:, 0] *= 30
                assert rel_err(f(Wm, 8, 0)[0] * f(Wm, 8, 0)[1], Wm) < rel_err(f(Wm, 8)[0] * f(Wm, 8)[1], Wm), "per-channel should beat per-tensor when channel ranges differ"''',
             solution=r'''
            def quantize_sym_solution(x, bits=8, axis=None):
                qmax = 2 ** (bits - 1) - 1
                amax = np.abs(x).max() if axis is None else np.abs(x).max(axis=axis, keepdims=True)
                scale = np.maximum(amax, 1e-12) / qmax
                return np.clip(np.round(x / scale), -qmax, qmax), scale'''),
        dict(name='w8a8', fn='w8a8_matmul', title='A W8A8 matmul', md=r'''
            Quantize **X per-tensor** and **W per-output-channel** to INT8, multiply the integer matrices (use `np.int64` to stand in for INT32 accumulation), then rescale to float: `Y ≈ (qX @ qW) * sX * sW`.''',
             starter=r'''
            def w8a8_matmul(X, W, quant=None):
                quant = quant or quantize_sym
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_w8a8_matmul(f):
                Xs = rng0.normal(0, 1, (16, 128)); ref = Xs @ W
                assert rel_err(f(Xs, W), ref) < 0.02, "W8A8 on well-behaved activations should be within ~2% of FP"
                assert rel_err(f(X, W), X @ W) > 0.02, "(sanity) outlier activations should hurt per-tensor W8A8"''',
             solution=r'''
            def w8a8_matmul_solution(X, W, quant=None):
                quant = quant or quantize_sym_solution
                qx, sx = quant(X, 8)               # per-tensor activations
                qw, sw = quant(W, 8, axis=0)       # per-output-channel weights, shape (1, out)
                return (qx.astype(np.int64) @ qw.astype(np.int64)) * sx * sw'''),
        dict(name='smooth', fn='smoothquant', title='SmoothQuant: migrate outliers into the weights', md=r'''
            Per input channel $j$: $s_j = \max|X_{:,j}|^{\alpha} / \max|W_{j,:}|^{1-\alpha}$ (paper eq. 4, α = 0.5 by default).
            Return `(X / s, W * s[:, None], s)`. The product is **mathematically unchanged**: $(X\,\mathrm{diag}(s)^{-1})(\mathrm{diag}(s)\,W) = XW$.''',
             starter=r'''
            def smoothquant(X, W, alpha=0.5):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _w8a8_ref(A, B):
                qa = lambda x, ax: (lambda s: (np.clip(np.round(x / s), -127, 127), s))(np.maximum(np.abs(x).max(axis=ax, keepdims=ax is not None), 1e-12) / 127)
                (x8, sx), (w8, sw) = qa(A, None), qa(B, 0)
                return (x8.astype(np.int64) @ w8.astype(np.int64)) * sx * sw

            def _test_smoothquant(f):
                Xs, Ws, s = f(X, W, 0.5)
                assert s.shape == (128,), f"one factor per input channel: shape {s.shape}"
                assert np.allclose(Xs @ Ws, X @ W, atol=1e-9), "smoothing must not change X @ W"
                before = rel_err(_w8a8_ref(X, W), X @ W); after = rel_err(_w8a8_ref(Xs, Ws), X @ W)
                assert after < 0.5 * before, f"smoothing should at least halve W8A8 error (before {before:.3f}, after {after:.3f})"''',
             solution=r'''
            def smoothquant_solution(X, W, alpha=0.5):
                s = np.abs(X).max(axis=0) ** alpha / np.maximum(np.abs(W).max(axis=1), 1e-12) ** (1 - alpha)
                return X / s, W * s[:, None], s'''),
    ],
    explore=r'''
print(f"W8A8 error, raw outlier activations : {rel_err(w8a8_matmul_solution(X, W), X @ W):.3%}")
for a in (0.25, 0.5, 0.75, 0.9):
    Xs, Ws, _ = smoothquant_solution(X, W, a)
    print(f"W8A8 error after SmoothQuant a={a:<4}: {rel_err(w8a8_matmul_solution(Xs, Ws), X @ W):.3%}")
for g in (128, 32, 8):
    Wg = W.reshape(128 // g, g, 96); q, s = quantize_sym_solution(Wg, 4, axis=1)
    print(f"INT4 weight-only, group size {g:3d}: weight error {rel_err((q * s).reshape(128, 96), W):.2%}")''',
    takeaways='''
    - Quantization error scales with the **range** each scale must cover. Per-channel and per-group scales shrink that range.
    - LLM activations have **outlier channels** that break per-tensor INT8. SmoothQuant moves that difficulty into the weights with an exactly equivalent rescaling (**up to 1.56× faster, 2× less memory** reported).
    - Weight-only methods (GPTQ, AWQ) push weights to 3–4 bits. AWQ protects the ~1% of salient weights identified from activation statistics.''',
))

# ------------------------------------------------------------------ 11
NBS.append(dict(
    slug='11_fp8_emulation', title='11 · FP8 (E4M3 / E5M2) emulation', deck='inference/07-quantization/', deck_name='Quantization', minutes=30,
    goals='the two FP8 formats from Micikevicius et al. (2022): enumerate every representable value, round with saturation, and see why per-tensor scaling is needed.',
    setup="print('formats: e4m3 (bias 7, 3 mantissa bits, no infinities) and e5m2 (bias 15, 2 mantissa bits, IEEE-style specials)')",
    tasks=[
        dict(name='grid', fn='fp8_grid', title='Every representable value', md=r'''
            Return a sorted array of all **finite, non-negative** values (including 0):
            - Exponent field `e`, mantissa field `m`. Subnormals: `e == 0` → $m/2^{M} \cdot 2^{1-bias}$. Normals: $(1 + m/2^{M}) \cdot 2^{e-bias}$.
            - **e4m3**: bias 7, M = 3, e ∈ 0..15, but `e=15, m=7` is NaN (no infinities) → max **448**.
            - **e5m2**: bias 15, M = 2, e ∈ 0..30 (e = 31 is reserved for inf/NaN) → max **57,344**.''',
             starter=r'''
            def fp8_grid(fmt):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_fp8_grid(f):
                a, b = f('e4m3'), f('e5m2')
                assert len(a) == 127 and len(b) == 124, f"expected 127 (e4m3) and 124 (e5m2) finite non-negative values, got {len(a)}, {len(b)}"
                assert a.max() == 448 and b.max() == 57344, "max normals are 448 (e4m3) and 57,344 (e5m2)"
                assert a[1] == 2.0 ** -9 and b[1] == 2.0 ** -16, "smallest subnormals are 2^-9 and 2^-16"
                assert np.all(np.diff(a) > 0), "grid must be sorted and unique"''',
             solution=r'''
            def fp8_grid_solution(fmt):
                bias, M, emax = (7, 3, 15) if fmt == 'e4m3' else (15, 2, 30)
                vals = []
                for e in range(emax + 1):
                    for m in range(2 ** M):
                        if fmt == 'e4m3' and e == 15 and m == 7: continue      # NaN
                        vals.append((m / 2 ** M) * 2.0 ** (1 - bias) if e == 0 else (1 + m / 2 ** M) * 2.0 ** (e - bias))
                return np.array(sorted(vals))'''),
        dict(name='cast', fn='to_fp8', title='Round to FP8 (saturating)', md=r'''
            Round every element to the **nearest** representable value (keep the sign) and **saturate** magnitudes beyond the max to ±max.''',
             starter=r'''
            def to_fp8(x, fmt, grid=None):
                grid = fp8_grid(fmt) if grid is None else grid
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _grid_ref(fmt):
                bias, M, emax = (7, 3, 15) if fmt == 'e4m3' else (15, 2, 30)
                v = [(m / 2 ** M) * 2.0 ** (1 - bias) if e == 0 else (1 + m / 2 ** M) * 2.0 ** (e - bias)
                     for e in range(emax + 1) for m in range(2 ** M) if not (fmt == 'e4m3' and e == 15 and m == 7)]
                return np.array(sorted(v))

            def _test_to_fp8(f):
                g = _grid_ref('e4m3')
                assert f(np.array([1000.0, -1000.0]), 'e4m3', g).tolist() == [448.0, -448.0], "saturate to ±448"
                x = np.random.default_rng(0).uniform(0.02, 400, 5000) * np.random.default_rng(1).choice([-1, 1], 5000)
                y = f(x, 'e4m3', g)
                assert np.isin(np.abs(y), g).all(), "outputs must be representable e4m3 values"
                assert (np.abs(y - x) / np.abs(x)).max() <= 2 ** -4 + 1e-12, "relative rounding error in the normal range must be <= 2^-4 (half a step with 3 mantissa bits)"''',
             solution=r'''
            def to_fp8_solution(x, fmt, grid=None):
                g = fp8_grid_solution(fmt) if grid is None else grid
                a = np.minimum(np.abs(x), g[-1])
                i = np.clip(np.searchsorted(g, a), 1, len(g) - 1)
                lo, hi = g[i - 1], g[i]
                return np.sign(x) * np.where(a - lo <= hi - a, lo, hi)'''),
        dict(name='scale', fn='scaled_fp8', title='Per-tensor scaling', md=r'''
            Small values underflow without scaling. Implement `scale = amax / fmt_max`, cast `x / scale` to FP8, and return `(dequantized, scale)`.''',
             starter=r'''
            def scaled_fp8(x, fmt):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _cast_ref(x, g):
                a = np.minimum(np.abs(x), g[-1]); i = np.clip(np.searchsorted(g, a), 1, len(g) - 1)
                return np.sign(x) * np.where(a - g[i - 1] <= g[i] - a, g[i - 1], g[i])

            def _test_scaled_fp8(f):
                x = np.random.default_rng(2).normal(0, 1e-4, 4096)
                gg = np.array(sorted([(m / 8) * 2.0 ** -6 if e == 0 else (1 + m / 8) * 2.0 ** (e - 7) for e in range(16) for m in range(8) if not (e == 15 and m == 7)]))
                naive = _cast_ref(x, gg); y, s = f(x, 'e4m3')
                e = lambda a: np.linalg.norm(a - x) / np.linalg.norm(x)
                assert e(naive) > 0.5, "(sanity) unscaled tiny values mostly underflow"
                assert e(y) < 0.05, f"scaled FP8 error should be < 5%, got {e(y):.3f}"''',
             solution=r'''
            def scaled_fp8_solution(x, fmt):
                fmax = 448.0 if fmt == 'e4m3' else 57344.0
                scale = max(np.abs(x).max(), 1e-30) / fmax
                return to_fp8_solution(x / scale, fmt) * scale, scale'''),
    ],
    explore=r'''
for fmt in ('e4m3', 'e5m2'):
    g = fp8_grid_solution(fmt)
    print(f"{fmt}: {len(g)} finite non-negative values, max {g[-1]:g}, smallest subnormal {g[1]:.3g}, relative step ~2^-{3 if fmt=='e4m3' else 2}")
print("e4m3 trades range for precision (often used for weights/activations); e5m2 trades precision for range (often used for gradients).")''',
    takeaways='''
    - E4M3 has max 448 and more precision; E5M2 has max 57,344 and more range. Micikevicius et al. (2022) reported matching 16-bit training quality on models up to 175B.
    - FP8's range is small, so real systems keep **scaling factors** (per tensor or per block) alongside the FP8 data.
    - The same idea, small formats plus scales, carries on to FP4 microscaling formats.''',
))

# ------------------------------------------------------------------ 12
NBS.append(dict(
    slug='12_tensor_parallel', title='12 · Tensor-parallel linear layers (Megatron-style)', deck='inference/08-parallelism/', deck_name='Parallelism for inference', minutes=35,
    goals='column- and row-parallel matmuls over simulated GPUs, and a tensor-parallel MLP that needs exactly one all-reduce.',
    setup=r'''
def gelu(x): return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x ** 3)))

def all_reduce(parts, comm):
    """Sum tensors held by different ranks; log the op and the size of the reduced tensor."""
    comm.append(('all_reduce', parts[0].size)); return sum(parts)

def all_gather(parts, axis, comm):
    comm.append(('all_gather', sum(p.size for p in parts))); return np.concatenate(parts, axis=axis)

r = np.random.default_rng(0)
X = r.normal(size=(8, 32)); W1 = r.normal(0, .2, (32, 128)); W2 = r.normal(0, .2, (128, 32))
print('X [8x32], W1 [32x128], W2 [128x32]; helpers all_reduce(parts, comm), all_gather(parts, axis, comm)')''',
    tasks=[
        dict(name='col', fn='column_parallel', title='Column-parallel linear', md=r'''
            Split `W` along its **output** columns into `n` shards. Each rank computes `X @ W_i` (no communication).
            Return the **list** of per-rank outputs; the caller decides whether to gather them.''',
             starter=r'''
            def column_parallel(X, W, n):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_column_parallel(f):
                parts = f(X, W1, 4)
                assert len(parts) == 4 and parts[0].shape == (8, 32), "4 ranks, each [8 x 128/4]"
                assert np.allclose(np.concatenate(parts, 1), X @ W1), "concatenated shards must equal X @ W1"''',
             solution=r'''
            def column_parallel_solution(X, W, n):
                return [X @ Wi for Wi in np.split(W, n, axis=1)]'''),
        dict(name='row', fn='row_parallel', title='Row-parallel linear', md=r'''
            The input arrives **already split** along its feature dimension: `X_parts[i]` has shape [T, in/n]. Split `W` along its **input** rows to match, compute the partial products `X_i @ W_i`, and **all-reduce** (sum) them with `all_reduce(parts, comm)`.''',
             starter=r'''
            def row_parallel(X_parts, W, comm):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_row_parallel(f):
                comm = []; H = gelu(X @ W1)
                y = f(np.split(H, 4, axis=1), W2, comm)
                assert np.allclose(y, H @ W2), "row-parallel result must equal the full matmul"
                assert comm == [('all_reduce', 8 * 32)], f"expected exactly one all-reduce of an 8x32 tensor, got {comm}"''',
             solution=r'''
            def row_parallel_solution(X_parts, W, comm):
                W_parts = np.split(W, len(X_parts), axis=0)
                return all_reduce([x @ w for x, w in zip(X_parts, W_parts)], comm)'''),
        dict(name='mlp', fn='tp_mlp', title='Tensor-parallel MLP with one all-reduce', md=r'''
            Compute `gelu(X @ W1) @ W2` across `n` ranks: **column-parallel** W1, apply GELU **locally** on each shard (it's elementwise, so no communication), then **row-parallel** W2. Exactly one all-reduce, no all-gather.''',
             starter=r'''
            def tp_mlp(X, W1, W2, n, comm):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_tp_mlp(f):
                comm = []
                assert np.allclose(f(X, W1, W2, 4, comm), gelu(X @ W1) @ W2), "TP MLP must equal the unsplit MLP"
                assert comm == [('all_reduce', 8 * 32)], f"the MLP should need exactly ONE all-reduce, got {comm}"''',
             solution=r'''
            def tp_mlp_solution(X, W1, W2, n, comm):
                local = [gelu(h) for h in column_parallel_solution(X, W1, n)]   # no communication
                return row_parallel_solution(local, W2, comm)'''),
    ],
    explore=r'''
# Per-token communication of TP in decode: one all-reduce of d_model values per (attention or MLP) block per layer.
for name, d, layers in [('8B-shaped', 4096, 32), ('70B-shaped', 8192, 80)]:
    per_tok = 2 * layers * d * 2                    # 2 all-reduces per layer, BF16 bytes
    print(f"{name}: ~{per_tok/1e6:.2f} MB all-reduced per generated token per sequence (before ring factor 2(n-1)/n)")
print("That small, latency-sensitive traffic is why TP stays inside the NVLink domain.")''',
    takeaways='''
    - Column split → each rank owns some output features. Row split → each rank holds a partial sum that needs an **all-reduce**.
    - Column-then-row (Megatron) keeps elementwise ops local, so each MLP or attention block costs **one** all-reduce.
    - In decode those all-reduces are small and on the critical path, so TP is kept within NVLink.''',
))
