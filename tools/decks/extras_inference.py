"""Per-deck extras for the Inference guide. Every number in a worked example is computed here, not typed."""
from math import ceil

GiB, KiB = 2 ** 30, 2 ** 10
H100_BW = 3.35e12          # H100 SXM HBM3 bandwidth, bytes/s (spec sheet)
H100_BF16 = 989e12         # H100 SXM dense BF16 tensor FLOP/s (spec sheet)

P = dict(  # verified papers (titles and numbers checked against the arXiv abstracts / conference page)
    pope=dict(title='Efficiently Scaling Transformer Inference', authors='Pope et al.', year=2023, venue='MLSys', url='https://arxiv.org/abs/2211.05102',
              summary='An analytical model of inference cost that picks how to partition a model across chips for a given latency target; shows prefill and decode need different strategies and that multi-query attention allows much longer contexts.',
              number='29 ms/token on PaLM 540B with int8 weights; 76% MFU on large-batch prefill; MQA enables up to 32× longer context'),
    distserve=dict(title='DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving', authors='Zhong et al.', year=2024, venue='OSDI', url='https://arxiv.org/abs/2401.09670',
                   summary='Defines serving quality as goodput, the request rate served within both TTFT and TPOT targets, and runs prefill and decode on separate GPUs so they stop interfering.',
                   number='7.4× more requests or 12.6× tighter SLO than colocated systems'),
    splitwise=dict(title='Splitwise: Efficient Generative LLM Inference Using Phase Splitting', authors='Patel et al.', year=2024, venue='ISCA', url='https://arxiv.org/abs/2311.18677',
                   summary='Characterizes prompt computation as compute-intensive and token generation as memory-intensive, and splits them onto separate machines, possibly of different GPU types.',
                   number='1.4× throughput at 20% lower cost, or 2.35× throughput at the same cost and power'),
    mqa=dict(title='Fast Transformer Decoding: One Write-Head is All You Need', authors='Shazeer', year=2019, venue='arXiv', url='https://arxiv.org/abs/1911.02150',
             summary='Introduces multi-query attention: all heads share one key/value head, cutting the memory bandwidth of incremental decoding with only minor quality loss.',
             number='1 K/V head instead of h'),
    gqa=dict(title='GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints', authors='Ainslie et al.', year=2023, venue='EMNLP', url='https://arxiv.org/abs/2305.13245',
             summary='Grouped-query attention: an intermediate number of key/value heads, plus a recipe to convert existing multi-head checkpoints.',
             number='quality close to MHA, speed close to MQA; uptraining with 5% of the original pretraining compute'),
    dsv2=dict(title='DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model', authors='DeepSeek-AI', year=2024, venue='arXiv', url='https://arxiv.org/abs/2405.04434',
              summary='Introduces multi-head latent attention (MLA), which compresses keys and values into a small latent vector per token, alongside a Mixture-of-Experts design.',
              number='KV cache reduced by 93.3%; maximum generation throughput 5.76× vs DeepSeek 67B'),
    orca=dict(title='Orca: A Distributed Serving System for Transformer-Based Generative Models', authors='Yu et al.', year=2022, venue='OSDI', url='https://www.usenix.org/conference/osdi22/presentation/yu',
              summary='Iteration-level scheduling (requests join and leave the batch after every decode step) plus selective batching (batch the matmuls, run attention per request).',
              number='36.9× throughput over FasterTransformer at the same latency (GPT-3 175B)'),
    vllm=dict(title='Efficient Memory Management for Large Language Model Serving with PagedAttention', authors='Kwon et al.', year=2023, venue='SOSP', url='https://arxiv.org/abs/2309.06180',
              summary='Stores the KV cache in fixed-size blocks mapped by a block table, like virtual memory pages, giving near-zero fragmentation and sharing with copy-on-write. The basis of vLLM.',
              number='2–4× throughput vs FasterTransformer and Orca at the same latency'),
    sglang=dict(title='SGLang: Efficient Execution of Structured Language Model Programs', authors='Zheng et al.', year=2024, venue='NeurIPS', url='https://arxiv.org/abs/2312.07104',
                summary='A runtime and frontend for multi-call LLM programs; RadixAttention keeps KV caches in a radix tree so shared prefixes are reused across requests automatically.',
                number='up to 6.4× higher throughput'),
    sarathi=dict(title='SARATHI: Efficient LLM Inference by Piggybacking Decodes with Chunked Prefills', authors='Agrawal et al.', year=2023, venue='arXiv', url='https://arxiv.org/abs/2308.16369',
                 summary='Splits prefills into equal chunks and fills the rest of each batch with decodes, which "piggyback" on the compute-heavy chunk.',
                 number='up to 10× decode throughput (LLaMA-13B, A6000)'),
    sarathi_serve=dict(title='Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve', authors='Agrawal et al.', year=2024, venue='OSDI', url='https://arxiv.org/abs/2403.02310',
                       summary='Chunked prefills plus stall-free scheduling: new requests are added without pausing ongoing decodes, so throughput rises without TPOT spikes.',
                       number='2.6× serving capacity (Mistral-7B, 1 A100) and up to 3.7× (Yi-34B, 2 A100s) vs vLLM; up to 5.6× with pipeline parallelism (Falcon-180B)'),
    leviathan=dict(title='Fast Inference from Transformers via Speculative Decoding', authors='Leviathan et al.', year=2023, venue='ICML', url='https://arxiv.org/abs/2211.17192',
                   summary='A small model drafts tokens, the large model verifies them in parallel, and a modified rejection rule keeps the output distribution exactly unchanged.',
                   number='2–3× faster on T5-XXL with identical outputs'),
    chen=dict(title='Accelerating Large Language Model Decoding with Speculative Sampling', authors='Chen et al.', year=2023, venue='arXiv', url='https://arxiv.org/abs/2302.01318',
              summary='Independent derivation of speculative sampling with a modified rejection scheme that preserves the target distribution.',
              number='2–2.5× decoding speedup on Chinchilla 70B'),
    int8=dict(title='LLM.int8(): 8-bit Matrix Multiplication for Transformers at Scale', authors='Dettmers et al.', year=2022, venue='NeurIPS', url='https://arxiv.org/abs/2208.07339',
              summary='Finds systematic outlier features in large transformers and handles them with a mixed-precision decomposition: outlier dimensions in 16-bit, everything else in 8-bit.',
              number='more than 99.9% of values multiplied in 8-bit, no degradation up to 175B'),
    smoothquant=dict(title='SmoothQuant: Accurate and Efficient Post-Training Quantization for Large Language Models', authors='Xiao et al.', year=2023, venue='ICML', url='https://arxiv.org/abs/2211.10438',
                     summary='Migrates quantization difficulty from activation outliers to weights with a mathematically equivalent per-channel scaling, enabling W8A8 (8-bit weights and activations).',
                     number='up to 1.56× speedup and 2× memory reduction'),
    gptq=dict(title='GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers', authors='Frantar et al.', year=2023, venue='ICLR', url='https://arxiv.org/abs/2210.17323',
              summary='One-shot weight quantization using approximate second-order information, quantizing one column at a time and compensating the error in the rest.',
              number='175B model to 3–4 bits in about four GPU hours'),
    awq=dict(title='AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration', authors='Lin et al.', year=2024, venue='MLSys', url='https://arxiv.org/abs/2306.00978',
             summary='Weight-only low-bit quantization that protects the most important weight channels, chosen by activation magnitude, by scaling them up before quantizing.',
             number='protecting 1% of salient weights greatly reduces error; >3× over Hugging Face FP16 with its TinyChat kernels'),
    fp8=dict(title='FP8 Formats for Deep Learning', authors='Micikevicius et al.', year=2022, venue='arXiv', url='https://arxiv.org/abs/2209.05433',
             summary='Defines the two FP8 encodings, E4M3 (more precision) and E5M2 (more range), and shows FP8 training and post-training quantization matching 16-bit results.',
             number='E4M3 max 448, E5M2 max 57,344'),
    megatron=dict(title='Megatron-LM: Training Multi-Billion Parameter Language Models Using Model Parallelism', authors='Shoeybi et al.', year=2019, venue='arXiv', url='https://arxiv.org/abs/1909.08053',
                  summary='Intra-layer (tensor) model parallelism that splits each attention and MLP block across GPUs with only a few all-reduce operations, implemented in plain PyTorch.',
                  number='2 all-reduces per transformer block in the forward pass; 76% scaling efficiency on 512 GPUs'),
)

EXTRAS = {}

# ------------------------------------------------------------------ 01
_P, _N, _O = 8.03e9, 2000, 300
_prefill_flop = 2 * _P * _N
_ttft = _prefill_flop / (0.4 * H100_BF16)
_step = 2 * _P / H100_BW
EXTRAS['01-inference-workload'] = dict(
    glance=dict(steps=[('request', 'arrives, waits in queue', 'f'), ('prefill', 'whole prompt in one pass\ncompute-bound', 'a'), ('first token', 'TTFT ends here', 'e'),
                       ('decode step', 'one token per sequence\nmemory-bound', 'b'), ('done', 'end-of-sequence or limit', 'f')],
                loop=(3, 3, 'repeat once per output token: each step takes one TPOT'),
                caption='Every request has one compute-heavy prefill, then many memory-heavy decode steps.'),
    example=dict(title='Worked example: latency of one request',
                 setup='Llama-3-8B (8.03B parameters, BF16) on one H100 SXM. A 2,000-token prompt and a 300-token answer, at batch size 1. Spec sheet: 989 TFLOP/s dense BF16, 3.35 TB/s HBM (high-bandwidth memory). Assume prefill reaches 40% of peak.',
                 steps=[f'Prefill compute ≈ 2 × parameters × prompt tokens = 2 × 8.03B × 2,000 = <b>{_prefill_flop / 1e12:.1f} TFLOP</b>.',
                        f'TTFT ≈ {_prefill_flop / 1e12:.1f} TFLOP ÷ (0.4 × 989 TFLOP/s) ≈ <b>{_ttft * 1e3:.0f} ms</b> (plus any queueing).',
                        f'Each decode step must read all weights once: 2 bytes × 8.03B = 16.1 GB at 3.35 TB/s ≈ <b>{_step * 1e3:.1f} ms</b>. That is the TPOT floor at batch 1.',
                        f'Decode total ≈ {_O - 1} more tokens × {_step * 1e3:.1f} ms ≈ <b>{(_O - 1) * _step:.2f} s</b>.'],
                 result=f'End-to-end ≈ {_ttft:.2f} + {(_O - 1) * _step:.2f} ≈ <b>{_ttft + (_O - 1) * _step:.2f} s</b>, and decode is {(_O - 1) * _step / (_ttft + (_O - 1) * _step) * 100:.0f}% of it. At batch 1 the GPU does ~{2 * _P / _step / 1e12:.0f} TFLOP/s during decode, a few percent of peak, which is why batching (deck 03) matters.'),
    traps=dict(tricks=[('Forward FLOPs ≈ 2 × parameters per token.', 'Prefill cost ≈ 2·N·prompt_tokens; good to within the attention term for normal contexts.'),
                       ('Decode floor ≈ bytes read ÷ HBM bandwidth.', 'At small batch, TPOT ≈ (weight bytes + KV bytes) / bandwidth, not FLOPs / peak.'),
                       ('Latency ≈ TTFT + (output − 1) × TPOT.', 'Long answers are dominated by decode; long prompts by prefill.'),
                       ('Quote goodput, not throughput.', 'Requests per second that meet both the TTFT and TPOT SLOs.')],
               traps=[('Comparing tokens/s across workloads.', 'Prompt-heavy and output-heavy mixes give very different numbers on the same server.'),
                      ('Averages instead of percentiles.', 'p99 TTFT and TPOT are what break products; means hide them.'),
                      ('Forgetting the queue.', 'Measured TTFT includes waiting time; under load it can dominate prefill.'),
                      ('Counting prompt tokens as generated.', 'Input tokens/s and output tokens/s are different metrics with different costs.')]),
    papers=[P['pope'], P['distserve'], P['splitwise']],
)

# ------------------------------------------------------------------ 02
_per_tok = 2 * 80 * 8 * 128 * 2
_seq = _per_tok * 8192
EXTRAS['02-kv-cache'] = dict(
    glance=dict(steps=[('new token', 'embedding of the latest token', 'f'), ('q, k, v', 'computed for this token only', 'a'), ('append k, v', 'to every layer\'s cache', 'b'),
                       ('attend', 'q · all cached keys\n→ weights × cached values', 'c'), ('next token', 'sample, feed back in', 'e')],
                loop=(4, 0, 'one decode step per token; the cache grows by one entry per layer each step'),
                caption='The cache turns "recompute the whole prefix" into "compute one token and read the past".'),
    example=dict(title='Worked example: how big is the cache?',
                 setup='Llama-3-70B: 80 layers, 8 KV (key-value) heads (GQA), head dimension 128, BF16 (2 bytes). Context 8,192 tokens, batch 32.',
                 steps=[f'Per token: 2 (K and V) × 80 layers × 8 heads × 128 × 2 bytes = <b>{_per_tok:,} bytes = {_per_tok // KiB} KiB</b>.',
                        f'Per sequence at 8,192 tokens: {_per_tok // KiB} KiB × 8,192 = <b>{_seq / GiB:.1f} GiB</b>.',
                        f'Batch of 32: <b>{32 * _seq / GiB:.0f} GiB</b>, about as much as the 70B weights in FP8.',
                        f'Without GQA (64 KV heads, one per query head) it would be 8× larger: <b>{8 * 32 * _seq / GiB:.0f} GiB</b>.'],
                 result=f'Rule: KV bytes per token = 2 × layers × KV heads × head_dim × bytes. For this model, every 1,000 tokens of context costs <b>{_per_tok * 1000 / GiB:.2f} GiB</b> per sequence.'),
    traps=dict(tricks=[('KV bytes/token = 2·L·n_kv·d_head·bytes.', 'Use KV heads, not query heads.'),
                       ('Total = per-token × context × batch.', 'Batch and context trade against each other for the same memory.'),
                       ('GQA saves n_heads / n_kv.', 'Llama-3-70B: 64 query heads / 8 KV heads = 8× smaller cache.'),
                       ('Break-even with weights.', 'Context × batch where KV = weight bytes tells you when memory, not weights, limits concurrency.')],
               traps=[('Using num_attention_heads.', 'With GQA the cache scales with num_key_value_heads; using query heads overestimates by the group factor.'),
                      ('Dropping the factor 2.', 'There are two cached tensors, K and V.'),
                      ('Caching queries.', 'Past queries are never reused; only K and V are cached.'),
                      ('Thinking the cache changes outputs.', 'It is exact: identical logits to recomputing everything.')]),
    papers=[P['mqa'], P['gqa'], P['dsv2'], P['pope']],
)

# ------------------------------------------------------------------ 03
_lens = [10, 20, 50, 200]
_static_slots = len(_lens) * max(_lens)
EXTRAS['03-batching'] = dict(
    glance=dict(steps=[('waiting queue', 'new requests', 'f'), ('admit', 'if a slot and KV memory are free', 'a'), ('one decode step', 'whole batch together', 'b'),
                       ('evict finished', 'free slot and KV now', 'e')],
                loop=(3, 1, 'every iteration: the batch is recomposed'),
                caption='Scheduling happens per iteration (one decode step), not per batch.'),
    example=dict(title='Worked example: slots wasted by static batching',
                 setup=f'Four requests start together and need {", ".join(map(str, _lens))} output tokens.',
                 steps=[f'Static batching keeps the batch together until the longest finishes: 4 slots × {max(_lens)} steps = <b>{_static_slots} slot-steps</b> reserved.',
                        f'Useful work is only {" + ".join(map(str, _lens))} = <b>{sum(_lens)} slot-steps</b>.',
                        f'Utilization = {sum(_lens)} / {_static_slots} = <b>{sum(_lens) / _static_slots:.0%}</b>; the three short requests also wait for the batch to finish before being returned.',
                        'Continuous batching refills each slot the iteration after it frees, so with a queue of waiting requests the slots stay ~100% busy.'],
                 result=f'Same hardware, same model: in this example continuous batching does up to <b>{_static_slots / sum(_lens):.1f}×</b> more useful work per step, and short requests return as soon as they finish.'),
    traps=dict(tricks=[('Granularity = one decode step.', 'Join and leave between iterations; never wait for the batch to drain.'),
                       ('Selective batching.', 'Batch the matmuls across requests; run attention per request, because each has its own KV length.'),
                       ('Throughput ∝ batch while memory-bound.', 'Adding sequences reuses the same weight read until compute becomes the limit.')],
               traps=[('Padding to the longest sequence.', 'Wastes compute and memory; continuous batching with paged KV avoids it.'),
                      ('Ignoring KV memory.', 'Batch size is capped by free KV memory, not only by a configured maximum; engines preempt when it runs out.'),
                      ('Assuming bigger batch is always better.', 'TPOT rises with batch; past the SLO, more batch adds no goodput.')]),
    papers=[P['orca'], P['vllm']],
)

# ------------------------------------------------------------------ 04
_budget, _decodes, _prompt = 512, 100, 8000
_left = _budget - _decodes
EXTRAS['04-chunked-prefill'] = dict(
    glance=dict(steps=[('token budget', 'per iteration, e.g. 512', 'f'), ('decodes first', '1 token each, never paused', 'b'), ('prefill chunk', 'fills the remaining budget', 'a'),
                       ('one forward pass', 'mixed batch', 'c')],
                loop=(3, 0, 'next iteration: the next chunk of the same prompt continues'),
                caption='Every iteration has a bounded size, so decode latency stays flat while long prompts stream in.'),
    example=dict(title='Worked example: an 8,000-token prompt arrives',
                 setup=f'{_decodes} sequences are decoding. Token budget per iteration: {_budget}.',
                 steps=[f'Prefill-first: the next iteration processes {_prompt:,} + {_decodes} = <b>{_prompt + _decodes:,} tokens</b>; every running sequence waits for it (a TPOT spike).',
                        f'Chunked: decodes take {_decodes} tokens of the budget, leaving <b>{_left}</b> for the new prompt.',
                        f'The prompt is processed in ⌈{_prompt:,} / {_left}⌉ = <b>{ceil(_prompt / _left)} chunks</b>, each iteration at most {_budget} tokens.',
                        'Each chunk attends to the KV of earlier chunks, so the result is identical to one big prefill.'],
                 result=f'Running sequences never stall: every iteration is ≤ {_budget} tokens instead of one {_prompt + _decodes:,}-token iteration. The cost: the new request\'s TTFT is spread over {ceil(_prompt / _left)} iterations.'),
    traps=dict(tricks=[('Size the budget from the TPOT SLO.', 'Pick the largest budget whose iteration time still meets the TPOT target.'),
                       ('Decodes piggyback.', 'A decode token costs little extra when batched with a compute-heavy prefill chunk.'),
                       ('Chunking is exact.', 'Later chunks attend to earlier chunks\' cached K and V.')],
               traps=[('Chunks too small.', 'Low arithmetic intensity, and each chunk re-reads the growing KV of earlier chunks.'),
                      ('Expecting less total work.', 'Chunking reorganizes prefill, it does not remove FLOPs (and adds a little overhead).'),
                      ('Ignoring TTFT.', 'Long prompts finish prefill later than with prefill-first; that is the trade being made.')]),
    papers=[P['sarathi'], P['sarathi_serve']],
)

# ------------------------------------------------------------------ 05
_bs, _len, _max = 16, 1000, 4096
_blocks = ceil(_len / _bs)
_waste = _blocks * _bs - _len
EXTRAS['05-paged-attention'] = dict(
    glance=dict(steps=[('sequence', 'logical token positions', 'f'), ('logical blocks', '16 tokens each', 'a'), ('block table', 'logical → physical', 'c'),
                       ('physical blocks', 'anywhere in GPU memory\nshared blocks ref-counted', 'b')],
                caption='Like virtual memory: contiguous for the sequence, scattered in the GPU.'),
    example=dict(title='Worked example: memory wasted per sequence',
                 setup=f'Block size {_bs} tokens (vLLM\'s default). A sequence ends at {_len:,} tokens; the server\'s maximum length is {_max:,}.',
                 steps=[f'Paged: ⌈{_len:,} / {_bs}⌉ = <b>{_blocks} blocks</b>, holding {_blocks * _bs:,} slots.',
                        f'Waste = {_blocks * _bs:,} − {_len:,} = <b>{_waste} tokens</b> ({_waste / (_blocks * _bs):.1%}), only in the last block.',
                        f'Contiguous reservation for the maximum length: {_max:,} − {_len:,} = <b>{_max - _len:,} tokens</b> wasted ({(_max - _len) / _max:.1%}).',
                        'Prefix sharing: 8 parallel samples of the same prompt share its blocks (ref count 8) and copy a block only when they diverge.'],
                 result=f'Waste falls from {(_max - _len) / _max:.0%} to under {_waste / (_blocks * _bs) * 100 + 0.5:.0f}% here; at most block_size − 1 = {_bs - 1} tokens per sequence, whatever its length.'),
    traps=dict(tricks=[('Internal waste ≤ block_size − 1 tokens.', 'Per sequence, independent of length.'),
                       ('Copy-on-write.', 'Parallel sampling and beam search share prompt blocks until a block is written.'),
                       ('Prefix cache = skip prefill.', 'A shared system prompt already in cache costs no prefill compute for later requests.')],
               traps=[('Blocks too small.', 'More table lookups and less efficient memory access in the attention kernel.'),
                      ('Prefix match must be exact tokens.', 'One different token early in the prompt invalidates everything after it.'),
                      ('Cache eviction.', 'Under memory pressure, least-recently-used prefixes are evicted; a hot prefix can still miss.')]),
    papers=[P['vllm'], P['sglang']],
)

# ------------------------------------------------------------------ 06
_a, _g, _c = 0.8, 4, 0.05
_etok = (1 - _a ** (_g + 1)) / (1 - _a)
_speed = _etok / (_g * _c + 1)
EXTRAS['06-speculative-decoding'] = dict(
    glance=dict(steps=[('draft γ tokens', 'small model, cheap', 'b'), ('verify in one pass', 'target scores all γ + 1 positions', 'a'), ('accept / reject', 'modified rejection sampling', 'c'),
                       ('emit', 'accepted prefix\n+ 1 token from the target', 'e')],
                loop=(3, 0, 'repeat from the last accepted token'),
                caption='Exact: the output distribution is the target model\'s.'),
    example=dict(title='Worked example: expected speedup',
                 setup=f'Acceptance rate α = {_a}, draft length γ = {_g}, and a draft that costs c = {_c} of a target forward pass.',
                 steps=[f'Expected tokens per target pass = (1 − α<sup>γ+1</sup>) / (1 − α) = (1 − {_a}<sup>{_g + 1}</sup>) / {1 - _a:.1f} = <b>{_etok:.2f}</b>.',
                        f'Cost per iteration = γ·c + 1 = {_g} × {_c} + 1 = <b>{_g * _c + 1:.2f}</b> target-pass equivalents.',
                        f'Speedup = {_etok:.2f} / {_g * _c + 1:.2f} ≈ <b>{_speed:.1f}×</b>.',
                        f'With α = 0.5 instead: tokens = {(1 - 0.5 ** 5) / 0.5:.2f}, speedup ≈ {(1 - 0.5 ** 5) / 0.5 / 1.2:.1f}×. Draft quality matters more than draft length.'],
                 result='Formulas from Leviathan et al. (2023). This assumes the target pass costs the same for 1 or γ + 1 tokens, which holds while decode is memory-bound (small batch).'),
    traps=dict(tricks=[('E[tokens] = (1 − α^(γ+1)) / (1 − α).', 'Speedup = E[tokens] / (γc + 1).'),
                       ('Best at small batch.', 'Verifying γ + 1 tokens is nearly free only while the target is memory-bound.'),
                       ('Every iteration emits ≥ 1 token.', 'Even if all drafts are rejected, the target\'s own token is kept.')],
               traps=[('Assuming it changes outputs.', 'With the modified rejection rule the samples are exactly from the target distribution.'),
                      ('Using it at large batch.', 'When decode is already compute-bound, the extra verification FLOPs reduce or erase the gain.'),
                      ('Ignoring draft cost and KV.', 'The draft model also needs memory, its own KV cache and time; c is not zero.')]),
    papers=[P['leviathan'], P['chen']],
)

# ------------------------------------------------------------------ 07
_W = 70e9
_bytes = {'BF16': 2, 'INT8': 1, 'INT4': 0.5}
_scale_bits = 16 / 128
EXTRAS['07-quantization'] = dict(
    glance=dict(steps=[('BF16 weights', 'and activations', 'f'), ('pick granularity', 'tensor / channel / group', 'c'), ('scales + codes', 'INT8, INT4, FP8', 'a'),
                       ('matmul', 'dequantize or low-bit kernel', 'b'), ('fewer bytes', 'faster decode, more KV room', 'e')],
                caption='Quantization trades a little accuracy for fewer bytes to store and to read.'),
    example=dict(title='Worked example: memory and decode speed for a 70B model',
                 setup='70B parameters; group-wise INT4 uses one FP16 scale per 128 weights. Decode at batch 1 reads every weight once per token (H100: 3.35 TB/s).',
                 steps=[f'BF16: 70B × 2 bytes = <b>{_W * 2 / 1e9:.0f} GB</b>; INT8: <b>{_W / 1e9:.0f} GB</b>; INT4: <b>{_W * 0.5 / 1e9:.0f} GB</b>.',
                        f'INT4 scale overhead: 16 bits / 128 weights = {_scale_bits:.3f} bits per weight → +{_W * _scale_bits / 8 / 1e9:.1f} GB, so {4 + _scale_bits:.3f} effective bits.',
                        f'Time to read the weights once: BF16 {_W * 2 / H100_BW * 1e3:.0f} ms, INT8 {_W / H100_BW * 1e3:.0f} ms, INT4 {_W * (0.5 + _scale_bits / 8) / H100_BW * 1e3:.0f} ms (bandwidth only, as if on one GPU).',
                        'Prefill is compute-bound, so weight-only INT4 helps it far less unless the kernel computes in low precision.'],
                 result=f'Weight-only INT4 cuts the per-token weight read about {2 / (0.5 + _scale_bits / 8):.1f}× vs BF16. That speeds memory-bound decode and frees memory for KV cache.'),
    traps=dict(tricks=[('Effective bits = bits + scale_bits / group_size.', 'INT4 with FP16 scales per 128 → 4.125 bits.'),
                       ('Weight-only quantization speeds decode.', 'Decode is bandwidth-bound; fewer bytes per weight = faster steps.'),
                       ('Handle outliers.', 'Per-channel scales, SmoothQuant\'s migration (α = 0.5 default), or keep outlier dimensions in 16-bit (LLM.int8()).')],
               traps=[('Per-tensor activation scales.', 'A few outlier channels blow up the scale and crush everything else to zero.'),
                      ('Forgetting the scales.', 'Group scales add real memory; group size trades accuracy for overhead.'),
                      ('Expecting INT4 compute speedups everywhere.', 'Without low-bit kernels, weights are dequantized and the matmul runs in 16-bit.'),
                      ('Treating KV-cache and weight quantization as the same.', 'KV is quantized at runtime per token; errors accumulate differently.')]),
    papers=[P['int8'], P['smoothquant'], P['gptq'], P['awq'], P['fp8']],
)

# ------------------------------------------------------------------ 08
_w = 140e9
EXTRAS['08-parallelism'] = dict(
    glance=dict(steps=[('X (replicated)', 'every GPU has the input', 'f'), ('W₁ split by columns', 'each GPU: its share\n+ GELU locally', 'a'), ('W₂ split by rows', 'partial outputs', 'b'),
                       ('all-reduce', 'sum partials over NVLink', 'd'), ('Y (replicated)', 'next block', 'f')],
                caption='Megatron MLP: one all-reduce in the forward pass; attention splits by heads the same way.'),
    example=dict(title='Worked example: tensor parallelism for a 70B model',
                 setup='70B parameters in BF16 = 140 GB of weights. H100s with 80 GB each, 3.35 TB/s HBM. 80 layers.',
                 steps=[f'One GPU can\'t even hold the weights (140 GB > 80 GB). TP = 8: <b>{_w / 8 / 1e9:.1f} GB</b> per GPU.',
                        f'Per-token weight read: {_w / H100_BW * 1e3:.1f} ms if one GPU could hold it, vs <b>{_w / 8 / H100_BW * 1e3:.1f} ms</b> with TP = 8, since each GPU reads only its eighth in parallel.',
                        f'Communication: 2 all-reduces per layer × 80 layers = <b>160 all-reduces per token</b>, each only batch × 8,192 × 2 bytes ({8192 * 2 // 1024} KiB at batch 1).',
                        'Those messages are small and latency-bound, so they need NVLink inside one server; across a network they would dominate.'],
                 result=f'TP cuts per-token latency up to ~8× here, minus communication; it is the standard way to serve models larger than one GPU at low latency.'),
    traps=dict(tricks=[('TP lowers latency, PP raises throughput.', 'TP splits every layer across GPUs; PP splits the layers into stages (pipeline parallelism).'),
                       ('Two all-reduces per transformer block.', 'One after attention, one after the MLP (forward pass).'),
                       ('Keep TP within the NVLink domain.', 'Typically TP ≤ GPUs per server.')],
               traps=[('TP across nodes.', 'Hundreds of small all-reduces per token over a slower network erase the gain.'),
                      ('TP degree > KV heads.', 'With 8 KV heads and TP = 16, KV heads must be replicated, wasting cache memory.'),
                      ('Expecting linear speedup.', 'Communication and fixed per-step costs grow with TP degree.')]),
    papers=[P['megatron'], P['pope']],
)

# ------------------------------------------------------------------ 09
_kv = 4000 * _per_tok
EXTRAS['09-disaggregated-serving'] = dict(
    glance=dict(steps=[('request', 'prompt', 'f'), ('prefill pool', 'compute-heavy GPUs\nbuilds KV', 'a'), ('KV transfer', 'network / NVLink', 'd'),
                       ('decode pool', 'memory-heavy GPUs\nstreams tokens', 'b'), ('user', 'tokens arrive', 'f')],
                caption='Each pool gets its own GPUs, parallelism and scale, so prefill bursts don\'t slow ongoing decodes.'),
    example=dict(title='Worked example: what does moving the KV cost?',
                 setup='Llama-3-70B KV cache: 320 KiB per token (deck 02). A 4,000-token prompt.',
                 steps=[f'KV to move: 4,000 × {_per_tok // KiB} KiB = <b>{_kv / GiB:.2f} GiB</b> ({_kv / 1e9:.2f} GB).',
                        f'Over a 400 Gb/s NIC (network interface card, 50 GB/s): <b>{_kv / 50e9 * 1e3:.0f} ms</b>.',
                        f'Over NVLink at 900 GB/s (H100): <b>{_kv / 900e9 * 1e3:.1f} ms</b>.',
                        'Transfer can overlap with prefill layer by layer, so much of it can be hidden.'],
                 result=f'Disaggregation pays when the interference it removes costs more than ~{_kv / 50e9 * 1e3:.0f} ms of transfer per request, which is typical with tight TPOT SLOs and long prompts.'),
    traps=dict(tricks=[('Transfer time = KV bytes ÷ link bandwidth.', 'Compute it before deciding; GQA and FP8 KV shrink it.'),
                       ('Size pools by demand.', 'Ratio of prefill GPUs to decode GPUs follows the prompt/output mix.'),
                       ('Optimize per phase.', 'Different parallelism and even different GPU types per pool (Splitwise).')],
               traps=[('Short prompts, small models.', 'Little interference to remove; the extra hop may cost more than it saves.'),
                      ('Slow links.', 'Without fast interconnect the KV transfer dominates TTFT.'),
                      ('Pool imbalance.', 'A shift in traffic mix leaves one pool idle and the other overloaded.')]),
    papers=[P['distserve'], P['splitwise']],
)

# ------------------------------------------------------------------ 10
_free = 80e9 - 16.06e9 - 6e9
_kvseq = 4096 * 2 * 32 * 8 * 128 * 2
EXTRAS['10-putting-it-together'] = dict(
    glance=dict(steps=[('measure', 'TTFT, TPOT, goodput,\nKV use, batch, queue', 'a'), ('locate', 'which phase?\nwhich resource?', 'c'), ('fix', 'matching technique', 'e'),
                       ('re-measure', 'did the SLO metric move?', 'b')],
                loop=(3, 0, 'one bottleneck at a time'),
                caption='Diagnose by phase (prefill or decode) and resource (compute, memory bandwidth, memory capacity, network).'),
    example=dict(title='Worked example: why is the batch stuck at ~100?',
                 setup='Llama-3-8B in BF16 on one 80 GB H100, 4,096-token contexts. The batch never grows past ~100 and GPU compute utilization is low.',
                 steps=[f'Weights: 16.06 GB. Leave ~6 GB for activations and the runtime → <b>{_free / 1e9:.0f} GB</b> for KV.',
                        f'KV per sequence: 2 × 32 layers × 8 KV heads × 128 × 2 bytes × 4,096 = <b>{_kvseq / GiB:.2f} GiB</b>.',
                        f'Maximum batch ≈ {_free / 1e9:.0f} GB / {_kvseq / 1e9:.2f} GB ≈ <b>{int(_free / _kvseq)}</b> sequences: memory capacity is the bottleneck, not compute.',
                        f'Fixes: FP8 KV halves it → ~{int(_free / (_kvseq / 2))} sequences; paging removes fragmentation; prefix caching shares system prompts; or add GPUs.'],
                 result='Measure → the KV pool is full → resource = memory capacity in decode → apply KV-shrinking techniques, then re-measure TPOT and goodput.'),
    traps=dict(tricks=[('Classify every symptom by phase × resource.', 'High TTFT → prefill compute or queueing; high TPOT → decode bandwidth or interference.'),
                       ('Read utilization correctly.', 'Low compute utilization in decode is normal; low batch with a full KV pool means capacity-bound.'),
                       ('Change one thing at a time.', 'Many techniques interact (chunk size vs TPOT, quantization vs accuracy).')],
               traps=[('Tuning before measuring.', 'Adding speculative decoding to a capacity-bound server does little.'),
                      ('Optimizing averages.', 'Tail latency (p99) is usually what violates SLOs.'),
                      ('Benchmarking an unrealistic mix.', 'Prompt and output length distributions decide which bottleneck you hit.')]),
    papers=[P['vllm'], P['sglang'], P['sarathi_serve'], P['distserve']],
)
