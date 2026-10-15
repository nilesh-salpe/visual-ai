---
name: deck-review
description: Review Visual AI decks for freshness and correctness, update outdated facts, and label techniques as current practice, recent trend, legacy, or research-only. Use when asked to review, refresh, audit or update decks, to find stale or outdated content, or to label what is used in production today.
---

# Deck review

Keep the decks on https://nilesh-salpe.github.io/visual-ai current: re-verify facts and pinned versions, fold in what changed, and label how each technique stands today.

## Labels

| Label | Badge | Use when |
|---|---|---|
| `current` | Current practice | widely used in production systems today |
| `trend` | Recent trend | new (roughly the last 18 months) and gaining adoption; details may still change |
| `legacy` | Legacy | superseded by something better; mostly found in older systems or kept for history |
| `research` | Research | promising results, but not common in production |

Two places to put them:

- **Deck level**, in the front matter of `content/<topic>/<slug>/deck.md`:
  ```yaml
  status: {label: current, reviewed: 2026-10-15, note: "short reason, one line"}
  ```
  The build shows a badge under the title-slide kicker and on the topic hub card. `reviewed` is the date of this review (always update it, even if nothing else changes).
- **Inline**, next to a technique in slide text: `[[legacy]]`, `[[trend]]`, `[[current]]`, `[[research]]`. Example: `Fixed thinking budgets (budget_tokens) [[legacy]]; adaptive thinking with an effort level [[current]]`. Use inline labels sparingly: only where a reader could otherwise mistake an old technique for today's practice, or a new one for settled practice.

Every `legacy`, `trend` or `research` label needs evidence: a primary source (paper, official docs, release notes, a lab's engineering post) that shows the change. If you cannot find one, do not label.

## Procedure

1. **Pick decks.** If the user named a topic or deck, use it. Otherwise list candidates:
   ```bash
   python3 tools/review_status.py --stale 90          # never reviewed, or reviewed > 90 days ago
   python3 tools/review_status.py --topic <topic>
   ```
   Review a topic at a time (its decks cross-reference each other). Tell the user which decks you will review before starting a large batch.

2. **Read the deck source**, `content/<topic>/<slug>/deck.md` (it is the source of truth; edit it directly). Note every claim that can go stale: version pins, API parameters and defaults, benchmark numbers and leaderboards, "state of the art" statements, product names, prices and limits.

3. **Re-verify against primary sources.** Use the `trusted-sources` skill (`.claude/skills/trusted-sources/`): its tier rules decide what counts as evidence, and `sources.yml` lists where to look.
   - Pinned versions: check the latest release (`curl -s https://pypi.org/pypi/<pkg>/json`, `gh api repos/<owner>/<repo>/releases`); read the changelog for changed defaults, removals and deprecations.
   - API facts (Claude, OpenAI, MCP, A2A, Kubernetes, Slurm…): fetch the current official docs page and compare parameter names, defaults and limits.
   - Techniques: search for what has replaced or extended them since the deck was written (papers and lab engineering posts first; blogs only as pointers to primary sources).
   - Numbers: keep the original source's number unless the source itself was corrected; add newer results as additional facts with their own source rather than overwriting history.
   - Run `python3 tools/check_papers.py` so every cited link still resolves.

4. **Update the deck.**
   - Fix outdated facts in place; when something changed, say what changed and when (for example "deprecated in 4.6, rejected from 4.7").
   - Add inline labels where they help; set the deck-level `status` with today's date and a one-line note.
   - Add new sources to `content/papers.yml` (unique key; the build fails on duplicate keys) and to the deck's `papers:` list.
   - Keep the deck's template and structure: agent decks use Problem → Core idea → High-level design → Low-level design → Trade-offs → Failure modes → Production; LLM decks use the 9-beat template; system-design decks follow their walkthrough sequence. Keep content, markup and style separate (`::: diagram`, `::: table`, `::: code`; no inline styles). See `content/README.md`.
   - Never use the word "interview" in any visual. Expand acronyms only through `shared/glossary.json`.

5. **Rebuild and verify.**
   ```bash
   python3 tools/build_decks.py <topic> && python3 tools/build_indexes.py && python3 tools/build_home.py && python3 tools/build_site_extras.py
   python3 tools/review_status.py --write
   python3 tools/decks/acronyms.py lint */[0-9][0-9]-*/index.html
   python3 tools/check_papers.py
   ```
   The build fails on leaked Markdown (`:::` text, accidental code blocks) and duplicate paper keys. Open changed slides at phone width (headless Chrome screenshots) and check for errors and overflow. If a deck has a Colab notebook whose facts changed, update and re-validate it (`tools/notebooks/build_<topic>.py`).

6. **Report and commit.** Summarise per deck: what was outdated, what changed, labels added (with the evidence), and anything you could not verify. Commit on `main` with a message listing the reviewed decks, ending with the co-author line the session specifies, and push only when the user has asked for it.

## Judgement guide

- Prefer adding a short "what changed" sentence over deleting history: the original idea is often still the best way to learn the concept (for example MQA → GQA; label MQA `legacy` only if production models no longer use it).
- A technique is `current` if major open models or production systems use it now, not merely because it is recent.
- `trend` expires: on the next review, promote it to `current` or drop the label.
- When sources disagree, say so on the slide and cite both.
