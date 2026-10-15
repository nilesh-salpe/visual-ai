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
papers:
- lg_graph_api
- lg_overview
- pregel
- react
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Visual Agents · Frameworks · 02</div>
    <h1>LangGraph core</h1>
    <p class="sub">An agent as a graph: typed shared state with reducers, nodes that return partial updates, fixed and conditional edges, and a runtime that executes in Pregel-style super-steps. Pinned to LangGraph 1.2.15.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Real agents are more than one loop: they route, branch in parallel, retry, wait for people and hand off between agents. Encoding that in nested while-loops and flags gets unreadable, and such code cannot be paused, inspected or resumed.</div>
      <div class="c"><b>Core idea</b>Describe the agent as a <b>state graph</b>. <b>State</b> is a typed dict where each key has a <b>reducer</b> (default: overwrite). <b>Nodes</b> are functions that read state and return <b>partial updates</b>. <b>Edges</b> are fixed or <b>conditional</b> (a routing function picks the next node). The runtime runs active nodes in <b>super-steps</b>, applies updates through the reducers, and stops when no node is active.</div>
    </div>
    <div class="toc" data-auto></div>
    <p class="start-hint">Previous: <a href="../01-langchain-basics/index.html">LangChain basics</a> · Next: <a href="../03-langgraph-production/index.html">LangGraph in production →</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

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

<div class="visual dgm" data-steps="[&quot;State is MessagesState: one key, messages, merged with add_messages.&quot;, &quot;The agent node calls the model on the messages and returns {\&quot;messages\&quot;: [reply]}.&quot;, &quot;A conditional edge inspects the reply: tools_condition routes to \&quot;tools\&quot; if it contains tool calls.&quot;, &quot;The tools node runs every call and appends one ToolMessage each; a fixed edge goes back to the agent.&quot;, &quot;With no tool calls, tools_condition routes to END and the run returns the final state.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 240" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="162.0" y1="48.0" x2="216.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah2)"/></g><g data-step="3"><line x1="392.0" y1="48.0" x2="446.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah2)"/></g><g data-step="4"><line x1="550.0" y1="78.0" x2="550.0" y2="146.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah2)"/></g><g data-step="4"><line x1="493.5" y1="148.0" x2="365.3" y2="80.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah2)"/></g><g data-step="5"><line x1="493.5" y1="78.0" x2="365.3" y2="146.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah2)"/></g><g data-step="1"><rect x="10" y="20" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="85.0" y="53.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">START</text></g><g data-step="2"><rect x="220" y="20" width="170" height="56" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="305.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">agent</text><text x="305.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">model.invoke(messages)</text></g><g data-step="3"><rect x="450" y="20" width="200" height="56" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="550.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">tools_condition</text><text x="550.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">tool calls in last message?</text></g><g data-step="4"><rect x="450" y="150" width="200" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="550.0" y="176.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">tools</text><text x="550.0" y="192.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">ToolNode runs each call</text></g><g data-step="5"><rect x="220" y="150" width="170" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="305.0" y="176.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">END</text><text x="305.0" y="192.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">final answer</text></g><g data-step="1"><rect x="10" y="150" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="85.0" y="176.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">MessagesState</text><text x="85.0" y="192.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">add_messages</text></g><g data-step="4"><text x="550.0" y="107.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">yes</text></g><g data-step="4"><text x="429.4" y="109.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">results</text></g><g data-step="5"><text x="429.4" y="107.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">no</text></g></svg><p class="readout dgcap"></p></div>

<div class="visual"><pre style="margin:0;font:13px/1.55 'JetBrains Mono',monospace;white-space:pre-wrap">from langchain.chat_models import init_chat_model&#10;from langgraph.graph import StateGraph, START, MessagesState&#10;from langgraph.prebuilt import ToolNode, tools_condition&#10;&#10;model = init_chat_model("anthropic:claude-sonnet-5-5").bind_tools(tools)&#10;g = StateGraph(MessagesState)&#10;g.add_node("agent", lambda s: {"messages": [model.invoke(s["messages"])]})&#10;g.add_node("tools", ToolNode(tools))&#10;g.add_edge(START, "agent")&#10;g.add_conditional_edges("agent", tools_condition)   # → "tools" or END&#10;g.add_edge("tools", "agent")&#10;app = g.compile()</pre></div>

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## How a run executes

<div class="visual dgm" data-steps="[&quot;The input is written into the state channels; nodes triggered from START become active.&quot;, &quot;In each super-step all active nodes run, in parallel, on a snapshot of the state.&quot;, &quot;Their partial updates are merged key by key through the reducers. Two nodes writing a plain (overwrite) key in the same step is an error: InvalidUpdateError, \&quot;Can receive only one value per step\&quot;.&quot;, &quot;With a checkpointer, the merged state is saved after the step.&quot;, &quot;Edges (and Send objects for map-reduce fan-out) decide which nodes are active in the next step.&quot;, &quot;The run ends when no node is active. A recursion limit caps the number of super-steps and raises GraphRecursionError.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 240" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah3" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="162.0" y1="48.0" x2="186.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah3)"/></g><g data-step="3"><line x1="352.0" y1="48.0" x2="376.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah3)"/></g><g data-step="4"><line x1="512.0" y1="48.0" x2="536.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah3)"/></g><g data-step="5"><line x1="560.4" y1="78.0" x2="481.9" y2="146.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah3)"/></g><g data-step="5"><line x1="404.6" y1="148.0" x2="313.1" y2="80.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah3)"/></g><g data-step="6"><line x1="512.0" y1="178.0" x2="536.0" y2="178.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah3)"/></g><g data-step="6"><line x1="270.0" y1="148.0" x2="270.0" y2="80.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah3)"/></g><g data-step="1"><rect x="10" y="20" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="85.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Input</text><text x="85.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">initial state</text></g><g data-step="2"><rect x="190" y="20" width="160" height="56" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="270.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Super-step</text><text x="270.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">active nodes run</text></g><g data-step="3"><rect x="380" y="20" width="130" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="445.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Reducers</text><text x="445.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">merge updates</text></g><g data-step="4"><rect x="540" y="20" width="110" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="595.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Checkpoint</text><text x="595.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">if enabled</text></g><g data-step="5"><rect x="380" y="150" width="130" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="445.0" y="176.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Next nodes</text><text x="445.0" y="192.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">edges · Send</text></g><g data-step="6"><rect x="540" y="150" width="110" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="595.0" y="176.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Done</text><text x="595.0" y="192.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">none active</text></g><g data-step="6"><rect x="190" y="150" width="160" height="56" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="270.0" y="176.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Recursion limit</text><text x="270.0" y="192.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">max super-steps</text></g><g data-step="3"><text x="364.0" y="43.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">updates</text></g><g data-step="5"><text x="358.8" y="109.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">loop</text></g><g data-step="6"><text x="270.0" y="109.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">guards</text></g></svg><p class="readout dgcap"></p></div>

<div class="visual scroll-x"><table class="tbl"><tr><th>Primitive</th><th>Use</th></tr><tr><td>Send(node, state)</td><td>fan out: run one node many times in parallel with different inputs (map-reduce)</td></tr><tr><td>Command(update=..., goto=...)</td><td>a node updates state and chooses the next node itself; static edges still run as well</td></tr><tr><td>stream_mode</td><td>values, updates, messages (tokens), custom, checkpoints, tasks, debug</td></tr><tr><td>recursion_limit</td><td>set it explicitly: the default has changed across versions (the docs say 1,000 from 1.0.6; the 1.2.15 source sets 10,007)</td></tr></table></div>

<div class="visual" style="display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;background:var(--e-soft);border-color:var(--e)"><div><b>🛠 Try it in Colab</b><p class="caption" style="margin:4px 0 0">Write a reducer, route with a conditional edge, and build the ReAct agent from ToolNode and tools_condition. Runs with a scripted fake model: no API key needed.</p></div><a class="btn primary" href="https://colab.research.google.com/github/nilesh-salpe/visual-ai/blob/main/build-it/agent-frameworks/02_langgraph_core.ipynb" target="_blank" rel="noopener">Open notebook →</a></div>

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

<div class="visual scroll-x"><table class="tbl"><tr><th>Choice</th><th>Benefit</th><th>Cost</th></tr><tr><td>Explicit graph</td><td>visible control flow; each step inspectable and testable</td><td>more code than a loop for simple agents</td></tr><tr><td>create_agent on top</td><td>the standard loop in one call</td><td>custom flows need the graph API anyway</td></tr><tr><td>Fine-grained nodes</td><td>precise checkpoints and retries</td><td>more state traffic and checkpoint writes</td></tr><tr><td>Parallel branches / Send</td><td>lower latency for independent work</td><td>reducers needed for keys written in parallel</td></tr><tr><td>Command-based routing</td><td>routing logic beside the work</td><td>edges are no longer visible in the graph definition alone</td></tr></table></div>

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

<div class="visual scroll-x"><table class="tbl"><tr><th>Failure</th><th>Symptom</th><th>Mitigation</th></tr><tr><td>Missing reducer</td><td>InvalidUpdateError when parallel nodes write the same key</td><td>Annotated reducers for keys with several writers</td></tr><tr><td>Overwrite instead of append</td><td>history disappears after a node returns messages</td><td>use add_messages / operator.add for accumulating keys</td></tr><tr><td>Cycles without exit</td><td>GraphRecursionError or a huge bill</td><td>explicit stop conditions; a small recursion_limit per run</td></tr><tr><td>State bloat</td><td>every step carries megabytes of tool output</td><td>store large blobs outside state; keep references</td></tr><tr><td>Router returns an unknown name</td><td>run fails at the edge</td><td>path maps in add_conditional_edges; tests for each route</td></tr></table></div>

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
