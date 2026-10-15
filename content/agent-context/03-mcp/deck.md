---
title: Model Context Protocol (MCP)
body:
  data-deck: Model Context Protocol (MCP)
  data-home: ../index.html
  data-home-label: Context
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
- ../../shared/diagram.js
intro:
  kicker: Visual Agents · Context · 03
  h1: Model Context Protocol (MCP)
  sub: 'The open standard for connecting AI applications to tools and data: hosts, clients and servers over JSON-RPC 2.0, the three server features, transports, and
    what changed in the stateless 2026-07-28 revision.'
  problem: 'Every AI application integrated every data source and tool with custom code: N applications × M integrations, each with its own auth, schemas and quirks.'
  core: '<b>MCP</b> standardises the connection. <b>Hosts</b> (AI applications) run <b>clients</b> that talk to <b>servers</b> using JSON-RPC 2.0. Servers expose
    <b>tools</b> (model-controlled functions), <b>resources</b> (context data) and <b>prompts</b> (templates). In revision <b>2026-07-28</b> every request is <b>self-contained</b>:
    it carries its protocol version and capabilities, with no initialize handshake or session.'
  hint: 'Previous: [Agentic retrieval (RAG)](../02-agentic-rag/index.html) · Next: [Agent2Agent protocol (A2A) →](../04-a2a/index.html) · [All decks](../index.html)'
papers:
- mcp_spec
- mcp_changes
- mcp_announce
---

<!-- slide from="title" -->

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## N × M integrations

::: cards grid3
### [d] Custom connectors
Each app re-implements GitHub, Slack, databases, file systems…

### [b] Inconsistent semantics
Different schemas, errors and auth flows per integration.

### [c] No reuse
A connector written for one assistant does not work in another.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## One protocol between apps and capabilities

::: cards grid2
### [f] Roles
Host: the LLM application. Client: a connector inside the host. Server: a service providing context and capabilities.

### [a] Messages
JSON-RPC 2.0, UTF-8. Inspired by the Language Server Protocol for editors.

### [c] Server features
Tools (model-controlled functions), resources (data for the user or model), prompts (templated workflows).

### [e] Client features
Elicitation: servers can ask for more information from the user, through the client.
:::

Anthropic introduced MCP on 25 November 2024 as "a universal, open standard for connecting AI systems with data sources". This deck follows specification revision 2026-07-28.

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## Hosts, clients, servers

::: diagram 660x300
nodes:
  h: {at: [20, 90, 170, 130], text: Host, sub: 'AI app (IDE, chat)', color: a, step: 1}
  c1: {at: [40, 140, 130, 30], text: client 1, color: f, step: 2}
  c2: {at: [40, 180, 130, 30], text: client 2, color: f, step: 2}
  s1: {at: [400, 40, 230, 60], text: 'MCP server: files', sub: stdio (local subprocess), color: c, step: 3}
  s2: {at: [400, 150, 230, 60], text: 'MCP server: SaaS API', sub: Streamable HTTP (remote), color: b, step: 4}
  llm: {at: [230, 250, 140, 44], text: LLM, sub: sees tools, color: e, step: 5}
edges:
  - {from: c1, to: s1, label: JSON-RPC, step: 3}
  - {from: c2, to: s2, label: JSON-RPC, step: 4}
  - {from: h, to: llm, label: 'tools, resources', step: 5}
steps:
  - The host is the AI application the user works in.
  - It runs one client per server connection.
  - A local server runs as a subprocess and speaks over stdio (newline-delimited messages on standard streams).
  - 'A remote server is reached over Streamable HTTP: each message is an HTTP POST to one endpoint, replies are JSON or a request-scoped SSE stream.'
  - 'The host exposes server tools and resources to the model, and SHOULD keep a human able to deny tool invocations.'
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## A tool call in revision 2026-07-28

::: diagram 660x300
nodes:
  d: {at: [20, 20, 180, 56], text: server/discover, sub: versions · capabilities, color: f, step: 1}
  l: {at: [240, 20, 180, 56], text: tools/list, sub: names + JSON Schemas, color: c, step: 2}
  cl: {at: [460, 20, 180, 56], text: tools/call, sub: '_meta: version, caps', color: a, step: 3}
  ir: {at: [460, 140, 180, 56], text: 'input_required?', sub: multi round-trip, color: d, step: 4}
  rt: {at: [240, 140, 180, 56], text: retry with, sub: inputResponses, color: b, step: 5}
  res: {at: [460, 240, 180, 50], text: result, sub: 'resultType: complete', color: e, step: 6}
edges:
  - {from: d, to: l, step: 2}
  - {from: l, to: cl, step: 3}
  - {from: cl, to: ir, step: 4}
  - {from: ir, to: rt, label: 'yes', step: 5}
  - {from: rt, to: cl, step: 5, style: dash}
  - {from: ir, to: res, label: 'no', step: 6}
steps:
  - Optionally call server/discover (servers MUST implement it) to learn supported versions and capabilities; there is no initialize handshake any more.
  - 'List tools; results carry ttlMs and cacheScope hints, and servers SHOULD list tools in a deterministic order.'
  - 'Call a tool. Every request carries its protocol version and client capabilities in _meta (io.modelcontextprotocol/protocolVersion, …/clientCapabilities).'
  - 'If the server needs more (user input, model output, roots), it returns resultType "input_required" with inputRequests, replacing server-initiated sampling and elicitation requests.'
  - The client gathers the answers and retries the original request with inputResponses.
  - A finished call returns resultType "complete" with the tool output.
:::



::: table
| Change in 2026-07-28 | Before (2025-11-25 and earlier) |
|---|---|
| stateless: version and capabilities on every request | initialize / notifications/initialized handshake, sessions |
| server/discover for up-front version selection | versions agreed during initialize |
| multi round-trip requests (input_required) | server-initiated sampling/createMessage, elicitation/create, roots/list |
| subscriptions/listen for change notifications | HTTP GET stream; resources/subscribe |
| broken stream: client re-issues the request | SSE resumability with Last-Event-ID |
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

::: table
| Choice | Benefit | Cost |
|---|---|---|
| MCP server vs direct function tools | reusable across hosts; standard discovery | another process or service to run and secure |
| stdio (local) | simple, no network exposure | one machine; process management |
| Streamable HTTP (remote) | shared, centrally managed servers | auth (OAuth-based), network latency |
| Many connected servers | broad capability | long tool lists cost tokens and confuse tool selection |
| Stateless protocol (2026-07-28) | load-balanceable, no session affinity | state must be passed explicitly (server-minted handles) |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Malicious or poisoned tool descriptions | model follows hidden instructions in metadata | trust only reviewed servers; show tools to users |
| Over-broad credentials | a server can act far beyond the task | least-privilege tokens; per-user auth |
| Version mismatch | UnsupportedProtocolVersionError | discover first; support legacy versions during migration |
| Lost in-flight request | stream broke mid-call | client re-issues with a new request id (no resumability in 2026-07-28) |
| Unconfirmed side effects | tool runs without the user knowing | confirmation prompts; visible tool-call indicators (spec SHOULDs) |
:::

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Authorization
Remote servers use OAuth-based authorization; clients must validate the issuer (iss) and bind credentials to it.

### [c] Caching
Honour ttlMs/cacheScope on list results; deterministic tool order helps prompt caching.

### [b] Observability
Propagate OpenTelemetry trace context in _meta (traceparent, tracestate).

### [e] Migration
Dual-era implementations support both the stateless and legacy handshake-based revisions.
:::

<!-- slide id="s-papers" from="papers" -->
