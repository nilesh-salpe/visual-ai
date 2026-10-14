---
title: SentencePiece
body:
  data-deck: SentencePiece
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
  - 'raw sentence :: no pre-tokenizer :: f'
  - 'normalize :: NFKC by default :: c'
  - 'spaces → ▁ :: whitespace is a symbol :: b'
  - 'BPE or unigram :: on the whole stream :: a'
  - 'decode :: join, ▁ → space: lossless :: e'
  caption: 'Language-independent: no hand-written rules for where words start.'
example:
  title: 'Worked example: lossless round trip'
  setup: 'Text: "Hello world." with a unigram SentencePiece model.'
  steps:
  - 'Replace spaces with ▁ and prefix one: "▁Hello▁world."'
  - Segment the stream, e.g. [▁Hello, ▁world, .].
  - 'Decode: concatenate pieces → "▁Hello▁world." → replace ▁ with a space → " Hello world." → strip the leading space.'
  - No information about spacing was lost, so detokenization needs no language-specific rules (also works for Japanese or Chinese without spaces).
  result: Treating whitespace as an ordinary symbol is what makes SentencePiece reversible across languages. Llama 2 and T5 use it.
traps:
  tricks:
  - '▁ marks a word start. :: It is U+2581, not an underscore.'
  - 'One library, two algorithms. :: SentencePiece implements both BPE and unigram LM.'
  - 'Byte fallback. :: Unknown characters become UTF-8 byte tokens (as in Llama 2).'
  traps:
  - 'Calling SentencePiece an algorithm. :: It is a toolkit and pipeline; BPE or unigram does the segmentation.'
  - 'Stripping ▁ incorrectly. :: Leads to doubled or missing spaces on decode.'
  - 'Forgetting normalization. :: NFKC changes some characters before tokenization.'
papers:
- sentencepiece
- kudo
- t5
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Tokenization for LLMs · 05</div>
    <h1>SentencePiece</h1>
    <p class="sub">A language-independent tokenizer and detokenizer that trains directly on raw text, treats whitespace as an ordinary symbol, and round-trips losslessly (Kudo and Richardson, 2018).</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Existing tools assumed text was already split into words, and relied on hand-written, language-specific rules to tokenize and detokenize.</div>
      <div class="c"><b>Core idea</b>Treat the input as a raw Unicode sequence. Escape whitespace as ▁ (U+2581), learn BPE (byte-pair encoding) or unigram subwords on top, and decode exactly.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Tokenizing and detokenizing raw text is language-dependent

<div class="grid2">
  <div class="visual" style="margin-top:0"><h3>English</h3><p class="caption" style="margin-top:4px">Raw: <code>Hello world.</code><br>Pre-tokenized: <code>[Hello] [world] [.]</code></p><p>The pre-tokenized form has lost the fact that there was <b>no space</b> between "world" and ".", so the detokenizer has to guess with language rules.</p></div>
  <div class="visual" style="margin-top:0"><h3>Japanese</h3><p class="caption" style="margin-top:4px">Raw: <code>こんにちは世界。</code> (Hello world.)<br>Pre-tokenized: <code>[こんにちは] [世界] [。]</code></p><p>There are no spaces at all, so splitting into words needs a separate word segmenter, and detokenizing must <b>not</b> insert spaces.</p></div>
</div>

<div class="cite">Examples from the SentencePiece paper, §3.1.</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Hand-written pre- and post-processors don't scale across languages

::: cards grid3
### [d] Hand-crafted rules
Moses, the standard toolkit at the time, uses language-dependent rules "whose effectiveness for NMT (neural machine translation) has not been proven".

### [b] European bias
These tools were "mainly designed for European languages where words are segmented with whitespaces".

### [c] Multilingual pain
Every language needs its own pre/post-processor configuration, which makes multilingual models hard to build (§1).
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Make it reversible in any language

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? How can a tokenizer be exactly reversible on raw text in any language, with no language-specific rules?
- [ ] Keep a per-language list of spacing rules
- [x] Treat whitespace as an ordinary symbol and keep it inside the tokens
- [ ] Delete whitespace before tokenizing
- [ ] Always split on spaces first
> <b>B.</b> SentencePiece escapes each space as the visible symbol ▁ (U+2581) and tokenizes the whole string as a character sequence. Because the spaces are inside the tokens, detokenizing is just joining the tokens and turning ▁ back into a space.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Raw text in, whitespace as a symbol, lossless out

<div class="eq">Decode( Encode( Normalize(text) ) ) = Normalize(text)</div>

<div class="grid3" style="margin-top:14px">
  <div class="card a"><h3>Raw sentences</h3><p>"SentencePiece can train subword models directly from raw sentences", with no word segmenter needed.</p></div>
  <div class="card b"><h3>▁ for whitespace</h3><p>Spaces are escaped as ▁ (U+2581), so <code>Hello▁world.</code> → <code>[Hello] [▁wor] [ld] [.]</code>.</p></div>
  <div class="card e"><h3>Two algorithms</h3><p>Implements both BPE (Sennrich et al.) and the unigram LM (Kudo), selected as a training option.</p></div>
</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Encode and decode, step by step

Top: the paper's real example (Figure 1, a model trained with vocabulary size 1000). Bottom: try your own text. Normalization and the ▁ escape are computed exactly; the subword split below them is <span class="ill">illustrative</span>, since no trained model runs in this page.
{: .lede}

<div class="visual">
  <h3>Paper example</h3>
  <div class="tokrow"><div class="lab">input</div><div class="toks"><span class="tok c0">Hello world.</span></div><div class="cnt"></div></div>
  <div class="tokrow"><div class="lab">spm_encode</div><div id="figToks"></div><div class="cnt">5</div></div>
  <div class="tokrow"><div class="lab">spm_decode</div><div class="toks"><span class="tok c3">Hello world.</span></div><div class="cnt">✓</div></div>
  <h3 style="margin-top:16px">Your text</h3>
  <input class="tk-in" id="spIn" value="ＡＢＣ  costs  ½ price." style="width:100%">
  <div id="spRows" style="margin-top:8px"></div>
</div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Four components and id management

<div class="grid2">
  <div class="visual" style="margin-top:0"><h3>Pipeline (§2)</h3><div class="steps" style="margin-top:8px"><button class="on">Normalizer</button><button class="on">Trainer</button><button class="on">Encoder</button><button class="on">Decoder</button></div>
    <p class="caption">The Normalizer maps equivalent Unicode to a canonical form (NFKC (Unicode Normalization Form KC (compatibility composition)) by default). The Trainer learns the subword model from the normalized corpus. The Encoder normalizes and tokenizes, and the Decoder turns pieces back into normalized text.</p></div>
  <div class="visual" style="margin-top:0"><h3>Vocabulary and ids (§3.3)</h3>
    <p class="caption" style="margin-top:4px">You set the <b>final vocabulary size</b> (<code>--vocab_size</code>) rather than a number of merges, which works for both BPE and unigram. Ids are reserved for meta symbols: <code>&lt;unk&gt;</code>, <code>&lt;s&gt;</code> (BOS (beginning of sequence)), <code>&lt;/s&gt;</code> (EOS (end of sequence)), <code>&lt;pad&gt;</code>, plus custom ones such as language tags <code>&lt;2ja&gt;</code> and <code>&lt;2de&gt;</code>.</p></div>
</div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works, and where it is used

::: cards grid2
### [e] Lossless by design
Whitespace lives inside the tokens, so detokenization is <code>''.join(tokens).replace('▁', ' ')</code>, with no language rules.

### [a] Language-independent
Chinese, Japanese and Korean need no external word segmenter: the model learns pieces from raw characters.

### [b] Efficient
BPE training uses an O(N log N) heap-based algorithm instead of a naive O(N²) one, and unigram training and segmentation are linear in input size (§3.2).

### [c] Used by LLMs
Llama 1 and 2: BPE via SentencePiece, 32K vocabulary, digits split individually, bytes for unknown UTF-8 (UTF = Unicode Transformation Format) characters. T5: SentencePiece with a 32,000-wordpiece vocabulary.
:::

<div class="cite">Llama 2 paper §2.2 (Tokenizer); T5 paper §3.1.3.</div>

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "SentencePiece is a new segmentation algorithm."
> It is a <b>library</b> that implements two existing algorithms, BPE and the unigram LM, with raw-text training and lossless detokenization.
:::

::: reveal myth
? "▁ is just an underscore."
> It is <b>U+2581</b> (LOWER ONE EIGHTH BLOCK), chosen so it won't collide with real underscores in the text.
:::

::: reveal myth
? "SentencePiece reproduces the exact raw input."
> It is lossless with respect to the <b>normalized</b> text. NFKC normalization (the default) can change characters, e.g. fullwidth "ＡＢＣ" becomes "ABC" (§3.4).
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

<div class="quiz">
  <p class="qq">Which symbol does SentencePiece use for whitespace?</p>
  <div class="opts">
  <button>A. _ (U+005F)</button>
  <button data-ok>B. ▁ (U+2581)</button>
  <button>C. @@</button>
  <button>D. ·</button>
  </div>
  <div class="why"><b>▁, U+2581.</b> subword-nmt instead uses @@ as an intra-word boundary marker.</div>
</div>

::: quiz
? What does lossless tokenization guarantee?
- [ ] Encode(text) = text
- [x] Decode(Encode(Normalize(text))) = Normalize(text)
- [ ] Every token is a word
- [ ] No normalization happens
> <b>Decode(Encode(Normalize(text))) = Normalize(text)</b> (§3.1).
:::

<div class="quiz ">
  <p class="qq">Why does treating whitespace as a symbol matter for Japanese and Chinese?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">These languages have no spaces between words, so a tokenizer that assumes space-split input needs an external segmenter, and detokenizing must not add spaces. SentencePiece needs neither.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">SentencePiece tokenizes raw text in any language: whitespace becomes ▁, BPE or unigram pieces are learned on top, and decoding is exactly lossless on normalized text.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Earlier tokenizers assumed space-separated words and relied on language-specific rules to tokenize and detokenize, which breaks for Japanese or Chinese and complicates multilingual models. SentencePiece trains directly on raw sentences: it normalizes with NFKC, escapes spaces as ▁ (U+2581), and learns BPE or unigram pieces. Because whitespace is inside the tokens, decoding is just joining them and restoring spaces, so Decode(Encode(Normalize(text))) equals Normalize(text). Llama 1 and 2 and T5 use it.</p></div>

<div class="recap"><div><span><b>Problem:</b> language-specific pre-/post-processing; text without spaces; detokenization that isn't reversible.</span></div><div><span><b>Core idea:</b> a raw-text tokenizer with ▁ for spaces, BPE or unigram inside, and lossless decoding.</span></div></div>

<p class="start-hint">Next: <a href="../06-many-tokenizations/index.html">06 · One text, many tokenizations →</a> · Previous: <a href="../04-wordpiece-unigram/index.html">← 04</a> · <a href="../index.html">All decks</a> · <a href="../playground/index.html">Playground</a></p>

<!-- slide id="s-papers" from="papers" -->
