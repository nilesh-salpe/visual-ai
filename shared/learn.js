// Quiz / reveal behaviour for "Your turn", "Misconceptions" and "Check yourself" beats.
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.quiz').forEach(q => {
    const btns = [...q.querySelectorAll('.opts button')];
    btns.forEach(b => b.addEventListener('click', () => {
      if (q.classList.contains('done')) return;
      q.classList.add('done');
      btns.forEach(x => { x.disabled = true; if (x.hasAttribute('data-ok')) x.classList.add('right'); });
      if (!b.hasAttribute('data-ok')) b.classList.add('wrong');
    }));
    const r = q.querySelector('.reveal');
    if (r) r.addEventListener('click', () => q.classList.add('done'));
  });
});
