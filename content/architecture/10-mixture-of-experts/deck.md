---
title: Mixture of Experts
body:
  data-deck: Mixture of Experts
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
  - 'token :: after attention :: f'
  - 'router :: logits over N experts :: c'
  - 'top-k experts :: k of N FFNs run :: a'
  - 'weighted sum :: softmax over top-k :: e'
  caption: Parameters scale with N; compute per token scales with k.
example:
  title: 'Worked example: Mixtral and expert capacity'
  setup: 'Mixtral: 8 experts, top-2. A batch of 4,096 tokens with capacity factor 1.25.'
  steps:
  - 'Parameters: 47B in total, about 13B active per token (attention and embeddings are shared; 2 of 8 FFNs run).'
  - Expert capacity = tokens / experts × capacity factor = 4,096 / 8 × 1.25 = <b>640</b> token slots per expert (counting top-1 assignments).
  - 'If routing sends 30% of tokens to one expert, that is 1,228 tokens for 640 slots: <b>588</b> are dropped from that expert.'
  - Switch auxiliary loss α·N·Σfᵢ·Pᵢ equals α = 0.01 when perfectly balanced and α·N = 0.08 when collapsed onto one expert.
  result: MoE cuts FLOPs per token but not memory, and only works if routing stays balanced.
traps:
  tricks:
  - 'Active ≈ shared + k × expert size. :: Mixtral: ~13B of 47B per token.'
  - 'Capacity = tokens/N × capacity factor. :: Overflow tokens skip the expert via the residual.'
  - 'Aux loss minimum = α. :: At uniform routing fᵢ = Pᵢ = 1/N.'
  traps:
  - '"Runs like a 13B model." :: Memory must hold all 47B; expert parallelism adds all-to-all traffic.'
  - 'Expecting topic experts. :: Mixtral''s routing follows syntax more than domain.'
  - 'Ignoring drops. :: Imbalanced routing silently skips tokens at fixed capacity.'
papers:
- switch
- mixtral
- sparse_moe
- dsv2
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">The Modern LLM · 10</div>
    <h1>Mixture of Experts (MoE)</h1>
    <p class="sub">Replace the dense FFN (feed-forward network) with many expert FFNs and a router that sends each token to a few of them: more parameters without more compute per token, and the balancing problems that come with it.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>In a dense model every token uses every parameter, so adding parameters (more knowledge) adds FLOPs (floating-point operations) to every token in training and serving.</div>
      <div class="c"><b>Core idea</b>Swap the FFN for <b>N experts</b> plus a <b>router</b>. Each token is processed by its <b>top-k</b> experts, weighted by the router. Parameters scale with N; compute scales with k. An auxiliary loss keeps the experts evenly used.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Parameters vs compute per token

Total parameters (what must be stored) vs active parameters per token (roughly what each token computes with), from the papers. In a dense model they are equal; in an MoE (Mixture of Experts) they come apart.
{: .lede}

<div class="visual"><div id="mBars"></div></div>

<p class="caption">Mixtral 8x7B: 47B total, 13B active. DeepSeek-V2: 236B total, 21B active. Llama 3 70B: dense, so total = active.</p>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why not just make the dense model bigger?

::: cards grid3
### [d] Every FLOP is paid by every token
Doubling a dense model roughly doubles the training and inference compute per token, even for easy tokens.

### [b] Knowledge needs parameters
Many capabilities improve with parameter count, but most tokens only need a small part of the model's knowledge at a time.

### [c] Serving cost scales with active compute
Decode time per token is driven by the weights each token touches. Fewer active parameters means cheaper tokens, though the memory to hold all experts remains.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Which costs does MoE cut?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Mixtral has 47B total parameters and 13B active per token. Compared with a dense 47B model, what does it save?
- [ ] GPU memory for weights
- [x] FLOPs per token
- [ ] Both equally
- [ ] Neither
> <b>B.</b> Each token runs through only 2 of 8 experts per layer, so compute per token is like a ~13B model. But all 47B parameters must still be held in memory, and routing adds communication when experts are spread over GPUs (graphics processing units).
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Router + experts

<div class="grid3">
  <div class="card a"><h3>Experts</h3><p>N independent FFNs (SwiGLU (Swish-gated linear unit) in Mixtral) replace the single FFN in each layer. Attention stays shared and dense.</p></div>
  <div class="card b"><h3>Router</h3><p>A linear layer gives each token a logit per expert. Mixtral: G(x) = Softmax(TopK(x·W_g)), keeping the top 2 logits and softmaxing over just those. Switch Transformer routes to <b>one</b> expert (k = 1).</p></div>
  <div class="card e"><h3>Combine</h3><p>y = Σ over the top-k experts of G(x)ᵢ · Eᵢ(x). Different tokens, even in the same sequence, use different experts, and the choice can change at every layer.</p></div>
</div>

<div class="deep"><h4>DeepSeekMoE: many small experts plus shared ones</h4><p>DeepSeek-V2 splits experts more finely and isolates some as <b>shared</b> experts that every token uses: each MoE layer has <b>2 shared + 160 routed</b> experts, with <b>6</b> routed experts active per token (236B total, 21B active). Fine-grained experts give the router more combinations to choose from; shared experts hold common knowledge so routed ones don't each have to duplicate it.</p></div>

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Routing six tokens

Each token's router picks its top-k experts; the gate weights are printed on the token and drawn as line thickness. Switch between top-1 (Switch Transformer) and top-2 (Mixtral). The bars show how many tokens each expert receives: that load is what has to be balanced.
{: .lede}

<div class="visual">
  <div class="seg" id="kSeg"><button data-v="1">top-1</button><button data-v="2" class="on">top-2</button></div>
  <svg id="rSvg" viewBox="0 0 660 250" style="margin-top:10px" role="img" aria-label="Token to expert routing"></svg>
</div>

<p class="caption">Illustrative router logits (fixed random values), 8 experts.</p>

<!-- slide id="s-how2" chapter="How" tag="5 · How it works" tagclass="b5" -->
## Load balancing and capacity

4,096 tokens, 8 experts, top-1 routing. Increase the router's skew towards some experts and watch three things: each expert's share of tokens, the Switch auxiliary loss, and the tokens dropped when each expert has a fixed capacity of 1.25 × (tokens / experts).
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0"><label class="ctl">Router skew <input type="range" id="bS" min="0" max="3" step="0.1" value="1.5"> <output id="bSo"></output></label></div>
  <div id="bBars" style="margin-top:12px"></div>
  <div class="grid3" style="margin-top:12px">
    <div class="stat"><div class="num" id="bL"></div><div class="lbl">aux loss α·N·Σ fᵢPᵢ (min 0.010)</div></div>
    <div class="stat"><div class="num" id="bM"></div><div class="lbl">busiest expert's share</div></div>
    <div class="stat"><div class="num" id="bD" style="color:var(--d)"></div><div class="lbl">tokens dropped</div></div>
  </div>
</div>

<div class="deep"><h4>The Switch Transformer loss</h4><p>loss = α · N · Σᵢ fᵢ · Pᵢ, where fᵢ is the fraction of tokens whose top-1 expert is i and Pᵢ is the average router probability for expert i. Both should be 1/N, and the loss is minimized under uniform routing. The paper uses α = 10⁻²: "sufficiently large to ensure load balancing while small enough to not to overwhelm the primary cross-entropy objective". Expert capacity = (tokens per batch / number of experts) × capacity factor; overflow tokens skip the expert through the residual connection.</p></div>

<!-- slide id="s-example" from="example" chapter="How" tag="5 · How it works" tagclass="b5" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why MoE works, and what it costs

::: cards grid2
### [a] Parameters without FLOPs
Switch Transformer reports up to <b>7×</b> faster pre-training than T5-Base/Large at the same compute, and a 4× speedup over T5-XXL with its trillion-parameter model.

### [e] Experts specialize, just not by topic
Mixtral's analysis: expert choice "appears to be more aligned with the syntax rather than the domain", especially in the first and last layers. Don't expect a "math expert".

### [d] Memory and communication
All experts must be in memory. Spread across GPUs (expert parallelism), every MoE layer needs an all-to-all exchange to send tokens to their experts and back.

### [b] Balance and stability
Without a balancing loss the router collapses onto a few experts. Fixed capacity drops tokens when routing is uneven, and Switch needed extra tricks to train stably in bfloat16.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Each expert is a domain specialist: one for code, one for maths."
> Mixtral's routing analysis found no obvious topic-based assignment. Routing follows <b>syntax</b> and token-level patterns more than domains.
:::

::: reveal myth
? "A 47B MoE with 13B active parameters runs like a 13B model."
> Compute per token is close to 13B, but memory must hold <b>all 47B</b>, and expert routing adds communication. On memory-bound hardware it does not behave like a 13B model.
:::

::: reveal myth
? "MoE replaces the whole Transformer layer."
> Usually only the <b>FFN</b> becomes experts. Attention, norms and embeddings stay dense and shared.
:::

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="7 · Tricks and traps" tagclass="b7" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

<div class="quiz">
  <p class="qq">In Mixtral, how are the gate weights computed?</p>
  <div class="opts">
  <button>A. Softmax over all 8 logits</button>
  <button data-ok>B. Softmax over the top-2 logits only</button>
  <button>C. Uniform 0.5 each</button>
  <button>D. Sigmoid of each logit</button>
  </div>
  <div class="why"><b>Softmax over the top-2 logits</b>: G(x) = Softmax(TopK(x·W_g)).</div>
</div>

<div class="quiz ">
  <p class="qq">What value does the Switch auxiliary loss take under perfectly uniform routing, and under total collapse onto one expert?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Uniform: fᵢ = Pᵢ = 1/N, so the loss = α·N·N·(1/N²) = <b>α</b>. Collapse: f = P = 1 for one expert, so the loss = <b>α·N</b>.</div>
</div>

<div class="quiz ">
  <p class="qq">Why do MoE models drop tokens, and what happens to a dropped token?</p>
  <button class="reveal">Think first, then reveal</button>
  <div class="why">Each expert has a fixed buffer (capacity = tokens/experts × capacity factor) so shapes stay static. Tokens routed to a full expert are dropped from that layer's FFN and carried forward by the residual connection.</div>
</div>

<!-- slide id="s-take" chapter="Takeaway" tag="9 · Key takeaway" tagclass="b9" -->
## Key takeaway

<div class="take-line">MoE swaps the FFN for many experts and a top-k router: parameters grow with the number of experts, compute with k, and a balancing loss keeps the experts evenly used.</div>

<div class="explain"><b>Say it in 30 seconds</b><p>In a dense model every token uses every parameter. A Mixture-of-Experts layer replaces the FFN with N expert FFNs and a router that sends each token to its top k, weighting their outputs by a softmax over the selected logits. Mixtral has 8 experts with top-2 routing, 47 billion parameters in total but about 13 billion active per token; DeepSeek-V2 uses 160 fine-grained routed experts plus 2 shared ones. Compute per token drops, but all experts must sit in memory and tokens are exchanged between GPUs. Routers tend to collapse, so Switch Transformer adds an auxiliary loss, alpha times N times the sum of f-i times P-i, that is minimized by uniform routing. Fixed expert capacity drops overflow tokens.</p></div>

<div class="recap"><div><span><b>Problem:</b> dense models pay for every parameter on every token.</span></div><div><span><b>Core idea:</b> router + N experts, top-k per token; params ∝ N, FLOPs ∝ k.</span></div><div><span><b>Costs:</b> all experts in memory, all-to-all communication, balancing loss and capacity.</span></div></div>

<div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/architecture/09_moe_router.ipynb" target="_blank" rel="noopener">09 · Mixture-of-Experts: router, dispatch and load balancing</a> <span style="color:var(--faint)">· 45 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/architecture/09_moe_router.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>

<p class="start-hint">Next: <a href="../11-putting-it-together/index.html">11 · Putting it together →</a> · Previous: <a href="../09-flash-attention/index.html">← 09</a> · <a href="../index.html">All decks</a></p>

<p class="cite">Sources: Fedus et al. 2022, "Switch Transformers" (eq. 3–6, α = 10⁻²); Jiang et al. 2024, "Mixtral of Experts" (§2.1, Fig. 8); DeepSeek-AI 2024, DeepSeek-V2 (§2.2, DeepSeekMoE); Shazeer et al. 2017 (sparsely-gated MoE).</p>

<!-- slide id="s-papers" from="papers" -->
