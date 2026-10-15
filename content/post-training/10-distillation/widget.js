(() => {
  const { svg, clear, fmt } = Deck;
  const s = document.getElementById('kdSvg'), X0 = -8, X1 = 8, N = 321;
  const xs = Array.from({ length: N }, (_, i) => X0 + (X1 - X0) * i / (N - 1)), dx = (X1 - X0) / (N - 1);
  const g = (x, m, sd) => Math.exp(-0.5 * ((x - m) / sd) ** 2) / (sd * Math.sqrt(2 * Math.PI));
  const px = x => 40 + (x - X0) / (X1 - X0) * 580, py = y => 250 - y * 560;
  const curve = (ys, col, w, dash) => svg('path', { d: ys.map((y, i) => (i ? 'L' : 'M') + px(xs[i]).toFixed(1) + ',' + py(y).toFixed(1)).join(''), style: `fill:none;stroke:${col};stroke-width:${w}` + (dash ? ';stroke-dasharray:6 4' : '') }, s);
  Deck.bind(['kdD', 'kdW'], () => {
    const d = Deck.val('kdD'), w = Deck.val('kdW');
    Deck.out('kdDo', d.toFixed(1)); Deck.out('kdWo', w.toFixed(2));
    const P = xs.map(x => w * g(x, -d, 1) + (1 - w) * g(x, d, 1));
    const mu = (1 - 2 * w) * d, va = 1 + d * d - mu * mu;           // forward KL = moment matching
    const F = xs.map(x => g(x, mu, Math.sqrt(va)));
    let best = [1e9, 0, 1];                                          // reverse KL by grid search
    for (let m = -5; m <= 5; m += 0.1) for (let sd = 0.4; sd <= 4; sd += 0.05) {
      let kl = 0; for (let i = 0; i < N; i++) { const q = g(xs[i], m, sd); if (q > 1e-12) kl += q * Math.log(q / (P[i] + 1e-300)) * dx; }
      if (kl < best[0]) best = [kl, m, sd];
    }
    const R = xs.map(x => g(x, best[1], best[2]));
    clear(s);
    svg('line', { x1: 40, y1: 250, x2: 620, y2: 250, class: 'ln' }, s);
    svg('path', { d: 'M40,250' + P.map((y, i) => 'L' + px(xs[i]).toFixed(1) + ',' + py(y).toFixed(1)).join('') + 'L620,250Z', style: 'fill:var(--faint);opacity:.3' }, s);
    curve(P, 'var(--faint)', 2); curve(F, 'var(--b)', 3, true); curve(R, 'var(--a)', 3);
    [['teacher p', 'var(--faint)', 50], ['forward KL(p‖q) fit', 'var(--b)', 230], ['reverse KL(q‖p) fit', 'var(--a)', 450]].forEach(([t, c, x]) => svg('text', { x, y: 278, class: 't', style: `fill:${c};font-weight:700`, text: t }, s));
    const mid = P[Math.round((0 - X0) / dx)], one = best[2] < 1.3, f1 = v => (Math.abs(v) < 0.05 ? 0 : v).toFixed(1);
    document.getElementById('kdOut').innerHTML = `Teacher modes ${(2 * d).toFixed(1)} apart (each σ = 1). <b>Forward KL</b> (distillation on teacher probabilities) is mean-seeking: the student covers both modes (μ = ${f1(mu)}, σ = ${Math.sqrt(va).toFixed(2)}) and puts mass between them, where the teacher's density is ${mid.toFixed(3)}. <b>Reverse KL</b> (MiniLLM, on-policy distillation): ` +
      (one ? `mode-seeking, the student sits on one mode (μ = ${f1(best[1])}, σ = ${best[2].toFixed(2)}) and ignores the other.` : `while the modes overlap it also spreads (μ = ${f1(best[1])}, σ = ${best[2].toFixed(2)}); separate them, or make one heavier, and it locks onto a single mode.`);
  });
})();
