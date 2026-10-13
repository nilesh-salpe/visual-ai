"""Expand each glossary acronym at its first body-text use in a deck, and lint decks for unexpanded acronyms.

Each deck can be opened on its own, so the rule is per deck: the first time an acronym appears in
readable body text it must be spelled out, e.g. "KV (key-value) cache". Headings, buttons, slider
labels, tags, formulas, code and scripts are skipped (they are too short to carry an expansion), so the
expansion lands in the first sentence that uses the term.

    python3 tools/decks/acronyms.py lint  <html files...>   # report problems, exit 1 if any
    python3 tools/decks/acronyms.py fix   <html files...>   # expand in place (idempotent)
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GLOSSARY = json.load(open(os.path.join(HERE, '..', '..', 'shared', 'glossary.json')))
TERMS, EXEMPT = GLOSSARY['terms'], set(GLOSSARY['exempt'])

SKIP_TAGS = {'script', 'style', 'title', 'h1', 'h2', 'h3', 'h4', 'sup', 'sub', 'button', 'option', 'select', 'output', 'svg', 'label', 'code', 'pre', 'th', 'summary'}
SKIP_CLASSES = {'qtag', 'ill', 'kicker', 'eq', 'mono', 'legend', 'cite', 'n', 'tags'}
TOKEN = re.compile(r'<script\b.*?</script>|<style\b.*?</style>|<!--.*?-->|<(/?)([a-zA-Z][a-zA-Z0-9]*)([^>]*)>|([^<]+|<)', re.S)
VOID = {'br', 'hr', 'img', 'input', 'meta', 'link', 'source', 'wbr'}


def _norm(s):
    return re.sub(r'[\s\-]+', ' ', s.lower())


def _segments(html):
    """Yield (kind, text, skip) where kind is 'tag' or 'text'. skip=True for text that must not be touched."""
    stack = []  # (tag, skipping)
    body = False
    for m in TOKEN.finditer(html):
        close, tag, attrs, text = m.group(1), (m.group(2) or '').lower(), m.group(3) or '', m.group(4)
        if text is not None:
            skipping = (not body) or any(s for _, s in stack)
            yield 'text', text, skipping
            continue
        yield 'tag', m.group(0), True
        if m.group(0).startswith(('<!--', '<script', '<style')) or tag in VOID or attrs.rstrip().endswith('/'):
            if tag == 'body' and not close:
                body = True
            continue
        if tag == 'body':
            body = not close
            continue
        if close:
            for i in range(len(stack) - 1, -1, -1):
                if stack[i][0] == tag:
                    del stack[i:]
                    break
        else:
            cls = re.search(r'class="([^"]*)"', attrs)
            classes = set(cls.group(1).split()) if cls else set()
            stack.append((tag, tag in SKIP_TAGS or bool(classes & SKIP_CLASSES)))


def _pattern(acr):
    return re.compile(r'(?<![A-Za-z0-9_\-])' + re.escape(acr) + r'(s?)(?![A-Za-z0-9_])')


PATTERNS = {a: _pattern(a) for a in TERMS}


def _explained(acr, before, after):
    """Already spelled out nearby: 'time to first token (TTFT)' or 'TTFT (time to first token)'."""
    exp = TERMS[acr]['exp'].split(',')[0]
    if after.lstrip().startswith('(') or re.match(r'[\w\-]*\s*\(' + re.escape(acr) + ' = ', after):
        return True
    return _norm(exp) in _norm(before[-400:])


def process(html, fix=True):
    """Return (new_html, report). report = list of (acronym, status) for acronyms found in body text."""
    out, seen_text, done, report = [], '', set(), []
    for kind, text, skip in _segments(html):
        if kind == 'tag' or skip:
            out.append(text)
            continue
        new = text
        hits = []                                   # (position, acronym, match) of first uses in this text node
        for acr, pat in PATTERNS.items():
            if acr in done:
                continue
            m = pat.search(text)
            if m:
                hits.append((m.start(), acr, m))
        inserts = []
        for _, acr, m in sorted(hits):
            done.add(acr)
            if _explained(acr, seen_text + text[:m.start()], text[m.end():]):
                report.append((acr, 'ok'))
                continue
            report.append((acr, 'expanded' if fix else 'MISSING'))
            exp = TERMS[acr]['exp']
            if m.group(1) == 's':
                exp = TERMS[acr].get('plural', exp + 's')
            end = m.end()
            if end < len(text) and text[end] == '-':        # compound like "KV-cache": explain after the word
                w = re.match(r'[A-Za-z0-9\-]+', text[end:])
                end += w.end() if w else 0
                inserts.append((end, f' ({acr} = {TERMS[acr]["exp"]})'))
            else:
                inserts.append((end, f' ({exp})'))
        if fix:                                     # insert right to left so positions stay valid
            for pos, ins in sorted(inserts, reverse=True):
                new = new[:pos] + ins + new[pos:]
        out.append(new)
        seen_text += new
    return ''.join(out), report


def unknown_acronyms(html):
    """Acronym-like tokens in body text that are neither in the glossary nor exempt."""
    found = set()
    for kind, text, skip in _segments(html):
        if kind == 'text' and not skip:
            for m in re.finditer(r'(?<![A-Za-z0-9_\-])([A-Z][A-Za-z0-9]*[A-Z0-9][A-Za-z0-9]*?)(s?)(?![A-Za-z0-9_])', text):
                w = m.group(1)
                if sum(c.isupper() for c in w) >= 2 and w not in TERMS and w not in EXEMPT and w + m.group(2) not in EXEMPT and w + m.group(2) not in TERMS and not re.fullmatch(r'[A-Z]\d+[A-Za-z0-9]*', w):
                    found.add(w)
    return found


if __name__ == '__main__':
    mode, files = sys.argv[1], sys.argv[2:]
    bad = 0
    for f in files:
        html = open(f).read()
        if mode == 'fix':
            new, rep = process(html, fix=True)
            if new != html:
                open(f, 'w').write(new)
            print(f'{f}: expanded {sum(1 for _, s in rep if s == "expanded")}')
        else:
            _, rep = process(html, fix=False)
            missing = [a for a, s in rep if s == 'MISSING']
            unk = sorted(unknown_acronyms(html))
            if missing or unk:
                bad += 1
                print(f'{f}\n  unexpanded: {" ".join(missing) or "-"}\n  not in glossary: {" ".join(unk) or "-"}')
    if mode == 'lint':
        print(f'{len(files) - bad}/{len(files)} decks clean')
        sys.exit(1 if bad else 0)
