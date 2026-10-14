(() => {
  const { svg, clear, fmt } = Deck;
  const rng = seed => () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };

  /* Llama table */
  const L3 = [
    ['Faulty GPU', 148, 1], ['GPU HBM3 memory', 72, 1], ['Software bug', 54, 0], ['Network switch / cable', 35, 0],
    ['Host maintenance', 32, 0], ['GPU SRAM memory', 19, 1], ['GPU system processor', 17, 1], ['NIC', 7, 0],
    ['NCCL watchdog timeouts', 7, 0], ['Silent data corruption', 6, 1], ['GPU thermal / sensor', 6, 1], ['SSD', 3, 0],
    ['Power supply', 3, 0], ['Other (chassis, CPU, DRAM, …)', 10, 0],
  ];
  Deck.seg('llSeg', v => {
    const rows = L3.filter(r => v === 'all' || r[2]);
    Deck.hbars(document.getElementById('llBars'), rows.map(r => ({ label: r[0], value: r[1], color: r[2] ? 'var(--d)' : 'var(--faint)', text: `${r[1]} · ${(100 * r[1] / 419).toFixed(1)}%` })), { max: 150 });
  });

  /* MTBF */
  const LAMBDA = 419 / (54 * 24) / 16384;
  Deck.bind(['mN'], () => {
    const N = Math.round(Math.pow(2, Deck.val('mN')));
    Deck.out('mNo', N.toLocaleString());
    const M = 1 / (LAMBDA * N);
    Deck.out('mM', M >= 48 ? (M / 24).toFixed(1) + ' days' : M >= 1 ? M.toFixed(1) + ' h' : (M * 60).toFixed(0) + ' min');
    Deck.out('mDay', (24 / M).toFixed(24 / M < 1 ? 2 : 1));
    const p = Math.exp(-24 / M);
    Deck.out('mP', p < 0.001 ? '≈ 0%' : (100 * p).toFixed(p > .1 ? 0 : 1) + '%');
    const s = clear(document.getElementById('mSvg'));
    const L = 70, R = 640, T = 10, B = 190;
    const X = n => L + (Math.log2(n) - 3) / 14 * (R - L);
    const Y = h => B - (Math.log10(h) + 1) / 5 * (B - T);
    [[0.1, '6 min'], [1, '1 h'], [10, '10 h'], [100, '4 days'], [1000, '6 wks']].forEach(([h, t]) => {
      svg('line', { x1: L, x2: R, y1: Y(h), y2: Y(h), class: 'ln' }, s);
      svg('text', { x: L - 6, y: Y(h) + 4, 'text-anchor': 'end', class: 'tm tc', style: 'font-size:10px', text: t }, s);
    });
    [8, 64, 512, 4096, 32768, 131072].forEach(n => svg('text', { x: X(n), y: B + 16, 'text-anchor': 'middle', class: 'tm tc', style: 'font-size:10px', text: fmt(n, 0) }, s));
    svg('text', { x: (L + R) / 2, y: B + 34, 'text-anchor': 'middle', class: 'tm', text: 'GPUs in the job' }, s);
    let pts = '';
    for (let n = 8; n <= 131072; n *= 1.2) pts += `${X(n)},${Y(Math.min(5000, 1 / (LAMBDA * n)))} `;
    svg('polyline', { points: pts, fill: 'none', style: 'stroke:var(--d);stroke-width:3' }, s);
    svg('circle', { cx: X(16384), cy: Y(1 / (LAMBDA * 16384)), r: 5, style: 'fill:var(--faint)' }, s);
    svg('text', { x: X(16384) + 8, y: Y(1 / (LAMBDA * 16384)) - 8, class: 'tm', style: 'font-size:11px', text: 'Llama 3 405B' }, s);
    svg('circle', { cx: X(N), cy: Y(Math.min(5000, M)), r: 8, style: 'fill:var(--d);stroke:var(--panel);stroke-width:2' }, s);
  });

  /* Xid */
  const XID = [
    ['13', 'sw', 'Graphics engine exception', 'Usually an <b>application bug</b>, such as an out-of-bounds access in a kernel. If it repeats on one GPU across different jobs, suspect the hardware.'],
    ['31', 'sw', 'GPU memory page fault (MMU)', 'An illegal address was accessed. Almost always an <b>application or driver bug</b> (bad pointer, use-after-free in custom kernels).'],
    ['43', 'sw', 'GPU stopped processing', 'Usually follows a user-application fault. The context is killed and the GPU itself stays healthy.'],
    ['48', 'hw', 'Double-bit ECC error (DBE)', '<b>Uncorrectable memory error.</b> The application is killed. Reset the GPU so the bad row is remapped, and RMA it if the errors recur.'],
    ['63 / 64', 'hw', 'Row remapping event / failure', 'HBM rows are being retired and remapped to spare rows. <b>64 = remapping failed</b> (no spare rows left), so pull the GPU for RMA.'],
    ['74', 'mixed', 'NVLink error', 'A link-level error between a GPU and NVSwitch. A one-off can be cleared by a reset; repeated errors mean a bad link or baseboard.'],
    ['79', 'hw', 'GPU has fallen off the bus', '<b>The GPU stopped responding on PCIe.</b> Severe (power, thermal or hardware). Drain the node, power-cycle it and run diagnostics.'],
    ['94 / 95', 'hw', 'Contained / uncontained ECC error', '94: the error was contained to one application, which is killed, and the GPU keeps working. <b>95: uncontained, so the GPU must be reset</b> and every process on it is affected.'],
    ['119 / 120', 'mixed', 'GSP timeout / error', 'The GPU System Processor (on-chip firmware controller) didn\'t respond. Often fixed by a reset or a driver/firmware update; recurring on one GPU means hardware.'],
  ];
  const xb = document.getElementById('xidBtns');
  xb.innerHTML = XID.map((x, i) => `<button data-i="${i}" data-sev="${x[1]}">Xid ${x[0]}</button>`).join('');
  const pickX = i => {
    const x = XID[i];
    Deck.$$('button', xb).forEach(b => b.classList.toggle('on', +b.dataset.i === i));
    document.getElementById('xidInfo').innerHTML = `<b>Xid ${x[0]}: ${x[2]}</b><br>${x[3]}`;
  };
  xb.addEventListener('click', e => { const b = e.target.closest('button'); if (b) pickX(+b.dataset.i); });
  pickX(6);

  /* blast radius */
  let killed = false, killT = 0;
  const drawBlast = t => {
    const s = clear(document.getElementById('bSvg'));
    const n = 8, cx = 330, cy = 120, r = 90;
    svg('circle', { cx, cy, r: 30, style: 'fill:var(--panel-2);stroke:var(--line)' }, s);
    svg('text', { x: cx, y: cy - 2, 'text-anchor': 'middle', class: 't', style: 'font-size:11px;font-weight:600', text: 'all-reduce' }, s);
    svg('text', { x: cx, y: cy + 13, 'text-anchor': 'middle', class: 'tm', style: 'font-size:10px', text: killed ? 'waiting…' : 'step ' + Math.floor(t * 2) }, s);
    const el = killed ? t - killT : 0, timeout = 6;
    for (let i = 0; i < n; i++) {
      const a = i / n * Math.PI * 2 - Math.PI / 2, x = cx + Math.cos(a) * r * 1.6, y = cy + Math.sin(a) * r;
      const dead = killed && i === 5, aborted = killed && el > timeout;
      const pulse = !killed ? (Math.sin(t * 6 + i) > 0) : false;
      svg('line', { x1: x, y1: y, x2: cx + Math.cos(a) * 30, y2: cy + Math.sin(a) * 30, style: `stroke:${dead ? 'var(--d)' : killed ? 'var(--b)' : 'var(--a)'};stroke-width:${pulse ? 4 : 2};stroke-dasharray:${dead ? '4 4' : 'none'}` }, s);
      svg('rect', { x: x - 34, y: y - 18, width: 68, height: 36, rx: 7, style: `fill:${dead ? 'var(--d)' : aborted ? 'var(--faint)' : killed ? 'var(--b)' : 'var(--a)'}` }, s);
      svg('text', { x, y: y + 4, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11.5px;font-weight:600', text: dead ? '✕ rank 5' : aborted ? 'aborted' : killed ? 'blocked' : 'rank ' + i }, s);
    }
    if (killed) {
      const w = Math.min(1, el / timeout) * 300;
      svg('rect', { x: 180, y: 232, width: 300, height: 10, rx: 5, class: 'f-panel' }, s);
      svg('rect', { x: 180, y: 232, width: w, height: 10, rx: 5, style: `fill:${el > timeout ? 'var(--d)' : 'var(--b)'}` }, s);
      svg('text', { x: 172, y: 241, 'text-anchor': 'end', class: 'tm', style: 'font-size:10.5px', text: 'watchdog' }, s);
      Deck.out('bState', el > timeout ? '⏱ Timeout: whole job aborts → cordon node → restart from checkpoint' : '7 healthy ranks idle, waiting for rank 5 …');
    } else Deck.out('bState', 'Healthy: every rank joins every all-reduce');
  };
  Deck.enter('s-blast', () => {
    let tt = 0;
    document.getElementById('bKill').onclick = () => { if (!killed) { killed = true; killT = tt; } };
    document.getElementById('bReset').onclick = () => { killed = false; };
    return Deck.loop(t => { tt = t; drawBlast(t); });
  });
  drawBlast(0);

  /* stragglers */
  Deck.bind(['sS', 'sJ'], () => {
    const slow = Deck.val('sS') / 100, jit = Deck.val('sJ') / 100;
    Deck.out('sSo', '+' + (slow * 100).toFixed(0) + '%'); Deck.out('sJo', '±' + (jit * 100).toFixed(0) + '%');
    const r = rng(7), n = 32, base = 1.0;
    const t = [...Array(n)].map((_, i) => base * (1 + (r() * 2 - 1) * jit) * (i === 19 ? 1 + slow : 1));
    const mx = Math.max(...t), mean = t.reduce((a, b) => a + b, 0) / n;
    const s = clear(document.getElementById('sSvg'));
    const L = 40, W = 610, B = 200, H = 170, sc = H / 1.7;
    t.forEach((v, i) => {
      const x = L + i * (W / n);
      svg('rect', { x, y: B - v * sc, width: W / n - 3, height: v * sc, style: `fill:${v === mx ? 'var(--d)' : 'var(--a)'};opacity:${v === mx ? 1 : .75}` }, s);
      svg('rect', { x, y: B - mx * sc, width: W / n - 3, height: (mx - v) * sc, style: 'fill:var(--d-soft)' }, s);
    });
    svg('line', { x1: L, x2: L + W, y1: B - mx * sc, y2: B - mx * sc, style: 'stroke:var(--d);stroke-dasharray:5 4;stroke-width:2' }, s);
    svg('text', { x: L + W, y: B - mx * sc - 6, 'text-anchor': 'end', class: 't', style: 'fill:var(--d);font-size:11px;font-weight:600', text: 'everyone waits until here' }, s);
    svg('text', { x: L + W / 2, y: B + 18, 'text-anchor': 'middle', class: 'tm', text: 'ranks (shaded = idle waiting at the collective)' }, s);
    Deck.out('sStep', (mx / base).toFixed(2) + '×');
    const eff = mean / mx;
    Deck.out('sEff', (eff * 100).toFixed(0) + '%');
    Deck.out('sCost', fmt(16384 * 24 * (1 - eff), 0));
  });

  /* checkpoint */
  Deck.bind(['cM', 'cD', 'cR', 'cT'], () => {
    const M = Deck.val('cM') * 60, d = Deck.val('cD'), R = Deck.val('cR'), tau = Deck.val('cT');
    Deck.out('cMo', Deck.val('cM') + ' h'); Deck.out('cDo', d + ' min'); Deck.out('cRo', R + ' min'); Deck.out('cTo', tau + ' min');
    const good = x => Math.max(0, (x / (x + d)) * (1 - (R + (x + d) / 2) / M));
    let best = 5; for (let x = 1; x <= 600; x += 0.5) if (good(x) > good(best)) best = x;
    Deck.out('cG', (100 * good(tau)).toFixed(1) + '%');
    Deck.out('cOpt', `${best.toFixed(0)} min · ${(100 * good(best)).toFixed(1)}%`);
    const s = clear(document.getElementById('cSvg'));
    const L = 40, Rr = 350, T = 10, B = 180, X = x => L + x / 360 * (Rr - L), Y = g => B - g * (B - T);
    [0, .25, .5, .75, 1].forEach(g => { svg('line', { x1: L, x2: Rr, y1: Y(g), y2: Y(g), class: 'ln' }, s); svg('text', { x: L - 4, y: Y(g) + 4, 'text-anchor': 'end', class: 'tm tc', style: 'font-size:9.5px', text: (g * 100) + '%' }, s); });
    [0, 60, 120, 180, 240, 300, 360].forEach(x => svg('text', { x: X(x), y: B + 14, 'text-anchor': 'middle', class: 'tm tc', style: 'font-size:9.5px', text: x }, s));
    svg('text', { x: (L + Rr) / 2, y: B + 30, 'text-anchor': 'middle', class: 'tm', style: 'font-size:10.5px', text: 'checkpoint interval τ (min)' }, s);
    let pts = ''; for (let x = 2; x <= 360; x += 2) pts += `${X(x)},${Y(good(x))} `;
    svg('polyline', { points: pts, fill: 'none', style: 'stroke:var(--a);stroke-width:2.5' }, s);
    svg('line', { x1: X(best), x2: X(best), y1: T, y2: B, style: 'stroke:var(--e);stroke-dasharray:4 3' }, s);
    svg('circle', { cx: X(tau), cy: Y(good(tau)), r: 6, style: 'fill:var(--a);stroke:var(--panel);stroke-width:2' }, s);
    // timeline simulation
    const tl = clear(document.getElementById('cTl')), r = rng(42), DAY = 1440, sx = 350 / DAY;
    let t = 0, lastCk = 0, nextFail = -Math.log(1 - r()) * M, sinceCk = 0;
    const seg = (a, b, c) => svg('rect', { x: 5 + a * sx, y: 14, width: Math.max(.4, (b - a) * sx), height: 36, style: `fill:${c}` }, tl);
    let fails = 0;
    while (t < DAY) {
      const nextCk = t + (tau - sinceCk);
      if (nextFail < nextCk && nextFail < DAY) {
        seg(t, nextFail, 'var(--a)');
        const lostStart = nextFail - (sinceCk + (nextFail - t));
        seg(Math.max(0, lostStart), nextFail, 'var(--d)');
        seg(nextFail, Math.min(DAY, nextFail + R), 'var(--faint)');
        t = nextFail + R; sinceCk = 0; fails++;
        nextFail = t - Math.log(1 - r()) * M;
      } else {
        const end = Math.min(DAY, nextCk);
        seg(t, end, 'var(--a)'); if (end >= DAY) break;
        seg(end, Math.min(DAY, end + d), 'var(--c)');
        t = end + d; sinceCk = 0;
        if (nextFail < t) { nextFail = t - Math.log(1 - r()) * M; }
      }
    }
    svg('text', { x: 5, y: 68, class: 'tm', style: 'font-size:10px', text: `0 h` }, tl);
    svg('text', { x: 355, y: 68, 'text-anchor': 'end', class: 'tm', style: 'font-size:10px', text: `24 h · ${fails} failures` }, tl);
  });

  /* fast recovery */
  const fx = () => {
    const on = {}; Deck.$$('#fxT input').forEach(i => on[i.dataset.k] = i.checked);
    const parts = [
      ['detect', on.hb ? 1 : 10, 'var(--b)'],
      ['replace', on.spare ? 3 : 15, 'var(--faint)'],
      ['load', (on.warm ? 2 : 6) + (on.mem ? 1 : 6), 'var(--c)'],
      ['recompute', on.async ? 5 : 30, 'var(--d)'],
    ];
    const tot = parts.reduce((a, p) => a + p[1], 0);
    const s = clear(document.getElementById('fxSvg'));
    const sc = 620 / 80; let x = 20;
    parts.forEach(([n, v, c]) => {
      svg('rect', { x, y: 20, width: v * sc, height: 44, style: `fill:${c}` }, s);
      if (v * sc > 40) svg('text', { x: x + v * sc / 2, y: 47, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11.5px;font-weight:600', text: v + ' min' }, s);
      x += v * sc;
    });
    for (let m = 0; m <= 75; m += 15) svg('text', { x: 20 + m * sc, y: 86, 'text-anchor': 'middle', class: 'tm tc', style: 'font-size:10px', text: m + ' min' }, s);
    const perDay = 24 / 3, lostH = tot / 60 * perDay;
    Deck.out('fxPer', tot + ' min');
    Deck.out('fxDay', fmt(lostH * 16384, 0));
    Deck.out('fxGood', (100 * (1 - lostH / 24)).toFixed(0) + '%');
  };
  Deck.$$('#fxT input').forEach(i => i.addEventListener('change', fx));
  fx();

  /* SDC */
  let injected = false;
  const sdc = () => {
    const z = Deck.val('sdcZ'); Deck.out('sdcZo', z + 'σ');
    const r = rng(3), n = 1000, loss = [];
    for (let i = 0; i < n; i++) {
      let v = 2.2 + 2.0 * Math.exp(-i / 180) + (r() - .5) * 0.06;
      if (injected && i >= 600 && i < 606) v += [0.9, 0.5, 0.25, 0.12, 0.06, 0.03][i - 600];
      if (injected && i >= 606) v += 0.03;
      loss.push(v);
    }
    let flagged = -1;
    for (let i = 50; i < n; i++) {
      const w = loss.slice(i - 50, i), m = w.reduce((a, b) => a + b, 0) / 50, sd = Math.sqrt(w.reduce((a, b) => a + (b - m) ** 2, 0) / 50);
      if ((loss[i] - m) / sd > z) { flagged = i; break; }
    }
    const s = clear(document.getElementById('sdcSvg'));
    const L = 40, R = 650, T = 10, B = 200, X = i => L + i / n * (R - L), Y = v => B - (v - 2) / 2.6 * (B - T);
    svg('polyline', { points: loss.map((v, i) => `${X(i)},${Y(v)}`).join(' '), fill: 'none', style: 'stroke:var(--a);stroke-width:1.6' }, s);
    svg('text', { x: (L + R) / 2, y: B + 22, 'text-anchor': 'middle', class: 'tm', text: 'training step' }, s);
    svg('text', { x: L - 6, y: Y(4) + 4, 'text-anchor': 'end', class: 'tm', style: 'font-size:10px', text: 'loss' }, s);
    if (injected) svg('line', { x1: X(600), x2: X(600), y1: T, y2: B, style: 'stroke:var(--d);stroke-dasharray:4 3' }, s);
    const out = document.getElementById('sdcOut');
    if (!injected) out.innerHTML = 'Clean run. Lower the threshold to see false alarms.';
    if (flagged >= 0) {
      svg('circle', { cx: X(flagged), cy: Y(loss[flagged]), r: 8, style: 'fill:none;stroke:var(--d);stroke-width:2.5' }, s);
      out.innerHTML = injected && flagged >= 600 ? `<span style="color:var(--e)">Detected at step ${flagged}</span> → roll back to the last checkpoint, skip the batch, run a known-answer test on the suspect hosts.`
        : `<span style="color:var(--b)">False alarm at step ${flagged}</span>: threshold too low, so routine noise triggers a rollback.`;
    } else if (injected) out.innerHTML = '<span style="color:var(--d)">Not detected</span>: the spike stays below the threshold, and the corruption leaves a small, permanent loss offset.';
  };
  document.getElementById('sdcGo').onclick = () => { injected = true; sdc(); };
  document.getElementById('sdcReset').onclick = () => { injected = false; sdc(); };
  Deck.bind(['sdcZ'], sdc);
})();
