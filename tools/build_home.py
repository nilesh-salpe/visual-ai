"""Landing pages: the root chooser (index.html), the LLM guide (llm/index.html) and the agents guide (agents/index.html).

Card text is written without acronym expansions; build_site_extras.py expands each acronym at its first use per page.
Run before build_site_extras.py:
    python3 tools/build_home.py
"""
import glob, html, os

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

LLM_SECTIONS = [  # (section, [(folder, label, title, blurb, tags), ...])
    ('Foundations', [
        ('math', 'Foundations · 10 decks + 6 Colab notebooks', 'Math for LLMs and neural networks', 'Vectors, matrices, SVD and low rank, the chain rule, probability and sampling, maximum likelihood, entropy and KL, stable softmax, optimization and floating point.', ['dot products', 'backprop', 'KL', 'softmax']),
        ('nn-fundamentals', 'Foundations · 10 decks + 7 Colab notebooks', 'Neural network fundamentals for LLMs', 'MLPs, activations, backpropagation, losses, AdamW and schedules, initialization, normalization and residuals, regularization, embeddings and a first language model.', ['backprop', 'AdamW', 'init', 'embeddings']),
    ]),
    ('Hardware and clusters', [
        ('gpu', 'Topic · 8 decks', 'GPU for GenAI', 'What a GPU is, why AI runs on it, the memory hierarchy, servers, clusters, failures, mixed fleets and sharing.', ['roofline', 'NVLink', 'all-reduce', 'MIG']),
        ('cluster-scheduling', 'Topic · 4 decks + 2 Colab notebooks', 'Cluster scheduling', 'How GPU clusters are shared: queues, priorities, fair share, gang placement and backfill; Slurm (26.05); Kubernetes with device plugins, DRA, Kueue and JobSet; and automated failure recovery.', ['Slurm', 'backfill', 'Kueue', 'fair share']),
    ]),
    ('The model', [
        ('transformer', 'Paper · 14 decks', 'Attention Is All You Need', 'The original Transformer paper, explained visually: the problem each piece solves and the core idea behind it, checked against arXiv v7.', ['self-attention', 'multi-head', 'positional encoding', 'results']),
        ('tokenization', 'Topic · 10 decks + playground', 'Tokenization for LLMs', 'How text becomes token ids: BPE, byte-level BPE, WordPiece, unigram LM and SentencePiece, plus vocabulary trade-offs, multilingual cost and quirks. Includes a live tokenizer playground.', ['BPE', 'tiktoken', 'SentencePiece', 'playground']),
        ('architecture', 'Topic · 12 decks + 10 Colab notebooks', 'The Modern LLM Architecture', 'What changed after 2017: pre-norm and RMSNorm, RoPE, SwiGLU, MQA/GQA/MLA, decoder-only stacks, long context (RoPE scaling, sliding window), FlashAttention internals, Mixture of Experts, and SSM and linear-attention hybrids.', ['RoPE', 'GQA', 'FlashAttention', 'MoE']),
    ]),
    ('Data and training', [
        ('pretraining-data', 'Topic · 10 decks + 6 Colab notebooks', 'Web crawling and pretraining data', 'How crawlers work and stay polite, robots.txt and consent, text extraction, quality filtering, MinHash deduplication, PII and safety filtering, data mixtures and the C4 → FineWeb → Llama 3 pipelines.', ['crawler', 'robots.txt', 'MinHash', 'FineWeb']),
        ('distributed', 'Topic · 11 decks + 8 Colab notebooks', 'Distributed training &amp; reliability', 'Data, sharded (ZeRO/FSDP), tensor, pipeline, context and expert parallelism, activation recomputation, mixed precision and FP8, 4D layouts, checkpointing and loss spikes.', ['FSDP', 'pipeline', 'ring attention', 'FP8']),
        ('post-training', 'Topic · 10 decks + 8 Colab notebooks', 'Post-training LLMs', 'SFT, LoRA and QLoRA, reward models, RLHF with PPO, reward hacking, DPO and KTO, RL with verifiable rewards (GRPO, DeepSeek-R1), Constitutional AI, and knowledge distillation.', ['RLHF', 'DPO', 'GRPO', 'LoRA']),
    ]),
    ('Frameworks', [
        ('pytorch', 'Framework · 9 decks + 9 Colab notebooks', 'PyTorch for LLMs', 'Tensors and views, autograd, nn.Module, the training loop, data pipelines, mixed precision, torch.compile and SDPA, DDP and FSDP2, and a tiny GPT. Checked against PyTorch 2.14.1.', ['autograd', 'SDPA', 'torch.compile', 'FSDP2']),
        ('vllm', 'Framework · 10 decks + 6 Colab notebooks', 'vLLM internals and operation', 'How the vLLM engine works and how to run it: process architecture, paged KV cache, the token-budget scheduler, prefix caching, speculative decoding, parallelism, quantization, tuning, single- and multi-node deployment, and the vLLM Router. Checked against vLLM v0.31.0.', ['PagedAttention', 'scheduler', 'deployment', 'router']),
    ]),
    ('Frontier topics', [
        ('reasoning', 'Topic · 4 decks + 1 Colab notebook', 'Reasoning and test-time compute', 'Chain of thought, self-consistency and coverage, verifiers and process reward models, compute-optimal search, and reasoning models (RL on verifiable rewards, budget forcing, thinking budgets, faithfulness).', ['chain of thought', 'best-of-N', 'PRM', 'R1']),
        ('interpretability', 'Topic · 3 decks + 1 Colab notebook', 'Interpretability', 'Features and superposition, sparse autoencoders (Claude 3 Sonnet, GPT-4, Gemma Scope), and circuits, attribution graphs, probes and steering vectors.', ['superposition', 'SAEs', 'circuits', 'steering']),
        ('multimodal', 'Topic · 3 decks + 1 Colab notebook', 'Multimodal LLMs', 'ViT and CLIP, connecting a vision encoder to an LLM (LLaVA, Flamingo, BLIP-2, early fusion), and images as tokens in practice: cost, limits, evaluation and hallucination.', ['ViT', 'CLIP', 'LLaVA', 'visual tokens']),
    ]),
    ('Case studies', [
        ('system-design', 'Case studies · 4 decks + 4 design docs', 'System design case studies', 'End-to-end designs: serving a chat assistant, an enterprise RAG assistant, an autonomous coding agent, and planning a pretraining run.', ['capacity', 'KV cache', 'checkpoints', 'trade-offs']),
    ]),
    ('Serving and evaluation', [
        ('inference', 'Topic · 13 decks + 13 Colab notebooks', 'LLM Inference and Serving', 'Prefill vs decode, KV cache, continuous batching, chunked prefill, PagedAttention, speculative decoding, quantization, tensor parallelism, disaggregation, decoding strategies, and serving at scale (large MoE models, the KV cache across a fleet), with hands-on notebooks.', ['KV cache', 'vLLM', 'speculative', 'Colab']),
        ('evals', 'Topic · 9 decks + 5 Colab notebooks', 'Evaluating LLMs', 'What a score measures, benchmark failure modes, pass@k, error bars and paired comparisons, contamination, LLM-as-judge biases, arena ratings, experiments in LLM training (seed noise, small-to-large decisions), and hallucination and factuality.', ['pass@k', 'error bars', 'LLM judge', 'Arena']),
    ]),
]

AGENT_SECTIONS = [  # same shape as LLM_SECTIONS
    ('Building agents', [
        ('agent-foundations', 'Topic · 5 decks', 'Agent foundations', 'What an agent is, tool calling, the ReAct loop, planning and task decomposition, and prompting and in-context learning.', ['agent loop', 'tool calling', 'ReAct', 'prompting']),
        ('agent-context', 'Topic · 5 decks', 'Agent context', 'Memory and context management, agentic retrieval, the Model Context Protocol (revision 2026-07-28), the Agent2Agent protocol (v1.0), and choosing between retrieval, fine-tuning and long context.', ['memory', 'agentic RAG', 'MCP', 'A2A']),
        ('agent-systems', 'Topic · 3 decks', 'Agent systems', 'Multi-agent orchestrator-workers designs, computer and browser use, and durable workflows for long-running agents.', ['multi-agent', 'computer use', 'Temporal']),
        ('agent-frameworks', 'Topic · 3 decks + 3 notebooks', 'Agent frameworks', 'LangChain basics, LangGraph core and LangGraph in production (checkpoints, interrupts, resuming), with Colab notebooks.', ['LangChain', 'LangGraph', 'checkpoints', 'interrupts']),
    ]),
    ('Platform', [
        ('agent-infra', 'Topic · 4 decks', 'Agent infrastructure', 'The LLM gateway, model and agent routing, identity and access control, and sandboxing agent-run code.', ['LLM gateway', 'routing', 'RBAC', 'sandboxing']),
        ('agent-retrieval', 'Topic · 3 decks', 'Retrieval stack', 'Indexing pipelines, vector databases and ANN indexes, and rerankers.', ['chunking', 'HNSW', 'IVF-PQ', 'rerankers']),
        ('agent-models', 'Topic · 2 decks', 'Models for agents', 'Training LLMs for tool use and agency, and serving LLMs for agent workloads.', ['tool-use SFT', 'agentic RL', 'prefix reuse', 'constrained decoding']),
    ]),
    ('Case studies', [
        ('system-design', 'Case studies · 4 decks + 4 design docs', 'System design case studies', 'End-to-end designs: serving a chat assistant, an enterprise RAG assistant, an autonomous coding agent, and planning a pretraining run.', ['RAG', 'sandboxes', 'durable execution', 'trade-offs']),
    ]),
    ('Running agents', [
        ('agent-operations', 'Topic · 5 decks', 'Agent operations', 'Evaluating agents (pass^k), safety and reliability, cost and latency, online experimentation for LLM products, and jailbreaks and adversarial robustness.', ['evals', 'prompt injection', 'A/B tests', 'jailbreaks']),
    ]),
]
AGENT_PLANNED = ['What an agent is: an LLM in a loop', 'Tool calling and function schemas', 'ReAct: interleaving reasoning and actions', 'Planning and task decomposition',
                 'Memory: context, retrieval and long-term stores', 'Retrieval for agents', 'MCP and tool ecosystems', 'Multi-agent patterns', 'Computer and browser use',
                 'Evaluating agents', 'Reliability and safety: prompt injection, sandboxing, human oversight', 'Cost and latency of agent loops']

PAGE = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="{up}shared/deck.css">
<style>body {{ overflow-y: auto; }} .sec {{ margin: 30px 0 4px; font: 700 12px 'JetBrains Mono', monospace; letter-spacing: .06em; text-transform: uppercase; color: var(--a); }} .hub-card.planned {{ opacity: .72; cursor: default; }} .hub-card.big h3 {{ font-size: 26px; }} .hub-card.big {{ padding: 26px; }}</style>
</head>
<body>
<div class="hub">
{body}
</div>
</body>
</html>
'''


def n_decks(folder):
    return len(glob.glob(os.path.join(REPO, folder, '[0-9][0-9]-*', 'index.html')))


def card(folder, label, title, blurb, tags, up='../'):
    t = ''.join(f'<span>{x}</span>' for x in tags)
    return f'<a class="hub-card" href="{up}{folder}/index.html"><div class="n">{label}</div><h3>{title}</h3><p>{blurb}</p><div class="tags">{t}</div></a>'


def sections_html(sections):
    return ''.join(f'\n  <div class="sec">{name}</div>\n  <div class="hub-grid">\n    ' + '\n    '.join(card(*c) for c in cards) + '\n  </div>' for name, cards in sections)


def links(up):
    return f'<p style="margin:6px 0 0;display:flex;gap:10px;flex-wrap:wrap"><a class="btn" href="{up}glossary/index.html">🔤 Glossary of acronyms</a><a class="btn" href="{up}build-it/index.html">🛠 All Colab notebooks</a></p>'


def llm_page():
    topics = sum(len(c) for _, c in LLM_SECTIONS); decks = sum(n_decks(c[0]) for _, cs in LLM_SECTIONS for c in cs)
    body = f'''  <a class="brand" href="../index.html">← Visual AI</a>
  <div class="label" style="margin-top:28px">Visual LLM · {topics} topics · {decks} decks</div>
  <h1>How large language models work</h1>
  <p class="lede">Interactive slide decks on LLM systems, from the math and hardware underneath to architecture, data, training, serving and evaluation. Each topic is a folder, and each subtopic is a deck inside it.</p>
  {links('../')}{sections_html(LLM_SECTIONS)}
  <p style="margin-top:28px"><a class="btn" href="../agents/index.html">Next: Visual Agents →</a></p>'''
    return PAGE.format(title='Visual LLM', up='../', body=body)


def agents_page():
    if AGENT_SECTIONS:
        content = sections_html(AGENT_SECTIONS)
    else:
        items = '\n    '.join(f'<div class="hub-card planned"><div class="n">Planned</div><h3>{html.escape(t)}</h3></div>' for t in AGENT_PLANNED)
        content = f'\n  <div class="sec">In preparation · draft outline</div>\n  <div class="hub-grid">\n    {items}\n  </div>'
    body = f'''  <a class="brand" href="../index.html">← Visual AI</a>
  <div class="label" style="margin-top:28px">Visual Agents</div>
  <h1>How LLM agents work</h1>
  <p class="lede">Interactive slide decks on agentic systems built on LLMs. Each deck follows one template: problem, core idea, high-level design, low-level design, trade-offs, failure modes and challenges in production, with diagrams you can step through. They build on the <a href="../llm/index.html">Visual LLM</a> guide.</p>
  {links('../')}{content}
  <p style="margin-top:28px"><a class="btn" href="../llm/index.html">← Visual LLM</a></p>'''
    return PAGE.format(title='Visual Agents', up='../', body=body)


def root_page():
    llm_decks = sum(n_decks(c[0]) for _, cs in LLM_SECTIONS for c in cs)
    agent_decks = sum(n_decks(c[0]) for _, cs in AGENT_SECTIONS for c in cs)
    body = f'''  <div class="label">Visual AI</div>
  <h1>AI concepts, explained visually</h1>
  <p class="lede">Interactive slide decks and hands-on Colab notebooks that explain how modern AI systems work. Pick a guide.</p>
  <div class="hub-grid" style="margin-top:22px">
    <a class="hub-card big" href="llm/index.html"><div class="n">Visual LLM · {sum(len(c) for _, c in LLM_SECTIONS)} topics · {llm_decks} decks</div><h3>Large language models</h3><p>Math and neural-network foundations, GPUs, the Transformer and modern architectures, tokenization, pretraining data, distributed training, post-training, inference and evaluation.</p><div class="tags"><span>Transformer</span><span>KV cache</span><span>RLHF</span><span>FSDP</span></div></a>
    <a class="hub-card big" href="agents/index.html"><div class="n">Visual Agents · {f"{agent_decks} decks" if agent_decks else "in preparation"}</div><h3>LLM agents</h3><p>Agentic systems built on LLMs: tool calling, reasoning-action loops, planning, memory and retrieval, multi-agent patterns, evaluation and safety.</p><div class="tags"><span>tool use</span><span>ReAct</span><span>memory</span><span>MCP</span></div></a>
  </div>
  <p style="margin-top:18px">Also: <a href="system-design/index.html">System design case studies</a> · <a href="status/index.html">Review status of every deck</a></p>
  {links('')}'''
    return PAGE.format(title='Visual AI', up='', body=body)


if __name__ == '__main__':
    for path, page in [('index.html', root_page()), ('llm/index.html', llm_page()), ('agents/index.html', agents_page())]:
        os.makedirs(os.path.dirname(os.path.join(REPO, path)) or REPO, exist_ok=True)
        open(os.path.join(REPO, path), 'w').write(page)
        print('wrote', path)
