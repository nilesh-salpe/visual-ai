"""Generate the tokenization decks (9-beat template) into visual-ai/tokenization/."""
import os, sys
from tool import section, REPO

OUT = os.path.join(REPO, 'tokenization')
SLUGS = ['01-why-tokenize', '02-bpe-from-scratch', '03-byte-level-bpe', '04-wordpiece-unigram', '05-sentencepiece',
         '06-many-tokenizations', '07-vocabulary-size', '08-tokenizers-in-llms', '09-multilingual-cost', '10-tokenization-quirks']
NAMES = ['Why tokenize?', 'BPE from scratch', 'Byte-level BPE', 'WordPiece and unigram LM', 'SentencePiece',
         'One text, many tokenizations', 'Vocabulary size trade-offs', 'Tokenizers in real LLMs', 'Multilingual cost', 'Tokenization quirks']


def page(i, d):
    n = i + 1
    prev = f'<a href="../{SLUGS[i - 1]}/index.html">← {i:02d}</a>' if i else ''
    nxt = f'<a href="../{SLUGS[i + 1]}/index.html">{n + 1:02d} · {NAMES[i + 1]} →</a>' if i < len(SLUGS) - 1 else 'You\'ve finished the series. <a href="../playground/index.html">Try the live tokenizer playground →</a>'
    links = ' · '.join(x for x in [('Next: ' + nxt) if i < len(SLUGS) - 1 else nxt, ('Previous: ' + prev) if prev else '', '<a href="../index.html">All decks</a>', '<a href="../playground/index.html">Playground</a>'] if x)
    recap = ''.join(f'<div><span><b>{k}:</b> {v}</span></div>' for k, v in d['recap'])
    take = section('s-take', 9, 'Key takeaway', f'''    <div class="take-line">{d['line']}</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>{d['explain']}</p></div>
    <div class="recap">{recap}</div>
    <p class="start-hint">{links}</p>''')
    title = f'''<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Tokenization for LLMs · {n:02d}</div>
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
<link rel="stylesheet" href="../tk.css">
{('<style>' + d['css'] + '</style>') if d.get('css') else ''}
</head>
<body data-deck="{NAMES[i]}" data-home="../index.html" data-home-label="Tokenization">

{body}

<script src="../../shared/deck.js"></script>
<script src="../../shared/learn.js"></script>
<script src="../data/examples.js"></script>
<script src="../tk.js"></script>
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
    import os
    from tok_a import DECKS as A
    from tok_b import DECKS as B
    decks = {**A, **B}
    for i, slug in enumerate(SLUGS):
        if slug not in decks:
            continue
        os.makedirs(f'{OUT}/{slug}', exist_ok=True)
        open(f'{OUT}/{slug}/index.html', 'w').write(page(i, decks[slug]))
        print('wrote', slug)
