# Visual AI

Interactive slide decks that explain AI systems concepts visually.

**Live site:** https://nilesh-salpe.github.io/visual-ai/

## Math for LLMs and neural networks

Ten 9-beat decks plus 6 hands-on [Colab notebooks](build-it/).

| # | Deck |
|---|------|
| 01 | [Vectors and dot products](math/01-vectors-dot-products/) |
| 02 | [Matrices and linear layers](math/02-matrices-linear-layers/) |
| 03 | [Eigenvalues, SVD and low rank](math/03-eigen-svd-low-rank/) |
| 04 | [Derivatives and the chain rule](math/04-derivatives-chain-rule/) |
| 05 | [Probability and sampling](math/05-probability-sampling/) |
| 06 | [Maximum likelihood and cross-entropy](math/06-maximum-likelihood/) |
| 07 | [Information theory for LLMs](math/07-information-theory/) |
| 08 | [Softmax and log-sum-exp](math/08-softmax-logsumexp/) |
| 09 | [Optimization basics](math/09-optimization-basics/) |
| 10 | [Floating-point numbers](math/10-floating-point/) |

## Neural network fundamentals for LLMs

Ten 9-beat decks plus 7 hands-on [Colab notebooks](build-it/).

| # | Deck |
|---|------|
| 01 | [From perceptron to MLP](nn-fundamentals/01-perceptron-to-mlp/) |
| 02 | [Activation functions](nn-fundamentals/02-activation-functions/) |
| 03 | [Backpropagation](nn-fundamentals/03-backpropagation/) |
| 04 | [Loss functions](nn-fundamentals/04-loss-functions/) |
| 05 | [Optimizers](nn-fundamentals/05-optimizers/) |
| 06 | [Initialization](nn-fundamentals/06-initialization/) |
| 07 | [Normalization and residual connections](nn-fundamentals/07-normalization-residuals/) |
| 08 | [Regularization and generalization](nn-fundamentals/08-regularization/) |
| 09 | [Embeddings](nn-fundamentals/09-embeddings/) |
| 10 | [From MLP to language model](nn-fundamentals/10-mlp-to-language-model/) |

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

## Distributed training & reliability

Eleven 9-beat decks plus 8 hands-on [Colab notebooks](build-it/).

| # | Deck |
|---|------|
| 01 | [Why training must be distributed](distributed/01-why-distribute/) |
| 02 | [Data parallelism](distributed/02-data-parallelism/) |
| 03 | [ZeRO and FSDP](distributed/03-zero-fsdp/) |
| 04 | [Tensor and sequence parallelism](distributed/04-tensor-sequence-parallelism/) |
| 05 | [Pipeline parallelism](distributed/05-pipeline-parallelism/) |
| 06 | [Context parallelism](distributed/06-context-parallelism/) |
| 07 | [Expert parallelism](distributed/07-expert-parallelism/) |
| 08 | [Activation memory and recomputation](distributed/08-activation-memory/) |
| 09 | [Mixed precision and FP8 training](distributed/09-mixed-precision-fp8/) |
| 10 | [Putting it together: 4D layouts](distributed/10-putting-it-together/) |
| 11 | [Reliability and stability](distributed/11-reliability-stability/) |

## Web crawling and pretraining data

Ten 9-beat decks plus 6 hands-on [Colab notebooks](build-it/).

| # | Deck |
|---|------|
| 01 | [Where pretraining data comes from](pretraining-data/01-where-data-comes-from/) |
| 02 | [How a web crawler works](pretraining-data/02-how-a-crawler-works/) |
| 03 | [Crawling at scale](pretraining-data/03-crawling-at-scale/) |
| 04 | [robots.txt and consent](pretraining-data/04-robots-and-consent/) |
| 05 | [Text extraction](pretraining-data/05-text-extraction/) |
| 06 | [Quality filtering](pretraining-data/06-quality-filtering/) |
| 07 | [Deduplication](pretraining-data/07-deduplication/) |
| 08 | [PII and safety filtering](pretraining-data/08-pii-and-safety/) |
| 09 | [Data mixtures and repetition](pretraining-data/09-mixtures-and-repetition/) |
| 10 | [Reference pipelines](pretraining-data/10-reference-pipelines/) |

## PyTorch for LLMs

Nine 9-beat decks plus 9 hands-on [Colab notebooks](build-it/), checked against PyTorch 2.14.1.

| # | Deck |
|---|------|
| 01 | [Tensors, strides and views](pytorch/01-tensors/) |
| 02 | [Autograd](pytorch/02-autograd/) |
| 03 | [nn.Module and a transformer block](pytorch/03-nn-module/) |
| 04 | [The training loop](pytorch/04-training-loop/) |
| 05 | [Data pipelines for LLMs](pytorch/05-data/) |
| 06 | [Mixed precision in PyTorch](pytorch/06-mixed-precision/) |
| 07 | [Performance: compile, SDPA, memory](pytorch/07-performance/) |
| 08 | [Distributed training in PyTorch](pytorch/08-distributed/) |
| 09 | [Putting it together: a tiny GPT](pytorch/09-putting-it-together/) |

## vLLM internals and operation

Eight 9-beat decks plus 5 hands-on [Colab notebooks](build-it/), checked against vLLM v0.31.0.

| # | Deck |
|---|------|
| 01 | [What vLLM is and a request's life](vllm/01-what-is-vllm/) |
| 02 | [Engine architecture](vllm/02-engine-architecture/) |
| 03 | [KV cache manager and PagedAttention](vllm/03-kv-cache-manager/) |
| 04 | [The scheduler: continuous batching and chunked prefill](vllm/04-scheduler/) |
| 05 | [Automatic prefix caching](vllm/05-prefix-caching/) |
| 06 | [Speculative decoding in vLLM](vllm/06-speculative-decoding/) |
| 07 | [Parallelism and quantization](vllm/07-parallelism-and-quantization/) |
| 08 | [Running and tuning vLLM](vllm/08-running-and-tuning/) |

## Visual Agents

Twelve decks in four topics, using the agent template: problem, core idea, high-level design, low-level design, trade-offs, failure modes, challenges in production.

| Topic | Deck |
|---|---|
| agent-foundations | [What an agent is](agent-foundations/01-what-is-an-agent/) |
| agent-foundations | [Tool calling](agent-foundations/02-tool-calling/) |
| agent-foundations | [ReAct: reasoning and acting](agent-foundations/03-react-loop/) |
| agent-foundations | [Planning and task decomposition](agent-foundations/04-planning/) |
| agent-context | [Memory and context management](agent-context/01-memory/) |
| agent-context | [Agentic retrieval (RAG)](agent-context/02-agentic-rag/) |
| agent-context | [Model Context Protocol (MCP)](agent-context/03-mcp/) |
| agent-systems | [Multi-agent systems](agent-systems/01-multi-agent/) |
| agent-systems | [Computer and browser use](agent-systems/02-computer-use/) |
| agent-operations | [Evaluating agents](agent-operations/01-evaluating-agents/) |
| agent-operations | [Safety and reliability](agent-operations/02-safety-and-reliability/) |
| agent-operations | [Cost and latency](agent-operations/03-cost-and-latency/) |

## Editing and regenerating

Deck content lives in [`content/`](content/) as Markdown (`deck.md`) plus each deck's interactive code (`widget.js`); see [`content/README.md`](content/README.md) for the format. To rebuild the site:

```bash
pip install -r tools/requirements.txt
python3 tools/build_decks.py        # content/ → <topic>/<slug>/index.html
python3 tools/build_indexes.py      # notebook index and generated hub pages
python3 tools/build_home.py         # landing pages: index.html (chooser), llm/, agents/
python3 tools/build_site_extras.py  # glossary, reading lists, hub maps (run last)
python3 tools/decks/acronyms.py lint */[0-9][0-9]-*/index.html   # every acronym explained at first use
python3 tools/check_papers.py       # paper links and arXiv titles
```

Pushing changes under `content/`, `shared/` or `tools/` to `main` runs the same build in a GitHub Action, which commits the regenerated pages. Notebooks are generated by `tools/notebooks/build_*.py`. The old Python deck generators are kept read-only in [`tools/legacy/`](tools/legacy/).

These are static HTML files with no build step. Open `index.html` in a browser. Keyboard controls: ←/→ or Space to move between slides, F for full screen.
