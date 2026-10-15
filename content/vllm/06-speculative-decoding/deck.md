---
title: Speculative Decoding in vLLM
body:
  data-deck: Speculative decoding in vLLM
  data-home: ../index.html
  data-home-label: vLLM
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'proposer :: k draft tokens :: c'
  - 'target pass :: score k + 1 positions :: a'
  - 'rejection sampling :: accept a prefix :: b'
  - 'emit :: accepted + 1 :: e'
  loop: '3 -> 0 :: every decode step'
  caption: 'Concept and math: Inference deck 06.'
example:
  title: 'Worked example: expected tokens per pass'
  setup: 'Acceptance probability α per proposed token, k proposed tokens: expected tokens per target pass = (1 − α^(k+1)) / (1 − α) (Leviathan et al., 2023).'
  steps:
  - 'α = 0.5, k = 4: <b>1.94</b> tokens per pass.'
  - 'α = 0.7, k = 4: <b>2.77</b>.'
  - 'α = 0.9, k = 4: <b>4.10</b>.'
  - 'Notebook 05: the n-gram proposer on a repetitive code snippet produced 16 tokens in 10 target passes (1.6 tokens/pass) with k = 3.'
  result: Speed-up depends on acceptance, which depends on the proposer and the workload; overhead must be smaller than the saving.
traps:
  tricks:
  - 'n-gram needs no extra model. :: Great for edits, quoting, code.'
  - 'EAGLE / MTP heads. :: Higher acceptance on general text.'
  - 'Watch acceptance metrics. :: vllm:spec_decode_num_accepted_tokens_per_pos.'
  traps:
  - 'Large k with low acceptance. :: Wasted verification compute.'
  - 'Speculation at very high batch sizes. :: The GPU is no longer idle, so gains shrink.'
  - 'Mismatched draft tokenizer. :: Draft and target must share a vocabulary.'
papers:
- leviathan
- vllm_spec
- vllm_release
status: {label: current, reviewed: 2026-10-15, note: "v0.31.0 latest; v0.30-0.31 added more drafters on Model Runner V2"}
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">vLLM · 06</div>
    <h1>Speculative decoding in vLLM</h1>
    <p class="sub">How vLLM produces several tokens per target-model pass: proposers (n-gram, draft models, EAGLE, MTP, Medusa, suffix), verification with rejection sampling, and when it pays.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Decoding generates one token per forward pass and is memory-bound: the GPU reads all weights to produce a single token per request, leaving compute idle.</div>
      <div class="c"><b>Core idea</b>A cheap <b>proposer</b> guesses k tokens; the target model scores all of them in <b>one pass</b>; a <b>rejection sampler</b> accepts the longest valid prefix (plus one token of its own), so the output distribution is unchanged. In vLLM it is configured with <code>--speculative-config</code>, and the scheduler treats proposed tokens as more tokens to catch up.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Tokens per target pass

Expected tokens produced per target forward pass as a function of acceptance rate α and the number of proposed tokens k.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">acceptance α <input type="range" id="eA" min="0" max="0.98" step="0.02" value="0.7"> <output id="eAo"></output></label><label class="ctl">proposed k <input type="range" id="eK" min="1" max="10" step="1" value="4"> <output id="eKo"></output></label></div>
  <svg id="eSvg" viewBox="0 0 660 220" style="margin-top:10px" role="img" aria-label="Expected tokens per pass"></svg>
  <p class="readout" id="eOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why decoding leaves the GPU idle

::: cards grid3
### [d] Memory-bound
Each step reads every weight to make one token per request.

### [b] Sequential
Token t + 1 needs token t, so steps cannot be parallelised naively.

### [c] Latency
Per-token time sets user-visible speed in chat.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Does speculation change the output?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? With vLLM's rejection sampler, does speculative decoding change which tokens the model would generate?
- [ ] Yes, it trades quality for speed
- [x] No: the output distribution matches the target model's
- [ ] Only with temperature 0
- [ ] Only for n-gram proposals
> <b>B.</b> Rejection sampling accepts a proposal with probability min(1, p/q) and resamples otherwise, so outputs follow the target distribution exactly.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Proposers in v0.31.0

::: cards grid2
### [c] ngram
Copy continuations of earlier matching n-grams from the context. No extra model.

### [a] draft_model
A small model of the same family proposes tokens.

### [b] EAGLE / EAGLE-3 / MTP
Light heads on the target's hidden states (or built-in multi-token-prediction layers) propose tokens.

### [e] Medusa, suffix, others
Extra decoding heads; suffix decoding over previous outputs; plus custom classes.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Configuring it

<div class="visual"><pre style="margin:0;font:13px/1.55 'JetBrains Mono',monospace;white-space:pre-wrap">$ vllm serve meta-llama/Llama-3.1-8B-Instruct     --speculative-config '{"method": "ngram", "num_speculative_tokens": 4,&#10;                           "prompt_lookup_max": 4}'&#10;&#10;$ vllm serve <target>     --speculative-config '{"method": "eagle3", "model": "<eagle3 head>",&#10;                           "num_speculative_tokens": 3}'</pre></div>
<p class="caption">Method names from SpeculativeMethod in vllm/config/speculative.py (v0.31.0). See the vLLM speculative decoding docs for each method's options.</p>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it speeds things up

::: cards grid2
### [a] Free compute
Scoring k + 1 positions costs about the same as one in a memory-bound step.

### [e] Exactness
Rejection sampling keeps outputs identical in distribution.

### [b] Fits the scheduler
Proposed tokens are just extra tokens to catch up (num_tokens_with_spec).

### [c] Workload-dependent
Repetitive or predictable text gets high acceptance; creative text less.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Speculative decoding always helps."
> At large batch sizes the GPU is already compute-busy; overhead can outweigh gains.
:::

::: reveal myth
? "You need a separate draft model."
> n-gram, suffix and EAGLE/MTP methods avoid a full second model.
:::

::: reveal myth
? "More proposed tokens is better."
> Expected gain saturates at 1/(1 − α); extra proposals mostly get rejected.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Expected tokens per pass with α = 0.8 and k = 4?
- [ ] ≈ 1.8
- [x] ≈ 3.4
- [ ] ≈ 4.0
- [ ] 5
> (1 − 0.8⁵)/(1 − 0.8) ≈ <b>3.36</b>.
:::

::: reveal
? How does the vLLM scheduler handle speculative tokens?
> They count toward num_tokens_with_spec; the scheduler assigns budget so computed tokens catch up, verifying them in the same step.
:::

::: reveal
? When does n-gram speculation work well?
> When outputs repeat or copy context: code edits, summaries quoting the source, structured data.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">vLLM speculative decoding lets a proposer (n-gram, draft, EAGLE, MTP, …) guess k tokens that the target verifies in one pass with rejection sampling: same outputs, (1 − α^(k+1))/(1 − α) tokens per pass.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Decoding is memory-bound: each step reads all the weights to produce one token per request. Speculative decoding uses that idle compute. A cheap proposer, which in vLLM can be an n-gram lookup, a small draft model, EAGLE or multi-token-prediction heads, Medusa or suffix decoding, guesses a few tokens; the target model scores them all in one pass; and a rejection sampler accepts the longest valid prefix plus one token of its own, so the output distribution is unchanged. With acceptance alpha and k proposals you get one minus alpha to the k plus one, over one minus alpha, tokens per pass.</p></div>
    <div class="recap"><div><span><b>Problem:</b> one token per memory-bound pass.</span></div><div><span><b>Core idea:</b> propose k, verify in one pass, rejection-sample.</span></div><div><span><b>Config:</b> --speculative-config {"method": …}.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/vllm/05_ngram_speculation.ipynb" target="_blank" rel="noopener">05 · N-gram speculative decoding</a> <span style="color:var(--faint)">· 30 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/vllm/05_ngram_speculation.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../07-parallelism-and-quantization/index.html">07 · Parallelism and quantization →</a> · Previous: <a href="../05-prefix-caching/index.html">← 05</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
