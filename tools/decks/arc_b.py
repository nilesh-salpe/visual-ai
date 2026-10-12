from tool import section, your_turn, myths, check

DECKS = {}


def deep(title, html):
    return f'    <div class="deep"><h4>{title}</h4>{html}</div>'


# =============================================================== 07
DECKS['07-rope-scaling'] = dict(
    title='Long Context I: Stretching RoPE', h1='Long context I: stretching RoPE',
    sub='Why a model trained on 4K tokens falls apart at 32K, and how Position Interpolation, NTK-aware scaling, YaRN and Llama 3\'s long-context training fix it.',
    prob='A RoPE model trained at length L sees angles m·θᵢ only for m < L. Beyond L, the slow pairs reach angles the model has never seen, and attention scores blow up.',
    core='Remap the rotation frequencies so long positions land on <b>angles seen in training</b>. PI slows every pair by s. NTK-aware raises the base. YaRN slows only the slow pairs and adds a temperature. Then fine-tune briefly, or train long from the start.',
    build=['06_rope_scaling'],
    sources='Chen et al. 2023, "Extending Context Window of Large Language Models via Positional Interpolation"; Peng et al. 2023, "YaRN" (eq. 13–22, §4); Su et al. 2021 (RoFormer); Llama Team 2024 (Llama 3 §3.2 RoPE base; §3.4.2 long-context pretraining).',
    slides=[
        section('s-p1', 1, 'Fast pairs have seen every angle; slow pairs haven\'t', '''    <p class="lede">Each RoPE pair turns at its own speed. During training at L = 4,096 (d = 128, base 10,000), a fast pair goes round the circle hundreds of times, so every angle is familiar. A slow pair covers only part of the circle. Pick a pair and an extension factor: green is the arc seen in training, red is new territory at s·L.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">Pair i <input type="range" id="eI" min="0" max="63" step="1" value="50"> <output id="eIo"></output></label>
        <div class="seg" id="eS"><button data-v="2">2×</button><button data-v="4">4×</button><button data-v="8" class="on">8× (32K)</button></div>
      </div>
      <svg id="eSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Trained vs extended angle range"></svg>
      <p class="readout" id="eOut"></p>
    </div>'''),
        section('s-lim', 2, 'Why the obvious options fail', '''    <div class="grid3">
      <div class="card d"><h3>Just run longer (extrapolate)</h3><p>Unseen angles in the slow pairs produce what PI calls "catastrophically high attention scores". Perplexity shoots up as soon as you pass L.</p></div>
      <div class="card b"><h3>Train long from the start</h3><p>Attention costs grow with sequence length, and most pretraining documents are short anyway. Paying for 128K context on every step is wasteful.</p></div>
      <div class="card c"><h3>Squeeze naively</h3><p>Dividing every position by s keeps angles in range, but neighbouring tokens become s× closer in the fast pairs. Local order gets blurry, which costs short-context quality unless you fine-tune.</p></div>
    </div>'''),
        your_turn('s-turn', 'What does Position Interpolation do?',
                  'A LLaMA model trained at 2,048 tokens should handle 8,192. What does Position Interpolation (Chen et al. 2023) change?',
                  ['Adds new position embeddings for 2,048–8,192', 'Uses position m/4 instead of m, then fine-tunes briefly', 'Drops RoPE beyond 2,048', 'Trains from scratch at 8,192'], 1,
                  '<b>B.</b> PI "linearly down-scales the input position indices to match the original context window size". Every angle stays inside the trained range. About 1,000 fine-tuning steps were enough to reach 32,768 tokens on LLaMA 7B–65B, and the authors bound interpolation\'s error at about 600× smaller than extrapolation\'s.'),
        section('s-core', 4, 'Three ways to remap frequencies', '''    <div class="grid3">
      <div class="card a"><h3>PI: slow everything by s</h3><p>θᵢ → θᵢ / s for every pair. Simple and safe, but it compresses local resolution by s in the fast pairs.</p></div>
      <div class="card b"><h3>NTK-aware: change the base</h3><p>base → base · s<sup>d/(d−2)</sup>. The fastest pair is unchanged, the slowest is slowed by exactly s, and those in between are slowed smoothly. It keeps local order sharp, but most slow pairs still slightly overshoot.</p></div>
      <div class="card e"><h3>YaRN: by parts, plus temperature</h3><p>Count each pair's turns within L: r = L/λᵢ. If r &lt; α (=1): interpolate fully (θ/s). If r &gt; β (=32): leave alone. Blend linearly in between. Scale logits by √(1/t) = 0.1·ln s + 1.</p></div>
    </div>
''' + deep('Why YaRN adds a temperature', '<p>Stretching the context spreads attention over many more tokens, so the softmax gets flatter (higher entropy). YaRN scales q and k so the logits are multiplied by (0.1·ln s + 1)²; at s = 8, √(1/t) ≈ 1.208. The coefficient was fit empirically on LLaMA models. YaRN reports needing about <b>10× fewer tokens and 2.5× fewer training steps</b> than previous methods: <b>400 steps</b>, about 0.1% of the original pretraining data, and it was the first method to extend Llama 2\'s effective context to 128K.</p>')),
        section('s-how', 5, 'Slow-down per pair, for each method', '''    <p class="lede">For each of the 64 pairs (d = 128, L = 4,096), how much each method slows that pair (θ ÷ θ′). Pairs to the right are slower. The shaded region marks pairs whose wavelength is longer than L: they never complete a turn in training, so they are the ones that must be slowed by s.</p>
    <div class="visual">
      <div class="seg" id="sS"><button data-v="4">s = 4</button><button data-v="8" class="on">s = 8</button><button data-v="32">s = 32</button></div>
      <svg id="sSvg" viewBox="0 0 660 260" style="margin-top:10px" role="img" aria-label="Slow-down factor by pair"></svg>
      <div class="legend"><span><i style="background:var(--faint)"></i>no scaling</span><span><i style="background:var(--d)"></i>PI</span><span><i style="background:var(--b)"></i>NTK-aware</span><span><i style="background:var(--a)"></i>YaRN (α = 1, β = 32)</span></div>
      <p class="readout" id="sOut"></p>
    </div>'''),
        section('s-how2', 5, 'Or train long directly: the Llama 3 recipe', '''    <div class="grid2">
      <div class="card a"><h3>A larger RoPE base from the start</h3><p>Llama 3 sets the RoPE base to <b>500,000</b> (Llama 2: 10,000) "to better support longer contexts". Every pair except the first rotates more slowly, so more of the spectrum stays distinguishable at long range.</p></div>
      <div class="card e"><h3>Grow the context in stages</h3><p>Pretrain at 8K, then extend in <b>six stages</b> up to 128K using about <b>800B tokens</b>. Each stage continues until short-context performance has fully recovered and needle-in-a-haystack retrieval is solved perfectly at that length.</p></div>
    </div>
    <div class="visual scroll-x" style="margin-top:12px"><table class="tbl">
      <tr><th>Method</th><th>What changes</th><th>Training cost reported</th><th>Reach reported</th></tr>
      <tr><td>Extrapolation</td><td>nothing</td><td>none</td><td>breaks just past L</td></tr>
      <tr><td>PI (2023)</td><td>positions ÷ s</td><td>~1,000 steps</td><td>32,768 (LLaMA 7B–65B)</td></tr>
      <tr><td>NTK-aware (2023)</td><td>RoPE base × s<sup>d/(d−2)</sup></td><td>none needed: "much better" than PI on non-fine-tuned models</td><td>but worse than PI after fine-tuning, because some pairs go slightly out of bounds (YaRN §3.1)</td></tr>
      <tr><td>YaRN (2023)</td><td>per-pair ramp + temperature</td><td>400 steps, ~0.1% of pretraining data</td><td>128K (Llama 2)</td></tr>
      <tr><td>Llama 3 (2024)</td><td>base 500K + 6-stage continued pretraining</td><td>~800B tokens</td><td>128K</td></tr>
    </table></div>'''),
        section('s-why', 6, 'Why remapping works', '''    <div class="grid2">
      <div class="card a"><h3>Attention only needs familiar angles</h3><p>The model learned what each angle in each pair means. Keep every (pair, angle) combination inside the trained range and attention behaves normally, even at positions it never saw.</p></div>
      <div class="card e"><h3>Fast pairs don't need help</h3><p>A pair that turned hundreds of times during training has seen every angle, so its behaviour at long range is not new. Leaving it alone (NTK, YaRN) keeps fine local resolution.</p></div>
      <div class="card b"><h3>Slow pairs do</h3><p>Pairs with wavelength longer than L only ever covered part of the circle. They are where unseen angles come from, so they get the full s× slow-down.</p></div>
      <div class="card d"><h3>Fine-tuning closes the gap</h3><p>Any remapping shifts the distribution a little. A short fine-tune at the new length lets the model adapt; the methods differ mostly in how short that can be.</p></div>
    </div>'''),
        myths('s-myth', [
            ('A 128K context window means the model uses all 128K tokens well.', 'The window is what it accepts. How well it retrieves and reasons over distant tokens has to be measured (needle-in-a-haystack, long-document tasks). Llama 3 used both as stage criteria.'),
            ('Position Interpolation needs no training.', 'PI keeps angles in range but compresses local resolution. The paper fine-tunes for about 1,000 steps.'),
            ('Raising the RoPE base is all you need.', 'A bigger base changes the frequencies the model was trained on. It has to be trained (or fine-tuned) at long lengths with that base, which is what Llama 3\'s staged continued pretraining does.'),
        ]),
        check('s-check', [
            ('mcq', 'In YaRN, a pair that completes more than β = 32 turns within the original context is…', ['interpolated by s', 'left unchanged', 'removed', 'given a larger temperature'], 1, '<b>Left unchanged</b>: it has already seen every angle.'),
            ('open', 'Why does plain extrapolation fail, while PI works after a short fine-tune?', 'Beyond L, slow RoPE pairs reach angles never seen in training and attention scores blow up. PI divides positions by s so every angle stays inside the trained range; the fine-tune adapts the model to the compressed local spacing.'),
            ('open', 'What did Llama 3 do instead of a post-hoc scaling trick?', 'A larger RoPE base (500,000) plus six stages of continued pretraining from 8K to 128K tokens (about 800B tokens), moving on only once short-context quality recovered and needle-in-a-haystack was solved.'),
        ]),
    ],
    js=r'''
  const d = 128, base = 1e4, Lc = 4096, TH = [...Array(64)].map((_, i) => Math.pow(base, -2 * i / d));
  let es = 8;
  const arc = () => {
    const i = Deck.val('eI'); Deck.out('eIo', i);
    const th = TH[i], lam = 2 * Math.PI / th, seen = Lc * th, ext = es * Lc * th;
    const s = clear(document.getElementById('eSvg')), cx = 160, cy = 115, r = 85;
    svg('circle', { cx, cy, r, style: 'fill:none;stroke:var(--line);stroke-width:10' }, s);
    const path = (a0, a1, color) => {
      const sweep = Math.min(a1, 2 * Math.PI - 1e-4) - a0; if (sweep <= 0) return;
      const p = a => [cx + r * Math.cos(a), cy - r * Math.sin(a)];
      const [x0, y0] = p(a0), [x1, y1] = p(a0 + sweep);
      svg('path', { d: `M${x0} ${y0} A${r} ${r} 0 ${sweep > Math.PI ? 1 : 0} 0 ${x1} ${y1}`, fill: 'none', style: `stroke:${color};stroke-width:10` }, s);
    };
    if (seen >= 2 * Math.PI) path(0, 2 * Math.PI, 'var(--e)'); else { path(seen, ext, 'var(--d)'); path(0, seen, 'var(--e)'); }
    const turns = seen / (2 * Math.PI);
    svg('text', { x: cx, y: cy + 5, 'text-anchor': 'middle', class: 't', style: 'font-weight:700', text: `pair ${i}` }, s);
    const lines = [`θ = ${th.toPrecision(3)} rad/token`, `wavelength = ${Math.round(lam).toLocaleString()} tokens`, `turns during training (L = 4,096): ${turns >= 10 ? turns.toFixed(0) : turns.toFixed(2)}`, `turns needed at ${es}× (${(es * Lc).toLocaleString()} tokens): ${(turns * es) >= 10 ? (turns * es).toFixed(0) : (turns * es).toFixed(2)}`];
    lines.forEach((t, k) => svg('text', { x: 300, y: 60 + k * 30, class: k > 1 ? 't' : 'tm', text: t }, s));
    document.getElementById('eOut').innerHTML = turns >= 1
      ? 'This pair completed at least one full turn in training: every angle is already familiar, so going longer adds nothing new.'
      : `This pair covered only <b>${(100 * turns).toFixed(0)}%</b> of the circle in training. At ${es}× length it would reach angles it has <b>never seen</b> (red). These slow pairs are the ones that need interpolation.`;
  };
  Deck.bind(['eI'], arc); Deck.seg('eS', v => { es = +v; arc(); });
  Deck.seg('sS', v => {
    const sc = +v, ntkB = base * Math.pow(sc, d / (d - 2));
    const pi = TH.map(t => sc), ntk = TH.map((t, i) => t / Math.pow(ntkB, -2 * i / d));
    const yarn = TH.map(t => { const r = Lc * t / (2 * Math.PI), g = Math.min(1, Math.max(0, (r - 1) / 31)); return t / ((1 - g) * t / sc + g * t); });
    const s = clear(document.getElementById('sSvg')), L0 = 60, R0 = 630, T0 = 14, B0 = 210, X = i => L0 + i / 63 * (R0 - L0), Y = f => B0 - Math.log(f) / Math.log(32) * (B0 - T0);
    const firstSlow = TH.findIndex(t => 2 * Math.PI / t > Lc);
    svg('rect', { x: X(firstSlow), y: T0, width: R0 - X(firstSlow), height: B0 - T0, style: 'fill:var(--d-soft)' }, s);
    svg('text', { x: (X(firstSlow) + R0) / 2, y: T0 + 16, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: 'wavelength > L' }, s);
    [1, 2, 4, 8, 16, 32].forEach(f => { svg('line', { x1: L0, x2: R0, y1: Y(f), y2: Y(f), class: 'ln' }, s); svg('text', { x: L0 - 8, y: Y(f) + 4, 'text-anchor': 'end', class: 'tm', text: f + '×' }, s); });
    [0, 16, 32, 48, 63].forEach(i => svg('text', { x: X(i), y: B0 + 18, 'text-anchor': 'middle', class: 'tm', text: i }, s));
    const line = (vals, c) => svg('polyline', { points: vals.map((f, i) => `${X(i)},${Y(f)}`).join(' '), fill: 'none', style: `stroke:${c};stroke-width:2.5` }, s);
    line(TH.map(() => 1), 'var(--faint)'); line(pi, 'var(--d)'); line(ntk, 'var(--b)'); line(yarn, 'var(--a)');
    svg('text', { x: (L0 + R0) / 2, y: B0 + 40, 'text-anchor': 'middle', class: 'tm', text: 'pair index i (fast → slow)' }, s);
    const over = arr => TH.filter((t, i) => 2 * Math.PI / t > Lc && (sc * Lc - 1) * (t / arr[i]) > Lc * t).length;
    document.getElementById('sOut').innerHTML = `Slow pairs (shaded, ${64 - firstSlow} of 64) still pushed past their trained angle range at ${sc}× length: no scaling <b>${over(TH.map(() => 1))}</b>, PI <b>${over(pi)}</b>, NTK-aware <b>${over(ntk)}</b>, YaRN <b>${over(yarn)}</b>. PI also slows the fastest pair ${sc}×; NTK and YaRN leave it at 1×.`;
  });
''',
    line='Long context means keeping every RoPE angle inside the range seen in training: slow the slow pairs (PI, NTK, YaRN) or train long with a bigger base (Llama 3).',
    explain='A RoPE model trained at length L has seen each pair\'s angles only up to L times theta. Fast pairs turn many times, so every angle is familiar, but slow pairs cover only part of the circle, and past L they produce unseen angles and exploding attention scores. Position Interpolation divides positions by the extension factor so every angle stays in range, then fine-tunes for about a thousand steps. NTK-aware scaling raises the base so fast pairs stay sharp. YaRN interpolates only the slow pairs, adds an attention temperature, and needs about 400 steps. Llama 3 instead uses a base of 500,000 and six stages of continued pretraining up to 128K.',
    recap=[('Problem', 'slow RoPE pairs hit unseen angles past the trained length.'), ('Remap', 'PI (all ÷ s), NTK-aware (bigger base), YaRN (slow pairs only + temperature).'), ('Train long', 'Llama 3: base 500K, 6 stages, 8K → 128K, ~800B tokens.')],
)

# =============================================================== 08
DECKS['08-sliding-window'] = dict(
    title='Long Context II: Sliding Window and ALiBi', h1='Long context II: sliding window and ALiBi',
    sub='Two other ways to handle long sequences: limit how far each layer looks (sliding-window attention with a rolling KV cache), or bias scores by distance (ALiBi).',
    prob='Full attention costs O(T²) compute and its KV cache grows with every token. At long T, both memory and time explode, even when most useful context is nearby.',
    core='<b>Sliding window</b>: each token attends only to the last W tokens, and stacked layers relay information further back, so the cache can be a fixed-size ring buffer. <b>ALiBi</b>: no position embeddings; subtract a head-specific slope × distance from every score.',
    build=['07_sliding_window'],
    sources='Jiang et al. 2023, "Mistral 7B" (§2, Table 1, Fig. 1–2); Jiang et al. 2024 (Mixtral §2, dense 32K); Beltagy et al. 2020 (Longformer); Press et al. 2022, "Train Short, Test Long: Attention with Linear Biases" (ALiBi, §3).',
    slides=[
        section('s-p1', 1, 'Full attention gets expensive fast', '''    <p class="lede">Score computations per layer and KV-cache entries per layer, as the sequence grows. Full causal attention computes about T²/2 scores and caches T entries. A sliding window of W = 4,096 computes at most T·W and caches at most W.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0"><label class="ctl">Sequence length T <input type="range" id="cT" min="10" max="17" step="0.5" value="15"> <output id="cTo"></output></label></div>
      <div id="cBars" style="margin-top:12px"></div>
    </div>'''),
        section('s-lim', 2, 'Why not just cut the context?', '''    <div class="grid3">
      <div class="card d"><h3>Truncating loses information</h3><p>Dropping everything older than W tokens at the input means the model can't use it at all.</p></div>
      <div class="card b"><h3>Sparse patterns are fiddly</h3><p>Hand-designed sparse attention (strided, global tokens) needs custom kernels and careful choices for every pattern.</p></div>
      <div class="card c"><h3>Position extrapolation still matters</h3><p>Even with cheaper attention, the position encoding must behave sensibly at lengths beyond training (deck 07, and ALiBi below).</p></div>
    </div>'''),
        your_turn('s-turn', 'How far can a window see?',
                  'Mistral 7B uses a window of W = 4,096 tokens in each of its 32 layers. What is the theoretical attention span at the last layer?',
                  ['4,096 tokens', '8,192 tokens', 'About 131K tokens', 'Unlimited'], 2,
                  '<b>C.</b> Each layer lets information move up to W tokens further back. After 32 layers that is about 32 × 4,096 ≈ <b>131K</b> tokens (Mistral\'s figure). Exactly: L·(W−1)+1 = 131,041 with an inclusive window of W keys.'),
        section('s-core', 4, 'Two ideas', '''    <div class="grid2">
      <div class="card a"><h3>Sliding-window attention (SWA)</h3><p>Token i attends to positions i−W+1 … i only. Information from further back reaches i indirectly: token i−W saw it in the previous layer. The KV cache needs only the last W entries, stored in a <b>rolling buffer</b> at slot i mod W. Mistral 7B: W = 4,096, 2× faster at 16K with its kernel changes, 8× less cache at 32K.</p></div>
      <div class="card b"><h3>ALiBi</h3><p>Don't add position embeddings at all. Add a <b>linear penalty</b> −m·(i−j) to each query-key score, with a different slope m per head (a geometric sequence, 1/2 … 1/256 for 8 heads). Trained at 1,024 tokens, a 1.3B model extrapolates to 2,048 and matches a sinusoidal model trained at 2,048, while training 11% faster and using 11% less memory.</p></div>
    </div>
''' + deep('Not every Mistral-family model uses the window', '<p>Mixtral\'s paper notes it "supports a fully dense context length of 32k tokens", meaning full attention, unlike Mistral 7B\'s sliding window. Windowing is a per-model design choice; a model card or config (<code>sliding_window</code>) tells you which.</p>')),
        section('s-how', 5, 'Stacked windows: the receptive field grows with depth', '''    <p class="lede">Each row is a layer, each column a position (newest on the right). Highlighted cells are positions that can influence the last token\'s output through the stack. One layer sees W positions; each extra layer reaches W−1 further.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">Window W <input type="range" id="wW" min="2" max="8" step="1" value="4"> <output id="wWo"></output></label>
        <label class="ctl">Layers <input type="range" id="wL" min="1" max="8" step="1" value="4"> <output id="wLo"></output></label>
      </div>
      <svg id="wSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Receptive field across layers"></svg>
      <p class="readout" id="wOut"></p>
    </div>'''),
        section('s-how2', 5, 'The rolling-buffer KV cache', '''    <p class="lede">A cache of W = 4 slots. Token t's key and value are written to slot <b>t mod 4</b>, overwriting the entry from t−4, which the window no longer needs. Press "next token".</p>
    <div class="visual">
      <div class="controls" style="margin-top:0"><button class="btn primary" id="rbNext">next token</button><button class="btn" id="rbReset">reset</button></div>
      <svg id="rbSvg" viewBox="0 0 660 170" style="margin-top:10px" role="img" aria-label="Rolling buffer"></svg>
      <p class="readout" id="rbOut"></p>
    </div>'''),
        section('s-how3', 5, 'ALiBi: a distance penalty per head', '''    <p class="lede">The bias added to each attention score for one head (rows: query position i, columns: key position j, causal). Darker means a bigger penalty. Heads with a steep slope focus locally; heads with a gentle slope can look far back.</p>
    <div class="visual">
      <div class="seg" id="aSeg"><button data-v="1" class="on">head 1 (m = 1/2)</button><button data-v="3">head 3 (m = 1/8)</button><button data-v="5">head 5 (m = 1/32)</button><button data-v="8">head 8 (m = 1/256)</button></div>
      <svg id="aSvg" viewBox="0 0 660 260" style="margin-top:10px" role="img" aria-label="ALiBi bias matrix"></svg>
    </div>
    <p class="caption">Slopes for 8 heads: the geometric sequence 1/2¹, 1/2², …, 1/2⁸. For n heads it starts at 2^(−8/n) with the same ratio (Press et al.).</p>'''),
        section('s-why', 6, 'Why they work, and their limits', '''    <div class="grid2">
      <div class="card a"><h3>Most attention is local</h3><p>Many heads mostly look nearby. A window keeps that cheap and lets depth carry longer-range information.</p></div>
      <div class="card e"><h3>Memory becomes constant</h3><p>With a rolling buffer, KV memory per sequence is capped at W entries per layer: 8× smaller at 32K for Mistral 7B, and it never grows during generation.</p></div>
      <div class="card b"><h3>ALiBi has no unseen positions</h3><p>A penalty proportional to distance is defined for any distance, and longer distances just get a larger penalty, which is why it extrapolates.</p></div>
      <div class="card d"><h3>Limits</h3><p>Information older than W must survive several relays, so exact long-range retrieval is harder than with full attention. ALiBi's built-in bias towards recent tokens can also limit how much distant text is used.</p></div>
    </div>'''),
        myths('s-myth', [
            ('A sliding-window model can\'t use anything older than W tokens.', 'It can, indirectly: information moves up to W further back per layer, so the theoretical span is about L × W. It is lossy, though.'),
            ('ALiBi is a kind of position embedding.', 'Nothing is added to the embeddings. ALiBi adds a fixed, distance-dependent <b>bias to the attention scores</b>.'),
            ('Every Mistral model uses sliding-window attention.', 'Mistral 7B does (W = 4,096). Mixtral uses fully dense attention over 32K. Check the config.'),
        ]),
        check('s-check', [
            ('mcq', 'In Mistral\'s rolling buffer with W = 4,096, where is token 10,000\'s key stored?', ['slot 10,000', 'slot 10,000 mod 4,096 = 1,808', 'slot 0', 'it isn\'t cached'], 1, '<b>Slot i mod W = 1,808</b>, overwriting token 5,904\'s entry.'),
            ('open', 'What does ALiBi add to the score between query i and key j?', '−m·(i − j), a negative bias growing linearly with distance, with a fixed slope m per head (e.g. 1/2 … 1/256 for 8 heads). No position embeddings at all.'),
            ('open', 'Why does sliding-window attention make the KV cache constant-size?', 'A token never attends further back than W positions, so older keys and values are never needed again and can be overwritten in a ring buffer of W slots.'),
        ]),
    ],
    js=r'''
  Deck.bind(['cT'], () => {
    const T = Math.round(Math.pow(2, Deck.val('cT'))), W = 4096; Deck.out('cTo', T.toLocaleString());
    const full = T * (T + 1) / 2, win = T <= W ? full : W * (W + 1) / 2 + (T - W) * W;
    Deck.hbars(document.getElementById('cBars'), [
      { label: 'scores, full attention', value: full, color: 'var(--d)', text: Deck.fmt(full) },
      { label: 'scores, window 4,096', value: win, color: 'var(--a)', text: Deck.fmt(win) },
      { label: 'KV entries, full', value: T, color: 'var(--d)', text: T.toLocaleString() },
      { label: 'KV entries, rolling buffer', value: Math.min(T, W), color: 'var(--a)', text: Math.min(T, W).toLocaleString() }], { log: true, min: 100 });
  });
  Deck.bind(['wW', 'wL'], () => {
    const W = Deck.val('wW'), L = Deck.val('wL'), N = 40; Deck.out('wWo', W); Deck.out('wLo', L);
    const s = clear(document.getElementById('wSvg')), c = 15, x0 = 30, rowH = 210 / (L + 1);
    for (let l = 0; l <= L; l++) {
      const reach = l === 0 ? 1 : l * (W - 1) + 1, y = 200 - l * rowH;
      for (let p = 0; p < N; p++) {
        const dist = N - 1 - p, on = l === 0 ? dist === 0 : dist < reach;
        svg('rect', { x: x0 + p * c, y: y - c + 2, width: c - 3, height: c - 3, rx: 3, style: `fill:${on ? (l === L ? 'var(--a)' : 'var(--a-soft)') : 'var(--panel-2)'}` }, s);
      }
      svg('text', { x: x0 - 6, y: y - 3, 'text-anchor': 'end', class: 'tm', style: 'font-size:10px', text: l === 0 ? 'out' : 'L' + l }, s);
    }
    const span = L * (W - 1) + 1;
    document.getElementById('wOut').innerHTML = `${L} layer${L > 1 ? 's' : ''} × window ${W}: the last token can be influenced by <b>${span}</b> positions (L·(W−1)+1). Mistral 7B: 32·4,095+1 = <b>131,041</b> ≈ 131K.`;
  });
  let t = 0; const W = 4, slots = Array(W).fill(null);
  const rb = () => {
    const s = clear(document.getElementById('rbSvg'));
    for (let k = 0; k < W; k++) {
      const x = 130 + k * 105, hot = t > 0 && (t - 1) % W === k;
      svg('rect', { x, y: 40, width: 90, height: 60, rx: 9, style: `fill:${hot ? 'var(--b)' : slots[k] === null ? 'var(--panel-2)' : 'var(--a)'}` }, s);
      svg('text', { x: x + 45, y: 76, 'text-anchor': 'middle', class: 't', style: slots[k] === null ? '' : 'fill:#fff;font-weight:700', text: slots[k] === null ? 'empty' : 'k,v of t=' + slots[k] }, s);
      svg('text', { x: x + 45, y: 120, 'text-anchor': 'middle', class: 'tm', text: 'slot ' + k }, s);
    }
    document.getElementById('rbOut').innerHTML = t === 0 ? 'Empty cache. Press "next token".' : `Token t = ${t - 1} written to slot ${(t - 1) % W} = ${t - 1} mod ${W}. The cache holds tokens ${Math.max(0, t - W)}…${t - 1}, exactly the window. A full cache would now hold ${t} entries; this one never exceeds ${W}.`;
  };
  document.getElementById('rbNext').addEventListener('click', () => { slots[t % W] = t; t++; rb(); });
  document.getElementById('rbReset').addEventListener('click', () => { t = 0; slots.fill(null); rb(); });
  rb();
  Deck.seg('aSeg', v => {
    const h = +v, m = Math.pow(2, -h), N = 12, s = clear(document.getElementById('aSvg')), c = 18, x0 = 200, y0 = 14, maxPen = 11 * 0.5;
    for (let i = 0; i < N; i++) for (let j = 0; j < N; j++) {
      if (j > i) { svg('rect', { x: x0 + j * c, y: y0 + i * c, width: c - 2, height: c - 2, rx: 2, style: 'fill:var(--panel-2)' }, s); continue; }
      const pen = m * (i - j);
      svg('rect', { x: x0 + j * c, y: y0 + i * c, width: c - 2, height: c - 2, rx: 2, style: `fill:var(--d);opacity:${(0.06 + 0.94 * pen / maxPen).toFixed(3)}` }, s);
    }
    svg('text', { x: x0 + N * c / 2, y: y0 + N * c + 20, 'text-anchor': 'middle', class: 'tm', text: 'key position j →' }, s);
    svg('text', { x: x0 - 10, y: y0 + N * c / 2, 'text-anchor': 'end', class: 'tm', text: 'query i ↓' }, s);
    svg('text', { x: 460, y: 60, class: 't', text: `slope m = 1/${Math.pow(2, h)}` }, s);
    svg('text', { x: 460, y: 86, class: 'tm', text: `bias at distance 1: −${m.toPrecision(2)}` }, s);
    svg('text', { x: 460, y: 108, class: 'tm', text: `bias at distance 11: −${(11 * m).toPrecision(2)}` }, s);
    svg('text', { x: 460, y: 130, class: 'tm', text: `bias at distance 1,000: −${(1000 * m).toPrecision(3)}` }, s);
  });
''',
    line='Sliding windows cap attention cost and KV memory and rely on depth to reach further; ALiBi replaces position embeddings with a per-head distance penalty that extrapolates.',
    explain='Full attention costs order T squared and its cache grows with every token. Sliding-window attention lets each token attend only to the last W tokens. Information older than that still flows indirectly through the stack, so Mistral 7B, with W of 4,096 over 32 layers, has a theoretical span of about 131K. Because no token looks back further than W, the KV cache can be a ring buffer indexed by position mod W: 8 times less memory at 32K. ALiBi removes position embeddings and subtracts a head-specific slope times the distance from each attention score, which let a model trained at 1,024 tokens work at 2,048.',
    recap=[('Problem', 'O(T²) scores and an ever-growing KV cache.'), ('SWA', 'attend to the last W; span ≈ L·W; rolling buffer at i mod W.'), ('ALiBi', 'score − m·distance, slopes 1/2…1/256; train short, test long.')],
)

# =============================================================== 09
DECKS['09-flash-attention'] = dict(
    title='FlashAttention Internals', h1='FlashAttention internals',
    sub='How computing exact attention in tiles, with an online softmax, avoids writing the N×N matrix to GPU memory. Plus what FlashAttention-2 and -3 changed.',
    prob='Standard attention writes the N×N score matrix to HBM, reads it back for the softmax, writes probabilities and reads them again. At long N this memory traffic, not arithmetic, dominates the runtime.',
    core='Load blocks of Q, K and V into on-chip SRAM, compute scores, softmax and output for that tile there, and combine tiles with an <b>online softmax</b> (running max and sum, rescaling). The N×N matrix never touches HBM. The result is exact.',
    build=['08_flash_attention'],
    sources='Dao et al. 2022, "FlashAttention" (Algorithm 1, Theorem 2, Fig. 2, §2.1 A100 figures); Dao 2023, "FlashAttention-2"; Shah et al. 2024, "FlashAttention-3"; Milakov & Gimelshein 2018, "Online normalizer calculation for softmax".',
    slides=[
        section('s-p1', 1, 'Attention is memory-bound', '''    <p class="lede">On an A100 (figures from the FlashAttention paper): HBM holds 40–80 GB at 1.5–2.0 TB/s. On-chip SRAM is 192 KB per streaming multiprocessor across 108 SMs, at around 19 TB/s. SRAM is roughly 10× faster and many orders of magnitude smaller. Standard attention runs as several separate passes, each reading from and writing to HBM. See <a href="../../gpu/03-memory-hierarchy/index.html">GPU deck 03</a> for the hierarchy.</p>
    <div class="visual">
      <svg id="pSvg" viewBox="0 0 660 190" role="img" aria-label="Standard attention passes over HBM"></svg>
    </div>'''),
        section('s-lim', 2, 'Why earlier speed-ups didn\'t help', '''    <div class="grid3">
      <div class="card d"><h3>Approximate attention cuts FLOPs</h3><p>Sparse and low-rank methods reduce computation but trade quality, and the FlashAttention abstract notes they "often do not achieve wall-clock speedup".</p></div>
      <div class="card b"><h3>FLOPs aren't the bottleneck</h3><p>Softmax, masking and dropout are element-wise over N² entries, so they do little arithmetic per byte moved. Their runtime is set by HBM bandwidth.</p></div>
      <div class="card c"><h3>Memory grows as N²</h3><p>Storing S and P for the backward pass needs N² values per head. At N = 65,536 in BF16 that is 8 GiB per head, per layer.</p></div>
    </div>'''),
        your_turn('s-turn', 'What does FlashAttention save?',
                  'FlashAttention actually does slightly <i>more</i> FLOPs than standard attention (it recomputes in the backward pass), yet it is several times faster. What does it reduce?',
                  ['The number of attention heads', 'Reads and writes to HBM', 'The precision of the softmax', 'The sequence length'], 1,
                  '<b>B.</b> It is IO-aware: tiling keeps S and P in SRAM, so HBM traffic drops. GPT-2 medium (N = 1,024), forward + backward on an A100: standard 66.6 GFLOPs, <b>40.3 GB</b> HBM, 41.7 ms; FlashAttention 75.2 GFLOPs, <b>4.4 GB</b>, <b>7.3 ms</b>.'),
        section('s-core', 4, 'Three ingredients', '''    <div class="grid3">
      <div class="card a"><h3>Tiling</h3><p>Split Q into row blocks and K, V into column blocks sized to fit in SRAM. For each pair of blocks compute S = QKᵀ/√d, then the partial softmax and partial output, without leaving the chip.</p></div>
      <div class="card b"><h3>Online softmax</h3><p>Softmax needs a row max and sum over <b>all</b> columns. Keep a running max m and sum ℓ per row; when a new block raises the max, rescale the old sum and the old partial output by e<sup>m_old − m_new</sup>. The result is exact.</p></div>
      <div class="card e"><h3>Recompute in the backward pass</h3><p>Don't store P. Save only the per-row softmax statistics (FA2: just the log-sum-exp) and recompute S and P block by block in the backward pass. Extra FLOPs, far less memory traffic, and memory linear in N.</p></div>
    </div>
''' + deep('IO complexity (FA1, Theorem 2)', '<p>With head dimension d and SRAM size M: standard attention needs <b>Θ(Nd + N²)</b> HBM accesses, while FlashAttention needs <b>Θ(N²d²/M)</b>. For typical d (64–128) and M (~100 KB), d² is many times smaller than M. The paper also proves no exact attention algorithm can asymptotically do better for all M.</p>')),
        section('s-how', 5, 'Online softmax, step by step', '''    <p class="lede">One row of 12 scores, processed in chunks of 4 as if they arrived from three K blocks. Watch the running max m and running sum ℓ. When the max increases, the old sum is multiplied by e<sup>m_old − m_new</sup>.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0"><button class="btn primary" id="osNext">next chunk</button><button class="btn" id="osReset">reset</button></div>
      <svg id="osSvg" viewBox="0 0 660 190" style="margin-top:10px" role="img" aria-label="Online softmax"></svg>
      <p class="readout" id="osOut"></p>
    </div>'''),
        section('s-how2', 5, 'Tiling: which blocks are touched', '''    <p class="lede">FlashAttention-2 order: for each Q block (outer loop, run in parallel across thread blocks), stream every K/V block through SRAM (inner loop). Step through and compare the elements moved to and from HBM with standard attention. Turn on causal: blocks entirely above the diagonal are skipped.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0"><button class="btn primary" id="tlNext">next tile</button><button class="btn" id="tlRun">run all</button><div class="seg" id="tlC"><button data-v="0" class="on">full</button><button data-v="1">causal</button></div></div>
      <svg id="tlSvg" viewBox="0 0 660 240" style="margin-top:10px" role="img" aria-label="Tiled attention"></svg>
      <p class="readout" id="tlOut"></p>
    </div>
    <p class="caption">N = 8 blocks of 128 rows, d = 64. Forward pass, element counts: standard ≈ 4Nd + 4N², tiled ≈ 2Nd + (N/B_r)·2Nd (the same traffic model as notebook 08).</p>'''),
        section('s-why', 6, 'Measured results, and FA1 → FA2 → FA3', '''    <div class="visual"><div id="fBars"></div><p class="caption">FA1 Fig. 2: GPT-2 medium attention (N = 1,024, d = 64, 16 heads, batch 64), forward + backward, A100.</p></div>
    <div class="visual scroll-x" style="margin-top:12px"><table class="tbl">
      <tr><th></th><th>Key change</th><th>Reported result</th></tr>
      <tr><td>FlashAttention (2022)</td><td>Tiling + online softmax + recompute; IO-aware, exact</td><td>15% faster BERT-large training vs MLPerf 1.1 record; 3× GPT-2 (1K); 2.4× Long Range Arena</td></tr>
      <tr><td>FlashAttention-2 (2023)</td><td>Fewer non-matmul FLOPs; parallelize over sequence (outer loop over Q blocks); split work across warps; rescale the output once at the end</td><td>~2× FA1; 50–73% of peak FLOPs on A100 (FA1: 25–40%); up to 225 TFLOPs/s training GPT models</td></tr>
      <tr><td>FlashAttention-3 (2024)</td><td>Hopper features: asynchronous Tensor Cores and TMA, warp specialization, interleaved matmul + softmax, FP8 with block quantization</td><td>1.5–2.0× on H100; up to 740 TFLOPs/s FP16 (~75%); ~1.2 PFLOPs/s FP8 with 2.6× lower error than a baseline FP8 attention</td></tr>
    </table></div>'''),
        myths('s-myth', [
            ('FlashAttention is an approximation of attention.', 'It is <b>exact</b>: the same outputs up to floating-point rounding (notebook 08: max error ~1e-15). Only the order of operations changes.'),
            ('FlashAttention makes attention O(N).', 'Compute is still O(N²). What becomes O(N) is the <b>extra memory</b>: no N×N matrix is stored. HBM traffic drops by a large factor but is still quadratic in N.'),
            ('It is faster because it does fewer FLOPs.', 'It does <b>more</b> FLOPs (75.2 vs 66.6 GFLOPs in Fig. 2) because of recomputation. It is faster because it moves about 9× fewer bytes.'),
        ]),
        check('s-check', [
            ('mcq', 'In the online softmax, when a new block has a larger maximum, what happens to the running sum ℓ?', ['It is reset to 0', 'It is multiplied by e^(m_old − m_new)', 'It is divided by the block size', 'Nothing'], 1, '<b>Rescaled by e^(m_old − m_new)</b>, and so is the partial output.'),
            ('open', 'What does FlashAttention store for the backward pass instead of P?', 'Only per-row softmax statistics (in FA2, just the log-sum-exp L = m + log ℓ). S and P are recomputed block by block in SRAM during the backward pass.'),
            ('open', 'Name two changes in FlashAttention-2 compared with FA1.', 'Parallelize over the sequence (outer loop over Q blocks, not K/V); fewer non-matmul FLOPs (rescale the output once at the end); better work split across warps; store only the log-sum-exp.'),
        ]),
    ],
    js=r'''
  (() => {
    const s = document.getElementById('pSvg'), steps = [['S = QKᵀ', 'read Q, K · write S (N²)'], ['P = softmax(S)', 'read S · write P (N²)'], ['O = PV', 'read P, V · write O']];
    steps.forEach(([a, b], i) => {
      const x = 20 + i * 215;
      svg('rect', { x, y: 30, width: 190, height: 50, rx: 9, class: 'f-a' }, s);
      svg('text', { x: x + 95, y: 61, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:700', text: a }, s);
      svg('text', { x: x + 95, y: 104, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: b }, s);
      svg('path', { d: `M${x + 95} 112 V140`, style: 'stroke:var(--d);stroke-width:2;stroke-dasharray:4 3' }, s);
    });
    svg('rect', { x: 20, y: 140, width: 620, height: 34, rx: 8, style: 'fill:var(--d-soft);stroke:var(--d)' }, s);
    svg('text', { x: 330, y: 162, 'text-anchor': 'middle', class: 't', text: 'HBM: every arrow is a round trip at 1.5–2.0 TB/s (each N² matrix is written, then read)' }, s);
  })();
  const X = [1.2, 0.3, 2.0, -0.5, 3.1, 0.8, 1.9, 2.5, 4.0, -1.0, 0.2, 3.6];
  let os = 0;
  const osDraw = () => {
    const s = clear(document.getElementById('osSvg')); let m = -Infinity, l = 0, msg = [];
    for (let c = 0; c < os; c++) {
      const ch = X.slice(c * 4, c * 4 + 4), mn = Math.max(m, ...ch), corr = isFinite(m) ? Math.exp(m - mn) : 0;
      l = l * corr + ch.reduce((a, x) => a + Math.exp(x - mn), 0);
      msg.push(`chunk ${c + 1}: max ${isFinite(m) ? m.toFixed(1) : '−∞'} → ${mn.toFixed(1)}${c && mn > m ? `, old sum × e^(${m.toFixed(1)}−${mn.toFixed(1)}) = ×${corr.toFixed(3)}` : ''}; ℓ = ${l.toFixed(3)}`);
      m = mn;
    }
    X.forEach((x, i) => {
      const done = i < os * 4, cx = 40 + i * 50;
      svg('rect', { x: cx - 20, y: 20, width: 40, height: 36, rx: 6, style: `fill:${done ? 'var(--a)' : 'var(--panel-2)'}` }, s);
      svg('text', { x: cx, y: 43, 'text-anchor': 'middle', class: 't', style: done ? 'fill:#fff;font-weight:600' : '', text: x.toFixed(1) }, s);
      if (i % 4 === 0) svg('text', { x: cx + 75, y: 74, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: 'chunk ' + (i / 4 + 1) }, s);
    });
    msg.forEach((t, k) => svg('text', { x: 20, y: 110 + k * 24, class: 't', style: 'font-size:12.5px', text: t }, s));
    const trueL = X.reduce((a, x) => a + Math.exp(x - 4.0), 0);
    document.getElementById('osOut').innerHTML = os < 3 ? `After ${os} of 3 chunks: m = ${isFinite(m) ? m.toFixed(1) : '−∞'}, ℓ = ${l.toFixed(3)}.` : `Done. m = ${m.toFixed(1)}, ℓ = ${l.toFixed(4)}; a two-pass softmax gives Σ e^(x − 4.0) = ${trueL.toFixed(4)}, identical. softmax(x)ᵢ = e^(xᵢ − m) / ℓ.`;
  };
  document.getElementById('osNext').addEventListener('click', () => { os = Math.min(3, os + 1); osDraw(); });
  document.getElementById('osReset').addEventListener('click', () => { os = 0; osDraw(); });
  osDraw();
  const NB = 8, Bsz = 128, dd = 64, N = NB * Bsz; let causal = false, tile = 0, timer = null;
  const tiles = () => { const t = []; for (let i = 0; i < NB; i++) for (let j = 0; j < NB; j++) if (!causal || j <= i) t.push([i, j]); return t; };
  const tlDraw = () => {
    const T = tiles(), s = clear(document.getElementById('tlSvg')), c = 24, x0 = 70, y0 = 20;
    for (let i = 0; i < NB; i++) for (let j = 0; j < NB; j++) {
      const k = T.findIndex(([a, b]) => a === i && b === j), done = k >= 0 && k < tile, cur = k === tile - 1, skip = k < 0;
      svg('rect', { x: x0 + j * c, y: y0 + i * c, width: c - 3, height: c - 3, rx: 3, style: `fill:${cur ? 'var(--b)' : done ? 'var(--a)' : skip ? 'var(--panel)' : 'var(--panel-2)'};${skip ? 'stroke:var(--line);stroke-dasharray:2 2' : ''}` }, s);
    }
    svg('text', { x: x0 + NB * c / 2, y: y0 + NB * c + 18, 'text-anchor': 'middle', class: 'tm', text: 'K/V blocks (inner loop) →' }, s);
    svg('text', { x: x0 - 8, y: y0 + NB * c / 2, 'text-anchor': 'end', class: 'tm', text: 'Q ↓' }, s);
    const rowsDone = new Set(T.slice(0, tile).map(([i]) => i)).size;
    const flash = rowsDone * Bsz * dd * 2 + T.slice(0, tile).length * Bsz * dd * 2;
    const std = 4 * N * dd + 4 * N * N * (causal ? 0.5 : 1);
    [['tiles computed', `${tile} / ${T.length}`], ['tiled HBM traffic so far', Deck.fmt(flash) + ' elements'], ['standard, whole pass', Deck.fmt(std) + ' elements'], ['N×N kept in HBM', 'never']].forEach(([a, b], k) => {
      svg('text', { x: 340, y: 50 + k * 34, class: 'tm', text: a }, s); svg('text', { x: 640, y: 50 + k * 34, 'text-anchor': 'end', class: 't', style: 'font-weight:700', text: b }, s);
    });
    document.getElementById('tlOut').innerHTML = tile === T.length ? `Finished: tiled ≈ <b>${Deck.fmt(flash)}</b> vs standard ≈ <b>${Deck.fmt(std)}</b> elements moved (${(std / flash).toFixed(1)}× less)${causal ? `; ${NB * NB - T.length} future blocks skipped` : ''}.` : 'Each orange tile: load Q_i (once per row), K_j and V_j into SRAM, update m, ℓ and Õ for that row block.';
  };
  document.getElementById('tlNext').addEventListener('click', () => { tile = Math.min(tiles().length, tile + 1); tlDraw(); });
  document.getElementById('tlRun').addEventListener('click', () => { clearInterval(timer); timer = setInterval(() => { tile++; if (tile >= tiles().length) { tile = tiles().length; clearInterval(timer); } tlDraw(); }, 70); });
  Deck.seg('tlC', v => { causal = v === '1'; tile = 0; clearInterval(timer); tlDraw(); });
  Deck.hbars(document.getElementById('fBars'), [
    { label: 'GFLOPs, standard', value: 66.6, color: 'var(--faint)', text: '66.6' }, { label: 'GFLOPs, Flash', value: 75.2, color: 'var(--faint)', text: '75.2 (more!)' },
    { label: 'HBM R/W, standard', value: 40.3, color: 'var(--d)', text: '40.3 GB' }, { label: 'HBM R/W, Flash', value: 4.4, color: 'var(--e)', text: '4.4 GB' },
    { label: 'runtime, standard', value: 41.7, color: 'var(--d)', text: '41.7 ms' }, { label: 'runtime, Flash', value: 7.3, color: 'var(--e)', text: '7.3 ms' }], { max: 80 });
''',
    line='FlashAttention computes exact attention tile by tile in SRAM with an online softmax, so the N×N matrix never touches HBM: more FLOPs, far fewer bytes, much faster.',
    explain='Standard attention writes the N by N score matrix to GPU high-bandwidth memory, reads it back for the softmax, writes the probabilities and reads them again, and at long sequences that traffic, not arithmetic, sets the runtime. FlashAttention loads blocks of Q, K and V into on-chip SRAM and computes scores, softmax and output there. It combines blocks with an online softmax that keeps a running max and sum per row and rescales when the max grows. The backward pass recomputes scores from saved statistics instead of storing them. It is exact, uses memory linear in N, and on GPT-2 cut HBM traffic from 40 to 4.4 GB. FlashAttention-2 reordered the loops for parallelism; FlashAttention-3 uses Hopper\'s asynchrony and FP8.',
    recap=[('Problem', 'N×N intermediates make attention memory-bound and O(N²) in memory.'), ('Core idea', 'tiling + online softmax + recompute: exact, linear memory, ~9× less HBM traffic.'), ('Versions', 'FA2: loop order and parallelism (50–73% of peak); FA3: Hopper async + FP8 (740 TFLOPs/s).')],
)

# =============================================================== 10
DECKS['10-mixture-of-experts'] = dict(
    title='Mixture of Experts', h1='Mixture of Experts (MoE)',
    sub='Replace the dense FFN with many expert FFNs and a router that sends each token to a few of them: more parameters without more compute per token, and the balancing problems that come with it.',
    prob='In a dense model every token uses every parameter, so adding parameters (more knowledge) adds FLOPs to every token in training and serving.',
    core='Swap the FFN for <b>N experts</b> plus a <b>router</b>. Each token is processed by its <b>top-k</b> experts, weighted by the router. Parameters scale with N; compute scales with k. An auxiliary loss keeps the experts evenly used.',
    build=['09_moe_router'],
    sources='Fedus et al. 2022, "Switch Transformers" (eq. 3–6, α = 10⁻²); Jiang et al. 2024, "Mixtral of Experts" (§2.1, Fig. 8); DeepSeek-AI 2024, DeepSeek-V2 (§2.2, DeepSeekMoE); Shazeer et al. 2017 (sparsely-gated MoE).',
    slides=[
        section('s-p1', 1, 'Parameters vs compute per token', '''    <p class="lede">Total parameters (what must be stored) vs active parameters per token (roughly what each token computes with), from the papers. In a dense model they are equal; in an MoE they come apart.</p>
    <div class="visual"><div id="mBars"></div></div>
    <p class="caption">Mixtral 8x7B: 47B total, 13B active. DeepSeek-V2: 236B total, 21B active. Llama 3 70B: dense, so total = active.</p>'''),
        section('s-lim', 2, 'Why not just make the dense model bigger?', '''    <div class="grid3">
      <div class="card d"><h3>Every FLOP is paid by every token</h3><p>Doubling a dense model roughly doubles the training and inference compute per token, even for easy tokens.</p></div>
      <div class="card b"><h3>Knowledge needs parameters</h3><p>Many capabilities improve with parameter count, but most tokens only need a small part of the model's knowledge at a time.</p></div>
      <div class="card c"><h3>Serving cost scales with active compute</h3><p>Decode time per token is driven by the weights each token touches. Fewer active parameters means cheaper tokens, though the memory to hold all experts remains.</p></div>
    </div>'''),
        your_turn('s-turn', 'Which costs does MoE cut?',
                  'Mixtral has 47B total parameters and 13B active per token. Compared with a dense 47B model, what does it save?',
                  ['GPU memory for weights', 'FLOPs per token', 'Both equally', 'Neither'], 1,
                  '<b>B.</b> Each token runs through only 2 of 8 experts per layer, so compute per token is like a ~13B model. But all 47B parameters must still be held in memory, and routing adds communication when experts are spread over GPUs.'),
        section('s-core', 4, 'Router + experts', '''    <div class="grid3">
      <div class="card a"><h3>Experts</h3><p>N independent FFNs (SwiGLU in Mixtral) replace the single FFN in each layer. Attention stays shared and dense.</p></div>
      <div class="card b"><h3>Router</h3><p>A linear layer gives each token a logit per expert. Mixtral: G(x) = Softmax(TopK(x·W_g)), keeping the top 2 logits and softmaxing over just those. Switch Transformer routes to <b>one</b> expert (k = 1).</p></div>
      <div class="card e"><h3>Combine</h3><p>y = Σ over the top-k experts of G(x)ᵢ · Eᵢ(x). Different tokens, even in the same sequence, use different experts, and the choice can change at every layer.</p></div>
    </div>
''' + deep('DeepSeekMoE: many small experts plus shared ones', '<p>DeepSeek-V2 splits experts more finely and isolates some as <b>shared</b> experts that every token uses: each MoE layer has <b>2 shared + 160 routed</b> experts, with <b>6</b> routed experts active per token (236B total, 21B active). Fine-grained experts give the router more combinations to choose from; shared experts hold common knowledge so routed ones don\'t each have to duplicate it.</p>')),
        section('s-how', 5, 'Routing six tokens', '''    <p class="lede">Each token's router picks its top-k experts; the gate weights are printed on the token and drawn as line thickness. Switch between top-1 (Switch Transformer) and top-2 (Mixtral). The bars show how many tokens each expert receives: that load is what has to be balanced.</p>
    <div class="visual">
      <div class="seg" id="kSeg"><button data-v="1">top-1</button><button data-v="2" class="on">top-2</button></div>
      <svg id="rSvg" viewBox="0 0 660 250" style="margin-top:10px" role="img" aria-label="Token to expert routing"></svg>
    </div>
    <p class="caption">Illustrative router logits (fixed random values), 8 experts.</p>'''),
        section('s-how2', 5, 'Load balancing and capacity', '''    <p class="lede">4,096 tokens, 8 experts, top-1 routing. Increase the router's skew towards some experts and watch three things: each expert's share of tokens, the Switch auxiliary loss, and the tokens dropped when each expert has a fixed capacity of 1.25 × (tokens / experts).</p>
    <div class="visual">
      <div class="controls" style="margin-top:0"><label class="ctl">Router skew <input type="range" id="bS" min="0" max="3" step="0.1" value="1.5"> <output id="bSo"></output></label></div>
      <div id="bBars" style="margin-top:12px"></div>
      <div class="grid3" style="margin-top:12px">
        <div class="stat"><div class="num" id="bL"></div><div class="lbl">aux loss α·N·Σ fᵢPᵢ (min 0.010)</div></div>
        <div class="stat"><div class="num" id="bM"></div><div class="lbl">busiest expert's share</div></div>
        <div class="stat"><div class="num" id="bD" style="color:var(--d)"></div><div class="lbl">tokens dropped</div></div>
      </div>
    </div>
''' + deep('The Switch Transformer loss', '<p>loss = α · N · Σᵢ fᵢ · Pᵢ, where fᵢ is the fraction of tokens whose top-1 expert is i and Pᵢ is the average router probability for expert i. Both should be 1/N, and the loss is minimized under uniform routing. The paper uses α = 10⁻²: "sufficiently large to ensure load balancing while small enough to not to overwhelm the primary cross-entropy objective". Expert capacity = (tokens per batch / number of experts) × capacity factor; overflow tokens skip the expert through the residual connection.</p>')),
        section('s-why', 6, 'Why MoE works, and what it costs', '''    <div class="grid2">
      <div class="card a"><h3>Parameters without FLOPs</h3><p>Switch Transformer reports up to <b>7×</b> faster pre-training than T5-Base/Large at the same compute, and a 4× speedup over T5-XXL with its trillion-parameter model.</p></div>
      <div class="card e"><h3>Experts specialize, just not by topic</h3><p>Mixtral's analysis: expert choice "appears to be more aligned with the syntax rather than the domain", especially in the first and last layers. Don't expect a "math expert".</p></div>
      <div class="card d"><h3>Memory and communication</h3><p>All experts must be in memory. Spread across GPUs (expert parallelism), every MoE layer needs an all-to-all exchange to send tokens to their experts and back.</p></div>
      <div class="card b"><h3>Balance and stability</h3><p>Without a balancing loss the router collapses onto a few experts. Fixed capacity drops tokens when routing is uneven, and Switch needed extra tricks to train stably in bfloat16.</p></div>
    </div>'''),
        myths('s-myth', [
            ('Each expert is a domain specialist: one for code, one for maths.', 'Mixtral\'s routing analysis found no obvious topic-based assignment. Routing follows <b>syntax</b> and token-level patterns more than domains.'),
            ('A 47B MoE with 13B active parameters runs like a 13B model.', 'Compute per token is close to 13B, but memory must hold <b>all 47B</b>, and expert routing adds communication. On memory-bound hardware it does not behave like a 13B model.'),
            ('MoE replaces the whole Transformer layer.', 'Usually only the <b>FFN</b> becomes experts. Attention, norms and embeddings stay dense and shared.'),
        ]),
        check('s-check', [
            ('mcq', 'In Mixtral, how are the gate weights computed?', ['Softmax over all 8 logits', 'Softmax over the top-2 logits only', 'Uniform 0.5 each', 'Sigmoid of each logit'], 1, '<b>Softmax over the top-2 logits</b>: G(x) = Softmax(TopK(x·W_g)).'),
            ('open', 'What value does the Switch auxiliary loss take under perfectly uniform routing, and under total collapse onto one expert?', 'Uniform: fᵢ = Pᵢ = 1/N, so the loss = α·N·N·(1/N²) = <b>α</b>. Collapse: f = P = 1 for one expert, so the loss = <b>α·N</b>.'),
            ('open', 'Why do MoE models drop tokens, and what happens to a dropped token?', 'Each expert has a fixed buffer (capacity = tokens/experts × capacity factor) so shapes stay static. Tokens routed to a full expert are dropped from that layer\'s FFN and carried forward by the residual connection.'),
        ]),
    ],
    js=r'''
  Deck.hbars(document.getElementById('mBars'), [
    { label: 'Mixtral 8x7B total', value: 47, color: 'var(--faint)', text: '47B' }, { label: 'Mixtral active / token', value: 13, color: 'var(--a)', text: '13B' },
    { label: 'DeepSeek-V2 total', value: 236, color: 'var(--faint)', text: '236B' }, { label: 'DeepSeek-V2 active / token', value: 21, color: 'var(--a)', text: '21B' },
    { label: 'Llama 3 70B (dense)', value: 70, color: 'var(--b)', text: '70B = 70B' }], { max: 240 });
  let seed = 7; const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  const gauss = () => { const u = Math.max(1e-9, rnd()), v = rnd(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
  const LOG = [...Array(6)].map(() => [...Array(8)].map(() => gauss() * 1.4));
  Deck.seg('kSeg', v => {
    const k = +v, s = clear(document.getElementById('rSvg')), load = Array(8).fill(0);
    LOG.forEach((row, t) => {
      const idx = row.map((x, i) => [x, i]).sort((a, b) => b[0] - a[0]).slice(0, k), mx = idx[0][0], ex = idx.map(([x]) => Math.exp(x - mx)), sum = ex.reduce((a, b) => a + b);
      const ty = 30 + t * 36;
      svg('rect', { x: 10, y: ty - 13, width: 210, height: 26, rx: 6, style: 'fill:var(--b)' }, s);
      svg('text', { x: 115, y: ty + 5, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:600;font-size:12px', text: `token ${t + 1} → ` + idx.map(([x, e], j) => `E${e + 1} ${(ex[j] / sum).toFixed(2)}`).join(' · ') }, s);
      idx.forEach(([x, e], j) => { load[e]++; const ey = 22 + e * 27; svg('line', { x1: 220, y1: ty, x2: 420, y2: ey + 10, style: `stroke:var(--a);stroke-width:${1 + 7 * ex[j] / sum};opacity:.85` }, s); });
    });
    for (let e = 0; e < 8; e++) {
      const ey = 22 + e * 27; svg('rect', { x: 420, y: ey, width: 80, height: 21, rx: 5, class: 'f-a' }, s);
      svg('text', { x: 460, y: ey + 15, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:12px', text: 'expert ' + (e + 1) }, s);
      svg('rect', { x: 510, y: ey + 3, width: load[e] * 22, height: 15, rx: 3, style: 'fill:var(--c)' }, s);
      svg('text', { x: 516 + load[e] * 22, y: ey + 15, class: 'tm', style: 'font-size:11px', text: load[e] }, s);
    }
  });
  const TOK = 4096, NE = 8; seed = 11; const BASE = [...Array(TOK)].map(() => [...Array(NE)].map(gauss));
  Deck.bind(['bS'], () => {
    const sk = Deck.val('bS'); Deck.out('bSo', sk.toFixed(1));
    const f = Array(NE).fill(0), P = Array(NE).fill(0), assign = [];
    BASE.forEach(row => {
      const lg = row.map((x, i) => x + sk * (1 - i / (NE - 1))), mx = Math.max(...lg), ex = lg.map(x => Math.exp(x - mx)), sm = ex.reduce((a, b) => a + b);
      ex.forEach((e, i) => P[i] += e / sm / TOK); const a = lg.indexOf(mx); f[a] += 1 / TOK; assign.push(a);
    });
    const cap = Math.floor(TOK / NE * 1.25), used = Array(NE).fill(0); let drop = 0; assign.forEach(a => { if (used[a] < cap) used[a]++; else drop++; });
    Deck.out('bL', (0.01 * NE * f.reduce((a, x, i) => a + x * P[i], 0)).toFixed(4)); Deck.out('bM', (100 * Math.max(...f)).toFixed(0) + '%'); Deck.out('bD', (100 * drop / TOK).toFixed(1) + '%');
    Deck.hbars(document.getElementById('bBars'), f.map((x, i) => ({ label: 'expert ' + (i + 1), value: x, color: x * TOK > cap ? 'var(--d)' : 'var(--a)', text: (100 * x).toFixed(1) + '%' })), { max: 0.5 });
  });
''',
    line='MoE swaps the FFN for many experts and a top-k router: parameters grow with the number of experts, compute with k, and a balancing loss keeps the experts evenly used.',
    explain='In a dense model every token uses every parameter. A Mixture-of-Experts layer replaces the FFN with N expert FFNs and a router that sends each token to its top k, weighting their outputs by a softmax over the selected logits. Mixtral has 8 experts with top-2 routing, 47 billion parameters in total but about 13 billion active per token; DeepSeek-V2 uses 160 fine-grained routed experts plus 2 shared ones. Compute per token drops, but all experts must sit in memory and tokens are exchanged between GPUs. Routers tend to collapse, so Switch Transformer adds an auxiliary loss, alpha times N times the sum of f-i times P-i, that is minimized by uniform routing. Fixed expert capacity drops overflow tokens.',
    recap=[('Problem', 'dense models pay for every parameter on every token.'), ('Core idea', 'router + N experts, top-k per token; params ∝ N, FLOPs ∝ k.'), ('Costs', 'all experts in memory, all-to-all communication, balancing loss and capacity.')],
)

# =============================================================== 11
DECKS['11-putting-it-together'] = dict(
    title='Putting It Together', h1='Putting it together',
    sub='Build a modern decoder from its parts, compute its size from a config, and practise naming the design choices behind real models.',
    prob='Knowing each component separately isn\'t enough. You need to read a model description, reconstruct the block, estimate its size and costs, and explain why each choice was made.',
    core='A modern LLM layer = <b>RMSNorm → attention (GQA + RoPE, FlashAttention kernel) → residual → RMSNorm → SwiGLU FFN (or MoE) → residual</b>, stacked L times between a token embedding and a final RMSNorm + output head.',
    build=['10_llama_block'],
    sources='Touvron et al. 2023 (LLaMA, Llama 2); Llama Team 2024 (Llama 3 Table 3); Meta-Llama-3-8B config.json; Jiang et al. 2023 (Mistral 7B Table 1); Kaplan et al. 2020 (≈2N FLOPs per token for the forward pass).',
    slides=[
        section('s-p1', 1, 'The whole block on one screen', '''    <p class="lede">One Llama 3 layer, with each part labelled by the problem it solves and the deck that explains it. Hover or tap a part.</p>
    <div class="visual">
      <svg id="bSvg" viewBox="0 0 660 330" role="img" aria-label="Modern decoder block"></svg>
      <div class="infobox" id="bInfo" style="background:var(--panel-2);border-radius:10px;padding:12px 14px;margin-top:10px;font-size:14px;color:var(--muted)">Tap a part of the block.</div>
    </div>'''),
        section('s-lim', 2, 'Where people get stuck', '''    <div class="grid3">
      <div class="card d"><h3>Mixing up what is cached</h3><p>K and V (after RoPE) are cached, Q isn't. With GQA only the K/V heads are cached. With MLA it's the latent plus the RoPE key.</p></div>
      <div class="card b"><h3>Counting parameters wrongly</h3><p>Forgetting that GQA shrinks Wk and Wv, that SwiGLU has three matrices, or that untied embeddings count twice.</p></div>
      <div class="card c"><h3>Confusing kernel and architecture</h3><p>FlashAttention doesn't change the model; it computes the same function faster. RoPE scaling and sliding windows <b>do</b> change what the model computes.</p></div>
    </div>'''),
        your_turn('s-turn', 'Name the recipe',
                  'A config says: num_attention_heads 32, num_key_value_heads 8, hidden_act "silu", intermediate_size 14336, rope_theta 1000000, sliding_window 4096. Which features does this model use?',
                  ['MHA, GELU, learned positions', 'GQA, SwiGLU, RoPE (large base), sliding-window attention', 'MQA, ReLU, ALiBi', 'MLA, SwiGLU, NTK scaling'], 1,
                  '<b>B.</b> 8 K/V heads for 32 query heads is GQA; silu with an intermediate size is a SwiGLU FFN; rope_theta is the RoPE base; sliding_window means SWA. (A hypothetical config: always read the actual model card.)'),
        section('s-core', 4, 'The checklist for any model description', '''    <div class="visual scroll-x"><table class="tbl">
      <tr><th>Question</th><th>Where to look</th><th>Typical modern answer</th><th>Deck</th></tr>
      <tr><td>Stack and mask?</td><td>architecture name</td><td>decoder-only, causal (+ document mask for packing)</td><td>06</td></tr>
      <tr><td>Norm placement and type?</td><td><code>rms_norm_eps</code></td><td>pre-norm RMSNorm + final norm</td><td>02</td></tr>
      <tr><td>Position encoding?</td><td><code>rope_theta</code>, <code>rope_scaling</code></td><td>RoPE, base 10K–1M, maybe YaRN/linear scaling</td><td>03, 07</td></tr>
      <tr><td>K/V sharing?</td><td><code>num_key_value_heads</code></td><td>GQA with 8 K/V heads; MLA in DeepSeek</td><td>05</td></tr>
      <tr><td>FFN?</td><td><code>hidden_act</code>, <code>intermediate_size</code></td><td>SwiGLU, hidden ≈ 2.7–3.5·d</td><td>04</td></tr>
      <tr><td>Sparse?</td><td><code>num_local_experts</code>, <code>num_experts_per_tok</code></td><td>dense, or MoE with top-k routing</td><td>10</td></tr>
      <tr><td>Long-context mechanism?</td><td><code>sliding_window</code>, context length</td><td>long-context training; optional SWA</td><td>07, 08</td></tr>
    </table></div>'''),
        section('s-how', 5, 'Size calculator', '''    <p class="lede">Pick a preset or move the sliders. Parameters are counted exactly as in notebook 10 (Llama 2 7B gives 6,738,415,616; Llama 3 8B gives 8,030,261,248). KV cache is per token in BF16. Forward FLOPs per token ≈ 2 × parameters, ignoring attention over the context.</p>
    <div class="visual">
      <div class="seg" id="zSeg"><button data-v="32000,4096,32,32,32,11008" >Llama 2 7B</button><button data-v="128256,4096,32,32,8,14336" class="on">Llama 3 8B</button><button data-v="32000,4096,32,32,8,14336">Mistral 7B</button><button data-v="128256,8192,80,64,8,28672">Llama 3 70B</button></div>
      <div class="controls">
        <label class="ctl">d <input type="range" id="zD" min="1024" max="16384" step="512" value="4096"> <output id="zDo"></output></label>
        <label class="ctl">layers <input type="range" id="zL" min="8" max="128" step="1" value="32"> <output id="zLo"></output></label>
        <label class="ctl">K/V heads <input type="range" id="zK" min="1" max="64" step="1" value="8"> <output id="zKo"></output></label>
        <label class="ctl">FFN hidden <input type="range" id="zH" min="2048" max="57344" step="256" value="14336"> <output id="zHo"></output></label>
      </div>
      <div class="grid4" style="margin-top:12px">
        <div class="stat"><div class="num" id="zP" style="color:var(--a)"></div><div class="lbl">parameters</div></div>
        <div class="stat"><div class="num" id="zKV"></div><div class="lbl">KV cache / token</div></div>
        <div class="stat"><div class="num" id="zF"></div><div class="lbl">forward FLOPs / token (≈2N)</div></div>
        <div class="stat"><div class="num" id="zW"></div><div class="lbl">BF16 weights</div></div>
      </div>
      <div id="zBars" style="margin-top:12px"></div>
    </div>
    <p class="caption">Head dimension is fixed at 128 for the calculator (true for all four presets). Query heads = d / 128. Memory units are binary (KB = KiB, GB = GiB).</p>'''),
        section('s-how2', 5, 'Follow one token through the stack', '''    <div class="grid3">
      <div class="card a"><h3>1. Embed</h3><p>Token id → row of the embedding table (d numbers). No position vector is added.</p></div>
      <div class="card b"><h3>2. Attention sub-layer</h3><p>RMSNorm → q, k, v projections (fewer K/V heads) → RoPE on q and k → append k, v to the KV cache → attention over the cache with FlashAttention → Wo → add to the stream.</p></div>
      <div class="card c"><h3>3. FFN sub-layer</h3><p>RMSNorm → SwiGLU (or route to top-k experts) → add to the stream.</p></div>
      <div class="card e"><h3>4. Repeat L times</h3><p>The residual stream accumulates every layer's contribution; nothing renormalizes it along the way.</p></div>
      <div class="card a"><h3>5. Output</h3><p>Final RMSNorm → output head (vocab logits) → sample the next token, which becomes the next input.</p></div>
      <div class="card b"><h3>6. Long inputs</h3><p>Positions beyond the trained range need RoPE scaling or long-context training; a sliding window caps the cache.</p></div>
    </div>'''),
        section('s-why', 6, 'Why the pieces fit together', '''    <div class="grid2">
      <div class="card a"><h3>They solve different problems</h3><p>Stability (pre-norm), cost per op (RMSNorm), position (RoPE), FFN quality (SwiGLU), serving memory (GQA/MLA), memory traffic (FlashAttention), parameters per FLOP (MoE). Each fix is local, so none conflicts with the others.</p></div>
      <div class="card e"><h3>The few interactions are known</h3><p>RoPE plus MLA needs decoupled RoPE. RoPE plus long context needs scaling. MoE plus GQA is fine (Mixtral). Pre-norm needs a final norm.</p></div>
      <div class="card b"><h3>Inference shaped the design</h3><p>The KV cache explains GQA, MLA, sliding windows and why decoder-only won. Active parameters explain MoE. Memory traffic explains FlashAttention.</p></div>
      <div class="card c"><h3>What comes next</h3><p>Training these models at scale (data, scaling laws, parallelism) and aligning them (post-training) are the next topics in this guide.</p></div>
    </div>'''),
        myths('s-myth', [
            ('Parameter count tells you serving cost.', 'Serving cost also depends on the KV cache (set by K/V heads, layers and context length) and, for MoE, on <b>active</b> rather than total parameters.'),
            ('Two models with the same parameters have the same architecture.', 'Llama 2 7B and Llama 3 8B are similar in size but differ in K/V heads (32 vs 8), FFN width (11,008 vs 14,336), vocabulary (32K vs 128K) and RoPE base (10K vs 500K).'),
            ('FlashAttention is part of the model architecture.', 'It is a <b>kernel</b>. Swapping it for standard attention gives the same outputs, only slower and using more memory.'),
        ]),
        check('s-check', [
            ('open', 'Write the two residual updates of a Llama block, naming every component.', 'h = x + Wo·FlashAttn(RoPE(Wq·RMSNorm(x)), RoPE(Wk·RMSNorm(x)), Wv·RMSNorm(x)) with GQA K/V heads; out = h + W_down(SiLU(W_gate·RMSNorm(h)) ⊙ W_up·RMSNorm(h)).'),
            ('mcq', 'Llama 3 8B: about what share of parameters is in the FFNs?', ['~15%', '~40%', '~70%', '~95%'], 2, '<b>~70%</b> (5.64B of 8.03B). Attention ~17% thanks to GQA, embeddings + head ~13% because of the 128K vocabulary.'),
            ('open', 'KV cache per token for Llama 3 8B in BF16?', '2 (K and V) × 32 layers × 8 K/V heads × 128 dims × 2 bytes = <b>131,072 bytes = 128 KiB</b>.'),
        ]),
    ],
    js=r'''
  const PARTS = [
    ['emb', 'token embedding', 290, 'Token id → vector of d numbers. With RoPE there is no position vector here. Llama 3: 128,256 × 4,096 (≈525M parameters).'],
    ['n1', 'RMSNorm', 245, 'Pre-norm: normalize only the input to the sub-layer, dividing by the root mean square. (Deck 02)'],
    ['att', 'GQA attention + RoPE (FlashAttention)', 200, '32 query heads, 8 K/V heads (GQA, deck 05). RoPE rotates q and k (deck 03). Computed with a tiled, exact kernel (deck 09). K and V go into the KV cache.'],
    ['r1', '+ residual', 155, 'Add the attention output to the stream. The stream itself is never normalized.'],
    ['n2', 'RMSNorm', 120, 'Second pre-norm, before the FFN.'],
    ['ffn', 'SwiGLU FFN (or MoE experts)', 75, 'SiLU-gated FFN, 14,336 hidden (deck 04); in MoE models, a router picks the top-k expert FFNs (deck 10). About 70% of the parameters.'],
    ['r2', '+ residual', 30, 'Add the FFN output. Repeat the whole block L times; then a final RMSNorm and the output head.'],
  ];
  (() => {
    const s = document.getElementById('bSvg');
    PARTS.forEach(([k, label, y, info], i) => {
      const g = svg('g', { style: 'cursor:pointer' }, s), wide = k === 'att' || k === 'ffn';
      svg('rect', { x: wide ? 130 : 200, y, width: wide ? 400 : 260, height: 34, rx: 8, class: ['emb', 'r1', 'r2'].includes(k) ? 'f-panel' : k === 'att' ? 'f-c' : k === 'ffn' ? 'f-a' : 'f-e', style: 'stroke:var(--line)' }, g);
      svg('text', { x: 330, y: y + 22, 'text-anchor': 'middle', class: 't', style: ['emb', 'r1', 'r2'].includes(k) ? 'font-weight:600' : 'fill:#fff;font-weight:600', text: label }, g);
      const show = () => { document.getElementById('bInfo').innerHTML = `<b>${label}</b>: ${info}`; };
      g.addEventListener('mouseenter', show); g.addEventListener('click', show);
    });
    svg('text', { x: 560, y: 180, class: 'tm', style: 'font-size:11px', text: '× L layers' }, s);
    svg('line', { x1: 550, x2: 550, y1: 30, y2: 280, style: 'stroke:var(--faint);stroke-dasharray:4 4' }, s);
  })();
  const count = (V, d, L, H, G, h) => { const dh = d / H; return V * d * 2 + L * (2 * d * d + 2 * d * G * dh + 3 * d * h + 2 * d) + d; };
  let vocab = 128256;
  const calc = () => {
    const d = Deck.val('zD'), L = Deck.val('zL'), H = d / 128; let G = Deck.val('zK'); const h = Deck.val('zH');
    if (G > H) G = H; while (H % G) G--;
    Deck.out('zDo', d.toLocaleString()); Deck.out('zLo', L); Deck.out('zKo', G + ` (of ${H} q heads)`); Deck.out('zHo', h.toLocaleString());
    const P = count(vocab, d, L, H, G, h), emb = 2 * vocab * d, attn = L * (2 * d * d + 2 * d * G * 128), ffn = L * 3 * d * h;
    Deck.out('zP', (P / 1e9).toFixed(2) + 'B'); Deck.out('zKV', Deck.bytes(2 * L * G * 128 * 2)); Deck.out('zF', (2 * P / 1e9).toFixed(1) + ' GFLOP'); Deck.out('zW', Deck.bytes(2 * P));
    Deck.hbars(document.getElementById('zBars'), [
      { label: 'FFN', value: ffn, color: 'var(--a)', text: (100 * ffn / P).toFixed(1) + '%' },
      { label: 'attention', value: attn, color: 'var(--c)', text: (100 * attn / P).toFixed(1) + '%' },
      { label: 'embeddings + head', value: emb, color: 'var(--b)', text: (100 * emb / P).toFixed(1) + '%' }], { max: P });
  };
  Deck.seg('zSeg', v => {
    const [V, d, L, H, G, h] = v.split(',').map(Number); vocab = V;
    document.getElementById('zD').value = d; document.getElementById('zL').value = L; document.getElementById('zK').value = G; document.getElementById('zH').value = h; calc();
  });
  Deck.bind(['zD', 'zL', 'zK', 'zH'], calc);
''',
    line='A modern LLM layer is RMSNorm → GQA attention with RoPE → residual → RMSNorm → SwiGLU (or MoE) → residual, computed with FlashAttention, and its size and cache follow directly from the config.',
    explain='Every modern open LLM is the same template. A token embedding with no position vector; then L identical blocks, each a pre-norm RMSNorm, grouped-query attention with RoPE on queries and keys computed by a FlashAttention kernel, a residual add, another RMSNorm, a SwiGLU feed-forward or a set of routed experts, and another residual add; then a final RMSNorm and the output head. Parameters, KV cache per token and FLOPs follow directly from the config: Llama 3 8B has 8.03 billion parameters, 70% of them in FFNs, and a 128 KiB KV cache per token. Each design choice maps to a specific scaling problem.',
    recap=[('Template', 'embed → L × [RMSNorm, GQA+RoPE, +, RMSNorm, SwiGLU/MoE, +] → RMSNorm → head.'), ('Sizes', 'Llama 3 8B: 8.03B params, ~70% FFN, 128 KiB KV per token.'), ('Reading configs', 'num_key_value_heads, rope_theta, intermediate_size, hidden_act, sliding_window, experts.')],
)
