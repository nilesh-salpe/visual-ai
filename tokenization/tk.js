// Tokenization helpers: render real tokens (from data/examples.js), a small BPE trainer/encoder
// following Sennrich et al. (2016), and a unigram-LM segmentation lattice (Kudo, 2018).
const TK = (() => {
  const dec = new TextDecoder('utf-8', { fatal: true });
  const hex = b => b.map(x => '\\x' + x.toString(16).toUpperCase().padStart(2, '0')).join('');
  const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const vis = s => esc(s).replace(/ /g, '<span class="ws">·</span>').replace(/\n/g, '<span class="ws">↵</span>').replace(/\t/g, '<span class="ws">→</span>');

  const tryDec = b => { try { return dec.decode(new Uint8Array(b)); } catch (e) { return null; } };
  // Decode a token's bytes. Incomplete UTF-8 at either edge is kept as hex; the valid middle stays text.
  function tokText(bytes) {
    const full = tryDec(bytes);
    if (full !== null) return { s: full, ok: true, html: vis(full) };
    let i = 0;
    while (i < bytes.length && bytes[i] >= 0x80 && bytes[i] < 0xC0) i++;
    let j = bytes.length, mid = null;
    for (; j > i; j--) { mid = tryDec(bytes.slice(i, j)); if (mid !== null) break; }
    const pre = bytes.slice(0, i), post = bytes.slice(Math.max(i, j));
    const html = (pre.length ? `<span class="hex">${hex(pre)}</span>` : '') + (mid ? vis(mid) : '') + (post.length ? `<span class="hex">${hex(post)}</span>` : '');
    return { s: hex(bytes), ok: false, html };
  }

  // toks: [[id, bytes]] (real data) or [{text, id}] (toy). o.ids shows ids under each token.
  function render(el, toks, o = {}) {
    el.className = 'toks' + (o.ids ? ' with-ids' : '');
    el.innerHTML = toks.map((t, i) => {
      let id, r;
      if (Array.isArray(t)) { id = t[0]; r = tokText(t[1]); } else { id = t.id; r = { s: t.text, ok: true }; }
      const body = r.html != null ? r.html : vis(r.s);
      const title = id != null ? `id ${id}${r.ok ? '' : ' · incomplete UTF-8 bytes'}` : '';
      return `<span class="tok c${i % 6}${r.ok ? '' : ' partial'}" title="${title}">${body}${o.ids && id != null ? `<span class="id">${id}</span>` : ''}</span>`;
    }).join('');
  }

  const get = (key, enc) => TOK.x[key][enc];
  const text = key => TOK.x[key].text;
  const ENC = { gpt2: 'GPT-2 (gpt2)', cl100k_base: 'cl100k_base', o200k_base: 'o200k_base' };

  // ---- BPE (Sennrich et al., 2016, Algorithm 1). '·' marks end of word, as in the paper's Figure 1.
  const EOW = '·';
  function applyMerge(sy, a, b, drop = 0, rnd = Math.random) {
    const out = [];
    for (let i = 0; i < sy.length; i++) {
      if (i < sy.length - 1 && sy[i] === a && sy[i + 1] === b && !(drop && rnd() < drop)) { out.push(a + b); i++; }
      else out.push(sy[i]);
    }
    return out;
  }
  // corpus: [[word, count], ...]. Ties go to the pair seen first, matching max() over Python's dict.
  function bpeTrain(corpus, nMerges) {
    let vocab = corpus.map(([w, c]) => [[...w, EOW], c]);
    const steps = [];
    for (let m = 0; m < nMerges; m++) {
      const counts = new Map();
      vocab.forEach(([sy, c]) => { for (let i = 0; i < sy.length - 1; i++) { const k = sy[i] + '\u0000' + sy[i + 1]; counts.set(k, (counts.get(k) || 0) + c); } });
      if (!counts.size) break;
      let best = null, bc = -1;
      for (const [k, v] of counts) if (v > bc) { best = k; bc = v; }
      const [a, b] = best.split('\u0000');
      vocab = vocab.map(([sy, c]) => [applyMerge(sy, a, b), c]);
      steps.push({ a, b, count: bc, vocab: vocab.map(([s, c]) => [s.slice(), c]), counts });
    }
    return steps;
  }
  function bpeEncode(word, merges, drop = 0, rnd) {
    let sy = [...word, EOW];
    merges.forEach(([a, b]) => { sy = applyMerge(sy, a, b, drop, rnd); });
    return sy;
  }
  function parseCorpus(txt) {
    return txt.split(/[\n,]+/).map(s => s.trim()).filter(Boolean).map(s => {
      const m = s.match(/^(\S+)\s*[:×x]\s*(\d+)$/); return m ? [m[1], +m[2]] : [s.split(/\s+/)[0], 1];
    });
  }

  // ---- Unigram LM segmentation (Kudo, 2018): P(x) = Π p(x_i); best path by Viterbi.
  function segmentations(word, probs, limit = 400) {
    const out = [];
    const rec = (i, path, lp) => {
      if (out.length >= limit) return;
      if (i === word.length) { out.push({ pieces: path.slice(), logp: lp }); return; }
      for (let j = i + 1; j <= word.length; j++) {
        const p = probs[word.slice(i, j)];
        if (p) { path.push(word.slice(i, j)); rec(j, path, lp + Math.log(p)); path.pop(); }
      }
    };
    rec(0, [], 0);
    return out.sort((a, b) => b.logp - a.logp);
  }
  function viterbi(word, probs) {
    const best = [{ lp: 0, prev: -1 }];
    for (let j = 1; j <= word.length; j++) {
      best[j] = { lp: -Infinity, prev: -1 };
      for (let i = 0; i < j; i++) { const p = probs[word.slice(i, j)]; if (p && best[i].lp + Math.log(p) > best[j].lp) best[j] = { lp: best[i].lp + Math.log(p), prev: i }; }
    }
    const pieces = []; let j = word.length;
    while (j > 0 && best[j].prev >= 0) { pieces.unshift(word.slice(best[j].prev, j)); j = best[j].prev; }
    return { pieces, logp: best[word.length].lp };
  }
  // P(x_i | X) ≅ P(x_i)^α / Σ_j P(x_j)^α over the l-best candidates (Kudo §3.3).
  function smoothed(cands, alpha, l) {
    const c = cands.slice(0, l), w = c.map(s => Math.exp(alpha * s.logp)), z = w.reduce((a, b) => a + b, 0) || 1;
    return c.map((s, i) => ({ ...s, p: w[i] / z }));
  }
  function sample(dist, rnd = Math.random) { let r = rnd(); for (const d of dist) { r -= d.p; if (r <= 0) return d; } return dist[dist.length - 1]; }

  return { tokText, render, get, text, ENC, EOW, bpeTrain, bpeEncode, parseCorpus, segmentations, viterbi, smoothed, sample, esc, vis };
})();
