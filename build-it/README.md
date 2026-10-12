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
