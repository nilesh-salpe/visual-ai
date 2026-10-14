---
title: GPU Failures at Scale
body:
  data-deck: GPU failures
  data-home: ../index.html
  data-home-label: GPU
styles:
- ../../shared/deck.css
- ../../shared/learn.css
css: |-
  .xid { display: flex; flex-wrap: wrap; gap: 6px; }
    .xid button { border: 1px solid var(--line); background: var(--panel); color: var(--ink); border-radius: 8px; padding: 6px 10px; cursor: pointer; font: 600 13px 'JetBrains Mono', monospace; }
    .xid button.on { background: var(--a-soft); border-color: var(--a); color: var(--a); }
    .xid button[data-sev="hw"] { border-left: 4px solid var(--d); }
    .xid button[data-sev="sw"] { border-left: 4px solid var(--b); }
    .xid button[data-sev="mixed"] { border-left: 4px solid var(--c); }
    .infobox { min-height: 90px; background: var(--panel-2); border-radius: 10px; padding: 12px 14px; font-size: 14px; color: var(--muted); margin-top: 12px; }
    .infobox b { color: var(--ink); }
    .toggles { display: flex; flex-wrap: wrap; gap: 8px; }
    .toggles label { display: flex; align-items: center; gap: 6px; font-size: 14px; border: 1px solid var(--line); border-radius: 8px; padding: 6px 10px; cursor: pointer; background: var(--panel); }
    .toggles input { accent-color: var(--a); }
    .flow { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
    .flow .card { position: relative; }
    @media (max-width: 820px) { .flow { grid-template-columns: 1fr 1fr; } }
scripts:
- ../../shared/deck.js
glance:
  steps:
  - 'fault :: GPU, NIC, host, software :: d'
  - 'detect :: Xid errors, timeouts, health checks :: b'
  - 'stop job :: one rank down halts all :: c'
  - 'replace / restart :: from last checkpoint :: a'
  - 'resume :: lost work = time since checkpoint :: e'
  caption: At 16K GPUs, failures are routine; the goal is to make each one cheap.
example:
  title: 'Worked example: how often to checkpoint'
  setup: 'Llama 3 405B: 419 unexpected interruptions in 54 days on 16,384 GPUs. Assume a checkpoint takes 5 minutes to write.'
  steps:
  - Job MTBF (mean time between failures) = 54 × 24 h ÷ 419 ≈ <b>3.1 h</b>.
  - 'Per-GPU MTBF ≈ 3.1 h × 16,384 ≈ <b>5.8 years</b>: each GPU is reliable; the fleet is not.'
  - 'Young''s approximation: interval ≈ √(2 × checkpoint cost × MTBF) = √(2 × 0.083 h × 3.1 h) ≈ <b>43 min</b>.'
  - Expected loss per failure ≈ half an interval (22 min) plus restart time; faster checkpoints shorten the interval.
  result: Checkpoint cost and failure rate together set the interval; cutting checkpoint time (async, in-memory) is the main lever.
traps:
  tricks:
  - 'Cluster MTBF = GPU MTBF ÷ N. :: Double the GPUs, halve the time between failures.'
  - 'Checkpoint interval ≈ √(2·C·MTBF). :: Young''s approximation.'
  - 'Stragglers matter. :: A slow GPU slows every synchronous step.'
  traps:
  - 'Waiting for hard failures only. :: Silent data corruption gives wrong numbers with no error.'
  - 'Restarting on the same bad node. :: Drain and test before returning it to the pool.'
  - 'Synchronous checkpoint writes. :: They stall all GPUs for the whole write.'
papers:
- llama3
- megascale
- sdc
- cores_count
---

<!-- slide raw -->
<section class="slide title-slide" id="s-title" data-chapter="Start">
  <div class="inner">
    <div class="kicker">GPU for GenAI · 06</div>
    <h1>GPU failures:<br>at scale they are routine</h1>
    <p class="sub">With 16,000 GPUs (graphics processing units), something breaks every few hours. The question is how quickly you notice, how much work you lose and how fast you resume. This deck covers failure rates, failure types, why a single fault stops the whole job, checkpointing maths, and silent data corruption.</p>
    <div class="toc" data-auto></div>
    <p class="start-hint">Press <kbd>→</kbd> or <kbd>Space</kbd> to begin.</p>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-llama" data-chapter="The data">
  <div class="inner">
    <div class="label">01 · The data</div>
    <h2>Llama 3 405B: 419 unexpected interruptions in 54 days</h2>
    <hr>
    <div class="grid4">
      <div class="stat"><div class="num">16,384</div><div class="lbl">H100 GPUs</div></div>
      <div class="stat"><div class="num" style="color:var(--d)">~3 h</div><div class="lbl">mean time between interruptions</div></div>
      <div class="stat"><div class="num">~78%</div><div class="lbl">confirmed or suspected hardware</div></div>
      <div class="stat"><div class="num" style="color:var(--e)">&gt;90%</div><div class="lbl">effective training time</div></div>
    </div>
    <div class="visual">
      <div class="seg" id="llSeg"><button data-v="all" class="on">All causes</button><button data-v="gpu">GPU-related only</button></div>
      <div id="llBars" style="margin-top:14px"></div>
    </div>
    <p class="caption">Counts of unexpected interruptions by root cause. A further 47 interruptions were planned (466 in total). Only 3 needed significant manual intervention; automation handled the rest.</p>
    <div class="takeaway">The GPU itself (faulty GPU, HBM3 (third-generation high-bandwidth memory), SRAM (static random-access memory, fast on-chip memory), the GSP (GPU System Processor) and thermal issues) accounts for more than half of all interruptions. Plan as though hardware will fail during the run.</div>
    <div class="cite">Llama Team, "The Llama 3 Herd of Models" (2024), Table 5. The paper lists Faulty GPU as 30.1% next to a count of 148; the counts are shown here.</div>
  
    <!--x:glance--><div class="glance"><h4>At a glance</h4><svg viewBox="0 0 660 166" role="img" aria-label="At 16K GPUs, failures are routine; the goal is to make each one cheap." class="glance-svg"><defs><marker id="gArr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--muted)"/></marker></defs><rect x="10.0" y="28" width="113.6" height="64" rx="10" style="fill:var(--d)"/><text x="66.8" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">fault</text><text x="66.8" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">GPU, NIC, host,</text><text x="66.8" y="123.0" text-anchor="middle" class="tm" style="font-size:11px">software</text><rect x="141.6" y="28" width="113.6" height="64" rx="10" style="fill:var(--b)"/><text x="198.4" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">detect</text><text x="198.4" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">Xid errors,</text><text x="198.4" y="123.0" text-anchor="middle" class="tm" style="font-size:11px">timeouts, health</text><text x="198.4" y="137.0" text-anchor="middle" class="tm" style="font-size:11px">checks</text><line x1="125.6" y1="60.0" x2="139.6" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/><rect x="273.2" y="28" width="113.6" height="64" rx="10" style="fill:var(--c)"/><text x="330.0" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">stop job</text><text x="330.0" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">one rank down</text><text x="330.0" y="123.0" text-anchor="middle" class="tm" style="font-size:11px">halts all</text><line x1="257.2" y1="60.0" x2="271.2" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/><rect x="404.8" y="28" width="113.6" height="64" rx="10" style="fill:var(--a)"/><text x="461.6" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">replace / restart</text><text x="461.6" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">from last</text><text x="461.6" y="123.0" text-anchor="middle" class="tm" style="font-size:11px">checkpoint</text><line x1="388.8" y1="60.0" x2="402.8" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/><rect x="536.4" y="28" width="113.6" height="64" rx="10" style="fill:var(--e)"/><text x="593.2" y="65.0" text-anchor="middle" class="t" style="fill:#fff;font-weight:700;font-size:12px">resume</text><text x="593.2" y="109.0" text-anchor="middle" class="tm" style="font-size:11px">lost work = time</text><text x="593.2" y="123.0" text-anchor="middle" class="tm" style="font-size:11px">since checkpoint</text><line x1="520.4" y1="60.0" x2="534.4" y2="60.0" style="stroke:var(--muted);stroke-width:2" marker-end="url(#gArr)"/></svg><p class="caption" style="margin:4px 0 0">At 16K GPUs, failures are routine; the goal is to make each one cheap.</p></div><!--/x:glance-->
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-mtbf" data-chapter="The data">
  <div class="inner">
    <div class="label">02 · The data</div>
    <h2>Cluster MTBF = per-GPU MTBF ÷ number of GPUs</h2>
    <hr>
    <p class="lede">Each H100 is quite reliable: the Llama 3 data implies about <b>50,000 hours</b> (roughly 6 years) between interruptions per GPU. But the job is only as reliable as the <em>product</em> of all its components, so the failure rate grows with the size of the cluster.</p>
    <div class="visual">
      <label class="ctl">GPUs in job <input type="range" id="mN" min="3" max="17" step="0.25" value="14"> <output id="mNo"></output></label>
      <div class="grid3" style="margin-top:14px">
        <div class="stat"><div class="num" id="mM" style="color:var(--d)"></div><div class="lbl">expected time between failures</div></div>
        <div class="stat"><div class="num" id="mDay"></div><div class="lbl">failures per day</div></div>
        <div class="stat"><div class="num" id="mP"></div><div class="lbl">chance a 24 h run has no failure</div></div>
      </div>
      <svg id="mSvg" viewBox="0 0 660 230" style="margin-top:12px" role="img" aria-label="MTBF vs cluster size"></svg>
    </div>
    <p class="caption">Assumes the Llama 3 rate (419 interruptions ÷ 54 days ÷ 16,384 GPUs ≈ 2×10⁻⁵ per GPU-hour) and independent failures. Real rates depend on hardware age (burn-in failures early, wear-out late), temperature and firmware.</p>
    <div class="takeaway">At 100K GPUs you should expect a failure about every 30 minutes. Recovery has to be <b>automatic and fast</b>; paging an engineer each time doesn't scale.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-xid" data-chapter="Failure types">
  <div class="inner">
    <div class="label">03 · Failure types</div>
    <h2>Reading the signals: Xid errors and other failure modes</h2>
    <hr>
    <p class="lede">The NVIDIA driver logs <b>Xid</b> events to the kernel log (<code>dmesg</code>). Some point to your code, some to the hardware. Click one.</p>
    <div class="visual">
      <div class="xid" id="xidBtns"></div>
      <div class="infobox" id="xidInfo"></div>
      <div class="legend"><span><i style="background:var(--d)"></i>usually hardware: drain the node</span><span><i style="background:var(--c)"></i>could be either</span><span><i style="background:var(--b)"></i>usually software / application</span></div>
    </div>
    <div class="grid4" style="margin-top:14px">
      <div class="card d"><h3>Fail-stop</h3><p>GPU off the bus, uncorrectable ECC (error-correcting code), node crash. Loud and easy to detect.</p></div>
      <div class="card c"><h3>Network</h3><p>Link flaps, bad optics or cables, switch reboots. They show up as NCCL (NVIDIA Collective Communications Library) timeouts or hangs.</p></div>
      <div class="card b"><h3>Fail-slow</h3><p>Thermal throttling, degraded links, a slow host. No error at all, just a slower job.</p></div>
      <div class="card a"><h3>Silent (SDC)</h3><p>The arithmetic is wrong and nothing reports an error. The hardest to detect (slide 08).</p></div>
    </div>
    <div class="cite">NVIDIA "XID Errors" documentation. Exact meanings vary by driver version; always confirm with <code>nvidia-smi -q</code> and DCGM.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-blast" data-chapter="Blast radius">
  <div class="inner">
    <div class="label">04 · Blast radius</div>
    <h2>Why one dead GPU stops 16,383 healthy ones</h2>
    <hr>
    <p class="lede">Synchronous training is a chain of collectives. If one rank stops contributing, every other rank <b>waits inside the all-reduce</b> until a watchdog times out. The job then has to tear down, swap the bad node and restart from the last checkpoint.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0"><button class="btn primary" id="bKill">Kill rank 5</button><button class="btn" id="bReset">Reset</button><span class="readout" id="bState"></span></div>
      <svg id="bSvg" viewBox="0 0 660 250" style="margin-top:10px" role="img" aria-label="Ranks waiting on a collective"></svg>
    </div>
    <div class="takeaway">The cost of a failure = time to detect + time to restart + <b>work lost since the last checkpoint</b>, multiplied by every GPU in the job. A 10-minute NCCL timeout on 16K GPUs wastes about 2,700 GPU-hours before anything has even been diagnosed.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-strag" data-chapter="Blast radius">
  <div class="inner">
    <div class="label">05 · Blast radius</div>
    <h2>Stragglers: a slow GPU is worse than a dead one</h2>
    <hr>
    <p class="lede">A dead GPU triggers a restart. A GPU that is <em>20% slow</em> (thermal throttling, a degraded NVLink, a noisy neighbour on the host) quietly slows <b>every step</b> of the job, and nothing raises an alarm.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">Straggler slowdown <input type="range" id="sS" min="0" max="60" step="1" value="20"> <output id="sSo"></output></label>
        <label class="ctl">Per-rank jitter <input type="range" id="sJ" min="0" max="15" step="1" value="3"> <output id="sJo"></output></label>
      </div>
      <svg id="sSvg" viewBox="0 0 660 240" style="margin-top:10px" role="img" aria-label="Per-rank step times"></svg>
      <div class="grid3">
        <div class="stat"><div class="num" id="sStep"></div><div class="lbl">step time (= slowest rank)</div></div>
        <div class="stat"><div class="num" id="sEff" style="color:var(--d)"></div><div class="lbl">job efficiency</div></div>
        <div class="stat"><div class="num" id="sCost"></div><div class="lbl">GPU-hours wasted per day (16K GPUs)</div></div>
      </div>
    </div>
    <div class="takeaway">Detect stragglers by timing each rank's compute and communication, for example with the NCCL flight recorder, per-rank step-time histograms, or comparing a rank's GEMM (general matrix multiplication) TFLOPS (trillion floating-point operations per second) with its peers. Then evict the slow node like a dead one.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-ckpt" data-chapter="Recovery">
  <div class="inner">
    <div class="label">06 · Recovery</div>
    <h2>Checkpoint interval: frequent saves vs. lost work</h2>
    <hr>
    <p class="lede">Checkpointing often means more time spent saving. Checkpointing rarely means more work lost per failure. The optimum is about <code>τ* ≈ √(2 · δ · MTBF)</code> (Young/Daly), where δ is the time the training loop is blocked while saving.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">Cluster MTBF <input type="range" id="cM" min="0.25" max="24" step="0.25" value="3"> <output id="cMo"></output></label>
        <label class="ctl">Checkpoint stall δ <input type="range" id="cD" min="0.5" max="20" step="0.5" value="5"> <output id="cDo"></output></label>
        <label class="ctl">Restart cost R <input type="range" id="cR" min="1" max="60" step="1" value="20"> <output id="cRo"></output></label>
        <label class="ctl">Interval τ <input type="range" id="cT" min="5" max="360" step="5" value="120"> <output id="cTo"></output></label>
      </div>
      <div class="grid2" style="margin-top:12px">
        <svg id="cSvg" viewBox="0 0 360 220" role="img" aria-label="Goodput vs checkpoint interval"></svg>
        <div>
          <div class="grid2">
            <div class="stat"><div class="num" id="cG" style="color:var(--a)"></div><div class="lbl">goodput at your τ</div></div>
            <div class="stat"><div class="num" id="cOpt" style="color:var(--e)"></div><div class="lbl">optimal τ* (goodput)</div></div>
          </div>
          <h3 style="margin-top:14px">Simulated 24 hours</h3>
          <svg id="cTl" viewBox="0 0 360 80" role="img" aria-label="Simulated timeline"></svg>
          <div class="legend"><span><i style="background:var(--a)"></i>useful</span><span><i style="background:var(--c)"></i>checkpoint stall</span><span><i style="background:var(--d)"></i>lost work</span><span><i style="background:var(--faint)"></i>restart</span></div>
        </div>
      </div>
    </div>
    <div class="takeaway">Lowering δ is what moves the curve, and <b>async checkpointing</b> does that: snapshot the state to CPU (central processing unit) memory in seconds, then write it to storage in the background. Then you can checkpoint every few minutes.</div>
  </div>
</section>

<!-- slide id="s-example" from="example" chapter="Example" tag="Worked example" tagclass="b5" -->

<!-- slide raw -->
<section class="slide" id="s-fast" data-chapter="Recovery">
  <div class="inner">
    <div class="label">07 · Recovery</div>
    <h2>Making each failure cheap</h2>
    <hr>
    <p class="lede">Turn on each technique to see what it removes from the time lost per failure. The cluster is 16K GPUs with a failure about every 3 hours.</p>
    <div class="visual">
      <div class="toggles" id="fxT">
        <label><input type="checkbox" data-k="hb"> Fast detection (heartbeats, not a 10-min timeout)</label>
        <label><input type="checkbox" data-k="spare"> Hot spare nodes</label>
        <label><input type="checkbox" data-k="mem"> In-memory / peer checkpoints</label>
        <label><input type="checkbox" data-k="async"> Async checkpoints every 10 min (vs. hourly)</label>
        <label><input type="checkbox" data-k="warm"> Warm restart (keep processes, skip re-init)</label>
      </div>
      <svg id="fxSvg" viewBox="0 0 660 120" style="margin-top:14px" role="img" aria-label="Recovery breakdown"></svg>
      <div class="legend"><span><i style="background:var(--b)"></i>detect</span><span><i style="background:var(--faint)"></i>replace node / reschedule</span><span><i style="background:var(--c)"></i>re-init + load checkpoint</span><span><i style="background:var(--d)"></i>recompute lost work</span></div>
      <div class="grid3" style="margin-top:10px">
        <div class="stat"><div class="num" id="fxPer"></div><div class="lbl">lost per failure</div></div>
        <div class="stat"><div class="num" id="fxDay" style="color:var(--d)"></div><div class="lbl">GPU-hours lost per day</div></div>
        <div class="stat"><div class="num" id="fxGood" style="color:var(--e)"></div><div class="lbl">effective training time</div></div>
      </div>
    </div>
    <div class="takeaway">Labs build all of this: health-check daemons, spare pools, in-memory checkpoint replication (for example Gemini-style or ByteDance-style systems), and elastic or partial restarts. Llama 3 reached more than 90% effective training time with automation.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-sdc" data-chapter="Silent errors">
  <div class="inner">
    <div class="label">08 · Silent errors</div>
    <h2>Silent data corruption: the GPU gives a wrong answer and reports nothing</h2>
    <hr>
    <p class="lede">A defective ALU (arithmetic logic unit), a marginal voltage or an aging part can flip bits in a computation without triggering ECC. Training continues on bad numbers. Sometimes the loss spikes; sometimes the model just gets subtly worse.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0"><button class="btn primary" id="sdcGo">Inject SDC at step 600</button><button class="btn" id="sdcReset">Reset</button>
        <label class="ctl">Detector threshold (σ) <input type="range" id="sdcZ" min="2" max="8" step="0.5" value="4"> <output id="sdcZo"></output></label></div>
      <svg id="sdcSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Loss curve with SDC"></svg>
      <p class="readout" id="sdcOut"></p>
    </div>
    <div class="grid4" style="margin-top:12px">
      <div class="card a"><h3>Loss / grad-norm monitors</h3><p>Flag spikes against a rolling z-score, then roll back and skip the batch.</p></div>
      <div class="card c"><h3>Cross-replica checks</h3><p>DP (data parallelism) replicas should hold identical weights. Compare checksums periodically.</p></div>
      <div class="card b"><h3>Deterministic replay</h3><p>Re-run the suspicious step on other hardware and diff the results.</p></div>
      <div class="card e"><h3>Known-answer tests</h3><p>Periodic GEMM tests with known answers, run during the job or in preflight.</p></div>
    </div>
    <div class="cite">Meta, "Detecting silent errors in the wild" (2022); Google, "Cores that don't count" (HotOS 2021). Llama 3 attributed 6 of 419 interruptions to SDC.</div>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-ops" data-chapter="Silent errors">
  <div class="inner">
    <div class="label">09 · Operations</div>
    <h2>The node lifecycle in a well-run cluster</h2>
    <hr>
    <div class="flow">
      <div class="card e"><h3>1 · Burn-in</h3><p>New nodes run multi-day stress tests (GEMM, HBM (high-bandwidth memory), NVLink, NCCL) to catch early failures before they join production.</p></div>
      <div class="card a"><h3>2 · Preflight</h3><p>Before each job: <code>dcgmi diag</code>, an NCCL all-reduce check against expected busbw, a GEMM TFLOPS check, and ECC / row-remap counters.</p></div>
      <div class="card b"><h3>3 · In-job monitoring</h3><p>Xid watchers, per-rank step-time telemetry, NIC (network interface card) counters, temperature and clocks. Automatic cordon on anomalies.</p></div>
      <div class="card d"><h3>4 · Quarantine / RMA</h3><p>Failing nodes are drained, re-tested, repaired or sent back to the vendor. A node returns only after it passes burn-in again.</p></div>
    </div>
    <div class="takeaway">"How would you design fault tolerance for a 10K-GPU training job?" Cover five layers: <b>prevent</b> (burn-in, preflight), <b>detect</b> (fast, per-rank), <b>contain</b> (cordon, spares), <b>recover</b> (async and in-memory checkpoints, warm restart), <b>verify</b> (SDC (silent data corruption) checks).</div>
  </div>
</section>

<!-- slide id="s-traps" from="traps" chapter="Traps" tag="Tricks and traps" tagclass="b7" -->

<!-- slide raw -->
<section class="slide" id="s-qa" data-chapter="Test yourself">
  <div class="inner">
    <div class="label">10 · Test yourself</div>
    <h2>Questions to test your understanding</h2>
    <hr>
    <details class="qa"><summary>Your 4K-GPU job hangs at step 30,000 with no error. How do you debug it?</summary><div class="ans">A hang means some rank isn't entering, or isn't finishing, a collective. Steps: (1) Use the <b>NCCL flight recorder</b> or dumps to see which collective each rank is stuck in and which rank is missing. (2) Use <code>py-spy dump</code> on the stuck ranks for the Python stack. (3) Check that node's <code>dmesg</code> for Xid errors, NIC and link counters, and thermal throttling. (4) Look for a code-level cause, such as data-dependent control flow making ranks issue collectives in different orders. Then cordon the node and restart from checkpoint, with a shorter watchdog timeout in future.</div></details>
    <details class="qa"><summary>How often should you checkpoint a 16K-GPU run?</summary><div class="ans">Use Young/Daly: τ* ≈ √(2δM). With an MTBF of about 3 h and a 5-minute blocking checkpoint, τ* ≈ √(2 × 5 × 180) ≈ 42 minutes. With async checkpointing the stall drops to about 10–30 s, which gives τ* ≈ 10 minutes and much less lost work. Also check storage bandwidth: a 405B model with optimizer state is about 6 TB, so how fast you can write it (and spreading the writes across ranks) matters.</div></details>
    <details class="qa"><summary>What's the difference between fail-stop, fail-slow and silent failures?</summary><div class="ans"><b>Fail-stop</b>: the component dies and reports an error (Xid 79, uncorrectable ECC), so it's easy to detect and the response is restart. <b>Fail-slow</b>: it works, but degraded (throttling, link down-training), so the whole synchronous job slows and you need per-rank telemetry to find it. <b>Silent</b> (SDC): wrong results with no error. You need numerical monitors, cross-replica checksums and replay. Many teams consider SDC the most dangerous because it can damage the model without anyone noticing.</div></details>
    <details class="qa"><summary>Why not just make training asynchronous so failures don't block everyone?</summary><div class="ans">Asynchronous or stale-gradient SGD (stochastic gradient descent) hurts convergence and reproducibility at LLM (large language model) scale. Synchronous data parallelism with large batches is the proven approach. The industry made synchronous training <em>resilient</em> instead: fast detection, hot spares and cheap checkpoints. There is research on elastic and partial-failure-tolerant training (for example dropping a DP replica for a few steps), but it isn't yet the default.</div></details>
  </div>
</section>

<!-- slide raw -->
<section class="slide" id="s-end" data-chapter="Test yourself">
  <div class="inner">
    <div class="label">11 · Take it with you</div>
    <h2>Four things to remember</h2>
    <hr>
    <div class="recap">
      <div><span><b>Failures scale linearly with GPU count.</b> At 16K H100s, expect one about every 3 hours, mostly from the GPU and HBM.</span></div>
      <div><span><b>One fault stops the whole synchronous job</b>, and stragglers slow every step without raising an error.</span></div>
      <div><span><b>Optimal checkpoint interval ≈ √(2δ·MTBF).</b> Async and in-memory checkpoints reduce δ, and the lost work along with it.</span></div>
      <div><span><b>Prevent, detect, contain, recover, verify</b>, with SDC as the silent risk that needs active checks.</span></div>
    </div>
    <p class="start-hint">Next: <a href="../07-heterogeneous-gpus/index.html">07 · Heterogeneous GPUs →</a> · Previous: <a href="../05-cluster-topology/index.html">← 05</a></p>
  </div>
</section>

<!-- slide id="s-papers" from="papers" -->
