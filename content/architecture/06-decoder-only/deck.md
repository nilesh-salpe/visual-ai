---
title: Decoder-only, and Why It Won
body:
  data-deck: Decoder-only, and why it won
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
  - 'tokens 0…T−1 :: one sequence :: f'
  - 'causal stack :: each position sees only the past :: c'
  - 'logits at every position :: predict token t+1 :: a'
  - 'loss on all T :: every token is a target :: e'
  caption: One stack, one mask, one objective; at serving time past K and V never change, so they can be cached.
example:
  title: 'Worked example: training signal per sequence'
  setup: One sequence of 2,048 tokens.
  steps:
  - 'Causal LM: every position predicts its next token → <b>2,047</b> targets.'
  - 'BERT-style masked LM (15% masked): <b>307</b> targets.'
  - 'Encoder-decoder with a 50/50 split: <b>1,024</b> targets, and two stacks.'
  - 'Packed with a document mask: same target count, no attention across documents.'
  result: The causal objective extracts ~6.7× more supervised positions per sequence than 15% masking, from raw text with no labels.
traps:
  tricks:
  - 'Causal mask: j ≤ i. :: Prefix-LM: bidirectional within the prompt, causal after.'
  - 'Pack + document mask. :: Full-length rows with no cross-document attention.'
  - 'Same mask everywhere. :: Pretraining, SFT and serving all use the causal mask.'
  traps:
  - 'Packing without a document mask. :: Tokens attend into unrelated previous documents.'
  - '"Decoders can''t read the input." :: The last position sees the whole prompt.'
  - 'Calling encoder-decoder obsolete. :: Wang et al. found non-causal objectives win after multitask fine-tuning; encoders still lead retrieval.'
papers:
- wang22
- gpt2
- t5
- bert
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">The Modern LLM · 06</div>
    <h1>Decoder-only, and why it won</h1>
    <p class="sub">Encoder-decoder, encoder-only and decoder-only stacks differ mainly in their attention masks. Why the plain causal decoder became the default for LLMs (large language models).</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>The 2017 Transformer has an encoder and a decoder with cross-attention. BERT (Bidirectional Encoder Representations from Transformers) kept only the encoder. GPT kept only the decoder. For one general-purpose model, which shape is best?</div>
      <div class="c"><b>Core idea</b>A <b>causal decoder</b>: one stack, one mask (each token sees only the past), trained to predict the next token at <b>every</b> position. Prompts, documents and answers all live in one sequence.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Three families, one difference: the mask

Every family computes the same attention. What differs is which positions may see which. Each grid shows "row may attend to column" for 8 tokens. In the encoder-decoder, tokens 0–3 are the input and 4–7 the output.
{: .lede}

<div class="visual">
  <div class="seg" id="fSeg"><button data-v="causal" class="on">Causal decoder (GPT, Llama)</button><button data-v="prefix">Prefix-LM (non-causal decoder)</button><button data-v="encdec">Encoder-decoder (T5, 2017)</button><button data-v="enc">Encoder-only (BERT)</button></div>
  <svg id="fSvg" viewBox="0 0 660 250" style="margin-top:10px" role="img" aria-label="Attention mask"></svg>
  <p class="readout" id="fOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## What the other shapes cost

::: cards grid3
### [d] Encoder-only can't generate
BERT sees both directions and is trained to fill in masked tokens (15% of them). Great for classification and retrieval, but there's no natural way to write a long answer token by token.

### [b] Encoder-decoder needs a split
Every example must be cut into "input" and "target", and the two stacks are joined by cross-attention. Chat turns, documents and code don't come with a natural split.

### [c] Fewer training signals per token
Masked-LM objectives compute loss only on the corrupted positions. A causal LM (language model) computes loss on <b>every</b> position of every sequence, so each forward pass yields T training targets.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Which one serves chat most simply?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? A multi-turn chat keeps growing. Which architecture can reuse all previous computation (the KV (key-value) cache) as each new message arrives?
- [ ] Encoder-only
- [ ] Encoder-decoder
- [x] Causal decoder
- [ ] All of them equally
> <b>C.</b> In a causal decoder a token's keys and values depend only on earlier tokens, so they never change when new tokens arrive. Cache once, append forever. An encoder's bidirectional states change whenever the input grows, so they would have to be recomputed.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## The causal decoder recipe

::: cards grid3
### [a] One stack
Embedding → N identical blocks (attention + FFN (feed-forward network)) → output head. No encoder and no cross-attention. Fewer moving parts to tune and to parallelize.

### [e] One objective
Predict token t+1 from tokens ≤ t, at every position, on any text. No labels, no input/target split, so all of the web is training data.

### [b] One sequence for everything
Instructions, documents, few-shot examples, tool calls and answers are all just tokens in context. GPT-2 and GPT-3 showed tasks can be specified in the prompt.
:::

<div class="deep"><h4>Packing and the document mask</h4><p>Pretraining packs many documents back to back into one long sequence, so no compute is wasted on padding. With a plain causal mask, a token can attend into the <b>previous, unrelated</b> document. Llama 3: "we use an attention mask that prevents self-attention between different documents within the same sequence". It had limited impact in standard pretraining but mattered for continued pretraining on very long sequences. Notebook 05 shows a packed batch with this mask gives exactly the same outputs as running each document alone.</p></div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Training signal per sequence

How many positions produce a loss in one forward pass of length T? Compare a causal LM, BERT-style masked LM (15% of tokens) and an encoder-decoder trained on a 50/50 input/target split.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">Sequence length T <input type="range" id="tT" min="128" max="8192" step="128" value="2048"> <output id="tTo"></output></label></div>
  <div id="tBars" style="margin-top:12px"></div>
</div>

<p class="caption">Illustrative counts. Real objectives vary: T5's span corruption predicts about 15% of tokens; prefix-LM computes loss only on the target part.</p>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Same model, three uses

::: cards grid3
### [a] Pretraining
Full causal mask (plus the document mask when packing) over long sequences. Loss on every token.

### [b] Fine-tuning (SFT)
Same causal mask. Prompt and response in one sequence, with the loss usually counted only on response tokens. No architecture change.

### [e] Serving
Prefill the prompt with one causal pass (cache K/V), then decode one token at a time, appending to the cache. Exactly the training computation, done incrementally.
:::

<div class="deep"><h4>What about bidirectional context?</h4><p>A prefix-LM lets prompt tokens see each other in both directions and keeps the generated part causal. Wang et al. found this <b>non-causal decoder with masked-LM pretraining</b> did best after <b>multitask fine-tuning</b>, while the causal decoder did best for zero-shot use after self-supervised pretraining alone. They also showed models can be adapted between the two. The industry chose the simplest shape that scales and serves well, plus instruction tuning.</p></div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why the causal decoder won

::: cards grid2
### [a] Best zero-shot after pretraining alone
Wang et al. (2022): causal decoder-only models trained autoregressively "exhibit the strongest zero-shot generalization after purely unsupervised pretraining".

### [e] Every token is a target
Dense supervision from raw text, with no input/target split, makes it the simplest objective to scale on trillions of tokens.

### [b] Serving is incremental
Past K/V never change, so the KV cache, prefix caching, continuous batching and speculative decoding all fit naturally (Inference decks 02–06).

### [c] One interface for every task
Prompting turns any task into "continue this text", so one model and one serving stack cover translation, coding, chat and tool use.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Decoder-only models can't "understand" the input because they only look left."
> Every prompt token sees all earlier prompt tokens, and the <b>last</b> position sees the whole prompt. Bidirectionality inside the prompt (prefix-LM) can help some setups, but it is not required to model the input well.
:::

::: reveal myth
? "Encoder-decoder models are obsolete."
> Wang et al. found non-causal objectives can win after multitask fine-tuning, and encoder-style models remain standard for embeddings and retrieval. Decoder-only is the default for <b>general-purpose generative</b> LLMs.
:::

::: reveal myth
? "A decoder-only Transformer is just the 2017 decoder."
> It drops the 2017 decoder's cross-attention sub-layer entirely. Each block is just masked self-attention plus FFN.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? In a causal mask, query position i may attend to key position j when…
- [ ] j ≥ i
- [x] j ≤ i
- [ ] j = i
- [ ] always
> <b>j ≤ i</b>: itself and the past.
:::

<div class="quiz ">
  <p class="qq">Why do packed pretraining sequences need a document mask?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Without it, tokens attend into earlier, unrelated documents in the same packed sequence. The document mask restricts attention to the same document, making a packed batch equivalent to running each document separately.</div>
</div>

<div class="quiz ">
  <p class="qq">Give two reasons the causal decoder is convenient at serving time.</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Past keys and values never change, so they can be cached and reused (KV cache, prefix caching). And the serving computation is exactly the training computation done incrementally, with no separate encoder pass.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">A causal decoder is one stack, one mask and one objective: predict the next token at every position. Simple to train at scale, and incremental to serve.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Encoder-only, encoder-decoder and decoder-only Transformers mostly differ in their attention mask. The causal decoder lets each token see only the past and trains it to predict the next token at every position, so every token of raw text is a training target and there is no input/target split. At serving time past keys and values never change, so they can be cached, and prompts let one model do any task. Wang et al. found causal decoders give the best zero-shot generalization after plain pretraining, while non-causal variants can win after multitask fine-tuning. When documents are packed together, a document mask stops attention leaking between them.</p></div>

<div class="recap"><div><span><b>Problem:</b> three stack shapes; which one for a general LLM?</span></div><div><span><b>Core idea:</b> causal decoder: one stack, next-token loss on every position, past K/V never change.</span></div><div><span><b>Detail:</b> packing + document mask; prefix-LM is the in-between option.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/architecture/05_attention_masks.ipynb" target="_blank" rel="noopener">05 · Causal, prefix-LM and document masks</a> <span style="color:var(--faint)">· 25 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/architecture/05_attention_masks.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../07-rope-scaling/index.html">07 · Long context I: stretching RoPE →</a> · Previous: <a href="../05-attention-variants/index.html">← 05</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Vaswani et al. 2017; Devlin et al. 2019 (BERT, 15% masking); Raffel et al. 2020 (T5); Radford et al. 2019 (GPT-2); Wang et al. 2022, "What Language Model Architecture and Pretraining Objective Work Best for Zero-Shot Generalization?"; Llama Team 2024 (Llama 3 §3.2, document mask).</p>

<!-- slide id="s-papers" from="papers" -->
