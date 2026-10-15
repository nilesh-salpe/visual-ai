---
title: Decoding Strategies
body:
  data-deck: Decoding strategies
  data-home: ../index.html
  data-home-label: Inference
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'logits :: one score per token :: f'
  - 'penalties :: repetition · frequency · presence :: d'
  - 'temperature :: sharpen or flatten :: b'
  - 'truncate :: min-p · top-k · top-p :: a'
  - 'sample :: or argmax if T = 0 :: e'
  caption: 'The order vLLM v0.31.0 applies: penalties, temperature, min-p, top-k and top-p, then sample.'
example:
  title: 'Worked example: one step, four rules'
  setup: Five candidate tokens with probabilities 0.50, 0.25, 0.15, 0.06 and 0.04 at temperature 1.
  steps:
  - Top-k = 2 keeps 0.50 and 0.25 and renormalises them to 0.67 and 0.33.
  - 'Top-p = 0.9: the cumulative sums are 0.50, 0.75, 0.90, so the first three survive (the token that reaches 0.9 is included), renormalised to 0.56, 0.28, 0.17.'
  - 'Min-p = 0.1: the threshold is 0.1 × 0.50 = 0.05, so 0.50, 0.25, 0.15 and 0.06 survive and 0.04 is dropped.'
  - 'Temperature 0.5 first: probabilities become proportional to p², giving 0.74, 0.18, 0.07, 0.01, 0.005. Now top-p = 0.9 keeps only two tokens (0.74 + 0.18 = 0.92).'
  result: Temperature changes the shape; truncation decides which tokens can be drawn at all. Because temperature comes first, it changes what top-p keeps.
traps:
  tricks:
  - 'Temperature 0 means greedy. :: In vLLM any temperature below 1e-5 switches to argmax, and n must then be 1.'
  - 'Adaptive beats fixed. :: A fixed k is too many tokens when the model is sure and too few when it is not; top-p and min-p follow the distribution.'
  - 'Match the rule to the task. :: Greedy or beam search for short closed outputs (extraction, translation); sampling with truncation for open-ended text.'
  traps:
  - 'Expecting temperature 0 to be deterministic. :: 1,000 greedy runs of a Qwen3-235B model gave 80 distinct completions, because kernels depend on batch size.'
  - 'Beam search for open-ended text. :: Maximising likelihood leads to bland, repetitive text (Holtzman et al.).'
  - 'Strong repetition penalties. :: They also suppress tokens that should repeat (names, code identifiers); vLLM''s repetition penalty counts prompt tokens too.'
papers:
- holtzman
- topk_fan
- ctrl
- minp
- minp_critique
- vllm_sampling
- claude_messages_api
- oai_latest_model
- tm_nondeterminism
- xgrammar
status:
  label: current
  reviewed: '2026-10-15'
  note: Checked against vLLM v0.31.0 source and the Claude and OpenAI API docs (2026-10-15).
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">LLM Inference &amp; Serving · 11</div>
    <h1>Decoding: from probabilities to text</h1>
    <p class="sub">How the next token is chosen from the model's probabilities: greedy and beam search, temperature, top-k, top-p and min-p, repetition penalties, the order a serving engine applies them, and why temperature 0 is still not deterministic.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>At every step the model gives a probability for each token in its vocabulary, and something has to pick one. Always taking the most likely token produces bland, repetitive text; sampling from the full distribution wanders into the unreliable tail and produces incoherent text.</div>
      <div class="c"><b>Core idea</b>Decoding is a <b>rule for choosing from the next-token distribution</b>. <b>Greedy</b> and <b>beam search</b> maximise likelihood, which suits short, closed answers. For open-ended text, <b>reshape</b> the distribution with <b>temperature</b>, <b>cut its tail</b> with <b>top-k</b>, <b>top-p</b> (nucleus) or <b>min-p</b>, then sample. <b>Penalties</b> discourage repeats. Serving engines apply these steps in a fixed order, for every sequence in the batch.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## The model gives probabilities, not words

At every step the model outputs one score (logit) for every token in the vocabulary; softmax turns them into probabilities. Generation is a long chain of choices from these distributions.
            {: .lede}

::: cards grid3
### [f] A choice per token
Hundreds of choices for a paragraph, each from a distribution over the whole vocabulary.

### [d] Maximising is bland
Holtzman et al.: beam search (size 32) on GPT-2 Large produced degenerate repetition; the probability of a repeated phrase rises with each repetition.

### [b] Pure sampling is incoherent
The long tail of unlikely tokens has substantial mass in total, so full sampling regularly draws a token that derails the text.
:::

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why one rule does not fit every step

::: cards grid3
### [d] Fixed k
Top-k with k = 10 (Fan et al. 2018, story generation) keeps ten tokens whether the model has one sensible choice or hundreds.

### [b] Temperature alone
Lowering temperature removes tail mass everywhere but also removes diversity; raising it brings the incoherence back.

### [c] Repetition loops
Once a phrase repeats, repeating it again becomes more likely (Holtzman et al., Figure 4), so greedy text gets stuck.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Which tokens does top-p keep?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Probabilities are 0.50, 0.25, 0.15, 0.06 and 0.04, and top_p = 0.8. Which tokens can be sampled?
- [ ] Only the 0.50 token
- [ ] The 0.50 and 0.25 tokens
- [x] The 0.50, 0.25 and 0.15 tokens
- [ ] All five
> **C.** Sort by probability and keep the smallest set whose cumulative probability reaches p: 0.50 + 0.25 = 0.75 is below 0.8, so the 0.15 token is needed (0.90). Then renormalise.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Reshape, cut the tail, sample

::: cards grid2
### [f] Greedy and beam search
Take the argmax, or keep the B most likely partial sequences by total log-probability. Good for short, closed outputs; degenerates on open-ended text.

### [b] Temperature T
Divide the logits by T before softmax, so probabilities become proportional to p^(1/T). T &lt; 1 sharpens, T &gt; 1 flattens, T → 0 is greedy.

### [a] Truncation
<b>Top-k</b>: the k most likely tokens. <b>Top-p</b> (nucleus): the smallest set with cumulative probability ≥ p. <b>Min-p</b>: tokens with p ≥ min_p × p_max, so the cut scales with the model's confidence.

### [d] Penalties
<b>Repetition penalty</b> (CTRL, θ ≈ 1.2 with greedy decoding): divide a seen token's positive logit by θ. <b>Frequency</b> and <b>presence</b> penalties subtract an amount per count and per occurrence.
:::

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## One decoding step <span class="ill">interactive</span>

<div class="visual"><div class="controls"><label class="ctl">temperature <input type="range" id="dT" min="0" max="2" step="0.05" value="1"> <output id="dTo"></output></label><label class="ctl">top-k <input type="range" id="dK" min="0" max="10" step="1" value="0"> <output id="dKo"></output></label><label class="ctl">top-p <input type="range" id="dP" min="0.3" max="1" step="0.05" value="1"> <output id="dPo"></output></label><label class="ctl">min-p <input type="range" id="dM" min="0" max="0.5" step="0.01" value="0"> <output id="dMo"></output></label></div><div class="bars"><div id="dBars"></div></div><p class="readout" id="dOut"></p></div>

The distribution is illustrative. Applied in vLLM's order: temperature, then min-p, then top-k and top-p, then renormalise and sample.

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Inside a serving engine

::: table
| Parameter | vLLM default | What it does |
|---|---|---|
| `temperature` | 1.0 | divides logits; below 1e-5 means greedy (then `n` must be 1) |
| `top_k` | 0 (off) | keep the k most likely tokens |
| `top_p` | 1.0 (off) | keep the smallest set with cumulative probability ≥ p |
| `min_p` | 0.0 (off) | keep tokens with p ≥ min_p × p_max |
| `repetition_penalty` | 1.0 (off) | scales logits of tokens seen in the prompt **or** the output |
| `frequency_penalty`, `presence_penalty` | 0.0 (off) | subtract per count / per occurrence, output tokens only (OpenAI definition) |
| `seed` | none | per-request random seed |
:::

**Hosted reasoning models fix these knobs.** On the Claude API, `temperature`, `top_p` and `top_k` are deprecated: models released after Claude Opus 4.6 reject any non-default value with a 400 error [[legacy]]. OpenAI's latest-model guide says to remove `temperature` and `top_p` when reasoning effort is not none. The knobs matter most when you serve open models yourself.

::: deep Constrained decoding
Structured output (JSON schemas, grammars) is also a decoding step: before sampling, a grammar engine such as XGrammar sets the logits of every token that would break the grammar to −∞, so only valid continuations can be drawn. See the serving-for-agents deck in Visual Agents.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why truncation works, and what it cannot fix

::: cards grid2
### [a] The tail is unreliable
Each tail token is unlikely, but together they are drawn often; cutting the tail removes most incoherent draws (Holtzman et al.).

### [c] Adaptive cut
Top-p and min-p keep few tokens when the distribution is peaked and many when it is flat. In the notebook's 1,000-token example, as T goes from 0.5 to 1.6, top-p 0.9 keeps 4 → 739 tokens and min-p 0.1 keeps 2 → 28.

### [b] Disputed: min-p vs top-p
Nguyen et al. (ICLR 2025) report min-p improves quality and diversity at high temperature. Schaeffer et al. (2025) re-analysed the evidence and found no improvement once hyperparameter tuning is controlled. Treat it as one more option, not a default.

### [e] Greedy is not reproducible by default
Floating-point sums depend on batch size. With batch-invariant kernels, all 1,000 temperature-0 completions matched (Thinking Machines).
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Temperature 0 gives the same output every time."
> Thinking Machines sampled 1,000 completions at temperature 0 and got 80 distinct ones; they first diverged at token 103. The Claude API documentation also notes temperature 0.0 is not fully deterministic.
:::

::: reveal myth
? "The most likely sequence is the best text."
> Holtzman et al.: maximisation is an inappropriate objective for open-ended generation; beam search text is bland and repetitive.
:::

::: reveal myth
? "Min-p has been shown to beat top-p."
> The original paper reports gains; a 2025 re-analysis found none when tuning effort is equalised. Sources disagree.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? With vLLM's defaults (temperature 1.0, top_p 1.0, top_k 0, min_p 0.0), how is the next token chosen?
- [ ] Greedy
- [x] Sampled from the full softmax distribution
- [ ] Top-50 sampling
- [ ] Beam search
> **B.** All truncation is off and temperature is 1, so it samples from the unmodified distribution. Set the parameters explicitly for your use case.
:::

::: reveal
? Why does lowering the temperature change what top-p keeps?
> Temperature is applied before truncation. A sharper distribution reaches the cumulative threshold with fewer tokens.
:::

::: reveal
? With min-p = 0.1, what is the cut when the top token has probability 0.9? And 0.2?
> Thresholds 0.09 and 0.02. When the model is confident only a few tokens survive; when it is unsure, many do.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Decoding turns probabilities into text: maximise for short closed answers; for open-ended text, reshape with temperature, cut the unreliable tail, then sample.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>At each step the model outputs a distribution over the vocabulary. Greedy decoding and beam search pick the most likely continuation, which is right for short closed answers but makes open-ended text bland and repetitive. Sampling instead divides the logits by a temperature and truncates the unreliable tail with top-k, top-p (the smallest set reaching cumulative probability p) or min-p (tokens above a fraction of the top probability). vLLM applies penalties, then temperature, then min-p, then top-k and top-p. Hosted reasoning models increasingly fix these parameters, and even temperature 0 is not deterministic without batch-invariant kernels.</p></div>
    <div class="recap"><div><span><b>Maximise:</b> greedy and beam search, for closed tasks</span></div><div><span><b>Reshape:</b> temperature: p^(1/T)</span></div><div><span><b>Truncate:</b> top-k, top-p, min-p</span></div><div><span><b>In practice:</b> fixed order in engines; hosted reasoning models fix these knobs</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/inference/13_decoding.ipynb" target="_blank" rel="noopener">13 · Decoding: temperature, top-k, top-p, min-p and beam search</a> <span style="color:var(--faint)">· 40 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/inference/13_decoding.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">You've finished the series. <a href="../../build-it/index.html">See all Build-it notebooks →</a> · Previous: <a href="../10-putting-it-together/index.html">← 10</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
