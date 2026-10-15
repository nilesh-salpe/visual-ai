"""Site-wide extras: glossary page, per-topic reading lists, and a "big picture" map on each topic hub.

Run after the deck generators, tools/build_indexes.py and tools/build_home.py:
    python3 tools/build_site_extras.py
Reading lists are collected from the Key papers slide of every deck, so they never drift from the decks.
Hub pages get a block between <!--x:map--> markers (replaced on every run).
"""
import html, json, os, re

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TOPICS = {  # folder: (title, [(stage, [slug, ...]), ...])
    'math': ('Math for LLMs', [('Linear algebra', ['01-vectors-dot-products', '02-matrices-linear-layers', '03-eigen-svd-low-rank']), ('Calculus', ['04-derivatives-chain-rule']),
                               ('Probability and information', ['05-probability-sampling', '06-maximum-likelihood', '07-information-theory']),
                               ('Numerics and optimization', ['08-softmax-logsumexp', '09-optimization-basics', '10-floating-point'])]),
    'pytorch': ('PyTorch for LLMs', [('Core', ['01-tensors', '02-autograd', '03-nn-module']), ('Training', ['04-training-loop', '05-data', '06-mixed-precision']),
                                     ('Scaling up', ['07-performance', '08-distributed']), ('Together', ['09-putting-it-together'])]),
    'vllm': ('vLLM', [('The engine', ['01-what-is-vllm', '02-engine-architecture']), ('Memory and scheduling', ['03-kv-cache-manager', '04-scheduler', '05-prefix-caching']),
                      ('Speed and scale', ['06-speculative-decoding', '07-parallelism-and-quantization']), ('Operating it', ['08-running-and-tuning'])]),
    'pretraining-data': ('Web Crawling and Pretraining Data', [('Sources', ['01-where-data-comes-from']), ('Crawling', ['02-how-a-crawler-works', '03-crawling-at-scale', '04-robots-and-consent']),
                                                               ('Cleaning', ['05-text-extraction', '06-quality-filtering', '07-deduplication', '08-pii-and-safety']), ('Assembling', ['09-mixtures-and-repetition', '10-reference-pipelines'])]),
    'nn-fundamentals': ('Neural Network Fundamentals', [('Networks', ['01-perceptron-to-mlp', '02-activation-functions']), ('Learning', ['03-backpropagation', '04-loss-functions', '05-optimizers']),
                                                        ('Making depth work', ['06-initialization', '07-normalization-residuals', '08-regularization']), ('Toward LLMs', ['09-embeddings', '10-mlp-to-language-model'])]),
    'gpu': ('GPU for GenAI', [('The chip', ['01-what-is-a-gpu', '02-why-gpus-for-ai', '03-memory-hierarchy']), ('The machine', ['04-inside-gpu-server', '05-cluster-topology']),
                              ('Operating a fleet', ['06-gpu-failures', '07-heterogeneous-gpus', '08-sharing-gpus'])]),
    'transformer': ('Attention Is All You Need', [('Why', ['01-sequential-bottleneck', '02-transformer-architecture']),
                                                  ('Attention', ['03-self-attention', '04-queries-keys-values', '05-scaled-dot-product-attention', '06-multi-head-attention']),
                                                  ('Order and decoding', ['07-positional-encoding', '08-encoder-decoder-attention', '09-masked-self-attention']),
                                                  ('The rest of the block', ['10-residual-layernorm', '11-position-wise-ffn', '12-parallel-training-vs-generation']),
                                                  ('Evidence', ['13-why-it-works', '14-experimental-results'])]),
    'tokenization': ('Tokenization for LLMs', [('Why', ['01-why-tokenize']), ('Algorithms', ['02-bpe-from-scratch', '03-byte-level-bpe', '04-wordpiece-unigram', '05-sentencepiece']),
                                               ('Design choices', ['06-many-tokenizations', '07-vocabulary-size']), ('In practice', ['08-tokenizers-in-llms', '09-multilingual-cost', '10-tokenization-quirks'])]),
    'inference': ('LLM Inference and Serving', [('The workload', ['01-inference-workload']), ('Memory', ['02-kv-cache', '05-paged-attention']), ('Scheduling', ['03-batching', '04-chunked-prefill']),
                                                ('Speed', ['06-speculative-decoding', '07-quantization', '08-parallelism']), ('The system', ['09-disaggregated-serving', '10-putting-it-together'])]),
    'architecture': ('The Modern LLM Architecture', [('Overview', ['01-what-changed']), ('Inside the block', ['02-normalization', '03-rope', '04-swiglu', '05-attention-variants']),
                                                     ('The stack', ['06-decoder-only']), ('Long context', ['07-rope-scaling', '08-sliding-window']),
                                                     ('Efficiency', ['09-flash-attention', '10-mixture-of-experts']), ('Together', ['11-putting-it-together'])]),
    'post-training': ('Post-training LLMs', [('Pipeline', ['01-pipeline']), ('Imitation', ['02-supervised-fine-tuning', '03-lora-qlora']),
                                             ('Preferences', ['04-reward-models', '05-rlhf-ppo', '06-reward-hacking', '07-dpo-and-friends']), ('Beyond human labels', ['08-rlvr-grpo', '09-rlaif-constitutional-ai'])]),
    'evals': ('Evaluating LLMs', [('What a score is', ['01-what-an-eval-measures']), ('Benchmarks', ['02-benchmarks', '03-pass-at-k']), ('Statistics', ['04-error-bars', '05-contamination']),
                                  ('Judgement', ['06-llm-as-judge', '07-arenas'])]),
    'distributed': ('Distributed Training', [('Why', ['01-why-distribute']), ('Data axis', ['02-data-parallelism', '03-zero-fsdp']),
                                             ('Model axes', ['04-tensor-sequence-parallelism', '05-pipeline-parallelism', '06-context-parallelism', '07-expert-parallelism']),
                                             ('Memory and precision', ['08-activation-memory', '09-mixed-precision-fp8']), ('At scale', ['10-putting-it-together', '11-reliability-stability'])]),
}
PAGE = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="{up}shared/deck.css">
<link rel="stylesheet" href="{up}shared/learn.css">
<style>body {{ overflow-y: auto; }} {css}</style>
</head>
<body>
<div class="hub">
  <a class="brand" href="{back}">← {back_label}</a>
{body}
</div>
{script}
</body>
</html>
'''


def deck_title(folder, slug):
    s = open(os.path.join(REPO, folder, slug, 'index.html')).read()
    m = re.search(r'data-deck="([^"]*)"', s)
    return html.unescape(m.group(1)) if m else slug


def papers_of(folder, slug):
    s = open(os.path.join(REPO, folder, slug, 'index.html')).read()
    sec = re.search(r'<section class="slide" id="s-papers".*?</section>', s, re.S)
    out = []
    if sec:
        for m in re.finditer(r'<div class="paper-item"><a href="([^"]+)"[^>]*>(.*?)</a>\s*<div class="meta">(.*?)</div>\s*<p>(.*?)</p>(?:<div class="num">(.*?)</div>)?', sec.group(0), re.S):
            out.append(dict(url=m.group(1), title=m.group(2), meta=m.group(3), summary=m.group(4), num=m.group(5) or ''))
    return out


def reading_list(folder):
    title, stages = TOPICS[folder]
    seen, order = {}, []
    for _, slugs in stages:
        for slug in slugs:
            for p in papers_of(folder, slug):
                if p['url'] not in seen:
                    seen[p['url']] = dict(p, decks=[]); order.append(p['url'])
                seen[p['url']]['decks'].append((slug, deck_title(folder, slug)))
    items = ''.join(f'''
    <div class="paper-item"><a href="{p["url"]}" target="_blank" rel="noopener">{p["title"]}</a>
      <div class="meta">{p["meta"]} · cited in {", ".join(f'<a href="{s}/index.html" style="font-weight:500;color:var(--a)">{t}</a>' for s, t in p["decks"])}</div>
      <p>{p["summary"]}</p>{f'<div class="num">{p["num"]}</div>' if p["num"] else ''}</div>''' for p in (seen[u] for u in order))
    body = f'''  <div class="label" style="margin-top:28px">Reading list · {len(order)} papers and docs</div>
  <h1>{title}: key papers</h1>
  <p class="lede">Every paper cited on the decks' Key papers slides, in the order the guide introduces them. Each entry links to the paper and to the decks that use it.</p>
  <div class="papers" style="margin-top:18px">{items}
  </div>'''
    open(os.path.join(REPO, folder, 'reading-list.html'), 'w').write(PAGE.format(title=f'{title} Reading List', up='../', css='', back='index.html', back_label=title, body=body, script=''))
    return len(order)


MAP_CSS = '''<style>
.bigmap { display: flex; gap: 10px; align-items: stretch; overflow-x: auto; padding: 4px 2px 10px; }
.bigmap .stage { flex: 1 1 0; min-width: 150px; display: flex; flex-direction: column; gap: 8px; }
.bigmap .stage h4 { margin: 0 0 2px; font: 700 11.5px 'JetBrains Mono', monospace; letter-spacing: .05em; text-transform: uppercase; color: var(--a); }
.bigmap .stage a { display: block; padding: 9px 11px; border-radius: 10px; background: var(--panel); border: 1px solid var(--line); color: var(--ink); text-decoration: none; font-size: 14px; line-height: 1.3; }
.bigmap .stage a:hover { border-color: var(--a); background: var(--a-soft); }
.bigmap .stage a span { display: block; font: 600 11px 'JetBrains Mono', monospace; color: var(--faint); }
.bigmap .arrow { align-self: center; color: var(--faint); font-size: 20px; }
.hub-links { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 14px; }
@media (max-width: 700px) { .bigmap { flex-direction: column; } .bigmap .arrow { transform: rotate(90deg); } }
</style>'''


def hub_block(folder):
    title, stages = TOPICS[folder]
    cols = []
    for stage, slugs in stages:
        links = ''.join(f'<a href="{s}/index.html"><span>{s[:2]}</span>{html.escape(deck_title(folder, s))}</a>' for s in slugs)
        cols.append(f'<div class="stage"><h4>{stage}</h4>{links}</div>')
    m = '<div class="arrow">→</div>'.join(cols)
    return f'''<!--x:map-->{MAP_CSS}
  <div class="visual" style="margin-top:22px">
    <h3 style="margin:0 0 10px">The big picture</h3>
    <div class="bigmap">{m}</div>
    <div class="hub-links"><a class="btn" href="reading-list.html">📚 Reading list</a><a class="btn" href="../glossary/index.html">🔤 Glossary</a></div>
  </div>
<!--/x:map-->
'''


def patch_hub(folder):
    f = os.path.join(REPO, folder, 'index.html')
    s = open(f).read()
    s = re.sub(r'<!--x:map-->.*?<!--/x:map-->\n?', '', s, flags=re.S)
    i = s.index('<div class="hub-grid">')
    i = s.rindex('\n', 0, i) + 1
    s = s[:i] + hub_block(folder) + s[i:]
    open(f, 'w').write(s)


def glossary():
    g = json.load(open(os.path.join(REPO, 'shared', 'glossary.json')))
    terms = sorted(g['terms'].items(), key=lambda kv: kv[0].lower())
    rows = ''.join(f'<tr data-k="{html.escape(k.lower() + " " + v["exp"].lower())}"><td><b>{html.escape(k)}</b></td><td>{html.escape(v["exp"])}</td></tr>' for k, v in terms)
    body = f'''  <div class="label" style="margin-top:28px">Glossary · {len(terms)} terms</div>
  <h1>Acronyms and abbreviations</h1>
  <p class="lede">Every acronym used across the guides. Each deck also spells out each acronym the first time it appears, so decks can be read on their own.</p>
  <input id="q" type="search" placeholder="Filter, e.g. KV or attention" style="margin-top:14px;width:100%;max-width:420px;padding:10px 12px;border-radius:10px;border:1px solid var(--line);background:var(--panel);color:var(--ink);font-size:15px">
  <div class="visual scroll-x" style="margin-top:14px"><table class="tbl" id="gt"><tr><th>Term</th><th>Meaning</th></tr>{rows}</table></div>'''
    script = '''<script>
(() => { const q = document.getElementById('q'), rows = [...document.querySelectorAll('#gt tr[data-k]')];
  q.addEventListener('input', () => { const t = q.value.trim().toLowerCase(); rows.forEach(r => { r.style.display = !t || r.dataset.k.includes(t) ? '' : 'none'; }); }); })();
</script>'''
    os.makedirs(os.path.join(REPO, 'glossary'), exist_ok=True)
    open(os.path.join(REPO, 'glossary', 'index.html'), 'w').write(PAGE.format(title='Glossary', up='../', css='', back='../index.html', back_label='Visual AI', body=body, script=script))
    return len(terms)


def expand_page(path):
    import sys
    sys.path.insert(0, os.path.join(REPO, 'tools', 'decks'))
    from acronyms import process
    f = os.path.join(REPO, path)
    text = open(f).read()                 # read first: opening with 'w' would truncate the file
    assert text.strip(), f'{path} is empty'
    out = process(text)[0]
    if out != text:
        open(f, 'w').write(out)


def link_glossary_from_home():
    f = os.path.join(REPO, 'index.html')
    s = open(f).read()
    if 'glossary/index.html' not in s:
        s = s.replace('  <div class="hub-grid">', '  <p style="margin:6px 0 0"><a class="btn" href="glossary/index.html">🔤 Glossary of acronyms</a></p>\n  <div class="hub-grid">', 1)
        open(f, 'w').write(s)


if __name__ == '__main__':
    for folder in TOPICS:
        n = reading_list(folder)
        patch_hub(folder)
        expand_page(os.path.join(folder, 'index.html'))
        print(f'{folder}: reading list with {n} entries, hub map updated')
    print(f'glossary: {glossary()} terms')
    link_glossary_from_home()
    for page in ['index.html', 'llm/index.html', 'agents/index.html']:
        expand_page(page)
    expand_page('build-it/index.html')
