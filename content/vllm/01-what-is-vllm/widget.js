(() => {
  const { svg, clear, fmt } = Deck;
  const ST = [['client', 'HTTP request or LLM.generate()', 'f'], ['API server', 'chat template, tokenise, validate (entrypoints/)', 'c'], ['EngineCore', 'scheduler: prefix-cache lookup, KV blocks, token budget (v1/core/sched)', 'a'],
    ['GPU worker', 'model runner: batched forward pass + sampling (v1/worker)', 'b'], ['EngineCore', 'update request state; repeat each step until done (v1/engine/core.py)', 'a'], ['API server', 'detokenise and stream tokens (v1/engine/output_processor.py)', 'e']];
  let k = 0;
  const draw = () => {
    const s = clear(document.getElementById('lSvg')), w = 102;
    ST.forEach(([n, d, c], i) => { svg('rect', { x: 10 + i * (w + 6), y: 40, width: w, height: 70, rx: 10, style: `fill:var(--${c});opacity:${i <= k ? 1 : .25}` }, s);
      svg('text', { x: 10 + i * (w + 6) + w / 2, y: 80, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:700;font-size:12px', text: n }, s);
      if (i < ST.length - 1) svg('text', { x: 10 + (i + 1) * (w + 6) - 3, y: 80, 'text-anchor': 'middle', class: 'tm', text: '→' }, s); });
    svg('text', { x: 330, y: 150, 'text-anchor': 'middle', class: 'tm', text: 'stages 3–5 repeat once per generated token' }, s);
    document.getElementById('lOut').innerHTML = `<b>${k + 1}. ${ST[k][0]}</b>: ${ST[k][1]}.`;
  };
  document.getElementById('lNext').addEventListener('click', () => { k = Math.min(ST.length - 1, k + 1); draw(); });
  document.getElementById('lReset').addEventListener('click', () => { k = 0; draw(); });
  draw();
})();
