---
title: What an Agent Is
body:
  data-deck: What an agent is
  data-home: ../index.html
  data-home-label: Foundations
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
papers:
- bea
- react
- toolformer
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Visual Agents · Foundations · 01</div>
    <h1>What an agent is</h1>
    <p class="sub">The difference between a single LLM call, a workflow and an agent, and the loop every agent shares: decide, act, observe, repeat.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>A single model call cannot look anything up, take actions, or adapt when a step fails. Real tasks need several steps whose number and order are not known in advance.</div>
      <div class="c"><b>Core idea</b>An <b>agent</b> is an LLM that <b>directs its own process</b>: in a loop it chooses a tool call, the application executes it, the result is fed back, and it decides what to do next until it can answer. A <b>workflow</b> orchestrates LLM calls through <b>predefined code paths</b>. Start with the simplest option that works.</div>
    </div>
    <div class="toc" data-auto></div>
    <p class="start-hint">Next: <a href="../02-tool-calling/index.html">Tool calling →</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## One call is not enough

Ask "Which of our three cloud regions had the most failed deployments last week, and open a ticket for it?" A single LLM call has to guess: it has no data, cannot query anything, and cannot act.
            {: .lede}

::: cards grid3
### [d] No access
Facts live in databases, APIs and documents outside the model.

### [b] No actions
Creating a ticket, running code or sending a message requires calling a system.

### [c] No adaptation
If a query fails or returns surprising data, a single call cannot react and try something else.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## An LLM in a loop

Anthropic's distinction: <b>workflows</b> are systems where LLMs and tools are orchestrated through predefined code paths; <b>agents</b> are systems where LLMs dynamically direct their own processes and tool usage.
            {: .lede}

::: cards grid2
### [f] Augmented LLM
The building block: an LLM with retrieval, tools and memory available.

### [a] Workflow
Your code decides the steps: chain, route, parallelise, evaluate-and-revise.

### [e] Agent
The model decides the steps: call a tool, read the result, decide again, until done or stopped.

### [d] Rule of thumb
"Find the simplest solution possible, and only increase complexity when needed." Agents trade latency and cost for task performance.
:::

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## The agent loop

<div class="visual dgm" data-steps="[&quot;The user states a goal, not a step-by-step procedure.&quot;, &quot;The agent loop is an LLM call wrapped in code that keeps going while the model asks for tools.&quot;, &quot;The model picks a tool and arguments; the application executes the call.&quot;, &quot;The tool acts on the environment; the observation (result or error) goes back into the context.&quot;, &quot;Memory keeps what matters across steps: the conversation, notes, retrieved facts.&quot;, &quot;When the model stops asking for tools, its final message goes back to the user.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 300" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="1"><line x1="132.0" y1="148.0" x2="196.0" y2="148.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah1)"/></g><g data-step="3"><line x1="352.0" y1="121.8" x2="446.0" y2="89.9" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah1)"/></g><g data-step="4"><line x1="540.0" y1="88.0" x2="540.0" y2="126.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah1)"/></g><g data-step="4"><line x1="447.6" y1="164.5" x2="353.6" y2="161.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah1)"/></g><g data-step="5"><line x1="352.0" y1="179.1" x2="468.2" y2="226.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah1)"/></g><g data-step="6"><line x1="198.0" y1="158.0" x2="134.0" y2="158.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah1)"/></g><g data-step="1"><rect x="20" y="120" width="110" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="75.0" y="146.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">User</text><text x="75.0" y="162.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">goal</text></g><g data-step="2"><rect x="200" y="110" width="150" height="76" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="275.0" y="146.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Agent loop</text><text x="275.0" y="162.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">LLM decides</text></g><g data-step="3"><rect x="450" y="30" width="180" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="540.0" y="56.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Tools</text><text x="540.0" y="72.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">search · code · APIs</text></g><g data-step="4"><rect x="450" y="130" width="180" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="540.0" y="156.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Environment</text><text x="540.0" y="172.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">files · web · systems</text></g><g data-step="5"><rect x="450" y="230" width="180" height="50" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="540.0" y="253.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Memory</text><text x="540.0" y="269.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">context · notes</text></g><g data-step="1"><text x="164.0" y="143.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">task</text></g><g data-step="3"><text x="399.0" y="100.9" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">tool call</text></g><g data-step="4"><text x="540.0" y="102.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">acts on</text></g><g data-step="4"><text x="400.6" y="177.7" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">observation</text></g><g data-step="5"><text x="410.1" y="197.5" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">read / write</text></g><g data-step="6"><text x="166.0" y="173.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">answer</text></g></svg><p class="readout dgcap"></p></div>

::: cards grid3
### [a] Decide
The LLM reads the goal and everything so far and picks the next action.

### [c] Act
Your code runs the tool with the model's arguments.

### [b] Observe
The result, including errors, is appended to the context for the next decision.
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Inside one loop iteration

<div class="visual dgm" data-steps="[&quot;Assemble the request: system prompt, tool definitions and the conversation so far.&quot;, &quot;Call the model.&quot;, &quot;Check why it stopped. With Anthropic&#x27;s API a tool request comes back as stop_reason \&quot;tool_use\&quot; with tool_use blocks.&quot;, &quot;Validate arguments, then run each requested tool with a timeout.&quot;, &quot;Send each result back as a tool_result block that references the tool_use id.&quot;, &quot;Before looping, enforce limits: maximum iterations, token or cost budget, wall-clock time.&quot;, &quot;If the model ended its turn without tool calls, its text is the answer.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 230" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="162.0" y1="48.0" x2="186.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah2)"/></g><g data-step="3"><line x1="342.0" y1="48.0" x2="366.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah2)"/></g><g data-step="4"><line x1="445.0" y1="78.0" x2="445.0" y2="146.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah2)"/></g><g data-step="5"><line x1="368.0" y1="178.0" x2="344.0" y2="178.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah2)"/></g><g data-step="6"><line x1="188.0" y1="178.0" x2="164.0" y2="178.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah2)"/></g><g data-step="6"><line x1="85.0" y1="148.0" x2="85.0" y2="80.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah2)"/></g><g data-step="7"><line x1="522.0" y1="48.0" x2="546.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah2)"/></g><g data-step="1"><rect x="10" y="20" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="85.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Build context</text><text x="85.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">system · tools · history</text></g><g data-step="2"><rect x="190" y="20" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="265.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Model call</text><text x="265.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">messages API</text></g><g data-step="3"><rect x="370" y="20" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="445.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Stop reason?</text><text x="445.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">tool_use / end_turn</text></g><g data-step="4"><rect x="370" y="150" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="445.0" y="176.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Execute tools</text><text x="445.0" y="192.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">validate · run · time out</text></g><g data-step="5"><rect x="190" y="150" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="265.0" y="176.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Append results</text><text x="265.0" y="192.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">tool_result blocks</text></g><g data-step="6"><rect x="10" y="150" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="85.0" y="176.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Guards</text><text x="85.0" y="192.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">max steps · budget</text></g><g data-step="7"><rect x="550" y="20" width="100" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="600.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Answer</text><text x="600.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">return text</text></g><g data-step="4"><text x="445.0" y="107.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">tool_use</text></g><g data-step="6"><text x="85.0" y="109.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">continue</text></g><g data-step="7"><text x="534.0" y="43.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">end_turn</text></g></svg><p class="readout dgcap"></p></div>

<div class="visual"><pre style="margin:0;font:13px/1.55 'JetBrains Mono',monospace;white-space:pre-wrap">messages = [user_goal]&#10;for step in range(MAX_STEPS):&#10;    resp = llm(system, tools, messages)&#10;    messages.append(resp)&#10;    if resp.stop_reason != "tool_use":&#10;        return resp.text&#10;    messages.append(run_tools(resp.tool_calls))   # results, including errors&#10;raise StepLimitExceeded</pre></div>

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Workflow or agent?

<div class="visual scroll-x"><table class="tbl"><tr><th>Option</th><th>You gain</th><th>You pay</th><th>Choose when</th></tr><tr><td>Single LLM call (+ retrieval)</td><td>cheapest, fastest, predictable</td><td>no actions, no adaptation</td><td>the answer needs only text in the prompt</td></tr><tr><td>Workflow (chain, route, parallelise)</td><td>predictable steps, easy to test</td><td>breaks on inputs the code did not anticipate</td><td>the steps are known in advance</td></tr><tr><td>Agent (model-directed loop)</td><td>handles open-ended tasks and surprises</td><td>more latency, cost, variance; harder to test</td><td>the number and order of steps cannot be predicted</td></tr><tr><td>Agent with human checkpoints</td><td>safety on consequential actions</td><td>slower, needs a UI</td><td>actions are costly or irreversible</td></tr></table></div>

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## How agents fail

<div class="visual scroll-x"><table class="tbl"><tr><th>Failure</th><th>What you see</th><th>Mitigation</th></tr><tr><td>Endless or repetitive loops</td><td>the same tool call again and again</td><td>step and budget limits; detect repeated calls</td></tr><tr><td>Compounding errors</td><td>one wrong observation leads to a confident wrong answer</td><td>verify key facts; let the agent re-check</td></tr><tr><td>Malformed tool calls</td><td>invalid arguments, wrong tool</td><td>strict schemas, validation errors returned to the model</td></tr><tr><td>Premature finish</td><td>answers before doing the work</td><td>explicit completion criteria; evaluator step</td></tr><tr><td>Acting on injected instructions</td><td>tool output tells it to do something else</td><td>treat tool output as data; least privilege (Operations deck 02)</td></tr></table></div>

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## Running agents for real

::: cards grid2
### [a] Cost and latency per task
Every iteration re-sends a growing context; Anthropic reports agents use about 4× the tokens of chat (Operations deck 03).

### [c] Observability
Log every step: prompt, tool call, result, timing. Without traces, failures are unexplainable.

### [b] Evaluation
Grade end states over many runs; agents are stochastic (Operations deck 01).

### [d] Permissions
Give tools the minimum access needed; confirm irreversible actions with a human.
:::

<!-- slide id="s-papers" from="papers" -->
