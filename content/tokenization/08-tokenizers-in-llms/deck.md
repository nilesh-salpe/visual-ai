---
title: Tokenizers in Real LLMs
body:
  data-deck: Tokenizers in real LLMs
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
  - 'normalizer :: e.g. NFKC or none :: f'
  - 'pre-tokenizer :: regex split :: c'
  - 'model :: merges or pieces + ids :: a'
  - 'special tokens :: reserved ids :: b'
  - 'post-processor :: add BOS, templates :: e'
  caption: All four parts must match the ones used in training.
example:
  title: 'Worked example: same text, three tokenizers'
  setup: '"Tokenizers turn text into integers: 12345, naïve café 👋 and def f(x): return x"'
  steps:
  - 'GPT-2: <b>22</b> tokens; cl100k_base: <b>23</b>; o200k_base: <b>23</b>.'
  - "Code \"for i in range(10):\n    print(i)\": GPT-2 15 tokens vs cl100k_base 11: newer vocabularies merge runs of spaces."
  - '"12345678": 3 tokens in all three; Llama 2 instead splits every digit (8 tokens).'
  - '<|endoftext|> is id 50256 in GPT-2 and 100257 in cl100k_base: the same string means different ids.'
  result: Token counts, digit handling and special ids differ by tokenizer; a model is only correct with its own.
traps:
  tricks:
  - 'GPT-2: 50,257 = 256 + 50,000 + 1. :: Bytes + merges + <|endoftext|>.'
  - 'Llama 2 splits digits. :: Every number is one token per digit.'
  - 'Count with the real tokenizer. :: Estimates from characters can be far off for code and non-English text.'
  traps:
  - 'Swapping tokenizers. :: Ids index the embedding table; a different tokenizer scrambles the input.'
  - 'Special tokens from user text. :: Literal "<|endoftext|>" in input must not become the special id.'
  - 'Assuming same family, same tokenizer. :: Llama 2 (32K SentencePiece) and Llama 3 (128K tiktoken-based) differ.'
papers:
- gpt2
- llama2
- llama3
- bert
- t5
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Tokenization for LLMs · 08</div>
    <h1>Tokenizers in real LLMs</h1>
    <p class="sub">What GPT-2, GPT-4, GPT-4o, Llama, BERT (Bidirectional Encoder Representations from Transformers) and T5 actually use: algorithm, vocabulary size, pre-tokenization rules and special tokens. Every row is checked against the model's paper or the tokenizer source.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Every model family ships its own tokenizer, so token counts, costs and behaviour differ, and ids mean nothing outside their own model.</div>
      <div class="c"><b>Core idea</b>A tokenizer is part of the model: a vocabulary (merges or scored pieces), a pre-tokenization rule, normalization, and special tokens, all frozen at training time.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Same text, three tokenizers, three answers

Real output from three OpenAI encodings on one sentence. Token boundaries, counts and ids all differ.
{: .lede}

<div class="visual"><div id="cmpRows"></div></div>

<p class="caption">Hover any token for its id. Try your own text in the <a href="../playground/index.html">live playground</a>.</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## You can't swap a tokenizer after training

::: cards grid3
### [d] Ids index the embeddings
Id 1234 is a specific learned row in this model's embedding matrix. In another tokenizer, id 1234 is a different string.

### [b] Rules are baked in
How digits, spaces and code are split determines what patterns the model learned to read.

### [c] Special tokens are reserved
End-of-text, padding and chat-role markers are specific ids the model was trained to treat specially.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Mismatched ids

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

<div class="quiz">
  <p class="qq">You feed Llama 3 a prompt tokenized with GPT-4's cl100k_base ids. What happens?</p>
  <div class="opts">
  <button>A. It works fine, since both use BPE</button>
  <button data-ok>B. Garbage: each id selects an unrelated embedding row</button>
  <button>C. Slightly worse quality</button>
  <button>D. It runs faster</button>
  </div>
  <div class="why"><b>B.</b> Ids are only meaningful with the tokenizer the model was trained with. Even though Llama 3's vocabulary includes 100K tokens taken from tiktoken, its id assignments and its extra 28K tokens are its own. Always use the model's own tokenizer.</div>
</div>

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## What a tokenizer actually consists of

::: cards grid2
### [a] Vocabulary
BPE (byte-pair encoding) merge ranks (tiktoken: about 100K–200K byte sequences with ranks), or scored pieces (a SentencePiece unigram model).

### [b] Pre-tokenization
A regex or rule that splits text into chunks before subword merging: words with their leading space, digit groups, punctuation.

### [c] Normalization
Optional Unicode normalization (SentencePiece defaults to NFKC (Unicode Normalization Form KC (compatibility composition))). Byte-level BPE keeps raw bytes.

### [e] Special tokens
Reserved ids for document boundaries, padding, fill-in-the-middle or chat structure, never produced from ordinary text.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## The tokenizers of well-known models

<div class="visual scroll-x">
  <table class="tbl">
    <tr><th>Model</th><th>Algorithm</th><th>Vocabulary</th><th>Notable rules</th><th>Source</th></tr>
    <tr><td>GPT-2</td><td>Byte-level BPE</td><td>50,257</td><td>256 bytes + 50,000 merges + &lt;|endoftext|&gt;; no merges across character categories</td><td>GPT-2 §2.2; tiktoken</td></tr>
    <tr><td>GPT-4 (cl100k_base)</td><td>Byte-level BPE</td><td>100,277 ids</td><td>Numbers split into ≤3-digit groups; FIM (fill-in-the-middle) special tokens</td><td>tiktoken source</td></tr>
    <tr><td>GPT-4o (o200k_base)</td><td>Byte-level BPE</td><td>200,019 ids</td><td>Different regex and merges; ≤3-digit number groups</td><td>tiktoken source</td></tr>
    <tr><td>Llama 1 / 2</td><td>BPE via SentencePiece</td><td>32K</td><td>Numbers split into <b>individual digits</b>; bytes for unknown UTF-8 (UTF = Unicode Transformation Format) characters</td><td>Llama 2 §2.2</td></tr>
    <tr><td>Llama 3</td><td>BPE (tiktoken-based)</td><td>128K</td><td>100K tiktoken tokens + 28K non-English tokens</td><td>Llama 3 §3.2</td></tr>
    <tr><td>BERT</td><td>WordPiece</td><td>30,000</td><td>[CLS (classification token)] starts every sequence; [SEP (separator token)] separates segments</td><td>BERT §3</td></tr>
    <tr><td>T5</td><td>SentencePiece (wordpieces)</td><td>32,000</td><td>Shared input/output vocabulary; covers EN, DE, FR, RO</td><td>T5 §3.1.3</td></tr>
  </table>
</div>

<p class="caption">"ids" counts include special tokens: tiktoken's n_vocab for cl100k_base is 100,277 and for o200k_base 200,019; the rest of the ids are mergeable byte sequences.</p>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Number handling differs a lot

"12345678" tokenized for real. GPT-2's pattern keeps a whole run of digits as one chunk and lets BPE merge it however it learned; cl100k and o200k pre-split numbers into groups of at most 3 digits; Llama 1/2 split every digit.
{: .lede}

<div class="visual"><div id="numRows"></div>
  <div class="tokrow"><div class="lab">Llama 1/2 rule</div><div class="toks"><span class="tok c0">1</span><span class="tok c1">2</span><span class="tok c2">3</span><span class="tok c3">4</span><span class="tok c4">5</span><span class="tok c5">6</span><span class="tok c0">7</span><span class="tok c1">8</span></div><div class="cnt">8</div></div>
</div>

<p class="caption">The Llama row applies the documented rule ("split all numbers into individual digits") rather than running the Llama tokenizer.</p>

<!-- slide id="s-how3" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Special tokens are reserved ids, not text

<div class="visual scroll-x">
  <table class="tbl">
    <tr><th>Tokenizer</th><th>Special tokens (id)</th></tr>
    <tr><td>gpt2</td><td><code>&lt;|endoftext|&gt;</code> 50256</td></tr>
    <tr><td>cl100k_base</td><td><code>&lt;|endoftext|&gt;</code> 100257 · <code>&lt;|fim_prefix|&gt;</code> 100258 · <code>&lt;|fim_middle|&gt;</code> 100259 · <code>&lt;|fim_suffix|&gt;</code> 100260 · <code>&lt;|endofprompt|&gt;</code> 100276</td></tr>
    <tr><td>o200k_base</td><td><code>&lt;|endoftext|&gt;</code> 199999 · <code>&lt;|endofprompt|&gt;</code> 200018</td></tr>
    <tr><td>BERT</td><td><code>[CLS]</code>, <code>[SEP]</code></td></tr>
    <tr><td>SentencePiece</td><td><code>&lt;unk&gt;</code>, <code>&lt;s&gt;</code>, <code>&lt;/s&gt;</code>, <code>&lt;pad&gt;</code>, plus user-defined ones such as <code>&lt;2ja&gt;</code></td></tr>
  </table>
</div>

<div class="paper"><b>Safety detail:</b> by default, tiktoken's <code>encode()</code> <b>raises an error</b> if ordinary text contains a special-token string such as <code>&lt;|endoftext|&gt;</code> (checked with tiktoken 0.14). This stops user-supplied text from silently turning into a control token.</div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why tokenizers differ

::: cards grid2
### [a] Different data
Tokenizers are trained on their model's data mix. More code and multilingual text in training produces tokens for those.

### [b] Different goals
Splitting digits individually (Llama) or into groups of three (cl100k/o200k) gives numbers a consistent structure. GPT-2's unbounded digit chunks don't.

### [c] Different eras
Vocabularies grew from about 30K (BERT, T5, Llama 2) to 100K–200K (GPT-4, Llama 3, GPT-4o) as models grew and multilingual use mattered more.

### [e] Tooling
SentencePiece (raw text, ▁) and tiktoken (byte-level BPE, regex pre-split) are the two families most LLMs (large language models) build on.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Token ids are universal across models."
> They're <b>model-specific</b>. The same id maps to different strings in different tokenizers, and even shared merges get different id assignments.
:::

<div class="quiz myth">
  <p class="qq">"Typing "<|endoftext|>" in a prompt ends the document."</p>
  <button class="reveal">Why is this wrong?</button>
  <div class="why">Special tokens are <b>reserved ids</b>. With tiktoken's defaults the literal string raises an error instead of being encoded as the control token.</div>
</div>

<div class="quiz myth">
  <p class="qq">"o200k_base is cl100k_base with more tokens added."</p>
  <button class="reveal">Why is this wrong?</button>
  <div class="why">It is a <b>separate encoding</b>: its own merge ranks and its own pre-tokenization pattern (tiktoken source).</div>
</div>

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? How do Llama 1 and 2 tokenize numbers?
- [ ] As whole numbers
- [ ] In groups of up to 3 digits
- [x] As individual digits
- [ ] As words
> <b>Individual digits</b> (Llama 2 paper §2.2, same as Llama 1).
:::

<div class="quiz">
  <p class="qq">What is &lt;|endoftext|&gt;'s id in gpt2?</p>
  <div class="opts">
  <button>A. 0</button>
  <button data-ok>B. 50256</button>
  <button>C. 100257</button>
  <button>D. 199999</button>
  </div>
  <div class="why"><b>50256</b>, the last id in GPT-2's 50,257-entry vocabulary.</div>
</div>

<div class="quiz ">
  <p class="qq">Name the four parts that make up a tokenizer.</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">A <b>vocabulary</b> (merges or scored pieces), a <b>pre-tokenization</b> rule, optional <b>normalization</b>, and <b>special tokens</b>.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Each LLM's tokenizer (vocabulary, pre-tokenization, normalization and special tokens) is part of the model. Ids, counts and number handling differ between models and don't transfer.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>GPT-2 uses byte-level BPE with 50,257 tokens; GPT-4's cl100k_base and GPT-4o's o200k_base are larger byte-level BPE encodings that split numbers into groups of up to three digits. Llama 1 and 2 use SentencePiece BPE with 32K tokens and individual digits; Llama 3 uses 128K tokens (100K from tiktoken plus 28K multilingual). BERT uses 30,000 WordPieces and T5 32,000 SentencePiece pieces. Special tokens are reserved ids, and ids only make sense with the model's own tokenizer.</p></div>

<div class="recap"><div><span><b>Problem:</b> tokenizers differ per model, so counts, costs and ids don't transfer.</span></div><div><span><b>Core idea:</b> tokenizer = vocabulary + pre-tokenization + normalization + special tokens, frozen with the model.</span></div></div>

<p class="start-hint">Next: <a href="../09-multilingual-cost/index.html">09 · Multilingual cost →</a> · Previous: <a href="../07-vocabulary-size/index.html">← 07</a> · <a href="../index.html">All decks</a> · <a href="../playground/index.html">Playground</a></p>

<!-- slide id="s-papers" from="papers" -->
