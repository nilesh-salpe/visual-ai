"""One-time migration: current HTML decks → content/<topic>/<slug>/deck.md + widget.js.

Structured parts (lede paragraphs, card grids, quizzes, myths, "In detail" boxes, the glance diagram and the
example / traps / papers slides) become readable Markdown blocks; anything else stays as raw HTML so the
rebuilt page is equivalent. Extras data (glance, example, traps) comes from tools/decks/extras_<topic>.py.

    python3 tools/migrate_to_md.py <topic> [...]
"""
import html as H, importlib, os, re, sys

import yaml

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'decks'))
EXTRAS_MODULE = {'inference': 'extras_inference', 'architecture': 'extras_architecture', 'post-training': 'extras_post', 'evals': 'extras_evals',
                 'tokenization': 'extras_tokenization', 'gpu': 'extras_gpu', 'transformer': 'extras_transformer'}
UNSAFE = re.compile(r'[*_`\[\]#|]|^\s*[-+>]|^\s*\d+\.', re.M)   # text that Markdown might reinterpret


class Lit(str):
    pass


yaml.add_representer(Lit, lambda d, s: d.represent_scalar('tag:yaml.org,2002:str', s, style='|'))


def paper_library():
    """All paper records by key, from every extras module, deduplicated by URL."""
    lib, by_url = {}, {}
    from papers import PAPERS
    sources = [PAPERS] + [getattr(importlib.import_module(m), a, {}) for m in EXTRAS_MODULE.values() for a in ('P', 'DOCS')]
    for src in sources:
        for k, p in src.items():
            sig = (p['url'], p['summary'], p.get('number', ''))
            if sig not in by_url:
                key, n = k, 2
                while key in lib:
                    key = f'{k}_{n}'; n += 1
                lib[key] = dict(p); by_url[sig] = key
    return lib, by_url


def lists(x):
    if isinstance(x, (list, tuple)):
        return [lists(v) for v in x]
    if isinstance(x, dict):
        return {k: lists(v) for k, v in x.items()}
    return x


def top_level(html):
    """Split an HTML fragment into top-level chunks (elements, comments, text)."""
    chunks, i, n = [], 0, len(html)
    while i < n:
        while i < n and html[i].isspace():
            i += 1
        if i >= n:
            break
        if html.startswith('<!--', i):
            j = html.index('-->', i) + 3
            if html.startswith('<!--x:glance-->', i):
                j = html.index('<!--/x:glance-->', i) + len('<!--/x:glance-->')
            chunks.append(html[i:j]); i = j; continue
        m = re.match(r'<([a-zA-Z][a-zA-Z0-9]*)\b', html[i:])
        if not m:
            j = html.find('<', i)
            j = n if j < 0 else j
            chunks.append(html[i:j]); i = j; continue
        tag, depth, j = m.group(1).lower(), 0, i
        pat = re.compile(r'<(/?)' + tag + r'\b[^>]*?(/?)>', re.I)
        for t in pat.finditer(html, i):
            if t.group(1):
                depth -= 1
            elif not t.group(2):
                depth += 1
            if depth == 0:
                j = t.end(); break
        else:
            j = n
        if tag in ('br', 'hr', 'img', 'input'):
            j = html.index('>', i) + 1
        chunks.append(html[i:j]); i = j
    return chunks


def inner(el):
    return el[el.index('>') + 1:el.rindex('<')]


def conv_chunk(c):
    """Convert one top-level chunk to Markdown when it is a known safe pattern, else return raw HTML."""
    s = c.strip()
    if s.startswith('<!--x:glance-->'):
        return '{{glance}}'
    m = re.fullmatch(r'<p class="lede">(.*)</p>', s, re.S)
    if m and not UNSAFE.search(m.group(1)) and '\n' not in m.group(1).strip():
        return m.group(1).strip() + '\n{: .lede}'
    m = re.fullmatch(r'<div class="(grid[234])">(.*)</div>', s, re.S)
    if m:
        cards = top_level(m.group(2))
        out = []
        for card in cards:
            cm = re.fullmatch(r'<div class="card( \w+)?"><h3>(.*?)</h3><p>(.*?)</p></div>', card.strip(), re.S)
            if not cm or UNSAFE.search(cm.group(2)) or UNSAFE.search(cm.group(3)) or '\n' in cm.group(3):
                return raw(s)
            col = (cm.group(1) or '').strip()
            out.append(f'### {"[" + col + "] " if col else ""}{cm.group(2)}\n{cm.group(3)}')
        return f'::: cards {m.group(1)}\n' + '\n\n'.join(out) + '\n:::'
    m = re.fullmatch(r'<div class="quiz">\s*<p class="qq">(.*?)(?:<small>(.*?)</small>)?</p>\s*<div class="opts">(.*?)</div>\s*<div class="why">(.*)</div>\s*</div>', s, re.S)
    if m:
        opts = re.findall(r'<button( data-ok)?>[A-Z]\. (.*?)</button>', m.group(3), re.S)
        texts = [m.group(1), m.group(2) or '', m.group(4)] + [o for _, o in opts]
        if opts and not any(UNSAFE.search(t) or '\n' in t for t in texts):
            body = [f'? {m.group(1)}'] + ([f'?? {m.group(2)}'] if m.group(2) else []) + [f'- [{"x" if ok else " "}] {o}' for ok, o in opts] + [f'> {m.group(4)}']
            return '::: quiz\n' + '\n'.join(body) + '\n:::'
        return raw(s)
    m = re.fullmatch(r'<div class="quiz( myth)?">\s*<p class="qq">(.*?)</p>\s*<button class="reveal">(.*?)</button>\s*<div class="why">(.*)</div>\s*</div>', s, re.S)
    if m:
        if any(UNSAFE.search(t) or '\n' in t for t in (m.group(2), m.group(4))):
            return raw(s)
        default = 'Why is this wrong?' if m.group(1) else 'Think first, then reveal'
        args = ('myth ' if m.group(1) else '') + ('' if m.group(3) == default else f'label="{m.group(3)}"')
        return f'::: reveal {args}'.rstrip() + f'\n? {m.group(2)}\n> {m.group(4)}\n:::'
    return raw(s)


def raw(s):
    """Raw HTML must start at column 0 and be separated by blank lines so Markdown leaves it alone."""
    lines = s.split('\n')
    return '\n'.join(l[4:] if l.startswith('    ') else l for l in lines)


def convert(topic, slug, lib, by_url, extras):
    f = os.path.join(REPO, topic, slug, 'index.html')
    src = open(f).read()
    head, body = src.split('<body', 1)
    fm = {'title': H.unescape(re.search(r'<title>(.*?)</title>', head).group(1))}
    battrs = re.match(r'([^>]*)>', body).group(1)
    fm['body'] = {k: H.unescape(v) for k, v in re.findall(r'([\w-]+)="([^"]*)"', battrs)}
    fm['styles'] = re.findall(r'<link rel="stylesheet" href="([^"]+)">', head)
    css = re.search(r'<style>(.*?)</style>', head, re.S)
    if css:
        fm['css'] = Lit(css.group(1).strip())
    fm['scripts'] = re.findall(r'<script src="([^"]+)"></script>', body)
    inline = re.findall(r'<script>\n?(.*?)</script>', body, re.S)
    spec = extras.get(slug, {})
    if spec.get('glance'):
        g = spec['glance']
        fm['glance'] = {'steps': [f'{l} :: {sub} :: {c}' for l, sub, c in g['steps']]}
        if g.get('loop'):
            fm['glance']['loop'] = f'{g["loop"][0]} -> {g["loop"][1]} :: {g["loop"][2]}'
        if g.get('caption'):
            fm['glance']['caption'] = g['caption']
    if spec.get('example'):
        fm['example'] = lists(spec['example'])
    if spec.get('traps'):
        fm['traps'] = {k: [f'{a} :: {b}' for a, b in spec['traps'][k]] for k in ('tricks', 'traps')}
    if spec.get('papers'):
        fm['papers'] = [by_url[(p['url'], p['summary'], p.get('number', ''))] for p in spec['papers']]
    out = []
    for m in re.finditer(r'<section class="slide([^"]*)" id="([^"]+)"([^>]*)>(.*?)</section>', body, re.S):
        cls, sid, rest, content = m.group(1).strip(), m.group(2), m.group(3), m.group(4)
        chap = re.search(r'data-chapter="([^"]*)"', rest)
        if sid in ('s-example', 's-traps', 's-papers'):
            kind = sid[2:]
            tag = re.search(r'<span class="qtag (\w+)">(.*?)</span>', content)
            attrs = f' from="{kind}"' + (f' chapter="{chap.group(1)}" tag="{tag.group(2)}" tagclass="{tag.group(1)}"' if kind != 'papers' else '')
            out.append(f'<!-- slide id="{sid}"{attrs} -->\n')
            continue
        sm = re.fullmatch(r'\s*<div class="inner">\s*<span class="qtag (\w+)">(.*?)</span>\s*<h2>(.*?)</h2>\s*<hr>(.*)</div>\s*', content, re.S)
        if sm and chap and '<' not in sm.group(2) and '\n' not in sm.group(3) and not UNSAFE.search(re.sub(r'<[^>]+>', '', sm.group(3))):
            chunks = top_level(sm.group(4))
            body_md = '\n\n'.join(conv_chunk(c) for c in chunks)
            out.append(f'<!-- slide id="{sid}" chapter="{chap.group(1)}" tag="{sm.group(2)}" tagclass="{sm.group(1)}"{(" class=" + chr(34) + cls + chr(34)) if cls else ""} -->\n## {sm.group(3)}\n\n{body_md}\n')
        else:
            out.append(f'<!-- slide raw -->\n{m.group(0)}\n')
    folder = os.path.join(REPO, 'content', topic, slug)
    os.makedirs(folder, exist_ok=True)
    front = yaml.dump(fm, allow_unicode=True, sort_keys=False, width=160)
    open(os.path.join(folder, 'deck.md'), 'w').write(f'---\n{front}---\n\n' + '\n'.join(out))
    if inline:
        open(os.path.join(folder, 'widget.js'), 'w').write('\n'.join(x.strip('\n') for x in inline) + '\n')


if __name__ == '__main__':
    lib, by_url = paper_library()
    os.makedirs(os.path.join(REPO, 'content'), exist_ok=True)
    yaml.add_representer(dict, lambda d, data: d.represent_dict(data.items()))
    open(os.path.join(REPO, 'content', 'papers.yml'), 'w').write(yaml.dump(lib, allow_unicode=True, sort_keys=False, width=160))
    for topic in sys.argv[1:]:
        extras = importlib.import_module(EXTRAS_MODULE[topic]).EXTRAS
        for slug in sorted(os.listdir(os.path.join(REPO, topic))):
            if re.match(r'\d\d-', slug):
                convert(topic, slug, lib, by_url, extras)
                print('migrated', topic, slug)
