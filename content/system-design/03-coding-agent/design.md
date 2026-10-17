---
title: 'Autonomous Coding Agent: design document'
back: index.html
back_label: Overview deck
---

# An autonomous coding agent

> **Design question.** Build a service that takes 10,000 coding tasks a day, works on each in an isolated environment, and opens a pull request that passes the tests, safely and at a predictable cost.

## 1. Goals and non-goals

**Goals:** resolve well-scoped issues end to end; strong isolation of agent-run code; no credentials exposed to the agent; resumable long tasks; measurable quality and cost.

**Non-goals:** merging without review; tasks that need production access; large refactors spanning many repositories.

## 2. Requirements

| Type | Requirement |
|---|---|
| Functional | submit task + repository; progress updates; cancel; branch and pull request with summary |
| Safety | isolated execution; no secrets in the environment; egress allowlist; human review before merge |
| Scale (assumption) | 10,000 tasks/day, ~40 steps and ~20 minutes per task, peak 3× |
| Reliability | a crash or deploy never restarts a task from scratch |
| Cost | budget per task (steps, tokens, wall-clock) |

## 3. Estimates

- **Context growth:** with a 20K-token prefix (system prompt, tools, issue, key files) and 2K tokens added per step, a 40-step task sends nP + T·n(n−1)/2 = 40 × 20K + 2K × 780 = **2.36M input tokens**.
- **Caching:** with prompt caching (5-minute writes at 1.25× base input price, reads at 0.1× on most Claude models) the same task costs about 15% of that in input-token terms, if every step hits the cache.
- **Daily volume:** 10,000 × 2.36M ≈ **23.6B input tokens/day** before caching.
- **Sandboxes:** 10,000 tasks / 1,440 minutes × 20 minutes ≈ 139 busy on average, **~420 at a 3× peak**.

## 4. Architecture

::: diagram 660x300
nodes:
  is: {at: [10, 120, 110, 56], text: Issue, sub: or task, color: f, step: 1}
  wf: {at: [160, 110, 160, 76], text: Workflow engine, sub: durable · per task, color: a, step: 2}
  llm: {at: [160, 10, 160, 56], text: Model API, sub: via gateway, color: b, step: 3}
  sb: {at: [370, 110, 150, 76], text: Sandbox (microVM), sub: repo · tests, color: c, step: 4}
  px: {at: [560, 60, 90, 56], text: Egress proxy, sub: allowlist, color: d, step: 5}
  gp: {at: [560, 160, 90, 56], text: Git proxy, sub: real token, color: d, step: 6}
  rv: {at: [160, 235, 160, 56], text: Review, sub: tests · human, color: e, step: 7}
  pr: {at: [370, 235, 150, 56], text: Pull request, sub: merge after review, color: e, step: 8}
edges:
  - {from: is, to: wf, step: 2}
  - {from: wf, to: llm, label: each step, step: 3}
  - {from: wf, to: sb, label: tool calls, step: 4}
  - {from: sb, to: px, step: 5, style: dash}
  - {from: sb, to: gp, label: push, step: 6}
  - {from: wf, to: rv, step: 7}
  - {from: rv, to: pr, step: 8}
steps:
  - 'A task arrives: an issue to fix or a change request.'
  - 'A durable workflow runs the agent loop; every model call and tool call is an activity whose result is recorded, so crashes resume without redoing work.'
  - 'Each step calls the model through the gateway (budgets, retries, caching).'
  - 'Tool calls (shell, file edits, tests) run in a fresh microVM sandbox holding a clone of the repository and no secrets.'
  - All network traffic leaves through an egress proxy that allows package registries and nothing else by default.
  - Pushing goes through a git proxy that checks the branch and attaches the real credential outside the sandbox.
  - 'The result is checked: tests must pass, and a human reviews the diff.'
  - Only then is a pull request opened or merged.
:::

## 5. Components

### 5.1 Task service and workflow engine
Each task is a durable workflow (e.g. Temporal): model calls and tool calls are activities with timeouts and retry policies; the event history lets any worker resume a task after a crash. Workflow code stays deterministic; LLM outputs are recorded results.

### 5.2 Agent loop
A single agent with tools: search code, read and edit files, run commands and tests. Budgets cap steps, tokens and wall-clock time. Tool outputs are truncated and summarised to keep the context lean; the history is compacted near the context limit.

### 5.3 Sandboxes
A fresh microVM per task (Firecracker boots in under 125 ms with under 5 MiB overhead), restored from a snapshot with the repository and dependency caches. The filesystem is limited to the workspace; all traffic goes through an egress proxy with an allowlist; CPU, memory, disk and time limits apply.

### 5.4 Credential and git proxies
The sandbox holds only a scoped, task-bound credential. A git proxy verifies that pushes target the task's branch and attaches the real token outside the sandbox (the pattern Anthropic describes for Claude Code on the web). No other secrets enter the sandbox.

### 5.5 Model access
Through the LLM gateway: per-tenant budgets, retries with backoff, prompt caching with stable prefixes (tool definitions and system prompt fixed and first).

### 5.6 Verification and review
Run the relevant tests during the loop and the full suite at the end; lint and type checks; a generated summary; a human approves the pull request.

## 6. Reliability

| Failure | Handling |
|---|---|
| Worker crash or deploy | workflow replays its history on another worker; completed steps are not repeated |
| Model 429 / 5xx | gateway retries with backoff, honours retry-after; workflow activity retries |
| Agent loops or stalls | step and token budgets; repeated-action detection; end with a report |
| Sandbox failure | recreate from snapshot and replay file changes recorded in the history |
| Weak tests | human review; track revert rate; add hidden checks for common failure classes |

## 7. Security

Threat model: prompt injection from issues, code comments or fetched pages; malicious dependencies; data exfiltration. Controls: microVM isolation, egress allowlist, no secrets in the sandbox, least-privilege git scope, audit log of commands and network requests, human approval for merges.

## 8. Evaluation and metrics

Offline: a fixed task set (in the style of SWE-bench Verified, where the project's own tests decide success), measured with pass^k so that consistency, not one lucky run, is rewarded. Online: resolved rate, pull-request acceptance, revert rate, time and cost per resolved task, budget overruns.

## 9. Alternatives considered

- **Containers instead of microVMs:** cheaper and faster but share the host kernel; acceptable only for trusted single-tenant code.
- **Multi-agent orchestration:** useful for broad parallel exploration; Anthropic reports multi-agent systems use about 15× the tokens of chat, too costly for most fixes.
- **Auto-merge on green tests:** faster, but tests often miss intent; consider only for narrow, well-tested change classes.

## 10. API and data model

```
POST /tasks              {"repo": "...", "issue": "...", "budget": {"steps": 60, "minutes": 30}}
GET  /tasks/{id}         → status, current step, cost so far, branch, pull request
POST /tasks/{id}/cancel
```

| Record | Store | Notes |
|---|---|---|
| Task | workflow engine (event history) + task table | durable; replayable after crashes |
| Step events | event history | model calls and tool results recorded as activity results |
| Sandbox snapshot | snapshot store | repository + dependency caches per repository |
| Audit log | append-only | every command, file write and network request |

## 11. Scaling

| Bottleneck | Fix |
|---|---|
| Sandboxes at peak (~420) | pre-warmed microVM pools per region, restored from snapshots |
| Model tokens | prompt caching with a stable prefix; compaction of long histories; cheaper model for simple steps |
| Workflow engine | shard by task id; it stores histories, not model state |
| Test time | run targeted tests during the loop and the full suite once at the end |

## 12. Observability

Per task: steps, tokens (input, cached, output), wall-clock time, tool errors, budget overruns, final outcome. Per fleet: resolved rate, pull-request acceptance and revert rates, cost per resolved task, sandbox start latency, egress-proxy denials (a signal of attempted exfiltration or broken allowlists).

## 13. Cost model

Per task (assumptions): 2.36M input tokens uncached, about 15% of that cost with prompt caching; output about 40 steps × 500 tokens = 20K tokens; about 20 sandbox-minutes. Daily: 10,000 tasks × these numbers. The dominant term is input tokens, which is why stable prefixes and compaction matter more than anything else. Cost per *resolved* task (total cost ÷ resolved tasks) is the number to track.

## 14. Rollout

Internal repositories first with human review of every pull request; measure resolved and revert rates against a fixed task set; widen to more repositories and task types; consider auto-merge only for narrow, well-tested change classes.

## 15. Risks and open questions

Prompt injection through issues or fetched content; tests that pass without fixing the real problem; cost blow-ups on hard tasks (budgets must end tasks with a report, not silently); dependency on model quality changes between versions.

## References

Anthropic, Beyond permission prompts (Claude Code sandboxing, 2025); Agache et al. 2020 (Firecracker); Temporal documentation (workflows, retries); Anthropic prompt caching documentation; Jimenez et al. 2024 (SWE-bench); Yao et al. (τ-bench, pass^k); Anthropic, Building effective agents. Related decks: sandboxing, durable workflows, tool calling, cost and latency, evaluating agents, safety and reliability.
