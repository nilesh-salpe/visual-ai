---
title: Tokenization Quirks
body:
  data-deck: Tokenization quirks
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
  - 'characters :: what people see :: f'
  - 'tokens :: what the model sees :: c'
  - 'quirk :: spelling, digits, spaces, glitch tokens :: d'
  - 'fix :: spell out, healing, digit splitting :: e'
  caption: Look at the tokens first when a model fails at something "trivial".
example:
  title: 'Worked example: why "how many r''s in strawberry?" is hard'
  setup: Real tiktoken output.
  steps:
  - '"strawberry" (no leading space): <b>3 tokens</b> in GPT-2; " strawberry" (with a space): <b>1 token</b>.'
  - The model never sees the letters r-r-r; it sees one or a few ids and must have memorized their spelling.
  - '"1234+5678=6912" is 8 tokens: digits are grouped irregularly, so column-wise arithmetic is misaligned.'
  - '" SolidGoldMagikarp" is <b>1</b> token in GPT-2 but 5 in cl100k_base: a rarely-trained token can behave strangely ("glitch token").'
  result: Spelling, counting, arithmetic and odd behaviours often trace back to tokens, not to reasoning.
traps:
  tricks:
  - 'Spell it out. :: Ask for letters separated by spaces to get one token per letter.'
  - 'Token healing. :: Back up over the prompt''s last token so generation can choose the natural boundary.'
  - 'Digit splitting. :: One token per digit makes arithmetic regular (Llama 2).'
  traps:
  - 'Prompt ending in a space. :: Splits a natural token (" word") and biases the next token.'
  - 'Case and spacing changes. :: "Hello", "HELLO" and " hello" are different tokens.'
  - 'Blaming reasoning first. :: Check the tokens before concluding the model "can''t count".'
papers:
- gpt2
- fim
- byt5
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Tokenization for LLMs · 10</div>
    <h1>Tokenization quirks in LLMs</h1>
    <p class="sub">Letter counting, arithmetic, leading spaces, prompts that end mid-token, and glitch tokens: many odd LLM (large language model) behaviours become obvious once you look at the tokens.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>LLMs show surprising failures on tasks that look trivial to people, such as spelling, counting letters, adding numbers, or continuing a prompt that ends in a colon.</div>
      <div class="c"><b>Core idea</b>The model sees <b>token ids, not characters</b>. Character-level facts must be learned indirectly, and unusual token boundaries put inputs outside what the model was trained on.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Trivial for people, surprisingly hard for models

::: cards grid3
### [d] Spelling and counting letters
"How many r's are in strawberry?"

### [b] Arithmetic
Multi-digit numbers arrive in irregular chunks.

### [c] Prompt endings
A trailing space or a cut-off "http:" changes the completion.
:::

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## The model never sees letters

After tokenization, " strawberry" is a <b>single id</b>. Nothing in that integer says which letters it contains. Any knowledge of its spelling has to be learned indirectly from training data.
{: .lede}

<div class="visual"><div id="limRows"></div></div>

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Why is letter counting hard?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

<div class="quiz">
  <p class="qq">Why might a model struggle to count the r's in "strawberry"?</p>
  <div class="opts">
  <button>A. Models can't count</button>
  <button data-ok>B. The model sees one to three tokens, not ten letters</button>
  <button>C. The tokenizer deletes the letter r</button>
  <button>D. The word never appears in training data</button>
  </div>
  <div class="why"><b>B.</b> In cl100k_base, "strawberry" is <code>str|aw|berry</code> (3 tokens) and " strawberry" is a single token. The letters are hidden inside opaque ids, so counting them means recalling each token's spelling, which is learned only indirectly.</div>
</div>

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Look at the tokens first

<div class="takeaway">When an LLM fails on something character-level, number-level or boundary-sensitive, check how the input was tokenized before blaming "reasoning".</div>

<div class="grid2" style="margin-top:14px">
  <div class="card a"><h3>Ids hide characters</h3><p>Spelling, rhyme, letter counts and character edits all need knowledge the ids don't carry.</p></div>
  <div class="card b"><h3>Boundaries carry meaning</h3><p>Training text was tokenized greedily, so an unusual split tells the model something it rarely saw, and that something is misleading.</p></div>
</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Quirk explorer: real tokens

<div class="visual">
  <div class="seg" id="qSeg"><button data-v="spell" class="on">Spelling</button><button data-v="num">Numbers</button><button data-v="space">Spaces &amp; case</button><button data-v="boundary">Prompt boundary</button><button data-v="glitch">Glitch tokens</button></div>
  <div id="qRows" style="margin-top:12px"></div>
  <div class="infobox" id="qInfo"></div>
</div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Token healing: fixing prompt boundaries

The prompt-boundary problem, from the Guidance project's notebook: in training data URLs are tokenized as <code>http</code> + <code>://</code>. A prompt ending in <code>http:</code> ends with a lone <code>:</code> token, which the model almost never saw followed by <code>//</code>. Their example model then produced <code>http: //www…</code>, an invalid URL with a space.
{: .lede}

<div class="visual">
  <div class="steps" id="thSteps"><button data-i="0" class="on">1 · Prompt "http:"</button><button data-i="1">2 · Back up one token</button><button data-i="2">3 · Constrain the next token</button></div>
  <div id="thOut" style="margin-top:12px"></div>
  <div class="infobox" id="thInfo"></div>
</div>

<div class="cite">guidance-ai/guidance, "Prompt boundaries and token healing" notebook. Token healing "automatically backs up the generation process by one token before the end of the prompt", then constrains the first generated token to start with the removed text.</div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why each quirk happens

<div class="grid2">
  <div class="card a"><h3>Spelling</h3><p>The ids are opaque, so character knowledge exists only to the extent the model learned each token's spelling.</p></div>
  <div class="card b"><h3>Arithmetic</h3><p>Digits come in irregular chunks (gpt2: 123|45|678; cl100k: 123|456|78), so place value isn't aligned across numbers. Llama 1/2 split every digit, and cl100k/o200k cap groups at 3.</p></div>
  <div class="card c"><h3>Spaces and case</h3><p>"hello", " hello" and "Hello" are different ids with separately learned embeddings. Whitespace is part of the token.</p></div>
  <div class="card e"><h3>Glitch tokens</h3><p>The tokenizer is trained separately from the model, so some vocabulary tokens barely appear in model training. Their embeddings stay under-trained and inputs containing them can trigger strange outputs (Land &amp; Bartolo, 2024).</p></div>
</div>

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

<div class="quiz myth">
  <p class="qq">"LLMs read text letter by letter."</p>
  <button class="reveal">Why is this wrong?</button>
  <div class="why">They read <b>token ids</b>. In cl100k_base, " strawberry" is a single id.</div>
</div>

::: reveal myth
? "A trailing space in a prompt is harmless."
> In GPT-style tokenizers a space usually starts the <b>next</b> token. A trailing space leaves the model with an unusual lone-space token, which changes what it predicts.
:::

::: reveal myth
? "Every token in the vocabulary was well trained."
> Some tokens are <b>under-trained</b>: present in the vocabulary but nearly absent from model training. " SolidGoldMagikarp" is the famous example, a single token in GPT-2's tokenizer.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

<div class="quiz">
  <p class="qq">How does cl100k_base tokenize "12345678"?</p>
  <div class="opts">
  <button>A. 1|2|3|4|5|6|7|8</button>
  <button data-ok>B. 123|456|78</button>
  <button>C. 12345678</button>
  <button>D. 1234|5678</button>
  </div>
  <div class="why"><b>123|456|78</b>: its pre-tokenizer splits numbers into groups of at most 3 digits.</div>
</div>

::: quiz
? What does token healing do?
- [ ] Fixes typos in the prompt
- [x] Removes the last prompt token and constrains the next generated token to start with that text
- [ ] Retrains bad tokens
- [ ] Adds spaces
> It <b>backs up one token</b> and constrains generation to start with the removed text, so the model can produce its natural token (e.g. "://").
:::

<div class="quiz ">
  <p class="qq">Why do under-trained ("glitch") tokens exist at all?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">The tokenizer is built <b>separately</b> from model training, on different data, so some vocabulary entries are rare or absent in the model's training data and their embeddings are barely trained (Land &amp; Bartolo, 2024).</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">LLMs see token ids, not characters. Spelling, arithmetic, spacing and prompt-boundary quirks, and glitch tokens, all follow from how text was tokenized.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>A model receives token ids, so character-level facts like spelling or letter counts are hidden inside opaque tokens: in cl100k_base, " strawberry" is one id. Numbers are chunked irregularly, leading spaces and capitalization change ids, and a prompt that ends mid-token (like "http:") puts the model at a boundary it rarely saw, which token healing fixes by backing up a token and constraining the next. Some tokens, such as GPT-2's " SolidGoldMagikarp", are under-trained because the tokenizer was built on different data from the model.</p></div>

<div class="recap"><div><span><b>Problem:</b> surprising failures on character-, number- and boundary-sensitive inputs.</span></div><div><span><b>Core idea:</b> the model sees ids, not characters; inspect the tokens and fix boundaries (e.g. token healing).</span></div></div>

<p class="start-hint">You've finished the series. <a href="../playground/index.html">Try the live tokenizer playground →</a> · Previous: <a href="../09-multilingual-cost/index.html">← 09</a> · <a href="../index.html">All decks</a> · <a href="../playground/index.html">Playground</a></p>

<!-- slide id="s-papers" from="papers" -->
