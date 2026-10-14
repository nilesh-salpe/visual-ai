(() => {
  const { svg, clear, fmt } = Deck;

  let seed = 3;
  const rng = s => () => { s |= 0; s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  const mk = () => { const r = rng(seed); let t = 0; return [...Array(14)].map((_, i) => { t += Math.floor(r() * 4); return { id: i, arrival: t, out: 3 + Math.floor(r() * r() * 22) }; }); };
  const staticSim = (reqs, B) => { const res = {}; let t = 0; for (let i = 0; i < reqs.length; i += B) { const g = reqs.slice(i, i + B), st = Math.max(t, ...g.map(q => q.arrival)), mx = Math.max(...g.map(q => q.out)); g.forEach((q, k) => res[q.id] = { slot: k, s: st, e: st + q.out, hold: st + mx }); t = st + mx; } return res; };
  const contSim = (reqs, B) => { const res = {}, q = reqs.slice(), slots = Array(B).fill(-1); let t = 0, done = 0; while (done < reqs.length) { for (let k = 0; k < B; k++) if (slots[k] >= 0 && res[slots[k]].e <= t) { slots[k] = -1; done++; } for (let k = 0; k < B; k++) if (slots[k] < 0 && q.length && q[0].arrival <= t) { const r = q.shift(); slots[k] = r.id; res[r.id] = { slot: k, s: t, e: t + r.out, hold: t + r.out }; } if (slots.every(x => x < 0)) { if (q.length) t = q[0].arrival; else break; continue; } t++; } return res; };
  const draw = (el, res, reqs, B, T) => {
    const s = clear(el), w = 300 / T, h = Math.min(30, 180 / B);
    for (let k = 0; k < B; k++) svg('rect', { x: 10, y: 10 + k * h, width: 300, height: h - 3, style: 'fill:var(--panel-2)' }, s);
    reqs.forEach(q => { const r = res[q.id]; if (r.hold > r.e) svg('rect', { x: 10 + r.e * w, y: 10 + r.slot * h, width: (r.hold - r.e) * w, height: h - 3, style: 'fill:var(--d-soft);stroke:var(--d);stroke-width:.5' }, s); svg('rect', { x: 10 + r.s * w, y: 10 + r.slot * h, width: Math.max(1, q.out * w - 1), height: h - 3, rx: 2, style: `fill:${['var(--a)', 'var(--b)', 'var(--c)', 'var(--e)', '#3a8fd8', '#c9a227'][q.id % 6]}` }, s); });
    el.setAttribute('viewBox', `0 0 320 ${20 + B * h}`);
  };
  const run = () => {
    const B = Deck.val('cbB'); Deck.out('cbBo', B);
    const reqs = mk(), st = staticSim(reqs, B), ct = contSim(reqs, B);
    const T = Math.max(...Object.values(st).map(r => r.hold), ...Object.values(ct).map(r => r.e)) + 1;
    draw(document.getElementById('stSvg'), st, reqs, B, T); draw(document.getElementById('ctSvg'), ct, reqs, B, T);
    const m = res => { const fin = Math.max(...Object.values(res).map(r => r.e)); const lat = reqs.map(q => res[q.id].e - q.arrival); return `done at step <b>${fin}</b> · mean latency <b>${(lat.reduce((a, b) => a + b, 0) / lat.length).toFixed(1)}</b> steps`; };
    document.getElementById('stOut').innerHTML = m(st); document.getElementById('ctOut').innerHTML = m(ct);
  };
  document.getElementById('cbNew').onclick = () => { seed++; run(); };
  Deck.bind(['cbB'], run);

})();
