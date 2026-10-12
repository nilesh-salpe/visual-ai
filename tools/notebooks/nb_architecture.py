"""Phase 2 (The modern LLM architecture) exercise notebooks."""

SOFTMAX = r'''
def softmax(x, axis=-1):
    x = x - x.max(axis=axis, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=axis, keepdims=True)
'''

REF_ROPE = r'''
def _rope_ref(x, pos, base=10000.0):
    """Interleaved-pair RoPE as in RoFormer: pairs (x0,x1), (x2,x3), ... rotate by pos * theta_i."""
    T, d = x.shape
    theta = base ** (-np.arange(0, d, 2) / d)            # [d/2]
    ang = np.asarray(pos, float)[:, None] * theta[None]  # [T, d/2]
    c, s = np.cos(ang), np.sin(ang)
    x0, x1 = x[:, 0::2], x[:, 1::2]
    out = np.empty_like(x, dtype=float)
    out[:, 0::2] = x0 * c - x1 * s
    out[:, 1::2] = x0 * s + x1 * c
    return out
'''

REF_NORM = r'''
def _rms_ref(x, g, eps=1e-6):
    return x / np.sqrt((x * x).mean(-1, keepdims=True) + eps) * g

def _ln_ref(x, g, b, eps=1e-6):
    return (x - x.mean(-1, keepdims=True)) / np.sqrt(x.var(-1, keepdims=True) + eps) * g + b
'''

REF_SWIGLU = r'''
def _silu(x):
    return x / (1 + np.exp(-x))

def _swiglu_ref(x, W_gate, W_up, W_down):
    return (_silu(x @ W_gate) * (x @ W_up)) @ W_down
'''

NBS = []

# ------------------------------------------------------------------ 01
NBS.append(dict(
    slug='01_norms_prenorm', title='01 · RMSNorm and pre-norm blocks', deck='architecture/02-normalization/', deck_name='Pre-norm and RMSNorm', minutes=35,
    goals='LayerNorm and RMSNorm from scratch, pre-norm and post-norm residual blocks, and an experiment that shows why deep post-norm stacks are hard to train.',
    setup=SOFTMAX + REF_NORM,
    tasks=[
        dict(fn='layer_norm', title='LayerNorm (the 2017 version)', md=r'''
            For each token (row) over its features: $\mathrm{LN}(x) = g \odot \frac{x-\mu}{\sqrt{\sigma^2+\epsilon}} + b$.
            Two steps: **re-centre** (subtract the mean) and **re-scale** (divide by the standard deviation).''',
             starter=r'''
            def layer_norm(x, g, b, eps=1e-6):
                """x: [T, d]; g, b: [d]. Returns [T, d]."""
                # TODO: subtract the per-row mean, divide by sqrt(per-row variance + eps), then scale by g and shift by b
                raise NotImplementedError''',
             test=r'''
            def _test_layer_norm(f):
                r = np.random.default_rng(1); x = r.normal(3, 2, (6, 16)); g = r.normal(1, .1, 16); b = r.normal(0, .1, 16)
                y = f(x, g, b)
                assert y.shape == x.shape, f"shape {y.shape} != {x.shape}"
                assert np.allclose(y, _ln_ref(x, g, b), atol=1e-6), "values differ: normalize over the LAST axis and use the variance inside the sqrt"''',
             solution=r'''
            def layer_norm_solution(x, g, b, eps=1e-6):
                mu = x.mean(-1, keepdims=True)
                var = x.var(-1, keepdims=True)
                return (x - mu) / np.sqrt(var + eps) * g + b'''),
        dict(fn='rms_norm', title='RMSNorm (what Llama uses)', md=r'''
            Zhang & Sennrich (2019) drop the re-centring step and keep only re-scaling:
            $$\mathrm{RMSNorm}(x) = g \odot \frac{x}{\sqrt{\tfrac{1}{d}\sum_i x_i^2 + \epsilon}}$$
            No mean, no bias. The tests check two properties: the output's RMS is about 1 (when $g=1$), and scaling the input by any $c>0$ leaves the output unchanged (**re-scaling invariance**).''',
             starter=r'''
            def rms_norm(x, g, eps=1e-6):
                """x: [T, d]; g: [d]. Returns [T, d]."""
                # TODO: divide each row by its root-mean-square (sqrt(mean(x**2) + eps)), then scale by g
                raise NotImplementedError''',
             test=r'''
            def _test_rms_norm(f):
                r = np.random.default_rng(2); x = r.normal(0.5, 3, (6, 32)); g = r.normal(1, .1, 32)
                y = f(x, g)
                assert y.shape == x.shape, f"shape {y.shape} != {x.shape}"
                assert np.allclose(y, _rms_ref(x, g), atol=1e-6), "values differ: use sqrt(mean(x**2) + eps) per row, and do NOT subtract the mean"
                one = f(x, np.ones(32))
                assert np.allclose(np.sqrt((one ** 2).mean(-1)), 1, atol=1e-4), "with g = 1 every output row should have RMS ≈ 1"
                assert np.allclose(f(7.5 * x, g), y, atol=1e-5), "RMSNorm must be invariant to scaling the input by a positive constant"
                assert not np.allclose(f(x + 10, g), f(x, g), atol=1e-2), "RMSNorm should NOT be shift-invariant (it does not subtract the mean)"''',
             solution=r'''
            def rms_norm_solution(x, g, eps=1e-6):
                rms = np.sqrt((x * x).mean(-1, keepdims=True) + eps)
                return x / rms * g'''),
        dict(fn='pre_norm_block', title='Pre-norm vs post-norm residual blocks', md=r'''
            The 2017 Transformer is **post-norm**: $x_{l+1} = \mathrm{Norm}(x_l + F(x_l))$.
            GPT-2, GPT-3 and Llama are **pre-norm**: $x_{l+1} = x_l + F(\mathrm{Norm}(x_l))$.
            In pre-norm the residual stream is a clean sum: nothing ever rescales $x_l$ on its way to the output.

            Implement both. `F` is any function [T, d] → [T, d]; `norm` is any function [T, d] → [T, d].''',
             starter=r'''
            def pre_norm_block(x, F, norm):
                # TODO: x + F(norm(x))
                raise NotImplementedError

            def post_norm_block(x, F, norm):
                # TODO: norm(x + F(x))
                raise NotImplementedError''',
             test=r'''
            def _test_pre_norm_block(f):
                r = np.random.default_rng(3); x = r.normal(size=(4, 8)); W = r.normal(size=(8, 8)) * .3
                F = lambda h: np.tanh(h @ W); nrm = lambda h: _rms_ref(h, np.ones(8))
                assert np.allclose(f(x, F, nrm), x + F(nrm(x))), "pre-norm must be x + F(norm(x))"
                post = post_norm_block_solution if f.__name__.endswith('_solution') else post_norm_block
                assert np.allclose(post(x, F, nrm), nrm(x + F(x))), "post-norm must be norm(x + F(x)); implement post_norm_block too"''',
             solution=r'''
            def pre_norm_block_solution(x, F, norm):
                return x + F(norm(x))

            def post_norm_block_solution(x, F, norm):
                return norm(x + F(x))'''),
    ],
    explore_md=r'''
        **Reproduce Xiong et al.'s (2020) finding at toy scale.** Build stacks of $L$ blocks (FFN sublayers, Xavier init, LayerNorm as in the paper) in both arrangements, and measure the gradient norm of the **last layer's** weights for a simple squared-error loss. The gradient is estimated by finite differences along 64 random directions, since $\mathbb{E}[(\nabla\cdot U)^2] = \|\nabla\|^2$ for Gaussian $U$.

        Paper's result: for post-LN the gradient near the output **does not shrink with depth**, while for pre-LN it scales like $1/\sqrt{L}$. Large gradients at initialization combined with a large learning rate make post-LN unstable, which is why it needs a warm-up, and pre-LN does not.

        These are random weights, so read the *trend* across depths, not the exact values.''',
    explore=r'''
        def grad_norm_last_layer(kind, L, T=16, d=64, n_dirs=64, seed=0):
            r = np.random.default_rng(seed + L)
            W1 = [r.normal(0, np.sqrt(2 / (5 * d)), (d, 4 * d)) for _ in range(L)]
            W2 = [r.normal(0, np.sqrt(2 / (5 * d)), (4 * d, d)) for _ in range(L)]
            x0, target = r.normal(size=(T, d)), r.normal(size=(T, d))
            ln = lambda h: layer_norm_solution(h, np.ones(d), np.zeros(d))
            def loss(W_last):
                x = x0
                for i in range(L):
                    Wb = W_last if i == L - 1 else W2[i]
                    F = lambda h, Wa=W1[i], Wb=Wb: np.maximum(0, h @ Wa) @ Wb
                    x = pre_norm_block_solution(x, F, ln) if kind == 'pre' else post_norm_block_solution(x, F, ln)
                if kind == 'pre':
                    x = ln(x)          # pre-norm models need a final norm
                return 0.5 * ((x - target) ** 2).sum()
            base, eps = loss(W2[-1]), 1e-6
            est = [((loss(W2[-1] + eps * U) - base) / eps) ** 2 for U in r.normal(size=(n_dirs,) + W2[-1].shape)]
            return np.sqrt(np.mean(est))

        depths = [3, 6, 12, 24, 48]
        print('depth L:                    ' + ''.join(f'{L:>8}' for L in depths))
        for kind in ['post', 'pre']:
            print(f'{kind}-norm last-layer |grad|: ' + ''.join(f'{grad_norm_last_layer(kind, L):8.1f}' for L in depths))
        print('1/sqrt(L) relative to L=3:    ' + ''.join(f'{np.sqrt(3 / L):8.2f}' for L in depths))''',
    takeaways=r'''
        * RMSNorm keeps LayerNorm's re-scaling and drops the re-centring: fewer operations, same quality (7–64% less running time in Zhang & Sennrich).
        * Post-norm puts a norm on the main path after every block. At initialization the gradient of the layers near the output stays large however deep the model is, so it needs a learning-rate warm-up (Xiong et al., 2020).
        * Pre-norm keeps an identity path from every layer to the output, and its gradients shrink like $1/\sqrt{L}$. It trains stably without warm-up, which is why GPT-2, GPT-3, Llama and almost every modern decoder use it. The price: the residual stream's scale grows with depth, so a **final norm** before the output head is required.''',
))

# ------------------------------------------------------------------ 02
NBS.append(dict(
    slug='02_rope', title='02 · Rotary position embeddings (RoPE)', deck='architecture/03-rope/', deck_name='RoPE', minutes=40,
    goals='RoPE in its rotation form and complex-number form, and tests that prove the key property: the attention score depends only on the distance between tokens.',
    setup=SOFTMAX + REF_ROPE,
    tasks=[
        dict(fn='rope', title='RoPE as pairwise rotations', md=r'''
            Split each vector of width $d$ into $d/2$ pairs $(x_{2i}, x_{2i+1})$. Pair $i$ has frequency
            $$\theta_i = \text{base}^{-2i/d},\quad i = 0,\dots,d/2-1 \qquad(\text{base} = 10000 \text{ in RoFormer})$$
            At position $m$, rotate pair $i$ by angle $m\theta_i$:
            $$\begin{pmatrix}x'_{2i}\\x'_{2i+1}\end{pmatrix}=\begin{pmatrix}\cos m\theta_i & -\sin m\theta_i\\ \sin m\theta_i & \cos m\theta_i\end{pmatrix}\begin{pmatrix}x_{2i}\\x_{2i+1}\end{pmatrix}$$
            RoPE is applied to **queries and keys only**, never to values, after the $W_q$ / $W_k$ projections.

            > Llama's code pairs dimension $i$ with $i + d/2$ ("rotate half") instead of neighbours. That is the same idea with the dimensions permuted. Here we use the paper's neighbouring pairs.''',
             starter=r'''
            def rope(x, pos, base=10000.0):
                """x: [T, d] (d even); pos: [T] integer positions. Returns rotated [T, d]."""
                # TODO: theta = base ** (-arange(0, d, 2) / d); angle = pos[:, None] * theta
                #       rotate each pair (x[:, 0::2], x[:, 1::2]) by its angle
                raise NotImplementedError''',
             test=r'''
            def _test_rope(f):
                r = np.random.default_rng(1); x = r.normal(size=(6, 16)); pos = np.array([0, 1, 2, 7, 100, 4096])
                y = f(x, pos)
                assert y.shape == x.shape, f"shape {y.shape} != {x.shape}"
                assert np.allclose(y[0], x[0]), "position 0 must be the identity (angle 0)"
                assert np.allclose(np.linalg.norm(y, axis=1), np.linalg.norm(x, axis=1)), "rotations must preserve each vector's length"
                assert np.allclose(y, _rope_ref(x, pos), atol=1e-9), "values differ: pair (x[2i], x[2i+1]) with theta_i = base**(-2i/d)"
                q, k = r.normal(size=(1, 16)), r.normal(size=(1, 16))
                s = lambda m, n: (f(q, [m]) @ f(k, [n]).T).item()
                assert np.isclose(s(5, 2), s(105, 102)) and np.isclose(s(5, 2), s(3, 0)), "score must depend only on m - n"''',
             solution=r'''
            def rope_solution(x, pos, base=10000.0):
                T, d = x.shape
                theta = base ** (-np.arange(0, d, 2) / d)
                ang = np.asarray(pos, float)[:, None] * theta[None, :]
                c, s = np.cos(ang), np.sin(ang)
                out = np.empty_like(x, dtype=float)
                out[:, 0::2] = x[:, 0::2] * c - x[:, 1::2] * s
                out[:, 1::2] = x[:, 0::2] * s + x[:, 1::2] * c
                return out'''),
        dict(fn='rope_complex', title='The same thing with complex numbers', md=r'''
            RoFormer writes RoPE as $f(x, m) = x\,e^{i m\theta}$: treat each pair as a complex number $x_{2i} + i\,x_{2i+1}$ and **multiply** by $e^{i m \theta_i}$.
            This is how many production implementations do it (`torch.polar` in Meta's Llama code).
            It also makes the relative-position proof one line:
            $\langle q e^{im\theta}, k e^{in\theta}\rangle = \mathrm{Re}[q\,\bar k\, e^{i(m-n)\theta}]$, which depends only on $m-n$.''',
             starter=r'''
            def rope_complex(x, pos, base=10000.0):
                """Same contract as rope(), implemented with complex multiplication."""
                # TODO: z = x[:, 0::2] + 1j * x[:, 1::2]; z *= exp(1j * pos[:, None] * theta); write real/imag back into pairs
                raise NotImplementedError''',
             test=r'''
            def _test_rope_complex(f):
                r = np.random.default_rng(2); x = r.normal(size=(5, 32)); pos = np.array([0, 3, 17, 512, 9999])
                y = f(x, pos)
                assert y.shape == x.shape, f"shape {y.shape} != {x.shape}"
                assert np.allclose(y, _rope_ref(x, pos), atol=1e-9), "complex form must match the rotation form exactly"''',
             solution=r'''
            def rope_complex_solution(x, pos, base=10000.0):
                d = x.shape[1]
                theta = base ** (-np.arange(0, d, 2) / d)
                z = (x[:, 0::2] + 1j * x[:, 1::2]) * np.exp(1j * np.asarray(pos, float)[:, None] * theta[None, :])
                out = np.empty_like(x, dtype=float)
                out[:, 0::2], out[:, 1::2] = z.real, z.imag
                return out'''),
        dict(fn='rope_attention_scores', title='Attention scores with RoPE', md=r'''
            Put it together for one head: given $q$ and $k$ of shape [T, d], apply RoPE at positions $0..T-1$, then return the **causal** score matrix $\frac{q'k'^\top}{\sqrt d}$ with $-\infty$ above the diagonal.
            The test shifts the whole sequence to start at position 1000 and checks that **nothing changes**. This is the property absolute position embeddings lack.''',
             starter=r'''
            def rope_attention_scores(q, k, start=0, base=10000.0):
                """q, k: [T, d]. Positions are start..start+T-1. Returns causal scores [T, T] (-inf above the diagonal)."""
                # TODO: rotate q and k with rope(..., positions), scores = q' k'^T / sqrt(d), mask the future
                raise NotImplementedError''',
             test=r'''
            def _test_rope_attention_scores(f):
                r = np.random.default_rng(3); q, k = r.normal(size=(6, 16)), r.normal(size=(6, 16))
                S0, S1 = f(q, k, 0), f(q, k, 1000)
                pos = np.arange(6); ref = _rope_ref(q, pos) @ _rope_ref(k, pos).T / 4
                tri = np.tril(np.ones((6, 6), bool))
                assert np.allclose(S0[tri], ref[tri]), "lower-triangular scores differ from reference (did you scale by 1/sqrt(d)?)"
                assert np.all(np.isneginf(S0[~tri])), "future positions must be -inf"
                assert np.allclose(S0[tri], S1[tri]), "shifting every position by 1000 must not change any score"''',
             solution=r'''
            def rope_attention_scores_solution(q, k, start=0, base=10000.0):
                T, d = q.shape; pos = start + np.arange(T)
                s = rope_solution(q, pos, base) @ rope_solution(k, pos, base).T / np.sqrt(d)
                return np.where(np.tril(np.ones((T, T), bool)), s, -np.inf)'''),
    ],
    explore_md=r'''
        **Long-term decay and the frequency spectrum.** Take $q = k = $ a vector of ones and plot the score as the distance $m-n$ grows. The high-frequency pairs spin fast and average out, while the low-frequency pairs keep the score high for longer. RoFormer §3.4.3 shows that an upper bound on the score decays with distance. Then compare base 10,000 (Llama 2) with 500,000 (Llama 3): a larger base slows every rotation, so the decay stretches over a much longer range.''',
    explore=r'''
        d = 128; q = np.ones((1, d))
        for base in [10_000, 500_000]:
            row = []
            for dist in [0, 1, 10, 100, 1_000, 10_000, 100_000]:
                row.append((rope_solution(q, [dist], base) @ rope_solution(q, [0], base).T).item() / d)
            print(f"base {base:>7,}: normalized score at distance 0,1,10,100,1k,10k,100k ->", ' '.join(f'{v:5.2f}' for v in row))
        theta = 10_000 ** (-np.arange(0, d, 2) / d)
        print("\nwavelength (tokens per full turn) of pair 0, 16, 32, 48, 63:", [f'{2 * np.pi / theta[i]:,.0f}' for i in [0, 16, 32, 48, 63]])''',
    takeaways=r'''
        * RoPE rotates each 2-D slice of $q$ and $k$ by an angle proportional to the position, with a different speed per slice.
        * Because both are rotated, the dot product sees only the **difference** of angles, so attention depends on relative position. No position vector is added to the residual stream.
        * Wavelengths range from about 6 tokens (pair 0) to about 54,000 tokens (last pair) at base 10,000. Long-context work (deck 07) is about what happens to the slow pairs beyond the training length.''',
))

# ------------------------------------------------------------------ 03
NBS.append(dict(
    slug='03_swiglu', title='03 · SwiGLU feed-forward layers', deck='architecture/04-swiglu/', deck_name='SwiGLU', minutes=30,
    goals='the SwiGLU FFN used by Llama, PaLM and Mistral, the hidden-size rule that keeps its parameter count equal to a 4d ReLU FFN, and the exact sizes of real models.',
    setup=SOFTMAX + REF_SWIGLU,
    tasks=[
        dict(fn='swiglu_ffn', title='The SwiGLU FFN', md=r'''
            The 2017 FFN is $\max(0, xW_1)W_2$. Shazeer (2020) replaces it with a **gated** linear unit:
            $$\mathrm{FFN}_{\mathrm{SwiGLU}}(x) = \big(\mathrm{Swish}(xW_{\text{gate}}) \odot xW_{\text{up}}\big)W_{\text{down}}, \qquad \mathrm{Swish}(z) = \mathrm{SiLU}(z) = z\,\sigma(z)$$
            One projection decides *how much* of each hidden unit to let through (the gate), and the other carries the *value*. That makes three weight matrices instead of two. (Llama's code calls them `w1` = gate, `w3` = up and `w2` = down.)''',
             starter=r'''
            def silu(z):
                # TODO: z * sigmoid(z)
                raise NotImplementedError

            def swiglu_ffn(x, W_gate, W_up, W_down):
                """x: [T, d]; W_gate, W_up: [d, h]; W_down: [h, d]. Returns [T, d]."""
                # TODO: (silu(x @ W_gate) * (x @ W_up)) @ W_down
                raise NotImplementedError''',
             test=r'''
            def _test_swiglu_ffn(f):
                r = np.random.default_rng(1); d, h = 16, 40
                x = r.normal(size=(5, d)); Wg, Wu, Wd = r.normal(size=(d, h)), r.normal(size=(d, h)), r.normal(size=(h, d))
                y = f(x, Wg, Wu, Wd)
                assert y.shape == (5, d), f"shape {y.shape} != (5, {d})"
                silu_ = silu_solution if f.__name__.endswith('_solution') else silu
                assert np.allclose(silu_(np.array([0.0, 1.0, -1.0])), [0, 0.7310586, -0.2689414], atol=1e-6), "silu(z) must be z * sigmoid(z)"
                assert np.allclose(y, _swiglu_ref(x, Wg, Wu, Wd), atol=1e-8), "values differ: the gate goes through silu, the up projection does not"''',
             solution=r'''
            def silu_solution(z):
                return z / (1 + np.exp(-z))

            def swiglu_ffn_solution(x, W_gate, W_up, W_down):
                return (silu_solution(x @ W_gate) * (x @ W_up)) @ W_down'''),
        dict(fn='llama_hidden_dim', title='The ⅔ rule and real hidden sizes', md=r'''
            Three matrices of size $d\times h$ cost $3dh$ parameters, while the ReLU FFN with $h = 4d$ costs $2\cdot d\cdot 4d = 8d^2$.
            To keep the budget equal, set $h = \tfrac{2}{3}\cdot 4d$ (Shazeer: 3072 → 2048; LLaMA paper: "$\tfrac{2}{3}4d$ instead of $4d$").
            Meta's code then optionally multiplies by `ffn_dim_multiplier` and rounds **up** to a multiple of `multiple_of`, which suits GPU tiles:
            ```
            hidden = int(2 * (4 * d) / 3)
            if ffn_dim_multiplier: hidden = int(ffn_dim_multiplier * hidden)
            hidden = multiple_of * ceil(hidden / multiple_of)
            ```
            Expected: LLaMA-7B (d = 4096, multiple_of = 256) gives **11,008**. Llama-3-8B (d = 4096, multiplier 1.3, multiple_of = 1024) gives **14,336**.''',
             starter=r'''
            def llama_hidden_dim(d, multiple_of=256, ffn_dim_multiplier=None):
                # TODO: follow the three lines above
                raise NotImplementedError''',
             test=r'''
            def _test_llama_hidden_dim(f):
                assert f(4096) == 11008, f"LLaMA-7B: got {f(4096)}, expected 11008"
                assert f(5120) == 13824, f"LLaMA-13B: got {f(5120)}, expected 13824"
                assert f(8192) == 22016, f"LLaMA-65B: got {f(8192)}, expected 22016"
                assert f(4096, 1024, 1.3) == 14336, f"Llama-3-8B: got {f(4096, 1024, 1.3)}, expected 14336"
                assert f(768, 1) == 2048, f"Shazeer's T5-base setting (d=768, no rounding): got {f(768, 1)}, expected 2048"''',
             solution=r'''
            def llama_hidden_dim_solution(d, multiple_of=256, ffn_dim_multiplier=None):
                hidden = int(2 * (4 * d) / 3)
                if ffn_dim_multiplier is not None:
                    hidden = int(ffn_dim_multiplier * hidden)
                return multiple_of * ((hidden + multiple_of - 1) // multiple_of)'''),
        dict(fn='ffn_params', title='Count the parameters', md=r'''
            Return the number of weight parameters (no biases; modern LLMs drop them) of one FFN:
            * `kind='relu'`: two matrices, $2dh$
            * `kind='swiglu'`: three matrices, $3dh$

            The test checks that SwiGLU at the ⅔ width costs the same as ReLU at $4d$ (up to rounding), and that the FFN is about two thirds of a Llama-3-8B layer.''',
             starter=r'''
            def ffn_params(d, h, kind):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_ffn_params(f):
                assert f(768, 3072, 'relu') == 768 * 3072 * 2
                assert f(768, 2048, 'swiglu') == f(768, 3072, 'relu'), "SwiGLU at 2048 must equal ReLU at 3072 for d = 768"
                ffn = f(4096, 14336, 'swiglu'); attn = 2 * 4096 * 4096 + 2 * 4096 * 1024
                assert ffn == 176_160_768, f"Llama-3-8B FFN params per layer: got {ffn:,}, expected 176,160,768"
                assert 0.80 < ffn / (ffn + attn) < 0.81, "the FFN should be about 81% of a Llama-3-8B layer's matmul parameters"''',
             solution=r'''
            def ffn_params_solution(d, h, kind):
                return {'relu': 2, 'swiglu': 3}[kind] * d * h'''),
    ],
    explore_md=r'''
        **What does the gate do?** For a few random inputs, look at how many hidden units each FFN effectively switches off. ReLU zeroes units with a hard cut. SiLU is smooth, slightly negative for negative inputs, and the separate *up* projection can flip the sign of what passes through. Then compare Shazeer's reported held-out log-perplexities (T5-base on C4, lower is better).''',
    explore=r'''
        r = np.random.default_rng(0); d = 64; h_relu, h_glu = 256, llama_hidden_dim_solution(d, 1)
        x = r.normal(size=(2000, d)); W1 = r.normal(0, d ** -.5, (d, h_relu)); Wg = r.normal(0, d ** -.5, (d, h_glu)); Wu = r.normal(0, d ** -.5, (d, h_glu))
        relu_h = np.maximum(0, x @ W1); glu_h = silu_solution(x @ Wg) * (x @ Wu)
        print(f"hidden units: ReLU {h_relu}, SwiGLU {h_glu} (same params: {2 * d * h_relu:,} vs {3 * d * h_glu:,})")
        print(f"fraction of hidden activations exactly 0: ReLU {np.mean(relu_h == 0):.2f}, SwiGLU {np.mean(glu_h == 0):.2f}")
        print(f"fraction negative:                        ReLU {np.mean(relu_h < 0):.2f}, SwiGLU {np.mean(glu_h < 0):.2f}")
        print("\nShazeer (2020) Table 1, held-out log-perplexity:")
        for name, a, b in [('ReLU (baseline)', 1.997, 1.677), ('GELU', 1.983, 1.679), ('GEGLU', 1.942, 1.633), ('SwiGLU', 1.944, 1.636)]:
            print(f"  {name:16} 65,536 steps: {a:.3f}   524,288 steps: {b:.3f}")''',
    takeaways=r'''
        * SwiGLU = SiLU-gated linear unit: a multiplicative gate plus a value projection, three matrices.
        * The hidden size shrinks to about ⅔·4d so the parameter budget stays the same, then real models round up to hardware-friendly multiples.
        * The FFN is about 80% of a Llama-3-8B layer's matmul parameters (the GQA attention is small). Most of a dense model's parameters and FLOPs live here, which is why Mixture-of-Experts (deck 10) replaces exactly this block.''',
))

# ------------------------------------------------------------------ 04
NBS.append(dict(
    slug='04_mla_absorption', title='04 · Multi-head latent attention (MLA) and weight absorption', deck='architecture/05-attention-variants/', deck_name='MQA → GQA → MLA', minutes=45,
    goals="DeepSeek-V2's latent KV cache, the 'absorb W_UK into W_Q' trick that avoids decompressing keys, a demonstration that RoPE breaks the trick, and the decoupled-RoPE fix.",
    setup=SOFTMAX + REF_ROPE + r'''
r = np.random.default_rng(0)
d, n_h, d_h, d_c, d_R = 64, 4, 16, 8, 4          # model width, heads, head dim, latent dim, RoPE dim
W_DKV = r.normal(0, d ** -.5, (d, d_c))           # down-projection: x -> latent c (this is what gets cached)
W_UK = r.normal(0, d_c ** -.5, (n_h, d_c, d_h))   # per-head up-projection: c -> key
W_UV = r.normal(0, d_c ** -.5, (n_h, d_c, d_h))   # per-head up-projection: c -> value
W_Q = r.normal(0, d ** -.5, (n_h, d, d_h))        # per-head query projection
W_QR = r.normal(0, d ** -.5, (n_h, d, d_R))       # per-head RoPE query
W_KR = r.normal(0, d ** -.5, (d, d_R))            # ONE RoPE key shared by all heads
X = r.normal(size=(10, d))                        # 10 tokens

def _naive_scores(x_q, C):
    """Decompress every cached latent into full keys, then do ordinary attention scores (no RoPE)."""
    return np.stack([(x_q @ W_Q[h]) @ (C @ W_UK[h]).T for h in range(n_h)]) / np.sqrt(d_h)
print(f"per-token cache: MHA would store 2*n_h*d_h = {2 * n_h * d_h} numbers; MLA stores d_c + d_R = {d_c + d_R}")
''',
    tasks=[
        dict(fn='latent_cache', title='Compress to the latent', md=r'''
            MLA caches **one small latent vector per token**, $c_t = x_t W^{DKV}$ (width $d_c$), instead of $n_h$ keys and $n_h$ values.
            Keys and values are reconstructed on demand: $k^{(h)}_t = c_t W^{UK}_h$ and $v^{(h)}_t = c_t W^{UV}_h$.''',
             starter=r'''
            def latent_cache(X):
                """X: [T, d]. Returns C: [T, d_c]."""
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_latent_cache(f):
                C = f(X)
                assert C.shape == (10, d_c), f"shape {C.shape} != (10, {d_c})"
                assert np.allclose(C, X @ W_DKV), "C must be X @ W_DKV"''',
             solution=r'''
            def latent_cache_solution(X):
                return X @ W_DKV'''),
        dict(fn='absorbed_scores', title='Absorb W_UK into the query', md=r'''
            Decompressing every past key at every step would waste the savings. Instead use associativity:
            $$q^{(h)} k^{(h)\top}_t = (x W^Q_h)(c_t W^{UK}_h)^\top = x\,\underbrace{W^Q_h W^{UK\top}_h}_{\text{precompute: } [d,\ d_c]}\,c_t^\top$$
            So the query is projected **straight into latent space** and scored against the cached $c_t$ directly. No key is ever materialized.
            Return scores of shape [n_h, T_q, T_k] (scaled by $1/\sqrt{d_h}$, no masking).''',
             starter=r'''
            def absorbed_scores(x_q, C):
                """x_q: [T_q, d]; C: [T_k, d_c] cached latents. Returns [n_h, T_q, T_k] WITHOUT computing any key."""
                # TODO: for each head, W_absorbed = W_Q[h] @ W_UK[h].T  ([d, d_c]); scores = (x_q @ W_absorbed) @ C.T / sqrt(d_h)
                raise NotImplementedError''',
             test=r'''
            def _test_absorbed_scores(f):
                C = X @ W_DKV; S = f(X[-3:], C)
                assert S.shape == (n_h, 3, 10), f"shape {S.shape} != ({n_h}, 3, 10)"
                assert np.allclose(S, _naive_scores(X[-3:], C), atol=1e-10), "absorbed scores must equal the decompress-then-score result exactly"''',
             solution=r'''
            def absorbed_scores_solution(x_q, C):
                return np.stack([(x_q @ (W_Q[h] @ W_UK[h].T)) @ C.T for h in range(n_h)]) / np.sqrt(d_h)'''),
        dict(fn='decoupled_rope_scores', title='Why RoPE breaks absorption, and decoupled RoPE', md=r'''
            With RoPE, the key becomes $R_t\,(c_t W^{UK}_h)$, where $R_t$ is a rotation that depends on position $t$. The middle matrix becomes $W^Q_h R_{m}^\top R_t W^{UK\top}_h$, which depends on **both positions**, so it can't be precomputed once. DeepSeek-V2: *"RoPE is incompatible with low-rank KV compression."*

            **Fix (decoupled RoPE):** carry position in a separate small slice:
            * content part: $q^{C}_h \cdot k^{C}_h$ via the absorbed latent path, with no RoPE;
            * position part: $\mathrm{RoPE}_m(x W^{QR}_h) \cdot \mathrm{RoPE}_t(x_t W^{KR})$, where the RoPE key $k^R_t$ is **shared by all heads** and cached alongside $c_t$.

            Score $= (q^C_h \cdot k^C_{h,t} + q^R_h \cdot k^R_t)/\sqrt{d_h + d_R}$. Implement it given cached `C` ([T, d_c]) and cached `KR` ([T, d_R], already rotated).''',
             starter=r'''
            def decoupled_rope_scores(x_q, q_pos, C, KR):
                """x_q: [T_q, d] at positions q_pos; C: [T_k, d_c]; KR: [T_k, d_R] rotated RoPE keys. Returns [n_h, T_q, T_k]."""
                # TODO: content = absorbed path (no RoPE); rope part = rope(x_q @ W_QR[h], q_pos) @ KR.T; sum, scale by 1/sqrt(d_h + d_R)
                raise NotImplementedError''',
             test=r'''
            def _test_decoupled_rope_scores(f):
                pos = np.arange(10); C = X @ W_DKV; KR = _rope_ref(X @ W_KR, pos)
                S = f(X[-2:], pos[-2:], C, KR)
                assert S.shape == (n_h, 2, 10), f"shape {S.shape} != ({n_h}, 2, 10)"
                ref = np.stack([((X[-2:] @ W_Q[h]) @ (C @ W_UK[h]).T + _rope_ref(X[-2:] @ W_QR[h], pos[-2:]) @ KR.T) for h in range(n_h)]) / np.sqrt(d_h + d_R)
                assert np.allclose(S, ref, atol=1e-10), "scores differ from explicit content + RoPE computation"
                S2 = f(X[-2:], pos[-2:] + 500, C, _rope_ref(X @ W_KR, pos + 500))
                assert np.allclose(S, S2, atol=1e-10), "shifting all positions must not change scores (RoPE is relative)"''',
             solution=r'''
            def decoupled_rope_scores_solution(x_q, q_pos, C, KR):
                out = []
                for h in range(n_h):
                    content = (x_q @ (W_Q[h] @ W_UK[h].T)) @ C.T
                    pos_part = _rope_ref(x_q @ W_QR[h], q_pos) @ KR.T
                    out.append(content + pos_part)
                return np.stack(out) / np.sqrt(d_h + d_R)'''),
    ],
    explore_md=r'''
        **1. See the incompatibility.** Apply RoPE directly to the decompressed keys, then try to reuse a single absorbed matrix. The error is far from zero.
        **2. Cache sizes with DeepSeek-V2's real dimensions** ($n_h=128$, $d_h=128$, $d_c=512$, $d_R=64$; numbers cached per token per layer). The paper reports MLA ≈ GQA with about 2.25 groups in cache size, with stronger quality than MHA.''',
    explore=r'''
        C = X @ W_DKV; pos = np.arange(10)
        true = np.stack([_rope_ref(X @ W_Q[h], pos) @ _rope_ref(C @ W_UK[h], pos).T for h in range(n_h)])
        fake = np.stack([(X @ (W_Q[h] @ W_UK[h].T)) @ C.T for h in range(n_h)])
        print(f"RoPE on full keys vs one precomputed absorbed matrix: max |error| = {np.abs(true - fake).max():.3f}  (not 0, so absorption fails)")
        nh, dh, dc, dR = 128, 128, 512, 64
        rows = [('MHA', 2 * nh * dh), ('GQA, 8 groups', 2 * 8 * dh), ('MQA', 2 * dh), ('MLA (d_c + d_R)', dc + dR)]
        print('\nKV-cache numbers per token per layer (DeepSeek-V2 dims):')
        for name, n in rows:
            print(f"  {name:16} {n:6,}   ({100 * n / rows[0][1]:5.1f}% of MHA)")
        print(f"  MLA expressed in head-dims: {(dc + dR) / dh:.2f} * d_h  (paper: ~9/2 d_h)")''',
    takeaways=r'''
        * MQA and GQA shrink the cache by **sharing** K/V heads. MLA shrinks it by **compressing** all heads into one latent and re-expanding on the fly.
        * Absorption ($W^QW^{UK\top}$) means the expansion never happens at inference. The query moves into latent space instead.
        * RoPE's position-dependent rotation sits between the two matrices and breaks absorption, so DeepSeek-V2 adds a small separate RoPE slice ($d_R = 64$) with a key shared across heads.''',
))

# ------------------------------------------------------------------ 05
NBS.append(dict(
    slug='05_attention_masks', title='05 · Causal, prefix-LM and document masks', deck='architecture/06-decoder-only/', deck_name='Decoder-only, and why it won', minutes=25,
    goals='the masks that define decoder-only, prefix-LM and packed-document training, plus a proof that a document mask makes a packed batch identical to running each document separately.',
    setup=SOFTMAX + r'''
def _attn(x, mask):
    s = x @ x.T / np.sqrt(x.shape[1])
    return softmax(np.where(mask, s, -np.inf)) @ x
''',
    tasks=[
        dict(fn='causal_mask', title='Causal mask', md=r'''
            Return a boolean [T, T] matrix `M` with `M[i, j] = True` when query *i* may attend to key *j*. Causal (decoder-only): $j \le i$.''',
             starter=r'''
            def causal_mask(T):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_causal_mask(f):
                M = f(5)
                assert M.dtype == bool and M.shape == (5, 5), "return a boolean [T, T] array"
                assert M[3, 3] and M[3, 0] and not M[0, 3], "row i may see columns 0..i only"
                assert M.sum() == 15, "a causal 5x5 mask has 15 allowed entries"''',
             solution=r'''
            def causal_mask_solution(T):
                return np.tril(np.ones((T, T), dtype=bool))'''),
        dict(fn='prefix_lm_mask', title='Prefix-LM (non-causal decoder) mask', md=r'''
            The first `P` tokens (the "prefix" or prompt) see **each other bidirectionally**. Later tokens are causal and see the whole prefix plus earlier targets.
            This is the "non-causal decoder" in Wang et al. (2022). It sits between an encoder-decoder and a pure causal decoder.''',
             starter=r'''
            def prefix_lm_mask(T, P):
                # TODO: start from causal, then allow every pair (i, j) with i < P and j < P
                raise NotImplementedError''',
             test=r'''
            def _test_prefix_lm_mask(f):
                M = f(6, 3)
                assert M[0, 2] and M[1, 2], "prefix tokens must see later prefix tokens"
                assert not M[2, 3], "prefix tokens must NOT see targets"
                assert M[5, 0] and M[5, 4] and not M[4, 5], "targets are causal"
                assert np.array_equal(f(6, 0), np.tril(np.ones((6, 6), bool))), "P = 0 is plain causal"''',
             solution=r'''
            def prefix_lm_mask_solution(T, P):
                M = np.tril(np.ones((T, T), dtype=bool))
                M[:P, :P] = True
                return M'''),
        dict(fn='document_mask', title='Packed documents: the document mask', md=r'''
            Pretraining packs several documents into one long sequence so no tokens are wasted on padding. Without a mask, a token can attend into the *previous, unrelated* document.
            Llama 3 (§3.2): *"we use an attention mask that prevents self-attention between different documents within the same sequence."*
            Given `doc_ids` (e.g. `[0,0,0,1,1,2,2,2]`), allow `(i, j)` only if `j <= i` **and** `doc_ids[i] == doc_ids[j]`.''',
             starter=r'''
            def document_mask(doc_ids):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_document_mask(f):
                ids = np.array([0, 0, 0, 1, 1, 2, 2, 2]); M = f(ids)
                assert M.shape == (8, 8) and M.dtype == bool
                assert not M[3, 2], "first token of doc 1 must not see doc 0"
                assert M[4, 3] and not M[3, 4], "causal inside a document"
                x = np.random.default_rng(1).normal(size=(8, 4))
                packed = _attn(x, M)
                for doc in range(3):
                    sel = ids == doc; n = sel.sum()
                    alone = _attn(x[sel], np.tril(np.ones((n, n), bool)))
                    assert np.allclose(packed[sel], alone), f"doc {doc}: packed output must equal running the document alone"''',
             solution=r'''
            def document_mask_solution(doc_ids):
                ids = np.asarray(doc_ids)
                return np.tril(np.ones((len(ids), len(ids)), dtype=bool)) & (ids[:, None] == ids[None, :])'''),
    ],
    explore_md=r'''
        **How much does packing without a mask leak?** Pack 4 documents of 64 tokens and measure the fraction of attention weight that lands in *other* documents when only a causal mask is used. Llama 3 reports the document mask had limited impact in standard pretraining but mattered for continued pretraining on very long sequences.''',
    explore=r'''
        r = np.random.default_rng(0); ids = np.repeat(np.arange(4), 64); x = r.normal(size=(256, 32))
        s = x @ x.T / np.sqrt(32); P = softmax(np.where(causal_mask_solution(256), s, -np.inf))
        cross = (P * (ids[:, None] != ids[None, :])).sum(1)
        for doc in range(4):
            print(f"doc {doc}: mean attention weight leaking into other documents = {cross[ids == doc].mean():.2f}")
        print(f"cost: a causal mask has {causal_mask_solution(256).sum():,} allowed pairs; the document mask has {document_mask_solution(ids).sum():,}")''',
    takeaways=r'''
        * The architecture families differ mostly in **the mask**: causal (GPT, Llama), prefix-LM (non-causal decoder), encoder-decoder (T5, the 2017 Transformer).
        * Causal decoders train on every token of every sequence and serve with a KV cache. Wang et al. (2022) found they generalize zero-shot best after pure self-supervised pretraining.
        * Packing plus a document mask gives full-length batches with no cross-document leakage.''',
))

# ------------------------------------------------------------------ 06
NBS.append(dict(
    slug='06_rope_scaling', title='06 · Extending context: PI, NTK-aware and YaRN', deck='architecture/07-rope-scaling/', deck_name='Long context I: stretching RoPE', minutes=45,
    goals='the three standard RoPE-scaling methods as frequency transforms, the YaRN attention temperature, and a check of which dimensions leave the trained angle range.',
    setup=SOFTMAX + r'''
def rope_freqs(d, base=10000.0):
    """theta_i = base^(-2i/d), i = 0..d/2-1."""
    return base ** (-np.arange(0, d, 2) / d)
''',
    tasks=[
        dict(fn='pi_freqs', title='Position Interpolation (Chen et al., 2023)', md=r'''
            To run a model trained on length $L$ at length $s\cdot L$, squeeze positions: $m \to m/s$. That is the same as dividing **every** frequency by $s$.
            All angles then stay inside the range seen in training. The cost: neighbouring tokens become $s\times$ harder to tell apart in the fast dimensions.''',
             starter=r'''
            def pi_freqs(d, s, base=10000.0):
                # TODO: rope_freqs(d, base) / s
                raise NotImplementedError''',
             test=r'''
            def _test_pi_freqs(f):
                th = rope_freqs(128); p = f(128, 4)
                assert np.allclose(p, th / 4), "every frequency divided by s"
                assert np.allclose((4 * 2048) * p, 2048 * th), "the max angle at 4x length must equal the trained max angle"''',
             solution=r'''
            def pi_freqs_solution(d, s, base=10000.0):
                return rope_freqs(d, base) / s'''),
        dict(fn='ntk_freqs', title='NTK-aware: change the base instead', md=r'''
            Instead of slowing every dimension equally, raise the base: $b' = b\cdot s^{\,d/(d-2)}$ (YaRN eq. 16).
            Effect: the **fastest** pair ($i=0$) is unchanged, so local order stays sharp, and the **slowest** pair is slowed by exactly $s$, like PI. Dimensions in between are slowed by a smoothly varying amount.''',
             starter=r'''
            def ntk_freqs(d, s, base=10000.0):
                # TODO: rope_freqs(d, base * s ** (d / (d - 2)))
                raise NotImplementedError''',
             test=r'''
            def _test_ntk_freqs(f):
                th = rope_freqs(128); n = f(128, 8)
                assert np.isclose(n[0], th[0]), "the highest frequency must be unchanged"
                assert np.isclose(n[-1], th[-1] / 8), "the lowest frequency must be divided by exactly s"
                assert np.all(np.diff(th / n) > 0), "the slow-down factor should grow smoothly from fast to slow pairs"''',
             solution=r'''
            def ntk_freqs_solution(d, s, base=10000.0):
                return rope_freqs(d, base * s ** (d / (d - 2)))'''),
        dict(fn='yarn_freqs', title='YaRN: NTK-by-parts plus temperature (Peng et al., 2023)', md=r'''
            Decide per dimension by how many full turns it makes inside the original context $L$:
            $r(i) = L/\lambda_i$, with wavelength $\lambda_i = 2\pi/\theta_i$.
            * $r < \alpha$ (fewer than α turns, slow pairs): **interpolate fully**, $\theta/s$, as PI does.
            * $r > \beta$ (many turns, fast pairs): **leave alone**.
            * In between: blend with the ramp $\gamma(r) = (r-\alpha)/(\beta-\alpha)$: $h(\theta) = (1-\gamma)\,\theta/s + \gamma\,\theta$.

            Paper's recommendation for Llama: $\alpha=1$, $\beta=32$. YaRN also scales the attention logits through $\sqrt{1/t} = 0.1\ln s + 1$ (≈ 1.208 at $s=8$), because stretched contexts flatten the softmax.''',
             starter=r'''
            def yarn_freqs(d, s, L, base=10000.0, alpha=1.0, beta=32.0):
                # TODO: theta = rope_freqs(d, base); r = L / (2*pi/theta); gamma = clip((r - alpha) / (beta - alpha), 0, 1)
                #       return (1 - gamma) * theta / s + gamma * theta
                raise NotImplementedError

            def yarn_mscale(s):
                # TODO: 0.1 * ln(s) + 1
                raise NotImplementedError''',
             test=r'''
            def _test_yarn_freqs(f):
                th = rope_freqs(128); y = f(128, 8, 4096)
                r = 4096 * th / (2 * np.pi)
                assert np.allclose(y[r > 32], th[r > 32]), "fast pairs (r > beta) must be unchanged"
                assert np.allclose(y[r < 1], th[r < 1] / 8), "slow pairs (r < alpha) must be divided by s"
                mid = (r >= 1) & (r <= 32)
                assert mid.any() and np.all((y[mid] <= th[mid] + 1e-12) & (y[mid] >= th[mid] / 8 - 1e-12)), "middle pairs must be between theta/s and theta"
                ms = yarn_mscale_solution if f.__name__.endswith('_solution') else yarn_mscale
                assert np.isclose(ms(8), 1.2079, atol=1e-4), "yarn_mscale(8) should be about 1.208"''',
             solution=r'''
            def yarn_freqs_solution(d, s, L, base=10000.0, alpha=1.0, beta=32.0):
                theta = rope_freqs(d, base)
                r = L * theta / (2 * np.pi)
                gamma = np.clip((r - alpha) / (beta - alpha), 0, 1)
                return (1 - gamma) * theta / s + gamma * theta

            def yarn_mscale_solution(s):
                return 0.1 * np.log(s) + 1'''),
    ],
    explore_md=r'''
        **Which dimensions go out of distribution?** A model trained at $L = 4096$ has only ever seen angles $m\theta_i \le 4095\,\theta_i$ in pair $i$. For the *slow* pairs that is less than one full turn, so an unseen angle is genuinely new to the model. Run at $s = 8$ (32K tokens) and count, per method, the slow pairs (wavelength > L) whose maximum angle exceeds the trained maximum.''',
    explore=r'''
        d, L, s = 128, 4096, 8; th = rope_freqs(d); lam = 2 * np.pi / th; slow = lam > L
        methods = {'no scaling (extrapolate)': th, 'PI': pi_freqs_solution(d, s), 'NTK-aware': ntk_freqs_solution(d, s), 'YaRN (by-parts)': yarn_freqs_solution(d, s, L)}
        for name, f in methods.items():
            ood = np.sum(slow & ((s * L - 1) * f > L * th))
            fast_res = th[0] / f[0]
            print(f"{name:26} slow pairs pushed past trained angles: {ood:2d}/{slow.sum()}   fastest pair slowed by {fast_res:.2f}x")
        print(f"\nYaRN logit scale at s={s}: (0.1 ln s + 1)^2 = {yarn_mscale_solution(s) ** 2:.3f}  (applied as sqrt to both q and k)")''',
    takeaways=r'''
        * NTK-aware still pushes most slow pairs slightly past the trained range (only the very slowest pair is slowed by exactly $s$). This is the partial extrapolation YaRN's "by-parts" ramp removes.
        * Without scaling, the slow RoPE pairs reach angles never seen in training, and attention scores blow up (PI's analysis: the interpolation bound is ~600× smaller than extrapolation's).
        * PI fixes this by slowing everything, at the cost of local resolution. NTK-aware keeps the fast pairs. YaRN interpolates only the slow pairs, adds a temperature, and needs about 0.1% of the pretraining data (400 steps) to fine-tune.
        * Llama 3 instead trains long directly: RoPE base 500,000, then six context-extension stages from 8K to 128K over about 800B tokens.''',
))

# ------------------------------------------------------------------ 07
NBS.append(dict(
    slug='07_sliding_window', title='07 · Sliding-window attention and the rolling KV cache', deck='architecture/08-sliding-window/', deck_name='Long context II: sliding window and ALiBi', minutes=40,
    goals="Mistral 7B's sliding-window mask, a rolling-buffer KV cache whose memory never grows, and a test that decoding with the buffer gives exactly the same outputs as full masked attention.",
    setup=SOFTMAX + r'''
def _swa_ref(q, k, v, W):
    T = len(q); i, j = np.indices((T, T))
    s = q @ k.T / np.sqrt(q.shape[1])
    return softmax(np.where((j <= i) & (i - j < W), s, -np.inf)) @ v
''',
    tasks=[
        dict(fn='sliding_window_mask', title='The sliding-window mask', md=r'''
            Each query $i$ attends to itself and the previous $W-1$ tokens: allowed iff $j \le i$ and $i - j < W$.
            (Mistral: position $i$ attends to positions between $i-W$ and $i$ of the previous layer. Off-by-one conventions vary between codebases. Here a window holds exactly $W$ keys, matching a cache of size $W$.)''',
             starter=r'''
            def sliding_window_mask(T, W):
                # TODO: boolean [T, T]
                raise NotImplementedError''',
             test=r'''
            def _test_sliding_window_mask(f):
                M = f(6, 3)
                assert M.dtype == bool and M.shape == (6, 6)
                assert M[5, 5] and M[5, 3] and not M[5, 2], "row 5 with W=3 sees columns 3, 4, 5"
                assert not M[2, 3], "still causal"
                assert np.all(M.sum(1) == np.minimum(np.arange(1, 7), 3)), "each row sees min(i+1, W) keys"''',
             solution=r'''
            def sliding_window_mask_solution(T, W):
                i, j = np.indices((T, T))
                return (j <= i) & (i - j < W)'''),
        dict(fn='RollingKVCache', title='A rolling-buffer KV cache', md=r'''
            Mistral 7B: *"The cache has a fixed size of W, and the keys and values for the timestep i are stored in position i mod W of the cache."* Old entries are simply overwritten.
            Implement `append(k, v)` and `get()`. `get()` returns the stored keys and values **in chronological order** (oldest first) as two arrays of shape [min(t, W), d].''',
             starter=r'''
            class RollingKVCache:
                def __init__(self, W, d):
                    self.W, self.t = W, 0
                    self.K = np.zeros((W, d)); self.V = np.zeros((W, d))

                def append(self, k, v):
                    # TODO: write at slot t % W, then t += 1
                    raise NotImplementedError

                def get(self):
                    # TODO: return (K, V) of the last min(t, W) steps, oldest first
                    raise NotImplementedError''',
             test=r'''
            def _test_RollingKVCache(cls):
                c = cls(4, 2)
                for t in range(10):
                    c.append(np.array([t, t]), np.array([-t, -t]))
                    K, V = c.get()
                    want = np.arange(max(0, t - 3), t + 1)
                    assert K.shape == (len(want), 2), f"after {t + 1} appends expected {len(want)} entries, got {K.shape[0]}"
                    assert np.array_equal(K[:, 0], want), f"after {t + 1} appends keys should be {want.tolist()}, got {K[:, 0].tolist()}"
                    assert np.array_equal(V[:, 0], -want), "values out of order"
                assert c.K.shape == (4, 2), "the buffer itself must never grow"''',
             solution=r'''
            class RollingKVCache_solution:
                def __init__(self, W, d):
                    self.W, self.t = W, 0
                    self.K = np.zeros((W, d)); self.V = np.zeros((W, d))

                def append(self, k, v):
                    self.K[self.t % self.W] = k; self.V[self.t % self.W] = v
                    self.t += 1

                def get(self):
                    n = min(self.t, self.W)
                    idx = [(self.t - n + i) % self.W for i in range(n)]
                    return self.K[idx], self.V[idx]'''),
        dict(fn='decode_with_rolling_cache', title='Decode with the rolling cache', md=r'''
            Process tokens one at a time: append $(k_t, v_t)$ to a `RollingKVCache`, then attend $q_t$ over whatever `get()` returns.
            The test checks that the result equals `softmax(masked scores) @ v` with the sliding-window mask, **exactly**. The cache needs $W$ slots no matter how long the sequence gets.''',
             starter=r'''
            def decode_with_rolling_cache(q, k, v, W, cache_cls=None):
                """q, k, v: [T, d]. Returns [T, d], one token at a time."""
                cache_cls = cache_cls or RollingKVCache
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_decode_with_rolling_cache(f):
                r = np.random.default_rng(1); q, k, v = r.normal(size=(3, 20, 8))
                for W in [1, 4, 7, 20, 32]:
                    out = f(q, k, v, W)
                    assert out.shape == (20, 8)
                    assert np.allclose(out, _swa_ref(q, k, v, W), atol=1e-10), f"W={W}: rolling-cache decode differs from masked sliding-window attention"''',
             solution=r'''
            def decode_with_rolling_cache_solution(q, k, v, W, cache_cls=None):
                cache = (cache_cls or RollingKVCache_solution)(W, k.shape[1]); out = []
                for t in range(len(q)):
                    cache.append(k[t], v[t]); K, V = cache.get()
                    out.append(softmax(q[t] @ K.T / np.sqrt(q.shape[1])) @ V)
                return np.array(out)'''),
    ],
    explore_md=r'''
        **Stacked windows see much further than one window.** Information can hop $W-1$ tokens per layer, so after $L$ layers the receptive field is about $L\cdot(W-1)+1$. Below we compute it exactly by composing masks, then apply the formula to Mistral 7B ($W=4096$, 32 layers). The paper quotes about 131K tokens ($W\times L$). Note this is a *theoretical* span: information from far away has to survive many hops.''',
    explore=r'''
        T, W = 64, 5; M = sliding_window_mask_solution(T, W).astype(int); reach = np.eye(T, dtype=int)
        for layer in range(1, 9):
            reach = (M @ reach > 0).astype(int)
            print(f"layers={layer}: last token can be influenced by {reach[-1].sum():2d} tokens  (formula L*(W-1)+1 = {layer * (W - 1) + 1})")
        print(f"\nMistral 7B: 32 * (4096 - 1) + 1 = {32 * 4095 + 1:,} tokens (paper: ~131K)")
        kv = lambda tokens: 2 * 32 * 8 * 128 * 2 * tokens   # layers * kv_heads * head_dim * bf16 bytes
        print(f"KV cache at 32K tokens: full {kv(32768) / 2**30:.2f} GiB vs rolling buffer {kv(4096) / 2**30:.2f} GiB  ({32768 // 4096}x smaller, as the paper reports)")''',
    takeaways=r'''
        * Sliding-window attention costs $O(T\cdot W)$ instead of $O(T^2)$, and the KV cache is capped at $W$ entries per layer.
        * Depth stacks windows: $L$ layers reach about $L\cdot W$ tokens (131K for Mistral 7B), though only indirectly.
        * The rolling buffer (`i mod W`) is what makes the memory saving real at inference: 8× less cache at 32K tokens for Mistral 7B.''',
))

# ------------------------------------------------------------------ 08
NBS.append(dict(
    slug='08_flash_attention', title='08 · FlashAttention from scratch: online softmax and tiling', deck='architecture/09-flash-attention/', deck_name='FlashAttention internals', minutes=50,
    goals='the online-softmax recurrence, a tiled FlashAttention-2-style forward pass that never materializes the N×N matrix, and an HBM-traffic model that shows why it is faster.',
    setup=SOFTMAX + r'''
def _naive_attention(Q, K, V, causal=False):
    S = Q @ K.T / np.sqrt(Q.shape[1])
    if causal:
        S = np.where(np.tril(np.ones(S.shape, bool)), S, -np.inf)
    return softmax(S) @ V
''',
    tasks=[
        dict(fn='online_softmax', title='Online softmax (Milakov & Gimelshein, 2018)', md=r'''
            Softmax normally needs the max of the whole row before exponentiating. The online version streams through the row **in chunks**, keeping a running max $m$ and a running sum $\ell$:
            $$m_{new} = \max(m, \max(\text{chunk})),\qquad \ell \leftarrow \ell\,e^{m-m_{new}} + \textstyle\sum e^{\text{chunk}-m_{new}}$$
            When the max goes up, the old sum is **rescaled** by $e^{m-m_{new}}$. After the last chunk, softmax $= e^{x - m}/\ell$.
            Return `(m, l)` computed with the given chunk size. (The test then builds the softmax from them.)''',
             starter=r'''
            def online_softmax(x, chunk):
                """x: 1-D array. Returns (m, l): final running max and running sum of exp(x - m)."""
                m, l = -np.inf, 0.0
                # TODO: loop over x[i:i+chunk], update m and l
                raise NotImplementedError''',
             test=r'''
            def _test_online_softmax(f):
                r = np.random.default_rng(1); x = r.normal(0, 5, 37)
                for chunk in [1, 4, 10, 37]:
                    m, l = f(x, chunk)
                    assert np.isclose(m, x.max()), f"chunk={chunk}: running max wrong"
                    assert np.allclose(np.exp(x - m) / l, softmax(x)), f"chunk={chunk}: exp(x - m) / l must equal softmax(x). Did you rescale the old sum?"''',
             solution=r'''
            def online_softmax_solution(x, chunk):
                m, l = -np.inf, 0.0
                for i in range(0, len(x), chunk):
                    c = x[i:i + chunk]; m_new = max(m, c.max())
                    l = l * np.exp(m - m_new) + np.exp(c - m_new).sum()
                    m = m_new
                return m, l'''),
        dict(fn='flash_attention', title='Tiled attention forward (FlashAttention-2 loop order)', md=r'''
            Split $Q$ into row blocks of size $B_r$ and $K, V$ into column blocks of size $B_c$. For each $Q$ block (the **outer** loop, which FA2 runs in parallel across thread blocks), stream over K/V blocks (the **inner** loop) and keep, per row, a running max $m$, running sum $\ell$ and **unnormalized** output $\tilde O$:
            ```
            S = Q_i K_j^T / sqrt(d)            # [Br, Bc] lives only in SRAM
            m_new = max(m, rowmax(S))
            P = exp(S - m_new)
            l = l * exp(m - m_new) + rowsum(P)
            O~ = O~ * exp(m - m_new) + P @ V_j  # rescale old partial output, add new
            m = m_new
            ```
            After the inner loop: $O_i = \tilde O / \ell$, and save the log-sum-exp $L_i = m + \log \ell$ for the backward pass (FA2 stores only this one number per row).
            Support `causal=True`: mask entries with column > row, and skip K/V blocks that lie entirely in the future.''',
             starter=r'''
            def flash_attention(Q, K, V, Br=4, Bc=4, causal=False):
                """Q, K, V: [N, d]. Returns (O [N, d], L [N] log-sum-exp per row). Never build an [N, N] array."""
                N, d = Q.shape; O = np.zeros((N, d)); L = np.zeros(N)
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_flash_attention(f):
                r = np.random.default_rng(2)
                for N, d, Br, Bc in [(16, 8, 4, 4), (19, 8, 5, 3), (7, 4, 16, 16), (33, 16, 8, 1)]:
                    Q, K, V = r.normal(size=(3, N, d))
                    for causal in [False, True]:
                        O, L = f(Q, K, V, Br, Bc, causal)
                        assert np.allclose(O, _naive_attention(Q, K, V, causal), atol=1e-10), f"N={N} Br={Br} Bc={Bc} causal={causal}: output differs from naive attention"
                        S = Q @ K.T / np.sqrt(d)
                        if causal: S = np.where(np.tril(np.ones((N, N), bool)), S, -np.inf)
                        mx = S.max(1); assert np.allclose(L, mx + np.log(np.exp(S - mx[:, None]).sum(1))), "L must be the row-wise log-sum-exp"''',
             solution=r'''
            def flash_attention_solution(Q, K, V, Br=4, Bc=4, causal=False):
                N, d = Q.shape; O = np.zeros((N, d)); L = np.zeros(N); scale = 1 / np.sqrt(d)
                for i0 in range(0, N, Br):                      # outer loop: query blocks (parallel on GPU)
                    Qi = Q[i0:i0 + Br]; rows = np.arange(i0, i0 + len(Qi))
                    m = np.full(len(Qi), -np.inf); l = np.zeros(len(Qi)); acc = np.zeros((len(Qi), d))
                    for j0 in range(0, N, Bc):                  # inner loop: stream K/V blocks through "SRAM"
                        if causal and j0 > rows[-1]:
                            break                                # whole block is in the future
                        S = Qi @ K[j0:j0 + Bc].T * scale
                        if causal:
                            S = np.where(np.arange(j0, j0 + S.shape[1])[None, :] <= rows[:, None], S, -np.inf)
                        m_new = np.maximum(m, S.max(1))
                        P = np.exp(S - m_new[:, None])
                        corr = np.exp(m - m_new)
                        l = l * corr + P.sum(1)
                        acc = acc * corr[:, None] + P @ V[j0:j0 + Bc]
                        m = m_new
                    O[i0:i0 + Br] = acc / l[:, None]
                    L[i0:i0 + Br] = m + np.log(l)
                return O, L'''),
        dict(fn='hbm_traffic', title='Count the memory traffic', md=r'''
            Model HBM reads and writes in **elements** for one head (forward pass only):
            * **Standard** (Algorithm 0 in the FA1 paper): read Q, K and write S ($2Nd + N^2$); read S, write P ($2N^2$); read P, V and write O ($N^2 + 2Nd$).
            * **Flash** (FA2 loop order): read each $Q_i$ once and write each $O_i$ once ($2Nd$); for each of the $\lceil N/B_r\rceil$ query blocks, read all of K and V ($2Nd$ each time).

            Return a dict `{'standard': ..., 'flash': ...}`. The FA1 paper's Theorem 2 gives $\Theta(Nd + N^2)$ vs $\Theta(N^2d^2M^{-1})$, where block size $\propto M/d$ for SRAM size $M$.''',
             starter=r'''
            def hbm_traffic(N, d, Br):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_hbm_traffic(f):
                t = f(1024, 64, 64)
                assert t['standard'] == 4 * 1024 * 64 + 4 * 1024 ** 2, f"standard: got {t['standard']:,}"
                assert t['flash'] == 2 * 1024 * 64 + 16 * 2 * 1024 * 64, f"flash: got {t['flash']:,}"
                assert f(4096, 64, 128)['flash'] < f(4096, 64, 128)['standard'] / 3, "with d=64 and Br=128, flash should move under a third of the data"
                assert f(4096, 64, 256)['flash'] < f(4096, 64, 128)['flash'], "bigger query tiles mean fewer K/V re-reads"''',
             solution=r'''
            def hbm_traffic_solution(N, d, Br):
                standard = (2 * N * d + N * N) + (2 * N * N) + (N * N + 2 * N * d)
                flash = 2 * N * d + int(np.ceil(N / Br)) * 2 * N * d
                return {'standard': standard, 'flash': flash}'''),
    ],
    explore_md=r'''
        **Traffic and memory as the sequence grows** (d = 64 as in GPT-2 medium, B_r = 128, BF16 = 2 bytes). In this simple forward-only model, standard attention moves about $4N^2$ elements (S and P written and read back), while Flash re-reads K and V once per query block, about $2N^2d/B_r$. With $B_r = 2d$ that is about 4× less traffic, and larger tiles help further, up to what SRAM can hold. The bigger win in this model is **memory**: Flash's extra state is $O(N)$ (the $m$, $\ell$ or $L$ per row) instead of an $O(N^2)$ matrix per head.

The paper measures much more: on GPT-2 medium (N = 1024, d = 64, forward + backward, A100), standard attention did **66.6 GFLOPs, 40.3 GB of HBM traffic, 41.7 ms**, and FlashAttention did **75.2 GFLOPs** (more, because of recomputation), **4.4 GB, 7.3 ms** (FA1 Fig. 2). Real gains include the backward pass (which no longer reads S and P) and fusing mask, softmax and dropout into one kernel instead of several separate passes over HBM.''',
    explore=r'''
        for N in [1024, 4096, 16384, 65536]:
            t = hbm_traffic_solution(N, 64, 128)
            print(f"N={N:6,}: standard {2 * t['standard'] / 2**20:9,.0f} MiB moved, flash {2 * t['flash'] / 2**20:7,.0f} MiB  ({t['standard'] / t['flash']:4.1f}x less);"
                  f"  N×N score matrix alone = {2 * N * N / 2**20:8,.0f} MiB per head")
        print("\nFA1 paper, GPT-2 medium fwd+bwd on A100: standard 40.3 GB / 41.7 ms vs FlashAttention 4.4 GB / 7.3 ms (9.2x less traffic, 5.7x faster)")
        r = np.random.default_rng(0); Q, K, V = r.normal(size=(3, 512, 64))
        O, _ = flash_attention_solution(Q, K, V, 64, 64, causal=True)
        print(f"\nmax |flash - naive| at N=512, causal: {np.abs(O - _naive_attention(Q, K, V, True)).max():.1e}  (exact up to float rounding)")''',
    takeaways=r'''
        * The online-softmax rescaling trick lets attention be computed block by block, without ever holding a full row of scores.
        * Tiling keeps S and P in on-chip SRAM. HBM sees only Q, K, V and O, so memory is linear in N, and the speedup comes from moving fewer bytes, not from fewer FLOPs.
        * FA2's changes: loop over query blocks on the outside (parallel across thread blocks), rescale the output only once at the end, and store just the log-sum-exp for the backward pass, which recomputes S and P on chip instead of reading them.''',
))

# ------------------------------------------------------------------ 09
NBS.append(dict(
    slug='09_moe_router', title='09 · Mixture-of-Experts: router, dispatch and load balancing', deck='architecture/10-mixture-of-experts/', deck_name='Mixture of Experts', minutes=45,
    goals="Mixtral-style top-k routing, a sparse MoE layer, the Switch Transformer load-balancing loss, and expert capacity with token dropping.",
    setup=SOFTMAX + r'''
r = np.random.default_rng(0)
d, n_exp, h = 16, 8, 32
experts = [(r.normal(0, d ** -.5, (d, h)), r.normal(0, h ** -.5, (h, d))) for _ in range(n_exp)]
expert_fn = lambda e, x: np.maximum(0, x @ experts[e][0]) @ experts[e][1]
W_g = r.normal(0, d ** -.5, (d, n_exp))
''',
    tasks=[
        dict(fn='topk_route', title='Top-k routing (Mixtral)', md=r'''
            Mixtral: $G(x) = \mathrm{Softmax}(\mathrm{TopK}(x\cdot W_g))$. Keep the $k$ largest router logits per token and softmax over **only those $k$**. The other experts get weight 0.
            Return `idx` [T, k] (expert ids, largest logit first) and `w` [T, k] (weights summing to 1 per token).''',
             starter=r'''
            def topk_route(logits, k):
                """logits: [T, n_exp]. Returns (idx [T, k], w [T, k])."""
                # TODO: argsort descending, take the first k, softmax over those k logits
                raise NotImplementedError''',
             test=r'''
            def _test_topk_route(f):
                lg = np.array([[1.0, 3.0, 2.0, -1.0], [0.0, 0.0, 5.0, 4.0]])
                idx, w = f(lg, 2)
                assert idx.shape == (2, 2) and w.shape == (2, 2), "shapes must be [T, k]"
                assert idx.tolist() == [[1, 2], [2, 3]], f"expected [[1, 2], [2, 3]], got {idx.tolist()}"
                assert np.allclose(w.sum(1), 1), "weights per token must sum to 1"
                assert np.allclose(w[0], softmax(np.array([3.0, 2.0]))), "softmax over the top-k logits only"''',
             solution=r'''
            def topk_route_solution(logits, k):
                idx = np.argsort(-logits, axis=1)[:, :k]
                top = np.take_along_axis(logits, idx, axis=1)
                return idx, softmax(top, axis=1)'''),
        dict(fn='moe_layer', title='The sparse MoE layer', md=r'''
            $y = \sum_{i \in \text{top-}k} G(x)_i \cdot E_i(x)$. Each token runs only $k$ of the $n$ experts. For Mixtral: 8 experts, $k=2$, 47B total params, about 13B active per token.
            Use `expert_fn(e, x)` from setup. Make it **sparse**: for each expert, gather only the tokens routed to it and run the expert once on that batch. This dispatch pattern becomes all-to-all communication under expert parallelism.''',
             starter=r'''
            def moe_layer(x, k=2):
                """x: [T, d]. Returns (y [T, d], idx [T, k])."""
                # TODO: route with topk_route(x @ W_g, k); for each expert e, find (token, slot) pairs routed to e,
                #       run expert_fn(e, x[tokens]) once, add weight * output into y[tokens]
                raise NotImplementedError''',
             test=r'''
            def _test_moe_layer(f):
                x = np.random.default_rng(1).normal(size=(12, d))
                y, idx = f(x, 2)
                ref_idx, ref_w = topk_route_solution(x @ W_g, 2)
                ref = np.stack([sum(ref_w[t, j] * expert_fn(ref_idx[t, j], x[t:t + 1])[0] for j in range(2)) for t in range(12)])
                assert y.shape == (12, d)
                assert np.allclose(y, ref, atol=1e-10), "output must equal the weighted sum of each token's top-k experts"
                calls = []
                global expert_fn
                orig = expert_fn; expert_fn = lambda e, xx: (calls.append(e), orig(e, xx))[1]
                try: f(x, 2)
                finally: expert_fn = orig
                assert len(calls) <= n_exp, f"call each expert at most once per layer (batched dispatch); got {len(calls)} calls"''',
             solution=r'''
            def moe_layer_solution(x, k=2):
                idx, w = topk_route_solution(x @ W_g, k); y = np.zeros_like(x)
                for e in range(n_exp):
                    tok, slot = np.nonzero(idx == e)
                    if len(tok):
                        y[tok] += w[tok, slot][:, None] * expert_fn(e, x[tok])
                return y, idx'''),
        dict(fn='load_balance_loss', title='Switch Transformer load-balancing loss', md=r'''
            Left alone, a router collapses onto a few experts. Switch Transformer (eq. 4–6) adds
            $$\text{loss} = \alpha\cdot N\cdot\sum_{i=1}^{N} f_i\,P_i$$
            * $f_i$: the fraction of tokens whose **top-1** expert is $i$
            * $P_i$: the mean router probability (full softmax) assigned to expert $i$
            * $\alpha = 10^{-2}$ in the paper

            Under perfectly uniform routing $f_i = P_i = 1/N$, so the loss is exactly $\alpha$. If every token picks one expert with certainty, the loss is $\alpha N$.''',
             starter=r'''
            def load_balance_loss(logits, alpha=1e-2):
                """logits: [T, N] router logits."""
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_load_balance_loss(f):
                T, N = 64, 8
                uni = np.tile(np.eye(N) * 1e-3, (T // N, 1))
                assert np.isclose(f(uni), 1e-2, rtol=1e-3), f"uniform routing should give alpha = 0.01, got {f(uni):.5f}"
                col = np.zeros((T, N)); col[:, 3] = 50
                assert np.isclose(f(col), 1e-2 * N, rtol=1e-3), f"total collapse should give alpha * N = 0.08, got {f(col):.5f}"
                r = np.random.default_rng(2); lg = r.normal(size=(T, N))
                p = softmax(lg); fi = np.bincount(lg.argmax(1), minlength=N) / T
                assert np.isclose(f(lg), 1e-2 * N * (fi * p.mean(0)).sum()), "use top-1 fractions f_i and mean full-softmax probabilities P_i"''',
             solution=r'''
            def load_balance_loss_solution(logits, alpha=1e-2):
                T, N = logits.shape
                f = np.bincount(logits.argmax(1), minlength=N) / T
                P = softmax(logits, axis=1).mean(0)
                return alpha * N * (f * P).sum()'''),
        dict(fn='capacity_dispatch', title='Expert capacity and dropped tokens', md=r'''
            On accelerators each expert gets a fixed-size buffer:
            $$\text{capacity} = \frac{\text{tokens per batch}}{\text{number of experts}} \times \text{capacity factor}$$
            Tokens routed to a full expert are **dropped** (they skip the layer through the residual connection).
            Given top-1 assignments `assign` [T], return a boolean `kept` [T]: keep tokens in arrival order until their expert's buffer (`int(capacity)`) is full.''',
             starter=r'''
            def capacity_dispatch(assign, n_experts, capacity_factor):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_capacity_dispatch(f):
                a = np.array([0, 0, 0, 1, 0, 1, 2, 3])
                k = f(a, 4, 1.0)          # capacity = 8/4 * 1.0 = 2
                assert k.tolist() == [True, True, False, True, False, True, True, True], f"got {k.tolist()}"
                assert f(a, 4, 2.0).all(), "capacity 4 fits everything"''',
             solution=r'''
            def capacity_dispatch_solution(assign, n_experts, capacity_factor):
                cap = int(len(assign) / n_experts * capacity_factor); used = np.zeros(n_experts, int); kept = np.zeros(len(assign), bool)
                for t, e in enumerate(assign):
                    if used[e] < cap:
                        kept[t] = True; used[e] += 1
                return kept'''),
    ],
    explore_md=r'''
        **Total vs active parameters, and what balancing buys.** First, the arithmetic of sparsity using Mixtral's published figures. Then route 4,096 tokens through a deliberately skewed router and see how the load-balancing loss and the drop rate respond as the skew shrinks. That shrinking is what the auxiliary loss pushes training toward.''',
    explore=r'''
        print("Mixtral 8x7B: 8 experts, top-2 -> 47B total parameters, ~13B active per token")
        print("DeepSeek-V2: 2 shared + 160 routed experts, 6 routed active -> 236B total, 21B active\n")
        r = np.random.default_rng(0); T, N = 4096, 8
        for skew in [3.0, 1.5, 0.5, 0.0]:
            lg = r.normal(size=(T, N)) + skew * np.linspace(1, 0, N)
            a = lg.argmax(1); kept = capacity_dispatch_solution(a, N, 1.25)
            load = np.bincount(a, minlength=N) / T
            print(f"skew {skew:3.1f}: busiest expert gets {load.max():.0%} of tokens, aux loss {load_balance_loss_solution(lg):.4f}, "
                  f"dropped at capacity factor 1.25: {1 - kept.mean():.1%}")''',
    takeaways=r'''
        * MoE replaces the dense FFN with $N$ expert FFNs and a router. Each token uses $k$ of them, so parameters grow with $N$ while FLOPs grow with $k$.
        * Without an auxiliary loss, routing collapses. The Switch loss $\alpha N\sum f_iP_i$ is minimized by uniform routing.
        * Fixed expert capacity makes compute static but drops overflow tokens. Load balance is therefore a quality issue as well as an efficiency one.''',
))

# ------------------------------------------------------------------ 10
NBS.append(dict(
    slug='10_llama_block', title='10 · Build a Llama-style decoder block and count its parameters', deck='architecture/11-putting-it-together/', deck_name='Putting it together', minutes=50,
    goals='a complete modern decoder block (pre-norm RMSNorm, GQA with RoPE, SwiGLU), a parameter counter that reproduces Llama 2 7B and Llama 3 8B exactly, and a check that the block is causal.',
    setup=SOFTMAX + REF_NORM + REF_ROPE + REF_SWIGLU + r'''
def init_block(d=64, n_heads=8, n_kv=2, hidden=176, seed=0):
    r = np.random.default_rng(seed); dh = d // n_heads
    n = lambda *s: r.normal(0, s[0] ** -.5, s)
    return dict(n_heads=n_heads, n_kv=n_kv, g_attn=np.ones(d), g_ffn=np.ones(d),
                Wq=n(d, n_heads * dh), Wk=n(d, n_kv * dh), Wv=n(d, n_kv * dh), Wo=n(n_heads * dh, d),
                W_gate=n(d, hidden), W_up=n(d, hidden), W_down=n(hidden, d))
B = init_block()
''',
    tasks=[
        dict(fn='gqa_rope_attention', title='Grouped-query attention with RoPE', md=r'''
            1. Project: $q = xW_q$ → [T, n_heads, dh]; $k = xW_k$ and $v = xW_v$ → [T, n_kv, dh].
            2. Apply RoPE (`_rope_ref(x, pos)`, per head, positions 0..T-1) to **q and k only**.
            3. Query head $h$ uses KV head $h \div (n_{heads}/n_{kv})$, so consecutive query heads share a KV head.
            4. Causal softmax of $qk^\top/\sqrt{dh}$, multiply by $v$, concatenate heads, then $\cdot W_o$.''',
             starter=r'''
            def gqa_rope_attention(x, B):
                """x: [T, d] (already normed). Returns [T, d]."""
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_gqa_rope_attention(f):
                x = np.random.default_rng(1).normal(size=(9, 64)); y = f(x, B)
                assert y.shape == (9, 64)
                T, H, G = 9, 8, 2; dh = 8; pos = np.arange(T)
                q = (x @ B['Wq']).reshape(T, H, dh); k = (x @ B['Wk']).reshape(T, G, dh); v = (x @ B['Wv']).reshape(T, G, dh)
                outs = []
                for h in range(H):
                    g = h // (H // G); s = _rope_ref(q[:, h], pos) @ _rope_ref(k[:, g], pos).T / np.sqrt(dh)
                    outs.append(softmax(np.where(np.tril(np.ones((T, T), bool)), s, -np.inf)) @ v[:, g])
                assert np.allclose(y, np.concatenate(outs, 1) @ B['Wo'], atol=1e-10), "values differ: check RoPE on q and k, the head-to-group mapping h // (H // G), and the causal mask"''',
             solution=r'''
            def gqa_rope_attention_solution(x, B):
                T, d = x.shape; H, G = B['n_heads'], B['n_kv']; dh = B['Wq'].shape[1] // H; pos = np.arange(T)
                q = (x @ B['Wq']).reshape(T, H, dh); k = (x @ B['Wk']).reshape(T, G, dh); v = (x @ B['Wv']).reshape(T, G, dh)
                mask = np.tril(np.ones((T, T), bool)); outs = []
                for h in range(H):
                    g = h // (H // G)
                    s = _rope_ref(q[:, h], pos) @ _rope_ref(k[:, g], pos).T / np.sqrt(dh)
                    outs.append(softmax(np.where(mask, s, -np.inf)) @ v[:, g])
                return np.concatenate(outs, axis=1) @ B['Wo']'''),
        dict(fn='llama_block', title='The full block', md=r'''
            $$h = x + \mathrm{Attn}(\mathrm{RMSNorm}(x)), \qquad \text{out} = h + \mathrm{SwiGLU}(\mathrm{RMSNorm}(h))$$
            Use `_rms_ref(x, g)` with `B['g_attn']` and `B['g_ffn']`, your `gqa_rope_attention` (or the `_solution`), and `_swiglu_ref`. No biases anywhere. The test also checks that changing the last token leaves earlier outputs untouched.''',
             starter=r'''
            def llama_block(x, B):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_llama_block(f):
                x = np.random.default_rng(2).normal(size=(7, 64)); y = f(x, B)
                attn = globals().get('gqa_rope_attention_solution') or _ref_attn
                h = x + attn(_rms_ref(x, B['g_attn']), B)
                ref = h + _swiglu_ref(_rms_ref(h, B['g_ffn']), B['W_gate'], B['W_up'], B['W_down'])
                assert y.shape == x.shape
                assert np.allclose(y, ref, atol=1e-10), "values differ: pre-norm RMSNorm -> attention -> residual, then pre-norm RMSNorm -> SwiGLU -> residual"
                x2 = x.copy(); x2[-1] += 3
                assert np.allclose(f(x2, B)[:-1], y[:-1]), "the block must be causal"

            def _ref_attn(x, B):
                T, d = x.shape; H, G = B['n_heads'], B['n_kv']; dh = B['Wq'].shape[1] // H; pos = np.arange(T)
                q = (x @ B['Wq']).reshape(T, H, dh); k = (x @ B['Wk']).reshape(T, G, dh); v = (x @ B['Wv']).reshape(T, G, dh)
                outs = [softmax(np.where(np.tril(np.ones((T, T), bool)), _rope_ref(q[:, h], pos) @ _rope_ref(k[:, h // (H // G)], pos).T / np.sqrt(dh), -np.inf)) @ v[:, h // (H // G)] for h in range(H)]
                return np.concatenate(outs, axis=1) @ B['Wo']''',
             solution=r'''
            def llama_block_solution(x, B):
                h = x + gqa_rope_attention_solution(_rms_ref(x, B['g_attn']), B)
                return h + _swiglu_ref(_rms_ref(h, B['g_ffn']), B['W_gate'], B['W_up'], B['W_down'])'''),
        dict(fn='count_params', title='Count a real model\'s parameters', md=r'''
            Given a config, return total parameters:
            * embeddings: `vocab × d`; output head: another `vocab × d` unless `tied`
            * per layer: $W_q$ and $W_o$ ($d\times d$ each); $W_k$ and $W_v$ ($d \times n_{kv}\cdot d_h$ each, $d_h = d/n_{heads}$); SwiGLU ($3\cdot d\cdot h$); two RMSNorm gains ($2d$)
            * one final RMSNorm ($d$)

            Expected: **Llama 2 7B = 6,738,415,616** and **Llama 3 8B = 8,030,261,248**.''',
             starter=r'''
            def count_params(vocab, d, n_layers, n_heads, n_kv, hidden, tied=False):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_count_params(f):
                l2 = f(32000, 4096, 32, 32, 32, 11008)
                assert l2 == 6_738_415_616, f"Llama 2 7B: got {l2:,}, expected 6,738,415,616"
                l3 = f(128256, 4096, 32, 32, 8, 14336)
                assert l3 == 8_030_261_248, f"Llama 3 8B: got {l3:,}, expected 8,030,261,248"
                assert f(100, 8, 1, 2, 2, 16, tied=True) == 100 * 8 + (4 * 64 + 3 * 8 * 16 + 16) + 8, "tied embeddings count once"''',
             solution=r'''
            def count_params_solution(vocab, d, n_layers, n_heads, n_kv, hidden, tied=False):
                dh = d // n_heads
                attn = 2 * d * d + 2 * d * n_kv * dh
                layer = attn + 3 * d * hidden + 2 * d
                return vocab * d * (1 if tied else 2) + n_layers * layer + d'''),
    ],
    explore_md=r'''
        **Where do the parameters go?** Break down Llama 3 8B, and see how GQA and the 128K vocabulary shifted the budget compared with Llama 2 7B.''',
    explore=r'''
        def breakdown(name, vocab, d, L, H, G, hid):
            dh = d // H; emb = 2 * vocab * d; attn = L * (2 * d * d + 2 * d * G * dh); ffn = L * 3 * d * hid
            tot = count_params_solution(vocab, d, L, H, G, hid)
            print(f"{name}: total {tot / 1e9:.2f}B | embeddings+head {emb / tot:5.1%} | attention {attn / tot:5.1%} | FFN {ffn / tot:5.1%}")
        breakdown('Llama 2 7B ', 32000, 4096, 32, 32, 32, 11008)
        breakdown('Llama 3 8B ', 128256, 4096, 32, 32, 8, 14336)
        x = np.random.default_rng(0).normal(size=(16, 64))
        y = x
        for layer in range(4):
            y = llama_block_solution(y, init_block(seed=layer))
        print(f"\n4 random blocks ran end to end: output shape {y.shape}, residual RMS grew from {np.sqrt((x**2).mean()):.2f} to {np.sqrt((y**2).mean()):.2f} (why a final RMSNorm is needed)")''',
    takeaways=r'''
        * A Llama block is just the 2017 block with four swaps: pre-norm, RMSNorm, RoPE inside attention, SwiGLU FFN. Llama 2 70B and Llama 3 add GQA.
        * Parameter counts follow directly from the config. Being able to reproduce 8.03B from `config.json` is a good sanity check of your mental model.
        * In Llama 3 8B the FFN is about 70% of all parameters, attention (thanks to GQA) about 17%, and the 128K-vocabulary embeddings plus output head about 13%.''',
))
