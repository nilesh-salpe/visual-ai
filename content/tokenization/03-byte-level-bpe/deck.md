---
title: Byte-Level BPE
body:
  data-deck: Byte-level BPE
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
  - 'text :: any Unicode :: f'
  - 'UTF-8 bytes :: 1–4 bytes per character :: c'
  - 'pre-tokenize :: regex: no merges across categories :: b'
  - 'byte-level BPE :: 256 base symbols + merges :: a'
  - 'ids :: never unknown :: e'
  caption: 'Any string can be encoded: in the worst case, one token per byte.'
example:
  title: 'Worked example: bytes behind the tokens'
  setup: UTF-8 uses 1 byte for ASCII, 2 for most accented Latin and Cyrillic, 3 for most Asian scripts, 4 for emoji.
  steps:
  - '"héllo 👋" is 11 bytes (7 characters): GPT-2 uses <b>5</b> tokens, o200k_base <b>4</b>.'
  - '"नमस्ते दुनिया" (Hindi) is 37 bytes: GPT-2 <b>23</b> tokens, cl100k_base 13, o200k_base <b>5</b>.'
  - '"こんにちは世界。" is 24 bytes: GPT-2 <b>11</b>, o200k_base <b>3</b>.'
  - Some tokens hold only part of a character's bytes, which is why decoded pieces can look like garbage until joined.
  result: Byte-level BPE guarantees coverage; how efficient it is depends on how much of each script the merges learned.
traps:
  tricks:
  - 'Base vocabulary = 256. :: Every byte value; no unknown token needed.'
  - 'Pre-tokenization regex. :: Keeps letters, digits and punctuation from merging together.'
  - 'Count bytes for worst case. :: Tokens ≤ UTF-8 bytes.'
  traps:
  - 'Decoding token by token. :: A token can end mid-character; decode the joined bytes.'
  - '"Byte-level means fair." :: Coverage is universal, efficiency is not (deck 09).'
  - 'Character counts as cost. :: Cost is tokens, which track bytes and merges, not characters.'
papers:
- gpt2
- byt5
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Tokenization for LLMs · 03</div>
    <h1>Byte-level BPE</h1>
    <p class="sub">How GPT-2 made BPE (byte-pair encoding) work on any string at all (emoji, every script, code) with a base vocabulary of only 256 symbols (Radford et al., 2019, §2.2).</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>A general language model should be able to give a probability to, and generate, any string. Character-level BPE either needs a huge base vocabulary or produces unknown tokens.</div>
      <div class="c"><b>Core idea</b>Run BPE over the UTF-8 (UTF = Unicode Transformation Format) <b>bytes</b> of the text instead of Unicode characters. The base vocabulary is 256 bytes, so nothing is ever unknown.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## An LLM must handle any string

The GPT-2 paper sets the requirement: "A general language model (LM) should be able to compute the probability of (and also generate) any string." Real input includes accented letters, emoji, dozens of scripts, code, and stray control characters.
{: .lede}

<div class="visual"><div class="bytes" id="p1Chars"></div></div>

<div class="takeaway">Lowercasing, word-level tokenization and unknown tokens all <b>restrict which strings the model can represent</b> (§2.2).</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## BPE over Unicode characters needs a huge base vocabulary

Reference BPE implementations of the time worked on Unicode code points. Covering every possible string that way would need "a base vocabulary of over 130,000 before any multi-symbol tokens are added", far larger than the 32,000–64,000-token vocabularies typically used with BPE.
{: .lede}

<div class="visual"><div id="limBars"></div></div>

<div class="cite">GPT-2 paper §2.2. The alternative, an unknown token for rare characters, gives up the "any string" requirement.</div>

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Cover everything with a small base

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

<div class="quiz">
  <p class="qq">How can BPE cover every possible string while keeping the base vocabulary small?</p>
  <div class="opts">
  <button>A. Include all Unicode characters in the base vocabulary</button>
  <button data-ok>B. Run BPE over the 256 possible UTF-8 byte values</button>
  <button>C. Keep ASCII only and map everything else to [UNK]</button>
  <button>D. Use whole words</button>
  </div>
  <div class="why"><b>B.</b> Every string is a sequence of UTF-8 bytes, and there are only 256 byte values. Starting BPE from bytes makes the base vocabulary 256 and leaves no unknown symbols. Option A needs more than 130,000 base symbols, and C gives up coverage.</div>
</div>

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## BPE on bytes: 256 base symbols, then merges

<div class="grid3">
  <div class="card a"><h3>Base = 256 bytes</h3><p>Any text is first encoded as UTF-8, a sequence of bytes 0–255. That's the starting alphabet.</p></div>
  <div class="card b"><h3>Merges on top</h3><p>BPE merges frequent byte sequences into tokens. Common English words become single tokens, and rarer scripts use more, shorter tokens.</p></div>
  <div class="card e"><h3>GPT-2's numbers</h3><p>Vocabulary 50,257 = <b>256 bytes + 50,000 merges + 1 special token</b> (&lt;|endoftext|&gt;), checked with tiktoken.</p></div>
</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## From characters to bytes: try it

Type anything. Each character becomes 1 to 4 UTF-8 bytes. ASCII takes 1 byte, accented Latin letters 2, Devanagari and Japanese 3, and most emoji 4.
{: .lede}

<div class="visual">
  <input class="tk-in" id="byIn" value="héllo 👋 नमस्ते" style="width:100%">
  <div class="bytes" id="byOut" style="margin-top:12px"></div>
  <p class="readout" id="byCnt" style="margin-top:8px"></p>
</div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Real byte-level tokens, including partial characters

Real output from three tiktoken encodings. A token can end <b>in the middle of a character</b>. Tokens with a dashed red outline hold incomplete UTF-8 bytes, which only become a character when joined with their neighbours.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <div class="seg" id="exSeg"><button data-v="hello_emoji" class="on">héllo 👋</button><button data-v="hindi">नमस्ते दुनिया</button><button data-v="jp">こんにちは世界。</button></div>
  </div>
  <div id="exRows" style="margin-top:12px"></div>
</div>

<!-- slide id="s-how3" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Pre-tokenization: no merges across character categories

Applied naively, byte-level BPE wasted vocabulary on variants such as <code>dog.</code>, <code>dog!</code> and <code>dog?</code>. GPT-2 therefore stops BPE from merging across character categories. A regular expression first splits text into chunks (letters, numbers, punctuation), with an exception that lets a space attach to the following word.
{: .lede}

<div class="visual">
  <h3>Pre-tokenized chunks (GPT-2 pattern)</h3><div id="dogChunks" style="margin-top:6px"></div>
  <h3 style="margin-top:14px">Final tokens (gpt2)</h3><div id="dogToks" style="margin-top:6px"></div>
</div>

<div class="cite">§2.2: "We observed BPE including many versions of common words like dog since they occur in many variations such as dog. dog! dog?" Pattern shown is GPT-2's (tiktoken r50k), minus regex features JavaScript lacks.</div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works

::: cards grid2
### [a] Nothing is ever unknown
Every string is a byte sequence and all 256 bytes are in the vocabulary, so any input can be encoded.

### [e] Any string gets a probability
"Since our approach can assign a probability to any Unicode string," GPT-2 could be evaluated on any dataset "regardless of pre-processing, tokenization, or vocab size" (§2.2).

### [b] Word-level efficiency where it counts
Merges make frequent strings single tokens, combining "the empirical benefits of word-level LMs with the generality of byte-level approaches".

### [c] Vocabulary spent well
The category rule stops near-duplicate tokens like "dog." and "dog!" from using up vocabulary slots.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Byte-level means one token per byte."
> Bytes are only the <b>base</b>. Merges build multi-byte tokens, so a common English word with its leading space is usually a single token.
:::

::: reveal myth
? "Every token decodes to valid text."
> A token can hold a <b>partial</b> UTF-8 character: the 👋 emoji above is split across two tokens. Streaming output has to buffer bytes until a character is complete.
:::

::: reveal myth
? "The space between words is its own token."
> In GPT-2-style pre-tokenization a single space attaches to the <b>following</b> word: " dog" is one token.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? How big is the base vocabulary of byte-level BPE?
- [ ] 26
- [x] 256
- [ ] 50,257
- [ ] 130,000+
> <b>256</b>, one symbol per byte value.
:::

<div class="quiz">
  <p class="qq">What makes up GPT-2's 50,257-token vocabulary?</p>
  <div class="opts">
  <button>A. 50,257 words</button>
  <button data-ok>B. 256 bytes + 50,000 merges + 1 special token</button>
  <button>C. 130,000 characters pruned to 50K</button>
  <button>D. 50,000 bytes + 257 merges</button>
  </div>
  <div class="why"><b>256 + 50,000 + 1</b>. The special token is &lt;|endoftext|&gt; (id 50256).</div>
</div>

<div class="quiz ">
  <p class="qq">Why can a byte-level BPE tokenizer never output an unknown token?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Every possible input is a sequence of bytes, and every byte value is a base token, so the worst case is simply one token per byte.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Byte-level BPE runs BPE over UTF-8 bytes: a 256-symbol base means any string can be encoded with no unknowns, while merges keep common text compact.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>GPT-2 wanted a model that could assign a probability to any string. BPE over Unicode characters would need a base vocabulary of more than 130,000 symbols, so GPT-2 runs BPE over UTF-8 bytes instead: 256 base symbols plus 50,000 merges plus one special token gives 50,257. A regex pre-tokenizer stops merges across letters, digits and punctuation, so near-duplicates like "dog." and "dog!" don't waste vocabulary. Tokens can hold partial characters, so decoding has to buffer bytes.</p></div>

<div class="recap"><div><span><b>Problem:</b> any-string coverage with character BPE needs 130K+ base symbols, or [UNK (unknown token)].</span></div><div><span><b>Core idea:</b> BPE over bytes: a base of 256, nothing unknown, merges for efficiency, regex pre-tokenization.</span></div></div>

<p class="start-hint">Next: <a href="../04-wordpiece-unigram/index.html">04 · WordPiece and unigram LM →</a> · Previous: <a href="../02-bpe-from-scratch/index.html">← 02</a> · <a href="../index.html">All decks</a> · <a href="../playground/index.html">Playground</a></p>

<!-- slide id="s-papers" from="papers" -->
