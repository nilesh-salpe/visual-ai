// Shared slide engine: chrome, navigation (#N hashes), keyboard/swipe, theme, and small helpers.
// Each deck registers per-slide setup with Deck.enter(slideId, fn); fn may return a cleanup function.
(function () {
  const enterFns = {};
  const SVGNS = 'http://www.w3.org/2000/svg';

  const Deck = {
    enter(id, fn) { (enterFns[id] = enterFns[id] || []).push(fn); },
    $(sel, root) { return (root || document).querySelector(sel); },
    $$(sel, root) { return [...(root || document).querySelectorAll(sel)]; },
    svg(tag, attrs, parent) {
      const el = document.createElementNS(SVGNS, tag);
      for (const k in attrs || {}) {
        if (k === 'text') el.textContent = attrs[k];
        else el.setAttribute(k, attrs[k]);
      }
      if (parent) parent.appendChild(el);
      return el;
    },
    clear(el) { while (el.firstChild) el.removeChild(el.firstChild); return el; },
    fmt(n, d = 1) {
      if (!isFinite(n)) return '∞';
      const a = Math.abs(n);
      if (a >= 1e12) return (n / 1e12).toFixed(d) + 'T';
      if (a >= 1e9) return (n / 1e9).toFixed(d) + 'B';
      if (a >= 1e6) return (n / 1e6).toFixed(d) + 'M';
      if (a >= 1e4) return (n / 1e3).toFixed(d) + 'K';
      if (a >= 100) return n.toFixed(0);
      if (a >= 10) return n.toFixed(Math.min(d, 1));
      return n.toFixed(d + 1).replace(/\.?0+$/, '') || '0';
    },
    bytes(b) {
      const u = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
      let i = 0;
      while (Math.abs(b) >= 1024 && i < u.length - 1) { b /= 1024; i++; }
      return (b >= 100 ? b.toFixed(0) : b >= 10 ? b.toFixed(1) : b.toFixed(2)) + ' ' + u[i];
    },
    // Bind range/select inputs: calls fn() on every change and once immediately.
    bind(ids, fn) {
      ids.forEach(id => {
        const el = document.getElementById(id);
        el.addEventListener('input', fn);
        el.addEventListener('change', fn);
      });
      fn();
    },
    val(id) { const el = document.getElementById(id); return el.type === 'range' ? +el.value : el.value; },
    out(id, text) { document.getElementById(id).textContent = text; },
    // Segmented control: <div class="seg" id=..><button data-v=..>. Calls fn(value).
    seg(id, fn) {
      const root = document.getElementById(id);
      const btns = [...root.querySelectorAll('button')];
      const pick = b => { btns.forEach(x => x.classList.toggle('on', x === b)); fn(b.dataset.v, b); };
      btns.forEach(b => b.addEventListener('click', () => pick(b)));
      pick(btns.find(b => b.classList.contains('on')) || btns[0]);
    },
    // Horizontal bar chart. rows: [{label, value, color, text}]. opts: {log, max, min}
    hbars(el, rows, opts = {}) {
      const vals = rows.map(r => r.value);
      const max = opts.max || Math.max(...vals);
      const min = opts.min || Math.min(...vals.filter(v => v > 0)) / 2;
      const pct = v => {
        if (v <= 0) return 0;
        if (opts.log) return Math.max(1.5, 100 * Math.log(v / min) / Math.log(max / min));
        return Math.max(0.8, 100 * v / max);
      };
      if (el.children.length !== rows.length) {
        el.className = 'hbars';
        el.innerHTML = rows.map(() => '<div class="hbar"><div class="lab"></div><div class="track"><div class="fill"></div></div><div class="val"></div></div>').join('');
      }
      rows.forEach((r, i) => {
        const row = el.children[i];
        row.querySelector('.lab').innerHTML = r.label;
        const f = row.querySelector('.fill');
        f.style.width = Math.min(100, pct(r.value)) + '%';
        f.style.background = r.color || 'var(--a)';
        row.querySelector('.val').textContent = r.text != null ? r.text : Deck.fmt(r.value);
      });
    },
    // requestAnimationFrame loop that stops on cleanup. fn(t_seconds, dt)
    loop(fn) {
      let id, last = performance.now(), t = 0, alive = true;
      const tick = now => {
        if (!alive) return;
        const dt = Math.min(0.1, (now - last) / 1000); last = now; t += dt;
        fn(t, dt);
        id = requestAnimationFrame(tick);
      };
      id = requestAnimationFrame(tick);
      return () => { alive = false; cancelAnimationFrame(id); };
    },
    go: null,
  };
  window.Deck = Deck;

  function storeGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function storeSet(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* ignore */ } }

  function init() {
    const slides = Deck.$$('.slide');
    if (!slides.length) return;
    const deckTitle = document.body.dataset.deck || document.title;
    const home = document.body.dataset.home || '../index.html';
    const homeLabel = document.body.dataset.homeLabel || 'Index';

    const theme = storeGet('deck-theme');
    if (theme) document.documentElement.dataset.theme = theme;

    // chapters
    const chapters = [];
    slides.forEach((s, i) => {
      const c = s.dataset.chapter;
      if (c && !chapters.find(x => x.name === c)) chapters.push({ name: c, first: i });
    });

    const top = document.createElement('header');
    top.className = 'topbar';
    top.innerHTML = `<a class="brand" href="${home}">← ${homeLabel} · <span>${deckTitle}</span></a>
      <nav class="chapters">${chapters.map((c, i) => `<button data-i="${c.first}">${String(i + 1).padStart(2, '0')} ${c.name}</button>`).join('')}</nav>
      <button class="icon-btn" id="themeBtn" title="Toggle theme">◐</button>`;
    document.body.prepend(top);

    const wrap = document.createElement('main');
    wrap.className = 'slides';
    slides[0].parentNode.insertBefore(wrap, slides[0]);
    slides.forEach(s => wrap.appendChild(s));

    // running header + labels
    slides.forEach(s => {
      const inner = s.querySelector('.inner');
      if (inner && !s.classList.contains('title-slide')) {
        const r = document.createElement('div');
        r.className = 'running';
        r.textContent = deckTitle;
        inner.prepend(r);
      }
    });

    const prog = document.createElement('div');
    prog.className = 'progress';
    document.body.appendChild(prog);

    const foot = document.createElement('footer');
    foot.className = 'footer';
    foot.innerHTML = `<div class="hint"><kbd>←</kbd> <kbd>→</kbd> / <kbd>Space</kbd> to move · <kbd>F</kbd> full screen</div>
      <div class="nav"><button class="icon-btn" id="prevBtn" aria-label="Previous">←</button>
      <span class="counter" id="counter"></span>
      <button class="icon-btn" id="nextBtn" aria-label="Next">→</button>
      <button class="icon-btn" id="fsBtn" title="Full screen (F)">⛶</button></div>`;
    document.body.appendChild(foot);

    // title-slide table of contents
    Deck.$$('.toc[data-auto]').forEach(toc => {
      toc.innerHTML = chapters.slice(1).map((c, i) => `<button data-i="${c.first}"><b>${String(i + 1).padStart(2, '0')}</b>${c.name}</button>`).join('');
    });
    document.addEventListener('click', e => {
      const b = e.target.closest('[data-i]');
      if (b && (b.closest('.chapters') || b.closest('.toc'))) show(+b.dataset.i);
    });

    let cur = -1, cleanups = [];
    function show(i) {
      i = Math.max(0, Math.min(slides.length - 1, i));
      if (i === cur) return;
      cleanups.forEach(f => { try { f(); } catch (e) { console.error(e); } });
      cleanups = [];
      if (cur >= 0) slides[cur].classList.remove('active');
      cur = i;
      const s = slides[i];
      s.classList.add('active');
      s.scrollTop = 0;
      Deck.out('counter', `${i + 1} / ${slides.length}`);
      prog.style.width = (100 * (i + 1) / slides.length) + '%';
      const ch = s.dataset.chapter;
      Deck.$$('.chapters button').forEach(b => {
        const on = slides[+b.dataset.i].dataset.chapter === ch;
        b.classList.toggle('active', on);
        if (on) b.scrollIntoView({ block: 'nearest', inline: 'nearest' });
      });
      try { history.replaceState(null, '', '#' + (i + 1)); } catch (e) { /* file:// in some browsers */ }
      (enterFns[s.id] || []).forEach(fn => {
        try { const c = fn(s); if (typeof c === 'function') cleanups.push(c); } catch (e) { console.error(e); }
      });
    }
    Deck.go = show;

    const next = () => show(cur + 1), prev = () => show(cur - 1);
    Deck.$('#nextBtn').onclick = next;
    Deck.$('#prevBtn').onclick = prev;
    const fs = () => {
      if (!document.fullscreenElement) document.documentElement.requestFullscreen && document.documentElement.requestFullscreen().catch(() => {});
      else document.exitFullscreen();
    };
    Deck.$('#fsBtn').onclick = fs;
    Deck.$('#themeBtn').onclick = () => {
      const dark = getComputedStyle(document.documentElement).colorScheme.includes('dark');
      const t = dark ? 'light' : 'dark';
      document.documentElement.dataset.theme = t;
      storeSet('deck-theme', t);
    };

    document.addEventListener('keydown', e => {
      const tag = (e.target.tagName || '').toLowerCase();
      if (tag === 'input' || tag === 'select' || tag === 'textarea') return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key === 'ArrowRight' || e.key === 'PageDown' || (e.key === ' ' && tag !== 'button' && tag !== 'summary')) { e.preventDefault(); next(); }
      else if (e.key === 'ArrowLeft' || e.key === 'PageUp') { e.preventDefault(); prev(); }
      else if (e.key === 'Home') show(0);
      else if (e.key === 'End') show(slides.length - 1);
      else if (e.key === 'f' || e.key === 'F') fs();
    });

    let tx = null, ty = null;
    wrap.addEventListener('touchstart', e => { tx = e.touches[0].clientX; ty = e.touches[0].clientY; }, { passive: true });
    wrap.addEventListener('touchend', e => {
      if (tx == null) return;
      if (e.target.closest('input, .visual svg')) { tx = null; return; }
      const dx = e.changedTouches[0].clientX - tx, dy = e.changedTouches[0].clientY - ty;
      if (Math.abs(dx) > 70 && Math.abs(dx) > 2 * Math.abs(dy)) (dx < 0 ? next : prev)();
      tx = null;
    }, { passive: true });

    const fromHash = () => {
      const n = parseInt((location.hash || '').slice(1), 10);
      return isNaN(n) ? 0 : n - 1;
    };
    window.addEventListener('hashchange', () => show(fromHash()));
    show(fromHash());
  }

  document.addEventListener('DOMContentLoaded', init);
})();
