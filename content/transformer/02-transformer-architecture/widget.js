(() => {
  const { svg, clear } = Deck;

  /* distance vs operations */
  Deck.bind(['dD'], () => {
    const D = Deck.val('dD'); Deck.out('dDo', D);
    const k = 3;
    Deck.hbars(document.getElementById('dBars'), [
      { label: 'RNN (recurrent)', value: D, color: 'var(--d)', text: D + ' ops' },
      { label: 'ConvS2S (linear in distance)', value: Math.ceil(D / (k - 1)), color: 'var(--b)', text: Math.ceil(D / (k - 1)) + ' ops' },
      { label: 'ByteNet (logarithmic)', value: Math.max(1, Math.ceil(Math.log(D + 1) / Math.log(k))), color: 'var(--c)', text: Math.max(1, Math.ceil(Math.log(D + 1) / Math.log(k))) + ' ops' },
      { label: 'Transformer (constant)', value: 1, color: 'var(--e)', text: '1 op' },
    ], { max: 200 });
  });

  /* Figure 1 */
  const INFO = {
    inEmb: ['Input Embedding', 'Learned lookup table: each source token → a 512-dim vector, multiplied by √d<sub>model</sub>. Its weights are shared with the output embedding and the final linear layer (§3.4). Shape: n × 512.', null],
    outEmb: ['Output Embedding', 'Same shared embedding matrix applied to the target tokens. During training the target is <b>shifted right</b>, so position i only receives tokens before i.', '09-masked-self-attention'],
    pe: ['Positional Encoding (⊕)', 'Fixed sinusoids added to the embeddings so the model knows token order: PE(pos,2i) = sin(pos/10000<sup>2i/d<sub>model</sub></sup>). Dropout is applied to this sum.', '07-positional-encoding'],
    encMHA: ['Multi-Head Attention (encoder self-attention)', 'Q, K and V all come from the previous encoder layer. Every source token attends to every source token, using h = 8 heads of d<sub>k</sub> = 64.', '03-self-attention'],
    decMMHA: ['Masked Multi-Head Attention', 'Decoder self-attention. Positions to the right are masked by setting their scores to −∞ before the softmax, so no position can see the future.', '09-masked-self-attention'],
    decMHA: ['Multi-Head Attention (encoder-decoder)', 'Queries come from the decoder; <b>keys and values come from the encoder output</b>. This is how each target position looks at the source sentence.', '08-encoder-decoder-attention'],
    ffn: ['Feed Forward', 'Position-wise FFN: max(0, xW₁+b₁)W₂+b₂, 512 → 2048 → 512, applied to each position separately with the same weights. Each layer has its own parameters.', '11-position-wise-ffn'],
    an: ['Add & Norm', 'Residual connection followed by layer normalization: <code>LayerNorm(x + Sublayer(x))</code>. Dropout (0.1) is applied to the sub-layer output before the addition.', '10-residual-layernorm'],
    enc: ['Encoder stack (×N, N = 6)', 'Six identical layers, each with 2 sub-layers. Its final output (n × 512) is the memory that every decoder layer attends to.', '02-transformer-architecture'],
    dec: ['Decoder stack (×N, N = 6)', 'Six identical layers, each with 3 sub-layers: masked self-attention, encoder-decoder attention, and FFN.', '02-transformer-architecture'],
    lin: ['Linear', 'Projects each 512-dim decoder output to vocabulary logits. Its weight matrix is shared (tied) with the embedding layers (§3.4).', null],
    soft: ['Softmax', 'Turns logits into next-token probabilities. Training uses label smoothing ε<sub>ls</sub> = 0.1; generation uses beam search.', '12-parallel-training-vs-generation'],
  };
  const fig = document.getElementById('figSvg');
  TX.arrowDefs(fig, 'fa', 'var(--muted)');
  const B = (k, x, y, w, h, fill, label) => { const g = TX.box(fig, x, y, w, h, fill, label, { attrs: { 'data-k': k }, fs: 12 }); return g; };
  const A = (x1, y1, x2, y2) => TX.arrow(fig, x1, y1, x2, y2, 'fa', 'var(--muted)', 1.6);
  const R = pts => svg('polyline', { points: pts.map(p => p.join(',')).join(' '), fill: 'none', style: 'stroke:var(--faint);stroke-width:1.6;stroke-dasharray:5 4', 'marker-end': 'url(#fa)' }, fig);
  // frames
  svg('rect', { x: 40, y: 215, width: 240, height: 235, rx: 14, 'data-k': 'enc', style: 'fill:var(--a-soft);stroke:var(--a);stroke-width:2' }, fig);
  svg('rect', { x: 370, y: 140, width: 260, height: 310, rx: 14, 'data-k': 'dec', style: 'fill:var(--c-soft);stroke:var(--c);stroke-width:2' }, fig);
  svg('text', { x: 24, y: 335, 'text-anchor': 'middle', transform: 'rotate(-90 24 335)', class: 't', style: 'fill:var(--a);font-weight:700', text: 'Encoder · N× (N = 6)' }, fig);
  svg('text', { x: 648, y: 300, 'text-anchor': 'middle', transform: 'rotate(90 648 300)', class: 't', style: 'fill:var(--c);font-weight:700', text: 'Decoder · N× (N = 6)' }, fig);
  // encoder
  R([[160, 438], [58, 438], [58, 358], [70, 358]]);
  R([[160, 332], [58, 332], [58, 253], [70, 253]]);
  [110, 160, 210].forEach(x => A(x, 438, x, 427));
  B('encMHA', 70, 385, 180, 40, 'var(--b)', 'Multi-Head\nAttention');
  A(160, 385, 160, 373); B('an', 70, 345, 180, 26, 'var(--e)', 'Add & Norm');
  A(160, 345, 160, 322); B('ffn', 70, 280, 180, 40, '#3a8fd8', 'Feed\nForward');
  A(160, 280, 160, 268); B('an', 70, 240, 180, 26, 'var(--e)', 'Add & Norm');
  B('inEmb', 70, 515, 180, 34, 'var(--faint)', 'Input Embedding');
  A(160, 515, 160, 499);
  const pe1 = svg('g', { 'data-k': 'pe' }, fig); svg('circle', { cx: 160, cy: 485, r: 13, style: 'fill:#c9a227' }, pe1); svg('text', { x: 160, y: 490, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:16px;font-weight:700', text: '+' }, pe1);
  svg('text', { x: 108, y: 482, 'text-anchor': 'end', class: 'tm', style: 'font-size:10.5px', text: 'Positional' }, fig); svg('text', { x: 108, y: 495, 'text-anchor': 'end', class: 'tm', style: 'font-size:10.5px', text: 'Encoding' }, fig);
  svg('line', { x1: 160, y1: 472, x2: 160, y2: 438, style: 'stroke:var(--muted);stroke-width:1.6' }, fig);
  svg('line', { x1: 110, y1: 438, x2: 210, y2: 438, style: 'stroke:var(--muted);stroke-width:1.6' }, fig);
  svg('text', { x: 160, y: 585, 'text-anchor': 'middle', class: 't', style: 'font-weight:600', text: 'Inputs' }, fig);
  A(160, 570, 160, 551);
  // decoder
  R([[500, 443], [388, 443], [388, 365], [410, 365]]);
  R([[500, 340], [388, 340], [388, 265], [410, 265]]);
  R([[500, 243], [388, 243], [388, 168], [410, 168]]);
  [455, 500, 545].forEach(x => A(x, 443, x, 432));
  B('decMMHA', 410, 390, 180, 40, 'var(--b)', 'Masked\nMulti-Head Attention');
  A(500, 390, 500, 380); B('an', 410, 352, 180, 26, 'var(--e)', 'Add & Norm');
  A(545, 352, 545, 332); B('decMHA', 410, 290, 180, 40, 'var(--b)', 'Multi-Head\nAttention');
  A(500, 290, 500, 280); B('an', 410, 252, 180, 26, 'var(--e)', 'Add & Norm');
  A(500, 252, 500, 237); B('ffn', 410, 195, 180, 40, '#3a8fd8', 'Feed\nForward');
  A(500, 195, 500, 183); B('an', 410, 155, 180, 26, 'var(--e)', 'Add & Norm');
  A(500, 155, 500, 125); B('lin', 430, 95, 140, 28, 'var(--c)', 'Linear');
  A(500, 95, 500, 85); B('soft', 430, 55, 140, 28, 'var(--c)', 'Softmax');
  A(500, 55, 500, 32); svg('text', { x: 500, y: 22, 'text-anchor': 'middle', class: 't', style: 'font-weight:600', text: 'Output Probabilities' }, fig);
  B('outEmb', 410, 515, 180, 34, 'var(--faint)', 'Output Embedding');
  A(500, 515, 500, 499);
  const pe2 = svg('g', { 'data-k': 'pe' }, fig); svg('circle', { cx: 500, cy: 485, r: 13, style: 'fill:#c9a227' }, pe2); svg('text', { x: 500, y: 490, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:16px;font-weight:700', text: '+' }, pe2);
  svg('text', { x: 520, y: 482, class: 'tm', style: 'font-size:10.5px', text: 'Positional' }, fig); svg('text', { x: 520, y: 495, class: 'tm', style: 'font-size:10.5px', text: 'Encoding' }, fig);
  svg('line', { x1: 500, y1: 472, x2: 500, y2: 443, style: 'stroke:var(--muted);stroke-width:1.6' }, fig);
  svg('line', { x1: 455, y1: 443, x2: 545, y2: 443, style: 'stroke:var(--muted);stroke-width:1.6' }, fig);
  svg('text', { x: 500, y: 585, 'text-anchor': 'middle', class: 't', style: 'font-weight:600', text: 'Outputs (shifted right)' }, fig);
  A(500, 570, 500, 551);
  // encoder → decoder (K, V)
  TX.arrowDefs(fig, 'fk', 'var(--a)');
  svg('polyline', { points: '160,240 160,200 340,200 340,312 406,312', fill: 'none', style: 'stroke:var(--a);stroke-width:2.5', 'marker-end': 'url(#fk)' }, fig);
  svg('text', { x: 250, y: 192, 'text-anchor': 'middle', class: 't', style: 'fill:var(--a);font-size:11px;font-weight:600', text: 'encoder output → K, V' }, fig);
  svg('text', { x: 556, y: 346, class: 't', style: 'fill:var(--c);font-size:10px;font-weight:600', text: 'Q' }, fig);
  fig.addEventListener('click', e => {
    const g = e.target.closest('[data-k]'); if (!g) return;
    const [t, d, deck] = INFO[g.dataset.k];
    document.getElementById('figInfo').innerHTML = `<b>${t}</b><br>${d}${deck ? `<br><br><a href="../${deck}/index.html">Open the deck →</a>` : ''}`;
  });

  /* shape flow */
  const FLOW = [
    ['Source tokens', '[n]', 'Byte-pair tokens of the source sentence (shared EN-DE vocabulary ≈ 37,000 tokens).'],
    ['Embed × √512', '[n × 512]', 'Look up each token in the shared embedding matrix and multiply by √d<sub>model</sub> ≈ 22.6.'],
    ['+ Positional encoding', '[n × 512]', 'Add sinusoidal PE so each vector also encodes its position, then dropout (0.1).'],
    ['Encoder × 6', '[n × 512]', 'Each layer: self-attention, then FFN, each wrapped in Add & Norm. The shape never changes, so the output becomes the "memory".'],
    ['Target, shifted right', '[m]', 'Target tokens with a start symbol in front, so position i is given tokens &lt; i and asked to predict token i.'],
    ['Embed + PE', '[m × 512]', 'Same shared embedding matrix (×√512) plus positional encodings.'],
    ['Decoder × 6', '[m × 512]', 'Each layer: masked self-attention → encoder-decoder attention (K, V = memory [n × 512]) → FFN, each with Add & Norm.'],
    ['Linear (tied weights)', '[m × V]', 'Project to vocabulary logits with the transpose of the shared embedding matrix.'],
    ['Softmax', '[m × V]', 'A probability distribution over the next token at each of the m positions, all computed in one parallel pass during training.'],
  ];
  const fs = document.getElementById('flowSteps');
  fs.innerHTML = FLOW.map((f, i) => `<button data-i="${i}">${i + 1}. ${f[0]}</button>`).join('');
  const pickFlow = i => {
    Deck.$$('button', fs).forEach(b => b.classList.toggle('on', +b.dataset.i === i));
    const [t, sh, d] = FLOW[i];
    document.getElementById('flowInfo').innerHTML = `<b>${i + 1}. ${t}</b> &nbsp; <span class="shape">${sh}</span><br><br>${d}`;
  };
  fs.addEventListener('click', e => { const b = e.target.closest('button'); if (b) pickFlow(+b.dataset.i); });
  pickFlow(0);
})();
