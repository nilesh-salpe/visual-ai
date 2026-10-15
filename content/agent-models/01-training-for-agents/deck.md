---
title: Training LLMs for Agents
body:
  data-deck: Training LLMs for agents
  data-home: ../index.html
  data-home-label: Models
styles:
- ../../shared/deck.css
- ../../shared/learn.css
scripts:
- ../../shared/deck.js
- ../../shared/learn.js
papers:
- toolformer
- gorilla
- toolllm
- kimi_k2
- swe_rl
- r1
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">Visual Agents · Models · 01</div>
    <h1>Training LLMs for tool use and agency</h1>
    <p class="sub">How models learn to call tools, recover from errors and finish long tasks: synthetic tool-use trajectories for fine-tuning, then reinforcement learning in environments with checkable rewards.</p>
    <div class="ps">
      <div class="p"><b>What is the problem?</b>Multi-step tool use is rare in pretraining text. Untrained models call the wrong API, invent arguments, stop after one step or never recover from an error. Kimi K2's report: agentic capabilities such as multi-step reasoning, long-term planning and tool use "are rare in natural data and costly to scale".</div>
      <div class="c"><b>Core idea</b>Two stages. <b>Supervised fine-tuning</b> on tool-use trajectories, mostly <b>synthesised</b>: real and generated tool specs, generated tasks with rubrics, simulated or real environments, and a judge that filters the results. Then <b>reinforcement learning</b> with rewards you can check (tests pass, final state correct), plus rubric or self-critique rewards for open-ended tasks.</div>
    </div>
    <div class="toc" data-auto></div>
    <p class="start-hint">Next: <a href="../02-serving-for-agents/index.html">Serving LLMs for agent workloads →</a> · <a href="../index.html">All decks</a></p>
  </div>
</section>

<!-- slide id="s-problem" chapter="Problem" tag="1 · Problem" tagclass="b1" -->
## Agency is missing from the training data

::: cards grid3
### [d] Wrong calls
Gorilla's starting point: even GPT-4 generated inaccurate API arguments and hallucinated API usage.

### [b] Short horizons
Chat data rewards one good reply, not a 50-step task that ends in the right state.

### [c] No recovery
Models rarely see examples of reading an error and changing course.
:::

<!-- slide id="s-core" chapter="Core idea" tag="2 · Core idea" tagclass="b2" -->
## Synthesise trajectories, then reinforce outcomes

::: cards grid2
### [f] Self-labelled calls
Toolformer: the model inserts candidate API calls into text and keeps those that make the next tokens more likely.

### [a] Fine-tuning on APIs
Gorilla fine-tunes on API documentation with a retriever; ToolLLM builds ToolBench from 16,464 real REST APIs with ChatGPT-generated instructions and depth-first-search solution paths.

### [c] Pipelines at scale
Kimi K2: 3,000+ real MCP tools and 20,000+ synthetic tools, thousands of generated agents, tasks with explicit rubrics, simulated multi-turn trajectories filtered by an LLM judge, plus real sandboxes for code.

### [e] RL on outcomes
SWE-RL rewards similarity to the real fix on GitHub history and reaches 41.0% on SWE-bench Verified with a 70B model; RL also improved out-of-domain tasks where an SFT baseline got worse.
:::

<!-- slide id="s-hld" chapter="High-level design" tag="3 · High-level design" tagclass="b3" -->
## The training pipeline

<div class="visual dgm" data-steps="[&quot;Collect tool specifications: real ones (Kimi K2 fetched 3,000+ MCP tools from GitHub) and synthetic ones evolved per domain (20,000+).&quot;, &quot;Generate agents (system prompts, tool sets) and tasks from simple to complex, each with a rubric of success criteria.&quot;, &quot;Run a model through each task in an environment: simulated tools and a simulated user, or real sandboxes where fidelity matters (code with test suites).&quot;, &quot;A judge scores each trajectory against its rubric; only passing ones are kept.&quot;, &quot;Supervised fine-tuning on the kept trajectories teaches formats and habits.&quot;, &quot;Reinforcement learning then lets the policy act in environments and learn from rewards: verifiable ones (tests, final state) and, for open-ended tasks, rubric or self-critique rewards.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 300" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah13" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="152.0" y1="48.0" x2="176.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah13)"/></g><g data-step="3"><line x1="322.0" y1="48.0" x2="346.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah13)"/></g><g data-step="3"><line x1="492.0" y1="48.0" x2="506.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah13)"/></g><g data-step="4"><line x1="580.0" y1="78.0" x2="580.0" y2="136.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah13)"/></g><g data-step="5"><line x1="508.0" y1="168.0" x2="494.0" y2="168.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah13)"/></g><g data-step="6"><line x1="348.0" y1="168.0" x2="324.0" y2="168.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah13)"/></g><g data-step="6"><line x1="292.5" y1="138.0" x2="374.7" y2="80.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah13)"/></g><g data-step="6"><line x1="250.0" y1="243.0" x2="250.0" y2="200.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah13)"/></g><g data-step="1"><rect x="10" y="20" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="80.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Tool specs</text><text x="80.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">real + synthetic</text></g><g data-step="2"><rect x="180" y="20" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="250.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Tasks</text><text x="250.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">with rubrics</text></g><g data-step="3"><rect x="350" y="20" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="420.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Environments</text><text x="420.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">simulated + sandboxes</text></g><g data-step="3"><rect x="510" y="20" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="580.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Trajectories</text><text x="580.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">multi-turn</text></g><g data-step="4"><rect x="510" y="140" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="580.0" y="166.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Judge filter</text><text x="580.0" y="182.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">rubric check</text></g><g data-step="5"><rect x="350" y="140" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="420.0" y="166.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">SFT</text><text x="420.0" y="182.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">imitate good runs</text></g><g data-step="6"><rect x="180" y="140" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="250.0" y="166.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">RL</text><text x="250.0" y="182.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">policy rollouts</text></g><g data-step="6"><rect x="180" y="245" width="140" height="50" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="250.0" y="268.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Rewards</text><text x="250.0" y="284.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">tests · state · rubric</text></g><g data-step="5"><text x="501.0" y="163.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">kept</text></g><g data-step="6"><text x="336.0" y="163.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">init</text></g><g data-step="6"><text x="333.6" y="104.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">rollouts</text></g></svg><p class="readout dgcap"></p></div>

<!-- slide id="s-lld" chapter="Low-level design" tag="4 · Low-level design" tagclass="b4" -->
## One RL step for an agent

<div class="visual dgm" data-steps="[&quot;Sample a task with its tools and environment.&quot;, &quot;Generate several multi-turn attempts; each tool call is executed in a sandbox and the observation appended, like inference.&quot;, &quot;Score each finished episode: do the tests pass, is the database in the expected state, does the answer match.&quot;, &quot;Compare each attempt with the others for the same task (group-relative advantages, as in GRPO used by DeepSeek-R1).&quot;, &quot;Compute the loss only on tokens the model generated; tool outputs in the context are masked out, since the model did not produce them.&quot;, &quot;Update the policy, usually with a penalty for drifting too far from the reference model.&quot;]"><div class="controls" style="margin-top:0"><button class="btn primary" data-dg="next">next step</button><button class="btn" data-dg="all">show all</button><button class="btn" data-dg="reset">reset</button></div><svg viewBox="0 0 660 240" style="width:100%;height:auto;margin-top:8px" role="img" aria-label="diagram"><defs><marker id="ah14" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs><g data-step="2"><line x1="162.0" y1="48.0" x2="186.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah14)"/></g><g data-step="2"><line x1="342.0" y1="48.0" x2="366.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah14)"/></g><g data-step="2"><line x1="368.0" y1="58.0" x2="344.0" y2="58.0" style="stroke:var(--ink);stroke-width:1.6;stroke-dasharray:5 4;" marker-end="url(#ah14)"/></g><g data-step="3"><line x1="512.0" y1="48.0" x2="536.0" y2="48.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah14)"/></g><g data-step="4"><line x1="595.0" y1="78.0" x2="595.0" y2="156.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah14)"/></g><g data-step="5"><line x1="538.0" y1="188.0" x2="514.0" y2="188.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah14)"/></g><g data-step="6"><line x1="328.0" y1="188.0" x2="304.0" y2="188.0" style="stroke:var(--ink);stroke-width:1.6;" marker-end="url(#ah14)"/></g><g data-step="1"><rect x="10" y="20" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--faint) 16%, var(--panel));stroke:var(--faint);stroke-width:2"/><text x="85.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Task + tools</text><text x="85.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">from the gym</text></g><g data-step="2"><rect x="190" y="20" width="150" height="56" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="265.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Rollouts</text><text x="265.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">G attempts each</text></g><g data-step="2"><rect x="370" y="20" width="140" height="56" rx="10" style="fill:color-mix(in srgb, var(--c) 16%, var(--panel));stroke:var(--c);stroke-width:2"/><text x="440.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Sandbox</text><text x="440.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">executes tool calls</text></g><g data-step="3"><rect x="540" y="20" width="110" height="56" rx="10" style="fill:color-mix(in srgb, var(--e) 16%, var(--panel));stroke:var(--e);stroke-width:2"/><text x="595.0" y="46.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Reward</text><text x="595.0" y="62.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">end of episode</text></g><g data-step="4"><rect x="540" y="160" width="110" height="56" rx="10" style="fill:color-mix(in srgb, var(--b) 16%, var(--panel));stroke:var(--b);stroke-width:2"/><text x="595.0" y="186.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Advantage</text><text x="595.0" y="202.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">vs group mean</text></g><g data-step="5"><rect x="330" y="160" width="180" height="56" rx="10" style="fill:color-mix(in srgb, var(--d) 16%, var(--panel));stroke:var(--d);stroke-width:2"/><text x="420.0" y="186.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Loss mask</text><text x="420.0" y="202.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">model tokens only</text></g><g data-step="6"><rect x="120" y="160" width="180" height="56" rx="10" style="fill:color-mix(in srgb, var(--a) 16%, var(--panel));stroke:var(--a);stroke-width:2"/><text x="210.0" y="186.0" text-anchor="middle" style="font:700 13px Inter,sans-serif;fill:var(--ink)">Policy update</text><text x="210.0" y="202.0" text-anchor="middle" style="font:500 11px Inter,sans-serif;fill:var(--muted)">KL-regularised</text></g><g data-step="2"><text x="354.0" y="43.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">tool call</text></g><g data-step="2"><text x="356.0" y="73.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">observation</text></g><g data-step="3"><text x="524.0" y="43.0" text-anchor="middle" style="font:600 11px Inter,sans-serif;fill:var(--muted);paint-order:stroke;stroke:var(--panel);stroke-width:4px">final state</text></g></svg><p class="readout dgcap"></p></div>

<div class="visual scroll-x"><table class="tbl"><tr><th>Signal</th><th>Example</th><th>Risk</th></tr><tr><td>Verifiable reward</td><td>unit tests pass; final state matches</td><td>reward hacking (editing the tests)</td></tr><tr><td>Similarity reward</td><td>SWE-RL: patch similarity to the real fix</td><td>rewards one solution among many valid ones</td></tr><tr><td>Rubric / LLM judge</td><td>Kimi K2 self-critique rubric reward</td><td>judge bias; reward models can be gamed</td></tr></table></div>

<!-- slide id="s-trade" chapter="Trade-offs" tag="5 · Trade-offs" tagclass="b5" -->
## Trade-offs

<div class="visual scroll-x"><table class="tbl"><tr><th>Choice</th><th>Benefit</th><th>Cost</th></tr><tr><td>Real APIs and sandboxes</td><td>faithful feedback</td><td>slow, flaky, expensive to scale and reset</td></tr><tr><td>Simulated tools and users</td><td>cheap, unlimited, controllable</td><td>simulation gap: the model learns the simulator</td></tr><tr><td>SFT only</td><td>stable and simple</td><td>imitates the generator's mistakes; weak at recovery</td></tr><tr><td>RL on outcomes</td><td>learns recovery and long-horizon strategy</td><td>needs environments, verifiers and lots of compute</td></tr><tr><td>Distil from a stronger agent</td><td>fast way to a capable small model</td><td>capped by the teacher; licence limits on outputs</td></tr></table></div>

<!-- slide id="s-fail" chapter="Failure modes" tag="6 · Failure modes" tagclass="b6" -->
## Failure modes

<div class="visual scroll-x"><table class="tbl"><tr><th>Failure</th><th>Symptom</th><th>Mitigation</th></tr><tr><td>Reward hacking</td><td>model deletes failing tests or special-cases checks</td><td>hidden tests, protected files, review of high-reward episodes</td></tr><tr><td>Overfitting to tool formats</td><td>great on the benchmark's tools, poor on new ones</td><td>held-out tools and APIs (ToolLLM tested unseen APIs and APIBench)</td></tr><tr><td>Credit assignment</td><td>one reward for 50 steps learns slowly</td><td>shorter tasks first, intermediate checks, curricula of moderate difficulty</td></tr><tr><td>Forgetting general skills</td><td>chat and reasoning regress after agent tuning</td><td>mixed data; RL rather than narrow SFT (SWE-RL's finding)</td></tr><tr><td>Unsafe habits</td><td>learns to take destructive shortcuts</td><td>safety tasks and penalties in the gym</td></tr></table></div>

<!-- slide id="s-prod" chapter="Production" tag="7 · Challenges in production" tagclass="b7" -->
## In production

::: cards grid2
### [a] Environment infrastructure
Thousands of isolated sandboxes that start fast, reset cleanly and log everything.

### [c] Evaluation beyond the gym
Track agent benchmarks (SWE-bench Verified, τ-bench) and your own tasks, with pass^k for consistency.

### [b] Data provenance
Know which trajectories came from which generator and environment version.

### [e] Fine-tune or prompt?
For most applications, tool descriptions and examples beat training; fine-tune when volume justifies a smaller specialised model.
:::

<!-- slide id="s-papers" from="papers" -->
