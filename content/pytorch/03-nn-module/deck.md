---
title: nn.Module and a Transformer Block
body:
  data-deck: nn.Module and a transformer block
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
  - 'x :: (B, T, C) :: f'
  - 'RMSNorm → attention :: SDPA, causal :: a'
  - '+ residual :: x + attn(norm(x)) :: e'
  - 'RMSNorm → MLP :: C → 4C → C :: c'
  - '+ residual :: x + mlp(norm(x)) :: e'
  caption: ≈ 12C² weights per block (+ 2C norm gains).
example:
  title: 'Worked example: counting GPT-2 small''s parameters'
  setup: 'GPT-2 small (as in nanoGPT): C = 768, 12 layers, vocabulary 50,257, context 1,024, tied embeddings. Each block ≈ 12C² weights.'
  steps:
  - 'Per block: 12 × 768² = <b>7.08M</b>; × 12 blocks = <b>84.9M</b>.'
  - 'Token embedding: 50,257 × 768 = <b>38.6M</b> (reused as the output head); positions 1,024 × 768 = 0.79M.'
  - 'Total ≈ 124M, plus biases and LayerNorm parameters: nanoGPT reports <b>124M</b>.'
  - 'Notebook 03 checks the formula exactly for its RMSNorm block without biases: 12 × 64² + 2 × 64 = 49,280.'
  result: Shapes give parameter counts directly; tying the head to the embedding saves a whole V × C matrix.
traps:
  tricks:
  - 'sum(p.numel() for p in m.parameters()). :: The parameter count.'
  - 'register_buffer(…, persistent=False). :: For caches that should not be saved (e.g. RoPE tables you can recompute).'
  - 'is_causal=True. :: Instead of building a T×T mask.'
  traps:
  - 'Plain Python lists of layers. :: Use nn.ModuleList, or parameters are not registered.'
  - 'Building a mask and passing is_causal too. :: Use one or the other.'
  - 'Forgetting model.eval(). :: Dropout stays active during evaluation.'
papers:
- pytorch
- pt_sdpa
- nanogpt
- fa2
status: {label: current, reviewed: 2026-10-15, note: "PyTorch 2.14.1 is still the latest release"}
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">PyTorch for LLMs · 03</div>
    <h1>nn.Module and a transformer block</h1>
    <p class="sub">How PyTorch models are built: nn.Module, parameters and buffers, state_dict, and a complete pre-norm transformer block with fused attention (scaled_dot_product_attention).</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>An LLM has dozens of blocks with hundreds of tensors. Code must organise them, count them, move them between devices, save and load them, and run attention efficiently.</div>
      <div class="c"><b>Core idea</b>Subclass <b>nn.Module</b>: assign layers in <code>__init__</code>, compute in <code>forward</code>. Assigned <b>parameters</b> and sub-modules are tracked automatically; <b>buffers</b> (<code>register_buffer</code>) hold non-trainable state. Attention is one call: <code>F.scaled_dot_product_attention(q, k, v, is_causal=True)</code>, which picks a fused kernel when available.</div>
    </div>
    <div class="toc" data-auto></div>
  </div>
</section>

<!-- slide id="s-p1" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Count a model's parameters

A decoder-only model built from the block on this page. Move width, depth and vocabulary; compare with GPT-2 small. Toggle weight tying.
{: .lede}

<div class="visual">
  <div class="controls" style="margin-top:0">
    <label class="ctl">width C <input type="range" id="pC" min="64" max="8192" step="64" value="768"> <output id="pCo"></output></label>
    <label class="ctl">layers L <input type="range" id="pL" min="1" max="96" step="1" value="12"> <output id="pLo"></output></label>
    <label class="ctl">vocabulary V <input type="range" id="pV" min="1000" max="256000" step="1000" value="50000"> <output id="pVo"></output></label>
    <label class="ctl"><input type="checkbox" id="pT" checked> tie head to embedding</label>
  </div>
  <div id="pBars" style="margin-top:12px"></div>
  <p class="readout" id="pOut"></p>
</div>

<!-- slide id="s-lim" chapter="Limitation" tag="2 · Limitation" tagclass="b2" -->
## Why not just write functions?

::: cards grid3
### [d] Bookkeeping
Hundreds of weight tensors must be found for the optimizer, moved to GPUs, saved and loaded.

### [b] Modes
Dropout and normalisation behave differently in training and evaluation.

### [c] Attention speed
A hand-written masked softmax materialises the T × T matrix; fused kernels do not.
:::

<!-- slide id="s-turn" chapter="Your turn" tag="3 · Your turn" tagclass="b3" -->
## Which is registered?

Pick an answer before moving on. Committing to a guess, even a wrong one, makes the real answer stick.
{: .lede}

::: quiz
? Inside __init__ you write self.layers = [nn.Linear(8, 8) for _ in range(4)]. What does model.parameters() contain?
- [ ] All four layers' weights
- [x] None of them
- [ ] Only the first layer
- [ ] An error is raised
> <b>B.</b> A plain Python list is not a Module, so its layers are invisible to parameters(), .to(device) and state_dict(). Use nn.ModuleList.
:::

<!-- slide id="s-core" chapter="Core idea" tag="4 · Core idea" tagclass="b4" -->
## Modules, parameters, buffers

::: cards grid2
### [a] nn.Module
__init__ assigns sub-modules and nn.Parameters; forward computes. Calling the module runs forward plus hooks.

### [c] Containers
nn.Sequential, nn.ModuleList, nn.ModuleDict register children so they are tracked.

### [b] Buffers
register_buffer for non-trainable tensors (masks, RoPE frequencies); persistent=False keeps them out of state_dict.

### [e] state_dict
Name → tensor mapping of parameters and persistent buffers; what checkpoints store.
:::

{{glance}}

<!-- slide id="s-how" chapter="How" tag="5 · How it works" tagclass="b5" -->
## The block in code

<div class="visual"><pre style="margin:0;font:13px/1.55 'JetBrains Mono',monospace;white-space:pre-wrap">class Block(nn.Module):&#10;    def __init__(self, C, H):&#10;        super().__init__()&#10;        self.n1, self.attn = nn.RMSNorm(C), CausalSelfAttention(C, H)&#10;        self.n2 = nn.RMSNorm(C)&#10;        self.mlp = nn.Sequential(nn.Linear(C, 4*C, bias=False), nn.GELU(),&#10;                                 nn.Linear(4*C, C, bias=False))&#10;    def forward(self, x):&#10;        x = x + self.attn(self.n1(x))&#10;        return x + self.mlp(self.n2(x))&#10;&#10;# inside CausalSelfAttention.forward:&#10;y = F.scaled_dot_product_attention(q, k, v, is_causal=True)   # (B, H, T, D)</pre></div>

::: deep SDPA backends
scaled_dot_product_attention dispatches to one of FLASH_ATTENTION, EFFICIENT_ATTENTION, CUDNN_ATTENTION or MATH (the SDPBackend enum), depending on hardware, dtype and inputs. torch.nn.attention.sdpa_kernel restricts the choice. It also accepts enable_gqa=True for grouped-query attention.
:::

<!-- slide id="s-example" from="example" -->

<!-- slide id="s-why" chapter="Why" tag="6 · Why it works" tagclass="b6" -->
## Why this structure works

::: cards grid2
### [a] Automatic tracking
Assigning attributes registers parameters, so optimizers, .to(), FSDP and checkpoints find them.

### [e] Composable
A model is a tree of modules; blocks are reused, replaced (LoRA) or wrapped (FSDP) per sub-module.

### [b] Fused attention for free
One SDPA call gets FlashAttention-class kernels on supported GPUs.

### [c] Testable
Each module can be checked alone against a reference, as notebook 03 does.
:::

<!-- slide id="s-myth" chapter="Myths" tag="7 · Misconceptions" tagclass="b7" -->
## Common misconceptions

Each statement below is a mental model people often get wrong. Decide why it is wrong, then reveal.
{: .lede}

::: reveal myth
? "Buffers are trained like parameters."
> Buffers are never returned by parameters(), so optimizers never update them.
:::

::: reveal myth
? "SDPA is an approximation."
> It computes exact attention; fused backends just avoid storing the score matrix.
:::

::: reveal myth
? "state_dict contains the optimizer state."
> Only the model's parameters and persistent buffers; the optimizer has its own state_dict.
:::

<!-- slide id="s-traps" from="traps" -->

<!-- slide id="s-check" chapter="Check" tag="8 · Check yourself" tagclass="b8" -->
## Check yourself

Answer from memory. If you can't, revisit the slide named in the answer.
{: .lede}

::: quiz
? Parameters in one block with C = 1,024 (12C² + 2C)?
- [ ] ≈ 1.2M
- [x] ≈ 12.6M
- [ ] ≈ 126M
- [ ] ≈ 4M
> 12 × 1,024² + 2,048 ≈ <b>12.6M</b>.
:::

::: reveal
? When would you use register_buffer(…, persistent=False)?
> For derived, non-trainable state you can recompute (causal masks, RoPE caches) that should not be saved in checkpoints.
:::

::: reveal
? What does is_causal=True do in SDPA?
> Applies a lower-triangular causal mask so each position attends only to itself and earlier positions, without building the mask tensor.
:::

<!-- slide raw -->
<section class="slide" id="s-take" data-chapter="Takeaway">
  <div class="inner">
    <span class="qtag b9">9 · Key takeaway</span>
    <h2>Key takeaway</h2>
    <hr>
    <div class="take-line">Models are trees of nn.Modules whose parameters and buffers are tracked automatically; a pre-norm block is two residual branches around SDPA attention and an MLP, ≈ 12C² weights.</div>
    <div class="explain"><b>Say it in 30 seconds</b><p>In PyTorch a model is an nn.Module: you assign layers in init and compute in forward, and every parameter you assign is tracked, so optimizers, device moves, sharding and checkpoints find it. Containers like ModuleList register children; buffers hold non-trainable state such as masks or rotary tables. A pre-norm transformer block is x plus attention of the normalised x, then x plus an MLP of the normalised x. Attention is one call to scaled dot product attention with is_causal set, which uses fused kernels such as FlashAttention when the hardware allows.</p></div>
    <div class="recap"><div><span><b>Problem:</b> organise, count, move and save many tensors.</span></div><div><span><b>Core idea:</b> nn.Module tree; parameters vs buffers; state_dict.</span></div><div><span><b>Block:</b> x + attn(norm x); x + mlp(norm x); SDPA.</span></div></div>
    <div class="paper" style="border-left-color:var(--e);background:var(--e-soft)"><b style="color:var(--e)">🛠 Build it (Colab notebook)</b><ul style="margin:6px 0 0;padding-left:20px"><li><a href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/03_transformer_block.ipynb" target="_blank" rel="noopener">03 · nn.Module: a pre-norm transformer block</a> <span style="color:var(--faint)">· 40 min · <a href="https://github.com/nilesh-salpe/visual-ai/blob/main/build-it/pytorch/03_transformer_block.ipynb" target="_blank" rel="noopener">view on GitHub</a></span></li></ul></div>
    <p class="start-hint">Next: <a href="../04-training-loop/index.html">04 · The training loop →</a> · Previous: <a href="../02-autograd/index.html">← 02</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
