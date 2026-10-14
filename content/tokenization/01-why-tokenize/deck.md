---
title: Why Tokenize
body:
  data-deck: Why tokenize?
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
  - 'raw text :: any string :: f'
  - 'normalize :: optional (e.g. NFKC) :: f'
  - 'pre-tokenize :: split on spaces, punctuation :: c'
  - 'subword model :: BPE, WordPiece, unigram :: a'
  - 'ids :: integers into the embedding table :: e'
  caption: 'Decoding runs the same pipeline backwards: ids → pieces → text.'
example:
  title: 'Worked example: one sentence, three tokenizers'
  setup: '"The Abwasserbehandlungsanlage handled 12,345 litres." tokenized with tiktoken.'
  steps:
  - 'GPT-2 (50,257 tokens): <b>17</b> tokens; cl100k_base (~100K): <b>17</b>; o200k_base (~200K): <b>14</b>.'
  - 'The rare compound " Abwasserbehandlungsanlage" alone: 10 / 9 / 6 tokens; the common word " unbelievable" is 1 token in all three.'
  - Characters as units would need 52 positions; whole words would need a vocabulary with every compound and number.
  - 'Subwords sit in between: frequent words stay whole, rare ones split into reusable pieces.'
  result: Bigger vocabularies compress better, but every entry costs embedding parameters (deck 07).
traps:
  tricks:
  - 'Rule of thumb for English. :: A few characters per token; Llama 3 measured 3.94 characters per token.'
  - 'Leading spaces matter. :: " hello" and "hello" are different tokens.'
  - 'Everything is ids. :: The model sees integers; letters exist only inside the embedding.'
  traps:
  - 'Counting words as tokens. :: Token counts and word counts differ, by language and tokenizer.'
  - 'Assuming one tokenizer per language. :: Each model family has its own; ids aren''t portable.'
  - 'Ignoring the tokenizer in evals. :: Some failures (spelling, arithmetic) start at tokenization.'
papers:
- sennrich
- gpt2
- bert
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Tokenization for LLMs · 01</div>
    <h1>Why tokenize?</h1>
    <p class="sub">A language model can only process numbers. Tokenization decides how text becomes a sequence of integer ids, and that choice affects vocabulary size, sequence length, cost, and what the model can "see".</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Characters make sequences very long. Whole words leave rare and new words unknown.</div>
      <div class="c"><b>Core idea</b>Use <b>subwords</b>: common words stay whole, rare words split into known pieces, so any text fits a fixed vocabulary.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## A model never sees text, only integer ids

<p class="lede">Before an LLM (large language model) does anything, the input string is cut into <b>tokens</b>, and each token is replaced by its id in a fixed vocabulary. The model's first layer looks up one embedding row per id. Below is a real tokenization with <code>cl100k_base</code> (GPT-4's encoding).</p>

<div class="visual">
  <h3>"Tokenization turns text into numbers."</h3>
  <div id="introToks" style="margin-top:10px"></div>
  <p class="caption">Hover a token for its id. <span class="ws">·</span> marks a space, which belongs to the token that follows it.</p>
  <div class="paper" style="margin-top:14px"><b>Next step inside the model:</b> each id selects one row of the embedding matrix (vocabulary size V × model width d). The model's output layer then scores all V ids to predict the next token.</div>
</div>

<div class="takeaway">Everything the model learns, it learns over these ids. How text is split decides what each id means.</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## The two obvious units both break

Split by <b>characters</b> and the vocabulary is tiny, but sequences get long, and attention cost grows with the square of the length. Split by <b>words</b> and sequences are short, but any word outside the vocabulary becomes an unknown token. Pick a sentence.
{: .lede}

<div class="visual">
  <div class="seg" id="limSeg"><button data-v="s_animal" class="on">Everyday sentence</button><button data-v="s_rare">Rare word + number</button><button data-v="s_code">Code</button></div>
  <div id="limRows" style="margin-top:12px"></div>
  <p class="caption">Characters and words are split in the browser. The word row uses a <span class="ill">toy</span> vocabulary of about 100 common English words, and anything else becomes [UNK]. The subword row is the real <code>cl100k_base</code> output.</p>
</div>

<div class="cite">Sennrich et al. (2016) put the trade-off this way: an increase in text length "reduces efficiency and increases the distances over which neural models need to pass information", while large vocabularies cost time and space.</div>

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Pick the unit

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Which unit gives a fixed, modest vocabulary, reasonably short sequences, and no unknown words?
- [ ] Whole words
- [ ] Single characters
- [x] Subwords: frequent strings kept whole, rare ones split into known pieces
- [ ] Whole sentences
> <b>C.</b> Words (A) leave rare words unknown, characters (B) make sequences long, and sentences (D) would need an infinite vocabulary. Subwords sit in between: common words become single tokens, and anything rare is spelled out with smaller pieces that are in the vocabulary.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Subwords: common words stay whole, rare words split

Real tokenizer output. Note the leading space: in these tokenizers a word and the space before it usually form one token.
{: .lede}

<div class="visual">
  <div class="seg" id="coreEnc"><button data-v="gpt2">gpt2</button><button data-v="cl100k_base" class="on">cl100k_base</button><button data-v="o200k_base">o200k_base</button></div>
  <div id="coreRows" style="margin-top:12px"></div>
</div>

<div class="takeaway">The vocabulary is fixed (about 100K tokens for cl100k_base), yet any word can still be written, from "the" to "Abwasserbehandlungsanlage" (Sennrich et al.'s example of a German compound).</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## The tokenization pipeline, end to end

<p class="lede">Tokenizers differ in detail, but most follow the same stages. Below, one sentence goes through them with real GPT-2-style pre-tokenization and real <code>cl100k_base</code> tokens.</p>

<div class="visual">
  <div class="steps" id="pipeSteps"></div>
  <div id="pipeOut" style="margin-top:14px"></div>
  <div class="infobox" id="pipeInfo"></div>
</div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why subwords work

<div class="grid2">
  <div class="card a"><h3>Compression</h3><p>tiktoken's README puts typical BPE (byte-pair encoding) compression at about <b>4 bytes per token</b>. On this guide's 408-character English sample, <code>cl100k_base</code> uses 79 tokens, about 5.2 characters per token.</p></div>
  <div class="card b"><h3>Fixed output layer</h3><p>The model predicts one of V ids at every step. A fixed V (50K–200K) keeps that softmax bounded.</p></div>
  <div class="card c"><h3>Open vocabulary</h3><p>Rare words are spelled with smaller pieces, and byte-level tokenizers (deck 03) can encode any string at all.</p></div>
  <div class="card e"><h3>Shorter sequences</h3><p>Fewer tokens means less attention compute (it grows with n²) and more text in a fixed context window (deck 07).</p></div>
</div>

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

<div class="quiz myth">
  <p class="qq">"A token is a word."</p>
  <button class="reveal">Why is this wrong?</button>
  <div class="why">Often it is a <b>piece</b> of a word, and it usually includes the space before it: " strawberry" is one token in cl100k_base, but "strawberry" without the space is three (deck 10).</div>
</div>

<div class="quiz myth">
  <p class="qq">"Every model counts tokens the same way."</p>
  <button class="reveal">Why is this wrong?</button>
  <div class="why">Each model has its own tokenizer. The sentence on the "Characters or words?" slide gets different token counts in gpt2, cl100k_base and o200k_base (deck 08).</div>
</div>

::: reveal myth
? "Tokenization throws information away."
> Modern BPE tokenizers are <b>reversible and lossless</b> (tiktoken README): concatenating the tokens' bytes gives back the original text exactly.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Roughly how many bytes of text does one BPE token cover on average, according to tiktoken's README?
- [ ] 1
- [x] About 4
- [ ] About 40
- [ ] One whole sentence
> <b>About 4 bytes per token</b> in practice. It varies with language and content.
:::

<div class="quiz ">
  <p class="qq">Why not just use characters as tokens?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Sequences become several times longer, and attention cost grows with the square of the length, so compute rises and less text fits in the context window.</div>
</div>

<div class="quiz">
  <p class="qq">A subword tokenizer meets a word it has never seen. What happens?</p>
  <div class="opts">
  <button>A. It outputs [UNK]</button>
  <button data-ok>B. It splits the word into smaller known pieces</button>
  <button>C. It skips the word</button>
  <button>D. It raises an error</button>
  </div>
  <div class="why"><b>It splits the word into known pieces</b>, down to single characters or bytes if needed.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Tokenization maps text to integer ids from a fixed vocabulary. Subwords keep common words whole and spell rare ones in pieces, balancing vocabulary size against sequence length.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Models work on integers, so text is split into tokens and each token becomes an id from a fixed vocabulary. Characters give tiny vocabularies but long sequences, and words give short sequences but unknown words. Subword tokenizers keep frequent strings as single tokens and split rare words into known pieces. The pipeline is normalize, pre-tokenize, apply the subword model, then map to ids, and decoding reverses it losslessly.</p></div>

<div class="recap"><div><span><b>Problem:</b> characters make sequences long; words leave rare words unknown.</span></div><div><span><b>Core idea:</b> subword tokens: a fixed vocabulary where any text is spelled with known pieces, about 4 bytes per token.</span></div></div>

<p class="start-hint">Next: <a href="../02-bpe-from-scratch/index.html">02 · BPE from scratch →</a> · <a href="../index.html">All decks</a> · <a href="../playground/index.html">Playground</a></p>

<!-- slide id="s-papers" from="papers" -->
