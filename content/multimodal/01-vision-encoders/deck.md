---
title: 'Vision Encoders: ViT and CLIP'
body:
  data-deck: 'Vision encoders: ViT and CLIP'
  data-home: ../index.html
  data-home-label: Multimodal
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'image :: H × W × 3 pixels :: f'
  - 'patches :: 16 × 16 → tokens :: a'
  - 'ViT encoder :: transformer over patches :: b'
  - 'contrastive :: match image ↔ caption :: c'
  - 'shared space :: zero-shot by text :: e'
  caption: Patches make images sequences; contrastive training makes them speak the language of text.
example:
  title: 'Worked example: zero-shot classification with CLIP'
  setup: Classify a photo as dog, cat or car without training a classifier.
  steps:
  - 'Write one prompt per class: "a photo of a dog", "a photo of a cat", "a photo of a car", and embed each with the text encoder.'
  - Embed the photo with the image encoder; normalise all vectors.
  - Compute the cosine similarity between the photo and each prompt; the highest wins.
  - This is how CLIP matched the original ResNet-50 on ImageNet zero-shot, without using any of its 1.28 million training examples.
  result: With a shared embedding space, a class is just a sentence.
traps:
  tricks:
  - 'Tokens = (H/p) × (W/p). :: 224 px with 16 px patches → 14 × 14 = 196 patch tokens (+1 class token in ViT).'
  - 'Contrastive = batch classification. :: Each image must pick its own caption out of the batch, and each caption its image.'
  - 'Sigmoid loss scales easily. :: SigLIP scores each pair independently, so no batch-wide normalisation is needed.'
  traps:
  - 'Forgetting resolution cost. :: Halving the patch size quadruples the token count.'
  - 'ViT on small data. :: ViT shines when pretrained at scale (ImageNet-21k, JFT-300M); from scratch on small data CNNs win.'
  - 'Assuming CLIP reads text in images well. :: Its strengths and weaknesses vary widely across the 30+ datasets evaluated.'
papers:
- vit
- clip
- siglip
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Multimodal LLMs · 01</div>
    <h1>Vision encoders: ViT and CLIP</h1>
    <p class="sub">How images become sequences a transformer can read (patches), and how contrastive training on image-caption pairs gives encoders that line up with language: ViT, CLIP and SigLIP.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>A language model reads tokens. An image is a grid of millions of pixel values with no tokens, and classic vision models were trained to predict a fixed list of labels, so their features do not connect to the open vocabulary of language.</div>
      <div class="c"><b>Core idea</b>Cut the image into <b>patches</b> (16 × 16 pixels in ViT) and treat each as a token: a 224 × 224 image becomes 196 tokens. Train the encoder <b>contrastively</b> against text: CLIP learns to tell which caption goes with which image across a batch, from 400 million internet pairs, so image and text embeddings share one space and classes can be named in words (zero-shot).</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Pixels are not tokens

A 1,000 × 1,000 photo is three million numbers. A language model expects a sequence of a few thousand token embeddings at most.
            {: .lede}

::: cards grid3
### [d] No tokens
Images have no natural vocabulary or word boundaries.

### [b] Fixed labels
Classic classifiers predict a predetermined set of categories; naming a new concept needs new labelled data.

### [c] Separate spaces
Image features and word embeddings were trained apart, so they do not line up.
:::

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## What earlier vision models lacked

::: cards grid3
### [d] CNN inductive biases
Convolutions build in locality, but tie vision to an architecture separate from language models.

### [b] Label bottleneck
ImageNet's 1.28 million labelled images cover 1,000 classes.

### [c] Poor transfer by name
You cannot ask a label classifier about "a corgi wearing sunglasses".
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## How many tokens?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? A ViT reads 224 × 224 RGB images with 16 × 16 patches. How many patch tokens does one image produce?
- [ ] 224
- [x] 196
- [ ] 50,176
- [ ] 768
> **B.** (224 / 16)² = 14² = 196 patches; each patch flattens to 16 × 16 × 3 = 768 values before the linear projection.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Patches, then contrastive alignment

::: cards grid2
### [f] ViT
Split into 16 × 16 patches, linearly embed, add positions and a [class] token, run a standard transformer. Pretrained on ImageNet-21k or JFT-300M, it reached 88.55% on ImageNet with less training compute than comparable CNNs.

### [a] CLIP
Train image and text encoders to predict which caption goes with which image in a batch; 400 million internet pairs; evaluated on over 30 datasets.

### [c] Zero-shot transfer
Classify by comparing an image with text prompts for each class: CLIP matched the original ResNet-50 on ImageNet without its 1.28M training labels.

### [e] SigLIP
A pairwise sigmoid loss needs no batch-wide softmax: 84.5% zero-shot ImageNet with 4 TPUv4 chips in 2 days; batches beyond 32k gave little extra benefit.
:::

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## From image to tokens <span class="ill">interactive</span>

<div class="visual"><div class="controls"><label class="ctl">image side <input type="range" id="pS" min="112" max="672" step="112" value="224"> <output id="pSo"></output></label><label class="ctl">patch size <input type="range" id="pP" min="8" max="32" step="2" value="16"> <output id="pPo"></output></label></div><svg id="pSvg" viewBox="0 0 600 260" class="ill-svg"></svg><p class="readout" id="pOut"></p></div>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works

::: cards grid2
### [a] Language as supervision
Captions name millions of concepts for free; the web supplies the labels.

### [c] Shared space
Matching pairs pulled together, mismatches pushed apart, so text can query images and vice versa.

### [b] Scale over bias
With enough data, a plain transformer learns the spatial structure CNNs had built in.

### [e] Reusable encoders
CLIP-style encoders became the eyes of many vision-language models (deck 02).
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Vision transformers need convolutions."
> ViT is a pure transformer over patches; with large-scale pretraining it matches or beats CNNs.
:::

::: reveal myth
? "CLIP was trained on ImageNet labels."
> It was trained on 400M image-text pairs from the internet; its ImageNet result is zero-shot.
:::

::: reveal myth
? "Contrastive learning needs huge batches forever."
> SigLIP found benefits diminish quickly; 32k was sufficient.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? What is CLIP's training objective?
- [ ] Predict the next pixel
- [x] Pick the matching caption for each image (and image for each caption) within a batch
- [ ] Classify 1,000 ImageNet classes
- [ ] Reconstruct the image
> **B.** A symmetric contrastive loss over the batch.
:::

::: reveal
? How does zero-shot classification with CLIP work?
> Embed a text prompt per class and the image; predict the class with the highest cosine similarity.
:::

::: reveal
? What does SigLIP change?
> It replaces the softmax over the batch with an independent sigmoid on each image-text pair, which decouples the loss from batch size.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">A vision encoder turns an image into patch tokens; contrastive training puts those tokens in the same space as language.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>A Vision Transformer splits an image into fixed-size patches (16 × 16 pixels), embeds each with a linear projection, adds positions and runs a standard transformer; a 224 × 224 image is 196 patch tokens. Pretrained at scale, ViT reached 88.55% on ImageNet. CLIP trains an image encoder and a text encoder together to pick the matching caption among a batch, on 400 million image-text pairs; the shared space allows zero-shot classification, matching ResNet-50 on ImageNet without its training labels. SigLIP replaces the softmax with a pairwise sigmoid loss and reached 84.5% zero-shot ImageNet with four TPUv4 chips in two days.</p></div>
    <div class="recap"><div><span><b>Patches:</b> images as token sequences</span></div><div><span><b>ViT:</b> a plain transformer over patches</span></div><div><span><b>CLIP:</b> contrastive image-text training, 400M pairs</span></div><div><span><b>Zero-shot:</b> classes named by text prompts</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/multimodal/01_images_as_tokens.ipynb" target="_blank" rel="noopener">01 · Images as tokens: patches, CLIP loss, zero-shot and token cost</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/multimodal/01_images_as_tokens.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../02-vision-language-models/index.html">02 · Connecting vision to an LLM →</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
