(() => {
  const { svg, clear } = Deck;
  const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  const hex = c => { const m = c.match(/^#([0-9a-f]{6})$/i); return m ? [parseInt(m[1].slice(0, 2), 16), parseInt(m[1].slice(2, 4), 16), parseInt(m[1].slice(4), 16)] : [128, 128, 128]; };

  /* permutation demo */
  const EMB = { dog: [1.0, 0.2, -0.3, 0.4], bites: [-0.2, 1.0, 0.5, -0.4], man: [0.3, -0.5, 1.0, 0.6] };
  let order = 'a', usePE = false;
  const attn = X => { const S = TX.matMul(X, TX.T(X)).map(r => r.map(x => x / 2)); return TX.matMul(S.map(TX.softmax), X); };
  const perm = () => {
    const words = order === 'a' ? ['dog', 'bites', 'man'] : ['man', 'bites', 'dog'];
    const X = words.map((w, p) => usePE ? EMB[w].map((x, i) => x + 0.8 * TX.pe(p, i, 4)) : EMB[w].slice());
    const Y = attn(X);
    const other = order === 'a' ? ['man', 'bites', 'dog'] : ['dog', 'bites', 'man'];
    const Xo = other.map((w, p) => usePE ? EMB[w].map((x, i) => x + 0.8 * TX.pe(p, i, 4)) : EMB[w].slice());
    const Yo = attn(Xo);
    const s = clear(document.getElementById('permSvg'));
    svg('text', { x: 10, y: 18, class: 'tm', style: 'font-size:11px', text: 'position' }, s);
    svg('text', { x: 140, y: 18, class: 'tm', style: 'font-size:11px', text: 'word' }, s);
    svg('text', { x: 260, y: 18, class: 'tm', style: 'font-size:11px', text: 'attention output for this word' }, s);
    svg('text', { x: 470, y: 18, class: 'tm', style: 'font-size:11px', text: 'same word, other order' }, s);
    let allSame = true;
    words.forEach((w, p) => {
      const y = 30 + p * 62, q = other.indexOf(w), same = Y[p].every((v, i) => Math.abs(v - Yo[q][i]) < 1e-9);
      allSame = allSame && same;
      svg('text', { x: 20, y: y + 26, class: 't tc', style: 'font-weight:700', text: p }, s);
      TX.box(s, 120, y + 6, 100, 30, 'var(--panel-2)', w, { text: 'var(--ink)', stroke: 'var(--line)' });
      TX.vec(s, Y[p], { x: 260, y: y + 4, cell: 44, vals: true, max: 1.2 });
      TX.vec(s, Yo[q], { x: 470, y: y + 4, cell: 28, vals: false, max: 1.2 });
      svg('text', { x: 590, y: y + 22, class: 't', style: `font-weight:700;font-size:12px;fill:${same ? 'var(--d)' : 'var(--e)'}`, text: same ? '= same' : '≠ differs' }, s);
    });
    document.getElementById('permOut').innerHTML = allSame
      ? '<span class="em-d">Identical outputs for every word in both orders.</span> The model can\'t tell who bit whom.'
      : '<span class="em-e">Outputs now depend on position.</span> "dog" at position 0 and "dog" at position 2 get different representations.';
  };
  Deck.seg('oSeg', v => { order = v; perm(); });
  Deck.seg('peSeg', v => { usePE = v === '1'; perm(); });

  /* add diagram */
  (() => {
    const s = document.getElementById('addSvg');
    const r = TX.rng(3), emb = [...Array(16)].map(() => TX.randn(r) * .6);
    const pos = 3, pev = [...Array(16)].map((_, i) => TX.pe(pos, i, 16));
    TX.vec(s, emb, { x: 140, y: 20, cell: 28, label: 'embedding("cat") × √d', max: 1.5 });
    svg('text', { x: 360, y: 82, 'text-anchor': 'middle', class: 't', style: 'font-size:22px;font-weight:700', text: '+' }, s);
    TX.vec(s, pev, { x: 140, y: 100, cell: 28, label: `PE(pos = ${pos})`, max: 1.5, color: '#c9a227' });
    svg('line', { x1: 140, x2: 586, y1: 140, y2: 140, class: 's-ink', 'stroke-width': 1.5 }, s);
    TX.vec(s, emb.map((x, i) => x + pev[i]), { x: 140, y: 152, cell: 28, label: 'input to layer 1', max: 1.5 });
    svg('text', { x: 140, y: 205, class: 'tm', style: 'font-size:11px', text: 'Showing 16 of 512 dimensions. Toy embedding values.' }, s);
  })();

  /* heatmap + wave */
  const D = 512;
  const drawHeat = () => {
    const P = Deck.val('hP'), I = Deck.val('hI');
    Deck.out('hPo', P); Deck.out('hIo', I + ` (dims ${2 * I}, ${2 * I + 1})`);
    const cv = document.getElementById('peCanvas'), ctx = cv.getContext('2d'), img = ctx.createImageData(512, 100);
    const pos = hex(css('--a')), neg = hex(css('--d')), bg = hex(css('--panel')) ;
    for (let p = 0; p < 100; p++) for (let i = 0; i < D; i++) {
      const v = TX.pe(p, i, D), c = v >= 0 ? pos : neg, a = Math.abs(v), k = (p * 512 + i) * 4;
      for (let ch = 0; ch < 3; ch++) img.data[k + ch] = bg[ch] + (c[ch] - bg[ch]) * a;
      img.data[k + 3] = 255;
    }
    ctx.putImageData(img, 0, 0);
    ctx.strokeStyle = css('--ink'); ctx.lineWidth = 1; ctx.strokeRect(0.5, P - 0.5, 511, 2);
    ctx.strokeStyle = css('--b'); ctx.strokeRect(2 * I - .5, 0, 2, 100);
    const s = clear(document.getElementById('waveSvg'));
    const L = 20, W = 290, mid = 80, A = 60;
    svg('line', { x1: L, x2: L + W, y1: mid, y2: mid, class: 'ln' }, s);
    let pts = '';
    for (let p = 0; p <= 99; p += 0.25) pts += `${L + p / 99 * W},${mid - A * TX.pe(p, 2 * I, D)} `;
    svg('polyline', { points: pts, fill: 'none', style: 'stroke:var(--b);stroke-width:2.5' }, s);
    svg('circle', { cx: L + P / 99 * W, cy: mid - A * TX.pe(P, 2 * I, D), r: 6, style: 'fill:var(--ink)' }, s);
    svg('text', { x: L, y: 165, class: 'tm tc', style: 'font-size:10px', text: 'pos 0' }, s);
    svg('text', { x: L + W, y: 165, 'text-anchor': 'end', class: 'tm tc', style: 'font-size:10px', text: 'pos 99' }, s);
    const wl = 2 * Math.PI * Math.pow(10000, 2 * I / D);
    document.getElementById('waveCap').innerHTML = `sin(pos / 10000<sup>${(2 * I / D).toFixed(3)}</sup>): wavelength ≈ <b>${wl < 1000 ? wl.toFixed(1) : Math.round(wl).toLocaleString()}</b> positions · PE(${P}, ${2 * I}) = ${TX.pe(P, 2 * I, D).toFixed(3)}`;
  };
  Deck.bind(['hP', 'hI'], drawHeat);

  /* rotation + similarity */
  Deck.bind(['rP', 'rK'], () => {
    const p = Deck.val('rP'), k = Deck.val('rK'); Deck.out('rPo', p); Deck.out('rKo', k);
    const s = clear(document.getElementById('circSvg'));
    TX.arrowDefs(s, 'ra', 'var(--b)');
    const cx = 160, cy = 125, R = 95, w = 1 / Math.pow(10000, 2 * 4 / 64);
    svg('circle', { cx, cy, r: R, style: 'fill:none;stroke:var(--line);stroke-width:2' }, s);
    const pt = q => [cx + R * Math.sin(w * q), cy - R * Math.cos(w * q)];
    for (let q = 0; q <= 60; q++) { const [x, y] = pt(q); svg('circle', { cx: x, cy: y, r: 2, style: 'fill:var(--faint)' }, s); }
    const [x1, y1] = pt(p), [x2, y2] = pt(p + k);
    svg('line', { x1: cx, y1: cy, x2: x1, y2: y1, style: 'stroke:var(--a);stroke-width:3' }, s);
    svg('line', { x1: cx, y1: cy, x2: x2, y2: y2, style: 'stroke:var(--b);stroke-width:3' }, s);
    svg('circle', { cx: x1, cy: y1, r: 7, class: 'f-a' }, s);
    svg('circle', { cx: x2, cy: y2, r: 7, class: 'f-b' }, s);
    svg('text', { x: x1 + 10, y: y1 - 8, class: 't', style: 'fill:var(--a);font-weight:700;font-size:12px', text: `PE(${p})` }, s);
    svg('text', { x: x2 + 10, y: y2 + 16, class: 't', style: 'fill:var(--b);font-weight:700;font-size:12px', text: `PE(${p + k})` }, s);
    svg('text', { x: 160, y: 250, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: `rotation angle ω·k = ${(w * k * 180 / Math.PI).toFixed(1)}°, the same for any p (dims 8, 9 of d = 64)` }, s);
    const cv = document.getElementById('simCanvas'), ctx = cv.getContext('2d'), img = ctx.createImageData(64, 64);
    const col = hex(css('--a')), bg = hex(css('--panel'));
    const vec = q => [...Array(64)].map((_, i) => TX.pe(q, i, 64));
    const V = [...Array(64)].map((_, q) => vec(q)), mx = TX.dot(V[0], V[0]);
    for (let a = 0; a < 64; a++) for (let b = 0; b < 64; b++) {
      const v = Math.max(0, TX.dot(V[a], V[b]) / mx), kk = (a * 64 + b) * 4;
      const hl = (a === p && b === p + k) || (a === p + k && b === p);
      for (let ch = 0; ch < 3; ch++) img.data[kk + ch] = hl ? hex(css('--b'))[ch] : bg[ch] + (col[ch] - bg[ch]) * Math.pow(v, 2);
      img.data[kk + 3] = 255;
    }
    ctx.putImageData(img, 0, 0);
  });
})();
