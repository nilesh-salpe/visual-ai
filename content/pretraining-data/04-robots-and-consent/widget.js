(() => {
  const { svg, clear, fmt } = Deck;
  const parse = text => { const g = {}; let cur = [], inRules = false;
    text.split('\n').forEach(raw => { const line = raw.split('#')[0].trim(); const i = line.indexOf(':'); if (i < 0) return;
      const k = line.slice(0, i).trim().toLowerCase(), v = line.slice(i + 1).trim();
      if (k === 'user-agent') { if (inRules) { cur = []; inRules = false; } const t = v.toLowerCase(); cur.push(t); g[t] = g[t] || []; }
      else if ((k === 'allow' || k === 'disallow') && cur.length) { inRules = true; if (v) cur.forEach(t => g[t].push([k, v])); } });
    return g; };
  const match = (pat, path) => { const anch = pat.endsWith('$'), p = anch ? pat.slice(0, -1) : pat; const rx = new RegExp('^' + p.split('*').map(s => s.replace(/[.+?^${}()|[\]\\]/g, '\\$&')).join('.*') + (anch ? '$' : '')); return rx.test(path) ? p.length : -1; };
  const run = () => {
    const g = parse(document.getElementById('rTxt').value), ua = document.getElementById('rUA').value.trim().toLowerCase(), path = document.getElementById('rP').value.trim() || '/';
    const name = ua in g ? ua : ('*' in g ? '*' : null), rules = name ? g[name] : [];
    let best = -1, kind = 'allow', rule = null;
    rules.forEach(([k, p]) => { const n = match(p, path); if (n > best || (n === best && k === 'allow' && n >= 0)) { best = n; kind = k; rule = `${k}: ${p}`; } });
    const ok = path === '/robots.txt' || best < 0 || kind === 'allow';
    document.getElementById('rOut').innerHTML = `Group used: <b>${name === null ? 'none (no rules apply)' : name === '*' ? '* (no group for this crawler)' : name}</b>. ${best >= 0 ? `Longest matching rule: <code>${rule}</code> (${best} characters).` : 'No rule matches.'} → <b style="color:${ok ? 'var(--e)' : 'var(--d)'}">${ok ? 'ALLOWED' : 'DISALLOWED'}</b>`;
  };
  const TA = document.getElementById('rTxt'); if (!TA.value) TA.value = 'User-agent: *\nDisallow: /private/\nAllow: /private/public-page.html\n\nUser-agent: ExampleBot\nDisallow: /tmp\nDisallow: /*.pdf$\nAllow: /tmp/ok\n\nUser-agent: CCBot\nDisallow: /';
  ['rTxt', 'rUA', 'rP'].forEach(id => document.getElementById(id).addEventListener('input', run)); run();
})();
