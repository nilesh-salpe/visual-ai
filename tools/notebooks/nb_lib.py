"""Build Colab-ready exercise notebooks and validate them by executing every cell.

Each notebook: header (Colab badge + deck link) -> setup (form) -> per task: spec (md),
starter (visible, raises NotImplementedError), tests (form, prints ⏳/✅/❌) -> reference
solutions (form, hidden) -> optional experiments using the reference solution.
"""
import json, io, contextlib, textwrap

REPO = 'nilesh-salpe/visual-ai'
SITE = 'https://nilesh-salpe.github.io/visual-ai'

CHECK = '''import numpy as np, math, time, itertools, collections
np.set_printoptions(precision=4, suppress=True)

def check(name, test, impl):
    """Run `test(impl)` and report: ⏳ not implemented, ✅ passed, ❌ failed with the reason."""
    try:
        test(impl)
        print(f"✅ {name}: all tests passed")
    except NotImplementedError:
        print(f"⏳ {name}: not implemented yet. Fill in the TODO in the cell above, then re-run this cell.")
    except AssertionError as e:
        print(f"❌ {name}: {e}")
'''


def _src(s):
    s = textwrap.dedent(s).strip('\n')
    lines = s.split('\n')
    return [l + '\n' for l in lines[:-1]] + [lines[-1]]


def md(s):
    return {'cell_type': 'markdown', 'metadata': {}, 'source': _src(s)}


def code(s, title=None):
    src = (f'# @title {title}\n' if title else '') + textwrap.dedent(s).strip('\n')
    meta = {'cellView': 'form'} if title else {}
    return {'cell_type': 'code', 'metadata': meta, 'execution_count': None, 'outputs': [], 'source': _src(src)}


def build(nb, folder):
    """nb: dict(slug, title, deck, minutes, goals, setup, tasks=[dict(name, fn, md, starter, test, solution)], explore)."""
    path = f'build-it/{folder}/{nb["slug"]}.ipynb'
    colab = f'https://colab.research.google.com/github/{REPO}/blob/main/{path}'
    cells = [md(f'''
        # {nb["title"]}

        [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({colab}) &nbsp; 📖 Concept deck: [{nb["deck_name"]}]({SITE}/{nb["deck"]}) &nbsp; ⏱️ Suggested time: **{nb["minutes"]} min**

        **You will build:** {nb["goals"]}

        **How to use this notebook**
        1. Run the **Setup** cell.
        2. For each task, fill in the `TODO` in the code cell, then run the **Tests** cell under it. You'll see ⏳ (not done yet), ✅ (passed) or ❌ (failed, with the reason).
        3. Stuck? The **Reference solutions** at the bottom are collapsed. Try first.

        {nb.get("runtime", "Everything runs on CPU with NumPy, so no GPU is needed.")}
        ''')]
    if nb.get('install'):
        cells.append(code(nb['install'], title='Install pinned packages'))
    cells.append(code(CHECK + '\n' + textwrap.dedent(nb.get('setup', '')), title='Setup: run this first'))
    for i, t in enumerate(nb['tasks'], 1):
        cells.append(md(f'## Task {i}: {t["title"]}\n\n' + textwrap.dedent(t['md']).strip()))
        cells.append(code(t['starter']))
        cells.append(code(textwrap.dedent(t['test']).strip('\n') + f'\n\ncheck("{t["fn"]}", _test_{t["fn"]}, {t["fn"]})', title=f'Tests for Task {i}: run after implementing'))
    cells.append(md('---\n## Reference solutions\nTry the tasks first. Each cell below is collapsed in Colab: double-click it (or click "Show code") to reveal the solution. Running it also checks the reference against the same tests.'))
    for i, t in enumerate(nb['tasks'], 1):
        cells.append(code(textwrap.dedent(t['solution']).strip('\n') + f'\n\ncheck("{t["fn"]} (reference)", _test_{t["fn"]}, {t["fn"]}_solution)', title=f'Solution for Task {i}: {t["title"]}'))
    if nb.get('explore'):
        cells.append(md('---\n## Experiments\n' + textwrap.dedent(nb.get('explore_md', 'These use the reference solutions, so they run even before you finish.')).strip()))
        cells.append(code(nb['explore']))
    if nb.get('takeaways'):
        cells.append(md('---\n## Takeaways\n' + textwrap.dedent(nb['takeaways']).strip()))
    doc = {'cells': cells, 'metadata': {'colab': {'provenance': [], 'name': nb['slug'] + '.ipynb'}, 'kernelspec': {'name': 'python3', 'display_name': 'Python 3'}, 'language_info': {'name': 'python'}}, 'nbformat': 4, 'nbformat_minor': 0}
    return path, doc, colab


def validate(doc, tasks):
    """Execute all code cells in order. Every learner check must print ⏳ and every reference check ✅."""
    ns, out = {}, io.StringIO()
    for c in doc['cells']:
        if c['cell_type'] != 'code':
            continue
        src = ''.join(c['source'])
        if any(l.lstrip().startswith(('%', '!')) for l in src.split('\n')):
            continue                                    # install cells: the validating environment is prepared beforehand
        with contextlib.redirect_stdout(out):
            exec(compile(src, '<cell>', 'exec'), ns)
    log = out.getvalue()
    problems = []
    for t in tasks:
        if f'⏳ {t["fn"]}:' not in log:
            problems.append(f'starter for {t["fn"]} did not report ⏳')
        if f'✅ {t["fn"]} (reference): all tests passed' not in log:
            problems.append(f'reference for {t["fn"]} did not pass')
    return problems, log
