# Build it: hands-on notebooks

Run in Google Colab (NumPy, CPU only). Each notebook: Setup → tasks with `TODO`s → built-in tests (⏳/✅/❌) → collapsed reference solutions → experiments.

## Foundations · Math for LLMs

| Notebook | Time | Colab |
|---|---|---|
| [01 · Vectors, dot products and similarity](math/01_vectors_similarity.ipynb) | 25 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/math/01_vectors_similarity.ipynb) |
| [02 · SVD and low-rank approximation](math/02_svd_low_rank.ipynb) | 30 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/math/02_svd_low_rank.ipynb) |
| [03 · Chain rule by hand and gradient checking](math/03_chain_rule_gradcheck.ipynb) | 30 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/math/03_chain_rule_gradcheck.ipynb) |
| [04 · Entropy, cross-entropy, KL and perplexity](math/04_cross_entropy_kl.ipynb) | 25 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/math/04_cross_entropy_kl.ipynb) |
| [05 · Stable softmax, log-sum-exp and online softmax](math/05_stable_softmax.ipynb) | 30 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/math/05_stable_softmax.ipynb) |
| [06 · Gradient descent, momentum and Adam](math/06_gradient_descent.ipynb) | 30 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/math/06_gradient_descent.ipynb) |

Concept decks: https://nilesh-salpe.github.io/visual-ai/math/

## Foundations · Neural network fundamentals

| Notebook | Time | Colab |
|---|---|---|
| [01 · Build an autograd engine (micrograd-style)](nn-fundamentals/01_micrograd.ipynb) | 40 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/nn-fundamentals/01_micrograd.ipynb) |
| [02 · An MLP from scratch: solving XOR](nn-fundamentals/02_mlp_numpy.ipynb) | 35 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/nn-fundamentals/02_mlp_numpy.ipynb) |
| [03 · Activations and vanishing gradients](nn-fundamentals/03_activations_depth.ipynb) | 25 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/nn-fundamentals/03_activations_depth.ipynb) |
| [04 · SGD, Adam, AdamW and learning-rate schedules](nn-fundamentals/04_optimizers_schedules.ipynb) | 35 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/nn-fundamentals/04_optimizers_schedules.ipynb) |
| [05 · Initialization: keeping signals alive](nn-fundamentals/05_initialization.ipynb) | 25 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/nn-fundamentals/05_initialization.ipynb) |
| [06 · Overfitting, dropout and weight decay](nn-fundamentals/06_overfitting_dropout.ipynb) | 30 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/nn-fundamentals/06_overfitting_dropout.ipynb) |
| [07 · A tiny character-level language model](nn-fundamentals/07_tiny_char_lm.ipynb) | 40 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/nn-fundamentals/07_tiny_char_lm.ipynb) |

Concept decks: https://nilesh-salpe.github.io/visual-ai/nn-fundamentals/

## Phase 1 · LLM inference and serving

| Notebook | Time | Colab |
|---|---|---|
| [01 · A tiny GPT forward pass in NumPy](inference/01_tiny_gpt_forward.ipynb) | 40 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/01_tiny_gpt_forward.ipynb) |
| [02 · KV-cache decoding](inference/02_kv_cache.ipynb) | 35 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/02_kv_cache.ipynb) |
| [03 · Grouped-query attention (GQA) and multi-query attention (MQA)](inference/03_gqa_mqa.ipynb) | 25 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/03_gqa_mqa.ipynb) |
| [04 · KV-cache memory calculator](inference/04_kv_memory_calculator.ipynb) | 20 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/04_kv_memory_calculator.ipynb) |
| [05 · Continuous (iteration-level) batching](inference/05_continuous_batching.ipynb) | 35 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/05_continuous_batching.ipynb) |
| [06 · Chunked prefill with a token budget](inference/06_chunked_prefill.ipynb) | 40 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/06_chunked_prefill.ipynb) |
| [07 · A paged KV-cache allocator](inference/07_paged_kv_allocator.ipynb) | 40 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/07_paged_kv_allocator.ipynb) |
| [08 · Prefix caching with a token trie (RadixAttention-style)](inference/08_prefix_cache.ipynb) | 35 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/08_prefix_cache.ipynb) |
| [09 · Speculative sampling](inference/09_speculative_sampling.ipynb) | 45 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/09_speculative_sampling.ipynb) |
| [10 · INT8/INT4 quantization and SmoothQuant](inference/10_quantization.ipynb) | 45 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/10_quantization.ipynb) |
| [11 · FP8 (E4M3 / E5M2) emulation](inference/11_fp8_emulation.ipynb) | 30 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/11_fp8_emulation.ipynb) |
| [12 · Tensor-parallel linear layers (Megatron-style)](inference/12_tensor_parallel.ipynb) | 35 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/12_tensor_parallel.ipynb) |

Concept decks: https://nilesh-salpe.github.io/visual-ai/inference/

## Phase 2 · The modern LLM architecture

| Notebook | Time | Colab |
|---|---|---|
| [01 · RMSNorm and pre-norm blocks](architecture/01_norms_prenorm.ipynb) | 35 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/architecture/01_norms_prenorm.ipynb) |
| [02 · Rotary position embeddings (RoPE)](architecture/02_rope.ipynb) | 40 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/architecture/02_rope.ipynb) |
| [03 · SwiGLU feed-forward layers](architecture/03_swiglu.ipynb) | 30 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/architecture/03_swiglu.ipynb) |
| [04 · Multi-head latent attention (MLA) and weight absorption](architecture/04_mla_absorption.ipynb) | 45 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/architecture/04_mla_absorption.ipynb) |
| [05 · Causal, prefix-LM and document masks](architecture/05_attention_masks.ipynb) | 25 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/architecture/05_attention_masks.ipynb) |
| [06 · Extending context: PI, NTK-aware and YaRN](architecture/06_rope_scaling.ipynb) | 45 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/architecture/06_rope_scaling.ipynb) |
| [07 · Sliding-window attention and the rolling KV cache](architecture/07_sliding_window.ipynb) | 40 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/architecture/07_sliding_window.ipynb) |
| [08 · FlashAttention from scratch: online softmax and tiling](architecture/08_flash_attention.ipynb) | 50 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/architecture/08_flash_attention.ipynb) |
| [09 · Mixture-of-Experts: router, dispatch and load balancing](architecture/09_moe_router.ipynb) | 45 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/architecture/09_moe_router.ipynb) |
| [10 · Build a Llama-style decoder block and count its parameters](architecture/10_llama_block.ipynb) | 50 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/architecture/10_llama_block.ipynb) |

Concept decks: https://nilesh-salpe.github.io/visual-ai/architecture/

## Phase 3 · Post-training

| Notebook | Time | Colab |
|---|---|---|
| [01 · Supervised fine-tuning: chat templates, loss masking and packing](post-training/01_sft_loss_masking.ipynb) | 35 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/post-training/01_sft_loss_masking.ipynb) |
| [02 · LoRA from scratch](post-training/02_lora.ipynb) | 40 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/post-training/02_lora.ipynb) |
| [03 · QLoRA's NF4 and double quantization](post-training/03_nf4_quantization.ipynb) | 30 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/post-training/03_nf4_quantization.ipynb) |
| [04 · Train a Bradley-Terry reward model](post-training/04_reward_model.ipynb) | 35 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/post-training/04_reward_model.ipynb) |
| [05 · PPO with a KL penalty on a toy policy](post-training/05_ppo_toy.ipynb) | 45 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/post-training/05_ppo_toy.ipynb) |
| [06 · Reward hacking: best-of-n against a flawed reward model](post-training/06_overoptimization.ipynb) | 35 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/post-training/06_overoptimization.ipynb) |
| [07 · Direct Preference Optimization (DPO)](post-training/07_dpo.ipynb) | 40 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/post-training/07_dpo.ipynb) |
| [08 · RL with verifiable rewards and GRPO](post-training/08_grpo_rlvr.ipynb) | 45 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/post-training/08_grpo_rlvr.ipynb) |

Concept decks: https://nilesh-salpe.github.io/visual-ai/post-training/

## Phase 4 · Evaluating LLMs

| Notebook | Time | Colab |
|---|---|---|
| [01 · pass@k: the unbiased estimator](evals/01_pass_at_k.ipynb) | 30 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/evals/01_pass_at_k.ipynb) |
| [02 · Error bars, clustered errors and paired comparisons](evals/02_error_bars.ipynb) | 40 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/evals/02_error_bars.ipynb) |
| [03 · Detecting benchmark contamination with n-grams](evals/03_contamination.ipynb) | 35 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/evals/03_contamination.ipynb) |
| [04 · LLM judges and arena ratings](evals/04_judges_and_arenas.ipynb) | 45 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/evals/04_judges_and_arenas.ipynb) |
| [05 · Experiments: seed noise, A/B sample size and the cost of peeking](evals/05_experiments.ipynb) | 30 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/evals/05_experiments.ipynb) |

Concept decks: https://nilesh-salpe.github.io/visual-ai/evals/

## Phase 5 · Distributed training & reliability

| Notebook | Time | Colab |
|---|---|---|
| [01 · Ring all-reduce from scratch](distributed/01_ring_allreduce.ipynb) | 35 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/distributed/01_ring_allreduce.ipynb) |
| [02 · ZeRO / FSDP: sharded data parallelism](distributed/02_zero_sharding.ipynb) | 45 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/distributed/02_zero_sharding.ipynb) |
| [03 · Tensor-parallel MLP: forward and backward](distributed/03_tensor_parallel_training.ipynb) | 40 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/distributed/03_tensor_parallel_training.ipynb) |
| [04 · Pipeline schedules: GPipe vs 1F1B](distributed/04_pipeline_schedules.ipynb) | 45 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/distributed/04_pipeline_schedules.ipynb) |
| [05 · Activation checkpointing](distributed/05_activation_checkpointing.ipynb) | 35 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/distributed/05_activation_checkpointing.ipynb) |
| [06 · Mixed precision: FP16, BF16 and loss scaling](distributed/06_mixed_precision.ipynb) | 40 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/distributed/06_mixed_precision.ipynb) |
| [07 · Context parallelism: ring attention](distributed/07_ring_attention.ipynb) | 40 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/distributed/07_ring_attention.ipynb) |
| [08 · Failures, checkpoints and goodput](distributed/08_checkpoint_failures.ipynb) | 35 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/distributed/08_checkpoint_failures.ipynb) |

Concept decks: https://nilesh-salpe.github.io/visual-ai/distributed/

## Phase 6 · Web crawling & pretraining data

| Notebook | Time | Colab |
|---|---|---|
| [01 · A polite crawler on a simulated web](pretraining-data/01_polite_crawler.ipynb) | 40 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pretraining-data/01_polite_crawler.ipynb) |
| [02 · A robots.txt parser following RFC 9309](pretraining-data/02_robots_txt.ipynb) | 35 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pretraining-data/02_robots_txt.ipynb) |
| [03 · From HTML to clean text](pretraining-data/03_text_extraction.ipynb) | 30 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pretraining-data/03_text_extraction.ipynb) |
| [04 · Heuristic quality filters (C4 and Gopher rules)](pretraining-data/04_quality_filters.ipynb) | 35 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pretraining-data/04_quality_filters.ipynb) |
| [05 · Near-duplicate detection with MinHash and LSH](pretraining-data/05_minhash_lsh.ipynb) | 40 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pretraining-data/05_minhash_lsh.ipynb) |
| [06 · Data mixtures, sampling temperature and epochs](pretraining-data/06_data_mixture.ipynb) | 25 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pretraining-data/06_data_mixture.ipynb) |

Concept decks: https://nilesh-salpe.github.io/visual-ai/pretraining-data/

## Frameworks · PyTorch for LLMs

| Notebook | Time | Colab |
|---|---|---|
| [01 · Tensors: shapes, strides, views and einsum](pytorch/01_tensors_views.ipynb) | 30 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/01_tensors_views.ipynb) |
| [02 · Autograd: graphs, custom functions and accumulation](pytorch/02_autograd.ipynb) | 30 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/02_autograd.ipynb) |
| [03 · nn.Module: a pre-norm transformer block](pytorch/03_transformer_block.ipynb) | 40 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/03_transformer_block.ipynb) |
| [04 · The training loop: AdamW, schedules, clipping, checkpoints](pytorch/04_training_loop.ipynb) | 35 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/04_training_loop.ipynb) |
| [05 · Data: Dataset, DataLoader, padding, masks and packing](pytorch/05_data_pipeline.ipynb) | 30 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/05_data_pipeline.ipynb) |
| [06 · Mixed precision: autocast, BF16 and GradScaler](pytorch/06_mixed_precision.ipynb) | 25 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/06_mixed_precision.ipynb) |
| [07 · torch.compile and fused attention](pytorch/07_compile_and_sdpa.ipynb) | 30 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/07_compile_and_sdpa.ipynb) |
| [08 · Distributed: all_reduce and DDP with torchrun](pytorch/08_ddp_torchrun.ipynb) | 35 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/08_ddp_torchrun.ipynb) |
| [09 · Train a tiny GPT end to end](pytorch/09_tiny_gpt.ipynb) | 40 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/09_tiny_gpt.ipynb) |

Concept decks: https://nilesh-salpe.github.io/visual-ai/pytorch/

## Frameworks · vLLM internals

| Notebook | Time | Colab |
|---|---|---|
| [01 · The KV block pool: paging, ref counts and LRU](vllm/01_block_pool.ipynb) | 35 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/vllm/01_block_pool.ipynb) |
| [02 · Automatic prefix caching with chained block hashes](vllm/02_prefix_cache.ipynb) | 35 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/vllm/02_prefix_cache.ipynb) |
| [03 · The unified token-budget scheduler](vllm/03_token_budget_scheduler.ipynb) | 40 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/vllm/03_token_budget_scheduler.ipynb) |
| [04 · Planning GPU memory: weights, KV cache and concurrency](vllm/04_memory_planner.ipynb) | 25 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/vllm/04_memory_planner.ipynb) |
| [05 · N-gram speculative decoding](vllm/05_ngram_speculation.ipynb) | 30 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/vllm/05_ngram_speculation.ipynb) |

Concept decks: https://nilesh-salpe.github.io/visual-ai/vllm/

## Infrastructure · Cluster scheduling

| Notebook | Time | Colab |
|---|---|---|
| [01 · Queues and backfill: FIFO vs EASY backfill on a GPU cluster](cluster-scheduling/01_backfill_scheduler.ipynb) | 35 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/cluster-scheduling/01_backfill_scheduler.ipynb) |
| [02 · Fair share, job priority and preemption (Slurm-style)](cluster-scheduling/02_fair_share_priority.ipynb) | 30 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/cluster-scheduling/02_fair_share_priority.ipynb) |

Concept decks: https://nilesh-salpe.github.io/visual-ai/cluster-scheduling/

## Frontier · Reasoning and test-time compute

| Notebook | Time | Colab |
|---|---|---|
| [01 · Test-time compute: majority voting, coverage and best-of-N](reasoning/01_test_time_compute.ipynb) | 35 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/reasoning/01_test_time_compute.ipynb) |

Concept decks: https://nilesh-salpe.github.io/visual-ai/reasoning/

## Agents · LangChain and LangGraph

| Notebook | Time | Colab |
|---|---|---|
| [01 · LangChain basics: tools, tool calls and the agent loop](agent-frameworks/01_langchain_basics.ipynb) | 30 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/agent-frameworks/01_langchain_basics.ipynb) |
| [02 · LangGraph core: state, reducers, edges and a ReAct graph](agent-frameworks/02_langgraph_core.ipynb) | 35 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/agent-frameworks/02_langgraph_core.ipynb) |
| [03 · LangGraph in production: checkpoints, threads, interrupts and resuming](agent-frameworks/03_langgraph_production.ipynb) | 35 min | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/agent-frameworks/03_langgraph_production.ipynb) |

Concept decks: https://nilesh-salpe.github.io/visual-ai/agent-frameworks/
