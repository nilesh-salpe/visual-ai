(() => {
  const { svg, clear, fmt } = Deck;
  const rnd = seed => () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const POL = ['round robin', 'power of two', 'consistent hash', 'cache-aware'];
  Deck.bind(['rtW', 'rtS', 'rtH'], () => {
    const W = Deck.val('rtW'), S = Deck.val('rtS'), hot = Deck.val('rtH') / 100;
    Deck.out('rtWo', W); Deck.out('rtSo', S); Deck.out('rtHo', Math.round(hot * 100) + '%');
    const res = POL.map((p, pi) => {
      const r = rnd(7), r2 = rnd(11), last = {}, served = new Array(W).fill(0), load = new Array(W).fill(0);
      const home = s => { let x = s * 2654435761 % 4294967296; return Math.floor((x / 4294967296) * W); };
      let hits = 0, follow = 0, rr = 0;
      for (let n = 0; n < 3000; n++) {
        const s = r() < hot ? Math.floor(r() * Math.max(1, S * 0.05)) : Math.floor(r() * S);
        let w;
        if (p === 'round robin') w = rr++ % W;
        else if (p === 'power of two') { const a = Math.floor(r2() * W); let b = Math.floor(r2() * (W - 1)); if (b >= a) b++; w = load[a] <= load[b] ? a : b; }
        else if (p === 'consistent hash') w = home(s);
        else { const mx = Math.max(...load), mn = Math.min(...load); w = (mx - mn > 32 && mx > 1.1 * mn) ? load.indexOf(mn) : (last[s] !== undefined ? last[s] : load.indexOf(mn)); }
        if (last[s] !== undefined) { follow++; if (last[s] === w) hits++; }
        last[s] = w; served[w]++; load[w] += 1;
        if (n % 4 === 3) for (let k = 0; k < W; k++) load[k] = Math.max(0, load[k] - 1);
      }
      return { reuse: hits / Math.max(1, follow), spread: Math.max(...served) / (3000 / W) };
    });
    Deck.hbars(document.getElementById('rtBars'), res.flatMap((x, i) => [
      { label: POL[i] + ': prefix reuse', value: x.reuse, color: 'var(--e)', text: Math.round(100 * x.reuse) + '%' },
      { label: POL[i] + ': busiest vs even', value: x.spread / 3, color: 'var(--d)', text: x.spread.toFixed(2) + '×' }]), { max: 1 });
    document.getElementById('rtOut').innerHTML = `${W} replicas, ${S} active sessions, ${Math.round(hot * 100)}% of requests from a few hot sessions. Prefix reuse = later turns that land where the session\'s previous turn ran. Consistent hashing reuses everything but piles hot sessions on one replica as the hot share grows; cache-aware gives up some reuse to stay balanced. (Illustrative simulation; the notebook builds the real policies.)`;
  });
})();
