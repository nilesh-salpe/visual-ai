---
title: Identity and Access Control
body:
  data-deck: Identity and access control
  data-home: ../index.html
  data-home-label: Infrastructure
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
- ../../shared/diagram.js
intro:
  kicker: Visual Agents · Infrastructure · 03
  h1: Identity and access control for agents
  sub: 'Making an agent act with the user''s permissions and no more: role- and attribute-based policies enforced outside the model, delegated and audience-bound
    tokens, and permission-aware retrieval.'
  problem: An agent with one broad service credential can do anything that credential can, for anyone who talks to it, including an attacker hiding instructions in
    a document. That is a <b>confused deputy</b>. Retrieval without permissions hands users documents they could never open.
  core: Authorise every action <b>as the user</b>, with <b>least privilege</b>. A policy engine (role-based, attribute-based or relationship-based access control)
    decides outside the model, a gateway in front of tools enforces it, tokens are <b>scoped and bound to one audience</b> (OAuth 2.1, RFC 8707) and delegation is
    explicit (RFC 8693). Retrieval filters by the user's access lists <b>before</b> the model sees any text. The model never decides who may do what.
  hint: 'Previous: [Model and agent routing](../02-model-router/index.html) · Next: [Sandboxing agents →](../04-sandboxing/index.html) · [All decks](../index.html)'
papers:
- owasp_llm
- nist_rbac
- nist_abac
- zanzibar
- mcp_auth
- mcp_changes
- rfc8693
---

<!-- slide from="title" -->

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Agents are perfect confused deputies

::: cards grid2
### [d] Confused deputy
A privileged program tricked into using its authority for someone who lacks it; the agent is the deputy, injected text the trickster.

### [b] Excessive agency
OWASP LLM06:2025 names the root causes: excessive functionality, excessive permissions and excessive autonomy.

### [c] Leaky retrieval
An index built from every document answers any user; OWASP lists Vector and Embedding Weaknesses (LLM08:2025).

### [a] Untraceable actions
If every call uses the agent's own key, logs cannot say which user caused what.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Decide outside the model, act as the user

::: cards grid2
### [f] RBAC
Role-based access control: users get roles, roles carry permissions. Formalised by Ferraiolo and Kuhn in 1992; the NIST model became ANSI/INCITS 359-2004.

### [a] ABAC
Attribute-based access control (NIST Special Publication 800-162): decide from attributes of subject, object, action and environment, e.g. "same department, business hours, document not restricted".

### [c] ReBAC
Relationship-based: "user is editor of folder that contains doc". Google's Zanzibar serves trillions of such access lists, millions of checks per second, p95 under 10 ms.

### [e] Delegation
RFC 8693 token exchange distinguishes impersonation (A is B) from delegation ("A is an agent for B"), recorded in the token's act claim.
:::

The model proposes actions; deterministic code checks them. OWASP's mitigations say the same: minimise tools and their permissions, execute in the user's context, require approval for high-impact actions, and use <b>complete mediation</b> (check every request at the downstream system).

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## Policy around the agent

::: diagram 660x300
nodes:
  u: {at: [10, 120, 100, 56], text: User, sub: signed in, color: f, step: 1}
  ag: {at: [150, 110, 150, 76], text: Agent, sub: carries user identity, color: a, step: 2}
  pep: {at: [340, 120, 150, 56], text: Tool gateway, sub: enforcement point, color: d, step: 3}
  pdp: {at: [340, 20, 150, 56], text: Policy engine, sub: RBAC · ABAC · ReBAC, color: b, step: 3}
  t: {at: [540, 120, 110, 56], text: Tools / APIs, sub: scoped tokens, color: c, step: 4}
  rt: {at: [340, 230, 150, 56], text: Retriever, sub: filters by ACL, color: e, step: 5}
  ix: {at: [540, 230, 110, 56], text: Index, sub: chunks + ACLs, color: e, step: 5}
  au: {at: [540, 20, 110, 56], text: Audit log, sub: user · agent · act, color: f, step: 6}
edges:
  - {from: u, to: ag, step: 2}
  - {from: ag, to: pep, label: tool call, step: 3}
  - {from: pep, to: pdp, label: 'allowed?', step: 3}
  - {from: pep, to: t, label: scoped call, step: 4}
  - {from: ag, to: rt, label: query as user, step: 5}
  - {from: rt, to: ix, step: 5}
  - {from: pep, to: au, step: 6, style: dash}
steps:
  - 'The user signs in; the session carries their identity, not just the agent''s.'
  - 'The agent plans with tools, but holds no broad credentials of its own.'
  - 'Every tool call passes an enforcement point that asks the policy engine: may this user, through this agent, do this action on this resource now?'
  - Allowed calls go out with a token scoped to that tool and that user; denied calls return an error the model can explain.
  - 'Retrieval runs with the user''s identity: the index stores each chunk''s access list and filters before ranking.'
  - 'Every decision is logged with the user, the agent and the action, so incidents can be traced.'
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Authorization in MCP (revision 2026-07-28)

::: diagram 660x290
nodes:
  c: {at: [10, 120, 140, 60], text: MCP client, sub: agent host, color: f, step: 1}
  m: {at: [220, 20, 170, 60], text: MCP server, sub: resource server, color: a, step: 1}
  as: {at: [440, 220, 200, 60], text: Authorization server, sub: OAuth 2.1, color: b, step: 2}
  up: {at: [500, 20, 150, 60], text: Upstream API, sub: its own tokens, color: c, step: 5}
edges:
  - {from: c, to: m, label: 401 + scope, step: 1}
  - {from: c, to: as, label: PKCE + resource, step: 2}
  - {from: as, to: c, label: audience-bound token, step: 3, style: back}
  - {from: m, to: up, label: separate token, step: 5}
  - {from: m, to: as, label: validate audience, step: 4, style: dash}
steps:
  - A request without a token gets 401 with a WWW-Authenticate header naming the Protected Resource Metadata (RFC 9728) and the scopes needed. Servers MUST publish that metadata.
  - 'The client discovers the authorization server, then authorizes with PKCE (S256) and the resource parameter (RFC 8707) naming the server''s canonical URI, in both the authorization and token requests.'
  - 'The token is issued for that one server and sent as "Authorization: Bearer" on every request, never in the URL.'
  - 'The server MUST validate the token was issued for it as audience; a token with too little scope gets 403 insufficient_scope, and the client re-authorizes with the union of old and new scopes (step-up).'
  - 'Calling an upstream API, the server uses a separate token from the upstream authorization server. It MUST NOT pass through the client''s token.'
:::

::: cards grid2
### [e] Permission-aware retrieval
Store access lists with each chunk and filter inside the search (pre-filter), not after the model has read the text. Sync access changes into the index promptly.

### [d] Proxy servers
MCP proxy servers using a static client ID MUST get user consent for each dynamically registered client before forwarding to a third-party authorization server, which closes a confused-deputy hole. Dynamic Client Registration itself is deprecated in 2026-07-28 in favour of Client ID Metadata Documents [[legacy]].
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

::: table
| Choice | Benefit | Cost |
|---|---|---|
| One service account for the agent | simple | every user gets the agent's full power; no per-user audit |
| Per-user delegated tokens (OAuth) | actions limited to the user's rights; clear audit | consent flows, token storage and refresh |
| RBAC | easy to reason about and review | role explosion for fine-grained rules |
| ABAC / ReBAC | fine-grained, contextual decisions | policy complexity; a check service on the hot path |
| Pre-filter retrieval by access list | no leaked text | restrictive filters can hurt ANN recall |
| Human approval for risky actions | stops injected or mistaken actions | latency and approval fatigue |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Token passthrough | a token meant for one service works at another | audience validation; separate upstream tokens (MCP: MUST NOT pass through) |
| Injected instruction uses a permitted tool | data sent out with a valid token | authorization does not stop this alone: egress limits, approval for sensitive actions |
| Over-broad scopes | one token can read and write everything | request minimal scopes; step-up when more are needed |
| Stale ACLs in the index | revoked users still retrieve documents | propagate permission changes; re-check at read time |
| Cross-user memory | agent recalls one user's data for another | partition memory and caches by user and tenant |
| Tokens in logs or prompts | credentials leak through traces or the model | keep tokens in the tool layer, never in the context window |
:::

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Short-lived tokens
Issue short-lived access tokens and rotate refresh tokens for public clients, as the MCP spec requires.

### [c] Policy as code
Version and test policies like software; review new tools for the permissions they need.

### [b] Tenant isolation
Separate indexes, caches and memory per tenant where the data demands it.

### [e] Kill switches
Be able to revoke an agent's or a user's tokens and disable a tool instantly.
:::

<!-- slide id="s-papers" from="papers" -->
