"""Apply extras to the hand-written GPU and Transformer decks, then expand acronyms. Idempotent.
    python3 tools/decks/apply_augment.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from augment import augment
from acronyms import process
from tool import REPO
import extras_gpu, extras_transformer

for topic, mod in [('gpu', extras_gpu), ('transformer', extras_transformer)]:
    for slug, spec in mod.EXTRAS.items():
        f = os.path.join(REPO, topic, slug, 'index.html')
        html = augment(open(f).read(), spec)
        html, _ = process(html)
        open(f, 'w').write(html)
        print('augmented', topic, slug)
