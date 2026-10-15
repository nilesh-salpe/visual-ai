---
title: Verifiers and Search
body:
  data-deck: Verifiers and search
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
  - 'candidates :: sampled solutions :: f'
  - 'ORM :: score the final answer :: b'
  - 'PRM :: score each step :: a'
  - 'search :: extend the best steps :: c'
  - 'adaptive budget :: by difficulty :: e'
  caption: Verifiers turn many samples into one good answer; process supervision checks the steps too.
example:
  title: 'Worked example: best-of-N with an imperfect verifier'
  setup: A problem where each sampled solution is right with probability 0.2; N = 16 samples.
  steps:
  - 'Coverage: 1 − 0.8¹⁶ ≈ <b>97%</b> of such problems have at least one right solution.'
  - A verifier with score noise 0.5 (relative to the gap between right and wrong) picks a right one about 84% of the time (notebook simulation).
  - A noisier verifier (noise 1.5) picks right only about 43% of the time.
  - 'Majority voting with errors spread over 10 answers: about 48%.'
  result: The verifier's quality, not the number of samples, decides how much of the coverage you keep.
traps:
  tricks:
  - 'Process beats outcome supervision. :: Lightman et al.: a PRM solved 78% of a representative MATH subset.'
  - 'Match compute to difficulty. :: Compute-optimal allocation was over 4× more efficient than best-of-N.'
  - 'Small model + search can beat a big model. :: On problems with non-trivial base success, FLOPs-matched, it outperformed a 14× larger model.'
  traps:
  - 'Over-optimising the verifier. :: With many samples, best-of-N finds solutions that fool the reward model.'
  - 'Lucky answers. :: Outcome-only labels reward correct answers reached by flawed reasoning.'
  - 'Same budget for all prompts. :: Easy prompts gain nothing from extra search.'
papers:
- gsm8k_verifiers
- prm
- snell_ttc
- tot
- monkeys
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Reasoning and test-time compute · 03</div>
    <h1>Verifiers and search</h1>
    <p class="sub">Using trained models to score candidate solutions: outcome vs process reward models, best-of-N and step-level search, and allocating test-time compute by problem difficulty.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>When answers cannot be checked automatically, choosing among many sampled solutions needs a judge. Scoring only final answers rewards lucky guesses with wrong reasoning, and spending the same compute on every question wastes it on easy ones.</div>
      <div class="c"><b>Core idea</b>Train a <b>verifier</b> to score solutions. An <b>outcome reward model</b> (ORM) scores the final answer; a <b>process reward model</b> (PRM) scores <b>every step</b>, which supervises reasoning directly and lets you <b>search</b> step by step (beam search, trees). Then spend compute <b>adaptively</b>: more samples or search on hard prompts, less on easy ones.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Who picks the winner?

You sampled 16 solutions to a competition math problem; three different final answers came up. There is no answer key at inference time.
            {: .lede}

            ::: cards grid3
### [d] No automatic check
Most reasoning tasks have no unit test.

### [b] Votes are not enough
Majority voting fails when errors are correlated.

### [c] Flawed reasoning, right answer
A final-answer check can accept a solution whose steps are wrong.
:::

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Problems with judging answers only

::: cards grid3
### [d] Sparse signal
An outcome label says the solution failed, not where.

### [b] False positives
Correct answers from incorrect reasoning are rewarded and reinforced.

### [c] Uniform budgets
Easy prompts are solved on the first try; hard ones need far more compute than an even split gives them.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Outcome or process?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Which supervision gives a verifier the most direct signal about where a solution went wrong?
- [ ] Label only the final answer
- [x] Label each reasoning step as correct or incorrect
- [ ] Label the length of the solution
- [ ] No labels: use majority voting
> **B.** Process supervision labels every step, so the reward model learns to spot the first wrong step; Lightman et al. found it significantly outperformed outcome supervision on MATH.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Verifiers, step scores and adaptive compute

::: cards grid2
### [f] Outcome verifiers (ORM)
Cobbe et al.: generate many candidates, select the one ranked highest by a trained verifier; verification scaled better with data than finetuning.

### [a] Process reward models (PRM)
Score each step. PRM800K: 800,000 human step labels; the PRM solved 78% of a representative MATH subset; active learning improved label efficiency.

### [c] Search over steps
Keep the best partial solutions by PRM score and extend them: beam search, or trees of thoughts with look-ahead and backtracking.

### [e] Compute-optimal scaling
Choose the method and budget per prompt by difficulty: over 4× more efficient than best-of-N; FLOPs-matched, it beat a 14× larger model where the small model had non-trivial success.
:::

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## How good must the verifier be? <span class="ill">simulation</span>

<div class="visual"><div class="controls"><label class="ctl">p(one sample right) <input type="range" id="bP" min="5" max="90" step="5" value="20"> <output id="bPo"></output></label><label class="ctl">N samples <input type="range" id="bN" min="1" max="64" step="1" value="16"> <output id="bNo"></output></label><label class="ctl">verifier noise <input type="range" id="bS" min="0" max="3" step="0.1" value="0.5"> <output id="bSo"></output></label></div><div class="bars"><div id="bBars"></div></div><p class="readout" id="bOut"></p></div>

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why process supervision and adaptivity help

::: cards grid2
### [a] Dense credit
Step labels say exactly which step failed, a richer training signal than one bit per solution.

### [c] Prune early
Scoring partial solutions lets search drop bad branches before spending tokens on them.

### [b] Difficulty varies
Easy prompts saturate quickly; hard prompts benefit from search or revisions; very hard ones may need a bigger model.

### [e] Alignment benefit
Rewarding correct steps, not just answers, reinforces reasoning a human would endorse.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Best-of-N with a reward model scales without limit."
> Reward models are imperfect: with many samples, the top-scored candidate increasingly exploits the verifier's mistakes.
:::

::: reveal myth
? "A verifier must be as large as the generator."
> It can be useful at any size; what matters is how well it separates right from wrong solutions.
:::

::: reveal myth
? "Test-time compute replaces a bigger model."
> Only partly: Snell et al. found it beat a 14× larger model on problems the small model could sometimes solve, not on the hardest ones.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? What does a process reward model score?
- [ ] Only the final answer
- [x] Each intermediate step
- [ ] Response length
- [ ] The prompt
> **B.** It scores steps, which also enables step-level search.
:::

::: reveal
? What is compute-optimal test-time scaling?
> Allocating test-time compute per prompt (method and amount) according to estimated difficulty, rather than the same best-of-N budget everywhere.
:::

::: reveal
? Why can best-of-N get worse with a weak verifier as N grows?
> More samples give more chances for a wrong solution to receive a spuriously high score, so the selector picks verifier errors.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">A verifier converts samples into accuracy; a process verifier also tells you which step went wrong.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>Cobbe et al. introduced GSM8K and trained verifiers to rank many candidate solutions, which scaled better with data than finetuning alone. Lightman et al. compared outcome supervision with process supervision (labels for each step, 800,000 of them in PRM800K): the process-supervised reward model solved 78% of a representative MATH subset. Snell et al. showed the best use of test-time compute depends on difficulty: allocating it per prompt was over 4× more efficient than best-of-N, and could beat a 14× larger model at equal FLOPs on problems the small model could sometimes solve.</p></div>
    <div class="recap"><div><span><b>ORM:</b> scores the final answer</span></div><div><span><b>PRM:</b> scores every step; enables step search</span></div><div><span><b>Best-of-N:</b> only as good as the verifier</span></div><div><span><b>Compute-optimal:</b> spend by difficulty</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/reasoning/01_test_time_compute.ipynb" target="_blank" rel="noopener">01 · Test-time compute: majority voting, coverage and best-of-N</a> <span style="color:var(--faint)">· 35 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/reasoning/01_test_time_compute.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../04-reasoning-models/index.html">04 · Reasoning models and thinking budgets →</a> · Previous: <a href="../02-sampling-and-voting/index.html">← 02</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
