(() => {
  const { svg, clear, fmt } = Deck;
  let sel = 0;
  const draw = () => {
    const N = Deck.val('rN'), G = Deck.val('rG'), W = N * G; Deck.out('rNo', N); Deck.out('rGo', G); if (sel >= W) sel = 0;
    const s = clear(document.getElementById('rSvg')), bw = 600 / N;
    for (let n = 0; n < N; n++) { svg('rect', { x: 30 + n * bw, y: 10, width: bw - 12, height: 170, rx: 10, style: 'fill:var(--panel-2);stroke:var(--line)' }, s); svg('text', { x: 30 + n * bw + 10, y: 30, class: 'tm', text: `node ${n}` }, s);
      for (let g = 0; g < G; g++) { const r = n * G + g, col = g % 4, row = Math.floor(g / 4), cw = (bw - 32) / 4, x = 40 + n * bw + col * cw, y = 45 + row * 62;
        const el = svg('rect', { x, y, width: cw - 6, height: 52, rx: 6, style: `fill:${r === sel ? 'var(--b)' : 'var(--a)'};cursor:pointer` }, s);
        svg('text', { x: x + (cw - 6) / 2, y: y + 22, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:11px;pointer-events:none', text: `rank ${r}` }, s);
        svg('text', { x: x + (cw - 6) / 2, y: y + 40, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-size:10px;pointer-events:none', text: `local ${g}` }, s);
        el.addEventListener('click', () => { sel = r; draw(); }); } }
    svg('text', { x: 330, y: 210, 'text-anchor': 'middle', class: 'tm', text: `torchrun --nnodes ${N} --nproc_per_node ${G} train.py` }, s);
    document.getElementById('rOut').innerHTML = `Selected process: <code>RANK=${sel} LOCAL_RANK=${sel % G} WORLD_SIZE=${W}</code> → <code>torch.cuda.set_device(${sel % G})</code>; it reads data shard ${sel} of ${W}.`;
  };
  Deck.bind(['rN', 'rG'], draw);
})();
