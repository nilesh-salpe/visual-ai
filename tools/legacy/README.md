# Legacy generators (read-only history)

Before October 2026 the decks were generated from Python spec files (`gen_*.py`, `*_a.py`/`*_b.py`,
`extras_*.py`) and, for the hand-written GPU and Transformer decks, augmented in place (`augment.py`).
`migrate_to_md.py` converted every deck to `content/<topic>/<slug>/deck.md` + `widget.js`, and the rebuilt
pages were verified identical (visible text and element structure) to the originals.

**Do not edit these files to change a deck.** Edit `content/` and run `tools/build_decks.py` instead.
They are kept so the history of how each deck was produced stays readable.
