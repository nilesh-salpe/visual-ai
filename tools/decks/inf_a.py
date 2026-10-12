from tool import section, your_turn, myths, check

DECKS = {}

# =============================================================== 01
DECKS['01-inference-workload'] = dict(
    title='The Inference Workload', h1='The inference workload',
    sub='What happens when a request hits an LLM server: the two phases, the metrics users feel and the ones operators pay for, and why a single "tokens per second" number misleads.',
    prob='Users care about latency, operators care about throughput, and the two pull in opposite directions.',
    core='Separate the work into <b>prefill</b> (the whole prompt at once) and <b>decode</b> (one token at a time). Measure TTFT, TPOT, and <b>goodput</b>: throughput that still meets latency targets.',
    build=['01_tiny_gpt_forward'],
    slides=[
        section('s-p1', 1, 'One request, two very different phases', '''    <p class="lede">A chat request has a prompt of P tokens and generates O output tokens. The server first processes the whole prompt in one pass, which is <b>prefill</b>. Then it generates output tokens one at a time, each depending on the last, which is <b>decode</b>.</p>
    <div class="visual"><svg id="p1Svg" viewBox="0 0 660 150" role="img" aria-label="Prefill then decode timeline"></svg></div>
    <div class="takeaway">Time to first token comes from prefill. The steady stream of tokens after that comes from decode. They are limited by different resources (see the roofline in GPU deck 02).</div>'''),
        section('s-lim', 2, 'Why "tokens per second" isn\'t enough', '''    <div class="grid3">
      <div class="card d"><h3>Throughput hides latency</h3><p>A huge batch maximizes tokens/s for the server while each user waits longer per token.</p></div>
      <div class="card b"><h3>Averages hide tails</h3><p>A good mean latency can coexist with a p99 that breaks the product experience.</p></div>
      <div class="card c"><h3>Two phases, one number</h3><p>Prefill speed (prompt tokens/s) and decode speed (output tokens/s) behave differently and need different fixes.</p></div>
    </div>'''),
        your_turn('s-turn', 'Pick the right metric',
                  'Which metric captures "how much load the server handles while still meeting its latency targets"?',
                  ['Peak tokens per second', 'Goodput: requests per second served within the TTFT and TPOT SLOs', 'GPU utilization', 'Average end-to-end latency'], 1,
                  '<b>B.</b> DistServe defines <b>goodput</b> as the request rate a system can serve while meeting its time-to-first-token and time-per-output-token targets. Peak tokens/s ignores latency, utilization can be high while users wait, and averages hide tails.'),
        section('s-core', 4, 'The four numbers that describe a serving system', '''    <div class="grid2">
      <div class="card a"><h3>TTFT: time to first token</h3><p>Queueing plus prefill of the prompt. Grows with prompt length. Users feel it as "how long until it starts typing".</p></div>
      <div class="card b"><h3>TPOT: time per output token</h3><p>Time per decode step, also called inter-token latency. Users feel it as streaming speed.</p></div>
      <div class="card c"><h3>Throughput</h3><p>Tokens (or requests) per second across all users. This is what the operator pays for.</p></div>
      <div class="card e"><h3>Goodput</h3><p>Throughput counted only while TTFT and TPOT stay within their SLOs. It's the metric that matters (DistServe, OSDI '24).</p></div>
    </div>'''),
        section('s-how', 5, 'Batching trades TPOT for throughput <span class="ill">illustrative step-time model</span>', '''    <p class="lede">A decode step reads all the weights once whatever the batch size, so batching raises throughput. Each step also gets a little slower as the batch grows. Set a TPOT SLO and find the largest batch that still meets it.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">TPOT SLO <input type="range" id="sloT" min="20" max="80" step="1" value="40"> <output id="sloTo"></output></label>
        <label class="ctl">Batch <input type="range" id="bB" min="0" max="8" step="0.1" value="5"> <output id="bBo"></output></label>
      </div>
      <svg id="gpSvg" viewBox="0 0 660 260" style="margin-top:10px" role="img" aria-label="Throughput vs batch with SLO"></svg>
      <div class="grid4">
        <div class="stat"><div class="num" id="kT"></div><div class="lbl">TPOT at this batch</div></div>
        <div class="stat"><div class="num" id="kX"></div><div class="lbl">throughput (tokens/s)</div></div>
        <div class="stat"><div class="num" id="kB"></div><div class="lbl">largest batch within SLO</div></div>
        <div class="stat"><div class="num" id="kG" style="color:var(--e)"></div><div class="lbl">goodput (tokens/s)</div></div>
      </div>
    </div>
    <p class="caption">Toy model: step time = 18 ms + 0.12 ms × batch. Real curves come from the roofline: memory-bound at small batch, then compute-bound (GPU deck 02).</p>'''),
        section('s-how2', 5, 'One request\'s latency, end to end', '''    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">Prompt tokens <input type="range" id="rP" min="7" max="15" step="0.5" value="11"> <output id="rPo"></output></label>
        <label class="ctl">Output tokens <input type="range" id="rO" min="4" max="11" step="0.5" value="8"> <output id="rOo"></output></label>
        <label class="ctl">Prefill speed <select id="rS"><option value="5000">5K tok/s</option><option value="20000" selected>20K tok/s</option><option value="80000">80K tok/s</option></select></label>
        <label class="ctl">TPOT <select id="rD"><option value="15">15 ms</option><option value="30" selected>30 ms</option><option value="60">60 ms</option></select></label>
      </div>
      <svg id="rSvg" viewBox="0 0 660 90" style="margin-top:10px" role="img" aria-label="Latency breakdown"></svg>
      <p class="readout" id="rOut"></p>
    </div>
    <p class="caption">Illustrative speeds. TTFT ≈ prompt ÷ prefill speed (ignoring queueing), and total ≈ TTFT + output tokens × TPOT.</p>'''),
        section('s-why', 6, 'Why splitting the metrics pays off: each one has its own fixes', '''    <div class="visual scroll-x"><table class="tbl">
      <tr><th>Symptom</th><th>Bottleneck</th><th>Techniques (deck)</th></tr>
      <tr><td>Low throughput at small batch</td><td>Decode is memory-bound, so GPU compute sits idle</td><td>Continuous batching (03), quantization (07)</td></tr>
      <tr><td>Can't fit enough requests</td><td>KV-cache memory</td><td>GQA/MLA (02), PagedAttention (05), FP8 KV (07)</td></tr>
      <tr><td>TPOT spikes when long prompts arrive</td><td>Prefill interferes with decode</td><td>Chunked prefill (04), disaggregation (09)</td></tr>
      <tr><td>High TTFT on repeated prompts</td><td>Recomputing shared prefixes</td><td>Prefix caching (05)</td></tr>
      <tr><td>TPOT too slow even at batch 1</td><td>Sequential decode</td><td>Speculative decoding (06), tensor parallelism (08)</td></tr>
    </table></div>'''),
        myths('s-myth', [
            ('Tokens per second tells you how good a server is.', 'Not on its own. Without latency targets it rewards huge batches that make each user wait. Use <b>goodput under SLOs</b>.'),
            ('A bigger batch is always better.', 'Throughput rises, but so does TPOT. Past the SLO limit, extra batch size adds no goodput.'),
            ('TTFT and TPOT have the same bottleneck.', 'TTFT is mostly <b>prefill compute</b> plus queueing. TPOT is mostly <b>memory bandwidth</b> per decode step. They need different fixes.'),
        ]),
        check('s-check', [
            ('open', 'Prompt 2,000 tokens at a prefill speed of 20,000 tokens/s, then 500 output tokens at 30 ms TPOT. Roughly what are TTFT and total latency?', 'TTFT ≈ 2,000 / 20,000 = <b>0.1 s</b>. Decode ≈ 500 × 0.03 = 15 s, so the total is about <b>15.1 s</b>. Decode dominates long answers.'),
            ('mcq', 'Which definition of goodput does DistServe use?', ['Peak tokens/s', 'Request rate served while meeting TTFT and TPOT SLOs', 'GPU FLOPs utilization', 'Requests per GPU'], 1, '<b>Request rate within the latency SLOs</b>.'),
            ('open', 'Why does batching help decode throughput so much?', 'Each decode step must read <b>all the weights</b> anyway. A larger batch reuses that one read for many sequences, moving decode from memory-bound toward compute-bound.'),
        ]),
    ],
    js=r'''
  (() => {
    const s = document.getElementById('p1Svg');
    svg('rect', { x: 20, y: 40, width: 150, height: 40, rx: 6, class: 'f-a' }, s);
    svg('text', { x: 95, y: 65, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:700', text: 'prefill (P tokens)' }, s);
    for (let i = 0; i < 14; i++) svg('rect', { x: 178 + i * 32, y: 40, width: 28, height: 40, rx: 4, style: 'fill:var(--b)' }, s);
    svg('text', { x: 400, y: 100, 'text-anchor': 'middle', class: 'tm', text: 'decode: one token per step, each step reads all weights + KV cache' }, s);
    svg('line', { x1: 172, x2: 172, y1: 26, y2: 92, style: 'stroke:var(--d);stroke-width:2;stroke-dasharray:4 3' }, s);
    svg('text', { x: 172, y: 20, 'text-anchor': 'middle', class: 't', style: 'fill:var(--d);font-size:11px;font-weight:600', text: 'first token (TTFT)' }, s);
    svg('text', { x: 210, y: 130, class: 'tm', style: 'font-size:11px', text: '↔ TPOT = time between tokens' }, s);
  })();
  const step = b => 18 + 0.12 * b;
  const gp = () => {
    const slo = Deck.val('sloT'), b = Math.round(Math.pow(2, Deck.val('bB')));
    Deck.out('sloTo', slo + ' ms'); Deck.out('bBo', b);
    const bmax = Math.max(0, Math.floor((slo - 18) / 0.12));
    Deck.out('kT', step(b).toFixed(1) + ' ms'); Deck.out('kX', fmt(b / step(b) * 1000, 0));
    Deck.out('kB', bmax ? bmax : 'none'); Deck.out('kG', bmax ? fmt(Math.min(b, bmax) / step(Math.min(b, bmax)) * 1000, 0) : '0');
    document.getElementById('kT').style.color = step(b) <= slo ? 'var(--e)' : 'var(--d)';
    const s = clear(document.getElementById('gpSvg')), L = 60, R = 640, T = 14, B = 220;
    const X = x => L + Math.log2(x) / 8 * (R - L), ymax = 256 / step(256) * 1000 * 1.1, Y = v => B - v / ymax * (B - T);
    if (bmax < 256) svg('rect', { x: X(Math.max(1, bmax)), y: T, width: R - X(Math.max(1, bmax)), height: B - T, style: 'fill:var(--d-soft)' }, s);
    [1, 4, 16, 64, 256].forEach(v => { svg('line', { x1: X(v), x2: X(v), y1: T, y2: B, class: 'ln' }, s); svg('text', { x: X(v), y: B + 16, 'text-anchor': 'middle', class: 'tm tc', text: v }, s); });
    let pts = ''; for (let v = 1; v <= 256; v *= 1.05) pts += `${X(v)},${Y(v / step(v) * 1000)} `;
    svg('polyline', { points: pts, fill: 'none', style: 'stroke:var(--a);stroke-width:3' }, s);
    svg('circle', { cx: X(b), cy: Y(b / step(b) * 1000), r: 7, style: `fill:${step(b) <= slo ? 'var(--a)' : 'var(--d)'};stroke:var(--panel);stroke-width:2` }, s);
    svg('text', { x: (L + R) / 2, y: B + 34, 'text-anchor': 'middle', class: 'tm', text: 'batch size (red zone violates the TPOT SLO)' }, s);
    svg('text', { x: 14, y: (T + B) / 2, 'text-anchor': 'middle', class: 'tm', transform: `rotate(-90 14 ${(T + B) / 2})`, text: 'tokens / s' }, s);
  };
  Deck.bind(['sloT', 'bB'], gp);
  const lat = () => {
    const P = Math.round(Math.pow(2, Deck.val('rP'))), O = Math.round(Math.pow(2, Deck.val('rO'))), sp = +Deck.val('rS'), d = +Deck.val('rD');
    Deck.out('rPo', P.toLocaleString()); Deck.out('rOo', O.toLocaleString());
    const ttft = P / sp, dec = O * d / 1000, tot = ttft + dec;
    const s = clear(document.getElementById('rSvg')), W = 620;
    svg('rect', { x: 20, y: 20, width: Math.max(2, W * ttft / tot), height: 34, rx: 4, class: 'f-a' }, s);
    svg('rect', { x: 20 + W * ttft / tot, y: 20, width: W * dec / tot, height: 34, rx: 4, style: 'fill:var(--b)' }, s);
    svg('text', { x: 20, y: 76, class: 'tm', style: 'font-size:11px', text: `prefill ${(ttft * 1000).toFixed(0)} ms` }, s);
    svg('text', { x: 640, y: 76, 'text-anchor': 'end', class: 'tm', style: 'font-size:11px', text: `decode ${dec.toFixed(2)} s` }, s);
    document.getElementById('rOut').innerHTML = `TTFT ≈ <b>${(ttft * 1000).toFixed(0)} ms</b> · total ≈ <b>${tot.toFixed(2)} s</b> · decode is ${(100 * dec / tot).toFixed(0)}% of the time`;
  };
  Deck.bind(['rP', 'rO', 'rS', 'rD'], lat);
''',
    line='Serving is two workloads, a compute-bound prefill and a memory-bound decode, judged by TTFT, TPOT and goodput under SLOs.',
    explain='An LLM request has a prefill phase that processes the whole prompt in one pass, which sets the time to first token, and a decode phase that generates one token per step, which sets the time per output token. Throughput is what operators pay for, but bigger batches slow each step, so the right metric is goodput: the load you can serve while TTFT and TPOT stay within their SLOs. Each later technique targets one of these bottlenecks.',
    recap=[('Problem', 'latency and throughput conflict, and a single tokens/s number hides that.'), ('Core idea', 'separate prefill and decode, measure TTFT, TPOT and goodput, then fix each bottleneck.')],
)

# =============================================================== 02
DECKS['02-kv-cache'] = dict(
    title='KV Cache', h1='The KV cache',
    sub='Why every LLM server stores past keys and values, how much memory that takes, and how GQA and MLA shrink it.',
    prob='Without caching, generating token t re-runs attention over all t previous tokens, so total work grows quadratically.',
    core='Store each layer\'s <b>K and V</b> for every past token. A new token computes only its own q, k and v and attends over the cache. The result is exact, but memory grows with context × batch.',
    build=['02_kv_cache', '03_gqa_mqa', '04_kv_memory_calculator'],
    slides=[
        section('s-p1', 1, 'Naive generation redoes almost all of its work', '''    <p class="lede">Generating token <i>t</i> needs attention between the new token and all <i>t</i> previous tokens. A naive loop re-runs the full forward pass over the whole prefix for every new token.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">Prompt <input type="range" id="nP" min="16" max="2048" step="16" value="512"> <output id="nPo"></output></label>
        <label class="ctl">New tokens <input type="range" id="nN" min="16" max="2048" step="16" value="512"> <output id="nNo"></output></label>
      </div>
      <div id="nBars" style="margin-top:12px"></div>
    </div>
    <p class="caption">Token positions processed by the forward pass: naive = Σ (prompt + i) for i &lt; n; cached = prompt + n.</p>'''),
        section('s-lim', 2, 'Recomputing is pure waste', '''    <div class="grid3">
      <div class="card d"><h3>Same K and V every time</h3><p>Past tokens' keys and values don't change when a new token arrives, because causal masking means earlier positions never see later ones.</p></div>
      <div class="card b"><h3>Quadratic total work</h3><p>Generating n tokens costs about n²/2 token-passes, so long answers get disproportionately slow.</p></div>
      <div class="card c"><h3>Latency grows each step</h3><p>Every step is slower than the one before it, so TPOT keeps rising throughout the answer.</p></div>
    </div>'''),
        your_turn('s-turn', 'What should be cached?',
                  'To avoid recomputation during decoding, which tensors from past tokens should be stored?',
                  ['The final logits', 'The queries (Q)', 'The keys and values (K, V) of every layer', 'The attention weights'], 2,
                  '<b>C.</b> A new token needs <em>its own</em> query and <em>everyone\'s</em> keys and values. Past queries are never used again, and attention weights change with every new token.'),
        section('s-core', 4, 'Cache K and V per layer; compute only the new token', '''    <div class="grid3">
      <div class="card a"><h3>Prefill</h3><p>Run the prompt once and store K and V for every layer and position.</p></div>
      <div class="card b"><h3>Decode step</h3><p>Compute q, k and v for the new token only, append k and v to the cache, then attend q over the cache.</p></div>
      <div class="card e"><h3>Exact</h3><p>The logits are identical to full recomputation. The cache trades compute for <b>memory</b>.</p></div>
    </div>
    <div class="eq">KV bytes = 2 × layers × kv_heads × head_dim × bytes/element × tokens × batch</div>'''),
        section('s-how', 5, 'KV-cache memory calculator', '''    <div class="visual">
      <div class="controls" style="margin-top:0">
        <select id="mM"><option value="32,8,128,16">8B-shaped (32 layers, 8 KV heads)</option><option value="80,8,128,140" selected>70B-shaped (80 layers, 8 KV heads)</option><option value="80,64,128,140">70B-shaped without GQA (64 KV heads)</option></select>
        <label class="ctl">Context <input type="range" id="mC" min="10" max="17" step="1" value="13"> <output id="mCo"></output></label>
        <label class="ctl">Batch <input type="range" id="mB" min="0" max="8" step="1" value="5"> <output id="mBo"></output></label>
        <div class="seg" id="mD"><button data-v="2" class="on">BF16</button><button data-v="1">FP8</button></div>
      </div>
      <div class="grid3" style="margin-top:14px">
        <div class="stat"><div class="num" id="mTok"></div><div class="lbl">KV per token</div></div>
        <div class="stat"><div class="num" id="mTot" style="color:var(--b)"></div><div class="lbl">total KV cache</div></div>
        <div class="stat"><div class="num" id="mW"></div><div class="lbl">weights (BF16) for comparison</div></div>
      </div>
      <div id="mBars" style="margin-top:12px"></div>
    </div>
    <p class="caption">Shapes match Llama-3-8B and 70B (head_dim 128). At long context or large batch the cache exceeds the weights.</p>'''),
        section('s-how2', 5, 'Shrinking the cache: MQA, GQA and MLA', '''    <p class="lede">The cache scales with the number of <b>key/value heads</b>. Let several query heads share one KV head.</p>
    <div class="visual">
      <div class="seg" id="gSeg"><button data-v="8">MHA (8 KV heads)</button><button data-v="2" class="on">GQA (2 KV heads)</button><button data-v="1">MQA (1 KV head)</button></div>
      <svg id="gSvg" viewBox="0 0 660 170" style="margin-top:10px" role="img" aria-label="Query heads sharing KV heads"></svg>
      <p class="readout" id="gOut"></p>
    </div>
    <div class="grid2" style="margin-top:12px">
      <div class="card a"><h3>GQA (Ainslie et al., EMNLP 2023)</h3><p>Between MHA and MQA. Quality close to MHA at speeds comparable to MQA, and MHA checkpoints can be "uptrained" with about 5% of the original pre-training compute.</p></div>
      <div class="card c"><h3>MLA (DeepSeek-V2, 2024)</h3><p>Compresses K and V into a latent vector: <b>93.3%</b> smaller KV cache and <b>5.76×</b> max generation throughput compared with DeepSeek 67B.</p></div>
    </div>'''),
        section('s-why', 6, 'Why the KV cache shapes everything else', '''    <div class="grid2">
      <div class="card e"><h3>Compute becomes cheap</h3><p>Each step does work for one token, so decode is dominated by <b>reading</b> weights and cache.</p></div>
      <div class="card d"><h3>Memory becomes the limit</h3><p>Batch size × context is capped by KV memory, so concurrency depends on the cache's size.</p></div>
      <div class="card b"><h3>It drives later techniques</h3><p>Paging (05), prefix sharing (05), FP8 KV (07), and moving KV between pools (09) all manage this cache.</p></div>
      <div class="card c"><h3>Architecture responds</h3><p>GQA, MQA and MLA are architecture changes made largely to shrink this cache.</p></div>
    </div>'''),
        myths('s-myth', [
            ('Using a KV cache changes the model\'s outputs.', 'It is <b>exact</b>: logits match full recomputation, because causal attention never lets past positions see the future.'),
            ('You should cache the queries too.', 'Queries are needed only for the <b>current</b> token. Past queries are never reused.'),
            ('The KV cache is small compared with the weights.', 'At long context it isn\'t: a 70B-shaped model with GQA needs <b>40 GiB per sequence at 128K tokens</b> in BF16.'),
        ]),
        check('s-check', [
            ('mcq', 'KV bytes per token for 80 layers, 8 KV heads, head_dim 128, BF16?', ['32 KB', '320 KB', '3.2 MB', '2.6 MB'], 1, '2 × 80 × 8 × 128 × 2 = <b>327,680 bytes ≈ 320 KB</b>.'),
            ('mcq', '64 query heads sharing 8 KV heads makes the cache how much smaller than MHA?', ['2×', '8×', '64×', 'No change'], 1, '<b>8×</b>: the cache scales with KV heads (64 / 8).'),
            ('open', 'Why can\'t you avoid the cache by just making attention faster?', 'Without a cache, every step reprocesses the whole prefix (quadratic total work). A faster kernel speeds up each pass but doesn\'t remove that redundant work.'),
        ]),
    ],
    js=r'''
  Deck.bind(['nP', 'nN'], () => {
    const p = Deck.val('nP'), n = Deck.val('nN'); Deck.out('nPo', p); Deck.out('nNo', n);
    const naive = n * p + n * (n - 1) / 2, cached = p + n;
    Deck.hbars(document.getElementById('nBars'), [
      { label: 'naive (recompute prefix)', value: naive, color: 'var(--d)', text: fmt(naive) + ' positions' },
      { label: 'KV cache', value: cached, color: 'var(--e)', text: fmt(cached) + ' positions · ' + (naive / cached).toFixed(0) + '× less' },
    ], { log: true, min: 10 });
  });
  let dt = 2;
  const kv = () => {
    const [L, H, d, w] = Deck.val('mM').split(',').map(Number), C = 2 ** Deck.val('mC'), B = 2 ** Deck.val('mB');
    Deck.out('mCo', C >= 1024 ? C / 1024 + 'K' : C); Deck.out('mBo', B);
    const per = 2 * L * H * d * dt, tot = per * C * B;
    Deck.out('mTok', Deck.bytes(per)); Deck.out('mTot', Deck.bytes(tot)); Deck.out('mW', w + ' GB');
    Deck.hbars(document.getElementById('mBars'), [{ label: 'weights', value: w * 1e9, color: 'var(--faint)', text: w + ' GB' }, { label: 'KV cache', value: tot, color: tot > w * 1e9 ? 'var(--d)' : 'var(--b)', text: (tot / 1e9).toFixed(1) + ' GB' }], { log: true, min: 1e8 });
  };
  Deck.seg('mD', v => { dt = +v; if (document.getElementById('mM')) kv(); });
  Deck.bind(['mM', 'mC', 'mB'], kv);
  Deck.seg('gSeg', v => {
    const hk = +v, s = clear(document.getElementById('gSvg')), H = 8;
    for (let h = 0; h < H; h++) {
      const x = 40 + h * 75, g = Math.floor(h / (H / hk)), gx = 40 + (g + .5) * (600 / hk) - 30;
      svg('line', { x1: x + 25, y1: 50, x2: gx + 30, y2: 110, style: `stroke:${['var(--a)', 'var(--b)', 'var(--c)', 'var(--e)', 'var(--d)', '#3a8fd8', '#c9a227', '#8a6d3b'][g]};stroke-width:2;opacity:.7` }, s);
      svg('rect', { x, y: 18, width: 50, height: 32, rx: 6, class: 'f-a' }, s);
      svg('text', { x: x + 25, y: 39, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11px;font-weight:600', text: 'Q' + h }, s);
    }
    for (let g = 0; g < hk; g++) {
      const gx = 40 + (g + .5) * (600 / hk) - 30;
      svg('rect', { x: gx, y: 110, width: 60, height: 34, rx: 6, style: `fill:${['var(--a)', 'var(--b)', 'var(--c)', 'var(--e)', 'var(--d)', '#3a8fd8', '#c9a227', '#8a6d3b'][g]}` }, s);
      svg('text', { x: gx + 30, y: 132, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11px;font-weight:600', text: 'KV' + g }, s);
    }
    document.getElementById('gOut').innerHTML = `${H} query heads share <b>${hk}</b> KV head${hk > 1 ? 's' : ''} → KV cache is <b>${H / hk}×</b> smaller than MHA`;
  });
''',
    line='The KV cache stores past keys and values so each decode step computes only one new token. It is exact, but its memory (2 × layers × kv_heads × head_dim × bytes × tokens × batch) becomes the main serving constraint.',
    explain='Without a cache, generating each token reprocesses the whole prefix, so total work is quadratic. The KV cache stores every layer\'s keys and values for past tokens; a new token computes its own q, k and v and attends over the cache, giving identical logits. Its size is 2 × layers × KV heads × head_dim × bytes × tokens × batch, about 320 KB per token for a 70B-shaped model, so at long context it limits concurrency. GQA, MQA and MLA shrink it; MLA reported a 93.3% reduction.',
    recap=[('Problem', 'naive decoding recomputes the whole prefix every step.'), ('Core idea', 'cache K and V; exact, linear work per step, memory grows with context × batch; shrink it with GQA or MLA.')],
)

# =============================================================== 03
DECKS['03-batching'] = dict(
    title='Continuous Batching', h1='Continuous batching',
    sub='Iteration-level scheduling (Orca, OSDI 2022): admit and retire requests at every decode step instead of running fixed batches to completion.',
    prob='Decode at batch 1 wastes the GPU. Static batches, though, hold every slot until the longest request finishes, and new arrivals have to wait.',
    core='Schedule at the granularity of <b>one iteration</b>: finished requests leave and waiting requests join between every decode step.',
    build=['05_continuous_batching'],
    slides=[
        section('s-p1', 1, 'One sequence at a time leaves the GPU idle', '''    <p class="lede">A decode step reads all the weights to produce one token per sequence. With one sequence, that read serves one token. Batching lets the same read serve many sequences, which is why servers batch.</p>
    <div class="takeaway">Batching is how decode gets from memory-bound toward compute-bound (GPU deck 02, the roofline).</div>'''),
        section('s-lim', 2, 'Static batching wastes slots and makes requests wait', '''    <p class="lede">Static (request-level) batching groups requests and runs the group until its <b>longest</b> member finishes. Short requests sit idle in their slots, and new arrivals can't join a running batch.</p>
    <div class="grid2">
      <div class="card d"><h3>Finished but still occupying a slot</h3><p>Requests produce different numbers of tokens. Early finishers can't be replaced until the whole batch ends.</p></div>
      <div class="card b"><h3>Queueing delay</h3><p>A request arriving just after a batch starts waits for the whole batch to finish.</p></div>
    </div>'''),
        your_turn('s-turn', 'Choose the scheduling granularity',
                  'At what granularity should the scheduler decide which requests run?',
                  ['Per request: run each batch to completion', 'Per iteration: re-decide at every decode step', 'Once per minute', 'Per layer'], 1,
                  '<b>B.</b> Orca\'s <b>iteration-level scheduling</b> re-forms the batch at every model iteration. A request that finishes returns immediately and a waiting request takes its slot on the next step.'),
        section('s-core', 4, 'Iteration-level scheduling + selective batching', '''    <div class="grid2">
      <div class="card a"><h3>Iteration-level scheduling</h3><p>Between every decode iteration, retire finished sequences and admit new ones, up to the batch or memory limit.</p></div>
      <div class="card c"><h3>Selective batching</h3><p>Requests at different positions have different lengths. Orca batches the operations that don't depend on length (the linear layers) and handles attention per request.</p></div>
    </div>'''),
        section('s-how', 5, 'Static vs continuous, simulated', '''    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">Max batch <input type="range" id="cbB" min="2" max="8" step="1" value="4"> <output id="cbBo"></output></label>
        <button class="btn" id="cbNew">New requests</button>
      </div>
      <div class="grid2" style="margin-top:10px">
        <div><h3>Static batching</h3><svg id="stSvg" viewBox="0 0 320 200" role="img" aria-label="Static batching slots"></svg><p class="readout" id="stOut"></p></div>
        <div><h3>Continuous batching</h3><svg id="ctSvg" viewBox="0 0 320 200" role="img" aria-label="Continuous batching slots"></svg><p class="readout" id="ctOut"></p></div>
      </div>
      <div class="legend"><span><i style="background:var(--a)"></i>generating tokens</span><span><i style="background:var(--d-soft);border:1px solid var(--d)"></i>slot held but idle (static)</span></div>
    </div>
    <p class="caption">Each row is a batch slot over time; each coloured bar is one request. The simulation uses the same rules as Build-it notebook 05.</p>'''),
        section('s-why', 6, 'Why it works', '''    <div class="grid2">
      <div class="card e"><h3>No idle slots</h3><p>A slot is refilled on the very next iteration, so the batch stays full whenever requests are waiting.</p></div>
      <div class="card a"><h3>Less queueing</h3><p>New requests start within one iteration instead of waiting for a batch to drain.</p></div>
      <div class="card b"><h3>Measured</h3><p>On GPT-3 175B, Orca reported a <b>36.9×</b> throughput improvement over NVIDIA FasterTransformer at the same latency.</p></div>
      <div class="card c"><h3>Foundation for what follows</h3><p>Paged KV (05) and chunked prefill (04) both build on per-iteration scheduling.</p></div>
    </div>'''),
        myths('s-myth', [
            ('Continuous batching just means a bigger batch.', 'The batch size limit can be the same. What changes is <b>when</b> membership changes: at every iteration rather than per batch.'),
            ('Batched requests must have the same length.', 'Iteration-level scheduling mixes requests at different positions. Orca\'s selective batching handles the length-dependent attention part.'),
            ('Batching always increases user latency.', 'Each step gets a little slower, but removing queueing usually <b>lowers</b> end-to-end latency, as the simulation shows.'),
        ]),
        check('s-check', [
            ('mcq', 'What problem of static batching does iteration-level scheduling fix?', ['Too much KV memory', 'Slots held by finished requests and new requests waiting', 'Low prefill speed', 'Quantization error'], 1, 'Finished requests <b>free their slots immediately</b> and new ones join at the next iteration.'),
            ('mcq', 'What did Orca report on GPT-3 175B versus FasterTransformer at the same latency?', ['2×', '5.6×', '36.9×', '100×'], 2, '<b>36.9×</b> throughput (Orca, OSDI \'22).'),
            ('open', 'Why does continuous batching need careful memory management?', 'Requests join and leave constantly, with KV caches of unpredictable length. That calls for dynamic allocation, which PagedAttention provides (deck 05).'),
        ]),
    ],
    js=r'''
  let seed = 3;
  const rng = s => () => { s |= 0; s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  const mk = () => { const r = rng(seed); let t = 0; return [...Array(14)].map((_, i) => { t += Math.floor(r() * 4); return { id: i, arrival: t, out: 3 + Math.floor(r() * r() * 22) }; }); };
  const staticSim = (reqs, B) => { const res = {}; let t = 0; for (let i = 0; i < reqs.length; i += B) { const g = reqs.slice(i, i + B), st = Math.max(t, ...g.map(q => q.arrival)), mx = Math.max(...g.map(q => q.out)); g.forEach((q, k) => res[q.id] = { slot: k, s: st, e: st + q.out, hold: st + mx }); t = st + mx; } return res; };
  const contSim = (reqs, B) => { const res = {}, q = reqs.slice(), slots = Array(B).fill(-1); let t = 0, done = 0; while (done < reqs.length) { for (let k = 0; k < B; k++) if (slots[k] >= 0 && res[slots[k]].e <= t) { slots[k] = -1; done++; } for (let k = 0; k < B; k++) if (slots[k] < 0 && q.length && q[0].arrival <= t) { const r = q.shift(); slots[k] = r.id; res[r.id] = { slot: k, s: t, e: t + r.out, hold: t + r.out }; } if (slots.every(x => x < 0)) { if (q.length) t = q[0].arrival; else break; continue; } t++; } return res; };
  const draw = (el, res, reqs, B, T) => {
    const s = clear(el), w = 300 / T, h = Math.min(30, 180 / B);
    for (let k = 0; k < B; k++) svg('rect', { x: 10, y: 10 + k * h, width: 300, height: h - 3, style: 'fill:var(--panel-2)' }, s);
    reqs.forEach(q => { const r = res[q.id]; if (r.hold > r.e) svg('rect', { x: 10 + r.e * w, y: 10 + r.slot * h, width: (r.hold - r.e) * w, height: h - 3, style: 'fill:var(--d-soft);stroke:var(--d);stroke-width:.5' }, s); svg('rect', { x: 10 + r.s * w, y: 10 + r.slot * h, width: Math.max(1, q.out * w - 1), height: h - 3, rx: 2, style: `fill:${['var(--a)', 'var(--b)', 'var(--c)', 'var(--e)', '#3a8fd8', '#c9a227'][q.id % 6]}` }, s); });
    el.setAttribute('viewBox', `0 0 320 ${20 + B * h}`);
  };
  const run = () => {
    const B = Deck.val('cbB'); Deck.out('cbBo', B);
    const reqs = mk(), st = staticSim(reqs, B), ct = contSim(reqs, B);
    const T = Math.max(...Object.values(st).map(r => r.hold), ...Object.values(ct).map(r => r.e)) + 1;
    draw(document.getElementById('stSvg'), st, reqs, B, T); draw(document.getElementById('ctSvg'), ct, reqs, B, T);
    const m = res => { const fin = Math.max(...Object.values(res).map(r => r.e)); const lat = reqs.map(q => res[q.id].e - q.arrival); return `done at step <b>${fin}</b> · mean latency <b>${(lat.reduce((a, b) => a + b, 0) / lat.length).toFixed(1)}</b> steps`; };
    document.getElementById('stOut').innerHTML = m(st); document.getElementById('ctOut').innerHTML = m(ct);
  };
  document.getElementById('cbNew').onclick = () => { seed++; run(); };
  Deck.bind(['cbB'], run);
''',
    line='Continuous batching re-forms the batch at every decode iteration: finished requests leave and new ones join immediately, so slots never sit idle.',
    explain='Decode needs batching to use the GPU, but static batching runs each batch until its longest request finishes, wasting slots and making new requests wait. Orca introduced iteration-level scheduling: the server re-decides the batch between every decode step, with selective batching for the length-dependent attention. It reported 36.9× throughput over FasterTransformer at the same latency on GPT-3 175B, and it\'s now standard in LLM servers.',
    recap=[('Problem', 'static batches hold finished requests\' slots and make new arrivals wait.'), ('Core idea', 'iteration-level scheduling: admit and retire requests at every decode step.')],
)

# =============================================================== 04
DECKS['04-chunked-prefill'] = dict(
    title='Chunked Prefill', h1='Chunked prefill',
    sub='Splitting long prompts into chunks so they share each iteration with ongoing decodes instead of stalling them (Sarathi-Serve, 2024).',
    prob='When a long prompt arrives, its prefill either stalls every running decode or waits behind them. Either throughput or latency suffers.',
    core='Give each iteration a <b>token budget</b>: decodes go first (stall-free), and the rest of the budget goes to <b>chunks</b> of waiting prefills.',
    build=['06_chunked_prefill'],
    slides=[
        section('s-p1', 1, 'Prefill and decode compete for the same iterations', '''    <div class="grid2">
      <div class="card a"><h3>Prefill</h3><p>Hundreds to thousands of tokens in one pass. Compute-heavy and slow per iteration.</p></div>
      <div class="card b"><h3>Decode</h3><p>One token per running request. Fast, but uses little of the GPU's compute.</p></div>
    </div>
    <div class="takeaway">Naively interleaving the two makes it hard to get high throughput and low latency at the same time (Sarathi-Serve).</div>'''),
        section('s-lim', 2, 'Two naive policies, two failure modes', '''    <div class="vs">
      <div class="card d"><h3>Prefill-first</h3><p>Run a new prompt's whole prefill as soon as it arrives. Every running decode <b>stalls</b> behind that long iteration, causing TPOT spikes.</p></div>
      <div class="card b"><h3>Decode-first</h3><p>Finish decodes before admitting prefills. New requests wait, which hurts TTFT, and decode-only batches underuse compute.</p></div>
    </div>'''),
        your_turn('s-turn', 'Avoid both failure modes',
                  'How can new prompts make progress without stalling running decodes?',
                  ['Only run prefills when no decodes are active', 'Split each prefill into chunks and add them to each iteration alongside the decodes, under a token budget', 'Reject long prompts', 'Run prefill on the CPU'], 1,
                  '<b>B.</b> With a per-iteration token budget, decodes take their one token each first, and the leftover budget goes to prefill chunks. Iterations stay short and predictable, and prefills still progress every step.'),
        section('s-core', 4, 'Chunked prefills + stall-free scheduling', '''    <div class="grid3">
      <div class="card a"><h3>Token budget</h3><p>Each iteration processes at most B tokens in total, which bounds iteration time and therefore TPOT.</p></div>
      <div class="card b"><h3>Decodes first</h3><p>Every running request gets its token, so decodes never stall.</p></div>
      <div class="card e"><h3>Prefill chunks fill the rest</h3><p>Waiting prompts are processed in near-equal chunks. The first output token appears when the last chunk finishes.</p></div>
    </div>'''),
        section('s-how', 5, 'Tokens per iteration: prefill-first vs chunked', '''    <div class="visual">
      <label class="ctl">Token budget B <input type="range" id="ckB" min="64" max="1024" step="64" value="256"> <output id="ckBo"></output></label>
      <h3 style="margin-top:10px">Prefill-first (whole prompts at once)</h3><svg id="pfSvg" viewBox="0 0 660 120" role="img" aria-label="Prefill-first iterations"></svg>
      <h3>Chunked (decodes first, then prefill chunks)</h3><svg id="ckSvg" viewBox="0 0 660 120" role="img" aria-label="Chunked iterations"></svg>
      <div class="legend"><span><i style="background:var(--b)"></i>decode tokens</span><span><i style="background:var(--a)"></i>prefill tokens</span><span><i style="background:var(--d)"></i>iteration larger than the budget</span></div>
      <p class="readout" id="ckOut"></p>
    </div>
    <p class="caption">Same request trace for both, from the rules in Build-it notebook 06. Bar height = tokens processed in that iteration, a proxy for iteration time.</p>'''),
        section('s-why', 6, 'Why it works', '''    <div class="grid2">
      <div class="card e"><h3>Predictable TPOT</h3><p>Every iteration is bounded by B tokens, so no decode waits behind a huge prefill.</p></div>
      <div class="card a"><h3>Better utilization</h3><p>Decodes ride along with compute-heavy prefill chunks, filling the GPU's otherwise idle compute.</p></div>
      <div class="card b"><h3>One knob</h3><p>A smaller B means smoother TPOT but more iterations to finish a long prompt (higher TTFT), and a larger B the reverse.</p></div>
      <div class="card c"><h3>Measured (vs vLLM, under latency SLOs)</h3><p>Sarathi-Serve: <b>2.6×</b> capacity (Mistral-7B, 1×A100), up to <b>3.7×</b> (Yi-34B, 2×A100), up to <b>5.6×</b> (Falcon-180B with pipeline parallelism).</p></div>
    </div>'''),
        myths('s-myth', [
            ('Chunking changes the model\'s output.', 'No. Attention over earlier chunks uses the KV cache, so the result is the same as a single prefill pass.'),
            ('A bigger budget is always better.', 'A bigger B finishes prompts sooner but allows longer iterations, which brings back TPOT spikes. It\'s a <b>trade-off</b>.'),
            ('Chunked prefill only helps long prompts.', 'It also raises <b>utilization</b>, because decode-only iterations underuse compute and the chunks fill that gap.'),
        ]),
        check('s-check', [
            ('mcq', 'In stall-free scheduling, what gets the budget first?', ['New prefills', 'Running decodes, one token each', 'The longest prompt', 'Whichever arrived last'], 1, '<b>Decodes first</b>, so they never stall. Prefill chunks use what\'s left.'),
            ('open', 'What happens to TTFT and TPOT as the token budget B shrinks?', 'TPOT becomes smoother and lower (short iterations), but <b>TTFT rises</b> because long prompts need more iterations to finish prefill.'),
            ('mcq', 'What serving-capacity gain did Sarathi-Serve report for Mistral-7B on one A100 vs vLLM?', ['1.1×', '2.6×', '6.4×', '36.9×'], 1, '<b>2.6×</b> under tail-latency constraints.'),
        ]),
    ],
    js=r'''
  const reqs = (() => { let s = 7; const r = () => { s = (s * 1103515245 + 12345) % 2147483648; return s / 2147483648; }; let t = 0; return [...Array(14)].map((_, i) => { t += Math.floor(r() * 4); return { id: i, arrival: t, P: [64, 128, 512, 1500][Math.floor(r() * 4)], O: 5 + Math.floor(r() * 30) }; }); })();
  const prefillFirst = () => { let i = 0, t = 0; const dec = [], left = {}, its = []; while (i < reqs.length || dec.length) { const w = []; while (i < reqs.length && reqs[i].arrival <= t) w.push(reqs[i++]); if (w.length) { its.push({ d: 0, p: w.reduce((a, r) => a + r.P, 0) }); w.forEach(r => { left[r.id] = r.O - 1; if (left[r.id] > 0) dec.push(r); }); } else if (dec.length) { its.push({ d: dec.length, p: 0 }); for (const r of dec.slice()) { if (--left[r.id] === 0) dec.splice(dec.indexOf(r), 1); } } else { t = reqs[i].arrival; continue; } t++; } return its; };
  const chunked = B => { const pre = {}, left = {}; reqs.forEach(r => { pre[r.id] = r.P; left[r.id] = r.O; }); const dec = [], its = []; let t = 0, done = 0; while (done < reqs.length) { let used = 0, d = 0; for (const r of dec.slice()) { used++; d++; if (--left[r.id] === 0) { dec.splice(dec.indexOf(r), 1); done++; } } for (const r of reqs) { if (r.arrival > t || pre[r.id] === 0 || used >= B) continue; const c = Math.min(pre[r.id], B - used); pre[r.id] -= c; used += c; if (pre[r.id] === 0) { if (--left[r.id] === 0) done++; else dec.push(r); } } if (!used) { t = Math.min(...reqs.filter(r => pre[r.id] > 0).map(r => r.arrival)); continue; } its.push({ d, p: used - d }); t++; } return its; };
  const bars = (el, its, cap, ymax) => { const s = clear(el), w = 640 / Math.max(its.length, 60); its.forEach((it, k) => { const hd = 100 * it.d / ymax, hp = 100 * it.p / ymax; svg('rect', { x: 10 + k * w, y: 110 - hd, width: Math.max(1, w - 1), height: hd, style: 'fill:var(--b)' }, s); svg('rect', { x: 10 + k * w, y: 110 - hd - hp, width: Math.max(1, w - 1), height: hp, style: `fill:${cap && it.d + it.p > cap ? 'var(--d)' : 'var(--a)'}` }, s); }); if (cap) { const y = 110 - 100 * cap / ymax; svg('line', { x1: 10, x2: 650, y1: y, y2: y, style: 'stroke:var(--ink);stroke-dasharray:4 3' }, s); svg('text', { x: 650, y: y - 4, 'text-anchor': 'end', class: 'tm tc', style: 'font-size:10px', text: 'budget ' + cap }, s); } };
  Deck.bind(['ckB'], () => {
    const B = Deck.val('ckB'); Deck.out('ckBo', B);
    const pf = prefillFirst(), ck = chunked(B), ymax = Math.max(...pf.map(i => i.d + i.p), B) * 1.05;
    bars(document.getElementById('pfSvg'), pf, B, ymax); bars(document.getElementById('ckSvg'), ck, B, ymax);
    document.getElementById('ckOut').innerHTML = `Largest iteration: prefill-first <b style="color:var(--d)">${Math.max(...pf.map(i => i.d + i.p))}</b> tokens vs chunked <b style="color:var(--e)">${Math.max(...ck.map(i => i.d + i.p))}</b> tokens · chunked needs ${ck.length} iterations vs ${pf.length}.`;
  });
''',
    line='Chunked prefill bounds every iteration with a token budget: decodes go first and prefill chunks fill the rest, so long prompts never stall streaming users.',
    explain='Prefill is compute-heavy and decode is light, and naive schedulers either stall decodes behind a long prefill or delay new requests. Sarathi-Serve splits prefills into chunks and gives each iteration a token budget: running decodes get their token first, then waiting prompts get chunks of whatever budget is left. Iterations stay short and predictable, decodes piggyback on compute-heavy chunks, and it reported 2.6× to 5.6× more serving capacity than vLLM under latency SLOs.',
    recap=[('Problem', 'long prefills stall decodes (TPOT spikes) or wait behind them (TTFT).'), ('Core idea', 'a per-iteration token budget: decodes first, prefill chunks after.')],
)

# =============================================================== 05
DECKS['05-paged-attention'] = dict(
    title='PagedAttention and Prefix Caching', h1='PagedAttention and prefix caching',
    sub='Managing the KV cache like virtual memory (vLLM, SOSP 2023), and reusing the KV of shared prompt prefixes (SGLang\'s RadixAttention).',
    prob='KV caches grow token by token to unknown final lengths. Reserving contiguous memory wastes most of it, and identical prompt prefixes get stored and recomputed again and again.',
    core='Store KV in fixed-size <b>blocks</b> mapped by a per-sequence <b>block table</b>, with reference counts and copy-on-write for sharing. Index cached prefixes in a <b>tree</b> so later requests can reuse them.',
    build=['07_paged_kv_allocator', '08_prefix_cache'],
    slides=[
        section('s-p1', 1, 'The KV cache is dynamic and unpredictable', '''    <div class="grid3">
      <div class="card a"><h3>Grows every step</h3><p>Each generated token appends K and V to every layer's cache.</p></div>
      <div class="card b"><h3>Unknown final length</h3><p>Nobody knows in advance whether a reply will be 10 tokens or 2,000.</p></div>
      <div class="card c"><h3>Lots of sharing</h3><p>Parallel samples, beam search and common system prompts all start from the same prefix.</p></div>
    </div>'''),
        section('s-lim', 2, 'Contiguous reservations waste memory and duplicate shared data', '''    <div class="grid2">
      <div class="card d"><h3>Fragmentation</h3><p>Reserving max-length buffers leaves most slots unused. Uneven sizes also leave gaps between buffers. The vLLM paper calls this waste from "fragmentation and redundant duplication", and it limits batch size.</p></div>
      <div class="card b"><h3>Duplication</h3><p>Each sample of the same prompt gets its own copy of identical K and V. Every request with the same system prompt recomputes it during prefill.</p></div>
    </div>'''),
        your_turn('s-turn', 'Borrow an idea from operating systems',
                  'Which operating-system idea fits the "growing, unpredictable, shareable memory" problem best?',
                  ['Swapping whole processes to disk', 'Paging: fixed-size pages, a page table per process, copy-on-write for shared pages', 'A bigger contiguous heap', 'Garbage collection'], 1,
                  '<b>B.</b> PagedAttention stores each sequence\'s KV in fixed-size <b>blocks</b> (vLLM\'s default is 16 tokens) that need not be contiguous. A <b>block table</b> maps logical positions to physical blocks, and shared blocks are reference-counted and copied on write, just like OS pages.'),
        section('s-core', 4, 'Blocks, block tables, and copy-on-write', '''    <div class="grid3">
      <div class="card a"><h3>Fixed-size blocks</h3><p>KV for B tokens per block. vLLM sets the default block size to <b>16</b>, as a balance between GPU efficiency and internal fragmentation.</p></div>
      <div class="card b"><h3>Block table</h3><p>Per sequence: logical block i → physical block id. The attention kernel reads K and V through this table.</p></div>
      <div class="card e"><h3>Share and copy on write</h3><p>Forked sequences point at the same blocks (refcount &gt; 1). The first write to a shared, partly filled block copies it.</p></div>
    </div>'''),
        section('s-how', 5, 'Watch the allocator <span class="ill">block size 4 for readability</span>', '''    <div class="visual">
      <div class="steps" id="paSteps"></div>
      <div class="grid2" style="margin-top:12px;grid-template-columns:1.3fr 1fr">
        <div><h3>Physical blocks</h3><svg id="paSvg" viewBox="0 0 420 150" role="img" aria-label="Physical KV blocks"></svg></div>
        <div><h3>Block tables</h3><div id="paTables" class="mergelist" style="font-size:13px"></div></div>
      </div>
      <div class="infobox" id="paInfo"></div>
    </div>'''),
        section('s-how2', 5, 'Prefix caching: reuse shared prompts', '''    <p class="lede">Many requests begin with the same tokens: a system prompt, few-shot examples, earlier chat turns. Keep their KV after a request finishes, index it in a tree keyed by tokens, and the next request skips prefill for the longest cached prefix. SGLang's <b>RadixAttention</b> uses a radix tree with LRU eviction.</p>
    <div class="visual">
      <div class="steps" id="pcSteps"></div>
      <div id="pcOut" style="margin-top:12px"></div>
      <div class="infobox" id="pcInfo"></div>
    </div>'''),
        section('s-why', 6, 'Why it works', '''    <div class="grid2">
      <div class="card e"><h3>Near-zero waste</h3><p>Only the last block of each sequence can be partly empty, so waste is under one block per sequence. Build-it notebook 04 measures <b>0.6%</b> vs <b>48%</b> for contiguous max-length reservation on random lengths.</p></div>
      <div class="card a"><h3>Bigger batches</h3><p>Freed memory holds more sequences. vLLM reported <b>2–4×</b> throughput over FasterTransformer and Orca at the same latency.</p></div>
      <div class="card b"><h3>Free sharing</h3><p>Parallel sampling and beam search share prompt blocks through reference counts.</p></div>
      <div class="card c"><h3>Prefix reuse</h3><p>Shared prefixes skip prefill entirely. SGLang reported up to <b>6.4×</b> higher throughput on structured LLM programs.</p></div>
    </div>'''),
        myths('s-myth', [
            ('PagedAttention makes attention compute faster.', 'Its main win is <b>memory</b>: less waste and more sharing allow bigger batches, which raises throughput. The kernel has to read through the block table.'),
            ('Bigger blocks are always better.', 'Larger blocks are more GPU-efficient but waste more in each sequence\'s last block. vLLM picked 16 as the balance.'),
            ('Prefix caching only helps identical prompts.', 'It reuses the <b>longest shared prefix</b>, so different requests with the same system prompt still benefit.'),
        ]),
        check('s-check', [
            ('mcq', 'What is vLLM\'s default KV block size?', ['1 token', '16 tokens', '256 tokens', 'one whole sequence'], 1, '<b>16 tokens</b>.'),
            ('open', 'Two samples share a prompt whose last block is half full. What happens when sample 2 generates its next token?', 'That block is <b>shared</b> (refcount 2) and partly filled, so the allocator copies it on write: sample 2 gets a fresh block, and the old block\'s refcount drops to 1.'),
            ('mcq', 'What throughput gain did vLLM report over FasterTransformer and Orca at the same latency?', ['1.2×', '2–4×', '36.9×', '93%'], 1, '<b>2–4×</b>, with larger gains for longer sequences and larger models.'),
        ]),
    ],
    js=r'''
  class BM { constructor(n, bs) { this.bs = bs; this.free = [...Array(n).keys()].reverse(); this.ref = Array(n).fill(0); this.t = {}; this.k = {}; this.owner = Array(n).fill(null); }
    al(o) { const b = this.free.pop(); this.ref[b] = 1; this.owner[b] = o; return b; } rel(b) { if (--this.ref[b] === 0) { this.free.push(b); this.owner[b] = null; } }
    add(s) { this.t[s] = []; this.k[s] = 0; }
    app(s, n) { for (let i = 0; i < n; i++) { const t = this.t[s], k = this.k[s]; if (k % this.bs === 0) t.push(this.al(s)); else if (this.ref[t[t.length - 1]] > 1) { const nb = this.al(s); this.rel(t[t.length - 1]); t[t.length - 1] = nb; } this.k[s]++; } }
    fork(p, c) { this.t[c] = this.t[p].slice(); this.k[c] = this.k[p]; this.t[c].forEach(b => this.ref[b]++); }
    freeSeq(s) { this.t[s].forEach(b => this.rel(b)); delete this.t[s]; delete this.k[s]; } }
  const OPS = [
    ['1 · A: 10-token prompt', m => { m.add('A'); m.app('A', 10); }, 'A needs ceil(10/4) = 3 blocks. They needn\'t be contiguous, and the last one is half full.'],
    ['2 · B: 6-token prompt', m => { m.add('B'); m.app('B', 6); }, 'B gets 2 blocks from the free pool, with no reservation for its future length.'],
    ['3 · A generates 3 tokens', m => m.app('A', 3), 'A fills its last block (2 slots), then needs one new block for the 3rd token.'],
    ['4 · Fork A → A′ (parallel sample)', m => m.fork('A', "A'"), 'A′ shares all of A\'s blocks (refcount 2, outlined). No memory is copied.'],
    ['5 · A′ generates 1 token', m => m.app("A'", 1), 'A′ writes into the shared, partly filled last block, so it gets copied on write. The full blocks stay shared.'],
    ['6 · B finishes', m => m.freeSeq('B'), 'B\'s blocks return to the pool immediately for the next request.'],
  ];
  const COL = { A: 'var(--a)', B: 'var(--b)', "A'": 'var(--c)' };
  const ps = document.getElementById('paSteps'); ps.innerHTML = OPS.map((o, i) => `<button data-i="${i}">${o[0]}</button>`).join('');
  const pick = i => {
    Deck.$$('button', ps).forEach(b => b.classList.toggle('on', +b.dataset.i === i));
    const m = new BM(16, 4); OPS.slice(0, i + 1).forEach(o => o[1](m));
    const s = clear(document.getElementById('paSvg'));
    for (let b = 0; b < 16; b++) {
      const x = 10 + (b % 8) * 51, y = 10 + Math.floor(b / 8) * 66, used = m.ref[b] > 0, shared = m.ref[b] > 1;
      let fill = 0; Object.keys(m.t).forEach(sq => { const idx = m.t[sq].indexOf(b); if (idx >= 0) fill = Math.max(fill, Math.min(4, m.k[sq] - idx * 4)); });
      svg('rect', { x, y, width: 46, height: 54, rx: 5, style: `fill:var(--panel-2);stroke:${shared ? 'var(--ink)' : 'var(--line)'};stroke-width:${shared ? 2.5 : 1}` }, s);
      if (used) for (let k = 0; k < fill; k++) svg('rect', { x: x + 4, y: y + 42 - k * 12, width: 38, height: 10, rx: 2, style: `fill:${COL[m.owner[b]] || 'var(--faint)'}` }, s);
      svg('text', { x: x + 23, y: y + 66 > 140 ? y + 64 : y + 64, 'text-anchor': 'middle', class: 'tm tc', style: 'font-size:9px', text: '#' + b + (shared ? ' ×' + m.ref[b] : '') }, s);
    }
    document.getElementById('paTables').innerHTML = Object.keys(m.t).map(sq => `<div><b style="color:${COL[sq]}">${sq}</b> (${m.k[sq]} tok): [${m.t[sq].join(', ')}]</div>`).join('') + `<div style="margin-top:6px;color:var(--muted)">free blocks: ${m.free.length} / 16</div>`;
    document.getElementById('paInfo').innerHTML = OPS[i][2];
  };
  ps.addEventListener('click', e => { const b = e.target.closest('button'); if (b) pick(+b.dataset.i); }); pick(0);
  const SYS = ['<sys>', 'You', 'are', 'a', 'helpful', 'assistant', '.'];
  const REQ = [['User', ':', 'hi'], ['User', ':', 'summarize', 'this'], ['User', ':', 'hi', 'again']];
  const pcs = document.getElementById('pcSteps'); pcs.innerHTML = REQ.map((r, i) => `<button data-i="${i}">Request ${i + 1}</button>`).join('');
  const pc = i => {
    Deck.$$('button', pcs).forEach(b => b.classList.toggle('on', +b.dataset.i === i));
    const cached = new Set(); let html = '';
    for (let k = 0; k <= i; k++) {
      const toks = SYS.concat(REQ[k]); let hit = 0;
      for (let j = 0; j < toks.length; j++) { const key = toks.slice(0, j + 1).join('\u0001'); if (cached.has(key) && hit === j) hit++; }
      if (k === i) html = `<div class="toks">${toks.map((t, j) => `<span class="tok" style="background:${j < hit ? 'var(--e-soft)' : 'var(--b-soft)'};outline:${j < hit ? '1.5px solid var(--e)' : 'none'}">${t}</span>`).join('')}</div>`
        + `<p class="readout" style="margin-top:8px"><span style="color:var(--e)">${hit} cached</span> · <span style="color:var(--b)">${toks.length - hit} to prefill</span></p>`;
      toks.forEach((_, j) => cached.add(toks.slice(0, j + 1).join('\u0001')));
    }
    document.getElementById('pcOut').innerHTML = html;
    document.getElementById('pcInfo').innerHTML = ['The first request has nothing cached, so the whole prompt is prefilled and stays in the cache.', 'The 7-token system prompt plus "User :" (9 tokens) is reused, and only the new suffix is prefilled.', 'Request 3 shares even more with request 1, "… User : hi", so 10 tokens are reused.'][i];
  };
  pcs.addEventListener('click', e => { const b = e.target.closest('button'); if (b) pc(+b.dataset.i); }); pc(0);
''',
    line='PagedAttention manages the KV cache like virtual memory, with blocks, block tables and copy-on-write, and prefix caching reuses the KV of shared prompts.',
    explain='KV caches grow token by token to unknown lengths, so contiguous max-length reservations waste most of the memory and duplicate shared prompts. vLLM\'s PagedAttention stores KV in fixed blocks (16 tokens by default) mapped through a per-sequence block table, with reference counts and copy-on-write so forks share memory. Waste drops to under one block per sequence, batches get bigger, and vLLM reported 2–4× throughput. Prefix caching, such as SGLang\'s RadixAttention, keeps shared prefixes in a tree so later requests skip their prefill.',
    recap=[('Problem', 'dynamic KV sizes cause fragmentation, and shared prefixes get duplicated and recomputed.'), ('Core idea', 'paged blocks plus block tables plus copy-on-write; a token tree for prefix reuse.')],
)
