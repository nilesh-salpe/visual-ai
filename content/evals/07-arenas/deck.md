---
title: Arenas and Ratings
body:
  data-deck: Arenas and ratings
  data-home: ../index.html
  data-home-label: Evals
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
glance:
  steps:
  - 'user prompt :: real, fresh :: f'
  - 'two anonymous models :: answer side by side :: c'
  - 'vote :: A, B or tie :: b'
  - 'Bradley-Terry MLE :: over all votes :: a'
  - 'rating ± CI :: Elo-like scale :: e'
  caption: Order-independent ratings with honest uncertainty.
example:
  title: 'Worked example: what rating gaps mean'
  setup: 'Ratings on the Elo-like scale: R = 400 × ξ / ln 10, where ξ is the Bradley-Terry strength.'
  steps:
  - '100-point gap: P(win) = 1/(1 + 10<sup>−100/400</sup>) = <b>64%</b>.'
  - '400-point gap: <b>91%</b> (10:1 odds).'
  - Strength gap of 1.0 log-odds = 400/ln 10 = <b>174 points</b> = 73% win rate.
  - Two models 15 points apart with ±20-point intervals are statistically tied.
  result: Read ratings as win probabilities and intervals, not as strict ranks.
traps:
  tricks:
  - 'P(win) = 1 / (1 + 10^(−Δ/400)). :: 100 points ≈ 64%.'
  - 'BT = logistic regression on votes. :: Order-independent; intervals by sandwich estimator or bootstrap.'
  - 'Combine with benchmarks. :: Arenas measure preference; benchmarks measure specific skills.'
  traps:
  - 'Online Elo. :: Depends on vote order and K.'
  - 'Strict ranks. :: Neighbours often overlap.'
  - 'Preference = correctness. :: Votes include style and length.'
papers:
- arena
- mtbench
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Evaluating LLMs · 07</div>
    <h1>Arenas and ratings</h1>
    <p class="sub">Ranking models from crowdsourced head-to-head votes: the Bradley-Terry model behind Chatbot Arena, how it compares with online Elo, and why leaderboards need confidence intervals.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Static benchmarks miss what real users ask and value. Pairwise human votes on live prompts capture it, but they are noisy, unevenly distributed across models, and need a principled way to become a ranking.</div>
      <div class="c"><b>Core idea</b>Collect anonymous <b>pairwise votes</b> on user prompts, fit <b>Bradley-Terry</b> strengths by maximum likelihood (P(i beats j) = σ(ξᵢ − ξⱼ)), and publish ratings <b>with confidence intervals</b>.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## How an arena works

::: cards grid3
### [a] Real prompts
Users bring their own questions, so the distribution reflects actual use, and new prompts keep arriving, so there's no fixed test set to overfit.

### [b] Anonymous pairs
Two models answer the same prompt; the user votes for the better one (or a tie) before model names are revealed.

### [e] Ratings from votes
Chatbot Arena collected "over 240K votes" in the period covered by its paper and turns them into ratings with a statistical model.
:::

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Turning votes into a ranking is not trivial

::: cards grid3
### [d] Not everyone plays everyone
Some pairs get thousands of votes, others few. Win rates against different opponents aren't directly comparable.

### [b] Votes are noisy
Users disagree and prompts vary in difficulty, so any rating has uncertainty that must be reported.

### [c] Online Elo depends on order
Chess-style Elo updates after each game, so the same votes processed in a different order give different ratings, and K controls how much recent votes dominate.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Read a Bradley-Terry rating

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? On the Elo-style scale (400/ln 10 ≈ 174 points per log-odds unit), model A is rated 100 points above model B. Roughly how often should A win a head-to-head vote?
- [ ] 50%
- [x] about 64%
- [ ] about 90%
- [ ] 100%
> <b>B.</b> P(A wins) = 1/(1 + 10^(−100/400)) ≈ 0.64. On this scale, 100 points is a modest edge, and 400 points means about 10:1 odds.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Bradley-Terry vs online Elo

::: cards grid2
### [a] Bradley-Terry (maximum likelihood)
Fit all strengths ξ jointly to all votes: maximize Σ log σ(ξ<sub>winner</sub> − ξ<sub>loser</sub>). The result doesn't depend on vote order, uses every comparison, and comes with standard errors. Chatbot Arena estimates BT (Bradley-Terry) coefficients and reports intervals via a sandwich estimator and bootstrap.

### [b] Online Elo
After each vote, move the winner up and the loser down by K·(1 − expected score). Cheap and incremental, but sensitive to K and to the order of votes, and with no built-in uncertainty.
:::

<div class="eq">P(i beats j) = σ(ξᵢ − ξⱼ) = 1 / (1 + 10<sup>−(Rᵢ − Rⱼ)/400</sup>)  with  R = 400·ξ / ln 10</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Same votes, different Elo <span class="ill">simulation</span>

6 models with known true strengths and 3,000 simulated votes. Shuffle the order of the same votes and re-run online Elo; Bradley-Terry (fitted in your browser) doesn't move.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><button class="btn primary" id="aShuf">shuffle vote order</button><label class="ctl">Elo K <input type="range" id="aK" min="4" max="64" step="4" value="16"> <output id="aKo"></output></label></div>
  <svg id="aSvg" viewBox="0 0 660 250" style="margin-top:10px" role="img" aria-label="Elo vs Bradley-Terry"></svg>
  <div class="legend"><span><i style="background:var(--faint)"></i>true</span><span><i style="background:var(--a)"></i>Bradley-Terry</span><span><i style="background:var(--d)"></i>online Elo (this order)</span></div>
</div>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Read the intervals, not just the ranks

::: cards grid2
### [a] Overlap means "statistically tied"
If two models' intervals overlap heavily, their order may flip with more votes. Rank bands are more honest than strict ranks.

### [e] Intervals shrink with votes
Popular models get many votes and tight intervals; new models start uncertain. Arena's paper also studies sampling pairs to converge faster.

### [b] Style and length matter
Human voters, like LLM (large language model) judges, may prefer longer or better-formatted answers, so arenas measure user preference, not correctness alone.

### [c] Combine with benchmarks
Arenas capture preference on real prompts; benchmarks test specific skills with known answers. Use both.
:::

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why arenas became a standard reference

::: cards grid2
### [a] Hard to overfit
Prompts are fresh and diverse; there's no published test set to train on.

### [e] Matches what users feel
Ratings reflect preferences on real tasks, and the Arena paper reports crowdsourced votes agree well with expert raters.

### [b] Principled statistics
Bradley-Terry plus confidence intervals turns noisy, unbalanced votes into a ranking with honest uncertainty.

### [d] Limits
The user population and its prompts shape the result, preferences include style, and ratings can be gamed by optimizing for what voters like.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "An arena rating is a chess Elo computed game by game."
> Chatbot Arena fits Bradley-Terry coefficients by maximum likelihood over all votes, which is order-independent, and reports intervals. It is displayed on an Elo-like scale.
:::

::: reveal myth
? "A higher rank always means a better model."
> Neighbouring models often have overlapping intervals. Read rank bands, not strict positions.
:::

::: reveal myth
? "Arena ratings measure correctness."
> They measure which answer users prefer, which mixes correctness, helpfulness, style and length.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Which property does Bradley-Terry maximum likelihood have that online Elo lacks?
- [ ] It is faster to update
- [x] Its result does not depend on the order of votes
- [ ] It needs no data
- [ ] It ignores ties
> <b>Order independence</b>: it fits all votes jointly.
:::

<div class="quiz ">
  <p class="qq">Convert a Bradley-Terry strength difference of 1.0 (log-odds) to the Elo scale and a win probability.</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">400/ln 10 ≈ 174 points; P(win) = σ(1.0) ≈ 0.73.</div>
</div>

<div class="quiz ">
  <p class="qq">Why must arena leaderboards publish confidence intervals?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Votes are noisy and unevenly distributed across models, so ratings have uncertainty; close models may be statistically indistinguishable.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Arenas turn anonymous head-to-head votes on real prompts into ratings with Bradley-Terry maximum likelihood, which is order-independent, and should always be read with their confidence intervals.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>Chatbot Arena shows users two anonymous models answering their own prompt and asks which is better, collecting hundreds of thousands of votes on real, ever-changing prompts that can't be overfit. To rank models from unbalanced, noisy votes it fits the Bradley-Terry model, where the probability that one model beats another is the sigmoid of their strength difference, by maximum likelihood over all votes, and reports confidence intervals. Online Elo, which updates after each vote, depends on vote order and the step size. The ratings are shown on an Elo-like scale where 100 points is about a 64 percent win rate. Arenas measure user preference, including style, so read rank bands and use them alongside benchmarks.</p></div>

<div class="recap"><div><span><b>Problem:</b> benchmarks miss real use; votes are noisy and unbalanced.</span></div><div><span><b>Core idea:</b> Bradley-Terry MLE (maximum likelihood estimation) over all votes, with confidence intervals.</span></div><div><span><b>Watch:</b> Elo order dependence; overlapping intervals; preference ≠ correctness.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/evals/04_judges_and_arenas.ipynb" target="_blank" rel="noopener">04 · LLM judges and arena ratings</a> <span style="color:var(--faint)">· 45 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/evals/04_judges_and_arenas.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">You've finished the series. <a href="../../build-it/index.html">See all Build-it notebooks →</a> · Previous: <a href="../06-llm-as-judge/index.html">← 06</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Chiang et al. 2024, "Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference" (240K+ votes; Bradley-Terry maximum likelihood with sandwich and bootstrap intervals); Zheng et al. 2023 (MT-Bench and Arena agreement); Elo 1978.</p>

<!-- slide id="s-papers" from="papers" -->
