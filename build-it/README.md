# Build it: hands-on notebooks

Run in Google Colab (NumPy, CPU only). Each notebook: Setup → tasks with `TODO`s → built-in tests (⏳/✅/❌) → collapsed reference solutions → experiments.

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
