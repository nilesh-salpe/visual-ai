"""PyTorch for LLMs exercise notebooks. Run on CPU (Colab's default runtime is fine). Validated against PyTorch 2.14.1."""

TORCH = r'''
import torch, torch.nn as nn, torch.nn.functional as F
torch.manual_seed(0)
print("PyTorch", torch.__version__)
'''

NBS = []

# ------------------------------------------------------------------ 01
NBS.append(dict(
    slug='01_tensors_views', title='01 · Tensors: shapes, strides, views and einsum', deck='pytorch/01-tensors/', deck_name='Tensors, strides and views', minutes=30,
    goals='how a tensor maps to memory with strides, when `view` works and when you need `reshape`/`contiguous`, broadcasting rules, and attention scores with `einsum` and batched matmul.',
    setup=TORCH,
    tasks=[
        dict(fn='contiguous_strides', title='Strides of a contiguous tensor', md=r'''
            A contiguous row-major tensor of shape (d₀, d₁, …, dₙ₋₁) has stride[i] = product of all later dimensions. Write `contiguous_strides(shape)` and compare with `torch.empty(shape).stride()`.''',
             starter=r'''
            def contiguous_strides(shape):
                # TODO: last stride is 1; each earlier stride multiplies by the next dimension
                raise NotImplementedError''',
             test=r'''
            def _test_contiguous_strides(f):
                for shape in [(3, 4), (2, 3, 5), (7,), (2, 1, 4, 8)]:
                    assert tuple(f(shape)) == torch.empty(shape).stride(), f"shape {shape}"''',
             solution=r'''
            def contiguous_strides_solution(shape):
                out, acc = [], 1
                for d in reversed(shape):
                    out.append(acc); acc *= d
                return tuple(reversed(out))'''),
        dict(fn='split_merge', title='Split and merge attention heads', md=r'''
            Multi-head attention reshapes activations of shape (B, T, C) into (B, H, T, C/H) and back.
            Write `split_heads(x, H)` (use `view` then `transpose(1, 2)`) and `merge_heads(y)` (the inverse). `merge_heads` needs `.contiguous()` before `view`, because the transpose made the tensor non-contiguous (or use `reshape`, which copies only when needed). Return both functions.''',
             starter=r'''
            def split_heads(x, H):
                # TODO
                raise NotImplementedError

            def merge_heads(y):
                # TODO
                raise NotImplementedError

            def split_merge():
                return split_heads, merge_heads''',
             test=r'''
            def _test_split_merge(f):
                s, m = f()
                x = torch.randn(2, 5, 12)
                y = s(x, 3)
                assert y.shape == (2, 3, 5, 4), f"expected (B, H, T, C/H), got {tuple(y.shape)}"
                assert not y.is_contiguous(), "after transpose the tensor is a non-contiguous view"
                assert torch.equal(y[1, 2, 4], x[1, 4, 8:12]), "head h of token t holds channels h·D … (h+1)·D"
                assert torch.equal(m(y), x), "merge must invert split"''',
             solution=r'''
            def split_heads_s(x, H):
                B, T, C = x.shape
                return x.view(B, T, H, C // H).transpose(1, 2)

            def merge_heads_s(y):
                B, H, T, D = y.shape
                return y.transpose(1, 2).contiguous().view(B, T, H * D)

            def split_merge_solution():
                return split_heads_s, merge_heads_s'''),
        dict(fn='scores_einsum', title='Attention scores three ways', md=r'''
            For queries and keys of shape (B, H, T, D), the score tensor is S[b, h, i, j] = Σ_d q[b,h,i,d]·k[b,h,j,d] / √D.
            Return `(s_matmul, s_einsum)`: one computed with `q @ k.transpose(-2, -1)`, one with `torch.einsum("bhid,bhjd->bhij", …)`. Both must equal an explicit loop.''',
             starter=r'''
            def scores_einsum(q, k):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_scores_einsum(f):
                q, k = torch.randn(2, 3, 4, 8), torch.randn(2, 3, 5, 8)
                a, b = f(q, k)
                assert a.shape == (2, 3, 4, 5) and b.shape == (2, 3, 4, 5)
                ref = torch.zeros(2, 3, 4, 5)
                for i in range(4):
                    for j in range(5):
                        ref[:, :, i, j] = (q[:, :, i] * k[:, :, j]).sum(-1) / 8 ** 0.5
                assert torch.allclose(a, ref, atol=1e-5) and torch.allclose(b, ref, atol=1e-5)''',
             solution=r'''
            def scores_einsum_solution(q, k):
                D = q.shape[-1]
                return q @ k.transpose(-2, -1) / D ** 0.5, torch.einsum("bhid,bhjd->bhij", q, k) / D ** 0.5'''),
    ],
    explore_md=r'''
        **Views share memory.** Changing a view changes the original, and a transpose only swaps strides. Broadcasting stretches size-1 dimensions without copying (its stride is 0).''',
    explore=r'''
        x = torch.arange(12.).reshape(3, 4); v = x.t()
        print("x.stride()", x.stride(), " x.t().stride()", v.stride(), " same storage:", x.data_ptr() == v.data_ptr())
        v[0, 0] = 100; print("after editing the view, x[0, 0] =", x[0, 0].item())
        b = torch.tensor([1., 2., 3., 4.]).expand(3, 4); print("expanded stride:", b.stride(), "(0 = broadcast without copying)")
        try:
            v.view(12)
        except RuntimeError as e:
            print("view on a transposed tensor fails:", str(e)[:70], "…")
        print("reshape works (copies):", v.reshape(12)[:4])''',
    takeaways=r'''
        * A tensor is storage + shape + strides; `view`, `transpose`, `permute`, slicing and `expand` only change the metadata.
        * `view` needs compatible strides; after a transpose, call `.contiguous()` or use `reshape`.
        * `einsum` and batched `@` express attention in one line; both dispatch to the same matmul kernels.''',
))

# ------------------------------------------------------------------ 02
NBS.append(dict(
    slug='02_autograd', title='02 · Autograd: graphs, custom functions and accumulation', deck='pytorch/02-autograd/', deck_name='Autograd', minutes=30,
    goals='how `requires_grad`, `.grad`, `no_grad` and `detach` work, a custom `torch.autograd.Function` checked with `gradcheck`, and why gradient accumulation over micro-batches equals one big batch.',
    setup=TORCH,
    tasks=[
        dict(fn='SiLUFn', title='A custom autograd Function', md=r'''
            Implement SiLU, y = x·σ(x), as a `torch.autograd.Function` with `forward(ctx, x)` and `backward(ctx, grad_out)`. Save what backward needs with `ctx.save_for_backward`. Derivative: σ(x)·(1 + x·(1 − σ(x))).
            The test uses `torch.autograd.gradcheck` (float64 finite differences).''',
             starter=r'''
            class SiLUFn(torch.autograd.Function):
                @staticmethod
                def forward(ctx, x):
                    # TODO
                    raise NotImplementedError
                @staticmethod
                def backward(ctx, grad_out):
                    # TODO
                    raise NotImplementedError''',
             test=r'''
            def _test_SiLUFn(cls):
                x = torch.randn(10, dtype=torch.float64, requires_grad=True)
                assert torch.allclose(cls.apply(x), F.silu(x))
                assert torch.autograd.gradcheck(cls.apply, (x,)), "backward disagrees with finite differences"''',
             solution=r'''
            class SiLUFn_solution(torch.autograd.Function):
                @staticmethod
                def forward(ctx, x):
                    ctx.save_for_backward(x)
                    return x * torch.sigmoid(x)
                @staticmethod
                def backward(ctx, grad_out):
                    (x,) = ctx.saved_tensors
                    s = torch.sigmoid(x)
                    return grad_out * s * (1 + x * (1 - s))'''),
        dict(fn='accumulate', title='Gradient accumulation', md=r'''
            Given a model, a loss function and a batch split into `k` micro-batches, compute gradients by running backward on each micro-batch loss **divided by k** without zeroing in between. Return a dict `name -> grad` (cloned). It must equal the gradient of the mean loss over the full batch.''',
             starter=r'''
            def accumulate(model, X, Y, k):
                model.zero_grad()
                # TODO: for each of k chunks: loss = F.mse_loss(model(xc), yc) / k; loss.backward()
                raise NotImplementedError''',
             test=r'''
            def _test_accumulate(f):
                torch.manual_seed(1); m = nn.Sequential(nn.Linear(4, 8), nn.Tanh(), nn.Linear(8, 1))
                X, Y = torch.randn(32, 4), torch.randn(32, 1)
                g = f(m, X, Y, 4)
                m.zero_grad(); F.mse_loss(m(X), Y).backward()
                for n, p in m.named_parameters():
                    assert torch.allclose(g[n], p.grad, atol=1e-6), f"{n}: accumulated gradient differs from the full-batch gradient"''',
             solution=r'''
            def accumulate_solution(model, X, Y, k):
                model.zero_grad()
                for xc, yc in zip(X.chunk(k), Y.chunk(k)):
                    (F.mse_loss(model(xc), yc) / k).backward()
                return {n: p.grad.clone() for n, p in model.named_parameters()}'''),
        dict(fn='frozen_grads', title='no_grad, detach and frozen parameters', md=r'''
            Return a dict with three booleans, each found by running code (not by guessing):
            `'no_grad_output_requires_grad'`: does `w * 2` computed inside `torch.no_grad()` require grad (w has requires_grad=True)?
            `'detach_shares_storage'`: does `w.detach()` share memory with `w`?
            `'frozen_param_has_grad'`: after setting `lin.weight.requires_grad_(False)` and calling backward on `lin(x).sum()`, is `lin.weight.grad` not None?''',
             starter=r'''
            def frozen_grads():
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_frozen_grads(f):
                d = f()
                assert d == {"no_grad_output_requires_grad": False, "detach_shares_storage": True, "frozen_param_has_grad": False}, d''',
             solution=r'''
            def frozen_grads_solution():
                w = torch.randn(3, requires_grad=True)
                with torch.no_grad():
                    a = (w * 2).requires_grad
                b = w.detach().data_ptr() == w.data_ptr()
                lin = nn.Linear(3, 2); lin.weight.requires_grad_(False); lin(torch.randn(4, 3)).sum().backward()
                return {"no_grad_output_requires_grad": a, "detach_shares_storage": b, "frozen_param_has_grad": lin.weight.grad is not None}'''),
    ],
    explore_md=r'''
        **Look at the graph.** Every result of a differentiable op has a `grad_fn` pointing at its backward node; following `next_functions` walks the graph that `.backward()` traverses.''',
    explore=r'''
        x = torch.randn(3, requires_grad=True); y = (torch.tanh(x) * 2).sum()
        node, depth = y.grad_fn, 0
        while node is not None and depth < 6:
            print("  " * depth + type(node).__name__); nxt = [n for n, _ in node.next_functions if n is not None]; node = nxt[0] if nxt else None; depth += 1''',
    takeaways=r'''
        * Autograd records a graph of `grad_fn` nodes during the forward pass; `.backward()` walks it in reverse and accumulates into `.grad`.
        * Gradients accumulate, so call `zero_grad()` each step, and divide micro-batch losses by k to emulate a bigger batch.
        * `no_grad` stops recording, `detach` returns a graph-free view, and frozen parameters get no `.grad` (the basis of LoRA-style fine-tuning).''',
))

# ------------------------------------------------------------------ 03
NBS.append(dict(
    slug='03_transformer_block', title='03 · nn.Module: a pre-norm transformer block', deck='pytorch/03-nn-module/', deck_name='nn.Module and a transformer block', minutes=40,
    goals='a causal self-attention module with `F.scaled_dot_product_attention`, an MLP, RMSNorm and residuals assembled into a pre-norm block, with parameter counting, `state_dict` and buffers.',
    setup=TORCH,
    tasks=[
        dict(fn='CausalSelfAttention', title='Causal self-attention with SDPA', md=r'''
            One `nn.Linear(C, 3C)` produces q, k, v; split into H heads; call `F.scaled_dot_product_attention(q, k, v, is_causal=True)`; merge heads; project with `nn.Linear(C, C)`. No biases (`bias=False`).
            The test compares with an explicit masked-softmax implementation using your module's own weights.''',
             starter=r'''
            class CausalSelfAttention(nn.Module):
                def __init__(self, C, H):
                    super().__init__()
                    self.H = H
                    self.qkv = nn.Linear(C, 3 * C, bias=False)
                    self.proj = nn.Linear(C, C, bias=False)
                def forward(self, x):
                    # TODO
                    raise NotImplementedError''',
             test=r'''
            def _test_CausalSelfAttention(cls):
                torch.manual_seed(0); B, T, C, H = 2, 6, 16, 4
                m = cls(C, H); x = torch.randn(B, T, C)
                y = m(x); assert y.shape == (B, T, C)
                q, k, v = m.qkv(x).split(C, dim=2)
                q, k, v = (t.view(B, T, H, C // H).transpose(1, 2) for t in (q, k, v))
                att = (q @ k.transpose(-2, -1)) / (C // H) ** 0.5
                att = att.masked_fill(torch.triu(torch.ones(T, T, dtype=torch.bool), 1), float("-inf")).softmax(-1)
                ref = m.proj((att @ v).transpose(1, 2).reshape(B, T, C))
                assert torch.allclose(y, ref, atol=1e-5), "must match masked softmax attention"
                y2 = m(torch.cat([x[:, :3], torch.randn(B, 3, C)], 1))
                assert torch.allclose(y[:, :3], y2[:, :3], atol=1e-5), "causal: future tokens must not affect earlier outputs"''',
             solution=r'''
            class CausalSelfAttention_solution(nn.Module):
                def __init__(self, C, H):
                    super().__init__()
                    self.H = H
                    self.qkv = nn.Linear(C, 3 * C, bias=False)
                    self.proj = nn.Linear(C, C, bias=False)
                def forward(self, x):
                    B, T, C = x.shape
                    q, k, v = self.qkv(x).split(C, dim=2)
                    q, k, v = (t.view(B, T, self.H, C // self.H).transpose(1, 2) for t in (q, k, v))
                    y = F.scaled_dot_product_attention(q, k, v, is_causal=True)
                    return self.proj(y.transpose(1, 2).contiguous().view(B, T, C))'''),
        dict(fn='Block', title='A pre-norm block', md=r'''
            `x = x + attn(RMSNorm(x)); x = x + mlp(RMSNorm(x))`, with `nn.RMSNorm(C)` and an MLP `Linear(C, 4C, bias=False) → GELU → Linear(4C, C, bias=False)`. Use the reference attention class `CausalSelfAttention_solution` if yours isn't done (`attn_cls` argument).
            Parameter count: 3C² + C² (attention) + 8C² (MLP) + 2C (two norm gains) = 12C² + 2C.''',
             starter=r'''
            class Block(nn.Module):
                def __init__(self, C, H, attn_cls=None):
                    super().__init__()
                    attn_cls = attn_cls or CausalSelfAttention
                    # TODO: self.n1, self.attn, self.n2, self.mlp
                    raise NotImplementedError
                def forward(self, x):
                    # TODO
                    raise NotImplementedError''',
             test=r'''
            def _test_Block(cls):
                C, H = 32, 4
                ref_attn = globals().get("CausalSelfAttention_solution") or CausalSelfAttention
                b = cls(C, H, ref_attn)
                n = sum(p.numel() for p in b.parameters())
                assert n == 12 * C * C + 2 * C, f"expected 12C² + 2C = {12 * C * C + 2 * C} parameters, got {n}"
                x = torch.randn(2, 5, C); y = b(x)
                assert y.shape == x.shape
                with torch.no_grad():
                    for p in b.parameters(): p.zero_()
                assert torch.allclose(b(x), x), "with zero weights each residual branch outputs 0, so the block is the identity"''',
             solution=r'''
            class Block_solution(nn.Module):
                def __init__(self, C, H, attn_cls=None):
                    super().__init__()
                    attn_cls = attn_cls or CausalSelfAttention_solution
                    self.n1, self.attn = nn.RMSNorm(C), attn_cls(C, H)
                    self.n2 = nn.RMSNorm(C)
                    self.mlp = nn.Sequential(nn.Linear(C, 4 * C, bias=False), nn.GELU(), nn.Linear(4 * C, C, bias=False))
                def forward(self, x):
                    x = x + self.attn(self.n1(x))
                    return x + self.mlp(self.n2(x))'''),
        dict(fn='buffers_state', title='Parameters vs buffers in state_dict', md=r'''
            Register a non-trainable rotary-frequency table as a buffer. Write a tiny module `WithBuffers` that has one parameter `w` (shape (4,)), a persistent buffer `inv_freq` (shape (2,)) and a non-persistent buffer `cache` (shape (3,)).
            Return `sorted(module.state_dict().keys())` and the names in `parameters()`. Persistent buffers are saved; non-persistent ones are not; neither is trained.''',
             starter=r'''
            class WithBuffers(nn.Module):
                def __init__(self):
                    super().__init__()
                    # TODO: nn.Parameter, register_buffer(..., persistent=False)
                    raise NotImplementedError

            def buffers_state():
                m = WithBuffers()
                return sorted(m.state_dict().keys()), [n for n, _ in m.named_parameters()]''',
             test=r'''
            def _test_buffers_state(f):
                keys, params = f()
                assert keys == ["inv_freq", "w"], f"state_dict keys: {keys}"
                assert params == ["w"], "buffers are not parameters"''',
             solution=r'''
            class WithBuffers_solution(nn.Module):
                def __init__(self):
                    super().__init__()
                    self.w = nn.Parameter(torch.zeros(4))
                    self.register_buffer("inv_freq", torch.ones(2))
                    self.register_buffer("cache", torch.zeros(3), persistent=False)

            def buffers_state_solution():
                m = WithBuffers_solution()
                return sorted(m.state_dict().keys()), [n for n, _ in m.named_parameters()]'''),
    ],
    explore_md=r'''
        **Which SDPA backends exist?** On CPU, PyTorch uses its math or fused CPU kernels; on GPUs it can pick FlashAttention, memory-efficient attention or cuDNN. You can restrict the choice with `torch.nn.attention.sdpa_kernel`.''',
    explore=r'''
        from torch.nn.attention import SDPBackend, sdpa_kernel
        print("backends:", [b for b in dir(SDPBackend) if b.isupper()])
        q = k = v = torch.randn(1, 2, 8, 16)
        with sdpa_kernel(SDPBackend.MATH):
            a = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        b = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        print("math backend matches default:", torch.allclose(a, b, atol=1e-6))
        blk = Block_solution(64, 8); print("block parameters:", sum(p.numel() for p in blk.parameters()), "= 12·64² + 2·64 =", 12 * 64 * 64 + 128)''',
    takeaways=r'''
        * `nn.Module` tracks parameters and sub-modules automatically; buffers hold non-trainable state (persistent ones go in `state_dict`).
        * `F.scaled_dot_product_attention(…, is_causal=True)` replaces hand-written masked softmax and dispatches to fused kernels (FlashAttention on supported GPUs).
        * A pre-norm block is two residual branches; with ≈12C² weights per block, parameter counts follow directly.''',
))

# ------------------------------------------------------------------ 04
NBS.append(dict(
    slug='04_training_loop', title='04 · The training loop: AdamW, schedules, clipping, checkpoints', deck='pytorch/04-training-loop/', deck_name='The training loop', minutes=35,
    goals='a standard step (forward, loss, `zero_grad`, backward, clip, optimizer and scheduler step), parameter groups that exclude norms and biases from weight decay, a warmup + cosine `LambdaLR`, and checkpoints that resume bit-for-bit.',
    setup=TORCH + r'''
def toy_model(seed=0):
    torch.manual_seed(seed)
    return nn.Sequential(nn.Linear(8, 32), nn.LayerNorm(32), nn.GELU(), nn.Linear(32, 1))
gX = torch.Generator().manual_seed(1); DATA_X = torch.randn(256, 8, generator=gX); DATA_Y = (DATA_X[:, :1] * 2 - DATA_X[:, 1:2]).sin()
''',
    tasks=[
        dict(fn='param_groups', title='Weight decay only on matrices', md=r'''
            LLM recipes apply weight decay to 2-D weight matrices but not to biases or norm gains. Return two parameter groups for AdamW: `[{"params": decay, "weight_decay": wd}, {"params": no_decay, "weight_decay": 0.0}]`, splitting by `p.dim() >= 2`.''',
             starter=r'''
            def param_groups(model, wd=0.1):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_param_groups(f):
                m = toy_model(); g = f(m, 0.1)
                assert len(g) == 2 and g[0]["weight_decay"] == 0.1 and g[1]["weight_decay"] == 0.0
                assert sum(p.numel() for p in g[0]["params"]) == 8 * 32 + 32 * 1, "only the two Linear weight matrices decay"
                assert len(g[1]["params"]) == 4, "two biases + LayerNorm weight and bias"
                torch.optim.AdamW(g, lr=1e-3)''',
             solution=r'''
            def param_groups_solution(model, wd=0.1):
                decay = [p for p in model.parameters() if p.requires_grad and p.dim() >= 2]
                no_decay = [p for p in model.parameters() if p.requires_grad and p.dim() < 2]
                return [{"params": decay, "weight_decay": wd}, {"params": no_decay, "weight_decay": 0.0}]'''),
        dict(fn='make_scheduler', title='Warmup + cosine with LambdaLR', md=r'''
            `torch.optim.lr_scheduler.LambdaLR(opt, fn)` multiplies the base learning rate by `fn(step)`. Write `make_scheduler(opt, warmup, total, final=0.1)` with linear warmup to 1 over `warmup` steps, then cosine decay to `final` at `total`.''',
             starter=r'''
            def make_scheduler(opt, warmup, total, final=0.1):
                def fn(step):
                    # TODO
                    raise NotImplementedError
                return torch.optim.lr_scheduler.LambdaLR(opt, fn)''',
             test=r'''
            def _test_make_scheduler(f):
                opt = torch.optim.AdamW(toy_model().parameters(), lr=1.0)
                s = f(opt, 10, 110); lrs = []
                for _ in range(111):
                    lrs.append(opt.param_groups[0]["lr"]); opt.step(); s.step()
                assert abs(lrs[0] - 0.1) < 1e-9 and abs(lrs[9] - 1.0) < 1e-9, "warmup: (step+1)/warmup"
                assert abs(lrs[60] - 0.55) < 1e-9 and abs(lrs[110] - 0.1) < 1e-9, "cosine down to 10%"''',
             solution=r'''
            import math
            def make_scheduler_solution(opt, warmup, total, final=0.1):
                def fn(step):
                    if step < warmup:
                        return (step + 1) / warmup
                    p = min(1.0, (step - warmup) / max(1, total - warmup))
                    return final + (1 - final) * 0.5 * (1 + math.cos(math.pi * p))
                return torch.optim.lr_scheduler.LambdaLR(opt, fn)'''),
        dict(fn='train', title='Train, checkpoint, resume', md=r'''
            Write `train(model, opt, sched, steps, start=0)` that runs full-batch steps on `DATA_X, DATA_Y`: `opt.zero_grad(set_to_none=True)`, MSE loss, backward, `clip_grad_norm_(…, 1.0)`, `opt.step()`, `sched.step()`. Return the list of losses.
            The test trains 40 steps straight, and separately 20 steps → save `{"model", "opt", "sched"}` state dicts → load into fresh objects → 20 more. Both runs must end with identical weights.''',
             starter=r'''
            def train(model, opt, sched, steps):
                losses = []
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_train(f):
                import io
                pg = globals().get("param_groups_solution") or param_groups; ms = globals().get("make_scheduler_solution") or make_scheduler
                def fresh():
                    m = toy_model(); o = torch.optim.AdamW(pg(m), lr=3e-2); return m, o, ms(o, 5, 40)
                m1, o1, s1 = fresh(); l1 = f(m1, o1, s1, 40)
                assert l1[-1] < 0.5 * l1[0], "loss should fall"
                m2, o2, s2 = fresh(); f(m2, o2, s2, 20)
                buf = io.BytesIO(); torch.save({"model": m2.state_dict(), "opt": o2.state_dict(), "sched": s2.state_dict()}, buf); buf.seek(0)
                m3, o3, s3 = fresh(); ck = torch.load(buf)
                m3.load_state_dict(ck["model"]); o3.load_state_dict(ck["opt"]); s3.load_state_dict(ck["sched"])
                f(m3, o3, s3, 20)
                for a, b in zip(m1.parameters(), m3.parameters()):
                    assert torch.equal(a, b), "resuming from a checkpoint must reproduce the uninterrupted run exactly"''',
             solution=r'''
            def train_solution(model, opt, sched, steps):
                losses = []
                for _ in range(steps):
                    opt.zero_grad(set_to_none=True)
                    loss = F.mse_loss(model(DATA_X), DATA_Y)
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    opt.step(); sched.step(); losses.append(loss.item())
                return losses'''),
    ],
    explore_md=r'''
        **What a checkpoint must contain.** Saving only the model weights and resuming changes the trajectory: AdamW's moment estimates and the scheduler position are lost.''',
    explore=r'''
        import io
        def fresh():
            m = toy_model(); o = torch.optim.AdamW(param_groups_solution(m), lr=3e-2); return m, o, make_scheduler_solution(o, 5, 40)
        m0, o0, s0 = fresh(); train_solution(m0, o0, s0, 40)
        def run(save_opt):
            m, o, s = fresh(); train_solution(m, o, s, 20)
            ck = {"model": m.state_dict()} | ({"opt": o.state_dict(), "sched": s.state_dict()} if save_opt else {})
            m2, o2, s2 = fresh(); m2.load_state_dict(ck["model"])
            if save_opt: o2.load_state_dict(ck["opt"]); s2.load_state_dict(ck["sched"])
            train_solution(m2, o2, s2, 20)
            return max((a - b).abs().max().item() for a, b in zip(m0.parameters(), m2.parameters()))
        print(f"max weight difference vs the uninterrupted run, resuming with optimizer + scheduler state: {run(True):.2e}")
        print(f"max weight difference vs the uninterrupted run, resuming with weights only:             {run(False):.2e}")
        print("(weights only restarts warmup and Adam's moments, so the run takes a different path)")
        print("AdamW defaults:", {k: v for k, v in torch.optim.AdamW([torch.zeros(1, requires_grad=True)]).defaults.items() if k in ("lr", "betas", "eps", "weight_decay")})''',
    takeaways=r'''
        * One step: `zero_grad` → forward → loss → `backward` → clip → `optimizer.step()` → `scheduler.step()`.
        * Exclude biases and norm gains from weight decay with parameter groups; AdamW's PyTorch default weight decay is 0.01, LLM recipes often use 0.1.
        * A resumable checkpoint stores model, optimizer and scheduler state (and RNG/data position in real runs).''',
))

# ------------------------------------------------------------------ 05
NBS.append(dict(
    slug='05_data_pipeline', title='05 · Data: Dataset, DataLoader, padding, masks and packing', deck='pytorch/05-data/', deck_name='Data pipelines for LLMs', minutes=30,
    goals='a token-window `Dataset`, a collate function that pads variable-length examples and builds labels with `ignore_index=-100`, and sequence packing that removes padding waste.',
    setup=TORCH + r'''
from torch.utils.data import Dataset, DataLoader
PAD = 0
DOCS = [[5, 6, 7], [8, 9], [10, 11, 12, 13, 14], [15], [16, 17, 18, 19]]   # token ids of five short documents
''',
    tasks=[
        dict(fn='WindowDataset', title='Fixed-length windows over a token stream', md=r'''
            Pretraining usually concatenates documents into one long stream and cuts windows of `T + 1` tokens: inputs are the first T, targets the last T (shifted by one). Implement `__len__` and `__getitem__(i)` returning `(x, y)` long tensors for non-overlapping windows.''',
             starter=r'''
            class WindowDataset(Dataset):
                def __init__(self, tokens, T):
                    self.tokens, self.T = torch.as_tensor(tokens), T
                def __len__(self):
                    # TODO
                    raise NotImplementedError
                def __getitem__(self, i):
                    # TODO
                    raise NotImplementedError''',
             test=r'''
            def _test_WindowDataset(cls):
                ds = cls(list(range(100, 121)), 4)
                assert len(ds) == 5, "21 tokens → 5 full windows of 4 inputs + 1 target"
                x, y = ds[1]
                assert x.tolist() == [104, 105, 106, 107] and y.tolist() == [105, 106, 107, 108]
                xb, yb = next(iter(DataLoader(ds, batch_size=2)))
                assert xb.shape == (2, 4) and xb.dtype == torch.long''',
             solution=r'''
            class WindowDataset_solution(Dataset):
                def __init__(self, tokens, T):
                    self.tokens, self.T = torch.as_tensor(tokens), T
                def __len__(self):
                    return (len(self.tokens) - 1) // self.T
                def __getitem__(self, i):
                    s = i * self.T
                    chunk = self.tokens[s:s + self.T + 1]
                    return chunk[:-1].long(), chunk[1:].long()'''),
        dict(fn='pad_collate', title='Pad, mask and label', md=r'''
            For fine-tuning, each example is its own sequence. Write `pad_collate(batch)` for a list of 1-D token lists: right-pad inputs with `PAD`, build `attention_mask` (1 for real tokens), and `labels` = next tokens with **−100** at padding and at the last real position, so `F.cross_entropy(…, ignore_index=-100)` (the default) skips them.
            Return `(input_ids, attention_mask, labels)`, all shape (B, L) with L the longest length.''',
             starter=r'''
            def pad_collate(batch):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_pad_collate(f):
                ids, mask, lab = f([[5, 6, 7], [8, 9]])
                assert ids.tolist() == [[5, 6, 7], [8, 9, 0]]
                assert mask.tolist() == [[1, 1, 1], [1, 1, 0]]
                assert lab.tolist() == [[6, 7, -100], [9, -100, -100]]
                logits = torch.randn(2, 3, 20)
                full = F.cross_entropy(logits.view(-1, 20), lab.view(-1))
                keep = lab.view(-1) != -100
                assert torch.allclose(full, F.cross_entropy(logits.view(-1, 20)[keep], lab.view(-1)[keep])), "-100 positions are ignored"''',
             solution=r'''
            def pad_collate_solution(batch):
                L = max(len(b) for b in batch)
                ids = torch.full((len(batch), L), PAD, dtype=torch.long)
                mask = torch.zeros(len(batch), L, dtype=torch.long)
                lab = torch.full((len(batch), L), -100, dtype=torch.long)
                for i, b in enumerate(batch):
                    t = torch.tensor(b); ids[i, :len(b)] = t; mask[i, :len(b)] = 1; lab[i, :len(b) - 1] = t[1:]
                return ids, mask, lab'''),
        dict(fn='pack', title='Pack documents into fixed rows', md=r'''
            Padding wastes compute. **Packing** concatenates documents (each followed by an end-of-text id `eot`) into rows of exactly `L` tokens. Return `(rows, doc_ids)`: a (n_rows, L) tensor with the stream cut into rows (drop the incomplete tail) and a same-shaped tensor saying which document each token came from (so attention can be restricted to the same document).''',
             starter=r'''
            def pack(docs, L, eot=1):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_pack(f):
                rows, did = f(DOCS, 6)
                assert rows.shape == did.shape and rows.shape[1] == 6
                stream = sum(([*d, 1] for d in DOCS), [])
                assert rows.flatten().tolist() == stream[:rows.numel()], "rows are the concatenated stream"
                assert rows.shape[0] == len(stream) // 6
                assert did[0].tolist() == [0, 0, 0, 0, 1, 1], "first row: doc 0 (3 tokens + eot) then doc 1"''',
             solution=r'''
            def pack_solution(docs, L, eot=1):
                stream, owner = [], []
                for i, d in enumerate(docs):
                    stream += [*d, eot]; owner += [i] * (len(d) + 1)
                n = len(stream) // L
                return torch.tensor(stream[:n * L]).view(n, L), torch.tensor(owner[:n * L]).view(n, L)'''),
    ],
    explore_md=r'''
        **How much does padding waste?** Compare the share of padding tokens when batching documents of varied lengths with padding vs packing, and build the block-diagonal mask that keeps packed documents from attending to each other.''',
    explore=r'''
        g = torch.Generator().manual_seed(0); lengths = torch.randint(20, 400, (64,), generator=g).tolist()
        for bs in [8, 32]:
            pad = sum(bs * max(lengths[i:i + bs]) - sum(lengths[i:i + bs]) for i in range(0, 64, bs)); total = sum(lengths) + pad
            print(f"batch {bs:2d}: {pad / total:.0%} of computed tokens are padding")
        rows, did = pack_solution(DOCS, 6)
        same = did[0][:, None] == did[0][None, :]; causal = torch.tril(torch.ones(6, 6, dtype=torch.bool))
        print("document-causal mask for row 0:\n", (same & causal).int())''',
    takeaways=r'''
        * `Dataset` returns one example; `DataLoader` batches, shuffles and (with workers) prefetches; `collate_fn` controls how examples become a batch.
        * Labels use −100 (cross-entropy's default `ignore_index`) for padding and prompt tokens you don't want to train on.
        * Packing removes padding waste; a document mask (or per-document position ids) keeps packed documents independent.''',
))

# ------------------------------------------------------------------ 06
NBS.append(dict(
    slug='06_mixed_precision', title='06 · Mixed precision: autocast, BF16 and GradScaler', deck='pytorch/06-mixed-precision/', deck_name='Mixed precision in PyTorch', minutes=25,
    goals='what `torch.autocast` changes (matmuls in low precision, reductions kept in FP32), why accumulating in BF16 loses information, and how `GradScaler` scales the loss, skips steps with inf/NaN gradients and adapts its scale.',
    setup=TORCH,
    tasks=[
        dict(fn='autocast_dtypes', title='What runs in which dtype?', md=r'''
            Inside `torch.autocast("cpu", dtype=torch.bfloat16)`, return a dict of the output dtypes of: `"matmul"` (`a @ b`), `"linear"` (an `nn.Linear` on FP32 input), `"sum"` (`a.sum()`), `"softmax"` (`F.softmax(a, -1)`), and `"param"` (the Linear's weight dtype). Run the code; don't guess.''',
             starter=r'''
            def autocast_dtypes():
                a, b = torch.randn(8, 8), torch.randn(8, 8); lin = nn.Linear(8, 8)
                # TODO: with torch.autocast("cpu", dtype=torch.bfloat16): ...
                raise NotImplementedError''',
             test=r'''
            def _test_autocast_dtypes(f):
                d = f()
                assert d["matmul"] == torch.bfloat16 and d["linear"] == torch.bfloat16, "matmuls run in BF16"
                assert d["sum"] == torch.float32 and d["softmax"] == torch.float32, "reductions and softmax stay in FP32"
                assert d["param"] == torch.float32, "autocast never changes the stored (master) weights"''',
             solution=r'''
            def autocast_dtypes_solution():
                a, b = torch.randn(8, 8), torch.randn(8, 8); lin = nn.Linear(8, 8)
                with torch.autocast("cpu", dtype=torch.bfloat16):
                    return {"matmul": (a @ b).dtype, "linear": lin(a).dtype, "sum": a.sum().dtype, "softmax": F.softmax(a, -1).dtype, "param": lin.weight.dtype}'''),
        dict(fn='bf16_accumulate', title='Why accumulators stay in FP32', md=r'''
            Add `x = 1e-3` to a running total 10,000 times, once with the total stored in BF16 and once in FP32. Return `(bf16_total, fp32_total)` as Python floats. BF16 has 8 bits of precision: once the total is large, adding 0.001 rounds away.''',
             starter=r'''
            def bf16_accumulate(n=10_000, x=1e-3):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_bf16_accumulate(f):
                b, s = f()
                assert abs(s - 10.0) < 1e-2, "FP32 total ≈ 10"
                assert b < 5.0, f"the BF16 total should stall far below 10, got {b}"''',
             solution=r'''
            def bf16_accumulate_solution(n=10_000, x=1e-3):
                b = torch.zeros((), dtype=torch.bfloat16); s = torch.zeros((), dtype=torch.float32)
                xb, xs = torch.tensor(x, dtype=torch.bfloat16), torch.tensor(x, dtype=torch.float32)
                for _ in range(n):
                    b = b + xb; s = s + xs
                return b.item(), s.item()'''),
        dict(fn='scaler_steps', title='GradScaler skips bad steps and adapts', md=r'''
            Run 6 steps of the standard pattern on a tiny model with `scaler = torch.amp.GradScaler("cpu", init_scale=2.**16, growth_interval=2)`: `scaler.scale(loss).backward(); scaler.step(opt); scaler.update()`. On step 2 (0-indexed), multiply the loss by `float("inf")` to simulate an overflow.
            Return the list of `scaler.get_scale()` values after each `update()` and whether the weights changed on the overflow step.''',
             starter=r'''
            def scaler_steps():
                torch.manual_seed(0); m = nn.Linear(4, 1); opt = torch.optim.SGD(m.parameters(), lr=0.1)
                scaler = torch.amp.GradScaler("cpu", init_scale=2.**16, growth_interval=2)
                scales, changed_on_overflow = [], None
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_scaler_steps(f):
                scales, changed = f()
                assert scales[2] == scales[1] / 2, "an overflow halves the scale (backoff_factor 0.5)"
                assert changed is False, "the optimizer step is skipped when gradients contain inf/NaN"
                assert scales[-1] > scales[2], "after growth_interval clean steps the scale doubles again"''',
             solution=r'''
            def scaler_steps_solution():
                torch.manual_seed(0); m = nn.Linear(4, 1); opt = torch.optim.SGD(m.parameters(), lr=0.1)
                scaler = torch.amp.GradScaler("cpu", init_scale=2.**16, growth_interval=2)
                scales, changed = [], None
                for step in range(6):
                    opt.zero_grad(); loss = m(torch.randn(8, 4)).pow(2).mean()
                    if step == 2: loss = loss * float("inf")
                    before = m.weight.detach().clone()
                    scaler.scale(loss).backward(); scaler.step(opt); scaler.update()
                    if step == 2: changed = not torch.equal(before, m.weight)
                    scales.append(scaler.get_scale())
                return scales, changed'''),
    ],
    explore_md=r'''
        **GradScaler defaults** (PyTorch 2.14.1): initial scale 2¹⁶ = 65,536, growth factor 2, backoff factor 0.5, growth interval 2,000 steps. With BF16 you usually don't need a scaler at all; it exists for FP16.''',
    explore=r'''
        s = torch.amp.GradScaler("cpu"); print("defaults:", s.get_scale(), s.get_growth_factor(), s.get_backoff_factor(), s.get_growth_interval())
        print("autocast default dtype on cpu:", torch.get_autocast_dtype("cpu"), "| on cuda:", torch.get_autocast_dtype("cuda"))
        print("BF16 vs FP32 accumulation:", bf16_accumulate_solution())''',
    takeaways=r'''
        * `torch.autocast` runs matmuls and linear layers in BF16/FP16 but keeps reductions, softmax and the weights themselves in FP32.
        * Long accumulations must stay in FP32; BF16's 8-bit precision silently drops small increments.
        * `GradScaler` (for FP16) multiplies the loss, skips steps whose gradients overflow, halves the scale on overflow and doubles it after a run of clean steps.''',
))

# ------------------------------------------------------------------ 07
NBS.append(dict(
    slug='07_compile_and_sdpa', title='07 · torch.compile and fused attention', deck='pytorch/07-performance/', deck_name='Performance: compile, SDPA, memory', minutes=30,
    goals='compiling a function with `torch.compile`, checking it matches eager mode, finding graph breaks with `torch._dynamo.explain`, and measuring how attention memory grows with sequence length.',
    setup=TORCH + r'''
import time
def gelu_mlp(x, w1, w2):
    return F.gelu(x @ w1) @ w2
''',
    tasks=[
        dict(fn='compiled_matches', title='Compile and compare with eager', md=r'''
            Compile `gelu_mlp` with `torch.compile` and return the maximum absolute difference between compiled and eager outputs on random inputs (x: 64×128, w1: 128×512, w2: 512×128). The first call compiles (slow); later calls reuse the compiled code.''',
             starter=r'''
            def compiled_matches():
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_compiled_matches(f):
                d = f()
                assert d < 1e-4, f"compiled and eager outputs should match closely, max diff {d}"''',
             solution=r'''
            def compiled_matches_solution():
                torch.manual_seed(0); x, w1, w2 = torch.randn(64, 128), torch.randn(128, 512) / 11, torch.randn(512, 128) / 22
                cf = torch.compile(gelu_mlp)
                return (cf(x, w1, w2) - gelu_mlp(x, w1, w2)).abs().max().item()'''),
        dict(fn='count_graph_breaks', title='Find graph breaks', md=r'''
            Python control flow on tensor **values** (like `if x.sum() > 0:`) or calls TorchDynamo cannot trace split the program into several graphs. Use `torch._dynamo.explain(fn)(*args)` and return `(graph_count, graph_break_count)` for `fn_branchy` defined below versus `fn_clean`.''',
             starter=r'''
            def fn_branchy(x):
                y = x * 2
                if y.sum() > 0:          # data-dependent branch
                    y = y + 1
                print("side effect")     # also a break
                return y.relu()

            def fn_clean(x):
                return (x * 2 + 1).relu()

            def count_graph_breaks():
                # TODO: torch._dynamo.explain(fn)(torch.randn(8)) has .graph_count and .graph_break_count
                raise NotImplementedError''',
             test=r'''
            def _test_count_graph_breaks(f):
                (gb, bb), (gc, bc) = f()
                assert bc == 0 and gc == 1, "the clean function is one graph"
                assert bb >= 1 and gb >= 2, "the branchy function breaks into several graphs"''',
             solution=r'''
            def count_graph_breaks_solution():
                out = []
                for fn in (fn_branchy, fn_clean):
                    torch._dynamo.reset()
                    e = torch._dynamo.explain(fn)(torch.randn(8))
                    out.append((e.graph_count, e.graph_break_count))
                return tuple(out)'''),
        dict(fn='attention_bytes', title='Memory of naive vs fused attention', md=r'''
            Naive attention materialises the (B, H, T, T) score matrix; fused kernels (FlashAttention) never do. Return a dict for given B, H, T, D, bytes-per-element: `"scores"` = bytes of one score matrix, `"qkv"` = bytes of q, k and v together.
            At long T, the scores dwarf q, k, v, which is the memory FlashAttention saves.''',
             starter=r'''
            def attention_bytes(B, H, T, D, bytes_per=2):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_attention_bytes(f):
                d = f(1, 32, 8192, 128)
                assert d["scores"] == 32 * 8192 * 8192 * 2 and d["qkv"] == 3 * 32 * 8192 * 128 * 2
                assert d["scores"] / d["qkv"] > 20''',
             solution=r'''
            def attention_bytes_solution(B, H, T, D, bytes_per=2):
                return {"scores": B * H * T * T * bytes_per, "qkv": 3 * B * H * T * D * bytes_per}'''),
    ],
    explore_md=r'''
        **Time it (CPU, rough).** Speedups on a laptop CPU are modest and noisy; on GPUs `torch.compile` fuses elementwise ops into Triton kernels and SDPA picks FlashAttention. The PyTorch 2 paper reports 2.27× inference and 1.41× training geometric-mean speedups on an A100 across 180+ models.''',
    explore=r'''
        torch.manual_seed(0); x, w1, w2 = torch.randn(256, 512), torch.randn(512, 2048) / 22, torch.randn(2048, 512) / 45
        cf = torch.compile(gelu_mlp); cf(x, w1, w2)
        def bench(fn, n=20):
            t = time.perf_counter()
            for _ in range(n): fn(x, w1, w2)
            return (time.perf_counter() - t) / n * 1e3
        print(f"eager {bench(gelu_mlp):.2f} ms   compiled {bench(cf):.2f} ms   (CPU; numbers vary)")
        for T in [1024, 8192, 131072]:
            d = attention_bytes_solution(1, 32, T, 128); print(f"T={T:6d}: score matrix {d['scores'] / 2**30:8.2f} GiB vs q,k,v {d['qkv'] / 2**30:6.3f} GiB")''',
    takeaways=r'''
        * `torch.compile` = TorchDynamo (captures Python bytecode into graphs) + AOTAutograd (adds the backward) + TorchInductor (generates fused Triton/C++ code). The default backend is "inductor".
        * Graph breaks (data-dependent Python control flow, unsupported calls) split the graph and cost speed; find them with `torch._dynamo.explain`.
        * `F.scaled_dot_product_attention` avoids materialising the T×T score matrix when a fused backend is available.''',
))

# ------------------------------------------------------------------ 08
NBS.append(dict(
    slug='08_ddp_torchrun', title='08 · Distributed: all_reduce and DDP with torchrun', deck='pytorch/08-distributed/', deck_name='Distributed training in PyTorch', minutes=35,
    goals='launching two CPU processes with `torchrun` and the gloo backend, averaging gradients by hand with `dist.all_reduce`, and checking that `DistributedDataParallel` gives exactly the same result.',
    setup=TORCH + r'''
import subprocess, sys, textwrap, inspect, os, json, tempfile
def run_torchrun(script, nproc=2):
    """Write `script` to a temp file and run it with torchrun on CPU (gloo). Returns rank 0's printed JSON."""
    d = tempfile.mkdtemp(); path = os.path.join(d, "job.py"); open(path, "w").write(textwrap.dedent(script))
    r = subprocess.run([sys.executable, "-m", "torch.distributed.run", "--nproc_per_node", str(nproc), "--master_port", "29511", path], capture_output=True, text=True, timeout=300)
    lines = [l for l in r.stdout.splitlines() if l.startswith("{")]
    if not lines: raise RuntimeError(r.stderr[-2000:])
    return json.loads(lines[0])
COMMON = """
import json, torch, torch.nn as nn, torch.nn.functional as F, torch.distributed as dist
dist.init_process_group("gloo")
rank, world = dist.get_rank(), dist.get_world_size()
torch.manual_seed(0); model = nn.Linear(4, 1)
g = torch.Generator().manual_seed(1); X, Y = torch.randn(16, 4, generator=g), torch.randn(16, 1, generator=g)
xs, ys = X.chunk(world)[rank], Y.chunk(world)[rank]
"""
''',
    tasks=[
        dict(fn='average_gradients_src', title='Average gradients with all_reduce', md=r'''
            Write the body of `average_gradients(model, world)` as source code (a string) that, for every parameter, sums `p.grad` across ranks with `dist.all_reduce(p.grad, op=dist.ReduceOp.SUM)` and divides by `world`.
            The test runs it under `torchrun` with 2 processes, each holding half the batch, and checks the result equals the full-batch gradient.''',
             starter=r'''
            def average_gradients_src():
                return """
            def average_gradients(model, world):
                # TODO
                raise NotImplementedError
            """''',
             test=r'''
            def _test_average_gradients_src(f):
                src = f()
                if "NotImplementedError" in src: raise NotImplementedError
                out = run_torchrun(COMMON + textwrap.dedent(src) + """
            F.mse_loss(model(xs), ys).backward()
            average_gradients(model, world)
            ref = nn.Linear(4, 1); torch.manual_seed(0); ref = nn.Linear(4, 1); F.mse_loss(ref(X), Y).backward()
            ok = all(torch.allclose(p.grad, q.grad, atol=1e-6) for p, q in zip(model.parameters(), ref.parameters()))
            if rank == 0: print(json.dumps({"ok": ok}))
            dist.destroy_process_group()
            """)
                assert out["ok"], "averaged gradients must equal the full-batch gradient"''',
             solution=r'''
            def average_gradients_src_solution():
                return """
            def average_gradients(model, world):
                for p in model.parameters():
                    dist.all_reduce(p.grad, op=dist.ReduceOp.SUM)
                    p.grad /= world
            """'''),
        dict(fn='ddp_matches_src', title='DistributedDataParallel does it for you', md=r'''
            Now wrap the model: `ddp = torch.nn.parallel.DistributedDataParallel(model)`, run forward/backward on the local shard, and report whether every parameter's gradient equals the full-batch gradient. Return the script body as a string that prints `{"ok": …}` on rank 0.''',
             starter=r'''
            def ddp_matches_src():
                return """
            raise NotImplementedError
            """''',
             test=r'''
            def _test_ddp_matches_src(f):
                src = f()
                if "NotImplementedError" in src: raise NotImplementedError
                out = run_torchrun(COMMON + textwrap.dedent(src))
                assert out["ok"], "DDP gradients must equal the full-batch gradient"''',
             solution=r'''
            def ddp_matches_src_solution():
                return """
            ddp = torch.nn.parallel.DistributedDataParallel(model)
            F.mse_loss(ddp(xs), ys).backward()
            torch.manual_seed(0); ref = nn.Linear(4, 1); F.mse_loss(ref(X), Y).backward()
            ok = all(torch.allclose(p.grad, q.grad, atol=1e-6) for p, q in zip(model.parameters(), ref.parameters()))
            if rank == 0: print(json.dumps({"ok": ok}))
            dist.destroy_process_group()
            """'''),
    ],
    explore_md=r'''
        **What torchrun sets up.** Each process gets environment variables (`RANK`, `LOCAL_RANK`, `WORLD_SIZE`, `MASTER_ADDR`, `MASTER_PORT`) that `init_process_group` reads. On GPUs you would use the "nccl" backend and set the device from `LOCAL_RANK`; FSDP2 replaces DDP with `fully_shard(layer)` on each block and then on the root module.''',
    explore=r'''
        out = run_torchrun("""
        import os, json, torch.distributed as dist
        dist.init_process_group("gloo")
        env = {k: os.environ[k] for k in ["RANK", "LOCAL_RANK", "WORLD_SIZE", "MASTER_ADDR", "MASTER_PORT"]}
        if dist.get_rank() == 0: print(json.dumps(env))
        dist.destroy_process_group()
        """)
        print("rank 0 environment:", out)''',
    takeaways=r'''
        * `torchrun` launches one process per device and sets `RANK`, `LOCAL_RANK` and `WORLD_SIZE`; `init_process_group("nccl" | "gloo")` connects them.
        * Data parallelism = each rank computes gradients on its shard, then all-reduce averages them; DDP does this in buckets (25 MB by default) overlapped with backward.
        * FSDP2 (`fully_shard`) applies the same idea with sharded parameters: all-gather before use, reduce-scatter gradients after.''',
))

# ------------------------------------------------------------------ 09
NBS.append(dict(
    slug='09_tiny_gpt', title='09 · Train a tiny GPT end to end', deck='pytorch/09-putting-it-together/', deck_name='Putting it together: a tiny GPT', minutes=40,
    goals='a nanoGPT-style character model built from the earlier pieces (embedding, pre-norm blocks with SDPA, tied output head), trained with AdamW and a warmup + cosine schedule on CPU, then sampled.',
    setup=TORCH + r'''
import math
TEXT = ("the quick brown fox jumps over the lazy dog. " * 3 + "a stitch in time saves nine. " * 3 + "all that glitters is not gold. " * 3) * 8
chars = sorted(set(TEXT)); V = len(chars); stoi = {c: i for i, c in enumerate(chars)}
data = torch.tensor([stoi[c] for c in TEXT]); n = int(0.9 * len(data)); train_data, val_data = data[:n], data[n:]
def get_batch(split, B=16, T=32, g=None):
    d = train_data if split == "train" else val_data
    ix = torch.randint(len(d) - T - 1, (B,), generator=g)
    return torch.stack([d[i:i + T] for i in ix]), torch.stack([d[i + 1:i + T + 1] for i in ix])

class Attn(nn.Module):
    def __init__(self, C, H):
        super().__init__(); self.H = H; self.qkv = nn.Linear(C, 3 * C, bias=False); self.proj = nn.Linear(C, C, bias=False)
    def forward(self, x):
        B, T, C = x.shape; q, k, v = self.qkv(x).split(C, 2)
        q, k, v = (t.view(B, T, self.H, C // self.H).transpose(1, 2) for t in (q, k, v))
        return self.proj(F.scaled_dot_product_attention(q, k, v, is_causal=True).transpose(1, 2).reshape(B, T, C))
class Blk(nn.Module):
    def __init__(self, C, H):
        super().__init__(); self.n1, self.a, self.n2 = nn.RMSNorm(C), Attn(C, H), nn.RMSNorm(C)
        self.m = nn.Sequential(nn.Linear(C, 4 * C, bias=False), nn.GELU(), nn.Linear(4 * C, C, bias=False))
    def forward(self, x):
        x = x + self.a(self.n1(x)); return x + self.m(self.n2(x))
''',
    tasks=[
        dict(fn='TinyGPT', title='The model', md=r'''
            Token embedding (V × C) + learned position embedding (T_max × C), `L` blocks (`Blk` above), a final `nn.RMSNorm`, and an output head **tied** to the token embedding (`logits = h @ wte.weight.T`). `forward(idx, targets=None)` returns `(logits, loss)` with cross-entropy loss when targets are given.
            Initialise both embeddings with `nn.init.normal_(…, std=0.02)` as GPT-2 does: `nn.Embedding` defaults to std 1, which with a tied head makes the initial logits huge (loss ≈ 46 instead of ≈ ln V).''',
             starter=r'''
            class TinyGPT(nn.Module):
                def __init__(self, V, C=64, H=4, L=2, T_max=64):
                    super().__init__()
                    # TODO
                    raise NotImplementedError
                def forward(self, idx, targets=None):
                    # TODO
                    raise NotImplementedError''',
             test=r'''
            def _test_TinyGPT(cls):
                torch.manual_seed(0); m = cls(V)
                x, y = get_batch("train", g=torch.Generator().manual_seed(0))
                logits, loss = m(x, y)
                assert logits.shape == (16, 32, V)
                assert abs(loss.item() - math.log(V)) < 0.6, f"an untrained model's loss should be near ln V = {math.log(V):.2f}"
                n_tied = sum(p.numel() for p in m.parameters())
                assert n_tied == V * 64 + 64 * 64 + 2 * (12 * 64 * 64 + 2 * 64) + 64, f"expected {V * 64 + 64 * 64 + 2 * (12 * 64 * 64 + 128) + 64} parameters with a tied head, got {n_tied}"''',
             solution=r'''
            class TinyGPT_solution(nn.Module):
                def __init__(self, V, C=64, H=4, L=2, T_max=64):
                    super().__init__()
                    self.wte, self.wpe = nn.Embedding(V, C), nn.Embedding(T_max, C)
                    self.blocks = nn.ModuleList(Blk(C, H) for _ in range(L)); self.nf = nn.RMSNorm(C)
                    nn.init.normal_(self.wte.weight, std=0.02); nn.init.normal_(self.wpe.weight, std=0.02)
                def forward(self, idx, targets=None):
                    B, T = idx.shape
                    x = self.wte(idx) + self.wpe(torch.arange(T))
                    for b in self.blocks: x = b(x)
                    logits = self.nf(x) @ self.wte.weight.T
                    loss = None if targets is None else F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1))
                    return logits, loss'''),
        dict(fn='fit', title='Train it', md=r'''
            Train for `steps` steps with AdamW (lr 3e-3, weight decay 0.1 on 2-D weights only), linear warmup 20 steps then cosine to 10%, gradient clipping at 1.0. Return `(train_losses, val_loss)` where val_loss is the mean over 10 validation batches under `torch.no_grad()` and `model.eval()`.''',
             starter=r'''
            def fit(model, steps=300, seed=0):
                g = torch.Generator().manual_seed(seed)
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_fit(f):
                torch.manual_seed(0); M = globals().get("TinyGPT_solution") or TinyGPT
                tl, vl = f(M(V), steps=300)
                assert tl[-1] < 0.5 * tl[0], "training loss should drop by more than half"
                assert vl < 1.0, f"validation loss should fall below 1.0 nats/char on this repetitive text, got {vl:.2f}"''',
             solution=r'''
            def fit_solution(model, steps=300, seed=0):
                g = torch.Generator().manual_seed(seed)
                decay = [p for p in model.parameters() if p.dim() >= 2]; other = [p for p in model.parameters() if p.dim() < 2]
                opt = torch.optim.AdamW([{"params": decay, "weight_decay": 0.1}, {"params": other, "weight_decay": 0.0}], lr=3e-3, betas=(0.9, 0.95))
                sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: (s + 1) / 20 if s < 20 else 0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * min(1, (s - 20) / (steps - 20)))))
                losses = []
                model.train()
                for _ in range(steps):
                    x, y = get_batch("train", g=g); _, loss = model(x, y)
                    opt.zero_grad(set_to_none=True); loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); sched.step()
                    losses.append(loss.item())
                model.eval()
                with torch.no_grad():
                    vl = sum(model(*get_batch("val", g=g))[1].item() for _ in range(10)) / 10
                return losses, vl'''),
    ],
    explore_md=r'''
        **Sample from it.** Feed a prompt, take the last position's logits, divide by a temperature, sample, append, repeat.''',
    explore=r'''
        torch.manual_seed(0); model = TinyGPT_solution(V); tl, vl = fit_solution(model, 300)
        print(f"train loss {tl[0]:.2f} → {tl[-1]:.2f}, val loss {vl:.3f} nats/char (uniform would be {math.log(V):.2f})")
        idx = torch.tensor([[stoi[c] for c in "the "]]); g = torch.Generator().manual_seed(1)
        with torch.no_grad():
            for _ in range(80):
                logits, _ = model(idx[:, -64:]); p = F.softmax(logits[0, -1] / 0.8, -1)
                idx = torch.cat([idx, torch.multinomial(p, 1, generator=g)[None]], 1)
        print("".join(chars[i] for i in idx[0].tolist()))''',
    takeaways=r'''
        * A GPT is embeddings + a stack of pre-norm blocks + a final norm + an output head (often tied to the embedding).
        * The training loop is the same as for any model: AdamW with decay on matrices, warmup + cosine, clipping, `zero_grad` each step.
        * Scale this exact code up (more layers, data, GPUs with FSDP and `torch.compile`) and you have nanoGPT.''',
))
