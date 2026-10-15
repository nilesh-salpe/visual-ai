---
title: Images as Tokens in Practice
body:
  data-deck: Images as tokens in practice
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
  - 'image :: w × h pixels :: f'
  - 'resize? :: tier limits :: b'
  - 'visual tokens :: ⌈w/28⌉ × ⌈h/28⌉ :: a'
  - 'context + cost :: like text tokens :: c'
  - 'evaluate :: MMMU · hallucination :: d'
  caption: Every image is a bill in tokens; resolution decides the size.
example:
  title: 'Worked example: a screenshot-heavy agent'
  setup: A computer-use agent sends a 1920 × 1080 screenshot every step for 30 steps.
  steps:
  - 'Standard tier: the screenshot is downsized to 1456 × 819, which costs ⌈1456/28⌉ × ⌈819/28⌉ = 52 × 30 = <b>1,560</b> tokens.'
  - 'High-resolution tier: no downsizing, ⌈1920/28⌉ × ⌈1080/28⌉ = 69 × 39 = <b>2,691</b> tokens.'
  - If every past screenshot stays in the context, step 30 carries 30 × 2,691 ≈ <b>80,700</b> tokens of images.
  - Downsample when the extra detail is not needed, drop or summarise old screenshots, and cache stable prefixes.
  result: Image tokens accumulate in agent loops exactly like tool outputs do.
traps:
  tricks:
  - 'Tokens ≈ pixels / 784. :: One visual token per 28 × 28 patch (Claude API).'
  - 'Images first. :: Claude works best when images come before the text that refers to them.'
  - 'Upload once. :: The Files API avoids resending base64 bytes on every turn.'
  traps:
  - 'Many-image requests. :: Above 20 images per request a stricter per-image size limit applies; keep each side ≤ 2,000 px.'
  - 'Tiny or rotated images. :: Accuracy drops on low-quality images or ones under 200 pixels.'
  - 'Trusting object lists. :: Models often mention objects that frequently co-occur with what is in the image, even when absent.'
papers:
- claude_vision
- whisper
- mmmu
- pope_halluc
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Multimodal LLMs · 03</div>
    <h1>Images as tokens in practice</h1>
    <p class="sub">What multimodal input costs and how it fails: visual-token counts and resolution limits in a production API, many-image requests, audio as another input, benchmarks such as MMMU, and object hallucination.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Images make prompts expensive and slow in ways that are easy to miss: a single screenshot can cost thousands of tokens, and agents resend every image on every turn. Models also describe things that are not in the image.</div>
      <div class="c"><b>Core idea</b>Estimate the <b>visual-token cost</b> of every image: the Claude API counts one token per <b>28 × 28-pixel patch</b> and downsizes images above a <b>tier limit</b> (1,568 px and 1,568 tokens standard; 2,576 px and 4,784 tokens on high-resolution models). Resize before sending, put images before text, and reference repeated images by file. Evaluate on <b>expert multimodal benchmarks</b> (MMMU) and test for <b>object hallucination</b> (POPE).</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## A picture is worth a few thousand tokens

A user uploads ten full-resolution phone photos and asks a question. The request is slow and expensive, and the answer mentions a dog that is not in any photo.
            {: .lede}

            ::: cards grid3
### [d] Hidden cost
Images are converted to many tokens, billed like text input.

### [b] Resizing surprises
Large images are downsized, which can make small text unreadable.

### [c] Hallucination
Vision-language models describe plausible objects that are absent.
:::

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## What the user cannot see

::: cards grid3
### [d] Token count
Pixels do not show how many tokens an image becomes.

### [b] Limits
Per-request image counts, sizes and payload limits differ by platform.

### [c] Evaluation gaps
Captioning-style benchmarks miss expert reasoning and hallucination.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## How many tokens?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Under the Claude API rule of one visual token per 28 × 28 patch, about how many tokens does a 1000 × 1000 image cost (no resizing)?
- [ ] 28
- [ ] 784
- [x] 1,296
- [ ] 1,000,000
> **C.** ⌈1000 / 28⌉² = 36² = 1,296 tokens.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Budget, resize, order, evaluate

::: cards grid2
### [f] Count tokens
Claude: ⌈w / 28⌉ × ⌈h / 28⌉ visual tokens; images above the tier limit (standard 1,568 px / 1,568 tokens, high-resolution 2,576 px / 4,784 tokens) are downscaled keeping aspect ratio.

### [a] Send them well
Images before text; Files API for repeated images; up to 600 images per request (100 on 200k-context models), with stricter size limits above 20.

### [c] Other modalities
Audio is converted to model inputs the same way; Whisper was trained on 680,000 hours of multilingual, multitask audio and transfers zero-shot.

### [e] Evaluate hard cases
MMMU: 11.5K college-level questions across 30 subjects and 30 image types; GPT-4V 56%, Gemini Ultra 59%. POPE probes object hallucination with yes/no polling.
:::

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Image token calculator <span class="ill">Claude API rule</span>

<div class="visual"><div class="controls"><label class="ctl">width <input type="range" id="iW" min="200" max="4000" step="40" value="1920"> <output id="iWo"></output></label><label class="ctl">height <input type="range" id="iH" min="200" max="4000" step="40" value="1080"> <output id="iHo"></output></label><label class="ctl">images in context <input type="range" id="iN" min="1" max="50" step="1" value="1"> <output id="iNo"></output></label></div><div class="bars"><div id="iBars"></div></div><p class="readout" id="iOut"></p></div>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why these limits and failures exist

::: cards grid2
### [a] Attention cost
Every visual token is attended to like text, so resolution is capped to bound compute.

### [c] Detail vs budget
High-resolution tiers use up to about three times more tokens; worth it for screenshots and dense documents.

### [b] Language priors
Hallucinated objects tend to be ones that occur often in training instructions or co-occur with real objects.

### [e] Benchmarks shape progress
Expert-level, diverse image types (charts, maps, chemical structures) expose gaps that captioning hides.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Image cost depends on file size."
> It depends on pixel dimensions after resizing, not on bytes or format.
:::

::: reveal myth
? "Sending a higher resolution is always better."
> Above the tier limit the image is downsized anyway; below it, more pixels cost more tokens for detail you may not need.
:::

::: reveal myth
? "If the model names an object, it is in the image."
> POPE showed severe object hallucination across vision-language models.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? A 1920 × 1080 screenshot on a high-resolution Claude model costs how many visual tokens?
- [ ] 1,560
- [x] 2,691
- [ ] 4,784
- [ ] 2,073,600
> **B.** No downsizing: ⌈1920/28⌉ × ⌈1080/28⌉ = 69 × 39 = 2,691.
:::

::: reveal
? Give two ways to cut image cost in an agent loop.
> Downsample screenshots, drop or summarise old images, use the Files API instead of resending base64, keep prefixes stable for caching (any two).
:::

::: reveal
? What does POPE measure?
> Object hallucination in vision-language models, by polling yes/no questions about whether objects are present.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Treat images like long text: estimate their tokens, resize them, and check that the model is not seeing things.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>In the Claude API an image costs ⌈width / 28⌉ × ⌈height / 28⌉ visual tokens; images above a model's limits are downscaled (standard tier 1,568 px and 1,568 tokens; high-resolution models 2,576 px and 4,784 tokens). A 1080p screenshot costs 1,560 or 2,691 tokens, and agents that resend screenshots multiply that. Audio follows the same pattern of converting signals into model inputs; Whisper was trained on 680,000 hours of weakly supervised audio. On MMMU, 11.5K college-level multimodal questions, GPT-4V scored 56% and Gemini Ultra 59%. POPE showed vision-language models often hallucinate objects that frequently co-occur with real ones.</p></div>
    <div class="recap"><div><span><b>Cost:</b> ⌈w/28⌉ × ⌈h/28⌉ visual tokens</span></div><div><span><b>Limits:</b> 1,568 / 4,784 tokens by tier</span></div><div><span><b>Benchmarks:</b> MMMU: GPT-4V 56%, Gemini Ultra 59%</span></div><div><span><b>Failure:</b> object hallucination (POPE)</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/multimodal/01_images_as_tokens.ipynb" target="_blank" rel="noopener">01 · Images as tokens: patches, CLIP loss, zero-shot and token cost</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/multimodal/01_images_as_tokens.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">You've finished the series. <a href="../../build-it/index.html">See all Build-it notebooks →</a> · Previous: <a href="../02-vision-language-models/index.html">← 02</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
