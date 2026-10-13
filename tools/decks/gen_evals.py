"""Generate the evals decks (9-beat template) into visual-ai/evals/."""
import sys, os, json
from tool import section, REPO

OUT = os.path.join(REPO, 'evals')
NB_INDEX = os.path.join(REPO, 'tools', 'notebooks', 'index_evals.json')
SLUGS = ['01-what-an-eval-measures', '02-benchmarks', '03-pass-at-k', '04-error-bars', '05-contamination', '06-llm-as-judge', '07-arenas']
NAMES = ['What an eval measures', 'Benchmarks and their failure modes', 'pass@k and sampling metrics', 'Error bars and comparing models', 'Contamination', 'LLM-as-judge', 'Arenas and ratings']
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
    <div class="kicker">Evaluating LLMs · {n:02d}</div>
    <h1>{d['h1']}</h1>
    <p class="sub">{d['sub']}</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>{d['prob']}</div>
      <div class="c"><b>Core idea</b>{d['core']}</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>'''
    body = '\n\n'.join([title] + d['slides'] + [take])
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
<body data-deck="{NAMES[i]}" data-home="../index.html" data-home-label="Evals">

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
    from evals_decks import DECKS as decks
    for i, slug in enumerate(SLUGS):
        if slug in decks:
            os.makedirs(f'{OUT}/{slug}', exist_ok=True)
            open(f'{OUT}/{slug}/index.html', 'w').write(page(i, decks[slug]))
            print('wrote', slug)
