(() => {
  const { svg, clear, fmt } = Deck;
  const G = [0.8, -0.3, 0.5, 0.2]; let calls = 0, grad = 0, hist = [];
  const draw = () => {
    const div = document.getElementById('gDiv').checked, k = 4, target = G.reduce((a, b) => a + b) / k;
    Deck.hbars(document.getElementById('gBars'), [{ label: 'p.grad now', value: Math.abs(grad), color: Math.abs(grad - target) < 1e-9 && calls === 4 ? 'var(--e)' : 'var(--a)', text: grad.toFixed(3) },
      { label: 'full-batch gradient (target)', value: Math.abs(target), color: 'var(--faint)', text: target.toFixed(3) }], { max: 2.2 });
    document.getElementById('gOut').innerHTML = calls === 0 ? 'Press backward() for each micro-batch.' : `${calls} backward call(s): ${hist.join(' + ')}. ${calls === 4 && Math.abs(grad - target) < 1e-9 ? '<b>Equals the full-batch gradient.</b> Now zero_grad() before the next step.' : calls > 4 ? '<b>Too many: gradients from the next step are piling on. Call zero_grad().</b>' : calls === 4 ? '<b>Wrong scale: without ÷ k the sum is 4× the mean.</b>' : ''}`;
  };
  document.getElementById('gNext').addEventListener('click', () => { const div = document.getElementById('gDiv').checked, g = G[calls % 4] / (div ? 4 : 1); grad += g; hist.push(g.toFixed(3)); calls++; draw(); });
  document.getElementById('gZero').addEventListener('click', () => { grad = 0; calls = 0; hist = []; draw(); });
  document.getElementById('gDiv').addEventListener('change', () => { grad = 0; calls = 0; hist = []; draw(); });
  draw();
})();
