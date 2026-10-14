"""Generate the post-training decks (9-beat template) into visual-ai/post-training/."""
import sys, os, json
from tool import section, REPO
from extras import apply as apply_extras
from acronyms import process as expand_acronyms
from extras_post import EXTRAS

OUT = os.path.join(REPO, 'post-training')
NB_INDEX = os.path.join(REPO, 'tools', 'notebooks', 'index_post_training.json')
SLUGS = ['01-pipeline', '02-supervised-fine-tuning', '03-lora-qlora', '04-reward-models', '05-rlhf-ppo',
         '06-reward-hacking', '07-dpo-and-friends', '08-rlvr-grpo', '09-rlaif-constitutional-ai']
NAMES = ['The post-training pipeline', 'Supervised fine-tuning', 'LoRA and QLoRA', 'Reward models', 'RLHF with PPO',
         'Reward hacking and overoptimization', 'DPO, KTO and rejection sampling', 'RLVR and GRPO', 'RLAIF and Constitutional AI']
REPO_BLOB = 'https://github.com/nilesh-salpe/visual-ai/blob/main/'


def build_box(nb_slugs):
    if not nb_slugs:
        return ''
    idx = {n['slug']: n for n in json.load(open(NB_INDEX))}
    items = ''.join(f'<li><a href="{idx[s]["colab"]}" target="_blank" rel="noopener">{idx[s]["title"]}</a> <span style="color:var(--faint)">· {idx[s]["minutes"]} min · <a href="{REPO_BLOB}{idx[s]["path"]}" target="_blank" rel="noopener">view on GitHub</a></span></li>' for s in nb_slugs)
    return f'''
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px">{items}</ul></div>'''


def page(i, d):
    n = i + 1
    prev = f'<a href="../{SLUGS[i - 1]}/index.html">← {i:02d}</a>' if i else ''
    nxt = f'<a href="../{SLUGS[i + 1]}/index.html">{n + 1:02d} · {NAMES[i + 1]} →</a>' if i < len(SLUGS) - 1 else 'You\'ve finished the series. <a href="../../build-it/index.html">See all Build-it notebooks →</a>'
    links = ' · '.join(x for x in [('Next: ' + nxt) if i < len(SLUGS) - 1 else nxt, ('Previous: ' + prev) if prev else '', '<a href="../index.html">All decks</a>'] if x)
    recap = ''.join(f'<div><span><b>{k}:</b> {v}</span></div>' for k, v in d['recap'])
    take = section('s-take', 9, 'Key takeaway', f'''    <div class="take-line">{d['line']}</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>{d['explain']}</p></div>
    <div class="recap">{recap}</div>{build_box(d.get('build', []))}
    <p class="start-hint">{links}</p>{('<p class="cite">Sources: ' + d['sources'] + '</p>') if d.get('sources') else ''}''')
    title = f'''<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Post-training · {n:02d}</div>
    <h1>{d['h1']}</h1>
    <p class="sub">{d['sub']}</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>{d['prob']}</div>
      <div class="c"><b>Core idea</b>{d['core']}</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>'''
    body = '\n\n'.join(apply_extras([title] + d['slides'] + [take], EXTRAS.get(SLUGS[i], {})))
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{d['title']}</title>
<link rel="stylesheet" href="../../shared/deck.css">
<link rel="stylesheet" href="../../shared/learn.css">
{('<style>' + d['css'] + '</style>') if d.get('css') else ''}
</head>
<body data-deck="{NAMES[i]}" data-home="../index.html" data-home-label="Post-training">

{body}

<script src="../../shared/deck.js"></script>
<script src="../../shared/learn.js"></script>
<script>
(() => {{
  const {{ svg, clear, fmt }} = Deck;
{d.get('js', '')}
}})();
</script>
</body>
</html>
'''


if __name__ == '__main__':
    sys.path.insert(0, sys.path[0])
    from post_a import DECKS as A
    from post_b import DECKS as B
    decks = {**A, **B}
    for i, slug in enumerate(SLUGS):
        if slug in decks:
            os.makedirs(f'{OUT}/{slug}', exist_ok=True)
            open(f'{OUT}/{slug}/index.html', 'w').write(expand_acronyms(page(i, decks[slug]))[0])
            print('wrote', slug)
