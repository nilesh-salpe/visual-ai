(() => {
  const { svg, clear, fmt } = Deck;

  const MASKS = {
    causal: [(i, j) => j <= i, 'Causal: row i sees columns 0…i. Every position predicts the next token, so there are 8 training targets here.'],
    prefix: [(i, j) => (i < 4 && j < 4) || j <= i, 'Prefix-LM: the first 4 tokens (the prompt) see each other in both directions; the rest are causal. Loss is usually only on the last 4.'],
    encdec: [(i, j) => (i < 4 && j < 4) ? 2 : (i >= 4 && j >= 4 && j <= i) ? 1 : (i >= 4 && j < 4) ? 3 : 0, 'Encoder (top-left) is bidirectional over the input. Decoder (bottom-right) is causal over the output. Cross-attention (bottom-left) lets output tokens see the whole input. Two stacks.'],
    enc: [(i, j) => true, 'Encoder-only: everything sees everything. Trained by masking about 15% of tokens and predicting them. It cannot generate left to right.'],
  };
  Deck.seg('fSeg', v => {
    const [f, txt] = MASKS[v], s = clear(document.getElementById('fSvg')), c = 26, x0 = 220, y0 = 20;
    for (let i = 0; i < 8; i++) for (let j = 0; j < 8; j++) {
      const m = f(i, j), col = m === 3 ? 'var(--c)' : m === 2 ? 'var(--b)' : m ? 'var(--a)' : 'var(--panel-2)';
      svg('rect', { x: x0 + j * c, y: y0 + i * c, width: c - 3, height: c - 3, rx: 4, style: `fill:${col}` }, s);
    }
    for (let i = 0; i < 8; i++) { svg('text', { x: x0 - 10, y: y0 + i * c + 17, 'text-anchor': 'end', class: 'tm', text: 'q' + i }, s); svg('text', { x: x0 + i * c + 11, y: y0 + 8 * c + 14, 'text-anchor': 'middle', class: 'tm', text: 'k' + i }, s); }
    document.getElementById('fOut').innerHTML = txt;
  });
  Deck.bind(['tT'], () => {
    const T = Deck.val('tT'); Deck.out('tTo', T.toLocaleString());
    Deck.hbars(document.getElementById('tBars'), [
      { label: 'causal LM: every position', value: T, color: 'var(--a)', text: T.toLocaleString() },
      { label: 'encoder-decoder, 50/50 split', value: T / 2, color: 'var(--b)', text: (T / 2).toLocaleString() },
      { label: 'masked LM (15%)', value: Math.round(0.15 * T), color: 'var(--c)', text: Math.round(0.15 * T).toLocaleString() }], { max: 8192 });
  });

})();
