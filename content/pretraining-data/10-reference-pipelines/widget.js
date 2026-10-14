(() => {
  const { svg, clear, fmt } = Deck;
  const P = {
    c4: ['Common Crawl WET (April 2019)', 'langdetect, English ≥ 0.99', 'terminal punctuation, ≥ 5 words, ≥ 3 sentences, no "{" or lorem ipsum, cookie/JS lines removed', '—', 'three-sentence spans', 'bad-words list', '≈ 750 GB'],
    gopher: ['custom extraction (MassiveWeb)', 'English only', 'word count, word length, symbols, bullets, ellipses, alphabetic, stop words; repetition removal', '—', 'exact + MinHash 13-gram Jaccard > 0.8; test-set filtering', 'Google SafeSearch filter', 'MassiveWeb = 48% of MassiveText'],
    rw: ['WARC + trafilatura', 'fastText', 'URL score + 4.6M-domain blocklist; Gopher-style document and line rules; repetition removal', '— (deliberately rule-based)', 'MinHash (450 × 20) + exact substring; URL dedup', 'URL filtering', '5T tokens (600B released)'],
    fw: ['WARC + trafilatura', 'fastText, English score ≥ 0.65', 'URL blocklist + Gopher quality and repetition rules + selected C4 rules + custom filters', 'FineWeb-Edu: classifier on Llama-3-70B scores (threshold 3)', 'MinHash (14 × 8) per snapshot', 'URL blocklist; email and IP anonymisation', '15T tokens (Edu: 1.3T)'],
    dclm: ['re-extracted from HTML with resiliparse', 'fastText', 'RefinedWeb\'s heuristic filters', 'fastText classifier (OpenHermes 2.5 + ELI5 positives), keep top 10%', 'near-duplicate Bloom filter (MinHash performed comparably)', '—', '240T pool → 3.8T DCLM-Baseline'],
    dolma: ['CCNet output (Common Crawl WET text)', 'fastText (CCNet)', 'all Gopher rules + C4 no-punctuation rule', '—', 'URL, document and paragraph (Bloom filter)', 'regex PII masking; fastText toxicity', '3T tokens (11 TB)'],
    llama3: ['custom HTML parser (math and code aware)', 'fastText-based, 176 languages', 'duplicated n-grams, dirty words, token-distribution KL', 'fastText + DistilRoberta on Llama 2 labels; code and reasoning classifiers', 'URL + global MinHash + line (> 6 per 30M docs)', 'PII-heavy, unsafe and adult domains removed', '≈ 15T tokens; mix 50/25/17/8'] };
  const H = ['extraction', 'language ID', 'heuristic filters', 'model-based filter', 'deduplication', 'safety / PII', 'size'];
  Deck.seg('dSeg', v => { document.getElementById('dTbl').innerHTML = '<tr><th>stage</th><th>choice</th></tr>' + H.map((h, i) => `<tr><td><b>${h}</b></td><td>${P[v][i]}</td></tr>`).join(''); });
})();
