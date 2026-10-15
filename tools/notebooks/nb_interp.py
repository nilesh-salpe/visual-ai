"""Interpretability exercise notebook: superposition and a sparse autoencoder on a toy model, in NumPy."""

NBS = []

TRAIN = r'''
def make_features(m, d, seed=225):
    """m true feature directions (unit vectors) in a d-dimensional activation space."""
    F = np.random.default_rng(seed).normal(size=(m, d))
    return F / np.linalg.norm(F, axis=1, keepdims=True)

def make_data(F, n, p=0.1, seed=1):
    """Activations x = sum of active features: each feature is on with probability p, with a random strength."""
    rng = np.random.default_rng(seed)
    s = (rng.random((n, len(F))) < p) * rng.random((n, len(F)))
    return s @ F, s

def train_sae(X, h, l1=0.1, steps=4000, lr=3e-3, seed=2):
    """A ReLU sparse autoencoder trained with Adam: f = relu(W_enc (x - b_dec) + b_enc), x_hat = W_dec f + b_dec,
    loss = squared error + l1 * |f|_1, decoder columns kept at unit norm."""
    rng = np.random.default_rng(seed); n, d = X.shape
    Wd = rng.normal(size=(d, h)); Wd /= np.linalg.norm(Wd, axis=0); We = Wd.T.copy(); be = np.zeros(h); bd = X.mean(0)
    P = [We, be, Wd, bd]; m = [np.zeros_like(p) for p in P]; v = [np.zeros_like(p) for p in P]
    for t in range(1, steps + 1):
        x = X[rng.integers(0, n, 256)]
        pre = (x - bd) @ We.T + be; f = np.maximum(pre, 0); r = f @ Wd.T + bd - x
        g_xh = 2 * r / len(x)
        g_pre = (g_xh @ Wd + l1 * np.sign(f) / len(x)) * (pre > 0)
        G = [g_pre.T @ (x - bd), g_pre.sum(0), g_xh.T @ f, g_xh.sum(0) - (g_pre @ We).sum(0)]
        for i, (p, g) in enumerate(zip(P, G)):
            m[i] = 0.9 * m[i] + 0.1 * g; v[i] = 0.999 * v[i] + 0.001 * g * g
            p -= lr * (m[i] / (1 - 0.9 ** t)) / (np.sqrt(v[i] / (1 - 0.999 ** t)) + 1e-8)
        Wd /= np.linalg.norm(Wd, axis=0, keepdims=True)
    return We, be, Wd, bd
'''

NBS.append(dict(
    slug='01_superposition_and_sae', title='01 · Superposition and sparse autoencoders on a toy model', deck='interpretability/02-sparse-autoencoders/', deck_name='Sparse autoencoders', minutes=35,
    goals='a measure of interference between features packed into too few dimensions, the forward pass and loss of a sparse autoencoder, and a feature-recovery score, then train an SAE that recovers 8 hidden features from 4-dimensional activations where PCA cannot.',
    setup=TRAIN,
    tasks=[
        dict(fn='interference', title='Interference between features', md=r'''
            `F` holds one unit-length feature direction per row. If there are more features than dimensions they cannot all be orthogonal: return the **largest absolute cosine similarity between two different features** (0 means no interference).''',
             starter=r'''
            def interference(F):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_interference(f):
                assert f(np.eye(4)) < 1e-12, "orthonormal features do not interfere"
                assert f(make_features(8, 4)) > 0.3, "8 directions in 4 dimensions must overlap"
                G = np.array([[1.0, 0.0], [np.sqrt(0.5), np.sqrt(0.5)]])
                assert abs(f(G) - np.sqrt(0.5)) < 1e-9''',
             solution=r'''
            def interference_solution(F):
                C = np.abs(F @ F.T)
                np.fill_diagonal(C, 0)
                return float(C.max())'''),
        dict(fn='sae_forward', title='Sparse autoencoder forward pass', md=r'''
            For activations `x` of shape (n, d): `f = relu((x − b_dec) @ W_enc.T + b_enc)` (shape n × h), `x_hat = f @ W_dec.T + b_dec`, and
            `loss = mean over rows of Σ (x − x_hat)² + l1 × mean over rows of Σ |f|`. Return `(f, x_hat, loss)`.''',
             starter=r'''
            def sae_forward(x, W_enc, b_enc, W_dec, b_dec, l1):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_sae_forward(f):
                x = np.array([[1.0, 2.0]]); We = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]]); be = np.zeros(3); Wd = We.T.copy(); bd = np.zeros(2)
                feats, xh, loss = f(x, We, be, Wd, bd, 0.5)
                assert np.allclose(feats, [[1.0, 2.0, 0.0]]), "ReLU zeroes the negative latent"
                assert np.allclose(xh, x) and abs(loss - 0.5 * 3.0) < 1e-12, "perfect reconstruction, so the loss is just l1 × |f|₁ = 0.5 × 3"''',
             solution=r'''
            def sae_forward_solution(x, W_enc, b_enc, W_dec, b_dec, l1):
                f = np.maximum((x - b_dec) @ W_enc.T + b_enc, 0)
                x_hat = f @ W_dec.T + b_dec
                loss = ((x - x_hat) ** 2).sum(1).mean() + l1 * np.abs(f).sum(1).mean()
                return f, x_hat, float(loss)'''),
        dict(fn='feature_recovery', title='Did we find the features?', md=r'''
            `F` has the true features as rows (m × d); `W_dec` has one learned direction per **column** (d × h). For each true feature, take the **largest absolute cosine similarity** with any decoder column; return the mean over features (1.0 = every feature found exactly).''',
             starter=r'''
            def feature_recovery(W_dec, F):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_feature_recovery(f):
                F = make_features(8, 4)
                assert abs(f(F.T, F) - 1.0) < 1e-9, "a decoder containing every feature recovers all of them"
                assert abs(f(-F.T, F) - 1.0) < 1e-9, "sign does not matter"
                assert f(np.eye(4)[:, :1], F) < 0.9, "one direction cannot match eight features"''',
             solution=r'''
            def feature_recovery_solution(W_dec, F):
                D = W_dec / np.linalg.norm(W_dec, axis=0, keepdims=True)
                return float(np.abs(F @ D).max(1).mean())'''),
    ],
    explore_md='Eight sparse features squeezed into four dimensions (superposition). PCA can find at most four directions; a 16-latent SAE can find all eight. Then the sparsity trade-off: larger L1 means fewer active latents but worse reconstruction.',
    explore=r'''
F = make_features(8, 4); X, S = make_data(F, 20000)
print(f"interference between the 8 true features: {interference_solution(F):.2f}")
U, s, Vt = np.linalg.svd(X - X.mean(0), full_matrices=False)
print(f"PCA (4 directions) feature recovery: {feature_recovery_solution(Vt.T, F):.2f}")
for l1 in [0.1, 0.2, 0.4]:
    We, be, Wd, bd = train_sae(X, 16, l1=l1)
    f, xh, _ = sae_forward_solution(X, We, be, Wd, bd, l1)
    print(f"SAE l1={l1}: recovery {feature_recovery_solution(Wd, F):.2f}, active latents per input {(f > 1e-6).sum(1).mean():.2f}, reconstruction error {((X - xh) ** 2).sum(1).mean():.4f}")
print(f"(true active features per input: {(S > 0).sum(1).mean():.2f})")''',
    takeaways='''
        * When features are sparse, a network can store **more features than dimensions** in superposition, at the cost of interference.
        * A **sparse autoencoder** learns an overcomplete dictionary whose latents are sparse, recovering feature directions that individual neurons or PCA mix together.
        * The L1 coefficient trades reconstruction against sparsity; real SAEs are judged on both, plus how interpretable and causally useful their features are.''',
))
