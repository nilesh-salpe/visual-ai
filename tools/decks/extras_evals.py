"""Per-deck extras for the Evals guide. Numbers are computed here."""
from math import ceil, comb, log, sqrt
from papers import PAPERS as P

EXTRAS = {}

EXTRAS['01-what-an-eval-measures'] = dict(
    glance=dict(steps=[('capability', 'what should the score mean?', 'c'), ('questions', 'which set, how many', 'f'), ('prompt', 'template, shots', 'b'),
                       ('decoding', 'greedy or sampled, k', 'a'), ('scoring', 'match, log-prob, tests, judge', 'e'), ('score ± SE', 'with uncertainty', 'd')],
                caption='Report every stage with the number; change any one and the score changes.'),
    example=dict(title='Worked example: is a 2-point lead real?',
                 setup='Model A scores 72% and model B 70% on a 1,000-question benchmark, each in one prompt format.',
                 steps=[f'95% CI half-width at ~71%: 1.96 × √(0.71 × 0.29 / 1,000) = <b>±{1.96 * sqrt(0.71 * 0.29 / 1000) * 100:.1f} points</b>.',
                        'The 2-point gap is inside either model\'s interval; a paired test on the same questions is needed (deck 04).',
                        'Prompt format alone can move scores by tens of points (up to 76 for LLaMA-2-13B in Sclar et al.).',
                        'Evaluate both models over several equivalent formats and report the mean and spread.'],
                 result='Before calling a winner: same protocol, standard errors, a paired comparison, and the format spread.'),
    traps=dict(tricks=[('CI ≈ ±1.96·√(p(1−p)/n).', '±2.8 points at 70% on 1,000 questions.'),
                       ('Report the protocol.', 'Version, shots, template, decoding, scoring, n.'),
                       ('Measure more than accuracy.', 'HELM tracks calibration, robustness, fairness, bias, toxicity and efficiency too.')],
               traps=[('Comparing numbers across papers.', 'Different harnesses and prompts make them incomparable.'),
                      ('One prompt per model.', 'Formatting can decide the comparison.'),
                      ('Point estimates only.', 'Gaps smaller than the error bars are noise.')]),
    papers=[P['helm'], P['sclar']],
)

EXTRAS['02-benchmarks'] = dict(
    glance=dict(steps=[('format', 'recognize / produce / act', 'c'), ('scoring', 'log-prob, match, tests', 'b'), ('floor and ceiling', 'chance, experts, label noise', 'a'),
                       ('saturation', 'scores bunch near the top', 'd'), ('replace', 'harder or fresher set', 'e')],
                caption='Each benchmark lives until its scores stop separating models.'),
    example=dict(title='Worked example: how guessing inflates multiple choice',
                 setup='A model truly knows 50% of the answers and guesses uniformly on the rest.',
                 steps=[f'4 options: 0.5 + 0.5 × 1/4 = <b>{0.5 + 0.5 / 4:.1%}</b>.',
                        f'4 options, one distractor eliminated: 0.5 + 0.5 × 1/3 = <b>{0.5 + 0.5 / 3:.1%}</b>.',
                        f'10 options (MMLU-Pro): 0.5 + 0.5 × 1/10 = <b>{0.5 + 0.5 / 10:.1%}</b>.',
                        f'Chance-corrected knowledge from a 4-option score s: (s − 0.25) / 0.75; e.g. s = 62.5% → {(0.625 - 0.25) / 0.75:.0%}.'],
                 result='More options lower the floor, so scores reflect knowledge more; part of why MMLU-Pro scores are 16–33% lower.'),
    traps=dict(tricks=[('Subtract chance.', '(score − 1/k) / (1 − 1/k) for k options.'),
                       ('Know the expert ceiling.', 'GPQA: experts 65%, so 100% isn\'t the target.'),
                       ('Match the format to the use.', 'Recognize (MCQ), produce (short answer, code), act (agents).')],
               traps=[('MCQ = can produce the answer.', 'It measures recognition among options.'),
                      ('Small gaps on saturated sets.', 'Often inside the error bars or label noise.'),
                      ('Ignoring the scoring rule.', 'Log-prob vs parsed generation can disagree for the same model.')]),
    papers=[P['mmlu'], P['mmlupro'], P['gpqa'], P['swebench']],
)

_n, _c, _k = 20, 2, 10
_u = 1 - comb(_n - _c, _k) / comb(_n, _k)
EXTRAS['03-pass-at-k'] = dict(
    glance=dict(steps=[('sample n', 'per problem, n ≥ k', 'f'), ('run tests', 'count c passing', 'b'), ('1 − C(n−c,k)/C(n,k)', 'per problem', 'a'),
                       ('average', 'over problems', 'e')],
                caption='Unbiased, and it uses all n samples.'),
    example=dict(title='Worked example: pass@10 from 20 samples',
                 setup=f'n = {_n} samples for one problem, c = {_c} pass the unit tests, k = {_k}.',
                 steps=[f'C(18, 10) = {comb(18, 10):,}; C(20, 10) = {comb(20, 10):,}.',
                        f'pass@10 = 1 − {comb(18, 10):,} / {comb(20, 10):,} = <b>{_u:.3f}</b>.',
                        f'Plug-in estimate: 1 − (1 − 2/20)<sup>10</sup> = <b>{1 - 0.9 ** 10:.3f}</b>, lower.',
                        f'pass@1 = c/n = <b>{_c / _n:.2f}</b>.'],
                 result='Use the unbiased estimator per problem, then average over problems.'),
    traps=dict(tricks=[('pass@1 = c/n.', 'With many samples it is low-variance.'),
                       ('Product form.', '1 − ∏ (1 − k/i) for i from n − c + 1 to n avoids overflow.'),
                       ('n − c < k ⇒ 1.', 'Every k-subset contains a pass.')],
               traps=[('Plug-in 1 − (1 − c/n)^k.', 'Biased low (concave).'),
                      ('Reporting pass@100 as user quality.', 'Users usually get one attempt.'),
                      ('Weak tests.', 'Wrong programs that pass weak tests count as solved.')]),
    papers=[P['codex'], P['swebench']],
)

_q = ceil(((1.959964 + 0.841621) * 0.3 / 0.02) ** 2)
EXTRAS['04-error-bars'] = dict(
    glance=dict(steps=[('per-question scores', '0/1 or graded', 'f'), ('mean ± SE', 'CLT', 'a'), ('clusters?', 'clustered SE if grouped', 'b'),
                       ('compare models', 'paired differences', 'c'), ('enough questions?', 'power analysis', 'e')],
                caption='Treat every eval as a sample of questions.'),
    example=dict(title='Worked example: sizing an eval',
                 setup='You want to detect a 2-point improvement. Per-question differences between the two models have standard deviation 0.3.',
                 steps=['Two-sided 5% test with 80% power: z = 1.96 + 0.84 = 2.80.',
                        f'n = (2.80 × 0.3 / 0.02)² = <b>{_q:,}</b> questions.',
                        f'For a 1-point gap: <b>{ceil(((1.959964 + 0.841621) * 0.3 / 0.01) ** 2):,}</b> (≈ 4×).',
                        'If questions come in clusters of 10 correlated items, the effective n is closer to the number of clusters: plan for more.'],
                 result='Small gaps need big evals; paired comparisons need far fewer questions than comparing two separate intervals.'),
    traps=dict(tricks=[('n ∝ 1/δ².', 'Halving the gap needs four times the questions.'),
                       ('Pair whenever possible.', 'Same questions for both models → test the differences.'),
                       ('Report clusters.', 'Give the cluster count with clustered SEs.')],
               traps=[('Overlapping CIs ⇒ no difference.', 'Not for paired data.'),
                      ('Treating grouped questions as independent.', 'Clustered SEs can be over 3× naive ones.'),
                      ('Chasing noise.', 'Picking checkpoints by sub-SE differences selects luck.')]),
    papers=[P['errorbars'], P['arena']],
)

EXTRAS['05-contamination'] = dict(
    glance=dict(steps=[('training corpus', 'web-scale', 'f'), ('test set', 'public benchmark', 'f'), ('n-gram overlap', '13-grams (GPT-3)', 'b'),
                       ('clean vs dirty scores', 'does overlap matter?', 'a'), ('fresh test set', 'GSM1k-style check', 'e')],
                caption='Detect, report, validate.'),
    example=dict(title='Worked example: how much does leakage inflate a score?',
                 setup='True skill 55%. Leaked items are answered correctly 95% of the time (memorized).',
                 steps=[f'10% leaked: 0.1 × 0.95 + 0.9 × 0.55 = <b>{0.1 * 0.95 + 0.9 * 0.55:.1%}</b> reported (+{(0.1 * 0.95 + 0.9 * 0.55 - 0.55) * 100:.0f} points).',
                        f'20% leaked: <b>{0.2 * 0.95 + 0.8 * 0.55:.1%}</b> (+{(0.2 * 0.95 + 0.8 * 0.55 - 0.55) * 100:.0f} points).',
                        'The clean subset still scores ~55%: the gap between full and clean scores is the inflation.',
                        'A fresh, equivalent test set would also show ~55%.'],
                 result='Report clean-subset scores next to full ones, and confirm on fresh data when it matters.'),
    traps=dict(tricks=[('Inflation = frac × (memorized − true).', 'Quick estimate of the effect.'),
                       ('13-grams.', 'Conservative overlap flag, as in GPT-3.'),
                       ('Fresh sets reveal overfitting.', 'GSM1k: drops of up to 8% for some families.')],
               traps=[('Filtered = clean.', 'Filters miss paraphrases and can have bugs (GPT-3 had one).'),
                      ('Short n-grams.', 'Coincidental matches create false positives in real text.'),
                      ('Assuming it always matters a lot.', 'GPT-3 and GSM1k found it varies by model and dataset; measure it.')]),
    papers=[P['gpt3'], P['gsm1k']],
)

EXTRAS['06-llm-as-judge'] = dict(
    glance=dict(steps=[('answers A, B', 'same prompt', 'f'), ('judge (A, B)', 'first order', 'c'), ('judge (B, A)', 'swapped', 'c'),
                       ('consistent?', 'win, else tie', 'a'), ('length control', 'condition on length', 'e')],
                caption='Swap positions, control for length, give references for hard questions, and never let a model grade itself alone.'),
    example=dict(title='Worked example: reading MT-Bench\'s bias numbers',
                 setup='MT-Bench measured position consistency (same verdict after swapping) and a "repetitive list" verbosity attack.',
                 steps=['Position consistency, default prompt: GPT-4 <b>65.0%</b>, GPT-3.5 <b>46.2%</b>, Claude-v1 <b>23.8%</b>.',
                        'So one in three GPT-4 verdicts flips with the order; with a single query you can\'t tell which.',
                        'Verbosity attack (padding with rephrased duplicates): Claude-v1 and GPT-3.5 fooled <b>91.3%</b> of the time, GPT-4 <b>8.7%</b>.',
                        'Length-controlled AlpacaEval raised agreement with Chatbot Arena from 0.94 to 0.98 (Spearman).'],
                 result='Even a strong judge needs the protocol: swap, aggregate, control for length.'),
    traps=dict(tricks=[('Swap and aggregate.', 'Win only if preferred in both orders; otherwise tie.'),
                       ('Reference-guided grading.', 'Give the judge a reference answer for maths and reasoning.'),
                       ('Calibrate on a human sample.', 'Check agreement before trusting a new judge or task.')],
               traps=[('Single-order judging.', 'Position bias decides many verdicts.'),
                      ('Self-judging.', 'Models favour their own outputs.'),
                      ('Longer = better.', 'Verbosity bias; use length-controlled metrics.')]),
    papers=[P['mtbench'], P['lcalpaca']],
)

EXTRAS['07-arenas'] = dict(
    glance=dict(steps=[('user prompt', 'real, fresh', 'f'), ('two anonymous models', 'answer side by side', 'c'), ('vote', 'A, B or tie', 'b'),
                       ('Bradley-Terry MLE', 'over all votes', 'a'), ('rating ± CI', 'Elo-like scale', 'e')],
                caption='Order-independent ratings with honest uncertainty.'),
    example=dict(title='Worked example: what rating gaps mean',
                 setup='Ratings on the Elo-like scale: R = 400 × ξ / ln 10, where ξ is the Bradley-Terry strength.',
                 steps=[f'100-point gap: P(win) = 1/(1 + 10<sup>−100/400</sup>) = <b>{1 / (1 + 10 ** (-0.25)):.0%}</b>.',
                        f'400-point gap: <b>{1 / (1 + 10 ** (-1)):.0%}</b> (10:1 odds).',
                        f'Strength gap of 1.0 log-odds = 400/ln 10 = <b>{400 / log(10):.0f} points</b> = {1 / (1 + 10 ** (-400 / log(10) / 400)):.0%} win rate.',
                        'Two models 15 points apart with ±20-point intervals are statistically tied.'],
                 result='Read ratings as win probabilities and intervals, not as strict ranks.'),
    traps=dict(tricks=[('P(win) = 1 / (1 + 10^(−Δ/400)).', '100 points ≈ 64%.'),
                       ('BT = logistic regression on votes.', 'Order-independent; intervals by sandwich estimator or bootstrap.'),
                       ('Combine with benchmarks.', 'Arenas measure preference; benchmarks measure specific skills.')],
               traps=[('Online Elo.', 'Depends on vote order and K.'),
                      ('Strict ranks.', 'Neighbours often overlap.'),
                      ('Preference = correctness.', 'Votes include style and length.')]),
    papers=[P['arena'], P['mtbench']],
)
