/* Steppable diagrams (the ::: diagram block). The full design shows on load; "reset" then "next step"
   walks through it, highlighting the newest element and showing that step's caption. */
(() => {
  document.querySelectorAll('.dgm').forEach(box => {
    const caps = JSON.parse(box.dataset.steps), els = [...box.querySelectorAll('[data-step]')], cap = box.querySelector('.dgcap');
    const max = Math.max(0, ...els.map(e => +e.dataset.step));
    let k = max, full = true;
    const show = () => {
      els.forEach(e => {
        const s = +e.dataset.step;
        e.classList.toggle('dg-off', s > k);
        e.classList.toggle('dg-now', s === k && k > 0);
      });
      cap.innerHTML = k === 0 ? 'Press <b>next step</b> to walk through the design.'
        : k === max && full ? 'Full design shown. Press <b>reset</b>, then <b>next step</b>, to walk through it one step at a time.'
        : `<b>Step ${k} of ${max}.</b> ${caps[k - 1] || ''}`;
      full = false;
    };
    box.querySelector('[data-dg=next]').addEventListener('click', () => { k = Math.min(max, k + 1); show(); });
    box.querySelector('[data-dg=all]').addEventListener('click', () => { k = max; full = false; show(); cap.innerHTML = '<b>Full design.</b> ' + caps.map((c, i) => `${i + 1}. ${c}`).join(' '); });
    box.querySelector('[data-dg=reset]').addEventListener('click', () => { k = 0; show(); });
    show();
  });
})();
