---
title: LangGraph Core
body:
  data-deck: LangGraph core
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
  kicker: Visual Agents · Frameworks · 02
  h1: LangGraph core
  sub: 'An agent as a graph: typed shared state with reducers, nodes that return partial updates, fixed and conditional edges, and a runtime that executes in Pregel-style
    super-steps. Pinned to LangGraph 1.2.15.'
  problem: 'Real agents are more than one loop: they route, branch in parallel, retry, wait for people and hand off between agents. Encoding that in nested while-loops
    and flags gets unreadable, and such code cannot be paused, inspected or resumed.'
  core: 'Describe the agent as a <b>state graph</b>. <b>State</b> is a typed dict where each key has a <b>reducer</b> (default: overwrite). <b>Nodes</b> are functions
    that read state and return <b>partial updates</b>. <b>Edges</b> are fixed or <b>conditional</b> (a routing function picks the next node). The runtime runs active
    nodes in <b>super-steps</b>, applies updates through the reducers, and stops when no node is active.'
  hint: 'Previous: [LangChain basics](../01-langchain-basics/index.html) · Next: [LangGraph in production →](../03-langgraph-production/index.html) · [All decks](../index.html)'
papers:
- lg_graph_api
- lg_overview
- pregel
- react
status: {label: current, reviewed: 2026-10-15, note: "langgraph 1.2.15 still latest; APIs re-checked in source"}
---

<!-- slide from="title" -->

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Loops with flags do not scale

::: cards grid3
### [d] Control flow
Routing, retries and parallel branches tangle into conditionals around the model call.

### [b] Shared state
Several steps write the same history; ordering bugs drop or duplicate messages.

### [c] No pause or resume
A Python loop cannot stop for a human approval and continue tomorrow on another machine.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## State, nodes, edges

::: cards grid2
### [f] State and reducers
A TypedDict schema; Annotated[list, operator.add] appends, add_messages appends messages and replaces ones with the same id; other keys are overwritten.

### [a] Nodes
Plain functions (or runnables): state in, partial update out. They never return the whole state.

### [c] Edges
add_edge for fixed transitions; add_conditional_edges with a routing function that returns the next node name(s) or END.

### [e] Compile
compile() checks the graph and returns a runnable with invoke, stream and, with a checkpointer, get_state.
:::

The runtime is inspired by Google's Pregel: execution proceeds in discrete <b>super-steps</b> of message passing, and terminates when every node is inactive and no messages are in transit.

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## The ReAct agent as a graph

::: diagram 660x240
nodes:
  st: {at: [10, 20, 150, 56], text: START, color: f, step: 1}
  ag: {at: [220, 20, 170, 56], text: agent, sub: model.invoke(messages), color: a, step: 2}
  tc: {at: [450, 20, 200, 56], text: tools_condition, sub: 'tool calls in last message?', color: d, step: 3}
  tl: {at: [450, 150, 200, 56], text: tools, sub: ToolNode runs each call, color: c, step: 4}
  en: {at: [220, 150, 170, 56], text: END, sub: final answer, color: e, step: 5}
  ms: {at: [10, 150, 150, 56], text: MessagesState, sub: add_messages, color: b, step: 1}
edges:
  - {from: st, to: ag, step: 2}
  - {from: ag, to: tc, step: 3}
  - {from: tc, to: tl, label: 'yes', step: 4}
  - {from: tl, to: ag, label: results, step: 4, style: dash}
  - {from: tc, to: en, label: 'no', step: 5}
steps:
  - 'State is MessagesState: one key, messages, merged with add_messages.'
  - 'The agent node calls the model on the messages and returns {"messages": [reply]}.'
  - 'A conditional edge inspects the reply: tools_condition routes to "tools" if it contains tool calls.'
  - The tools node runs every call and appends one ToolMessage each; a fixed edge goes back to the agent.
  - 'With no tool calls, tools_condition routes to END and the run returns the final state.'
:::



::: code
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition

model = init_chat_model("anthropic:claude-sonnet-5-5").bind_tools(tools)
g = StateGraph(MessagesState)
g.add_node("agent", lambda s: {"messages": [model.invoke(s["messages"])]})
g.add_node("tools", ToolNode(tools))
g.add_edge(START, "agent")
g.add_conditional_edges("agent", tools_condition)   # → "tools" or END
g.add_edge("tools", "agent")
app = g.compile()
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## How a run executes

::: diagram 660x240
nodes:
  s0: {at: [10, 20, 150, 56], text: Input, sub: initial state, color: f, step: 1}
  ss: {at: [190, 20, 160, 56], text: Super-step, sub: active nodes run, color: a, step: 2}
  rd: {at: [380, 20, 130, 56], text: Reducers, sub: merge updates, color: b, step: 3}
  ck: {at: [540, 20, 110, 56], text: Checkpoint, sub: if enabled, color: e, step: 4}
  nx: {at: [380, 150, 130, 56], text: Next nodes, sub: edges · Send, color: c, step: 5}
  dn: {at: [540, 150, 110, 56], text: Done, sub: none active, color: e, step: 6}
  lim: {at: [190, 150, 160, 56], text: Recursion limit, sub: max super-steps, color: d, step: 6}
edges:
  - {from: s0, to: ss, step: 2}
  - {from: ss, to: rd, label: updates, step: 3}
  - {from: rd, to: ck, step: 4}
  - {from: ck, to: nx, step: 5}
  - {from: nx, to: ss, label: loop, step: 5, style: dash}
  - {from: nx, to: dn, step: 6}
  - {from: lim, to: ss, label: guards, step: 6, style: dash}
steps:
  - The input is written into the state channels; nodes triggered from START become active.
  - 'In each super-step all active nodes run, in parallel, on a snapshot of the state.'
  - 'Their partial updates are merged key by key through the reducers. Two nodes writing a plain (overwrite) key in the same step is an error: InvalidUpdateError, "Can receive only one value per step".'
  - 'With a checkpointer, the merged state is saved after the step.'
  - Edges (and Send objects for map-reduce fan-out) decide which nodes are active in the next step.
  - The run ends when no node is active. A recursion limit caps the number of super-steps and raises GraphRecursionError.
:::



::: table
| Primitive | Use |
|---|---|
| Send(node, state) | fan out: run one node many times in parallel with different inputs (map-reduce) |
| Command(update=..., goto=...) | a node updates state and chooses the next node itself; static edges still run as well |
| stream_mode | values, updates, messages (tokens), custom, checkpoints, tasks, debug |
| recursion_limit | set it explicitly: the default has changed across versions (the docs say 1,000 from 1.0.6; the 1.2.15 source sets 10,007) |
:::



::: colab build-it/agent-frameworks/02_langgraph_core.ipynb
Write a reducer, route with a conditional edge, and build the ReAct agent from ToolNode and tools_condition. Runs with a scripted fake model: no API key needed.
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

::: table
| Choice | Benefit | Cost |
|---|---|---|
| Explicit graph | visible control flow; each step inspectable and testable | more code than a loop for simple agents |
| create_agent on top | the standard loop in one call | custom flows need the graph API anyway |
| Fine-grained nodes | precise checkpoints and retries | more state traffic and checkpoint writes |
| Parallel branches / Send | lower latency for independent work | reducers needed for keys written in parallel |
| Command-based routing | routing logic beside the work | edges are no longer visible in the graph definition alone |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Missing reducer | InvalidUpdateError when parallel nodes write the same key | Annotated reducers for keys with several writers |
| Overwrite instead of append | history disappears after a node returns messages | use add_messages / operator.add for accumulating keys |
| Cycles without exit | GraphRecursionError or a huge bill | explicit stop conditions; a small recursion_limit per run |
| State bloat | every step carries megabytes of tool output | store large blobs outside state; keep references |
| Router returns an unknown name | run fails at the edge | path maps in add_conditional_edges; tests for each route |
:::

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Test nodes as functions
Nodes are plain functions: unit-test them with fake models before wiring the graph.

### [c] Draw the graph
get_graph().draw_mermaid() documents the real control flow; review it in code review.

### [b] Stream updates
Stream "updates" or "messages" to show progress and tokens to users during long runs.

### [e] Persistence next
Add a checkpointer to get memory, approvals and resumption (next deck).
:::

<!-- slide id="s-papers" from="papers" -->
