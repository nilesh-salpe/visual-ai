(() => {
  const { svg, clear, fmt } = Deck;

  (() => {
    const s = document.getElementById('dSvg');
    const b = (x, w, c, t1, t2) => { svg('rect', { x, y: 30, width: w, height: 70, rx: 10, style: `fill:${c}` }, s); svg('text', { x: x + w / 2, y: 60, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:700', text: t1 }, s); svg('text', { x: x + w / 2, y: 80, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11px', text: t2 }, s); };
    svg('text', { x: 10, y: 70, class: 'tm', text: 'prompts →' }, s);
    b(80, 200, 'var(--a)', 'Prefill pool', 'compute-bound · sets TTFT');
    svg('line', { x1: 285, x2: 375, y1: 65, y2: 65, style: 'stroke:var(--c);stroke-width:5' }, s);
    svg('text', { x: 330, y: 55, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: 'KV cache' }, s);
    b(380, 200, 'var(--b)', 'Decode pool', 'memory-bound · sets TPOT');
    svg('text', { x: 590, y: 70, class: 'tm', text: '→ tokens' }, s);
    svg('text', { x: 330, y: 135, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: 'each pool: its own GPU count, parallelism, batch size' }, s);
  })();
  let link = 450;
  const xf = () => {
    const per = +Deck.val('xM'), P = Math.round(Math.pow(2, Deck.val('xP'))); Deck.out('xPo', P.toLocaleString());
    const bytes = P * per, t = bytes / (link * 1e9) * 1000, pre = P / 20000 * 1000;
    Deck.out('xB', (bytes / 1e9).toFixed(2) + ' GB'); Deck.out('xT', t.toFixed(1) + ' ms'); Deck.out('xF', `${(100 * t / pre).toFixed(0)}% of ${pre.toFixed(0)} ms`);
  };
  Deck.seg('xL', v => { link = +v; if (document.getElementById('xM')) xf(); });
  Deck.bind(['xM', 'xP'], xf);

})();
