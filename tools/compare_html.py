"""Compare two builds of the same decks: visible text and element structure (tag + class), ignoring whitespace.
    python3 tools/compare_html.py <old_root> <new_root> <topic> [...]"""
import difflib, html as H, os, re, sys


def norm(s):
    s = re.sub(r'<script\b.*?</script>|<style\b.*?</style>|<!--.*?-->', ' ', s, flags=re.S)
    body = s.split('<body', 1)[1]
    text = re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', body))).strip()
    tags = [(t.lower(), ' '.join(sorted((re.search(r'class="([^"]*)"', a) or [None, ''])[1].split()))) for t, a in re.findall(r'<([a-zA-Z][a-zA-Z0-9]*)([^>]*)>', body)]
    return text, tags


old_root, new_root, topics = sys.argv[1], sys.argv[2], sys.argv[3:]
bad = 0
for t in topics:
    for slug in sorted(os.listdir(os.path.join(new_root, t))):
        a, b = os.path.join(old_root, t, slug, 'index.html'), os.path.join(new_root, t, slug, 'index.html')
        if not re.match(r'\d\d-', slug) or not os.path.exists(b):
            continue
        (ta, ga), (tb, gb) = norm(open(a).read()), norm(open(b).read())
        same_text, same_tags = ta == tb, ga == gb
        if not (same_text and same_tags):
            bad += 1
            print(f'{t}/{slug}: text {"same" if same_text else "DIFF"}, structure {"same" if same_tags else "DIFF"}')
            if not same_text:
                sm = difflib.SequenceMatcher(None, ta, tb)
                for op, i1, i2, j1, j2 in [o for o in sm.get_opcodes() if o[0] != 'equal'][:3]:
                    print(f'   {op}: …{ta[max(0, i1 - 40):i2 + 40]!r}\n      → …{tb[max(0, j1 - 40):j2 + 40]!r}')
            elif not same_tags:
                sm = difflib.SequenceMatcher(None, ga, gb)
                for op, i1, i2, j1, j2 in [o for o in sm.get_opcodes() if o[0] != 'equal'][:3]:
                    print(f'   {op}: {ga[i1:i2][:4]} → {gb[j1:j2][:4]}')
        else:
            print(f'{t}/{slug}: identical text and structure')
sys.exit(1 if bad else 0)
