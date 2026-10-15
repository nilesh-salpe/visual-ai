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
papers:
- toolformer
- ant_tools
- oai_functions
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Visual Agents · Foundations · 02</div>
    <h1>Tool calling</h1>
    <p class="sub">How a model asks your code to run a function: tool definitions with JSON schemas, structured tool-use outputs, executing and returning results, parallel calls and tool choice.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Free-text instructions like "now call the weather API for Paris" are hard to parse reliably, and the model has no way to see a function's result unless you feed it back.</div>
      <div class="c"><b>Core idea</b>Describe each tool with a <b>name, description and JSON schema</b>. The model returns a <b>structured call</b> (tool name + JSON arguments + an id) instead of prose; your code <b>executes</b> it and returns a <b>result</b> tied to that id; the model continues. Provider APIs add <b>tool choice</b>, <b>parallel calls</b> and <b>strict schemas</b>.</div>
    </div>
    <div class="toc" data-auto></div>
    <p class="start-hint">Previous: <a href="../01-what-is-an-agent/index.html">What an agent is</a> · Next: <a href="../03-react-loop/index.html">ReAct: reasoning and acting →</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

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

<div class="visual dgm" data-steps="[&quot;The registry holds each tool&#x27;s schema and the handler that implements it.&quot;, &quot;The application sends the conversation plus tool definitions.&quot;, &quot;The model replies with structured tool calls instead of (or as well as) text.&quot;, &quot;Client tools: your code validates arguments and runs the handler.&quot;, &quot;Server tools: the provider runs them (Anthropic: web_search, web_fetch, code_execution) and returns results in the same response.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 300" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah3" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="1"><line x1="95.0" y1="228.0" x2="95.0" y2="184.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah3)"/></g><g data-step="2"><line x1="172.0" y1="161.4" x2="246.0" y2="177.1" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah3)"/></g><g data-step="3"><line x1="245.9" y1="187.3" x2="171.9" y2="171.6" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah3)"/></g><g data-step="4"><line x1="172.0" y1="132.4" x2="486.0" y2="80.9" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah3)"/></g><g data-step="5"><line x1="412.0" y1="213.5" x2="486.0" y2="230.2" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah3)"/></g><g data-step="1"><rect x="20" y="110" width="150" height="70" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="95.0" y="143.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Your application</text><text x="95.0" y="159.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">agent loop</text></g><g data-step="2"><rect x="250" y="160" width="160" height="70" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="330.0" y="193.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Model API</text><text x="330.0" y="209.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">tools + messages</text></g><g data-step="1"><rect x="20" y="230" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="95.0" y="256.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Tool registry</text><text x="95.0" y="272.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">schemas · handlers</text></g><g data-step="4"><rect x="490" y="40" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="565.0" y="66.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Client tools</text><text x="565.0" y="82.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">run in your code</text></g><g data-step="5"><rect x="490" y="220" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="565.0" y="246.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Server tools</text><text x="565.0" y="262.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">run by provider</text></g><g data-step="1"><text x="95.0" y="201.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">definitions</text></g><g data-step="2"><text x="209.0" y="164.3" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">request</text></g><g data-step="3"><text x="208.9" y="194.5" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">tool calls</text></g><g data-step="4"><text x="329.0" y="101.7" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">execute</text></g><g data-step="5"><text x="449.0" y="216.8" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">execute</text></g></svg><p class="readout dgcap"></p></div>

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## The message sequence

<div class="visual dgm" data-steps="[&quot;The user asks a question; the request includes a get_weather tool with an input schema {city: string}.&quot;, &quot;The model answers with a tool_use block: an id, the tool name and JSON input {\&quot;city\&quot;: \&quot;Paris\&quot;}; stop_reason is \&quot;tool_use\&quot;.&quot;, &quot;Your code runs the tool and sends a tool_result block with the same id (tool_use_id) and the output.&quot;, &quot;With the result in context, the model writes the final answer.&quot;, &quot;The model may request several independent tools at once; return all results before the next call. OpenAI&#x27;s parallel_tool_calls=false or Anthropic&#x27;s disable_parallel_tool_use limits this.&quot;, &quot;If a tool fails, return the error as the result so the model can fix its arguments or try something else.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 220" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah4" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="212.0" y1="45.0" x2="231.0" y2="45.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah4)"/></g><g data-step="3"><line x1="427.0" y1="45.0" x2="446.0" y2="45.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah4)"/></g><g data-step="4"><line x1="545.0" y1="72.0" x2="545.0" y2="126.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah4)"/></g><g data-step="1"><rect x="20" y="20" width="190" height="50" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="115.0" y="43.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">user</text><text x="115.0" y="59.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">&quot;Weather in Paris?&quot;</text></g><g data-step="2"><rect x="235" y="20" width="190" height="50" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="330.0" y="43.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">assistant</text><text x="330.0" y="59.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">tool_use id=t1 get_weather</text></g><g data-step="3"><rect x="450" y="20" width="190" height="50" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="545.0" y="43.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">user</text><text x="545.0" y="59.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">tool_result t1: 18°C</text></g><g data-step="4"><rect x="450" y="130" width="190" height="50" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="545.0" y="153.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">assistant</text><text x="545.0" y="169.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">&quot;It is 18°C in Paris.&quot;</text></g><g data-step="5"><rect x="20" y="130" width="190" height="60" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="115.0" y="158.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">parallel calls</text><text x="115.0" y="174.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">several tool_use blocks</text></g><g data-step="6"><rect x="235" y="130" width="190" height="60" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="330.0" y="158.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">errors</text><text x="330.0" y="174.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">is_error result, model retries</text></g><g data-step="3"><text x="436.5" y="40.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">app runs tool</text></g></svg><p class="readout dgcap"></p></div>

<div class="visual scroll-x"><table class="tbl"><tr><th>Control</th><th>Anthropic</th><th>OpenAI</th></tr><tr><td>Schema field</td><td>input_schema</td><td>parameters (strict: true to enforce the schema)</td></tr><tr><td>Force a tool</td><td>tool_choice {"type": "tool", ...}</td><td>tool_choice "required" or a named function</td></tr><tr><td>Limit parallel calls</td><td>disable_parallel_tool_use</td><td>parallel_tool_calls: false</td></tr><tr><td>Result message</td><td>tool_result (tool_use_id)</td><td>function_call_output (call_id)</td></tr></table></div>

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Design choices

<div class="visual scroll-x"><table class="tbl"><tr><th>Choice</th><th>Benefit</th><th>Cost</th></tr><tr><td>Many specific tools</td><td>precise, easy to validate</td><td>more tokens in every request; harder for the model to pick</td></tr><tr><td>Few general tools (e.g. run_sql, bash)</td><td>flexible, small definitions</td><td>larger blast radius; harder to secure</td></tr><tr><td>Strict schemas</td><td>arguments always parse</td><td>less flexible input; schema subset limits</td></tr><tr><td>Parallel calls</td><td>lower latency for independent lookups</td><td>harder ordering and partial-failure handling</td></tr><tr><td>Server-side tools</td><td>no execution code to maintain</td><td>less control over execution and data flow</td></tr></table></div>

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

<div class="visual scroll-x"><table class="tbl"><tr><th>Failure</th><th>Symptom</th><th>Mitigation</th></tr><tr><td>Wrong tool chosen</td><td>plausible but irrelevant call</td><td>clear descriptions saying when to use and not use each tool; fewer overlapping tools</td></tr><tr><td>Invalid or hallucinated arguments</td><td>IDs that do not exist, wrong types</td><td>schemas, enums, validation errors fed back</td></tr><tr><td>Ignoring the result</td><td>answer contradicts the tool output</td><td>keep results concise and clearly labelled</td></tr><tr><td>Duplicate side effects</td><td>retry sends two emails</td><td>idempotency keys; confirm before irreversible actions</td></tr><tr><td>Huge results</td><td>context floods, cost spikes</td><td>truncate, paginate, summarise tool outputs</td></tr></table></div>

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
