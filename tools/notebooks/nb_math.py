"""Math for LLMs exercise notebooks (NumPy only)."""

NBS = []

# ------------------------------------------------------------------ 01
NBS.append(dict(
    slug='01_vectors_similarity', title='01 · Vectors, dot products and similarity', deck='math/01-vectors-dot-products/', deck_name='Vectors and dot products', minutes=25,
    goals='dot products, norms and cosine similarity from scratch, a nearest-neighbour search over toy embeddings, and the √d scaling that attention uses.',
    setup=r'''
rng = np.random.default_rng(0)
WORDS = ['king', 'queen', 'man', 'woman', 'apple', 'banana']
# toy 4-d embeddings: [royalty, male, female, fruit]
EMB = np.array([[0.9, 0.8, 0.1, 0.0], [0.9, 0.1, 0.8, 0.0], [0.1, 0.9, 0.1, 0.0],
                [0.1, 0.1, 0.9, 0.0], [0.0, 0.0, 0.1, 0.9], [0.0, 0.1, 0.0, 0.95]])
''',
    tasks=[
        dict(fn='cosine', title='Cosine similarity', md=r'''
            Implement $\cos(a, b) = \dfrac{a \cdot b}{\lVert a \rVert\,\lVert b \rVert}$ using only `np.sum` and `np.sqrt` (no `np.dot`, no `np.linalg`).
            It is the dot product after both vectors are scaled to length 1, so it measures **direction only**.''',
             starter=r'''
            def cosine(a, b):
                # TODO: dot product divided by the product of the two lengths
                raise NotImplementedError''',
             test=r'''
            def _test_cosine(f):
                assert np.isclose(f(np.array([1., 0]), np.array([0., 1])), 0), "orthogonal vectors have cosine 0"
                assert np.isclose(f(np.array([1., 2]), np.array([2., 4])), 1), "parallel vectors have cosine 1"
                assert np.isclose(f(np.array([1., 2]), np.array([-1., -2])), -1), "opposite vectors have cosine -1"
                a, b = rng.normal(size=8), rng.normal(size=8)
                assert np.isclose(f(a, b), a @ b / np.linalg.norm(a) / np.linalg.norm(b))
                assert np.isclose(f(3 * a, b), f(a, b)), "cosine must ignore length"''',
             solution=r'''
            def cosine_solution(a, b):
                return np.sum(a * b) / (np.sqrt(np.sum(a * a)) * np.sqrt(np.sum(b * b)))'''),
        dict(fn='nearest', title='Nearest neighbours by cosine', md=r'''
            Given a query vector and a matrix of embeddings (one row per word), return the indices of the `k` most similar rows, most similar first.
            Do it **vectorised**: normalise every row once, then one matrix-vector product gives all cosines at once. This is exactly how embedding search works.''',
             starter=r'''
            def nearest(query, E, k=2):
                # TODO: normalise rows of E and the query, compute all cosines with one matmul, return top-k indices
                raise NotImplementedError''',
             test=r'''
            def _test_nearest(f):
                idx = list(f(EMB[0], EMB, k=2))
                assert idx[0] == 0, "the closest vector to 'king' is 'king' itself"
                assert WORDS[idx[1]] in ('queen', 'man'), f"second nearest to king should be queen or man, got {WORDS[idx[1]]}"
                target = EMB[0] - EMB[2] + EMB[3]                    # king - man + woman
                best = [WORDS[i] for i in f(target, EMB, k=3)]
                assert best[0] == 'queen', f"king - man + woman should land nearest to queen, got {best}"
                assert WORDS[list(f(EMB[4], EMB, 2))[1]] == "banana"''',
             solution=r'''
            def nearest_solution(query, E, k=2):
                En = E / np.linalg.norm(E, axis=1, keepdims=True)
                sims = En @ (query / np.linalg.norm(query))
                return np.argsort(-sims)[:k]'''),
        dict(fn='dot_std', title='Why attention divides by √d', md=r'''
            Draw `n` pairs of random vectors with independent entries of mean 0 and variance 1 in dimension `d`, and return the **standard deviation of their dot products**.
            The Transformer paper notes that such a dot product has variance $d$, so its spread grows like $\sqrt{d}$. Dividing scores by $\sqrt{d}$ keeps the softmax out of its flat, saturated regions.''',
             starter=r'''
            def dot_std(d, n=20000, seed=0):
                r = np.random.default_rng(seed)
                # TODO: n pairs of d-dim standard-normal vectors; std of their dot products
                raise NotImplementedError''',
             test=r'''
            def _test_dot_std(f):
                for d in [4, 64, 256]:
                    s = f(d)
                    assert abs(s / np.sqrt(d) - 1) < 0.05, f"d={d}: expected std ≈ √d = {np.sqrt(d):.1f}, got {s:.2f}"''',
             solution=r'''
            def dot_std_solution(d, n=20000, seed=0):
                r = np.random.default_rng(seed)
                a, b = r.normal(size=(n, d)), r.normal(size=(n, d))
                return np.sum(a * b, axis=1).std()'''),
    ],
    explore_md=r'''
        **Random vectors in high dimension are nearly orthogonal.** The cosine of two random directions concentrates around 0 with spread ≈ 1/√d, which is why a few thousand dimensions can hold many nearly independent "features".''',
    explore=r'''
        r = np.random.default_rng(1)
        for d in [2, 16, 128, 1024, 4096]:
            a, b = r.normal(size=(5000, d)), r.normal(size=(5000, d))
            cos = np.sum(a * b, 1) / np.linalg.norm(a, axis=1) / np.linalg.norm(b, axis=1)
            print(f"d={d:5d}: std of cos = {cos.std():.3f}   (1/√d = {1 / np.sqrt(d):.3f})")''',
    takeaways=r'''
        * The dot product measures alignment scaled by length; cosine similarity removes the length.
        * Embedding search is one normalised matrix-vector product followed by a top-k.
        * Dot products of random d-dimensional vectors have spread √d, hence the 1/√d in scaled dot-product attention.''',
))

# ------------------------------------------------------------------ 02
NBS.append(dict(
    slug='02_svd_low_rank', title='02 · SVD and low-rank approximation', deck='math/03-eigen-svd-low-rank/', deck_name='Eigenvalues, SVD and low rank', minutes=30,
    goals='the truncated SVD, the energy captured by the top singular values, the Eckart–Young error of the best rank-r approximation, and the parameter count of a LoRA update.',
    setup=r'''
rng = np.random.default_rng(0)
def low_rank_plus_noise(m, n, r, noise=0.01, seed=0):
    g = np.random.default_rng(seed)
    return g.normal(size=(m, r)) @ g.normal(size=(r, n)) + noise * g.normal(size=(m, n))
''',
    tasks=[
        dict(fn='rank_r', title='Best rank-r approximation', md=r'''
            Use `np.linalg.svd(W, full_matrices=False)` to get $W = U \Sigma V^\top$, keep the top `r` singular values and vectors, and return the rank-r matrix $U_r \Sigma_r V_r^\top$.
            By the Eckart–Young theorem this is the closest rank-r matrix to W in Frobenius norm.''',
             starter=r'''
            def rank_r(W, r):
                # TODO: truncated SVD reconstruction
                raise NotImplementedError''',
             test=r'''
            def _test_rank_r(f):
                W = low_rank_plus_noise(40, 30, 5)
                A = f(W, 5)
                assert A.shape == W.shape
                assert np.linalg.matrix_rank(A, tol=1e-8) == 5, "result must have rank r"
                s = np.linalg.svd(W, compute_uv=False)
                err = np.linalg.norm(W - A)
                assert np.isclose(err, np.sqrt(np.sum(s[5:] ** 2))), "Eckart–Young: error² = sum of the discarded σ²"
                assert np.allclose(f(W, 30), W), "full rank must reproduce W"''',
             solution=r'''
            def rank_r_solution(W, r):
                U, s, Vt = np.linalg.svd(W, full_matrices=False)
                return (U[:, :r] * s[:r]) @ Vt[:r]'''),
        dict(fn='energy', title='Energy captured by the top r singular values', md=r'''
            Return the fraction $\sum_{i \le r} \sigma_i^2 / \sum_i \sigma_i^2$ for every r = 1 … min(m, n) as an array.
            For matrices with low-rank structure the curve jumps to almost 1 after a few components.''',
             starter=r'''
            def energy(W):
                # TODO: cumulative sum of squared singular values, normalised
                raise NotImplementedError''',
             test=r'''
            def _test_energy(f):
                e = f(low_rank_plus_noise(50, 40, 3))
                assert len(e) == 40 and np.isclose(e[-1], 1)
                assert np.all(np.diff(e) >= -1e-12), "energy must be non-decreasing"
                assert e[2] > 0.99, f"a rank-3 + noise matrix should have >99% energy in 3 components, got {e[2]:.3f}"
                er = f(np.random.default_rng(3).normal(size=(50, 40)))
                assert er[2] < 0.3, "a random matrix spreads energy over many components"''',
             solution=r'''
            def energy_solution(W):
                s2 = np.linalg.svd(W, compute_uv=False) ** 2
                return np.cumsum(s2) / s2.sum()'''),
        dict(fn='lora_params', title='Parameters in a LoRA update', md=r'''
            LoRA replaces a full update $\Delta W \in \mathbb{R}^{d \times k}$ with $BA$, where $B \in \mathbb{R}^{d \times r}$ and $A \in \mathbb{R}^{r \times k}$.
            Return `(full, lora, ratio)`: the parameter counts of $\Delta W$ and of $(B, A)$, and lora / full.''',
             starter=r'''
            def lora_params(d, k, r):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_lora_params(f):
                full, lora, ratio = f(4096, 4096, 8)
                assert full == 4096 * 4096 and lora == 8 * (4096 + 4096)
                assert np.isclose(ratio, 65536 / 16777216)
                assert f(10, 20, 1)[1] == 30''',
             solution=r'''
            def lora_params_solution(d, k, r):
                full, lora = d * k, r * (d + k)
                return full, lora, lora / full'''),
    ],
    explore_md=r'''
        **Compressing a matrix.** Storing the rank-r factors of an m×n matrix costs r(m+n) numbers instead of mn. Watch the error fall as r grows for a matrix with real low-rank structure.''',
    explore=r'''
        W = low_rank_plus_noise(256, 256, 16, noise=0.05, seed=2)
        for r in [1, 4, 8, 16, 32, 64]:
            A = rank_r_solution(W, r)
            print(f"r={r:3d}: relative error {np.linalg.norm(W - A) / np.linalg.norm(W):.4f}   storage {r * 512 / 65536:6.1%} of the full matrix")''',
    takeaways=r'''
        * The SVD writes any matrix as a sum of rank-1 pieces ordered by importance (singular values).
        * Truncating it gives the best rank-r approximation, with squared error equal to the discarded σ².
        * LoRA bets that fine-tuning updates are low rank: r(d+k) parameters instead of d·k.''',
))

# ------------------------------------------------------------------ 03
NBS.append(dict(
    slug='03_chain_rule_gradcheck', title='03 · Chain rule by hand and gradient checking', deck='math/04-derivatives-chain-rule/', deck_name='Derivatives and the chain rule', minutes=30,
    goals='forward and backward passes of a small computational graph by hand, the gradient of a linear layer with a squared loss, and a finite-difference gradient checker.',
    setup='',
    tasks=[
        dict(fn='graph_grads', title='Backward through a tiny graph', md=r'''
            For $f(x, y) = (x \cdot y + \sin x)^2$, compute the value and the gradient by the chain rule, node by node:
            $a = x y$, $b = \sin x$, $c = a + b$, $f = c^2$. Backward: $\partial f/\partial c = 2c$, then $\partial f/\partial x = 2c\,(y + \cos x)$ and $\partial f/\partial y = 2c\,x$.
            Return `(f, dfdx, dfdy)`.''',
             starter=r'''
            def graph_grads(x, y):
                # TODO: forward a, b, c, f; backward dc, then dx (two paths!) and dy
                raise NotImplementedError''',
             test=r'''
            def _test_graph_grads(f):
                v, dx, dy = f(1.0, 2.0)
                c = 2 + np.sin(1)
                assert np.isclose(v, c ** 2)
                assert np.isclose(dx, 2 * c * (2 + np.cos(1))), "x reaches f through two paths (a and b): add both"
                assert np.isclose(dy, 2 * c * 1.0)''',
             solution=r'''
            def graph_grads_solution(x, y):
                a, b = x * y, np.sin(x); c = a + b; f = c ** 2
                dc = 2 * c
                dx = dc * y + dc * np.cos(x)
                dy = dc * x
                return f, dx, dy'''),
        dict(fn='linear_mse_grads', title='Gradients of a linear layer', md=r'''
            For $\hat Y = X W + b$ and $L = \frac{1}{n}\sum (\hat Y - Y)^2$ (mean over all entries), return `(L, dW, db)`.
            Shapes: X is (n, d), W is (d, k), b is (k,). Hint: $\partial L / \partial \hat Y = \frac{2}{nk}(\hat Y - Y)$, then $dW = X^\top \, \partial L/\partial \hat Y$ and $db$ sums over rows.''',
             starter=r'''
            def linear_mse_grads(X, W, b, Y):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_linear_mse_grads(f):
                g = np.random.default_rng(0)
                X, W, b, Y = g.normal(size=(5, 3)), g.normal(size=(3, 2)), g.normal(size=2), g.normal(size=(5, 2))
                L, dW, db = f(X, W, b, Y)
                assert np.isclose(L, np.mean((X @ W + b - Y) ** 2))
                assert dW.shape == W.shape and db.shape == b.shape, "a gradient has the shape of its parameter"
                eps = 1e-6; Wp = W.copy(); Wp[1, 0] += eps
                num = (np.mean((X @ Wp + b - Y) ** 2) - L) / eps
                assert abs(num - dW[1, 0]) < 1e-4, "dW disagrees with a finite difference"''',
             solution=r'''
            def linear_mse_grads_solution(X, W, b, Y):
                Yh = X @ W + b
                L = np.mean((Yh - Y) ** 2)
                dY = 2 * (Yh - Y) / Yh.size
                return L, X.T @ dY, dY.sum(axis=0)'''),
        dict(fn='grad_check', title='A finite-difference gradient checker', md=r'''
            Write `grad_check(f, x, eps)` that returns the numerical gradient of a scalar function `f` at array `x` with **central differences**:
            $\dfrac{f(x + \epsilon e_i) - f(x - \epsilon e_i)}{2\epsilon}$ for each coordinate i. Central differences have error $O(\epsilon^2)$, one-sided $O(\epsilon)$.''',
             starter=r'''
            def grad_check(f, x, eps=1e-5):
                # TODO: loop over coordinates
                raise NotImplementedError''',
             test=r'''
            def _test_grad_check(f):
                x = np.array([0.5, -1.0, 2.0])
                g = f(lambda v: np.sum(v ** 3), x)
                assert np.allclose(g, 3 * x ** 2, atol=1e-6)
                g2 = f(lambda v: np.sin(v[0]) * v[1], np.array([1.0, 2.0]))
                assert np.allclose(g2, [2 * np.cos(1), np.sin(1)], atol=1e-6)''',
             solution=r'''
            def grad_check_solution(f, x, eps=1e-5):
                g = np.zeros_like(x, dtype=float)
                for i in range(x.size):
                    e = np.zeros_like(x, dtype=float); e.flat[i] = eps
                    g.flat[i] = (f(x + e) - f(x - e)) / (2 * eps)
                return g'''),
    ],
    explore_md=r'''
        **Choosing ε.** Too large and the approximation error dominates; too small and floating-point cancellation does. Central differences are best around ε ≈ 10⁻⁵ in float64.''',
    explore=r'''
        f, x, true = np.sin, 1.0, np.cos(1.0)
        for eps in [1e-1, 1e-3, 1e-5, 1e-8, 1e-11]:
            one = (f(x + eps) - f(x)) / eps; two = (f(x + eps) - f(x - eps)) / (2 * eps)
            print(f"eps={eps:.0e}: one-sided error {abs(one - true):.1e}   central error {abs(two - true):.1e}")''',
    takeaways=r'''
        * The chain rule multiplies local derivatives along each path and adds over paths.
        * A gradient always has the shape of the thing it differentiates; dW = Xᵀ·dŶ for a linear layer.
        * Check hand-written gradients against central finite differences before trusting them.''',
))

# ------------------------------------------------------------------ 04
NBS.append(dict(
    slug='04_cross_entropy_kl', title='04 · Entropy, cross-entropy, KL and perplexity', deck='math/07-information-theory/', deck_name='Information theory for LLMs', minutes=25,
    goals='entropy, cross-entropy and KL divergence from scratch, the identity H(p, q) = H(p) + KL(p‖q), and perplexity of a language model from its per-token probabilities.',
    setup='',
    tasks=[
        dict(fn='entropy', title='Entropy in nats and bits', md=r'''
            $H(p) = -\sum_i p_i \log p_i$, with the convention $0 \log 0 = 0$. Return `(nats, bits)`; bits use $\log_2$.''',
             starter=r'''
            def entropy(p):
                p = np.asarray(p, float)
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_entropy(f):
                assert np.isclose(f([0.5, 0.5])[1], 1), "a fair coin is 1 bit"
                assert np.isclose(f([1, 0, 0])[0], 0), "a certain outcome has zero entropy (watch 0·log 0)"
                assert np.isclose(f(np.ones(8) / 8)[1], 3), "uniform over 8 is 3 bits"
                n, b = f([0.7, 0.2, 0.1]); assert np.isclose(n, b * np.log(2))''',
             solution=r'''
            def entropy_solution(p):
                p = np.asarray(p, float); nz = p[p > 0]
                nats = -np.sum(nz * np.log(nz))
                return nats, nats / np.log(2)'''),
        dict(fn='cross_entropy_kl', title='Cross-entropy and KL divergence', md=r'''
            Return `(H_pq, KL_pq)` with $H(p, q) = -\sum p_i \log q_i$ and $\mathrm{KL}(p \Vert q) = \sum p_i \log (p_i / q_i)$, in nats.
            Training a language model minimises cross-entropy against the data distribution p; since H(p) is fixed, that is the same as minimising KL(p‖q).''',
             starter=r'''
            def cross_entropy_kl(p, q):
                p, q = np.asarray(p, float), np.asarray(q, float)
                # TODO (terms with p_i = 0 contribute 0)
                raise NotImplementedError''',
             test=r'''
            def _test_cross_entropy_kl(f):
                p, q = np.array([0.7, 0.2, 0.1]), np.array([0.5, 0.3, 0.2])
                H, KL = f(p, q)
                Hp = -np.sum(p * np.log(p))
                assert np.isclose(H, Hp + KL), "H(p,q) = H(p) + KL(p||q)"
                assert KL > 0 and np.isclose(f(p, p)[1], 0), "KL ≥ 0, with equality iff q = p"
                assert not np.isclose(f(p, q)[1], f(q, p)[1]), "KL is not symmetric"
                assert np.isclose(f([1, 0], [0.5, 0.5])[0], np.log(2))''',
             solution=r'''
            def cross_entropy_kl_solution(p, q):
                p, q = np.asarray(p, float), np.asarray(q, float); m = p > 0
                return -np.sum(p[m] * np.log(q[m])), np.sum(p[m] * np.log(p[m] / q[m]))'''),
        dict(fn='perplexity', title='Perplexity from token probabilities', md=r'''
            Given the probabilities a model assigned to each **actual** next token in a text, return `(loss, ppl)`: the mean negative log-likelihood in nats and the perplexity $e^{\text{loss}}$.
            Perplexity is the size of a uniform choice that would be equally surprising.''',
             starter=r'''
            def perplexity(token_probs):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_perplexity(f):
                loss, ppl = f([0.25] * 10)
                assert np.isclose(ppl, 4), "always giving the right token probability 1/4 = perplexity 4"
                assert np.isclose(f([1 / 50257] * 3)[0], np.log(50257)), "uniform over GPT-2's 50,257 tokens = ln 50257 nats"
                l, p = f([0.9, 0.5, 0.01]); assert np.isclose(p, np.exp(l))''',
             solution=r'''
            def perplexity_solution(token_probs):
                loss = -np.mean(np.log(np.asarray(token_probs, float)))
                return loss, np.exp(loss)'''),
    ],
    explore_md=r'''
        **Forward vs reverse KL.** Fit a single Gaussian-like bump q to a two-peaked p over a grid. Minimising KL(p‖q) spreads q to cover both peaks; minimising KL(q‖p) locks onto one. Which one does maximum likelihood use?''',
    explore=r'''
        x = np.linspace(-6, 6, 241)
        p = np.exp(-(x + 2.5) ** 2 / 0.5) + np.exp(-(x - 2.5) ** 2 / 0.5); p /= p.sum()
        best = {}
        for mu in np.linspace(-4, 4, 81):
            for s in [0.5, 1, 2, 3]:
                q = np.exp(-(x - mu) ** 2 / (2 * s * s)); q /= q.sum(); q = np.maximum(q, 1e-300)
                fwd, rev = np.sum(p * np.log(p / q + 1e-300)), np.sum(q * np.log(q / np.maximum(p, 1e-300)))
                for k, v in (('forward KL(p||q)', fwd), ('reverse KL(q||p)', rev)):
                    if k not in best or v < best[k][0]: best[k] = (v, mu, s)
        for k, (v, mu, s) in best.items(): print(f"{k}: best q has mean {mu:+.1f}, width {s}")''',
    takeaways=r'''
        * Entropy is average surprise; cross-entropy is surprise under the wrong model; KL is the gap between them.
        * LM training loss is cross-entropy in nats per token; perplexity = e^loss.
        * Maximum likelihood minimises forward KL(p‖q), which is mass-covering.''',
))

# ------------------------------------------------------------------ 05
NBS.append(dict(
    slug='05_stable_softmax', title='05 · Stable softmax, log-sum-exp and online softmax', deck='math/08-softmax-logsumexp/', deck_name='Softmax and log-sum-exp', minutes=30,
    goals='why the naive softmax overflows, the max-subtraction fix, a stable log-sum-exp and log-softmax, and the one-pass online softmax that FlashAttention builds on.',
    setup='',
    tasks=[
        dict(fn='softmax_stable', title='Softmax that never overflows', md=r'''
            Naively, `np.exp(x) / np.exp(x).sum()` overflows in float32 once a logit exceeds about 88.7. Subtracting the maximum first changes nothing mathematically (the factor $e^{-m}$ cancels) but keeps every exponent ≤ 0.
            Implement it for 1-D float32 input and return float32.''',
             starter=r'''
            def softmax_stable(x):
                x = np.asarray(x, np.float32)
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_softmax_stable(f):
                x = np.array([1000., 1001., 1002.], np.float32)
                with np.errstate(over='ignore', invalid='ignore'):
                    naive = np.exp(x) / np.exp(x).sum()
                assert np.isnan(naive).all(), "(sanity: the naive version breaks here)"
                y = f(x)
                assert np.all(np.isfinite(y)) and np.isclose(y.sum(), 1)
                assert np.allclose(y, f(x - 1000)), "softmax is shift-invariant"''',
             solution=r'''
            def softmax_stable_solution(x):
                x = np.asarray(x, np.float32)
                e = np.exp(x - x.max())
                return e / e.sum()'''),
        dict(fn='log_softmax', title='Log-sum-exp and log-softmax', md=r'''
            $\mathrm{LSE}(x) = \log \sum_i e^{x_i} = m + \log \sum_i e^{x_i - m}$ with $m = \max x$. Then $\log \mathrm{softmax}(x)_i = x_i - \mathrm{LSE}(x)$.
            Cross-entropy losses use log-softmax directly, never `log(softmax(x))`, which turns tiny probabilities into `log(0) = -inf`.''',
             starter=r'''
            def log_softmax(x):
                x = np.asarray(x, float)
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_log_softmax(f):
                x = np.array([0., 800., 1.])
                y = f(x)
                assert np.all(np.isfinite(y)), "must stay finite even when a probability underflows"
                assert np.isclose(y[0], -800), "log p(0) = 0 - LSE ≈ -800"
                z = np.random.default_rng(0).normal(size=6)
                assert np.allclose(np.exp(f(z)), np.exp(z) / np.exp(z).sum())''',
             solution=r'''
            def log_softmax_solution(x):
                x = np.asarray(x, float); m = x.max()
                return x - (m + np.log(np.sum(np.exp(x - m))))'''),
        dict(fn='online_softmax', title='Online softmax in one pass over blocks', md=r'''
            Read the logits block by block, keeping only a running max `m` and running sum `d` of $e^{x - m}$. When a block raises the max to `m'`, rescale the old sum by $e^{m - m'}$ (Milakov & Gimelshein, 2018).
            Return `(m, d)` after all blocks; the softmax is then $e^{x - m}/d$ and $\mathrm{LSE} = m + \log d$.''',
             starter=r'''
            def online_softmax(x, block=4):
                m, d = -np.inf, 0.0
                # TODO: for each block: new max, rescale d, add the block's terms
                raise NotImplementedError''',
             test=r'''
            def _test_online_softmax(f):
                x = np.random.default_rng(1).normal(size=37) * 5
                for b in [1, 4, 10, 37]:
                    m, d = f(x, b)
                    assert np.isclose(m, x.max()), "m must end as the global max"
                    assert np.isclose(m + np.log(d), np.log(np.sum(np.exp(x)))), f"block={b}: LSE mismatch"''',
             solution=r'''
            def online_softmax_solution(x, block=4):
                m, d = -np.inf, 0.0
                for i in range(0, len(x), block):
                    blk = x[i:i + block]; m2 = max(m, blk.max())
                    d = d * np.exp(m - m2) + np.sum(np.exp(blk - m2)); m = m2
                return m, d'''),
    ],
    explore_md=r'''
        **Where formats overflow.** `exp(x)` overflows FP16 (max 65,504) once x > ln 65504 ≈ 11.09, and FP32 once x > ≈ 88.72. Attention logits easily exceed 11, which is one reason softmax runs with max subtraction and in higher precision.''',
    explore=r'''
        for dt in [np.float16, np.float32]:
            lim = np.log(np.finfo(dt).max)
            with np.errstate(over='ignore'):
                print(f"{dt.__name__}: max {float(np.finfo(dt).max):.4g}, exp overflows above x ≈ {lim:.2f}; exp({lim + 0.1:.2f}) = {np.exp(dt(lim + 0.1))}")''',
    takeaways=r'''
        * Subtract the max before exponentiating: same softmax, no overflow.
        * Use log-sum-exp / log-softmax for losses instead of log(softmax).
        * The online softmax keeps a running max and rescaled sum, so softmax can be computed block by block, the basis of FlashAttention.''',
))

# ------------------------------------------------------------------ 06
NBS.append(dict(
    slug='06_gradient_descent', title='06 · Gradient descent, momentum and Adam', deck='math/09-optimization-basics/', deck_name='Optimization basics', minutes=30,
    goals='gradient descent on an ill-conditioned quadratic, the 2/λ_max stability limit, momentum, and Adam from its update equations.',
    setup=r'''
def make_quadratic(kappa):
    """f(x) = 0.5 * x^T diag(1, kappa) x  -> curvatures 1 and kappa."""
    H = np.diag([1.0, kappa])
    return (lambda x: 0.5 * x @ H @ x), (lambda x: H @ x)
X0 = np.array([1.0, 1.0])
''',
    tasks=[
        dict(fn='gd', title='Plain gradient descent', md=r'''
            Run $x \leftarrow x - \eta \nabla f(x)$ for `steps` steps from `x0` and return the array of losses (length steps + 1, including the start).
            On a quadratic, GD converges only if $\eta < 2/\lambda_{\max}$; the slowest direction then shrinks by $|1 - \eta\lambda_{\min}|$ per step.''',
             starter=r'''
            def gd(f, grad, x0, lr, steps):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_gd(f):
                fn, g = make_quadratic(100)
                ok = f(fn, g, X0, 0.019, 300); bad = f(fn, g, X0, 0.021, 300)
                assert len(ok) == 301
                assert ok[-1] < 1e-2 * ok[0], "lr below 2/λmax = 0.02 must converge"
                assert bad[-1] > bad[0], "lr above 2/λmax = 0.02 must diverge"''',
             solution=r'''
            def gd_solution(f, grad, x0, lr, steps):
                x = x0.astype(float).copy(); out = [f(x)]
                for _ in range(steps):
                    x = x - lr * grad(x); out.append(f(x))
                return np.array(out)'''),
        dict(fn='momentum', title='Heavy-ball momentum', md=r'''
            Keep a velocity: $v \leftarrow \beta v + \nabla f(x)$, $x \leftarrow x - \eta v$. Return losses as before.
            Momentum averages away the zig-zag across the steep direction and accelerates along the shallow one.''',
             starter=r'''
            def momentum(f, grad, x0, lr, beta, steps):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_momentum(f):
                fn, g = make_quadratic(100)
                plain = gd_solution(fn, g, X0, 0.019, 200) if 'gd_solution' in globals() else None
                m = f(fn, g, X0, 0.019, 0.8, 200)
                assert len(m) == 201
                assert m[-1] < 1e-6, f"momentum should reach < 1e-6 in 200 steps, got {m[-1]:.2e}"
                assert plain is None or m[-1] < plain[-1], "momentum should beat plain GD here"''',
             solution=r'''
            def momentum_solution(f, grad, x0, lr, beta, steps):
                x = x0.astype(float).copy(); v = np.zeros_like(x); out = [f(x)]
                for _ in range(steps):
                    v = beta * v + grad(x); x = x - lr * v; out.append(f(x))
                return np.array(out)'''),
        dict(fn='adam', title='Adam', md=r'''
            Kingma & Ba (2014): $m \leftarrow \beta_1 m + (1-\beta_1) g$, $v \leftarrow \beta_2 v + (1-\beta_2) g^2$, bias-correct $\hat m = m/(1-\beta_1^t)$, $\hat v = v/(1-\beta_2^t)$, then $x \leftarrow x - \eta\, \hat m / (\sqrt{\hat v} + \epsilon)$.
            Defaults from the paper: β₁ = 0.9, β₂ = 0.999, ε = 10⁻⁸. Return the losses.''',
             starter=r'''
            def adam(f, grad, x0, lr, steps, b1=0.9, b2=0.999, eps=1e-8):
                # TODO (t starts at 1)
                raise NotImplementedError''',
             test=r'''
            def _test_adam(f):
                fn, g = make_quadratic(100)
                a = f(fn, g, X0, 0.05, 400)
                assert len(a) == 401 and a[-1] < 1e-3 * a[0], f"Adam should converge, got {a[-1]:.2e}"
                fn2, g2 = make_quadratic(1e4)
                a2 = f(fn2, g2, X0, 0.05, 400)
                assert a2[-1] < 1e-3 * a2[0], "Adam's per-coordinate scaling makes it robust to κ = 10^4 at the same lr"''',
             solution=r'''
            def adam_solution(f, grad, x0, lr, steps, b1=0.9, b2=0.999, eps=1e-8):
                x = x0.astype(float).copy(); m = np.zeros_like(x); v = np.zeros_like(x); out = [f(x)]
                for t in range(1, steps + 1):
                    gr = grad(x); m = b1 * m + (1 - b1) * gr; v = b2 * v + (1 - b2) * gr * gr
                    x = x - lr * (m / (1 - b1 ** t)) / (np.sqrt(v / (1 - b2 ** t)) + eps); out.append(f(x))
                return np.array(out)'''),
    ],
    explore_md=r'''
        **Condition number vs steps.** With the best fixed learning rate, plain GD needs roughly κ·ln(1/ε)/2 steps; momentum needs roughly √κ times fewer. Count steps to reach 10⁻⁶ of the start.''',
    explore=r'''
        for kappa in [10, 100, 1000]:
            fn, g = make_quadratic(kappa); lr = 2 / (1 + kappa)
            def steps_to(losses): return int(np.argmax(losses < 1e-6 * losses[0])) if (losses < 1e-6 * losses[0]).any() else None
            b = ((np.sqrt(kappa) - 1) / (np.sqrt(kappa) + 1)) ** 2; lr_m = (2 / (1 + np.sqrt(kappa))) ** 2
            print(f"kappa={kappa:5d}: GD {steps_to(gd_solution(fn, g, X0, lr, 20000))} steps, momentum {steps_to(momentum_solution(fn, g, X0, lr_m, b, 20000))} steps")''',
    takeaways=r'''
        * GD is stable only for η < 2/λmax, and the smallest curvature then sets the speed: ill-conditioning (large κ) makes it slow.
        * Momentum cuts the dependence on κ to about √κ.
        * Adam rescales each coordinate by its gradient RMS, making it far less sensitive to curvature differences.''',
))
