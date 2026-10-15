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
- ../../shared/diagram.js
intro:
  kicker: Visual Agents · Foundations · 01
  h1: What an agent is
  sub: 'The difference between a single LLM call, a workflow and an agent, and the loop every agent shares: decide, act, observe, repeat.'
  problem: A single model call cannot look anything up, take actions, or adapt when a step fails. Real tasks need several steps whose number and order are not known
    in advance.
  core: 'An <b>agent</b> is an LLM that <b>directs its own process</b>: in a loop it chooses a tool call, the application executes it, the result is fed back, and
    it decides what to do next until it can answer. A <b>workflow</b> orchestrates LLM calls through <b>predefined code paths</b>. Start with the simplest option
    that works.'
  hint: 'Next: [Tool calling →](../02-tool-calling/index.html) · [All decks](../index.html)'
papers:
- bea
- react
- toolformer
---

<!-- slide from="title" -->

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

::: diagram 660x300
nodes:
  u: {at: [20, 120, 110, 56], text: User, sub: goal, color: f, step: 1}
  ag: {at: [200, 110, 150, 76], text: Agent loop, sub: LLM decides, color: a, step: 2}
  t: {at: [450, 30, 180, 56], text: Tools, sub: search · code · APIs, color: c, step: 3}
  env: {at: [450, 130, 180, 56], text: Environment, sub: files · web · systems, color: b, step: 4}
  m: {at: [450, 230, 180, 50], text: Memory, sub: context · notes, color: e, step: 5}
edges:
  - {from: u, to: ag, label: task, step: 1}
  - {from: ag, to: t, label: tool call, step: 3}
  - {from: t, to: env, label: acts on, step: 4}
  - {from: env, to: ag, label: observation, step: 4, style: back}
  - {from: ag, to: m, label: read / write, step: 5}
  - {from: ag, to: u, label: answer, step: 6, style: back}
steps:
  - 'The user states a goal, not a step-by-step procedure.'
  - The agent loop is an LLM call wrapped in code that keeps going while the model asks for tools.
  - The model picks a tool and arguments; the application executes the call.
  - The tool acts on the environment; the observation (result or error) goes back into the context.
  - 'Memory keeps what matters across steps: the conversation, notes, retrieved facts.'
  - 'When the model stops asking for tools, its final message goes back to the user.'
:::

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

::: diagram 660x230
nodes:
  ctx: {at: [10, 20, 150, 56], text: Build context, sub: system · tools · history, color: f, step: 1}
  call: {at: [190, 20, 150, 56], text: Model call, sub: messages API, color: a, step: 2}
  dec: {at: [370, 20, 150, 56], text: 'Stop reason?', sub: tool_use / end_turn, color: d, step: 3}
  exe: {at: [370, 150, 150, 56], text: Execute tools, sub: validate · run · time out, color: c, step: 4}
  app: {at: [190, 150, 150, 56], text: Append results, sub: tool_result blocks, color: b, step: 5}
  guard: {at: [10, 150, 150, 56], text: Guards, sub: max steps · budget, color: d, step: 6}
  done: {at: [550, 20, 100, 56], text: Answer, sub: return text, color: e, step: 7}
edges:
  - {from: ctx, to: call, step: 2}
  - {from: call, to: dec, step: 3}
  - {from: dec, to: exe, label: tool_use, step: 4}
  - {from: exe, to: app, step: 5}
  - {from: app, to: guard, step: 6}
  - {from: guard, to: ctx, label: continue, step: 6}
  - {from: dec, to: done, label: end_turn, step: 7, style: dash}
steps:
  - 'Assemble the request: system prompt, tool definitions and the conversation so far.'
  - Call the model.
  - Check why it stopped. With Anthropic's API a tool request comes back as stop_reason "tool_use" with tool_use blocks.
  - 'Validate arguments, then run each requested tool with a timeout.'
  - Send each result back as a tool_result block that references the tool_use id.
  - 'Before looping, enforce limits: maximum iterations, token or cost budget, wall-clock time.'
  - 'If the model ended its turn without tool calls, its text is the answer.'
:::



::: code
messages = [user_goal]
for step in range(MAX_STEPS):
    resp = llm(system, tools, messages)
    messages.append(resp)
    if resp.stop_reason != "tool_use":
        return resp.text
    messages.append(run_tools(resp.tool_calls))   # results, including errors
raise StepLimitExceeded
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Workflow or agent?

::: table
| Option | You gain | You pay | Choose when |
|---|---|---|---|
| Single LLM call (+ retrieval) | cheapest, fastest, predictable | no actions, no adaptation | the answer needs only text in the prompt |
| Workflow (chain, route, parallelise) | predictable steps, easy to test | breaks on inputs the code did not anticipate | the steps are known in advance |
| Agent (model-directed loop) | handles open-ended tasks and surprises | more latency, cost, variance; harder to test | the number and order of steps cannot be predicted |
| Agent with human checkpoints | safety on consequential actions | slower, needs a UI | actions are costly or irreversible |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## How agents fail

::: table
| Failure | What you see | Mitigation |
|---|---|---|
| Endless or repetitive loops | the same tool call again and again | step and budget limits; detect repeated calls |
| Compounding errors | one wrong observation leads to a confident wrong answer | verify key facts; let the agent re-check |
| Malformed tool calls | invalid arguments, wrong tool | strict schemas, validation errors returned to the model |
| Premature finish | answers before doing the work | explicit completion criteria; evaluator step |
| Acting on injected instructions | tool output tells it to do something else | treat tool output as data; least privilege (Operations deck 02) |
:::

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
