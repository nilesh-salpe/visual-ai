---
title: Sandboxing Agents
body:
  data-deck: Sandboxing agents
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
  kicker: Visual Agents · Infrastructure · 04
  h1: Sandboxing agents
  sub: 'Running agent-written code and commands safely: the threat model, the isolation spectrum from syscall filters to microVMs, and the design of a per-task sandbox
    with no secrets inside and network access only through a proxy.'
  problem: Coding and computer-use agents run code they wrote a moment ago, often after reading untrusted text. Without isolation, one injected instruction can read
    SSH keys, delete files, mine crypto or send data anywhere, with your credentials.
  core: 'Run every task in a <b>sandbox</b> with two boundaries: <b>filesystem</b> (only the task''s files) and <b>network</b> (egress only through a proxy that enforces
    an allowlist). Keep <b>secrets outside</b>: a proxy adds real credentials to approved requests. Pick the isolation strength to match the risk: process sandboxes
    (bubblewrap, Seatbelt), containers, a user-space kernel (gVisor) or a <b>microVM</b> (Firecracker: under 125 ms to boot, under 5 MiB overhead).'
  hint: 'Previous: [Identity and access control](../03-access-control/index.html) · [All decks](../index.html)'
papers:
- ant_sandboxing
- firecracker
- gvisor
- seccomp
- owasp_llm
---

<!-- slide from="title" -->

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Agents run untrusted code by design

::: cards grid2
### [d] Untrusted inputs
Web pages, issues and documents can carry instructions that the model may follow.

### [b] Real side effects
Shell, package installs and file writes act on whatever machine the agent runs on.

### [c] Exfiltration
Anthropic's point: without network isolation a compromised agent could send out files such as SSH keys; without filesystem isolation it could escape the sandbox and gain network access.

### [a] Approval fatigue
Asking a human before every command is slow and people stop reading; Anthropic reports sandboxing cut permission prompts by 84% in internal use.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Two boundaries, secrets outside

::: cards grid2
### [f] Filesystem
The agent sees only its working directory (and read-only system files); writes elsewhere fail.

### [a] Network
All traffic leaves through a proxy outside the sandbox that allows listed domains and asks about new ones.

### [c] Credentials
Tokens never enter the sandbox: a proxy checks a scoped credential and attaches the real token (Anthropic's git proxy for Claude Code on the web).

### [e] Resources
CPU, memory, disk, process count and wall-clock limits stop runaway or abusive jobs.
:::

::: table
| Isolation | Mechanism | Strength | Start-up and cost |
|---|---|---|---|
| Syscall filter (seccomp) | BPF filter on system calls | shrinks the kernel attack surface; the kernel docs say it "isn't a sandbox" alone | negligible |
| Process sandbox (bubblewrap, Seatbelt) | namespaces / OS sandbox profiles | good for a local agent on a developer machine | milliseconds |
| Container | namespaces, cgroups, shared host kernel | kernel bugs can break out | sub-second |
| User-space kernel (gVisor) | Sentry services syscalls; does not pass them to the host | much smaller host kernel surface | slower syscall-heavy work; some incompatibilities |
| MicroVM (Firecracker) | KVM virtual machine with a minimal device model | hardware-virtualisation boundary | < 125 ms boot, < 5 MiB overhead, up to 150 microVMs/s per host |
:::

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## A sandbox per task

::: diagram 660x300
nodes:
  ag: {at: [10, 40, 120, 56], text: Agent loop, sub: model + harness, color: a, step: 1}
  or: {at: [205, 40, 145, 56], text: Orchestrator, sub: create · limit · destroy, color: f, step: 2}
  sb: {at: [380, 20, 270, 96], text: Sandbox (microVM / container), sub: task files · tools · no secrets, color: c, step: 3}
  px: {at: [380, 170, 130, 56], text: Egress proxy, sub: domain allowlist, color: d, step: 4}
  cr: {at: [530, 170, 120, 56], text: Credential proxy, sub: adds real token, color: b, step: 5}
  net: {at: [380, 262, 270, 34], text: Internet / internal APIs, color: f, step: 4}
edges:
  - {from: ag, to: or, label: command, step: 2}
  - {from: or, to: sb, label: exec, step: 3}
  - {from: sb, to: px, label: all traffic, step: 4}
  - {from: px, to: net, step: 4, style: dash}
  - {from: sb, to: cr, label: git push, step: 5}
  - {from: cr, to: net, step: 5, style: dash}
steps:
  - The agent decides to run a command or code.
  - An orchestrator creates (or reuses) a sandbox for this task and enforces its limits.
  - 'The command runs inside, seeing only the task''s files and tools. Restrictions apply to every subprocess it starts.'
  - 'Network traffic can only leave through the egress proxy, which enforces the allowed domains.'
  - Operations that need credentials go through a proxy that checks the request (e.g. the right repository and branch) and attaches the real token outside the sandbox.
:::

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## Inside the boundary

::: diagram 660x300
nodes:
  app: {at: [10, 20, 200, 56], text: Agent-run process, sub: python · npm · bash, color: f, step: 1}
  sen: {at: [240, 20, 190, 56], text: gVisor Sentry, sub: syscalls in user space, color: b, step: 2}
  gof: {at: [460, 20, 190, 56], text: Gofer, sub: mediates file access, color: b, step: 2}
  vmm: {at: [240, 150, 190, 56], text: Firecracker VMM, sub: minimal devices, color: c, step: 3}
  kvm: {at: [460, 150, 190, 56], text: Host kernel + KVM, color: d, step: 3}
  snap: {at: [10, 150, 200, 56], text: Snapshot / warm pool, sub: fast start, color: e, step: 4}
  lim: {at: [10, 245, 200, 50], text: cgroups limits, sub: CPU · memory · pids, color: e, step: 5}
edges:
  - {from: app, to: sen, label: syscall, step: 2}
  - {from: sen, to: gof, label: files, step: 2}
  - {from: sen, to: vmm, label: or run in a microVM, step: 3, style: dash}
  - {from: vmm, to: kvm, step: 3}
  - {from: snap, to: vmm, label: restore, step: 4, style: dash}
steps:
  - A process the agent started makes system calls as usual.
  - 'Under gVisor, the Sentry (written in Go) services them in user space and does not pass them to the host kernel; a Gofer process mediates file access.'
  - 'In a microVM, a guest kernel handles syscalls and Firecracker''s minimal virtual machine monitor talks to KVM on the host.'
  - Pools of pre-booted sandboxes or memory snapshots hide start-up time.
  - 'Resource limits (cgroups) cap CPU, memory and process count for each sandbox.'
:::

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

::: table
| Choice | Benefit | Cost |
|---|---|---|
| Stronger isolation (microVM) | protects against kernel exploits | more start-up time, memory and operational work |
| Lighter isolation (process / container) | fast and cheap; good on developer machines | a shared kernel is the boundary |
| No network | no exfiltration at all | cannot install packages or call APIs |
| Allowlisted egress | useful and contained | allowlisted domains can still be abused (e.g. upload to a permitted site) |
| Long-lived sandboxes | warm caches, faster tasks | state and secrets accumulate; cross-task leakage |
:::

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

::: table
| Failure | Symptom | Mitigation |
|---|---|---|
| Secrets inside the sandbox | tokens in env vars or files get exfiltrated | credential proxies; short-lived scoped tokens |
| Exfiltration through allowed domains | data posted to a permitted service | narrow allowlists; inspect or block uploads; per-task policies |
| Escape via kernel bug | container breakout | gVisor or microVMs for untrusted code; patch hosts |
| Resource abuse | crypto-mining, fork bombs, disk fill | cgroups limits, timeouts, quotas |
| Persistence between tasks | one task's files visible to the next | fresh sandbox per task; wipe or snapshot-restore |
:::

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Fast start
Users wait on sandbox creation: keep warm pools and restore from snapshots.

### [c] Audit everything
Log commands, network requests and denied actions per task for incident response.

### [b] Policy per task
Different tasks need different domains and files; generate the policy from the task, not one global list.

### [e] Defence in depth
Sandboxing complements least-privilege tools, approvals for risky actions and prompt-injection defences.
:::

<!-- slide id="s-papers" from="papers" -->
