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
papers:
- lg_persistence
- lg_interrupts
- lg_streaming
- lc_middleware
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Visual Agents · Frameworks · 03</div>
    <h1>LangGraph in production</h1>
    <p class="sub">What a checkpointer adds: per-thread memory, human-in-the-loop with interrupt and resume, recovery from failures without redoing finished steps, history and time travel, plus retries, durability modes and streaming.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Production agents run for minutes or hours, wait for people, call flaky services, crash halfway and must remember each user's conversation. A process-local loop loses all of that on the first restart.</div>
      <div class="c"><b>Core idea</b>Compile the graph with a <b>checkpointer</b>: state is saved after every super-step under a <b>thread_id</b>. That one mechanism gives <b>memory</b> (continue a thread), <b>human-in-the-loop</b> (<b>interrupt()</b> pauses, <b>Command(resume=...)</b> continues), <b>fault tolerance</b> (re-invoke with no input to resume from the last checkpoint) and <b>history</b> (inspect, replay or fork earlier states). Add <b>retry policies</b> per node and choose a <b>durability mode</b>.</div>
    </div>
    <div class="toc" data-auto></div>
    <p class="start-hint">Previous: <a href="../02-langgraph-core/index.html">LangGraph core</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

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

<div class="visual dgm" data-steps="[&quot;The client invokes the graph with a thread_id in the config.&quot;, &quot;The runtime loads the thread&#x27;s latest checkpoint (if any) and runs super-steps.&quot;, &quot;After each step the state is saved: in development InMemorySaver, in production a durable backend such as Postgres.&quot;, &quot;Nodes can read and write a store for memory that spans threads (e.g. per-user facts).&quot;, &quot;An interrupt pauses the run; the paused state sits in the checkpointer until a person (or system) resumes it, possibly much later and on another worker.&quot;, &quot;Streaming and traces expose progress and every step for debugging.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 300" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah4" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="1"><line x1="142.0" y1="148.0" x2="176.0" y2="148.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah4)"/></g><g data-step="3"><line x1="342.0" y1="117.1" x2="440.2" y2="80.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah4)"/></g><g data-step="4"><line x1="342.0" y1="148.0" x2="396.0" y2="148.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah4)"/></g><g data-step="5"><line x1="342.0" y1="180.5" x2="444.2" y2="221.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah4)"/></g><g data-step="5"><line x1="445.6" y1="232.3" x2="340.3" y2="190.6" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah4)"/></g><g data-step="6"><line x1="260.0" y1="188.0" x2="260.0" y2="236.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah4)"/></g><g data-step="1"><rect x="10" y="120" width="130" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="75.0" y="146.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Client</text><text x="75.0" y="162.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">thread_id</text></g><g data-step="2"><rect x="180" y="110" width="160" height="76" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="260.0" y="146.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Graph runtime</text><text x="260.0" y="162.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">super-steps</text></g><g data-step="3"><rect x="400" y="20" width="250" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="525.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Checkpointer</text><text x="525.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">state per thread, per step</text></g><g data-step="4"><rect x="400" y="120" width="250" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="525.0" y="146.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Store</text><text x="525.0" y="162.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">cross-thread memory</text></g><g data-step="5"><rect x="400" y="225" width="250" height="56" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="525.0" y="251.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Human reviewer</text><text x="525.0" y="267.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">approve · edit · reject</text></g><g data-step="6"><rect x="180" y="240" width="160" height="50" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="260.0" y="263.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Traces</text><text x="260.0" y="279.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">stream / logs</text></g><g data-step="1"><text x="159.0" y="143.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">invoke(input, config)</text></g><g data-step="3"><text x="391.1" y="93.5" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">save after each step</text></g><g data-step="4"><text x="369.0" y="143.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">read / write</text></g><g data-step="5"><text x="393.1" y="195.7" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">interrupt</text></g><g data-step="5"><text x="393.0" y="226.4" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">resume</text></g></svg><p class="readout dgcap"></p></div>

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Interrupt, resume, recover

<div class="visual dgm" data-steps="[&quot;A node decides what to do, e.g. delete a branch.&quot;, &quot;The approval node calls interrupt() with a JSON-serialisable payload describing the action.&quot;, &quot;The run stops and returns the payload under __interrupt__; get_state(...).next shows the paused node. A checkpointer and thread_id are required.&quot;, &quot;Resuming with Command(resume=value) restarts the whole approve node from the top; this time interrupt() returns value instead of pausing.&quot;, &quot;So side effects belong after the interrupt or in a later node, or they run twice. Do not wrap interrupt() in a bare try/except: it works by raising.&quot;, &quot;If a node crashes, the earlier steps are already checkpointed: invoking the same thread with None retries from the failed step only.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 240" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah5" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="152.0" y1="48.0" x2="186.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah5)"/></g><g data-step="3"><line x1="352.0" y1="48.0" x2="396.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah5)"/></g><g data-step="4"><line x1="525.0" y1="78.0" x2="525.0" y2="146.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah5)"/></g><g data-step="5"><line x1="398.0" y1="178.0" x2="324.0" y2="178.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah5)"/></g><g data-step="6"><line x1="168.0" y1="178.0" x2="144.0" y2="178.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah5)"/></g><g data-step="1"><rect x="10" y="20" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="80.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">plan</text><text x="80.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">choose action</text></g><g data-step="2"><rect x="190" y="20" width="160" height="56" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="270.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">approve</text><text x="270.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">interrupt({...})</text></g><g data-step="3"><rect x="400" y="20" width="250" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="525.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Paused</text><text x="525.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">checkpoint saved, run returns</text></g><g data-step="4"><rect x="400" y="150" width="250" height="56" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="525.0" y="176.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Command(resume=True)</text><text x="525.0" y="192.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">node re-runs from its start</text></g><g data-step="5"><rect x="170" y="150" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="245.0" y="176.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">execute</text><text x="245.0" y="192.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">side effect here</text></g><g data-step="6"><rect x="10" y="150" width="130" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="75.0" y="176.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Failure?</text><text x="75.0" y="192.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">invoke(None, config)</text></g><g data-step="4"><text x="525.0" y="107.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">later</text></g><g data-step="5"><text x="361.0" y="173.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">approved</text></g></svg><p class="readout dgcap"></p></div>

<div class="visual scroll-x"><table class="tbl"><tr><th>Setting</th><th>1.2.15 behaviour</th></tr><tr><td>RetryPolicy defaults</td><td>max_attempts 3 (including the first), initial_interval 0.5 s, backoff_factor 2, max_interval 128 s, jitter on</td></tr><tr><td>Default retry_on</td><td>retries ConnectionError and HTTP 5xx errors; does not retry ValueError, TypeError, RuntimeError, LookupError and other programming errors</td></tr><tr><td>durability</td><td>"sync": persist before the next step; "async": persist while the next step runs; "exit": persist only when the graph exits</td></tr><tr><td>Multiple interrupts</td><td>resume values match interrupts by position: keep their order stable between runs</td></tr></table></div>

<div class="visual" style="display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;background:var(--e-soft);border-color:var(--e)"><div><b>🛠 Try it in Colab</b><p class="caption" style="margin:4px 0 0">Per-thread memory with a checkpointer, an approval step with interrupt() that never runs the side effect twice, and resuming a failed run without repeating finished steps. Runs with a scripted fake model: no API key needed.</p></div><a class="btn primary" href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/agent-frameworks/03_langgraph_production.ipynb" target="_blank" rel="noopener">Open notebook →</a></div>

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

<div class="visual scroll-x"><table class="tbl"><tr><th>Choice</th><th>Benefit</th><th>Cost</th></tr><tr><td>durability "sync"</td><td>nothing lost on a crash</td><td>a write on the critical path of every step</td></tr><tr><td>durability "async" / "exit"</td><td>lower latency</td><td>recent steps (or the whole run) can be lost on a crash</td></tr><tr><td>Interrupt for approval</td><td>safe consequential actions; edits by humans</td><td>latency; UI and notification plumbing</td></tr><tr><td>Approval via middleware</td><td>HumanInTheLoopMiddleware adds it to create_agent with configuration</td><td>less control than a custom node</td></tr><tr><td>Graph checkpoints vs a workflow engine</td><td>agent-native state and replay</td><td>a dedicated durable-execution engine offers more scheduling and operations tooling</td></tr></table></div>

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

<div class="visual scroll-x"><table class="tbl"><tr><th>Failure</th><th>Symptom</th><th>Mitigation</th></tr><tr><td>Side effect before interrupt</td><td>email sent twice after approval</td><td>side effects after the interrupt or in a separate node; idempotency keys</td></tr><tr><td>Wrong thread_id</td><td>a user sees another conversation, or memory "forgets"</td><td>derive thread ids from authenticated identity; never from user input alone</td></tr><tr><td>InMemorySaver in production</td><td>all paused runs lost on deploy</td><td>a durable checkpointer (e.g. Postgres) with backups</td></tr><tr><td>Retrying non-idempotent nodes</td><td>duplicate payments or tickets</td><td>retry only idempotent work; keys on external calls</td></tr><tr><td>Unbounded checkpoint growth</td><td>storage grows with every step of every thread</td><td>retention policies; prune old threads</td></tr></table></div>

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
