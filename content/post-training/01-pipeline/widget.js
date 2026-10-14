(() => {
  const { svg, clear, fmt } = Deck;

  const OUT = [
    '<b>Prompt:</b> Explain why the sky is blue to a 6-year-old.<br><br><span style="color:var(--muted)">Explain why the grass is green to a 6-year-old. Explain why the sea is salty to a 6-year-old. Explain why…</span><br><br><i>The base model continues the pattern: on the web, a line like this is often part of a list of similar prompts.</i>',
    '<b>Prompt:</b> Explain why the sky is blue to a 6-year-old.<br><br><span style="color:var(--muted)">Sunlight is made of many colours. When it enters the atmosphere, the blue light is scattered by the gas molecules in the air more than other colours, which is called Rayleigh scattering, so we see blue.</span><br><br><i>SFT taught the format: it answers. But it copied the style of its demonstrations and ignored "6-year-old".</i>',
    '<b>Prompt:</b> Explain why the sky is blue to a 6-year-old.<br><br><span style="color:var(--muted)">Sunlight looks white, but it\'s really all the colours of the rainbow mixed together! When sunlight bumps into the tiny bits of air high above us, the blue part gets bounced all around the sky, much more than the other colours. So wherever you look up, blue light is coming at you. That\'s why the sky looks blue!</span><br><br><i>Preference tuning favoured the answer people rated higher: it follows the instruction about the audience.</i>',
  ];
  Deck.seg('sSeg', v => { document.getElementById('sOut').innerHTML = OUT[+v]; });
  const ST = {
    pre: ['trillions of web tokens', 'next-token loss', '1 (the model)', 'Architecture guide', 'Learns language and knowledge. Expensive: weeks on thousands of GPUs. Everything below is cheap by comparison.'],
    sft: ['~10k–100k demonstrations', 'next-token loss on answer tokens only', '1 (the policy)', '02 (+ 03 LoRA)', 'Learns the chat format, when to stop, and the style of the demonstrations. Loss is masked to the assistant\'s tokens.'],
    rm: ['~30k–1M+ comparisons', 'Bradley-Terry: −log σ(r_w − r_l)', '1 (the reward model)', '04', 'Learns to score a whole response with one number that agrees with human rankings. Usually initialized from the SFT model with a scalar head.'],
    ppo: ['prompts only (the policy samples answers)', 'reward − β·KL, PPO clipped objective', '4: policy, reference, reward model, value model', '05, 06', 'Online RL: sample from the current policy, score with the RM, update. Most expressive, but the most memory and the most tuning.'],
    dpo: ['preference pairs', '−log σ(β·(margin of log-ratios))', '2: policy and frozen reference', '07', 'Optimizes the same objective as RLHF in closed form, as a classification loss. No reward model, no sampling during training.'],
    rlvr: ['prompts with checkable answers', 'rule-based reward, group-relative advantage', '2: policy and reference (no critic)', '08', 'For maths, code and formats: a verifier replaces the reward model. GRPO uses a group of samples per prompt as its own baseline.'],
  };
  Deck.seg('pSeg', v => { const [d, l, m, k, info] = ST[v]; Deck.out('pD', d); Deck.out('pL', l); Deck.out('pM', m); Deck.out('pK', k); document.getElementById('pInfo').innerHTML = info; });

})();
