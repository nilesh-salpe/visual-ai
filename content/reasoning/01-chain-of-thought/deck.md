---
title: Chain of Thought
body:
  data-deck: Chain of thought
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
  - 'question :: multi-step problem :: f'
  - 'reasoning tokens :: intermediate steps :: a'
  - 'each step :: another forward pass :: b'
  - 'answer :: read off at the end :: e'
  caption: More generated tokens = more sequential computation before the answer.
example:
  title: 'Worked example: a word problem, direct vs step by step'
  setup: '"A cafeteria had 23 apples. They used 20 for lunch and bought 6 more. How many apples do they have?" (an exemplar style from the chain-of-thought paper).'
  steps:
  - 'Direct answer: the model must produce "9" in one step, combining both operations implicitly; in the paper''s standard-prompting example the model answers 27.'
  - 'Chain of thought: "They had 23 apples. They used 20, so 23 − 20 = 3. They bought 6 more, so 3 + 6 = 9."'
  - Each line is a simple operation the model can do reliably, and each result is now text in the context for the next step.
  - 'The final answer is read from the end of the chain: <b>9</b>.'
  result: The chain externalises intermediate results, so no single step has to do the whole computation.
traps:
  tricks:
  - 'CoT helps most on multi-step tasks. :: Little gain when a problem takes one or two steps and accuracy is already high.'
  - 'Zero-shot CoT is one line. :: "Let''s think step by step" lifted GSM8K from 10.4% to 40.7% on text-davinci-002.'
  - 'Put the answer last. :: Reasoning first, answer at the end, so the answer can depend on the steps.'
  traps:
  - 'Small models. :: Below about 100B parameters (in 2022 models) chains were fluent but illogical.'
  - 'Answer first, reasons after. :: A justification written after the answer cannot improve it.'
  - 'Treating the chain as an explanation. :: The written steps are not guaranteed to be how the model actually decided (deck 04).'
papers:
- cot
- zeroshot_cot
- gsm8k_verifiers
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Reasoning and test-time compute · 01</div>
    <h1>Chain of thought</h1>
    <p class="sub">Why asking a model to write out intermediate steps makes it better at multi-step problems: few-shot and zero-shot chain-of-thought prompting, when it helps, and what the extra tokens buy.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>A model asked for an answer directly must compute it in a single forward pass per output token. Multi-step problems (arithmetic word problems, logic, planning) need more sequential computation than that, so direct answers fail.</div>
      <div class="c"><b>Core idea</b>Let the model <b>write the intermediate steps</b> before the answer. Each generated token is another forward pass that can build on the previous steps, so a <b>chain of thought</b> turns one hard step into many easy ones. Show a few worked examples (few-shot CoT), or simply add "Let's think step by step" (zero-shot CoT).</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Some answers need more than one step

"Roger has 5 tennis balls. He buys 2 more cans of 3 tennis balls each. How many tennis balls does he have now?" Asked for the number directly, large models in 2022 often got problems like this wrong.
            {: .lede}

            ::: cards grid3
### [d] Fixed compute per token
Each output token gets one forward pass through the network.

### [b] Hidden intermediate results
A direct answer must hold "2 × 3 = 6" and "5 + 6 = 11" implicitly inside one pass.

### [c] Benchmarks
GSM8K, 8.5K grade-school math word problems, was built because even the largest models then struggled with multi-step arithmetic.
:::

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Bigger models alone did not fix it

::: cards grid3
### [d] Flat scaling
The chain-of-thought paper notes scaling up model size alone had not been enough for arithmetic, commonsense and symbolic reasoning.

### [b] Finetuning is costly
Training models to produce rationales needs large labelled datasets of worked solutions.

### [c] Direct answers waste the model
The capability to do each step is there; the prompt never asks for the steps.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Why would writing steps help?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Why does generating intermediate reasoning steps improve accuracy on multi-step problems?
- [ ] The model memorised the steps
- [x] Each generated token is another forward pass, and earlier results are in the context for later steps
- [ ] It makes the prompt longer
- [ ] It changes the model weights
> **B.** The model computes a little per token; writing steps spreads the computation over many tokens and keeps intermediate results available as text.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Ask for the reasoning, then the answer

::: cards grid2
### [f] Few-shot CoT
Include a few exemplars (question, worked steps, answer) in the prompt: the model imitates the format on the new question.

### [a] Zero-shot CoT
Append "Let's think step by step": MultiArith 17.7% → 78.7% and GSM8K 10.4% → 40.7% with text-davinci-002.

### [c] Scale matters
CoT was an emergent ability around 100B parameters in 2022; smaller models produced fluent but illogical chains.

### [e] Where it helps
Multi-step tasks, large models, flat scaling curves; little gain on one- or two-step problems already above 90%.
:::

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## The GSM8K result <span class="ill">paper figure</span>

<div class="visual"><div class="bars"><div id="cBars"></div></div><p class="readout">GSM8K solve rate (Wei et al. 2022, Figure 2): eight chain-of-thought exemplars took PaLM 540B from 18% to 57%, above the previous best, a finetuned GPT-3 with a separately trained verifier.</p></div>

Chain of thought is also the starting point for everything in this topic: sampling many chains and voting (deck 02), scoring chains with verifiers (deck 03), and training models to produce long chains with reinforcement learning (deck 04).

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why it works

::: cards grid2
### [a] Serial computation
Depth per token is fixed; generating more tokens adds sequential steps of computation.

### [c] Working memory
Intermediate results become context tokens the model can attend to.

### [b] Decomposition
Exemplars show how to break a problem into steps the model already handles well.

### [e] Inspectable (with limits)
You can read the steps to debug errors, though they may not be the model's true reasons (deck 04).
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Chain of thought makes any model reason."
> In the original experiments the gains appeared only at large scale (about 100B parameters); small models wrote fluent nonsense.
:::

::: reveal myth
? "The written steps are exactly how the model got its answer."
> Not necessarily: reasoning models often fail to mention hints they used (only 25% to 39% of the time in Anthropic's study).
:::

::: reveal myth
? "Longer chains are always better."
> Extra steps on easy problems waste tokens and time (overthinking, deck 04).
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Where in the output should the final answer go for chain-of-thought prompting?
- [ ] First, then the reasoning
- [x] At the end, after the reasoning
- [ ] In a separate request
- [ ] It does not matter
> **B.** The answer must be generated after, and conditioned on, the intermediate steps.
:::

::: reveal
? Name two conditions under which chain of thought helps most.
> The task needs multiple steps, the model is large enough, and the standard-prompting scaling curve is flat (any two).
:::

::: reveal
? What is zero-shot chain of thought?
> Adding a trigger phrase such as "Let's think step by step" without any worked exemplars.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">A chain of thought buys the model more sequential computation, one token at a time, before it commits to an answer.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>A transformer does a fixed amount of computation per generated token, so a direct answer to a multi-step problem has to happen in very few steps. Chain-of-thought prompting asks the model to write intermediate steps first; each step is cheap, and its result is in the context for the next one. With eight worked exemplars, PaLM 540B went from 18% to 57% on GSM8K, beating the previous best of 55%. Zero-shot, "Let's think step by step" took text-davinci-002 from 10.4% to 40.7% on GSM8K.</p></div>
    <div class="recap"><div><span><b>Mechanism:</b> intermediate steps are extra sequential computation</span></div><div><span><b>Few-shot:</b> worked exemplars in the prompt</span></div><div><span><b>Zero-shot:</b> "Let's think step by step"</span></div><div><span><b>Fit:</b> multi-step tasks, large models</span></div></div>
    <p class="start-hint">Next: <a href="../02-sampling-and-voting/index.html">02 · Sampling, voting and coverage →</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
