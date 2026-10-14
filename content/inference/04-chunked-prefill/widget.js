(() => {
  const { svg, clear, fmt } = Deck;

  const reqs = (() => { let s = 7; const r = () => { s = (s * 1103515245 + 12345) % 2147483648; return s / 2147483648; }; let t = 0; return [...Array(14)].map((_, i) => { t += Math.floor(r() * 4); return { id: i, arrival: t, P: [64, 128, 512, 1500][Math.floor(r() * 4)], O: 5 + Math.floor(r() * 30) }; }); })();
  const prefillFirst = () => { let i = 0, t = 0; const dec = [], left = {}, its = []; while (i < reqs.length || dec.length) { const w = []; while (i < reqs.length && reqs[i].arrival <= t) w.push(reqs[i++]); if (w.length) { its.push({ d: 0, p: w.reduce((a, r) => a + r.P, 0) }); w.forEach(r => { left[r.id] = r.O - 1; if (left[r.id] > 0) dec.push(r); }); } else if (dec.length) { its.push({ d: dec.length, p: 0 }); for (const r of dec.slice()) { if (--left[r.id] === 0) dec.splice(dec.indexOf(r), 1); } } else { t = reqs[i].arrival; continue; } t++; } return its; };
  const chunked = B => { const pre = {}, left = {}; reqs.forEach(r => { pre[r.id] = r.P; left[r.id] = r.O; }); const dec = [], its = []; let t = 0, done = 0; while (done < reqs.length) { let used = 0, d = 0; for (const r of dec.slice()) { used++; d++; if (--left[r.id] === 0) { dec.splice(dec.indexOf(r), 1); done++; } } for (const r of reqs) { if (r.arrival > t || pre[r.id] === 0 || used >= B) continue; const c = Math.min(pre[r.id], B - used); pre[r.id] -= c; used += c; if (pre[r.id] === 0) { if (--left[r.id] === 0) done++; else dec.push(r); } } if (!used) { t = Math.min(...reqs.filter(r => pre[r.id] > 0).map(r => r.arrival)); continue; } its.push({ d, p: used - d }); t++; } return its; };
  const bars = (el, its, cap, ymax) => { const s = clear(el), w = 640 / Math.max(its.length, 60); its.forEach((it, k) => { const hd = 100 * it.d / ymax, hp = 100 * it.p / ymax; svg('rect', { x: 10 + k * w, y: 110 - hd, width: Math.max(1, w - 1), height: hd, style: 'fill:var(--b)' }, s); svg('rect', { x: 10 + k * w, y: 110 - hd - hp, width: Math.max(1, w - 1), height: hp, style: `fill:${cap && it.d + it.p > cap ? 'var(--d)' : 'var(--a)'}` }, s); }); if (cap) { const y = 110 - 100 * cap / ymax; svg('line', { x1: 10, x2: 650, y1: y, y2: y, style: 'stroke:var(--ink);stroke-dasharray:4 3' }, s); svg('text', { x: 650, y: y - 4, 'text-anchor': 'end', class: 'tm tc', style: 'font-size:10px', text: 'budget ' + cap }, s); } };
  Deck.bind(['ckB'], () => {
    const B = Deck.val('ckB'); Deck.out('ckBo', B);
    const pf = prefillFirst(), ck = chunked(B), ymax = Math.max(...pf.map(i => i.d + i.p), B) * 1.05;
    bars(document.getElementById('pfSvg'), pf, B, ymax); bars(document.getElementById('ckSvg'), ck, B, ymax);
    document.getElementById('ckOut').innerHTML = `Largest iteration: prefill-first <b style="color:var(--d)">${Math.max(...pf.map(i => i.d + i.p))}</b> tokens vs chunked <b style="color:var(--e)">${Math.max(...ck.map(i => i.d + i.p))}</b> tokens · chunked needs ${ck.length} iterations vs ${pf.length}.`;
  });

})();
