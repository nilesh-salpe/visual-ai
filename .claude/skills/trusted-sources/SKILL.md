---
name: trusted-sources
description: The list of trusted sources for Visual AI decks (arXiv and peer-reviewed venues, frontier AI labs, NVIDIA, framework and infrastructure docs, standards bodies, benchmarks) with trust tiers and rules for verifying a fact. Use whenever researching, writing, fact-checking or reviewing deck content, choosing a citation, or deciding whether a source is good enough.
---

# Trusted sources

Every number, default, version and claim on the site must come from a source on this list (or one of equal standing), checked at the time of writing. The machine-readable list is `sources.yml` in this folder; this page explains how to use it.

## Trust tiers

| Tier | What | How to use |
|---|---|---|
| **1 · Primary** | the paper itself, official documentation, specifications, release notes, source code, a lab's own engineering or research post about its own work | cite directly; quote numbers exactly as published |
| **2 · Reputable secondary** | well-known analysis from established researchers or organisations (e.g. Epoch AI, the JAX scaling book, SemiAnalysis for hardware) | use for context and estimates; prefer a tier-1 source for any number you headline |
| **3 · Pointers only** | news articles, press coverage, aggregators, social media, personal blogs, AI-generated summaries | use only to find the tier-1 source, never as the citation |

Do not cite: content farms and SEO blogs, unattributed Medium posts, Q&A sites, AI chat answers, or a vendor's claims about a competitor.

## Verification rules

1. **Go to the original.** For a paper, read the arXiv abstract page (and the PDF or HTML for numbers in tables); for an API, the current official docs page; for a default, the release notes or source code of the pinned version.
2. **Pin versions.** Software facts are true for a version: record it in the deck ("vLLM v0.31.0", "LangGraph 1.2.15", "MCP revision 2026-07-28") and check PyPI or GitHub releases for the latest.
3. **Prefer the newest authoritative statement.** If docs and an older paper disagree on a product default, the current docs win for "how it works now"; the paper stays the source for its own experiments. Say so when they differ (e.g. the LangGraph recursion-limit default).
4. **Quote numbers with their conditions.** Model, dataset, setting and date ("PaLM 540B, GSM8K, 8 exemplars, 2022").
5. **Deprecation vs usage.** A maintainer's own official notice (release notes, changelog, docs or a deprecation warning in its source code) is enough to call that maintainer's feature *deprecated* or *removed*. Claims about the wider world (*outdated*, *superseded across the industry*, *no longer used in production*) need **two independent tier-1 sources**.
6. **Record it.** Add the source to `content/papers.yml` (unique key; title, authors, venue, year, URL, a one-line summary and the key number) and run `python3 tools/check_papers.py`.
7. **Access problems.** Some sites (OpenAI, ACM Digital Library, Microsoft Research, LMArena, MLCommons) return 403 to scripts. Read them in a browser if needed, and cite a stable alternative that the link checker can reach: the arXiv version of a paper, the GitHub repository, or the official docs mirror.

## Where to look first (summary of sources.yml)

- **Papers:** arXiv; OpenReview (ICLR and others); proceedings of NeurIPS, ICML (PMLR), ACL Anthology (ACL, EMNLP, NAACL), USENIX (OSDI, NSDI, ATC), ACM (SOSP, KDD, SIGIR), MLSys; Transformer Circuits Thread.
- **Frontier labs:** Anthropic (research, engineering, news, platform and Claude Code docs), OpenAI (research, developer docs, cookbook on GitHub), Google DeepMind and Google Research, Meta AI (FAIR, Llama), Microsoft Research, Mistral, DeepSeek (GitHub and arXiv), Qwen, Allen Institute for AI (OLMo, Tülu), Hugging Face.
- **NVIDIA:** developer technical blog, documentation hub (CUDA, NCCL, cuDNN, TensorRT-LLM, NeMo, Megatron-Core), data-center GPU datasheets for hardware numbers, GitHub (Megatron-LM, TensorRT-LLM).
- **Frameworks and serving:** PyTorch (docs, blog), JAX, vLLM, SGLang, Hugging Face Transformers, DeepSpeed, Ray, LangChain and LangGraph, Temporal, Kubernetes and its SIG projects (Kueue, JobSet), Slurm (SchedMD).
- **Standards and security:** Model Context Protocol spec, A2A spec, IETF RFCs, NIST, OWASP GenAI.
- **Benchmarks and measurement:** LMArena, SWE-bench, MLCommons (MLPerf), Epoch AI data.
- **Releases:** PyPI JSON API, GitHub releases (`gh api repos/<owner>/<repo>/releases`).

When a needed source is not on the list, apply the tier rules; if it is tier 1 and likely to be reused, add it to `sources.yml`.
