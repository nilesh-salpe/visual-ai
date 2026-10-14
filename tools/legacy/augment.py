"""Insert extras (glance, worked example, tricks & traps, key papers) into hand-written decks, idempotently.

Spec keys beyond extras.py: glance_in (slide id), example_after, traps_after (slide ids), beats (bool: deck uses
the 9-beat tags). Re-running removes previously inserted pieces first.
"""
import re
from extras import glance_html, example_slide, traps_slide, papers_slide

SECTION = re.compile(r'<section class="slide[^"]*" id="([^"]+)"[^>]*>.*?</section>', re.S)


def strip(html):
    html = re.sub(r'\n*<section class="slide" id="s-(example|traps|papers)"[^>]*>.*?</section>', '', html, flags=re.S)
    return re.sub(r'\n?\s*<!--x:glance-->.*?<!--/x:glance-->', '', html, flags=re.S)


def _after(html, sid, block):
    for m in SECTION.finditer(html):
        if m.group(1) == sid:
            return html[:m.end()] + '\n\n' + block + html[m.end():]
    raise KeyError(sid)


def augment(html, spec):
    html = strip(html)
    if 'shared/learn.css' not in html:
        html = html.replace('<link rel="stylesheet" href="../../shared/deck.css">',
                            '<link rel="stylesheet" href="../../shared/deck.css">\n<link rel="stylesheet" href="../../shared/learn.css">', 1)
    beats = spec.get('beats', True)
    if spec.get('glance'):
        m = next(m for m in SECTION.finditer(html) if m.group(1) == spec['glance_in'])
        sec = m.group(0); cut = sec.rindex('</div>')
        html = html[:m.start()] + sec[:cut] + glance_html(spec['glance']) + '\n  ' + sec[cut:] + html[m.end():]
    if spec.get('example'):
        html = _after(html, spec['example_after'],
                      example_slide(spec['example']) if beats else example_slide(spec['example'], chapter='Example', tag=('b5', 'Worked example')))
    if spec.get('traps'):
        html = _after(html, spec['traps_after'], traps_slide(spec['traps']) if beats else traps_slide(spec['traps'], tag=('b7', 'Tricks and traps')))
    if spec.get('papers'):
        last = list(SECTION.finditer(html))[-1].group(1)
        html = _after(html, last, papers_slide(spec['papers']))
    return html
