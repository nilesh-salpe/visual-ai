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
- ../../shared/diagram.js
intro:
  kicker: Visual Agents · Frameworks · 01
  h1: LangChain basics
  sub: The building blocks LangChain standardises across model providers (chat models, messages, tools, structured output) and create_agent, the agent loop compiled
    as a LangGraph graph. Pinned to LangChain 1.4.6.
  problem: Each provider has its own request shapes for messages, tool definitions, tool results, streaming and structured output. Writing the agent loop against
    each SDK repeats the same plumbing, and switching models means rewriting it.
  core: 'LangChain gives one interface for the pieces: <b>chat models</b> ("provider:model" strings), <b>messages</b> (system, human, AI, tool), <b>tools</b> (a Python
    function whose name, docstring and type hints become the JSON schema), and <b>structured output</b>. <b>create_agent</b> wires them into the model-tools loop,
    compiled as a LangGraph graph, with <b>middleware</b> hooks around every model and tool call.'
  hint: 'Next: [LangGraph core →](../02-langgraph-core/index.html) · [All decks](../index.html)'
papers:
- bea
- lc_agents
- lc_tools
- lc_middleware
- oai_agents_sdk
- claude_agent_sdk
- lc_pypi
- lc_v1_migration
status: {label: current, reviewed: 2026-10-15, note: "langchain 1.4.6 still latest; create_react_agent and legacy chains labelled"}
---

<!-- slide from="title" -->

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

Since LangChain and LangGraph 1.0: build agents with `langchain.agents.create_agent` [[current]]; `langgraph.prebuilt.create_react_agent` is deprecated [[legacy]], and legacy chains such as LLMChain moved to the separate langchain-classic package [[legacy]].

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## What create_agent builds

::: diagram 660x300
nodes:
  app: {at: [10, 120, 120, 56], text: Your app, sub: invoke / stream, color: f, step: 1}
  mw: {at: [170, 20, 160, 56], text: Middleware, sub: before / wrap / after, color: d, step: 4}
  mn: {at: [170, 120, 160, 56], text: model node, sub: chat model + tools, color: a, step: 2}
  tn: {at: [380, 120, 140, 56], text: tools node, sub: runs tool calls, color: c, step: 3}
  pv: {at: [380, 20, 140, 56], text: Provider API, sub: via integration, color: b, step: 2}
  fn: {at: [560, 120, 90, 56], text: Your functions, color: e, step: 3}
  cp: {at: [170, 235, 160, 56], text: Checkpointer, sub: optional memory, color: f, step: 5}
edges:
  - {from: app, to: mn, label: messages, step: 1}
  - {from: mn, to: pv, step: 2}
  - {from: mn, to: tn, label: tool calls, step: 3}
  - {from: tn, to: mn, label: results, step: 3, style: back}
  - {from: tn, to: fn, step: 3}
  - {from: mw, to: mn, label: hooks, step: 4, style: dash}
  - {from: mn, to: cp, label: state per thread, step: 5, style: dash}
steps:
  - Your application invokes the agent with a list of messages (the agent's state).
  - The model node calls the chat model with the tools bound; the integration package speaks the provider's API.
  - 'If the reply has tool calls, the tools node runs them and returns ToolMessages; the loop repeats until a reply has no tool calls.'
  - 'Middleware wraps the loop: hooks before and after the agent and each model call, and wrappers around each model and tool call.'
  - 'With a checkpointer, the conversation state is saved per thread_id, so the next invoke continues it.'
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## From function to tool call and back

::: code
from langchain.agents import create_agent
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """Return the current weather for a city."""
    return f"18°C and sunny in {city}"

agent = create_agent("anthropic:claude-sonnet-5-5", [get_weather],
                     system_prompt="You are a helpful assistant.")
out = agent.invoke({"messages": [{"role": "user", "content": "Weather in Paris?"}]})
# out["messages"]: Human → AI(tool_calls=[get_weather {city: Paris}]) → Tool("18°C ...") → AI("It is 18°C ...")
:::



::: table
| Piece | What LangChain generates or expects |
|---|---|
| Tool schema | name get_weather, description from the docstring, parameters &#123;"city": &#123;"type": "string"}}, required ["city"] |
| Tool call (in AIMessage) | &#123;"name": "get_weather", "args": &#123;"city": "Paris"}, "id": "t1", "type": "tool_call"} |
| Tool result | ToolMessage(content="18°C and sunny in Paris", tool_call_id="t1") |
| Structured output | response_format=Schema; strategies ToolStrategy (an extra output tool) or ProviderStrategy (the provider's native structured output) |
| Middleware hooks | before_agent, before_model, wrap_model_call, after_model, wrap_tool_call, after_agent |
:::

::: cards grid2
### [c] Built-in middleware (1.4.6)
SummarizationMiddleware, HumanInTheLoopMiddleware, ModelCallLimitMiddleware, ToolCallLimitMiddleware, ModelFallbackMiddleware, ModelRetryMiddleware, ToolRetryMiddleware, PIIMiddleware, LLMToolSelectorMiddleware, among others.

### [d] Tool errors
LangGraph's ToolNode by default returns invalid-argument errors to the model as a tool message and re-raises other exceptions; configure handle_tool_errors for anything else.
:::

::: colab build-it/agent-frameworks/01_langchain_basics.ipynb
Define a tool and check its schema, execute tool calls into tool messages (with errors), write the loop by hand, then compare with create_agent. Runs with a scripted fake model: no API key needed.
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Framework or SDK?

::: table
| Option | Gain | Cost |
|---|---|---|
| Provider SDK directly | full control, newest features first, nothing hidden | you write the loop, retries and limits |
| LangChain create_agent | one interface across providers; middleware for common needs | an abstraction layer to learn and debug; version churn |
| OpenAI Agents SDK | agents, handoffs, guardrails, sessions and tracing built in | centred on one provider's conventions |
| Claude Agent SDK | the Claude Code agent loop, built-in file and shell tools, permissions, hooks, subagents | built around Claude Code's harness and tools |
| Your own loop | a few dozen lines; easy to read | you rebuild persistence, approvals and streaming |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Hidden prompt changes | behaviour shifts after an upgrade | pin versions; log the exact requests sent to the provider |
| Lowest-common-denominator API | a provider feature (prompt-cache controls, server tools) is unavailable | pass provider-specific options through, or call that SDK for that step |
| Weak tool descriptions | wrong tool chosen | the docstring is the prompt: write when to use and when not to |
| Unbounded loops | cost spikes on a stuck task | call-limit middleware and a recursion limit |
| Swallowed errors | agent "succeeds" with a crashed tool | decide which errors go back to the model and which must fail the run |
:::

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
