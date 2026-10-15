"""Build slide decks from Markdown sources.

Source layout (one folder per deck):
    content/<topic>/<slug>/deck.md     front matter (YAML) + slides
    content/<topic>/<slug>/widget.js   the deck's interactive code (optional)
Output: <topic>/<slug>/index.html (same static HTML as before).

deck.md format
--------------
---
title: KV Cache                      # <title>
body: {data-deck: KV cache, ...}     # attributes of <body>
styles: [../../shared/deck.css, ...] # stylesheet links
scripts: [../../shared/deck.js, ...] # scripts loaded before widget.js
css: "..."                           # optional inline CSS
glance: {...}  example: {...}  traps: {...}  papers: [key, ...]   # extras (see tools/decks/extras.py)
---

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Slide title
Text in Markdown or raw HTML.
{: .lede}                              # attribute list: class on the paragraph above

::: cards grid3                        # card grid; each card starts with "### [colour] Title"
### [d] Throughput hides latency
A huge batch maximizes tokens/s …
:::

::: quiz                               # multiple choice: "- [x]" marks the right answer, "> " the explanation
? Which metric …
- [ ] Peak tokens per second
- [x] Goodput
> **B.** DistServe defines …
:::

::: reveal [myth] [label=…]            # open question: "? question", "> answer"
::: deep Title                         # "In detail" box
::: diagram 660x300                    # steppable box-and-arrow diagram in YAML (see tools/decks/diagram.py)
::: table                              # a Markdown pipe table, styled as .tbl
::: code [language]                    # a code sample, shown verbatim
::: colab <notebook path> [label]      # "Try it in Colab" banner; the body is the description
<!-- slide from="title" -->             # the title slide, from the front-matter `intro` (kicker, h1, sub, problem, core, hint)
{{glance}}                             # the at-a-glance diagram from front matter
<!-- slide id="s-example" from="example" -->   # a slide generated from front-matter data (example, traps, papers)
<!-- slide raw -->                     # a slide given as raw HTML, verbatim, up to the next marker

    python3 tools/build_decks.py [topic ...]
"""
import html as H, os, re, sys

import markdown
import yaml

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'decks'))
from acronyms import process as expand_acronyms                     # noqa: E402
from extras import glance_html, example_slide, traps_slide, papers_slide  # noqa: E402
import diagram                                                       # noqa: E402

COLAB = 'https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/'

MD = markdown.Markdown(extensions=['attr_list', 'md_in_html', 'tables'])
MARKER = re.compile(r'^<!-- slide(.*?)-->\s*$', re.M)
ATTR = re.compile(r'(\w+)="([^"]*)"')


def md(text):
    MD.reset()
    return MD.convert(text)


def md_inline(text):
    out = md(text.strip())
    return out[3:-4] if out.startswith('<p>') and out.endswith('</p>') and out.count('<p>') == 1 else out


def blocks(text, fm):
    """Render custom ::: blocks and {{glance}}; everything else goes through Markdown."""
    out, buf, lines, i = [], [], text.split('\n'), 0

    def flush():
        if ''.join(buf).strip():
            out.append(md('\n'.join(buf)))
        buf.clear()

    while i < len(lines):
        line = lines[i]
        if line.strip() == '{{glance}}':
            flush(); out.append(glance_html(fm['glance']).strip()); i += 1; continue
        m = re.match(r'^:::\s*(\w+)\s*(.*)$', line)
        if not m:
            buf.append(line); i += 1; continue
        flush()
        kind, args, body = m.group(1), m.group(2).strip(), []
        i += 1
        while i < len(lines) and lines[i].strip() != ':::':
            body.append(lines[i]); i += 1
        i += 1
        out.append(render_block(kind, args, '\n'.join(body)))
    flush()
    return '\n'.join(out)


def render_block(kind, args, body):
    if kind == 'cards':
        cards = re.split(r'^### ', body.strip(), flags=re.M)[1:]
        items = []
        for c in cards:
            head, _, rest = c.partition('\n')
            m = re.match(r'\[(\w+)\]\s*(.*)', head.strip())
            col, title = (m.group(1), m.group(2)) if m else ('', head.strip())
            items.append(f'<div class="card{(" " + col) if col else ""}"><h3>{md_inline(title)}</h3>{md(rest.strip())}</div>')
        return f'<div class="{args or "grid3"}">\n      ' + '\n      '.join(items) + '\n    </div>'
    if kind == 'quiz':
        q = re.search(r'^\?\s*(.*)$', body, re.M).group(1)
        sub = re.search(r'^\?\?\s*(.*)$', body, re.M)
        opts = re.findall(r'^- \[( |x)\]\s*(.*)$', body, re.M)
        why = '\n'.join(l[2:] if l.startswith('> ') else l[1:] for l in body.split('\n') if l.startswith('>'))
        btns = '\n'.join(f'      <button{" data-ok" if ok == "x" else ""}>{chr(65 + k)}. {md_inline(o)}</button>' for k, (ok, o) in enumerate(opts))
        s = f'<small>{md_inline(sub.group(1))}</small>' if sub else ''
        return f'''<div class="quiz">
      <p class="qq">{md_inline(q)}{s}</p>
      <div class="opts">
{btns}
      </div>
      <div class="why">{md_inline(why)}</div>
    </div>'''
    if kind == 'reveal':
        cls = ' myth' if 'myth' in args.split() else ''
        lab = re.search(r'label="([^"]*)"', args)
        q = re.search(r'^\?\s*(.*)$', body, re.M).group(1)
        ans = '\n'.join(l[2:] if l.startswith('> ') else l[1:] for l in body.split('\n') if l.startswith('>'))
        label = lab.group(1) if lab else ('Why is this wrong?' if cls else 'Think first, then reveal')
        return f'''<div class="quiz{cls}">
      <p class="qq">{md_inline(q)}</p>
      <button class="reveal">{label}</button>
      <div class="why">{md_inline(ans)}</div>
    </div>'''
    if kind == 'deep':
        return f'<div class="deep"><h4>{H.escape(args)}</h4>{md(body)}</div>'
    if kind == 'raw':
        return body
    if kind == 'diagram':
        return diagram.render(args, body, where=CURRENT[0])
    if kind == 'table':
        return '<div class="visual scroll-x">' + md(body.strip()).replace('<table>', '<table class="tbl">', 1) + '</div>'
    if kind == 'code':
        return f'<div class="visual"><pre class="code">{H.escape(body.strip(chr(10)))}</pre></div>'
    if kind == 'colab':
        path = args.split()[0]
        return (f'<div class="visual colab-banner"><div><b>🛠 Try it in Colab</b><p class="caption">{md_inline(body)}</p></div>'
                f'<a class="btn primary" href="{COLAB}{path}" target="_blank" rel="noopener">Open notebook →</a></div>')
    raise ValueError(f'unknown block ::: {kind}')


def render_slide(attrs, content, fm):
    a = dict(ATTR.findall(attrs))
    if 'raw' in attrs.split():
        return content.strip()
    if a.get('from') == 'example':
        return example_slide(fm['example'], *([a['chapter'], (a['tagclass'], a['tag'])] if 'tag' in a else []))
    if a.get('from') == 'traps':
        return traps_slide(fm['traps'], *([(a['tagclass'], a['tag'])] if 'tag' in a else []))
    if a.get('from') == 'papers':
        return papers_slide(fm['papers'])
    if a.get('from') == 'title':
        return title_slide(fm['intro'])
    title, _, body = content.strip().partition('\n')
    title = re.sub(r'^##\s*', '', title)
    tag = f'<span class="qtag {a.get("tagclass", "")}">{a["tag"]}</span>' if 'tag' in a else ''
    extra = a.get('pre', '')
    return f'''<section class="slide{(" " + a["class"]) if a.get("class") else ""}" id="{a["id"]}" data-chapter="{a["chapter"]}">
  <div class="inner">
    {tag}{extra}
    <h2>{md_inline(title)}</h2>
    <hr>
{blocks(body, fm)}
  </div>
</section>'''


def title_slide(t):
    return f'''<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">{H.escape(t["kicker"])}</div>
    <h1>{md_inline(t["h1"])}</h1>
    <p class="sub">{md_inline(t["sub"])}</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>{md_inline(t["problem"])}</div>
      <div class="c"><b>Core idea</b>{md_inline(t["core"])}</div>
    </div>
    <div class="toc" data-auto></div>
    <p class="start-hint">{md_inline(t["hint"])}</p>
  </div>
</section>'''


def resolve_papers(fm):
    if fm.get('papers') and isinstance(fm['papers'][0], str):
        lib = yaml.safe_load(open(os.path.join(REPO, 'content', 'papers.yml')))
        fm['papers'] = [lib[k] for k in fm['papers']]


def normalize(fm):
    """Expand the compact 'a :: b :: c' forms used in front matter."""
    g = fm.get('glance')
    if g:
        g['steps'] = [tuple(p.strip() for p in s.split('::')) for s in g['steps']]
        if isinstance(g.get('loop'), str):
            ends, label = g['loop'].split('::', 1)
            a, b = (int(x) for x in ends.split('->'))
            g['loop'] = (a, b, label.strip())
    t = fm.get('traps')
    if t:
        for k in ('tricks', 'traps'):
            t[k] = [tuple(p.strip() for p in s.split('::', 1)) for s in t[k]]


CURRENT = ['']


def build(folder):
    CURRENT[0] = os.path.relpath(folder, os.path.join(REPO, 'content'))
    diagram._count[0] = 0                                # marker ids only need to be unique within one page
    src = open(os.path.join(folder, 'deck.md')).read()
    _, front, body = src.split('---\n', 2)
    fm = yaml.safe_load(front)
    normalize(fm)
    resolve_papers(fm)
    parts = MARKER.split(body)
    slides = [render_slide(parts[k], parts[k + 1], fm) for k in range(1, len(parts), 2)]
    body_attrs = ' '.join(f'{k}="{H.escape(str(v), quote=True)}"' for k, v in fm.get('body', {}).items())
    links = '\n'.join(f'<link rel="stylesheet" href="{s}">' for s in fm.get('styles', []))
    scripts = '\n'.join(f'<script src="{s}"></script>' for s in fm.get('scripts', []))
    widget = os.path.join(folder, 'widget.js')
    inline = f'\n<script>\n{open(widget).read().rstrip()}\n</script>' if os.path.exists(widget) else ''
    css = f'\n<style>{fm["css"]}</style>' if fm.get('css') else ''
    page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{H.escape(fm["title"])}</title>
{links}{css}
</head>
<body {body_attrs}>

{chr(10).join(chr(10) + s for s in slides).strip()}

{scripts}{inline}
</body>
</html>
'''
    return expand_acronyms(page)[0]


if __name__ == '__main__':
    topics = sys.argv[1:] or sorted(d for d in os.listdir(os.path.join(REPO, 'content')) if os.path.isdir(os.path.join(REPO, 'content', d)))
    for t in topics:
        for slug in sorted(os.listdir(os.path.join(REPO, 'content', t))):
            folder = os.path.join(REPO, 'content', t, slug)
            if os.path.isdir(folder) and os.path.exists(os.path.join(folder, 'deck.md')):
                out = os.path.join(os.environ.get('OUT_ROOT', REPO), t, slug, 'index.html')
                os.makedirs(os.path.dirname(out), exist_ok=True)
                open(out, 'w').write(build(folder))
                print('built', t, slug)
