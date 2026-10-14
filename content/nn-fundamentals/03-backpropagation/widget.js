(() => {
  const { svg, clear, fmt } = Deck;
  const w = 0.5, x = 2, b = -0.3, y = 1;
  const R = [['w', 'input', () => w], ['x', 'input', () => x], ['b', 'input', () => b], ['m = w·x', 'mul(w, x)', v => v.w * v.x], ['n = m + b', 'add(m, b)', v => v.m + v.b], ['o = tanh(n)', 'tanh(n)', v => Math.tanh(v.n)], ['e = o − y', 'sub(o, y)', v => v.o - y], ['L = e²', 'pow(e, 2)', v => v.e * v.e]];
  const K = ['w', 'x', 'b', 'm', 'n', 'o', 'e', 'L'];
  let st = 0;
  const vals = {}, grads = {};
  const compute = () => { K.forEach((k, i) => { vals[k] = R[i][2](vals); }); const g = { L: 1 }; g.e = 2 * vals.e; g.o = g.e; g.n = g.o * (1 - vals.o ** 2); g.m = g.n; g.b = g.n; g.w = g.m * x; g.x = g.m * w; Object.assign(grads, g); };
  compute();
  const draw = () => {
    const fw = Math.min(st, 8), bw = Math.max(0, st - 8);
    const rows = R.map((r, i) => { const k = K[i], showV = i < fw, showG = 7 - i < bw, cur = (st <= 8 && i === fw - 1) || (st > 8 && 7 - i === bw - 1);
      return `<tr style="${cur ? 'background:var(--b-soft)' : ''}"><td><b>${r[0]}</b></td><td>${r[1]}</td><td>${showV ? vals[k].toFixed(4) : ''}</td><td style="color:var(--b);font-weight:700">${showG ? grads[k].toFixed(4) : ''}</td></tr>`; }).join('');
    document.getElementById('bTbl').innerHTML = '<tr><th>node</th><th>op</th><th>value (forward)</th><th>dL/dnode (backward)</th></tr>' + rows;
    const msg = st === 0 ? 'Press "next step" to run the forward pass.' : st < 8 ? 'Forward: each node computed from its inputs and recorded.' : st === 8 ? 'Forward done. Backward starts by setting dL/dL = 1 at the last node.' : st < 16 ? 'Backward: each node\'s gradient = upstream gradient × its local derivative, pushed to its inputs.' : `Done. dL/dw = <b>${grads.w.toFixed(4)}</b>: one backward walk gave every gradient.`;
    document.getElementById('bOut').innerHTML = msg;
  };
  document.getElementById('bNext').addEventListener('click', () => { if (st < 16) st++; draw(); });
  document.getElementById('bReset').addEventListener('click', () => { st = 0; draw(); });
  draw();
})();
