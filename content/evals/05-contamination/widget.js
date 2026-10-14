(() => {
  const { svg, clear, fmt } = Deck;

  Deck.bind(['lF'], () => {
    const f = Deck.val('lF'), clean = 0.55, full = f * 0.95 + (1 - f) * clean; Deck.out('lFo', (100 * f).toFixed(0) + '%');
    Deck.hbars(document.getElementById('lBars'), [{ label: 'reported (full set)', value: full, color: 'var(--d)', text: (100 * full).toFixed(1) + '%' }, { label: 'clean subset', value: clean, color: 'var(--a)', text: '55.0%' }, { label: 'dirty subset', value: f ? 0.95 : 0, color: 'var(--b)', text: f ? '95.0%' : '—' }], { max: 1 });
    document.getElementById('lOut').innerHTML = `With ${(100 * f).toFixed(0)}% leaked, the reported score is inflated by <b>${(100 * (full - clean)).toFixed(1)} points</b> over the model's real skill.`;
  });
  const TEST = 'a train leaves the station at noon travelling at sixty miles per hour toward the coast'.split(' ');
  const TRAIN = 'yesterday a train leaves the station at noon travelling quickly and nobody knows why the coast is quiet'.split(' ');
  Deck.bind(['nN'], () => {
    const n = Deck.val('nN'); Deck.out('nNo', n);
    const grams = new Set(); for (let i = 0; i + n <= TRAIN.length; i++) grams.add(TRAIN.slice(i, i + n).join(' '));
    const hit = new Array(TEST.length).fill(false); let any = 0;
    for (let i = 0; i + n <= TEST.length; i++) if (grams.has(TEST.slice(i, i + n).join(' '))) { any++; for (let j = i; j < i + n; j++) hit[j] = true; }
    const box = document.getElementById('nTest'); box.innerHTML = '';
    TEST.forEach((w, i) => { const s = document.createElement('span'); s.textContent = w; s.style.cssText = `padding:3px 7px;border-radius:5px;background:${hit[i] ? 'var(--d)' : 'var(--panel-2)'};color:${hit[i] ? '#fff' : 'var(--ink)'}`; box.appendChild(s); });
    document.getElementById('nTrain').textContent = TRAIN.join(' ');
    document.getElementById('nOut').innerHTML = any ? `<b>${any}</b> of the test item's ${n}-grams appear in training: <b>flagged</b>.` : `No shared ${n}-gram: <b>not flagged</b>, even though half the item was copied. Longer n misses partial copies.`;
  });

})();
