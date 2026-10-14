"""Distributed training & reliability exercise notebooks (NumPy simulations of many GPUs)."""

BASE = r'''
def softmax(x, axis=-1):
    x = x - x.max(axis=axis, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=axis, keepdims=True)
'''

NBS = []

# ------------------------------------------------------------------ 01
NBS.append(dict(
    slug='01_ring_allreduce', title='01 · Ring all-reduce from scratch', deck='distributed/02-data-parallelism/', deck_name='Data parallelism', minutes=35,
    goals='the ring all-reduce used for data-parallel gradients: a reduce-scatter phase and an all-gather phase on N simulated GPUs, with the bytes each GPU sends.',
    setup=BASE + r'''
def make_grads(N, L, seed=0):
    """N ranks, each with its own gradient vector of length L (L divisible by N)."""
    r = np.random.default_rng(seed)
    return [r.normal(size=L) for _ in range(N)]
''',
    tasks=[
        dict(fn='reduce_scatter_ring', title='Reduce-scatter around a ring', md=r'''
            Split every rank's vector into N chunks. In step s = 0 … N−2, rank r sends chunk (r − s) mod N to rank (r + 1) mod N, which **adds** it to its own copy of that chunk. All sends in a step happen at the same time, so use the values from before the step.
            After N − 1 steps, rank r holds the **fully summed** chunk (r + 1) mod N.

            Return `(chunks, sent)`: `chunks[r]` is rank r's list of N chunks after the phase, and `sent[r]` is the number of elements rank r sent.''',
             starter=r'''
            def reduce_scatter_ring(vectors):
                N = len(vectors)
                chunks = [list(np.split(v.astype(float).copy(), N)) for v in vectors]
                sent = [0] * N
                # TODO: N-1 steps; in each, every rank r sends chunk (r - s) % N to rank (r + 1) % N, which adds it
                raise NotImplementedError''',
             test=r'''
            def _test_reduce_scatter_ring(f):
                for N, L in [(2, 6), (4, 12), (5, 20)]:
                    g = make_grads(N, L, N); total = np.split(sum(g), N)
                    chunks, sent = f(g)
                    for r in range(N):
                        k = (r + 1) % N
                        assert np.allclose(chunks[r][k], total[k]), f"N={N}: rank {r} should hold the full sum of chunk {k}"
                    assert all(s == (N - 1) * L // N for s in sent), f"N={N}: each rank sends (N-1)·L/N elements, got {sent}"''',
             solution=r'''
            def reduce_scatter_ring_solution(vectors):
                N = len(vectors)
                chunks = [list(np.split(v.astype(float).copy(), N)) for v in vectors]
                sent = [0] * N
                for s in range(N - 1):
                    msgs = [((r + 1) % N, (r - s) % N, chunks[r][(r - s) % N].copy()) for r in range(N)]
                    for r, (dst, k, data) in enumerate(msgs):
                        chunks[dst][k] = chunks[dst][k] + data
                        sent[r] += data.size
                return chunks, sent'''),
        dict(fn='all_gather_ring', title='All-gather around the ring', md=r'''
            Now spread the summed chunks. Rank r starts owning chunk (r + 1) mod N. In step s = 0 … N−2, rank r sends chunk (r + 1 − s) mod N to rank (r + 1) mod N, which **overwrites** its copy.
            After N − 1 steps every rank holds every summed chunk. Return `(chunks, sent)` as before.''',
             starter=r'''
            def all_gather_ring(chunks):
                N = len(chunks)
                chunks = [[c.copy() for c in row] for row in chunks]
                sent = [0] * N
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_all_gather_ring(f):
                N, L = 4, 12
                g = make_grads(N, L, 7); total = np.split(sum(g), N)
                rs, _ = reduce_scatter_ring_solution(g) if 'reduce_scatter_ring_solution' in globals() else _rs_ref(g)
                chunks, sent = f(rs)
                for r in range(N):
                    assert np.allclose(np.concatenate(chunks[r]), sum(g)), f"rank {r} must end with the full summed vector"
                assert all(s == (N - 1) * L // N for s in sent)

            def _rs_ref(vectors):
                N = len(vectors); ch = [list(np.split(v.astype(float).copy(), N)) for v in vectors]
                for s in range(N - 1):
                    msgs = [((r + 1) % N, (r - s) % N, ch[r][(r - s) % N].copy()) for r in range(N)]
                    for dst, k, d in msgs: ch[dst][k] = ch[dst][k] + d
                return ch, None''',
             solution=r'''
            def all_gather_ring_solution(chunks):
                N = len(chunks)
                chunks = [[c.copy() for c in row] for row in chunks]
                sent = [0] * N
                for s in range(N - 1):
                    msgs = [((r + 1) % N, (r + 1 - s) % N, chunks[r][(r + 1 - s) % N].copy()) for r in range(N)]
                    for r, (dst, k, data) in enumerate(msgs):
                        chunks[dst][k] = data
                        sent[r] += data.size
                return chunks, sent'''),
        dict(fn='ring_allreduce', title='All-reduce = reduce-scatter + all-gather', md=r'''
            Compose the two phases. Return `(results, sent)`: `results[r]` is the full summed vector on rank r, and `sent[r]` the total elements rank r sent.
            Each rank sends $2\frac{N-1}{N}L$ elements, which is **almost independent of N**. That is why ring all-reduce scales to many GPUs in bandwidth terms.''',
             starter=r'''
            def ring_allreduce(vectors):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_ring_allreduce(f):
                for N in [2, 3, 8]:
                    g = make_grads(N, 8 * N, N + 1)
                    res, sent = f(g)
                    assert all(np.allclose(x, sum(g)) for x in res), f"N={N}: every rank needs the full sum"
                    assert all(s == 2 * (N - 1) * 8 for s in sent), f"N={N}: expected 2(N-1)/N·L = {2 * (N - 1) * 8}, got {sent}"''',
             solution=r'''
            def ring_allreduce_solution(vectors):
                ch, s1 = reduce_scatter_ring_solution(vectors)
                ch, s2 = all_gather_ring_solution(ch)
                return [np.concatenate(c) for c in ch], [a + b for a, b in zip(s1, s2)]'''),
    ],
    explore_md=r'''
        **Ring vs "send everything to rank 0".** With a simple cost model, time = number of sequential steps × α (latency per message) + bytes on the busiest link ÷ bandwidth. Ring: 2(N−1) steps, 2(N−1)/N·S bytes per rank. Naive gather-and-broadcast through rank 0: rank 0 receives (N−1)·S and sends (N−1)·S. Bandwidth wins for ring; latency grows with N, which is where tree algorithms help.''',
    explore=r'''
        S, alpha, bw = 2e9, 10e-6, 50e9          # 1B BF16 gradients = 2 GB; 10 µs per message; 50 GB/s per link
        for N in [8, 64, 512, 4096]:
            ring = 2 * (N - 1) * alpha + 2 * (N - 1) / N * S / bw
            naive = 2 * (N - 1) * S / bw
            print(f"N={N:5d}: ring {ring * 1e3:8.1f} ms (latency part {2 * (N - 1) * alpha * 1e3:6.1f} ms)   naive via rank 0 {naive:8.1f} s")''',
    takeaways=r'''
        * Ring all-reduce = reduce-scatter (sum, each rank ends with one chunk) + all-gather (share the chunks).
        * Each GPU sends ≈ 2·S regardless of N, so the bandwidth cost of data parallelism stays flat as you add GPUs.
        * The latency term grows with N (2(N−1) sequential steps), so at large scale libraries switch to trees or hierarchical schemes; and frameworks overlap all-reduce with the backward pass in buckets (PyTorch DDP).''',
))

# ------------------------------------------------------------------ 02
NBS.append(dict(
    slug='02_zero_sharding', title='02 · ZeRO / FSDP: sharded data parallelism', deck='distributed/03-zero-fsdp/', deck_name='ZeRO and FSDP', minutes=45,
    goals='per-GPU memory for ZeRO stages 0–3, and a full ZeRO-3 training step (all-gather parameters, reduce-scatter gradients, sharded Adam) that matches single-GPU training exactly.',
    setup=BASE + r'''
r = np.random.default_rng(0)
D, N_RANK, B = 24, 4, 16                     # parameters, ranks, examples per rank
W_TRUE = r.normal(size=D)
DATA = [(r.normal(size=(B, D)), None) for _ in range(N_RANK)]
DATA = [(X, X @ W_TRUE + 0.1 * r.normal(size=B)) for X, _ in DATA]

def grad(W, X, y):
    """Gradient of mean squared error for a linear model."""
    return 2 * X.T @ (X @ W - y) / len(y)

def adam_update(w, g, m, v, t, lr=0.05, b1=0.9, b2=0.999, eps=1e-8):
    m = b1 * m + (1 - b1) * g; v = b2 * v + (1 - b2) * g * g
    mh, vh = m / (1 - b1 ** t), v / (1 - b2 ** t)
    return w - lr * mh / (np.sqrt(vh) + eps), m, v

def reference_training(steps):
    """One GPU on the full batch (the average of every rank's gradient)."""
    W = np.zeros(D); m = np.zeros(D); v = np.zeros(D)
    for t in range(1, steps + 1):
        g = np.mean([grad(W, X, y) for X, y in DATA], axis=0)
        W, m, v = adam_update(W, g, m, v, t)
    return W
''',
    tasks=[
        dict(fn='zero_bytes_per_gpu', title='Memory per GPU for each ZeRO stage', md=r'''
            Mixed-precision Adam keeps 16 bytes per parameter: BF16 weights (2) + BF16 gradients (2) + FP32 master weights, momentum and variance (12).
            * Stage 0 (plain data parallel): everything replicated: 16·P.
            * Stage 1: shard the optimizer state: 2P + 2P + 12P/N.
            * Stage 2: also shard gradients: 2P + 14P/N.
            * Stage 3 (≈ FSDP full sharding): shard everything: 16P/N.

            ZeRO reports "4x memory reduction" for stage 1, "8x" for stage 2 (as N grows) and reduction "linear with DP degree" for stage 3. Return bytes per GPU.''',
             starter=r'''
            def zero_bytes_per_gpu(P, N, stage):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_zero_bytes_per_gpu(f):
                P = 7e9
                assert np.isclose(f(P, 8, 0), 16 * P)
                assert np.isclose(f(P, 8, 3), 2 * P)
                assert np.isclose(f(P, 1e9, 0) / f(P, 1e9, 1), 4, rtol=1e-3), "stage 1 → 4× for large N"
                assert np.isclose(f(P, 1e9, 0) / f(P, 1e9, 2), 8, rtol=1e-3), "stage 2 → 8× for large N"
                assert np.isclose(f(P, 64, 0) / f(P, 64, 3), 64), "stage 3 → N×"''',
             solution=r'''
            def zero_bytes_per_gpu_solution(P, N, stage):
                return {0: 16 * P, 1: 4 * P + 12 * P / N, 2: 2 * P + 14 * P / N, 3: 16 * P / N}[stage]'''),
        dict(fn='zero3_train', title='A ZeRO-3 training loop', md=r'''
            Each of the N ranks stores only its **shard** of the weights and of Adam's m and v (use `np.array_split(…, N)`). One step:
            1. **All-gather** the shards into the full W (every rank needs it for its forward and backward pass).
            2. Each rank computes the gradient on its **own data** `DATA[r]`.
            3. **Reduce-scatter**: average the gradients across ranks, but each rank keeps only the slice matching its shard.
            4. Each rank runs Adam on its shard only.

            Return the final full W after `steps` steps. The test compares with `reference_training` (one GPU, full batch): they must match.''',
             starter=r'''
            def zero3_train(steps):
                W_shards = np.array_split(np.zeros(D), N_RANK)
                m_shards = [np.zeros_like(s) for s in W_shards]; v_shards = [np.zeros_like(s) for s in W_shards]
                # TODO: loop over steps: all-gather, local grads, reduce-scatter (average), sharded Adam
                raise NotImplementedError''',
             test=r'''
            def _test_zero3_train(f):
                W = f(25)
                assert W.shape == (D,)
                assert np.allclose(W, reference_training(25), atol=1e-10), "sharded training must match single-GPU training exactly"''',
             solution=r'''
            def zero3_train_solution(steps):
                W_shards = np.array_split(np.zeros(D), N_RANK)
                m_shards = [np.zeros_like(s) for s in W_shards]; v_shards = [np.zeros_like(s) for s in W_shards]
                bounds = np.cumsum([0] + [len(s) for s in W_shards])
                for t in range(1, steps + 1):
                    W = np.concatenate(W_shards)                                  # all-gather
                    local = [grad(W, X, y) for X, y in DATA]                       # each rank: own data
                    avg = np.mean(local, axis=0)                                   # reduce ...
                    for k in range(N_RANK):                                        # ... scatter + sharded Adam
                        g = avg[bounds[k]:bounds[k + 1]]
                        W_shards[k], m_shards[k], v_shards[k] = adam_update(W_shards[k], g, m_shards[k], v_shards[k], t)
                return np.concatenate(W_shards)'''),
    ],
    explore_md=r'''
        **Who fits where?** Per-GPU memory for model states (no activations) at several model sizes with 64 data-parallel GPUs of 80 GB. Stage 3 trades extra communication (an all-gather of parameters in both forward and backward) for memory.''',
    explore=r'''
        for P in [7e9, 70e9, 405e9]:
            row = '  '.join(f"stage {s}: {zero_bytes_per_gpu_solution(P, 64, s) / 1e9:7.1f} GB" for s in range(4))
            print(f"{P / 1e9:4.0f}B params, 64 GPUs → {row}")
        print("\nCommunication per step (elements per GPU, ring): stage 0–2 ≈ 2·P (all-reduce or reduce-scatter + all-gather), stage 3 ≈ 3·P (one more parameter all-gather in backward).")''',
    takeaways=r'''
        * Plain data parallelism replicates 16 bytes per parameter on every GPU; ZeRO shards optimizer state (stage 1), gradients (2) and parameters (3).
        * Sharding is exact: notebook results match single-GPU training bit for bit up to float error.
        * Stage 3 / FSDP adds parameter all-gathers (≈1.5× the communication of plain DP), so it is overlapped with compute via prefetching; Llama 3 uses FSDP with resharding disabled after the forward pass to avoid one extra all-gather.''',
))

# ------------------------------------------------------------------ 03
NBS.append(dict(
    slug='03_tensor_parallel_training', title='03 · Tensor-parallel MLP: forward and backward', deck='distributed/04-tensor-sequence-parallelism/', deck_name='Tensor and sequence parallelism', minutes=40,
    goals='a Megatron-style MLP split across t simulated GPUs (columns then rows), including the backward pass, with gradients that match the unsplit layer.',
    setup=BASE + r'''
r = np.random.default_rng(0)
T_, d, h = 6, 8, 16
X = r.normal(size=(T_, d)); A = r.normal(0, 0.3, (d, h)); Bw = r.normal(0, 0.3, (h, d)); dY = r.normal(size=(T_, d))

def mlp(X, A, B):
    return np.tanh(X @ A) @ B

def mlp_grads(X, A, B, dY):
    """Reference gradients of sum(Y * dY) for Y = tanh(XA) B."""
    Z = X @ A; H = np.tanh(Z)
    dB = H.T @ dY; dH = dY @ B.T; dZ = dH * (1 - H ** 2)
    return X.T @ dZ, dB, dZ @ A.T     # dA, dB, dX
''',
    tasks=[
        dict(fn='split_weights', title='Column-split A, row-split B', md=r'''
            Megatron splits the first matrix **by columns** and the second **by rows**, so each GPU computes tanh on its own hidden units with no communication in between.
            Return `(A_parts, B_parts)`, lists of length t, with `A_parts[i] = A[:, cols_i]` and `B_parts[i] = B[rows_i, :]` for the same index ranges.''',
             starter=r'''
            def split_weights(A, B, t):
                # TODO: use np.array_split on the hidden dimension
                raise NotImplementedError''',
             test=r'''
            def _test_split_weights(f):
                Ap, Bp = f(A, Bw, 4)
                assert len(Ap) == 4 and all(a.shape == (d, h // 4) for a in Ap) and all(b.shape == (h // 4, d) for b in Bp)
                assert np.allclose(np.concatenate(Ap, 1), A) and np.allclose(np.concatenate(Bp, 0), Bw)''',
             solution=r'''
            def split_weights_solution(A, B, t):
                idx = np.array_split(np.arange(A.shape[1]), t)
                return [A[:, i] for i in idx], [B[i, :] for i in idx]'''),
        dict(fn='tp_forward', title='Forward: one all-reduce', md=r'''
            Each GPU i computes a **partial** output $Y_i = \tanh(X A_i) B_i$. The true output is the **sum** of the partials: one all-reduce. Return Y.''',
             starter=r'''
            def tp_forward(X, A_parts, B_parts):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_tp_forward(f):
                Ap, Bp = (split_weights_solution if 'split_weights_solution' in globals() else _split)(A, Bw, 4)
                assert np.allclose(f(X, Ap, Bp), mlp(X, A, Bw))

            def _split(A, B, t):
                idx = np.array_split(np.arange(A.shape[1]), t); return [A[:, i] for i in idx], [B[i, :] for i in idx]''',
             solution=r'''
            def tp_forward_solution(X, A_parts, B_parts):
                return sum(np.tanh(X @ a) @ b for a, b in zip(A_parts, B_parts))      # all-reduce = sum of partials'''),
        dict(fn='tp_backward', title='Backward: local weight gradients, one all-reduce for dX', md=r'''
            With the incoming gradient dY (same on every GPU), each GPU i computes its weight gradients **locally**:
            $H_i = \tanh(XA_i)$, $dB_i = H_i^\top dY$, $dZ_i = (dY B_i^\top)\odot(1 - H_i^2)$, $dA_i = X^\top dZ_i$.
            The input gradient needs contributions from every GPU: $dX = \sum_i dZ_i A_i^\top$, which is the backward pass's all-reduce.
            Return `(dA_parts, dB_parts, dX)`.''',
             starter=r'''
            def tp_backward(X, A_parts, B_parts, dY):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_tp_backward(f):
                Ap, Bp = _split(A, Bw, 4)
                dAp, dBp, dX = f(X, Ap, Bp, dY)
                rA, rB, rX = mlp_grads(X, A, Bw, dY)
                assert np.allclose(np.concatenate(dAp, 1), rA), "dA shards must concatenate to the full dA"
                assert np.allclose(np.concatenate(dBp, 0), rB), "dB shards must stack to the full dB"
                assert np.allclose(dX, rX), "dX needs the sum over GPUs (all-reduce)"''',
             solution=r'''
            def tp_backward_solution(X, A_parts, B_parts, dY):
                dA, dB, dX = [], [], 0
                for a, b in zip(A_parts, B_parts):
                    H = np.tanh(X @ a)
                    dB.append(H.T @ dY)
                    dZ = (dY @ b.T) * (1 - H ** 2)
                    dA.append(X.T @ dZ)
                    dX = dX + dZ @ a.T                       # all-reduce in backward
                return dA, dB, dX'''),
    ],
    explore_md=r'''
        **Communication per transformer layer.** Each block (attention + MLP) needs one all-reduce in the forward pass and one in the backward pass, each of size tokens × d. Sequence parallelism (Korthikanti et al.) replaces each all-reduce with a reduce-scatter + all-gather of the same total volume, but stores the LayerNorm/dropout activations sharded along the sequence instead of replicated. Below: per-layer activation memory with the paper's formula $sbh(34 + 5as/h)$ bytes, divided by t with tensor + sequence parallelism.''',
    explore=r'''
        s, b, hd, a = 2048, 1, 12288, 96     # GPT-3 175B-like: sequence, micro-batch, hidden, heads
        base = s * b * hd * (34 + 5 * a * s / hd)
        print(f"5as/h = {5 * a * s / hd:.0f} (the attention-score term; paper: 80 for GPT-3)")
        for t in [1, 2, 4, 8]:
            print(f"t={t}: activations per layer {base / t / 2**30:6.2f} GiB with TP+SP; selective recompute keeps only 34·sbh/t = {34 * s * b * hd / t / 2**30:5.2f} GiB")''',
    takeaways=r'''
        * Column-then-row splitting lets each GPU apply the nonlinearity locally: one all-reduce forward and one backward per MLP (and per attention block).
        * Weight gradients are local; only the activation gradient needs communication.
        * Tensor parallelism communicates every layer, so it lives inside the NVLink domain; sequence parallelism also shards the activations TP alone would replicate.''',
))

# ------------------------------------------------------------------ 04
NBS.append(dict(
    slug='04_pipeline_schedules', title='04 · Pipeline schedules: GPipe vs 1F1B', deck='distributed/05-pipeline-parallelism/', deck_name='Pipeline parallelism', minutes=45,
    goals='a small pipeline simulator that turns per-stage operation orders into a timeline, then GPipe and 1F1B schedules, their bubble and their peak activation memory.',
    setup=BASE + r'''
def simulate(orders, p, tf=1.0, tb=2.0):
    """orders[s] = list of ('F' or 'B', microbatch) for stage s, executed in that order.
    F(s,i) needs F(s-1,i); B(s,i) needs B(s+1,i) and F(s,i). Returns (makespan, finish times dict, peak in-flight per stage)."""
    done, ptr, clock = {}, [0] * p, [0.0] * p
    inflight, peak = [0] * p, [0] * p
    progress = True
    while progress:
        progress = False
        for s in range(p):
            if ptr[s] >= len(orders[s]):
                continue
            op, i = orders[s][ptr[s]]
            deps = [('F', s - 1, i)] if op == 'F' and s > 0 else []
            if op == 'B':
                deps = [('F', s, i)] + ([('B', s + 1, i)] if s < p - 1 else [])
            if all(dp in done for dp in deps):
                start = max([clock[s]] + [done[dp] for dp in deps])
                done[(op, s, i)] = clock[s] = start + (tf if op == 'F' else tb)
                inflight[s] += 1 if op == 'F' else -1
                peak[s] = max(peak[s], inflight[s])
                ptr[s] += 1; progress = True
    assert all(ptr[s] == len(orders[s]) for s in range(p)), "deadlock: an order violates dependencies"
    return max(clock), done, peak
''',
    tasks=[
        dict(fn='gpipe_orders', title='GPipe: all forwards, then all backwards', md=r'''
            GPipe runs every micro-batch forward through the pipeline, then every backward. For each stage s the order is F0, F1, …, F(m−1), B0, B1, …, B(m−1).
            Return `orders` (a list of p lists of `('F', i)` / `('B', i)`).''',
             starter=r'''
            def gpipe_orders(p, m):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_gpipe_orders(f):
                p, m = 4, 8
                mk, _, peak = simulate(f(p, m), p)
                assert np.isclose(mk, (m + p - 1) * 3.0), f"GPipe makespan should be (m+p-1)(tf+tb) = {(m + p - 1) * 3.0}, got {mk}"
                assert peak == [m] * p, f"GPipe keeps all m micro-batches' activations: peak {peak}"''',
             solution=r'''
            def gpipe_orders_solution(p, m):
                return [[('F', i) for i in range(m)] + [('B', i) for i in range(m)] for _ in range(p)]'''),
        dict(fn='one_f_one_b_orders', title='1F1B: start backwards early', md=r'''
            PipeDream's 1F1B schedule: stage s does `p − s − 1` warm-up forwards, then alternates one forward and one backward, then finishes the remaining backwards.
            Same makespan as GPipe for the same p and m, but each stage holds at most `p − s` micro-batches of activations instead of m.''',
             starter=r'''
            def one_f_one_b_orders(p, m):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_one_f_one_b_orders(f):
                p, m = 4, 8
                orders = f(p, m)
                assert all(sorted(o) == sorted([('F', i) for i in range(m)] + [('B', i) for i in range(m)]) for o in orders), "each stage does every F and B once"
                mk, _, peak = simulate(orders, p)
                assert np.isclose(mk, (m + p - 1) * 3.0), f"1F1B makespan should equal GPipe's, got {mk}"
                assert peak == [p - s for s in range(p)], f"peak in-flight should be p - s per stage, got {peak}"''',
             solution=r'''
            def one_f_one_b_orders_solution(p, m):
                orders = []
                for s in range(p):
                    warm = min(p - s - 1, m)
                    o = [('F', i) for i in range(warm)]
                    f_next, b_next = warm, 0
                    while f_next < m:
                        o += [('F', f_next), ('B', b_next)]; f_next += 1; b_next += 1
                    o += [('B', i) for i in range(b_next, m)]
                    orders.append(o)
                return orders'''),
        dict(fn='bubble_fraction', title='The bubble', md=r'''
            Ideal time (no pipeline) for one stage's work is m·(tf + tb). The **bubble fraction** is the extra time relative to that ideal:
            $$\text{bubble} = \frac{\text{makespan} - m(t_f+t_b)}{m(t_f+t_b)}$$
            Megatron (Narayanan et al., 2021) derives it as $(p-1)/m$, and with an interleaved schedule of v chunks per GPU as $(p-1)/(v\cdot m)$ (also the formula Llama 3 quotes). Compute it from a simulated makespan.''',
             starter=r'''
            def bubble_fraction(makespan, m, tf=1.0, tb=2.0):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_bubble_fraction(f):
                for p, m in [(4, 8), (8, 32), (16, 64)]:
                    mk, _, _ = simulate(gpipe_orders_solution(p, m) if 'gpipe_orders_solution' in globals() else [[('F', i) for i in range(m)] + [('B', i) for i in range(m)] for _ in range(p)], p)
                    assert np.isclose(f(mk, m), (p - 1) / m), f"p={p}, m={m}: expected (p-1)/m = {(p - 1) / m:.3f}"''',
             solution=r'''
            def bubble_fraction_solution(makespan, m, tf=1.0, tb=2.0):
                ideal = m * (tf + tb)
                return (makespan - ideal) / ideal'''),
    ],
    explore_md=r'''
        **Bubble vs micro-batches, and the memory trade-off.** More micro-batches shrink the bubble ((p−1)/m) but GPipe must hold all of them; 1F1B caps memory at p in-flight micro-batches on the first stage. Interleaving (v model chunks per GPU) divides the bubble by v at the cost of v× more point-to-point messages.''',
    explore=r'''
        p = 8
        for m in [8, 16, 32, 64]:
            mk, _, peak_g = simulate(gpipe_orders_solution(p, m), p)
            _, _, peak_1 = simulate(one_f_one_b_orders_solution(p, m), p)
            b = bubble_fraction_solution(mk, m)
            print(f"p={p}, m={m:3d}: bubble {b:5.1%}  (interleaved v=4: {(p - 1) / (4 * m):5.1%})   peak activations stage 0: GPipe {peak_g[0]:3d}, 1F1B {peak_1[0]}")''',
    takeaways=r'''
        * A pipeline of p stages idles while it fills and drains: bubble = (p−1)/m of the ideal time, so you need many micro-batches (GPipe: negligible when m ≥ 4p).
        * 1F1B has the same bubble as GPipe but bounds activation memory by p micro-batches instead of m.
        * Interleaved schedules divide the bubble by v; zero-bubble schedules split the backward pass to fill the remaining gaps.''',
))

# ------------------------------------------------------------------ 05
NBS.append(dict(
    slug='05_activation_checkpointing', title='05 · Activation checkpointing', deck='distributed/08-activation-memory/', deck_name='Activation memory and recomputation', minutes=35,
    goals='a manual backward pass for a deep stack, then a checkpointed version that stores every k-th activation and recomputes the rest, with exact gradients and the √n memory trade-off.',
    setup=BASE + r'''
r = np.random.default_rng(0)
L, Wd = 16, 6
Ws = [r.normal(0, 0.5, (Wd, Wd)) for _ in range(L)]
x0 = r.normal(size=(3, Wd))

def layer(h, W):
    return np.tanh(h @ W)

def ref_grads(x):
    """Plain backprop of loss = sum(output) storing every activation."""
    acts = [x]
    for W in Ws:
        acts.append(layer(acts[-1], W))
    g = np.ones_like(acts[-1]); gW = [None] * L
    for i in range(L - 1, -1, -1):
        dz = g * (1 - acts[i + 1] ** 2)
        gW[i] = acts[i].T @ dz
        g = dz @ Ws[i].T
    return gW
''',
    tasks=[
        dict(fn='backward_from', title='Backward through one segment', md=r'''
            Write the backward pass for layers `lo … hi−1` given the segment's **input** activation `h_lo` and the gradient `g` arriving at its output. Recompute the segment's activations from `h_lo` (that is the "recompute" part), then backpropagate:
            $dz = g \odot (1 - a_{i+1}^2)$, $\;dW_i = a_i^\top dz$, $\;g \leftarrow dz\,W_i^\top$.
            Return `(grads_dict {i: dW_i}, g_at_input, n_layer_evals)`.''',
             starter=r'''
            def backward_from(h_lo, lo, hi, g):
                # TODO: recompute acts for layers lo..hi-1 from h_lo, then backprop through them
                raise NotImplementedError''',
             test=r'''
            def _test_backward_from(f):
                gW = ref_grads(x0)
                grads, g_in, evals = f(x0, 0, L, np.ones((3, Wd)))
                assert evals == L, "recomputing a segment of L layers takes L layer evaluations"
                assert all(np.allclose(grads[i], gW[i]) for i in range(L)), "gradients must match plain backprop"''',
             solution=r'''
            def backward_from_solution(h_lo, lo, hi, g):
                acts = [h_lo]
                for i in range(lo, hi):
                    acts.append(layer(acts[-1], Ws[i]))
                grads = {}
                for j in range(hi - lo - 1, -1, -1):
                    i = lo + j
                    dz = g * (1 - acts[j + 1] ** 2)
                    grads[i] = acts[j].T @ dz
                    g = dz @ Ws[i].T
                return grads, g, hi - lo'''),
        dict(fn='checkpointed_grads', title='Checkpoint every k layers', md=r'''
            Forward pass: keep only the activations at layers 0, k, 2k, … (the **checkpoints**), discard the rest.
            Backward pass: for each segment, from last to first, recompute it from its checkpoint and backpropagate (use `backward_from`).
            Return `(grads_list, peak_stored, extra_evals)`: `peak_stored` = number of checkpoints + the largest segment's activations held during its backward (k); `extra_evals` = layer evaluations spent on recomputation.''',
             starter=r'''
            def checkpointed_grads(x, k, bf=None):
                bf = bf or backward_from
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_checkpointed_grads(f):
                gW = ref_grads(x0)
                bf = backward_from_solution if f.__name__.endswith('_solution') else backward_from
                for k in [1, 2, 4, 8, 16]:
                    grads, peak, extra = f(x0, k, bf)
                    assert all(np.allclose(grads[i], gW[i]) for i in range(L)), f"k={k}: gradients must match"
                    assert peak == L // k + k, f"k={k}: peak stored should be L/k + k = {L // k + k}, got {peak}"
                    assert extra == L, f"k={k}: recomputation costs one extra forward (L layer evals), got {extra}"''',
             solution=r'''
            def checkpointed_grads_solution(x, k, bf=None):
                bf = bf or backward_from_solution
                ckpt, h = {0: x}, x
                for i in range(L):
                    h = layer(h, Ws[i])
                    if (i + 1) % k == 0 and i + 1 < L:
                        ckpt[i + 1] = h
                g = np.ones_like(h); grads = [None] * L; extra = 0
                for lo in sorted(ckpt, reverse=True):
                    hi = min(lo + k, L)
                    gd, g, ev = bf(ckpt[lo], lo, hi, g)
                    for i, v in gd.items():
                        grads[i] = v
                    extra += ev
                return grads, len(ckpt) + k, extra'''),
    ],
    explore_md=r'''
        **The √n sweet spot.** Stored activations ≈ L/k + k, minimized at k = √L, for one extra forward pass. Chen et al. (2016) cut a 1,000-layer network from 48 GB to 7 GB for about 30% more time. Modern LLM training uses *selective* recomputation: recompute only the cheap-but-large attention-score part (Korthikanti et al.), saving most memory for little compute.''',
    explore=r'''
        for Lx in [16, 64, 256, 1024]:
            best = min(range(1, Lx + 1), key=lambda k: Lx / k + k)
            print(f"L={Lx:5d}: store everything = {Lx:5d} activations; checkpoint every √L = {best:3d} → {Lx // best + best:4d}  ({(Lx // best + best) / Lx:.1%} of the memory)")''',
    takeaways=r'''
        * Checkpointing trades compute for memory: store a few activations, recompute the rest during backward.
        * Every k layers → memory ≈ L/k + k, best at k ≈ √L, cost ≈ one extra forward pass (~30% more time).
        * Recompute is exact: gradients are identical.''',
))

# ------------------------------------------------------------------ 06
NBS.append(dict(
    slug='06_mixed_precision', title='06 · Mixed precision: FP16, BF16 and loss scaling', deck='distributed/09-mixed-precision-fp8/', deck_name='Mixed precision and FP8 training', minutes=40,
    goals='BF16 rounding, a dynamic loss scaler, and a training loop with FP16 gradients and FP32 master weights that works only when the loss is scaled.',
    setup=BASE + r'''
r = np.random.default_rng(0)
Dm = 8
Xs = r.normal(0, 1e-4, (64, Dm)); w_star = r.normal(size=Dm); ys = Xs @ w_star     # tiny features → tiny gradients

def loss_and_grad(w):
    e = Xs @ w - ys
    return float(np.mean(e ** 2)), 2 * Xs.T @ e / len(ys)
''',
    tasks=[
        dict(fn='to_bf16', title='Round to bfloat16', md=r'''
            BF16 keeps FP32's 8 exponent bits and only 7 mantissa bits: it is the top 16 bits of an FP32 number. Round to nearest-even on the dropped 16 bits:
            ```
            u = x.astype(np.float32).view(np.uint32)
            u = u + 0x7FFF + ((u >> 16) & 1)       # round to nearest even
            return (u & 0xFFFF0000).view(np.float32)
            ```
            BF16 has FP32's range (up to ~3.4e38, tiny values survive) but coarse precision; FP16 has more precision but overflows above 65,504 and underflows below ~6e-8.''',
             starter=r'''
            def to_bf16(x):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_to_bf16(f):
                x = np.array([1.0, 1.00390625, 3.14159265, 70000.0, 1e-30], dtype=np.float32)
                y = f(x)
                assert y[0] == 1.0 and y[2] == np.float32(3.140625), f"precision: got {y[:3]}"
                assert y[3] == 70144.0, "70,000 is representable in BF16 (rounded), unlike FP16 which overflows"
                assert y[4] > 0, "1e-30 survives in BF16 (FP16 would flush it to 0)"
                assert np.isinf(np.float16(70000.0)) and np.float16(1e-30) == 0''',
             solution=r'''
            def to_bf16_solution(x):
                u = np.asarray(x, dtype=np.float32).view(np.uint32).astype(np.uint64)
                u = (u + 0x7FFF + ((u >> 16) & 1)) & 0xFFFF0000
                return u.astype(np.uint32).view(np.float32)'''),
        dict(fn='LossScaler', title='A dynamic loss scaler', md=r'''
            Multiply the loss by a scale S before backward so small gradients don't underflow in FP16; divide the gradients by S (in FP32) before the update.
            * If any scaled gradient is inf or NaN: **skip** the step and halve S.
            * After `interval` consecutive good steps: double S.

            Implement `update(grads_fp16)` → returns `True` if the step should be applied, and adjusts `self.scale`.''',
             starter=r'''
            class LossScaler:
                def __init__(self, scale=2.0 ** 15, interval=50):
                    self.scale, self.interval, self.good = scale, interval, 0

                def update(self, grads_fp16):
                    # TODO
                    raise NotImplementedError''',
             test=r'''
            def _test_LossScaler(cls):
                s = cls(1024.0, interval=3)
                assert s.update(np.array([1.0], np.float16)) and s.scale == 1024.0
                assert not s.update(np.array([np.inf], np.float16)) and s.scale == 512.0, "overflow: skip and halve"
                for _ in range(3):
                    assert s.update(np.array([1.0], np.float16))
                assert s.scale == 1024.0, "after `interval` good steps, double"''',
             solution=r'''
            class LossScaler_solution:
                def __init__(self, scale=2.0 ** 15, interval=50):
                    self.scale, self.interval, self.good = scale, interval, 0

                def update(self, grads_fp16):
                    if not np.all(np.isfinite(grads_fp16)):
                        self.scale /= 2; self.good = 0
                        return False
                    self.good += 1
                    if self.good >= self.interval:
                        self.scale *= 2; self.good = 0
                    return True'''),
        dict(fn='train_mixed', title='Train with FP16 gradients and FP32 master weights', md=r'''
            Micikevicius et al. (2018): keep an FP32 **master copy** of the weights; compute gradients in half precision; scale the loss so they don't underflow.
            For `steps` iterations: compute the FP32 gradient, emulate the half-precision backward as `np.float16(grad * scale)`, let the scaler decide, then (if applied) update the master weights with SGD using `grad16 / scale` (in FP32). With `use_scaling=False`, use scale 1 and never skip.
            Return the final loss. The features are tiny, so unscaled FP16 gradients mostly flush to zero.''',
             starter=r'''
            def train_mixed(use_scaling, steps=300, lr=2e7, scaler_cls=None):
                w = np.zeros(Dm, dtype=np.float32)
                scaler = (scaler_cls or LossScaler)(2.0 ** 15, 50) if use_scaling else None
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_train_mixed(f):
                cls = LossScaler_solution if f.__name__.endswith('_solution') else LossScaler
                l0 = loss_and_grad(np.zeros(Dm))[0]
                ls = f(True, scaler_cls=cls); ln = f(False, scaler_cls=cls)
                ref = l0
                w = np.zeros(Dm)
                for _ in range(300):
                    w = w - 2e7 * loss_and_grad(w)[1]
                ref = loss_and_grad(w)[0]
                assert ls < 1e-3 * l0, f"with loss scaling, loss should drop a lot ({l0:.2e} → {ls:.2e})"
                assert abs(ls - ref) < 0.05 * l0, "scaled FP16 training should track FP32 training"
                assert ln > 0.1 * l0, f"without scaling, gradients underflow and training stalls ({ln:.2e} of {l0:.2e})"''',
             solution=r'''
            def train_mixed_solution(use_scaling, steps=300, lr=2e7, scaler_cls=None):
                w = np.zeros(Dm, dtype=np.float32)
                scaler = (scaler_cls or LossScaler_solution)(2.0 ** 15, 50) if use_scaling else None
                for _ in range(steps):
                    _, g = loss_and_grad(w)
                    scale = scaler.scale if scaler else 1.0
                    g16 = np.float16(g * scale)
                    if scaler and not scaler.update(g16):
                        continue
                    w = (w - lr * (g16.astype(np.float32) / np.float32(scale))).astype(np.float32)
                return loss_and_grad(w)[0]'''),
    ],
    explore_md=r'''
        **What fraction of gradients survives?** Cast the same gradient vector to FP16 with and without scaling, and to BF16. BF16's FP32-sized exponent is why most LLM training uses BF16 without loss scaling; FP8 training (DeepSeek-V3) needs fine-grained scales instead: one per 1×128 activation tile and per 128×128 weight block.''',
    explore=r'''
        np.seterr(over='ignore')
        g = r.lognormal(-18, 2, 100000) * r.choice([-1, 1], 100000)
        for name, conv in [('FP16, no scale', lambda v: np.float16(v)), ('FP16, ×2^15', lambda v: np.float16(v * 2 ** 15)), ('BF16, no scale', to_bf16_solution)]:
            print(f"{name:15} nonzero after cast: {np.mean(conv(g) != 0):6.1%}")''',
    takeaways=r'''
        * Mixed precision = low-precision math and storage, FP32 master weights and FP32 accumulation.
        * FP16's narrow range needs dynamic loss scaling (skip and halve on overflow, grow when stable); BF16 has FP32's range, so it usually doesn't.
        * Lower precision (FP8) needs finer-grained scaling; Llama 3 also accumulates and reduce-scatters gradients in FP32 for stability.''',
))

# ------------------------------------------------------------------ 07
NBS.append(dict(
    slug='07_ring_attention', title='07 · Context parallelism: ring attention', deck='distributed/06-context-parallelism/', deck_name='Context parallelism', minutes=40,
    goals='causal attention over a sequence split across N simulated GPUs: each keeps its query block and K/V blocks travel around a ring, combined with an online softmax. Exact, with memory per GPU ∝ sequence / N.',
    setup=BASE + r'''
def full_causal_attention(Q, K, V):
    S = Q @ K.T / np.sqrt(Q.shape[1])
    S = np.where(np.tril(np.ones(S.shape, bool)), S, -np.inf)
    return softmax(S) @ V
''',
    tasks=[
        dict(fn='ring_attention', title='Ring attention with an online softmax', md=r'''
            Split Q, K, V into N equal blocks along the sequence; GPU i owns Q_i and starts with (K_i, V_i).
            For step t = 0 … N−1, GPU i holds the K/V block j = (i − t) mod N (blocks move one GPU around the ring per step). It updates a running max m, sum ℓ and unnormalized output Õ for its queries:
            * skip if j > i (entirely in the future, causal);
            * on j = i, apply the causal mask within the block;
            * otherwise attend to the whole block.

            At the end O_i = Õ / ℓ. Return the full output (concatenate the N blocks) and the number of K/V blocks each GPU received.''',
             starter=r'''
            def ring_attention(Q, K, V, N):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_ring_attention(f):
                r = np.random.default_rng(1)
                for T, N in [(16, 4), (24, 3), (8, 8)]:
                    Q, K, V = r.normal(size=(3, T, 8))
                    O, recv = f(Q, K, V, N)
                    assert np.allclose(O, full_causal_attention(Q, K, V), atol=1e-10), f"T={T}, N={N}: must equal full causal attention"
                    assert recv == N - 1, f"each GPU receives N-1 K/V blocks, got {recv}"''',
             solution=r'''
            def ring_attention_solution(Q, K, V, N):
                Qb, Kb, Vb = np.split(Q, N), np.split(K, N), np.split(V, N)
                bs, d = Qb[0].shape
                out = []
                for i in range(N):
                    m = np.full(bs, -np.inf); l = np.zeros(bs); acc = np.zeros((bs, V.shape[1]))
                    for t in range(N):
                        j = (i - t) % N
                        if j > i:
                            continue
                        S = Qb[i] @ Kb[j].T / np.sqrt(d)
                        if j == i:
                            S = np.where(np.tril(np.ones((bs, bs), bool)), S, -np.inf)
                        m_new = np.maximum(m, S.max(1))
                        P = np.exp(S - m_new[:, None]); corr = np.exp(m - m_new)
                        l = l * corr + P.sum(1); acc = acc * corr[:, None] + P @ Vb[j]; m = m_new
                    out.append(acc / l[:, None])
                return np.concatenate(out), N - 1'''),
        dict(fn='cp_comm_bytes', title='Ring vs all-gather communication', md=r'''
            Per GPU, per layer, for sequence length S, KV width w (= 2 · n_kv_heads · head_dim) and b bytes per value:
            * **Ring** (Liu et al.): receives N − 1 K/V blocks of S/N tokens: (N−1)/N · S · w · b, overlapped with compute.
            * **All-gather** (the variant Llama 3 uses): also receives (N−1)/N · S · w · b, but all at once before attention; simpler with arbitrary masks such as document masks, at the cost of exposed latency.

            Return the bytes per GPU (same for both). The point of the exercise: the difference is *when*, not *how much*.''',
             starter=r'''
            def cp_comm_bytes(S, N, w, b=2):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_cp_comm_bytes(f):
                assert f(131072, 16, 2 * 8 * 128) == 15 / 16 * 131072 * 2048 * 2''',
             solution=r'''
            def cp_comm_bytes_solution(S, N, w, b=2):
                return (N - 1) / N * S * w * b'''),
    ],
    explore_md=r'''
        **Load balance.** With a causal mask, GPU 0 (earliest tokens) skips most K/V blocks and GPU N−1 does the most work. Count attended blocks per GPU; real systems reorder tokens (e.g. give each GPU one early and one late chunk) to balance it.''',
    explore=r'''
        N = 8
        work = [sum(1 for t in range(N) if (i - t) % N <= i) for i in range(N)]
        print("K/V blocks attended per GPU with naive contiguous chunks:", work)
        print("Llama 3 405B at 128K context: CP = 16 →", f"{cp_comm_bytes_solution(131072, 16, 2 * 8 * 128) / 2**20:.0f} MiB of K/V per GPU per layer (BF16)")''',
    takeaways=r'''
        * Context parallelism splits the sequence; attention still needs every earlier token, so K/V blocks move between GPUs.
        * With an online softmax the result is exact; memory per GPU scales with S/N, so the context can grow with the number of GPUs.
        * Ring passes overlap communication with compute; all-gather is simpler for complex masks. Causal masks need load balancing.''',
))

# ------------------------------------------------------------------ 08
NBS.append(dict(
    slug='08_checkpoint_failures', title='08 · Failures, checkpoints and goodput', deck='distributed/11-reliability-stability/', deck_name='Reliability and stability', minutes=35,
    goals='Young\'s checkpoint interval, a Monte Carlo simulation of a training run with random failures, and the effect of faster (async, in-memory) checkpoints on effective training time.',
    setup=BASE + r'''
HOURS = 24 * 54                       # a 54-day run
MTBF = 54 * 24 / 419                  # Llama 3 405B: 419 interruptions in 54 days → ~3.1 h
RESTART = 10 / 60                     # 10 minutes to detect, restart and reload
''',
    tasks=[
        dict(fn='young_interval', title='Young\'s approximation', md=r'''
            If a checkpoint costs C hours and failures arrive every M hours on average, the interval that minimizes lost time is approximately
            $$\tau^\star \approx \sqrt{2\,C\,M}$$
            (Young, 1974). Return τ* in hours.''',
             starter=r'''
            def young_interval(C, M):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_young_interval(f):
                assert np.isclose(f(5 / 60, MTBF), np.sqrt(2 * 5 / 60 * MTBF))
                assert np.isclose(f(0.5, 2.0), np.sqrt(2.0))''',
             solution=r'''
            def young_interval_solution(C, M):
                return np.sqrt(2 * C * M)'''),
        dict(fn='simulate_goodput', title='Simulate a run', md=r'''
            Simulate wall-clock time until `HOURS` of useful training is done:
            * work in segments of `tau` hours followed by a checkpoint costing `C` (training is paused while it writes);
            * failures arrive as a Poisson process with mean gap `M` (draw exponential gaps with `rng.exponential(M)`); a failure loses all work since the last completed checkpoint and costs `RESTART`.

            Return **goodput** = useful hours ÷ wall-clock hours. Use the given `rng` so results are reproducible.''',
             starter=r'''
            def simulate_goodput(tau, C, M=MTBF, seed=0):
                rng = np.random.default_rng(seed)
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_simulate_goodput(f):
                g_good = f(young_interval_solution(5 / 60, MTBF) if 'young_interval_solution' in globals() else np.sqrt(2 * 5 / 60 * MTBF), 5 / 60)
                g_rare = f(12.0, 5 / 60); g_often = f(0.05, 5 / 60)
                assert 0.5 < g_good < 1.0
                assert g_good > g_rare and g_good > g_often, f"Young's interval ({g_good:.3f}) should beat checkpointing far too rarely ({g_rare:.3f}) or too often ({g_often:.3f})"
                assert np.isclose(f(1.0, 0.01, M=1e9), 1 / 1.01, atol=1e-3), "with no failures, goodput = tau / (tau + C)"''',
             solution=r'''
            def simulate_goodput_solution(tau, C, M=MTBF, seed=0):
                rng = np.random.default_rng(seed)
                useful = wall = 0.0
                next_fail = rng.exponential(M)
                while useful < HOURS:
                    seg = min(tau, HOURS - useful)
                    if wall + seg + C <= next_fail:          # segment and checkpoint finish before the next failure
                        wall += seg + C; useful += seg
                    else:                                     # failure: lose the partial segment, pay restart
                        wall = next_fail + RESTART
                        next_fail = wall + rng.exponential(M)
                return useful / wall'''),
    ],
    explore_md=r'''
        **Faster checkpoints change everything.** Compare a 5-minute synchronous checkpoint with a 30-second one (async write, the GPU only pauses to snapshot) and a 5-second in-memory one (Gemini-style: copies to peer CPU memory, reported >13× faster recovery). Each uses its own Young interval.''',
    explore=r'''
        for name, C in [('sync to storage, 5 min', 5 / 60), ('async, 30 s pause', 0.5 / 60), ('in-memory, 5 s', 5 / 3600)]:
            tau = young_interval_solution(C, MTBF)
            g = np.mean([simulate_goodput_solution(tau, C, seed=s) for s in range(5)])
            print(f"{name:24} interval {tau * 60:5.1f} min → goodput {g:.1%}")
        print("\nLlama 3 reported >90% effective training time over 54 days on 16,384 GPUs.")''',
    takeaways=r'''
        * Failures are routine at scale: what matters is how much work each one costs.
        * Checkpoint interval ≈ √(2·C·MTBF); cheaper checkpoints allow more frequent saves and less lost work.
        * Async and in-memory checkpointing, fast restart, and spare capacity are the levers that keep goodput above 90%.''',
))
