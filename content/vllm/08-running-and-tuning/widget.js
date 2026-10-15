(() => {
  const { svg, clear, fmt } = Deck;
  let goal = 'lat';
  const draw = () => {
    const g = Deck.val('cG'); Deck.out('cGo', g); const fp8 = document.getElementById('cF').checked, spec = document.getElementById('cS').checked;
    const lines = ['vllm serve meta-llama/Llama-3.1-8B-Instruct'], why = [];
    if (goal === 'thr' && g > 1) { lines.push(`  -dp ${g}`); why.push(`<b>-dp ${g}</b>: the model fits on one GPU, so replicas add throughput.`); }
    else if (g > 1) { lines.push(`  -tp ${g}`); why.push(`<b>-tp ${g}</b>: shards weights and KV heads, freeing KV room and cutting per-step work.`); }
    if (goal === 'lat') { lines.push('  --max-num-batched-tokens 2048'); why.push('<b>--max-num-batched-tokens 2048</b>: smaller steps keep inter-token latency low.'); }
    if (goal === 'thr') { lines.push('  --max-num-batched-tokens 16384 --max-num-seqs 512'); why.push('<b>larger budget and concurrency</b>: fuller steps, higher tokens/s (watch preemptions).'); }
    if (goal === 'long') { lines.push('  --max-model-len 131072 --max-num-seqs 16'); why.push('<b>--max-model-len 131072, fewer sequences</b>: room for long contexts per request.'); }
    if (fp8) { lines.push('  --kv-cache-dtype fp8'); why.push('<b>--kv-cache-dtype fp8</b>: halves KV memory.'); }
    if (spec) { lines.push(`  --speculative-config '{"method": "ngram", "num_speculative_tokens": 4, "prompt_lookup_max": 4}'`); why.push('<b>n-gram speculation</b>: helps when outputs copy the input (summaries, code edits).'); }
    lines.push('  --gpu-memory-utilization 0.92'); why.push('<b>0.92</b> is the v0.31.0 default; lower it if other processes share the GPU.');
    document.getElementById('cCmd').textContent = lines.join(' \\\n');
    document.getElementById('cOut').innerHTML = why.join('<br>') + '<br>Then: <code>vllm bench serve</code> against it and check <code>/metrics</code>.';
  };
  Deck.seg('cGoal', v => { goal = v; draw(); }); Deck.bind(['cG', 'cF', 'cS'], draw);
})();
