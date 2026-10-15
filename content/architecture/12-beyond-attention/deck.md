---
title: 'Beyond Attention: SSMs and Hybrids'
body:
  data-deck: 'Beyond attention: SSMs and hybrids'
  data-home: ../index.html
  data-home-label: Architecture
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'softmax attention :: cache grows with context :: d'
  - 'fixed-size state :: linear attention · SSM :: a'
  - 'selective update :: keep or forget per token :: b'
  - 'recall gap :: copying, lookup :: c'
  - 'hybrid :: a few attention layers :: e'
  caption: Cheap fixed-size memory for most layers; exact attention where recall needs it.
example:
  title: 'Worked example: decode memory in a 3 : 1 hybrid'
  setup: 'Qwen3-Next-80B-A3B (model card): 48 layers, 12 with gated attention (2 KV heads of dimension 256) and 36 with Gated DeltaNet (32 value heads, head dimension
    128). BF16, one sequence of 262,144 tokens.'
  steps:
  - 'KV cache per token per attention layer: 2 (K and V) × 2 heads × 256 × 2 bytes = 2,048 bytes.'
  - 'If all 48 layers were attention: 48 × 2,048 = 96 KiB per token, so <b>24 GiB</b> for 262,144 tokens.'
  - 'With 12 attention layers: 24 KiB per token, so <b>6 GiB</b>: a quarter, because only a quarter of the layers cache keys and values.'
  - 'The 36 DeltaNet layers each keep a state of 32 × 128 × 128 values: about 36 MiB in total in BF16, the same at 1K or 262K tokens.'
  result: Memory at long context is set by the attention layers; the linear layers add a small constant. (Our calculation from the published configuration.)
traps:
  tricks:
  - 'State, not cache. :: A linear or SSM layer stores a fixed-size matrix per layer; an attention layer stores K and V for every token.'
  - 'Count the attention layers. :: In a hybrid, KV-cache memory scales with the number of full-attention layers.'
  - 'Recall is the hard part. :: Zoology: 82% of the perplexity gap between gated convolutions and attention came from associative recall.'
  traps:
  - '"Attention-free" means "no attention needed". :: Pure SSMs lagged transformers on five-shot MMLU, phonebook lookup and long-context reasoning at 8B (Waleffe
    et al.).'
  - 'Assuming quadratic cost dominates. :: At inference the pain is KV-cache memory and bandwidth, which grow linearly per token, not the N² of training.'
  - 'Comparing models without matching data. :: Architecture claims need the same data and token budget; Waleffe et al. trained all 8B variants on the same 3.5T tokens.'
papers:
- linear_attn
- s4
- mamba
- mamba2
- rwkv
- retnet
- gated_deltanet
- zoology
- repeat_after_me
- mamba_hybrid
- jamba
- minimax01
- nemotronh
- kimi_linear
- qwen3next_card
status:
  label: trend
  reviewed: '2026-10-15'
  note: Hybrid linear/SSM + attention stacks shipped in several open models in 2024–2025; attention-free LLMs remain research.
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">The Modern LLM · 12</div>
    <h1>Beyond attention: state space models, linear attention and hybrids</h1>
    <p class="sub">Layers that keep a fixed-size state instead of a growing KV cache: linear attention, selective state space models (Mamba, Mamba-2), the gated delta rule, why they struggle to copy and recall, and the hybrid stacks now shipping in open models.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Attention compares each token with every earlier token. Training cost grows quadratically with sequence length, and at inference every attention layer caches keys and values for every past token, so long contexts, long reasoning traces and agents make decoding memory-bound and expensive.</div>
      <div class="c"><b>Core idea</b>Replace most attention layers with layers that keep a <b>fixed-size state</b> updated once per token: <b>linear attention</b> (a running sum of key-value outer products), <b>selective state space models</b> such as <b>Mamba</b> (an input-dependent recurrence), and <b>delta-rule</b> layers such as <b>Gated DeltaNet</b> (overwrite the value stored for a key, decay the rest). A fixed state cannot hold every token exactly, so these layers are weak at <b>copying and in-context recall</b>. Shipping models are therefore <b>hybrids</b>: mostly linear or SSM layers plus a few full-attention layers (1 in 4 to 1 in 8).</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Attention gets expensive as context grows

Long documents, long reasoning traces and agents that run for hundreds of turns all push context lengths up. Attention's costs grow with them.
            {: .lede}

::: cards grid3
### [d] Quadratic training cost
Each token attends to every earlier token, so compute per sequence grows with N².

### [b] A cache that grows
At inference each attention layer stores keys and values for every past token; memory per sequence grows linearly with context.

### [c] Decoding is memory-bound
Each new token re-reads the whole KV cache, so long contexts lower throughput and the batch size that fits (KV cache deck).
:::

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Earlier fixes kept full attention

::: cards grid3
### [d] Fewer KV heads
GQA and MLA shrink the cache by a constant factor; it still grows with every token.

### [b] Local windows
Sliding-window attention caps memory, but a layer cannot see past its window.

### [c] Classic RNNs
A fixed-size state is cheap at inference, but LSTMs train sequentially and lagged transformers in quality.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What does a fixed-size state lose?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? In Zoology, a 70M-parameter attention model beat a 1.4B-parameter gated-convolution model on one task. Which kind?
- [ ] Arithmetic
- [x] Associative recall: retrieving the value paired with a key earlier in the context
- [ ] Sentiment classification
- [ ] Predicting common words
> **B.** A fixed-size state must compress the past, so exact lookup of an earlier token is hard; attention reads it directly. Recall explained 82% of the perplexity gap on the Pile.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## A fixed-size state, updated selectively

::: cards grid2
### [f] Linear attention
Replace softmax(q·k) with a kernel φ(q)·φ(k). Attention becomes a running sum S ← S + φ(k)vᵀ read as φ(q)ᵀS: parallel in training, an RNN at inference (up to 4000× faster autoregressive prediction on very long sequences, Katharopoulos et al.). RWKV and RetNet are related designs.

### [a] Selective SSMs (Mamba)
Structured state space models (S4) with parameters that depend on the input, so each token decides what to keep or forget. Mamba: 5× the generation throughput of transformers; Mamba-3B matched transformers twice its size. Mamba-2 (state space duality) is 2 to 8× faster.

### [b] Delta rule and gating
Gated DeltaNet overwrites the value stored for a key (the delta rule) and decays old memory (gating); it beat Mamba-2 and DeltaNet on language modelling, in-context retrieval and long-context tasks.

### [e] Hybrids
Keep a few full-attention layers for exact recall. An 8B Mamba-2-Hybrid (24 Mamba-2, 4 attention, 28 MLP layers) beat a matched 8B transformer on all 12 standard tasks (+2.65 points) and is predicted to generate up to 8× faster.
:::

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Memory at long context <span class="ill">calculator</span>

<div class="visual"><div class="controls"><label class="ctl">context (log₂ tokens) <input type="range" id="baN" min="10" max="20" step="1" value="18"> <output id="baNo"></output></label><label class="ctl">attention layers <input type="range" id="baR" min="0" max="8" step="1" value="4"> <output id="baRo"></output></label></div><div class="bars"><div id="baBars"></div></div><p class="readout" id="baOut"></p></div>

Set "attention layers" to 1 for a standard transformer, 4 for Qwen3-Next and Kimi Linear, 8 for Jamba and MiniMax-01, and 0 for a pure fixed-state model.

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Hybrids in released models

::: table
| Model | Layers | Linear : full attention |
|---|---|---|
| Jamba (AI21, 2024) | Mamba + attention, with MoE | 7 : 1; 256K context |
| MiniMax-Text-01 (2025) | lightning (linear) attention + softmax attention, MoE, 456B total / 45.9B active | 7 : 1; 1M tokens in training, 4M at inference |
| Nemotron-H 8B, 56B (NVIDIA, 2025) | Mamba-2 + attention + FFN | about 8% attention (4 of 52 layers in 8B); up to 3× faster inference |
| Qwen3-Next-80B-A3B (2025) | Gated DeltaNet + gated attention, MoE | 3 : 1; 10× throughput beyond 32K tokens vs Qwen3-32B |
| Kimi Linear 48B-A3B (2025) | Kimi Delta Attention + MLA | 3 : 1; KV cache up to 75% smaller, up to 6× decoding throughput at 1M |
:::

Hybrid stacks of linear or SSM layers with a few attention layers [[trend]] have moved into released open models since 2024. Fully attention-free language models [[research]] still trail on copying and in-context recall.

::: deep Why a fixed state cannot copy everything
Jelassi et al. prove that a two-layer transformer can copy strings of length exponential in its size, while any model with a fixed-size state is limited by that state, and confirm it empirically: transformers learned copying and retrieval from context far more efficiently. Zoology found the same gap on real language (associative recall) and showed that adding sparse, input-dependent attention closed 97.4% of it.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why hybrids work

::: cards grid2
### [a] Most tokens need a summary
Much of language modelling needs a compressed running summary of the past, which a fixed state provides cheaply.

### [c] Some tokens need exact lookup
Copying, retrieval from documents and few-shot examples need attention; a few layers are enough to supply it.

### [b] Decoding is bound by memory
Cutting KV-cache memory 4 to 8 times raises the batch size and throughput at long context; Kimi Linear reports up to 6× decoding throughput at 1M tokens.

### [e] They train like transformers
Linear attention, SSD (Mamba-2) and Gated DeltaNet have parallel or chunkwise algorithms for GPUs; the recurrence is only used when generating.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Mamba replaced transformers."
> The released models in the table keep some full attention. At 8B, pure Mamba and Mamba-2 lagged transformers on tasks needing copying or in-context learning (Waleffe et al.).
:::

::: reveal myth
? "Linear attention is just a faster approximation of attention."
> It changes what the model can do: its memory is a fixed-size summary, so exact recall of a distant token is no longer guaranteed.
:::

::: reveal myth
? "Recurrent layers cannot be trained in parallel."
> Linear attention, Mamba-2 (SSD) and Gated DeltaNet all train with parallel or chunkwise algorithms; only generation runs step by step.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Why does decode memory stay constant for a Mamba or linear-attention layer?
- [ ] It drops old tokens from the context
- [x] It keeps a fixed-size state updated at every token, instead of keys and values for every token
- [ ] It quantizes the KV cache
- [ ] It recomputes attention from scratch
> **B.** The state has the same size at 1K or 1M tokens; information about old tokens survives only as far as the state can hold it.
:::

::: reveal
? Why do hybrid models keep any full-attention layers?
> For exact recall: copying, looking up a value given a key, using in-context examples and retrieving from long documents, where fixed-state layers are weak.
:::

::: reveal
? In Qwen3-Next, what share of layers use full attention, and what does that do to the KV cache?
> 12 of 48 (1 in 4), so the KV cache is a quarter of an all-attention model with the same attention configuration; the DeltaNet layers add a small fixed state.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Swap most attention layers for fixed-size-state layers to make long context cheap, and keep a few attention layers so the model can still look things up exactly.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Attention's KV cache grows with every token, which makes long contexts memory-bound. Linear attention, selective state space models (Mamba) and gated delta-rule layers keep a fixed-size state instead, so decode memory is constant per layer and throughput rises (Mamba reported 5×). The cost is exact recall: fixed-state models lag on copying, lookup and in-context learning. Hybrids fix this with a few full-attention layers: an 8B Mamba-2-Hybrid beat a matched transformer on 12 standard tasks, and Jamba, MiniMax-01, Nemotron-H, Qwen3-Next and Kimi Linear all ship hybrid stacks with one attention layer per 4 to 8 layers.</p></div>
    <div class="recap"><div><span><b>Problem:</b> the KV cache grows with every token</span></div><div><span><b>Fixed state:</b> linear attention, Mamba, Gated DeltaNet</span></div><div><span><b>Weakness:</b> copying and in-context recall</span></div><div><span><b>Practice:</b> hybrids: 1 attention layer in 4 to 8</span></div></div>
    <p class="start-hint">You've finished the series. <a href="../../build-it/index.html">See all Build-it notebooks →</a> · Previous: <a href="../11-putting-it-together/index.html">← 11</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
