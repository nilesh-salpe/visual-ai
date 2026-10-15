(() => {
  const { svg, clear, fmt } = Deck;
  const L = 48;
  Deck.bind(['baN', 'baR'], () => {
    const n = Math.round(Math.pow(2, Deck.val('baN'))), r = Deck.val('baR');
    const att = r === 0 ? 0 : Math.round(L / r), lin = L - att;
    Deck.out('baNo', n >= 1048576 ? (n / 1048576).toFixed(0) + 'M' : n >= 1024 ? Math.round(n / 1024) + 'K' : n);
    Deck.out('baRo', r === 0 ? 'none' : r === 1 ? 'all' : '1 in ' + r);
    const kv = 2 * 2 * 256 * 2, state = 32 * 128 * 128 * 2, GiB = 1024 ** 3;
    const full = L * kv * n / GiB, hyb = (att * kv * n + lin * state) / GiB;
    Deck.hbars(document.getElementById('baBars'), [
      { label: 'all 48 layers full attention', value: full, color: 'var(--d)', text: full >= 1 ? full.toFixed(1) + ' GiB' : (full * 1024).toFixed(0) + ' MiB' },
      { label: r === 0 ? 'no attention layers (pure linear)' : `${att} attention + ${lin} linear layers`, value: hyb, color: r === 0 ? 'var(--c)' : 'var(--e)', text: hyb >= 1 ? hyb.toFixed(1) + ' GiB' : (hyb * 1024).toFixed(0) + ' MiB' }], { max: Math.max(full, hyb) * 1.05 });
    document.getElementById('baOut').innerHTML = `One sequence of ${n.toLocaleString()} tokens, BF16, attention layers with 2 KV heads × 256 and linear layers with a 32 × 128 × 128 state (the Qwen3-Next configuration). ` +
      (r === 0 ? 'With no attention, memory is constant in context length, but exact recall suffers.' : `The hybrid needs <b>${(full / hyb).toFixed(1)}×</b> less memory; at long context the ratio approaches the attention fraction.`);
  });
})();
