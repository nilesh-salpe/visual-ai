from tool import section, your_turn, myths, check

DECKS = {}


def deep(title, html):
    return f'    <div class="deep"><h4>{title}</h4>{html}</div>'


# =============================================================== 01
DECKS['01-what-changed'] = dict(
    title='What Changed Since 2017', h1='What changed since 2017',
    sub='The 2017 Transformer and a 2024 Llama block side by side: seven changes, what problem each one solved, and where each is explained in this guide.',
    prob='The 2017 Transformer was built for translation on 8 GPUs. Scaling it to hundreds of billions of parameters, long contexts and millions of users exposed problems in training stability, position handling, FFN quality, inference memory and attention speed.',
    core='Modern LLMs keep the 2017 skeleton (attention + FFN + residuals) and swap specific parts: <b>pre-norm RMSNorm</b>, <b>RoPE</b>, <b>SwiGLU</b>, <b>GQA/MLA</b>, a <b>decoder-only</b> stack, <b>long-context</b> tricks and <b>FlashAttention</b>, with <b>MoE</b> for the largest models.',
    build=['10_llama_block'],
    sources='Vaswani et al. 2017; Radford et al. 2019 (GPT-2 §2.3); Chowdhery et al. 2022 (PaLM §2); Touvron et al. 2023 (LLaMA §2.2; Llama 2 Table 1); Jiang et al. 2023 (Mistral 7B); Jiang et al. 2024 (Mixtral); DeepSeek-AI 2024 (DeepSeek-V2); Llama Team 2024 (Llama 3 §3.2, Table 3); Meta-Llama-3-8B config.json.',
    css='.cfg{font:500 13px/1.75 "JetBrains Mono",monospace;background:var(--panel-2);border-radius:10px;padding:12px 14px;margin:0;overflow-x:auto}.cfg span{cursor:pointer;border-radius:4px;padding:1px 3px}.cfg span:hover{background:var(--a-soft)}.cfg span.on{background:var(--b-soft);outline:1px solid var(--b)}',
    slides=[
        section('s-p1', 1, 'Same skeleton, different parts', '''    <p class="lede">Pick a change to see which part of the block it replaced. Left: one decoder layer as described in 2017. Right: a Llama 3 layer. Both are a stack of identical layers with residual connections. What changed is inside the boxes.</p>
    <div class="visual">
      <div class="seg" id="chSeg" style="flex-wrap:wrap"><button data-v="normpos" class="on">Norm placement</button><button data-v="normtype">Norm type</button><button data-v="pos">Position</button><button data-v="ffn">FFN</button><button data-v="heads">K/V heads</button><button data-v="family">Stack</button><button data-v="kernel">Attention kernel</button></div>
      <svg id="cmpSvg" viewBox="0 0 660 340" style="margin-top:10px" role="img" aria-label="2017 block vs Llama 3 block"></svg>
      <div class="infobox" id="chInfo" style="background:var(--panel-2);border-radius:10px;padding:12px 14px;margin-top:10px;font-size:14px;color:var(--muted)"></div>
    </div>'''),
        section('s-lim', 2, 'What broke when the 2017 design was scaled up', '''    <div class="grid3">
      <div class="card d"><h3>Training stability</h3><p>Post-norm (a LayerNorm after each residual add) gives large gradients near the output at initialization. It needs a carefully tuned learning-rate warm-up, and deeper stacks make this worse (Xiong et al., 2020).</p></div>
      <div class="card b"><h3>Position handling</h3><p>Sinusoidal or learned vectors are <b>added</b> to the token embedding, so position is mixed into the content. Attention sees relative distance only indirectly, and learned positions don't exist beyond the trained length.</p></div>
      <div class="card c"><h3>Inference memory</h3><p>Every head keeps its own keys and values. During generation that KV cache, not compute, limits batch size and context (Inference deck 02).</p></div>
      <div class="card a"><h3>FFN quality per parameter</h3><p>The ReLU FFN holds about two thirds of a layer's weights. A gated variant (SwiGLU) gets lower perplexity at the same parameter count (Shazeer, 2020).</p></div>
      <div class="card e"><h3>Attention is memory-bound</h3><p>A plain implementation writes the N×N score matrix to GPU memory and reads it back. At long N that traffic, not FLOPs, sets the runtime (Dao et al., 2022).</p></div>
      <div class="card d"><h3>Two stacks for one job</h3><p>An encoder-decoder needs separate inputs, targets and cross-attention. For "continue this text" a single causal stack is simpler, and it learns from every token.</p></div>
    </div>'''),
        your_turn('s-turn', 'Which change is mostly about serving cost?',
                  'Which of these changes mainly reduces memory at inference time, rather than improving training quality?',
                  ['RMSNorm instead of LayerNorm', 'SwiGLU instead of ReLU', 'Grouped-query attention (fewer K/V heads)', 'RoPE instead of sinusoidal embeddings'], 2,
                  '<b>C.</b> GQA lets several query heads share one key/value head, so the KV cache shrinks by the sharing factor (8× for Llama 3 with 64 query heads per 8 KV heads in 70B). PaLM reported MQA as roughly neutral for quality and training speed but a significant saving at decoding time. The others mainly help training speed, stability or quality.'),
        section('s-core', 4, 'The seven swaps, in one table', '''    <div class="visual scroll-x"><table class="tbl">
      <tr><th>Part</th><th>2017</th><th>Modern default</th><th>Problem it solves</th><th>Deck</th></tr>
      <tr><td>Norm placement</td><td>Post-norm: Norm(x + F(x))</td><td><b>Pre-norm</b>: x + F(Norm(x)), plus a final norm</td><td>Stable training without warm-up, even when deep</td><td>02</td></tr>
      <tr><td>Norm type</td><td>LayerNorm (centre + scale)</td><td><b>RMSNorm</b> (scale only)</td><td>Fewer operations, same quality</td><td>02</td></tr>
      <tr><td>Position</td><td>Sinusoidal vector added at the input</td><td><b>RoPE</b>: rotate q and k in every layer</td><td>Attention depends on relative distance; nothing added to the residual stream</td><td>03, 07</td></tr>
      <tr><td>FFN</td><td>ReLU, hidden 4d, 2 matrices</td><td><b>SwiGLU</b>, hidden ≈ ⅔·4d, 3 matrices</td><td>Better perplexity for the same parameters</td><td>04</td></tr>
      <tr><td>K/V heads</td><td>One K/V per query head</td><td><b>GQA</b> (or MQA, or MLA)</td><td>Smaller KV cache, faster decoding</td><td>05</td></tr>
      <tr><td>Stack</td><td>Encoder-decoder</td><td><b>Decoder-only</b>, causal mask</td><td>One stack, every token is a training target, natural fit for chat and KV caching</td><td>06</td></tr>
      <tr><td>Attention kernel</td><td>Materialize the N×N matrix</td><td><b>FlashAttention</b> (tiled, exact)</td><td>Memory linear in N, far less HBM traffic</td><td>09</td></tr>
    </table></div>
''' + deep('Also new, but not in every model', '<ul><li><b>Long context</b>: RoPE scaling (PI, NTK-aware, YaRN), larger RoPE base, sliding-window attention. Decks 07 and 08.</li><li><b>Mixture of Experts</b>: replace the FFN with many expert FFNs and a router. Mixtral and DeepSeek-V2. Deck 10.</li><li><b>No biases</b> in linear layers and norms (PaLM: "this results in increased training stability for large models"). Llama\'s config also has <code>attention_bias: false</code>.</li></ul>')),
        section('s-how', 5, 'How the recipe accumulated, model by model', '''    <p class="lede">No single paper introduced the modern block. Each model adopted a few changes, and the combination that LLaMA published in 2023 became the default. Only details stated in each paper are listed. A dot means the paper doesn't say.</p>
    <div class="visual scroll-x"><table class="tbl">
      <tr><th>Model</th><th>Norm</th><th>Position</th><th>FFN</th><th>Attention</th><th>Notable</th></tr>
      <tr><td>Transformer (2017)</td><td>post-norm LayerNorm</td><td>sinusoidal, added</td><td>ReLU</td><td>MHA</td><td>encoder-decoder</td></tr>
      <tr><td>GPT-2 (2019)</td><td><b>pre-norm</b> + final LN</td><td>learned, added</td><td>·</td><td>MHA</td><td>decoder-only, 1024 context</td></tr>
      <tr><td>PaLM (2022)</td><td>pre-norm, no biases</td><td><b>RoPE</b></td><td><b>SwiGLU</b></td><td><b>MQA</b></td><td>parallel attention + MLP, 256K vocab</td></tr>
      <tr><td>LLaMA (2023)</td><td>pre-norm <b>RMSNorm</b></td><td>RoPE</td><td>SwiGLU, ⅔·4d</td><td>MHA</td><td>the recipe that stuck</td></tr>
      <tr><td>Llama 2 (2023)</td><td>pre-norm RMSNorm</td><td>RoPE</td><td>SwiGLU</td><td><b>GQA</b> (34B, 70B)</td><td>4K context</td></tr>
      <tr><td>Mistral 7B (2023)</td><td>·</td><td>RoPE</td><td>·</td><td>GQA (8 KV heads)</td><td><b>sliding window</b> 4096</td></tr>
      <tr><td>Mixtral (2024)</td><td>as Mistral 7B</td><td>RoPE</td><td>SwiGLU <b>experts</b></td><td>GQA</td><td><b>MoE</b> 8 experts, top-2; dense 32K context</td></tr>
      <tr><td>DeepSeek-V2 (2024)</td><td>·</td><td>decoupled RoPE</td><td>DeepSeekMoE</td><td><b>MLA</b></td><td>236B total, 21B active</td></tr>
      <tr><td>Llama 3 (2024)</td><td>pre-norm RMSNorm</td><td>RoPE, base <b>500,000</b></td><td>SwiGLU</td><td>GQA, 8 KV heads (all sizes)</td><td>128K vocab, document mask</td></tr>
    </table></div>'''),
        section('s-how2', 5, 'Read a real config.json', '''    <p class="lede">These fields are from the published config.json of Meta-Llama-3-8B (a subset; the file also has token ids, dtype and similar). Click any field to see which concept it controls. Being able to read a config like this and explain each line is a quick test of the whole guide.</p>
    <div class="visual">
      <div class="grid2" style="align-items:start">
        <pre class="cfg" id="cfg"></pre>
        <div class="infobox" id="cfgInfo" style="background:var(--panel-2);border-radius:10px;padding:12px 14px;font-size:14px;color:var(--muted)">Click a field on the left.</div>
      </div>
    </div>'''),
        section('s-why', 6, 'Why these changes stuck', '''    <div class="grid2">
      <div class="card a"><h3>They are cheap to adopt</h3><p>Each swap changes one sub-component and keeps the residual stream and the attention + FFN layout. They compose: you can take all of them at once, as LLaMA did.</p></div>
      <div class="card e"><h3>They target scale problems</h3><p>Pre-norm and RMSNorm address stability and speed at depth. GQA and MLA address serving memory. FlashAttention and RoPE scaling address long sequences. These problems only appeared at scale.</p></div>
      <div class="card b"><h3>They were tested in public</h3><p>Shazeer's GLU ablation, Xiong's norm analysis, RoFormer and the GQA uptraining study each report controlled comparisons, and open model families then confirmed the combination.</p></div>
      <div class="card c"><h3>Inference shaped training</h3><p>Several changes (MQA/GQA/MLA, sliding windows, MoE's active parameters) exist mainly because a model is served billions of times after it is trained once.</p></div>
    </div>'''),
        myths('s-myth', [
            ('Modern LLMs use a completely different architecture from the 2017 Transformer.', 'The skeleton is the same: token embeddings, a stack of attention + FFN layers with residual connections, and a softmax output. The changes are <b>targeted swaps</b> inside that skeleton.'),
            ('Each change was invented by the model that made it famous.', 'Mostly not. LLaMA credits pre-normalization to GPT-3, SwiGLU to PaLM (and Shazeer 2020), and rotary embeddings to GPT-Neo (and Su et al. 2021). Its contribution was the combination and the open release.'),
            ('These changes are mostly about accuracy.', 'Many are about <b>cost</b>: RMSNorm (speed), GQA/MLA (KV memory), FlashAttention (memory traffic), MoE (FLOPs per token). Quality had to stay roughly the same; the cost went down.'),
        ]),
        check('s-check', [
            ('mcq', 'In a pre-norm block, where is the normalization applied?', ['After the residual addition', 'To the input of each sub-layer, inside the residual branch', 'Only once, at the end of the network', 'To the attention weights'], 1, '<b>B.</b> x + F(Norm(x)). The residual path itself is never normalized, so a final norm is added before the output head.'),
            ('open', 'Llama 3 8B has num_attention_heads 32 and num_key_value_heads 8. What does that mean, and what does it buy?', 'It uses <b>GQA</b>: groups of 4 query heads share one key/value head. The KV cache is 4× smaller than with full multi-head attention, which means more concurrent sequences or longer contexts per GPU.'),
            ('open', 'Name the parts of a Llama block that differ from the 2017 block, and one reason for each.', 'Pre-norm (stable without warm-up), RMSNorm (cheaper), RoPE (relative positions; no added vector), SwiGLU (better quality per parameter), GQA (smaller KV cache), decoder-only (one stack, every token trains). FlashAttention is the kernel used to compute the same attention faster.'),
        ]),
    ],
    js=r'''
  const L = [
    { k: 'family', t: 'decoder layer of an encoder-decoder' },
    { k: 'pos', t: 'token embedding + sinusoidal PE (input only)' },
    { k: 'heads', t: 'masked self-attention: 8 Q, 8 K, 8 V heads' },
    { k: 'kernel', t: 'scores N×N written to memory' },
    { k: 'normpos', t: 'Add, then LayerNorm (post-norm)' },
    { k: 'cross', t: 'cross-attention to encoder, Add & LayerNorm' },
    { k: 'ffn', t: 'FFN: ReLU, hidden 4d (2 matrices)' },
    { k: 'normtype', t: 'Add, then LayerNorm' },
  ];
  const R = [
    { k: 'family', t: 'decoder-only stack, causal mask' },
    { k: 'pos', t: 'token embedding only (no position vector)' },
    { k: 'normtype', t: 'RMSNorm (pre-norm, inside the branch)' },
    { k: 'heads', t: 'GQA (32 Q, 8 K/V heads) + RoPE on q, k' },
    { k: 'kernel', t: 'FlashAttention: tiled, exact' },
    { k: 'normpos', t: 'Add (residual is never normalized)' },
    { k: 'ffn', t: 'RMSNorm, then SwiGLU FFN (3 matrices, ≈⅔·4d)' },
    { k: 'final', t: 'final RMSNorm before the output head' },
  ];
  const INFO = {
    normpos: '<b>Pre-norm.</b> 2017: x ← Norm(x + F(x)). Modern: x ← x + F(Norm(x)). The residual stream becomes a clean sum of every layer\'s output, which keeps gradients well behaved at initialization and removes the need for warm-up (Xiong et al., 2020). GPT-2 already made this move. <a href="../02-normalization/index.html">Deck 02 →</a>',
    normtype: '<b>RMSNorm.</b> Drop LayerNorm\'s mean subtraction and bias and keep only division by the root mean square. Zhang & Sennrich (2019) report similar quality with 7–64% less running time. LLaMA adopted it. <a href="../02-normalization/index.html">Deck 02 →</a>',
    pos: '<b>RoPE.</b> Instead of adding a position vector to the embeddings once, rotate the query and key vectors in every attention layer by an angle proportional to the position. The q·k score then depends only on the distance between tokens. <a href="../03-rope/index.html">Deck 03 →</a>',
    ffn: '<b>SwiGLU.</b> FFN(x) = (SiLU(xW_gate) ⊙ xW_up)W_down. Three matrices instead of two, so the hidden size drops to about ⅔·4d to keep the parameter count. Lower perplexity in Shazeer\'s 2020 ablation. <a href="../04-swiglu/index.html">Deck 04 →</a>',
    heads: '<b>GQA.</b> Many query heads share each key/value head. The KV cache shrinks by the sharing factor with little quality loss (Ainslie et al., 2023). MQA (one shared K/V head) and MLA (compressed latent K/V) are the extremes. <a href="../05-attention-variants/index.html">Deck 05 →</a>',
    family: '<b>Decoder-only.</b> One stack with a causal mask, trained to predict the next token at every position. No separate encoder and no cross-attention. Wang et al. (2022) found causal decoders generalize best zero-shot after self-supervised pretraining alone. <a href="../06-decoder-only/index.html">Deck 06 →</a>',
    kernel: '<b>FlashAttention.</b> Same maths, different kernel: compute attention in tiles that fit in on-chip SRAM, using an online softmax, so the N×N matrix never goes to HBM. Exact, linear memory in N, and much faster. <a href="../09-flash-attention/index.html">Deck 09 →</a>',
  };
  let pick = 'normpos';
  const draw = () => {
    const s = clear(document.getElementById('cmpSvg'));
    const col = (items, x, title) => {
      svg('text', { x: x + 150, y: 18, 'text-anchor': 'middle', class: 't', style: 'font-weight:700', text: title }, s);
      items.forEach((b, i) => {
        const y = 312 - i * 37, on = b.k === pick || (pick === 'normpos' && b.k === 'final' && x > 300);
        svg('rect', { x, y: y - 24, width: 300, height: 30, rx: 7, style: `fill:${on ? (x < 300 ? 'var(--d-soft)' : 'var(--e-soft)') : 'var(--panel-2)'};stroke:${on ? (x < 300 ? 'var(--d)' : 'var(--e)') : 'var(--line)'};stroke-width:${on ? 2 : 1}` }, s);
        svg('text', { x: x + 150, y: y - 4, 'text-anchor': 'middle', class: on ? 't' : 'tm', style: on ? 'font-weight:600' : '', text: b.t }, s);
      });
    };
    col(L, 10, '2017 (one decoder layer)'); col(R, 350, 'Llama 3 (one layer)');
    svg('text', { x: 330, y: 334, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: 'read each column bottom to top · red = replaced, green = replacement' }, s);
    document.getElementById('chInfo').innerHTML = INFO[pick];
  };
  Deck.seg('chSeg', v => { pick = v; draw(); });

  const CFG = [
    ['hidden_size', 4096, 'Model width d. Every token is a 4,096-number vector in the residual stream.'],
    ['num_hidden_layers', 32, 'Number of identical decoder blocks stacked.'],
    ['num_attention_heads', 32, 'Query heads. Head dimension = 4096 / 32 = 128.'],
    ['num_key_value_heads', 8, '<b>GQA</b>: only 8 K/V heads, each shared by 4 query heads, so the KV cache is 4× smaller than MHA. 2 × 32 layers × 8 × 128 × 2 bytes = 128 KiB per token in BF16. (Deck 05)'],
    ['intermediate_size', 14336, '<b>SwiGLU</b> hidden size. 3.5 × d: Meta\'s formula ⅔·4d × 1.3, rounded up to a multiple of 1024. (Deck 04)'],
    ['hidden_act', '"silu"', '<b>SwiGLU</b>: the gate uses SiLU = Swish₁, x·σ(x). (Deck 04)'],
    ['rms_norm_eps', '1e-05', '<b>RMSNorm</b> epsilon. No mean, no bias. (Deck 02)'],
    ['rope_theta', '500000.0', '<b>RoPE</b> base. Llama 2 used 10,000; Llama 3 raised it to 500,000 to support longer contexts: every pair rotates more slowly. (Decks 03, 07)'],
    ['max_position_embeddings', 8192, 'Context length the base model was pretrained with (8K). Llama 3.1 later extended this to 128K. Note there is no position embedding <i>table</i>; the name is historical. (Deck 07)'],
    ['vocab_size', 128256, 'Tokenizer size: 128K tokens (100K from tiktoken + 28K extra). With untied embeddings the input table and output head each cost 128,256 × 4,096 ≈ 525M parameters.'],
    ['tie_word_embeddings', 'false', 'Separate input embedding and output projection matrices (PaLM shared them).'],
    ['attention_bias', 'false', 'No bias vectors in the attention projections.'],
  ];
  const pre = document.getElementById('cfg'); pre.innerHTML = '{\n' + CFG.map(([k, v], i) => `  <span data-i="${i}">"${k}": ${v}${i < CFG.length - 1 ? ',' : ''}</span>`).join('\n') + '\n}';
  pre.querySelectorAll('span').forEach(sp => sp.addEventListener('click', () => {
    pre.querySelectorAll('span').forEach(x => x.classList.toggle('on', x === sp));
    const c = CFG[+sp.dataset.i]; document.getElementById('cfgInfo').innerHTML = `<b style="font-family:JetBrains Mono,monospace">${c[0]}</b><br>${c[2]}`;
  }));
  pre.querySelectorAll('span')[3].click();
''',
    line='A modern LLM is the 2017 Transformer with seven targeted swaps: pre-norm, RMSNorm, RoPE, SwiGLU, shared or compressed K/V heads, a decoder-only stack and an IO-aware attention kernel.',
    explain='The skeleton hasn\'t changed: attention plus FFN layers with residual connections. What changed are the parts that broke at scale. Normalization moved inside the residual branch and became RMSNorm, for stability and speed. Positions became rotations of q and k (RoPE), so attention depends on relative distance. The FFN became a gated SwiGLU. Query heads now share key/value heads (GQA) to shrink the KV cache. Everything runs as a single causal decoder, computed with FlashAttention. Long-context tricks and Mixture-of-Experts sit on top for the models that need them.',
    recap=[('Problem', 'the 2017 block had stability, position, memory and speed problems at scale.'), ('Core idea', 'keep the skeleton; swap norm, position, FFN, K/V heads, stack type and kernel.'), ('Read configs', 'every field in a config.json maps to one of these decisions.')],
)

# =============================================================== 02
DECKS['02-normalization'] = dict(
    title='Pre-norm and RMSNorm', h1='Pre-norm and RMSNorm',
    sub='Where the normalization sits in a residual block decides whether a deep Transformer trains smoothly. And most of what LayerNorm computes turns out to be unnecessary.',
    prob='Deep post-norm Transformers need a carefully tuned learning-rate warm-up or they diverge, and LayerNorm itself costs time on every token in every layer.',
    core='<b>Pre-norm</b>: normalize the input of each sub-layer, x + F(Norm(x)), so the residual path is a clean identity. <b>RMSNorm</b>: skip the mean subtraction and just divide by the root mean square.',
    build=['01_norms_prenorm'],
    sources='Xiong et al. 2020, "On Layer Normalization in the Transformer Architecture" (ICML); Zhang & Sennrich 2019, "Root Mean Square Layer Normalization" (NeurIPS); Radford et al. 2019 (GPT-2 §2.3); Touvron et al. 2023 (LLaMA §2.2).',
    slides=[
        section('s-p1', 1, 'Two ways to wire the same block', '''    <p class="lede">A Transformer layer is a sub-layer F (attention or FFN) plus a residual connection plus a normalization. The 2017 paper puts the norm <b>after</b> the addition. Switch between the two wirings and follow the main path (thick line) from input to output.</p>
    <div class="visual">
      <div class="seg" id="wSeg"><button data-v="post" class="on">Post-norm (2017)</button><button data-v="pre">Pre-norm (GPT-2 onward)</button></div>
      <svg id="wSvg" viewBox="0 0 660 200" style="margin-top:10px" role="img" aria-label="Residual block wiring"></svg>
      <p class="readout" id="wOut"></p>
    </div>'''),
        section('s-lim', 2, 'What goes wrong with post-norm', '''    <div class="grid3">
      <div class="card d"><h3>Large gradients near the output</h3><p>Xiong et al. (2020) show with mean-field analysis that at initialization the gradients of parameters near the output layer are large in post-norm, and they don't shrink as you add layers.</p></div>
      <div class="card b"><h3>Warm-up becomes mandatory</h3><p>With large gradients, a normal learning rate makes the first updates too big. Post-norm models need a warm-up stage: start with a tiny learning rate and ramp up. That is one more sensitive hyperparameter, and it slows training.</p></div>
      <div class="card c"><h3>LayerNorm does two jobs</h3><p>LayerNorm re-centres (subtracts the mean) and re-scales (divides by the standard deviation), then applies a gain and a bias. That is two reductions per token per norm, twice per layer, on every token ever processed.</p></div>
    </div>'''),
        your_turn('s-turn', 'Where should the norm go?',
                  'You want the residual stream to carry each layer\'s output straight to the end of the network, unchanged. Which wiring achieves that?',
                  ['Norm(x + F(x))', 'x + F(Norm(x))', 'Norm(x) + F(x)', 'F(Norm(x + x))'], 1,
                  '<b>B.</b> In x + F(Norm(x)), the norm only touches the copy that goes into F. The x that is passed along is never rescaled, so after L layers the output is x₀ + F₁ + F₂ + … + F_L: a plain sum with an identity path from every layer to the end.'),
        section('s-core', 4, 'Two independent changes', '''    <div class="grid2">
      <div class="card a"><h3>Pre-norm: move the norm inside the branch</h3><p><code>x ← x + Attn(Norm(x))</code><br><code>x ← x + FFN(Norm(x))</code><br>Then add <b>one final norm</b> before the output head, because the residual stream is never normalized along the way. GPT-2 did exactly this: "Layer normalization was moved to the input of each sub-block… and an additional layer normalization was added after the final self-attention block."</p></div>
      <div class="card e"><h3>RMSNorm: keep only the re-scaling</h3><p><code>RMSNorm(x) = g ⊙ x / √(mean(x²) + ε)</code><br>No mean subtraction, no bias. Zhang & Sennrich hypothesize that LayerNorm's re-centring invariance is "dispensable" and report comparable quality with <b>7–64% less running time</b> across their models. LLaMA uses pre-norm with RMSNorm.</p></div>
    </div>
''' + deep('Why the final norm matters', '<p>In pre-norm, each layer <b>adds</b> to the residual stream, so its scale grows with depth (notebook 01 measures this). Each sub-layer still sees normalized input, but the logits would see the raw, growing stream. The final RMSNorm (<code>model.norm</code> in Llama code) fixes the scale once, just before the output head.</p>')),
        section('s-how', 5, 'Measured: the last layer\'s gradient vs depth <span class="ill">toy model, random weights</span>', '''    <p class="lede">Stacks of L blocks (FFN sub-layers, Xavier init, LayerNorm), with the gradient norm of the <b>last layer's</b> weights for a squared-error loss. These are the values printed by the experiment in notebook 01, a small-scale reproduction of Xiong et al.'s analysis.</p>
    <div class="visual">
      <svg id="gSvg" viewBox="0 0 660 250" role="img" aria-label="Gradient norm vs depth"></svg>
      <div class="legend"><span><i style="background:var(--d)"></i>post-norm</span><span><i style="background:var(--a)"></i>pre-norm</span><span><i style="background:var(--faint)"></i>pre-norm at L=3 × √(3/L)</span></div>
    </div>
''' + deep('How to read it', '<p><b>Post-norm</b> stays between about 165 and 210 however deep the stack: the gradient near the output does not shrink with depth, which is the paper\'s result for post-LN. With a normal learning rate those large updates destabilize early training, hence warm-up. <b>Pre-norm</b> falls roughly like 1/√L (Xiong et al. prove an O(d√(ln d / L)) scaling), so updates stay modest and warm-up can be dropped. In the paper, pre-LN Transformers trained <b>without warm-up</b> reached comparable results with significantly less training time and hyperparameter tuning.</p>')),
        section('s-how2', 5, 'LayerNorm vs RMSNorm on a real vector', '''    <p class="lede">Eight features of one token. Shift them all up, or scale them all, and compare what the two norms output. (Gain g = 1, bias = 0.)</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">Shift every feature <input type="range" id="nS" min="-3" max="3" step="0.1" value="0"> <output id="nSo"></output></label>
        <label class="ctl">Scale every feature <input type="range" id="nK" min="0.2" max="5" step="0.1" value="1"> <output id="nKo"></output></label>
      </div>
      <svg id="nSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Input, LayerNorm and RMSNorm outputs"></svg>
      <p class="readout" id="nOut"></p>
    </div>
''' + deep('What the demo shows', '<ul><li><b>Scaling</b> the input changes neither output: both norms are re-scaling invariant.</li><li><b>Shifting</b> the input changes RMSNorm\'s output but not LayerNorm\'s, because LayerNorm subtracts the mean first. RMSNorm gives up shift invariance, and the paper\'s experiments suggest models don\'t need it.</li><li>Cost: LayerNorm needs a mean and a variance per token; RMSNorm needs one sum of squares. On GPUs these are memory-bound reductions, so the saving is in passes over the data.</li></ul>')),
        section('s-why', 6, 'Why pre-norm trains more easily', '''    <div class="grid2">
      <div class="card a"><h3>An identity path to every layer</h3><p>The output is x₀ plus the sum of every layer's contribution, so each layer receives gradient directly from the loss through the residual stream. That is the same idea as pre-activation ResNets, which GPT-2 cites.</p></div>
      <div class="card e"><h3>Gradients well-behaved at initialization</h3><p>Xiong et al. show pre-LN's gradients are well behaved at init, so the warm-up stage can be removed. Fewer hyperparameters, faster training.</p></div>
      <div class="card b"><h3>The cost: a growing stream</h3><p>Because nothing renormalizes the stream, its magnitude grows with depth. Later layers' contributions are relatively smaller, which is why a final norm is required and why some very deep models add extra tricks.</p></div>
      <div class="card c"><h3>RMSNorm: a free speed-up</h3><p>Same placement, fewer operations. Because it's a drop-in replacement with comparable quality, there is little reason not to use it, and LLaMA, Llama 2 and Llama 3 all do.</p></div>
    </div>'''),
        myths('s-myth', [
            ('LayerNorm normalizes across the batch, like BatchNorm.', 'No. Both LayerNorm and RMSNorm normalize <b>each token\'s feature vector on its own</b>. Nothing depends on other tokens or other sequences, which is why they work the same in training and at inference with any batch size.'),
            ('Pre-norm means you don\'t need a norm at the end.', 'The opposite. Because the residual stream is never normalized, pre-norm models <b>need</b> a final norm before the output head.'),
            ('RMSNorm is an approximation of LayerNorm that costs some quality.', 'It is a different normalization (no re-centring) that the authors found <b>comparable</b> in quality across tasks, and faster. LLaMA-family models use it.'),
        ]),
        check('s-check', [
            ('mcq', 'Which formula is RMSNorm?', ['(x − μ)/σ · g + b', 'x / √(mean(x²) + ε) · g', 'x / max|x|', '(x − μ) / √(mean(x²))'], 1, '<b>B.</b> Divide by the root mean square and scale by a learned gain. No mean and no bias.'),
            ('open', 'Why does post-norm usually need a learning-rate warm-up?', 'At initialization the gradients of parameters near the output are large (Xiong et al., 2020). A full learning rate on large gradients makes the first updates too big and training unstable; warm-up keeps early steps small.'),
            ('open', 'Write the two lines of a pre-norm Llama block.', '<code>h = x + Attention(RMSNorm(x))</code> and <code>out = h + SwiGLU(RMSNorm(h))</code>. After the last block: <code>RMSNorm</code>, then the output head.'),
        ]),
    ],
    js=r'''
  Deck.seg('wSeg', v => {
    const s = clear(document.getElementById('wSvg')), pre = v === 'pre';
    const box = (x, label, cls) => { svg('rect', { x, y: 70, width: 110, height: 44, rx: 8, class: cls }, s); svg('text', { x: x + 55, y: 97, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:600', text: label }, s); };
    svg('line', { x1: 20, x2: 640, y1: 40, y2: 40, style: 'stroke:var(--a);stroke-width:5' }, s);
    svg('text', { x: 24, y: 28, class: 'tm', text: 'x (residual stream)' }, s);
    if (pre) {
      svg('path', { d: 'M120 40 V92 H150', fill: 'none', style: 'stroke:var(--muted);stroke-width:2' }, s);
      box(150, 'Norm', 'f-c'); box(300, 'F (attn/FFN)', 'f-b');
      svg('line', { x1: 260, x2: 300, y1: 92, y2: 92, style: 'stroke:var(--muted);stroke-width:2' }, s);
      svg('path', { d: 'M410 92 H470 V48', fill: 'none', style: 'stroke:var(--muted);stroke-width:2' }, s);
      svg('circle', { cx: 470, cy: 40, r: 12, style: 'fill:var(--panel);stroke:var(--a);stroke-width:2' }, s); svg('text', { x: 470, y: 45, 'text-anchor': 'middle', class: 't', text: '+' }, s);
      svg('text', { x: 330, y: 160, 'text-anchor': 'middle', class: 'tm', text: 'x ← x + F(Norm(x)): the thick line never passes through a norm' }, s);
    } else {
      svg('path', { d: 'M120 40 V92 H190', fill: 'none', style: 'stroke:var(--muted);stroke-width:2' }, s);
      box(190, 'F (attn/FFN)', 'f-b');
      svg('path', { d: 'M300 92 H380 V48', fill: 'none', style: 'stroke:var(--muted);stroke-width:2' }, s);
      svg('circle', { cx: 380, cy: 40, r: 12, style: 'fill:var(--panel);stroke:var(--a);stroke-width:2' }, s); svg('text', { x: 380, y: 45, 'text-anchor': 'middle', class: 't', text: '+' }, s);
      svg('rect', { x: 440, y: 18, width: 90, height: 44, rx: 8, class: 'f-d' }, s); svg('text', { x: 485, y: 45, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:600', text: 'Norm' }, s);
      svg('text', { x: 330, y: 160, 'text-anchor': 'middle', class: 'tm', text: 'x ← Norm(x + F(x)): the main path is renormalized after every sub-layer' }, s);
    }
    document.getElementById('wOut').innerHTML = pre
      ? 'After L layers: output = x₀ + F₁ + F₂ + … + F_L, then one final norm. Every layer has a direct, un-rescaled route to the output.'
      : 'After L layers the signal from layer 1 has passed through L norms. Each one rescales it, and gradients near the output are large at initialization.';
  });
  (() => {
    const D = [3, 6, 12, 24, 48], post = [190.6, 207.1, 192.0, 166.4, 204.1], pre = [163.2, 147.0, 107.3, 67.4, 56.3];
    const s = document.getElementById('gSvg'), L0 = 70, R0 = 620, T0 = 16, B0 = 200, X = i => L0 + i * (R0 - L0) / 4, Y = v => B0 - v / 240 * (B0 - T0);
    [0, 60, 120, 180, 240].forEach(v => { svg('line', { x1: L0, x2: R0, y1: Y(v), y2: Y(v), class: 'ln' }, s); svg('text', { x: L0 - 8, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm', text: v }, s); });
    D.forEach((d, i) => svg('text', { x: X(i), y: B0 + 18, 'text-anchor': 'middle', class: 'tm', text: 'L=' + d }, s));
    const line = (vals, color, dash) => svg('polyline', { points: vals.map((v, i) => `${X(i)},${Y(v)}`).join(' '), fill: 'none', style: `stroke:${color};stroke-width:3${dash ? ';stroke-dasharray:6 5' : ''}` }, s);
    line(D.map(d => pre[0] * Math.sqrt(3 / d)), 'var(--faint)', true); line(post, 'var(--d)'); line(pre, 'var(--a)');
    [[post, 'var(--d)'], [pre, 'var(--a)']].forEach(([v, c]) => v.forEach((y, i) => svg('circle', { cx: X(i), cy: Y(y), r: 5, style: `fill:${c}` }, s)));
    svg('text', { x: (L0 + R0) / 2, y: B0 + 40, 'text-anchor': 'middle', class: 'tm', text: 'number of blocks (log-spaced)' }, s);
    svg('text', { x: 16, y: (T0 + B0) / 2, 'text-anchor': 'middle', class: 'tm', transform: `rotate(-90 16 ${(T0 + B0) / 2})`, text: '|grad| of last layer' }, s);
  })();
  const base = [1.2, -0.4, 2.1, 0.3, -1.5, 0.9, 1.8, -0.6];
  Deck.bind(['nS', 'nK'], () => {
    const sh = Deck.val('nS'), k = Deck.val('nK'); Deck.out('nSo', sh.toFixed(1)); Deck.out('nKo', k.toFixed(1) + '×');
    const x = base.map(v => (v + sh) * k), n = x.length, mu = x.reduce((a, b) => a + b) / n;
    const sd = Math.sqrt(x.reduce((a, b) => a + (b - mu) ** 2, 0) / n + 1e-6), rms = Math.sqrt(x.reduce((a, b) => a + b * b, 0) / n + 1e-6);
    const ln = x.map(v => (v - mu) / sd), rn = x.map(v => v / rms);
    const s = clear(document.getElementById('nSvg')), groups = [['input x', x, 'var(--faint)'], ['LayerNorm', ln, 'var(--c)'], ['RMSNorm', rn, 'var(--a)']];
    groups.forEach(([name, v, c], gi) => {
      const x0 = 20 + gi * 215, mid = 120, sc = 22;
      svg('text', { x: x0 + 95, y: 16, 'text-anchor': 'middle', class: 't', style: 'font-weight:600', text: name }, s);
      svg('line', { x1: x0, x2: x0 + 190, y1: mid, y2: mid, class: 'ln' }, s);
      v.forEach((val, i) => { const h = Math.max(-95, Math.min(95, val * sc)); svg('rect', { x: x0 + 6 + i * 23, y: h > 0 ? mid - h : mid, width: 17, height: Math.abs(h), rx: 3, style: `fill:${c}` }, s); });
      const m = v.reduce((a, b) => a + b) / n, r = Math.sqrt(v.reduce((a, b) => a + b * b, 0) / n);
      svg('text', { x: x0 + 95, y: 222, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: `mean ${m.toFixed(2)} · rms ${r.toFixed(2)}` }, s);
    });
    document.getElementById('nOut').innerHTML = sh === 0 ? 'Move the shift slider: LayerNorm\'s bars stay put, RMSNorm\'s change. Move scale: neither changes.' : `With a shift of ${sh.toFixed(1)}, RMSNorm output mean = <b>${(rn.reduce((a, b) => a + b) / n).toFixed(2)}</b> (it keeps the offset), while LayerNorm's mean stays <b>0.00</b>.`;
  });
''',
    line='Put the norm inside the residual branch (pre-norm) and drop the mean (RMSNorm): stable deep training without warm-up, at lower cost.',
    explain='The 2017 Transformer normalizes after each residual addition. At initialization that makes gradients near the output large regardless of depth, so training needs a learning-rate warm-up. Pre-norm normalizes only the input to each sub-layer, x plus F of Norm x, so the residual stream is a clean sum with an identity path from every layer to the output; gradients are well behaved and warm-up can go. You then need one final norm before the output head. RMSNorm goes further and drops LayerNorm\'s mean subtraction, dividing only by the root mean square. Quality is comparable and it is cheaper. Llama uses both.',
    recap=[('Problem', 'post-norm needs warm-up and LayerNorm costs two reductions per token.'), ('Pre-norm', 'x + F(Norm(x)) plus a final norm; the gradient no longer stays large near the output.'), ('RMSNorm', 'x / rms(x) · g; scale-invariant, not shift-invariant, 7–64% faster in the paper.')],
)

# =============================================================== 03
DECKS['03-rope'] = dict(
    title='RoPE', h1='Rotary position embeddings (RoPE)',
    sub='How rotating queries and keys by an angle proportional to position makes attention depend only on the distance between tokens, with no position vector added anywhere.',
    prob='Attention is order-blind. The 2017 fix adds a position vector to each token embedding, which mixes position into content and lets attention see relative distance only indirectly.',
    core='Split q and k into 2-D pairs and <b>rotate</b> pair i by angle <b>m·θᵢ</b> at position m, with θᵢ = 10000<sup>−2i/d</sup>. The dot product of two rotated vectors depends only on the angle <b>difference</b>, so q·k depends on <b>m − n</b>.',
    build=['02_rope'],
    sources='Su et al. 2021, "RoFormer: Enhanced Transformer with Rotary Position Embedding" (§3.2–3.4); Touvron et al. 2023 (LLaMA §2.2); Llama Team 2024 (Llama 3 §3.2, RoPE base 500,000); Chowdhery et al. 2022 (PaLM §2). Another visual explainer: murtuzasaifee.github.io/RoPE_Visualization.',
    slides=[
        section('s-p1', 1, 'Attention can\'t see order by itself', '''    <p class="lede">Self-attention scores every pair of tokens with q·k. Shuffle the input tokens and each token gets exactly the same scores, just permuted. "dog bites man" and "man bites dog" would look identical. Position has to be injected somehow.</p>
    <div class="grid2">
      <div class="card b"><h3>The 2017 answer: add a vector</h3><p>x₀ = embedding(token) + PE(position), once, at the input. Every later layer has to untangle "what" from "where" inside the same vector. Recap: <a href="../../transformer/07-positional-encoding/index.html">Transformer deck 07</a>.</p></div>
      <div class="card a"><h3>What attention actually needs</h3><p>Mostly <b>relative</b> information: "the word two to my left", "the subject of this clause". A score that depends on m − n directly would be ideal, and it should keep working when the whole sequence shifts.</p></div>
    </div>'''),
        section('s-lim', 2, 'Limits of added position vectors', '''    <div class="grid3">
      <div class="card d"><h3>Absolute, not relative</h3><p>With x + PE, the score (x_m + p_m)·W·(x_n + p_n) has content-position cross terms. Relative distance appears only through how the network learns to combine them.</p></div>
      <div class="card b"><h3>Added once, diluted later</h3><p>The position signal enters at layer 0 and has to survive every residual update to be useful in layer 40.</p></div>
      <div class="card c"><h3>Learned tables stop at L</h3><p>GPT-2-style learned position embeddings have exactly 1,024 rows. Position 1,025 has no vector at all.</p></div>
    </div>
''' + deep('Relative position attempts before RoPE', '<p>Relative-position schemes (Shaw et al. 2018; T5\'s bucketed biases) add learned terms that depend on m − n to the attention scores. They work, but they need extra tables or bias terms, and RoFormer argues they are awkward to combine with linear-attention variants. RoPE gets relative behaviour from a fixed rotation with <b>no learned parameters</b>.</p>')),
        your_turn('s-turn', 'Rotate both, compare',
                  'Rotate query q by angle mθ and key k by angle nθ in the same plane. Their dot product depends on…',
                  ['m only', 'n only', 'm − n only (plus the vectors themselves)', 'm + n'], 2,
                  '<b>C.</b> A dot product depends only on the vectors\' lengths and the angle between them. Rotating q by mθ and k by nθ changes that angle by (m − n)θ. Shift both positions by the same amount and nothing changes. RoFormer: "the inner product encodes position information only in the relative form."'),
        section('s-core', 4, 'The RoPE recipe', '''    <div class="grid3">
      <div class="card a"><h3>1. Pair up dimensions</h3><p>Split a d-dimensional q (or k) into d/2 pairs: (x₀,x₁), (x₂,x₃), … Treat each pair as a point in a 2-D plane, or as a complex number x₂ᵢ + i·x₂ᵢ₊₁.</p></div>
      <div class="card b"><h3>2. Give each pair a speed</h3><p>θᵢ = base<sup>−2i/d</sup>, base = 10,000 (RoFormer, LLaMA) or 500,000 (Llama 3). Pair 0 turns about once every 6 tokens; the last pair takes tens of thousands of tokens per turn.</p></div>
      <div class="card e"><h3>3. Rotate by position</h3><p>At position m, rotate pair i by m·θᵢ. Do this to q and k in <b>every attention layer</b>, after the projections. Values are not rotated, and nothing is added to the residual stream.</p></div>
    </div>
    <div class="eq">q′ₘ · k′ₙ = Re[ Σᵢ qᵢ · conj(kᵢ) · e<sup>i(m−n)θᵢ</sup> ]   (pairs written as complex numbers)</div>'''),
        section('s-how', 5, 'One pair, two tokens: only the gap matters', '''    <p class="lede">The left dial shows one pair of the query at position m; the right shows one pair of the key at position n. The score contribution is their dot product. Drag m and n, then use "shift both" to slide the pair along the sequence without changing the gap.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">Query position m <input type="range" id="rM" min="0" max="60" step="1" value="12"> <output id="rMo"></output></label>
        <label class="ctl">Key position n <input type="range" id="rN" min="0" max="60" step="1" value="9"> <output id="rNo"></output></label>
        <div class="seg" id="rPair"><button data-v="0" class="on">pair 0 (fast)</button><button data-v="2">pair 2</button><button data-v="5">pair 5 (slow)</button></div>
        <button class="btn" id="rShift">shift both +10</button>
      </div>
      <svg id="rSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Rotated query and key"></svg>
      <p class="readout" id="rOut"></p>
    </div>
    <p class="caption">d = 16 here (8 pairs), base 10,000, so θ₀ = 1 rad/token, θ₂ = 0.1, θ₅ ≈ 0.0032. Real heads use d = 128 (64 pairs).</p>'''),
        section('s-how2', 5, 'Many speeds: the frequency spectrum and long-term decay', '''    <p class="lede">Each pair rotates at its own speed. Fast pairs separate nearby positions; slow pairs separate far-apart ones. For q = k (all ones) the total score drifts down as the distance grows. RoFormer calls this <b>long-term decay</b>: distant tokens interact more weakly by default.</p>
    <div class="visual">
      <div class="seg" id="bSeg"><button data-v="10000" class="on">base 10,000 (Llama 2)</button><button data-v="500000">base 500,000 (Llama 3)</button></div>
      <svg id="dSvg" viewBox="0 0 660 240" style="margin-top:10px" role="img" aria-label="Score vs distance"></svg>
      <p class="readout" id="dOut"></p>
    </div>
''' + deep('Wavelengths for d = 128, base 10,000', '<p>Tokens per full turn of pair i is 2π/θᵢ: pair 0 ≈ <b>6</b>, pair 16 ≈ <b>63</b>, pair 32 ≈ <b>628</b>, pair 48 ≈ <b>6,283</b>, pair 63 ≈ <b>54,410</b> (computed in notebook 02). Pairs whose wavelength exceeds the training length never complete a turn during training. That fact is the key to long-context extension in deck 07.</p>')),
        section('s-why', 6, 'Why RoPE won', '''    <div class="grid2">
      <div class="card a"><h3>Relative by construction</h3><p>The score depends on m − n, proven in one line with complex numbers. The model doesn't have to learn to undo absolute positions.</p></div>
      <div class="card e"><h3>Zero parameters, nothing added to the stream</h3><p>A fixed rotation, applied inside attention, in every layer. The residual stream carries content only, and every layer gets fresh position information.</p></div>
      <div class="card b"><h3>Plays well with the KV cache</h3><p>A key's rotation depends only on its own position, so it is rotated once when written to the cache and never touched again. (Relative-bias schemes recompute per pair.)</p></div>
      <div class="card c"><h3>Adopted everywhere</h3><p>GPT-NeoX/GPT-J, PaLM ("better performance on long sequences"), LLaMA, Mistral and most open models since. Its main weakness, behaviour beyond the trained length, has its own family of fixes (deck 07).</p></div>
    </div>'''),
        myths('s-myth', [
            ('RoPE adds a position vector to the token embeddings.', 'Nothing is added. RoPE <b>multiplies</b> (rotates) q and k inside each attention layer. The residual stream never sees a position vector.'),
            ('RoPE is applied to the values too.', 'Only <b>queries and keys</b> are rotated, because only their dot product needs position. Values carry content to the output unchanged.'),
            ('With RoPE a model works at any length.', 'The maths extends to any position, but the model never saw the large angles of slow pairs beyond its training length, so quality collapses without scaling or long-context training (deck 07).'),
        ]),
        check('s-check', [
            ('mcq', 'For head dimension d = 128 and base 10,000, what is θ for pair i = 0?', ['10,000', '1 radian per token', '1/128', '2π'], 1, '<b>B.</b> θ₀ = 10000<sup>0</sup> = 1 rad/token, about one full turn every 6.3 tokens. The fastest pair.'),
            ('open', 'Why does shifting every position by the same amount leave all RoPE attention scores unchanged?', 'Each score depends on the angle between rotated q and k, which is (m − n)θᵢ for each pair. Adding the same shift to m and n leaves m − n unchanged.'),
            ('open', 'Llama 3 raised the RoPE base from 10,000 to 500,000. What does that do to the rotation speeds?', 'Every θᵢ = base<sup>−2i/d</sup> gets smaller except pair 0, so pairs rotate more slowly and wavelengths stretch. More pairs stay distinguishable over long distances, which supports longer contexts.'),
        ]),
    ],
    js=r'''
  let pair = 0;
  const draw = () => {
    const m = Deck.val('rM'), n = Deck.val('rN'); Deck.out('rMo', m); Deck.out('rNo', n);
    const th = Math.pow(10000, -2 * pair / 16), q0 = Math.atan2(0.6, 1), k0 = Math.atan2(-0.3, 1);
    const qa = q0 + m * th, ka = k0 + n * th, qr = 1.166, kr = 1.044;
    const s = clear(document.getElementById('rSvg'));
    const dial = (cx, ang0, ang, r, color, label, pos) => {
      svg('circle', { cx, cy: 110, r: 80, style: 'fill:none;stroke:var(--line)' }, s);
      svg('line', { x1: cx - 85, x2: cx + 85, y1: 110, y2: 110, class: 'ln' }, s); svg('line', { x1: cx, x2: cx, y1: 25, y2: 195, class: 'ln' }, s);
      svg('line', { x1: cx, y1: 110, x2: cx + 70 * r * Math.cos(ang0), y2: 110 - 70 * r * Math.sin(ang0), style: 'stroke:var(--faint);stroke-width:2;stroke-dasharray:4 3' }, s);
      svg('line', { x1: cx, y1: 110, x2: cx + 70 * r * Math.cos(ang), y2: 110 - 70 * r * Math.sin(ang), style: `stroke:${color};stroke-width:4` }, s);
      svg('circle', { cx: cx + 70 * r * Math.cos(ang), cy: 110 - 70 * r * Math.sin(ang), r: 6, style: `fill:${color}` }, s);
      svg('text', { x: cx, y: 222, 'text-anchor': 'middle', class: 't', text: `${label} at position ${pos}: rotated ${(pos * th).toFixed(2)} rad` }, s);
    };
    dial(150, q0, qa, qr, 'var(--a)', 'q', m); dial(510, k0, ka, kr, 'var(--b)', 'k', n);
    const score = qr * kr * Math.cos(qa - ka);
    svg('text', { x: 330, y: 100, 'text-anchor': 'middle', class: 't', style: 'font-weight:700;font-size:15px', text: `q·k = ${score.toFixed(3)}` }, s);
    svg('text', { x: 330, y: 122, 'text-anchor': 'middle', class: 'tm', text: `m − n = ${m - n}` }, s);
    document.getElementById('rOut').innerHTML = `Pair ${pair}: θ = ${th.toPrecision(3)} rad/token. Angle between q and k = (q₀ − k₀) + (m − n)·θ = <b>${(qa - ka).toFixed(3)} rad</b>. Try "shift both": m and n move, the score doesn't.`;
  };
  Deck.bind(['rM', 'rN'], draw);
  Deck.seg('rPair', v => { pair = +v; draw(); });
  document.getElementById('rShift').addEventListener('click', () => {
    const M = document.getElementById('rM'), N = document.getElementById('rN');
    if (+M.value + 10 > 60 || +N.value + 10 > 60) { M.value = Math.max(0, +M.value - 40); N.value = Math.max(0, +N.value - 40); } else { M.value = +M.value + 10; N.value = +N.value + 10; }
    draw();
  });
  Deck.seg('bSeg', v => {
    const base = +v, d = 128, th = [...Array(64)].map((_, i) => Math.pow(base, -2 * i / d));
    const score = dist => th.reduce((a, t) => a + Math.cos(dist * t), 0) / 64;
    const s = clear(document.getElementById('dSvg')), L0 = 60, R0 = 630, T0 = 14, B0 = 190, X = x => L0 + Math.log10(x) / 5 * (R0 - L0), Y = y => B0 - (y + 0.2) / 1.2 * (B0 - T0);
    [-0.2, 0, 0.5, 1].forEach(v => { svg('line', { x1: L0, x2: R0, y1: Y(v), y2: Y(v), class: 'ln' }, s); svg('text', { x: L0 - 8, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm', text: v }, s); });
    [1, 10, 100, 1000, 10000, 100000].forEach(v => svg('text', { x: X(v), y: B0 + 18, 'text-anchor': 'middle', class: 'tm', text: v >= 1000 ? (v / 1000) + 'K' : v }, s));
    let pts = ''; for (let e = 0; e <= 5; e += 0.01) { const x = Math.pow(10, e); pts += `${X(x)},${Y(score(x))} `; }
    svg('polyline', { points: pts, fill: 'none', style: 'stroke:var(--a);stroke-width:2.5' }, s);
    svg('text', { x: (L0 + R0) / 2, y: B0 + 40, 'text-anchor': 'middle', class: 'tm', text: 'distance m − n (log scale)' }, s);
    svg('text', { x: 14, y: (T0 + B0) / 2, 'text-anchor': 'middle', class: 'tm', transform: `rotate(-90 14 ${(T0 + B0) / 2})`, text: 'score (q = k = 1s)' }, s);
    const at = [100, 1000, 10000].map(x => score(x).toFixed(2));
    document.getElementById('dOut').innerHTML = `Normalized score at distance 100 / 1K / 10K: <b>${at.join(' / ')}</b>. A larger base keeps the score higher for longer, because every pair (except pair 0) turns more slowly.`;
  });
''',
    line='RoPE rotates each 2-D slice of q and k by position × frequency, so attention scores depend only on the distance between tokens.',
    explain='Attention is order-blind, so position has to be injected. The 2017 Transformer added a position vector at the input. RoPE instead splits each query and key into 2-D pairs and rotates pair i by the position times a frequency theta-i, which ranges from about one turn every six tokens down to one turn every fifty thousand. A dot product depends only on the angle between the two vectors, so the score depends only on m minus n: relative position for free, with no parameters, nothing added to the residual stream, and keys that are rotated once when cached. The slow pairs are why extending context needs care.',
    recap=[('Problem', 'attention is permutation-invariant; added position vectors are absolute and diluted.'), ('Core idea', 'rotate q and k pairs by m·θᵢ; q·k depends on m − n.'), ('Spectrum', 'θᵢ = base^(−2i/d); fast pairs for local order, slow pairs for long range; base 10K → 500K in Llama 3.')],
)

# =============================================================== 04
DECKS['04-swiglu'] = dict(
    title='SwiGLU', h1='SwiGLU feed-forward layers',
    sub='Why modern LLMs replaced the ReLU FFN with a gated unit that has three weight matrices, and how its odd hidden sizes (11,008, 14,336) are derived.',
    prob='The FFN holds most of a Transformer\'s parameters and FLOPs. The 2017 ReLU FFN is a plain two-layer MLP, and a better design at the same cost improves the whole model.',
    core='Use a <b>gated linear unit</b>: one projection, passed through Swish/SiLU, gates another projection element by element. FFN(x) = (SiLU(xW<sub>gate</sub>) ⊙ xW<sub>up</sub>)W<sub>down</sub>. Shrink the hidden size to ⅔·4d to keep the parameter count.',
    build=['03_swiglu'],
    sources='Shazeer 2020, "GLU Variants Improve Transformer" (eq. 5–6, Table 1); Dauphin et al. 2017 (GLU); Touvron et al. 2023 (LLaMA §2.2); Chowdhery et al. 2022 (PaLM §2); Meta llama3 model.py and llama-models sku_list (multiple_of, ffn_dim_multiplier).',
    slides=[
        section('s-p1', 1, 'Most of the model is FFN', '''    <p class="lede">Count the weights in one Llama 3 8B layer: attention (Wq, Wk, Wv, Wo with GQA) vs the FFN. The FFN is where most parameters and most per-token FLOPs live, so its design matters more than any other sub-layer's.</p>
    <div class="visual"><div id="pBars"></div></div>
    <p class="caption">Llama 3 8B: d = 4,096, 8 K/V heads of 128, FFN hidden 14,336. Attention = 2·d² + 2·d·1,024; FFN = 3·d·14,336.</p>'''),
        section('s-lim', 2, 'What a plain ReLU FFN leaves on the table', '''    <div class="grid3">
      <div class="card d"><h3>Hard zeros</h3><p>ReLU outputs exactly 0 for all negative inputs, so about half the hidden units are off for any token, and their gradient is zero too.</p></div>
      <div class="card b"><h3>No multiplicative interaction</h3><p>Each hidden unit is a single linear function passed through a fixed nonlinearity. Units can't modulate one another, so the layer can't directly compute "feature A, but only when feature B is present".</p></div>
      <div class="card c"><h3>Smoother activations help only a little</h3><p>GELU and Swish soften ReLU's kink. In Shazeer's ablation they barely move the result: 1.983 and 1.994 log-perplexity vs ReLU's 1.997 at 65K steps.</p></div>
    </div>'''),
        your_turn('s-turn', 'Same budget, three matrices',
                  'A ReLU FFN with d = 768 and hidden 3,072 has 2 matrices. A SwiGLU FFN has 3. What hidden size keeps the parameter count the same?',
                  ['3,072', '2,048', '1,536', '4,608'], 1,
                  '<b>B.</b> 2 · 768 · 3,072 = 3 · 768 · h, so h = ⅔ · 3,072 = 2,048. That is exactly what Shazeer used: "we reduce the hidden layer to d_ff = 2048, so as to maintain the same parameter and operation counts as the base model."'),
        section('s-core', 4, 'Gate × value', '''    <div class="grid3">
      <div class="card a"><h3>Gate path</h3><p><code>g = SiLU(x W_gate)</code>, where SiLU(z) = z·σ(z), also called Swish₁. A smooth "how much to let through" signal per hidden unit, slightly negative for negative inputs.</p></div>
      <div class="card b"><h3>Value path</h3><p><code>u = x W_up</code>: a plain linear projection with no nonlinearity. It carries what gets let through, and its sign can be either way.</p></div>
      <div class="card e"><h3>Combine and project</h3><p><code>FFN(x) = (g ⊙ u) W_down</code>. The element-wise product lets one projection modulate another. That multiplicative interaction is what a ReLU FFN lacks.</p></div>
    </div>
    <div class="eq">FFN<sub>SwiGLU</sub>(x) = (Swish₁(xW) ⊗ xV) W₂   (Shazeer 2020, eq. 6, biases omitted)</div>
''' + deep('The GLU family', '<p>GLU (Dauphin et al. 2017) uses a sigmoid gate: σ(xW) ⊗ xV. Shazeer tries several gates: <b>ReGLU</b> (ReLU), <b>GEGLU</b> (GELU), <b>SwiGLU</b> (Swish) and <b>Bilinear</b> (no nonlinearity at all). All gated versions beat the non-gated baselines in his Table 1; GEGLU and SwiGLU are best. PaLM and LLaMA chose SwiGLU. Llama\'s code calls the matrices <code>w1</code> (gate), <code>w3</code> (up) and <code>w2</code> (down).</p>')),
        section('s-how', 5, 'The activations, and what the gate does', '''    <p class="lede">Left: ReLU, GELU and SiLU as functions of one pre-activation z. Right: one SwiGLU hidden unit, the gate SiLU(a) times the value b, for a fixed value b. Drag b: the unit's output can be positive, negative or near zero depending on <b>both</b> projections.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0"><label class="ctl">Value projection b <input type="range" id="gB" min="-2" max="2" step="0.1" value="1"> <output id="gBo"></output></label></div>
      <svg id="aSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Activation functions and gated unit"></svg>
      <div class="legend"><span><i style="background:var(--faint)"></i>ReLU</span><span><i style="background:var(--c)"></i>GELU</span><span><i style="background:var(--a)"></i>SiLU / Swish₁</span><span><i style="background:var(--b)"></i>SiLU(a) × b</span></div>
    </div>'''),
        section('s-how2', 5, 'Where 11,008 and 14,336 come from', '''    <p class="lede">Real models start from ⅔·4d, optionally multiply, then round <b>up</b> to a hardware-friendly multiple. Pick a model to see each step. (This is Meta's code, reproduced and tested in notebook 03.)</p>
    <div class="visual">
      <div class="seg" id="hSeg"><button data-v="4096,256,0" class="on">LLaMA 7B</button><button data-v="5120,256,0">LLaMA 13B</button><button data-v="8192,256,0">LLaMA 65B</button><button data-v="4096,1024,1.3">Llama 3 8B</button></div>
      <div class="grid4" style="margin-top:14px">
        <div class="stat"><div class="num" id="h1"></div><div class="lbl">4d</div></div>
        <div class="stat"><div class="num" id="h2"></div><div class="lbl">int(⅔ · 4d)</div></div>
        <div class="stat"><div class="num" id="h3"></div><div class="lbl">× ffn_dim_multiplier</div></div>
        <div class="stat"><div class="num" id="h4" style="color:var(--e)"></div><div class="lbl">rounded up → hidden</div></div>
      </div>
      <div id="hBars" style="margin-top:12px"></div>
    </div>
    <p class="caption">Values from Meta's released configs: multiple_of 256 for LLaMA 1, and multiple_of 1024 with ffn_dim_multiplier 1.3 for Llama 3 8B.</p>'''),
        section('s-why', 6, 'Why it works: the evidence, and the honest answer', '''    <div class="visual">
      <div id="sBars"></div>
      <p class="caption">Shazeer 2020, Table 1: held-out log-perplexity on C4 for T5-base after 524,288 steps (lower is better). Every variant has the same parameters and operations.</p>
    </div>
    <div class="grid2" style="margin-top:12px">
      <div class="card e"><h3>Same cost, consistently better</h3><p>Gated variants win at both training lengths and also on downstream GLUE and SuperGLUE fine-tuning in the same paper. That consistency is why PaLM and LLaMA adopted SwiGLU.</p></div>
      <div class="card b"><h3>Why, exactly? Nobody fully knows</h3><p>The paper's conclusion: "We offer no explanation as to why these architectures seem to work; we attribute their success, as all else, to divine benevolence." The usual intuition is that multiplicative gating adds expressiveness, but this is empirical.</p></div>
    </div>'''),
        myths('s-myth', [
            ('SwiGLU makes the FFN bigger.', 'At the ⅔·4d hidden size it has the <b>same</b> parameters and FLOPs as the 4d ReLU FFN. Llama 3\'s 1.3 multiplier is a separate decision to spend more parameters there.'),
            ('Swish and SwiGLU are the same thing.', 'Swish (SiLU) is the activation function. SwiGLU is the whole <b>gated</b> unit: Swish of one projection times another projection, then a down projection. FFN<sub>Swish</sub> alone scored 1.994, about the same as ReLU.'),
            ('Gating was introduced to save compute.', 'It costs the same compute. It was introduced for <b>quality</b>: lower perplexity at equal parameters.'),
        ]),
        check('s-check', [
            ('mcq', 'How many weight matrices does a SwiGLU FFN have?', ['1', '2', '3', '4'], 2, '<b>3</b>: gate, up and down.'),
            ('open', 'Compute LLaMA-7B\'s FFN hidden size from d = 4,096 and multiple_of = 256.', '4d = 16,384 → int(⅔ · 16,384) = 10,922 → round up to a multiple of 256 → <b>11,008</b>.'),
            ('open', 'Write the SwiGLU FFN and say which part is the gate.', '(SiLU(xW_gate) ⊙ xW_up)W_down. SiLU(xW_gate) is the gate; xW_up is the value it scales.'),
        ]),
    ],
    js=r'''
  (() => {
    const d = 4096, attn = 2 * d * d + 2 * d * 1024, ffn = 3 * d * 14336;
    Deck.hbars(document.getElementById('pBars'), [
      { label: 'attention (GQA)', value: attn, color: 'var(--c)', text: (attn / 1e6).toFixed(1) + 'M (' + (100 * attn / (attn + ffn)).toFixed(0) + '%)' },
      { label: 'FFN (SwiGLU)', value: ffn, color: 'var(--a)', text: (ffn / 1e6).toFixed(1) + 'M (' + (100 * ffn / (attn + ffn)).toFixed(0) + '%)' }], { max: ffn * 1.05 });
  })();
  const silu = z => z / (1 + Math.exp(-z)), gelu = z => 0.5 * z * (1 + Math.tanh(Math.sqrt(2 / Math.PI) * (z + 0.044715 * z ** 3)));
  Deck.bind(['gB'], () => {
    const b = Deck.val('gB'); Deck.out('gBo', b.toFixed(1));
    const s = clear(document.getElementById('aSvg'));
    const panel = (x0, title, fns, ymin, ymax) => {
      const W = 290, X = z => x0 + (z + 4) / 8 * W, Y = y => 190 - (y - ymin) / (ymax - ymin) * 160;
      svg('text', { x: x0 + W / 2, y: 18, 'text-anchor': 'middle', class: 't', style: 'font-weight:600', text: title }, s);
      svg('line', { x1: x0, x2: x0 + W, y1: Y(0), y2: Y(0), class: 'ln' }, s); svg('line', { x1: X(0), x2: X(0), y1: 30, y2: 190, class: 'ln' }, s);
      fns.forEach(([f, c]) => { let p = ''; for (let z = -4; z <= 4.001; z += 0.05) p += `${X(z)},${Y(Math.max(ymin, Math.min(ymax, f(z))))} `; svg('polyline', { points: p, fill: 'none', style: `stroke:${c};stroke-width:2.5` }, s); });
      svg('text', { x: x0 + W / 2, y: 214, 'text-anchor': 'middle', class: 'tm', text: 'pre-activation (z or a)' }, s);
    };
    panel(20, 'activation functions', [[z => Math.max(0, z), 'var(--faint)'], [gelu, 'var(--c)'], [silu, 'var(--a)']], -1, 4);
    panel(350, `gated unit: SiLU(a) × ${b.toFixed(1)}`, [[z => silu(z), 'var(--a)'], [z => silu(z) * b, 'var(--b)']], -4, 4);
  });
  Deck.seg('hSeg', v => {
    const [d, mo, mult] = v.split(',').map(Number), h1 = 4 * d, h2 = Math.floor(2 * h1 / 3), h3 = mult ? Math.floor(mult * h2) : h2, h4 = mo * Math.ceil(h3 / mo);
    Deck.out('h1', h1.toLocaleString()); Deck.out('h2', h2.toLocaleString()); Deck.out('h3', mult ? h3.toLocaleString() : '(none)'); Deck.out('h4', h4.toLocaleString());
    Deck.hbars(document.getElementById('hBars'), [
      { label: 'ReLU FFN params (2·d·4d)', value: 2 * d * h1, color: 'var(--faint)', text: (2 * d * h1 / 1e6).toFixed(0) + 'M' },
      { label: 'SwiGLU params (3·d·hidden)', value: 3 * d * h4, color: 'var(--a)', text: (3 * d * h4 / 1e6).toFixed(0) + 'M' }], { max: 3 * 4096 * 14336 * 1.05 * (d / 4096) ** 2 });
  });
  Deck.hbars(document.getElementById('sBars'), [['ReLU (baseline)', 1.677], ['GELU', 1.679], ['Swish', 1.683], ['GLU (sigmoid)', 1.663], ['Bilinear', 1.648], ['ReGLU', 1.645], ['SwiGLU', 1.636], ['GEGLU', 1.633]].map(([n, v]) => ({ label: n, value: v - 1.6, color: /GLU|Bilinear/.test(n) ? 'var(--a)' : 'var(--faint)', text: v.toFixed(3) })), { max: 0.09 });
''',
    line='SwiGLU gates one projection with SiLU of another: three matrices at ⅔ the width, same cost as the ReLU FFN, consistently lower perplexity.',
    explain='The FFN is most of a Transformer\'s parameters. The 2017 version is a ReLU MLP with hidden size 4d. SwiGLU computes SiLU of x times W-gate, multiplies that element-wise by x times W-up, and projects back down with W-down. The gate lets one projection modulate the other. Three matrices instead of two means the hidden size drops to two-thirds of 4d to keep parameters equal, which real models round up to hardware-friendly multiples, giving 11,008 for LLaMA-7B and 14,336 for Llama 3 8B. Shazeer\'s ablation shows lower perplexity at the same cost, and PaLM and LLaMA adopted it, although nobody has a full explanation of why it works.',
    recap=[('Problem', 'the FFN dominates parameters; the ReLU MLP is not the best use of them.'), ('Core idea', '(SiLU(xW_gate) ⊙ xW_up)W_down; hidden ≈ ⅔·4d keeps cost equal.'), ('Evidence', 'Shazeer Table 1: 1.677 → 1.636 log-ppl at the same parameters and operations.')],
)

# =============================================================== 05
DECKS['05-attention-variants'] = dict(
    title='MQA, GQA and MLA', h1='MQA, GQA and MLA: fewer keys and values',
    sub='The modelling side of shrinking the KV cache: sharing key/value heads (MQA, GQA), compressing them into a latent (MLA), and why MLA needs "decoupled" RoPE.',
    prob='During generation every layer stores keys and values for every past token and head. That cache, not compute, limits batch size and context length.',
    core='<b>Share</b> K/V heads across groups of query heads (MQA: 1 group, GQA: g groups), or <b>compress</b> all heads\' K/V into one small latent per token and re-expand on the fly (MLA).',
    build=['04_mla_absorption'],
    sources='Shazeer 2019, "Fast Transformer Decoding: One Write-Head is All You Need"; Ainslie et al. 2023, "GQA" (EMNLP; mean-pooling, 5% uptraining); Chowdhery et al. 2022 (PaLM §2, MQA); Touvron et al. 2023 (Llama 2 Table 1); DeepSeek-AI 2024, DeepSeek-V2 (§2.1, Table 1); Llama 3 §3.2.',
    slides=[
        section('s-p1', 1, 'The cache scales with K/V heads', '''    <p class="lede">The KV cache stores 2 × layers × <b>K/V heads</b> × head_dim numbers per token. With standard multi-head attention (MHA), every query head has its own K and V. This deck is the architecture view; memory sizes in GB and serving effects are in <a href="../../inference/02-kv-cache/index.html">Inference deck 02</a>.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0"><label class="ctl">K/V heads (32 query heads) <input type="range" id="kH" min="0" max="5" step="1" value="5"> <output id="kHo"></output></label></div>
      <svg id="kSvg" viewBox="0 0 660 170" style="margin-top:10px" role="img" aria-label="Query heads sharing KV heads"></svg>
      <p class="readout" id="kOut"></p>
    </div>'''),
        section('s-lim', 2, 'Why not just use one K/V head?', '''    <div class="grid3">
      <div class="card d"><h3>MQA can lose quality</h3><p>Multi-query attention (Shazeer 2019) shares <b>one</b> K/V head across all query heads. Ainslie et al.: MQA "can lead to quality degradation and training instability".</p></div>
      <div class="card b"><h3>Training a second model is expensive</h3><p>Pretraining a separate MQA model just for faster inference is costly. Ideally you could convert an existing MHA checkpoint.</p></div>
      <div class="card c"><h3>Tensor parallelism wants ≥ 1 K/V head per GPU</h3><p>With one K/V head and 8-way tensor parallelism, that head is replicated on every GPU, which wastes the saving. A few groups split cleanly across GPUs.</p></div>
    </div>'''),
        your_turn('s-turn', 'Count the groups',
                  'Llama 3 70B has 64 query heads and 8 key/value heads. How many query heads share each K/V head, and how much smaller is the KV cache than MHA?',
                  ['8 each; 8× smaller', '64 each; 64× smaller', '8 each; 64× smaller', 'They don\'t share; same size'], 0,
                  '<b>A.</b> 64 / 8 = 8 query heads per K/V head. The cache scales with the number of K/V heads, so it is 64 / 8 = <b>8×</b> smaller than MHA with 64 K/V heads.'),
        section('s-core', 4, 'Share or compress', '''    <div class="grid3">
      <div class="card b"><h3>MQA (2019)</h3><p>All query heads share <b>one</b> K and one V. Smallest cache (2·d_h per layer per token); PaLM used it. Risk: quality loss.</p></div>
      <div class="card a"><h3>GQA (2023)</h3><p>Query heads split into <b>g groups</b>; each group shares one K/V head. g = 1 is MQA; g = heads is MHA. "Quality close to multi-head attention with comparable speed to multi-query." Llama 2 (34B, 70B), Mistral, Llama 3.</p></div>
      <div class="card e"><h3>MLA (2024)</h3><p>Cache one <b>latent vector</b> c (d_c = 512 in DeepSeek-V2) per token and layer, and up-project to every head's K and V when needed. A small extra slice carries RoPE.</p></div>
    </div>
''' + deep('Converting MHA into GQA', '<p>Ainslie et al. convert a trained multi-head checkpoint: the key and value projection matrices within each group are <b>mean-pooled</b> into one head (mean pooling worked better than picking one head or random init), then the model is <b>uptrained</b> for about <b>5%</b> of its original pretraining compute. Uptrained GQA reached quality close to MHA with speed close to MQA.</p>')),
        section('s-how', 5, 'MLA step by step', '''    <p class="lede">Step through what DeepSeek-V2 computes for one token, and what goes into the cache.</p>
    <div class="visual">
      <div class="seg" id="mSeg"><button data-v="0" class="on">1 · compress</button><button data-v="1">2 · expand (naive)</button><button data-v="2">3 · absorb</button><button data-v="3">4 · RoPE problem</button><button data-v="4">5 · decoupled RoPE</button></div>
      <svg id="mSvg" viewBox="0 0 660 200" style="margin-top:10px" role="img" aria-label="MLA data flow"></svg>
      <div class="infobox" id="mInfo" style="background:var(--panel-2);border-radius:10px;padding:12px 14px;margin-top:10px;font-size:14px;color:var(--muted)"></div>
    </div>'''),
        section('s-how2', 5, 'Cache per token, per layer: the numbers', '''    <p class="lede">DeepSeek-V2's comparison (Table 1) in numbers of elements per token per layer, with its dimensions: n_h = 128 heads, d_h = 128, d_c = 512, RoPE slice d_h<sup>R</sup> = 64.</p>
    <div class="visual"><div id="cBars"></div></div>
''' + deep('Reading the table', '<p>MHA: 2·n_h·d_h. GQA: 2·n_g·d_h. MQA: 2·d_h. MLA: d_c + d_h<sup>R</sup> ≈ (9/2)·d_h, "equal to GQA with only 2.25 groups", while the paper reports <b>stronger</b> performance than MHA. Against DeepSeek 67B, DeepSeek-V2 reports a <b>93.3%</b> smaller KV cache and <b>5.76×</b> higher maximum generation throughput (that comparison also includes other changes, such as MoE and FP8 KV).</p>')),
        section('s-why', 6, 'Why sharing works, and what each option costs', '''    <div class="visual scroll-x"><table class="tbl">
      <tr><th></th><th>MHA</th><th>GQA</th><th>MQA</th><th>MLA</th></tr>
      <tr><td>KV cache / token / layer</td><td>2·n_h·d_h</td><td>2·g·d_h</td><td>2·d_h</td><td>d_c + d_R</td></tr>
      <tr><td>Quality</td><td>baseline</td><td>close to MHA</td><td>can degrade</td><td>reported ≥ MHA</td></tr>
      <tr><td>Extra compute</td><td>none</td><td>none</td><td>none</td><td>up-projections, absorbed into Q and O at inference</td></tr>
      <tr><td>Works with plain RoPE</td><td>yes</td><td>yes</td><td>yes</td><td>no: needs decoupled RoPE</td></tr>
      <tr><td>Used by</td><td>GPT-3, LLaMA 1</td><td>Llama 2 70B, Mistral, Llama 3</td><td>PaLM</td><td>DeepSeek-V2, V3</td></tr>
    </table></div>
''' + deep('Why sharing barely hurts', '<p>Decoding is memory-bound: each step reads the whole KV cache to produce one token per sequence. Query heads still differ, and each one attends to the shared keys in its own way, so the model keeps most of its capacity to look for different things. What it loses is the ability to <b>store</b> different keys per head. GQA\'s groups and MLA\'s per-head up-projections recover much of that.</p>')),
        myths('s-myth', [
            ('MQA means attention with a single head.', 'There are still many <b>query</b> heads, each attending differently. Only the keys and values are shared.'),
            ('GQA mainly saves FLOPs.', 'The FLOPs for attention scores barely change, because every query head still computes its scores. GQA saves <b>KV-cache memory and memory bandwidth</b>, which is what limits decoding.'),
            ('MLA is just low-rank GQA, and RoPE works the same.', 'MLA\'s trick depends on absorbing W_UK into W_Q, and RoPE\'s position-dependent rotation sits between them and breaks that. DeepSeek-V2 needs a separate decoupled RoPE slice with a key shared across heads.'),
        ]),
        check('s-check', [
            ('mcq', 'GQA with g = 1 is…', ['MHA', 'MQA', 'MLA', 'Sliding-window attention'], 1, '<b>MQA</b>: one group, so one K/V head shared by every query head.'),
            ('open', 'How do you turn a trained MHA model into a GQA model cheaply?', 'Mean-pool the K and V projection matrices of the heads in each group into one head, then uptrain for about 5% of the original pretraining compute (Ainslie et al., 2023).'),
            ('open', 'Why can\'t MLA simply apply RoPE to its reconstructed keys?', 'Inference relies on precomputing W_Q·W_UKᵀ so keys never get decompressed. RoPE inserts a rotation that depends on both positions between those matrices, so no single precomputed matrix works. DeepSeek-V2 carries position in a separate small RoPE query/key slice instead.'),
        ]),
    ],
    js=r'''
  const KV = [1, 2, 4, 8, 16, 32];
  Deck.bind(['kH'], () => {
    const g = KV[Deck.val('kH')], s = clear(document.getElementById('kSvg')), name = g === 1 ? 'MQA' : g === 32 ? 'MHA' : 'GQA';
    Deck.out('kHo', `${g} (${name})`);
    for (let i = 0; i < 32; i++) {
      const x = 14 + i * 20, grp = Math.floor(i / (32 / g)), gx = 14 + (grp + 0.5) * (640 / g) - 8;
      svg('line', { x1: x + 8, y1: 40, x2: gx + 8, y2: 118, style: `stroke:hsl(${grp * 360 / g},55%,55%);stroke-width:1.2;opacity:.7` }, s);
      svg('rect', { x, y: 20, width: 16, height: 20, rx: 3, style: `fill:hsl(${grp * 360 / g},55%,55%)` }, s);
    }
    for (let j = 0; j < g; j++) { const gx = 14 + (j + 0.5) * (640 / g) - 8; svg('rect', { x: gx, y: 118, width: 16, height: 26, rx: 3, style: `fill:hsl(${j * 360 / g},55%,40%)` }, s); }
    svg('text', { x: 4, y: 14, class: 'tm', style: 'font-size:11px', text: '32 query heads' }, s); svg('text', { x: 4, y: 162, class: 'tm', style: 'font-size:11px', text: `${g} K/V head${g > 1 ? 's' : ''} (cached)` }, s);
    const bytes = 2 * 32 * g * 128 * 2;
    document.getElementById('kOut').innerHTML = `${32 / g} query heads per K/V head. KV cache per token (32 layers, head_dim 128, BF16): <b>${Deck.bytes(bytes)}</b>, which is <b>${32 / g}×</b> smaller than MHA. Llama 3 8B uses 8.`;
  });
  const STEPS = [
    ['<b>Compress.</b> c = x·W<sup>DKV</sup>: one d_c-wide latent (512 in DeepSeek-V2) per token per layer. <b>This is what gets cached</b>, instead of 128 heads × (K + V).', ['x', 'c (cached)']],
    ['<b>Expand, naively.</b> Each head\'s key is k_h = c·W<sup>UK</sup>_h and value v_h = c·W<sup>UV</sup>_h. Doing this for every cached token at every step would cost a lot of compute and give back the memory you saved.', ['c (cached)', 'k_h, v_h for all heads']],
    ['<b>Absorb.</b> q_h·k_hᵀ = x·(W<sup>Q</sup>_h W<sup>UK</sup>_hᵀ)·cᵀ. Precompute the product once and the query goes straight into latent space; keys are never materialized. W<sup>UV</sup> is absorbed into the output projection the same way. Notebook 04 checks this is exact.', ['x → latent query', 'score against c directly']],
    ['<b>The RoPE problem.</b> With RoPE the key is R_t·(c_t W<sup>UK</sup>_h), where the rotation R_t depends on the key\'s position. The middle matrix becomes W<sup>Q</sup>_h R_mᵀ R_t W<sup>UK</sup>_hᵀ, which differs for every pair of positions, so it can\'t be precomputed. DeepSeek-V2: "RoPE is incompatible with low-rank KV compression."', ['absorbed matrix', 'depends on m and t ✗']],
    ['<b>Decoupled RoPE.</b> Keep the latent path position-free, and add a small extra slice (d_h<sup>R</sup> = 64) per head for queries plus <b>one RoPE key shared by all heads</b>, cached next to c. Score = content part + RoPE part. Cache per token: d_c + d_h<sup>R</sup> = 576 numbers per layer.', ['c (512) + k^R (64)', 'cached: 576 per layer']],
  ];
  Deck.seg('mSeg', v => {
    const [txt, labels] = STEPS[+v], s = clear(document.getElementById('mSvg'));
    const box = (x, w, label, cls) => { svg('rect', { x, y: 70, width: w, height: 56, rx: 9, class: cls }, s); svg('text', { x: x + w / 2, y: 103, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:600', text: label }, s); };
    box(30, 220, labels[0], 'f-a'); box(410, 220, labels[1], +v === 3 ? 'f-d' : 'f-e');
    svg('line', { x1: 255, x2: 400, y1: 98, y2: 98, style: 'stroke:var(--muted);stroke-width:2.5' }, s);
    svg('path', { d: 'M392 90 L404 98 L392 106', fill: 'none', style: 'stroke:var(--muted);stroke-width:2.5' }, s);
    svg('text', { x: 330, y: 160, 'text-anchor': 'middle', class: 'tm', text: ['W^DKV: d → d_c', 'W^UK, W^UV per head', 'W^Q·W^UKᵀ precomputed', 'R_m, R_t in the middle', 'separate RoPE slice'][+v] }, s);
    document.getElementById('mInfo').innerHTML = txt;
  });
  (() => {
    const rows = [['MHA', 2 * 128 * 128], ['GQA, 8 groups', 2 * 8 * 128], ['MLA (d_c + d_R)', 576], ['MQA', 2 * 128]];
    Deck.hbars(document.getElementById('cBars'), rows.map(([n, v]) => ({ label: n, value: v, color: n.startsWith('MLA') ? 'var(--e)' : n === 'MHA' ? 'var(--d)' : 'var(--a)', text: v.toLocaleString() + ` (${(100 * v / 32768).toFixed(1)}%)` })), { log: true, min: 100 });
  })();
''',
    line='The KV cache scales with K/V heads: share them (MQA, GQA) or compress them into a latent (MLA). MLA needs decoupled RoPE to keep its absorption trick.',
    explain='During decoding, memory, not compute, is the limit, and the KV cache scales with the number of key/value heads. MQA shares one K/V head across all query heads; it is smallest but can lose quality. GQA uses a few groups, gets quality close to MHA at near-MQA speed, and an existing model can be converted by mean-pooling heads and uptraining for about 5% of the original compute. MLA, from DeepSeek-V2, caches one small latent per token and re-expands it per head; at inference the up-projection is absorbed into the query projection so keys are never materialized. RoPE would break that absorption, so MLA adds a small decoupled RoPE slice.',
    recap=[('Problem', 'KV cache per token = 2 × layers × K/V heads × head_dim.'), ('Share', 'MQA (1 group) and GQA (g groups): cache shrinks by heads/g; convert by mean-pool + 5% uptraining.'), ('Compress', 'MLA caches d_c + d_R ≈ 4.5·d_h; absorption + decoupled RoPE.')],
)

# =============================================================== 06
DECKS['06-decoder-only'] = dict(
    title='Decoder-only, and Why It Won', h1='Decoder-only, and why it won',
    sub='Encoder-decoder, encoder-only and decoder-only stacks differ mainly in their attention masks. Why the plain causal decoder became the default for LLMs.',
    prob='The 2017 Transformer has an encoder and a decoder with cross-attention. BERT kept only the encoder. GPT kept only the decoder. For one general-purpose model, which shape is best?',
    core='A <b>causal decoder</b>: one stack, one mask (each token sees only the past), trained to predict the next token at <b>every</b> position. Prompts, documents and answers all live in one sequence.',
    build=['05_attention_masks'],
    sources='Vaswani et al. 2017; Devlin et al. 2019 (BERT, 15% masking); Raffel et al. 2020 (T5); Radford et al. 2019 (GPT-2); Wang et al. 2022, "What Language Model Architecture and Pretraining Objective Work Best for Zero-Shot Generalization?"; Llama Team 2024 (Llama 3 §3.2, document mask).',
    slides=[
        section('s-p1', 1, 'Three families, one difference: the mask', '''    <p class="lede">Every family computes the same attention. What differs is which positions may see which. Each grid shows "row may attend to column" for 8 tokens. In the encoder-decoder, tokens 0–3 are the input and 4–7 the output.</p>
    <div class="visual">
      <div class="seg" id="fSeg"><button data-v="causal" class="on">Causal decoder (GPT, Llama)</button><button data-v="prefix">Prefix-LM (non-causal decoder)</button><button data-v="encdec">Encoder-decoder (T5, 2017)</button><button data-v="enc">Encoder-only (BERT)</button></div>
      <svg id="fSvg" viewBox="0 0 660 250" style="margin-top:10px" role="img" aria-label="Attention mask"></svg>
      <p class="readout" id="fOut"></p>
    </div>'''),
        section('s-lim', 2, 'What the other shapes cost', '''    <div class="grid3">
      <div class="card d"><h3>Encoder-only can't generate</h3><p>BERT sees both directions and is trained to fill in masked tokens (15% of them). Great for classification and retrieval, but there's no natural way to write a long answer token by token.</p></div>
      <div class="card b"><h3>Encoder-decoder needs a split</h3><p>Every example must be cut into "input" and "target", and the two stacks are joined by cross-attention. Chat turns, documents and code don't come with a natural split.</p></div>
      <div class="card c"><h3>Fewer training signals per token</h3><p>Masked-LM objectives compute loss only on the corrupted positions. A causal LM computes loss on <b>every</b> position of every sequence, so each forward pass yields T training targets.</p></div>
    </div>'''),
        your_turn('s-turn', 'Which one serves chat most simply?',
                  'A multi-turn chat keeps growing. Which architecture can reuse all previous computation (the KV cache) as each new message arrives?',
                  ['Encoder-only', 'Encoder-decoder', 'Causal decoder', 'All of them equally'], 2,
                  '<b>C.</b> In a causal decoder a token\'s keys and values depend only on earlier tokens, so they never change when new tokens arrive. Cache once, append forever. An encoder\'s bidirectional states change whenever the input grows, so they would have to be recomputed.'),
        section('s-core', 4, 'The causal decoder recipe', '''    <div class="grid3">
      <div class="card a"><h3>One stack</h3><p>Embedding → N identical blocks (attention + FFN) → output head. No encoder and no cross-attention. Fewer moving parts to tune and to parallelize.</p></div>
      <div class="card e"><h3>One objective</h3><p>Predict token t+1 from tokens ≤ t, at every position, on any text. No labels, no input/target split, so all of the web is training data.</p></div>
      <div class="card b"><h3>One sequence for everything</h3><p>Instructions, documents, few-shot examples, tool calls and answers are all just tokens in context. GPT-2 and GPT-3 showed tasks can be specified in the prompt.</p></div>
    </div>
''' + deep('Packing and the document mask', '<p>Pretraining packs many documents back to back into one long sequence, so no compute is wasted on padding. With a plain causal mask, a token can attend into the <b>previous, unrelated</b> document. Llama 3: "we use an attention mask that prevents self-attention between different documents within the same sequence". It had limited impact in standard pretraining but mattered for continued pretraining on very long sequences. Notebook 05 shows a packed batch with this mask gives exactly the same outputs as running each document alone.</p>')),
        section('s-how', 5, 'Training signal per sequence', '''    <p class="lede">How many positions produce a loss in one forward pass of length T? Compare a causal LM, BERT-style masked LM (15% of tokens) and an encoder-decoder trained on a 50/50 input/target split.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0"><label class="ctl">Sequence length T <input type="range" id="tT" min="128" max="8192" step="128" value="2048"> <output id="tTo"></output></label></div>
      <div id="tBars" style="margin-top:12px"></div>
    </div>
    <p class="caption">Illustrative counts. Real objectives vary: T5's span corruption predicts about 15% of tokens; prefix-LM computes loss only on the target part.</p>'''),
        section('s-how2', 5, 'Same model, three uses', '''    <div class="grid3">
      <div class="card a"><h3>Pretraining</h3><p>Full causal mask (plus the document mask when packing) over long sequences. Loss on every token.</p></div>
      <div class="card b"><h3>Fine-tuning (SFT)</h3><p>Same causal mask. Prompt and response in one sequence, with the loss usually counted only on response tokens. No architecture change.</p></div>
      <div class="card e"><h3>Serving</h3><p>Prefill the prompt with one causal pass (cache K/V), then decode one token at a time, appending to the cache. Exactly the training computation, done incrementally.</p></div>
    </div>
''' + deep('What about bidirectional context?', '<p>A prefix-LM lets prompt tokens see each other in both directions and keeps the generated part causal. Wang et al. found this <b>non-causal decoder with masked-LM pretraining</b> did best after <b>multitask fine-tuning</b>, while the causal decoder did best for zero-shot use after self-supervised pretraining alone. They also showed models can be adapted between the two. The industry chose the simplest shape that scales and serves well, plus instruction tuning.</p>')),
        section('s-why', 6, 'Why the causal decoder won', '''    <div class="grid2">
      <div class="card a"><h3>Best zero-shot after pretraining alone</h3><p>Wang et al. (2022): causal decoder-only models trained autoregressively "exhibit the strongest zero-shot generalization after purely unsupervised pretraining".</p></div>
      <div class="card e"><h3>Every token is a target</h3><p>Dense supervision from raw text, with no input/target split, makes it the simplest objective to scale on trillions of tokens.</p></div>
      <div class="card b"><h3>Serving is incremental</h3><p>Past K/V never change, so the KV cache, prefix caching, continuous batching and speculative decoding all fit naturally (Inference decks 02–06).</p></div>
      <div class="card c"><h3>One interface for every task</h3><p>Prompting turns any task into "continue this text", so one model and one serving stack cover translation, coding, chat and tool use.</p></div>
    </div>'''),
        myths('s-myth', [
            ('Decoder-only models can\'t "understand" the input because they only look left.', 'Every prompt token sees all earlier prompt tokens, and the <b>last</b> position sees the whole prompt. Bidirectionality inside the prompt (prefix-LM) can help some setups, but it is not required to model the input well.'),
            ('Encoder-decoder models are obsolete.', 'Wang et al. found non-causal objectives can win after multitask fine-tuning, and encoder-style models remain standard for embeddings and retrieval. Decoder-only is the default for <b>general-purpose generative</b> LLMs.'),
            ('A decoder-only Transformer is just the 2017 decoder.', 'It drops the 2017 decoder\'s cross-attention sub-layer entirely. Each block is just masked self-attention plus FFN.'),
        ]),
        check('s-check', [
            ('mcq', 'In a causal mask, query position i may attend to key position j when…', ['j ≥ i', 'j ≤ i', 'j = i', 'always'], 1, '<b>j ≤ i</b>: itself and the past.'),
            ('open', 'Why do packed pretraining sequences need a document mask?', 'Without it, tokens attend into earlier, unrelated documents in the same packed sequence. The document mask restricts attention to the same document, making a packed batch equivalent to running each document separately.'),
            ('open', 'Give two reasons the causal decoder is convenient at serving time.', 'Past keys and values never change, so they can be cached and reused (KV cache, prefix caching). And the serving computation is exactly the training computation done incrementally, with no separate encoder pass.'),
        ]),
    ],
    js=r'''
  const MASKS = {
    causal: [(i, j) => j <= i, 'Causal: row i sees columns 0…i. Every position predicts the next token, so there are 8 training targets here.'],
    prefix: [(i, j) => (i < 4 && j < 4) || j <= i, 'Prefix-LM: the first 4 tokens (the prompt) see each other in both directions; the rest are causal. Loss is usually only on the last 4.'],
    encdec: [(i, j) => (i < 4 && j < 4) ? 2 : (i >= 4 && j >= 4 && j <= i) ? 1 : (i >= 4 && j < 4) ? 3 : 0, 'Encoder (top-left) is bidirectional over the input. Decoder (bottom-right) is causal over the output. Cross-attention (bottom-left) lets output tokens see the whole input. Two stacks.'],
    enc: [(i, j) => true, 'Encoder-only: everything sees everything. Trained by masking about 15% of tokens and predicting them. It cannot generate left to right.'],
  };
  Deck.seg('fSeg', v => {
    const [f, txt] = MASKS[v], s = clear(document.getElementById('fSvg')), c = 26, x0 = 220, y0 = 20;
    for (let i = 0; i < 8; i++) for (let j = 0; j < 8; j++) {
      const m = f(i, j), col = m === 3 ? 'var(--c)' : m === 2 ? 'var(--b)' : m ? 'var(--a)' : 'var(--panel-2)';
      svg('rect', { x: x0 + j * c, y: y0 + i * c, width: c - 3, height: c - 3, rx: 4, style: `fill:${col}` }, s);
    }
    for (let i = 0; i < 8; i++) { svg('text', { x: x0 - 10, y: y0 + i * c + 17, 'text-anchor': 'end', class: 'tm', text: 'q' + i }, s); svg('text', { x: x0 + i * c + 11, y: y0 + 8 * c + 14, 'text-anchor': 'middle', class: 'tm', text: 'k' + i }, s); }
    document.getElementById('fOut').innerHTML = txt;
  });
  Deck.bind(['tT'], () => {
    const T = Deck.val('tT'); Deck.out('tTo', T.toLocaleString());
    Deck.hbars(document.getElementById('tBars'), [
      { label: 'causal LM: every position', value: T, color: 'var(--a)', text: T.toLocaleString() },
      { label: 'encoder-decoder, 50/50 split', value: T / 2, color: 'var(--b)', text: (T / 2).toLocaleString() },
      { label: 'masked LM (15%)', value: Math.round(0.15 * T), color: 'var(--c)', text: Math.round(0.15 * T).toLocaleString() }], { max: 8192 });
  });
''',
    line='A causal decoder is one stack, one mask and one objective: predict the next token at every position. Simple to train at scale, and incremental to serve.',
    explain='Encoder-only, encoder-decoder and decoder-only Transformers mostly differ in their attention mask. The causal decoder lets each token see only the past and trains it to predict the next token at every position, so every token of raw text is a training target and there is no input/target split. At serving time past keys and values never change, so they can be cached, and prompts let one model do any task. Wang et al. found causal decoders give the best zero-shot generalization after plain pretraining, while non-causal variants can win after multitask fine-tuning. When documents are packed together, a document mask stops attention leaking between them.',
    recap=[('Problem', 'three stack shapes; which one for a general LLM?'), ('Core idea', 'causal decoder: one stack, next-token loss on every position, past K/V never change.'), ('Detail', 'packing + document mask; prefix-LM is the in-between option.')],
)
