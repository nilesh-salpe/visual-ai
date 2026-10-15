---
title: Durable Workflows for Agents
body:
  data-deck: Durable workflows for agents
  data-home: ../index.html
  data-home-label: Systems
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
- ../../shared/diagram.js
intro:
  kicker: Visual Agents · Systems · 03
  h1: Durable workflows for agents
  sub: 'Keeping long-running agents alive through crashes, deploys and days-long waits: durable execution with Temporal (event history, replay, activities), compared
    with LangGraph checkpoints and with DAG schedulers such as Airflow and Argo.'
  problem: An agent task can run for hours, call dozens of flaky services and wait days for a human. Process memory dies with a crash or a deploy; hand-written retry
    and resume logic for every step is error-prone and usually wrong.
  core: 'Use <b>durable execution</b>: write the agent as ordinary code, but run every side effect (LLM calls, tools, APIs) as an <b>activity</b> whose result is
    recorded in an <b>event history</b>. After a crash, a worker <b>replays</b> the workflow code against the history to rebuild its state and continues; finished
    activities are not re-run. Workflow code must therefore be <b>deterministic</b>. Use <b>DAG schedulers</b> (Airflow, Argo) for batch pipelines, not interactive
    agents.'
  hint: 'Previous: [Computer and browser use](../02-computer-use/index.html) · [All decks](../index.html)'
papers:
- temporal_workflows
- temporal_retries
- temporal_limits
- lg_persistence
- airflow
- argo
---

<!-- slide from="title" -->

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Agents outlive the processes that run them

::: cards grid3
### [d] Crashes and deploys
A restart loses in-memory progress; re-running from the start repeats paid LLM calls and side effects.

### [b] Flaky dependencies
Each tool and API fails sometimes; retries with backoff and timeouts are needed everywhere.

### [c] Long waits
Approvals and external events can take days; a process cannot sleep that long reliably.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Record every effect, replay the code

::: cards grid2
### [f] Workflow
The orchestration code. It must make the same decisions given the same history; use the SDK's replay-safe time, timers and randomness.

### [a] Activity
Anything that touches the outside world: LLM calls, tools, databases. Its result is recorded once and reused on replay.

### [c] Event history
The source of truth for a run. Temporal "doesn't restore memory from a snapshot": it re-runs the code and feeds it the recorded results.

### [e] Signals and timers
Send input to a running workflow (an approval) or sleep for days without holding a process.
:::

::: table
| Temporal default | Value |
|---|---|
| Activity retries: initial interval | 1 second |
| Backoff coefficient | 2.0 |
| Maximum interval | 100 × initial interval |
| Maximum attempts | unlimited (until success, cancellation or timeout) |
| Workflow retries | none unless you set a retry policy |
| Event history limit | warns at 10,240 events or 10 MB; limited to 51,200 events or 50 MB |
:::

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## Durable execution architecture

::: diagram 660x300
nodes:
  cl: {at: [10, 120, 120, 56], text: Client / UI, sub: start · signal, color: f, step: 1}
  ts: {at: [180, 110, 170, 76], text: Temporal service, sub: event history · queues, color: a, step: 2}
  wk: {at: [410, 110, 240, 76], text: Workers, sub: run workflow + activity code, color: c, step: 3}
  llm: {at: [410, 10, 110, 56], text: LLM API, color: b, step: 4}
  tl: {at: [540, 10, 110, 56], text: Tools / APIs, color: b, step: 4}
  db: {at: [180, 235, 170, 56], text: Persistence, sub: histories survive, color: e, step: 2}
  hu: {at: [410, 235, 240, 56], text: Human reviewer, sub: approve via signal, color: d, step: 5}
edges:
  - {from: cl, to: ts, step: 1}
  - {from: ts, to: db, step: 2}
  - {from: ts, to: wk, label: tasks, step: 3}
  - {from: wk, to: ts, label: commands · results, step: 3, style: back}
  - {from: wk, to: llm, label: activity, step: 4}
  - {from: wk, to: tl, label: activity, step: 4}
  - {from: hu, to: ts, label: signal, step: 5, style: dash}
steps:
  - A client starts a workflow (e.g. "fix this issue") and can later send it signals or query it.
  - The Temporal service stores each workflow's event history durably and dispatches work through task queues.
  - 'Stateless workers poll for tasks, run workflow code, and report commands and results back; any worker can continue any workflow.'
  - LLM calls and tool calls run as activities with timeouts and retry policies.
  - 'A human answers by sending a signal; the waiting workflow resumes, days later if needed.'
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Replay after a crash

::: diagram 660x300
nodes:
  h: {at: [10, 20, 300, 56], text: Event history, sub: started · activity done ×3 · ..., color: e, step: 1}
  cr: {at: [360, 20, 290, 56], text: Worker crashes, sub: mid-task, color: d, step: 2}
  w2: {at: [360, 140, 290, 56], text: New worker replays code, sub: recorded results fed back, color: a, step: 3}
  sk: {at: [10, 140, 250, 56], text: Finished activities, sub: not called again, color: c, step: 4}
  nx: {at: [10, 240, 250, 50], text: Next activity runs for real, color: b, step: 5}
  nd: {at: [360, 240, 290, 50], text: Non-determinism error, sub: if code diverges, color: d, step: 6}
edges:
  - {from: h, to: cr, step: 2}
  - {from: cr, to: w2, step: 3}
  - {from: w2, to: sk, label: same decisions, step: 4}
  - {from: sk, to: nx, step: 5}
  - {from: w2, to: nd, label: different decision, step: 6, style: dash}
steps:
  - 'The history records each step: workflow started, activity scheduled, activity completed with its result.'
  - The worker dies halfway through a task.
  - Another worker picks the workflow up and re-runs its code from the beginning.
  - 'Where the code schedules an activity that already completed, the recorded result is returned instead of calling the LLM or tool again.'
  - 'Replay reaches the point of the crash, and the next activity executes for real.'
  - 'If the code makes a different decision on replay (wall-clock time, randomness, changed code), Temporal raises a non-determinism error: version your workflow changes.'
:::



::: code
from datetime import timedelta
from temporalio import activity, workflow

@activity.defn
async def call_llm(prompt: str) -> str: ...     # network I/O: an activity, retried on failure

@activity.defn
async def run_tool(plan: str) -> str: ...

@workflow.defn
class AgentWorkflow:
    def __init__(self) -> None:
        self.approved: bool | None = None

    @workflow.signal
    def approve(self, ok: bool) -> None:         # a person answers, maybe days later
        self.approved = ok

    @workflow.run
    async def run(self, task: str) -> str:
        plan = await workflow.execute_activity(call_llm, task, start_to_close_timeout=timedelta(minutes=2))
        await workflow.wait_condition(lambda: self.approved is not None)   # no process is held while waiting
        if not self.approved:
            return "cancelled"
        return await workflow.execute_activity(run_tool, plan, start_to_close_timeout=timedelta(minutes=10))
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Which engine for which job

::: table
| Engine | Model | Best for | Less suited to |
|---|---|---|---|
| Temporal | durable execution: code + event history + replay | long-running, interactive, reliable agent and business processes | simple scheduled batch jobs |
| LangGraph checkpoints | state saved after each graph step, per thread | agent-native state, interrupts and replay inside one framework | cross-service orchestration with its own scheduling and operations tooling |
| Apache Airflow (3.x) | Python-defined DAGs of tasks, scheduled | batch data and ML pipelines with a clear start and end | interactive, low-latency, event-by-event agent loops |
| Argo Workflows | Kubernetes CRD; each step a container, steps or DAG | machine-learning pipelines, batch processing, continuous integration and delivery on Kubernetes | fine-grained in-process steps such as single LLM calls |
| Plain queue + database | your own state machine | very simple flows | everything above, rebuilt by hand |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Non-deterministic workflow code | replay fails after a crash or deploy | side effects, time and randomness only through activities and SDK APIs; version changes |
| Non-idempotent activities | a retried tool call books twice | idempotency keys; activities that check before acting |
| Huge histories | warnings past 10,240 events; hard stop at 51,200 | Continue-As-New to start a fresh run with carried-over state; keep big payloads out of history |
| Unbounded retries | an activity retries forever on a permanent error | mark non-retryable error types; set maximum attempts or timeouts |
| LLM output in history | large prompts and responses bloat and expose data | store blobs externally and record references; encrypt payloads |
:::

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Activities for every effect
Every LLM and tool call is an activity with a timeout and a retry policy chosen for that call.

### [c] Versioning
Deploys change code that running workflows will replay: use the SDK's versioning so old runs follow old paths.

### [b] Visibility
Search workflows by status and attributes; alert on stuck or failing runs.

### [e] Pick per job
Agents and interactive processes on durable execution; nightly data and training pipelines on Airflow or Argo.
:::

<!-- slide id="s-papers" from="papers" -->
