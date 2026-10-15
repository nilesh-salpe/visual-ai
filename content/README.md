# Deck sources

Every deck is a folder: `content/<topic>/<slug>/deck.md` (text) and, if it has interactive parts, `widget.js`.
Run `python3 tools/build_decks.py` (or push to `main`: a GitHub Action rebuilds the site) to regenerate
`<topic>/<slug>/index.html`. Never edit the generated HTML directly.

## deck.md

```markdown
---
title: KV Cache                                # browser tab title
body: {data-deck: KV cache, data-home: ../index.html, data-home-label: Inference}
styles: [../../shared/deck.css, ../../shared/learn.css]
scripts: [../../shared/deck.js, ../../shared/learn.js]
glance:                                        # "At a glance" diagram, placed where {{glance}} appears
  steps: ['new token :: embedding of the latest token :: f', 'q, k, v :: computed for this token only :: a']
  loop: '1 -> 0 :: label under the loop-back arrow'    # optional
  caption: One sentence under the diagram.
example: {title: ..., setup: ..., steps: [...], result: ...}   # Worked example slide
traps: {tricks: ['Rule :: explanation'], traps: ['Mistake :: why it is wrong']}
papers: [vllm, gqa]                            # keys into content/papers.yml
---

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Slide title

A paragraph. Markdown and inline HTML both work.
{: .lede}

::: cards grid3
### [d] Card title
Card text. Colours: a, b, c, d, e.
:::

::: quiz
? Question text
- [ ] Wrong option
- [x] Right option
> Explanation shown after answering.
:::

::: reveal myth
? "A common misconception."
> Why it is wrong.
:::

::: deep Title of the "In detail" box
Markdown content.
:::

{{glance}}

<!-- slide id="s-example" from="example" -->      # slides built from the front matter
<!-- slide id="s-traps" from="traps" -->
<!-- slide id="s-papers" from="papers" -->
<!-- slide raw -->                                # raw HTML slide, used verbatim
```

Colours for diagram steps and cards: `a` teal, `b` orange, `c` purple, `d` red, `e` green, `f` grey.
Acronyms are expanded automatically at their first use in each deck from `shared/glossary.json`; add new
terms there. Papers live once in `content/papers.yml` and are referenced by key.

## Agent decks (Visual Agents)

Decks under `content/agent-*/` use a different template: title → `s-problem` (1 · Problem) → `s-core` (2 · Core idea) → `s-hld` (3 · High-level design) → `s-lld` (4 · Low-level design) → `s-trade` (5 · Trade-offs) → `s-fail` (6 · Failure modes) → `s-prod` (7 · Challenges in production) → `s-papers`.
Agent decks keep content, markup and style apart: `deck.md` holds only text and data, the build renders it, and all styling is in `shared/deck.css` and `shared/learn.css` (no inline styles).

* **Title slide**: `<!-- slide from="title" -->`, rendered from the front-matter `intro` (`kicker`, `h1`, `sub`, `problem`, `core`, `hint`).
* **Diagrams**: a `::: diagram 660x300` block in YAML: `nodes` (`at: [x, y, w, h]`, `text`, `sub`, `color` a-e or f, `step`), `edges` (`from`, `to`, `label`, `step`, `style: dash | back`) and `steps` (one caption per step). `tools/decks/diagram.py` draws the SVG and warns when an arrow crosses a box it does not connect; `shared/diagram.js` (listed in `scripts`) shows the full diagram on load and steps through it.
* **Tables**: a Markdown pipe table inside `::: table`.
* **Code**: `::: code` shows its body verbatim.
* **Notebooks**: `::: colab build-it/<topic>/<notebook>.ipynb` with a one-line description as the body.
* **Widgets**: controls as HTML in `deck.md` (classes only), behaviour in `widget.js`.

## Review status and labels

Decks carry a review status in front matter, `status: {label: current | trend | legacy | research, reviewed: YYYY-MM-DD, note: "..."}`, shown as a badge on the title slide and the topic hub. Inline markers `[[current]]`, `[[trend]]`, `[[legacy]]`, `[[research]]` label individual techniques. `python3 tools/review_status.py` lists decks by review age and writes `status/index.html`. The review procedure is the `deck-review` skill and the source rules are the `trusted-sources` skill, both in `.claude/skills/`.
