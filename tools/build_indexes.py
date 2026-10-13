"""Regenerate build-it/index.html, build-it/README.md and architecture/index.html from the notebook indexes.

Run after tools/notebooks/build_*.py:  python3 tools/build_indexes.py
"""
import json, os

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GH = 'https://github.com/nilesh-salpe/visual-ai/blob/main/'
BADGE = 'https://colab.research.google.com/assets/colab-badge.svg'
PHASES = [  # (heading, notebook folder, index json)
    ('Phase 1 · LLM inference and serving', 'inference', 'index_inference.json'),
    ('Phase 2 · The modern LLM architecture', 'architecture', 'index_architecture.json'),
    ('Phase 3 · Post-training', 'post-training', 'index_post_training.json'),
    ('Phase 4 · Evaluating LLMs', 'evals', 'index_evals.json'),
]


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
  <a class="brand" href="../index.html">← Visual AI</a>
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
    open(os.path.join(REPO, 'build-it', 'index.html'), 'w').write(build_it_html())
    open(os.path.join(REPO, 'build-it', 'README.md'), 'w').write(build_it_md())
    open(os.path.join(REPO, 'architecture', 'index.html'), 'w').write(arch_hub())
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
  <a class="brand" href="../index.html">← Visual AI</a>
  <div class="label" style="margin-top:28px">Visual guide · {len(POST_CARDS)} decks + {n_nb} Colab notebooks</div>
  <h1>Post-training LLMs</h1>
  <p class="lede">How a pretrained model becomes an assistant: supervised fine-tuning, LoRA and QLoRA, reward models, RLHF with PPO, reward hacking, DPO and its relatives, RL with verifiable rewards (GRPO), and Constitutional AI. Every deck follows the 9-beat template, numbers are checked against the source papers, and most concepts have a hands-on Colab notebook.</p>
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
    open(os.path.join(REPO, 'post-training', 'index.html'), 'w').write(post_hub())
    print('wrote post-training/index.html')


EVAL_CARDS = [
    ('01-what-an-eval-measures', 'What an eval measures', 'A score is a protocol: prompts, decoding, scoring, uncertainty. HELM\'s 7 metrics.'),
    ('02-benchmarks', 'Benchmarks and their failure modes', 'MMLU, GPQA, GSM8K, HumanEval, SWE-bench; floors, ceilings, saturation.'),
    ('03-pass-at-k', 'pass@k and sampling metrics', 'The unbiased estimator and choosing k.'),
    ('04-error-bars', 'Error bars and comparing models', 'Standard errors, clustered errors, paired tests, power analysis.'),
    ('05-contamination', 'Contamination', '13-gram overlap, clean vs dirty scores, fresh test sets.'),
    ('06-llm-as-judge', 'LLM-as-judge', 'Agreement with humans; position, verbosity and self-enhancement bias.'),
    ('07-arenas', 'Arenas and ratings', 'Bradley-Terry vs online Elo, confidence intervals.'),
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
  <a class="brand" href="../index.html">← Visual AI</a>
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
    open(os.path.join(REPO, 'evals', 'index.html'), 'w').write(evals_hub())
    print('wrote evals/index.html')
