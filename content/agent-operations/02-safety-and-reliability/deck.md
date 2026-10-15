---
title: Safety and Reliability
body:
  data-deck: Safety and reliability
  data-home: ../index.html
  data-home-label: Operations
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
- ../../shared/diagram.js
intro:
  kicker: Visual Agents · Operations · 02
  h1: Safety and reliability
  sub: Agents read untrusted content and hold real permissions. Indirect prompt injection, least privilege, sandboxing, human confirmation, and the engineering that
    keeps long-running agents dependable.
  problem: 'An agent that browses, reads email or calls tools processes text written by strangers. Instructions hidden in that text can hijack it, and its permissions
    make the damage real: data exfiltration, unwanted purchases, deleted files.'
  core: Assume <b>tool outputs are untrusted data</b>, not instructions. Contain the blast radius with <b>least privilege</b>, <b>sandboxing</b> and <b>allowlists</b>;
    require <b>human confirmation</b> for consequential actions; detect attacks with classifiers and monitoring; and engineer reliability with timeouts, idempotent
    retries, checkpoints and audit logs.
  hint: 'Previous: [Evaluating agents](../01-evaluating-agents/index.html) · Next: [Cost and latency →](../03-cost-and-latency/index.html) · [All decks](../index.html)'
papers:
- greshake
- agentdojo
- ant_computer
- mcp_spec
---

<!-- slide from="title" -->

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Untrusted input + real permissions

::: cards grid3
### [d] Indirect prompt injection
Greshake et al.: prompts planted in data the app retrieves can override instructions: data theft, worming, manipulation.

### [b] Real side effects
Agents send messages, move money, change files.

### [c] Long runs
More steps mean more chances for a failure or an attack to occur.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Defence in depth

::: cards grid2
### [a] Least privilege
Each tool gets only the access the task needs, per user.

### [c] Isolation
Sandboxed VMs or containers; network allowlists; no sensitive credentials in reach (Anthropic computer-use guidance).

### [b] Human in the loop
Confirm consequential actions; MCP says hosts SHOULD let a human deny tool invocations.

### [e] Detection and testing
Classifiers on tool outputs; red-team with AgentDojo-style suites (97 tasks, 629 security test cases).
:::

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## Guardrail layers

::: diagram 660x300
nodes:
  in: {at: [20, 120, 120, 56], text: Untrusted input, sub: web · email · docs, color: d, step: 1}
  cls: {at: [180, 40, 150, 50], text: Input checks, sub: injection classifiers, color: c, step: 2}
  ag: {at: [180, 130, 150, 60], text: Agent, sub: treats data as data, color: a, step: 3}
  pol: {at: [380, 130, 140, 60], text: Policy engine, sub: 'allowed? confirm?', color: b, step: 4}
  hu: {at: [380, 240, 140, 50], text: Human approval, color: e, step: 5}
  tool: {at: [560, 130, 90, 60], text: Tools, sub: scoped creds, color: c, step: 6}
  log: {at: [180, 240, 150, 50], text: Audit log, sub: every action, color: f, step: 7}
edges:
  - {from: in, to: cls, step: 2}
  - {from: cls, to: ag, step: 3}
  - {from: ag, to: pol, label: proposed action, step: 4}
  - {from: pol, to: hu, label: risky, step: 5}
  - {from: pol, to: tool, label: allowed, step: 6}
  - {from: ag, to: log, step: 7, style: dash}
steps:
  - Content from tools and the web is untrusted.
  - Input checks flag likely injections before or after they reach the model.
  - 'The agent is prompted and trained to treat tool output as data, not instructions.'
  - A policy layer outside the model decides whether a proposed action is allowed; models cannot be the only line of defence.
  - Consequential or unusual actions require explicit human approval.
  - 'Tools run with narrowly scoped credentials, so even a hijacked agent can do little.'
  - Everything is logged for audit and incident response.
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Permission and reliability details

::: diagram 660x300
nodes:
  r: {at: [20, 20, 190, 56], text: Read-only tools, sub: auto-approve, color: e, step: 1}
  w: {at: [235, 20, 190, 56], text: Reversible writes, sub: allow + log, color: b, step: 2}
  x: {at: [450, 20, 190, 56], text: Irreversible / external, sub: require approval, color: d, step: 3}
  to: {at: [20, 140, 190, 56], text: Timeouts, sub: every tool call, color: c, step: 4}
  id: {at: [235, 140, 190, 56], text: Idempotent retries, sub: keys per action, color: c, step: 5}
  ck: {at: [450, 140, 190, 56], text: Checkpoints, sub: resume long tasks, color: a, step: 6}
  ks: {at: [235, 240, 190, 50], text: Kill switch, sub: 'stop runs, revoke creds', color: d, step: 7}
edges: []
steps:
  - 'Classify tools by risk: reading data can usually proceed automatically.'
  - Writes that can be undone are allowed but logged.
  - 'Irreversible or externally visible actions (payments, emails, deletions) need confirmation.'
  - Every tool call has a timeout so one hung dependency cannot stall the agent.
  - Retries carry idempotency keys so a retried action does not happen twice.
  - Persist state so long tasks resume after a crash instead of restarting.
  - Operators can stop agents and revoke their credentials immediately.
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

::: table
| Choice | Benefit | Cost |
|---|---|---|
| More autonomy | faster, fewer interruptions | larger blast radius |
| Confirm every action | maximum control | unusable; users rubber-stamp |
| Risk-tiered confirmation | friction only where it matters | needs a correct risk classification |
| Strict sandbox and allowlists | contains attacks and accidents | some tasks become impossible |
| Model-based injection detection | catches novel attacks | false positives; can be evaded |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Example | Mitigation |
|---|---|---|
| Data exfiltration | injected text makes the agent send private data to an attacker URL | egress allowlists; no secrets in context |
| Destructive action | agent deletes files or records | approval tier; backups; reversible operations |
| Privilege escalation | agent uses broad credentials beyond the task | per-task scoped tokens |
| Persistent injection | malicious instruction saved into memory | validate memory writes; provenance |
| Cascading failure | retry storm or hung dependency | timeouts, backoff, circuit breakers |
:::

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Red-teaming
Test against injection suites before launch and after every change.

### [c] Monitoring
Alert on unusual tool sequences, new domains, spikes in actions.

### [b] Incident response
Audit logs, kill switches and credential revocation ready before you need them.

### [e] User clarity
Show what the agent is doing and why; make approvals informative.
:::

<!-- slide id="s-papers" from="papers" -->
