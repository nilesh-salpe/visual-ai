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
papers:
- greshake
- agentdojo
- ant_computer
- mcp_spec
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Visual Agents · Operations · 02</div>
    <h1>Safety and reliability</h1>
    <p class="sub">Agents read untrusted content and hold real permissions. Indirect prompt injection, least privilege, sandboxing, human confirmation, and the engineering that keeps long-running agents dependable.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>An agent that browses, reads email or calls tools processes text written by strangers. Instructions hidden in that text can hijack it, and its permissions make the damage real: data exfiltration, unwanted purchases, deleted files.</div>
      <div class="c"><b>Core idea</b>Assume <b>tool outputs are untrusted data</b>, not instructions. Contain the blast radius with <b>least privilege</b>, <b>sandboxing</b> and <b>allowlists</b>; require <b>human confirmation</b> for consequential actions; detect attacks with classifiers and monitoring; and engineer reliability with timeouts, idempotent retries, checkpoints and audit logs.</div>
    </div>
    <div class="toc" data-auto></div>
    <p class="start-hint">Previous: <a href="../01-evaluating-agents/index.html">Evaluating agents</a> · Next: <a href="../03-cost-and-latency/index.html">Cost and latency →</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

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

<div class="visual dgm" data-steps="[&quot;Content from tools and the web is untrusted.&quot;, &quot;Input checks flag likely injections before or after they reach the model.&quot;, &quot;The agent is prompted and trained to treat tool output as data, not instructions.&quot;, &quot;A policy layer outside the model decides whether a proposed action is allowed; models cannot be the only line of defence.&quot;, &quot;Consequential or unusual actions require explicit human approval.&quot;, &quot;Tools run with narrowly scoped credentials, so even a hijacked agent can do little.&quot;, &quot;Everything is logged for audit and incident response.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 300" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah19" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="142.0" y1="118.6" x2="193.9" y2="94.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah19)"/></g><g data-step="3"><line x1="255.0" y1="92.0" x2="255.0" y2="126.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah19)"/></g><g data-step="4"><line x1="332.0" y1="160.0" x2="376.0" y2="160.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah19)"/></g><g data-step="5"><line x1="450.0" y1="192.0" x2="450.0" y2="236.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah19)"/></g><g data-step="6"><line x1="522.0" y1="160.0" x2="556.0" y2="160.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah19)"/></g><g data-step="7"><line x1="255.0" y1="192.0" x2="255.0" y2="236.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah19)"/></g><g data-step="1"><rect x="20" y="120" width="120" height="56" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="80.0" y="146.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Untrusted input</text><text x="80.0" y="162.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">web · email · docs</text></g><g data-step="2"><rect x="180" y="40" width="150" height="50" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="255.0" y="63.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Input checks</text><text x="255.0" y="79.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">injection classifiers</text></g><g data-step="3"><rect x="180" y="130" width="150" height="60" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="255.0" y="158.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Agent</text><text x="255.0" y="174.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">treats data as data</text></g><g data-step="4"><rect x="380" y="130" width="140" height="60" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="450.0" y="158.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Policy engine</text><text x="450.0" y="174.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">allowed? confirm?</text></g><g data-step="5"><rect x="380" y="240" width="140" height="50" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="450.0" y="270.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Human approval</text></g><g data-step="6"><rect x="560" y="130" width="90" height="60" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="605.0" y="158.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Tools</text><text x="605.0" y="174.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">scoped creds</text></g><g data-step="7"><rect x="180" y="240" width="150" height="50" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="255.0" y="263.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Audit log</text><text x="255.0" y="279.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">every action</text></g><g data-step="4"><text x="354.0" y="155.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">proposed action</text></g><g data-step="5"><text x="450.0" y="209.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">risky</text></g><g data-step="6"><text x="539.0" y="155.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">allowed</text></g></svg><p class="readout dgcap"></p></div>

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Permission and reliability details

<div class="visual dgm" data-steps="[&quot;Classify tools by risk: reading data can usually proceed automatically.&quot;, &quot;Writes that can be undone are allowed but logged.&quot;, &quot;Irreversible or externally visible actions (payments, emails, deletions) need confirmation.&quot;, &quot;Every tool call has a timeout so one hung dependency cannot stall the agent.&quot;, &quot;Retries carry idempotency keys so a retried action does not happen twice.&quot;, &quot;Persist state so long tasks resume after a crash instead of restarting.&quot;, &quot;Operators can stop agents and revoke their credentials immediately.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 300" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah20" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="1"><rect x="20" y="20" width="190" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="115.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Read-only tools</text><text x="115.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">auto-approve</text></g><g data-step="2"><rect x="235" y="20" width="190" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="330.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Reversible writes</text><text x="330.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">allow + log</text></g><g data-step="3"><rect x="450" y="20" width="190" height="56" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="545.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Irreversible / external</text><text x="545.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">require approval</text></g><g data-step="4"><rect x="20" y="140" width="190" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="115.0" y="166.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Timeouts</text><text x="115.0" y="182.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">every tool call</text></g><g data-step="5"><rect x="235" y="140" width="190" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="330.0" y="166.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Idempotent retries</text><text x="330.0" y="182.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">keys per action</text></g><g data-step="6"><rect x="450" y="140" width="190" height="56" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="545.0" y="166.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Checkpoints</text><text x="545.0" y="182.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">resume long tasks</text></g><g data-step="7"><rect x="235" y="240" width="190" height="50" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="330.0" y="263.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Kill switch</text><text x="330.0" y="279.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">stop runs, revoke creds</text></g></svg><p class="readout dgcap"></p></div>

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

<div class="visual scroll-x"><table class="tbl"><tr><th>Choice</th><th>Benefit</th><th>Cost</th></tr><tr><td>More autonomy</td><td>faster, fewer interruptions</td><td>larger blast radius</td></tr><tr><td>Confirm every action</td><td>maximum control</td><td>unusable; users rubber-stamp</td></tr><tr><td>Risk-tiered confirmation</td><td>friction only where it matters</td><td>needs a correct risk classification</td></tr><tr><td>Strict sandbox and allowlists</td><td>contains attacks and accidents</td><td>some tasks become impossible</td></tr><tr><td>Model-based injection detection</td><td>catches novel attacks</td><td>false positives; can be evaded</td></tr></table></div>

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

<div class="visual scroll-x"><table class="tbl"><tr><th>Failure</th><th>Example</th><th>Mitigation</th></tr><tr><td>Data exfiltration</td><td>injected text makes the agent send private data to an attacker URL</td><td>egress allowlists; no secrets in context</td></tr><tr><td>Destructive action</td><td>agent deletes files or records</td><td>approval tier; backups; reversible operations</td></tr><tr><td>Privilege escalation</td><td>agent uses broad credentials beyond the task</td><td>per-task scoped tokens</td></tr><tr><td>Persistent injection</td><td>malicious instruction saved into memory</td><td>validate memory writes; provenance</td></tr><tr><td>Cascading failure</td><td>retry storm or hung dependency</td><td>timeouts, backoff, circuit breakers</td></tr></table></div>

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
