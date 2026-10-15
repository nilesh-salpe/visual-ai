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
papers:
- mcp_spec
- mcp_changes
- mcp_announce
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Visual Agents · Context · 03</div>
    <h1>Model Context Protocol (MCP)</h1>
    <p class="sub">The open standard for connecting AI applications to tools and data: hosts, clients and servers over JSON-RPC 2.0, the three server features, transports, and what changed in the stateless 2026-07-28 revision.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Every AI application integrated every data source and tool with custom code: N applications × M integrations, each with its own auth, schemas and quirks.</div>
      <div class="c"><b>Core idea</b><b>MCP</b> standardises the connection. <b>Hosts</b> (AI applications) run <b>clients</b> that talk to <b>servers</b> using JSON-RPC 2.0. Servers expose <b>tools</b> (model-controlled functions), <b>resources</b> (context data) and <b>prompts</b> (templates). In revision <b>2026-07-28</b> every request is <b>self-contained</b>: it carries its protocol version and capabilities, with no initialize handshake or session.</div>
    </div>
    <div class="toc" data-auto></div>
    <p class="start-hint">Previous: <a href="../02-agentic-rag/index.html">Agentic retrieval (RAG)</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

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

<div class="visual dgm" data-steps="[&quot;The host is the AI application the user works in.&quot;, &quot;It runs one client per server connection.&quot;, &quot;A local server runs as a subprocess and speaks over stdio (newline-delimited messages on standard streams).&quot;, &quot;A remote server is reached over Streamable HTTP: each message is an HTTP POST to one endpoint, replies are JSON or a request-scoped SSE stream.&quot;, &quot;The host exposes server tools and resources to the model, and SHOULD keep a human able to deny tool invocations.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 300" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah12" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="3"><line x1="172.0" y1="141.1" x2="396.0" y2="94.7" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah12)"/></g><g data-step="4"><line x1="172.0" y1="192.5" x2="396.0" y2="184.4" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah12)"/></g><g data-step="5"><line x1="192.0" y1="207.2" x2="256.7" y2="246.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah12)"/></g><g data-step="1"><rect x="20" y="90" width="170" height="130" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="105.0" y="153.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Host</text><text x="105.0" y="169.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">AI app (IDE, chat)</text></g><g data-step="2"><rect x="40" y="140" width="130" height="30" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="105.0" y="160.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">client 1</text></g><g data-step="2"><rect x="40" y="180" width="130" height="30" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="105.0" y="200.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">client 2</text></g><g data-step="3"><rect x="400" y="40" width="230" height="60" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="515.0" y="68.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">MCP server: files</text><text x="515.0" y="84.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">stdio (local subprocess)</text></g><g data-step="4"><rect x="400" y="150" width="230" height="60" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="515.0" y="178.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">MCP server: SaaS API</text><text x="515.0" y="194.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">Streamable HTTP (remote)</text></g><g data-step="5"><rect x="230" y="250" width="140" height="44" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="300.0" y="270.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">LLM</text><text x="300.0" y="286.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">sees tools</text></g><g data-step="3"><text x="284.0" y="112.9" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">JSON-RPC</text></g><g data-step="4"><text x="284.0" y="183.5" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">JSON-RPC</text></g><g data-step="5"><text x="224.3" y="221.6" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">tools, resources</text></g></svg><p class="readout dgcap"></p></div>

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## A tool call in revision 2026-07-28

<div class="visual dgm" data-steps="[&quot;Optionally call server/discover (servers MUST implement it) to learn supported versions and capabilities; there is no initialize handshake any more.&quot;, &quot;List tools; results carry ttlMs and cacheScope hints, and servers SHOULD list tools in a deterministic order.&quot;, &quot;Call a tool. Every request carries its protocol version and client capabilities in _meta (io.modelcontextprotocol/protocolVersion, \u2026/clientCapabilities).&quot;, &quot;If the server needs more (user input, model output, roots), it returns resultType \&quot;input_required\&quot; with inputRequests, replacing server-initiated sampling and elicitation requests.&quot;, &quot;The client gathers the answers and retries the original request with inputResponses.&quot;, &quot;A finished call returns resultType \&quot;complete\&quot; with the tool output.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 300" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah13" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="202.0" y1="48.0" x2="236.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah13)"/></g><g data-step="3"><line x1="422.0" y1="48.0" x2="456.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah13)"/></g><g data-step="4"><line x1="550.0" y1="78.0" x2="550.0" y2="136.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah13)"/></g><g data-step="5"><line x1="458.0" y1="168.0" x2="424.0" y2="168.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah13)"/></g><g data-step="5"><line x1="385.0" y1="138.0" x2="491.3" y2="80.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah13)"/></g><g data-step="6"><line x1="550.0" y1="198.0" x2="550.0" y2="236.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah13)"/></g><g data-step="1"><rect x="20" y="20" width="180" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="110.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">server/discover</text><text x="110.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">versions · capabilities</text></g><g data-step="2"><rect x="240" y="20" width="180" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="330.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">tools/list</text><text x="330.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">names + JSON Schemas</text></g><g data-step="3"><rect x="460" y="20" width="180" height="56" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="550.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">tools/call</text><text x="550.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">_meta: version, caps</text></g><g data-step="4"><rect x="460" y="140" width="180" height="56" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="550.0" y="166.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">input_required?</text><text x="550.0" y="182.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">multi round-trip</text></g><g data-step="5"><rect x="240" y="140" width="180" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="330.0" y="166.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">retry with</text><text x="330.0" y="182.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">inputResponses</text></g><g data-step="6"><rect x="460" y="240" width="180" height="50" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="550.0" y="263.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">result</text><text x="550.0" y="279.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">resultType: complete</text></g><g data-step="5"><text x="441.0" y="163.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">yes</text></g><g data-step="6"><text x="550.0" y="212.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">no</text></g></svg><p class="readout dgcap"></p></div>

<div class="visual scroll-x"><table class="tbl"><tr><th>Change in 2026-07-28</th><th>Before (2025-11-25 and earlier)</th></tr><tr><td>stateless: version and capabilities on every request</td><td>initialize / notifications/initialized handshake, sessions</td></tr><tr><td>server/discover for up-front version selection</td><td>versions agreed during initialize</td></tr><tr><td>multi round-trip requests (input_required)</td><td>server-initiated sampling/createMessage, elicitation/create, roots/list</td></tr><tr><td>subscriptions/listen for change notifications</td><td>HTTP GET stream; resources/subscribe</td></tr><tr><td>broken stream: client re-issues the request</td><td>SSE resumability with Last-Event-ID</td></tr></table></div>

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

<div class="visual scroll-x"><table class="tbl"><tr><th>Choice</th><th>Benefit</th><th>Cost</th></tr><tr><td>MCP server vs direct function tools</td><td>reusable across hosts; standard discovery</td><td>another process or service to run and secure</td></tr><tr><td>stdio (local)</td><td>simple, no network exposure</td><td>one machine; process management</td></tr><tr><td>Streamable HTTP (remote)</td><td>shared, centrally managed servers</td><td>auth (OAuth-based), network latency</td></tr><tr><td>Many connected servers</td><td>broad capability</td><td>long tool lists cost tokens and confuse tool selection</td></tr><tr><td>Stateless protocol (2026-07-28)</td><td>load-balanceable, no session affinity</td><td>state must be passed explicitly (server-minted handles)</td></tr></table></div>

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

<div class="visual scroll-x"><table class="tbl"><tr><th>Failure</th><th>Symptom</th><th>Mitigation</th></tr><tr><td>Malicious or poisoned tool descriptions</td><td>model follows hidden instructions in metadata</td><td>trust only reviewed servers; show tools to users</td></tr><tr><td>Over-broad credentials</td><td>a server can act far beyond the task</td><td>least-privilege tokens; per-user auth</td></tr><tr><td>Version mismatch</td><td>UnsupportedProtocolVersionError</td><td>discover first; support legacy versions during migration</td></tr><tr><td>Lost in-flight request</td><td>stream broke mid-call</td><td>client re-issues with a new request id (no resumability in 2026-07-28)</td></tr><tr><td>Unconfirmed side effects</td><td>tool runs without the user knowing</td><td>confirmation prompts; visible tool-call indicators (spec SHOULDs)</td></tr></table></div>

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
