"""Reasoning and test-time compute exercise notebook: majority voting, coverage and best-of-N with a noisy verifier, simulated on CPU."""

NBS = []

NBS.append(dict(
    slug='01_test_time_compute', title='01 · Test-time compute: majority voting, coverage and best-of-N', deck='reasoning/02-sampling-and-voting/', deck_name='Sampling, voting and coverage', minutes=35,
    goals='majority voting over sampled answers (self-consistency), a simulator of voting accuracy, and best-of-N selection with an imperfect verifier, then the gap between coverage and what a selector can actually pick.',
    setup=r'''
# A question is modelled by p, the chance that one sampled chain of thought ends in the right answer.
# Wrong samples land on one of n_wrong distinct wrong answers, uniformly.
from collections import Counter
''',
    tasks=[
        dict(fn='majority_vote', title='Majority vote', md=r'''
            Given a list of final answers from sampled chains of thought, return the most frequent one. Break ties by the answer that **appeared first**. (This is self-consistency: sample several reasoning paths, then marginalise over the paths by voting on the answer.)''',
             starter=r'''
            def majority_vote(answers):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_majority_vote(f):
                assert f(["12", "15", "12", "9", "12"]) == "12"
                assert f(["a", "b", "b", "a"]) == "a", "tie: the answer seen first wins"
                assert f(["7"]) == "7"''',
             solution=r'''
            def majority_vote_solution(answers):
                counts = Counter(answers)
                best = max(counts.values())
                return next(a for a in answers if counts[a] == best)'''),
        dict(fn='voting_accuracy', title='How accurate is voting?', md=r'''
            Simulate `trials` questions with the same `p`. For each, draw `n` samples: correct (`"right"`) with probability `p`, otherwise one of `n_wrong` wrong answers chosen uniformly. Return the fraction of questions where the majority vote (your `majority_vote`, or the reference) is right. Use `np.random.default_rng(seed)`.''',
             starter=r'''
            def voting_accuracy(p, n, n_wrong=10, trials=2000, seed=0):
                rng = np.random.default_rng(seed)
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_voting_accuracy(f):
                one = f(0.6, 1)
                assert abs(one - 0.6) < 0.04, f"one sample is just p, got {one:.3f}"
                assert f(0.6, 15) > 0.9, "with 15 votes a 60%-likely answer almost always wins"
                assert f(0.3, 25, n_wrong=10) > 0.6, "errors scattered over many answers: the right one still wins"
                assert f(0.3, 25, n_wrong=1) < 0.1, "one dominant wrong answer: voting makes things worse"''',
             solution=r'''
            def voting_accuracy_solution(p, n, n_wrong=10, trials=2000, seed=0):
                rng = np.random.default_rng(seed)
                hits = 0
                for _ in range(trials):
                    ok = rng.random(n) < p
                    wrong = rng.integers(0, n_wrong, n)
                    answers = ["right" if o else f"w{w}" for o, w in zip(ok, wrong)]
                    hits += majority_vote_solution(answers) == "right"
                return hits / trials'''),
        dict(fn='best_of_n_accuracy', title='Best-of-N with a noisy verifier', md=r'''
            A verifier scores each sample as `correct + noise`, with `correct` in {0, 1} and noise ~ Normal(0, `noise`). Best-of-N returns the highest-scoring sample. Simulate `trials` questions with `n` samples each and return the fraction where the chosen sample is correct. With `noise = 0` this equals **coverage** (pass@n); as noise grows it falls back toward `p`.''',
             starter=r'''
            def best_of_n_accuracy(p, n, noise, trials=4000, seed=0):
                rng = np.random.default_rng(seed)
                # TODO (vectorise: arrays of shape (trials, n))
                raise NotImplementedError''',
             test=r'''
            def _test_best_of_n_accuracy(f):
                assert abs(f(0.2, 10, 0.0) - (1 - 0.8 ** 10)) < 0.03, "a perfect verifier finds a correct sample whenever one exists"
                assert abs(f(0.2, 10, 50.0) - 0.2) < 0.03, "a useless verifier picks at random"
                assert f(0.2, 10, 0.5) > f(0.2, 10, 1.5), "a better verifier picks better"''',
             solution=r'''
            def best_of_n_accuracy_solution(p, n, noise, trials=4000, seed=0):
                rng = np.random.default_rng(seed)
                correct = rng.random((trials, n)) < p
                score = correct + rng.normal(0, noise, (trials, n)) if noise > 0 else correct.astype(float) + rng.random((trials, n)) * 1e-9
                return float(correct[np.arange(trials), score.argmax(1)].mean())'''),
    ],
    explore_md='One hard question type (p = 0.2): coverage keeps rising with n, but what you can actually select depends on the selector. This is the gap Large Language Monkeys reports: majority voting and reward models plateau while coverage keeps growing.',
    explore=r'''
p = 0.2
print("   n   coverage   majority vote   best-of-N (verifier noise 0.5)   best-of-N (noise 1.5)")
for n in [1, 4, 16, 64, 256]:
    cov = 1 - (1 - p) ** n
    print(f"{n:4} {cov:10.2f} {voting_accuracy_solution(p, n, trials=600):15.2f} {best_of_n_accuracy_solution(p, n, 0.5, trials=1500):31.2f} {best_of_n_accuracy_solution(p, n, 1.5, trials=1500):22.2f}")''',
    takeaways='''
        * **Coverage** (any sample right) grows with samples; **selection** (picking the right one) is the bottleneck when answers cannot be checked automatically.
        * Majority voting works when errors scatter over many answers and fails when one wrong answer dominates.
        * Best-of-N is only as good as its verifier: with automatic checks (unit tests, proofs) it approaches coverage, with a noisy reward model it plateaus.''',
))
