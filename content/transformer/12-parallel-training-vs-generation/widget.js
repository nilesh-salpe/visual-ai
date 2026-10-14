(() => {
  const { svg, clear } = Deck;

  /* step counts */
  Deck.bind(['tM'], () => {
    const m = Deck.val('tM'); Deck.out('tMo', m);
    const s = clear(document.getElementById('tSvg'));
    const rows = [['RNN, training', m, 'var(--d)'], ['Transformer, training', 1, 'var(--e)'], ['Transformer, generation', m, 'var(--b)']];
    const W = 460, bw = Math.min(30, W / 40);
    rows.forEach(([lab, k, c], r) => {
      const y = 20 + r * 66;
      svg('text', { x: 0, y: y + 22, class: 't', style: 'font-size:12.5px;font-weight:600', text: lab }, s);
      for (let i = 0; i < k; i++) svg('rect', { x: 190 + i * (bw + 1.5), y: y + 4, width: bw, height: 28, rx: 3, style: `fill:${c}` }, s);
      if (k === 1) svg('rect', { x: 190, y: y + 4, width: m * (bw + 1.5), height: 28, rx: 3, style: 'fill:var(--e);opacity:.25' }, s);
      svg('text', { x: 190 + Math.max(k, k === 1 ? m : k) * (bw + 1.5) + 8, y: y + 23, class: 't tc', style: 'font-size:12px;font-weight:700', text: `${k} sequential step${k > 1 ? 's' : ''}` }, s);
      if (k === 1) svg('text', { x: 196, y: y + 23, class: 't', style: 'fill:#fff;font-size:11px;font-weight:600', text: `all ${m} positions at once` }, s);
    });
  });

  /* training diagram */
  (() => {
    const s = document.getElementById('trSvg');
    TX.arrowDefs(s, 'ta', 'var(--muted)');
    const IN = ['<s>', 'Die', 'Katze', 'saß', 'auf', 'der', 'Matte'], OUT = ['Die', 'Katze', 'saß', 'auf', 'der', 'Matte', '</s>'];
    svg('text', { x: 4, y: 250, class: 'tm', style: 'font-size:11px', text: 'input' }, s);
    svg('text', { x: 4, y: 30, class: 'tm', style: 'font-size:11px', text: 'target' }, s);
    const ip = TX.tokens(s, IN, { x0: 60, width: 590, y: 230, h: 28, color: () => 'var(--c-soft)', textColor: () => 'var(--c)', font: 12 });
    TX.box(s, 60, 120, 590, 60, 'var(--c)', 'Decoder × 6: masked self-attention · enc-dec attention · FFN\none forward pass over all 7 positions', { fs: 12.5 });
    ip.forEach(p => TX.arrow(s, p.x, 228, p.x, 184, 'ta', 'var(--muted)', 1.5));
    const op = TX.tokens(s, OUT, { x0: 60, width: 590, y: 12, h: 28, color: () => 'var(--e)', textColor: () => '#fff', font: 12 });
    op.forEach((p, i) => {
      TX.arrow(s, p.x, 118, p.x, 76, 'ta', 'var(--muted)', 1.5);
      svg('text', { x: p.x, y: 62, 'text-anchor': 'middle', class: 'tm tc', style: 'font-size:10px', text: `loss${i + 1}` }, s);
    });
    svg('text', { x: 355, y: 102, 'text-anchor': 'middle', class: 't', style: 'font-size:12px;font-weight:600;fill:var(--e)', text: 'total loss = Σ loss_i, and one backward pass updates everything' }, s);
  })();

  /* generation stepper */
  const SEQ = ['Die', 'Katze', 'saß', 'auf', 'der', 'Matte', '</s>'];
  let k = 0;
  const gen = () => {
    const s = clear(document.getElementById('gSvg'));
    TX.arrowDefs(s, 'ga', 'var(--muted)');
    TX.box(s, 10, 30, 150, 50, 'var(--a)', 'Encoder (ran once)\n"The cat sat on the mat"', { fs: 11 });
    TX.box(s, 10, 100, 150, 40, 'var(--a-soft)', 'memory (reused)', { text: 'var(--a)', stroke: 'var(--a)' });
    const prefix = ['<s>', ...SEQ.slice(0, k)];
    TX.box(s, 220, 70, 260, 60, 'var(--c)', `Decoder pass #${k + 1}\nreads ${prefix.length} token${prefix.length > 1 ? 's' : ''}`, { fs: 12.5 });
    svg('polyline', { points: '160,120 190,120 190,100 216,100', fill: 'none', style: 'stroke:var(--a);stroke-width:2.5', 'marker-end': 'url(#ga)' }, s);
    const ip = TX.tokens(s, prefix, { x0: 220, width: Math.min(420, prefix.length * 62), y: 200, h: 28, color: i => i === prefix.length - 1 && k > 0 ? 'var(--e)' : 'var(--c-soft)', textColor: i => i === prefix.length - 1 && k > 0 ? '#fff' : 'var(--c)', font: 12 });
    TX.arrow(s, 350, 198, 350, 134, 'ga');
    svg('text', { x: 220, y: 246, class: 'tm', style: 'font-size:11px', text: 'decoder input = start token + everything generated so far' }, s);
    const done = k >= SEQ.length;
    if (!done) {
      TX.arrow(s, 482, 100, 540, 100, 'ga');
      TX.box(s, 545, 82, 100, 36, 'var(--e)', SEQ[k]);
      svg('text', { x: 595, y: 140, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: 'next token' }, s);
      svg('path', { d: 'M 595 120 Q 640 180 600 205', fill: 'none', style: 'stroke:var(--e);stroke-width:2;stroke-dasharray:5 4', 'marker-end': 'url(#ga)' }, s);
      svg('text', { x: 610, y: 185, class: 'tm', style: 'font-size:10px', text: 'append' }, s);
    } else svg('text', { x: 560, y: 105, 'text-anchor': 'middle', class: 't', style: 'fill:var(--e);font-weight:700', text: 'done: </s>' }, s);
    Deck.out('gOut', `decoder passes so far: ${Math.min(k + 1, SEQ.length)} · encoder passes: 1`);
  };
  document.getElementById('gStep').onclick = () => { if (k < SEQ.length) k++; gen(); };
  document.getElementById('gReset').onclick = () => { k = 0; gen(); };
  gen();

  /* beam search */
  const P = {
    '<s>': { Die: .55, Der: .30, Eine: .15 }, Die: { Katze: .7, Kater: .2, Matte: .1 }, Der: { Kater: .8, Katze: .2 }, Eine: { Katze: .9, Matte: .1 },
    Katze: { 'saß': .6, sitzt: .35, '</s>': .05 }, Kater: { 'saß': .5, sitzt: .45, '</s>': .05 }, Matte: { '</s>': .6, 'saß': .4 },
    'saß': { auf: .9, '</s>': .1 }, sitzt: { auf: .85, '</s>': .15 }, auf: { der: .8, die: .2 }, der: { Matte: .9, Katze: .1 }, die: { Matte: .95, Katze: .05 },
  };
  const lp = n => Math.pow((5 + n) / 6, 0.6);
  const runBeam = steps => {
    let alive = [{ toks: [], lp: 0 }], done = [];
    for (let t = 0; t < steps; t++) {
      const cand = [];
      alive.forEach(h => {
        const last = h.toks.length ? h.toks[h.toks.length - 1] : '<s>';
        Object.entries(P[last] || { '</s>': 1 }).forEach(([w, p]) => cand.push({ toks: [...h.toks, w], lp: h.lp + Math.log(p) }));
      });
      cand.sort((a, b) => b.lp - a.lp);
      alive = [];
      for (const c of cand) {
        if (c.toks[c.toks.length - 1] === '</s>') { if (done.length < 8) done.push(c); }
        else if (alive.length < 4) alive.push(c);
      }
    }
    return { alive, done };
  };
  Deck.bind(['bS'], () => {
    const st = Deck.val('bS'); Deck.out('bSo', st);
    const { alive, done } = runBeam(st);
    Deck.hbars(document.getElementById('bAlive'), alive.length ? alive.map(h => ({ label: h.toks.join(' ').replace(/</g, '&lt;'), value: Math.exp(h.lp), color: 'var(--c)', text: 'log P = ' + h.lp.toFixed(2) })) : [{ label: '(all finished)', value: 0, text: '' }], { max: 1 });
    const ranked = done.map(h => ({ ...h, sc: h.lp / lp(h.toks.length) })).sort((a, b) => b.sc - a.sc);
    Deck.hbars(document.getElementById('bDone'), ranked.length ? ranked.slice(0, 5).map((h, i) => ({ label: (i === 0 ? '★ ' : '') + h.toks.join(' ').replace(/</g, '&lt;'), value: Math.exp(h.sc), color: i === 0 ? 'var(--e)' : 'var(--faint)', text: 'score ' + h.sc.toFixed(2) })) : [{ label: '(none yet)', value: 0, text: '' }], { max: 1 });
  });
})();
