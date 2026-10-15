import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from nb_lib import build, validate
from nb_reasoning import NBS
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ok = True; index = []
for nb in NBS:
    path, doc, colab = build(nb, 'reasoning')
    problems, log = validate(doc, nb['tasks'])
    status = 'OK' if not problems else 'FAIL: ' + '; '.join(problems)
    print(f"{nb['slug']:28} {status}")
    if problems:
        ok = False; print(log[-1500:])
    os.makedirs(os.path.dirname(f'{REPO}/{path}'), exist_ok=True)
    json.dump(doc, open(f'{REPO}/{path}', 'w'), indent=1, ensure_ascii=False)
    index.append((nb, path, colab))
json.dump([{'slug': n['slug'], 'title': n['title'], 'path': p, 'colab': c, 'deck': n['deck'], 'minutes': n['minutes']} for n, p, c in index], open(os.path.join(os.path.dirname(__file__), 'index_reasoning.json'), 'w'), indent=1)
sys.exit(0 if ok else 1)
