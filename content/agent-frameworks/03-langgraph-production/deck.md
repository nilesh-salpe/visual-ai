---
title: LangGraph in Production
body:
  data-deck: LangGraph in production
  data-home: ../index.html
  data-home-label: Frameworks
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
- ../../shared/diagram.js
intro:
  kicker: Visual Agents · Frameworks · 03
  h1: LangGraph in production
  sub: 'What a checkpointer adds: per-thread memory, human-in-the-loop with interrupt and resume, recovery from failures without redoing finished steps, history and
    time travel, plus retries, durability modes and streaming.'
  problem: Production agents run for minutes or hours, wait for people, call flaky services, crash halfway and must remember each user's conversation. A process-local
    loop loses all of that on the first restart.
  core: 'Compile the graph with a <b>checkpointer</b>: state is saved after every super-step under a <b>thread_id</b>. That one mechanism gives <b>memory</b> (continue
    a thread), <b>human-in-the-loop</b> (<b>interrupt()</b> pauses, <b>Command(resume=...)</b> continues), <b>fault tolerance</b> (re-invoke with no input to resume
    from the last checkpoint) and <b>history</b> (inspect, replay or fork earlier states). Add <b>retry policies</b> per node and choose a <b>durability mode</b>.'
  hint: 'Previous: [LangGraph core](../02-langgraph-core/index.html) · [All decks](../index.html)'
papers:
- lg_persistence
- lg_interrupts
- lg_streaming
- lc_middleware
---

<!-- slide from="title" -->

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Agents outlive processes

::: cards grid3
### [d] Long waits
An approval can take hours; holding a process open for it is fragile.

### [b] Crashes mid-task
Restarting from scratch repeats expensive or non-repeatable steps.

### [c] Many conversations
Each user and thread needs its own state, isolated and resumable.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Checkpoint every step

::: cards grid2
### [f] Threads
config={"configurable": {"thread_id": ...}} selects whose state to load and save.

### [a] Interrupts
interrupt(payload) pauses the run and surfaces the payload under __interrupt__; Command(resume=value) continues, and value becomes interrupt()'s return value.

### [c] Resume after failure
Finished steps stay checkpointed; invoking the same thread with None continues from the failed step.

### [e] History
get_state and get_state_history list every checkpoint, for debugging, replay and forking.
:::

Checkpointers hold thread-scoped state; a separate <b>store</b> holds data shared across threads, such as user preferences and long-term facts.

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## Persistence architecture

::: diagram 660x300
nodes:
  cl: {at: [10, 120, 130, 56], text: Client, sub: thread_id, color: f, step: 1}
  rt: {at: [180, 110, 160, 76], text: Graph runtime, sub: super-steps, color: a, step: 2}
  cp: {at: [400, 20, 250, 56], text: Checkpointer, sub: 'state per thread, per step', color: e, step: 3}
  st: {at: [400, 120, 250, 56], text: Store, sub: cross-thread memory, color: b, step: 4}
  hu: {at: [400, 225, 250, 56], text: Human reviewer, sub: approve · edit · reject, color: d, step: 5}
  lg: {at: [180, 240, 160, 50], text: Traces, sub: stream / logs, color: c, step: 6}
edges:
  - {from: cl, to: rt, label: 'invoke(input, config)', step: 1}
  - {from: rt, to: cp, label: save after each step, step: 3}
  - {from: rt, to: st, label: read / write, step: 4, style: dash}
  - {from: rt, to: hu, label: interrupt, step: 5}
  - {from: hu, to: rt, label: resume, step: 5, style: back}
  - {from: rt, to: lg, step: 6, style: dash}
steps:
  - The client invokes the graph with a thread_id in the config.
  - The runtime loads the thread's latest checkpoint (if any) and runs super-steps.
  - 'After each step the state is saved: in development InMemorySaver, in production a durable backend such as Postgres.'
  - Nodes can read and write a store for memory that spans threads (e.g. per-user facts).
  - 'An interrupt pauses the run; the paused state sits in the checkpointer until a person (or system) resumes it, possibly much later and on another worker.'
  - Streaming and traces expose progress and every step for debugging.
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Interrupt, resume, recover

::: diagram 660x240
nodes:
  p: {at: [10, 20, 140, 56], text: plan, sub: choose action, color: f, step: 1}
  a: {at: [190, 20, 160, 56], text: approve, sub: 'interrupt({...})', color: d, step: 2}
  ps: {at: [400, 20, 250, 56], text: Paused, sub: 'checkpoint saved, run returns', color: b, step: 3}
  rs: {at: [400, 150, 250, 56], text: Command(resume=True), sub: node re-runs from its start, color: a, step: 4}
  ex: {at: [170, 150, 150, 56], text: execute, sub: side effect here, color: c, step: 5}
  fx: {at: [10, 150, 130, 56], text: 'Failure?', sub: 'invoke(None, config)', color: e, step: 6}
edges:
  - {from: p, to: a, step: 2}
  - {from: a, to: ps, step: 3}
  - {from: ps, to: rs, label: later, step: 4}
  - {from: rs, to: ex, label: approved, step: 5}
  - {from: ex, to: fx, step: 6, style: dash}
steps:
  - 'A node decides what to do, e.g. delete a branch.'
  - The approval node calls interrupt() with a JSON-serialisable payload describing the action.
  - The run stops and returns the payload under __interrupt__; get_state(...).next shows the paused node. A checkpointer and thread_id are required.
  - Resuming with Command(resume=value) restarts the whole approve node from the top; this time interrupt() returns value instead of pausing.
  - 'So side effects belong after the interrupt or in a later node, or they run twice. Do not wrap interrupt() in a bare try/except: it works by raising.'
  - 'If a node crashes, the earlier steps are already checkpointed: invoking the same thread with None retries from the failed step only.'
:::



::: table
| Setting | 1.2.15 behaviour |
|---|---|
| RetryPolicy defaults | max_attempts 3 (including the first), initial_interval 0.5 s, backoff_factor 2, max_interval 128 s, jitter on |
| Default retry_on | retries ConnectionError and HTTP 5xx errors; does not retry ValueError, TypeError, RuntimeError, LookupError and other programming errors |
| durability | "sync": persist before the next step; "async": persist while the next step runs; "exit": persist only when the graph exits |
| Multiple interrupts | resume values match interrupts by position: keep their order stable between runs |
:::



::: colab build-it/agent-frameworks/03_langgraph_production.ipynb
Per-thread memory with a checkpointer, an approval step with interrupt() that never runs the side effect twice, and resuming a failed run without repeating finished steps. Runs with a scripted fake model: no API key needed.
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

::: table
| Choice | Benefit | Cost |
|---|---|---|
| durability "sync" | nothing lost on a crash | a write on the critical path of every step |
| durability "async" / "exit" | lower latency | recent steps (or the whole run) can be lost on a crash |
| Interrupt for approval | safe consequential actions; edits by humans | latency; UI and notification plumbing |
| Approval via middleware | HumanInTheLoopMiddleware adds it to create_agent with configuration | less control than a custom node |
| Graph checkpoints vs a workflow engine | agent-native state and replay | a dedicated durable-execution engine offers more scheduling and operations tooling |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Side effect before interrupt | email sent twice after approval | side effects after the interrupt or in a separate node; idempotency keys |
| Wrong thread_id | a user sees another conversation, or memory "forgets" | derive thread ids from authenticated identity; never from user input alone |
| InMemorySaver in production | all paused runs lost on deploy | a durable checkpointer (e.g. Postgres) with backups |
| Retrying non-idempotent nodes | duplicate payments or tickets | retry only idempotent work; keys on external calls |
| Unbounded checkpoint growth | storage grows with every step of every thread | retention policies; prune old threads |
:::

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Idempotent nodes
Assume any node can run more than once: after resume, retry or replay.

### [c] Serializable state
Keep state and interrupt payloads JSON-serialisable; checkpointers may not store arbitrary objects.

### [b] Workers anywhere
Because state lives in the checkpointer, any worker can resume any thread: scale workers independently.

### [e] Observe pauses
Track how long runs wait on humans and how many are stuck; alert on stale interrupts.
:::

<!-- slide id="s-papers" from="papers" -->
