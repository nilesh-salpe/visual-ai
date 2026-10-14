(() => {
  const { svg, clear, fmt } = Deck;
  const PAT = [['EMAIL_ADDRESS', /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g], ['IP_ADDRESS', /\b(?:\d{1,3}\.){3}\d{1,3}\b/g], ['PHONE_NUMBER', /(?:\+\d{1,3}[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}\b/g]];
  const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const run = () => {
    let t = document.getElementById('pTxt').value, spans = [];
    PAT.forEach(([k, rx]) => { for (const m of t.matchAll(rx)) spans.push([m.index, m.index + m[0].length, k]); });
    spans.sort((a, b) => a[0] - b[0]); const clean = []; let end = -1; spans.forEach(s => { if (s[0] >= end) { clean.push(s); end = s[1]; } });
    let out = '', i = 0; clean.forEach(([a, b, k]) => { out += esc(t.slice(i, a)) + `<b style="color:var(--b)">|||${k}|||</b>`; i = b; }); out += esc(t.slice(i));
    const drop = clean.length > 5;
    document.getElementById('pOut').innerHTML = drop ? `<span style="color:var(--d)">(document removed)</span>` : out;
    document.getElementById('pMsg').innerHTML = `${clean.length} PII span(s) found: ${[['EMAIL_ADDRESS', 'email'], ['IP_ADDRESS', 'IP address'], ['PHONE_NUMBER', 'phone number']].map(([k, n]) => `${clean.filter(s => s[2] === k).length} ${n}`).join(', ')}. ${drop ? '<b>More than 5 → drop the whole document.</b>' : '<b>5 or fewer → mask the spans, keep the text.</b>'}`;
  };
  document.getElementById('pTxt').addEventListener('input', run); run();
})();
