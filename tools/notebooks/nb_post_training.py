"""Post-training exercise notebooks."""

BASE = r'''
def softmax(x, axis=-1):
    x = x - x.max(axis=axis, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=axis, keepdims=True)

def log_softmax(x, axis=-1):
    x = x - x.max(axis=axis, keepdims=True)
    return x - np.log(np.exp(x).sum(axis=axis, keepdims=True))

def log_sigmoid(z):
    return -np.logaddexp(0, -z)
'''

NBS = []

# ------------------------------------------------------------------ 01
NBS.append(dict(
    slug='01_sft_loss_masking', title='01 · Supervised fine-tuning: chat templates, loss masking and packing', deck='post-training/02-supervised-fine-tuning/', deck_name='Supervised fine-tuning', minutes=35,
    goals='the data side of SFT: render a conversation with a chat template, train only on the assistant\'s tokens, compute the masked loss, and pack many short examples into fixed-length rows.',
    setup=BASE + r'''
SPECIAL = ['<pad>', '<bos>', '<system>', '<user>', '<assistant>', '<eot>']
VOCAB = {t: i for i, t in enumerate(SPECIAL)}
def encode(text):
    """Toy word-level tokenizer: every new word gets the next id."""
    return [VOCAB.setdefault(w, len(VOCAB)) for w in text.split()]
PAD, BOS, EOT = VOCAB['<pad>'], VOCAB['<bos>'], VOCAB['<eot>']
IGNORE = -100   # the label value PyTorch's cross_entropy ignores by default

chat = [{'role': 'system', 'content': 'you are helpful'},
        {'role': 'user', 'content': 'what is two plus two'},
        {'role': 'assistant', 'content': 'two plus two is four'},
        {'role': 'user', 'content': 'and three plus three'},
        {'role': 'assistant', 'content': 'six'}]

def _render_ref(messages):
    tokens, mask = [BOS], [False]
    for m in messages:
        body = encode(m['content']); learn = m['role'] == 'assistant'
        tokens += [VOCAB['<' + m['role'] + '>']] + body + [EOT]; mask += [False] + [learn] * len(body) + [learn]
    return tokens, mask
''',
    tasks=[
        dict(fn='render_chat', title='Render a chat template with a loss mask', md=r'''
            A chat model sees one flat token sequence. A **chat template** turns a list of messages into that sequence using special tokens. Ours (illustrative, Llama-style) is:
            ```
            <bos> <role> content... <eot> <role> content... <eot> ...
            ```
            Return `tokens` (list of ids) and `mask` (list of bools, same length). `mask[i]` is True when token *i* should be **learned**: the assistant's content tokens **and** its closing `<eot>`, so the model learns when to stop. Everything else is context: `<bos>`, role tokens, and system and user content.

            Llama 2: *"we zero-out the loss on tokens from the user prompt, so as a result, we backpropagate only on answer tokens."*''',
             starter=r'''
            def render_chat(messages):
                """Returns (tokens, mask)."""
                # TODO: start with [BOS] / [False]; for each message add VOCAB['<'+role+'>'], encode(content), EOT
                raise NotImplementedError''',
             test=r'''
            def _test_render_chat(f):
                toks, mask = f(chat)
                assert len(toks) == len(mask), "tokens and mask must have the same length"
                assert toks[0] == BOS and not mask[0], "first token is <bos> and is not trained"
                words = [k for t in toks for k, v in VOCAB.items() if v == t]
                assert words[:3] == ['<bos>', '<system>', 'you'], f"unexpected start: {words[:3]}"
                trained = [w for w, m in zip(words, mask) if m]
                assert trained == ['two', 'plus', 'two', 'is', 'four', '<eot>', 'six', '<eot>'], f"trained tokens should be the assistant answers + their <eot>, got {trained}"
                assert words.count('<eot>') == 5, "every message ends with <eot>"''',
             solution=r'''
            def render_chat_solution(messages):
                tokens, mask = [BOS], [False]
                for m in messages:
                    learn = m['role'] == 'assistant'
                    body = encode(m['content'])
                    tokens += [VOCAB['<' + m['role'] + '>']] + body + [EOT]
                    mask += [False] + [learn] * len(body) + [learn]
                return tokens, mask'''),
        dict(fn='build_labels', title='Shift and mask the labels', md=r'''
            Next-token prediction: the input at position *t* predicts the token at *t+1*. So `inputs = tokens[:-1]` and `labels = tokens[1:]`. Replace every label whose **target token** is not trained with `IGNORE` (−100).''',
             starter=r'''
            def build_labels(tokens, mask):
                """Returns (inputs, labels) as numpy int arrays of length len(tokens) - 1."""
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_build_labels(f):
                toks, mask = _render_ref(chat)
                x, y = f(toks, mask)
                assert len(x) == len(y) == len(toks) - 1
                assert np.array_equal(x, toks[:-1]), "inputs are tokens[:-1]"
                keep = np.array(mask[1:])
                assert np.array_equal(y[keep], np.array(toks[1:])[keep]), "kept labels are the next tokens"
                assert np.all(y[~keep] == IGNORE), "untrained targets must be IGNORE"
                assert (y != IGNORE).sum() == 8''',
             solution=r'''
            def build_labels_solution(tokens, mask):
                t = np.array(tokens)
                labels = np.where(np.array(mask[1:]), t[1:], IGNORE)
                return t[:-1], labels'''),
        dict(fn='masked_cross_entropy', title='The masked loss', md=r'''
            Given `logits` [T, V] and `labels` [T], return the mean of $-\log p(\text{label}_t)$ over positions whose label is not `IGNORE`. The mean is over **trained tokens only**: averaging over all positions would quietly shrink the loss, and with it the effective learning rate.''',
             starter=r'''
            def masked_cross_entropy(logits, labels):
                # TODO: log_softmax, pick the label's log-prob where labels != IGNORE, average over those
                raise NotImplementedError''',
             test=r'''
            def _test_masked_cross_entropy(f):
                r = np.random.default_rng(1); L = r.normal(size=(6, 10)); y = np.array([3, IGNORE, 1, IGNORE, IGNORE, 9])
                lp = log_softmax(L); want = -(lp[0, 3] + lp[2, 1] + lp[5, 9]) / 3
                assert np.isclose(f(L, y), want), "average -log p over non-ignored positions only"
                assert np.isclose(f(L, np.full(6, 4)), -lp[:, 4].mean())''',
             solution=r'''
            def masked_cross_entropy_solution(logits, labels):
                keep = labels != IGNORE
                lp = log_softmax(logits[keep])
                return -lp[np.arange(keep.sum()), labels[keep]].mean()'''),
        dict(fn='pack', title='Pack examples into fixed-length rows', md=r'''
            Real SFT sets have many short examples. Padding each one to the max length wastes compute, so **pack** them: fill each row of length `max_len` with whole examples **in order**, starting a new row when the next example doesn't fit, then pad the rest (`PAD` input, `IGNORE` label). Llama 2: *"we concatenate all the prompts and answers from the training set"* to fill the sequence length.

            Input: a list of `(inputs, labels)` pairs. Return `rows_x`, `rows_y` and `doc_ids` (int arrays [n_rows, max_len]; `doc_ids` = example index, −1 for padding). Pair this with the document mask from [Architecture notebook 05](https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/architecture/05_attention_masks.ipynb) so examples can't attend to each other.''',
             starter=r'''
            def pack(examples, max_len):
                # TODO: greedily append each example to the current row if it fits, else start a new row
                raise NotImplementedError''',
             test=r'''
            def _test_pack(f):
                r = np.random.default_rng(2)
                ex = [(np.arange(n), np.where(r.random(n) < .5, IGNORE, 1)) for n in [5, 3, 7, 2, 6, 1, 4]]
                X, Y, D = f(ex, 10)
                assert X.shape == Y.shape == D.shape and X.shape[1] == 10
                for i, (x, y) in enumerate(ex):
                    sel = D == i
                    assert sel.sum() == len(x), f"example {i} must appear exactly once, whole"
                    assert np.array_equal(X[sel], x) and np.array_equal(Y[sel], y), f"example {i} content changed"
                assert np.all(Y[D == -1] == IGNORE) and np.all(X[D == -1] == PAD), "padding: PAD inputs, IGNORE labels"
                assert X.shape[0] == 4, f"greedy in-order packing should need 4 rows of 10 here, got {X.shape[0]}"''',
             solution=r'''
            def pack_solution(examples, max_len):
                rows, cur = [], []
                for i, (x, y) in enumerate(examples):
                    if sum(len(e[0]) for e in cur) + len(x) > max_len:
                        rows.append(cur); cur = []
                    cur.append((x, y, i))
                if cur: rows.append(cur)
                X = np.full((len(rows), max_len), PAD); Y = np.full((len(rows), max_len), IGNORE); D = np.full((len(rows), max_len), -1)
                for r_, row in enumerate(rows):
                    p = 0
                    for x, y, i in row:
                        X[r_, p:p + len(x)] = x; Y[r_, p:p + len(x)] = y; D[r_, p:p + len(x)] = i; p += len(x)
                return X, Y, D'''),
    ],
    explore_md=r'''
        **How much of a chat is actually trained on?** In multi-turn data with long system prompts, the trained fraction can be small. That is fine, because the context still conditions the answer. Below: the trained fraction for our chat, and the padding waste of "one example per row" vs packing for random example lengths.''',
    explore=r'''
        toks, mask = render_chat_solution(chat)
        print(f"chat: {len(toks)} tokens, {sum(mask)} trained ({sum(mask) / len(toks):.0%})")
        r = np.random.default_rng(0); lens = r.integers(20, 400, 2000); L = 2048
        ex = [(np.zeros(n, int), np.ones(n, int)) for n in lens]
        X, Y, D = pack_solution(ex, L)
        print(f"one example per row (padded to {lens.max()}): {lens.sum() / (len(lens) * lens.max()):.0%} of positions are real tokens")
        print(f"packed into {X.shape[0]} rows of {L}: {(D >= 0).mean():.0%} real tokens")''',
    takeaways=r'''
        * SFT is ordinary next-token training on demonstrations. What makes it *instruction* tuning is the chat template and training only on the assistant's tokens.
        * Train on the `<eot>` after each answer, or the model never learns to stop.
        * Pack to avoid padding waste, with a document mask (or position resets) so examples don't leak into each other.
        * Quality beats quantity: Llama 2 stopped at 27,540 high-quality SFT annotations ("Quality Is All You Need").''',
))

# ------------------------------------------------------------------ 02
NBS.append(dict(
    slug='02_lora', title='02 · LoRA from scratch', deck='post-training/03-lora-qlora/', deck_name='LoRA and QLoRA', minutes=40,
    goals='a LoRA linear layer, weight merging for zero-latency inference, parameter counting for real models, and a training loop that shows when a low rank is enough.',
    setup=BASE,
    tasks=[
        dict(fn='LoRALinear', title='The LoRA layer', md=r'''
            Freeze the pretrained weight $W_0$ ([d_in, d_out]) and learn a low-rank update $\Delta W = AB$ with $A \in \mathbb{R}^{d_{in}\times r}$, $B \in \mathbb{R}^{r\times d_{out}}$:
            $$y = xW_0 + \tfrac{\alpha}{r}\, xAB$$
            Initialization (LoRA paper): *"a random Gaussian initialization for A and zero for B, so ΔW = BA is zero at the beginning of training"*. The model starts exactly at $W_0$. (The paper writes $BA$ for column vectors; we use row vectors, so it's $AB$.)

            Implement `__init__` (A ~ N(0, 1/d_in), B = 0), `forward(x)` and `merged()` (returns $W_0 + \frac{\alpha}{r}AB$).''',
             starter=r'''
            class LoRALinear:
                def __init__(self, W0, r, alpha, seed=0):
                    self.W0, self.r, self.alpha = W0, r, alpha
                    rng = np.random.default_rng(seed)
                    # TODO: self.A ~ normal(0, 1/sqrt(d_in)) shape [d_in, r]; self.B zeros [r, d_out]
                    raise NotImplementedError

                def forward(self, x):
                    raise NotImplementedError

                def merged(self):
                    raise NotImplementedError''',
             test=r'''
            def _test_LoRALinear(cls):
                r_ = np.random.default_rng(1); W0 = r_.normal(size=(12, 7)); x = r_.normal(size=(5, 12))
                m = cls(W0, r=3, alpha=6)
                assert m.A.shape == (12, 3) and m.B.shape == (3, 7), "A is [d_in, r], B is [r, d_out]"
                assert np.allclose(m.forward(x), x @ W0), "with B = 0 the layer must equal the frozen W0"
                m.B = r_.normal(size=(3, 7))
                assert np.allclose(m.forward(x), x @ W0 + 2.0 * x @ m.A @ m.B), "scale alpha/r = 2 here"
                assert np.allclose(x @ m.merged(), m.forward(x)), "merged weight must give identical outputs"''',
             solution=r'''
            class LoRALinear_solution:
                def __init__(self, W0, r, alpha, seed=0):
                    self.W0, self.r, self.alpha = W0, r, alpha
                    rng = np.random.default_rng(seed)
                    self.A = rng.normal(0, 1 / np.sqrt(W0.shape[0]), (W0.shape[0], r))
                    self.B = np.zeros((r, W0.shape[1]))

                def forward(self, x):
                    return x @ self.W0 + (self.alpha / self.r) * (x @ self.A) @ self.B

                def merged(self):
                    return self.W0 + (self.alpha / self.r) * self.A @ self.B'''),
        dict(fn='lora_param_count', title='Count trainable parameters', md=r'''
            One adapted matrix of shape [d_in, d_out] adds $r(d_{in} + d_{out})$ trainable parameters.
            `targets` is a list of `(d_in, d_out)` shapes adapted in **each layer**; return the total over `n_layers`.

            The LoRA paper mostly adapts only $W_q$ and $W_v$. For Llama 3 8B ($W_q$: 4096×4096, $W_v$: 4096×1024 with GQA, 32 layers) at r = 8 that is **3,407,872**, about 0.04% of 8.03B.''',
             starter=r'''
            def lora_param_count(targets, n_layers, r):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_lora_param_count(f):
                assert f([(4096, 4096), (4096, 1024)], 32, 8) == 3_407_872, f"got {f([(4096, 4096), (4096, 1024)], 32, 8):,}"
                assert f([(10, 20)], 1, 1) == 30
                assert f([(10, 20)], 3, 4) == 360''',
             solution=r'''
            def lora_param_count_solution(targets, n_layers, r):
                return n_layers * sum(r * (a + b) for a, b in targets)'''),
        dict(fn='train_lora', title='Train only A and B', md=r'''
            Fit a frozen $W_0$ plus LoRA to targets $Y = XW^\star$, where the true update $W^\star - W_0$ has rank 4. Minimize $\frac{1}{N}\|XW_0 + sXAB - Y\|^2$ (with $s = \alpha/r$) by gradient descent on **A and B only**:
            $$E = XW_0 + sXAB - Y,\quad \nabla_B = \tfrac{2s}{N}(XA)^\top E,\quad \nabla_A = \tfrac{2s}{N}X^\top (E B^\top)$$
            Return the trained layer and the loss history. The tests check that rank ≥ 4 fits almost perfectly and rank 1 cannot.''',
             starter=r'''
            def train_lora(X, Y, W0, r, alpha=None, steps=2000, lr=0.05, layer_cls=None):
                alpha = alpha or r
                layer = (layer_cls or LoRALinear)(W0, r, alpha)
                hist = []
                # TODO: loop: compute E, grads for A and B, update both, record loss
                raise NotImplementedError''',
             test=r'''
            def _test_train_lora(f):
                rng = np.random.default_rng(3); d_in, d_out, N = 32, 24, 400
                W0 = rng.normal(0, 1 / np.sqrt(d_in), (d_in, d_out))
                Wstar = W0 + rng.normal(size=(d_in, 4)) @ rng.normal(size=(4, d_out)) / d_in
                X = rng.normal(size=(N, d_in)); Y = X @ Wstar
                cls = LoRALinear_solution if f.__name__.endswith('_solution') else LoRALinear
                _, h4 = f(X, Y, W0, 4, layer_cls=cls); _, h1 = f(X, Y, W0, 1, layer_cls=cls)
                assert h4[-1] < 0.02 * h4[0], f"rank 4 should fit the rank-4 update (loss {h4[0]:.4f} -> {h4[-1]:.4f})"
                assert h1[-1] > 0.2 * h4[0], f"rank 1 should NOT be able to fit a rank-4 update (final {h1[-1]:.4f})"''',
             solution=r'''
            def train_lora_solution(X, Y, W0, r, alpha=None, steps=2000, lr=0.05, layer_cls=None):
                alpha = alpha or r
                L = (layer_cls or LoRALinear_solution)(W0, r, alpha); s = alpha / r; N = len(X); hist = []
                for _ in range(steps):
                    XA = X @ L.A
                    E = X @ W0 + s * XA @ L.B - Y
                    hist.append((E ** 2).sum() / N)
                    gB = 2 * s / N * XA.T @ E
                    gA = 2 * s / N * X.T @ (E @ L.B.T)
                    L.A -= lr * gA; L.B -= lr * gB
                return L, hist'''),
    ],
    explore_md=r'''
        **Rank sweep.** Fit the same rank-4 update with r = 1…8. The error drops sharply once r reaches the true rank, which is the LoRA bet: fine-tuning updates have low "intrinsic rank". (The paper finds even r = 1–4 works for $W_q$ and $W_v$ on GPT-3.) Then the memory arithmetic: full fine-tuning with Adam keeps gradients and two optimizer moments for **every** parameter; LoRA keeps them only for A and B.''',
    explore=r'''
        rng = np.random.default_rng(3); d_in, d_out, N = 32, 24, 400
        W0 = rng.normal(0, 1 / np.sqrt(d_in), (d_in, d_out)); Wstar = W0 + rng.normal(size=(d_in, 4)) @ rng.normal(size=(4, d_out)) / d_in
        X = rng.normal(size=(N, d_in)); Y = X @ Wstar
        for r in [1, 2, 3, 4, 6, 8]:
            _, h = train_lora_solution(X, Y, W0, r)
            print(f"r={r}: final loss {h[-1]:.5f}  (trainable {lora_param_count_solution([(d_in, d_out)], 1, r)} vs full {d_in * d_out})")
        P = 8.03e9; lora = lora_param_count_solution([(4096, 4096), (4096, 1024)], 32, 8)
        print(f"\nLlama 3 8B, BF16 weights + FP32 grads + 2 FP32 Adam moments (rough):")
        print(f"  full fine-tune: {(2 * P + 12 * P) / 2**30:,.0f} GiB   LoRA r=8 on Wq,Wv: {(2 * P + 12 * lora) / 2**30:,.1f} GiB (frozen weights dominate)")''',
    takeaways=r'''
        * LoRA freezes $W_0$ and learns $\Delta W = AB$ of rank r. B starts at zero, so training starts exactly at the pretrained model.
        * After training, merge $W_0 + \frac{\alpha}{r}AB$ into one matrix: no extra inference latency, unlike adapter layers.
        * Trainable parameters shrink by orders of magnitude (the paper: 10,000× fewer for GPT-3 175B, 3× less GPU memory), and you can keep many small adapters for one base model.''',
))

# ------------------------------------------------------------------ 03
NBS.append(dict(
    slug='03_nf4_quantization', title='03 · QLoRA\'s NF4 and double quantization', deck='post-training/03-lora-qlora/', deck_name='LoRA and QLoRA', minutes=30,
    goals="QLoRA's 4-bit NormalFloat (NF4) blockwise quantizer, a comparison with uniform INT4 on Gaussian weights, and the double-quantization memory arithmetic.",
    setup=BASE + r'''
# Exact NF4 values from the QLoRA paper (Appendix E)
NF4 = np.array([-1.0, -0.6961928009986877, -0.5250730514526367, -0.39491748809814453, -0.28444138169288635,
                -0.18477343022823334, -0.09105003625154495, 0.0, 0.07958029955625534, 0.16093020141124725,
                0.24611230194568634, 0.33791524171829224, 0.44070982933044434, 0.5626170039176941,
                0.7229568362236023, 1.0])
INT4 = np.linspace(-1, 1, 16)   # 16 evenly spaced levels for comparison
''',
    tasks=[
        dict(fn='quantize_blockwise', title='Blockwise absmax quantization to a codebook', md=r'''
            Split the flattened weights into blocks of `block` values. For each block:
            1. the scale is $c = \max |w|$ in the block (the "absmax" quantization constant);
            2. normalize $w/c \in [-1, 1]$;
            3. store the **index** of the nearest codebook value (4 bits for 16 values).

            Return `(idx, scales)`, where `idx` has shape [n_blocks, block] and `scales` [n_blocks]. Assume `w.size` is a multiple of `block`.''',
             starter=r'''
            def quantize_blockwise(w, codebook, block=64):
                # TODO
                raise NotImplementedError

            def dequantize_blockwise(idx, scales, codebook, shape):
                # TODO: codebook[idx] * scales[:, None], reshaped
                raise NotImplementedError''',
             test=r'''
            def _test_quantize_blockwise(f):
                deq = dequantize_blockwise_solution if f.__name__.endswith('_solution') else dequantize_blockwise
                w = np.random.default_rng(1).normal(size=(8, 32))
                idx, sc = f(w, NF4, 64)
                assert idx.shape == (4, 64) and sc.shape == (4,), "4 blocks of 64"
                assert np.allclose(sc, np.abs(w.reshape(4, 64)).max(1)), "scale = absmax per block"
                assert idx.min() >= 0 and idx.max() <= 15
                wq = deq(idx, sc, NF4, w.shape)
                assert wq.shape == w.shape
                assert np.all(np.abs(wq) <= np.abs(w).max() + 1e-12)
                nearest = NF4[np.abs((w.reshape(4, 64) / sc[:, None])[..., None] - NF4).argmin(-1)]
                assert np.allclose(wq.reshape(4, 64), nearest * sc[:, None]), "each value must map to the NEAREST codebook entry"''',
             solution=r'''
            def quantize_blockwise_solution(w, codebook, block=64):
                b = w.reshape(-1, block)
                scales = np.abs(b).max(1)
                idx = np.abs((b / scales[:, None])[..., None] - codebook).argmin(-1)
                return idx, scales

            def dequantize_blockwise_solution(idx, scales, codebook, shape):
                return (codebook[idx] * scales[:, None]).reshape(shape)'''),
        dict(fn='quant_overhead_bits', title='Double quantization: the cost of the scales', md=r'''
            Each block stores one scale. With FP32 scales and blocksize 64 that's $32/64 = 0.5$ extra bits per parameter.
            **Double quantization** quantizes the scales themselves to 8 bits, in blocks of 256 with one FP32 constant each:
            $$\frac{8}{64} + \frac{32}{64\cdot 256} = 0.127 \text{ bits per parameter}$$
            QLoRA: a reduction of 0.373 bits per parameter, about 3 GB for a 65B model. Return the overhead in bits per parameter.''',
             starter=r'''
            def quant_overhead_bits(block=64, double=False, block2=256):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_quant_overhead_bits(f):
                assert np.isclose(f(64), 0.5)
                assert np.isclose(f(64, True), 0.126953125), f"got {f(64, True)} (the paper rounds this to 0.127)"
                saved_gb = (f(64) - f(64, True)) * 65e9 / 8 / 1e9
                assert 2.9 < saved_gb < 3.1, f"saving for 65B should be ~3 GB, got {saved_gb:.2f}"''',
             solution=r'''
            def quant_overhead_bits_solution(block=64, double=False, block2=256):
                return 8 / block + 32 / (block * block2) if double else 32 / block'''),
    ],
    explore_md=r'''
        **Why "NormalFloat"?** Pretrained weights are roughly zero-centred normal. NF4 puts its 16 levels at quantiles of a normal distribution, dense near 0 where most weights are, so it wastes fewer levels than evenly spaced INT4. QLoRA calls NF4 "information-theoretically optimal for normally distributed weights". Measure both on Gaussian weights, then add up the memory for a 65B model.''',
    explore=r'''
        w = np.random.default_rng(0).normal(0, 0.02, size=(4096, 1024))
        for name, cb in [('INT4 (uniform)', INT4), ('NF4', NF4)]:
            idx, sc = quantize_blockwise_solution(w, cb)
            wq = dequantize_blockwise_solution(idx, sc, cb, w.shape)
            print(f"{name:15} relative RMSE {np.sqrt(((w - wq) ** 2).mean()) / w.std():.4f}   levels used: {len(np.unique(idx))}/16")
        P = 65e9
        print(f"\n65B weights: BF16 {P * 2 / 1e9:.0f} GB  ->  NF4 {P * 0.5 / 1e9:.1f} GB + scales {P * quant_overhead_bits_solution(64) / 8 / 1e9:.1f} GB"
              f" (double-quantized: {P * quant_overhead_bits_solution(64, True) / 8 / 1e9:.1f} GB)")
        print("QLoRA reports fine-tuning 65B on a single 48 GB GPU (vs >780 GB for 16-bit full fine-tuning).")''',
    takeaways=r'''
        * QLoRA = a frozen base model stored in 4-bit NF4, dequantized to BF16 on the fly for each matmul, plus LoRA adapters trained in 16-bit.
        * NF4 spends its 16 levels where normally distributed weights actually are, so it has lower error than uniform INT4.
        * Double quantization shrinks the scale overhead from 0.5 to 0.127 bits per parameter. Paged optimizers absorb memory spikes. Together they let a 65B model fine-tune on one 48 GB GPU.''',
))

# ------------------------------------------------------------------ 04
NBS.append(dict(
    slug='04_reward_model', title='04 · Train a Bradley-Terry reward model', deck='post-training/04-reward-models/', deck_name='Reward models', minutes=35,
    goals='the pairwise preference loss used by InstructGPT and Llama 2, a reward model trained on simulated human comparisons, and the conversion from K-way rankings to training pairs.',
    setup=BASE + r'''
rng = np.random.default_rng(0)
d = 16
w_true = rng.normal(size=d)                      # the hidden "human" reward direction
def make_pairs(n, seed):
    """Two responses per prompt (feature vectors). The human prefers A with prob sigmoid(r_A - r_B) (Bradley-Terry)."""
    r_ = np.random.default_rng(seed)
    A, Bv = r_.normal(size=(n, d)), r_.normal(size=(n, d))
    pA = 1 / (1 + np.exp(-(A @ w_true - Bv @ w_true) / 2))
    a_wins = r_.random(n) < pA
    win = np.where(a_wins[:, None], A, Bv); lose = np.where(a_wins[:, None], Bv, A)
    return win, lose
train_w, train_l = make_pairs(2000, 1)
test_w, test_l = make_pairs(2000, 2)
''',
    tasks=[
        dict(fn='bt_loss', title='The pairwise loss', md=r'''
            A reward model $r_\theta(x, y)$ outputs one scalar per response. Under the **Bradley-Terry** model, the probability that $y_w$ beats $y_l$ is $\sigma(r_w - r_l)$. Train by maximizing the log-likelihood of the observed choices (InstructGPT eq. 1):
            $$\mathcal{L} = -\mathbb{E}\big[\log \sigma(r_\theta(x,y_w) - r_\theta(x,y_l))\big]$$
            Use `log_sigmoid` (numerically stable). Only **differences** matter, so adding a constant to every reward changes nothing.''',
             starter=r'''
            def bt_loss(r_w, r_l):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_bt_loss(f):
                assert np.isclose(f(np.array([0.0]), np.array([0.0])), np.log(2)), "equal rewards -> loss log 2"
                rw, rl = np.array([2.0, -1.0, 50.0]), np.array([1.0, 1.0, -50.0])
                assert np.isclose(f(rw, rl), np.mean([np.log1p(np.exp(-1)), np.log1p(np.exp(2)), 0.0]), atol=1e-12)
                assert np.isclose(f(rw + 7, rl + 7), f(rw, rl)), "shift invariance"
                assert np.isfinite(f(np.array([-1000.0]), np.array([1000.0]))), "must be numerically stable"''',
             solution=r'''
            def bt_loss_solution(r_w, r_l):
                return -log_sigmoid(r_w - r_l).mean()'''),
        dict(fn='train_rm', title='Fit a linear reward model', md=r'''
            Our "responses" are feature vectors, and the reward model is linear: $r = \phi \cdot w$. Fit $w$ by gradient descent on the Bradley-Terry loss:
            $$\nabla_w \mathcal{L} = -\tfrac{1}{N}\textstyle\sum (1-\sigma(z))(\phi_w - \phi_l),\qquad z = (\phi_w - \phi_l)\cdot w$$
            Return `w` and the loss history. The tests check held-out accuracy (fraction of pairs where the RM prefers the human's choice) is close to the best achievable, because the labels themselves are noisy.''',
             starter=r'''
            def train_rm(Phi_w, Phi_l, steps=500, lr=0.5):
                w = np.zeros(Phi_w.shape[1]); hist = []
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_train_rm(f):
                w, hist = f(train_w, train_l)
                assert hist[-1] < hist[0], "loss must decrease"
                acc = ((test_w - test_l) @ w > 0).mean()
                oracle = ((test_w - test_l) @ w_true > 0).mean()
                assert acc > oracle - 0.03, f"held-out accuracy {acc:.3f} should be close to the oracle's {oracle:.3f}"''',
             solution=r'''
            def train_rm_solution(Phi_w, Phi_l, steps=500, lr=0.5):
                w = np.zeros(Phi_w.shape[1]); D = Phi_w - Phi_l; hist = []
                for _ in range(steps):
                    z = D @ w
                    hist.append(-log_sigmoid(z).mean())
                    grad = -((1 - 1 / (1 + np.exp(-z)))[:, None] * D).mean(0)
                    w -= lr * grad
                return w, hist'''),
        dict(fn='ranking_to_pairs', title='From a K-way ranking to pairs', md=r'''
            InstructGPT labelers ranked between **K = 4 and K = 9** responses per prompt. A ranking of K items yields $\binom{K}{2}$ comparisons. Given a ranking (best first), return all `(winner, loser)` pairs.
            (InstructGPT trains on all $\binom{K}{2}$ pairs from one prompt as a single batch element, because the pairs are highly correlated and treating them as independent caused overfitting.)''',
             starter=r'''
            def ranking_to_pairs(ranking):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_ranking_to_pairs(f):
                p = f(['a', 'b', 'c'])
                assert sorted(p) == [('a', 'b'), ('a', 'c'), ('b', 'c')]
                assert len(f(list(range(4)))) == 6 and len(f(list(range(9)))) == 36, "C(4,2)=6, C(9,2)=36"''',
             solution=r'''
            def ranking_to_pairs_solution(ranking):
                return [(ranking[i], ranking[j]) for i in range(len(ranking)) for j in range(i + 1, len(ranking))]'''),
    ],
    explore_md=r'''
        **Accuracy vs data, and the noise ceiling.** Human labels are noisy, so even the true reward function can't predict every choice. Real reward models reach only modest held-out agreement with labelers, which is expected, not a bug. See how accuracy grows with the number of comparisons.''',
    explore=r'''
        oracle = ((test_w - test_l) @ w_true > 0).mean()
        for n in [25, 100, 400, 2000]:
            w, _ = train_rm_solution(train_w[:n], train_l[:n])
            print(f"{n:5d} comparisons: held-out accuracy {((test_w - test_l) @ w > 0).mean():.3f}   (oracle ceiling {oracle:.3f})")
        print("\nLlama 2 trained its reward models on over 1 million human binary comparisons (1,418,091 Meta comparisons).")''',
    takeaways=r'''
        * A reward model turns comparisons into a scalar score via the Bradley-Terry loss $-\log\sigma(r_w - r_l)$. Only differences between rewards are identified.
        * Comparisons are easier and more consistent for humans than absolute scores, and a K-way ranking gives $\binom{K}{2}$ pairs.
        * Accuracy is capped by label noise. A perfect reward model doesn't exist, which is one reason RL against it needs a leash (decks 05–06).''',
))

# ------------------------------------------------------------------ 05
NBS.append(dict(
    slug='05_ppo_toy', title='05 · PPO with a KL penalty on a toy policy', deck='post-training/05-rlhf-ppo/', deck_name='RLHF with PPO', minutes=45,
    goals='the KL-penalized reward used in RLHF, the PPO clipped objective, and a training loop on a one-step "language model" whose exact optimum you can compute and compare against.',
    setup=BASE + r'''
V = 8                                             # a "vocabulary" of 8 possible responses
theta_ref = np.array([2.0, 1.5, 1.0, 0.5, 0.0, -0.5, -1.0, -1.5])   # SFT / reference policy logits
reward = np.array([0.0, 0.2, 0.5, 0.1, 1.0, 0.3, 2.0, 0.0])        # reward model score per response
pi_ref = softmax(theta_ref)

def optimal_policy(beta):
    """Closed-form optimum of E[r] - beta*KL(pi || pi_ref): pi* ∝ pi_ref * exp(r / beta)."""
    return softmax(np.log(pi_ref) + reward / beta)

def kl(p, q):
    return float((p * (np.log(p) - np.log(q))).sum())
''',
    tasks=[
        dict(fn='kl_penalized_reward', title='The KL-penalized reward', md=r'''
            InstructGPT adds *"a per-token KL penalty from the SFT model at each token to mitigate overoptimization of the reward model"*:
            $$R(x, y) = r_\theta(x,y) - \beta \log\frac{\pi^{RL}(y\mid x)}{\pi^{SFT}(y\mid x)}$$
            Given per-sample rewards, policy log-probs and reference log-probs, return R. Averaged over samples from π, the penalty term equals β·KL(π‖π_ref).''',
             starter=r'''
            def kl_penalized_reward(r, logp, logp_ref, beta):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_kl_penalized_reward(f):
                assert np.allclose(f(np.array([1.0, 2.0]), np.log([.5, .25]), np.log([.25, .25]), 0.5), [1 - 0.5 * np.log(2), 2.0])
                p = softmax(np.array([1.0, 0, -1])); q = softmax(np.zeros(3)); r_ = np.zeros(3)
                assert np.isclose((p * f(r_, np.log(p), np.log(q), 1.0)).sum(), -kl(p, q)), "expected penalty = beta * KL"''',
             solution=r'''
            def kl_penalized_reward_solution(r, logp, logp_ref, beta):
                return r - beta * (logp - logp_ref)'''),
        dict(fn='ppo_clip_objective', title='The PPO clipped objective', md=r'''
            PPO (Schulman et al. 2017) maximizes
            $$L^{CLIP} = \mathbb{E}\big[\min\big(\rho\,\hat A,\ \mathrm{clip}(\rho, 1-\epsilon, 1+\epsilon)\,\hat A\big)\big],\qquad \rho = \frac{\pi_\theta(a)}{\pi_{\theta_{old}}(a)}$$
            with ε = 0.2 in the paper. The `min` makes it pessimistic: once the ratio moves past 1±ε in the direction that helps, the gradient stops, so one batch can't push the policy too far.
            Return the objective (to **maximize**) given new and old log-probs and advantages.''',
             starter=r'''
            def ppo_clip_objective(logp_new, logp_old, adv, eps=0.2):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_ppo_clip_objective(f):
                lo = np.log(np.full(4, .25)); ln = np.log([.25, .5, .1, .4]); A = np.array([1.0, 1.0, -1.0, -1.0])
                ratio = np.exp(ln - lo)   # 1, 2, 0.4, 1.6
                want = np.mean([1.0, 1.2, -0.8, -1.6])
                assert np.isclose(f(ln, lo, A), want), f"got {f(ln, lo, A)}, expected {want} (min of unclipped and clipped)"
                assert np.isclose(f(lo, lo, A), A.mean()), "ratio 1 -> plain advantage"''',
             solution=r'''
            def ppo_clip_objective_solution(logp_new, logp_old, adv, eps=0.2):
                ratio = np.exp(logp_new - logp_old)
                return np.minimum(ratio * adv, np.clip(ratio, 1 - eps, 1 + eps) * adv).mean()'''),
        dict(fn='train_ppo', title='Train the toy policy with PPO', md=r'''
            Loop for `iters` iterations:
            1. Sample `batch` responses from the current policy $\pi_{old} = \mathrm{softmax}(\theta)$.
            2. Compute KL-penalized rewards; advantage = reward − batch mean (a simple baseline instead of a value network).
            3. Run `epochs` gradient-**ascent** steps on $L^{CLIP}$ w.r.t. θ. For a softmax policy, $\nabla_\theta \log\pi(a) = e_a - \pi$. Each sample whose term is *not* clipped contributes $\hat A\,\rho\,(e_a - \pi)$; clipped samples contribute 0.

            Return final θ and a history of (expected reward, KL to reference). The tests compare your result with the exact optimum $\pi^\star \propto \pi_{ref}\,e^{r/\beta}$.''',
             starter=r'''
            def train_ppo(beta=0.5, iters=300, batch=256, epochs=4, lr=0.5, eps=0.2, seed=0):
                rng = np.random.default_rng(seed); theta = theta_ref.copy(); hist = []
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_train_ppo(f):
                th, h = f(beta=0.5)
                p = softmax(th)
                assert h[-1][0] > h[0][0] + 0.3, "expected reward should rise substantially"
                assert kl(optimal_policy(0.5), p) < 0.05, f"should approach pi* ∝ pi_ref*exp(r/beta); KL(pi*||pi) = {kl(optimal_policy(0.5), p):.3f}"
                th2, h2 = f(beta=2.0)
                assert h2[-1][1] < h[-1][1], "a larger beta must keep the policy closer to the reference"''',
             solution=r'''
            def train_ppo_solution(beta=0.5, iters=300, batch=256, epochs=4, lr=0.5, eps=0.2, seed=0):
                rng = np.random.default_rng(seed); theta = theta_ref.copy(); hist = []
                for _ in range(iters):
                    p_old = softmax(theta); a = rng.choice(V, size=batch, p=p_old)
                    R = kl_penalized_reward_solution(reward[a], np.log(p_old[a]), np.log(pi_ref[a]), beta)
                    adv = R - R.mean()
                    for _ in range(epochs):
                        p = softmax(theta); ratio = p[a] / p_old[a]
                        active = ~(((adv > 0) & (ratio > 1 + eps)) | ((adv < 0) & (ratio < 1 - eps)))
                        coef = np.where(active, adv * ratio, 0.0)
                        grad = (np.bincount(a, weights=coef, minlength=V) - coef.sum() * p) / batch
                        theta = theta + lr * grad
                    p = softmax(theta); hist.append((float(p @ reward), kl(p, pi_ref)))
                return theta, hist'''),
    ],
    explore_md=r'''
        **β is the leash.** Small β lets the policy chase the reward model; large β keeps it near the SFT model. The exact optimum of $\mathbb{E}[r] - \beta\,\mathrm{KL}$ is $\pi^\star \propto \pi_{ref}e^{r/\beta}$: the same formula DPO builds on (notebook 07).''',
    explore=r'''
        print("beta   E[reward]  KL(pi||ref)   P(best response)   | exact optimum E[r], KL")
        for beta in [0.1, 0.25, 0.5, 1.0, 2.0, 5.0]:
            th, h = train_ppo_solution(beta=beta, iters=200)
            p, ps = softmax(th), optimal_policy(beta)
            print(f"{beta:4}   {p @ reward:8.3f}   {kl(p, pi_ref):10.3f}   {p[6]:15.2f}     | {ps @ reward:.3f}, {kl(ps, pi_ref):.3f}")''',
    takeaways=r'''
        * RLHF maximizes the reward-model score minus β·KL to the SFT model. The KL term stops the policy drifting into regions where the reward model is wrong.
        * PPO's clipped ratio limits how far one batch can move the policy, which makes many gradient steps per batch safe.
        * Real RLHF keeps four models in memory: the policy, the reference (SFT), the reward model, and a value model (critic) that estimates advantages per token. Here a batch-mean baseline replaces the critic, which is the idea GRPO scales up (notebook 08).''',
))

# ------------------------------------------------------------------ 06
NBS.append(dict(
    slug='06_overoptimization', title='06 · Reward hacking: best-of-n against a flawed reward model', deck='post-training/06-reward-hacking/', deck_name='Reward hacking and overoptimization', minutes=35,
    goals="best-of-n sampling, its analytic KL, and a simulation where optimizing a proxy reward model first helps and then hurts the true (gold) reward, reproducing Gao et al.'s overoptimization curve.",
    setup=BASE + r'''
def sample_responses(n, rng):
    """Each response has two features: 'helpfulness' h and 'length' L (both standard normal)."""
    return rng.normal(size=(n, 2))

def gold_reward(F):
    """What we actually want: helpfulness counts, extreme length is bad."""
    return F[:, 0] - 0.5 * F[:, 1] ** 2

def proxy_reward(F):
    """A learned reward model that partly mistook length for quality."""
    return F[:, 0] + 1.0 * F[:, 1]
''',
    tasks=[
        dict(fn='kl_bon', title='KL of best-of-n', md=r'''
            Best-of-n: sample n responses, return the one the reward model scores highest. It is a simple, strong baseline (Llama 2 calls its version *rejection sampling*). How far does it move from the base policy? Analytically (Stiennon et al. 2020, used by Gao et al.):
            $$\mathrm{KL}_{bon} = \log n - \frac{n-1}{n}$$''',
             starter=r'''
            def kl_bon(n):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_kl_bon(f):
                assert np.isclose(f(1), 0.0)
                assert np.isclose(f(2), np.log(2) - 0.5)
                assert np.isclose(f(1000), np.log(1000) - 0.999)''',
             solution=r'''
            def kl_bon_solution(n):
                return np.log(n) - (n - 1) / n'''),
        dict(fn='best_of_n', title='Pick the best by the proxy', md=r'''
            Given proxy scores and gold scores of shape [prompts, n], select per prompt the response with the highest **proxy** score and return the mean proxy and mean **gold** score of the selected responses.''',
             starter=r'''
            def best_of_n(proxy, gold):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_best_of_n(f):
                p = np.array([[1, 5, 2], [0, -1, 3]]); g = np.array([[10, 0, 4], [1, 2, -6]])
                assert np.allclose(f(p, g), (4.0, -3.0)), f"got {f(p, g)}"''',
             solution=r'''
            def best_of_n_solution(proxy, gold):
                i = proxy.argmax(1); rows = np.arange(len(proxy))
                return proxy[rows, i].mean(), gold[rows, i].mean()'''),
        dict(fn='bon_sweep', title='Sweep n and watch the gold reward', md=r'''
            For each n in `ns`, sample `prompts × n` responses, score them with `proxy_reward` and `gold_reward`, run `best_of_n`, and record `(n, kl_bon(n), proxy, gold)`.
            Expected (and tested): the proxy rises monotonically, but gold **peaks and then falls**, because large n increasingly selects long responses the proxy over-rewards. That is Goodhart's law: "When a measure becomes a target, it ceases to be a good measure."''',
             starter=r'''
            def bon_sweep(ns=(1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024), prompts=2000, seed=0):
                rng = np.random.default_rng(seed); out = []
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_bon_sweep(f):
                res = np.array(f())
                proxy, gold = res[:, 2], res[:, 3]
                assert np.all(np.diff(proxy) > 0), "proxy score must increase with n"
                k = gold.argmax()
                assert 0 < k < len(gold) - 1, f"gold should peak at an intermediate n, peaked at index {k}"
                assert gold[-1] < gold[k] - 0.2, "gold must fall clearly after the peak"''',
             solution=r'''
            def bon_sweep_solution(ns=(1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024), prompts=2000, seed=0):
                rng = np.random.default_rng(seed); out = []
                for n in ns:
                    F = sample_responses(prompts * n, rng)
                    p, g = proxy_reward(F).reshape(prompts, n), gold_reward(F).reshape(prompts, n)
                    mp, mg = best_of_n_solution(p, g)
                    out.append((n, kl_bon_solution(n), mp, mg))
                return out'''),
    ],
    explore_md=r'''
        **Fit Gao et al.'s functional form.** They found that for best-of-n the gold score follows $R(d) = d(\alpha - \beta d)$ with $d = \sqrt{\mathrm{KL}}$ (for RL: $d(\alpha - \beta\log d)$). Fit α and β to the simulation by least squares and compare predicted and simulated values. Our toy model isn't theirs, so expect the shape, not their coefficients.''',
    explore=r'''
        res = np.array(bon_sweep_solution()); d = np.sqrt(res[:, 1]); gold = res[:, 3] - res[0, 3]
        A = np.stack([d, -d ** 2], 1); (a, b), *_ = np.linalg.lstsq(A, gold, rcond=None)
        print(f"fit: R(d) = d({a:.3f} - {b:.3f} d)   -> predicted peak at d = {a / (2 * b):.2f} (KL ≈ {(a / (2 * b)) ** 2:.2f} nats)")
        for (n, k, p, g), gd in zip(res, gold):
            dd = np.sqrt(k)
            print(f"n={int(n):5d}  KL={k:5.2f}  proxy={p:5.2f}  gold Δ={gd:+.3f}  fit Δ={dd * (a - b * dd):+.3f}")''',
    takeaways=r'''
        * Any reward model is a proxy. Optimize it hard enough and you find its mistakes: the proxy score keeps rising while true quality falls.
        * KL from the starting policy is the natural "distance optimized". Gao et al. show gold reward vs $\sqrt{\mathrm{KL}}$ has a predictable rise-then-fall shape whose coefficients scale smoothly with reward-model size.
        * Mitigations: a KL penalty or early stopping, bigger and better reward models, fresh preference data on the current policy's outputs (Llama 2 and 3 iterate in rounds), and rewards that can be verified (deck 08).''',
))

# ------------------------------------------------------------------ 07
NBS.append(dict(
    slug='07_dpo', title='07 · Direct Preference Optimization (DPO)', deck='post-training/07-dpo-and-friends/', deck_name='DPO, KTO and rejection sampling', minutes=40,
    goals='the DPO loss, the implicit reward it defines, and training on preference pairs; then a check that DPO recovers the same optimal policy RLHF targets, with no reward model and no RL loop.',
    setup=BASE + r'''
K = 6
theta_ref = np.array([1.0, 0.5, 0.0, 0.0, -0.5, -1.0]); pi_ref = softmax(theta_ref)
r_true = np.array([0.0, 1.0, -0.5, 2.0, 0.5, 1.5])   # hidden reward behind the human labels
BETA = 0.5
def optimal_policy(beta):
    return softmax(np.log(pi_ref) + r_true / beta)
def kl(p, q):
    return float((p * (np.log(p) - np.log(q))).sum())
def make_prefs(n, seed=0):
    """Pairs sampled from the reference policy, labelled by Bradley-Terry on r_true."""
    rng = np.random.default_rng(seed)
    a, b = rng.choice(K, n, p=pi_ref), rng.choice(K, n, p=pi_ref)
    keep = a != b; a, b = a[keep], b[keep]
    a_wins = rng.random(len(a)) < 1 / (1 + np.exp(-(r_true[a] - r_true[b])))
    return np.where(a_wins, a, b), np.where(a_wins, b, a)
yw, yl = make_prefs(20000)
''',
    tasks=[
        dict(fn='dpo_loss', title='The DPO loss', md=r'''
            Rafailov et al. (2023) show the RLHF optimum $\pi^\star \propto \pi_{ref}\,e^{r/\beta}$ can be inverted: $r(x,y) = \beta\log\frac{\pi^\star(y|x)}{\pi_{ref}(y|x)} + \beta\log Z(x)$. Plug this into the Bradley-Terry loss and $Z$ cancels:
            $$\mathcal{L}_{DPO} = -\mathbb{E}\Big[\log\sigma\Big(\beta\log\frac{\pi_\theta(y_w)}{\pi_{ref}(y_w)} - \beta\log\frac{\pi_\theta(y_l)}{\pi_{ref}(y_l)}\Big)\Big]$$
            Implement it from log-probs, plus `implicit_reward(logp, logp_ref, beta)` $= \beta(\log\pi_\theta - \log\pi_{ref})$.''',
             starter=r'''
            def implicit_reward(logp, logp_ref, beta):
                raise NotImplementedError

            def dpo_loss(lp_w, lp_l, ref_w, ref_l, beta):
                # TODO: -mean log_sigmoid(beta * ((lp_w - ref_w) - (lp_l - ref_l)))
                raise NotImplementedError''',
             test=r'''
            def _test_dpo_loss(f):
                z = np.zeros(3)
                assert np.isclose(f(z, z, z, z, 0.5), np.log(2)), "policy == reference -> loss log 2"
                lw, ll, rw, rl = np.log([.5, .2]), np.log([.1, .3]), np.log([.25, .25]), np.log([.25, .25])
                want = -log_sigmoid(0.5 * ((lw - rw) - (ll - rl))).mean()
                assert np.isclose(f(lw, ll, rw, rl, 0.5), want)
                ir = implicit_reward_solution if f.__name__.endswith('_solution') else implicit_reward
                assert np.allclose(ir(np.log([.5]), np.log([.25]), 2.0), [2 * np.log(2)])''',
             solution=r'''
            def implicit_reward_solution(logp, logp_ref, beta):
                return beta * (logp - logp_ref)

            def dpo_loss_solution(lp_w, lp_l, ref_w, ref_l, beta):
                return -log_sigmoid(beta * ((lp_w - ref_w) - (lp_l - ref_l))).mean()'''),
        dict(fn='train_dpo', title='Train with DPO', md=r'''
            Our policy is a softmax over K responses with logits θ (start at `theta_ref`). With $z = \beta[(\log\pi(y_w) - \log\pi_{ref}(y_w)) - (\log\pi(y_l) - \log\pi_{ref}(y_l))]$ and $\nabla_\theta\log\pi(a) = e_a - \pi$, the gradient of the loss for one pair is
            $$\nabla_\theta\mathcal{L} = -(1 - \sigma(z))\,\beta\,(e_{y_w} - e_{y_l})$$
            (the $-\pi$ terms cancel). Run full-batch gradient descent on all pairs and return θ and the loss history.''',
             starter=r'''
            def train_dpo(yw, yl, beta=BETA, steps=1500, lr=2.0):
                theta = theta_ref.copy(); hist = []
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_train_dpo(f):
                th, hist = f(yw, yl)
                assert hist[-1] < hist[0], "loss must decrease"
                p = softmax(th)
                assert kl(optimal_policy(BETA), p) < 0.02, f"DPO should recover pi* ∝ pi_ref*exp(r/beta); KL = {kl(optimal_policy(BETA), p):.4f}"
                ir = BETA * (np.log(p) - np.log(pi_ref))
                assert np.corrcoef(ir, r_true)[0, 1] > 0.98, "implicit rewards should match the true rewards up to a constant"''',
             solution=r'''
            def train_dpo_solution(yw, yl, beta=BETA, steps=1500, lr=2.0):
                theta = theta_ref.copy(); hist = []; lref = np.log(pi_ref)
                for _ in range(steps):
                    lp = log_softmax(theta)
                    z = beta * ((lp[yw] - lref[yw]) - (lp[yl] - lref[yl]))
                    hist.append(-log_sigmoid(z).mean())
                    c = (1 - 1 / (1 + np.exp(-z))) * beta
                    grad = -(np.bincount(yw, c, K) - np.bincount(yl, c, K)) / len(yw)
                    theta = theta - lr * grad
                return theta, hist'''),
    ],
    explore_md=r'''
        **Same target, two routes.** RLHF: fit a reward model, then run RL with a KL penalty (notebooks 04–05). DPO: one classification-style loss directly on the policy. With enough data both aim at $\pi^\star \propto \pi_{ref}e^{r/\beta}$. Below, the effect of β and of data size, and the implicit rewards DPO learns (equal to the true rewards up to a constant).''',
    explore=r'''
        for beta in [0.1, 0.5, 2.0]:
            th, _ = train_dpo_solution(yw, yl, beta=beta); p = softmax(th)
            print(f"beta={beta}: KL(pi||ref)={kl(p, pi_ref):.3f}  E[r_true]={p @ r_true:.3f}  KL(pi*||pi)={kl(optimal_policy(beta), p):.4f}")
        for n in [200, 2000, 20000]:
            a, b = make_prefs(n, seed=5); th, _ = train_dpo_solution(a, b); p = softmax(th)
            print(f"{n:6d} pairs: KL(pi*||pi) = {kl(optimal_policy(BETA), p):.4f}")
        th, _ = train_dpo_solution(yw, yl); ir = BETA * (log_softmax(th) - np.log(pi_ref))
        print("\nimplicit reward − mean:", np.round(ir - ir.mean(), 2), "\ntrue reward − mean:    ", np.round(r_true - r_true.mean(), 2))''',
    takeaways=r'''
        * DPO turns RLHF's objective into a supervised loss on preference pairs: no reward model, no sampling, no critic. That is why it is popular (Llama 3's post-training uses SFT, rejection sampling and DPO).
        * The policy *is* the reward model: $\beta\log\frac{\pi_\theta}{\pi_{ref}}$ is its implicit reward.
        * Caveats: DPO learns only from the fixed pairs it is given (offline). Iterating, by collecting new pairs from the current model, closes much of the gap with online RL.''',
))

# ------------------------------------------------------------------ 08
NBS.append(dict(
    slug='08_grpo_rlvr', title='08 · RL with verifiable rewards and GRPO', deck='post-training/08-rlvr-grpo/', deck_name='RLVR and GRPO', minutes=45,
    goals='a verifiable reward, group-relative advantages (GRPO), and a critic-free RL loop that teaches a toy "model" to do arithmetic, plus a look at why groups where every answer is right or wrong give no signal.',
    setup=BASE + r'''
QUESTIONS = [(a, b) for a in range(10) for b in range(10)]      # "what is a + b?"
N_ANS = 19                                                       # answers 0..18
def base_logits(seed=0):
    """A weak 'base model': some mass on the right answer, more on near misses and a few favourite numbers."""
    rng = np.random.default_rng(seed); L = rng.normal(0, 1.0, (len(QUESTIONS), N_ANS))
    for q, (a, b) in enumerate(QUESTIONS):
        L[q, a + b] += 1.5; L[q, max(0, a + b - 1)] += 1.0; L[q, min(18, a + b + 1)] += 1.0
    return L
THETA0 = base_logits()
def accuracy(theta):
    p = softmax(theta); return float(np.mean([p[q, a + b] for q, (a, b) in enumerate(QUESTIONS)]))
print(f"base model: expected accuracy {accuracy(THETA0):.2f}")
''',
    tasks=[
        dict(fn='verify', title='A verifiable reward', md=r'''
            For maths, code and logic you can often **check** an answer instead of asking a reward model. DeepSeek-R1-Zero uses rule-based rewards: an *accuracy* reward (is the final answer correct?) and a *format* reward (is the reasoning inside the required tags?). Tülu 3 named this approach **RLVR** (RL with verifiable rewards).
            Return 1.0 if `answer == a + b`, else 0.0. (No format term in this toy.)''',
             starter=r'''
            def verify(question, answer):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_verify(f):
                assert f((3, 4), 7) == 1.0 and f((3, 4), 8) == 0.0 and f((0, 0), 0) == 1.0''',
             solution=r'''
            def verify_solution(question, answer):
                return float(answer == question[0] + question[1])'''),
        dict(fn='group_advantages', title='Group-relative advantages', md=r'''
            GRPO (DeepSeekMath, 2024) samples a **group** of G outputs per question and uses the group itself as the baseline:
            $$\hat A_i = \frac{r_i - \mathrm{mean}(r)}{\mathrm{std}(r)}$$
            Every token of output *i* gets this advantage. No value network (critic) is needed: *"GRPO foregoes the critic model, instead estimating the baseline from group scores"*.
            Return the advantages for one group. If all rewards are equal (std = 0), return zeros: the group carries no learning signal.''',
             starter=r'''
            def group_advantages(r, eps=1e-8):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_group_advantages(f):
                a = f(np.array([1.0, 0.0, 0.0, 1.0]))
                assert np.allclose(a, [1, -1, -1, 1]), f"got {a}"
                assert np.allclose(f(np.ones(5)), 0) and np.allclose(f(np.zeros(5)), 0), "all-equal groups give zero advantage"
                b = f(np.array([1.0, 0, 0, 0]))
                assert np.isclose(b.mean(), 0) and np.isclose(b.std(), 1)''',
             solution=r'''
            def group_advantages_solution(r, eps=1e-8):
                s = r.std()
                return np.zeros_like(r) if s < eps else (r - r.mean()) / s'''),
        dict(fn='train_grpo', title='A critic-free RL loop', md=r'''
            Each iteration:
            1. Pick `n_q` random questions. For each, sample **G** answers from softmax(θ[q]).
            2. Score them with `verify` and compute group advantages.
            3. Policy-gradient step: $\theta[q] \mathrel{+}= \frac{lr}{G}\sum_i \hat A_i\,(e_{o_i} - \pi_q)$, then subtract $\beta(\pi_q - \pi_{ref,q})$: a simple pull back toward the starting policy that stands in for GRPO's KL penalty (DeepSeek-R1 uses a KL coefficient of 0.001; we use a small β).

            (Full GRPO also uses PPO's clipped ratio for several updates per batch; with one on-policy step the ratio is 1, so it drops out.) Return θ and the accuracy history.''',
             starter=r'''
            def train_grpo(G=8, iters=400, n_q=32, lr=1.0, beta=0.01, seed=0):
                rng = np.random.default_rng(seed); theta = THETA0.copy(); pref = softmax(THETA0); hist = []
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_train_grpo(f):
                th, h = f()
                assert h[0] < 0.4 and h[-1] > 0.9, f"accuracy should go from ~{accuracy(THETA0):.2f} to > 0.9, got {h[-1]:.2f}"''',
             solution=r'''
            def train_grpo_solution(G=8, iters=400, n_q=32, lr=1.0, beta=0.01, seed=0):
                rng = np.random.default_rng(seed); theta = THETA0.copy(); pref = softmax(THETA0); hist = []
                for _ in range(iters):
                    for q in rng.choice(len(QUESTIONS), n_q, replace=False):
                        p = softmax(theta[q]); outs = rng.choice(N_ANS, G, p=p)
                        A = group_advantages_solution(np.array([verify_solution(QUESTIONS[q], o) for o in outs]))
                        grad = (np.bincount(outs, A, N_ANS) - A.sum() * p) / G
                        theta[q] += lr * (grad - beta * (p - pref[q]))
                    hist.append(accuracy(theta))
                return theta, hist'''),
    ],
    explore_md=r'''
        **When does a group teach anything?** If all G answers are right, or all wrong, every advantage is 0. Questions the model always or never solves give no gradient, which is why RLVR data is filtered to problems of the right difficulty and why larger G helps on hard questions. Compute the fraction of "dead" groups for the base model at several G, then the effect of G on training.''',
    explore=r'''
        p_right = np.array([softmax(THETA0[q])[a + b] for q, (a, b) in enumerate(QUESTIONS)])
        for G in [2, 4, 8, 16, 64]:
            dead = np.mean(p_right ** G + (1 - p_right) ** G)
            print(f"G={G:3d}: expected fraction of groups with zero signal = {dead:.2f}")
        print()
        for G in [2, 4, 16]:
            _, h = train_grpo_solution(G=G, iters=150)
            print(f"G={G:2d}: accuracy after 150 iterations {h[-1]:.2f}  (samples used: {150 * 32 * G:,})")''',
    takeaways=r'''
        * Where correctness can be checked (maths, code, formats), a rule-based reward replaces the learned reward model, and there is far less to hack.
        * GRPO drops PPO's critic: the mean and std of a group of samples for the same prompt act as the baseline. That saves a whole model's worth of memory.
        * DeepSeekMath: GRPO took MATH from 46.8% to 51.7%. DeepSeek-R1-Zero: RL alone (no SFT) took AIME 2024 pass@1 from 15.6% to 77.9%, with longer reasoning and self-reflection emerging along the way.''',
))
