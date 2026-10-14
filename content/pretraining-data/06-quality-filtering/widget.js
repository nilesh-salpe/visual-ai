(() => {
  const { svg, clear, fmt } = Deck;
  const DOCS = { article: 'Gradient descent updates the weights in the direction that reduces the loss. The step size is set by the learning rate. If it is too large, training diverges. If it is too small, training is slow. Modern language models use the Adam optimizer with a warmup schedule. This keeps early updates small while statistics settle. Later the learning rate decays, letting the model settle into a good region of the loss surface.',
    nav: 'Home\nProducts\nAbout us\nContact\nLog in\nSign up',
    spam: 'best cheap shoes '.repeat(10).trim(),
    code: "function add(a, b) { return a + b; } const x = add(1, 2); console.log(x); if (x > 2) { alert('big'); } // this is a comment line that goes on for a while to be long enough",
    hashtags: Array(4).fill('#ai #ml #deep #learning #love #photo #instagood #follow #nofilter #tbt').join(' ') + ' this post is about the best day of my life and I have to say that the light was perfect with friends',
    lorem: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.' };
  const STOP = new Set(['the', 'be', 'to', 'of', 'and', 'that', 'have', 'with']);
  const c4 = t => { if (/lorem ipsum/i.test(t)) return 'lorem ipsum'; if (t.includes('{')) return 'curly bracket'; const lines = t.split(/\n|(?<=[.!?"”])\s+/).map(s => s.trim()).filter(l => l && '.!?"”'.includes(l.slice(-1)) && l.split(/\s+/).length >= 5 && !/javascript/i.test(l)); return (lines.join(' ').match(/[.!?]["”]?(\s|$)/g) || []).length >= 3 ? null : 'fewer than 3 sentences'; };
  const gopher = t => { const w = t.split(/\s+/).filter(Boolean), n = w.length; if (n < 50 || n > 100000) return 'word count';
    const ml = w.reduce((a, x) => a + x.length, 0) / n; if (ml < 3 || ml > 10) return 'mean word length';
    if ((t.match(/#/g) || []).length / n > 0.1 || ((t.match(/\.\.\./g) || []).length + (t.match(/…/g) || []).length) / n > 0.1) return 'symbol ratio';
    if (w.filter(x => /[A-Za-z]/.test(x)).length / n < 0.8) return 'alphabetic words';
    if ([...new Set(w.map(x => x.toLowerCase().replace(/[.,;:!?]/g, '')))].filter(x => STOP.has(x)).length < 2) return 'stop words'; return null; };
  const rep = t => { const w = t.toLowerCase().split(/\s+/), g = []; for (let i = 0; i + 2 < w.length; i++) g.push(w.slice(i, i + 3).join(' ')); const c = {}; g.forEach(x => c[x] = (c[x] || 0) + 1); const cov = new Set(); g.forEach((x, i) => { if (c[x] > 1) [i, i + 1, i + 2].forEach(j => cov.add(j)); }); return cov.size / w.length > 0.3 ? `repetition ${(cov.size / w.length).toFixed(2)}` : null; };
  Deck.seg('qSeg', v => {
    document.getElementById('qList').innerHTML = Object.entries(DOCS).map(([k, t]) => {
      const why = v === 'c4' ? c4(t) : v === 'gopher' ? gopher(t) : (c4(t) && 'C4: ' + c4(t)) || (gopher(t) && 'Gopher: ' + gopher(t)) || rep(t), keep = !why;
      return `<div style="display:flex;gap:10px;align-items:center;padding:8px 10px;border-radius:8px;background:${keep ? 'var(--a-soft)' : 'var(--panel-2)'}"><b style="min-width:76px">${k}</b><span style="flex:1;font-size:13px;color:var(--faint)">${t.replace(/\n/g, ' / ').slice(0, 90)}…</span><span style="font:600 11px 'JetBrains Mono',monospace;color:${keep ? 'var(--e)' : 'var(--d)'}">${keep ? 'KEEP' : 'drop: ' + why}</span></div>`;
    }).join('');
  });
})();
