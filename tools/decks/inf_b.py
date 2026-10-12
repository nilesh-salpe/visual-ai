from tool import section, your_turn, myths, check, mcq, openq

DECKS = {}

# =============================================================== 06
DECKS['06-speculative-decoding'] = dict(
    title='Speculative Decoding', h1='Speculative decoding',
    sub='Draft several tokens with a small model, verify them all in one pass of the large model, and keep exactly the large model\'s output distribution (Leviathan et al., ICML 2023; Chen et al., 2023).',
    prob='Decode produces one token per full read of the model\'s weights. The GPU waits on memory while its compute sits mostly idle, and tokens can\'t be generated in parallel because each depends on the last.',
    core='A cheap <b>draft</b> model proposes γ tokens; the target model <b>scores all of them in one forward pass</b>; a modified rejection rule accepts a prefix of them, so the output distribution is unchanged.',
    build=['09_speculative_sampling'],
    slides=[
        section('s-p1', 1, 'Decode is slow for a reason that has nothing to do with compute', '''    <p class="lede">At batch 1, every decode step reads all the weights, about 140 GB for a 70B model in BF16, to produce <b>one</b> token. Scoring several tokens in the same pass costs almost the same, because the memory read is the bottleneck, not the math (GPU deck 02).</p>
    <div class="takeaway">If we knew which tokens to score, we could check several of them for about the price of one step.</div>'''),
        section('s-lim', 2, 'The obvious shortcuts break something', '''    <div class="grid3">
      <div class="card d"><h3>Just use a small model</h3><p>Fast, but the quality is the small model's, not the large one's.</p></div>
      <div class="card b"><h3>Generate in parallel</h3><p>Impossible directly: token t+1 depends on token t (autoregression).</p></div>
      <div class="card c"><h3>Bigger batches</h3><p>Help throughput across users, but don't make <em>one</em> user's stream faster.</p></div>
    </div>'''),
        your_turn('s-turn', 'Faster, without changing the output',
                  'How can a large model generate faster without changing what it would output?',
                  ['Replace it with a distilled small model', 'Let a small model draft several tokens and have the large model verify them all in one parallel pass', 'Skip every other layer', 'Use greedy decoding only'], 1,
                  '<b>B.</b> Verification of γ drafted positions happens in <b>one</b> target forward pass. With the modified rejection rule, the accepted tokens are distributed exactly as if the target had sampled them itself.'),
        section('s-core', 4, 'Draft, verify, accept or reject', '''    <div class="grid2">
      <div class="card a"><h3>1. Draft</h3><p>The draft model q samples γ tokens autoregressively. It's cheap because it's small (often about two orders of magnitude smaller, per Leviathan et al.).</p></div>
      <div class="card b"><h3>2. Verify</h3><p>The target model p scores all γ positions plus one extra in a single forward pass.</p></div>
      <div class="card e"><h3>3. Accept or reject</h3><p>Accept draft x with probability min(1, p(x)/q(x)). On the first rejection, sample a replacement from norm(max(0, p − q)) and stop.</p></div>
      <div class="card c"><h3>4. Bonus token</h3><p>If all γ are accepted, sample one more token from p for free. Each pass yields 1 to γ+1 tokens.</p></div>
    </div>'''),
        section('s-how', 5, 'One verification step, by hand <span class="ill">illustrative probabilities</span>', '''    <div class="visual">
      <div class="seg" id="exSeg"><button data-v="a" class="on">Example 1</button><button data-v="b">Example 2</button></div>
      <div class="scroll-x" style="margin-top:10px"><table class="tbl" id="exTbl"></table></div>
      <p class="readout" id="exOut" style="margin-top:8px"></p>
    </div>
    <p class="caption">u is the uniform random number drawn for each draft token. Accept if u &lt; min(1, p/q).</p>'''),
        section('s-how2', 5, 'How many tokens per target pass, and how much faster?', '''    <p class="lede">If each draft token is accepted with probability α, the expected tokens per target pass is <b>(1 − α<sup>γ+1</sup>) / (1 − α)</b> (Leviathan et al., eq. 1). With draft cost c relative to the target, the wall-clock improvement is that divided by <b>(γc + 1)</b> (Theorem 3.8).</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">α (acceptance) <input type="range" id="sA" min="0.3" max="0.95" step="0.01" value="0.8"> <output id="sAo"></output></label>
        <label class="ctl">γ (draft length) <input type="range" id="sG" min="1" max="12" step="1" value="4"> <output id="sGo"></output></label>
        <label class="ctl">c (draft cost) <input type="range" id="sC" min="0" max="0.3" step="0.01" value="0.05"> <output id="sCo"></output></label>
      </div>
      <svg id="sSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Speedup vs gamma"></svg>
      <div class="grid3">
        <div class="stat"><div class="num" id="sE"></div><div class="lbl">expected tokens per target pass</div></div>
        <div class="stat"><div class="num" id="sS" style="color:var(--e)"></div><div class="lbl">expected wall-clock speedup</div></div>
        <div class="stat"><div class="num" id="sO"></div><div class="lbl">best γ for this α and c</div></div>
      </div>
    </div>'''),
        section('s-why', 6, 'Why it works', '''    <div class="grid2">
      <div class="card e"><h3>Exactness</h3><p>The rejection rule makes the output distribution identical to the target's. Leviathan et al. report <b>identical outputs</b>, and Chen et al. preserve it "within hardware numerics". Build-it notebook 09 checks this by Monte Carlo.</p></div>
      <div class="card a"><h3>Spare compute</h3><p>Decode is memory-bound, so verifying γ+1 positions costs about one step. Accepted drafts are close to free tokens.</p></div>
      <div class="card b"><h3>Measured</h3><p><b>2–3×</b> on T5-XXL (Leviathan et al.); <b>2–2.5×</b> on Chinchilla 70B (Chen et al.).</p></div>
      <div class="card c"><h3>Limit</h3><p>Even with a free draft (c ≈ 0), the speedup is bounded by 1/(1 − α), so the acceptance rate matters most.</p></div>
    </div>'''),
        myths('s-myth', [
            ('Speculative decoding trades quality for speed.', 'The output distribution is <b>exactly</b> the target model\'s. Only latency changes.'),
            ('It only works with greedy decoding.', 'The modified rejection sampling works for <b>sampling</b> too, which is the setting both papers address.'),
            ('A longer draft (bigger γ) is always faster.', 'Each extra draft token costs c and is less likely to be accepted. The best γ depends on α and c.'),
        ]),
        check('s-check', [
            ('mcq', 'With α = 0.8 and γ = 4, what is the expected number of tokens per target pass?', ['1.8', '3.36', '4', '5'], 1, '(1 − 0.8⁵) / 0.2 = <b>3.36</b>.'),
            ('open', 'What is the maximum possible speedup as γ → ∞ with a free draft model (c = 0)?', '<b>1 / (1 − α)</b>, e.g. 5× for α = 0.8. Throughput per target pass is capped by the acceptance rate.'),
            ('mcq', 'On rejecting draft x at position i, what is the replacement token sampled from?', ['The draft q', 'The target p', 'norm(max(0, p − q))', 'Uniform'], 2, 'The <b>residual distribution</b> norm(max(0, p − q)), which corrects for what the draft over-proposed.'),
        ]),
    ],
    js=r'''
  const EX = {
    a: [['the', .40, .50, .31], ['cat', .30, .25, .74], ['sat', .55, .60, .52], ['on', .45, .40, .12]],
    b: [['the', .40, .50, .31], ['dog', .05, .30, .44], ['ran', .20, .30, .10], ['to', .30, .30, .20]],
  };
  Deck.seg('exSeg', v => {
    const rows = EX[v]; let out = [], stop = false;
    const html = rows.map(([tok, p, q, u], i) => {
      if (stop) return `<tr style="opacity:.35"><td>${i + 1}</td><td><code>${tok}</code></td><td>${p}</td><td>${q}</td><td>–</td><td>–</td><td>not checked</td></tr>`;
      const a = Math.min(1, p / q), ok = u < a;
      if (ok) out.push(tok); else { out.push('⟨resample⟩'); stop = true; }
      return `<tr><td>${i + 1}</td><td><code>${tok}</code></td><td>${p}</td><td>${q}</td><td>${a.toFixed(2)}</td><td>${u}</td><td style="color:${ok ? 'var(--e)' : 'var(--d)'};font-weight:700">${ok ? 'accept' : 'reject → sample from norm(max(0, p−q))'}</td></tr>`;
    }).join('');
    if (!stop) out.push('⟨bonus from p⟩');
    document.getElementById('exTbl').innerHTML = '<tr><th>#</th><th>draft x</th><th>p(x)</th><th>q(x)</th><th>min(1, p/q)</th><th>u</th><th>decision</th></tr>' + html;
    document.getElementById('exOut').innerHTML = `This target pass yields <b>${out.length}</b> token${out.length > 1 ? 's' : ''}: ${out.map(t => `<code>${t}</code>`).join(' ')}`;
  });
  const E = (a, g) => (1 - Math.pow(a, g + 1)) / (1 - a), S = (a, g, c) => E(a, g) / (g * c + 1);
  Deck.bind(['sA', 'sG', 'sC'], () => {
    const a = Deck.val('sA'), g = Deck.val('sG'), c = Deck.val('sC');
    Deck.out('sAo', a.toFixed(2)); Deck.out('sGo', g); Deck.out('sCo', c.toFixed(2));
    let best = 1; for (let k = 1; k <= 20; k++) if (S(a, k, c) > S(a, best, c)) best = k;
    Deck.out('sE', E(a, g).toFixed(2)); Deck.out('sS', S(a, g, c).toFixed(2) + '×'); Deck.out('sO', best + ` (${S(a, best, c).toFixed(2)}×)`);
    const s = clear(document.getElementById('sSvg')), L = 50, R = 640, T = 10, B = 190, ymax = Math.max(1 / (1 - a), 2) * 1.05;
    const X = k => L + (k - 1) / 19 * (R - L), Y = v => B - v / ymax * (B - T);
    [1, 5, 10, 15, 20].forEach(k => { svg('line', { x1: X(k), x2: X(k), y1: T, y2: B, class: 'ln' }, s); svg('text', { x: X(k), y: B + 16, 'text-anchor': 'middle', class: 'tm tc', text: k }, s); });
    svg('line', { x1: L, x2: R, y1: Y(1), y2: Y(1), style: 'stroke:var(--faint);stroke-dasharray:4 3' }, s);
    svg('text', { x: R, y: Y(1) - 4, 'text-anchor': 'end', class: 'tm', style: 'font-size:10px', text: 'no speedup' }, s);
    svg('line', { x1: L, x2: R, y1: Y(1 / (1 - a)), y2: Y(1 / (1 - a)), style: 'stroke:var(--d);stroke-dasharray:4 3' }, s);
    svg('text', { x: R, y: Y(1 / (1 - a)) - 4, 'text-anchor': 'end', class: 'tm', style: 'font-size:10px;fill:var(--d)', text: 'cap 1/(1−α)' }, s);
    let pe = '', ps = ''; for (let k = 1; k <= 20; k++) { pe += `${X(k)},${Y(E(a, k))} `; ps += `${X(k)},${Y(S(a, k, c))} `; }
    svg('polyline', { points: pe, fill: 'none', style: 'stroke:var(--a);stroke-width:2;opacity:.6' }, s);
    svg('polyline', { points: ps, fill: 'none', style: 'stroke:var(--e);stroke-width:3' }, s);
    svg('circle', { cx: X(g), cy: Y(S(a, g, c)), r: 7, style: 'fill:var(--e);stroke:var(--panel);stroke-width:2' }, s);
    svg('text', { x: (L + R) / 2, y: B + 34, 'text-anchor': 'middle', class: 'tm', text: 'γ: teal = tokens per target pass, green = wall-clock speedup' }, s);
  });
''',
    line='Speculative decoding drafts γ tokens with a cheap model and verifies them in one target pass. A modified rejection rule keeps the output exactly the target\'s, and speedup ≈ (1 − α^(γ+1)) / ((1 − α)(γc + 1)).',
    explain='Decode is memory-bound: each step reads all the weights to make one token, so scoring several tokens costs about the same as scoring one. Speculative decoding lets a small draft model propose γ tokens, then the target model scores them all in one pass and accepts each with probability min(1, p/q), resampling from max(0, p − q) on the first rejection. The output distribution is exactly the target\'s. Expected tokens per pass is (1 − α^(γ+1))/(1 − α), and the papers reported 2–3× speedups.',
    recap=[('Problem', 'one token per full weight read; autoregression blocks parallel generation.'), ('Core idea', 'draft cheaply, verify in parallel, accept or reject exactly; speedup is set by α, γ and c.')],
)

# =============================================================== 07
DECKS['07-quantization'] = dict(
    title='Quantization', h1='Quantization for inference',
    sub='Fewer bits per weight, activation and KV entry: INT8 and INT4 scales, the activation-outlier problem and SmoothQuant\'s fix, weight-only methods (GPTQ, AWQ), and FP8.',
    prob='Decode speed and capacity are limited by bytes: weights and KV cache read every step. 16-bit numbers are expensive to move.',
    core='Store numbers in 8, 4 or fewer bits with <b>scales</b>, chosen per tensor, per channel or per group, and handle <b>outliers</b> so accuracy survives.',
    build=['10_quantization', '11_fp8_emulation'],
    slides=[
        section('s-p1', 1, 'Bytes, not FLOPs, set decode speed', '''    <p class="lede">At small batch, every decode step streams the weights (and the KV cache) from HBM. Halve the bytes and you roughly halve that time, and twice as much fits in memory.</p>
    <div class="visual"><div id="p1Bars"></div></div>
    <p class="caption">Weight bytes for a 70B-parameter model at different precisions.</p>'''),
        section('s-lim', 2, 'Naive rounding fails on LLM activations', '''    <div class="grid3">
      <div class="card d"><h3>One scale for everything</h3><p>A per-tensor scale must cover the largest value. Everything else gets only a few effective levels.</p></div>
      <div class="card b"><h3>Activation outliers</h3><p>A few activation channels are far larger than the rest, so per-tensor INT8 on activations loses the small values (the problem SmoothQuant targets).</p></div>
      <div class="card c"><h3>Very low bits</h3><p>Naive 3–4-bit rounding of weights loses accuracy without smarter error handling.</p></div>
    </div>'''),
        your_turn('s-turn', 'Deal with the outlier channel',
                  'A few activation channels have huge values, which breaks per-tensor INT8. Which fix keeps the matmul result mathematically the same?',
                  ['Clip the outliers', 'Divide each activation channel by a factor and multiply the matching weight row by the same factor', 'Drop the outlier channels', 'Use a per-tensor scale with more care'], 1,
                  '<b>B is SmoothQuant.</b> X·W = (X·diag(s)⁻¹)·(diag(s)·W), so dividing activation channel j by s<sub>j</sub> and multiplying weight row j by s<sub>j</sub> moves the difficulty into the weights, which are easier to quantize, with no change to the result.'),
        section('s-core', 4, 'Scales, granularity, and where the bits go', '''    <div class="eq">q = clip(round(x / s), −qmax, qmax), &nbsp; x̂ = q · s, &nbsp; s = max|x| / qmax</div>
    <div class="grid2" style="margin-top:12px">
      <div class="card a"><h3>Granularity</h3><p>Per tensor → per channel → per group: smaller groups mean tighter ranges and less error, at the cost of storing more scales.</p></div>
      <div class="card b"><h3>W8A8 (SmoothQuant)</h3><p>INT8 weights and activations via smoothing: up to <b>1.56×</b> speed and <b>2×</b> less memory with negligible accuracy loss.</p></div>
      <div class="card c"><h3>Weight-only, 3–4 bits</h3><p><b>GPTQ</b>: second-order one-shot quantization; a 175B model in ~4 GPU-hours; 3.25× (A100) and 4.5× (A6000) over FP16. <b>AWQ</b>: protect the ~1% salient weights found from activations; &gt;3× over HF FP16.</p></div>
      <div class="card e"><h3>FP8</h3><p>E4M3 and E5M2 floating point, with per-tensor or per-block scales. It matched 16-bit training quality in Micikevicius et al. (2022).</p></div>
    </div>'''),
        section('s-how', 5, 'Rounding on a number line <span class="ill">random values</span>', '''    <div class="visual">
      <div class="controls" style="margin-top:0">
        <div class="seg" id="qBits"><button data-v="8">INT8</button><button data-v="4" class="on">INT4</button></div>
        <div class="seg" id="qGran"><button data-v="tensor" class="on">per-tensor scale</button><button data-v="group">per-group (8) scales</button></div>
        <div class="seg" id="qOut"><button data-v="0" class="on">no outlier</button><button data-v="1">add an outlier</button></div>
      </div>
      <svg id="qSvg" viewBox="0 0 660 200" style="margin-top:10px" role="img" aria-label="Quantization number line"></svg>
      <p class="readout" id="qRes"></p>
    </div>'''),
        section('s-how2', 5, 'SmoothQuant on live data', '''    <p class="lede">Activations with two outlier channels (×40), as LLMs show. The smoothing factor is <b>s<sub>j</sub> = max|X<sub>j</sub>|<sup>α</sup> / max|W<sub>j</sub>|<sup>1−α</sup></b> (paper eq. 4). α = 0.5 is the paper's default, and 0.75 was used for GLM-130B.</p>
    <div class="visual">
      <label class="ctl">migration strength α <input type="range" id="smA" min="0" max="1" step="0.05" value="0.5"> <output id="smAo"></output></label>
      <div class="grid2" style="margin-top:10px">
        <div><h3>Per-channel max |X| (first 32 channels)</h3><svg id="smX" viewBox="0 0 320 120" role="img" aria-label="Activation channel ranges"></svg></div>
        <div><h3>W8A8 matmul error</h3><div id="smBars"></div></div>
      </div>
    </div>
    <p class="caption">Same construction as Build-it notebook 10 (64 × 128 activations, 128 × 96 weights). Errors are computed live in your browser.</p>'''),
        section('s-how3', 5, 'FP8: two formats', '''    <div class="visual scroll-x"><table class="tbl">
      <tr><th></th><th>E4M3</th><th>E5M2</th></tr>
      <tr><td>Exponent / mantissa bits</td><td>4 / 3</td><td>5 / 2</td></tr>
      <tr><td>Exponent bias</td><td>7</td><td>15</td></tr>
      <tr><td>Max normal</td><td><b>448</b></td><td><b>57,344</b></td></tr>
      <tr><td>Infinities</td><td>none (range extended instead)</td><td>IEEE-style</td></tr>
      <tr><td>Character</td><td>more precision</td><td>more range</td></tr>
    </table></div>
    <div class="cite">Micikevicius et al., "FP8 Formats for Deep Learning" (2022), Table 1. Build-it notebook 11 enumerates all 127 / 124 finite non-negative values.</div>'''),
        section('s-why', 6, 'Why it works', '''    <div class="grid2">
      <div class="card e"><h3>Fewer bytes, faster decode</h3><p>Decode is memory-bound, so moving fewer bytes per step speeds it up directly and frees memory for more KV.</p></div>
      <div class="card a"><h3>Finer scales, smaller ranges</h3><p>Error is about half a step, and the step is range / levels, so finer granularity means smaller error.</p></div>
      <div class="card b"><h3>Outliers moved, not removed</h3><p>SmoothQuant's transform is exactly equivalent and balances activation and weight ranges.</p></div>
      <div class="card c"><h3>Error-aware rounding</h3><p>GPTQ compensates rounding errors using second-order information, and AWQ protects activation-salient weights.</p></div>
    </div>'''),
        myths('s-myth', [
            ('Quantization always costs a lot of accuracy.', 'With good scales and outlier handling, INT8 (SmoothQuant) and 3–4-bit weight-only (GPTQ, AWQ) report small or negligible losses on large models.'),
            ('Weight-only INT4 speeds up everything equally.', 'It reduces <b>weight bytes</b>, which helps memory-bound decode the most. Compute-bound prefill gains less.'),
            ('Per-tensor scales are fine for activations.', 'LLM activations have <b>outlier channels</b>, so per-tensor activation INT8 needs SmoothQuant-style smoothing or finer scales.'),
        ]),
        check('s-check', [
            ('mcq', 'What is the maximum normal value of FP8 E4M3?', ['127', '240', '448', '57,344'], 2, '<b>448</b> (E5M2: 57,344).'),
            ('open', 'Why is SmoothQuant\'s transform "free" at inference?', 'X·W = (X·diag(s)⁻¹)(diag(s)·W). The weight scaling is folded in <b>offline</b> and the activation division can be fused into the previous layer, so the result is unchanged and nothing is added at runtime.'),
            ('mcq', 'What fraction of weights does AWQ find to be salient?', ['0.01%', 'About 1%', 'About 50%', 'All'], 1, '"Protecting only <b>1%</b> salient weights can greatly reduce quantization error".'),
        ]),
    ],
    js=r'''
  Deck.hbars(document.getElementById('p1Bars'), [['FP32', 4], ['BF16 / FP16', 2], ['FP8 / INT8', 1], ['INT4', .5]].map(([n, b], i) => ({ label: n, value: 70 * b, color: ['var(--faint)', 'var(--a)', 'var(--e)', 'var(--c)'][i], text: (70 * b) + ' GB' })));
  let bits = 4, gran = 'tensor', outl = 0;
  const base = (() => { let s = 11; const r = () => { s = (s * 16807) % 2147483647; return s / 2147483647; }; return [...Array(16)].map(() => { const u = r(), v = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }); })();
  const qz = () => {
    const xs = base.map((v, i) => outl && i === 5 ? 9 : v), qmax = 2 ** (bits - 1) - 1;
    const scaleOf = arr => Math.max(...arr.map(Math.abs)) / qmax;
    const scales = xs.map((_, i) => gran === 'tensor' ? scaleOf(xs) : scaleOf(xs.slice(Math.floor(i / 8) * 8, Math.floor(i / 8) * 8 + 8)));
    const deq = xs.map((v, i) => Math.max(-qmax, Math.min(qmax, Math.round(v / scales[i]))) * scales[i]);
    const s = clear(document.getElementById('qSvg')), L = 30, R = 640, lim = Math.max(...xs.map(Math.abs)) * 1.05, X = v => (L + R) / 2 + v / lim * (R - L) / 2;
    svg('line', { x1: L, x2: R, y1: 100, y2: 100, class: 's-line', 'stroke-width': 2 }, s);
    const sc0 = scales[0];
    for (let k = -qmax; k <= qmax; k++) svg('line', { x1: X(k * sc0), x2: X(k * sc0), y1: 92, y2: 108, style: 'stroke:var(--faint)' }, s);
    xs.forEach((v, i) => { svg('line', { x1: X(v), y1: 60, x2: X(deq[i]), y2: 140, style: 'stroke:var(--d);opacity:.5' }, s); svg('circle', { cx: X(v), cy: 60, r: 5, class: 'f-a' }, s); svg('circle', { cx: X(deq[i]), cy: 140, r: 5, style: 'fill:var(--b)' }, s); });
    svg('text', { x: L, y: 40, class: 'tm', style: 'font-size:11px', text: 'original values' }, s);
    svg('text', { x: L, y: 170, class: 'tm', style: 'font-size:11px', text: `dequantized (${gran === 'tensor' ? 'grid ticks = the single per-tensor step' : 'ticks shown for group 1'})` }, s);
    const err = Math.sqrt(xs.reduce((a, v, i) => a + (v - deq[i]) ** 2, 0) / xs.reduce((a, v) => a + v * v, 0));
    const small = xs.map((v, i) => [v, deq[i]]).filter((_, i) => i !== 5 || !outl);
    const zeroed = small.filter(([v, d]) => d === 0 && v !== 0).length;
    document.getElementById('qRes').innerHTML = `INT${bits}, ${gran === 'tensor' ? 'one scale' : 'one scale per 8 values'}: relative error <b>${(100 * err).toFixed(1)}%</b> · ${zeroed} of ${small.length} non-outlier values rounded to 0`;
  };
  Deck.seg('qBits', v => { bits = +v; qz(); }); Deck.seg('qGran', v => { gran = v; qz(); }); Deck.seg('qOut', v => { outl = +v; qz(); });
  // SmoothQuant live
  const R = (() => { let s = 5; return () => { s = (s * 16807) % 2147483647; return s / 2147483647; }; })();
  const N = () => Math.sqrt(-2 * Math.log(R() + 1e-12)) * Math.cos(2 * Math.PI * R());
  const X = [...Array(64)].map(() => [...Array(128)].map((_, j) => N() * (j === 5 || j === 77 ? 40 : 1)));
  const Wm = [...Array(128)].map(() => [...Array(96)].map(() => N() * 0.05));
  const mm = (A, B) => A.map(r => B[0].map((_, j) => r.reduce((acc, v, k) => acc + v * B[k][j], 0)));
  const ref = mm(X, Wm);
  const w8a8 = (A, B) => {
    const sa = Math.max(...A.flat().map(Math.abs)) / 127, qa = A.map(r => r.map(v => Math.max(-127, Math.min(127, Math.round(v / sa)))));
    const sw = B[0].map((_, j) => Math.max(...B.map(r => Math.abs(r[j]))) / 127), qw = B.map(r => r.map((v, j) => Math.max(-127, Math.min(127, Math.round(v / sw[j])))));
    return mm(qa, qw).map(r => r.map((v, j) => v * sa * sw[j]));
  };
  const rel = Y => Math.sqrt(Y.flat().reduce((a, v, i) => a + (v - ref.flat()[i]) ** 2, 0) / ref.flat().reduce((a, v) => a + v * v, 0));
  const before = rel(w8a8(X, Wm));
  Deck.bind(['smA'], () => {
    const a = Deck.val('smA'); Deck.out('smAo', a.toFixed(2));
    const xmax = X[0].map((_, j) => Math.max(...X.map(r => Math.abs(r[j])))), wmax = Wm.map(r => Math.max(...r.map(Math.abs)));
    const s = xmax.map((m, j) => Math.pow(m, a) / Math.pow(Math.max(wmax[j], 1e-12), 1 - a));
    const Xs = X.map(r => r.map((v, j) => v / s[j])), Ws = Wm.map((r, j) => r.map(v => v * s[j]));
    const after = rel(w8a8(Xs, Ws));
    const sv = clear(document.getElementById('smX')), xm2 = Xs[0].map((_, j) => Math.max(...Xs.map(r => Math.abs(r[j])))), top = Math.max(...xmax);
    for (let j = 0; j < 32; j++) { const jj = j < 16 ? j : 64 + j; svg('rect', { x: 4 + j * 9.8, y: 110 - 100 * xmax[jj === 80 ? 77 : jj] / top, width: 4, height: 100 * xmax[jj === 80 ? 77 : jj] / top, style: 'fill:var(--d);opacity:.5' }, sv); svg('rect', { x: 8.5 + j * 9.8, y: 110 - 100 * xm2[jj === 80 ? 77 : jj] / top, width: 4, height: Math.max(1, 100 * xm2[jj === 80 ? 77 : jj] / top), style: 'fill:var(--e)' }, sv); }
    Deck.hbars(document.getElementById('smBars'), [{ label: 'raw W8A8', value: before, color: 'var(--d)', text: (100 * before).toFixed(2) + '%' }, { label: `smoothed (α=${a.toFixed(2)})`, value: after, color: 'var(--e)', text: (100 * after).toFixed(2) + '%' }], { max: Math.max(before, after) * 1.1 });
  });
''',
    line='Quantization cuts the bytes that bound decode. Scales at the right granularity, outlier handling (SmoothQuant), error-aware weight methods (GPTQ, AWQ) and FP8 keep accuracy while moving 2–4× fewer bytes.',
    explain='Decode is memory-bound, so storing weights, activations and KV in fewer bits speeds it up and frees memory. Quantization maps values to integers with a scale. Finer scales (per channel, per group) cut error, but LLM activations have outlier channels that break per-tensor INT8. SmoothQuant moves that difficulty into the weights with an exact rescaling, reporting up to 1.56× speed and 2× less memory. GPTQ and AWQ push weights to 3–4 bits. FP8 (E4M3, max 448; E5M2, max 57,344) uses floating point with scales.',
    recap=[('Problem', '16-bit bytes bound decode; naive low-bit rounding breaks on outliers.'), ('Core idea', 'scales at the right granularity, outlier migration, error-aware weight quantization, FP8.')],
)

# =============================================================== 08
DECKS['08-parallelism'] = dict(
    title='Parallelism for Inference', h1='Parallelism for inference',
    sub='Splitting a model across GPUs to serve it: tensor parallelism for latency and fit, pipeline and data parallelism for throughput, expert parallelism for MoE, and why the communication pattern decides where each one runs.',
    prob='A large model may not fit in one GPU\'s memory, and even when it fits, one GPU\'s memory bandwidth limits how fast each decode step can be.',
    core='<b>Tensor parallelism</b> splits every matmul so each GPU reads only its share of the weights per token, at the cost of one all-reduce per block, which must stay on NVLink.',
    build=['12_tensor_parallel'],
    slides=[
        section('s-p1', 1, 'Fit and speed both hit a single-GPU wall', '''    <div class="grid2">
      <div class="card d"><h3>Fit</h3><p>A 70B model in BF16 is about 140 GB of weights, more than one 80 GB GPU, before any KV cache.</p></div>
      <div class="card b"><h3>Speed</h3><p>At batch 1, one decode step must read all the weights. At 3.35 TB/s (H100 HBM), 140 GB takes at least about 42 ms per token.</p></div>
    </div>'''),
        section('s-lim', 2, 'Not every split helps latency', '''    <div class="grid3">
      <div class="card b"><h3>Pipeline (layers across GPUs)</h3><p>Fits the model, but a single request still visits every stage in turn, so per-token latency doesn't improve.</p></div>
      <div class="card c"><h3>Data parallel (replicas)</h3><p>More throughput, but each replica must hold the whole model, and per-request latency is unchanged.</p></div>
      <div class="card d"><h3>Naive splits</h3><p>Splitting carelessly forces communication after every matmul.</p></div>
    </div>'''),
        your_turn('s-turn', 'Lower per-token latency',
                  'Which kind of parallelism reduces per-token decode latency for a single request?',
                  ['Data parallelism (more replicas)', 'Tensor parallelism: split each weight matrix so every GPU reads 1/n of the weights per token', 'Pipeline parallelism across nodes', 'Larger batch size'], 1,
                  '<b>B.</b> With TP of degree n, each GPU streams only 1/n of the weights each step, so the memory-bound step time drops roughly n× (minus communication). Pipeline and data parallelism help capacity and throughput, not one request\'s latency.'),
        section('s-core', 4, 'Megatron-style tensor parallelism', '''    <div class="visual"><svg id="tpSvg" viewBox="0 0 660 200" role="img" aria-label="Column then row parallel MLP"></svg></div>
    <div class="grid3" style="margin-top:12px">
      <div class="card a"><h3>Column-parallel first</h3><p>Split W₁ by output columns. Each GPU computes its slice, and GELU stays local because it's elementwise.</p></div>
      <div class="card b"><h3>Row-parallel second</h3><p>Split W₂ by input rows to match. Each GPU holds a partial sum.</p></div>
      <div class="card e"><h3>One all-reduce</h3><p>Sum the partials once per MLP (and once per attention block). That's two all-reduces per layer.</p></div>
    </div>'''),
        section('s-how', 5, 'TP degree vs latency and communication <span class="ill">bandwidth-only model</span>', '''    <div class="visual">
      <div class="controls" style="margin-top:0">
        <select id="tM"><option value="16,4096,32">8B-shaped (16 GB, d=4096, 32 layers)</option><option value="140,8192,80" selected>70B-shaped (140 GB, d=8192, 80 layers)</option></select>
        <div class="seg" id="tN"><button data-v="1">TP 1</button><button data-v="2">TP 2</button><button data-v="4">TP 4</button><button data-v="8" class="on">TP 8</button></div>
        <div class="seg" id="tL"><button data-v="450" class="on">NVLink (450 GB/s)</button><button data-v="50">400G network (50 GB/s)</button></div>
      </div>
      <div class="grid4" style="margin-top:14px">
        <div class="stat"><div class="num" id="tW"></div><div class="lbl">weights per GPU</div></div>
        <div class="stat"><div class="num" id="tR"></div><div class="lbl">weight-read time per step (≥)</div></div>
        <div class="stat"><div class="num" id="tC"></div><div class="lbl">all-reduce time per step</div></div>
        <div class="stat"><div class="num" id="tT" style="color:var(--a)"></div><div class="lbl">≈ TPOT lower bound (batch 1)</div></div>
      </div>
    </div>
    <p class="caption">Per step: read weights ÷ n at 3.35 TB/s (H100 HBM), plus 2 all-reduces per layer of d BF16 values × 2(n−1)/n over the link. Latency per message is ignored, and in practice it makes off-node TP even worse.</p>'''),
        section('s-why', 6, 'Why TP lives inside the NVLink domain', '''    <div class="grid2">
      <div class="card e"><h3>Less to read per GPU</h3><p>Decode is bound by bytes. Splitting weights n ways cuts each GPU's per-step read about n×.</p></div>
      <div class="card d"><h3>Small, frequent, blocking messages</h3><p>Two all-reduces per layer per step sit on the critical path, so they need NVLink-class bandwidth and latency (GPU decks 04 and 05).</p></div>
      <div class="card b"><h3>Combine strategies</h3><p>TP within a node; pipeline across nodes for very large models; data-parallel replicas for throughput.</p></div>
      <div class="card c"><h3>MoE: expert parallelism</h3><p>Experts live on different GPUs and tokens travel by all-to-all. TensorRT-LLM, for example, lists "Wide Expert Parallelism" as a runtime feature.</p></div>
    </div>'''),
        myths('s-myth', [
            ('More TP always means lower latency.', 'Weight reads shrink as 1/n, but all-reduce cost does not. Beyond the NVLink domain, communication can dominate.'),
            ('Pipeline parallelism speeds up a single request.', 'A request still passes through every stage in order. Pipelining helps fit and throughput, not one request\'s latency.'),
            ('TP needs communication after every matmul.', 'The column-then-row (Megatron) arrangement needs <b>one</b> all-reduce per MLP or attention block.'),
        ]),
        check('s-check', [
            ('mcq', 'How many all-reduces per transformer layer does Megatron-style TP need in the forward pass?', ['0', '1', '2', 'one per matmul'], 2, '<b>Two</b>: one after attention, one after the MLP.'),
            ('open', 'Why is GELU between the two MLP matmuls "free" under TP?', 'After the column-parallel W₁ each GPU holds complete columns of the hidden activation, and GELU is <b>elementwise</b>, so it runs locally with no communication.'),
            ('open', 'Roughly what is the minimum per-token decode time for 140 GB of weights on one H100 (3.35 TB/s), and with TP 8?', '140 / 3,350 ≈ <b>42 ms</b>. With TP 8 each GPU reads 17.5 GB, about <b>5.2 ms</b>, plus all-reduce time.'),
        ]),
    ],
    js=r'''
  (() => {
    const s = document.getElementById('tpSvg');
    const box = (x, y, w, h, c, t) => { svg('rect', { x, y, width: w, height: h, rx: 6, style: `fill:${c}` }, s); svg('text', { x: x + w / 2, y: y + h / 2 + 4, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11px;font-weight:600', text: t }, s); };
    box(10, 80, 60, 40, 'var(--faint)', 'X');
    for (let g = 0; g < 4; g++) { const y = 10 + g * 46; box(110, y, 110, 36, 'var(--a)', `GPU${g}: X·W₁[:, ${g}]`); box(240, y, 70, 36, 'var(--a)', 'GELU'); box(330, y, 130, 36, 'var(--b)', `·W₂[${g}, :] → partial`); svg('line', { x1: 70, y1: 100, x2: 110, y2: y + 18, class: 's-line', 'stroke-width': 1.5 }, s); svg('line', { x1: 460, y1: y + 18, x2: 500, y2: 100, class: 's-line', 'stroke-width': 1.5 }, s); }
    box(500, 75, 80, 50, 'var(--e)', 'all-reduce Σ'); box(600, 80, 50, 40, 'var(--faint)', 'Y');
    svg('text', { x: 285, y: 196, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: 'no communication until the single all-reduce' }, s);
  })();
  let n = 8, bw = 450;
  const tp = () => {
    const [w, d, L] = Deck.val('tM').split(',').map(Number);
    const read = w / n / 3350 * 1000, comm = n > 1 ? 2 * L * d * 2 * (2 * (n - 1) / n) / (bw * 1e9) * 1000 : 0;
    Deck.out('tW', (w / n).toFixed(1) + ' GB'); Deck.out('tR', read.toFixed(1) + ' ms'); Deck.out('tC', comm.toFixed(2) + ' ms'); Deck.out('tT', (read + comm).toFixed(1) + ' ms');
    document.getElementById('tW').style.color = w / n > 80 ? 'var(--d)' : 'var(--ink)';
  };
  Deck.seg('tN', v => { n = +v; tp(); }); Deck.seg('tL', v => { bw = +v; tp(); }); Deck.bind(['tM'], tp);
''',
    line='Tensor parallelism splits every weight matrix so each GPU reads 1/n of the weights per token, cutting latency and fitting big models, at the cost of two small all-reduces per layer that must stay on NVLink.',
    explain='One GPU may not hold a large model, and at batch 1 a decode step is bounded by reading all the weights: about 42 ms for 140 GB at H100 bandwidth. Tensor parallelism splits each matmul Megatron-style (column-parallel then row-parallel), so each GPU reads 1/n of the weights and only one all-reduce is needed per attention or MLP block. Those all-reduces are small but on the critical path, so TP stays inside the NVLink domain. Pipeline and data parallelism add capacity and throughput, and expert parallelism spreads MoE experts across GPUs.',
    recap=[('Problem', 'single-GPU memory capacity and bandwidth limit both fit and per-token latency.'), ('Core idea', 'column → row TP: 1/n of the weights per GPU, two all-reduces per layer, kept on NVLink.')],
)

# =============================================================== 09
DECKS['09-disaggregated-serving'] = dict(
    title='Disaggregated Serving', h1='Disaggregated prefill and decode',
    sub='Running prefill and decode on separate GPU pools, each sized and configured for its phase, and moving the KV cache between them (DistServe, OSDI 2024; Splitwise, 2024).',
    prob='Prefill (compute-heavy) and decode (memory-heavy) interfere when they share GPUs, and one configuration can\'t be optimal for both.',
    core='<b>Split the phases</b> across machines. Prefill GPUs compute the prompt and its KV, the KV moves to decode GPUs, and each pool gets its own parallelism and scale to maximize <b>goodput</b> under SLOs.',
    build=['06_chunked_prefill', '04_kv_memory_calculator'],
    slides=[
        section('s-p1', 1, 'Two phases with opposite needs', '''    <div class="vs">
      <div class="card a"><h3>Prefill: "prompt computation"</h3><p>Compute-intensive: many tokens per pass. Sets TTFT.</p></div>
      <div class="card b"><h3>Decode: "token generation"</h3><p>Memory-intensive: one token per sequence per step. Sets TPOT.</p></div>
    </div>
    <div class="cite">Splitwise describes these as a compute-intensive prompt phase and a memory-intensive token-generation phase.</div>'''),
        section('s-lim', 2, 'Colocation forces compromises', '''    <div class="grid3">
      <div class="card d"><h3>Interference</h3><p>A new prompt's prefill shares iterations with ongoing decodes and slows them, or waits behind them (deck 04).</p></div>
      <div class="card b"><h3>One configuration for two jobs</h3><p>The best parallelism and batch size for prefill and for decode differ, but colocation forces a single choice.</p></div>
      <div class="card c"><h3>Coupled scaling</h3><p>You can't add prefill capacity without also adding decode capacity, even if only one is short.</p></div>
    </div>'''),
        your_turn('s-turn', 'Remove the interference',
                  'What removes prefill-decode interference entirely while letting each phase be configured separately?',
                  ['A bigger token budget', 'Run prefill and decode on different GPUs and transfer the KV cache between them', 'Use only one phase', 'Quantize harder'], 1,
                  '<b>B.</b> DistServe "assigns prefill and decoding computation to different GPUs", and Splitwise runs the phases on separate machines, transferring state over the cluster interconnect. Each pool is then tuned for its own SLO.'),
        section('s-core', 4, 'Prefill pool → KV transfer → decode pool', '''    <div class="visual"><svg id="dSvg" viewBox="0 0 660 150" role="img" aria-label="Disaggregated serving pipeline"></svg></div>
    <div class="grid3" style="margin-top:12px">
      <div class="card a"><h3>Prefill pool</h3><p>Sized and parallelized for TTFT, batching prompts for compute efficiency.</p></div>
      <div class="card c"><h3>KV transfer</h3><p>The prompt's KV cache moves to a decode GPU. Placement and interconnect bandwidth decide how much this costs.</p></div>
      <div class="card b"><h3>Decode pool</h3><p>Sized for TPOT and KV capacity, running large continuous batches.</p></div>
    </div>'''),
        section('s-how', 5, 'What does moving the KV cost?', '''    <div class="visual">
      <div class="controls" style="margin-top:0">
        <select id="xM"><option value="131072">8B-shaped (128 KB/token)</option><option value="327680" selected>70B-shaped (320 KB/token)</option></select>
        <label class="ctl">Prompt tokens <input type="range" id="xP" min="9" max="17" step="0.5" value="12"> <output id="xPo"></output></label>
        <div class="seg" id="xL"><button data-v="450" class="on">NVLink 450 GB/s</button><button data-v="50">400G NIC 50 GB/s</button><button data-v="400">8× NICs 400 GB/s</button></div>
      </div>
      <div class="grid3" style="margin-top:14px">
        <div class="stat"><div class="num" id="xB"></div><div class="lbl">KV to transfer</div></div>
        <div class="stat"><div class="num" id="xT" style="color:var(--c)"></div><div class="lbl">transfer time (bandwidth only)</div></div>
        <div class="stat"><div class="num" id="xF"></div><div class="lbl">vs prefill at 20K tok/s (illustrative)</div></div>
      </div>
    </div>
    <p class="caption">KV bytes = prompt × per-token KV (BF16). Transfer can be overlapped layer by layer with prefill. This is a bandwidth estimate, not a measured system.</p>'''),
        section('s-why', 6, 'Why it works, and what it costs', '''    <div class="grid2">
      <div class="card e"><h3>No interference</h3><p>Long prompts never stall decode iterations, and decode batches never slow prefill.</p></div>
      <div class="card a"><h3>Independent tuning</h3><p>Each pool picks its own parallelism, batch size and GPU count for its own SLO, so goodput goes up.</p></div>
      <div class="card b"><h3>Measured</h3><p>DistServe: <b>7.4×</b> more requests or <b>12.6×</b> tighter SLOs. Splitwise: <b>1.4×</b> throughput at <b>20%</b> lower cost, or <b>2.35×</b> throughput at the same cost and power.</p></div>
      <div class="card d"><h3>Cost</h3><p>KV transfer needs fast interconnect and smart placement, and the pools add operational complexity.</p></div>
    </div>'''),
        myths('s-myth', [
            ('Disaggregation is always better than chunked prefill.', 'It adds KV transfer and operational complexity. Chunked prefill (deck 04) also reduces interference on shared GPUs. Which wins depends on workload, scale and interconnect.'),
            ('Prefill and decode pools must use the same hardware.', 'Splitwise explicitly provisions <b>different machines</b> for each phase, and heterogeneous pools are part of the appeal.'),
            ('The KV transfer is negligible.', 'For long prompts on large models it is gigabytes per request. It needs NVLink/RDMA-class links or overlapping with prefill.'),
        ]),
        check('s-check', [
            ('mcq', 'What does DistServe optimize?', ['Peak FLOPs', 'Goodput under TTFT and TPOT SLOs', 'Model size', 'Tokens per watt only'], 1, '<b>Goodput</b>: requests served within the TTFT and TPOT SLOs.'),
            ('open', 'Roughly how much KV must move for a 4,096-token prompt on a 70B-shaped model (320 KB/token, BF16)?', '4,096 × 320 KB ≈ <b>1.34 GB</b>, about 3 ms over NVLink at 450 GB/s, or about 27 ms over a single 50 GB/s NIC.'),
            ('mcq', 'What did Splitwise report at the same cost and power budget?', ['1.1×', '2.35× throughput', '7.4× requests', '36.9×'], 1, '<b>2.35×</b> more throughput.'),
        ]),
    ],
    js=r'''
  (() => {
    const s = document.getElementById('dSvg');
    const b = (x, w, c, t1, t2) => { svg('rect', { x, y: 30, width: w, height: 70, rx: 10, style: `fill:${c}` }, s); svg('text', { x: x + w / 2, y: 60, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:700', text: t1 }, s); svg('text', { x: x + w / 2, y: 80, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11px', text: t2 }, s); };
    svg('text', { x: 10, y: 70, class: 'tm', text: 'prompts →' }, s);
    b(80, 200, 'var(--a)', 'Prefill pool', 'compute-bound · sets TTFT');
    svg('line', { x1: 285, x2: 375, y1: 65, y2: 65, style: 'stroke:var(--c);stroke-width:5' }, s);
    svg('text', { x: 330, y: 55, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: 'KV cache' }, s);
    b(380, 200, 'var(--b)', 'Decode pool', 'memory-bound · sets TPOT');
    svg('text', { x: 590, y: 70, class: 'tm', text: '→ tokens' }, s);
    svg('text', { x: 330, y: 135, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: 'each pool: its own GPU count, parallelism, batch size' }, s);
  })();
  let link = 450;
  const xf = () => {
    const per = +Deck.val('xM'), P = Math.round(Math.pow(2, Deck.val('xP'))); Deck.out('xPo', P.toLocaleString());
    const bytes = P * per, t = bytes / (link * 1e9) * 1000, pre = P / 20000 * 1000;
    Deck.out('xB', (bytes / 1e9).toFixed(2) + ' GB'); Deck.out('xT', t.toFixed(1) + ' ms'); Deck.out('xF', `${(100 * t / pre).toFixed(0)}% of ${pre.toFixed(0)} ms`);
  };
  Deck.seg('xL', v => { link = +v; if (document.getElementById('xM')) xf(); });
  Deck.bind(['xM', 'xP'], xf);
''',
    line='Disaggregated serving runs prefill and decode on separate, separately tuned GPU pools and moves the KV cache between them. That removes interference and raises goodput, at the price of fast KV transfer.',
    explain='Prefill is compute-bound and decode is memory-bound, and sharing GPUs makes them interfere and forces one configuration onto both. DistServe and Splitwise run the phases on different machines: the prefill pool computes the prompt and its KV cache, the KV moves over a fast interconnect, and the decode pool streams tokens. Each pool is sized for its own SLO. DistServe reported 7.4× more requests or 12.6× tighter SLOs, and Splitwise 1.4× throughput at 20% lower cost. The cost is gigabytes of KV transfer for long prompts.',
    recap=[('Problem', 'prefill and decode interfere and want different configurations.'), ('Core idea', 'separate pools plus KV transfer, each pool tuned for goodput.')],
)

# =============================================================== 10
DECKS['10-putting-it-together'] = dict(
    title='Putting It Together', h1='Putting it together: diagnosing a serving system',
    sub='How the techniques combine in real engines, and a symptom → cause → fix playbook for the questions you\'ll actually face.',
    prob='A production server has dozens of knobs, and turning the wrong one wastes GPUs or breaks SLOs.',
    core='Measure first (TTFT, TPOT, goodput, KV utilization, batch size, queue length), identify the bottleneck <b>phase and resource</b>, then apply the matching technique.',
    build=[],
    slides=[
        section('s-p1', 1, 'Every technique fixes one bottleneck', '''    <div class="visual scroll-x"><table class="tbl">
      <tr><th>Technique</th><th>Fixes</th><th>Main cost</th><th>Deck</th></tr>
      <tr><td>KV cache</td><td>Quadratic recompute</td><td>Memory</td><td>02</td></tr>
      <tr><td>Continuous batching</td><td>Idle slots, queueing</td><td>Dynamic memory management</td><td>03</td></tr>
      <tr><td>Chunked prefill</td><td>Decode stalls from prefill</td><td>Higher TTFT for long prompts</td><td>04</td></tr>
      <tr><td>PagedAttention / prefix cache</td><td>Fragmentation, duplicated prefixes</td><td>Indirection in the kernel</td><td>05</td></tr>
      <tr><td>Speculative decoding</td><td>Sequential decode latency</td><td>Draft compute, depends on α</td><td>06</td></tr>
      <tr><td>Quantization</td><td>Bytes per step, memory fit</td><td>Accuracy risk, calibration</td><td>07</td></tr>
      <tr><td>Tensor parallelism</td><td>Fit, per-token latency</td><td>All-reduce on the critical path</td><td>08</td></tr>
      <tr><td>Disaggregation</td><td>Prefill-decode interference</td><td>KV transfer, complexity</td><td>09</td></tr>
    </table></div>'''),
        section('s-lim', 2, 'Tuning without measuring goes wrong', '''    <div class="grid3">
      <div class="card d"><h3>Wrong knob</h3><p>Adding GPUs when the problem is queueing, or quantizing when the problem is prefill compute.</p></div>
      <div class="card b"><h3>Averages</h3><p>Tuning mean latency while the p99 TPOT breaks the SLO.</p></div>
      <div class="card c"><h3>One phase</h3><p>Fixing TTFT by enlarging prefill iterations, which spikes everyone's TPOT.</p></div>
    </div>'''),
        your_turn('s-turn', 'Diagnose this',
                  'TTFT is high and rising with load. TPOT is fine. KV memory is only 40% used and requests are queueing. What\'s the most likely fix?',
                  ['Quantize the weights to INT4', 'Add prefill capacity or admit more prompts per iteration, e.g. a bigger chunk budget or more prefill GPUs', 'Enable speculative decoding', 'Reduce the batch size'], 1,
                  '<b>B.</b> Rising TTFT with fine TPOT and spare KV memory points at <b>prefill throughput or queueing</b>. Speculative decoding and quantization mainly help decode. Smaller batches would make queueing worse.'),
        section('s-core', 4, 'Measure, locate, fix', '''    <div class="grid2">
      <div class="card a"><h3>Measure</h3><p>TTFT and TPOT percentiles, goodput at the SLO, running batch size, queue length, KV-cache utilization, prefix-cache hit rate, GPU compute and bandwidth utilization.</p></div>
      <div class="card b"><h3>Locate</h3><p>Which <b>phase</b> (prefill or decode)? Which <b>resource</b> (compute, HBM bandwidth, KV capacity, interconnect, scheduler)?</p></div>
      <div class="card e"><h3>Fix</h3><p>Apply the technique matched to that phase and resource (table on the first slide).</p></div>
      <div class="card c"><h3>Verify</h3><p>Re-measure goodput at the SLO, not just mean throughput.</p></div>
    </div>'''),
        section('s-how', 5, 'The playbook: symptom → cause → fix', '''    <p class="lede">Decide the cause before revealing.</p>
''' + '\n'.join(openq(q, a) for q, a in [
            ('TPOT spikes whenever long prompts arrive; TTFT is fine.', '<b>Prefill interfering with decode.</b> Use chunked prefill with a token budget (04), or disaggregate (09).'),
            ('Batch size stays small although many requests are queued; KV memory is "full".', '<b>KV fragmentation or over-reservation, or KV too large.</b> Use paged KV (05), GQA-class models (02), FP8 KV (07), or shorter maximum context.'),
            ('Single-user latency is too slow even at batch 1; GPUs aren\'t compute-bound.', '<b>Memory-bound sequential decode.</b> Use speculative decoding (06), weight quantization (07), or more TP within NVLink (08).'),
            ('Many requests share a long system prompt, and TTFT is high.', '<b>Recomputing the same prefix.</b> Turn on prefix caching (05).'),
            ('After moving to 16-way TP across two nodes, TPOT got worse.', '<b>All-reduce over the network is on the critical path.</b> Keep TP within the NVLink domain and use pipeline or data parallelism across nodes (08).'),
        ])),
        section('s-how2', 5, 'How the published engines describe themselves', '''    <div class="visual scroll-x"><table class="tbl">
      <tr><th>Engine</th><th>What its source says it does</th><th>Source</th></tr>
      <tr><td>vLLM</td><td>PagedAttention: near-zero KV waste, flexible KV sharing; 2–4× throughput over FasterTransformer and Orca at the same latency</td><td>Kwon et al., SOSP 2023</td></tr>
      <tr><td>SGLang</td><td>RadixAttention for KV-cache reuse; compressed finite-state machines for structured output; up to 6.4× throughput</td><td>Zheng et al., 2023/24</td></tr>
      <tr><td>TensorRT-LLM</td><td>Custom attention, GEMM and MoE kernels; prefill-decode disaggregation, wide expert parallelism, speculative decoding; FP8/FP4 quantization; prefix caching, chunked context, CUDA graphs</td><td>NVIDIA/TensorRT-LLM README</td></tr>
    </table></div>
    <p class="caption">Feature lists are taken from each project's paper or README. This guide doesn't benchmark engines against each other.</p>'''),
        section('s-why', 6, 'Why a phase-and-resource view works', '''    <div class="grid2">
      <div class="card e"><h3>The physics is simple</h3><p>Prefill is compute-bound and decode is bandwidth- and capacity-bound (GPU deck 02 roofline). Almost every symptom maps to one of a few resources.</p></div>
      <div class="card a"><h3>Techniques compose</h3><p>Continuous batching, paged KV, chunked prefill, quantization and speculative decoding stack, because each targets a different bottleneck.</p></div>
      <div class="card b"><h3>Goodput keeps you honest</h3><p>Measuring throughput only within the SLO stops you from "optimizing" by breaking latency.</p></div>
      <div class="card c"><h3>Interviews test exactly this</h3><p>"Our TTFT doubled after launch: what do you check?" is a phase-and-resource question.</p></div>
    </div>'''),
        myths('s-myth', [
            ('One engine or setting is best for every workload.', 'The right configuration depends on prompt and output lengths, sharing, SLOs, model size and interconnect. Measure goodput on <b>your</b> traffic.'),
            ('Higher GPU utilization means the server is healthy.', 'Utilization can be high while queues grow and SLOs fail. Track <b>goodput and tail latency</b>.'),
            ('Optimizations are independent, so stack them all.', 'Some trade against each other: bigger chunk budgets raise TPOT, more TP raises communication, speculative decoding uses compute that big batches also want.'),
        ]),
        check('s-check', [
            ('mcq', 'TPOT spikes only when long prompts arrive. Which technique targets that first?', ['Prefix caching', 'Chunked prefill', 'INT4 weights', 'More DP replicas'], 1, '<b>Chunked prefill</b> (or disaggregation).'),
            ('open', 'Name four metrics you\'d check first on a struggling LLM server.', 'TTFT and TPOT <b>percentiles</b>, <b>goodput</b> at the SLO, running <b>batch size and queue length</b>, and <b>KV-cache utilization</b>. Prefix-hit rate and GPU bandwidth utilization are good next ones.'),
            ('open', 'Why might speculative decoding help less at very high batch sizes?', 'At large batch, decode moves toward <b>compute-bound</b>, so spare compute for verifying drafts shrinks. Speculative decoding exploits the memory-bound regime.'),
        ]),
    ],
    js='',
    line='Diagnose by phase and resource: measure TTFT, TPOT, goodput, batch, queue and KV, find whether prefill or decode is short of compute, bandwidth or memory, then apply the matching technique.',
    explain='Each serving technique fixes one bottleneck: KV cache for recompute, continuous batching for idle slots, chunked prefill and disaggregation for prefill-decode interference, paging and prefix caching for KV memory, speculative decoding, quantization and tensor parallelism for decode latency. In practice you measure tail TTFT and TPOT, goodput at the SLO, batch size, queue length and KV utilization; decide whether prefill or decode is limited by compute, bandwidth, memory or interconnect; then apply the matching fix and re-measure goodput.',
    recap=[('Problem', 'many knobs; tuning without measurement breaks SLOs or wastes GPUs.'), ('Core idea', 'measure → locate the phase and resource → apply the matching technique → re-check goodput.')],
)
