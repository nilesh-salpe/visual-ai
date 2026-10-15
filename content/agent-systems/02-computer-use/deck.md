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
- ../../shared/diagram.js
intro:
  kicker: Visual Agents · Systems · 02
  h1: Computer and browser use
  sub: 'Agents that operate graphical interfaces: the screenshot-action loop, how actions are grounded to pixels, benchmarks of how hard it is, and the sandboxing
    it requires.'
  problem: 'Many tasks only exist behind GUIs: legacy apps, websites without APIs, desktop software. An API-only agent cannot do them.'
  core: Give the model <b>screenshot, mouse and keyboard</b> tools. In a loop it sees the screen, chooses an action (click at coordinates, type, scroll, key press),
    the harness performs it in a <b>sandboxed VM or container</b>, and returns a new screenshot. Prefer APIs when they exist; GUIs are slower and more error-prone.
  hint: 'Previous: [Multi-agent systems](../01-multi-agent/index.html) · Next: [Durable workflows for agents →](../03-durable-workflows/index.html) · [All decks](../index.html)'
papers:
- ant_computer
- osworld
- webarena
---

<!-- slide from="title" -->

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

::: diagram 660x300
nodes:
  app: {at: [20, 120, 150, 60], text: Your harness, sub: agent loop, color: f, step: 1}
  m: {at: [230, 15, 140, 60], text: Model, sub: decides action, color: a, step: 2}
  vm: {at: [440, 105, 200, 90], text: Sandbox VM / container, sub: desktop + browser, color: c, step: 3}
  net: {at: [440, 230, 200, 50], text: Network allowlist, sub: only approved domains, color: d, step: 5}
  hu: {at: [230, 240, 140, 50], text: Human approval, sub: risky actions, color: b, step: 6}
edges:
  - {from: app, to: m, label: screenshot, step: 2}
  - {from: m, to: app, label: action, step: 3, style: back}
  - {from: app, to: vm, label: execute, step: 3}
  - {from: vm, to: app, label: new screenshot, step: 4, style: back}
  - {from: vm, to: net, step: 5, style: dash}
  - {from: app, to: hu, label: confirm, step: 6, style: dash}
steps:
  - Your harness runs the loop; the model never touches the machine directly.
  - It sends the current screenshot and history to the model.
  - The model returns an action (e.g. left_click at coordinates); the harness performs it inside the sandbox.
  - 'After the action, a fresh screenshot shows the result.'
  - The sandbox has minimal privileges and internet limited to an allowlist of domains (Anthropic's recommendations).
  - 'Actions with real-world consequences (purchases, sending messages, accepting terms) go to a human for confirmation.'
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## One action step

::: diagram 660x220
nodes:
  s: {at: [20, 20, 170, 56], text: Screenshot, sub: scaled resolution, color: f, step: 1}
  g: {at: [245, 20, 170, 56], text: Ground target, sub: 'which element, where', color: a, step: 2}
  a: {at: [470, 20, 170, 56], text: Action, sub: 'left_click [x, y]', color: c, step: 3}
  sc: {at: [470, 140, 170, 56], text: Scale coords, sub: model → screen pixels, color: b, step: 4}
  w: {at: [245, 140, 170, 56], text: Wait, sub: page load / animation, color: d, step: 5}
  v: {at: [20, 140, 170, 56], text: Verify, sub: new screenshot, color: e, step: 6}
edges:
  - {from: s, to: g, step: 2}
  - {from: g, to: a, step: 3}
  - {from: a, to: sc, step: 4}
  - {from: sc, to: w, step: 5}
  - {from: w, to: v, step: 6}
  - {from: v, to: s, label: next step, step: 6, style: dash}
steps:
  - 'Capture the screen, often downscaled to a resolution the model handles well.'
  - 'The model must locate the target element on screen: "GUI grounding", the main weakness found by OSWorld.'
  - It outputs an action with coordinates or keys.
  - The harness maps coordinates back to the real screen resolution.
  - Wait for the UI to settle; acting during loading clicks the wrong thing.
  - Verify with a new screenshot before continuing.
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

::: table
| Choice | Benefit | Cost |
|---|---|---|
| GUI automation vs an API | works on anything a human can use | slower, brittle, more tokens (images) |
| Screenshots only | general across apps | grounding errors; small text hard to read |
| + accessibility tree / DOM | precise element targeting | not always available; large |
| Batching actions | fewer model calls | errors compound before verification |
| More autonomy | faster completion | higher risk; confirmations add friction |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Mis-grounded clicks | clicks the wrong button or field | zoom, accessibility data, verify after each action |
| Timing | acts before the page loads | waits and state checks |
| Prompt injection from the screen | web page text redirects the agent | classifiers, isolation from sensitive data, allowlists |
| Irreversible actions | unintended purchase or deletion | human confirmation; sandbox accounts |
| Credential exposure | logins visible to the model | do not give the model sensitive credentials |
:::

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
