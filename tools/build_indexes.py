"""Regenerate build-it/index.html, build-it/README.md and architecture/index.html from the notebook indexes.

Run after tools/notebooks/build_*.py:  python3 tools/build_indexes.py
"""
import json, os

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GH = 'https://github.com/nilesh-salpe/visual-ai/blob/main/'
BADGE = 'https://colab.research.google.com/assets/colab-badge.svg'
PHASES = [  # (heading, notebook folder, index json)
    ('Foundations · Math for LLMs', 'math', 'index_math.json'),
    ('Foundations · Neural network fundamentals', 'nn-fundamentals', 'index_nn.json'),
    ('Phase 1 · LLM inference and serving', 'inference', 'index_inference.json'),
    ('Phase 2 · The modern LLM architecture', 'architecture', 'index_architecture.json'),
    ('Phase 3 · Post-training', 'post-training', 'index_post_training.json'),
    ('Phase 4 · Evaluating LLMs', 'evals', 'index_evals.json'),
    ('Phase 5 · Distributed training & reliability', 'distributed', 'index_distributed.json'),
    ('Phase 6 · Web crawling & pretraining data', 'pretraining-data', 'index_data.json'),
    ('Frameworks · PyTorch for LLMs', 'pytorch', 'index_torch.json'),
    ('Frameworks · vLLM internals', 'vllm', 'index_vllm.json'),
    ('Infrastructure · Cluster scheduling', 'cluster-scheduling', 'index_cluster.json'),
    ('Frontier · Reasoning and test-time compute', 'reasoning', 'index_reasoning.json'),
    ('Frontier · Interpretability', 'interpretability', 'index_interp.json'),
    ('Frontier · Multimodal LLMs', 'multimodal', 'index_multimodal.json'),
    ('Agents · LangChain and LangGraph', 'agent-frameworks', 'index_agent_frameworks.json'),
]



def _write(path, text):
    """Build first, then write: opening with 'w' before the text exists would truncate the file if building fails."""
    assert text.strip(), path
    with open(path, 'w') as fh:
        fh.write(text)

def load(name):
    return json.load(open(os.path.join(REPO, 'tools', 'notebooks', name)))


def build_it_html():
    sections = []
    for heading, _, idx in PHASES:
        rows = ''.join(
            f'<tr><td>{n["title"]}</td><td>{n["minutes"]} min</td>'
            f'<td><a href="{n["colab"]}" target="_blank" rel="noopener"><img src="{BADGE}" alt="Open in Colab" style="vertical-align:middle"></a></td>'
            f'<td><a href="{GH}{n["path"]}" target="_blank" rel="noopener">GitHub</a> · <a href="../{n["deck"]}index.html">deck</a></td></tr>'
            for n in load(idx))
        sections.append(f'  <h2 style="margin-top:30px;font-size:22px">{heading}</h2>\n'
                        f'  <div class="visual scroll-x"><table class="tbl"><tr><th>Notebook</th><th>Time</th><th>Run</th><th>Links</th></tr>{rows}</table></div>')
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Build It Notebooks</title>
<link rel="stylesheet" href="../shared/deck.css">
<style>body {{ overflow-y: auto; }} .tbl td {{ vertical-align: middle; }}</style>
</head>
<body>
<div class="hub">
  <a class="brand" href="../index.html">← Visual AI</a>
  <div class="label" style="margin-top:28px">Hands-on · Google Colab</div>
  <h1>Build it</h1>
  <p class="lede">Implement the systems behind the decks yourself. Each notebook runs in Google Colab with NumPy on CPU, so no GPU or setup is needed.</p>
  <div class="visual">
    <h3>How each notebook works</h3>
    <ol style="margin:8px 0 0;padding-left:20px;color:var(--muted);line-height:1.7">
      <li>Click <b>Open in Colab</b>, then run the <b>Setup</b> cell.</li>
      <li>Fill in each <code>TODO</code>, then run the collapsed <b>Tests</b> cell under it: ⏳ not done · ✅ passed · ❌ failed, with the reason.</li>
      <li>Stuck? <b>Reference solutions</b> are collapsed at the bottom. Try first.</li>
      <li>The <b>Experiments</b> section uses the solutions to show the effect at scale.</li>
    </ol>
  </div>
{chr(10).join(sections)}
  <p class="cite" style="margin-top:20px">Later phases (distributed training, pretraining, GPU performance) will add their notebooks here.</p>
</div>
</body>
</html>
'''


def build_it_md():
    out = ['# Build it: hands-on notebooks', '',
           'Run in Google Colab (NumPy, CPU only). Each notebook: Setup → tasks with `TODO`s → built-in tests (⏳/✅/❌) → collapsed reference solutions → experiments.', '']
    for heading, folder, idx in PHASES:
        out += [f'## {heading}', '', '| Notebook | Time | Colab |', '|---|---|---|']
        for n in load(idx):
            out.append(f'| [{n["title"]}]({n["path"].replace("build-it/", "")}) | {n["minutes"]} min | [![Open In Colab]({BADGE})]({n["colab"]}) |')
        out += ['', f'Concept decks: https://nilesh-salpe.github.io/visual-ai/{folder}/', '']
    return '\n'.join(out)


ARCH_CARDS = [
    ('01-what-changed', 'What changed since 2017', 'The 2017 block vs a Llama 3 block: seven swaps, and how to read a config.json.'),
    ('02-normalization', 'Pre-norm and RMSNorm', 'Why the norm moved inside the residual branch, and why the mean was dropped.'),
    ('03-rope', 'RoPE', 'Rotate q and k by position: scores depend only on distance.'),
    ('04-swiglu', 'SwiGLU', 'Gated FFNs, the ⅔ rule, and where 11,008 and 14,336 come from.'),
    ('05-attention-variants', 'MQA, GQA and MLA', 'Share or compress keys and values; decoupled RoPE.'),
    ('06-decoder-only', 'Decoder-only, and why it won', 'Masks for every family, packing and the document mask.'),
    ('07-rope-scaling', 'Long context I: stretching RoPE', 'PI, NTK-aware, YaRN and Llama 3\'s staged long-context training.'),
    ('08-sliding-window', 'Long context II: sliding window and ALiBi', 'Windows relayed through depth, rolling KV buffers, distance penalties.'),
    ('09-flash-attention', 'FlashAttention internals', 'Tiling, online softmax, recompute; FA1 → FA2 → FA3.'),
    ('10-mixture-of-experts', 'Mixture of Experts', 'Top-k routing, load balancing, capacity; Mixtral and DeepSeek-V2.'),
    ('11-putting-it-together', 'Putting it together', 'The whole block, a size calculator, and a checklist for any model.'),
]


def arch_hub():
    cards = ''.join(f'<a class="hub-card" href="{s}/index.html"><div class="n">{s[:2]}</div><h3>{t}</h3><p>{p}</p></a>' for s, t, p in ARCH_CARDS)
    n_nb = len(load('index_architecture.json'))
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Modern LLM</title>
<link rel="stylesheet" href="../shared/deck.css">
<style>body {{ overflow-y: auto; }}</style>
</head>
<body>
<div class="hub">
  <a class="brand" href="../llm/index.html">← Visual LLM</a>
  <div class="label" style="margin-top:28px">Visual guide · {len(ARCH_CARDS)} decks + {n_nb} Colab notebooks</div>
  <h1>The Modern LLM Architecture</h1>
  <p class="lede">What changed after the 2017 Transformer, and why: pre-norm and RMSNorm, RoPE, SwiGLU, MQA/GQA/MLA, decoder-only stacks, long-context methods, FlashAttention and Mixture of Experts. Every deck follows the 9-beat template, numbers are checked against the source papers and model configs, and each concept has a hands-on Colab notebook. Start with the <a href="../transformer/index.html">Attention Is All You Need</a> guide if the 2017 block is new to you.</p>
  <div class="visual" style="margin-top:22px;display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;background:var(--e-soft);border-color:var(--e)">
    <div><h3 style="margin:0 0 4px">🛠 Build it: {n_nb} Colab notebooks</h3><p class="caption" style="margin:0">Implement RMSNorm, RoPE, SwiGLU, MLA weight absorption, attention masks, PI/NTK/YaRN, a rolling KV cache, FlashAttention, an MoE router and a full Llama block in NumPy. Built-in tests, hidden solutions, no GPU needed.</p></div>
    <a class="btn primary" href="../build-it/index.html">Open the notebooks →</a>
  </div>
  <div class="hub-grid">{cards}</div>
  <p class="cite" style="margin-top:26px">Sources: Xiong et al. 2020; Zhang &amp; Sennrich 2019; Su et al. 2021 (RoFormer); Shazeer 2020 (GLU variants); Shazeer 2019 (MQA); Ainslie et al. 2023 (GQA); DeepSeek-V2 2024; Wang et al. 2022; Chen et al. 2023 (PI); Peng et al. 2023 (YaRN); Jiang et al. 2023 (Mistral 7B); Press et al. 2022 (ALiBi); Dao et al. 2022, Dao 2023, Shah et al. 2024 (FlashAttention 1–3); Milakov &amp; Gimelshein 2018; Fedus et al. 2022 (Switch); Jiang et al. 2024 (Mixtral); Radford et al. 2019 (GPT-2); Chowdhery et al. 2022 (PaLM); Touvron et al. 2023 (LLaMA, Llama 2); Llama Team 2024 (Llama 3).</p>
</div>
</body>
</html>
'''


if __name__ == '__main__':
    _write(os.path.join(REPO, 'build-it', 'index.html'), build_it_html())
    _write(os.path.join(REPO, 'build-it', 'README.md'), build_it_md())
    _write(os.path.join(REPO, 'architecture', 'index.html'), arch_hub())
    print('wrote build-it/index.html, build-it/README.md, architecture/index.html')


POST_CARDS = [
    ('01-pipeline', 'The post-training pipeline', 'From base model to assistant: SFT, preferences, verifiable rewards; real lab recipes.'),
    ('02-supervised-fine-tuning', 'Supervised fine-tuning', 'Chat templates, loss on assistant tokens only, packing, quality over quantity.'),
    ('03-lora-qlora', 'LoRA and QLoRA', 'Low-rank adapters, merging, NF4, double quantization.'),
    ('04-reward-models', 'Reward models', 'Bradley-Terry, rankings to pairs, noise ceilings.'),
    ('05-rlhf-ppo', 'RLHF with PPO', 'Reward − β·KL, clipped updates, four models, PPO-ptx.'),
    ('06-reward-hacking', 'Reward hacking and overoptimization', 'Goodhart curves in KL, best-of-n, mitigations.'),
    ('07-dpo-and-friends', 'DPO, KTO and rejection sampling', 'The implicit reward and RL-free preference tuning.'),
    ('08-rlvr-grpo', 'RLVR and GRPO', 'Verifiable rewards, group baselines, DeepSeek-R1.'),
    ('09-rlaif-constitutional-ai', 'RLAIF and Constitutional AI', 'Principles, self-critique and AI preference labels.'),
    ('10-distillation', 'Knowledge distillation', 'Soft targets, sequence-level and on-policy distillation; how small open models are trained.'),
]


def post_hub():
    cards = ''.join(f'<a class="hub-card" href="{s}/index.html"><div class="n">{s[:2]}</div><h3>{t}</h3><p>{p}</p></a>' for s, t, p in POST_CARDS)
    n_nb = len(load('index_post_training.json'))
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Post-training LLMs</title>
<link rel="stylesheet" href="../shared/deck.css">
<style>body {{ overflow-y: auto; }}</style>
</head>
<body>
<div class="hub">
  <a class="brand" href="../llm/index.html">← Visual LLM</a>
  <div class="label" style="margin-top:28px">Visual guide · {len(POST_CARDS)} decks + {n_nb} Colab notebooks</div>
  <h1>Post-training LLMs</h1>
  <p class="lede">How a pretrained model becomes an assistant: supervised fine-tuning, LoRA and QLoRA, reward models, RLHF with PPO, reward hacking, DPO and its relatives, RL with verifiable rewards (GRPO), Constitutional AI, and knowledge distillation into smaller models. Every deck follows the 9-beat template, numbers are checked against the source papers, and most concepts have a hands-on Colab notebook.</p>
  <div class="visual" style="margin-top:22px;display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;background:var(--e-soft);border-color:var(--e)">
    <div><h3 style="margin:0 0 4px">🛠 Build it: {n_nb} Colab notebooks</h3><p class="caption" style="margin:0">Implement SFT loss masking and packing, LoRA, NF4 quantization, a Bradley-Terry reward model, PPO with a KL penalty, best-of-n overoptimization, DPO and GRPO in NumPy. Built-in tests, hidden solutions, no GPU needed.</p></div>
    <a class="btn primary" href="../build-it/index.html">Open the notebooks →</a>
  </div>
  <div class="hub-grid">{cards}</div>
  <p class="cite" style="margin-top:26px">Sources: Ouyang et al. 2022 (InstructGPT); Christiano et al. 2017; Stiennon et al. 2020; Schulman et al. 2017 (PPO); Touvron et al. 2023 (Llama 2); Llama Team 2024 (Llama 3); Hu et al. 2021 (LoRA); Dettmers et al. 2023 (QLoRA); Gao et al. 2022 (RM overoptimization); Rafailov et al. 2023 (DPO); Ethayarajh et al. 2024 (KTO); Shao et al. 2024 (DeepSeekMath, GRPO); DeepSeek-AI 2025 (DeepSeek-R1); Lambert et al. 2024 (Tülu 3); Bai et al. 2022 (Constitutional AI).</p>
</div>
</body>
</html>
'''


if __name__ == '__main__':
    _write(os.path.join(REPO, 'post-training', 'index.html'), post_hub())
    print('wrote post-training/index.html')


EVAL_CARDS = [
    ('01-what-an-eval-measures', 'What an eval measures', 'A score is a protocol: prompts, decoding, scoring, uncertainty. HELM\'s 7 metrics.'),
    ('02-benchmarks', 'Benchmarks and their failure modes', 'MMLU, GPQA, GSM8K, HumanEval, SWE-bench; floors, ceilings, saturation.'),
    ('03-pass-at-k', 'pass@k and sampling metrics', 'The unbiased estimator and choosing k.'),
    ('04-error-bars', 'Error bars and comparing models', 'Standard errors, clustered errors, paired tests, power analysis.'),
    ('05-contamination', 'Contamination', '13-gram overlap, clean vs dirty scores, fresh test sets.'),
    ('06-llm-as-judge', 'LLM-as-judge', 'Agreement with humans; position, verbosity and self-enhancement bias.'),
    ('07-arenas', 'Arenas and ratings', 'Bradley-Terry vs online Elo, confidence intervals.'),
    ('08-training-experiments', 'Experiments in LLM training', 'Seed noise, low-noise metrics, small-to-large decisions, search.'),
    ('09-hallucination', 'Hallucination and factuality', 'Why models guess, SimpleQA and FActScore, sample-based detection, grounding.'),
]


def evals_hub():
    cards = ''.join(f'<a class="hub-card" href="{s}/index.html"><div class="n">{s[:2]}</div><h3>{t}</h3><p>{p}</p></a>' for s, t, p in EVAL_CARDS)
    n_nb = len(load('index_evals.json'))
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Evaluating LLMs</title>
<link rel="stylesheet" href="../shared/deck.css">
<style>body {{ overflow-y: auto; }}</style>
</head>
<body>
<div class="hub">
  <a class="brand" href="../llm/index.html">← Visual LLM</a>
  <div class="label" style="margin-top:28px">Visual guide · {len(EVAL_CARDS)} decks + {n_nb} Colab notebooks</div>
  <h1>Evaluating LLMs</h1>
  <p class="lede">What an eval score really measures and how much to trust it: benchmark design and failure modes, pass@k, error bars and paired comparisons, contamination, LLM-as-judge biases, and arena ratings. Every deck follows the 9-beat template, numbers are checked against the source papers, and the statistics have hands-on Colab notebooks.</p>
  <div class="visual" style="margin-top:22px;display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;background:var(--e-soft);border-color:var(--e)">
    <div><h3 style="margin:0 0 4px">🛠 Build it: {n_nb} Colab notebooks</h3><p class="caption" style="margin:0">Implement the unbiased pass@k estimator, standard and clustered errors, paired tests and power analysis, an n-gram contamination detector, a judge position-swap test, Bradley-Terry ratings and online Elo in NumPy.</p></div>
    <a class="btn primary" href="../build-it/index.html">Open the notebooks →</a>
  </div>
  <div class="hub-grid">{cards}</div>
  <p class="cite" style="margin-top:26px">Sources: Liang et al. 2022 (HELM); Sclar et al. 2023; Hendrycks et al. 2021 (MMLU); Wang et al. 2024 (MMLU-Pro); Rein et al. 2023 (GPQA); Cobbe et al. 2021 (GSM8K); Chen et al. 2021 (HumanEval, pass@k); Jimenez et al. 2024 (SWE-bench); Miller 2024 (error bars); Brown et al. 2020 (GPT-3 contamination); Zhang et al. 2024 (GSM1k); Zheng et al. 2023 (MT-Bench); Dubois et al. 2024 (length-controlled AlpacaEval); Chiang et al. 2024 (Chatbot Arena).</p>
</div>
</body>
</html>
'''


if __name__ == '__main__':
    _write(os.path.join(REPO, 'evals', 'index.html'), evals_hub())
    print('wrote evals/index.html')


DIST_CARDS = [
    ('01-why-distribute', 'Why training must be distributed', 'The memory and time walls; the four axes of parallelism.'),
    ('02-data-parallelism', 'Data parallelism', 'Ring all-reduce (≈ 2·S per GPU) and bucketed overlap.'),
    ('03-zero-fsdp', 'ZeRO and FSDP', 'Shard optimizer state, gradients and parameters: 4×, 8×, N×.'),
    ('04-tensor-sequence-parallelism', 'Tensor and sequence parallelism', 'Megatron column/row splits, sequence parallelism, selective recompute.'),
    ('05-pipeline-parallelism', 'Pipeline parallelism', 'GPipe, 1F1B, interleaved and zero-bubble schedules; the (p−1)/m bubble.'),
    ('06-context-parallelism', 'Context parallelism', 'Ring attention, all-gather K/V (Llama 3) and Ulysses all-to-all.'),
    ('07-expert-parallelism', 'Expert parallelism', 'All-to-all dispatch and combine; DeepSeek-V3 at 64-way EP.'),
    ('08-activation-memory', 'Activation memory and recomputation', 'sbh(34 + 5as/h), √n checkpointing, selective recompute.'),
    ('09-mixed-precision-fp8', 'Mixed precision and FP8 training', 'FP32 master weights, loss scaling, BF16, fine-grained FP8 scales.'),
    ('10-putting-it-together', 'Putting it together: 4D layouts', 'TP ⊂ CP ⊂ PP ⊂ DP; Llama 3 405B on 16,384 GPUs.'),
    ('11-reliability-stability', 'Reliability and stability', 'Checkpoint intervals, stragglers, loss spikes, z-loss and QK-norm.'),
]


def dist_hub():
    cards = ''.join(f'<a class="hub-card" href="{s}/index.html"><div class="n">{s[:2]}</div><h3>{t}</h3><p>{p}</p></a>' for s, t, p in DIST_CARDS)
    n_nb = len(load('index_distributed.json'))
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Distributed Training</title>
<link rel="stylesheet" href="../shared/deck.css">
<style>body {{ overflow-y: auto; }}</style>
</head>
<body>
<div class="hub">
  <a class="brand" href="../llm/index.html">← Visual LLM</a>
  <div class="label" style="margin-top:28px">Visual guide · {len(DIST_CARDS)} decks + {n_nb} Colab notebooks</div>
  <h1>Distributed training &amp; reliability</h1>
  <p class="lede">How frontier models are trained across thousands of GPUs: data, sharded, tensor, sequence, pipeline, context and expert parallelism, activation recomputation, mixed precision and FP8, 4D layouts, and keeping a months-long run alive. Every deck follows the 9-beat template and numbers are checked against the source papers.</p>
  <div class="visual" style="margin-top:22px;display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;background:var(--e-soft);border-color:var(--e)">
    <div><h3 style="margin:0 0 4px">🛠 Build it: {n_nb} Colab notebooks</h3><p class="caption" style="margin:0">Implement ring all-reduce, ZeRO sharding, tensor-parallel training, pipeline schedules, activation checkpointing, loss scaling, ring attention and a checkpoint/failure simulator in NumPy.</p></div>
    <a class="btn primary" href="../build-it/index.html">Open the notebooks →</a>
  </div>
  <div class="hub-grid">{cards}</div>
  <p class="cite" style="margin-top:26px">Sources: Li et al. 2020 (PyTorch DDP); Rajbhandari et al. 2020 (ZeRO); Zhao et al. 2023 (FSDP); Shoeybi et al. 2019 and Narayanan et al. 2021 (Megatron-LM); Korthikanti et al. 2022; Huang et al. 2019 (GPipe); Narayanan et al. 2019 (PipeDream); Qi et al. 2023 (Zero Bubble); Liu et al. 2023 (Ring Attention); Jacobs et al. 2023 (Ulysses); Lepikhin et al. 2020 (GShard); Chen et al. 2016; Micikevicius et al. 2018; DeepSeek-AI 2024 (V3); Llama Team 2024 (Llama 3); Jiang et al. 2024 (MegaScale); Wang et al. 2023 (Gemini); Chowdhery et al. 2022 (PaLM); Dehghani et al. 2023 (ViT-22B).</p>
</div>
</body>
</html>
'''


if __name__ == '__main__':
    _write(os.path.join(REPO, 'distributed', 'index.html'), dist_hub())
    print('wrote distributed/index.html')


LABELS = {'current': 'Current practice', 'trend': 'Recent trend', 'legacy': 'Legacy', 'research': 'Research'}


def _status_badge(folder, slug):
    """The deck's review-status label (front matter `status.label`), if it has been reviewed."""
    path = os.path.join(REPO, 'content', folder, slug, 'deck.md')
    if not os.path.exists(path):
        return ''
    import yaml
    st = (yaml.safe_load(open(path).read().split('---\n', 2)[1]) or {}).get('status') or {}
    return f'<div><span class="lbl lbl-{st["label"]}">{LABELS[st["label"]]}</span></div>' if st.get('label') in LABELS else ''


def topic_hub(folder, title, label, lede, nb_index, nb_blurb, cards, sources, back='../llm/index.html', back_label='Visual LLM'):
    """Generic hub page for a topic: header, optional Build-it banner, deck cards, sources."""
    grid = ''.join(f'<a class="hub-card" href="{s}/index.html"><div class="n">{s[:2]}</div><h3>{t}</h3><p>{p}</p>{_status_badge(folder, s)}</a>' for s, t, p in cards)
    n_nb = len(load(nb_index)) if nb_index else 0
    count = f'{len(cards)} decks' + (f' + {n_nb} Colab notebooks' if n_nb else '')
    banner = '' if not n_nb else f'''
  <div class="visual" style="margin-top:22px;display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;background:var(--e-soft);border-color:var(--e)">
    <div><h3 style="margin:0 0 4px">🛠 Build it: {n_nb} Colab notebooks</h3><p class="caption" style="margin:0">{nb_blurb}</p></div>
    <a class="btn primary" href="../build-it/index.html">Open the notebooks →</a>
  </div>'''
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{label}</title>
<link rel="stylesheet" href="../shared/deck.css">
<style>body {{ overflow-y: auto; }}</style>
</head>
<body>
<div class="hub">
  <a class="brand" href="{back}">← {back_label}</a>
  <div class="label" style="margin-top:28px">Visual guide · {count}</div>
  <h1>{title}</h1>
  <p class="lede">{lede}</p>{banner}
  <div class="hub-grid">{grid}</div>
  <p class="cite" style="margin-top:26px">Sources: {sources}</p>
</div>
</body>
</html>
'''


MATH_CARDS = [
    ('01-vectors-dot-products', 'Vectors and dot products', 'Similarity, cosine, and the √d in attention.'),
    ('02-matrices-linear-layers', 'Matrices and linear layers', 'What a matrix does; shapes, parameters (≈12d² per layer) and 2mkn FLOPs.'),
    ('03-eigen-svd-low-rank', 'Eigenvalues, SVD and low rank', 'Best rank-r approximation and why LoRA works.'),
    ('04-derivatives-chain-rule', 'Derivatives and the chain rule', 'Computational graphs, reverse-mode autodiff, gradient checks.'),
    ('05-probability-sampling', 'Probability and sampling', 'Next-token distributions, temperature, top-k and top-p.'),
    ('06-maximum-likelihood', 'Maximum likelihood and cross-entropy', 'The LLM loss, its p − onehot gradient, and perplexity.'),
    ('07-information-theory', 'Information theory for LLMs', 'Entropy, cross-entropy, KL and where KL appears.'),
    ('08-softmax-logsumexp', 'Softmax and log-sum-exp', 'The max-trick, log-softmax and the online softmax.'),
    ('09-optimization-basics', 'Optimization basics', 'Learning-rate limits, conditioning, momentum and Adam.'),
    ('10-floating-point', 'Floating-point numbers', 'Exponent vs mantissa; FP32, BF16, FP16 and FP8.'),
]

if __name__ == '__main__':
    _write(os.path.join(REPO, 'math', 'index.html'), topic_hub(
        'math', 'Math for LLMs and neural networks', 'Math for LLMs',
        'The mathematics every LLM concept rests on, each idea tied to where it appears in a real model: vectors and matrices, the SVD and low rank, derivatives and backpropagation, probability and sampling, maximum likelihood, information theory, softmax numerics, optimization and floating point. Every deck follows the 9-beat template and has an interactive widget.',
        'index_math.json', 'Implement cosine search, truncated SVD and LoRA counts, hand-written gradients with a gradient checker, entropy/KL/perplexity, a stable and online softmax, and gradient descent, momentum and Adam in NumPy.',
        MATH_CARDS, 'Mikolov et al. 2013 (word2vec); Vaswani et al. 2017; Brown et al. 2020 (GPT-3); Kaplan et al. 2020; Hu et al. 2021 (LoRA); Aghajanyan et al. 2021; Rumelhart, Hinton & Williams 1986; Baydin et al. 2018; Bengio et al. 2003; Holtzman et al. 2020; Shannon 1948; Kullback & Leibler 1951; Hinton et al. 2015; Milakov & Gimelshein 2018; Dao et al. 2022; Kingma & Ba 2015; Dauphin et al. 2014; Goh 2017; Goldberg 1991; Kalamkar et al. 2019; Micikevicius et al. 2018.'))
    print('wrote math/index.html')


NN_CARDS = [
    ('01-perceptron-to-mlp', 'From perceptron to MLP', 'Why one neuron fails at XOR and a hidden layer fixes it.'),
    ('02-activation-functions', 'Activation functions', 'Sigmoid, ReLU, GELU, SiLU and vanishing gradients.'),
    ('03-backpropagation', 'Backpropagation', 'Record the graph, walk it backwards, accumulate.'),
    ('04-loss-functions', 'Loss functions', 'MSE vs cross-entropy, p − y, label smoothing.'),
    ('05-optimizers', 'Optimizers', 'Momentum, Adam, AdamW and warmup + cosine schedules.'),
    ('06-initialization', 'Initialization', 'Variance budgets: Xavier and He.'),
    ('07-normalization-residuals', 'Normalization and residual connections', 'LayerNorm, RMSNorm, x + f(Norm(x)).'),
    ('08-regularization', 'Regularization and generalization', 'Weight decay, dropout, random labels, double descent.'),
    ('09-embeddings', 'Embeddings', 'Learned lookup tables and their geometry.'),
    ('10-mlp-to-language-model', 'From MLP to language model', 'Bigram → neural LM → transformer.'),
]

if __name__ == '__main__':
    _write(os.path.join(REPO, 'nn-fundamentals', 'index.html'), topic_hub(
        'nn-fundamentals', 'Neural network fundamentals for LLMs', 'Neural Network Fundamentals',
        'The deep-learning machinery every LLM is built from: neurons and MLPs, activations, backpropagation, losses, optimizers and schedules, initialization, normalization and residuals, regularization, embeddings, and a first language model. Every deck follows the 9-beat template and has an interactive widget.',
        'index_nn.json', 'Build a micrograd-style autograd engine, an MLP that solves XOR, activation and depth experiments, AdamW with warmup + cosine, initialization tests, dropout and weight decay, and a tiny character-level language model in NumPy.',
        NN_CARDS, 'Rumelhart, Hinton & Williams 1986; Cybenko 1989; Hornik et al. 1989; Nair & Hinton 2010; Hendrycks & Gimpel 2016 (GELU); Ramachandran et al. 2018 (Swish); Shazeer 2020; Baydin et al. 2018; Szegedy et al. 2016; Bengio et al. 2003; Kingma & Ba 2015; Loshchilov & Hutter 2017, 2019; Sutskever et al. 2013; Touvron et al. 2023 (LLaMA); Glorot & Bengio 2010; He et al. 2015, 2016; Radford et al. 2019 (GPT-2); Ioffe & Szegedy 2015; Ba et al. 2016; Zhang & Sennrich 2019; Srivastava et al. 2014; Zhang et al. 2017; Belkin et al. 2019; Nakkiran et al. 2020; Mikolov et al. 2013.'))
    print('wrote nn-fundamentals/index.html')


DATA_CARDS = [
    ('01-where-data-comes-from', 'Where pretraining data comes from', 'Common Crawl, WARC/WET, and the ~90% a pipeline removes.'),
    ('02-how-a-crawler-works', 'How a web crawler works', 'Frontier, per-host politeness, robots checks, normalisation.'),
    ('03-crawling-at-scale', 'Crawling at scale', 'IRLbot\'s 6.3B pages, budgets, traps, simhash, freshness.'),
    ('04-robots-and-consent', 'robots.txt and consent', 'RFC 9309 rules and the rise of AI opt-outs.'),
    ('05-text-extraction', 'Text extraction', 'Boilerplate removal, link density, trafilatura, language ID.'),
    ('06-quality-filtering', 'Quality filtering', 'C4 and Gopher rules, CCNet perplexity, DCLM and FineWeb-Edu classifiers.'),
    ('07-deduplication', 'Deduplication', 'Exact hashes, MinHash + LSH, line and substring dedup.'),
    ('08-pii-and-safety', 'PII and safety filtering', 'Domain blocklists, regex masking, toxicity classifiers.'),
    ('09-mixtures-and-repetition', 'Data mixtures and repetition', 'Temperature sampling, DoReMi, the ~4-epoch rule.'),
    ('10-reference-pipelines', 'Reference pipelines', 'C4 → Gopher → RefinedWeb → FineWeb → DCLM → Dolma → Llama 3.'),
]

if __name__ == '__main__':
    _write(os.path.join(REPO, 'pretraining-data', 'index.html'), topic_hub(
        'pretraining-data', 'Web crawling and pretraining data', 'Web Crawling and Pretraining Data',
        'Where the trillions of training tokens come from and how they are made usable: how crawlers work and stay polite, robots.txt and consent, text extraction, quality filtering, deduplication, PII and safety filtering, data mixtures, and the published pipelines from C4 to Llama 3. Every deck follows the 9-beat template and numbers are checked against the source papers and standards.',
        'index_data.json', 'Build a polite crawler on a simulated web, an RFC 9309 robots.txt parser, an HTML text extractor, C4 and Gopher quality filters, MinHash with LSH banding, and a data-mixture planner in Python.',
        DATA_CARDS, 'RFC 9309 (2022); Common Crawl; Brin & Page 1998; Najork & Heydon 2001 (Mercator); Lee et al. 2008 (IRLbot); Manku et al. 2007; Broder 1997; Raffel et al. 2020 (C4); Rae et al. 2021 (Gopher); Wenzek et al. 2020 (CCNet); Penedo et al. 2023 (RefinedWeb), 2024 (FineWeb); Li et al. 2024 (DCLM); Lee et al. 2022; Soldaini et al. 2024 (Dolma); Longpre et al. 2024; Barbaresi 2021 (trafilatura); Joulin et al. 2017 (fastText); Muennighoff et al. 2023; Xie et al. 2023 (DoReMi); Llama Team 2024 (Llama 3).'))
    print('wrote pretraining-data/index.html')


TORCH_CARDS = [
    ('01-tensors', 'Tensors, strides and views', 'Storage, shape, strides; view vs reshape; broadcasting and einsum.'),
    ('02-autograd', 'Autograd', 'grad_fn graphs, accumulation, no_grad, detach, custom Functions.'),
    ('03-nn-module', 'nn.Module and a transformer block', 'Parameters, buffers, state_dict, SDPA, a pre-norm block.'),
    ('04-training-loop', 'The training loop', 'zero_grad → backward → clip → step; decay groups; resumable checkpoints.'),
    ('05-data', 'Data pipelines for LLMs', 'Dataset, DataLoader, padding, −100 labels, packing.'),
    ('06-mixed-precision', 'Mixed precision in PyTorch', 'autocast op dtypes, FP32 accumulation, GradScaler.'),
    ('07-performance', 'Performance: compile, SDPA, memory', 'Dynamo + AOTAutograd + Inductor, graph breaks, fused attention.'),
    ('08-distributed', 'Distributed training in PyTorch', 'torchrun, process groups, DDP buckets, FSDP2 fully_shard.'),
    ('09-putting-it-together', 'Putting it together: a tiny GPT', 'A nanoGPT-style model trained and sampled on CPU.'),
]

if __name__ == '__main__':
    _write(os.path.join(REPO, 'pytorch', 'index.html'), topic_hub(
        'pytorch', 'PyTorch for LLMs', 'PyTorch for LLMs',
        'The PyTorch you need to build and train LLMs: tensors and views, autograd, nn.Module, the training loop, data pipelines, mixed precision, torch.compile and fused attention, and distributed training, ending with a tiny GPT. Checked against PyTorch 2.14.1; every notebook was executed with it before publishing.',
        'index_torch.json', 'Split attention heads with strides, write a custom autograd Function, build a transformer block with SDPA, a resumable training loop, padding and packing collators, autocast and GradScaler, torch.compile graph-break hunting, DDP with torchrun, and a tiny GPT, all runnable on a CPU runtime.',
        TORCH_CARDS, 'Paszke et al. 2019 (PyTorch); Ansel et al. 2024 (PyTorch 2); PyTorch 2.14 documentation (tensor views, autograd mechanics, torch.utils.data, torch.amp, torch.compiler, SDPA tutorial, FSDP2 tutorial, torchrun, CUDA semantics); Li et al. 2020 (DDP); Zhao et al. 2023 (FSDP); Micikevicius et al. 2018; Kalamkar et al. 2019; Loshchilov & Hutter 2019; Dao 2023; Radford et al. 2019; Karpathy (nanoGPT).'))
    print('wrote pytorch/index.html')


VLLM_CARDS = [
    ('01-what-is-vllm', "What vLLM is and a request's life", 'Offline LLM class vs vllm serve; every stage a request passes.'),
    ('02-engine-architecture', 'Engine architecture', 'API servers, EngineCore per DP rank, workers per GPU: A + DP + N processes.'),
    ('03-kv-cache-manager', 'KV cache manager and PagedAttention', '16-token blocks, block tables, ref counts, LRU free queue.'),
    ('04-scheduler', 'The scheduler', 'One token budget, running first, chunked prefill, preemption by recompute.'),
    ('05-prefix-caching', 'Automatic prefix caching', 'Chained block hashes, longest-prefix reuse, on by default.'),
    ('06-speculative-decoding', 'Speculative decoding in vLLM', 'n-gram, draft, EAGLE, MTP proposers; rejection sampling.'),
    ('07-parallelism-and-quantization', 'Parallelism and quantization', '-tp, -pp, -dp, expert parallelism, FP8 weights and KV.'),
    ('08-running-and-tuning', 'Running and tuning vLLM', 'Flags, OpenAI endpoints, /metrics, vllm bench, fixing preemptions.'),
]

if __name__ == '__main__':
    _write(os.path.join(REPO, 'vllm', 'index.html'), topic_hub(
        'vllm', 'vLLM internals and operation', 'vLLM',
        'How the vLLM serving engine works inside and how to run it: the process architecture, the paged KV cache manager, the unified token-budget scheduler, automatic prefix caching, speculative decoding, parallelism and quantization, and tuning with metrics. Checked against the vLLM v0.31.0 source and documentation; the concepts are introduced in the LLM Inference topic.',
        'index_vllm.json', 'Re-implement vLLM\'s block pool with ref counts and LRU, chained-hash prefix caching, the token-budget scheduler with chunked prefill and preemption, a GPU memory and concurrency planner, and n-gram speculative decoding, all as CPU simulations.',
        VLLM_CARDS, 'Kwon et al. 2023 (PagedAttention / vLLM); vLLM V1 blog 2025; vLLM v0.31.0 source (vllm/v1/core, vllm/config, vllm/engine) and documentation (architecture overview, automatic prefix caching design, optimization and tuning, OpenAI-compatible server, parallelism and scaling, speculative decoding, quantization); Yu et al. 2022 (Orca); Agrawal et al. 2024 (Sarathi-Serve); Leviathan et al. 2023; Zheng et al. 2024 (SGLang).'))
    print('wrote vllm/index.html')


CLUSTER_CARDS = [
    ('01-scheduling-basics', 'Scheduling a GPU cluster', 'Priority, quotas, gang placement, backfill, preemption.'),
    ('02-slurm', 'Slurm for GPU clusters', 'Daemons, GRES, multifactor priority, backfill, topology, preemption.'),
    ('03-kubernetes-gpus', 'Kubernetes for GPU workloads', 'Device plugins, DRA, Kueue, JobSet, topology-aware scheduling.'),
    ('04-operating-clusters', 'Operating a training cluster', 'Health checks, drain, requeue, checkpoints; Slurm or Kubernetes.'),
]


def write_cluster_hub():
    _write(os.path.join(REPO, 'cluster-scheduling', 'index.html'), topic_hub(
        'cluster-scheduling', 'Cluster scheduling', 'Cluster scheduling',
        'How GPU clusters are shared between teams and kept busy: what a scheduler decides, Slurm in depth (pinned to 26.05), Kubernetes with device plugins, Dynamic Resource Allocation, Kueue and JobSet, and the automated loop that recovers jobs from failures. Each deck follows the systems template: problem, core idea, high-level design, low-level design, trade-offs, failure modes and challenges in production.',
        'index_cluster.json', 'Simulate FIFO vs EASY backfill on a GPU cluster, then Slurm-style decayed usage, fair share, multifactor priority and preemption. Plain Python, no cluster needed.',
        CLUSTER_CARDS, 'Slurm 26.05 documentation (overview, GRES, multifactor priority, fair share, scheduling, topology, preemption, slurm.conf); Kubernetes 1.35 documentation (GPUs, DRA); Kueue and JobSet documentation; NVIDIA (SchedMD acquisition); Llama 3 report.'))
    print('wrote cluster-scheduling/index.html')

# Visual LLM topics with a standard hub: (title, lede, notebook index, notebook blurb, cards, sources)
LLM_HUBS = {
    'reasoning': ('Reasoning and test-time compute', 'How models get better answers by spending more compute at inference: chain of thought, sampling and majority voting, verifiers and step-level search, and reasoning models trained with reinforcement learning, with their thinking budgets and limits. Every deck follows the 9-beat template and numbers are checked against the papers.',
                  'index_reasoning.json', 'Simulate majority voting, coverage and best-of-N with a noisy verifier, and see why selection, not sampling, is the bottleneck.', [
        ('01-chain-of-thought', 'Chain of thought', 'Few-shot and zero-shot CoT; why steps help.'),
        ('02-sampling-and-voting', 'Sampling, voting and coverage', 'Self-consistency, coverage, automatic verifiers.'),
        ('03-verifiers-and-search', 'Verifiers and search', 'ORM vs PRM, step search, compute-optimal scaling.'),
        ('04-reasoning-models', 'Reasoning models and thinking budgets', 'RL on verifiable rewards, budget forcing, limits.')],
        'Wei et al. 2022; Kojima et al. 2022; Wang et al. 2023; Cobbe et al. 2021; Lightman et al. 2024; Snell et al. 2025; Brown et al. 2024; DeepSeek-AI 2025; Muennighoff et al. 2025; Chen et al. 2024; Chen et al. 2025 (Anthropic); Claude API thinking documentation.'),
    'interpretability': ('Interpretability', 'What is going on inside a language model: features as directions and superposition, sparse autoencoders from a one-layer transformer to Claude 3 Sonnet and GPT-4, and the causal tools (patching, circuits, attribution graphs, probes and steering vectors) that turn descriptions into mechanisms. 9-beat template; numbers checked against the papers.',
                         'index_interp.json', 'Measure interference between features in superposition, then build and train a sparse autoencoder in NumPy that recovers 8 hidden features from 4 dimensions where PCA cannot.', [
        ('01-features-and-superposition', 'Features and superposition', 'Directions, polysemantic neurons, packing sparse features.'),
        ('02-sparse-autoencoders', 'Sparse autoencoders', 'Dictionary learning from one layer to Claude 3 Sonnet.'),
        ('03-circuits-and-steering', 'Circuits, probes and steering', 'Patching, IOI, attribution graphs, ActAdd.')],
        'Elhage et al. 2022; Olsson et al. 2022; Bricken et al. 2023; Cunningham et al. 2024; Templeton et al. 2024; Gao et al. 2024; Lieberum et al. 2024; Wang et al. 2023; Meng et al. 2022; Lindsey et al. 2025; Turner et al. 2023; Zou et al. 2023.'),
    'multimodal': ('Multimodal LLMs', 'How language models see: images as patch tokens and contrastive vision encoders (ViT, CLIP, SigLIP), connectors that join a vision encoder to an LLM (LLaVA, Flamingo, BLIP-2, early fusion), and what images cost and how vision-language models fail in practice. 9-beat template; numbers checked against the papers and API documentation.',
                   'index_multimodal.json', 'Patchify an image ViT-style, implement CLIP\'s contrastive loss and zero-shot classification, and build an image-token cost calculator that reproduces the Claude API\'s published counts.', [
        ('01-vision-encoders', 'Vision encoders: ViT and CLIP', 'Patches as tokens; contrastive image-text training.'),
        ('02-vision-language-models', 'Connecting vision to an LLM', 'Projection, resampler, Q-Former, early fusion.'),
        ('03-images-in-practice', 'Images as tokens in practice', 'Visual-token cost, limits, MMMU, hallucination.')],
        'Dosovitskiy et al. 2021; Radford et al. 2021; Zhai et al. 2023; Liu et al. 2023, 2024; Alayrac et al. 2022; Li et al. 2023 (BLIP-2); Chameleon Team 2024; Radford et al. 2023 (Whisper); Yue et al. 2024; Li et al. 2023 (POPE); Claude API vision documentation.'),
}


def write_llm_hubs():
    for folder, (title, lede, nb, blurb, cards, sources) in LLM_HUBS.items():
        _write(os.path.join(REPO, folder, 'index.html'), topic_hub(folder, title, title, lede, nb, blurb, cards, sources))
        print('wrote', folder + '/index.html')

CASE_CARDS = [
    ('01-chat-assistant', 'Serving a chat assistant', '1M daily users on a 70B model: KV-cache sizing, prefix caching, routing.'),
    ('02-enterprise-rag', 'Enterprise RAG assistant', '10M documents: permission-aware hybrid retrieval, reranking, citations.'),
    ('03-coding-agent', 'Autonomous coding agent', '10K tasks a day: durable loop, microVM sandboxes, verification, review.'),
    ('04-pretraining-run', 'Planning a pretraining run', '70B on 15T tokens: compute, 4D layout, checkpoints vs failures.'),
]


def write_case_hub():
    lede = ('End-to-end designs that combine the topics of both guides. Each case has an overview deck that walks the design the way you would present it '
            '(requirements, estimates, architecture, a walkthrough, a deep dive, scaling, failures, trade-offs) and a long-form design document with the full reasoning. '
            'Every number is either a stated assumption or a verified fact from the topic decks, and each case has a calculator for its estimates.')
    cards = [(s, t, p + ' <a href="' + s + '/design.html">Design doc →</a>') for s, t, p in CASE_CARDS]
    _write(os.path.join(REPO, 'system-design', 'index.html'), topic_hub(
        'system-design', 'System design case studies', 'System design', lede, None, '', cards,
        'See each case\'s design document and Key papers slide.', back='../index.html', back_label='Visual AI'))
    print('wrote system-design/index.html')

AGENT_HUBS = {
    'agent-foundations': ('Agent foundations', 'What an agent is, how models call tools, the ReAct loop, and planning: the building blocks every agent shares.', [
        ('01-what-is-an-agent', 'What an agent is', 'Workflows vs agents; the decide-act-observe loop.'),
        ('02-tool-calling', 'Tool calling', 'Schemas, structured calls, results, parallel calls, tool choice.'),
        ('03-react-loop', 'ReAct: reasoning and acting', 'Thought → action → observation; Reflexion.'),
        ('04-planning', 'Planning and task decomposition', 'Plan-and-execute, task DAGs, Tree of Thoughts, replanning.')]),
    'agent-context': ('Agent context', 'What an agent knows: memory and context management, agentic retrieval, and the Model Context Protocol for connecting tools and data.', [
        ('01-memory', 'Memory and context management', 'Context rot, compaction, notes, scored long-term memory.'),
        ('02-agentic-rag', 'Agentic retrieval (RAG)', 'Retrieve, grade, refine, cite; Self-RAG and CRAG.'),
        ('03-mcp', 'Model Context Protocol (MCP)', 'Hosts, clients, servers; the stateless 2026-07-28 revision.'),
        ('04-a2a', 'Agent2Agent protocol (A2A)', 'Agent Cards, tasks, artifacts; agents talking to agents (v1.0).')]),
    'agent-systems': ('Agent systems', 'Larger agent architectures: lead agents with parallel subagents, and agents that operate computers and browsers.', [
        ('01-multi-agent', 'Multi-agent systems', 'Orchestrator-workers, delegation, the 15× token cost.'),
        ('02-computer-use', 'Computer and browser use', 'Screenshot-action loops, grounding, sandboxing.'),
        ('03-durable-workflows', 'Durable workflows for agents', 'Temporal event history and replay; vs LangGraph, Airflow, Argo.')]),
    'agent-operations': ('Agent operations', 'Running agents for real: evaluating them, keeping them safe and reliable, and controlling cost and latency.', [
        ('01-evaluating-agents', 'Evaluating agents', 'End-state grading, pass^k, harnesses, benchmarks.'),
        ('02-safety-and-reliability', 'Safety and reliability', 'Prompt injection, least privilege, approvals, idempotency.'),
        ('03-cost-and-latency', 'Cost and latency', 'Quadratic context growth, prompt caching, routing, budgets.'),
        ('04-experimentation', 'Experimentation for LLM products', 'Shadow traffic, A/B tests, guardrails, peeking, SRM, CUPED.')]),
    'agent-frameworks': ('Agent frameworks', 'The agent loop and graph runtime in a widely used framework: LangChain\'s building blocks and create_agent, LangGraph\'s state graphs, and the persistence layer behind memory, approvals and recovery. Pinned to LangChain 1.4.6 and LangGraph 1.2.15.', [
        ('01-langchain-basics', 'LangChain basics', 'Chat models, messages, tools, create_agent, middleware.'),
        ('02-langgraph-core', 'LangGraph core', 'State, reducers, nodes, edges, super-steps.'),
        ('03-langgraph-production', 'LangGraph in production', 'Checkpoints, threads, interrupts, retries, resuming.')]),
    'agent-infra': ('Agent infrastructure', 'The platform under agents: one gateway for all model traffic, routing each request to the right model or agent, and making agents act with the user\'s permissions and no more.', [
        ('01-llm-gateway', 'LLM gateway', 'Virtual keys, limits, retries, fallbacks, metering.'),
        ('02-model-router', 'Model and agent routing', 'Intent routing, learned routers, cascades.'),
        ('03-access-control', 'Identity and access control', 'RBAC, ABAC, delegation, MCP authorization, ACL-aware retrieval.'),
        ('04-sandboxing', 'Sandboxing agents', 'Filesystem and network boundaries, gVisor, Firecracker, secrets outside.')]),
    'agent-retrieval': ('Retrieval stack', 'What sits under agentic retrieval: building the index, searching vectors fast, and reranking candidates before they reach the model.', [
        ('01-indexing', 'Indexing pipelines', 'Parsing, chunking, contextual chunks, incremental updates.'),
        ('02-vector-databases', 'Vector databases', 'IVF, product quantization, HNSW, DiskANN, filters.'),
        ('03-rerankers', 'Rerankers', 'Cross-encoders, ColBERT, LLM reranking, fusion.')]),
    'agent-models': ('Models for agents', 'The models themselves: how they are trained to use tools and finish long tasks, and how inference servers handle agent traffic.', [
        ('01-training-for-agents', 'Training LLMs for agents', 'Synthetic trajectories, SFT, RL with verifiable rewards.'),
        ('02-serving-for-agents', 'Serving LLMs for agent workloads', 'Prefix reuse, constrained decoding, program-aware scheduling.')]),
}

if __name__ == '__main__':
    write_cluster_hub()
    write_case_hub()
    write_llm_hubs()
    for folder, (title, lede, cards) in AGENT_HUBS.items():
        _write(os.path.join(REPO, folder, 'index.html'), topic_hub(
            folder, title, title, lede + ' Each deck follows the agent template: problem, core idea, high-level design, low-level design, trade-offs, failure modes and challenges in production, with steppable diagrams and sources checked against the primary papers, specifications and documentation.',
            *(('index_agent_frameworks.json', 'Build a tool and its schema, the agent loop by hand, a ReAct graph, per-thread memory, an approval step with interrupt() and crash recovery. A scripted fake model means no API key is needed.') if folder == 'agent-frameworks' else (None, '')),
            cards, 'See each deck\'s Key papers slide and this topic\'s reading list.', back='../agents/index.html', back_label='Visual Agents'))
        print('wrote', folder + '/index.html')
