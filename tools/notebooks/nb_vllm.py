"""vLLM internals exercise notebooks: CPU simulations of the algorithms in vLLM v0.31.0 (vllm/v1/core). No GPU needed."""

NBS = []

# ------------------------------------------------------------------ 01
NBS.append(dict(
    slug='01_block_pool', title='01 · The KV block pool: paging, ref counts and LRU', deck='vllm/03-kv-cache-manager/', deck_name='KV cache manager and PagedAttention', minutes=35,
    goals='a pool of fixed-size KV blocks with a free list, per-request block tables, reference counts for shared blocks, and LRU reuse of freed blocks, the design of `vllm/v1/core/block_pool.py`.',
    setup=r'''
from collections import OrderedDict
import math
BLOCK = 16          # vLLM's CacheConfig.DEFAULT_BLOCK_SIZE
''',
    tasks=[
        dict(fn='blocks_needed', title='How many blocks?', md=r'''
            A request with `n` tokens needs ⌈n / block_size⌉ blocks; the last one may be partly empty. Return `(blocks, wasted_slots)` where wasted slots are the unused token slots in the last block.''',
             starter=r'''
            def blocks_needed(n, block=BLOCK):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_blocks_needed(f):
                assert f(1) == (1, 15) and f(16) == (1, 0) and f(17) == (2, 15) and f(1000) == (63, 8)''',
             solution=r'''
            def blocks_needed_solution(n, block=BLOCK):
                b = math.ceil(n / block)
                return b, b * block - n'''),
        dict(fn='BlockPool', title='A block pool with ref counts and an LRU free queue', md=r'''
            Implement `BlockPool(num_blocks)` with:
            * `allocate(k)` → list of k block ids taken from the **front** of the free queue (the least recently freed), or `None` if fewer than k are free. Allocated blocks get ref count 1.
            * `share(block_ids)` → increments ref counts (another request reuses these blocks, e.g. a cached prefix).
            * `free(block_ids)` → decrements ref counts; blocks reaching 0 go to the **back** of the free queue. vLLM frees a request's blocks in **reverse** order, so the tail of a sequence is evicted before its head.
            * `num_free()`.''',
             starter=r'''
            class BlockPool:
                def __init__(self, num_blocks):
                    self.free_q = OrderedDict((i, None) for i in range(num_blocks))
                    self.ref = [0] * num_blocks
                def allocate(self, k):
                    # TODO
                    raise NotImplementedError
                def share(self, ids):
                    # TODO
                    raise NotImplementedError
                def free(self, ids):
                    # TODO (iterate in reverse)
                    raise NotImplementedError
                def num_free(self):
                    return len(self.free_q)''',
             test=r'''
            def _test_BlockPool(cls):
                p = cls(8)
                a = p.allocate(3); b = p.allocate(2)
                assert a == [0, 1, 2] and b == [3, 4] and p.num_free() == 3
                assert p.allocate(4) is None, "not enough free blocks"
                p.share(a[:2])                      # another request reuses the first two blocks
                p.free(a)
                assert p.num_free() == 4, "only block 2 reached ref count 0"
                p.free(a[:2])
                assert p.num_free() == 6
                assert list(p.free_q)[-3:] == [2, 1, 0], "freed in reverse order: tail first in eviction order"''',
             solution=r'''
            class BlockPool_solution:
                def __init__(self, num_blocks):
                    self.free_q = OrderedDict((i, None) for i in range(num_blocks))
                    self.ref = [0] * num_blocks
                def allocate(self, k):
                    if len(self.free_q) < k: return None
                    ids = []
                    for _ in range(k):
                        i, _ = self.free_q.popitem(last=False); self.ref[i] = 1; ids.append(i)
                    return ids
                def share(self, ids):
                    for i in ids:
                        if self.ref[i] == 0: self.free_q.pop(i, None)
                        self.ref[i] += 1
                def free(self, ids):
                    for i in reversed(ids):
                        self.ref[i] -= 1
                        if self.ref[i] == 0: self.free_q[i] = None
                def num_free(self):
                    return len(self.free_q)'''),
        dict(fn='paged_vs_contiguous', title='Paged vs contiguous reservation', md=r'''
            Before paging, servers reserved a contiguous region of `max_len` token slots per request. Given the actual final lengths of a set of requests, return `(contiguous_waste, paged_waste)`: the fraction of reserved slots never used, for (a) reserving `max_len` each and (b) paging with 16-token blocks.''',
             starter=r'''
            def paged_vs_contiguous(lengths, max_len=2048, block=BLOCK):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_paged_vs_contiguous(f):
                c, p = f([100, 300, 1500, 40], 2048)
                assert abs(c - (1 - 1940 / 8192)) < 1e-9
                assert p < 0.03, "paging wastes at most one partial block per request"''',
             solution=r'''
            def paged_vs_contiguous_solution(lengths, max_len=2048, block=BLOCK):
                used = sum(lengths)
                paged = sum(math.ceil(n / block) * block for n in lengths)
                return 1 - used / (max_len * len(lengths)), 1 - used / paged'''),
    ],
    explore_md=r'''
        **Fragmentation at scale.** Draw 1,000 requests with output lengths between 50 and 2,000 tokens and compare waste. The PagedAttention paper (Kwon et al., 2023) measured that earlier systems used only 20.4%–38.2% of KV cache memory for actual token states, versus 96.3% for vLLM.''',
    explore=r'''
        import random
        r = random.Random(0); L = [r.randint(50, 2000) for _ in range(1000)]
        c, p = paged_vs_contiguous_solution(L, 2048)
        print(f"contiguous max_len reservation wastes {c:.1%}; paged (16-token blocks) wastes {p:.2%}")
        for bs in [8, 16, 32, 128]:
            print(f"block size {bs:3d}: paged waste {paged_vs_contiguous_solution(L, 2048, bs)[1]:.2%}")''',
    takeaways=r'''
        * vLLM splits the KV cache into fixed-size blocks (16 tokens by default) and gives each request a block table, like OS virtual memory pages.
        * Reference counts let several requests share blocks (cached prefixes, parallel sampling) without copying.
        * Freed blocks join the back of an LRU free queue, in reverse order, so cached content survives as long as possible.''',
))

# ------------------------------------------------------------------ 02
NBS.append(dict(
    slug='02_prefix_cache', title='02 · Automatic prefix caching with chained block hashes', deck='vllm/05-prefix-caching/', deck_name='Automatic prefix caching', minutes=35,
    goals='hashing each full KV block together with its parent block\'s hash, looking up the longest cached prefix of a new prompt, and measuring how much prefill a shared system prompt saves.',
    setup=r'''
import hashlib, pickle, math
BLOCK = 16
def H(obj):
    """vLLM's default prefix_caching_hash_algo is sha256 over a pickled tuple."""
    return hashlib.sha256(pickle.dumps(obj)).digest()
NONE_HASH = b"\x00" * 32
SYSTEM = list(range(1000, 1000 + 70))           # a 70-token shared system prompt
''',
    tasks=[
        dict(fn='block_hashes', title='Chained block hashes', md=r'''
            For a token list, return the hashes of its **full** blocks only (a trailing partial block is not cached). Block i's hash is `H((parent_hash, tuple(block_tokens), None))` with `parent_hash = NONE_HASH` for the first block, as in `hash_block_tokens` in vLLM.
            Chaining means equal blocks at different positions, or after different prefixes, get different hashes.''',
             starter=r'''
            def block_hashes(tokens, block=BLOCK):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_block_hashes(f):
                a = f(list(range(40)))
                assert len(a) == 2, "40 tokens = 2 full blocks + 8 uncached tokens"
                b = f(list(range(32)) + [7] * 5)
                assert a == b, "same first 32 tokens → same two hashes"
                c = f([99] + list(range(1, 40)))
                assert c[0] != a[0] and c[1] != a[1], "a different first block changes every later hash (chaining)"''',
             solution=r'''
            def block_hashes_solution(tokens, block=BLOCK):
                out, parent = [], NONE_HASH
                for i in range(len(tokens) // block):
                    parent = H((parent, tuple(tokens[i * block:(i + 1) * block]), None)); out.append(parent)
                return out'''),
        dict(fn='PrefixCache', title='Look up the longest cached prefix', md=r'''
            `PrefixCache` maps block hash → block id. `lookup(tokens)` returns the number of prompt tokens whose KV can be reused: walk the prompt's block hashes from the start and stop at the first miss. `insert(tokens)` registers all full blocks of a finished prefill (assign new ids 0, 1, 2, …).
            vLLM never reuses the very last token's KV for a full hit: the model must compute at least one token to produce logits. Cap the reusable count at `len(tokens) - 1`.''',
             starter=r'''
            class PrefixCache:
                def __init__(self):
                    self.map, self.next_id = {}, 0
                def insert(self, tokens):
                    # TODO
                    raise NotImplementedError
                def lookup(self, tokens):
                    # TODO
                    raise NotImplementedError''',
             test=r'''
            def _test_PrefixCache(cls):
                hb = globals().get("block_hashes_solution") or block_hashes
                pc = cls(); pc.insert(SYSTEM + [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
                assert pc.lookup(SYSTEM + [50, 51, 52]) == 64, "70-token system prompt → 4 full blocks (64 tokens) reusable"
                assert pc.lookup([5] + SYSTEM) == 0, "a different first token invalidates everything"
                assert pc.lookup(SYSTEM[:32]) == 31, "exact full hit: keep one token to compute"''',
             solution=r'''
            class PrefixCache_solution:
                def __init__(self):
                    self.map, self.next_id = {}, 0
                def insert(self, tokens):
                    for h in block_hashes_solution(tokens):
                        if h not in self.map:
                            self.map[h] = self.next_id; self.next_id += 1
                def lookup(self, tokens):
                    n = 0
                    for h in block_hashes_solution(tokens):
                        if h not in self.map: break
                        n += BLOCK
                    return min(n, len(tokens) - 1)'''),
        dict(fn='prefill_saved', title='How much prefill does caching save?', md=r'''
            Simulate `n_users` chat requests, each = `SYSTEM` + a unique 30-token user message (use token ids 5000 + 30·u + j). Process them in order with a shared `PrefixCache`, inserting each after its prefill. Return the fraction of prompt tokens that did **not** need prefill.''',
             starter=r'''
            def prefill_saved(n_users=20):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_prefill_saved(f):
                s = f(20)
                total = 20 * 100; expected = 19 * 64 / total
                assert abs(s - expected) < 1e-9, f"19 of 20 requests reuse 64 cached tokens: {expected:.3f}, got {s:.3f}"''',
             solution=r'''
            def prefill_saved_solution(n_users=20):
                pc, saved, total = PrefixCache_solution(), 0, 0
                for u in range(n_users):
                    prompt = SYSTEM + [5000 + 30 * u + j for j in range(30)]
                    saved += pc.lookup(prompt); total += len(prompt); pc.insert(prompt)
                return saved / total'''),
    ],
    explore_md=r'''
        **System prompt length vs savings.** Only full blocks are cached, so a system prompt just over a block boundary wastes the remainder. Longer shared prefixes (few-shot examples, documents in RAG, multi-turn chats) save the most.''',
    explore=r'''
        for sys_len in [10, 16, 70, 500, 2000]:
            SYSTEM = list(range(1000, 1000 + sys_len))
            print(f"shared prefix {sys_len:5d} tokens → {prefill_saved_solution(50):.1%} of prompt tokens skip prefill")''',
    takeaways=r'''
        * vLLM hashes each full block with its parent's hash (sha256 by default), so a block hash identifies the entire prefix up to it.
        * A new request reuses the longest run of matching block hashes; partial blocks and the last token are always recomputed.
        * Prefix caching is on by default in vLLM V1 (`enable_prefix_caching=True`) and costs almost nothing when there are no hits.''',
))

# ------------------------------------------------------------------ 03
NBS.append(dict(
    slug='03_token_budget_scheduler', title='03 · The unified token-budget scheduler', deck='vllm/04-scheduler/', deck_name='The scheduler: continuous batching and chunked prefill', minutes=40,
    goals='a step-by-step simulation of vLLM V1\'s scheduler: a per-step token budget shared by decodes and (chunked) prefills, running requests served first, a long-prefill threshold, and preemption by recomputation when KV blocks run out.',
    setup=r'''
import math
from dataclasses import dataclass, field
BLOCK = 16
@dataclass
class Req:
    rid: int
    prompt: int            # prompt tokens
    out: int               # tokens to generate
    computed: int = 0      # num_computed_tokens
    generated: int = 0
    blocks: int = 0
    preemptions: int = 0
    def total(self):       # tokens that should have KV once caught up
        return self.prompt + self.generated
''',
    tasks=[
        dict(fn='step', title='One scheduling step', md=r'''
            Implement `step(running, waiting, budget, free_blocks, long_prefill=0)` following vLLM V1:
            1. For each **running** request in order: it wants `total() - computed` new tokens (prefill chunks or 1 decode token); cap by `long_prefill` (if > 0) and by the remaining budget. If it needs more blocks than are free, **preempt** the *last* running request (free its blocks, set `computed = 0`, move it to the front of `waiting`) and retry; if it is itself the last, preempt it.
            2. Then admit **waiting** requests in order while budget and blocks remain.
            Return `(scheduled, free_blocks)` with `scheduled = {rid: num_tokens}`. Blocks needed = ⌈(computed + n) / 16⌉ − blocks.''',
             starter=r'''
            def step(running, waiting, budget, free_blocks, long_prefill=0):
                scheduled = {}
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_step(f):
                run = [Req(0, 10, 5, computed=10, generated=1, blocks=1)]; wait = [Req(1, 100, 5)]
                s, free = f(run, wait, budget=64, free_blocks=100)
                assert s == {0: 1, 1: 63}, f"decode first (1 token), then a 63-token prefill chunk; got {s}"
                assert run[-1].rid == 1 and not wait, "an admitted request moves to running"
                run = [Req(0, 16, 5, computed=16, generated=1, blocks=1), Req(1, 40, 5, computed=40, generated=1, blocks=3)]
                s, free = f(run, [], budget=64, free_blocks=0)
                assert 0 in s and 1 not in s, "request 0 needs a new block, so the last running request is preempted"''',
             solution=r'''
            def step_solution(running, waiting, budget, free_blocks, long_prefill=0):
                scheduled = {}
                i = 0
                while i < len(running) and budget > 0:
                    r = running[i]
                    n = r.total() - r.computed
                    if long_prefill > 0: n = min(n, long_prefill)
                    n = min(n, budget)
                    need = math.ceil((r.computed + n) / BLOCK) - r.blocks
                    while need > free_blocks:
                        victim = running.pop()
                        free_blocks += victim.blocks; victim.blocks = 0; victim.computed = 0; victim.preemptions += 1
                        scheduled.pop(victim.rid, None); waiting.insert(0, victim)
                        if victim is r: break
                    else:
                        r.blocks += need; free_blocks -= need; scheduled[r.rid] = n; budget -= n; i += 1
                        continue
                    break
                while waiting and budget > 0:
                    r = waiting[0]
                    n = r.total() - r.computed
                    if long_prefill > 0: n = min(n, long_prefill)
                    n = min(n, budget)
                    need = math.ceil((r.computed + n) / BLOCK) - r.blocks
                    if need > free_blocks: break
                    waiting.pop(0); running.append(r)
                    r.blocks += need; free_blocks -= need; scheduled[r.rid] = n; budget -= n
                return scheduled, free_blocks'''),
        dict(fn='simulate', title='Run the engine loop', md=r'''
            Repeatedly call your `step`, then **apply** it: add scheduled tokens to `computed`; a request whose `computed` reaches `total()` samples one token (`generated += 1`); requests with `generated == out` finish and free their blocks. Return `(steps, total_preemptions, tokens_per_step)`.''',
             starter=r'''
            def simulate(reqs, budget=256, num_blocks=200, long_prefill=0, max_steps=10_000):
                running, waiting, free = [], list(reqs), num_blocks
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_simulate(f):
                reqs = [Req(i, 200 + 37 * i, 20 + 5 * i) for i in range(8)]
                steps, pre, tps = f([Req(r.rid, r.prompt, r.out) for r in reqs], budget=256, num_blocks=400)
                assert pre == 0, "plenty of blocks: no preemptions"
                assert steps < 200
                steps2, pre2, _ = f([Req(r.rid, r.prompt, r.out) for r in reqs], budget=256, num_blocks=40)
                assert pre2 > 0, "too few blocks: requests get preempted and recomputed"''',
             solution=r'''
            def simulate_solution(reqs, budget=256, num_blocks=200, long_prefill=0, max_steps=10_000, step_fn=None):
                step_fn = step_fn or step_solution
                running, waiting, free = [], list(reqs), num_blocks
                steps, tps = 0, []
                while (running or waiting) and steps < max_steps:
                    s, free = step_fn(running, waiting, budget, free, long_prefill)
                    steps += 1; tps.append(sum(s.values()))
                    for r in list(running):
                        if r.rid in s:
                            r.computed += s[r.rid]
                            if r.computed == r.total():
                                r.generated += 1
                                if r.generated == r.out:
                                    running.remove(r); free += r.blocks; r.blocks = 0
                return steps, sum(r.preemptions for r in reqs), tps'''),
    ],
    explore_md=r'''
        **Token budget vs throughput and smoothness.** A larger `max_num_batched_tokens` finishes in fewer steps but makes each step longer (higher inter-token latency for running requests). A long-prefill threshold caps how much of a step one huge prompt can take, leaving room for other prefills.''',
    explore=r'''
        def make(): return [Req(i, 2000 if i == 0 else 100 + 20 * i, 30) for i in range(12)]
        for budget in [128, 512, 2048]:
            st, pre, tps = simulate_solution(make(), budget=budget, num_blocks=1000)
            print(f"budget {budget:5d}: {st:4d} steps, max tokens in one step {max(tps):5d}, preemptions {pre}")
        for lp in [0, 256]:
            biggest = []
            def rec(*a, **k):
                s, free = step_solution(*a, **k); biggest.append(max(s.values(), default=0)); return s, free
            st, pre, tps = simulate_solution(make(), budget=2048, num_blocks=1000, long_prefill=lp, step_fn=rec)
            print(f"budget 2048, long_prefill_token_threshold {lp:3d}: {st} steps, largest chunk given to one request in a step: {max(biggest)} tokens")''',
    takeaways=r'''
        * vLLM V1's scheduler has no prefill or decode phase: each step hands out a token budget so every request's computed tokens catch up with its known tokens.
        * Running requests are served first; new requests fill the remaining budget, with long prompts split into chunks (chunked prefill is on by default).
        * When KV blocks run out, the most recently admitted running request is preempted: its blocks are freed and it is recomputed later.''',
))

# ------------------------------------------------------------------ 04
NBS.append(dict(
    slug='04_memory_planner', title='04 · Planning GPU memory: weights, KV cache and concurrency', deck='vllm/08-running-and-tuning/', deck_name='Running and tuning vLLM', minutes=25,
    goals='how `gpu_memory_utilization` splits a GPU into weights, activation workspace and KV cache, the KV bytes per token of a model, and the resulting maximum number of concurrent tokens and requests.',
    setup=r'''
GiB = 2 ** 30
MODELS = {  # layers, KV heads, head dim, parameters (billions)
    "Llama-3.1-8B":  dict(L=32, kv=8, d=128, P=8.03),
    "Llama-3.1-70B": dict(L=80, kv=8, d=128, P=70.6),
    "Qwen2.5-7B":    dict(L=28, kv=4, d=128, P=7.62),
}
''',
    tasks=[
        dict(fn='kv_bytes_per_token', title='KV bytes per token', md=r'''
            Each token stores a key and a value vector per layer per KV head: `2 × L × kv_heads × head_dim × bytes`. Return it for a model dict and a dtype size (2 for BF16, 1 for an FP8 KV cache).''',
             starter=r'''
            def kv_bytes_per_token(m, dtype_bytes=2):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_kv_bytes_per_token(f):
                assert f(MODELS["Llama-3.1-8B"]) == 131072, "Llama-3.1-8B: 128 KiB per token in BF16"
                assert f(MODELS["Llama-3.1-8B"], 1) == 65536''',
             solution=r'''
            def kv_bytes_per_token_solution(m, dtype_bytes=2):
                return 2 * m["L"] * m["kv"] * m["d"] * dtype_bytes'''),
        dict(fn='kv_capacity', title='How many tokens fit?', md=r'''
            vLLM uses `gpu_memory_utilization × GPU memory` in total (default **0.92** in v0.31.0). From that it subtracts the weights (P × bytes per weight) and the activation peak measured while profiling, and gives the rest to the KV cache.
            Return `(kv_gib, max_tokens, max_requests)` for a context of `ctx` tokens per request (max_requests = floor(max_tokens / ctx)).''',
             starter=r'''
            def kv_capacity(m, gpu_gib=80, util=0.92, weight_bytes=2, act_gib=4, kv_dtype_bytes=2, ctx=8192):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_kv_capacity(f):
                kv, tok, req = f(MODELS["Llama-3.1-8B"])
                assert abs(kv - (0.92 * 80 - 8.03e9 * 2 / GiB - 4)) < 1e-6
                assert tok == int(kv * GiB // 131072) and req == tok // 8192
                assert f(MODELS["Llama-3.1-8B"], kv_dtype_bytes=1)[1] == 2 * tok or abs(f(MODELS["Llama-3.1-8B"], kv_dtype_bytes=1)[1] - 2 * tok) <= 1, "FP8 KV doubles capacity"
                assert f(MODELS["Llama-3.1-70B"])[0] < 0, "70B in BF16 does not fit on one 80 GB GPU"''',
             solution=r'''
            def kv_capacity_solution(m, gpu_gib=80, util=0.92, weight_bytes=2, act_gib=4, kv_dtype_bytes=2, ctx=8192):
                kv_gib = util * gpu_gib - m["P"] * 1e9 * weight_bytes / GiB - act_gib
                tokens = int(kv_gib * GiB // kv_bytes_per_token_solution(m, kv_dtype_bytes)) if kv_gib > 0 else 0
                return kv_gib, tokens, tokens // ctx'''),
        dict(fn='tp_capacity', title='Tensor parallelism frees KV space', md=r'''
            With tensor parallelism `tp`, each GPU holds 1/tp of the weights and of the KV heads (so 1/tp of the KV bytes per token). Return the total number of KV tokens the `tp` GPUs together can hold for the model (same per-GPU budget as above).''',
             starter=r'''
            def tp_capacity(m, tp, gpu_gib=80, util=0.92, weight_bytes=2, act_gib=4, kv_dtype_bytes=2):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_tp_capacity(f):
                m = MODELS["Llama-3.1-70B"]
                assert f(m, 1) == 0 and f(m, 2) > 0, "70B fits with TP = 2"
                assert f(m, 4) > 2 * f(m, 2), "doubling TP more than doubles KV capacity: weights per GPU shrink too"''',
             solution=r'''
            def tp_capacity_solution(m, tp, gpu_gib=80, util=0.92, weight_bytes=2, act_gib=4, kv_dtype_bytes=2):
                per_gpu = util * gpu_gib - m["P"] * 1e9 * weight_bytes / GiB / tp - act_gib
                if per_gpu <= 0: return 0
                return int(per_gpu * GiB // (kv_bytes_per_token_solution(m, kv_dtype_bytes) / tp))'''),
    ],
    explore_md=r'''
        **A planning table.** KV capacity and concurrent 8K-token requests for each model on an 80 GB GPU, in BF16 and with an FP8 KV cache (`--kv-cache-dtype fp8`).''',
    explore=r'''
        for name, m in MODELS.items():
            for tp in [1, 2, 4]:
                bf, f8 = tp_capacity_solution(m, tp), tp_capacity_solution(m, tp, kv_dtype_bytes=1)
                if bf or f8: print(f"{name:14s} TP={tp}: {bf:9,d} KV tokens BF16 ({bf // 8192:4d} × 8K requests) | FP8 KV {f8:9,d} ({f8 // 8192:4d})")''',
    takeaways=r'''
        * KV bytes per token = 2 × layers × KV heads × head dim × bytes; GQA (few KV heads) and FP8 KV caches shrink it.
        * vLLM reserves `gpu_memory_utilization` (0.92 by default in v0.31.0) of GPU memory, subtracts weights and the profiled activation peak, and pages the rest as KV blocks.
        * Tensor parallelism splits both weights and KV heads, so KV capacity grows faster than the GPU count.''',
))

# ------------------------------------------------------------------ 05
NBS.append(dict(
    slug='05_ngram_speculation', title='05 · N-gram speculative decoding', deck='vllm/06-speculative-decoding/', deck_name='Speculative decoding in vLLM', minutes=30,
    goals='the n-gram ("prompt lookup") proposer vLLM ships, greedy verification of proposed tokens, and the expected tokens per step for a given acceptance rate.',
    setup=r'''
CODE = "def add(a, b): return a + b . def sub(a, b): return a - b . def mul(a, b): return a * b .".split()
''',
    tasks=[
        dict(fn='ngram_propose', title='Propose by matching the last n tokens', md=r'''
            Find the most recent earlier occurrence of the last `n` tokens in the context (excluding the suffix itself) and propose the `k` tokens that followed it. Try n from `max_n` down to `min_n`; return `[]` if nothing matches. This is the idea behind vLLM's `method="ngram"` (prompt lookup decoding).''',
             starter=r'''
            def ngram_propose(tokens, k=3, max_n=3, min_n=1):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_ngram_propose(f):
                ctx = CODE[:CODE.index("sub(a,") + 2]       # ... "def", "sub(a,", "b):"
                assert f(ctx, k=3) == ["return", "a", "+"], "the earlier 'b):' was followed by 'return a +'"
                assert f(["x", "y", "z"], k=2) == [], "no earlier match"''',
             solution=r'''
            def ngram_propose_solution(tokens, k=3, max_n=3, min_n=1):
                for n in range(max_n, min_n - 1, -1):
                    if len(tokens) <= n: continue
                    suffix = tokens[-n:]
                    for s in range(len(tokens) - n - 1, -1, -1):
                        if tokens[s:s + n] == suffix:
                            return tokens[s + n:s + n + k]
                return []'''),
        dict(fn='verify_greedy', title='Verify against the target model', md=r'''
            The target model scores all proposed positions in one forward pass. With greedy decoding, accept proposals left to right while they equal the target's own choice; at the first mismatch take the target's token instead. If all k are accepted, the pass also yields one bonus token. Return the list of tokens emitted this step (always ≥ 1).''',
             starter=r'''
            def verify_greedy(proposal, target_next):
                """target_next[i] = the target model's greedy token at proposal position i (len = len(proposal) + 1)."""
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_verify_greedy(f):
                assert f(["a", "b", "c"], ["a", "b", "c", "d"]) == ["a", "b", "c", "d"], "all accepted + bonus"
                assert f(["a", "x", "c"], ["a", "b", "c", "d"]) == ["a", "b"], "stop at first mismatch, emit the target's token"
                assert f([], ["z"]) == ["z"], "no proposal = ordinary decoding"''',
             solution=r'''
            def verify_greedy_solution(proposal, target_next):
                out = []
                for p, t in zip(proposal, target_next):
                    if p != t:
                        return out + [t]
                    out.append(p)
                return out + [target_next[len(proposal)]]'''),
        dict(fn='expected_tokens', title='Expected tokens per target pass', md=r'''
            If each proposed token is accepted independently with probability α and k tokens are proposed, the expected number of tokens per target forward pass is (1 − α^(k+1)) / (1 − α) (Leviathan et al., 2023). Return it (handle α = 1).''',
             starter=r'''
            def expected_tokens(alpha, k):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_expected_tokens(f):
                assert abs(f(0.0, 4) - 1) < 1e-12 and abs(f(1.0, 4) - 5) < 1e-12
                assert abs(f(0.8, 4) - (1 - 0.8 ** 5) / 0.2) < 1e-12''',
             solution=r'''
            def expected_tokens_solution(alpha, k):
                return k + 1.0 if alpha == 1 else (1 - alpha ** (k + 1)) / (1 - alpha)'''),
    ],
    explore_md=r'''
        **Where n-gram speculation shines.** Repetitive outputs (code edits, quoting the prompt, structured data) give high acceptance. Simulate decoding `CODE` with a "target" that always knows the next token and count target passes.''',
    explore=r'''
        for k in [1, 3, 5]:
            ctx, passes = CODE[:8], 0
            while len(ctx) < len(CODE):
                prop = ngram_propose_solution(ctx, k=k)
                target = CODE[len(ctx):len(ctx) + len(prop) + 1] + ["<eos>"] * (len(prop) + 1)
                emitted = verify_greedy_solution(prop, target[:len(prop) + 1]); ctx += emitted; passes += 1
            print(f"k={k}: {len(CODE) - 8} tokens in {passes} target passes ({(len(CODE) - 8) / passes:.2f} tokens/pass)")
        for a in [0.5, 0.7, 0.9]:
            print(f"alpha={a}: expected tokens/pass with k=4: {expected_tokens_solution(a, 4):.2f}")''',
    takeaways=r'''
        * Speculative decoding lets a cheap proposer guess k tokens and the target verify them in one pass; the output is identical to the target's own.
        * vLLM's n-gram method needs no draft model: it copies continuations of earlier matching n-grams from the context.
        * Speed-up depends on acceptance: (1 − α^(k+1)) / (1 − α) tokens per pass, minus the proposer and verification overhead.''',
))
