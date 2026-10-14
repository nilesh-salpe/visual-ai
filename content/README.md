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
