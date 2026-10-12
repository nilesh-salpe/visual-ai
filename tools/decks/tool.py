"""Restructure the transformer decks into the 9-beat learning template.

Reads each deck from git HEAD (so reruns are idempotent), keeps existing slides
(re-tagged into beats), inserts new beat slides, and writes the result.
"""
import os, re, subprocess, sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BEATS = ['Problem', 'Limitation', 'Your turn', 'Core idea', 'How it works', 'Why it works', 'Misconceptions', 'Check yourself', 'Key takeaway']
CHAPTER = {1: 'Problem', 2: 'Limitation', 3: 'Your turn', 4: 'Core idea', 5: 'How', 6: 'Why', 7: 'Myths', 8: 'Check', 9: 'Takeaway'}


def tag(b):
    return f'<span class="qtag b{b}">{b} · {BEATS[b - 1]}</span>'


def section(sid, b, title, body):
    return f'''<section class="slide" id="{sid}" data-chapter="{CHAPTER[b]}">
  <div class="inner">
    {tag(b)}
    <h2>{title}</h2>
    <hr>
{body}
  </div>
</section>'''


def mcq(q, opts, ok, why, sub=None):
    btns = '\n'.join(f'      <button{" data-ok" if i == ok else ""}>{chr(65 + i)}. {o}</button>' for i, o in enumerate(opts))
    s = f'<small>{sub}</small>' if sub else ''
    return f'''    <div class="quiz">
      <p class="qq">{q}{s}</p>
      <div class="opts">
{btns}
      </div>
      <div class="why">{why}</div>
    </div>'''


def openq(q, ans, label='Think first, then reveal', cls=''):
    return f'''    <div class="quiz {cls}">
      <p class="qq">{q}</p>
      <button class="reveal">{label}</button>
      <div class="why">{ans}</div>
    </div>'''


def your_turn(sid, title, q, opts, ok, why):
    body = '    <p class="lede">Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.</p>\n' + mcq(q, opts, ok, why)
    return section(sid, 3, title, body)


def myths(sid, items, title='Common misconceptions'):
    body = '    <p class="lede">Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.</p>\n' + '\n'.join(openq(f'"{m}"', t, 'Why is this wrong?', 'myth') for m, t in items)
    return section(sid, 7, title, body)


def check(sid, items, title='Check yourself'):
    parts = []
    for it in items:
        if it[0] == 'mcq':
            parts.append(mcq(*it[1:]))
        else:
            parts.append(openq(it[1], it[2]))
    body = '    <p class="lede">Answer from memory. If you can\'t, revisit the slide named in the answer.</p>\n' + '\n'.join(parts)
    return section(sid, 8, title, body)


def retag(html, b):
    html = re.sub(r'data-chapter="[^"]*"', f'data-chapter="{CHAPTER[b]}"', html, count=1)
    m = re.search(r'<span class="qtag [^"]*">.*?</span>', html)
    if m:
        return html[:m.start()] + tag(b) + html[m.end():]
    m = re.search(r'<div class="label ppr">In the paper · (.*?)</div>', html)
    if m:
        return html[:m.start()] + tag(b) + f' <span class="ill" style="color:var(--c);border-color:var(--c)">from the paper · {m.group(1)}</span>' + html[m.end():]
    raise ValueError('no tag found to replace')


def takeaway(line, interview, end_html):
    recap = end_html[end_html.index('<div class="recap">'):end_html.index('<p class="start-hint">')].rstrip()
    hint = end_html[end_html.index('<p class="start-hint">'):]
    hint = hint[:hint.index('</p>') + 4]
    body = f'''    <div class="take-line">{line}</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>{interview}</p></div>
    {recap}
    {hint}'''
    return section('s-take', 9, 'Key takeaway', body)


def build(deck, spec):
    path = f'transformer/{deck}/index.html'
    src = subprocess.run(['git', '-C', REPO, 'show', f'HEAD:{path}'], capture_output=True, text=True, check=True).stdout
    secs = {m.group(1): m.group(0) for m in re.finditer(r'<section class="slide[^"]*" id="([^"]+)"[^>]*>.*?</section>', src, re.S)}
    first = src.index('<section'); last = src.rindex('</section>') + len('</section>')
    out = [secs['s-title']]
    for item in spec['order']:
        if isinstance(item, tuple) and item[0] == 'html':
            out.append(item[1])
        else:
            sid, b = item
            out.append(retag(secs[sid], b))
    out.append(takeaway(spec['line'], spec['interview'], secs['s-end']))
    html = src[:first] + '\n\n'.join(out) + src[last:]
    if spec.get('js'):
        html = html.replace('</body>', f'<script>\n(() => {{\n{spec["js"]}\n}})();\n</script>\n</body>')
    open(f'{REPO}/{path}', 'w').write(html)
    used = {i[0] for i in spec['order'] if not (isinstance(i, tuple) and i[0] == 'html')}
    dropped = set(secs) - used - {'s-title', 's-end'}
    return dropped


if __name__ == '__main__':
    sys.path.insert(0, sys.path[0])
    from specs_a import DECKS as A
    from specs_b import DECKS as B
    for deck, spec in {**A, **B}.items():
        dropped = build(deck, spec)
        print(deck, 'OK', ('DROPPED: ' + ', '.join(sorted(dropped))) if dropped else '')
