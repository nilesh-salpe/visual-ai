---
title: Agent2Agent Protocol (A2A)
body:
  data-deck: Agent2Agent protocol (A2A)
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
  kicker: Visual Agents · Context · 04
  h1: Agent2Agent protocol (A2A)
  sub: An open protocol for agents built by different teams and vendors to discover each other, delegate tasks and stream results, without sharing their internals.
    Pinned to A2A v1.0.
  problem: An agent that needs help from another organisation's agent has no standard way to find it, learn what it can do, hand it a long-running task, follow progress,
    or receive files back. Wrapping every remote agent as a custom tool repeats that integration for each pair.
  core: 'Each agent publishes an <b>Agent Card</b> (its skills, endpoints, capabilities and security schemes). A client agent sends a <b>Message</b> made of <b>Parts</b>;
    the remote agent answers with a Message or a <b>Task</b> that moves through a lifecycle and produces <b>Artifacts</b>. Agents stay <b>opaque</b>: they cooperate
    without sharing memory, tools or plans. MCP connects an agent to tools and data; A2A connects agents to agents.'
  hint: 'Previous: [Model Context Protocol (MCP)](../03-mcp/index.html) · Next: [RAG, fine-tuning or long context →](../05-rag-vs-finetuning/index.html) · [All decks](../index.html)'
papers:
- a2a_spec
- a2a_announce
- a2a_lf
- mcp_spec
---

<!-- slide from="title" -->

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Agents from different builders cannot cooperate

::: cards grid3
### [d] Discovery
No standard place to learn what a remote agent does, where it lives and how to authenticate.

### [b] Long-running work
Delegated work may take hours and need more input midway; a single request-response call does not fit.

### [c] Opaque partners
Vendors will not expose their prompts, tools or memory; integration must work through a narrow interface.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Cards, messages, tasks, artifacts

::: cards grid2
### [f] Agent Card
A JSON document at https://{domain}/.well-known/agent-card.json: name, description, supportedInterfaces (first is preferred), capabilities (streaming, push notifications), skills, securitySchemes.

### [a] Message and Part
A turn with a role (user or agent) and Parts; each Part holds exactly one of text, raw bytes, a url or structured data.

### [c] Task
The unit of work: id, contextId, status, artifacts and history. A contextId groups related tasks and messages into one conversation.

### [e] Artifact
An output of a task, itself made of Parts: a report, a file, structured data.
:::

Google announced A2A on 9 April 2025 with more than 50 partners; the project moved to the Linux Foundation, released v1.0 in March 2026, and by April 2026 had more than 150 supporting organisations.

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## Client agent and remote agent

::: diagram 660x300
nodes:
  u: {at: [10, 120, 110, 56], text: User, color: f, step: 1}
  ca: {at: [160, 110, 150, 76], text: Client agent, sub: 'plans, delegates', color: a, step: 1}
  card: {at: [380, 10, 270, 56], text: Agent Card, sub: /.well-known/agent-card.json, color: b, step: 2}
  ra: {at: [380, 120, 270, 56], text: Remote agent (A2A server), sub: 'opaque: own model, tools, memory', color: c, step: 3}
  mcp: {at: [380, 230, 130, 56], text: MCP servers, sub: its tools, color: e, step: 5}
  wh: {at: [160, 240, 150, 50], text: Webhook, sub: push updates, color: d, step: 6}
edges:
  - {from: u, to: ca, step: 1}
  - {from: ca, to: card, label: discover, step: 2}
  - {from: ca, to: ra, label: SendMessage, step: 3}
  - {from: ra, to: ca, label: Task · status · Artifacts, step: 4, style: back}
  - {from: ra, to: mcp, label: uses, step: 5, style: dash}
  - {from: ra, to: wh, label: task updates, step: 6, style: dash}
steps:
  - A user asks the client agent for something it cannot do alone.
  - 'The client fetches the remote agent''s Agent Card to learn its skills, endpoint, capabilities and how to authenticate.'
  - 'It sends a Message (Parts: text, files, data) with SendMessage, or SendStreamingMessage for live updates.'
  - 'The remote agent replies with a Message for quick answers, or a Task whose status changes over time and whose results arrive as Artifacts.'
  - Internally the remote agent may use MCP to reach its own tools and data; the client never sees them.
  - For long tasks the client can register a webhook and receive push notifications instead of holding a connection.
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## A task's lifecycle on the wire

::: diagram 660x300
nodes:
  sub: {at: [10, 20, 130, 50], text: SUBMITTED, color: f, step: 1}
  wk: {at: [230, 20, 150, 50], text: WORKING, sub: artifact updates, color: a, step: 2}
  in: {at: [230, 140, 150, 56], text: INPUT_REQUIRED, sub: or AUTH_REQUIRED, color: d, step: 3}
  done: {at: [500, 20, 150, 50], text: COMPLETED, sub: artifacts final, color: e, step: 4}
  fail: {at: [500, 100, 150, 46], text: FAILED, color: d, step: 5}
  can: {at: [500, 195, 150, 46], text: CANCELED, sub: CancelTask, color: b, step: 5}
  rej: {at: [10, 140, 130, 50], text: REJECTED, sub: refused, color: b, step: 5}
  ctx: {at: [10, 245, 370, 46], text: 'Follow-up: same contextId, new task', sub: terminal tasks accept no more messages, color: c, step: 6}
edges:
  - {from: sub, to: wk, step: 2}
  - {from: wk, to: in, label: needs input, step: 3}
  - {from: in, to: wk, label: client replies, step: 3, style: back}
  - {from: wk, to: done, label: completes, step: 4}
  - {from: wk, to: fail, step: 5, style: dash}
  - {from: wk, to: can, step: 5, style: dash}
  - {from: sub, to: rej, step: 5, style: dash}
steps:
  - The server creates a task (it generates the id) and acknowledges it.
  - 'It works, streaming status updates and artifact chunks over Server-Sent Events, or via push notifications.'
  - 'It may pause in an interrupted state, INPUT_REQUIRED or AUTH_REQUIRED, until the client sends another message on the same task.'
  - 'When the work finishes the task is COMPLETED, a terminal state; the artifacts hold the result.'
  - 'FAILED, CANCELED and REJECTED are the other terminal states.'
  - 'A terminal task accepts no further messages: a follow-up starts a new task in the same contextId.'
:::



::: table
| Binding | Send a message | Read a task |
|---|---|---|
| JSON-RPC 2.0 | method SendMessage (PascalCase, matching gRPC) | GetTask |
| gRPC | SendMessage | GetTask |
| HTTP+JSON (REST) | POST /message:send (POST /message:stream for SSE) | GET /tasks/&#123;id} |
:::



::: code
{
  "name": "Travel booking agent",
  "description": "Finds and books flights and hotels.",
  "supportedInterfaces": [{"url": "https://agents.example.com/a2a", ...}],
  "capabilities": {"streaming": true, "pushNotifications": true},
  "skills": [{"id": "book-flight", "name": "Book a flight", ...}],
  "securitySchemes": {"oauth": {...}}
}
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

::: table
| Choice | Benefit | Cost |
|---|---|---|
| A2A between agents | one interface for any vendor's agent; long tasks, streaming, push | another protocol to operate and secure |
| Remote agent as an MCP tool | simple when the work is a quick function call | no task lifecycle, negotiation or partial results |
| Opaque agents | vendors keep their internals; loose coupling | harder to debug across the boundary |
| Streaming (SSE) | live progress | long-lived connections |
| Push notifications | no open connection for hours-long tasks | webhook endpoints to secure and keep reachable |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Spoofed or tampered Agent Card | client sends data to an impostor | TLS, signed Agent Cards (JWS) verified by the client, allowlists of trusted agents |
| Forged webhook calls | fake task updates injected | agents MUST authenticate webhook calls; clients MUST validate them |
| Prompt injection across agents | remote artifacts instruct the client agent | treat artifacts as untrusted data, as with any tool output |
| Version mismatch | v0.3 clients expect the removed kind field | pin versions; 1.0 replaced kind with member names |
| Orphaned tasks | work continues after the user gave up | CancelTask, timeouts and budgets on delegated work |
:::

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Identity and auth
Use the declared security schemes (OAuth 2.0, OpenID Connect, mutual TLS); the extended Agent Card MUST require authentication.

### [c] Trace across agents
Propagate trace ids through contextId and metadata so a delegated task appears in one trace.

### [b] Budgets for delegation
A remote agent can spend your money: cap steps, time and cost per delegated task.

### [e] Platform support
Microsoft (Azure AI Foundry, Copilot Studio) and AWS (Bedrock AgentCore Runtime) support A2A.
:::

<!-- slide id="s-papers" from="papers" -->
