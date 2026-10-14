# Visual AI

Interactive slide decks that explain AI systems concepts visually.

**Live site:** https://nilesh-salpe.github.io/visual-ai/

## GPU for GenAI

| # | Deck |
|---|------|
| 01 | [What a GPU is](gpu/01-what-is-a-gpu/) |
| 02 | [Why GPUs for AI](gpu/02-why-gpus-for-ai/) |
| 03 | [Memory hierarchy](gpu/03-memory-hierarchy/) |
| 04 | [Inside a GPU server](gpu/04-inside-gpu-server/) |
| 05 | [Cluster topology](gpu/05-cluster-topology/) |
| 06 | [GPU failures](gpu/06-gpu-failures/) |
| 07 | [Heterogeneous GPUs](gpu/07-heterogeneous-gpus/) |
| 08 | [Sharing GPUs](gpu/08-sharing-gpus/) |

## Attention Is All You Need (Vaswani et al., 2017)

Fourteen standalone explainers, each following the same 9 beats: Problem → Limitation → Your turn (predict the fix) → Core idea → How it works → Why it works → Misconceptions → Check yourself → Key takeaway. All numbers are checked against [arXiv:1706.03762v7](https://arxiv.org/abs/1706.03762v7).

| # | Concept |
|---|---------|
| 01 | [Sequential processing bottleneck](transformer/01-sequential-bottleneck/) |
| 02 | [The Transformer architecture](transformer/02-transformer-architecture/) |
| 03 | [Self-attention](transformer/03-self-attention/) |
| 04 | [Queries, keys and values](transformer/04-queries-keys-values/) |
| 05 | [Scaled dot-product attention](transformer/05-scaled-dot-product-attention/) |
| 06 | [Multi-head attention](transformer/06-multi-head-attention/) |
| 07 | [Positional encoding](transformer/07-positional-encoding/) |
| 08 | [Encoder-decoder attention](transformer/08-encoder-decoder-attention/) |
| 09 | [Masked self-attention](transformer/09-masked-self-attention/) |
| 10 | [Residuals and layer normalization](transformer/10-residual-layernorm/) |
| 11 | [Position-wise feed-forward networks](transformer/11-position-wise-ffn/) |
| 12 | [Parallel training vs autoregressive generation](transformer/12-parallel-training-vs-generation/) |
| 13 | [Why the Transformer works](transformer/13-why-it-works/) |
| 14 | [Experimental results](transformer/14-experimental-results/) |

## Tokenization for LLMs

Ten 9-beat decks plus a [live tokenizer playground](tokenization/playground/) that runs the real `gpt2`, `cl100k_base` and `o200k_base` encodings in the browser (js-tiktoken). Real token examples in the decks are generated with OpenAI's tiktoken.

| # | Deck |
|---|------|
| 01 | [Why tokenize?](tokenization/01-why-tokenize/) |
| 02 | [BPE from scratch](tokenization/02-bpe-from-scratch/) |
| 03 | [Byte-level BPE](tokenization/03-byte-level-bpe/) |
| 04 | [WordPiece and unigram LM](tokenization/04-wordpiece-unigram/) |
| 05 | [SentencePiece](tokenization/05-sentencepiece/) |
| 06 | [One text, many tokenizations](tokenization/06-many-tokenizations/) |
| 07 | [Vocabulary size trade-offs](tokenization/07-vocabulary-size/) |
| 08 | [Tokenizers in real LLMs](tokenization/08-tokenizers-in-llms/) |
| 09 | [Multilingual cost](tokenization/09-multilingual-cost/) |
| 10 | [Tokenization quirks](tokenization/10-tokenization-quirks/) |

## LLM Inference and Serving

Ten 9-beat decks plus 12 hands-on [Colab notebooks](build-it/) (NumPy, built-in tests, hidden solutions).

| # | Deck |
|---|------|
| 01 | [The inference workload](inference/01-inference-workload/) |
| 02 | [KV cache](inference/02-kv-cache/) |
| 03 | [Continuous batching](inference/03-batching/) |
| 04 | [Chunked prefill](inference/04-chunked-prefill/) |
| 05 | [PagedAttention and prefix caching](inference/05-paged-attention/) |
| 06 | [Speculative decoding](inference/06-speculative-decoding/) |
| 07 | [Quantization](inference/07-quantization/) |
| 08 | [Parallelism for inference](inference/08-parallelism/) |
| 09 | [Disaggregated serving](inference/09-disaggregated-serving/) |
| 10 | [Putting it together](inference/10-putting-it-together/) |

## The Modern LLM Architecture

Eleven 9-beat decks on what changed after 2017, plus 10 hands-on [Colab notebooks](build-it/).

| # | Deck |
|---|------|
| 01 | [What changed since 2017](architecture/01-what-changed/) |
| 02 | [Pre-norm and RMSNorm](architecture/02-normalization/) |
| 03 | [RoPE](architecture/03-rope/) |
| 04 | [SwiGLU](architecture/04-swiglu/) |
| 05 | [MQA, GQA and MLA](architecture/05-attention-variants/) |
| 06 | [Decoder-only, and why it won](architecture/06-decoder-only/) |
| 07 | [Long context I: stretching RoPE](architecture/07-rope-scaling/) |
| 08 | [Long context II: sliding window and ALiBi](architecture/08-sliding-window/) |
| 09 | [FlashAttention internals](architecture/09-flash-attention/) |
| 10 | [Mixture of Experts](architecture/10-mixture-of-experts/) |
| 11 | [Putting it together](architecture/11-putting-it-together/) |

## Post-training LLMs

Nine 9-beat decks plus 8 hands-on [Colab notebooks](build-it/).

| # | Deck |
|---|------|
| 01 | [The post-training pipeline](post-training/01-pipeline/) |
| 02 | [Supervised fine-tuning](post-training/02-supervised-fine-tuning/) |
| 03 | [LoRA and QLoRA](post-training/03-lora-qlora/) |
| 04 | [Reward models](post-training/04-reward-models/) |
| 05 | [RLHF with PPO](post-training/05-rlhf-ppo/) |
| 06 | [Reward hacking and overoptimization](post-training/06-reward-hacking/) |
| 07 | [DPO, KTO and rejection sampling](post-training/07-dpo-and-friends/) |
| 08 | [RLVR and GRPO](post-training/08-rlvr-grpo/) |
| 09 | [RLAIF and Constitutional AI](post-training/09-rlaif-constitutional-ai/) |

## Evaluating LLMs

Seven 9-beat decks plus 4 hands-on [Colab notebooks](build-it/).

| # | Deck |
|---|------|
| 01 | [What an eval measures](evals/01-what-an-eval-measures/) |
| 02 | [Benchmarks and their failure modes](evals/02-benchmarks/) |
| 03 | [pass@k and sampling metrics](evals/03-pass-at-k/) |
| 04 | [Error bars and comparing models](evals/04-error-bars/) |
| 05 | [Contamination](evals/05-contamination/) |
| 06 | [LLM-as-judge](evals/06-llm-as-judge/) |
| 07 | [Arenas and ratings](evals/07-arenas/) |

## Regenerating

The inference, tokenization, architecture, post-training and evals decks and all notebooks are generated by the scripts in [`tools/`](tools/): `tools/decks/gen_*.py` writes decks, `tools/notebooks/build_*.py` writes and validates notebooks (every starter must report ⏳ and every reference solution ✅), `tools/build_indexes.py` rebuilds the notebook and hub index pages, `tools/decks/apply_augment.py` adds the extras to the hand-written GPU and Transformer decks, and `tools/build_site_extras.py` (run last) builds the glossary, the per-topic reading lists and the hub maps. `tools/decks/acronyms.py lint` and `tools/check_papers.py` are the quality checks.

These are static HTML files with no build step. Open `index.html` in a browser. Keyboard controls: ←/→ or Space to move between slides, F for full screen.
