"""Extras for the hand-written GPU decks (inserted by augment.py). Numbers are computed here."""
from math import ceil, sqrt
from papers import PAPERS as P, paper

H100_TF, H100_BW = 989e12, 3.35e12
DOCS = dict(
    h100wp=paper('NVIDIA H100 Tensor Core GPU Architecture (whitepaper)', 'NVIDIA', 'whitepaper', 2022, 'https://resources.nvidia.com/en-us-tensor-core',
                 'The reference for Hopper: SM layout, fourth-generation Tensor Cores, FP8, TMA, thread-block clusters and the memory system.', '132 SMs (H100 SXM5), 989 TFLOP/s dense BF16'),
    mig=paper('NVIDIA Multi-Instance GPU User Guide', 'NVIDIA', 'docs', 2024, 'https://docs.nvidia.com/datacenter/tesla/mig-user-guide/',
              'How to partition a supported GPU into hardware-isolated instances with dedicated SMs, L2 slices and memory.', 'up to 7 instances per H100'),
    nccl=paper('NVIDIA Collective Communications Library (NCCL) documentation', 'NVIDIA', 'docs', 2024, 'https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/index.html',
               'The library that implements all-reduce, all-gather, reduce-scatter, broadcast and all-to-all over NVLink and the network, choosing ring or tree algorithms.', ''),
    nvl72=paper('NVIDIA GB200 NVL72', 'NVIDIA', 'product page', 2024, 'https://www.nvidia.com/en-us/data-center/gb200-nvl72/',
                'A rack-scale NVLink domain: 72 Blackwell GPUs connected all-to-all by NVLink switches.', '130 TB/s aggregate NVLink bandwidth'),
)
EXTRAS = {}

# 01 ------------------------------------------------------------------
_t1, _t2 = 11 * 12, 12 * 12
EXTRAS['01-what-is-a-gpu'] = dict(
    beats=False, glance_in='s-die', example_after='s-wave', traps_after='s-stack',
    glance=dict(steps=[('grid', 'all blocks of one kernel', 'f'), ('blocks', 'scheduled onto SMs', 'c'), ('warps of 32', 'one instruction, 32 lanes', 'a'),
                       ('Tensor Cores', 'matrix multiply per SM', 'b'), ('HBM', 'shared memory pool', 'e')],
                caption='You write one thread; the hardware runs thousands at once in warps of 32 across 132 SMs (streaming multiprocessors).'),
    example=dict(title='Worked example: wave quantization',
                 setup='An H100 SXM has 132 SMs. A matmul is split into 128 × 128 output tiles, and each SM runs one tile at a time.',
                 steps=[f'Output 1,408 × 1,536 → 11 × 12 = <b>{_t1} tiles</b> → exactly 1 wave: every SM busy, 100% use.',
                        f'Output 1,536 × 1,536 → 12 × 12 = <b>{_t2} tiles</b> → ⌈{_t2}/132⌉ = <b>2 waves</b>; the second wave has only {_t2 - 132} tiles.',
                        f'Efficiency = {_t2} tiles / (2 waves × 132 SMs) = <b>{_t2 / 264:.0%}</b>: 9% more work takes about twice as long.',
                        'Fixes: choose shapes whose tile count fills whole waves, use smaller tiles, or split K (split-K) to create more tiles.'],
                 result='GPU time is quantized in waves of 132 tiles; matrix sizes just above a wave boundary are the most wasteful.'),
    traps=dict(tricks=[('Warp = 32 threads.', 'Branches inside a warp run one after another (divergence).'),
                       ('Occupancy hides latency.', 'Enough resident warps per SM let the scheduler switch while others wait on memory.'),
                       ('Count waves.', 'tiles ÷ SMs, rounded up, sets the runtime.')],
               traps=[('Counting CUDA cores as speed.', 'For AI, Tensor Core throughput and memory bandwidth matter far more.'),
                      ('Divergent branches.', 'A warp with an if/else pays for both paths.'),
                      ('Shapes just past a wave.', 'A slightly larger matrix can take ~2× the time.')]),
    papers=[DOCS['h100wp'], P['hopper_bench']],
)

# 02 ------------------------------------------------------------------
_flop = 6 * 405e9 * 15.6e12
_gpuh = _flop / (H100_TF * 0.4) / 3600
EXTRAS['02-why-gpus-for-ai'] = dict(
    beats=False, glance_in='s-mm', example_after='s-mfu', traps_after='s-example',
    glance=dict(steps=[('model', 'N parameters', 'f'), ('FLOPs', '2·N per token forward,\n6·N·D to train', 'a'), ('bytes moved', 'weights, activations, KV', 'b'),
                       ('arithmetic intensity', 'FLOPs ÷ bytes', 'c'), ('roofline', 'compute- or memory-bound', 'e')],
                caption='Compare a kernel\'s intensity with the ridge point (peak FLOP/s ÷ bandwidth) to know which limit applies.'),
    example=dict(title='Worked example: estimate a training run on a whiteboard',
                 setup='Llama 3 405B: N = 405B parameters, D = 15.6T tokens, H100 at 989 TFLOP/s dense BF16, assume 40% MFU (model FLOPs utilization).',
                 steps=[f'Total compute ≈ 6 · N · D = 6 × 405B × 15.6T = <b>{_flop:.2e} FLOPs</b>.',
                        f'GPU-hours = {_flop:.2e} ÷ (989 TFLOP/s × 0.4) ÷ 3,600 ≈ <b>{_gpuh / 1e6:.1f}M</b> (Meta reported 30.84M including restarts and other overheads).',
                        f'On 16,384 GPUs: {_gpuh / 1e6:.1f}M ÷ 16,384 ÷ 24 ≈ <b>{_gpuh / 16384 / 24:.0f} days</b>.',
                        f'Ridge point of H100: 989 TFLOP/s ÷ 3.35 TB/s ≈ <b>{H100_TF / H100_BW:.0f} FLOPs per byte</b>; below that, a kernel is memory-bound.'],
                 result='Four numbers (N, D, peak FLOP/s, MFU) give a training budget in 30 seconds.'),
    traps=dict(tricks=[('Training ≈ 6·N·D, inference ≈ 2·N per token.', 'Forward 2, backward 4.'),
                       ('Ridge point = peak ÷ bandwidth.', '≈ 295 FLOPs/byte on H100 in BF16.'),
                       ('Decode intensity ≈ batch size.', 'Each weight read serves one token per sequence in the batch.')],
               traps=[('Using sparse peak numbers.', 'Datasheet 2:4-sparsity figures are 2× the dense ones.'),
                      ('Assuming 100% MFU.', 'Real large runs reach ~40% (Llama 3: 38–43%).'),
                      ('Calling decode compute-bound.', 'At small batch it is limited by bandwidth.')]),
    papers=[P['kaplan'], P['palm'], P['llama3']],
)

# 03 ------------------------------------------------------------------
EXTRAS['03-memory-hierarchy'] = dict(
    beats=False, glance_in='s-pyr', example_after='s-train', traps_after='s-off',
    glance=dict(steps=[('registers', 'per thread', 'a'), ('shared memory / L1', '228 KB per SM', 'c'), ('L2', '50 MB, whole GPU', 'b'), ('HBM', '80 GB, 3.35 TB/s', 'e'),
                       ('host DRAM / NVMe', 'behind PCIe', 'f')],
                caption='Each step down: bigger, slower, more energy per byte. Fast kernels keep data high in this list.'),
    example=dict(title='Worked example: does a 7B model fit for training?',
                 setup='Mixed-precision training with Adam: BF16 weights (2) + BF16 grads (2) + FP32 master weights (4) + two FP32 Adam moments (8) = 16 bytes per parameter, before activations.',
                 steps=[f'7B parameters × 16 bytes = <b>{7e9 * 16 / 1e9:.0f} GB</b>, more than one 80 GB H100.',
                        f'ZeRO-3 (Zero Redundancy Optimizer) across 8 GPUs shards all of it: <b>{7e9 * 16 / 8 / 1e9:.0f} GB</b> per GPU.',
                        f'70B parameters: <b>{70e9 * 16 / 1e9:,.0f} GB</b> of state → ≥ 14 GPUs just to hold it, before activations.',
                        'Activations scale with batch × sequence × layers; activation checkpointing trades recompute for memory.'],
                 result='Capacity, not FLOPs, usually decides the minimum number of GPUs for training.'),
    traps=dict(tricks=[('16 bytes/param for Adam training.', 'Plus activations.'),
                       ('Tiling cuts traffic by the tile size.', 'Load once into shared memory, reuse T times.'),
                       ('Fuse elementwise ops.', 'One trip to HBM instead of one per op.')],
               traps=[('Counting only weights.', 'Gradients and optimizer states are 6× the BF16 weights.'),
                      ('Ignoring energy.', 'A DRAM access costs far more energy than a multiply (Horowitz).'),
                      ('Offloading to host memory freely.', 'PCIe is ~50× slower than HBM.')]),
    papers=[P['horowitz'], P['fa1'], P['zero'], P['vllm']],
)

# 04 ------------------------------------------------------------------
_lad = [('HBM', 3350), ('NVLink', 450), ('PCIe Gen5', 64), ('NIC (400 Gb/s)', 50), ('NVMe', 7)]
EXTRAS['04-inside-gpu-server'] = dict(
    beats=False, glance_in='s-paths', example_after='s-ladder', traps_after='s-debug',
    glance=dict(steps=[('GPU ↔ HBM', '3,350 GB/s', 'e'), ('GPU ↔ GPU', 'NVLink 450 GB/s\nper direction', 'a'), ('GPU ↔ CPU / NIC', 'PCIe Gen5 64 GB/s', 'b'),
                       ('node ↔ node', 'NIC 50 GB/s', 'c'), ('storage', 'NVMe ~7 GB/s', 'f')],
                caption='Bandwidth falls roughly 10× at each step away from the GPU.'),
    example=dict(title='Worked example: moving 1 GB',
                 setup='Per-GPU, per-direction bandwidths from the deck.',
                 steps=[f'{n}: 1 GB ÷ {b:,} GB/s = <b>{1000 / b:.1f} ms</b>.' for n, b in _lad] +
                       ['Implication: keep tensor-parallel traffic on NVLink, data-parallel gradients on the network, and checkpoints off the critical path.'],
                 result=f'The same gigabyte takes {1000 / _lad[0][1]:.1f} ms in HBM and {1000 / _lad[-1][1]:.0f} ms from NVMe: placement decides speed.'),
    traps=dict(tricks=[('Memorize the ladder.', 'HBM 3,350 · NVLink 450 · PCIe 64 · NIC 50 · NVMe 7 GB/s.'),
                       ('Check affinity.', 'nvidia-smi topo -m shows which NIC and CPU socket sit closest to each GPU.'),
                       ('Power sets capacity.', 'A DGX H100 draws ~10.2 kW; racks are sized in kilowatts, not GPUs.')],
               traps=[('Cross-socket traffic.', 'A GPU using a NIC on the other CPU socket pays extra hops.'),
                      ('PCIe as GPU-to-GPU path.', 'Without NVLink, tensor parallelism is much slower.'),
                      ('Ignoring thermals.', 'Hot GPUs throttle clocks and become stragglers.')]),
    papers=[DOCS['nvl72'], P['llama3']],
)

# 05 ------------------------------------------------------------------
_S, _N = 16e9, 8
EXTRAS['05-cluster-topology'] = dict(
    beats=False, glance_in='s-tiers', example_after='s-cost', traps_after='s-moe',
    glance=dict(steps=[('GPU', 'in an NVLink domain', 'e'), ('node', '8 GPUs, NVSwitch', 'a'), ('leaf switch', 'rail-optimized', 'b'), ('spine', 'fat tree', 'c'),
                       ('cluster', '16K GPUs', 'f')],
                caption='Scale-up inside the node (NVLink), scale-out between nodes (InfiniBand or RoCE).'),
    example=dict(title='Worked example: one all-reduce of gradients',
                 setup='An 8B-parameter model has 16 GB of BF16 gradients. Ring all-reduce over N = 8 participants sends 2(N − 1)/N × S per GPU.',
                 steps=[f'Data per GPU: 2 × 7/8 × 16 GB = <b>{2 * (_N - 1) / _N * _S / 1e9:.0f} GB</b>.',
                        f'Inside one node over NVLink (450 GB/s): <b>{2 * (_N - 1) / _N * _S / 450e9 * 1e3:.0f} ms</b>.',
                        f'Across 8 nodes over 400 Gb/s NICs (50 GB/s): <b>{2 * (_N - 1) / _N * _S / 50e9 * 1e3:.0f} ms</b>.',
                        'The bandwidth term barely changes with N (2(N−1)/N → 2), but the latency term grows with N, which is where trees win.'],
                 result='Put the chattiest parallelism (tensor) on NVLink and the bulk all-reduce (data) on the network, overlapped with compute.'),
    traps=dict(tricks=[('Ring all-reduce sends ≈ 2S per GPU.', 'Independent of N for large N.'),
                       ('Place TP inside the node.', 'Llama 3 405B: TP = 8, PP = 16, DP = 128 on 16,384 GPUs.'),
                       ('Rail-optimized networks.', 'GPU i of every node shares a leaf switch.')],
               traps=[('Ignoring latency at scale.', 'Ring latency grows linearly with N; small messages need trees.'),
                      ('TP across nodes.', 'Per-layer all-reduces over the network stall every step.'),
                      ('Expert parallel imbalance.', 'All-to-all waits for the busiest GPU.')]),
    papers=[P['megatron21'], P['llama3'], DOCS['nccl']],
)

# 06 ------------------------------------------------------------------
_mtbf_job = 54 * 24 / 419
_C = 5 / 60
_T = sqrt(2 * _C * _mtbf_job)
EXTRAS['06-gpu-failures'] = dict(
    beats=False, glance_in='s-llama', example_after='s-ckpt', traps_after='s-ops',
    glance=dict(steps=[('fault', 'GPU, NIC, host, software', 'd'), ('detect', 'Xid errors, timeouts, health checks', 'b'), ('stop job', 'one rank down halts all', 'c'),
                       ('replace / restart', 'from last checkpoint', 'a'), ('resume', 'lost work = time since checkpoint', 'e')],
                caption='At 16K GPUs, failures are routine; the goal is to make each one cheap.'),
    example=dict(title='Worked example: how often to checkpoint',
                 setup='Llama 3 405B: 419 unexpected interruptions in 54 days on 16,384 GPUs. Assume a checkpoint takes 5 minutes to write.',
                 steps=[f'Job MTBF (mean time between failures) = 54 × 24 h ÷ 419 ≈ <b>{_mtbf_job:.1f} h</b>.',
                        f'Per-GPU MTBF ≈ {_mtbf_job:.1f} h × 16,384 ≈ <b>{_mtbf_job * 16384 / 24 / 365:.1f} years</b>: each GPU is reliable; the fleet is not.',
                        f'Young\'s approximation: interval ≈ √(2 × checkpoint cost × MTBF) = √(2 × {_C:.3f} h × {_mtbf_job:.1f} h) ≈ <b>{_T * 60:.0f} min</b>.',
                        f'Expected loss per failure ≈ half an interval ({_T * 30:.0f} min) plus restart time; faster checkpoints shorten the interval.'],
                 result='Checkpoint cost and failure rate together set the interval; cutting checkpoint time (async, in-memory) is the main lever.'),
    traps=dict(tricks=[('Cluster MTBF = GPU MTBF ÷ N.', 'Double the GPUs, halve the time between failures.'),
                       ('Checkpoint interval ≈ √(2·C·MTBF).', 'Young\'s approximation.'),
                       ('Stragglers matter.', 'A slow GPU slows every synchronous step.')],
               traps=[('Waiting for hard failures only.', 'Silent data corruption gives wrong numbers with no error.'),
                      ('Restarting on the same bad node.', 'Drain and test before returning it to the pool.'),
                      ('Synchronous checkpoint writes.', 'They stall all GPUs for the whole write.')]),
    papers=[P['llama3'], P['megascale'], P['sdc'], P['cores_count']],
)

# 07 ------------------------------------------------------------------
_a, _h = 312, 989
EXTRAS['07-heterogeneous-gpus'] = dict(
    beats=False, glance_in='s-fleet', example_after='s-pipe', traps_after='s-place',
    glance=dict(steps=[('mixed fleet', 'A100, H100, H200, B200', 'f'), ('classify work', 'training, prefill, decode, batch', 'c'),
                       ('match', 'compute-heavy → newest\nmemory-bound → older', 'a'), ('balance', 'work ∝ speed', 'e')],
                caption='Mixing hurts synchronous training unless work is balanced; it helps when phases have different needs.'),
    example=dict(title='Worked example: A100s and H100s in one synchronous job',
                 setup=f'Dense BF16 peak: A100 {_a} TFLOP/s, H100 {_h} TFLOP/s. Equal per-GPU batches.',
                 steps=[f'Each step waits for the A100: the H100 finishes in {_a / _h:.0%} of the step and idles <b>{1 - _a / _h:.0%}</b> of the time.',
                        f'Balance by speed: give each H100 {_h / _a:.1f}× the work of an A100.',
                        f'In a 1 A100 : 1 H100 pair, the H100 should get <b>{_h / (_h + _a):.0%}</b> of the batch.',
                        'Pipeline parallelism can instead give faster GPUs more layers.'],
                 result='Heterogeneity is fine when the work split follows each GPU\'s speed (and memory); equal splits waste the faster GPUs.'),
    traps=dict(tricks=[('Split work ∝ throughput.', 'Batch share or layer count per GPU type.'),
                       ('Prefill on new, decode on old.', 'Decode is memory-bound and runs well on older GPUs (Splitwise).'),
                       ('Keep TP within one GPU type.', 'Mixed types inside a TP group run at the slowest.')],
               traps=[('Equal batches on unequal GPUs.', 'The fast GPUs idle at every all-reduce.'),
                      ('Numerics differences.', 'Different kernels and formats (FP8 support) change results slightly.'),
                      ('Interconnect mismatch.', 'Different NVLink generations can\'t share a domain.')]),
    papers=[P['splitwise'], P['distserve'], P['mooncake']],
)

# 08 ------------------------------------------------------------------
EXTRAS['08-sharing-gpus'] = dict(
    beats=False, glance_in='s-spec', example_after='s-lora', traps_after='s-sched',
    glance=dict(steps=[('time-slicing', 'take turns, no isolation', 'f'), ('MPS', 'run side by side, soft limits', 'b'), ('MIG', 'hardware partitions, ≤ 7', 'a'),
                       ('continuous batching', 'one model, many users', 'c'), ('multi-LoRA', 'one base, many adapters', 'e')],
                caption='From splitting the hardware to sharing the model.'),
    example=dict(title='Worked example: one H100 for seven small services',
                 setup='Seven internal services each need ~8 GB of memory and a small share of compute.',
                 steps=['Time-slicing: all seven take turns on the whole GPU; a busy service delays the others, and memory isn\'t isolated.',
                        'MIG: seven 1g.10gb instances, each with its own SMs, L2 slice and ~10 GB of memory: guaranteed isolation and QoS.',
                        'MPS: processes share SMs concurrently with soft limits: better utilization, weaker isolation.',
                        'If all seven are LoRA variants of one base model, multi-LoRA serving keeps one copy of the base and batches them together (Punica: 12× throughput).'],
                 result='Use MIG when tenants need isolation, MPS for cooperating processes, and model-level sharing (batching, multi-LoRA) when they share a model.'),
    traps=dict(tricks=[('MIG ≤ 7 instances on H100.', 'Fixed profiles; reconfigure only when idle.'),
                       ('Share the model, not just the GPU.', 'Continuous batching and multi-LoRA beat partitioning for same-model traffic.'),
                       ('Gang scheduling.', 'Distributed jobs need all their GPUs at once.')],
               traps=[('Time-slicing for latency-sensitive work.', 'Turns add unpredictable delay.'),
                      ('Fragmentation.', 'Leftover GPUs that no job can use idle a cluster.'),
                      ('Assuming MPS isolates faults.', 'A crashing client can affect others.')]),
    papers=[DOCS['mig'], P['orca'], P['slora'], P['punica']],
)
