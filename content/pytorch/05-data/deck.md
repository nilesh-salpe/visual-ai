---
title: Data Pipelines for LLMs
body:
  data-deck: Data pipelines for LLMs
  data-home: ../index.html
  data-home-label: PyTorch
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'tokens on disk :: memory-mapped :: f'
  - 'Dataset :: one example :: a'
  - 'collate_fn :: pad / pack, labels :: c'
  - 'DataLoader :: batches, workers, pin_memory :: b'
  - 'GPU :: x.to(device, non_blocking=True) :: e'
  caption: Labels = inputs shifted by one; −100 where no loss should be taken.
example:
  title: 'Worked example: padding vs packing'
  setup: 'Notebook 05: 64 examples with lengths drawn uniformly between 20 and 400 tokens.'
  steps:
  - 'Padded batches of 8 (each padded to its longest example): <b>44%</b> of computed tokens are padding.'
  - 'Batches of 32: <b>48%</b> padding; bigger batches make it worse because the longest example dominates.'
  - 'Packing the same examples into full rows of fixed length: padding falls to at most the tail of the last row.'
  - Packed documents need a document mask (or per-document position ids) so tokens do not attend across document boundaries.
  result: Padding can waste nearly half the compute on varied lengths; packing recovers it.
traps:
  tricks:
  - 'labels = −100 on padding and prompt. :: F.cross_entropy ignores them by default.'
  - 'pin_memory=True + non_blocking. :: Overlaps host-to-GPU copies.'
  - 'num_workers > 0. :: Tokenisation and collation run in parallel processes.'
  traps:
  - 'Padding with a real token id and no mask. :: The model attends to padding.'
  - 'Training on prompt tokens in SFT. :: Usually you mask the prompt to −100.'
  - 'Overlapping windows by accident. :: Inflates epochs and leaks validation data.'
papers:
- pt_data
- pytorch
status: {label: current, reviewed: 2026-10-15, note: "PyTorch 2.14.1 is still the latest release"}
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">PyTorch for LLMs · 05</div>
    <h1>Data pipelines for LLMs</h1>
    <p class="sub">Getting tokens to the GPU: Dataset and DataLoader, fixed windows for pretraining, padding with attention masks and −100 labels for fine-tuning, and sequence packing.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Pretraining consumes a token stream; fine-tuning uses variable-length examples. Batches must be rectangular, padding must not leak into the loss, and the GPU must never wait for data.</div>
      <div class="c"><b>Core idea</b>A <b>Dataset</b> returns one example; a <b>DataLoader</b> batches (with <code>collate_fn</code>), shuffles and prefetches with worker processes. Pretraining cuts the token stream into fixed <b>windows</b>. Fine-tuning <b>pads</b> and marks ignored labels with <b>−100</b> (cross-entropy's default <code>ignore_index</code>). <b>Packing</b> concatenates examples to avoid padding waste.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## How much is padding?

A batch of variable-length sequences. Grey cells are padding the GPU still computes on. Change the batch size, or switch to packing.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">batch size <input type="range" id="dB" min="2" max="16" step="1" value="8"> <output id="dBo"></output></label><div class="seg" id="dSeg"><button data-v="pad" class="on">pad to longest</button><button data-v="pack">pack</button></div></div>
  <svg id="dSvg" viewBox="0 0 660 260" style="margin-top:10px" role="img" aria-label="Padding vs packing"></svg>
  <p class="readout" id="dOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why data loading is tricky

::: cards grid3
### [d] Rectangular batches
GPUs want fixed shapes; real text has every length.

### [b] Loss leakage
Padding or prompt tokens that count in the loss distort training.

### [c] Starving the GPU
Tokenising in the training process makes the GPU wait.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Which label is ignored?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? With F.cross_entropy's defaults, which label value is skipped in the loss?
- [ ] 0
- [ ] −1
- [x] −100
- [ ] the padding token id
> <b>C.</b> ignore_index defaults to −100. Padding token ids are ordinary ids unless their labels are set to −100.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Dataset, collate, DataLoader

::: cards grid3
### [a] Dataset
__len__ and __getitem__: one example, e.g. a window of T + 1 tokens split into inputs and targets.

### [c] collate_fn
Turns a list of examples into tensors: pad, build attention masks and labels, or pack.

### [b] DataLoader
batch_size, shuffle, num_workers, pin_memory, prefetch: keeps the GPU fed.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## One fine-tuning batch

<div class="visual scroll-x"><table class="tbl">
  <tr><th></th><th>example 1</th><th>example 2</th></tr>
  <tr><td>input_ids</td><td>5 6 7</td><td>8 9 <i>PAD</i></td></tr>
  <tr><td>attention_mask</td><td>1 1 1</td><td>1 1 0</td></tr>
  <tr><td>labels (next token)</td><td>6 7 −100</td><td>9 −100 −100</td></tr>
</table></div>
<p class="caption">Exactly what notebook 05's pad_collate returns. The loss averages over the 3 real targets only.</p>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why this design works

::: cards grid2
### [a] Separation of concerns
Datasets know examples; collate knows batching; the loader knows parallelism.

### [e] Exact loss
The −100 convention makes masking a label choice, with no special loss code.

### [b] Throughput
Worker processes and pinned memory overlap data preparation and copies with GPU compute.

### [c] Packing
Fills every position with real tokens; standard for pretraining and common for SFT.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "The attention mask removes padding from the loss."
> It only stops attention to padding; the loss needs labels of −100 at those positions.
:::

::: reveal myth
? "Bigger batches reduce padding waste."
> With padding to the longest example, bigger batches usually waste more (44% → 48% in notebook 05).
:::

::: reveal myth
? "Packing lets documents see each other harmlessly."
> Without a document mask, tokens attend across unrelated documents.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Pretraining window of T inputs needs how many tokens from the stream?
- [ ] T − 1
- [ ] T
- [x] T + 1
- [ ] 2T
> <b>T + 1</b>: inputs are the first T, targets the last T.
:::

::: reveal
? What do pin_memory and non_blocking=True do?
> Allocate page-locked host memory so host-to-GPU copies can run asynchronously, overlapping with compute.
:::

::: reveal
? How do you keep packed documents independent?
> Use a block-diagonal causal mask (or per-document position ids / varlen attention) so attention stays within each document.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">A Dataset returns examples, a collate function pads or packs them with −100 labels where no loss applies, and a DataLoader with workers keeps the GPU fed.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>PyTorch splits data loading into a Dataset that returns one example, a collate function that turns a list of examples into tensors, and a DataLoader that batches, shuffles and prefetches with worker processes. Pretraining cuts a long token stream into windows of T plus one tokens, inputs and shifted targets. Fine-tuning pads examples to a rectangle, builds an attention mask, and sets labels to minus one hundred wherever no loss should count, because that is cross-entropy's default ignore index. Padding can waste nearly half the compute, so packing concatenates examples into full rows with a document mask.</p></div>
    <div class="recap"><div><span><b>Problem:</b> variable lengths, exact loss, fed GPUs.</span></div><div><span><b>Core idea:</b> Dataset → collate → DataLoader; −100 labels.</span></div><div><span><b>Efficiency:</b> pack instead of pad; workers + pinned memory.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/05_data_pipeline.ipynb" target="_blank" rel="noopener">05 · Data: Dataset, DataLoader, padding, masks and packing</a> <span style="color:var(--faint)">· 30 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/05_data_pipeline.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../06-mixed-precision/index.html">06 · Mixed precision in PyTorch →</a> · Previous: <a href="../04-training-loop/index.html">← 04</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
