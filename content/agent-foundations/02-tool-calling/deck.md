---
title: Tool Calling
body:
  data-deck: Tool calling
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
  kicker: Visual Agents · Foundations · 02
  h1: Tool calling
  sub: 'How a model asks your code to run a function: tool definitions with JSON schemas, structured tool-use outputs, executing and returning results, parallel calls
    and tool choice.'
  problem: Free-text instructions like "now call the weather API for Paris" are hard to parse reliably, and the model has no way to see a function's result unless
    you feed it back.
  core: Describe each tool with a <b>name, description and JSON schema</b>. The model returns a <b>structured call</b> (tool name + JSON arguments + an id) instead
    of prose; your code <b>executes</b> it and returns a <b>result</b> tied to that id; the model continues. Provider APIs add <b>tool choice</b>, <b>parallel calls</b>
    and <b>strict schemas</b>.
  hint: 'Previous: [What an agent is](../01-what-is-an-agent/index.html) · Next: [ReAct: reasoning and acting →](../03-react-loop/index.html) · [All decks](../index.html)'
papers:
- toolformer
- ant_tools
- oai_functions
---

<!-- slide from="title" -->

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Free text is a bad interface

::: cards grid3
### [d] Parsing
Regexes over model prose break on wording changes.

### [b] Arguments
Types, required fields and enums need validation before calling real systems.

### [c] Round trip
The model must see the result, correlated with the call that produced it.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Schemas in, structured calls out

::: cards grid2
### [f] Define
Each tool: name, description of when to use it, and a JSON Schema for its input (Anthropic: input_schema; OpenAI: parameters).

### [a] Call
The model returns a tool call: name, arguments and an id. Anthropic responses stop with stop_reason "tool_use".

### [c] Execute
Your application runs client tools; server tools (e.g. web search) run on the provider's side.

### [e] Return
Send the output back referencing the id (tool_result / function_call_output); the model continues.
:::

Toolformer (2023) showed models can even learn by themselves when and how to call APIs; today's APIs make it a first-class, structured interface.

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## Components

::: diagram 660x300
nodes:
  app: {at: [20, 110, 150, 70], text: Your application, sub: agent loop, color: f, step: 1}
  api: {at: [250, 160, 160, 70], text: Model API, sub: tools + messages, color: a, step: 2}
  reg: {at: [20, 230, 150, 56], text: Tool registry, sub: schemas · handlers, color: e, step: 1}
  ct: {at: [490, 40, 150, 56], text: Client tools, sub: run in your code, color: c, step: 4}
  st: {at: [490, 220, 150, 56], text: Server tools, sub: run by provider, color: b, step: 5}
edges:
  - {from: reg, to: app, label: definitions, step: 1}
  - {from: app, to: api, label: request, step: 2}
  - {from: api, to: app, label: tool calls, step: 3, style: back}
  - {from: app, to: ct, label: execute, step: 4}
  - {from: api, to: st, label: execute, step: 5, style: dash}
steps:
  - The registry holds each tool's schema and the handler that implements it.
  - The application sends the conversation plus tool definitions.
  - The model replies with structured tool calls instead of (or as well as) text.
  - 'Client tools: your code validates arguments and runs the handler.'
  - 'Server tools: the provider runs them (Anthropic: web_search, web_fetch, code_execution) and returns results in the same response.'
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## The message sequence

::: diagram 660x220
nodes:
  u: {at: [20, 20, 190, 50], text: user, sub: '"Weather in Paris?"', color: f, step: 1}
  a1: {at: [235, 20, 190, 50], text: assistant, sub: tool_use id=t1 get_weather, color: a, step: 2}
  u2: {at: [450, 20, 190, 50], text: user, sub: 'tool_result t1: 18°C', color: c, step: 3}
  a2: {at: [450, 130, 190, 50], text: assistant, sub: '"It is 18°C in Paris."', color: e, step: 4}
  par: {at: [20, 130, 190, 60], text: parallel calls, sub: several tool_use blocks, color: b, step: 5}
  err: {at: [235, 130, 190, 60], text: errors, sub: 'is_error result, model retries', color: d, step: 6}
edges:
  - {from: u, to: a1, step: 2}
  - {from: a1, to: u2, label: app runs tool, step: 3}
  - {from: u2, to: a2, step: 4}
steps:
  - 'The user asks a question; the request includes a get_weather tool with an input schema {city: string}.'
  - 'The model answers with a tool_use block: an id, the tool name and JSON input {"city": "Paris"}; stop_reason is "tool_use".'
  - Your code runs the tool and sends a tool_result block with the same id (tool_use_id) and the output.
  - 'With the result in context, the model writes the final answer.'
  - The model may request several independent tools at once; return all results before the next call. OpenAI's parallel_tool_calls=false or Anthropic's disable_parallel_tool_use limits this.
  - 'If a tool fails, return the error as the result so the model can fix its arguments or try something else.'
:::



::: table
| Control | Anthropic | OpenAI |
|---|---|---|
| Schema field | input_schema | parameters (strict: true to enforce the schema) |
| Force a tool | tool_choice &#123;"type": "tool", ...} | tool_choice "required" or a named function |
| Limit parallel calls | disable_parallel_tool_use | parallel_tool_calls: false |
| Result message | tool_result (tool_use_id) | function_call_output (call_id) |
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Design choices

::: table
| Choice | Benefit | Cost |
|---|---|---|
| Many specific tools | precise, easy to validate | more tokens in every request; harder for the model to pick |
| Few general tools (e.g. run_sql, bash) | flexible, small definitions | larger blast radius; harder to secure |
| Strict schemas | arguments always parse | less flexible input; schema subset limits |
| Parallel calls | lower latency for independent lookups | harder ordering and partial-failure handling |
| Server-side tools | no execution code to maintain | less control over execution and data flow |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Wrong tool chosen | plausible but irrelevant call | clear descriptions saying when to use and not use each tool; fewer overlapping tools |
| Invalid or hallucinated arguments | IDs that do not exist, wrong types | schemas, enums, validation errors fed back |
| Ignoring the result | answer contradicts the tool output | keep results concise and clearly labelled |
| Duplicate side effects | retry sends two emails | idempotency keys; confirm before irreversible actions |
| Huge results | context floods, cost spikes | truncate, paginate, summarise tool outputs |
:::

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Versioned tool definitions
Tool descriptions are prompts: version them and evaluate changes.

### [c] Timeouts and retries
Every tool needs a timeout; retries must be idempotent.

### [b] Auth per tool
Scope credentials to what each tool needs, per user.

### [e] Stable ordering
Keep tool definitions in a fixed order so prompt caching hits (Operations deck 03).
:::

<!-- slide id="s-papers" from="papers" -->
