from tool import section, your_turn, myths, check

DECKS = {}


def deep(title, html):
    return f'    <div class="deep"><h4>{title}</h4>{html}</div>'


INFOBOX = 'class="infobox" style="background:var(--panel-2);border-radius:10px;padding:12px 14px;margin-top:10px;font-size:14px;color:var(--muted)"'

# =============================================================== 01
DECKS['01-what-an-eval-measures'] = dict(
    title='What an Eval Measures', h1='What an eval measures',
    sub='An eval score is the result of a task, a prompt, a sampling setup, a scoring rule and a sample of questions. Change any one and the number changes.',
    prob='Teams ship, rank and choose models based on single eval numbers, yet those numbers depend on many choices that are rarely reported, and accuracy alone hides most of what matters.',
    core='Treat every score as <b>a measurement with a protocol</b>: what capability, which questions, which prompt and decoding, which scoring rule, how much uncertainty. Measure more than accuracy, and report the setup with the number.',
    build=[],
    sources='Liang et al. 2022, "Holistic Evaluation of Language Models" (HELM: 7 metrics, 16 core scenarios, 42 scenarios, 30 models); Sclar et al. 2023, "Quantifying Language Models\' Sensitivity to Spurious Features in Prompt Design" (up to 76 points); Miller 2024, "Adding Error Bars to Evals".',
    slides=[
        section('s-p1', 1, 'One model, one benchmark, many scores', '''    <p class="lede">Every eval result passes through a pipeline of choices. Click each stage to see the decision it hides and how much it can move the number.</p>
    <div class="visual">
      <div class="seg" id="pSeg" style="flex-wrap:wrap"><button data-v="0" class="on">Capability</button><button data-v="1">Questions</button><button data-v="2">Prompt format</button><button data-v="3">Decoding</button><button data-v="4">Scoring</button><button data-v="5">Uncertainty</button></div>
      <div ''' + INFOBOX + ''' id="pInfo" style="font-size:15px;line-height:1.6"></div>
    </div>'''),
        section('s-lim', 2, 'Why a single number misleads', '''    <div class="grid3">
      <div class="card d"><h3>Prompt sensitivity</h3><p>Sclar et al. found accuracy varying by up to <b>76 points</b> for LLaMA-2-13B across semantically equivalent prompt formats (separators, spacing, casing). A comparison that uses one format per model can be decided by formatting.</p></div>
      <div class="card b"><h3>Accuracy isn't everything</h3><p>A model can be accurate but badly calibrated, brittle to typos, biased or slow. HELM measures 7 metrics per scenario precisely so the trade-offs stay visible.</p></div>
      <div class="card c"><h3>Sampling error</h3><p>Benchmarks are finite samples of questions. With 1,000 questions at 70% accuracy, the 95% interval is about ±2.8 points, often wider than the gap being celebrated (deck 04).</p></div>
    </div>'''),
        your_turn('s-turn', 'Same model, different numbers',
                  'Two papers report different MMLU scores for the same model. Which is the LEAST likely explanation?',
                  ['Different prompt formats or number of few-shot examples', 'Scoring by option log-probability vs by parsing generated text', 'Different random seeds for sampling', 'The model\'s weights changed between runs'], 3,
                  '<b>D.</b> Same weights, but every other item is a common source of differences. Prompt format alone can swing results by tens of points (Sclar et al.), and how the answer is extracted and scored differs between evaluation harnesses.'),
        section('s-core', 4, 'A score is a measurement protocol', '''    <div class="grid3">
      <div class="card a"><h3>Validity</h3><p>Does the task measure the capability you care about? Multiple-choice trivia measures recognition, not the ability to write a correct answer from scratch.</p></div>
      <div class="card b"><h3>Reliability</h3><p>Would you get the same number again with other prompts, seeds or a fresh sample of questions? Report standard errors and sensitivity, not just a point estimate.</p></div>
      <div class="card e"><h3>Coverage</h3><p>Measure several properties (accuracy, calibration, robustness, safety, cost) across several scenarios, so a gain in one isn't hiding a loss in another.</p></div>
    </div>
''' + deep('HELM\'s design', '<p>HELM measures <b>7 metrics</b> (accuracy, calibration, robustness, fairness, bias, toxicity and efficiency) on <b>16 core scenarios</b> "to the extent possible (87.5% of the time)", and evaluates <b>30</b> prominent models on <b>42</b> scenarios under standardized conditions. The point is to make the full trade-off visible rather than one leaderboard column.</p>')),
        section('s-how', 5, 'Prompt format sensitivity <span class="ill">illustrative</span>', '''    <p class="lede">The same 5 questions asked in different, equivalent formats. In this illustration the model's answers change with the format, as Sclar et al. measured at scale. A robust evaluation reports the <b>spread</b> across formats, not one pick.</p>
    <div class="visual">
      <div class="seg" id="fSeg"><button data-v="0" class="on">"Question: … Answer:"</button><button data-v="1">"Q: … A:"</button><button data-v="2">"QUESTION … ANSWER"</button><button data-v="3">"question - … answer -"</button></div>
      <div id="fBars" style="margin-top:12px"></div>
      <p class="readout" id="fOut"></p>
    </div>
    <p class="caption">Illustrative accuracies for one model on one task. The real reported spread: up to 76 accuracy points for LLaMA-2-13B on some tasks.</p>'''),
        section('s-how2', 5, 'A checklist for reading any eval result', '''    <div class="visual scroll-x"><table class="tbl">
      <tr><th>Question to ask</th><th>Why it matters</th><th>Deck</th></tr>
      <tr><td>Which benchmark version, split and number of questions?</td><td>Sets the sampling error and which questions count</td><td>02, 04</td></tr>
      <tr><td>Zero-shot or few-shot? Which prompt template? Chain of thought?</td><td>Format and shots can move scores by many points</td><td>01</td></tr>
      <tr><td>Greedy or sampled? How many samples? Which k?</td><td>pass@1 and pass@100 answer different questions</td><td>03</td></tr>
      <tr><td>How is the answer extracted and scored?</td><td>Log-prob of options vs parsed generation vs a judge model</td><td>02, 06</td></tr>
      <tr><td>What is the standard error, and was the comparison paired?</td><td>Is the difference real?</td><td>04</td></tr>
      <tr><td>Could the test set be in the training data?</td><td>Memorization inflates scores</td><td>05</td></tr>
    </table></div>'''),
        section('s-why', 6, 'Why the protocol view helps', '''    <div class="grid2">
      <div class="card a"><h3>Comparisons become fair</h3><p>Same prompts, same scoring and same questions for every model, as in HELM's standardized setup, make differences interpretable.</p></div>
      <div class="card e"><h3>Uncertainty becomes visible</h3><p>With standard errors and format spreads you can tell a real improvement from noise.</p></div>
      <div class="card b"><h3>Trade-offs stay honest</h3><p>Seeing calibration, robustness and cost next to accuracy stops a model from winning on one axis by losing on another.</p></div>
      <div class="card c"><h3>Results transfer</h3><p>A score whose protocol you know can be reproduced and compared with next year's models.</p></div>
    </div>'''),
        myths('s-myth', [
            ('A benchmark score is a property of the model.', 'It is a property of the model <b>plus</b> the prompt, decoding, scoring and question sample. Change those and the score changes, sometimes by a lot.'),
            ('Higher accuracy means a better model, full stop.', 'Accuracy can trade off against calibration, robustness, safety and cost. HELM reports 7 metrics for exactly this reason.'),
            ('If two papers use the same benchmark, their numbers are comparable.', 'Only if the protocol matches: version, shots, template, extraction and scoring. Often it doesn\'t.'),
        ]),
        check('s-check', [
            ('mcq', 'How many metrics does HELM measure for each core scenario?', ['1 (accuracy)', '3', '7', '42'], 2, '<b>7</b>: accuracy, calibration, robustness, fairness, bias, toxicity, efficiency.'),
            ('open', 'Name four protocol choices you would want reported with a benchmark score.', 'Benchmark version and number of questions; shots and prompt template; decoding (greedy or sampled, number of samples, k); answer extraction and scoring rule; standard error; contamination checks.'),
            ('open', 'How would you make a prompt-format comparison robust?', 'Evaluate each model over a set of equivalent formats and report the mean and spread (or the full distribution), rather than one format chosen per model.'),
        ]),
    ],
    js=r'''
  const P = [
    '<b>Capability.</b> What should the number tell you? "Knows chemistry facts", "can solve new maths problems", "fixes real bugs" and "users prefer it" need different evals. A mismatch here makes everything downstream irrelevant.',
    '<b>Questions.</b> Which benchmark, version and split, and how many questions? A few hundred questions give confidence intervals several points wide. Questions may also have leaked into training data (deck 05).',
    '<b>Prompt format.</b> Template, separators, number of few-shot examples, chain of thought or not. Sclar et al.: up to 76 accuracy points between equivalent formats for LLaMA-2-13B.',
    '<b>Decoding.</b> Greedy or sampled, temperature, how many samples. pass@1 measures reliability; pass@k with many samples measures whether the model can ever get it (deck 03).',
    '<b>Scoring.</b> Exact match, log-probability of each option, regex-parsing a generated answer, unit tests, or an LLM judge. Each makes different mistakes (decks 02, 06).',
    '<b>Uncertainty.</b> The score is a sample mean with a standard error. Grouped questions need clustered errors, and model comparisons should be paired (deck 04).',
  ];
  Deck.seg('pSeg', v => { document.getElementById('pInfo').innerHTML = P[+v]; });
  const F = [0.62, 0.48, 0.71, 0.36];
  Deck.seg('fSeg', v => {
    Deck.hbars(document.getElementById('fBars'), F.map((a, i) => ({ label: ['"Question: … Answer:"', '"Q: … A:"', '"QUESTION … ANSWER"', '"question - … answer -"'][i], value: a, color: i === +v ? 'var(--a)' : 'var(--faint)', text: (100 * a).toFixed(0) + '%' })), { max: 1 });
    document.getElementById('fOut').innerHTML = `Selected format: <b>${(100 * F[+v]).toFixed(0)}%</b>. Across formats: mean ${(100 * F.reduce((a, b) => a + b) / 4).toFixed(0)}%, range ${(100 * Math.min(...F)).toFixed(0)}–${(100 * Math.max(...F)).toFixed(0)}%. Reporting only one format hides a ${(100 * (Math.max(...F) - Math.min(...F))).toFixed(0)}-point spread.`;
  });
''',
    line='An eval score is a measurement protocol (capability, questions, prompt, decoding, scoring, uncertainty), so report the protocol and more than one metric along with the number.',
    explain='A benchmark number depends on the capability the task actually measures, which questions were used, the prompt format, how answers were sampled, how they were scored, and sampling error. Prompt format alone moved LLaMA-2-13B by up to 76 accuracy points between equivalent formats, and 1,000 questions give about plus or minus 2.8 points of uncertainty. HELM\'s answer is to standardize the setup and measure seven properties, from accuracy and calibration to toxicity and efficiency, across many scenarios. In practice: report the protocol, standard errors and spreads, and look beyond accuracy.',
    recap=[('Problem', 'single numbers hide prompts, scoring, sampling error and trade-offs.'), ('Core idea', 'a score = model + protocol; standardize it and measure several metrics.'), ('Practice', 'report setup, standard errors and format spread; check contamination.')],
)

# =============================================================== 02
DECKS['02-benchmarks'] = dict(
    title='Benchmarks and Their Failure Modes', h1='Benchmarks and their failure modes',
    sub='Multiple-choice, generative, code and agentic benchmarks: how each is scored, what it really measures, and why benchmarks saturate and get replaced.',
    prob='Benchmarks are how the field measures progress, but each format has blind spots, and once models approach the ceiling a benchmark stops telling models apart.',
    core='Pick benchmarks whose <b>format matches the capability</b> (recognize vs produce vs act), check how answers are <b>scored</b>, know the <b>chance and expert baselines</b>, and move to harder or fresher sets as a benchmark <b>saturates</b>.',
    build=['02_error_bars', '03_contamination'],
    sources='Hendrycks et al. 2021 (MMLU: 57 tasks); Wang et al. 2024 (MMLU-Pro: 10 options, 16–33% drop); Rein et al. 2023 (GPQA: 448 questions, experts 65%, non-experts 34%, GPT-4 39%); Cobbe et al. 2021 (GSM8K: 8.5K problems); Chen et al. 2021 (HumanEval: 164 problems); Jimenez et al. 2024 (SWE-bench: 2,294 issues, 1.96%).',
    slides=[
        section('s-p1', 1, 'Four kinds of benchmark', '''    <div class="grid2">
      <div class="card a"><h3>Multiple choice (MMLU, GPQA)</h3><p>Pick one of the given options. Cheap and unambiguous to score, but measures <b>recognition</b>, and a random guess already scores 1/(number of options).</p></div>
      <div class="card b"><h3>Short answer (GSM8K)</h3><p>Produce a final answer (a number) that is compared with the reference. 8.5K grade-school maths word problems; scoring depends on extracting the answer correctly.</p></div>
      <div class="card e"><h3>Code with tests (HumanEval)</h3><p>164 hand-written programming problems; the generated function must pass unit tests. Functional correctness instead of text similarity.</p></div>
      <div class="card c"><h3>Agentic (SWE-bench)</h3><p>2,294 real GitHub issues: edit a repository so the project's tests pass. Measures multi-step work in a realistic environment; at release the best model, Claude 2, solved 1.96%.</p></div>
    </div>'''),
        section('s-lim', 2, 'How benchmarks fail', '''    <div class="grid3">
      <div class="card d"><h3>Saturation</h3><p>Once top models score near the ceiling (or near the label-noise limit), differences shrink into the error bars and the benchmark stops ranking models.</p></div>
      <div class="card b"><h3>Shortcuts</h3><p>With 4 options, eliminating two weak distractors gives 50% without knowing the answer. MMLU-Pro raised options from 4 to 10 and accuracy dropped by 16–33%.</p></div>
      <div class="card c"><h3>Contamination and label errors</h3><p>Public test sets leak into training data (deck 05), and some "correct" answers are themselves wrong, which caps the achievable score.</p></div>
    </div>'''),
        your_turn('s-turn', 'Read the baselines',
                  'GPQA reports experts at 65%, skilled non-experts with web access at 34%, and GPT-4 at 39%. What makes GPQA useful as a benchmark?',
                  ['It is easy for everyone', 'Answers are hard to look up: non-experts barely beat guessing even with 30+ minutes of web search', 'It has many more questions than MMLU', 'It is open-ended'], 1,
                  '<b>B.</b> "Google-proof": the large gap between experts (65%) and skilled non-experts with unrestricted web access (34%, near the 25% chance level) means retrieval alone doesn\'t solve it, so it still separates strong models.'),
        section('s-core', 4, 'Know the floor, the ceiling and the format', '''    <div class="grid3">
      <div class="card a"><h3>Floor</h3><p>Chance level: 25% for 4 options, 10% for 10. MMLU's original paper: GPT-3 175B improved over random chance "by almost 20 percentage points on average".</p></div>
      <div class="card b"><h3>Ceiling</h3><p>Expert accuracy and label noise. If experts score 65% (GPQA) or some labels are wrong, 100% is neither expected nor meaningful.</p></div>
      <div class="card e"><h3>Format fit</h3><p>Recognize (multiple choice), produce (short answer, code), or act over many steps (agents). Use the format closest to how the model will be used.</p></div>
    </div>
''' + deep('Scoring multiple choice', '<p>Two common ways: compare the model\'s <b>log-probability</b> of each option (or option letter) and take the highest, or let the model <b>generate</b> an answer and parse the letter. They can give different scores for the same model: the first never fails to produce a valid answer, the second also tests instruction following and can lose points to parsing errors. Harnesses differ here, which is one reason published numbers disagree.</p>')),
        section('s-how', 5, 'Chance level vs number of options', '''    <p class="lede">Expected accuracy for a model that knows a fraction of the answers and guesses uniformly on the rest. More options lower the floor and make guessing less rewarding, which is part of how MMLU-Pro separates models better.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">Fraction truly known <input type="range" id="kK" min="0" max="1" step="0.05" value="0.5"> <output id="kKo"></output></label>
        <label class="ctl">Distractors eliminated <input type="range" id="kE" min="0" max="2" step="1" value="0"> <output id="kEo"></output></label>
      </div>
      <div id="kBars" style="margin-top:12px"></div>
    </div>'''),
        section('s-how2', 5, 'Benchmarks at a glance', '''    <div class="visual scroll-x"><table class="tbl">
      <tr><th>Benchmark</th><th>Size</th><th>Format / scoring</th><th>Reference points</th></tr>
      <tr><td>MMLU</td><td>57 tasks</td><td>4-option multiple choice</td><td>GPT-3 175B ≈ chance + 20 points at release</td></tr>
      <tr><td>MMLU-Pro</td><td>10 options</td><td>harder, reasoning-focused multiple choice</td><td>16–33% lower accuracy than MMLU</td></tr>
      <tr><td>GPQA</td><td>448 questions</td><td>expert-written multiple choice</td><td>experts 65%, non-experts 34%, GPT-4 39%</td></tr>
      <tr><td>GSM8K</td><td>8.5K problems</td><td>maths word problems, final-answer match</td><td>saturating; fresh variants show overfitting (deck 05)</td></tr>
      <tr><td>HumanEval</td><td>164 problems</td><td>Python functions, unit tests, pass@k</td><td>Codex-12B 28.8% pass@1</td></tr>
      <tr><td>SWE-bench</td><td>2,294 issues</td><td>edit a real repo, project tests must pass</td><td>Claude 2 1.96% at release</td></tr>
    </table></div>'''),
        section('s-why', 6, 'Why benchmarks keep being replaced', '''    <div class="grid2">
      <div class="card a"><h3>Progress compresses scores</h3><p>Near the ceiling, gaps between models fall inside the error bars, so the benchmark no longer ranks them.</p></div>
      <div class="card e"><h3>Harder versions restore spread</h3><p>More options (MMLU-Pro), expert-only questions (GPQA) and realistic tasks (SWE-bench) re-open the range.</p></div>
      <div class="card b"><h3>Fresh sets fight leakage</h3><p>The longer a test set is public, the more likely it is in training data. New or held-out sets restore trust.</p></div>
      <div class="card c"><h3>Usage moves on</h3><p>As models are used as agents and coders, benchmarks shift from recognizing answers to doing work end to end.</p></div>
    </div>'''),
        myths('s-myth', [
            ('25% on a 4-option benchmark means the model knows a quarter of the material.', '25% is what random guessing gets. Knowledge shows up only above the chance floor.'),
            ('A model at 90% on a saturated benchmark is clearly better than one at 88%.', 'Near the ceiling, a 2-point gap may be within the error bars or caused by label noise and prompt format.'),
            ('Multiple-choice accuracy shows the model can produce the answer.', 'It shows the model can <b>recognize</b> the answer among options. Producing it unaided is a harder, different skill.'),
        ]),
        check('s-check', [
            ('mcq', 'MMLU-Pro increased the number of options to…', ['5', '8', '10', '26'], 2, '<b>10</b>, lowering the chance floor to 10%, and accuracy dropped 16–33%.'),
            ('open', 'Why can log-prob scoring and generation scoring disagree on the same multiple-choice benchmark?', 'Log-prob scoring always yields a valid choice; generation can produce unparseable or differently formatted answers and also depends on instruction following and the parser.'),
            ('open', 'What does SWE-bench measure that HumanEval doesn\'t?', 'Working in a real repository on real issues: finding the relevant code, making multi-file edits and passing the project\'s own tests, rather than writing one standalone function.'),
        ]),
    ],
    js=r'''
  Deck.bind(['kK', 'kE'], () => {
    const k = Deck.val('kK'), e = Deck.val('kE'); Deck.out('kKo', (100 * k).toFixed(0) + '%'); Deck.out('kEo', e);
    const acc = n => k + (1 - k) / Math.max(1, n - e);
    Deck.hbars(document.getElementById('kBars'), [4, 10].map(n => ({ label: `${n} options (chance ${(100 / n).toFixed(0)}%)`, value: acc(n), color: n === 4 ? 'var(--b)' : 'var(--a)', text: (100 * acc(n)).toFixed(1) + '%' })), { max: 1 });
  });
''',
    line='Choose benchmarks by format (recognize, produce, act), read them against chance and expert baselines, and expect saturation, shortcuts and leakage to retire them.',
    explain='Benchmarks differ in what they measure. Multiple-choice sets like MMLU test recognition and have a guessing floor; short-answer sets like GSM8K test producing an answer; HumanEval checks code with unit tests; SWE-bench asks a model to resolve real GitHub issues, where the best model at release solved under 2 percent. Scores must be read against chance and expert levels: on GPQA experts score 65 percent and skilled non-experts with web search only 34. As models improve, benchmarks saturate, shortcuts appear and test sets leak, so harder versions like MMLU-Pro, with ten options and 16 to 33 percent lower scores, replace them.',
    recap=[('Problem', 'each format has blind spots; benchmarks saturate.'), ('Core idea', 'match format to capability; know floor, ceiling and scoring.'), ('Examples', 'MMLU/MMLU-Pro, GPQA, GSM8K, HumanEval, SWE-bench.')],
)

# =============================================================== 03
DECKS['03-pass-at-k'] = dict(
    title='pass@k and Sampling Metrics', h1='pass@k and sampling metrics',
    sub='When a model can try several times, what should the score be? pass@k, its unbiased estimator, and how to choose between pass@1 and pass@100.',
    prob='Generation is stochastic. A model that solves a problem 1 time in 10 looks like a failure with one sample and a success with 100. A single sample per problem is also a very noisy estimate.',
    core='Sample <b>n</b> solutions per problem, count the <b>c</b> that pass, and estimate pass@k = 1 − C(n−c, k)/C(n, k): the chance that at least one of k attempts passes. Report the k that matches how the model will be used.',
    build=['01_pass_at_k'],
    sources='Chen et al. 2021, "Evaluating Large Language Models Trained on Code" (HumanEval, §2.1 unbiased estimator, 28.8% pass@1 and 70.2% with 100 samples); Jimenez et al. 2024 (SWE-bench).',
    slides=[
        section('s-p1', 1, 'One sample or many?', '''    <p class="lede">A problem the model solves with probability p per attempt. With k attempts, the chance that at least one succeeds is 1 − (1−p)<sup>k</sup>. The same model looks very different at k = 1 and k = 100.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0"><label class="ctl">per-attempt success p <input type="range" id="pP" min="0.01" max="0.9" step="0.01" value="0.1"> <output id="pPo"></output></label></div>
      <svg id="pSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="pass@k vs k"></svg>
      <p class="readout" id="pOut"></p>
    </div>'''),
        section('s-lim', 2, 'Problems with the obvious approaches', '''    <div class="grid3">
      <div class="card d"><h3>Exactly k samples is noisy</h3><p>Drawing exactly k samples per problem and checking for a pass gives a 0/1 result per problem with high variance.</p></div>
      <div class="card b"><h3>Plug-in is biased</h3><p>Estimating p̂ = c/n and computing 1 − (1−p̂)<sup>k</sup> underestimates pass@k, because the curve is concave in p (notebook 01 measures −0.06 at p = 0.05, n = 20, k = 10).</p></div>
      <div class="card c"><h3>Text similarity isn't correctness</h3><p>BLEU-style metrics reward code that looks like the reference. HumanEval uses unit tests: functional correctness.</p></div>
    </div>'''),
        your_turn('s-turn', 'Compute pass@k',
                  'You sample n = 10 solutions and c = 3 pass. What is the unbiased estimate of pass@1?',
                  ['0.1', '0.3', '0.97', '1 − 0.7¹⁰'], 1,
                  '<b>B.</b> pass@1 = 1 − C(7,1)/C(10,1) = 1 − 7/10 = 0.3 = c/n. With k = 1 the estimator is simply the fraction of samples that pass, averaged over problems.'),
        section('s-core', 4, 'The unbiased estimator', '''    <div class="grid3">
      <div class="card a"><h3>Sample n ≥ k</h3><p>For each problem generate n samples (Codex used n = 200) and run the tests; c pass.</p></div>
      <div class="card b"><h3>Count subsets</h3><p>pass@k = 1 − C(n−c, k)/C(n, k): one minus the probability that a random size-k subset of the n samples contains no passing sample. Average over problems.</p></div>
      <div class="card e"><h3>Compute stably</h3><p>Binomials overflow, so use the product form 1 − ∏<sub>i=n−c+1..n</sub>(1 − k/i), as in the paper\'s numpy snippet. If n − c &lt; k, the answer is 1.</p></div>
    </div>'''),
        section('s-how', 5, 'pass@k calculator', '''    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">n samples <input type="range" id="cN" min="1" max="200" step="1" value="20"> <output id="cNo"></output></label>
        <label class="ctl">c passing <input type="range" id="cC" min="0" max="200" step="1" value="2"> <output id="cCo"></output></label>
        <label class="ctl">k <input type="range" id="cK" min="1" max="100" step="1" value="10"> <output id="cKo"></output></label>
      </div>
      <div class="grid3" style="margin-top:14px">
        <div class="stat"><div class="num" id="cU" style="color:var(--a)"></div><div class="lbl">unbiased pass@k</div></div>
        <div class="stat"><div class="num" id="cB"></div><div class="lbl">plug-in 1 − (1 − c/n)<sup>k</sup></div></div>
        <div class="stat"><div class="num" id="c1"></div><div class="lbl">pass@1 = c/n</div></div>
      </div>
      <p class="readout" id="cOut"></p>
    </div>'''),
        section('s-how2', 5, 'Which k should you report?', '''    <div class="grid2">
      <div class="card a"><h3>pass@1: reliability</h3><p>What a user gets from one attempt. Estimate it from many samples (n ≫ 1) for low variance; it equals the average per-sample pass rate.</p></div>
      <div class="card b"><h3>pass@k, k large: coverage</h3><p>Whether the model can solve it at all if you can verify attempts. Codex-12B: 28.8% at pass@1, and with 100 samples per problem 70.2% have at least one correct solution.</p></div>
      <div class="card e"><h3>Selection matters</h3><p>pass@k assumes an oracle picks a passing sample. Without one, you need a selection rule (highest likelihood, majority vote, a verifier), and the score falls between pass@1 and pass@k.</p></div>
      <div class="card c"><h3>Agentic tasks</h3><p>On SWE-bench-style tasks each attempt is expensive and long, so pass@1 with a fixed budget is usually what matters.</p></div>
    </div>'''),
        section('s-why', 6, 'Why the estimator is right', '''    <div class="grid2">
      <div class="card a"><h3>It is exact for the sample</h3><p>Given n samples with c passes, choosing k without replacement fails only if all k come from the n − c failures: probability C(n−c,k)/C(n,k). Averaging over the randomness in c gives exactly the true pass@k.</p></div>
      <div class="card e"><h3>It uses every sample</h3><p>All n samples contribute instead of k, which cuts variance compared with drawing exactly k.</p></div>
      <div class="card b"><h3>Notebook evidence</h3><p>At p = 0.05, n = 20, k = 10: unbiased error ≈ +0.004 (simulation noise), plug-in error −0.061.</p></div>
      <div class="card c"><h3>Tests define "pass"</h3><p>The metric is only as good as the unit tests: weak tests let wrong programs pass.</p></div>
    </div>'''),
        myths('s-myth', [
            ('pass@100 tells you how good the model is for users.', 'Users usually get one attempt. pass@100 measures what a verifier could select from 100 tries, which is a different question.'),
            ('1 − (1 − c/n)^k is a fine estimate of pass@k.', 'It is biased low because the function is concave. Use 1 − C(n−c,k)/C(n,k).'),
            ('pass@1 needs only one sample per problem.', 'One sample gives an unbiased but very noisy estimate. Many samples per problem give the same expectation with far lower variance.'),
        ]),
        check('s-check', [
            ('mcq', 'n = 5, c = 2, k = 4. pass@4 = ?', ['0.4', '0.8', '1.0', '0.87'], 2, '<b>1.0</b>: n − c = 3 &lt; k = 4, so every 4-subset contains a pass.'),
            ('open', 'Why is pass@k averaged over problems rather than computed from the pooled pass rate?', 'Problems differ in difficulty. pass@k is a per-problem probability; pooling the rate first and then applying 1 − (1−p)^k would mix easy and hard problems incorrectly (and is the biased plug-in).'),
            ('open', 'When is pass@k with large k the right metric?', 'When you can generate many candidates and automatically verify them (unit tests, a checker), so any passing sample can be selected.'),
        ]),
    ],
    js=r'''
  Deck.bind(['pP'], () => {
    const p = Deck.val('pP'); Deck.out('pPo', p.toFixed(2));
    const s = clear(document.getElementById('pSvg')), X = k => 60 + Math.log10(k) / 2 * 560, Y = v => 200 - v * 180;
    [0, 0.5, 1].forEach(v => { svg('line', { x1: 60, x2: 620, y1: Y(v), y2: Y(v), class: 'ln' }, s); svg('text', { x: 52, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm', text: v }, s); });
    [1, 10, 100].forEach(k => svg('text', { x: X(k), y: 218, 'text-anchor': 'middle', class: 'tm', text: 'k=' + k }, s));
    let pts = ''; for (let e = 0; e <= 2.001; e += 0.02) { const k = Math.pow(10, e); pts += `${X(k)},${Y(1 - Math.pow(1 - p, k))} `; }
    svg('polyline', { points: pts, fill: 'none', style: 'stroke:var(--a);stroke-width:3' }, s);
    document.getElementById('pOut').innerHTML = `pass@1 = <b>${p.toFixed(2)}</b>, pass@10 = <b>${(1 - Math.pow(1 - p, 10)).toFixed(2)}</b>, pass@100 = <b>${(1 - Math.pow(1 - p, 100)).toFixed(2)}</b>.`;
  });
  const passk = (n, c, k) => { if (n - c < k) return 1; let pr = 1; for (let i = n - c + 1; i <= n; i++) pr *= 1 - k / i; return 1 - pr; };
  Deck.bind(['cN', 'cC', 'cK'], () => {
    const N = document.getElementById('cN'), Cc = document.getElementById('cC'), K = document.getElementById('cK');
    const n = +N.value; if (+Cc.value > n) Cc.value = n; if (+K.value > n) K.value = n;
    const c = +Cc.value, k = +K.value; Deck.out('cNo', n); Deck.out('cCo', c); Deck.out('cKo', k);
    const u = passk(n, c, k), b = 1 - Math.pow(1 - c / n, k);
    Deck.out('cU', u.toFixed(3)); Deck.out('cB', b.toFixed(3)); Deck.out('c1', (c / n).toFixed(3));
    document.getElementById('cOut').innerHTML = n - c < k ? `n − c = ${n - c} &lt; k = ${k}: every subset of ${k} contains a passing sample, so pass@${k} = 1.` : `pass@${k} = 1 − C(${n - c}, ${k}) / C(${n}, ${k}). The plug-in differs by ${(b - u >= 0 ? '+' : '') + (b - u).toFixed(3)}.`;
  });
''',
    line='pass@k is the chance that at least one of k attempts passes; estimate it unbiasedly from n ≥ k samples as 1 − C(n−c,k)/C(n,k), and report the k that matches real use.',
    explain='Code and maths models are stochastic, so the score depends on how many attempts you allow. pass@k is the probability that at least one of k samples passes the tests. The Codex paper estimates it by drawing n samples per problem, counting the c that pass, and computing one minus the number of all-failing k-subsets over all k-subsets, averaged over problems, which is unbiased and uses every sample. The tempting plug-in of c over n into one minus one minus p to the k is biased low. pass@1 measures what a user gets from one try; large k measures what a verifier could find: Codex went from 28.8 percent at one sample to 70.2 percent with 100.',
    recap=[('Problem', 'stochastic generation: one sample is noisy, many samples need a definition.'), ('Core idea', 'pass@k = 1 − C(n−c,k)/C(n,k), product form for stability.'), ('Practice', 'pass@1 for reliability, large k only when attempts can be verified.')],
)

# =============================================================== 04
DECKS['04-error-bars'] = dict(
    title='Error Bars and Comparing Models', h1='Error bars and comparing models',
    sub='How much of an eval score is noise: standard errors, clustered questions, paired comparisons between models, and how many questions you need.',
    prob='Leaderboards rank models by gaps of a point or two, but an eval is a finite sample of questions, and those gaps are often smaller than the sampling error.',
    core='Report a <b>standard error</b> with every score; use <b>clustered</b> standard errors when questions come in groups; compare models with a <b>paired</b> test on per-question differences; size evals with <b>power analysis</b>.',
    build=['02_error_bars'],
    sources='Miller 2024, "Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations" (CLT standard errors, clustered SEs "can be over 3X larger", paired differences, power analysis); Chiang et al. 2024 (Chatbot Arena confidence intervals).',
    slides=[
        section('s-p1', 1, 'How wide is the error bar?', '''    <p class="lede">95% confidence interval half-width for an accuracy-style score: 1.96·√(p(1−p)/n). Move the number of questions and the accuracy.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">questions n <input type="range" id="eN" min="1.7" max="4.3" step="0.05" value="3"> <output id="eNo"></output></label>
        <label class="ctl">accuracy <input type="range" id="eP" min="0.05" max="0.95" step="0.05" value="0.7"> <output id="ePo"></output></label>
      </div>
      <svg id="eSvg" viewBox="0 0 660 120" style="margin-top:10px" role="img" aria-label="Confidence interval"></svg>
      <p class="readout" id="eOut"></p>
    </div>'''),
        section('s-lim', 2, 'Three common statistical mistakes', '''    <div class="grid3">
      <div class="card d"><h3>No error bars</h3><p>Reporting 71.3 vs 70.1 with no uncertainty invites over-reading a gap that may be noise.</p></div>
      <div class="card b"><h3>Ignoring clusters</h3><p>Ten questions about one passage, or one problem in ten languages, are not ten independent samples. Treating them as independent understates the error.</p></div>
      <div class="card c"><h3>Comparing separate intervals</h3><p>"The intervals overlap, so no difference" throws away the fact that both models answered the <b>same</b> questions, which a paired test exploits.</p></div>
    </div>'''),
        your_turn('s-turn', 'Is it a real improvement?',
                  'Model B scores 2 points higher than model A on the same 1,000 questions. Each score alone has a 95% interval of about ±2.8 points. What is the right next step?',
                  ['Conclude there is no difference because the intervals overlap', 'Conclude B is better because its score is higher', 'Test the per-question differences (a paired test)', 'Add more models to the comparison'], 2,
                  '<b>C.</b> Both models saw the same questions, so most of the noise (which questions are hard) is shared. The per-question differences have much smaller variance; in notebook 02\'s simulation, a ~3-point gap is detected 88% of the time with a paired test vs 10% by comparing separate intervals.'),
        section('s-core', 4, 'Four tools', '''    <div class="grid2">
      <div class="card a"><h3>Standard error (CLT)</h3><p>SE = √( (1/n) · (1/(n−1)) Σ(sᵢ − μ̂)² ); 95% CI = μ̂ ± 1.96·SE. Miller recommends this over bootstrapping as the default.</p></div>
      <div class="card b"><h3>Clustered SE</h3><p>Sum residuals within each cluster before squaring: SE = (1/n)·√(Σ<sub>c</sub>(Σ<sub>i∈c</sub>(sᵢ − μ̂))²). Report the cluster count next to the question count.</p></div>
      <div class="card e"><h3>Paired difference</h3><p>dᵢ = s<sup>A</sup>ᵢ − s<sup>B</sup>ᵢ; test mean(d) with SE = sd(d)/√n. Uses the shared question difficulty to cancel noise.</p></div>
      <div class="card c"><h3>Power analysis</h3><p>Questions needed to detect a gap δ (5% test, 80% power): n = ((1.96 + 0.84)·σ<sub>d</sub>/δ)². Halving δ needs 4× the questions.</p></div>
    </div>'''),
        section('s-how', 5, 'Paired vs unpaired <span class="ill">simulation</span>', '''    <p class="lede">Two models answer the same questions, simulated 120 times with notebook 02's model. The gap is real in every run. How often does each comparison notice it?</p>
    <div class="visual">
      <div class="controls" style="margin-top:0"><label class="ctl">true gap (log-odds) <input type="range" id="sG" min="0" max="0.4" step="0.05" value="0.2"> <output id="sGo"></output></label><label class="ctl">questions <input type="range" id="sN" min="200" max="4000" step="200" value="1000"> <output id="sNo"></output></label></div>
      <div class="grid3" style="margin-top:14px">
        <div class="stat"><div class="num" id="sD"></div><div class="lbl">average gap (points)</div></div>
        <div class="stat"><div class="num" id="sP" style="color:var(--a)"></div><div class="lbl">detected, paired test</div></div>
        <div class="stat"><div class="num" id="sU" style="color:var(--d)"></div><div class="lbl">detected, separate intervals</div></div>
      </div>
    </div>
    <p class="caption">120 simulated evals per setting, run in your browser. Questions vary in difficulty and the two models tend to fail the same ones (75% shared randomness).</p>'''),
        section('s-how2', 5, 'Clusters can triple the error', '''    <div class="visual"><div id="cBars"></div><p class="caption">Miller 2024, Table 4 (Anthropic models on real evals): clustered vs naive standard errors on the same data.</p></div>
''' + deep('Why clusters matter', '<p>Questions sharing a passage (DROP, RACE) or a source problem (MGSM\'s translations) succeed or fail together. The effective number of independent samples is closer to the number of <b>clusters</b> than the number of questions. Miller: "clustered standard errors can be over 3X larger than naive standard errors". Ratios above: DROP 3.05, MGSM 1.88, RACE-H 1.10.</p>')),
        section('s-why', 6, 'Why this matters for decisions', '''    <div class="grid2">
      <div class="card a"><h3>Avoid chasing noise</h3><p>Without error bars, teams "optimize" towards random fluctuations and pick checkpoints by luck.</p></div>
      <div class="card e"><h3>Get more from the same eval</h3><p>Paired tests detect real gaps that unpaired comparisons miss, with no extra questions.</p></div>
      <div class="card b"><h3>Design better evals</h3><p>Power analysis tells you before building an eval whether it can detect the differences you care about.</p></div>
      <div class="card c"><h3>Arenas do this too</h3><p>Chatbot Arena reports confidence intervals on its ratings, so overlapping models can be read as statistically tied (deck 07).</p></div>
    </div>'''),
        myths('s-myth', [
            ('Overlapping confidence intervals mean no significant difference.', 'Not for paired data. Two overlapping intervals can still hide a highly significant paired difference.'),
            ('More questions from the same passages give proportionally more precision.', 'Correlated questions add less information. Use clustered standard errors and count clusters.'),
            ('Bootstrapping is always needed for evals.', 'For mean scores the central-limit-theorem standard error is standard and simpler; Miller recommends it as the default.'),
        ]),
        check('s-check', [
            ('mcq', 'Roughly what is the 95% CI half-width for 70% accuracy on 1,000 questions?', ['±0.3 points', '±1 point', '±2.8 points', '±10 points'], 2, '1.96·√(0.7·0.3/1000) ≈ 0.028, so <b>±2.8 points</b>.'),
            ('open', 'Write the clustered standard error and say when to use it.', 'SE = (1/n)·√(Σ_c (Σ_{i∈c} (s_i − μ̂))²). Use it when questions come in correlated groups (shared passage, translations of one problem, multiple samples per prompt).'),
            ('open', 'You want to detect a 1-point gap and σ_d = 0.3. How many questions?', 'n = ((1.96 + 0.84)·0.3/0.01)² ≈ <b>7,060</b>. Small gaps need large evals.'),
        ]),
    ],
    js=r'''
  Deck.bind(['eN', 'eP'], () => {
    const n = Math.round(Math.pow(10, Deck.val('eN'))), p = Deck.val('eP'); Deck.out('eNo', n.toLocaleString()); Deck.out('ePo', (100 * p).toFixed(0) + '%');
    const h = 1.96 * Math.sqrt(p * (1 - p) / n), s = clear(document.getElementById('eSvg')), X = v => 30 + v * 600;
    svg('line', { x1: 30, x2: 630, y1: 60, y2: 60, class: 'ln' }, s);
    [0, 0.25, 0.5, 0.75, 1].forEach(v => svg('text', { x: X(v), y: 100, 'text-anchor': 'middle', class: 'tm', text: (100 * v) + '%' }, s));
    svg('rect', { x: X(Math.max(0, p - h)), y: 46, width: X(Math.min(1, p + h)) - X(Math.max(0, p - h)), height: 28, rx: 5, style: 'fill:var(--a-soft);stroke:var(--a)' }, s);
    svg('circle', { cx: X(p), cy: 60, r: 6, style: 'fill:var(--a)' }, s);
    document.getElementById('eOut').innerHTML = `95% CI: <b>${(100 * p).toFixed(0)}% ± ${(100 * h).toFixed(1)} points</b>. To halve the width you need 4× the questions.`;
  });
  const sig = z => 1 / (1 + Math.exp(-z));
  const simulate = (gap, nq) => {
    let seed = 12345; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647; const g = () => Math.sqrt(-2 * Math.log(Math.max(1e-9, rnd()))) * Math.cos(2 * Math.PI * rnd());
    let hp = 0, hu = 0, gs = 0; const R = 120;
    for (let r = 0; r < R; r++) {
      let sa = 0, sb = 0, sd = 0, sd2 = 0, sa2 = 0, sb2 = 0;
      for (let i = 0; i < nq; i++) {
        const lg = Math.log(0.7 / 0.3) - (1.5 * g() + g()), u = rnd(), ub = rnd() < 0.75 ? u : rnd();
        const a = u < sig(lg) ? 1 : 0, b = ub < sig(lg + gap) ? 1 : 0;
        sa += a; sb += b; sd += b - a; sd2 += (b - a) ** 2;
      }
      const ma = sa / nq, mb = sb / nq, md = sd / nq, vd = (sd2 - nq * md * md) / (nq - 1);
      const vu = (ma * (1 - ma) + mb * (1 - mb)) / (nq - 1);
      if (Math.abs(md) / Math.sqrt(vd / nq) > 1.96) hp++;
      if (Math.abs(md) / Math.sqrt(vu) > 1.96) hu++;
      gs += md;
    }
    return [gs / R, hp / R, hu / R];
  };
  Deck.bind(['sG', 'sN'], () => {
    const gap = Deck.val('sG'), nq = Deck.val('sN'); Deck.out('sGo', gap.toFixed(2)); Deck.out('sNo', nq.toLocaleString());
    const [d, p, u] = simulate(gap, nq);
    Deck.out('sD', (100 * d).toFixed(1)); Deck.out('sP', (100 * p).toFixed(0) + '%'); Deck.out('sU', (100 * u).toFixed(0) + '%');
  });
  Deck.hbars(document.getElementById('cBars'), [['DROP naive', 0.44], ['DROP clustered', 1.34], ['RACE-H naive', 0.46], ['RACE-H clustered', 0.51], ['MGSM naive', 0.86], ['MGSM clustered', 1.62]].map(([l, v]) => ({ label: l, value: v, color: l.includes('clustered') ? 'var(--d)' : 'var(--faint)', text: v.toFixed(2) })), { max: 1.5 });
''',
    line='Every eval score needs an error bar: CLT standard errors, clustered when questions are grouped, paired tests for model comparisons, and power analysis to size the eval.',
    explain='An eval is a finite sample of questions, so its score has sampling error: at 70 percent on a thousand questions the 95 percent interval is about plus or minus 2.8 points. Report the central-limit-theorem standard error with every score. When questions come in correlated groups, like many questions about one passage, use clustered standard errors, which on real evals can be over three times larger. When comparing two models on the same questions, test the per-question differences: shared difficulty cancels, so a paired test detects gaps that overlapping intervals hide. And use power analysis: detecting half the gap needs four times the questions.',
    recap=[('Problem', 'leaderboard gaps are often smaller than the sampling error.'), ('Tools', 'CLT SE, clustered SE, paired differences, power analysis.'), ('Numbers', '±2.8 pts at n = 1,000; clustered SE up to 3× naive; n ∝ 1/δ².')],
)

# =============================================================== 05
DECKS['05-contamination'] = dict(
    title='Contamination', h1='Benchmark contamination',
    sub='When test questions leak into training data the score partly measures memorization. How to detect overlap, how to report it, and how fresh test sets reveal overfitting.',
    prob='Pretraining corpora are scraped from the web, and benchmarks are published on the web. Test items (or close variants) can end up in training data, inflating scores in ways that don\'t reflect real capability.',
    core='<b>Detect</b> overlap (GPT-3 flagged any 13-gram match with the training set), <b>report</b> clean-subset scores next to full ones, and <b>validate</b> on fresh or held-out test sets that can\'t have leaked.',
    build=['03_contamination'],
    sources='Brown et al. 2020, "Language Models are Few-Shot Learners" (GPT-3 §4 and App. C: 13-gram overlap, filtering bug, clean vs dirty analysis); Zhang et al. 2024, "A Careful Examination of Large Language Model Performance on Grade School Arithmetic" (GSM1k: drops of up to 8%).',
    slides=[
        section('s-p1', 1, 'How leakage inflates a score <span class="ill">simulation</span>', '''    <p class="lede">A model with true skill 55% that answers leaked items correctly 95% of the time (memorized). Move the fraction of the test set that leaked into training.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0"><label class="ctl">leaked fraction <input type="range" id="lF" min="0" max="0.5" step="0.05" value="0.1"> <output id="lFo"></output></label></div>
      <div id="lBars" style="margin-top:12px"></div>
      <p class="readout" id="lOut"></p>
    </div>'''),
        section('s-lim', 2, 'Why it is hard to avoid', '''    <div class="grid3">
      <div class="card d"><h3>Web-scale data</h3><p>Benchmarks, their solutions and discussions of them are posted online and get scraped along with everything else.</p></div>
      <div class="card b"><h3>Filtering is imperfect</h3><p>GPT-3 tried to remove overlaps with its benchmarks, but "a bug in the filtering caused us to ignore some overlaps, and due to the cost of training it was not feasible to retrain the model."</p></div>
      <div class="card c"><h3>Paraphrases escape detection</h3><p>Exact n-gram matching misses translated, reworded or reformatted copies of test items.</p></div>
    </div>'''),
        your_turn('s-turn', 'Reading a contamination report',
                  'A model scores 80% on a benchmark, 81% on the flagged ("dirty") items and 80% on the clean items. What does that suggest?',
                  ['Heavy contamination inflated the score', 'Contamination is not driving the score on this benchmark', 'The benchmark is broken', 'The detector failed'], 1,
                  '<b>B.</b> If clean-subset performance matches the full score, the overlapping items aren\'t giving the model an advantage. That is GPT-3\'s method: compare scores on the clean subset with the full benchmark. GPT-3 found contamination "has a minimal effect" on most datasets, while flagging some where it did matter.'),
        section('s-core', 4, 'Detect, report, validate', '''    <div class="grid3">
      <div class="card a"><h3>Detect</h3><p>GPT-3 flagged test examples "that have a 13-gram overlap with anything in the pretraining set (or that overlap with the whole example when it is shorter than 13-grams)". Deliberately conservative.</p></div>
      <div class="card b"><h3>Report</h3><p>Score the full set, the clean subset and the dirty subset. A big gap between clean and full means the score is partly memorization.</p></div>
      <div class="card e"><h3>Validate</h3><p>Build new test sets the model can't have seen: GSM1k mirrors GSM8K\'s style with fresh problems. Models that overfit GSM8K drop on it.</p></div>
    </div>
''' + deep('What GSM1k found', '<p>On fresh, GSM8K-style problems, the authors "observe accuracy drops of up to 8%, with several families of models showing evidence of systematic overfitting across almost all model sizes", while frontier models (they name Gemini, GPT and Claude) "show little to no signs of overfitting". Contamination is not uniform: it depends on how each model\'s data was collected.</p>')),
        section('s-how', 5, 'n-gram overlap, by hand', '''    <p class="lede">A toy test item and a training document. Choose n and see which n-grams of the test item also appear in training. Short n flags coincidences; long n misses partial copies.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0"><label class="ctl">n <input type="range" id="nN" min="2" max="8" step="1" value="5"> <output id="nNo"></output></label></div>
      <div id="nTest" style="display:flex;flex-wrap:wrap;gap:4px;margin-top:12px;font:500 13px 'JetBrains Mono',monospace"></div>
      <p class="caption" style="margin-top:8px">training document: <span id="nTrain" style="font-family:'JetBrains Mono',monospace"></span></p>
      <p class="readout" id="nOut"></p>
    </div>'''),
        section('s-how2', 5, 'Other defences', '''    <div class="visual scroll-x"><table class="tbl">
      <tr><th>Defence</th><th>How it helps</th><th>Limits</th></tr>
      <tr><td>n-gram overlap filtering</td><td>Removes exact copies before training; flags items after</td><td>Misses paraphrases and translations</td></tr>
      <tr><td>Clean-subset reporting</td><td>Shows whether flagged items move the score</td><td>Only as good as the detector</td></tr>
      <tr><td>Fresh / held-out test sets</td><td>Can't have leaked (GSM1k)</td><td>Expensive to build; must match difficulty</td></tr>
      <tr><td>Private or rotating test sets</td><td>Never published, or replaced regularly</td><td>Less reproducible for outsiders</td></tr>
      <tr><td>Canary strings</td><td>A unique marker in benchmark files lets data pipelines filter them and lets models be probed for having seen them</td><td>Depends on pipelines honouring it</td></tr>
    </table></div>'''),
        section('s-why', 6, 'Why it matters', '''    <div class="grid2">
      <div class="card a"><h3>Scores stop meaning capability</h3><p>A memorized answer says nothing about solving a new problem of the same kind, which is what the benchmark is supposed to predict.</p></div>
      <div class="card e"><h3>Comparisons become unfair</h3><p>Models trained on different data are contaminated to different degrees, so rankings mix skill with exposure.</p></div>
      <div class="card b"><h3>It compounds over time</h3><p>The longer a benchmark is public, the more copies, solutions and discussions exist on the web.</p></div>
      <div class="card c"><h3>Fresh tests restore trust</h3><p>A gap between an old benchmark and a fresh equivalent (GSM8K vs GSM1k) is direct evidence of overfitting.</p></div>
    </div>'''),
        myths('s-myth', [
            ('If the benchmark was filtered from the training data, it is clean.', 'Filters miss paraphrases and can have bugs, as GPT-3\'s did. Report clean-subset results and use fresh sets.'),
            ('Contamination always inflates scores a lot.', 'GPT-3 found minimal effect on most benchmarks, and GSM1k found frontier models barely affected. It varies by model and dataset, so measure it.'),
            ('A shorter n-gram makes detection strictly better.', 'Short n-grams match by coincidence in real text, producing false positives. GPT-3 chose 13 to stay conservative.'),
        ]),
        check('s-check', [
            ('mcq', 'What n-gram length did GPT-3 use to flag potential contamination?', ['3', '8', '13', '50'], 2, '<b>13-grams</b> (or the whole example if shorter).'),
            ('open', 'How do clean and dirty subset scores tell you whether contamination matters?', 'If the clean-subset score matches the full score, overlap isn\'t driving results. If dirty items score much higher than clean ones, part of the score is memorization.'),
            ('open', 'What did GSM1k do, and what did it find?', 'Built fresh GSM8K-style problems. Accuracy dropped by up to 8% for some model families (systematic overfitting), while frontier models showed little to no drop.'),
        ]),
    ],
    js=r'''
  Deck.bind(['lF'], () => {
    const f = Deck.val('lF'), clean = 0.55, full = f * 0.95 + (1 - f) * clean; Deck.out('lFo', (100 * f).toFixed(0) + '%');
    Deck.hbars(document.getElementById('lBars'), [{ label: 'reported (full set)', value: full, color: 'var(--d)', text: (100 * full).toFixed(1) + '%' }, { label: 'clean subset', value: clean, color: 'var(--a)', text: '55.0%' }, { label: 'dirty subset', value: f ? 0.95 : 0, color: 'var(--b)', text: f ? '95.0%' : '—' }], { max: 1 });
    document.getElementById('lOut').innerHTML = `With ${(100 * f).toFixed(0)}% leaked, the reported score is inflated by <b>${(100 * (full - clean)).toFixed(1)} points</b> over the model's real skill.`;
  });
  const TEST = 'a train leaves the station at noon travelling at sixty miles per hour toward the coast'.split(' ');
  const TRAIN = 'yesterday a train leaves the station at noon travelling quickly and nobody knows why the coast is quiet'.split(' ');
  Deck.bind(['nN'], () => {
    const n = Deck.val('nN'); Deck.out('nNo', n);
    const grams = new Set(); for (let i = 0; i + n <= TRAIN.length; i++) grams.add(TRAIN.slice(i, i + n).join(' '));
    const hit = new Array(TEST.length).fill(false); let any = 0;
    for (let i = 0; i + n <= TEST.length; i++) if (grams.has(TEST.slice(i, i + n).join(' '))) { any++; for (let j = i; j < i + n; j++) hit[j] = true; }
    const box = document.getElementById('nTest'); box.innerHTML = '';
    TEST.forEach((w, i) => { const s = document.createElement('span'); s.textContent = w; s.style.cssText = `padding:3px 7px;border-radius:5px;background:${hit[i] ? 'var(--d)' : 'var(--panel-2)'};color:${hit[i] ? '#fff' : 'var(--ink)'}`; box.appendChild(s); });
    document.getElementById('nTrain').textContent = TRAIN.join(' ');
    document.getElementById('nOut').innerHTML = any ? `<b>${any}</b> of the test item's ${n}-grams appear in training: <b>flagged</b>.` : `No shared ${n}-gram: <b>not flagged</b>, even though half the item was copied. Longer n misses partial copies.`;
  });
''',
    line='Contaminated test items turn benchmarks into memory tests: detect overlap (13-grams), report clean-subset scores, and confirm on fresh test sets.',
    explain='Benchmarks live on the web, and so does training data, so test items leak. A model that memorized leaked items looks better than it is, and the effect differs between models. GPT-3 flagged any test example sharing a 13-gram with its training data and compared scores on the clean and dirty subsets; it found little effect on most benchmarks, after a filtering bug had left some overlap in. n-gram matching misses paraphrases, so the strongest evidence comes from fresh test sets: on GSM1k, new GSM8K-style problems, some model families dropped by up to 8 percent while frontier models barely changed.',
    recap=[('Problem', 'web-scale training data includes public test sets.'), ('Detect & report', '13-gram overlap; full vs clean vs dirty scores.'), ('Validate', 'fresh or private test sets; GSM1k drops of up to 8%.')],
)

# =============================================================== 06
DECKS['06-llm-as-judge'] = dict(
    title='LLM-as-Judge', h1='LLM-as-judge',
    sub='Using a strong model to grade open-ended answers: how well it agrees with people, the biases it brings (position, verbosity, self-preference), and how to control them.',
    prob='Open-ended answers (explanations, essays, chat) have no single correct string, and human grading is slow and expensive. Evaluating every checkpoint on thousands of such answers needs an automatic grader.',
    core='Ask a strong LLM to compare or score answers, then <b>measure and correct its biases</b>: swap answer positions, control for length, avoid letting a model judge itself, and check agreement with human labels.',
    build=['04_judges_and_arenas'],
    sources='Zheng et al. 2023, "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena" (>80% agreement; Table 2 position consistency; Table 3 "repetitive list" attack); Dubois et al. 2024, "Length-Controlled AlpacaEval" (Spearman 0.94 → 0.98 with Chatbot Arena).',
    slides=[
        section('s-p1', 1, 'Agreement with people', '''    <div class="grid3">
      <div class="card a"><h3>As good as another human</h3><p>MT-Bench: strong LLM judges like GPT-4 "match both controlled and crowdsourced human preferences well, achieving over 80% agreement, the same level of agreement between humans".</p></div>
      <div class="card b"><h3>Fast and cheap</h3><p>A judge model can grade thousands of answers per checkpoint, so open-ended quality can be tracked during development.</p></div>
      <div class="card e"><h3>Explainable</h3><p>Judges can be asked to reason before deciding, which makes their verdicts easier to audit.</p></div>
    </div>'''),
        section('s-lim', 2, 'Three documented biases', '''    <div class="grid3">
      <div class="card d"><h3>Position bias</h3><p>Favouring whichever answer is shown first (or second). With the answers swapped, Claude-v1 gave a consistent verdict only 23.8% of the time with the default prompt, GPT-3.5 46.2%, GPT-4 65.0%.</p></div>
      <div class="card b"><h3>Verbosity bias</h3><p>Favouring longer answers. MT-Bench's "repetitive list" attack (padding a list with rephrased duplicates) fooled Claude-v1 and GPT-3.5 91.3% of the time, GPT-4 8.7%.</p></div>
      <div class="card c"><h3>Self-enhancement bias</h3><p>Favouring answers written by the judge itself, or by similar models. A model shouldn't be the only judge of its own outputs.</p></div>
    </div>'''),
        your_turn('s-turn', 'Catch the bias',
                  'You ask a judge "Is A or B better?" and it says A. You swap them, asking "Is B or A better?", and it says the first one again (now B). What happened?',
                  ['The judge is consistent', 'Position bias: the verdict followed the slot, not the content', 'Verbosity bias', 'The answers are identical'], 1,
                  '<b>B.</b> A consistent judge picks the same underlying answer in both orders. Here it picked "whichever came first", so the verdict tells you nothing about A vs B. Count this as a tie, or ask more times.'),
        section('s-core', 4, 'Using a judge responsibly', '''    <div class="grid2">
      <div class="card a"><h3>Swap and aggregate</h3><p>Ask both orders; only count a win if the judge picks the same answer twice, otherwise call it a tie (the MT-Bench approach for pairwise comparisons).</p></div>
      <div class="card b"><h3>Control for length</h3><p>Length-controlled AlpacaEval predicts preferences while conditioning on the length difference, which raised its Spearman correlation with Chatbot Arena from 0.94 to 0.98.</p></div>
      <div class="card e"><h3>Use references for hard questions</h3><p>For maths and reasoning, judges can be fooled by wrong answers; giving the judge a reference solution helps.</p></div>
      <div class="card c"><h3>Calibrate against humans</h3><p>Check agreement on a human-labelled sample before trusting a judge on a new task, and re-check when the judge or the task changes.</p></div>
    </div>'''),
        section('s-how', 5, 'Position-swap test <span class="ill">simulation</span>', '''    <p class="lede">A simulated judge that adds a bias (in log-odds) to whichever answer is shown first. Ask about 500 answer pairs twice, swapping positions. Watch consistency fall as bias grows. Notebook 04 builds this test.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0"><label class="ctl">first-position bias <input type="range" id="jB" min="0" max="3" step="0.1" value="1"> <output id="jBo"></output></label><label class="ctl">judge noise <input type="range" id="jN" min="0.2" max="2" step="0.1" value="1"> <output id="jNo"></output></label></div>
      <div id="jBars" style="margin-top:12px"></div>
    </div>
    <p class="caption">For reference, MT-Bench (default prompt): consistency GPT-4 65.0%, GPT-3.5 46.2%, Claude-v1 23.8%.</p>'''),
        section('s-how2', 5, 'Verbosity bias and length control', '''    <div class="visual"><div id="vBars"></div><p class="caption">MT-Bench Table 3: failure rate of judges under the "repetitive list" attack on 23 answers (padding without new information).</p></div>
''' + deep('How length control works', '<p>Length-controlled AlpacaEval fits a model of the judge\'s preferences that includes the length difference between the two answers, then reports the win rate predicted with that length term set to zero: "what would the judge prefer if the answers were the same length?" This made the ranking agree better with human votes in Chatbot Arena (Spearman 0.94 → 0.98).</p>')),
        section('s-why', 6, 'Why judges work, and where they fail', '''    <div class="grid2">
      <div class="card a"><h3>Judging is easier than writing</h3><p>Comparing two answers is often easier than producing the best one, so a strong model can grade answers from comparable models reasonably well.</p></div>
      <div class="card e"><h3>Scales with automation</h3><p>Cheap enough to grade every checkpoint and every ablation.</p></div>
      <div class="card d"><h3>Biases are systematic</h3><p>Unlike random noise, position, length and self-preference push in consistent directions, so they can change rankings, and models can be tuned to exploit them.</p></div>
      <div class="card b"><h3>Weak on hard reasoning</h3><p>MT-Bench notes "limited reasoning ability": judges can approve wrong maths answers, especially without a reference solution.</p></div>
    </div>'''),
        myths('s-myth', [
            ('80% agreement means the judge is right 80% of the time.', 'It means it agrees with humans as often as humans agree with each other. Both can be wrong, and agreement varies by task.'),
            ('Asking once is enough if the judge is strong.', 'Even GPT-4 was position-consistent only 65% of the time in MT-Bench. Swap positions and aggregate.'),
            ('Longer answers winning means they\'re more helpful.', 'Judges have verbosity bias; length-controlled metrics agree better with human preference.'),
        ]),
        check('s-check', [
            ('mcq', 'Which judge resisted MT-Bench\'s "repetitive list" verbosity attack best?', ['Claude-v1', 'GPT-3.5', 'GPT-4', 'All failed equally'], 2, '<b>GPT-4</b>: 8.7% failure vs 91.3% for Claude-v1 and GPT-3.5.'),
            ('open', 'Describe a protocol that removes position bias from pairwise judging.', 'Ask with both orders. Count a win only when the judge picks the same underlying answer both times; otherwise record a tie (or ask more times).'),
            ('open', 'What does length-controlled AlpacaEval change, and what was the effect?', 'It conditions the judge\'s preference on the length difference and reports the length-neutral win rate. Correlation with Chatbot Arena rose from 0.94 to 0.98 (Spearman).'),
        ]),
    ],
    js=r'''
  const sig = z => 1 / (1 + Math.exp(-z));
  Deck.bind(['jB', 'jN'], () => {
    const b = Deck.val('jB'), nz = Deck.val('jN'); Deck.out('jBo', b.toFixed(1)); Deck.out('jNo', nz.toFixed(1));
    let seed = 99; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647; const g = () => Math.sqrt(-2 * Math.log(Math.max(1e-9, rnd()))) * Math.cos(2 * Math.PI * rnd());
    let cons = 0, first = 0, second = 0; const N = 500;
    for (let i = 0; i < N; i++) {
      const d = g();                                       // true quality difference (a minus b)
      const x = rnd() < sig((d + b) / nz) ? 'A' : 'B';      // order (a, b)
      const y = rnd() < sig((-d + b) / nz) ? 'A' : 'B';     // order (b, a)
      if ((x === 'A') === (y === 'B')) cons++; else if (x === 'A') first++; else second++;
    }
    Deck.hbars(document.getElementById('jBars'), [{ label: 'consistent', value: cons / N, color: 'var(--a)', text: (100 * cons / N).toFixed(0) + '%' }, { label: 'picked first both times', value: first / N, color: 'var(--d)', text: (100 * first / N).toFixed(0) + '%' }, { label: 'picked second both times', value: second / N, color: 'var(--b)', text: (100 * second / N).toFixed(0) + '%' }], { max: 1 });
  });
  Deck.hbars(document.getElementById('vBars'), [['Claude-v1', 0.913], ['GPT-3.5', 0.913], ['GPT-4', 0.087]].map(([l, v]) => ({ label: l, value: v, color: v > 0.5 ? 'var(--d)' : 'var(--a)', text: (100 * v).toFixed(1) + '% fooled' })), { max: 1 });
''',
    line='LLM judges agree with people about as often as people agree with each other, but they are biased by position, length and self-preference, so swap, length-control and calibrate.',
    explain='Open-ended answers need a grader, and a strong model can do it: MT-Bench found GPT-4\'s verdicts agree with human preferences over 80 percent of the time, about the same as humans agree with each other. But judges have systematic biases. Swapping the two answers changed GPT-4\'s verdict a third of the time and Claude-v1\'s most of the time. Padding answers with repeated content fooled weaker judges over 90 percent of the time. And models may favour their own outputs. So ask in both orders and count disagreements as ties, control for length, as length-controlled AlpacaEval did to raise its correlation with Chatbot Arena from 0.94 to 0.98, give references for hard questions, and check agreement with humans.',
    recap=[('Problem', 'open-ended answers need scalable grading.'), ('Core idea', 'LLM judges ≈ human agreement (>80%), but biased.'), ('Controls', 'position swap, length control, references, human calibration, no self-judging.')],
)

# =============================================================== 07
DECKS['07-arenas'] = dict(
    title='Arenas and Ratings', h1='Arenas and ratings',
    sub='Ranking models from crowdsourced head-to-head votes: the Bradley-Terry model behind Chatbot Arena, how it compares with online Elo, and why leaderboards need confidence intervals.',
    prob='Static benchmarks miss what real users ask and value. Pairwise human votes on live prompts capture it, but they are noisy, unevenly distributed across models, and need a principled way to become a ranking.',
    core='Collect anonymous <b>pairwise votes</b> on user prompts, fit <b>Bradley-Terry</b> strengths by maximum likelihood (P(i beats j) = σ(ξᵢ − ξⱼ)), and publish ratings <b>with confidence intervals</b>.',
    build=['04_judges_and_arenas'],
    sources='Chiang et al. 2024, "Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference" (240K+ votes; Bradley-Terry maximum likelihood with sandwich and bootstrap intervals); Zheng et al. 2023 (MT-Bench and Arena agreement); Elo 1978.',
    slides=[
        section('s-p1', 1, 'How an arena works', '''    <div class="grid3">
      <div class="card a"><h3>Real prompts</h3><p>Users bring their own questions, so the distribution reflects actual use, and new prompts keep arriving, so there's no fixed test set to overfit.</p></div>
      <div class="card b"><h3>Anonymous pairs</h3><p>Two models answer the same prompt; the user votes for the better one (or a tie) before model names are revealed.</p></div>
      <div class="card e"><h3>Ratings from votes</h3><p>Chatbot Arena collected "over 240K votes" in the period covered by its paper and turns them into ratings with a statistical model.</p></div>
    </div>'''),
        section('s-lim', 2, 'Turning votes into a ranking is not trivial', '''    <div class="grid3">
      <div class="card d"><h3>Not everyone plays everyone</h3><p>Some pairs get thousands of votes, others few. Win rates against different opponents aren't directly comparable.</p></div>
      <div class="card b"><h3>Votes are noisy</h3><p>Users disagree and prompts vary in difficulty, so any rating has uncertainty that must be reported.</p></div>
      <div class="card c"><h3>Online Elo depends on order</h3><p>Chess-style Elo updates after each game, so the same votes processed in a different order give different ratings, and K controls how much recent votes dominate.</p></div>
    </div>'''),
        your_turn('s-turn', 'Read a Bradley-Terry rating',
                  'On the Elo-style scale (400/ln 10 ≈ 174 points per log-odds unit), model A is rated 100 points above model B. Roughly how often should A win a head-to-head vote?',
                  ['50%', 'about 64%', 'about 90%', '100%'], 1,
                  '<b>B.</b> P(A wins) = 1/(1 + 10^(−100/400)) ≈ 0.64. On this scale, 100 points is a modest edge, and 400 points means about 10:1 odds.'),
        section('s-core', 4, 'Bradley-Terry vs online Elo', '''    <div class="grid2">
      <div class="card a"><h3>Bradley-Terry (maximum likelihood)</h3><p>Fit all strengths ξ jointly to all votes: maximize Σ log σ(ξ<sub>winner</sub> − ξ<sub>loser</sub>). The result doesn't depend on vote order, uses every comparison, and comes with standard errors. Chatbot Arena estimates BT coefficients and reports intervals via a sandwich estimator and bootstrap.</p></div>
      <div class="card b"><h3>Online Elo</h3><p>After each vote, move the winner up and the loser down by K·(1 − expected score). Cheap and incremental, but sensitive to K and to the order of votes, and with no built-in uncertainty.</p></div>
    </div>
    <div class="eq">P(i beats j) = σ(ξᵢ − ξⱼ) = 1 / (1 + 10<sup>−(Rᵢ − Rⱼ)/400</sup>)  with  R = 400·ξ / ln 10</div>'''),
        section('s-how', 5, 'Same votes, different Elo <span class="ill">simulation</span>', '''    <p class="lede">6 models with known true strengths and 3,000 simulated votes. Shuffle the order of the same votes and re-run online Elo; Bradley-Terry (fitted in your browser) doesn't move.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0"><button class="btn primary" id="aShuf">shuffle vote order</button><label class="ctl">Elo K <input type="range" id="aK" min="4" max="64" step="4" value="16"> <output id="aKo"></output></label></div>
      <svg id="aSvg" viewBox="0 0 660 250" style="margin-top:10px" role="img" aria-label="Elo vs Bradley-Terry"></svg>
      <div class="legend"><span><i style="background:var(--faint)"></i>true</span><span><i style="background:var(--a)"></i>Bradley-Terry</span><span><i style="background:var(--d)"></i>online Elo (this order)</span></div>
    </div>'''),
        section('s-how2', 5, 'Read the intervals, not just the ranks', '''    <div class="grid2">
      <div class="card a"><h3>Overlap means "statistically tied"</h3><p>If two models' intervals overlap heavily, their order may flip with more votes. Rank bands are more honest than strict ranks.</p></div>
      <div class="card e"><h3>Intervals shrink with votes</h3><p>Popular models get many votes and tight intervals; new models start uncertain. Arena's paper also studies sampling pairs to converge faster.</p></div>
      <div class="card b"><h3>Style and length matter</h3><p>Human voters, like LLM judges, may prefer longer or better-formatted answers, so arenas measure user preference, not correctness alone.</p></div>
      <div class="card c"><h3>Combine with benchmarks</h3><p>Arenas capture preference on real prompts; benchmarks test specific skills with known answers. Use both.</p></div>
    </div>'''),
        section('s-why', 6, 'Why arenas became a standard reference', '''    <div class="grid2">
      <div class="card a"><h3>Hard to overfit</h3><p>Prompts are fresh and diverse; there's no published test set to train on.</p></div>
      <div class="card e"><h3>Matches what users feel</h3><p>Ratings reflect preferences on real tasks, and the Arena paper reports crowdsourced votes agree well with expert raters.</p></div>
      <div class="card b"><h3>Principled statistics</h3><p>Bradley-Terry plus confidence intervals turns noisy, unbalanced votes into a ranking with honest uncertainty.</p></div>
      <div class="card d"><h3>Limits</h3><p>The user population and its prompts shape the result, preferences include style, and ratings can be gamed by optimizing for what voters like.</p></div>
    </div>'''),
        myths('s-myth', [
            ('An arena rating is a chess Elo computed game by game.', 'Chatbot Arena fits Bradley-Terry coefficients by maximum likelihood over all votes, which is order-independent, and reports intervals. It is displayed on an Elo-like scale.'),
            ('A higher rank always means a better model.', 'Neighbouring models often have overlapping intervals. Read rank bands, not strict positions.'),
            ('Arena ratings measure correctness.', 'They measure which answer users prefer, which mixes correctness, helpfulness, style and length.'),
        ]),
        check('s-check', [
            ('mcq', 'Which property does Bradley-Terry maximum likelihood have that online Elo lacks?', ['It is faster to update', 'Its result does not depend on the order of votes', 'It needs no data', 'It ignores ties'], 1, '<b>Order independence</b>: it fits all votes jointly.'),
            ('open', 'Convert a Bradley-Terry strength difference of 1.0 (log-odds) to the Elo scale and a win probability.', '400/ln 10 ≈ 174 points; P(win) = σ(1.0) ≈ 0.73.'),
            ('open', 'Why must arena leaderboards publish confidence intervals?', 'Votes are noisy and unevenly distributed across models, so ratings have uncertainty; close models may be statistically indistinguishable.'),
        ]),
    ],
    js=r'''
  const TRUE = [1.2, 0.8, 0.5, 0.0, -0.3, -1.0], M = 6, SC = 400 / Math.log(10), sig = z => 1 / (1 + Math.exp(-z));
  let seed = 42; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const VOTES = []; for (let t = 0; t < 3000; t++) { const i = Math.floor(rnd() * M), j = (i + 1 + Math.floor(rnd() * (M - 1))) % M; VOTES.push(rnd() < sig(TRUE[i] - TRUE[j]) ? [i, j] : [j, i]); }
  const bt = (() => { const xi = new Array(M).fill(0); for (let s = 0; s < 1500; s++) { const g = new Array(M).fill(0); VOTES.forEach(([w, l]) => { const d = 1 - sig(xi[w] - xi[l]); g[w] += d; g[l] -= d; }); for (let m = 0; m < M; m++) xi[m] += 2 * g[m] / VOTES.length; } const mu = xi.reduce((a, b) => a + b) / M; return xi.map(x => (x - mu) * SC + 1000); })();
  const tmu = TRUE.reduce((a, b) => a + b) / M, truth = TRUE.map(x => (x - tmu) * SC + 1000);
  let order = VOTES.map((_, i) => i);
  const draw = () => {
    const K = Deck.val('aK'); Deck.out('aKo', K);
    const R = new Array(M).fill(1000); order.forEach(ix => { const [w, l] = VOTES[ix]; const e = 1 / (1 + Math.pow(10, (R[l] - R[w]) / 400)); R[w] += K * (1 - e); R[l] -= K * (1 - e); });
    const s = clear(document.getElementById('aSvg')), Y = v => 225 - (v - 700) / 650 * 210;
    [800, 1000, 1200].forEach(v => { svg('line', { x1: 50, x2: 640, y1: Y(v), y2: Y(v), class: 'ln' }, s); svg('text', { x: 44, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm', text: v }, s); });
    for (let m = 0; m < M; m++) {
      const x = 90 + m * 95;
      svg('text', { x, y: 246, 'text-anchor': 'middle', class: 'tm', text: 'model ' + m }, s);
      [[truth[m], 'var(--faint)', -18], [bt[m], 'var(--a)', 0], [R[m], 'var(--d)', 18]].forEach(([v, c, dx]) => svg('rect', { x: x + dx - 7, y: Y(v), width: 14, height: Y(700) - Y(v), rx: 3, style: `fill:${c}` }, s));
    }
  };
  Deck.bind(['aK'], draw);
  document.getElementById('aShuf').addEventListener('click', () => { for (let i = order.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [order[i], order[j]] = [order[j], order[i]]; } draw(); });
''',
    line='Arenas turn anonymous head-to-head votes on real prompts into ratings with Bradley-Terry maximum likelihood, which is order-independent, and should always be read with their confidence intervals.',
    explain='Chatbot Arena shows users two anonymous models answering their own prompt and asks which is better, collecting hundreds of thousands of votes on real, ever-changing prompts that can\'t be overfit. To rank models from unbalanced, noisy votes it fits the Bradley-Terry model, where the probability that one model beats another is the sigmoid of their strength difference, by maximum likelihood over all votes, and reports confidence intervals. Online Elo, which updates after each vote, depends on vote order and the step size. The ratings are shown on an Elo-like scale where 100 points is about a 64 percent win rate. Arenas measure user preference, including style, so read rank bands and use them alongside benchmarks.',
    recap=[('Problem', 'benchmarks miss real use; votes are noisy and unbalanced.'), ('Core idea', 'Bradley-Terry MLE over all votes, with confidence intervals.'), ('Watch', 'Elo order dependence; overlapping intervals; preference ≠ correctness.')],
)
