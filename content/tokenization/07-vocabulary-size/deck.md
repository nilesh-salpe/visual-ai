---
title: Vocabulary Size
body:
  data-deck: Vocabulary size trade-offs
  data-home: ../index.html
  data-home-label: Tokenization
styles:
- ../../shared/deck.css
- ../../shared/learn.css
- ../tk.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
- ../data/examples.js
- ../tk.js
glance:
  steps:
  - 'bigger vocabulary :: more merges :: f'
  - 'fewer tokens :: per text :: a'
  - 'more context, less compute :: per document :: e'
  - 'more parameters :: embedding + output head :: d'
  caption: Compression buys context and effective data; every entry costs 2·d parameters with untied embeddings.
example:
  title: 'Worked example: the parameter bill vs the compression gain'
  setup: Llama 3 moved from 32K to 128,256 tokens with d = 4,096 (8B model, untied input and output matrices).
  steps:
  - 'Embedding + output head at 32,000: 2 × 32,000 × 4,096 = <b>0.26B</b>.'
  - 'At 128,256: 2 × 128,256 × 4,096 = <b>1.05B</b> (+0.79B).'
  - 'Compression on English: 3.17 → 3.94 characters per token = <b>24%</b> more text per token.'
  - The same 8K context now holds ≈ 32,276 characters instead of 25,969.
  result: For large models the extra embedding parameters are a small fraction, and the compression gain applies to every token of training and inference.
traps:
  tricks:
  - 'Embedding params = V × d (× 2 if untied). :: GPT-2 small: 50,257 × 768 ≈ 38.6M.'
  - 'Characters per token. :: The practical compression metric.'
  - 'Pad V to a multiple of 64 or 128. :: Helps matmul efficiency.'
  traps:
  - 'Huge vocabularies in small models. :: The embedding can dominate the parameter budget.'
  - 'Rare-token undertraining. :: Tokens seen rarely in training get poor embeddings.'
  - 'Comparing perplexity across vocabularies. :: Per-token losses aren''t comparable; use bits per byte or per character.'
papers:
- llama3
- llama2
- gpt2
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Tokenization for LLMs · 07</div>
    <h1>Vocabulary size trade-offs</h1>
    <p class="sub">How many tokens should a vocabulary have? Bigger vocabularies make sequences shorter but add parameters, and the benefit depends heavily on the language.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>The vocabulary size V sets sequence length, embedding and output-layer size, and how well each language is covered, all at once.</div>
      <div class="c"><b>Core idea</b>Choose V to balance <b>compression</b> (characters per token) against <b>parameters</b> (V × d), and measure it on the languages you care about.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## One number, many consequences

::: cards grid2
### [a] Sequence length
Fewer, longer tokens mean shorter sequences: less attention compute and more text in the context window.

### [b] Parameters
The input embedding and the output layer each have V × d weights.

### [c] Coverage
Which languages, scripts and domains get compact tokens depends on what the vocabulary was trained on.

### [e] Training signal
Every token in the vocabulary needs enough training examples to learn a good embedding.
:::

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Both extremes hurt

<div class="vs">
  <div class="card d"><h3>Too small</h3><p>Text is split into many short tokens: longer sequences, more compute per sentence, and less text per context window, especially for languages the vocabulary under-serves (deck 09).</p></div>
  <div class="card b"><h3>Too large</h3><p>Embedding and output matrices grow with V, and rare tokens get few training updates. Under-trained tokens that are nearly absent from training data can make models misbehave ("glitch tokens", Land &amp; Bartolo 2024; deck 10).</p></div>
</div>

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What did Llama 3 gain?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Llama 3 moved from Llama 2's 32K-token vocabulary to 128K tokens. What benefit does the paper report?
- [ ] Fewer total parameters
- [x] Better compression (more characters per token), so the model "reads" more text for the same compute
- [ ] A faster softmax
- [ ] No need for BPE any more
> <b>B.</b> On a sample of English data, characters per token rose from <b>3.17 to 3.94</b>, which "enables the model to 'read' more text for the same amount of training compute". Adding 28K non-English tokens also improved compression and downstream performance in those languages (Llama 3 paper, §3.2).
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Compression vs parameters

<div class="eq">embedding params = V × d &nbsp;&nbsp;(×2 if the output layer isn't tied to the input embedding)</div>

<div class="eq">tokens for a text ≈ characters ÷ (characters per token)</div>

<div class="takeaway">A larger V raises characters per token, but with diminishing returns once common words are already single tokens. Its cost in parameters grows linearly.</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Measured: does a bigger vocabulary compress better?

Real token counts from three tiktoken encodings (about 50K, 100K and 200K tokens) on this guide's sample texts: a 408-character English paragraph and one short Hindi sentence.
{: .lede}

<div class="visual">
  <div class="grid2">
    <div><h3>English paragraph: characters per token</h3><div id="enBars"></div></div>
    <div><h3>Hindi sentence: characters per token</h3><div id="hiBars"></div></div>
  </div>
  <p class="readout" id="cmpOut" style="margin-top:10px"></p>
</div>

<p class="caption">Measured on two small samples, so this illustrates the trend rather than serving as a benchmark. The Hindi sentence is "आज मौसम अच्छा है।" ("The weather is nice today.").</p>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## The parameter bill

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">Vocabulary V <input type="range" id="vV" min="13" max="18" step="0.05" value="17"> <output id="vVo"></output></label>
    <label class="ctl">Model width d <select id="vD"><option>768</option><option>2048</option><option selected>4096</option><option>8192</option></select></label>
    <label class="ctl">Total model <select id="vT"><option value="1e9">1B</option><option value="8e9" selected>8B</option><option value="70e9">70B</option></select></label>
    <div class="seg" id="vTie"><button data-v="1">tied in/out</button><button data-v="2" class="on">separate in/out</button></div>
  </div>
  <div class="grid3" style="margin-top:14px">
    <div class="stat"><div class="num" id="vPar"></div><div class="lbl">embedding + output parameters</div></div>
    <div class="stat"><div class="num" id="vPct"></div><div class="lbl">share of the total model</div></div>
    <div class="stat"><div class="num" id="vCtx"></div><div class="lbl">English characters per 8K-token context (est.)</div></div>
  </div>
</div>

<p class="caption">Characters per token are interpolated from the measured English points (gpt2, cl100k, o200k) and are approximate. Parameter counts are exact arithmetic for the chosen V and d.</p>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why the trade-off resolves the way it does

::: cards grid2
### [e] Compression buys effective data and context
Llama 3: 3.17 → 3.94 characters per token on English lets the model "read" more text for the same compute.

### [a] Parameters are cheap at scale
V × d is a large share of a small model but a small share of a large one. That's why large models can afford 100K–200K vocabularies.

### [b] Where to spend tokens
Llama 3 added 28K tokens for non-English languages, which improved their compression with no effect on English tokenization.

### [c] Diminishing returns in English
On the guide's sample, going from 50K to 200K tokens barely changes English, while the Hindi sentence shrinks from 27 tokens to 5.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "A bigger vocabulary is free."
> Each of the embedding and output matrices has V × d weights. At V = 128,000 and d = 4,096 that is about <b>524M parameters</b> per matrix.
:::

<div class="quiz myth">
  <p class="qq">"Doubling the vocabulary halves the token count."</p>
  <button class="reveal">Why is this wrong?</button>
  <div class="why">Returns diminish fast. On the English sample: 81 tokens (gpt2) → 79 (cl100k_base) → 79 (o200k_base). Most of the gain lands on under-served languages.</div>
</div>

::: reveal myth
? "Vocabulary size only matters for English text."
> It matters <b>most</b> for other languages and scripts (Llama 3's +28K multilingual tokens; deck 09).
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? GPT-2 small has d = 768 and V = 50,257. How many input-embedding parameters is that?
- [ ] ≈ 3.9M
- [x] ≈ 38.6M
- [ ] ≈ 386M
- [ ] ≈ 3.9B
> 50,257 × 768 ≈ <b>38.6M</b>.
:::

::: quiz
? How is Llama 3's 128K vocabulary made up?
- [ ] 128K SentencePiece unigram pieces
- [x] 100K tiktoken tokens + 28K extra non-English tokens
- [ ] 32K Llama 2 tokens × 4
- [ ] Bytes only
> <b>100K tokens from tiktoken plus 28K additional tokens</b> for non-English languages (§3.2).
:::

<div class="quiz ">
  <p class="qq">Why does better compression effectively lengthen the context window?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">The window is measured in <b>tokens</b>. More characters per token means more text fits into the same number of tokens.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Vocabulary size trades compression against parameters. Large models can afford 100K–200K tokens, and the extra tokens help non-English text far more than English.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Vocabulary size V sets how many characters each token covers and how big the embedding and output layers are (V × d each, unless tied). Too small means long sequences, more compute and less text per context window. Too large adds parameters and rarely seen, under-trained tokens. Llama 3 went from 32K to 128K tokens (100K from tiktoken plus 28K multilingual) and improved English compression from 3.17 to 3.94 characters per token. In my measurements, larger vocabularies mostly help under-served languages.</p></div>

<div class="recap"><div><span><b>Problem:</b> V controls sequence length, parameter count and language coverage all at once.</span></div><div><span><b>Core idea:</b> balance characters per token against V × d, and measure on your target languages.</span></div></div>

<p class="start-hint">Next: <a href="../08-tokenizers-in-llms/index.html">08 · Tokenizers in real LLMs →</a> · Previous: <a href="../06-many-tokenizations/index.html">← 06</a> · <a href="../index.html">All decks</a> · <a href="../playground/index.html">Playground</a></p>

<!-- slide id="s-papers" from="papers" -->
