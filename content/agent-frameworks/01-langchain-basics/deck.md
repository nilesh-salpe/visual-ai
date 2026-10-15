---
title: LangChain Basics
body:
  data-deck: LangChain basics
  data-home: ../index.html
  data-home-label: Frameworks
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
papers:
- bea
- lc_agents
- lc_tools
- lc_middleware
- oai_agents_sdk
- claude_agent_sdk
- lc_pypi
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Visual Agents · Frameworks · 01</div>
    <h1>LangChain basics</h1>
    <p class="sub">The building blocks LangChain standardises across model providers (chat models, messages, tools, structured output) and create_agent, the agent loop compiled as a LangGraph graph. Pinned to LangChain 1.4.6.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Each provider has its own request shapes for messages, tool definitions, tool results, streaming and structured output. Writing the agent loop against each SDK repeats the same plumbing, and switching models means rewriting it.</div>
      <div class="c"><b>Core idea</b>LangChain gives one interface for the pieces: <b>chat models</b> ("provider:model" strings), <b>messages</b> (system, human, AI, tool), <b>tools</b> (a Python function whose name, docstring and type hints become the JSON schema), and <b>structured output</b>. <b>create_agent</b> wires them into the model-tools loop, compiled as a LangGraph graph, with <b>middleware</b> hooks around every model and tool call.</div>
    </div>
    <div class="toc" data-auto></div>
    <p class="start-hint">Next: <a href="../02-langgraph-core/index.html">LangGraph core →</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## The same plumbing, once per provider

::: cards grid3
### [d] Different shapes
Anthropic sends tool results as tool_result blocks keyed by tool_use_id; OpenAI as function_call_output keyed by call_id.

### [b] Repeated loop code
Every agent needs the same steps: call, check for tool calls, execute, append results, repeat, stop.

### [c] Cross-cutting needs
Retries, step limits, summarisation, approvals and redaction get bolted onto each loop separately.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Standard parts, one agent loop

::: cards grid2
### [f] Chat models
A model is "provider:model" or an initialised model object; the provider package translates requests and responses.

### [a] Messages
SystemMessage, HumanMessage, AIMessage (with tool_calls), ToolMessage (with tool_call_id and a status of success or error).

### [c] Tools
@tool turns a function into a tool: the name, the docstring as description, and a JSON schema from the type hints.

### [e] create_agent
Model + tools + system prompt + middleware → a compiled LangGraph graph with a model node and a tools node.
:::

Anthropic's advice still applies: frameworks "make it easy to get started" but "often create extra layers of abstraction that can obscure the underlying prompts and responses". Know what the framework sends: the next slides open it up.

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## What create_agent builds

<div class="visual dgm" data-steps="[&quot;Your application invokes the agent with a list of messages (the agent&#x27;s state).&quot;, &quot;The model node calls the chat model with the tools bound; the integration package speaks the provider&#x27;s API.&quot;, &quot;If the reply has tool calls, the tools node runs them and returns ToolMessages; the loop repeats until a reply has no tool calls.&quot;, &quot;Middleware wraps the loop: hooks before and after the agent and each model call, and wrappers around each model and tool call.&quot;, &quot;With a checkpointer, the conversation state is saved per thread_id, so the next invoke continues it.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 300" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="1"><line x1="132.0" y1="148.0" x2="166.0" y2="148.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah1)"/></g><g data-step="2"><line x1="310.0" y1="118.0" x2="386.0" y2="80.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah1)"/></g><g data-step="3"><line x1="332.0" y1="148.0" x2="376.0" y2="148.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah1)"/></g><g data-step="3"><line x1="378.0" y1="158.0" x2="334.0" y2="158.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah1)"/></g><g data-step="3"><line x1="522.0" y1="148.0" x2="556.0" y2="148.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah1)"/></g><g data-step="4"><line x1="250.0" y1="78.0" x2="250.0" y2="116.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah1)"/></g><g data-step="5"><line x1="250.0" y1="178.0" x2="250.0" y2="231.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah1)"/></g><g data-step="1"><rect x="10" y="120" width="120" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="70.0" y="146.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Your app</text><text x="70.0" y="162.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">invoke / stream</text></g><g data-step="4"><rect x="170" y="20" width="160" height="56" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="250.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Middleware</text><text x="250.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">before / wrap / after</text></g><g data-step="2"><rect x="170" y="120" width="160" height="56" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="250.0" y="146.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">model node</text><text x="250.0" y="162.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">chat model + tools</text></g><g data-step="3"><rect x="380" y="120" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="450.0" y="146.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">tools node</text><text x="450.0" y="162.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">runs tool calls</text></g><g data-step="2"><rect x="380" y="20" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="450.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Provider API</text><text x="450.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">via integration</text></g><g data-step="3"><rect x="560" y="120" width="90" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="605.0" y="153.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Your functions</text></g><g data-step="5"><rect x="170" y="235" width="160" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="250.0" y="261.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Checkpointer</text><text x="250.0" y="277.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">optional memory</text></g><g data-step="1"><text x="149.0" y="143.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">messages</text></g><g data-step="3"><text x="354.0" y="143.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">tool calls</text></g><g data-step="3"><text x="356.0" y="173.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">results</text></g><g data-step="4"><text x="250.0" y="92.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">hooks</text></g><g data-step="5"><text x="250.0" y="199.5" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">state per thread</text></g></svg><p class="readout dgcap"></p></div>

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## From function to tool call and back

<div class="visual"><pre style="margin:0;font:13px/1.55 'JetBrains Mono',monospace;white-space:pre-wrap">from langchain.agents import create_agent&#10;from langchain_core.tools import tool&#10;&#10;@tool&#10;def get_weather(city: str) -> str:&#10;    """Return the current weather for a city."""&#10;    return f"18°C and sunny in {city}"&#10;&#10;agent = create_agent("anthropic:claude-sonnet-5-5", [get_weather],&#10;                     system_prompt="You are a helpful assistant.")&#10;out = agent.invoke({"messages": [{"role": "user", "content": "Weather in Paris?"}]})&#10;# out["messages"]: Human → AI(tool_calls=[get_weather {city: Paris}]) → Tool("18°C ...") → AI("It is 18°C ...")</pre></div>

<div class="visual scroll-x"><table class="tbl"><tr><th>Piece</th><th>What LangChain generates or expects</th></tr><tr><td>Tool schema</td><td>name get_weather, description from the docstring, parameters {"city": {"type": "string"}}, required ["city"]</td></tr><tr><td>Tool call (in AIMessage)</td><td>{"name": "get_weather", "args": {"city": "Paris"}, "id": "t1", "type": "tool_call"}</td></tr><tr><td>Tool result</td><td>ToolMessage(content="18°C and sunny in Paris", tool_call_id="t1")</td></tr><tr><td>Structured output</td><td>response_format=Schema; strategies ToolStrategy (an extra output tool) or ProviderStrategy (the provider's native structured output)</td></tr><tr><td>Middleware hooks</td><td>before_agent, before_model, wrap_model_call, after_model, wrap_tool_call, after_agent</td></tr></table></div>

::: cards grid2
### [c] Built-in middleware (1.4.6)
SummarizationMiddleware, HumanInTheLoopMiddleware, ModelCallLimitMiddleware, ToolCallLimitMiddleware, ModelFallbackMiddleware, ModelRetryMiddleware, ToolRetryMiddleware, PIIMiddleware, LLMToolSelectorMiddleware, among others.

### [d] Tool errors
LangGraph's ToolNode by default returns invalid-argument errors to the model as a tool message and re-raises other exceptions; configure handle_tool_errors for anything else.
:::

<div class="visual" style="display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;background:var(--e-soft);border-color:var(--e)"><div><b>🛠 Try it in Colab</b><p class="caption" style="margin:4px 0 0">Define a tool and check its schema, execute tool calls into tool messages (with errors), write the loop by hand, then compare with create_agent. Runs with a scripted fake model: no API key needed.</p></div><a class="btn primary" href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/agent-frameworks/01_langchain_basics.ipynb" target="_blank" rel="noopener">Open notebook →</a></div>

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Framework or SDK?

<div class="visual scroll-x"><table class="tbl"><tr><th>Option</th><th>Gain</th><th>Cost</th></tr><tr><td>Provider SDK directly</td><td>full control, newest features first, nothing hidden</td><td>you write the loop, retries and limits</td></tr><tr><td>LangChain create_agent</td><td>one interface across providers; middleware for common needs</td><td>an abstraction layer to learn and debug; version churn</td></tr><tr><td>OpenAI Agents SDK</td><td>agents, handoffs, guardrails, sessions and tracing built in</td><td>centred on one provider's conventions</td></tr><tr><td>Claude Agent SDK</td><td>the Claude Code agent loop, built-in file and shell tools, permissions, hooks, subagents</td><td>built around Claude Code's harness and tools</td></tr><tr><td>Your own loop</td><td>a few dozen lines; easy to read</td><td>you rebuild persistence, approvals and streaming</td></tr></table></div>

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

<div class="visual scroll-x"><table class="tbl"><tr><th>Failure</th><th>Symptom</th><th>Mitigation</th></tr><tr><td>Hidden prompt changes</td><td>behaviour shifts after an upgrade</td><td>pin versions; log the exact requests sent to the provider</td></tr><tr><td>Lowest-common-denominator API</td><td>a provider feature (prompt-cache controls, server tools) is unavailable</td><td>pass provider-specific options through, or call that SDK for that step</td></tr><tr><td>Weak tool descriptions</td><td>wrong tool chosen</td><td>the docstring is the prompt: write when to use and when not to</td></tr><tr><td>Unbounded loops</td><td>cost spikes on a stuck task</td><td>call-limit middleware and a recursion limit</td></tr><tr><td>Swallowed errors</td><td>agent "succeeds" with a crashed tool</td><td>decide which errors go back to the model and which must fail the run</td></tr></table></div>

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Pin and test upgrades
Pin langchain and langgraph versions; run your agent evaluations before upgrading.

### [c] Trace everything
Record every model request, tool call and result; framework traces are only useful if they show the raw messages.

### [b] Keep tools thin
Tools should validate inputs and call your services; business logic stays outside the framework.

### [e] Escape hatches
Use LangGraph directly when the flow is not a simple model-tools loop (next deck).
:::

<!-- slide id="s-papers" from="papers" -->
