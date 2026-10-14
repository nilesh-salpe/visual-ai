"""Neural network fundamentals exercise notebooks (NumPy only)."""

NBS = []

# ------------------------------------------------------------------ 01
NBS.append(dict(
    slug='01_micrograd', title='01 · Build an autograd engine (micrograd-style)', deck='nn-fundamentals/03-backpropagation/', deck_name='Backpropagation', minutes=40,
    goals='a scalar `Value` class that records the computational graph, local backward rules for +, ×, tanh and powers, and a topological-order backward pass that matches finite differences.',
    setup=r'''
import math

class Value:
    """A scalar that remembers how it was computed."""
    def __init__(self, data, parents=(), op=''):
        self.data, self.grad = float(data), 0.0
        self._parents, self._op = parents, op
        self._backward = lambda: None
    def __repr__(self):
        return f"Value(data={self.data:.4f}, grad={self.grad:.4f})"
''',
    tasks=[
        dict(fn='add_mul', title='Addition and multiplication with backward rules', md=r'''
            Write `add(a, b)` and `mul(a, b)` that return a new `Value` whose `_backward` adds the right local gradient into its parents:
            for $c = a + b$: $\partial c/\partial a = \partial c/\partial b = 1$; for $c = a \cdot b$: $\partial c/\partial a = b$, $\partial c/\partial b = a$.
            Always use `+=`: a value used twice must collect gradient from both uses.''',
             starter=r'''
            def add(a, b):
                out = Value(a.data + b.data, (a, b), '+')
                def _backward():
                    # TODO: a.grad += ... ; b.grad += ...
                    raise NotImplementedError
                out._backward = _backward
                return out

            def mul(a, b):
                # TODO
                raise NotImplementedError

            def add_mul(a, b):
                return add, mul''',
             test=r'''
            def _test_add_mul(f):
                add_, mul_ = f(None, None)
                a, b = Value(2.0), Value(-3.0)
                c = mul_(a, b); c.grad = 1.0; c._backward()
                assert c.data == -6 and a.grad == -3 and b.grad == 2, "d(ab)/da = b, d(ab)/db = a"
                x = Value(5.0); y = add_(x, x); y.grad = 1.0; y._backward()
                assert x.grad == 2, "x used twice must receive gradient twice (use +=)"''',
             solution=r'''
            def add_solution_(a, b):
                out = Value(a.data + b.data, (a, b), '+')
                def _backward():
                    a.grad += out.grad; b.grad += out.grad
                out._backward = _backward
                return out

            def mul_solution_(a, b):
                out = Value(a.data * b.data, (a, b), '*')
                def _backward():
                    a.grad += b.data * out.grad; b.grad += a.data * out.grad
                out._backward = _backward
                return out

            def add_mul_solution(a, b):
                return add_solution_, mul_solution_'''),
        dict(fn='tanh_pow', title='tanh and powers', md=r'''
            Add `tanh(a)` with $\frac{d}{da}\tanh a = 1 - \tanh^2 a$, and `pow_(a, k)` for a constant exponent k with $\frac{d}{da} a^k = k a^{k-1}$.''',
             starter=r'''
            def tanh(a):
                # TODO
                raise NotImplementedError

            def pow_(a, k):
                # TODO
                raise NotImplementedError

            def tanh_pow(a=None):
                return tanh, pow_''',
             test=r'''
            def _test_tanh_pow(f):
                tanh_, pow__ = f()
                a = Value(0.5); t = tanh_(a); t.grad = 1.0; t._backward()
                assert np.isclose(t.data, np.tanh(0.5)) and np.isclose(a.grad, 1 - np.tanh(0.5) ** 2)
                b = Value(3.0); p = pow__(b, 2); p.grad = 1.0; p._backward()
                assert p.data == 9 and b.grad == 6''',
             solution=r'''
            def tanh_solution_(a):
                t = math.tanh(a.data); out = Value(t, (a,), 'tanh')
                def _backward():
                    a.grad += (1 - t * t) * out.grad
                out._backward = _backward
                return out

            def pow_solution_(a, k):
                out = Value(a.data ** k, (a,), f'**{k}')
                def _backward():
                    a.grad += k * a.data ** (k - 1) * out.grad
                out._backward = _backward
                return out

            def tanh_pow_solution(a=None):
                return tanh_solution_, pow_solution_'''),
        dict(fn='backward', title='Backward in topological order', md=r'''
            `backward(root)` must (1) build a topological order of all nodes reachable from `root` (each node after all its parents), (2) set `root.grad = 1`, and (3) call `_backward()` on nodes in **reverse** topological order, so every node's gradient is complete before it is pushed to its parents.''',
             starter=r'''
            def backward(root):
                order, seen = [], set()
                # TODO: depth-first search over _parents to fill `order`, then reverse pass
                raise NotImplementedError''',
             test=r'''
            def _test_backward(f):
                def _op(data, parents, rule):
                    out = Value(data, parents)
                    def bw():
                        for p, g in zip(parents, rule(out)): p.grad += g * out.grad
                    out._backward = bw; return out
                A = lambda a, b: _op(a.data + b.data, (a, b), lambda o: (1, 1))
                M = lambda a, b: _op(a.data * b.data, (a, b), lambda o: (b.data, a.data))
                T = lambda a: _op(math.tanh(a.data), (a,), lambda o: (1 - o.data ** 2,))
                P = lambda a, k: _op(a.data ** k, (a,), lambda o: (k * a.data ** (k - 1),))
                # a neuron: tanh(w1*x1 + w2*x2 + b), and a squared error
                x1, x2, w1, w2, b = Value(2.0), Value(0.0), Value(-3.0), Value(1.0), Value(6.8813735870195432)
                out = T(A(A(M(x1, w1), M(x2, w2)), b)); loss = P(A(out, Value(-1.0)), 2)
                f(loss)
                def L(w1v):
                    return (math.tanh(2 * w1v + 0 + 6.8813735870195432) - 1) ** 2
                num = (L(-3 + 1e-6) - L(-3 - 1e-6)) / 2e-6
                assert abs(w1.grad - num) < 1e-5, f"dloss/dw1 = {w1.grad}, finite difference {num}"
                y = Value(3.0); z = M(y, y); f(z)
                assert y.grad == 6, "y*y: both uses contribute"''',
             solution=r'''
            def backward_solution(root):
                order, seen = [], set()
                def visit(v):
                    if id(v) in seen: return
                    seen.add(id(v))
                    for p in v._parents: visit(p)
                    order.append(v)
                visit(root)
                root.grad = 1.0
                for v in reversed(order): v._backward()'''),
    ],
    explore_md=r'''
        **Train one neuron.** Use your engine to fit tanh(w·x + b) to a few points by gradient descent: zero the grads, forward, backward, step.''',
    explore=r'''
        A, M = add_mul_solution(None, None); T, P = tanh_pow_solution()
        xs, ys = [-2.0, -1.0, 1.0, 2.0], [-0.9, -0.6, 0.6, 0.9]
        w, b = Value(0.1), Value(0.0)
        for step in range(201):
            loss = Value(0.0)
            for x, y in zip(xs, ys):
                loss = A(loss, P(A(T(A(M(w, Value(x)), b)), Value(-y)), 2))
            w.grad = b.grad = 0.0
            backward_solution(loss)
            w.data -= 0.1 * w.grad; b.data -= 0.1 * b.grad
            if step % 50 == 0: print(f"step {step:3d}: loss {loss.data:.4f}  w={w.data:.3f} b={b.data:.3f}")''',
    takeaways=r'''
        * Autograd = record each operation with its inputs, then apply local derivative rules in reverse topological order.
        * Gradients must accumulate (+=) because values can be used more than once.
        * PyTorch's autograd does exactly this, on tensors instead of scalars.''',
))

# ------------------------------------------------------------------ 02
NBS.append(dict(
    slug='02_mlp_numpy', title='02 · An MLP from scratch: solving XOR', deck='nn-fundamentals/01-perceptron-to-mlp/', deck_name='From perceptron to MLP', minutes=35,
    goals='why a linear model cannot fit XOR, a two-layer MLP with a hidden nonlinearity, its hand-written backward pass, and training it to 100% accuracy.',
    setup=r'''
X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], float)
Y = np.array([0, 1, 1, 0], float)        # XOR
def sigmoid(z): return 1 / (1 + np.exp(-z))
''',
    tasks=[
        dict(fn='best_linear_accuracy', title='A linear model cannot do XOR', md=r'''
            Try many random linear classifiers $\hat y = 1[w \cdot x + b > 0]$ (say 20,000 draws of w and b from a standard normal) and return the **best accuracy** any of them gets on XOR.
            No line separates {(0,1), (1,0)} from {(0,0), (1,1)}, so the best is 3/4.''',
             starter=r'''
            def best_linear_accuracy(n=20000, seed=0):
                r = np.random.default_rng(seed)
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_best_linear_accuracy(f):
                acc = f()
                assert np.isclose(acc, 0.75), f"best linear accuracy on XOR should be 0.75, got {acc}"''',
             solution=r'''
            def best_linear_accuracy_solution(n=20000, seed=0):
                r = np.random.default_rng(seed)
                W, B = r.normal(size=(n, 2)), r.normal(size=n)
                pred = (X @ W.T + B) > 0
                return ((pred == Y[:, None]).mean(axis=0)).max()'''),
        dict(fn='mlp_forward_backward', title='Forward and backward of a 2-layer MLP', md=r'''
            Model: $h = \tanh(X W_1 + b_1)$, $p = \sigma(h W_2 + b_2)$, binary cross-entropy $L = -\frac{1}{n}\sum [y\log p + (1-y)\log(1-p)]$.
            Return `(L, grads)` with `grads = dict(W1=..., b1=..., W2=..., b2=...)`. Useful facts: $\partial L/\partial z_2 = (p - y)/n$ for the output pre-activation; $\tanh' = 1 - h^2$.''',
             starter=r'''
            def mlp_forward_backward(params, X, Y):
                W1, b1, W2, b2 = params['W1'], params['b1'], params['W2'], params['b2']
                # TODO: forward, loss, backward
                raise NotImplementedError''',
             test=r'''
            def _test_mlp_forward_backward(f):
                r = np.random.default_rng(1)
                P = dict(W1=r.normal(size=(2, 4)), b1=r.normal(size=4), W2=r.normal(size=(4, 1)), b2=r.normal(size=1))
                L, g = f(P, X, Y)
                assert set(g) == {'W1', 'b1', 'W2', 'b2'} and all(g[k].shape == P[k].shape for k in P)
                for k in P:
                    Pp = {q: v.copy() for q, v in P.items()}; Pp[k].flat[0] += 1e-6
                    num = (f(Pp, X, Y)[0] - L) / 1e-6
                    assert abs(num - g[k].flat[0]) < 1e-4, f"grad of {k} disagrees with a finite difference ({g[k].flat[0]:.5f} vs {num:.5f})"''',
             solution=r'''
            def mlp_forward_backward_solution(params, X, Y):
                W1, b1, W2, b2 = params['W1'], params['b1'], params['W2'], params['b2']
                n = len(X)
                h = np.tanh(X @ W1 + b1); p = sigmoid(h @ W2 + b2)[:, 0]
                L = -np.mean(Y * np.log(p) + (1 - Y) * np.log(1 - p))
                dz2 = ((p - Y) / n)[:, None]
                dW2, db2 = h.T @ dz2, dz2.sum(0)
                dz1 = (dz2 @ W2.T) * (1 - h ** 2)
                return L, dict(W1=X.T @ dz1, b1=dz1.sum(0), W2=dW2, b2=db2)'''),
        dict(fn='train_xor', title='Train it', md=r'''
            Initialise W₁ (2 × hidden), W₂ (hidden × 1) from a normal with std 1, biases at 0, and run full-batch gradient descent with learning rate `lr` for `steps` steps.
            Return `(losses, accuracy)`.''',
             starter=r'''
            def train_xor(hidden=8, lr=1.0, steps=2000, seed=0):
                r = np.random.default_rng(seed)
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_train_xor(f):
                losses, acc = f()
                assert acc == 1.0, f"the MLP should solve XOR, accuracy {acc}"
                assert losses[-1] < 0.05 and losses[-1] < losses[0]''',
             solution=r'''
            def train_xor_solution(hidden=8, lr=1.0, steps=2000, seed=0):
                r = np.random.default_rng(seed)
                P = dict(W1=r.normal(size=(2, hidden)), b1=np.zeros(hidden), W2=r.normal(size=(hidden, 1)), b2=np.zeros(1))
                losses = []
                for _ in range(steps):
                    L, g = mlp_forward_backward_solution(P, X, Y); losses.append(L)
                    for k in P: P[k] -= lr * g[k]
                h = np.tanh(X @ P['W1'] + P['b1']); p = sigmoid(h @ P['W2'] + P['b2'])[:, 0]
                return losses, ((p > 0.5) == Y).mean()'''),
    ],
    explore_md=r'''
        **How many hidden units?** Two are enough in principle for XOR, but optimisation from a random start succeeds more reliably with a few more. Count successes over seeds.''',
    explore=r'''
        for hdim in [1, 2, 3, 4, 8]:
            ok = sum(train_xor_solution(hidden=hdim, seed=s)[1] == 1.0 for s in range(20))
            print(f"hidden={hdim}: solved XOR in {ok}/20 random starts")''',
    takeaways=r'''
        * A single linear layer draws one straight boundary; XOR needs two.
        * A hidden layer with a nonlinearity bends the input space so the output layer can separate it.
        * The backward pass is a few matmuls and elementwise products, exactly the chain rule.''',
))

# ------------------------------------------------------------------ 03
NBS.append(dict(
    slug='03_activations_depth', title='03 · Activations and vanishing gradients', deck='nn-fundamentals/02-activation-functions/', deck_name='Activation functions', minutes=25,
    goals='sigmoid, tanh, ReLU, GELU and SiLU with their derivatives, and a measurement of how gradient size changes through a deep stack for each.',
    setup=r'''
from math import erf, sqrt
_erf = np.vectorize(erf)
''',
    tasks=[
        dict(fn='activations', title='Activations and their derivatives', md=r'''
            Return a dict `name -> (f, df)` for `sigmoid`, `tanh`, `relu`, `gelu` (exact: $x\Phi(x)$ with $\Phi(x) = \frac{1}{2}(1 + \mathrm{erf}(x/\sqrt 2))$) and `silu` ($x\,\sigma(x)$).
            Derivatives: $\sigma' = \sigma(1-\sigma)$; $\mathrm{GELU}' = \Phi(x) + x\varphi(x)$ with $\varphi(x) = e^{-x^2/2}/\sqrt{2\pi}$; $\mathrm{SiLU}' = \sigma(x)(1 + x(1 - \sigma(x)))$.''',
             starter=r'''
            def activations():
                # TODO: return {'sigmoid': (f, df), 'tanh': ..., 'relu': ..., 'gelu': ..., 'silu': ...}
                raise NotImplementedError''',
             test=r'''
            def _test_activations(f):
                A = f(); x = np.linspace(-4, 4, 41)
                assert set(A) == {'sigmoid', 'tanh', 'relu', 'gelu', 'silu'}
                for k, (fn, df) in A.items():
                    num = (fn(x + 1e-6) - fn(x - 1e-6)) / 2e-6
                    m = np.abs(x) > 1e-3       # relu has a kink at 0
                    assert np.allclose(df(x)[m], num[m], atol=1e-5), f"{k}: derivative mismatch"
                assert np.isclose(A['gelu'][0](np.array([1.0]))[0], 0.8413447, atol=1e-6)
                assert np.isclose(A['silu'][0](np.array([1.0]))[0], 1 / (1 + np.exp(-1)), atol=1e-9)''',
             solution=r'''
            def activations_solution():
                sig = lambda x: 1 / (1 + np.exp(-x))
                Phi = lambda x: 0.5 * (1 + _erf(x / sqrt(2)))
                phi = lambda x: np.exp(-x * x / 2) / sqrt(2 * np.pi)
                return {'sigmoid': (sig, lambda x: sig(x) * (1 - sig(x))),
                        'tanh': (np.tanh, lambda x: 1 - np.tanh(x) ** 2),
                        'relu': (lambda x: np.maximum(x, 0), lambda x: (x > 0).astype(float)),
                        'gelu': (lambda x: x * Phi(x), lambda x: Phi(x) + x * phi(x)),
                        'silu': (lambda x: x * sig(x), lambda x: sig(x) * (1 + x * (1 - sig(x))))}'''),
        dict(fn='grad_through_depth', title='Gradient size through depth', md=r'''
            Build a stack of `depth` layers $h \leftarrow \text{act}(h W_\ell)$ of width `width`, with $W_\ell$ drawn with std $\sqrt{\text{gain}/\text{width}}$. Push a batch of 256 standard-normal inputs forward, then backpropagate a gradient of ones from the top.
            Return the array of mean |gradient| arriving at each layer's input, from the top layer (index 0) down to the bottom (index depth−1).''',
             starter=r'''
            def grad_through_depth(name, depth=30, width=256, gain=1.0, seed=0):
                f, df = activations()[name]          # your Task 1 functions
                r = np.random.default_rng(seed)
                # TODO: forward (store pre-activations), backward, record mean |grad| per layer
                raise NotImplementedError''',
             test=r'''
            def _test_grad_through_depth(f):
                g = f('sigmoid', depth=20)
                assert len(g) == 20
                assert g[-1] < 1e-6 * g[0], "sigmoid gradients should vanish by > 10^6 over 20 layers (σ' ≤ 1/4)"
                r = f('relu', depth=20, gain=2.0)
                assert 0.1 < r[-1] / r[0] < 10, "ReLU with He gain 2 should keep gradients roughly constant"''',
             solution=r'''
            def grad_through_depth_solution(name, depth=30, width=256, gain=1.0, seed=0):
                f, df = activations_solution()[name]
                r = np.random.default_rng(seed)
                Ws = [r.normal(scale=np.sqrt(gain / width), size=(width, width)) for _ in range(depth)]
                h = r.normal(size=(256, width)); pre = []
                for W in Ws:
                    z = h @ W; pre.append(z); h = f(z)
                g, out = np.ones_like(h), []
                for W, z in zip(reversed(Ws), reversed(pre)):
                    g = (g * df(z)) @ W.T; out.append(np.abs(g).mean())
                return np.array(out)'''),
    ],
    explore_md=r'''
        **Which activations keep the gradient alive?** Compare the ratio of bottom-layer to top-layer gradient size after 30 layers. For ReLU the variance-preserving gain is exactly 2 (He init). SiLU's outputs have a non-zero mean, so the simple rule breaks down; here a gain near 2.25 keeps gradients steady, and small changes either way make them shrink or grow by orders of magnitude over 30 layers. That sensitivity is one reason deep transformers lean on normalisation and residual connections instead of exact initialisation.''',
    explore=r'''
        for name, gain in [('sigmoid', 1.0), ('tanh', 1.0), ('relu', 2.0), ('gelu', 2.0), ('silu', 2.0), ('silu', 2.25), ('silu', 2.7)]:
            g = grad_through_depth_solution(name, depth=30, gain=gain)
            print(f"{name:8s} gain {gain}: bottom/top gradient ratio = {g[-1] / g[0]:.2e}")''',
    takeaways=r'''
        * Sigmoid's derivative is at most 1/4, so gradients shrink geometrically through depth.
        * ReLU-family activations (ReLU, GELU, SiLU) pass gradients with slope ≈ 1 for positive inputs; with the right init scale they stay healthy.
        * Modern LLMs use GELU or SiLU (inside SwiGLU) as smooth relatives of ReLU.''',
))

# ------------------------------------------------------------------ 04
NBS.append(dict(
    slug='04_optimizers_schedules', title='04 · SGD, Adam, AdamW and learning-rate schedules', deck='nn-fundamentals/05-optimizers/', deck_name='Optimizers', minutes=35,
    goals='SGD with momentum and AdamW as optimizer step functions, the difference between L2 regularisation and decoupled weight decay inside Adam, and a warmup + cosine learning-rate schedule.',
    setup=r'''
r0 = np.random.default_rng(0)
Xc = r0.normal(size=(400, 10)); w_true = r0.normal(size=10)
yc = (Xc @ w_true + 0.5 * r0.normal(size=400) > 0).astype(float)
def logreg_grad(w):
    p = 1 / (1 + np.exp(-(Xc @ w)))
    return Xc.T @ (p - yc) / len(yc), -np.mean(yc * np.log(p + 1e-12) + (1 - yc) * np.log(1 - p + 1e-12))
''',
    tasks=[
        dict(fn='warmup_cosine', title='Warmup + cosine schedule', md=r'''
            Return the learning rate at step `t` (0-indexed): linear warmup from 0 to `peak` over `warmup` steps (lr = peak·(t+1)/warmup), then cosine decay from `peak` to `peak·final_frac` at step `total`.
            This is the shape used by many LLM runs (Llama: 2,000 warmup steps, cosine to 10% of the peak).''',
             starter=r'''
            def warmup_cosine(t, peak, warmup, total, final_frac=0.1):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_warmup_cosine(f):
                assert np.isclose(f(0, 1.0, 10, 100), 0.1) and np.isclose(f(9, 1.0, 10, 100), 1.0)
                assert np.isclose(f(100, 1.0, 10, 100), 0.1), "ends at final_frac × peak"
                mid = f(55, 1.0, 10, 100)
                assert np.isclose(mid, 0.1 + 0.9 * 0.5), "halfway through the decay the cosine is at its midpoint"
                lrs = [f(t, 1.0, 10, 100) for t in range(10, 101)]
                assert all(a >= b - 1e-12 for a, b in zip(lrs, lrs[1:])), "must decrease after warmup"''',
             solution=r'''
            def warmup_cosine_solution(t, peak, warmup, total, final_frac=0.1):
                if t < warmup:
                    return peak * (t + 1) / warmup
                prog = min(1.0, (t - warmup) / max(1, total - warmup))
                return peak * (final_frac + (1 - final_frac) * 0.5 * (1 + np.cos(np.pi * prog)))'''),
        dict(fn='adamw_step', title='One AdamW step', md=r'''
            Given parameters `w`, gradient `g`, state `(m, v, t)` and hyper-parameters, return `(w_new, (m, v, t))`.
            Adam moments and bias correction as usual; then **decoupled** weight decay (Loshchilov & Hutter): $w \leftarrow w - \eta\,(\hat m/(\sqrt{\hat v} + \epsilon) + \lambda w)$. The decay term does **not** go through m and v.''',
             starter=r'''
            def adamw_step(w, g, state, lr, b1=0.9, b2=0.95, eps=1e-8, wd=0.1):
                m, v, t = state
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_adamw_step(f):
                w = np.array([1.0, -2.0]); st = (np.zeros(2), np.zeros(2), 0)
                w1, st1 = f(w, np.zeros(2), st, lr=0.1, wd=0.1)
                assert np.allclose(w1, w * (1 - 0.1 * 0.1)), "with zero gradient, AdamW still shrinks w by lr·wd"
                w2, st2 = f(w, np.array([0.5, 0.5]), st, lr=0.1, wd=0.0)
                assert np.allclose(w2, w - 0.1), "first Adam step moves each coordinate by ≈ lr (bias correction)"
                assert st2[2] == 1''',
             solution=r'''
            def adamw_step_solution(w, g, state, lr, b1=0.9, b2=0.95, eps=1e-8, wd=0.1):
                m, v, t = state; t += 1
                m = b1 * m + (1 - b1) * g; v = b2 * v + (1 - b2) * g * g
                mh, vh = m / (1 - b1 ** t), v / (1 - b2 ** t)
                return w - lr * (mh / (np.sqrt(vh) + eps) + wd * w), (m, v, t)'''),
        dict(fn='l2_vs_decoupled', title='L2 inside Adam is not weight decay', md=r'''
            Train logistic regression for 300 steps with Adam (lr 0.05) two ways: (a) **L2**: add λw to the gradient before Adam; (b) **AdamW**: decoupled decay λ. Use λ = 0.1 and start from w = 3·ones.
            Return `(norm_l2, norm_adamw)`: the final weight norms. Adam normalises the L2 term away for coordinates with large gradients, so the two differ.''',
             starter=r'''
            def l2_vs_decoupled(lam=0.1, steps=300, lr=0.05):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_l2_vs_decoupled(f):
                a, b = f()
                assert not np.isclose(a, b, rtol=0.02), "the two regularisers should give different weights"
                assert a > 0 and b > 0''',
             solution=r'''
            def l2_vs_decoupled_solution(lam=0.1, steps=300, lr=0.05):
                out = []
                for mode in ['l2', 'adamw']:
                    w = 3 * np.ones(10); st = (np.zeros(10), np.zeros(10), 0)
                    for _ in range(steps):
                        g, _ = logreg_grad(w)
                        if mode == 'l2':
                            w, st = adamw_step_solution(w, g + lam * w, st, lr, wd=0.0)
                        else:
                            w, st = adamw_step_solution(w, g, st, lr, wd=lam)
                    out.append(np.linalg.norm(w))
                return tuple(out)'''),
    ],
    explore_md=r'''
        **What the schedule looks like, and how far the two regularisers pull the weights.** Print a Llama-style schedule (peak 3e-4, 2,000 warmup steps, cosine to 10%) at a few steps, then compare final weight norms for L2-in-Adam vs AdamW across λ.''',
    explore=r'''
        for t in [0, 999, 1999, 50_000, 100_000, 199_999]:
            print(f"step {t:7d}: lr = {warmup_cosine_solution(t, 3e-4, 2000, 200_000):.2e}")
        for lam in [0.01, 0.1, 0.5]:
            a, b = l2_vs_decoupled_solution(lam)
            print(f"lambda {lam:4}: |w| with L2-in-Adam = {a:.3f}   with AdamW = {b:.3f}")''',
    takeaways=r'''
        * AdamW = Adam + weight decay applied directly to the weights, not through the gradient statistics.
        * L2 regularisation inside Adam gets divided by √v̂, so heavily-updated weights are barely regularised.
        * LLM runs warm the learning rate up, then decay it (often cosine) to a fraction of the peak.''',
))

# ------------------------------------------------------------------ 05
NBS.append(dict(
    slug='05_initialization', title='05 · Initialization: keeping signals alive', deck='nn-fundamentals/06-initialization/', deck_name='Initialization', minutes=25,
    goals='Xavier (Glorot) and He (Kaiming) initialisation, and measurements of how activation scale explodes or vanishes through depth when the variance is wrong.',
    setup='',
    tasks=[
        dict(fn='init_std', title='Xavier and He standard deviations', md=r'''
            Return the weight standard deviation for a layer with `fan_in` inputs and `fan_out` outputs:
            `'xavier'`: $\sqrt{2/(\text{fan\_in} + \text{fan\_out})}$ (Glorot & Bengio, 2010); `'he'`: $\sqrt{2/\text{fan\_in}}$ (He et al., 2015); `'naive'`: 1.''',
             starter=r'''
            def init_std(kind, fan_in, fan_out):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_init_std(f):
                assert np.isclose(f('xavier', 100, 300), np.sqrt(2 / 400))
                assert np.isclose(f('he', 512, 10), np.sqrt(2 / 512))
                assert f('naive', 5, 5) == 1''',
             solution=r'''
            def init_std_solution(kind, fan_in, fan_out):
                return {'xavier': np.sqrt(2 / (fan_in + fan_out)), 'he': np.sqrt(2 / fan_in), 'naive': 1.0}[kind]'''),
        dict(fn='activation_scale', title='Activation scale through 50 layers', md=r'''
            Push 512 standard-normal inputs through `depth` layers of width 256: $h \leftarrow \text{act}(h W)$ with W drawn using `init_std(kind, 256, 256)`. `act` is `'relu'` or `'tanh'`.
            Return the array of activation standard deviations after each layer.''',
             starter=r'''
            def activation_scale(kind, act, depth=50, width=256, seed=0):
                r = np.random.default_rng(seed)
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_activation_scale(f):
                s = f('he', 'relu')
                assert len(s) == 50 and 0.3 < s[-1] / s[0] < 3, "He init keeps ReLU activations at a stable scale"
                x = f('xavier', 'relu')
                assert x[-1] < 1e-3 * x[0], "Xavier is too small for ReLU (half the units are zero): the signal halves in variance each layer"
                n = f('naive', 'relu', depth=10)
                assert n[-1] > 1e8, "std 1 weights blow up by ≈ √(width/2) per layer"''',
             solution=r'''
            def activation_scale_solution(kind, act, depth=50, width=256, seed=0):
                r = np.random.default_rng(seed); h = r.normal(size=(512, width)); out = []
                fn = (lambda z: np.maximum(z, 0)) if act == 'relu' else np.tanh
                for _ in range(depth):
                    h = fn(h @ r.normal(scale=init_std_solution(kind, width, width), size=(width, width))); out.append(h.std())
                return np.array(out)'''),
    ],
    explore_md=r'''
        **Summary table.** Final-layer activation std after 50 layers for each initialisation and activation. Watch tanh with std-1 weights: its std stays near 1 because every unit is saturated at ±1, where the derivative is ≈ 0, so the signal survives but gradients do not.''',
    explore=r'''
        for act in ['relu', 'tanh']:
            for kind in ['naive', 'xavier', 'he']:
                with np.errstate(over='ignore', invalid='ignore'):
                    s = activation_scale_solution(kind, act)
                print(f"{act:5s} {kind:7s}: std after layer 1 = {s[0]:.3g}, after layer 50 = {s[-1]:.3g}")''',
    takeaways=r'''
        * Each layer multiplies activation variance by about fan_in × Var(w) × (activation's variance factor).
        * Choose Var(w) to make that factor 1: Xavier for tanh-like activations, He (2/fan_in) for ReLU.
        * Normalisation layers and residual connections (next deck) make deep transformers far less sensitive to this.''',
))

# ------------------------------------------------------------------ 06
NBS.append(dict(
    slug='06_overfitting_dropout', title='06 · Overfitting, dropout and weight decay', deck='nn-fundamentals/08-regularization/', deck_name='Regularization and generalization', minutes=30,
    goals='overfitting with polynomial regression, inverted dropout with the right scaling, and ridge (weight decay) as a fix, measured on held-out data.',
    setup=r'''
r0 = np.random.default_rng(0)
def make_data(n, seed):
    g = np.random.default_rng(seed); x = g.uniform(-1, 1, n)
    return x, np.sin(3 * x) + 0.2 * g.normal(size=n)
xtr, ytr = make_data(15, 1); xte, yte = make_data(500, 2)
def features(x, degree): return np.vander(x, degree + 1, increasing=True)
''',
    tasks=[
        dict(fn='fit_poly', title='Fit polynomials of growing degree', md=r'''
            Fit a least-squares polynomial of `degree` to the 15 training points (use `np.linalg.lstsq` on `features`), with optional ridge penalty `lam` (minimise $\lVert \Phi w - y\rVert^2 + \lambda \lVert w \rVert^2$).
            Return `(train_mse, test_mse)`.''',
             starter=r'''
            def fit_poly(degree, lam=0.0):
                # TODO (ridge: solve (ΦᵀΦ + λI) w = Φᵀy)
                raise NotImplementedError''',
             test=r'''
            def _test_fit_poly(f):
                tr3, te3 = f(3); tr14, te14 = f(14)
                assert tr14 < 1e-6, "degree 14 interpolates 15 points: train error ≈ 0"
                assert te14 > 10 * te3, "…but its test error explodes: overfitting"
                trr, ter = f(14, lam=1e-3)
                assert ter < te14 / 10, "a small ridge penalty tames the degree-14 fit"''',
             solution=r'''
            def fit_poly_solution(degree, lam=0.0):
                P = features(xtr, degree)
                w = np.linalg.lstsq(P, ytr, rcond=None)[0] if lam == 0 else np.linalg.solve(P.T @ P + lam * np.eye(degree + 1), P.T @ ytr)
                return np.mean((P @ w - ytr) ** 2), np.mean((features(xte, degree) @ w - yte) ** 2)'''),
        dict(fn='dropout', title='Inverted dropout', md=r'''
            In training mode, zero each element of `h` with probability `p` and **divide the survivors by (1 − p)** so the expected value is unchanged; in eval mode, return `h` untouched. Return `(out, mask)` (mask is all ones in eval).''',
             starter=r'''
            def dropout(h, p, train, rng):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_dropout(f):
                g = np.random.default_rng(0); h = np.ones((2000, 100))
                out, m = f(h, 0.5, True, g)
                assert abs((m == 0).mean() - 0.5) < 0.02, "about half the units dropped"
                assert abs(out.mean() - 1) < 0.02, "inverted scaling keeps the mean at 1"
                e, _ = f(h, 0.5, False, g); assert np.array_equal(e, h), "eval mode is the identity"''',
             solution=r'''
            def dropout_solution(h, p, train, rng):
                if not train:
                    return h, np.ones_like(h)
                m = (rng.random(h.shape) >= p).astype(h.dtype)
                return h * m / (1 - p), m'''),
    ],
    explore_md=r'''
        **The U-shaped curve.** Train and test error as the polynomial degree grows, with and without a small ridge penalty.''',
    explore=r'''
        for d in [1, 3, 5, 9, 12, 14]:
            tr, te = fit_poly_solution(d); trr, ter = fit_poly_solution(d, 1e-3)
            print(f"degree {d:2d}: train {tr:.4f} test {te:10.4f}   |  ridge 1e-3: train {trr:.4f} test {ter:.4f}")''',
    takeaways=r'''
        * More capacity always lowers training error; test error falls then rises when the model fits noise.
        * Weight decay (ridge) and dropout limit how much the model can bend to individual points.
        * Inverted dropout scales by 1/(1 − p) during training so nothing changes at inference.''',
))

# ------------------------------------------------------------------ 07
NBS.append(dict(
    slug='07_tiny_char_lm', title='07 · A tiny character-level language model', deck='nn-fundamentals/10-mlp-to-language-model/', deck_name='From MLP to language model', minutes=40,
    goals='a counting bigram model, then a Bengio-style neural model (embeddings → hidden layer → softmax over the next character) trained by cross-entropy, compared on held-out loss, and sampled.',
    setup=r'''
TEXT = ("the cat sat on the mat. the dog sat on the log. a cat and a dog met on a mat. "
        "the cat saw the dog and the dog saw the cat. on the log sat a frog. the frog sat still. ") * 6
chars = sorted(set(TEXT)); V = len(chars); stoi = {c: i for i, c in enumerate(chars)}
data = np.array([stoi[c] for c in TEXT]); split = int(0.9 * len(data))
train, val = data[:split], data[split:]
def softmax(z):
    z = z - z.max(-1, keepdims=True); e = np.exp(z); return e / e.sum(-1, keepdims=True)
''',
    tasks=[
        dict(fn='bigram_loss', title='Counting bigram model', md=r'''
            Count how often each character follows each other character in `train`, add `alpha` to every count (smoothing), normalise rows into probabilities, and return the mean negative log-likelihood (nats) of the next character on `val`.''',
             starter=r'''
            def bigram_loss(alpha=0.1):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_bigram_loss(f):
                L = f()
                assert L < np.log(V), f"must beat uniform ({np.log(V):.2f} nats), got {L:.2f}"
                assert f(alpha=100) > L, "heavy smoothing pushes the model toward uniform"''',
             solution=r'''
            def bigram_loss_solution(alpha=0.1):
                C = np.full((V, V), alpha)
                np.add.at(C, (train[:-1], train[1:]), 1)
                P = C / C.sum(1, keepdims=True)
                return -np.mean(np.log(P[val[:-1], val[1:]]))'''),
        dict(fn='mlp_lm', title='A neural language model with a context of 3', md=r'''
            Model (Bengio et al., 2003): embed each of the previous `ctx` characters with a shared table E (V × d), concatenate, $h = \tanh(x W_1 + b_1)$, logits $= h W_2 + b_2$, softmax over V.
            Train with full-batch gradient descent on cross-entropy for `steps` steps. Return `(train_losses, val_loss)`. The gradient of softmax + cross-entropy w.r.t. logits is $(p - \text{onehot})/n$. For E, scatter-add the gradient of each embedding slot back into its row (`np.add.at`).''',
             starter=r'''
            def mlp_lm(ctx=3, d=8, hidden=64, lr=0.5, steps=1500, seed=0):
                r = np.random.default_rng(seed)
                def windows(seq):
                    X = np.stack([seq[i:len(seq) - ctx + i] for i in range(ctx)], 1); return X, seq[ctx:]
                Xtr, Ytr = windows(train); Xva, Yva = windows(val)
                # TODO: init E, W1, b1, W2, b2; train; evaluate on Xva
                raise NotImplementedError''',
             test=r'''
            def _test_mlp_lm(f):
                tl, vl = f()
                assert tl[-1] < tl[0] * 0.6, "training loss should drop substantially"
                C = np.full((V, V), 0.1); np.add.at(C, (train[:-1], train[1:]), 1); P = C / C.sum(1, keepdims=True)
                bg = -np.mean(np.log(P[val[:-1], val[1:]]))
                assert vl < bg - 0.2, f"3 characters of context should beat the bigram model by > 0.2 nats (got {vl:.2f} vs {bg:.2f})"''',
             solution=r'''
            def mlp_lm_solution(ctx=3, d=8, hidden=64, lr=0.5, steps=1500, seed=0):
                r = np.random.default_rng(seed)
                def windows(seq):
                    X = np.stack([seq[i:len(seq) - ctx + i] for i in range(ctx)], 1); return X, seq[ctx:]
                Xtr, Ytr = windows(train); Xva, Yva = windows(val)
                E = r.normal(scale=0.5, size=(V, d)); W1 = r.normal(scale=1 / np.sqrt(ctx * d), size=(ctx * d, hidden)); b1 = np.zeros(hidden)
                W2 = r.normal(scale=1 / np.sqrt(hidden), size=(hidden, V)); b2 = np.zeros(V)
                def forward(X):
                    x = E[X].reshape(len(X), -1); h = np.tanh(x @ W1 + b1); return x, h, softmax(h @ W2 + b2)
                losses = []
                for _ in range(steps):
                    x, h, p = forward(Xtr); n = len(Ytr)
                    losses.append(-np.mean(np.log(p[np.arange(n), Ytr])))
                    dz = p.copy(); dz[np.arange(n), Ytr] -= 1; dz /= n
                    dW2, db2 = h.T @ dz, dz.sum(0); dh = dz @ W2.T * (1 - h ** 2)
                    dW1, db1 = x.T @ dh, dh.sum(0); dx = (dh @ W1.T).reshape(n, ctx, d)
                    dE = np.zeros_like(E); np.add.at(dE, Xtr, dx)
                    for P_, G_ in ((E, dE), (W1, dW1), (b1, db1), (W2, dW2), (b2, db2)): P_ -= lr * G_
                _, _, pv = forward(Xva)
                mlp_lm_solution.params = (E, W1, b1, W2, b2, ctx)
                return losses, -np.mean(np.log(pv[np.arange(len(Yva)), Yva]))'''),
    ],
    explore_md=r'''
        **Sample from it.** Start from "the" and repeatedly sample the next character at temperature 0.8.''',
    explore=r'''
        tl, vl = mlp_lm_solution()
        E, W1, b1, W2, b2, ctx = mlp_lm_solution.params
        print(f"bigram val loss {bigram_loss_solution():.3f} nats   MLP val loss {vl:.3f} nats   (uniform {np.log(V):.3f})")
        g = np.random.default_rng(3); s = [stoi[c] for c in 'the']
        for _ in range(120):
            h = np.tanh(E[s[-ctx:]].reshape(1, -1) @ W1 + b1); p = softmax((h @ W2 + b2) / 0.8)[0]
            s.append(g.choice(V, p=p))
        print(''.join(chars[i] for i in s))''',
    takeaways=r'''
        * A language model is a classifier over the next token, trained with cross-entropy on every position.
        * Learned embeddings + a hidden layer generalise beyond raw counts and use more context.
        * Transformers replace the fixed-context MLP with attention over the whole prefix, but the training objective is the same.''',
))
