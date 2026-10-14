---
title: Multilingual Cost
body:
  data-deck: Multilingual cost
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
  - 'training data mix :: mostly English :: f'
  - 'merges follow data :: English pieces get long :: c'
  - 'other scripts :: stay split into bytes :: b'
  - 'more tokens :: cost, latency, less context :: d'
  caption: 'Same meaning, different bill: the tokenization premium.'
example:
  title: 'Worked example: "The weather is nice today" in nine languages'
  setup: Token counts for the same sentence, from tiktoken.
  steps:
  - 'English: GPT-2 6, o200k_base 6 tokens.'
  - 'Hindi: GPT-2 <b>27</b> (4.5× English); o200k_base <b>5</b>.'
  - 'Russian: GPT-2 <b>27</b> (4.5×); o200k_base 6.'
  - 'Worst premium with GPT-2 here: 4.5×; with o200k_base: 1.0×.'
  result: A larger, more multilingual vocabulary shrinks the premium a lot; Petrov et al. measured gaps of up to 15× across languages.
traps:
  tricks:
  - 'Premium = tokens(lang) / tokens(English). :: For the same meaning.'
  - 'Same window, less text. :: A 3× premium means a third of the content fits.'
  - 'Bigger multilingual vocabularies help. :: Llama 3 added 28K non-English tokens.'
  traps:
  - '"Byte-level is fair." :: Byte and character models still show over 4× differences.'
  - 'Per-token pricing as equal. :: Users of some languages pay several times more for the same content.'
  - 'Judging by one sentence. :: Measure on a representative corpus per language.'
papers:
- petrov
- byt5
- llama3
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Tokenization for LLMs · 09</div>
    <h1>The multilingual token tax</h1>
    <p class="sub">The same sentence can cost very different numbers of tokens depending on its language, which affects price, latency and how much fits in context (Petrov et al., 2023).</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Tokenizers trained mostly on English text split other languages, especially non-Latin scripts, into many more tokens.</div>
      <div class="c"><b>Core idea</b>Measure the <b>tokenization premium</b> (tokens needed relative to English for the same content) and reduce it with multilingual tokenizer training and vocabulary.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Same meaning, different bill

"The weather is nice today." in nine languages, tokenized for real with GPT-2's tokenizer. Many models charge per token, generate one token at a time, and have a fixed token budget.
{: .lede}

<div class="visual"><div id="p1Bars"></div></div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Byte-level coverage isn't the same as efficiency

::: cards grid3
### [d] English-heavy training
Merges are learned from the tokenizer's training data, so frequent English strings become single tokens and rarer scripts stay split into byte-level pieces.

### [b] Up to 15× more tokens
Petrov et al. found the same text translated into different languages can differ in token length by <b>up to 15×</b>.

### [c] Bytes aren't fair either
Even character- and byte-level models show <b>over 4×</b> differences in encoding length for some language pairs, because scripts use different numbers of bytes per character.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Predict the most expensive language

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? With GPT-2's tokenizer, which of these translations of "The weather is nice today." needs the most tokens?
- [ ] Spanish
- [ ] German
- [x] Hindi
- [ ] Chinese
> <b>Hindi: 27 tokens</b>, against 6 for English, 10 for Spanish, 11 for German and 11 for Chinese. Devanagari takes 3 bytes per character in UTF-8 (UTF = Unicode Transformation Format), and GPT-2's merges rarely cover it, so most tokens are single bytes or short byte pieces.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## The tokenization premium

<div class="eq">premium(L) = tokens(text in L) ÷ tokens(same text in English)</div>

<div class="grid3" style="margin-top:14px">
  <div class="card d"><h3>Cost</h3><p>Pay-per-token APIs (application programming interfaces) charge the premium directly.</p></div>
  <div class="card b"><h3>Latency</h3><p>Generation is one token per step, so more tokens means slower responses.</p></div>
  <div class="card c"><h3>Context</h3><p>A fixed token window holds less content.</p></div>
</div>

<div class="cite">Petrov et al. (NeurIPS 2023) argue these disparities lead to unequal cost, latency and context room, and recommend multilingually fair tokenizers.</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Explore the premium by tokenizer

<div class="visual">
  <div class="seg" id="mlEnc"><button data-v="gpt2">gpt2</button><button data-v="cl100k_base" class="on">cl100k_base</button><button data-v="o200k_base">o200k_base</button></div>
  <div id="mlBars" style="margin-top:12px"></div>
  <p class="readout" id="mlOut" style="margin-top:8px"></p>
</div>

<p class="caption">Measured on one short sentence per language, so it illustrates the effect rather than measuring it. Petrov et al. use large parallel corpora.</p>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## How much fits in the same context window?

<div class="visual">
  <div class="controls" style="margin-top:0"><div class="seg" id="cxEnc"><button data-v="gpt2">gpt2</button><button data-v="cl100k_base" class="on">cl100k_base</button><button data-v="o200k_base">o200k_base</button></div>
    <label class="ctl">Context window <select id="cxW"><option value="4096">4K</option><option value="8192" selected>8K</option><option value="32768">32K</option><option value="131072">128K</option></select></label>
  </div>
  <div id="cxBars" style="margin-top:12px"></div>
</div>

<p class="caption">Copies of the sample sentence that fit in the window, estimated as window ÷ tokens per sentence.</p>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it happens, and what reduces it

<div class="grid2">
  <div class="card d"><h3>Merges follow the data</h3><p>BPE (byte-pair encoding) merges the most frequent pairs in its training data. If most of that data is English, most merges serve English.</p></div>
  <div class="card b"><h3>Scripts cost different numbers of bytes</h3><p>UTF-8 uses 1 byte per ASCII character but 2–3 for many other scripts, so byte-level fallback is uneven.</p></div>
  <div class="card e"><h3>Fix: multilingual vocabulary</h3><p>Llama 3 added 28K non-English tokens, improving compression and downstream performance with no effect on English. In this sample, o200k_base brings every language to 5–6 tokens.</p></div>
  <div class="card a"><h3>Fix: balanced tokenizer training</h3><p>Train the tokenizer on balanced multilingual data and target parity, as Petrov et al. recommend.</p></div>
</div>

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Byte-level BPE treats all languages equally."
> It guarantees <b>coverage</b>, not efficiency. Petrov et al. found even byte-level models differ by over 4× across some language pairs.
:::

::: reveal myth
? "The premium is only about price."
> It also means <b>higher latency</b> (more decoding steps) and <b>less usable context</b> for the same content.
:::

<div class="quiz myth">
  <p class="qq">"A language's premium is a fixed property of the language."</p>
  <button class="reveal">Why is this wrong?</button>
  <div class="why">It depends on the <b>tokenizer</b>: the Hindi sample costs 27 tokens with gpt2, 21 with cl100k_base and 5 with o200k_base.</div>
</div>

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

<div class="quiz">
  <p class="qq">What maximum disparity did Petrov et al. report?</p>
  <div class="opts">
  <button>A. 1.5×</button>
  <button>B. 4×</button>
  <button data-ok>C. Up to 15×</button>
  <button>D. 100×</button>
  </div>
  <div class="why"><b>Up to 15×</b> more tokens for the same text in some languages.</div>
</div>

<div class="quiz ">
  <p class="qq">Using this guide's sample, what is Hindi's premium in gpt2 (27 tokens vs 6 for English)?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">27 ÷ 6 = <b>4.5×</b>. With o200k_base it is 5 ÷ 6 ≈ 0.8×, slightly <em>fewer</em> tokens than English on this one sentence.</div>
</div>

<div class="quiz ">
  <p class="qq">Give two consequences of a high tokenization premium besides price.</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why"><b>Higher latency</b> (more tokens to generate) and <b>less content per context window</b>.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">The same content can cost several times more tokens outside English. That premium is set by the tokenizer, and it shows up as price, latency and lost context.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Tokenizers learn merges from their training data, so English-heavy data gives English compact tokens while other scripts fall back to byte pieces. Petrov et al. found up to 15× differences in token count for the same text, which means higher cost, slower generation and less content per context window. The premium depends on the tokenizer: in this guide's Hindi sample it drops from 27 tokens (gpt2) to 5 (o200k_base). Multilingual tokenizer training and vocabulary, like Llama 3's extra 28K tokens, reduce it.</p></div>

<div class="recap"><div><span><b>Problem:</b> English-centric tokenizers need many more tokens for other languages.</span></div><div><span><b>Core idea:</b> measure the premium against English and reduce it with multilingual tokenizer data and vocabulary.</span></div></div>

<p class="start-hint">Next: <a href="../10-tokenization-quirks/index.html">10 · Tokenization quirks →</a> · Previous: <a href="../08-tokenizers-in-llms/index.html">← 08</a> · <a href="../index.html">All decks</a> · <a href="../playground/index.html">Playground</a></p>

<!-- slide id="s-papers" from="papers" -->
