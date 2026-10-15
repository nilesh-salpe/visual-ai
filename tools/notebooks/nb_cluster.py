"""Cluster scheduling exercise notebooks: CPU simulations of FIFO and EASY backfill, and Slurm-style fair-share, priority and preemption."""

NBS = []

RUNTIME = 'Everything runs on CPU in plain Python, so no GPU or cluster is needed.'

# ------------------------------------------------------------------ 01
NBS.append(dict(
    slug='01_backfill_scheduler', title='01 · Queues and backfill: FIFO vs EASY backfill on a GPU cluster', deck='cluster-scheduling/01-scheduling-basics/', deck_name='Scheduling a GPU cluster', minutes=35,
    goals='a strict FIFO scheduler, an EASY backfill scheduler that lets short jobs jump ahead without delaying the job at the head of the queue, and the mean-wait metric to compare them.',
    runtime=RUNTIME,
    setup=r'''
# A job: {"id": str, "gpus": int, "runtime": hours}. Lists are in priority order (the queue).
# Jobs never ask for more GPUs than the cluster has, and the scheduler knows each job's runtime
# (in a real cluster it only knows the time limit the user requested).

def finished(running, t):
    """Running jobs still busy at time t: list of (end_time, gpus)."""
    return [(e, g) for e, g in running if e > t]
''',
    tasks=[
        dict(fn='fifo_schedule', title='Strict FIFO', md=r'''
            Simulate a cluster of `total_gpus` GPUs, all jobs submitted at time 0. Jobs start **strictly in queue order**: a job may start only when it fits **and** every job ahead of it has started. Return `{job_id: start_time}`.

            Event loop: at time `t`, drop finished jobs, start jobs from the front of the queue while they fit, then jump `t` to the next job end.''',
             starter=r'''
            def fifo_schedule(jobs, total_gpus):
                queue, running, starts, t = list(jobs), [], {}, 0
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_fifo_schedule(f):
                jobs = [dict(id="A", gpus=6, runtime=10), dict(id="B", gpus=8, runtime=5), dict(id="C", gpus=2, runtime=4), dict(id="D", gpus=2, runtime=12)]
                s = f(jobs, 8)
                assert s == {"A": 0, "B": 10, "C": 15, "D": 15}, f"got {s}: C and D must wait behind B, even though 2 GPUs sit idle for 10 hours"
                assert f([dict(id="x", gpus=4, runtime=1), dict(id="y", gpus=4, runtime=1)], 8) == {"x": 0, "y": 0}''',
             solution=r'''
            def fifo_schedule_solution(jobs, total_gpus):
                queue, running, starts, t = list(jobs), [], {}, 0
                while queue:
                    running = finished(running, t)
                    free = total_gpus - sum(g for _, g in running)
                    while queue and queue[0]["gpus"] <= free:
                        j = queue.pop(0)
                        starts[j["id"]] = t
                        running.append((t + j["runtime"], j["gpus"]))
                        free -= j["gpus"]
                    if queue:
                        t = min(e for e, _ in running if e > t)
                return starts'''),
        dict(fn='easy_backfill', title='EASY backfill', md=r'''
            Same loop, plus backfill. When the head job does not fit:
            1. **Reserve** for it: walk the running jobs in order of end time, adding their GPUs to the free count, until the head fits. That end time is the **shadow time**; the GPUs left over at that moment are the **extra** GPUs.
            2. Any later job that fits **now** may start if it **finishes by the shadow time**, or if it uses only **extra** GPUs (then reduce `extra` by its GPUs).

            This never delays the head job's reserved start. Return `{job_id: start_time}`.''',
             starter=r'''
            def easy_backfill(jobs, total_gpus):
                queue, running, starts, t = list(jobs), [], {}, 0
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_easy_backfill(f):
                jobs = [dict(id="A", gpus=6, runtime=10), dict(id="B", gpus=8, runtime=5), dict(id="C", gpus=2, runtime=4), dict(id="D", gpus=2, runtime=12)]
                s = f(jobs, 8)
                assert s == {"A": 0, "C": 0, "B": 10, "D": 15}, f"got {s}: C fits in the gap and ends before B's reserved start; D is too long"
                s = f(jobs, 10)
                assert s == {"A": 0, "C": 0, "D": 0, "B": 10}, f"got {s}: with 10 GPUs, 2 are extra at B's start, so the long job D may run now"''',
             solution=r'''
            def easy_backfill_solution(jobs, total_gpus):
                queue, running, starts, t = list(jobs), [], {}, 0
                def start(j, free):
                    starts[j["id"]] = t
                    running.append((t + j["runtime"], j["gpus"]))
                    return free - j["gpus"]
                while queue:
                    running = finished(running, t)
                    free = total_gpus - sum(g for _, g in running)
                    while queue and queue[0]["gpus"] <= free:
                        free = start(queue.pop(0), free)
                    if not queue:
                        break
                    head, avail, shadow = queue[0], free, t
                    for e, g in sorted(running):
                        if avail >= head["gpus"]:
                            break
                        avail, shadow = avail + g, e
                    extra = avail - head["gpus"]
                    for j in list(queue[1:]):
                        ends_in_time = t + j["runtime"] <= shadow
                        if j["gpus"] <= free and (ends_in_time or j["gpus"] <= extra):
                            free = start(j, free)
                            queue.remove(j)
                            if not ends_in_time:
                                extra -= j["gpus"]
                    t = min(e for e, _ in running if e > t)
                return starts'''),
        dict(fn='mean_wait', title='Measure the queue', md=r'''
            All jobs arrive at time 0, so a job's wait is its start time. Return the mean wait in hours, and the cluster **utilisation** over the makespan: GPU-hours used ÷ (total GPUs × time until the last job ends). Return `(mean_wait, utilisation)`.''',
             starter=r'''
            def mean_wait(starts, jobs, total_gpus):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_mean_wait(f):
                jobs = [dict(id="A", gpus=6, runtime=10), dict(id="B", gpus=8, runtime=5), dict(id="C", gpus=2, runtime=4), dict(id="D", gpus=2, runtime=12)]
                w, u = f({"A": 0, "B": 10, "C": 15, "D": 15}, jobs, 8)
                assert abs(w - 10.0) < 1e-9 and abs(u - 132 / (8 * 27)) < 1e-9, (w, u)
                w, u = f({"A": 0, "C": 0, "B": 10, "D": 15}, jobs, 8)
                assert abs(w - 6.25) < 1e-9, w''',
             solution=r'''
            def mean_wait_solution(starts, jobs, total_gpus):
                by_id = {j["id"]: j for j in jobs}
                wait = sum(starts.values()) / len(starts)
                makespan = max(starts[k] + by_id[k]["runtime"] for k in starts)
                used = sum(j["gpus"] * j["runtime"] for j in jobs)
                return wait, used / (total_gpus * makespan)'''),
    ],
    explore_md='A random workload of many small jobs and a few large ones on 64 GPUs: how much does backfill cut waiting? (It uses the true runtimes; with padded time limits it backfills less.)',
    explore=r'''
import random
random.seed(0)
work = [dict(id=f"j{i}", gpus=random.choice([1, 1, 2, 4, 8, 8, 16, 32, 64]), runtime=random.choice([1, 2, 4, 8, 24])) for i in range(300)]
for name, sched in [("FIFO", fifo_schedule_solution), ("EASY backfill", easy_backfill_solution)]:
    w, u = mean_wait_solution(sched(work, 64), work, 64)
    print(f"{name:14} mean wait {w:7.1f} h   utilisation {u:.0%}")''',
    takeaways='''
        * Strict FIFO leaves GPUs idle behind a large job at the head of the queue.
        * **Backfill** fills those holes with jobs that cannot delay the reserved start of the head job, so it depends on accurate **time limits**.
        * This is the idea behind Slurm's backfill plugin (`bf_window`, `bf_interval`), which also re-plans as jobs end early.''',
))

# ------------------------------------------------------------------ 02
NBS.append(dict(
    slug='02_fair_share_priority', title='02 · Fair share, job priority and preemption (Slurm-style)', deck='cluster-scheduling/02-slurm/', deck_name='Slurm for GPU clusters', minutes=30,
    goals='decayed usage with a half-life, the classic fair-share factor F = 2^(−U/S), the multifactor priority as a weighted sum, and choosing which running jobs to preempt.',
    runtime=RUNTIME,
    setup=r'''
import math
HALF_LIFE_DAYS = 7          # Slurm's default PriorityDecayHalfLife is 7 days
''',
    tasks=[
        dict(fn='decayed_usage', title='Usage with a half-life', md=r'''
            Each usage record is `(day, gpu_hours)`. Usage decays so that it counts half after one half-life: return `Σ gpu_hours · 0.5^((now − day) / half_life)`.''',
             starter=r'''
            def decayed_usage(records, now, half_life=HALF_LIFE_DAYS):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_decayed_usage(f):
                assert abs(f([(0, 100)], 7) - 50) < 1e-9, "one half-life halves the usage"
                assert abs(f([(0, 100), (14, 40)], 14) - 65) < 1e-9
                assert f([], 3) == 0''',
             solution=r'''
            def decayed_usage_solution(records, now, half_life=HALF_LIFE_DAYS):
                return sum(h * 0.5 ** ((now - d) / half_life) for d, h in records)'''),
        dict(fn='classic_fair_share', title='Classic fair-share factor', md=r'''
            Given each user's decayed `usage` and allocated `shares` (dicts), normalise both to fractions of their totals (U and S) and return `{user: 2 ** (-U / S)}`. A user who used exactly their share gets 0.5; under-served users approach 1, heavy users approach 0. (Slurm's default since 19.05 is the rank-based Fair Tree algorithm; classic is still available.)''',
             starter=r'''
            def classic_fair_share(usage, shares):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_classic_fair_share(f):
                F = f({"ana": 50, "bo": 50}, {"ana": 1, "bo": 1})
                assert abs(F["ana"] - 0.5) < 1e-9 and abs(F["bo"] - 0.5) < 1e-9, "used exactly their share → 0.5"
                F = f({"ana": 90, "bo": 10}, {"ana": 1, "bo": 1})
                assert F["bo"] > 0.5 > F["ana"], "the lighter user gets the higher factor"
                assert abs(F["ana"] - 2 ** (-0.9 / 0.5)) < 1e-9
                F = f({"ana": 0, "bo": 10}, {"ana": 1, "bo": 3})
                assert F["ana"] == 1.0''',
             solution=r'''
            def classic_fair_share_solution(usage, shares):
                tu, ts = sum(usage.values()) or 1, sum(shares.values())
                return {u: 2 ** (-(usage[u] / tu) / (shares[u] / ts)) for u in shares}'''),
        dict(fn='job_priority', title='Multifactor priority', md=r'''
            Slurm's multifactor priority is a weighted sum of factors that each lie in [0, 1], minus the job's nice value. `factors` and `weights` are dicts keyed by factor name (age, fairshare, jobsize, partition, qos); a missing weight means 0 (Slurm's default weight). Return the integer `round(Σ weight · factor) − nice`. Then sort a list of jobs by priority, highest first.''',
             starter=r'''
            def job_priority(factors, weights, nice=0):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_job_priority(f):
                w = {"age": 1000, "fairshare": 10000, "qos": 5000}
                assert f({"age": 0.5, "fairshare": 0.8, "qos": 1.0}, w) == 13500
                assert f({"age": 0.5, "fairshare": 0.8, "qos": 1.0, "jobsize": 1.0}, w) == 13500, "a factor with no weight contributes nothing"
                assert f({"fairshare": 0.25}, w, nice=100) == 2400''',
             solution=r'''
            def job_priority_solution(factors, weights, nice=0):
                return round(sum(weights.get(k, 0) * v for k, v in factors.items())) - nice'''),
        dict(fn='pick_preemptees', title='Whom to preempt', md=r'''
            A high-priority job needs `need` GPUs and only `free` are idle. `running` is a list of `(job_id, gpus, priority)` for preemptable jobs. Preempt the **lowest-priority** jobs first (ties: the smaller job first) until enough GPUs are free; return their ids in that order. If even preempting everything would not free enough, return `[]` and preempt nothing.''',
             starter=r'''
            def pick_preemptees(running, need, free):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_pick_preemptees(f):
                running = [("a", 8, 100), ("b", 2, 10), ("c", 4, 10), ("d", 8, 50)]
                assert f(running, 8, 2) == ["b", "c"], "lowest priority first, smaller first on ties, stop once 8 GPUs are free"
                assert f(running, 4, 4) == []
                assert f(running, 40, 0) == [], "cannot free 40 GPUs: preempt nothing"''',
             solution=r'''
            def pick_preemptees_solution(running, need, free):
                out = []
                for jid, g, _ in sorted(running, key=lambda r: (r[2], r[1])):
                    if free >= need:
                        break
                    out.append(jid); free += g
                return out if free >= need else []'''),
    ],
    explore_md='How a heavy week fades: the fair-share factor of a user who ran 1,000 GPU-hours on day 0, against a colleague with steady light use, over three weeks.',
    explore=r'''
for day in [0, 3, 7, 14, 21]:
    heavy = decayed_usage_solution([(0, 1000)], day)
    light = decayed_usage_solution([(d, 20) for d in range(day + 1)], day)
    F = classic_fair_share_solution({"heavy": heavy, "light": light}, {"heavy": 1, "light": 1})
    print(f"day {day:2}: usage heavy {heavy:6.0f} light {light:5.0f}   F heavy {F['heavy']:.2f} light {F['light']:.2f}")''',
    takeaways='''
        * Fair share compares **recent** usage (decayed with a half-life, 7 days by default) with allocated shares.
        * Priority is a weighted sum of normalised factors; weights default to 0, so the configuration decides what matters.
        * Preemption picks victims by priority; with `PreemptMode=REQUEUE` they go back to the queue, so checkpointing decides how much work is lost.''',
))
