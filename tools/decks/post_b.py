import json
from tool import section, your_turn, myths, check

DECKS = {}


def deep(title, html):
    return f'    <div class="deep"><h4>{title}</h4>{html}</div>'


INFOBOX = 'class="infobox" style="background:var(--panel-2);border-radius:10px;padding:12px 14px;margin-top:10px;font-size:14px;color:var(--muted)"'

# measured in notebook 06 (n, KL, proxy, gold-delta, fit-delta)
BON = [(1, 0.00, -0.03, 0.000, 0.000), (2, 0.19, 0.81, 0.414, 0.430), (4, 0.64, 1.45, 0.630, 0.632), (8, 1.20, 2.02, 0.704, 0.700), (16, 1.84, 2.51, 0.671, 0.684),
       (32, 2.50, 2.91, 0.628, 0.614), (64, 3.17, 3.33, 0.507, 0.507), (128, 3.86, 3.68, 0.419, 0.374), (256, 4.55, 4.01, 0.184, 0.220), (512, 5.24, 4.32, 0.025, 0.052), (1024, 5.93, 4.61, -0.109, -0.129)]

# =============================================================== 06
DECKS['06-reward-hacking'] = dict(
    title='Reward Hacking and Overoptimization', h1='Reward hacking and overoptimization',
    sub='Why optimizing a learned reward model too hard makes the model worse, how to measure "too hard" with KL, and the mitigations labs use.',
    prob='A reward model is a proxy trained on limited data. The harder RL or best-of-n pushes on it, the more it finds the RM\'s blind spots: the proxy score climbs while the real quality falls.',
    core='Treat optimization as a <b>budget measured in KL</b> from the starting policy. True ("gold") reward rises then falls as KL grows (Gao et al. 2022), so limit KL, refresh the reward model, and prefer rewards that can\'t be gamed.',
    build=['06_overoptimization'],
    sources='Gao, Schulman & Hilton 2022, "Scaling Laws for Reward Model Overoptimization" (functional forms, KL_bon); Stiennon et al. 2020 (App. G.3); Ouyang et al. 2022 (per-token KL penalty); Touvron et al. 2023 (Llama 2 iterative RLHF V1–V5).',
    slides=[
        section('s-p1', 1, 'The proxy keeps rising; the truth doesn\'t <span class="ill">simulation</span>', '''    <p class="lede">Best-of-n against a flawed reward model (notebook 06): the proxy RM partly mistakes "length" for quality, while the true (gold) reward penalizes extreme length. Move n. The x-axis is √KL, the distance from the base policy.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0"><label class="ctl">best-of-n <input type="range" id="hN" min="0" max="10" step="1" value="3"> <output id="hNo"></output></label></div>
      <svg id="hSvg" viewBox="0 0 660 260" style="margin-top:10px" role="img" aria-label="Proxy vs gold reward"></svg>
      <div class="legend"><span><i style="background:var(--b)"></i>proxy RM score</span><span><i style="background:var(--a)"></i>gold reward (change)</span><span><i style="background:var(--faint)"></i>fit d(α − βd)</span></div>
      <p class="readout" id="hOut"></p>
    </div>'''),
        section('s-lim', 2, 'Why a reward model can be gamed', '''    <div class="grid3">
      <div class="card d"><h3>Trained on a narrow distribution</h3><p>The RM saw outputs from earlier models. As the policy improves, it produces text the RM has never been checked on.</p></div>
      <div class="card b"><h3>Spurious features</h3><p>If longer or more confident answers tended to win in the data, the RM may reward length or confidence itself, even when they don't help.</p></div>
      <div class="card c"><h3>An optimizer finds every flaw</h3><p>RL is a search for high-scoring outputs. Any systematic error in the RM is a direction the search will follow. Goodhart's law: "When a measure becomes a target, it ceases to be a good measure."</p></div>
    </div>'''),
        your_turn('s-turn', 'What happens as you push harder?',
                  'You increase n in best-of-n (or train RL longer) against a fixed, imperfect reward model. What does the true quality typically do?',
                  ['Keeps improving, more slowly', 'Rises, peaks, then declines', 'Declines from the start', 'Stays flat'], 1,
                  '<b>B.</b> Gao et al. find gold reward follows d(α − βd) for best-of-n and d(α − β·log d) for RL, with d = √KL: an initial gain, a peak, then decline, while the proxy score keeps increasing.'),
        section('s-core', 4, 'Measure optimization in KL', '''    <div class="grid3">
      <div class="card a"><h3>KL as the distance travelled</h3><p>How far the optimized policy is from where it started. Best-of-n has an exact formula: KL<sub>bon</sub> = log n − (n−1)/n, which grows roughly like log n.</p></div>
      <div class="card b"><h3>Predictable curves</h3><p>Gold reward R(d), with d = √KL:<br>best-of-n: <b>d(α − βd)</b><br>RL: <b>d(α − β log d)</b><br>The coefficients scale smoothly with the reward model's size.</p></div>
      <div class="card e"><h3>The KL penalty is a brake</h3><p>RLHF's −β·KL term (deck 05) caps how far the policy goes, holding it near the region where the RM is trustworthy.</p></div>
    </div>
''' + deep('How Gao et al. measured this', '<p>Real human labels are too expensive to sweep, so they used a large "gold-standard" reward model as stand-in ground truth, trained smaller proxy RMs on labels from it, optimized policies against the proxies, and scored the results with the gold RM. That synthetic setup made the rise-then-fall curve measurable across many sizes.</p>')),
        section('s-how', 5, 'What the optimizer actually selected <span class="ill">simulation</span>', '''    <p class="lede">The same simulation: average features of the response picked by best-of-n. Helpfulness rises at first, but the optimizer increasingly buys proxy score with "length", which the gold reward penalizes.</p>
    <div class="visual">
      <svg id="sSvg" viewBox="0 0 660 230" role="img" aria-label="Selected features vs n"></svg>
      <div class="legend"><span><i style="background:var(--a)"></i>helpfulness of chosen answer</span><span><i style="background:var(--d)"></i>"length" of chosen answer</span></div>
    </div>
''' + deep('Real-world versions', '<p>Commonly reported symptoms include answers that grow longer without getting better, excessive hedging or flattery, and confident wording that the RM likes. Notebook 06 is a two-feature toy: the mechanism (a correlated but wrong feature exploited by search) is the general one.</p>')),
        section('s-how2', 5, 'Mitigations', '''    <div class="visual scroll-x"><table class="tbl">
      <tr><th>Mitigation</th><th>How it helps</th></tr>
      <tr><td>KL penalty / early stopping</td><td>Stop before the gold curve turns down; β or the step count sets the budget</td></tr>
      <tr><td>Bigger, better reward models</td><td>Overoptimization coefficients scale smoothly with RM size (Gao et al.)</td></tr>
      <tr><td>Iterate: fresh comparisons on the current policy</td><td>Keeps the RM accurate where the policy now is. Llama 2 ran RLHF-V1 to V5; Llama 3 ran six rounds</td></tr>
      <tr><td>Several reward models</td><td>Llama 2 used separate helpfulness and safety RMs</td></tr>
      <tr><td>Verifiable rewards</td><td>For maths and code, a checker is much harder to game than a learned scorer (deck 08)</td></tr>
      <tr><td>Watch the outputs</td><td>Track length, refusal rate and human spot checks, not only the RM score</td></tr>
    </table></div>'''),
        section('s-why', 6, 'Why the curve turns down', '''    <div class="grid2">
      <div class="card a"><h3>Early: real gains</h3><p>Near the start, the RM's ranking is mostly right, so picking higher-scoring answers picks better answers.</p></div>
      <div class="card d"><h3>Later: errors dominate</h3><p>The biggest proxy scores come increasingly from the RM's mistakes. Selection pressure concentrates on exactly those outputs.</p></div>
      <div class="card b"><h3>The fit is good</h3><p>In our toy, d(1.20 − 0.52d) predicts every simulated point within ~0.05, with a peak near KL ≈ 1.4 nats (n ≈ 8).</p></div>
      <div class="card e"><h3>Lesson</h3><p>A reward model's score is evidence, not a target. More optimization is not automatically better.</p></div>
    </div>'''),
        myths('s-myth', [
            ('If the reward model score goes up, the model got better.', 'Only up to a point. Past the peak, proxy score and true quality move in opposite directions.'),
            ('Best-of-n is safe because it doesn\'t change the model.', 'It still optimizes against the RM. KL<sub>bon</sub> = log n − (n−1)/n grows with n, and so does exploitation.'),
            ('Reward hacking is a bug in the RL algorithm.', 'It is a property of optimizing any imperfect proxy. A perfect optimizer hacks harder.'),
        ]),
        check('s-check', [
            ('mcq', 'KL of best-of-2 from the base policy?', ['0', 'log 2 − 0.5 ≈ 0.19', 'log 2 ≈ 0.69', '1'], 1, '<b>log 2 − 1/2 ≈ 0.19 nats.</b>'),
            ('open', 'Gao et al.\'s functional forms for gold reward vs d = √KL?', 'Best-of-n: d(α − βd). RL: d(α − β log d). Both rise then fall.'),
            ('open', 'Name three mitigations for reward hacking.', 'A KL penalty or early stopping; larger and fresher reward models (new comparisons each round); verifiable rewards where possible; multiple RMs; monitoring length and spot checks.'),
        ]),
    ],
    js=r'''
  const BON = ''' + json.dumps(BON) + r''';
  Deck.bind(['hN'], () => {
    const k = Deck.val('hN'), [n, kl, px, gd] = BON[k]; Deck.out('hNo', n);
    const s = clear(document.getElementById('hSvg')), X = d => 60 + d / 2.5 * 560, Y = v => 215 - (v + 0.4) / 5.2 * 195;
    [0, 1, 2, 3, 4, 5].forEach(v => { svg('line', { x1: 60, x2: 620, y1: Y(v), y2: Y(v), class: 'ln' }, s); svg('text', { x: 52, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm', text: v }, s); });
    const line = (i, c, w, dash) => svg('polyline', { points: BON.map(r => `${X(Math.sqrt(r[1]))},${Y(r[i])}`).join(' '), fill: 'none', style: `stroke:${c};stroke-width:${w}${dash ? ';stroke-dasharray:5 4' : ''}` }, s);
    line(4, 'var(--faint)', 2, true); line(2, 'var(--b)', 3); line(3, 'var(--a)', 3);
    svg('line', { x1: X(Math.sqrt(kl)), x2: X(Math.sqrt(kl)), y1: 15, y2: 215, style: 'stroke:var(--ink);stroke-dasharray:3 3' }, s);
    [0, 0.5, 1, 1.5, 2, 2.5].forEach(d => svg('text', { x: X(d), y: 234, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: d }, s));
    svg('text', { x: 340, y: 254, 'text-anchor': 'middle', class: 'tm', text: 'd = √KL from the base policy' }, s);
    document.getElementById('hOut').innerHTML = `n = ${n}: KL = log n − (n−1)/n = <b>${kl.toFixed(2)}</b> nats. Proxy score ${px.toFixed(2)}, gold change <b>${gd >= 0 ? '+' : ''}${gd.toFixed(2)}</b>${k > 3 ? (gd < 0.6 ? ' (past the peak: the extra proxy score is mostly exploitation)' : '') : ''}.`;
  });
  (() => {
    const s = document.getElementById('sSvg'), ns = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024];
    const ev = n => { let seed = 7 + n, h = 0, L = 0; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647; const g = () => Math.sqrt(-2 * Math.log(Math.max(1e-9, rnd()))) * Math.cos(2 * Math.PI * rnd());
      for (let t = 0; t < 200; t++) { let best = -1e9, bh = 0, bl = 0; for (let i = 0; i < n; i++) { const a = g(), b = g(), p = a + b; if (p > best) { best = p; bh = a; bl = b; } } h += bh; L += bl; } return [h / 200, L / 200]; };
    const R = ns.map(ev), X = i => 70 + i * 54, Y = v => 200 - v / 3 * 170;
    [0, 1, 2, 3].forEach(v => { svg('line', { x1: 60, x2: 620, y1: Y(v), y2: Y(v), class: 'ln' }, s); svg('text', { x: 52, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm', text: v }, s); });
    ns.forEach((n, i) => svg('text', { x: X(i), y: 220, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: n }, s));
    [[0, 'var(--a)'], [1, 'var(--d)']].forEach(([j, c]) => svg('polyline', { points: R.map((r, i) => `${X(i)},${Y(r[j])}`).join(' '), fill: 'none', style: `stroke:${c};stroke-width:3` }, s));
  })();
''',
    line='Optimizing a learned reward model is a KL budget: true quality rises, peaks and falls while the proxy keeps climbing, so cap KL and keep the reward honest.',
    explain='A reward model is a proxy trained on a narrow slice of outputs. Best-of-n sampling and RL are searches for high proxy scores, so the harder they push, the more they find the reward model\'s mistakes. Gao and colleagues measured this: plotted against the square root of KL from the starting policy, the true reward follows d times alpha minus beta d for best-of-n and d times alpha minus beta log d for RL, rising then falling while the proxy keeps increasing. Best-of-n\'s KL is log n minus n minus one over n. Mitigations are a KL penalty or early stopping, bigger and regularly refreshed reward models, and verifiable rewards where possible.',
    recap=[('Problem', 'the RM is a proxy; optimization finds its errors (Goodhart).'), ('Core idea', 'measure optimization in KL; gold reward vs √KL rises then falls.'), ('Fixes', 'KL penalty, early stopping, bigger and fresher RMs, verifiable rewards, monitoring.')],
)

# =============================================================== 07
DECKS['07-dpo-and-friends'] = dict(
    title='DPO, KTO and Rejection Sampling', h1='DPO, KTO and rejection sampling',
    sub='Simpler routes to the RLHF objective: Direct Preference Optimization turns it into a classification loss, KTO needs only good/bad labels, and rejection sampling fine-tunes on the best of many samples.',
    prob='PPO-based RLHF needs four models, generation inside the training loop and delicate tuning. Many teams want the benefit of preference data without running online RL.',
    core='<b>DPO</b>: the RLHF optimum π* ∝ π_ref·e<sup>r/β</sup> lets you write the reward as β·log(π/π_ref), so the Bradley-Terry loss can be applied <b>directly to the policy</b>, with no reward model and no sampling.',
    build=['07_dpo'],
    sources='Rafailov et al. 2023, "Direct Preference Optimization: Your Language Model is Secretly a Reward Model" (§4, eq. 7); Ethayarajh et al. 2024, "KTO: Model Alignment as Prospect Theoretic Optimization"; Touvron et al. 2023 (Llama 2 §3.2.3, rejection sampling); Llama Team 2024 (Llama 3 §4: SFT, RS, DPO in six rounds).',
    slides=[
        section('s-p1', 1, 'RLHF vs DPO, side by side', '''    <p class="lede">Both start from an SFT model and preference pairs and target the same objective. Compare what each pipeline has to run.</p>
    <div class="visual">
      <div class="seg" id="pSeg"><button data-v="rlhf" class="on">RLHF (RM + PPO)</button><button data-v="dpo">DPO</button></div>
      <svg id="pSvg" viewBox="0 0 660 200" style="margin-top:10px" role="img" aria-label="Pipeline comparison"></svg>
      <p class="readout" id="pOut"></p>
    </div>'''),
        section('s-lim', 2, 'What makes PPO-based RLHF heavy', '''    <div class="grid3">
      <div class="card d"><h3>Generation in the loop</h3><p>Every step samples full answers from the current policy: slow, and awkward to run efficiently next to training.</p></div>
      <div class="card b"><h3>Four models</h3><p>Policy, reference, reward model and value model must all fit, two of them with optimizer state.</p></div>
      <div class="card c"><h3>Tuning</h3><p>β, clipping ε, learning rates for two networks, advantage estimation settings. Instabilities are common.</p></div>
    </div>'''),
        your_turn('s-turn', 'The implicit reward',
                  'After DPO training, the policy gives answer y twice the probability the reference gives it (β = 0.1). What implicit reward does DPO assign to y, up to a per-prompt constant?',
                  ['0.1', '0.1 · ln 2 ≈ 0.069', '2', 'It has no reward'], 1,
                  '<b>B.</b> DPO\'s implicit reward is r̂(x,y) = β·log(π_θ(y|x)/π_ref(y|x)) = 0.1·ln 2 ≈ 0.069. "Your language model is secretly a reward model."'),
        section('s-core', 4, 'The derivation in three lines', '''    <div class="grid3">
      <div class="card a"><h3>1 · Known optimum</h3><p>The KL-regularized RLHF objective has the closed-form solution π*(y|x) = π_ref(y|x)·exp(r(x,y)/β) / Z(x).</p></div>
      <div class="card b"><h3>2 · Invert it</h3><p>Solve for the reward: r(x,y) = β·log(π*(y|x)/π_ref(y|x)) + β·log Z(x). Any policy defines a reward this way.</p></div>
      <div class="card e"><h3>3 · Plug into Bradley-Terry</h3><p>In r(y_w) − r(y_l) the β·log Z(x) terms <b>cancel</b>, leaving a loss on the policy alone.</p></div>
    </div>
    <div class="eq">L<sub>DPO</sub> = −E[ log σ( β·log(π<sub>θ</sub>(y<sub>w</sub>)/π<sub>ref</sub>(y<sub>w</sub>)) − β·log(π<sub>θ</sub>(y<sub>l</sub>)/π<sub>ref</sub>(y<sub>l</sub>)) ) ]</div>'''),
        section('s-how', 5, 'What the gradient does', '''    <p class="lede">The DPO gradient for one pair is (1 − σ(z))·β·(∇log π(y_w) − ∇log π(y_l)), where z is the current implicit-reward margin. Pairs the model already ranks correctly with a large margin get almost no weight; pairs it gets wrong get the most. Drag the margin.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0"><label class="ctl">implicit margin z <input type="range" id="gZ" min="-6" max="6" step="0.1" value="-1"> <output id="gZo"></output></label></div>
      <svg id="gSvg" viewBox="0 0 660 220" style="margin-top:10px" role="img" aria-label="DPO gradient weight"></svg>
      <p class="readout" id="gOut"></p>
    </div>
''' + deep('Notebook 07 checks the theory', '<p>On a toy 6-response problem with 20,000 simulated preference pairs, DPO converges to π* ∝ π_ref·e<sup>r/β</sup> (KL(π*‖π) ≈ 0.0008), and its implicit rewards match the hidden true rewards up to a constant: [−0.73, 0.20, −1.24, 1.23, −0.24, 0.78] vs [−0.75, 0.25, −1.25, 1.25, −0.25, 0.75]. With only 200 pairs the KL is 0.19: offline data limits it.</p>')),
        section('s-how2', 5, 'The family', '''    <div class="visual scroll-x"><table class="tbl">
      <tr><th>Method</th><th>Signal needed</th><th>Idea</th></tr>
      <tr><td><b>Rejection sampling FT</b> (best-of-n + SFT)</td><td>a reward model</td><td>Sample K answers, keep the highest-scoring one, fine-tune on it. Llama 2 used only this up to RLHF-V4, then PPO on top.</td></tr>
      <tr><td><b>DPO</b> (2023)</td><td>preference pairs</td><td>Bradley-Terry loss on the policy's implicit reward β·log(π/π_ref). No RM, no sampling.</td></tr>
      <tr><td><b>KTO</b> (2024)</td><td>a binary desirable / undesirable label per output</td><td>Uses a prospect-theory (Kahneman–Tversky) utility; no pairs needed. Matches or exceeds DPO from 1B to 30B parameters in the paper.</td></tr>
      <tr><td><b>Iterative DPO</b></td><td>fresh pairs each round</td><td>Generate with the current model, label, run DPO, repeat. Llama 3: six rounds of SFT, rejection sampling and DPO.</td></tr>
    </table></div>'''),
        section('s-why', 6, 'Why DPO caught on, and its limits', '''    <div class="grid2">
      <div class="card a"><h3>Simple and stable</h3><p>A supervised loss on fixed data: two models (policy and frozen reference), no generation, few hyperparameters (mainly β).</p></div>
      <div class="card e"><h3>Same target as RLHF</h3><p>In the ideal case it optimizes "the same objective as existing RLHF algorithms" (the paper), so it is not a weaker objective, just a different optimizer.</p></div>
      <div class="card b"><h3>Offline data limits it</h3><p>It learns only from the pairs it is given. If they don't cover what the current policy does, it can't correct those behaviours, which is why labs iterate with fresh on-policy pairs.</p></div>
      <div class="card d"><h3>Still a proxy</h3><p>The implicit reward is fit to finite, noisy labels. Pushing β small or training long can overfit the pairs, the DPO version of reward hacking.</p></div>
    </div>'''),
        myths('s-myth', [
            ('DPO doesn\'t need a reference model.', 'It does: both log-ratios are taken against a frozen π_ref (usually the SFT model). The reference defines the implicit reward and the KL anchor.'),
            ('DPO has no reward model, so it can\'t be reward-hacked.', 'The policy is its own reward model. It can still overfit noisy or narrow preference data and drift in odd directions.'),
            ('β in DPO is a learning rate.', 'β is the KL strength from the RLHF objective: a small β allows larger departures from the reference.'),
        ]),
        check('s-check', [
            ('mcq', 'Why does the partition function Z(x) disappear from the DPO loss?', ['It is approximated as 1', 'It cancels in the reward difference between y_w and y_l for the same prompt', 'It is learned separately', 'β absorbs it'], 1, '<b>B.</b> Both responses share the same prompt x, so β·log Z(x) cancels in r(y_w) − r(y_l).'),
            ('open', 'What does KTO need instead of preference pairs?', 'A binary label per output: desirable or undesirable. It optimizes a prospect-theory-inspired utility, so data without paired comparisons can be used.'),
            ('open', 'How did Llama 2 use rejection sampling?', 'Sample K answers per prompt, take the best by the reward model, fine-tune on those. Only rejection sampling up to RLHF-V4, then PPO applied on top of the rejection-sampling checkpoint.'),
        ]),
    ],
    js=r'''
  Deck.seg('pSeg', v => {
    const s = clear(document.getElementById('pSvg')), dpo = v === 'dpo';
    const box = (x, y, w, t, c) => { svg('rect', { x, y, width: w, height: 40, rx: 8, style: `fill:${c}` }, s); svg('text', { x: x + w / 2, y: y + 25, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:600;font-size:12px', text: t }, s); };
    const arrow = (x1, x2, y) => { svg('line', { x1, x2: x2 - 6, y1: y, y2: y, style: 'stroke:var(--muted);stroke-width:2' }, s); svg('path', { d: `M${x2 - 10} ${y - 5} L${x2} ${y} L${x2 - 10} ${y + 5}`, fill: 'none', style: 'stroke:var(--muted);stroke-width:2' }, s); };
    if (!dpo) {
      box(10, 20, 130, 'preference pairs', 'var(--faint)'); arrow(140, 175, 40); box(175, 20, 130, 'train reward model', 'var(--b)'); arrow(305, 340, 40);
      box(340, 20, 140, 'sample from policy', 'var(--c)'); arrow(480, 515, 40); box(515, 20, 130, 'score + PPO step', 'var(--a)');
      svg('path', { d: 'M580 62 V100 H410 V64', fill: 'none', style: 'stroke:var(--muted);stroke-width:2;stroke-dasharray:4 3' }, s);
      svg('text', { x: 495, y: 118, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: 'repeat for thousands of steps' }, s);
      [['policy', 'var(--a)'], ['reference', 'var(--faint)'], ['reward model', 'var(--b)'], ['value model', 'var(--c)']].forEach(([t, c], i) => box(40 + i * 150, 145, 130, t, c));
      document.getElementById('pOut').innerHTML = 'Two training stages, generation inside the loop, and <b>four</b> models in memory.';
    } else {
      box(60, 20, 170, 'preference pairs', 'var(--faint)'); arrow(230, 290, 40); box(290, 20, 300, 'DPO loss on log-ratios (one stage)', 'var(--a)');
      [['policy', 'var(--a)'], ['reference (frozen)', 'var(--faint)']].forEach(([t, c], i) => box(140 + i * 200, 145, 170, t, c));
      document.getElementById('pOut').innerHTML = 'One supervised stage on fixed pairs, no sampling, <b>two</b> models (and the reference only needs log-probs, which can be precomputed).';
    }
  });
  Deck.bind(['gZ'], () => {
    const z = Deck.val('gZ'), w = 1 - 1 / (1 + Math.exp(-z)); Deck.out('gZo', z.toFixed(1));
    const s = clear(document.getElementById('gSvg')), X = v => 60 + (v + 6) / 12 * 560, Y = v => 190 - v * 165;
    [0, 0.5, 1].forEach(v => { svg('line', { x1: 60, x2: 620, y1: Y(v), y2: Y(v), class: 'ln' }, s); svg('text', { x: 52, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm', text: v }, s); });
    let p = ''; for (let v = -6; v <= 6.001; v += 0.05) p += `${X(v)},${Y(1 - 1 / (1 + Math.exp(-v)))} `;
    svg('polyline', { points: p, fill: 'none', style: 'stroke:var(--a);stroke-width:3' }, s);
    svg('circle', { cx: X(z), cy: Y(w), r: 7, style: 'fill:var(--b)' }, s);
    svg('text', { x: 340, y: 214, 'text-anchor': 'middle', class: 'tm', text: 'z = β·[log-ratio(y_w) − log-ratio(y_l)]' }, s);
    document.getElementById('gOut').innerHTML = `Gradient weight 1 − σ(z) = <b>${w.toFixed(2)}</b>. ${z < 0 ? 'The model currently prefers the loser, so this pair gets a strong push.' : z > 3 ? 'Already ranked correctly by a wide margin: almost no update.' : 'Ranked correctly, but with a small margin: a moderate push.'}`;
  });
''',
    line='DPO rewrites the RLHF objective as a classification loss on β·log(π/π_ref), so preference data trains the policy directly, with no reward model or RL loop.',
    explain='PPO-based RLHF needs four models and generation inside training. DPO starts from the known optimum of the KL-regularized objective, the reference policy times exp of reward over beta, and inverts it: any policy implies a reward equal to beta times the log ratio to the reference, plus a per-prompt constant. Plugging that into the Bradley-Terry loss cancels the constant, giving a simple loss on preference pairs that needs only the policy and a frozen reference. Its gradient focuses on pairs the model gets wrong. KTO needs only good-or-bad labels, rejection sampling fine-tunes on the best of several samples, and labs iterate with fresh pairs because DPO only learns from the data it is given.',
    recap=[('Problem', 'PPO RLHF: four models, generation in the loop, fragile tuning.'), ('Core idea', 'implicit reward β·log(π/π_ref); Bradley-Terry loss directly on the policy.'), ('Family', 'rejection sampling (best-of-n + SFT), KTO (binary labels), iterative DPO.')],
)

# =============================================================== 08
DECKS['08-rlvr-grpo'] = dict(
    title='RLVR and GRPO', h1='RL with verifiable rewards and GRPO',
    sub='How reasoning models are trained: replace the learned reward model with a checker, replace the critic with a group of samples, and let RL discover long chains of thought.',
    prob='Learned reward models can be gamed and PPO\'s critic costs a whole extra model. For maths and code, correctness can often be checked exactly, so why approximate it?',
    core='<b>RLVR</b>: reward = 1 if a checker accepts the answer (plus format rules). <b>GRPO</b>: sample a group of G answers per prompt and use (r − mean)/std within the group as each answer\'s advantage, so no value model is needed.',
    build=['08_grpo_rlvr'],
    sources='Shao et al. 2024, "DeepSeekMath" (§4: GRPO, eq. for group-normalized advantage; GSM8K 82.9→88.2%, MATH 46.8→51.7%); DeepSeek-AI 2025, "DeepSeek-R1" (rule-based accuracy and format rewards, KL coefficient 0.001, AIME 2024 15.6%→77.9%, "aha moment", language consistency reward); Lambert et al. 2024 (Tülu 3, RLVR).',
    slides=[
        section('s-p1', 1, 'Some answers can simply be checked', '''    <div class="grid3">
      <div class="card a"><h3>Maths</h3><p>The final answer, in a required format (for example inside a box), is compared with the reference solution. DeepSeek-R1 calls this an <b>accuracy reward</b>.</p></div>
      <div class="card b"><h3>Code</h3><p>Run the program against test cases; reward the pass rate or all-pass.</p></div>
      <div class="card e"><h3>Format and constraints</h3><p>Did the model put its reasoning between the required tags, answer in the requested language, follow length limits? R1's <b>format reward</b> checks the thinking tags.</p></div>
    </div>
''' + deep('Why this matters', '<p>A learned reward model is a proxy with blind spots (deck 06). A checker is exact for what it checks, so there is far less to exploit. Tülu 3 named the approach <b>Reinforcement Learning with Verifiable Rewards (RLVR)</b>; DeepSeek-R1-Zero used rule-based rewards for maths, coding and logic and no neural reward model for them.</p>')),
        section('s-lim', 2, 'What PPO-style RLHF costs here', '''    <div class="grid3">
      <div class="card d"><h3>A critic as big as the policy</h3><p>PPO's value model is usually the same size as the policy, with its own gradients and optimizer state.</p></div>
      <div class="card b"><h3>Critics are hard for long outputs</h3><p>Predicting the expected final reward at every token of a long chain of thought is a hard regression problem, and a bad critic gives bad advantages.</p></div>
      <div class="card c"><h3>Reward models drift</h3><p>A learned RM goes stale and can be hacked; maths answers don't have that problem.</p></div>
    </div>'''),
        your_turn('s-turn', 'Compute group advantages',
                  'GRPO samples a group of 4 answers to one maths question. Rewards are [1, 0, 0, 1]. What are the advantages?',
                  ['[1, 0, 0, 1]', '[0.5, −0.5, −0.5, 0.5]', '[1, −1, −1, 1]', '[0.25, 0.25, 0.25, 0.25]'], 2,
                  '<b>C.</b> mean = 0.5, std = 0.5, so Â = (r − 0.5)/0.5 = [1, −1, −1, 1]. Every token of a correct answer is pushed up, every token of a wrong one pushed down, relative to this group.'),
        section('s-core', 4, 'GRPO in one picture', '''    <div class="grid3">
      <div class="card a"><h3>Sample a group</h3><p>For each question, sample G outputs {o₁ … o_G} from the old policy.</p></div>
      <div class="card b"><h3>Normalize within the group</h3><p>Â<sub>i</sub> = (r<sub>i</sub> − mean(r)) / std(r), applied to every token of o<sub>i</sub>. "GRPO foregoes the critic model, instead estimating the baseline from group scores."</p></div>
      <div class="card e"><h3>PPO-style update</h3><p>Clipped probability ratios as in PPO, plus a KL penalty to a reference model added to the loss (R1 used a KL coefficient of 0.001).</p></div>
    </div>
''' + deep('Why a group baseline works', '<p>A baseline only has to be "what reward would I expect for this prompt?". Several samples for the <b>same</b> prompt estimate that directly, with no network. The cost moves from memory (a critic) to compute (G samples per prompt), which also gives the reward signal more chances to be non-zero.</p>')),
        section('s-how', 5, 'When does a group teach anything?', '''    <p class="lede">If every answer in a group is right, or every answer is wrong, all advantages are 0 and the prompt contributes nothing. Probability of a "dead" group = p<sup>G</sup> + (1−p)<sup>G</sup>, where p is the chance of a correct answer. Pick p and G.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">P(correct) p <input type="range" id="dP" min="0.01" max="0.99" step="0.01" value="0.15"> <output id="dPo"></output></label>
        <label class="ctl">group size G <input type="range" id="dG" min="2" max="64" step="1" value="8"> <output id="dGo"></output></label>
      </div>
      <svg id="dSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Dead group probability"></svg>
      <p class="readout" id="dOut"></p>
    </div>
''' + deep('Practical consequence', '<p>Prompts the model always solves, or never solves, waste samples. RLVR datasets are therefore filtered towards problems of useful difficulty, and larger G helps on hard prompts. In notebook 08, a toy "base model" with 16% accuracy reaches 0.88 / 0.95 / 0.99 after 150 iterations with G = 2 / 4 / 16.</p>')),
        section('s-how2', 5, 'What DeepSeek reported', '''    <div class="visual"><div id="rBars"></div></div>
    <div class="grid2" style="margin-top:12px">
      <div class="card a"><h3>R1-Zero: RL without SFT</h3><p>RL with rule-based accuracy and format rewards directly on the base model. AIME 2024 pass@1 went from 15.6% to 77.9%, and responses grew longer as the model learned to think longer. The paper shows an "aha moment" where an intermediate checkpoint learns to stop and re-examine its own solution.</p></div>
      <div class="card b"><h3>R1: fixing R1-Zero's rough edges</h3><p>R1-Zero had "poor readability and language mixing". R1 adds cold-start long chain-of-thought data, a language consistency reward during RL, and a multi-stage pipeline integrating rejection sampling, RL and SFT.</p></div>
    </div>'''),
        section('s-why', 6, 'Why RLVR + GRPO took off', '''    <div class="grid2">
      <div class="card a"><h3>Hard-to-hack rewards</h3><p>A checker either accepts the answer or not. The model must actually get it right (or find a loophole in the checker, so checkers need care too).</p></div>
      <div class="card e"><h3>Cheaper RL</h3><p>No critic, no learned RM for these tasks: two models (policy and reference) instead of four.</p></div>
      <div class="card b"><h3>Reasoning emerges</h3><p>Rewarding only final correctness, R1-Zero developed longer reasoning, self-verification and reflection by itself, without demonstrations of how to reason.</p></div>
      <div class="card d"><h3>Limits</h3><p>Only for checkable tasks. Open-ended writing and helpfulness still need preference models, which is why R1 combines RLVR with other stages.</p></div>
    </div>'''),
        myths('s-myth', [
            ('Every sampled answer produces a gradient in GRPO.', 'Groups where all answers get the same reward have zero advantages. With 0/1 rewards, too-easy and too-hard prompts teach nothing.'),
            ('GRPO doesn\'t need a reference model.', 'It drops the <b>critic</b>, not the reference. A KL penalty to a reference policy is still part of the objective (coefficient 0.001 in R1).'),
            ('RLVR replaces preference tuning.', 'Only where answers can be verified. General chat quality, tone and safety still rely on preference data or other reward models.'),
        ]),
        check('s-check', [
            ('mcq', 'What replaces the value model in GRPO?', ['A reward model', 'The mean and std of rewards in a group of samples for the same prompt', 'A moving average over the dataset', 'Nothing; advantages are raw rewards'], 1, '<b>B.</b> The group statistics act as the baseline.'),
            ('open', 'Which two reward types did DeepSeek-R1-Zero use?', 'Rule-based <b>accuracy</b> rewards (is the final answer correct, e.g. checked inside a box or by test cases) and <b>format</b> rewards (is the reasoning inside the required tags), combined with equal weight.'),
            ('open', 'With p(correct) = 0.9 and G = 4, what fraction of groups give no signal?', '0.9⁴ + 0.1⁴ = 0.6561 + 0.0001 ≈ <b>66%</b>. Easy prompts mostly waste samples.'),
        ]),
    ],
    js=r'''
  Deck.bind(['dP', 'dG'], () => {
    const p = Deck.val('dP'), G = Deck.val('dG'); Deck.out('dPo', p.toFixed(2)); Deck.out('dGo', G);
    const dead = (pp, g) => Math.pow(pp, g) + Math.pow(1 - pp, g);
    const s = clear(document.getElementById('dSvg')), X = v => 60 + v * 560, Y = v => 200 - v * 180;
    [0, 0.5, 1].forEach(v => { svg('line', { x1: 60, x2: 620, y1: Y(v), y2: Y(v), class: 'ln' }, s); svg('text', { x: 52, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm', text: v }, s); });
    [2, 8, 32].forEach((g, i) => { let pts = ''; for (let v = 0.005; v < 1; v += 0.005) pts += `${X(v)},${Y(dead(v, g))} `; svg('polyline', { points: pts, fill: 'none', style: `stroke:${['var(--faint)', 'var(--c)', 'var(--b)'][i]};stroke-width:2` }, s); svg('text', { x: X(0.5) + 4, y: Y(dead(0.5, g)) - 6, class: 'tm', style: 'font-size:11px', text: 'G=' + g }, s); });
    let pts = ''; for (let v = 0.005; v < 1; v += 0.005) pts += `${X(v)},${Y(dead(v, G))} `;
    svg('polyline', { points: pts, fill: 'none', style: 'stroke:var(--a);stroke-width:3.5' }, s);
    svg('circle', { cx: X(p), cy: Y(dead(p, G)), r: 7, style: 'fill:var(--d)' }, s);
    svg('text', { x: 340, y: 224, 'text-anchor': 'middle', class: 'tm', text: 'P(correct answer) for the prompt' }, s);
    document.getElementById('dOut').innerHTML = `At p = ${p.toFixed(2)} and G = ${G}: <b>${(100 * dead(p, G)).toFixed(1)}%</b> of groups have identical rewards and contribute zero gradient.`;
  });
  Deck.hbars(document.getElementById('rBars'), [
    { label: 'DeepSeekMath-Instruct, MATH', value: 46.8, color: 'var(--faint)', text: '46.8%' }, { label: '+ GRPO (DeepSeekMath-RL)', value: 51.7, color: 'var(--a)', text: '51.7%' },
    { label: 'GSM8K before / after GRPO', value: 82.9, color: 'var(--faint)', text: '82.9%' }, { label: '', value: 88.2, color: 'var(--a)', text: '88.2%' },
    { label: 'R1-Zero AIME 2024, start of RL', value: 15.6, color: 'var(--faint)', text: '15.6%' }, { label: 'R1-Zero AIME 2024, after RL', value: 77.9, color: 'var(--a)', text: '77.9%' }], { max: 100 });
''',
    line='RLVR rewards answers a checker accepts; GRPO uses the spread of rewards within a group of samples as the baseline, dropping the critic. Together they trained today\'s reasoning models.',
    explain='For maths, code and formats, correctness can be checked, so RL with verifiable rewards replaces the learned reward model with a rule: one if the answer is right, plus format checks. GRPO, from DeepSeekMath, removes PPO\'s value model too: sample a group of answers per prompt and use each answer\'s reward minus the group mean, divided by the group standard deviation, as its advantage, keeping PPO\'s clipping and a small KL penalty to a reference. Groups where every answer gets the same reward teach nothing, so prompt difficulty and group size matter. DeepSeek-R1-Zero used this with no SFT and went from 15.6 to 77.9 percent on AIME 2024, learning longer, self-checking reasoning along the way.',
    recap=[('Problem', 'learned RMs can be hacked; PPO\'s critic is expensive.'), ('Core idea', 'verifier rewards + group-normalized advantages (r − mean)/std, no critic.'), ('Results', 'DeepSeekMath MATH 46.8→51.7%; R1-Zero AIME 15.6→77.9% with RL only.')],
)

# =============================================================== 09
DECKS['09-rlaif-constitutional-ai'] = dict(
    title='RLAIF and Constitutional AI', h1='RLAIF and Constitutional AI',
    sub='Using a model, guided by a written set of principles, to produce the feedback that humans used to provide: critique-and-revise for SFT, and AI preference labels for RL.',
    prob='Human preference labels are slow and expensive, and for harmful requests they require people to read and judge harmful content. The rules the model is meant to follow are also implicit in thousands of individual labels.',
    core='Write the rules down as a <b>constitution</b>. In a supervised stage, the model critiques and revises its own answers against principles; in an RL stage, an AI model compares pairs of answers against principles, and RL uses a preference model trained on those <b>AI labels</b> (RLAIF).',
    build=[],
    sources='Bai et al. 2022, "Constitutional AI: Harmlessness from AI Feedback" (§1, §3 SL-CAI, §4 RL-CAI); Christiano et al. 2017; Ouyang et al. 2022.',
    slides=[
        section('s-p1', 1, 'Feedback is the bottleneck', '''    <div class="grid3">
      <div class="card d"><h3>Scale</h3><p>Every RLHF round needs new comparisons on the latest model's outputs. Human labelling limits how often and how widely that can happen.</p></div>
      <div class="card b"><h3>Exposure</h3><p>Labelling harmlessness means people reading and ranking answers to harmful requests.</p></div>
      <div class="card c"><h3>Opacity</h3><p>The intended behaviour lives implicitly in many individual judgements. Nobody can read off "the rules" the model was trained on.</p></div>
    </div>'''),
        section('s-lim', 2, 'The harmless-but-evasive trap', '''    <p class="lede">An easy way to be "harmless" is to refuse anything borderline. That is unhelpful and teaches users nothing. The Constitutional AI paper's goal was a "harmless but non-evasive" assistant that "engages with harmful queries by explaining its objections to them".</p>
''' + deep('Why plain preference labels push towards evasion', '<p>If labelers judging harmlessness in isolation tend to prefer a refusal over any risky-looking answer, the reward model learns that refusing scores well, and RL amplifies it. Writing explicit principles that ask for explanations instead of bare refusals is one way to steer away from that.</p>')),
        your_turn('s-turn', 'What does "RLAIF" replace?',
                  'In the Constitutional AI paper, what does RL from AI Feedback replace?',
                  ['The pretraining data', 'Human preference labels for harmlessness', 'The PPO algorithm', 'All human involvement'], 1,
                  '<b>B.</b> "We replace human preferences for harmlessness with \'AI feedback\'": an AI evaluates responses according to constitutional principles. Humans still write the principles, and the paper still used human feedback for helpfulness.'),
        section('s-core', 4, 'Two stages', '''    <div class="grid2">
      <div class="card a"><h3>Supervised stage (SL-CAI)</h3><p>Sample responses to harmful (red-team) prompts from a <b>helpful-only</b> RLHF model; ask it to <b>critique</b> its own response against a randomly chosen principle, then <b>revise</b> it; repeat. Fine-tune the original model on the revised responses.</p></div>
      <div class="card e"><h3>RL stage (RL-CAI, i.e. RLAIF)</h3><p>Sample pairs of responses from the SL-CAI model; ask a model which one better satisfies a principle; train a preference model on these AI labels; run RL against it, exactly as in RLHF. The paper wrote <b>16 principles</b> and sampled one at random for each comparison label.</p></div>
    </div>
''' + deep('Chain of thought helps the judge', '<p>The paper reports that "both the SL and RL methods can leverage chain-of-thought style reasoning to improve the human-judged performance and transparency of AI decision making": asking the feedback model to reason before choosing makes its labels better and easier to inspect.</p>')),
        section('s-how', 5, 'Critique and revise, step by step <span class="ill">illustrative example</span>', '''    <p class="lede">An invented, low-stakes example of the SL-CAI loop, to show the mechanics. Real constitutions contain many principles; one is sampled for each critique.</p>
    <div class="visual">
      <div class="seg" id="cSeg"><button data-v="0" class="on">1 · prompt + response</button><button data-v="1">2 · principle</button><button data-v="2">3 · critique</button><button data-v="3">4 · revision</button><button data-v="4">5 · training data</button></div>
      <div class="infobox" id="cOut" style="background:var(--panel-2);border-radius:10px;padding:14px 16px;margin-top:12px;font-size:15px;line-height:1.6"></div>
    </div>'''),
        section('s-how2', 5, 'Where AI feedback plugs into the pipeline', '''    <div class="visual scroll-x"><table class="tbl">
      <tr><th>Step</th><th>RLHF</th><th>Constitutional AI (RLAIF)</th></tr>
      <tr><td>Supervised data</td><td>human demonstrations</td><td>model's own responses, critiqued and revised against principles</td></tr>
      <tr><td>Comparisons</td><td>human labelers pick the better response</td><td>a feedback model picks the response that better follows a principle</td></tr>
      <tr><td>Reward / preference model</td><td>trained on human labels</td><td>trained on AI labels (harmlessness) mixed with human labels (helpfulness)</td></tr>
      <tr><td>RL</td><td>PPO against the RM</td><td>same: RL against the preference model</td></tr>
      <tr><td>What humans provide</td><td>many individual judgements</td><td>a short list of written principles, plus helpfulness data</td></tr>
    </table></div>'''),
        section('s-why', 6, 'Why it works, and what to watch', '''    <div class="grid2">
      <div class="card a"><h3>Judging is easier than generating</h3><p>A capable model can often tell which of two answers better follows a stated principle even if its own first answer didn't.</p></div>
      <div class="card e"><h3>Scalable and inspectable</h3><p>AI labels are cheap to regenerate for every new model, and the principles are written down, so the target behaviour can be read, debated and changed.</p></div>
      <div class="card b"><h3>The feedback model's limits carry over</h3><p>If the judging model misreads a principle or has blind spots, those errors become training signal, so AI feedback still needs human evaluation.</p></div>
      <div class="card c"><h3>Widely reused idea</h3><p>Model-generated judgements now appear throughout post-training: rejection sampling with reward models, synthetic SFT data, and LLM-as-judge evaluation (Evals topic).</p></div>
    </div>'''),
        myths('s-myth', [
            ('RLAIF removes humans from alignment.', 'Humans write and choose the principles, and the paper still used human feedback for helpfulness. What changes is who produces each individual label.'),
            ('Constitutional AI is just a system prompt with rules.', 'The principles are used to <b>generate training data</b>: revised responses for SFT and AI preference labels for a preference model and RL. The behaviour is trained into the weights.'),
            ('Being harmless means refusing more.', 'The paper aimed for "harmless but non-evasive": engaging with the request and explaining objections rather than refusing blindly.'),
        ]),
        check('s-check', [
            ('open', 'Describe the two stages of Constitutional AI.', 'SL-CAI: the model critiques and revises its own responses against sampled principles, and is fine-tuned on the revisions. RL-CAI: a model labels which of two responses better follows a principle; a preference model is trained on those AI labels and used for RL (RLAIF).'),
            ('mcq', 'Which part of the Constitutional AI pipeline still used human preference labels?', ['Harmlessness', 'Helpfulness', 'Neither', 'Both'], 1, '<b>Helpfulness.</b> AI feedback replaced human labels for harmlessness.'),
            ('open', 'Why might AI feedback make the target behaviour more transparent?', 'The behaviour is specified by a short written list of principles that anyone can read, and chain-of-thought judgements show why each label was chosen, instead of being implicit in thousands of individual human labels.'),
        ]),
    ],
    js=r'''
  const C = [
    '<b>Prompt:</b> My neighbour\'s dog barks all night. Write a note I can leave on their door.<br><br><b>Initial response:</b> <span style="color:var(--muted)">"Your dog is a nightmare and you clearly don\'t care about anyone else. Fix it or I\'ll call the police."</span>',
    '<b>Sampled principle:</b> <span style="color:var(--muted)">"Choose the response that is most respectful and least likely to escalate a conflict, while still being helpful."</span>',
    '<b>Critique (written by the model):</b> <span style="color:var(--muted)">The note is hostile and accusatory. It assumes bad intent and threatens the neighbour, which is likely to escalate the conflict rather than solve the problem. A helpful note should describe the problem, assume good faith and suggest a next step.</span>',
    '<b>Revision (written by the model):</b> <span style="color:var(--muted)">"Hi! I live next door. Your dog has been barking a lot at night recently, and it\'s keeping me awake. You may not have noticed if you\'re asleep or out. Could we have a chat about it? Thanks, your neighbour at no. 12."</span>',
    '<b>Result:</b> the pair (prompt, revised response) becomes an SFT example. After several critique/revision rounds over many prompts and principles, the model is fine-tuned on the revisions (SL-CAI). In the RL stage, a model would instead be asked which of two sampled responses better follows the principle, producing an AI preference label.',
  ];
  Deck.seg('cSeg', v => { document.getElementById('cOut').innerHTML = C[+v]; });
''',
    line='Constitutional AI replaces human harmlessness labels with AI feedback guided by written principles: self-critique and revision for SFT, AI preference labels for RL.',
    explain='Human feedback is slow, hard to scale, and leaves the intended rules implicit. Constitutional AI writes those rules down as principles. In the supervised stage the model critiques its own responses against a sampled principle and revises them, and is fine-tuned on the revisions. In the RL stage a model compares pairs of responses against principles, a preference model is trained on those AI labels, and RL proceeds as in RLHF. That is RLAIF. The goal was an assistant that is harmless but not evasive, explaining its objections rather than refusing blindly. Humans still write the principles, and the paper kept human labels for helpfulness.',
    recap=[('Problem', 'human labels are slow, expensive and leave the rules implicit.'), ('Core idea', 'principles + AI critique/revision (SL-CAI) + AI preference labels for RL (RLAIF).'), ('Watch', 'the judge\'s blind spots become training signal; humans still set the principles.')],
)
