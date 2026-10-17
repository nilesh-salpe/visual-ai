---
title: Autonomous Coding Agent
body:
  data-deck: Autonomous coding agent
  data-home: ../index.html
  data-home-label: System design
  data-doc: design.html
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
- ../../shared/diagram.js
intro:
  kicker: Visual AI · System design · 03
  h1: An autonomous coding agent
  sub: 'A platform that takes issues and returns tested pull requests: the agent loop, sandboxes, durable execution, cost of long contexts, verification and human
    review.'
  problem: Design a service that takes 10,000 coding tasks a day (bug reports, small features), works on each in an isolated environment, and opens a pull request
    that passes the tests, safely and at a predictable cost.
  core: Run each task as a <b>durable workflow</b> around the agent loop; execute every tool call in a fresh <b>microVM sandbox</b> with <b>no secrets</b> and an
    <b>egress allowlist</b>; keep context cost in check with <b>prompt caching</b> and compaction; <b>verify</b> with the project's tests and pass^k evaluation; require
    <b>human review</b> before merge.
  hint: '[Read the full design doc →](design.html) · Previous: [Enterprise RAG assistant](../02-enterprise-rag/index.html) · Next: [Planning a pretraining run →](../04-pretraining-run/index.html)
    · [All case studies](../index.html)'
papers:
- ant_sandboxing
- firecracker
- temporal_workflows
- ant_caching
- swebench
- taubench
- bea
---

<!-- slide from="title" -->

<!-- slide id="s-req" chapter="Requirements" tag="1 · Requirements" tagclass="b1" -->
## What the system must do

::: cards grid2
### [f] Functional
Accept a task and a repository; produce a branch and pull request with a description; report progress; allow cancellation.

### [d] Safety
Agent-written code runs isolated; no credentials inside the environment; no unreviewed changes reach the main branch.

### [a] Scale (assumption)
10,000 tasks a day, about 40 agent steps and 20 minutes each, peak 3× average.

### [e] Quality and cost
Tests pass on every proposed change; cost per resolved task tracked and budgeted.
:::

<!-- slide id="s-est" chapter="Estimates" tag="2 · Estimates" tagclass="b2" -->
## Tokens and sandboxes <span class="ill">calculator</span>

<div class="visual"><div class="controls"><label class="ctl">tasks / day (K) <input type="range" id="kT" min="1" max="50" step="1" value="10"> <output id="kTo"></output></label><label class="ctl">steps / task <input type="range" id="kN" min="5" max="100" step="5" value="40"> <output id="kNo"></output></label><label class="ctl">prefix tokens (K) <input type="range" id="kP" min="2" max="60" step="1" value="20"> <output id="kPo"></output></label><label class="ctl">tokens added / step (×100) <input type="range" id="kS" min="5" max="100" step="5" value="20"> <output id="kSo"></output></label><label class="ctl">minutes / task <input type="range" id="kM" min="5" max="120" step="5" value="20"> <output id="kMo"></output></label><label class="ctl">peak factor <input type="range" id="kF" min="1" max="6" step="0.5" value="3"> <output id="kFo"></output></label></div><div class="bars"><div id="kBars"></div></div><p class="readout" id="kOut"></p></div>

Input tokens grow roughly with the square of the number of steps (nP + T·n(n−1)/2), because every step resends the growing history (Cost and latency deck).

<!-- slide id="s-arch" chapter="Architecture" tag="3 · Architecture" tagclass="b3" -->
## Architecture

::: diagram 660x300
nodes:
  is: {at: [10, 120, 110, 56], text: Issue, sub: or task, color: f, step: 1}
  wf: {at: [160, 110, 160, 76], text: Workflow engine, sub: durable · per task, color: a, step: 2}
  llm: {at: [160, 10, 160, 56], text: Model API, sub: via gateway, color: b, step: 3}
  sb: {at: [370, 110, 150, 76], text: Sandbox (microVM), sub: repo · tests, color: c, step: 4}
  px: {at: [560, 60, 90, 56], text: Egress proxy, sub: allowlist, color: d, step: 5}
  gp: {at: [560, 160, 90, 56], text: Git proxy, sub: real token, color: d, step: 6}
  rv: {at: [160, 235, 160, 56], text: Review, sub: tests · human, color: e, step: 7}
  pr: {at: [370, 235, 150, 56], text: Pull request, sub: merge after review, color: e, step: 8}
edges:
  - {from: is, to: wf, step: 2}
  - {from: wf, to: llm, label: each step, step: 3}
  - {from: wf, to: sb, label: tool calls, step: 4}
  - {from: sb, to: px, step: 5, style: dash}
  - {from: sb, to: gp, label: push, step: 6}
  - {from: wf, to: rv, step: 7}
  - {from: rv, to: pr, step: 8}
steps:
  - 'A task arrives: an issue to fix or a change request.'
  - 'A durable workflow runs the agent loop; every model call and tool call is an activity whose result is recorded, so crashes resume without redoing work.'
  - 'Each step calls the model through the gateway (budgets, retries, caching).'
  - 'Tool calls (shell, file edits, tests) run in a fresh microVM sandbox holding a clone of the repository and no secrets.'
  - All network traffic leaves through an egress proxy that allows package registries and nothing else by default.
  - Pushing goes through a git proxy that checks the branch and attaches the real credential outside the sandbox.
  - 'The result is checked: tests must pass, and a human reviews the diff.'
  - Only then is a pull request opened or merged.
:::

<!-- slide id="s-flow" chapter="Walkthrough" tag="4 · Walkthrough" tagclass="b4" -->
## One task, step by step

::: cards grid2
### [f] 1. Set up
Start a workflow; restore a warm microVM snapshot with the repository cloned and dependencies cached (Firecracker boots in under 125 ms).

### [a] 2. Explore and plan
Read the issue, search the code, run the failing test; the model plans in its reasoning.

### [c] 3. Edit and test
Loop: edit files, run tests, read results; each tool call is a recorded activity, so a crash resumes at the last step.

### [e] 4. Verify and hand off
Full test suite, lint, a short summary of the change; push through the git proxy; a human reviews the pull request.
:::

<!-- slide id="s-deep" chapter="Deep dive" tag="5 · Deep dive" tagclass="b5" -->
## Deep dive: the sandbox boundary

::: cards grid2
### [d] Two boundaries
Filesystem limited to the task's workspace; network only through a proxy with an allowlist (package registries). Anthropic's point: without both, a compromised agent can exfiltrate keys or escape.

### [b] No secrets inside
The git proxy checks that a push targets the task's branch and attaches the real token outside the sandbox, as in Claude Code on the web.

### [c] Isolation strength
Untrusted code from many customers calls for microVMs (Firecracker: under 5 MiB overhead, up to 150 microVMs per second per host) or gVisor, not plain containers.

### [e] Fresh per task
A new sandbox for every task, destroyed afterwards; warm pools and snapshots hide start-up time.
:::

<!-- slide id="s-scale" chapter="Scaling" tag="6 · Scaling" tagclass="b6" -->
## What breaks at 10×

::: table
| Bottleneck | Symptom | Response |
|---|---|---|
| Model rate limits | 429s during peaks; tasks stall | gateway queues and backoff; spread across model deployments; prompt caching (cached reads do not count toward Anthropic's input limits) |
| Context growth | cost per task rises with steps | compaction, concise tool outputs, subagents with separate contexts |
| Sandbox capacity | tasks wait for environments | warm pools sized to peak, snapshot restore, per-tenant quotas |
| Test time | slow suites dominate wall-clock | run the relevant tests first, full suite once at the end, test result caching |
| Review queue | pull requests pile up | auto-approve only low-risk classes with strong tests; prioritise by confidence |
:::

<!-- slide id="s-fail" chapter="Failures" tag="7 · Failures and operations" tagclass="b7" -->
## Failures and operations

::: cards grid2
### [d] Agent stuck or looping
Step, token and time budgets per task; repeated-action detection; the task ends with a report instead of burning budget.

### [b] Infrastructure failure
Durable execution replays the recorded history on another worker and continues from the last completed step.

### [c] Wrong but passing
Tests can be weak; review the diff, add hidden checks, and track post-merge reverts.

### [a] Measure
Resolved rate, pass^k on a fixed task set (consistency, not one lucky run), cost and time per resolved task, revert rate.
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="8 · Trade-offs" tagclass="b8" -->
## Trade-offs and alternatives

::: table
| Decision | Chosen | Alternative | Why |
|---|---|---|---|
| Isolation | microVM per task | containers | untrusted multi-tenant code; kernel exploits must not cross tasks |
| Execution | durable workflow engine | in-process loop | tasks run for many minutes; deploys and crashes must not lose work |
| Autonomy | human review before merge | auto-merge on green tests | tests miss intent; reversible but costly mistakes |
| Agents | single agent with tools | multi-agent orchestration | multi-agent costs about 15× chat tokens; use it for broad parallel research, not most fixes |
| Evaluation | tests + pass^k + review | single-run success rate | agents are stochastic; consistency matters for trust |
:::

<!-- slide id="s-sum" chapter="Summary" tag="9 · Summary" tagclass="b9" -->
## Summary

::: cards grid2
### [a] Durable loop
Every model and tool call is a recorded step; failures resume, not restart.

### [d] Sandboxed, secret-free
MicroVM per task, egress allowlist, credentials added by proxies outside.

### [c] Verified and reviewed
Tests, pass^k and human review gate every change.

### [e] Read more
Full design document: [design.html](design.html). Related decks: [Sandboxing](../../agent-infra/04-sandboxing/index.html), [Durable workflows](../../agent-systems/03-durable-workflows/index.html), [Cost and latency](../../agent-operations/03-cost-and-latency/index.html), [Evaluating agents](../../agent-operations/01-evaluating-agents/index.html).
:::

<!-- slide id="s-papers" from="papers" -->
