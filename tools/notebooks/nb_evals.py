"""Evals exercise notebooks."""

BASE = r'''
def sigmoid(z):
    return 1 / (1 + np.exp(-z))
'''

NBS = []

# ------------------------------------------------------------------ 01
NBS.append(dict(
    slug='01_pass_at_k', title='01 · pass@k: the unbiased estimator', deck='evals/03-pass-at-k/', deck_name='pass@k and sampling metrics', minutes=30,
    goals="the Codex paper's unbiased pass@k estimator and its numerically stable form, and a simulation showing why the obvious estimator is biased.",
    setup=BASE + r'''
from math import comb
''',
    tasks=[
        dict(fn='pass_at_k', title='The unbiased estimator', md=r'''
            pass@k = probability that **at least one of k** samples passes the unit tests. Sampling exactly k per problem is noisy, so Chen et al. (2021) sample **n ≥ k**, count the **c** that pass, and estimate
            $$\text{pass@}k = 1 - \frac{\binom{n-c}{k}}{\binom{n}{k}}$$
            i.e. one minus the chance that a random size-k subset of the n samples contains no passing sample. If $n - c < k$, every subset contains a pass, so the answer is 1.
            Binomials overflow for large n, so use the paper's stable product form: $1 - \prod_{i=n-c+1}^{n}\left(1 - \frac{k}{i}\right)$.''',
             starter=r'''
            def pass_at_k(n, c, k):
                # TODO: return 1.0 if n - c < k; else 1 - prod(1 - k / arange(n - c + 1, n + 1))
                raise NotImplementedError''',
             test=r'''
            def _test_pass_at_k(f):
                for n, c, k in [(10, 3, 1), (10, 3, 5), (20, 0, 5), (20, 20, 1), (200, 7, 100), (5, 2, 4)]:
                    want = 1.0 if n - c < k else 1 - comb(n - c, k) / comb(n, k)
                    assert np.isclose(f(n, c, k), want), f"pass_at_k({n},{c},{k}) = {f(n, c, k)}, expected {want}"
                assert np.isclose(f(10, 3, 1), 0.3), "pass@1 must equal c/n"
                assert np.isfinite(f(5000, 30, 1000)), "must not overflow for large n"''',
             solution=r'''
            def pass_at_k_solution(n, c, k):
                if n - c < k:
                    return 1.0
                return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))'''),
        dict(fn='naive_pass_at_k', title='The tempting (biased) estimator', md=r'''
            The obvious shortcut: estimate the per-sample pass rate $\hat p = c/n$, then use $1 - (1 - \hat p)^k$.
            It looks right, because that is the formula for the true pass@k given the true p. But $1-(1-p)^k$ is concave in p, so plugging in a noisy $\hat p$ **underestimates** on average (Jensen's inequality). The Codex paper notes this estimator is biased.''',
             starter=r'''
            def naive_pass_at_k(n, c, k):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_naive_pass_at_k(f):
                assert np.isclose(f(10, 3, 1), 0.3)
                assert np.isclose(f(10, 3, 5), 1 - 0.7 ** 5)''',
             solution=r'''
            def naive_pass_at_k_solution(n, c, k):
                return 1 - (1 - c / n) ** k'''),
        dict(fn='estimator_bias', title='Measure the bias by simulation', md=r'''
            For a problem whose true per-sample pass rate is `p`, the true pass@k is $1-(1-p)^k$. Simulate `trials` evaluations: each draws $c \sim \mathrm{Binomial}(n, p)$ and applies an estimator. Return `(mean_estimate - true_value)` for the given estimator function.
            The tests check the unbiased estimator's mean error is ≈ 0 and the naive one is clearly negative for small p.''',
             starter=r'''
            def estimator_bias(estimator, p, n, k, trials=20000, seed=0):
                rng = np.random.default_rng(seed)
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_estimator_bias(f):
                u = f(pass_at_k_solution if f.__name__.endswith('_solution') else _ref_unbiased, 0.05, 20, 10)
                nv = f(lambda n, c, k: 1 - (1 - c / n) ** k, 0.05, 20, 10)
                assert abs(u) < 0.01, f"unbiased estimator should have ~0 bias, got {u:+.4f}"
                assert nv < -0.03, f"naive estimator should underestimate here, got {nv:+.4f}"

            def _ref_unbiased(n, c, k):
                return 1.0 if n - c < k else 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))''',
             solution=r'''
            def estimator_bias_solution(estimator, p, n, k, trials=20000, seed=0):
                rng = np.random.default_rng(seed)
                cs = rng.binomial(n, p, trials)
                return np.mean([estimator(n, int(c), k) for c in cs]) - (1 - (1 - p) ** k)'''),
    ],
    explore_md=r'''
        **pass@1 vs pass@k on a benchmark.** Give 164 problems (HumanEval's size) a spread of difficulties, sample n = 200 per problem, and report pass@1, @10 and @100. Codex-12B scored 28.8% at pass@1 and 70.2% with 100 samples: sampling many attempts and picking any that passes is very effective when tests are available. Then the naive estimator's bias across p.''',
    explore=r'''
        rng = np.random.default_rng(0); p = rng.beta(0.4, 0.8, 164); n = 200
        c = rng.binomial(n, p)
        for k in [1, 10, 100]:
            print(f"pass@{k:<3} unbiased {np.mean([pass_at_k_solution(n, ci, k) for ci in c]):.3f}   naive {np.mean([naive_pass_at_k_solution(n, ci, k) for ci in c]):.3f}")
        print("\nbias of the naive estimator (n=20, k=10):")
        for pp in [0.01, 0.05, 0.1, 0.3]:
            print(f"  p={pp:<5} naive {estimator_bias_solution(naive_pass_at_k_solution, pp, 20, 10):+.4f}   unbiased {estimator_bias_solution(pass_at_k_solution, pp, 20, 10):+.4f}")''',
    takeaways=r'''
        * pass@k asks "does at least one of k attempts succeed?". It rewards coverage, not reliability, so always say which k (and which n) you report.
        * Estimate it from n ≥ k samples with $1 - \binom{n-c}{k}/\binom{n}{k}$ (product form for stability). Plugging c/n into $1-(1-p)^k$ underestimates.
        * pass@1 with many samples is just the average pass rate, with much lower variance than one sample per problem.''',
))

# ------------------------------------------------------------------ 02
NBS.append(dict(
    slug='02_error_bars', title='02 · Error bars, clustered errors and paired comparisons', deck='evals/04-error-bars/', deck_name='Error bars and comparing models', minutes=40,
    goals='the statistics an eval report needs: the standard error of a mean score, clustered standard errors for grouped questions, a paired test for comparing two models, and a sample-size calculation.',
    setup=BASE + r'''
def simulate_eval(n_q=1000, cluster_size=1, gap=0.0, seed=0, base=0.7, share=0.75):
    """Two models answer the same questions. Questions come in clusters that share difficulty.
    Returns (scores_a, scores_b, cluster_ids) with 0/1 scores."""
    rng = np.random.default_rng(seed)
    n_c = n_q // cluster_size
    cl_diff = rng.normal(0, 1.5, n_c)                       # cluster difficulty (shared within cluster)
    q_diff = np.repeat(cl_diff, cluster_size) + rng.normal(0, 1.0, n_c * cluster_size)
    logit = np.log(base / (1 - base)) - q_diff
    pa = sigmoid(logit); pb = sigmoid(logit + gap)
    u = rng.random(len(pa))                                 # partly shared randomness: the models tend to fail the same questions
    u_b = np.where(rng.random(len(pa)) < share, u, rng.random(len(pa)))
    return (u < pa).astype(float), (u_b < pb).astype(float), np.repeat(np.arange(n_c), cluster_size)
''',
    tasks=[
        dict(fn='standard_error', title='Standard error of the mean score', md=r'''
            An eval score is a sample mean over questions, so it has sampling error. By the central limit theorem,
            $$\mathrm{SE}(\hat\mu) = \sqrt{\frac{1}{n}\cdot\frac{1}{n-1}\sum_i (s_i - \hat\mu)^2}$$
            and a 95% confidence interval is $\hat\mu \pm 1.96\,\mathrm{SE}$. Miller (2024), "Adding Error Bars to Evals", recommends this over bootstrapping as the default. Return the SE.''',
             starter=r'''
            def standard_error(scores):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_standard_error(f):
                s = np.array([1, 0, 1, 1, 0, 1, 1, 1.0])
                assert np.isclose(f(s), s.std(ddof=1) / np.sqrt(len(s)))
                a, _, _ = simulate_eval(4000)
                assert 0.006 < f(a) < 0.009, f"for ~70% accuracy on 4000 questions SE should be ~0.007, got {f(a):.4f}"''',
             solution=r'''
            def standard_error_solution(scores):
                s = np.asarray(scores, float)
                return s.std(ddof=1) / np.sqrt(len(s))'''),
        dict(fn='clustered_se', title='Clustered standard errors', md=r'''
            Many evals contain **groups** of related questions: several questions about one passage (DROP, RACE), the same problem in many languages (MGSM). Their errors are correlated, so the effective sample size is smaller than n. The clustered SE sums residuals within each cluster first:
            $$\mathrm{SE}_{clustered} = \frac{1}{n}\sqrt{\sum_{c}\Big(\sum_{i \in c}(s_i - \hat\mu)\Big)^2}$$
            With one question per cluster this reduces to the naive SE (up to the n vs n−1 factor). Miller reports clustered SEs "can be over 3X larger than naive standard errors" on real evals.''',
             starter=r'''
            def clustered_se(scores, clusters):
                # TODO: residuals, sum per cluster (np.bincount with weights), then the formula above
                raise NotImplementedError''',
             test=r'''
            def _test_clustered_se(f):
                r = np.random.default_rng(1); s = r.integers(0, 2, 500).astype(float)
                assert np.isclose(f(s, np.arange(500)), np.sqrt(((s - s.mean()) ** 2).sum()) / 500), "singleton clusters = naive (ddof 0)"
                a, _, cl = simulate_eval(2000, cluster_size=10)
                assert f(a, cl) > 1.4 * a.std(ddof=1) / np.sqrt(len(a)), "with correlated clusters of 10 the clustered SE should be much larger"''',
             solution=r'''
            def clustered_se_solution(scores, clusters):
                s = np.asarray(scores, float); e = s - s.mean()
                per_cluster = np.bincount(clusters, weights=e)
                return np.sqrt((per_cluster ** 2).sum()) / len(s)'''),
        dict(fn='paired_difference', title='Compare two models on the same questions', md=r'''
            To compare models A and B on the **same** questions, don't compare two independent confidence intervals. Look at the per-question differences $d_i = s^A_i - s^B_i$:
            $$\hat\delta = \bar d,\qquad \mathrm{SE}(\hat\delta) = \frac{\mathrm{sd}(d)}{\sqrt n},\qquad z = \hat\delta / \mathrm{SE}$$
            Because both models find the same questions easy or hard, the differences have much less variance than the scores. Miller: conduct "statistical inference on the question-level paired differences, rather than the population-level summary statistics". Return `(delta, se, z)`.''',
             starter=r'''
            def paired_difference(a, b):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_paired_difference(f):
                a, b, _ = simulate_eval(1000, gap=0.2, seed=0)
                d, se, z = f(b, a)
                assert np.isclose(d, b.mean() - a.mean()) and np.isclose(se, (b - a).std(ddof=1) / np.sqrt(1000))
                unpaired_se = np.sqrt(a.var(ddof=1) / 1000 + b.var(ddof=1) / 1000)
                assert se < 0.75 * unpaired_se, "paired SE should be much smaller than the unpaired SE here"
                assert z > 1.96 and d / unpaired_se < 1.96, f"the paired test should detect the gap (z={z:.2f}) while comparing separate CIs does not ({d / unpaired_se:.2f})"''',
             solution=r'''
            def paired_difference_solution(a, b):
                d = np.asarray(a, float) - np.asarray(b, float)
                delta, se = d.mean(), d.std(ddof=1) / np.sqrt(len(d))
                return delta, se, delta / se'''),
        dict(fn='questions_needed', title='How many questions do you need?', md=r'''
            Power analysis: to detect a true difference δ with a two-sided 5% test and 80% power, you need
            $$n = \left(\frac{(z_{0.975} + z_{0.8})\,\sigma_d}{\delta}\right)^2,\qquad z_{0.975} = 1.96,\ z_{0.8} = 0.8416$$
            where σ_d is the standard deviation of the per-question differences. Return n rounded **up**.''',
             starter=r'''
            def questions_needed(delta, sd_diff, z_alpha=1.959964, z_power=0.841621):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_questions_needed(f):
                want = lambda d, sd: int(np.ceil(((1.959964 + 0.841621) * sd / d) ** 2))
                assert f(0.02, 0.3) == want(0.02, 0.3), f"got {f(0.02, 0.3)}, expected {want(0.02, 0.3)}"
                assert abs(f(0.01, 0.3) / f(0.02, 0.3) - 4) < 0.01, "halving delta should quadruple n"
                assert isinstance(f(0.05, 0.5), (int, np.integer)), "return an integer (rounded up)"''',
             solution=r'''
            def questions_needed_solution(delta, sd_diff, z_alpha=1.959964, z_power=0.841621):
                return int(np.ceil(((z_alpha + z_power) * sd_diff / delta) ** 2))'''),
    ],
    explore_md=r'''
        **How wide are typical error bars, and how much do clusters matter?** First the 95% CI half-width at 70% accuracy for common eval sizes. Then one simulated eval reported naively vs clustered, and finally how often a 2-point gap is detected by paired vs unpaired comparison across 500 simulated evals.''',
    explore=r'''
        for n in [100, 500, 1000, 5000, 15000]:
            print(f"n={n:6,}: 95% CI ≈ ±{1.96 * np.sqrt(0.7 * 0.3 / n) * 100:.1f} points")
        a, b, cl = simulate_eval(2500, cluster_size=10, seed=2)
        print(f"\nclusters of 10: naive SE {standard_error_solution(a) * 100:.2f} pts, clustered SE {clustered_se_solution(a, cl) * 100:.2f} pts "
              f"(ratio {clustered_se_solution(a, cl) / standard_error_solution(a):.2f})")
        hits_p = hits_u = 0; gaps = []
        for s in range(500):
            a, b, _ = simulate_eval(1000, gap=0.2, seed=100 + s)
            d, se, z = paired_difference_solution(b, a); gaps.append(d)
            hits_p += abs(z) > 1.96
            hits_u += abs(d) / np.sqrt(a.var(ddof=1) / 1000 + b.var(ddof=1) / 1000) > 1.96
        print(f"\naverage gap {np.mean(gaps) * 100:.1f} pts on 1,000 questions: detected by paired test {hits_p / 5:.0f}% of the time, by unpaired {hits_u / 5:.0f}%")''',
    takeaways=r'''
        * Always report a standard error: with 1,000 questions at 70% accuracy, the 95% interval is about ±2.8 points, wider than many leaderboard gaps.
        * Grouped questions need clustered standard errors. Ignoring the clustering can understate uncertainty by 3× or more.
        * When comparing two models on the same questions, test the paired per-question differences: it can detect gaps that overlapping confidence intervals hide.
        * Use power analysis before building an eval: the questions needed grow with $1/\delta^2$.''',
))

# ------------------------------------------------------------------ 03
NBS.append(dict(
    slug='03_contamination', title='03 · Detecting benchmark contamination with n-grams', deck='evals/05-contamination/', deck_name='Contamination', minutes=35,
    goals="a GPT-3-style 13-gram overlap detector, a contamination report that splits the benchmark into clean and dirty subsets, and a simulation of how leaked test items inflate scores.",
    setup=BASE + r'''
rng = np.random.default_rng(0)
WORDS = [f"w{i}" for i in range(5000)]
def doc(n):
    return list(rng.choice(WORDS, n))
train_docs = [doc(int(rng.integers(200, 800))) for _ in range(300)]
test_items = [doc(int(rng.integers(20, 60))) for _ in range(200)]
LEAKED = set(rng.choice(200, 30, replace=False).tolist())
for i in LEAKED:                       # copy a span of each leaked test item into a random training doc
    item = test_items[i]; span = item[:max(15, len(item) // 2)]
    d = train_docs[int(rng.integers(300))]; pos = int(rng.integers(len(d))); d[pos:pos] = span
print(f"{len(train_docs)} training docs, {len(test_items)} test items, {len(LEAKED)} secretly leaked")
''',
    tasks=[
        dict(fn='ngram_set', title='Collect n-grams', md=r'''
            Return the **set** of all contiguous n-grams (as tuples) in a token list. If the list is shorter than n, return an empty set.''',
             starter=r'''
            def ngram_set(tokens, n):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_ngram_set(f):
                assert f(['a', 'b', 'c', 'd'], 2) == {('a', 'b'), ('b', 'c'), ('c', 'd')}
                assert f(['a', 'b'], 3) == set()
                assert len(f(['x'] * 10, 3)) == 1''',
             solution=r'''
            def ngram_set_solution(tokens, n):
                return {tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}'''),
        dict(fn='flag_contaminated', title='Flag test items that overlap the training data', md=r'''
            GPT-3 flagged test examples "that have a 13-gram overlap with anything in the pretraining set (or that overlap with the whole example when it is shorter than 13-grams)". The goal was to "very conservatively flag anything that could potentially be contamination".
            Build one n-gram set over all training docs, then return a boolean array: is any n-gram of each test item in it? For items shorter than n, check whether the whole item appears as a contiguous span of some training doc (you may use a set of all len(item)-grams).''',
             starter=r'''
            def flag_contaminated(test_items, train_docs, n=13):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_flag_contaminated(f):
                flags = f(test_items, train_docs)
                assert flags.dtype == bool and len(flags) == 200
                found = set(np.nonzero(flags)[0].tolist())
                assert LEAKED <= found, f"missed leaked items: {sorted(LEAKED - found)}"
                assert len(found - LEAKED) == 0, f"false positives: {sorted(found - LEAKED)}"
                short = [['w1', 'w2', 'w3']]
                assert f(short, [['w0', 'w1', 'w2', 'w3', 'w4']])[0] and not f(short, [['w1', 'w3', 'w2']])[0], "short items: match the whole item as a span"''',
             solution=r'''
            def flag_contaminated_solution(test_items, train_docs, n=13):
                grams = set().union(*(ngram_set_solution(d, n) for d in train_docs))
                out = []
                for item in test_items:
                    if len(item) < n:
                        m = len(item)
                        out.append(any(tuple(item) in ngram_set_solution(d, m) for d in train_docs))
                    else:
                        out.append(not grams.isdisjoint(ngram_set_solution(item, n)))
                return np.array(out, dtype=bool)'''),
        dict(fn='contamination_report', title='Clean vs dirty scores', md=r'''
            GPT-3's approach: score the model on the full benchmark, on the **clean** subset (not flagged) and on the **dirty** subset (flagged). If clean ≈ full, contamination isn't driving the score.
            Given per-item 0/1 `scores` and boolean `flags`, return a dict with `full`, `clean`, `dirty` accuracies and `frac_dirty`.''',
             starter=r'''
            def contamination_report(scores, flags):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_contamination_report(f):
                s = np.array([1, 1, 0, 1, 0, 1.0]); fl = np.array([True, True, False, False, False, False])
                r = f(s, fl)
                assert np.isclose(r['full'], 4 / 6) and np.isclose(r['dirty'], 1.0) and np.isclose(r['clean'], 0.5) and np.isclose(r['frac_dirty'], 2 / 6)''',
             solution=r'''
            def contamination_report_solution(scores, flags):
                s = np.asarray(scores, float); fl = np.asarray(flags, bool)
                return dict(full=s.mean(), clean=s[~fl].mean(), dirty=s[fl].mean() if fl.any() else float('nan'), frac_dirty=fl.mean())'''),
    ],
    explore_md=r'''
        **How much does leakage inflate a score?** Simulate a model with true skill 55% that answers leaked items correctly 95% of the time (memorized). Sweep the leaked fraction and compare the reported score with the clean-subset score. Then run the detector at different n: smaller n catches paraphrase-like partial overlaps but also flags coincidental matches on real text, which is why GPT-3 chose a conservative 13. (Our random-word toy has no coincidental matches; real text does.)''',
    explore=r'''
        r = np.random.default_rng(1)
        for frac in [0.0, 0.05, 0.1, 0.2, 0.4]:
            fl = r.random(2000) < frac
            s = np.where(fl, r.random(2000) < 0.95, r.random(2000) < 0.55).astype(float)
            rep = contamination_report_solution(s, fl)
            print(f"leaked {frac:4.0%}: reported {rep['full']:.3f}   clean subset {rep['clean']:.3f}   inflation {100 * (rep['full'] - rep['clean']):+.1f} pts")
        for n in [8, 13, 20]:
            print(f"n={n:2d}: flagged {flag_contaminated_solution(test_items, train_docs, n).sum()} of 200 (30 truly leaked)")''',
    takeaways=r'''
        * Contamination means test items (or close variants) appeared in training data, so the score partly measures memorization.
        * n-gram overlap (GPT-3 used 13-grams) is a simple, conservative detector; report clean-subset scores next to full ones.
        * Detection misses paraphrases and translations. Fresh, held-out test sets (GSM1k found drops of up to 8% for some model families) and canary strings are complementary defences.''',
))

# ------------------------------------------------------------------ 04
NBS.append(dict(
    slug='04_judges_and_arenas', title='04 · LLM judges and arena ratings', deck='evals/07-arenas/', deck_name='Arenas and ratings', minutes=45,
    goals='a position-swap consistency test for an LLM judge, a Bradley-Terry fit from pairwise votes (as Chatbot Arena does), and an online Elo update, plus a demonstration that Elo depends on vote order while Bradley-Terry does not.',
    setup=BASE + r'''
rng = np.random.default_rng(0)
TRUE = np.array([1.2, 0.8, 0.5, 0.0, -0.3, -1.0])     # true strengths of 6 models (log-odds scale)
M = len(TRUE)
def simulate_votes(n, seed=0):
    """Random pairs of models; the user prefers i over j with prob sigmoid(TRUE[i] - TRUE[j])."""
    r = np.random.default_rng(seed)
    i = r.integers(0, M, n); j = (i + r.integers(1, M, n)) % M
    i_wins = r.random(n) < sigmoid(TRUE[i] - TRUE[j])
    return np.stack([np.where(i_wins, i, j), np.where(i_wins, j, i)], 1)   # rows: (winner, loser)
VOTES = simulate_votes(20000)

def make_judge(first_bias, seed=0):
    """A noisy judge that adds `first_bias` (in log-odds) to whichever answer is shown first."""
    r = np.random.default_rng(seed)
    def judge(qa, qb):
        return 'A' if r.random() < sigmoid(qa - qb + first_bias) else 'B'
    return judge
''',
    tasks=[
        dict(fn='swap_consistency', title='Position-swap consistency', md=r'''
            MT-Bench checked judges by asking twice, with the two answers swapped. A judge is **consistent** on a pair if it picks the same underlying answer both times. GPT-4 was consistent 65% of the time, GPT-3.5 46% and Claude-v1 24% (default prompt), with most inconsistency favouring the first position.
            `judge(qa, qb)` returns 'A' (first shown) or 'B'. For each `(qa, qb)` quality pair, query `judge(qa, qb)` and `judge(qb, qa)`. Return `(consistency, first_bias_rate)`, where the latter is the fraction of pairs where the judge picked the **first** answer both times.''',
             starter=r'''
            def swap_consistency(judge, pairs):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_swap_consistency(f):
                pairs = [(rng.normal(), rng.normal()) for _ in range(3000)]
                c0, b0 = f(make_judge(0.0, 1), pairs); c2, b2 = f(make_judge(2.0, 2), pairs)
                assert 0 <= c0 <= 1 and 0 <= b0 <= 1
                assert c2 < c0 - 0.15, f"a position-biased judge must be less consistent ({c2:.2f} vs {c0:.2f})"
                assert b2 > 0.4 and b0 < 0.2, f"first-position bias rate should jump ({b0:.2f} -> {b2:.2f})"''',
             solution=r'''
            def swap_consistency_solution(judge, pairs):
                cons = first = 0
                for qa, qb in pairs:
                    x, y = judge(qa, qb), judge(qb, qa)        # y == 'B' means it again chose the answer that was qa
                    cons += (x == 'A') == (y == 'B')
                    first += x == 'A' and y == 'A'
                return cons / len(pairs), first / len(pairs)'''),
        dict(fn='fit_bradley_terry', title='Fit Bradley-Terry strengths', md=r'''
            Chatbot Arena estimates model strengths $\xi$ by maximum likelihood under the Bradley-Terry model, $P(i \succ j) = \sigma(\xi_i - \xi_j)$ (with confidence intervals from a sandwich estimator or bootstrap).
            Fit $\xi$ by gradient **ascent** on the mean log-likelihood $\frac{1}{N}\sum \log\sigma(\xi_w - \xi_l)$. The gradient adds $(1-\sigma(\xi_w-\xi_l))$ to the winner and subtracts it from the loser. Only differences are identified, so re-centre $\xi$ to mean 0 at the end.''',
             starter=r'''
            def fit_bradley_terry(votes, m, steps=2000, lr=2.0):
                xi = np.zeros(m)
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_fit_bradley_terry(f):
                xi = f(VOTES, M)
                assert np.isclose(xi.mean(), 0, atol=1e-8), "centre the strengths"
                assert np.allclose(xi, TRUE - TRUE.mean(), atol=0.08), f"should recover true strengths: {np.round(xi, 2)} vs {np.round(TRUE - TRUE.mean(), 2)}"
                perm = np.random.default_rng(5).permutation(len(VOTES))
                assert np.allclose(f(VOTES[perm], M), xi, atol=1e-6), "BT must not depend on vote order"''',
             solution=r'''
            def fit_bradley_terry_solution(votes, m, steps=2000, lr=2.0):
                xi = np.zeros(m); w, l = votes[:, 0], votes[:, 1]
                for _ in range(steps):
                    g = 1 - sigmoid(xi[w] - xi[l])
                    xi += lr * (np.bincount(w, g, m) - np.bincount(l, g, m)) / len(votes)
                return xi - xi.mean()'''),
        dict(fn='online_elo', title='Online Elo', md=r'''
            Elo processes votes **one at a time**: expected score $E_w = 1/(1 + 10^{(R_l - R_w)/400})$, then $R_w \mathrel{+}= K(1 - E_w)$, $R_l \mathrel{-}= K(1 - E_w)$. Start everyone at 1000.
            It's cheap and online, but the final ratings depend on the **order** of the votes and on K. The test shuffles the same votes and checks that the ratings move.''',
             starter=r'''
            def online_elo(votes, m, k=4.0, init=1000.0):
                R = np.full(m, init)
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_online_elo(f):
                R = f(VOTES[:5000], M)
                assert np.argsort(-R).tolist() == list(range(M)), f"ranking should match the true order, got {np.argsort(-R).tolist()}"
                R2 = f(VOTES[:5000][::-1], M)
                assert np.abs(R - R2).max() > 1.0, "Elo should depend on vote order"
                assert np.isclose(f(np.array([[0, 1]]), 2, k=32)[0], 1016.0), "one win between equals moves K/2 = 16 points"''',
             solution=r'''
            def online_elo_solution(votes, m, k=4.0, init=1000.0):
                R = np.full(m, init)
                for w, l in votes:
                    e = 1 / (1 + 10 ** ((R[l] - R[w]) / 400))
                    R[w] += k * (1 - e); R[l] -= k * (1 - e)
                return R'''),
    ],
    explore_md=r'''
        **Order dependence and confidence intervals.** Run Elo on five random orderings of the same votes and look at the spread for each model. Then convert Bradley-Terry strengths to the familiar Elo scale ($400/\ln 10$ per log-odds unit) and add bootstrap 95% intervals, which is what an arena leaderboard should show.''',
    explore=r'''
        runs = np.array([online_elo_solution(VOTES[np.random.default_rng(s).permutation(len(VOTES))], M, k=16) for s in range(5)])
        print("online Elo (K=16) over 5 orderings of identical votes:")
        for i in range(M):
            print(f"  model {i}: {runs[:, i].min():7.1f} .. {runs[:, i].max():7.1f}")
        scale = 400 / np.log(10); xi = fit_bradley_terry_solution(VOTES, M) * scale + 1000
        boots = np.array([fit_bradley_terry_solution(VOTES[np.random.default_rng(100 + b).integers(0, len(VOTES), len(VOTES))], M, steps=600) for b in range(30)]) * scale + 1000
        lo, hi = np.percentile(boots, [2.5, 97.5], axis=0)
        print("\nBradley-Terry on the Elo scale, with bootstrap 95% CI:")
        for i in range(M):
            print(f"  model {i}: {xi[i]:7.1f}  [{lo[i]:7.1f}, {hi[i]:7.1f}]   true {(TRUE[i] - TRUE.mean()) * scale + 1000:7.1f}")''',
    takeaways=r'''
        * LLM judges are cheap and agree with humans about as often as humans agree with each other (MT-Bench: >80%), but they have position, verbosity and self-enhancement biases. Always swap positions and control for length.
        * Arena-style leaderboards turn pairwise votes into ratings. Bradley-Terry maximum likelihood is order-independent and gives proper confidence intervals; online Elo is order- and K-dependent.
        * Report intervals, not just ranks: neighbouring models often overlap.''',
))
