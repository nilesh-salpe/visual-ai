---
title: Sequential Processing Bottleneck
body:
  data-deck: Sequential bottleneck
  data-home: ../index.html
  data-home-label: Transformer
styles:
- ../../shared/deck.css
- ../../shared/learn.css
- ../tx.css
scripts:
- ../../shared/deck.js
- ../tx.js
glance:
  steps:
  - 'RNN :: h_t needs h_{t−1}: n sequential steps :: d'
  - 'distant words :: O(n) steps apart :: b'
  - 'self-attention :: every pair in one step :: a'
  - 'cost :: n² · d comparisons :: c'
  caption: Trade sequential steps for pairwise comparisons that run in parallel.
example:
  title: 'Worked example: recurrent vs self-attention cost for one layer'
  setup: A sentence of n = 50 tokens, model width d = 512 (the base Transformer).
  steps:
  - 'Self-attention: n² · d = 50² × 512 = <b>1.28M</b> operations, with O(1) sequential steps.'
  - 'Recurrent layer: n · d² = 50 × 512² = <b>13.1M</b> operations, with 50 sequential steps.'
  - 'Maximum path length between two words: self-attention 1; RNN up to 49.'
  - 'Break-even: self-attention is cheaper whenever n < d, i.e. sentences shorter than 512 tokens (the paper''s Table 1 argument).'
  result: For typical sentence lengths, self-attention is both cheaper per layer and fully parallel.
traps:
  tricks:
  - 'Table 1 in one line. :: Self-attention O(n²·d), O(1) sequential, path 1; recurrent O(n·d²), O(n) sequential, path n.'
  - 'Self-attention wins when n < d. :: Typical in translation sentences.'
  - 'Parallel over positions in training. :: All n outputs computed in one pass.'
  traps:
  - '"Attention is always cheaper." :: For very long n, n² dominates; that is why long-context methods exist.'
  - 'Confusing training and generation. :: Generation is still sequential, one token per step.'
  - 'Forgetting path length. :: Short paths are the long-range-dependency argument, not just speed.'
papers:
- vaswani
- seq2seq
- bahdanau
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Attention Is All You Need · 01</div>
    <h1>The sequential processing bottleneck</h1>
    <p class="sub">Why recurrent networks read one token at a time, why that limits parallel computation and makes long-range dependencies hard to learn, and how self-attention removes both limits.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>An RNN (recurrent neural network) computes h<sub>t</sub> from h<sub>t−1</sub>, so a sentence of n tokens takes n sequential steps, and signals between distant words must pass through many steps.</div>
      <div class="c"><b>Core idea</b>Self-attention connects every pair of positions directly: O(1) sequential operations and O(1) path length per layer.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## A sequence model must connect distant words and train fast on a lot of data

Translation is the paper's test bed. A good model has to do three things at once.
{: .lede}

::: cards grid3
### [a] Relate distant words
In "The animal didn't cross the street because it was tired", resolving "it" needs a link across 6 words. Long-range dependencies are "a key challenge in many sequence transduction tasks" (§4).

### [b] Learn from a lot of data
WMT (Workshop on Machine Translation) 2014 English-German has about 4.5 million sentence pairs; English-French has 36 million sentences (§5.1). Training speed decides what you can afford to try.

### [c] Use parallel hardware
GPUs (graphics processing units) run thousands of operations at the same time. Training is only fast if the work can be split across positions.
:::

<div class="takeaway">The architecture should make any two positions easy to connect, and let all positions be computed at the same time.</div>

<!-- slide id="s-rnn" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## An RNN must wait for step t−1 before it can compute step t

A recurrent layer computes the hidden state h<sub>t</sub> = f(h<sub>t−1</sub>, x<sub>t</sub>). Each step needs the result of the previous one, so the steps run <b>one after another</b>, even on hardware that could run thousands of operations at the same time.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><button class="btn primary" id="rPlay">Play</button><button class="btn" id="rReset">Reset</button><span class="readout" id="rOut"></span></div>
  <svg id="rSvg" viewBox="0 0 660 250" style="margin-top:8px" role="img" aria-label="RNN unrolled over time"></svg>
  <div class="key"><span><i style="background:var(--a)"></i>hidden state computed</span><span><i style="background:var(--panel-2);border:1px solid var(--line)"></i>waiting on the previous step</span><span><i style="background:var(--b)"></i>parallel hardware lane busy</span></div>
</div>

<div class="takeaway">Training on long sequences is slow because time steps can't run in parallel. Batching across sentences helps, but memory limits how far that goes for long sequences (§1 of the paper).</div>

<div class="cite">Paper §1: "This inherently sequential nature precludes parallelization within training examples, which becomes critical at longer sequence lengths."</div>

<!-- slide id="s-path" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Distant words are many steps apart

To link "<b>it</b>" to "<b>animal</b>", information has to travel through every hidden state in between. A longer path makes the dependency harder to learn: the forward signal and the backward gradient both pass through many transformations. Click two tokens.
{: .lede}

<div class="visual">
  <label class="ctl">Signal kept per step <span class="ill">illustrative</span> <input type="range" id="pK" min="0.5" max="0.98" step="0.01" value="0.8"> <output id="pKo"></output></label>
  <svg id="pSvg" viewBox="0 0 660 190" style="margin-top:10px" role="img" aria-label="Path between two tokens in an RNN"></svg>
  <div class="grid3">
    <div class="stat"><div class="num" id="pHops"></div><div class="lbl">sequential hops between the two tokens</div></div>
    <div class="stat"><div class="num" id="pSig" style="color:var(--d)"></div><div class="lbl">signal remaining (toy model)</div></div>
    <div class="stat"><div class="num">O(n)</div><div class="lbl">maximum path length, recurrent layer (Table 1)</div></div>
  </div>
</div>

<div class="takeaway">The paper's third criterion is the <b>path length</b> between long-range dependencies: "The shorter these paths … the easier it is to learn long-range dependencies" (§4).</div>

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## How would you fix both problems?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? How would you let "it" use "animal" directly, while computing all 10 positions at the same time?
- [ ] Give the RNN a bigger hidden state
- [ ] Run the RNN in both directions (bidirectional)
- [x] Let every position read every other position directly, weighted by relevance
- [ ] Stack more RNN layers
> <b>C is the paper's move.</b> A bigger state (A) or more layers (D) keeps the n-step chain. A bidirectional RNN (B) still needs n sequential steps and long paths in each direction. Only direct position-to-position connections give O(1) sequential operations and O(1) path length (Table 1).
:::

<!-- slide id="s-sa" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Self-attention connects every position to every other in one step

In a self-attention layer, every token reads from every other token <b>directly</b>, and all positions are computed <b>at the same time</b>. Switch between the two layer types.
{: .lede}

<div class="visual">
  <div class="seg" id="saSeg"><button data-v="rnn">Recurrent layer</button><button data-v="sa" class="on">Self-attention layer</button></div>
  <svg id="saSvg" viewBox="0 0 660 240" style="margin-top:10px" role="img" aria-label="Connections in each layer type"></svg>
  <div class="grid3">
    <div class="stat"><div class="num" id="saSeq"></div><div class="lbl">sequential operations</div></div>
    <div class="stat"><div class="num" id="saPath"></div><div class="lbl">max path length</div></div>
    <div class="stat"><div class="num" id="saLanes"></div><div class="lbl">positions computed in parallel</div></div>
  </div>
</div>

<div class="takeaway">Both problems from the previous slides go away: the whole layer is computed in parallel, and any two tokens are one hop apart.</div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## A loop of n dependent steps vs a few matrix products

The difference shows up directly in code. A recurrent layer is a loop where each step needs the previous one. A self-attention layer is a handful of matrix products over all positions at once.
{: .lede}

<div class="vs">
  <div class="visual" style="margin-top:0"><h3>Recurrent layer</h3><pre class="code">h = h0
for t in range(n):        # n dependent steps
h = f(h, x[t])        # needs h from step t-1
out[t] = h</pre></div>
  <div class="visual" style="margin-top:0"><h3>Self-attention layer</h3><pre class="code">Q, K, V = X@Wq, X@Wk, X@Wv  # all n positions
S = Q @ K.T / sqrt(d_k)     # n×n scores: 1 matmul
A = softmax(S, axis=-1)     # each row sums to 1
out = A @ V                 # all n outputs at once</pre></div>
</div>

<div class="paper">Every output row depends on <b>all</b> inputs, but no output depends on another output, so the whole layer runs in parallel. Decks 03–05 explain each line.</div>

<!-- slide id="s-cost" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## The cost: self-attention compares every pair, n² · d

Connecting every pair costs O(n²·d) per layer, versus O(n·d²) for recurrence. The paper points out that self-attention is <b>cheaper when n &lt; d</b>, which was typical for sentence-level translation with word-piece or BPE (byte-pair encoding) tokens.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">Sequence length n <input type="range" id="cN" min="1" max="3.6" step="0.01" value="1.5"> <output id="cNo"></output></label>
    <label class="ctl">Model dim d <input type="range" id="cD" min="6" max="11" step="1" value="9"> <output id="cDo"></output></label>
    <label class="ctl">Kernel k <input type="range" id="cK" min="2" max="9" step="1" value="3"> <output id="cKo"></output></label>
  </div>
  <div id="cBars" style="margin-top:14px"></div>
  <p class="readout" id="cOut" style="margin-top:8px"></p>
</div>

<p class="caption">Operation counts per layer from Table 1's complexity terms, without constants: self-attention n²·d, recurrent n·d², convolutional k·n·d². The paper's base model uses d = 512.</p>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide raw -->
<section class="slide" id="s-paper" data-chapter="Why">
  <div class="inner">
    <span class="qtag b6">6 · Why it works</span> <span class="ill" style="color:var(--c);border-color:var(--c)">from the paper · §4, Table 1</span>
    <h2>Why self-attention: three criteria</h2>
    <hr>
    <div class="visual scroll-x">
      <table class="tbl">
        <tr><th>Layer type</th><th>Complexity per layer</th><th>Sequential operations</th><th>Maximum path length</th></tr>
        <tr><td><b>Self-attention</b></td><td>O(n²·d)</td><td class="em-e">O(1)</td><td class="em-e">O(1)</td></tr>
        <tr><td>Recurrent</td><td>O(n·d²)</td><td class="em-d">O(n)</td><td class="em-d">O(n)</td></tr>
        <tr><td>Convolutional</td><td>O(k·n·d²)</td><td>O(1)</td><td>O(log<sub>k</sub>(n))</td></tr>
        <tr><td>Self-attention (restricted)</td><td>O(r·n·d)</td><td>O(1)</td><td>O(n/r)</td></tr>
      </table>
    </div>
    <div class="paper"><b>The three criteria (§4):</b> (1) total computational complexity per layer; (2) how much computation can be parallelized, measured by the minimum number of sequential operations; (3) the path length between long-range dependencies. n = sequence length, d = representation dimension, k = kernel size, r = neighbourhood size.</div>
    <div class="cite">Vaswani et al., "Attention Is All You Need", arXiv:1706.03762v7, Table 1 and §4.</div>
  </div>
</section>

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Self-attention is always cheaper than a recurrent layer."
> Per layer, self-attention costs O(n²·d) and recurrence O(n·d²). Self-attention is cheaper only when <b>n &lt; d</b>, which the paper notes is usually true for sentence-level translation. For very long sequences it suggests restricting attention to a neighbourhood of size r (§4).
:::

::: reveal myth
? "The Transformer has no sequential computation at all."
> Within a layer, all positions run in parallel. But the 6 layers still run one after another, and <b>generation</b> is still one token at a time (deck 12).
:::

::: reveal myth
? "RNNs can't learn long-range dependencies."
> They can (LSTMs (long short-term memory networks) were the state of the art). The paper's argument is that <b>longer paths make it harder</b>: shorter paths between positions make long-range dependencies easier to learn (§4).
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? What is the maximum path length between two positions in a recurrent layer (Table 1)?
- [ ] O(1)
- [ ] O(log n)
- [x] O(n)
- [ ] O(n²)
> <b>O(n).</b> Information must pass through every hidden state in between. Self-attention: O(1). See "Distant words are many steps apart".
:::

<div class="quiz ">
  <p class="qq">For n = 50 tokens and d = 512, which layer is cheaper per layer, self-attention or recurrent, and by roughly how much?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Self-attention: n²·d = 50² × 512 ≈ 1.3M. Recurrent: n·d² = 50 × 512² ≈ 13.1M. Self-attention is about <b>10× cheaper</b>, because n &lt; d.</div>
</div>

<div class="quiz ">
  <p class="qq">Why doesn't batching many sentences together fix the RNN bottleneck?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Batching parallelizes <em>across</em> sentences, but within each sentence the steps stay sequential, and memory limits how large batches can get for long sequences (§1).</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">Recurrence pushes computation and information through n sequential steps. Self-attention puts every pair of positions one hop apart and computes them all at once.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>RNNs compute h<sub>t</sub> from h<sub>t−1</sub>, so a layer needs O(n) sequential steps and distant tokens are O(n) hops apart. That makes training slow and long-range dependencies hard to learn. Self-attention connects all positions directly: O(1) sequential operations and O(1) path length per layer, at O(n²·d) cost, which is cheaper than recurrence's O(n·d²) when n &lt; d, as in sentence-level translation.</p></div>

<div class="recap">
  <div><span><b>Problem:</b> recurrence forces n sequential steps per layer, and puts O(n) hops between distant tokens.</span></div>
  <div><span><b>Core idea:</b> self-attention computes all positions at once with O(1) path length, at O(n²·d) cost, which is cheaper than recurrence when n &lt; d.</span></div>
</div>

<p class="start-hint">Next: <a href="../02-transformer-architecture/index.html">02 · The Transformer architecture →</a> · <a href="../index.html">All concepts</a></p>

<!-- slide id="s-papers" from="papers" -->
