---
title: Reasoning Models and Thinking Budgets
body:
  data-deck: Reasoning models and thinking budgets
  data-home: ../index.html
  data-home-label: Reasoning
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'RL on checkable tasks :: reward = correct answer :: a'
  - 'long chains emerge :: reflect · verify :: b'
  - 'control at inference :: budget · effort :: c'
  - 'limits :: overthinking · faithfulness :: d'
  caption: Reasoning models learn to use test-time compute; you decide how much to give them.
example:
  title: 'Worked example: what does thinking cost?'
  setup: A request produces 300 answer tokens; with deep thinking it also produces 6,000 thinking tokens. The model streams 80 output tokens per second.
  steps:
  - 'Without thinking: 300 output tokens, about 300 / 80 ≈ <b>4 s</b> of generation.'
  - 'With thinking: 6,300 output tokens, about <b>79 s</b>, and about 21× the output-token bill (thinking tokens are billed as output).'
  - 'If the question is easy, the extra 6,000 tokens buy nothing: that is overthinking.'
  - Use lower effort (or a smaller budget) for easy traffic and high effort only where accuracy pays for it.
  result: Thinking is test-time compute you pay for in latency and tokens; route it to the requests that need it.
traps:
  tricks:
  - 'Verifiable rewards scale. :: Math and code answers can be checked automatically, so RL needs no human labels per step.'
  - 'Budget forcing. :: Appending "Wait" when the model tries to stop made s1-32B check and fix its answers (AIME24 50% → 57%).'
  - 'Read the usage fields. :: Claude reports thinking tokens in usage.output_tokens_details.thinking_tokens.'
  traps:
  - 'Trusting the chain as an audit log. :: Claude 3.7 Sonnet mentioned hints it used only 25% of the time, DeepSeek R1 39%.'
  - 'Maximum effort everywhere. :: Overthinking spends compute on "2 + 3" with no gain.'
  - 'Pinning old API parameters. :: On newer Claude models fixed budget_tokens is deprecated or rejected; use adaptive thinking with an effort level.'
papers:
- r1
- s1
- overthinking
- cot_faithful
- claude_thinking
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Reasoning and test-time compute · 04</div>
    <h1>Reasoning models and thinking budgets</h1>
    <p class="sub">Models trained to think at length before answering: reinforcement learning on verifiable rewards, budget forcing, thinking controls in APIs, and the limits (overthinking, unfaithful reasoning, cost).</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Prompting and sampling get more out of a model that was never trained to reason at length. To use test-time compute well, the model itself must learn to explore, check and correct its work, and users need a way to control how much it thinks.</div>
      <div class="c"><b>Core idea</b>Train long chains of thought with <b>reinforcement learning on verifiable rewards</b> (math answers, tests): DeepSeek-R1-Zero went from 15.6% to 77.9% pass@1 on AIME 2024, and reflection and self-verification emerged. Even small supervised datasets plus <b>budget forcing</b> (s1: 1,000 examples; "Wait" to extend thinking) give test-time scaling. APIs expose thinking as a <b>controllable budget or effort level</b>; thinking tokens are billed as output.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Prompting can only go so far

Chain-of-thought prompting and sampling squeeze more out of an ordinary model. But the model was trained to imitate text, not to explore, check its work and backtrack over thousands of tokens.
            {: .lede}

::: cards grid3
### [d] Short habits
Pretrained models stop after a plausible-looking chain.

### [b] No self-correction
They rarely notice and fix their own mistakes unless trained to.

### [c] Uncontrolled cost
Users need to decide how much thinking a request deserves.
:::

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## What sampling alone does not give you

::: cards grid3
### [d] Independent samples
Each sample starts over; none learns from another's mistakes.

### [b] Selection limits
Without a perfect verifier, accuracy plateaus below coverage (deck 02).

### [c] Human-labelled reasoning is scarce
Supervising long chains step by step with people is expensive.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## What can RL reward?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? DeepSeek-R1-Zero was trained with reinforcement learning without human-written reasoning traces. What could the reward be based on?
- [ ] Human ratings of every step
- [x] Whether the final answer is correct (plus a format check), which can be verified automatically
- [ ] The length of the chain
- [ ] Agreement with GPT-4
> **B.** Rule-based accuracy and format rewards on tasks with checkable answers; the long, self-checking chains emerged from optimising them.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Train the thinking, then control it

::: cards grid2
### [f] RL on verifiable rewards
R1-Zero: AIME 2024 pass@1 15.6% → 77.9%; self-reflection, verification and strategy changes emerged without human-labelled traces. R1 adds cold-start data and a multi-stage pipeline.

### [a] Cheap test-time scaling (s1)
Finetune Qwen2.5-32B on 1,000 curated traces; budget forcing ends thinking early or appends "Wait" to extend it. s1-32B beat o1-preview by up to 27% on MATH and AIME24.

### [c] Thinking controls in APIs
Claude: adaptive thinking with an effort level on newer models (fixed budget_tokens, minimum 1,024, on older ones); thinking tokens count as billed output.

### [e] Interleaved thinking
In agent loops the model can think between tool calls, reasoning about each result before the next action.
:::

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## The cost of thinking <span class="ill">calculator</span>

<div class="visual"><div class="controls"><label class="ctl">answer tokens <input type="range" id="tA" min="50" max="2000" step="50" value="300"> <output id="tAo"></output></label><label class="ctl">thinking tokens <input type="range" id="tT" min="0" max="32000" step="500" value="6000"> <output id="tTo"></output></label><label class="ctl">tokens / second <input type="range" id="tS" min="20" max="200" step="10" value="80"> <output id="tSo"></output></label></div><div class="bars"><div id="tBars"></div></div><p class="readout" id="tOut"></p></div>

For thinking budgets above 32k tokens, Anthropic recommends batch processing, because such long requests can hit timeouts and connection limits.

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works, and where it stops

::: cards grid2
### [a] Learned search
RL rewards chains that end correctly, so the model learns to explore alternatives and check itself within one chain.

### [c] Compute on demand
Longer thinking on harder problems uses test-time compute adaptively.

### [b] Overthinking
o1-like models spend far more tokens than needed on simple problems such as "2 + 3", with minimal benefit; self-training can shorten chains without losing accuracy.

### [d] Unfaithful chains
Chains often omit what drove the answer; reward hacking rose under RL without being verbalised more. Chain-of-thought monitoring helps but cannot rule out bad behaviour.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "A reasoning model's chain of thought shows exactly why it answered."
> Anthropic found chains revealed hints the model used only 25% (Claude 3.7 Sonnet) and 39% (DeepSeek R1) of the time.
:::

::: reveal myth
? "Reasoning models need huge human-written reasoning datasets."
> R1-Zero used RL with rule-based rewards; s1 used only 1,000 curated examples.
:::

::: reveal myth
? "More thinking always helps."
> Gains diminish, and easy questions gain nothing while latency and cost grow.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? What does budget forcing do in s1?
- [ ] Limits the prompt length
- [x] Ends thinking at a budget or appends "Wait" to make the model keep thinking
- [ ] Removes the chain of thought
- [ ] Trains a reward model
> **B.** It controls test-time compute directly; extending with "Wait" often made the model double-check and fix answers.
:::

::: reveal
? How are thinking tokens billed on the Claude API?
> As output tokens; the usage field output_tokens_details.thinking_tokens reports how many of the billed output tokens were reasoning.
:::

::: reveal
? Why is chain-of-thought monitoring not sufficient for safety?
> Chains are often unfaithful: models use information or hacks without mentioning them, so a monitor can miss rare harmful behaviour.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Reasoning models are trained to spend test-time compute well; your job is to give them the right amount and not to over-trust what they write.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>DeepSeek-R1-Zero applied reinforcement learning with rule-based rewards directly to a base model: AIME 2024 pass@1 rose from 15.6% to 77.9%, and behaviours like reflection and verification emerged. s1 showed a cheap recipe: supervised finetuning on 1,000 curated reasoning traces plus budget forcing, which appends "Wait" to extend thinking (AIME24 50% → 57%). In APIs, thinking is a dial: Claude's newer models use adaptive thinking with an effort level, thinking tokens are billed as output. Limits: models overthink easy problems, and their chains are often unfaithful, mentioning hints they used only 25% (Claude 3.7 Sonnet) to 39% (DeepSeek R1) of the time.</p></div>
    <div class="recap"><div><span><b>Training:</b> RL on verifiable rewards grows long chains</span></div><div><span><b>Cheap recipe:</b> s1: 1,000 examples + budget forcing</span></div><div><span><b>Control:</b> budget or effort; billed as output</span></div><div><span><b>Limits:</b> overthinking, unfaithful chains</span></div></div>
    <p class="start-hint">You've finished the series. <a href="../../build-it/index.html">See all Build-it notebooks →</a> · Previous: <a href="../03-verifiers-and-search/index.html">← 03</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
