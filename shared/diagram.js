/* Steppable diagrams (the ::: diagram block). The full design shows on load. "Play" builds it up one
   step at a time with that step's caption; "next step" advances by hand; "reset" clears it. */
(() => {
  document.querySelectorAll('.dgm').forEach(box => {
    const caps = JSON.parse(box.dataset.steps), els = [...box.querySelectorAll('[data-step]')], cap = box.querySelector('.dgcap');
    const max = Math.max(0, ...els.map(e => +e.dataset.step));
    const playBtn = box.querySelector('[data-dg=play]');
    let k = max, full = true, timer = null;
    const show = () => {
      els.forEach(e => {
        const s = +e.dataset.step;
        e.classList.toggle('dg-off', s > k);
        e.classList.toggle('dg-now', s === k && k > 0);
      });
      cap.innerHTML = k === 0 ? 'Press <b>play</b>, or <b>next step</b> to go at your own pace.'
        : k === max && full ? 'Full design shown. Press <b>play</b> to build it up step by step.'
        : `<b>Step ${k} of ${max}.</b> ${caps[k - 1] || ''}`;
      full = false;
    };
    const stop = () => { if (timer) { clearInterval(timer); timer = null; } if (playBtn) playBtn.textContent = '▶ play'; };
    const play = () => {
      if (timer) { stop(); return; }
      if (k >= max) { k = 0; show(); }
      playBtn.textContent = '❚❚ pause';
      timer = setInterval(() => { k = Math.min(max, k + 1); show(); if (k >= max) stop(); }, 2600);
      k = Math.min(max, k + 1); show();
    };
    if (playBtn) playBtn.addEventListener('click', play);
    box.querySelector('[data-dg=next]').addEventListener('click', () => { stop(); k = Math.min(max, k + 1); show(); });
    box.querySelector('[data-dg=all]').addEventListener('click', () => { stop(); k = max; full = false; show(); cap.innerHTML = '<b>Full design.</b> ' + caps.map((c, i) => `${i + 1}. ${c}`).join(' '); });
    box.querySelector('[data-dg=reset]').addEventListener('click', () => { stop(); k = 0; show(); });
    show();
  });
})();
