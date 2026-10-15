---
title: Computer and Browser Use
body:
  data-deck: Computer and browser use
  data-home: ../index.html
  data-home-label: Systems
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
papers:
- ant_computer
- osworld
- webarena
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Visual Agents · Systems · 02</div>
    <h1>Computer and browser use</h1>
    <p class="sub">Agents that operate graphical interfaces: the screenshot-action loop, how actions are grounded to pixels, benchmarks of how hard it is, and the sandboxing it requires.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Many tasks only exist behind GUIs: legacy apps, websites without APIs, desktop software. An API-only agent cannot do them.</div>
      <div class="c"><b>Core idea</b>Give the model <b>screenshot, mouse and keyboard</b> tools. In a loop it sees the screen, chooses an action (click at coordinates, type, scroll, key press), the harness performs it in a <b>sandboxed VM or container</b>, and returns a new screenshot. Prefer APIs when they exist; GUIs are slower and more error-prone.</div>
    </div>
    <div class="toc" data-auto></div>
    <p class="start-hint">Previous: <a href="../01-multi-agent/index.html">Multi-agent systems</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Some work only has a GUI

::: cards grid3
### [d] No API
Internal tools, legacy desktop apps, many websites.

### [b] Visual state
The relevant information is laid out on screen, not in a data structure.

### [c] Human-like workflows
Multi-application tasks: copy from a spreadsheet, paste into a form, email the result.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## See, act, see again

::: cards grid2
### [a] Observe
A screenshot (and optionally an accessibility tree or DOM).

### [c] Act
Click/double-click at (x, y), type text, press keys, scroll, drag; short action batches.

### [b] Verify
Take another screenshot to confirm the action had the intended effect.

### [d] Still hard
At release, OSWorld: humans 72.36% vs best model 12.24%; WebArena: 14.41% vs 78.24%. Main struggles: GUI grounding and operational knowledge.
:::

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## The computer-use stack

<div class="visual dgm" data-steps="[&quot;Your harness runs the loop; the model never touches the machine directly.&quot;, &quot;It sends the current screenshot and history to the model.&quot;, &quot;The model returns an action (e.g. left_click at coordinates); the harness performs it inside the sandbox.&quot;, &quot;After the action, a fresh screenshot shows the result.&quot;, &quot;The sandbox has minimal privileges and internet limited to an allowlist of domains (Anthropic&#x27;s recommendations).&quot;, &quot;Actions with real-world consequences (purchases, sending messages, accepting terms) go to a human for confirmation.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 300" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah16" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="157.5" y1="118.0" x2="233.6" y2="79.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah16)"/></g><g data-step="3"><line x1="242.1" y1="85.9" x2="165.9" y2="124.9" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah16)"/></g><g data-step="3"><line x1="172.0" y1="150.0" x2="436.0" y2="150.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah16)"/></g><g data-step="4"><line x1="438.0" y1="160.0" x2="174.0" y2="160.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah16)"/></g><g data-step="5"><line x1="540.0" y1="197.0" x2="540.0" y2="226.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah16)"/></g><g data-step="6"><line x1="152.0" y1="182.0" x2="248.3" y2="236.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah16)"/></g><g data-step="1"><rect x="20" y="120" width="150" height="60" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="95.0" y="148.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Your harness</text><text x="95.0" y="164.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">agent loop</text></g><g data-step="2"><rect x="230" y="15" width="140" height="60" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="300.0" y="43.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Model</text><text x="300.0" y="59.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">decides action</text></g><g data-step="3"><rect x="440" y="105" width="200" height="90" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="540.0" y="148.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Sandbox VM / container</text><text x="540.0" y="164.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">desktop + browser</text></g><g data-step="5"><rect x="440" y="230" width="200" height="50" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="540.0" y="253.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Network allowlist</text><text x="540.0" y="269.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">only approved domains</text></g><g data-step="6"><rect x="230" y="240" width="140" height="50" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="300.0" y="263.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Human approval</text><text x="300.0" y="279.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">risky actions</text></g><g data-step="2"><text x="195.5" y="93.5" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">screenshot</text></g><g data-step="3"><text x="204.0" y="120.4" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">action</text></g><g data-step="3"><text x="304.0" y="145.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">execute</text></g><g data-step="4"><text x="306.0" y="175.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">new screenshot</text></g><g data-step="6"><text x="200.2" y="204.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">confirm</text></g></svg><p class="readout dgcap"></p></div>

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## One action step

<div class="visual dgm" data-steps="[&quot;Capture the screen, often downscaled to a resolution the model handles well.&quot;, &quot;The model must locate the target element on screen: \&quot;GUI grounding\&quot;, the main weakness found by OSWorld.&quot;, &quot;It outputs an action with coordinates or keys.&quot;, &quot;The harness maps coordinates back to the real screen resolution.&quot;, &quot;Wait for the UI to settle; acting during loading clicks the wrong thing.&quot;, &quot;Verify with a new screenshot before continuing.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 220" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah17" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="192.0" y1="48.0" x2="241.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah17)"/></g><g data-step="3"><line x1="417.0" y1="48.0" x2="466.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah17)"/></g><g data-step="4"><line x1="555.0" y1="78.0" x2="555.0" y2="136.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah17)"/></g><g data-step="5"><line x1="468.0" y1="168.0" x2="419.0" y2="168.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah17)"/></g><g data-step="6"><line x1="243.0" y1="168.0" x2="194.0" y2="168.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah17)"/></g><g data-step="6"><line x1="105.0" y1="138.0" x2="105.0" y2="80.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah17)"/></g><g data-step="1"><rect x="20" y="20" width="170" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="105.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Screenshot</text><text x="105.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">scaled resolution</text></g><g data-step="2"><rect x="245" y="20" width="170" height="56" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="330.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Ground target</text><text x="330.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">which element, where</text></g><g data-step="3"><rect x="470" y="20" width="170" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="555.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Action</text><text x="555.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">left_click [x, y]</text></g><g data-step="4"><rect x="470" y="140" width="170" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="555.0" y="166.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Scale coords</text><text x="555.0" y="182.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">model → screen pixels</text></g><g data-step="5"><rect x="245" y="140" width="170" height="56" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="330.0" y="166.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Wait</text><text x="330.0" y="182.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">page load / animation</text></g><g data-step="6"><rect x="20" y="140" width="170" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="105.0" y="166.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Verify</text><text x="105.0" y="182.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">new screenshot</text></g><g data-step="6"><text x="105.0" y="104.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">next step</text></g></svg><p class="readout dgcap"></p></div>

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

<div class="visual scroll-x"><table class="tbl"><tr><th>Choice</th><th>Benefit</th><th>Cost</th></tr><tr><td>GUI automation vs an API</td><td>works on anything a human can use</td><td>slower, brittle, more tokens (images)</td></tr><tr><td>Screenshots only</td><td>general across apps</td><td>grounding errors; small text hard to read</td></tr><tr><td>+ accessibility tree / DOM</td><td>precise element targeting</td><td>not always available; large</td></tr><tr><td>Batching actions</td><td>fewer model calls</td><td>errors compound before verification</td></tr><tr><td>More autonomy</td><td>faster completion</td><td>higher risk; confirmations add friction</td></tr></table></div>

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

<div class="visual scroll-x"><table class="tbl"><tr><th>Failure</th><th>Symptom</th><th>Mitigation</th></tr><tr><td>Mis-grounded clicks</td><td>clicks the wrong button or field</td><td>zoom, accessibility data, verify after each action</td></tr><tr><td>Timing</td><td>acts before the page loads</td><td>waits and state checks</td></tr><tr><td>Prompt injection from the screen</td><td>web page text redirects the agent</td><td>classifiers, isolation from sensitive data, allowlists</td></tr><tr><td>Irreversible actions</td><td>unintended purchase or deletion</td><td>human confirmation; sandbox accounts</td></tr><tr><td>Credential exposure</td><td>logins visible to the model</td><td>do not give the model sensitive credentials</td></tr></table></div>

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Isolation
A dedicated VM or container with minimal privileges, reset between tasks.

### [c] Recording
Keep screenshots and action logs for audit and debugging.

### [b] Cost
Every step sends an image; long tasks are expensive and slow.

### [e] Fallback to APIs
Use APIs or MCP tools wherever they exist; reserve GUI control for the rest.
:::

<!-- slide id="s-papers" from="papers" -->
