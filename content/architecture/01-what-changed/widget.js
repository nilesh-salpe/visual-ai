(() => {
  const { svg, clear, fmt } = Deck;

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

})();
