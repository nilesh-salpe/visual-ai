"""Insert the Google Analytics tag (gtag.js) into every published HTML page.

Run last, after all other build steps (CI does this):  python3 tools/add_analytics.py
The tag goes right after <head>, between <!--x:ga--> markers, so re-running replaces it instead of duplicating it.
"""
import os, re

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GA_ID = 'G-67CZB0CXVD'
TAG = f'''<!--x:ga--><!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());

  gtag('config', '{GA_ID}');
</script><!--/x:ga-->
'''
SKIP = {'.git', 'tools', 'content', 'node_modules'}


def main():
    n = 0
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith('.')]
        for f in files:
            if not f.endswith('.html'):
                continue
            p = os.path.join(root, f)
            s = open(p, encoding='utf-8').read()
            t = re.sub(r'<!--x:ga-->.*?<!--/x:ga-->\n?', '', s, flags=re.S)
            m = re.search(r'<head[^>]*>\n?', t)
            if not m:
                print('no <head>:', os.path.relpath(p, REPO))
                continue
            t = t[:m.end()] + TAG + t[m.end():]
            if t != s:
                open(p, 'w', encoding='utf-8').write(t)
                n += 1
    print(f'analytics tag in place; {n} files updated')


if __name__ == '__main__':
    main()
