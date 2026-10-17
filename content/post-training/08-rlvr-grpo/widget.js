(() => {
  const { svg, clear, fmt } = Deck;

  Deck.bind(['dP', 'dG'], () => {
    const p = Deck.val('dP'), G = Deck.val('dG'); Deck.out('dPo', p.toFixed(2)); Deck.out('dGo', G);
    const dead = (pp, g) => Math.pow(pp, g) + Math.pow(1 - pp, g);
    const s = clear(document.getElementById('dSvg')), X = v => 60 + v * 560, Y = v => 200 - v * 180;
    [0, 0.5, 1].forEach(v => { svg('line', { x1: 60, x2: 620, y1: Y(v), y2: Y(v), class: 'ln' }, s); svg('text', { x: 52, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm', text: v }, s); });
    [2, 8, 32].forEach((g, i) => { let pts = ''; for (let v = 0.005; v < 1; v += 0.005) pts += `${X(v)},${Y(dead(v, g))} `; svg('polyline', { points: pts, fill: 'none', style: `stroke:${['var(--faint)', 'var(--c)', 'var(--b)'][i]};stroke-width:2` }, s); const lv = [0.5, 0.2, 0.09][i]; svg('text', { x: X(lv) + 6, y: Y(dead(lv, g)) - 6, class: 'tm', style: 'font-size:11px', text: 'G=' + g }, s); });   // label each curve where the curves are apart
    let pts = ''; for (let v = 0.005; v < 1; v += 0.005) pts += `${X(v)},${Y(dead(v, G))} `;
    svg('polyline', { points: pts, fill: 'none', style: 'stroke:var(--a);stroke-width:3.5' }, s);
    svg('circle', { cx: X(p), cy: Y(dead(p, G)), r: 7, style: 'fill:var(--d)' }, s);
    svg('text', { x: 340, y: 224, 'text-anchor': 'middle', class: 'tm', text: 'P(correct answer) for the prompt' }, s);
    document.getElementById('dOut').innerHTML = `At p = ${p.toFixed(2)} and G = ${G}: <b>${(100 * dead(p, G)).toFixed(1)}%</b> of groups have identical rewards and contribute zero gradient.`;
  });
  Deck.hbars(document.getElementById('rBars'), [
    { label: 'DeepSeekMath-Instruct, MATH', value: 46.8, color: 'var(--faint)', text: '46.8%' }, { label: '+ GRPO (DeepSeekMath-RL)', value: 51.7, color: 'var(--a)', text: '51.7%' },
    { label: 'GSM8K before / after GRPO', value: 82.9, color: 'var(--faint)', text: '82.9%' }, { label: '', value: 88.2, color: 'var(--a)', text: '88.2%' },
    { label: 'R1-Zero AIME 2024, start of RL', value: 15.6, color: 'var(--faint)', text: '15.6%' }, { label: 'R1-Zero AIME 2024, after RL', value: 77.9, color: 'var(--a)', text: '77.9%' }], { max: 100 });

})();
