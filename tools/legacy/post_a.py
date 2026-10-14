from tool import section, your_turn, myths, check

DECKS = {}


def deep(title, html):
    return f'    <div class="deep"><h4>{title}</h4>{html}</div>'


INFOBOX = 'class="infobox" style="background:var(--panel-2);border-radius:10px;padding:12px 14px;margin-top:10px;font-size:14px;color:var(--muted)"'

# =============================================================== 01
DECKS['01-pipeline'] = dict(
    title='The Post-training Pipeline', h1='The post-training pipeline',
    sub='How a model that only predicts internet text becomes an assistant: demonstrations (SFT), preferences (reward models, RLHF, DPO) and verifiable rewards (RLVR), and how real labs combine them.',
    prob='Pretraining optimizes "predict the next token of internet text". That makes a model knowledgeable, not helpful: it continues prompts rather than following them, and it has no notion of which answer people prefer.',
    core='Fine-tune the pretrained model in stages. <b>SFT</b> imitates good demonstrations. <b>Preference optimization</b> (RLHF with a reward model, or DPO) pushes towards answers people prefer. <b>RL with verifiable rewards</b> sharpens tasks whose answers can be checked.',
    build=['01_sft_loss_masking'],
    sources='Ouyang et al. 2022, "Training language models to follow instructions with human feedback" (InstructGPT §3, Fig. 2); Christiano et al. 2017; Touvron et al. 2023 (Llama 2 §3); Llama Team 2024 (Llama 3 §4); Lambert et al. 2024 (Tülu 3); DeepSeek-AI 2025 (DeepSeek-R1).',
    slides=[
        section('s-p1', 1, 'Same knowledge, different behaviour', '''    <p class="lede">One prompt, three stages of the same model. The outputs are <b>illustrative</b> (written for this deck), but the pattern is the one InstructGPT documented: a base model continues text, an SFT model answers, and preference tuning makes the answer what people actually want.</p>
    <div class="visual">
      <div class="seg" id="sSeg"><button data-v="0" class="on">Base (pretrained)</button><button data-v="1">After SFT</button><button data-v="2">After preference tuning</button></div>
      <div class="infobox" id="sOut" style="background:var(--panel-2);border-radius:10px;padding:14px 16px;margin-top:12px;font-size:15px;line-height:1.6"></div>
    </div>'''),
        section('s-lim', 2, 'Why pretraining alone isn\'t enough', '''    <div class="grid3">
      <div class="card d"><h3>Wrong objective</h3><p>The pretraining loss rewards predicting what text comes next on the web, which includes unhelpful, wrong and toxic text. InstructGPT calls this objective "misaligned" with following instructions helpfully and safely.</p></div>
      <div class="card b"><h3>Demonstrations are expensive</h3><p>Writing an ideal answer for every kind of request takes expert time. InstructGPT's SFT set had about 13k prompts; Llama 2 stopped at 27,540 high-quality annotations.</p></div>
      <div class="card c"><h3>Imitation has a ceiling</h3><p>SFT can only copy its demonstrations. To prefer answers better than any single demonstrator would write, you need a signal that <b>compares</b> answers, which is much cheaper than writing them.</p></div>
    </div>'''),
        your_turn('s-turn', 'How much does alignment matter?',
                  'InstructGPT compared a 1.3B model with SFT + RLHF against the original 175B GPT-3. Which did human labelers prefer on the API prompt distribution?',
                  ['175B GPT-3, by a wide margin', 'They were tied', 'The 1.3B InstructGPT model', 'It depended only on prompt length'], 2,
                  '<b>C.</b> "Outputs from the 1.3B parameter InstructGPT model are preferred to outputs from the 175B GPT-3, despite having 100x fewer parameters." Post-training changed usefulness more than a 100× increase in parameters did.'),
        section('s-core', 4, 'The three InstructGPT steps', '''    <div class="grid3">
      <div class="card a"><h3>1 · SFT</h3><p>Labelers write demonstrations of the desired output for prompts; fine-tune the pretrained model on them with ordinary next-token loss. (~13k training prompts.)</p></div>
      <div class="card b"><h3>2 · Reward model</h3><p>Sample several outputs per prompt, labelers rank them (K = 4 to 9), and train a model to output a scalar score that agrees with the rankings. (~33k prompts.)</p></div>
      <div class="card e"><h3>3 · RL (PPO)</h3><p>Optimize the SFT model to maximize the reward model's score with PPO, with a KL penalty that keeps it close to the SFT model. (~31k prompts.)</p></div>
    </div>
''' + deep('Where the idea came from', '<p>Christiano et al. (2017) showed RL from human <b>comparisons</b> could teach Atari and robotics behaviours with feedback on less than 1% of the agent\'s interactions, and about an hour of human time for some novel behaviours. Stiennon et al. (2020) applied it to summarization; InstructGPT applied it to general instruction following.</p>')),
        section('s-how', 5, 'Each stage: data, loss, models in memory', '''    <p class="lede">Pick a stage to see what it consumes and what it costs. The later decks cover each one in depth.</p>
    <div class="visual">
      <div class="seg" id="pSeg"><button data-v="pre">Pretraining</button><button data-v="sft" class="on">SFT</button><button data-v="rm">Reward model</button><button data-v="ppo">RLHF (PPO)</button><button data-v="dpo">DPO</button><button data-v="rlvr">RLVR (GRPO)</button></div>
      <div class="grid4" style="margin-top:14px">
        <div class="stat"><div class="num" id="pD" style="font-size:16px"></div><div class="lbl">training data</div></div>
        <div class="stat"><div class="num" id="pL" style="font-size:16px"></div><div class="lbl">loss / signal</div></div>
        <div class="stat"><div class="num" id="pM" style="font-size:16px"></div><div class="lbl">models in memory</div></div>
        <div class="stat"><div class="num" id="pK" style="font-size:16px"></div><div class="lbl">deck</div></div>
      </div>
      <div ''' + INFOBOX + ''' id="pInfo"></div>
    </div>'''),
        section('s-how2', 5, 'How real recipes combine the pieces', '''    <div class="visual scroll-x"><table class="tbl">
      <tr><th>Model</th><th>Post-training recipe (as reported)</th></tr>
      <tr><td>InstructGPT (2022)</td><td>SFT → reward model → PPO, with a pretraining-loss mix ("PPO-ptx") to reduce regressions</td></tr>
      <tr><td>Llama 2-Chat (2023)</td><td>SFT on 27,540 annotations → two reward models (helpfulness, safety) on over 1M comparisons → five RLHF rounds: rejection-sampling fine-tuning only up to V4, then PPO on top</td></tr>
      <tr><td>Llama 3 (2024)</td><td>Several rounds (six, following Llama 2) of reward modelling → SFT on rejection-sampled data → DPO</td></tr>
      <tr><td>Tülu 3 (2024)</td><td>SFT → DPO → RL with verifiable rewards (the paper that named RLVR)</td></tr>
      <tr><td>DeepSeek-R1 (2025)</td><td>R1-Zero: RL with rule-based rewards directly on the base model, no SFT. R1: a "multi-stage learning framework that integrates rejection sampling, reinforcement learning, and supervised finetuning", starting from cold-start long chain-of-thought data</td></tr>
    </table></div>
''' + deep('The common pattern', '<p>Every recipe starts with SFT to teach the format, then uses <b>comparisons or checks on the model\'s own outputs</b> to improve beyond the demonstrations, and repeats in rounds so new preference data comes from the current model. The choice of optimizer (PPO, rejection sampling, DPO, GRPO) is mostly about cost, stability and what signal is available.</p>')),
        section('s-why', 6, 'Why preferences work so well', '''    <div class="grid2">
      <div class="card a"><h3>Judging is easier than writing</h3><p>A labeler can reliably pick the better of two answers even when they couldn't write either. Comparisons are cheaper and more consistent than absolute scores.</p></div>
      <div class="card e"><h3>Feedback on the model's own outputs</h3><p>SFT learns from someone else's text. Preference and RL methods learn from what <b>this</b> model actually produces, including its own mistakes.</p></div>
      <div class="card b"><h3>Knowledge comes from pretraining</h3><p>Post-training is small compared with pretraining (thousands to millions of examples vs trillions of tokens). It mostly selects and shapes behaviour the base model can already produce.</p></div>
      <div class="card c"><h3>The cost: an "alignment tax"</h3><p>InstructGPT saw RLHF reduce performance on some public NLP benchmarks, and mixing pretraining gradients into PPO (PPO-ptx) largely fixed it without hurting preference scores.</p></div>
    </div>'''),
        myths('s-myth', [
            ('Post-training is where the model learns its knowledge.', 'Knowledge comes overwhelmingly from pretraining on trillions of tokens. Post-training uses far less data and mainly changes <b>behaviour</b>: format, helpfulness, refusals, reasoning style.'),
            ('RLHF means humans give a reward to every answer during training.', 'Humans label a fixed set of comparisons once per round. A <b>reward model</b> trained on them scores the millions of samples seen during RL.'),
            ('There is one standard recipe.', 'InstructGPT used PPO, Llama 3 used rejection sampling + DPO, DeepSeek-R1-Zero used RL with rule-based rewards and no SFT. The building blocks are shared; the mix varies.'),
        ]),
        check('s-check', [
            ('mcq', 'In InstructGPT, what do labelers provide for the reward model?', ['Scores from 1 to 10', 'Rankings of 4–9 sampled outputs per prompt', 'Rewritten answers', 'Binary safe/unsafe labels'], 1, '<b>Rankings of K = 4–9 outputs</b>, converted into pairwise comparisons.'),
            ('open', 'Why is a KL penalty to the SFT model added during RL?', 'The reward model is an imperfect proxy. Without a leash, the policy drifts into outputs where the reward model is wrong (reward hacking). The KL term keeps it near the SFT model, where the reward model was trained.'),
            ('open', 'Name the three InstructGPT steps and what each trains.', 'SFT trains the policy on demonstrations; reward modelling trains a scalar scorer on rankings; PPO trains the policy to maximize that score minus a KL penalty.'),
        ]),
    ],
    js=r'''
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
''',
    line='Post-training turns a next-token predictor into an assistant: imitate demonstrations (SFT), then optimize towards what people prefer or what can be verified, repeating in rounds.',
    explain='A pretrained model knows a lot but just continues text. Post-training fixes behaviour in stages. Supervised fine-tuning imitates written demonstrations and teaches the chat format. Then preference optimization uses comparisons, which are much cheaper than demonstrations: either train a reward model and optimize against it with RL and a KL penalty, as InstructGPT did, or optimize the same objective directly with DPO. For maths and code, a verifier can replace the reward model. InstructGPT showed a 1.3 billion parameter model after this process was preferred to the 175 billion parameter base GPT-3.',
    recap=[('Problem', 'next-token pretraining is knowledgeable but not helpful.'), ('Core idea', 'SFT on demonstrations, then optimize preferences (RM + PPO, or DPO) or verifiable rewards.'), ('Practice', 'labs iterate rounds: InstructGPT PPO, Llama 3 RS + DPO, R1 RL with rule-based rewards.')],
)

# =============================================================== 02
DECKS['02-supervised-fine-tuning'] = dict(
    title='Supervised Fine-tuning', h1='Supervised fine-tuning (SFT)',
    sub='The first post-training step: chat templates, training only on the assistant\'s tokens, packing, and why a few thousand high-quality examples beat a million mediocre ones.',
    prob='A base model has no notion of "user" and "assistant", doesn\'t know when an answer ends, and imitates whatever style its prompt resembles.',
    core='Fine-tune on <b>demonstrations</b> rendered with a <b>chat template</b>, using ordinary next-token loss but <b>only on the assistant\'s tokens</b> (including its end-of-turn token). Pack examples to avoid wasting compute on padding.',
    build=['01_sft_loss_masking'],
    sources='Ouyang et al. 2022 (InstructGPT §3.5, Appendix); Touvron et al. 2023 (Llama 2 §3.1: "Quality Is All You Need", 27,540 annotations, loss on answer tokens only, packing, hyperparameters).',
    slides=[
        section('s-p1', 1, 'One conversation, one token sequence', '''    <p class="lede">A chat model sees a single flat sequence. The template inserts role markers and end-of-turn tokens. Colour shows what the loss is computed on. Toggle to compare training on everything vs only the assistant's answers.</p>
    <div class="visual">
      <div class="seg" id="mSeg"><button data-v="1" class="on">Loss on assistant tokens only</button><button data-v="0">Loss on every token</button></div>
      <div id="mToks" style="display:flex;flex-wrap:wrap;gap:5px;margin-top:14px;font:500 13px 'JetBrains Mono',monospace"></div>
      <p class="readout" id="mOut"></p>
    </div>
    <p class="caption">Illustrative template with generic role tokens. Real models define their own (each tokenizer's chat template), but the structure is the same.</p>'''),
        section('s-lim', 2, 'What a base model gets wrong', '''    <div class="grid3">
      <div class="card d"><h3>No turn structure</h3><p>It has never seen consistent role markers, so it may keep writing the user's next message, or invent a whole dialogue.</p></div>
      <div class="card b"><h3>No stopping point</h3><p>It doesn't know an answer is finished. Without a trained end-of-turn token it rambles until the length limit.</p></div>
      <div class="card c"><h3>Style follows the prompt</h3><p>Ask casually and you get forum-style text; ask formally and you get a paper. SFT pins down one consistent assistant style.</p></div>
    </div>'''),
        your_turn('s-turn', 'Which tokens should be trained?',
                  'In a two-turn chat (system, user, assistant, user, assistant), where should the SFT loss be computed?',
                  ['On every token', 'Only on the user turns', 'On the assistant turns, including each end-of-turn token', 'Only on the final assistant turn'], 2,
                  '<b>C.</b> The model should learn to <i>produce</i> answers and to stop, not to predict what users type. Llama 2: "we zero-out the loss on tokens from the user prompt, so as a result, we backpropagate only on answer tokens." Earlier assistant turns are valid targets too.'),
        section('s-core', 4, 'SFT in one paragraph', '''    <div class="grid3">
      <div class="card a"><h3>Render</h3><p>Messages → template → token ids, plus a mask marking the assistant's content and closing end-of-turn token as trainable.</p></div>
      <div class="card b"><h3>Shift and mask</h3><p>Inputs = tokens[:-1], labels = tokens[1:]. Set untrained labels to −100, the value standard cross-entropy implementations ignore.</p></div>
      <div class="card e"><h3>Train</h3><p>Average next-token loss over trained positions only. Small learning rate (Llama 2: 2×10⁻⁵), few epochs (Llama 2: 2), sequences up to 4,096 tokens.</p></div>
    </div>
''' + deep('Epochs and overfitting', '<p>InstructGPT found its SFT models "overfit on validation loss after 1 epoch", yet "training for more epochs helps both the RM score and human preference ratings, despite this overfitting". Validation loss on demonstrations is not the goal; behaviour is. That is one reason labs judge SFT checkpoints with preference models and evals rather than perplexity.</p>')),
        section('s-how', 5, 'Packing: stop paying for padding', '''    <p class="lede">20 examples of random length go into rows of 2,048 tokens. With one example per row, everything is padded to the longest example. Packing fills each row with whole examples, in order, and pads only the tail.</p>
    <div class="visual">
      <div class="seg" id="kSeg"><button data-v="pad">One example per row</button><button data-v="pack" class="on">Packed</button></div>
      <svg id="kSvg" viewBox="0 0 660 260" style="margin-top:10px" role="img" aria-label="Padding vs packing"></svg>
      <p class="readout" id="kOut"></p>
    </div>
''' + deep('Packing needs a document mask', '<p>Llama 2: "we concatenate all the prompts and answers from the training set", with a special token separating segments. Without a document mask (or position resets), tokens in one example can attend to the previous, unrelated example in the same row. See <a href="../../architecture/06-decoder-only/index.html">Architecture deck 06</a>.</p>')),
        section('s-how2', 5, 'Quality beats quantity', '''    <div class="grid2">
      <div class="card a"><h3>Llama 2: "Quality Is All You Need"</h3><p>Meta found third-party SFT data had "insufficient diversity and quality". They collected their own and stopped at <b>27,540</b> annotations: a small set of high-quality examples beat millions of mediocre ones.</p></div>
      <div class="card e"><h3>InstructGPT: ~13k prompts</h3><p>Written by a vetted team of labelers, covering generation, open QA, brainstorming, chat, rewriting, summarization and more.</p></div>
      <div class="card b"><h3>What makes data good</h3><p>Correct, consistent in format and style, diverse in task, and at the difficulty you want the model to reach. Errors in demonstrations are imitated faithfully.</p></div>
      <div class="card c"><h3>Synthetic data</h3><p>Modern recipes generate candidate answers with models and keep the best (rejection sampling, deck 07). Llama 3's SFT data combines human-collected prompts with rejection-sampled model responses, plus targeted synthetic data.</p></div>
    </div>'''),
        section('s-why', 6, 'Why SFT comes first', '''    <div class="grid2">
      <div class="card a"><h3>It makes RL feasible</h3><p>RL and preference methods learn from the model's own samples. If the model can't produce a sensible answer at all, there is nothing to compare or reward. SFT puts it in the right region.</p></div>
      <div class="card e"><h3>It defines the reference</h3><p>The SFT model is the reference policy for the KL penalty (PPO) and for DPO's log-ratios. Later stages stay close to it.</p></div>
      <div class="card b"><h3>Cheap and stable</h3><p>Plain supervised learning: no sampling, no reward model, one model in memory, and with LoRA it fits on modest hardware (deck 03).</p></div>
      <div class="card c"><h3>But it only imitates</h3><p>It can't exceed its demonstrations or learn from comparisons, and it gives no signal on which of two plausible answers is better.</p></div>
    </div>'''),
        myths('s-myth', [
            ('Training on the whole conversation is just as good.', 'Then the model spends capacity predicting user messages, and the loss is diluted by tokens you never want it to generate. Standard practice (Llama 2) masks prompt tokens.'),
            ('More SFT data is always better.', 'Llama 2 got better results from 27,540 carefully collected examples than from millions of third-party ones. Bad examples are imitated too.'),
            ('Lowest validation loss is the best SFT checkpoint.', 'InstructGPT trained past the validation-loss minimum because reward-model scores and human preferences kept improving.'),
        ]),
        check('s-check', [
            ('mcq', 'Which label value tells a standard cross-entropy loss to skip a position?', ['0', '−1', '−100', 'the pad token id'], 2, '<b>−100</b> (PyTorch\'s default ignore_index).'),
            ('open', 'Why must the assistant\'s end-of-turn token be trained?', 'Otherwise the model never learns when to stop. It would keep generating past the end of the answer, often inventing the next user turn.'),
            ('open', 'What does packing save, and what extra mechanism does it need?', 'It removes padding, so nearly every position is a real token. It needs a document mask (or position resets) so packed examples don\'t attend to each other.'),
        ]),
    ],
    js=r'''
  const T = [['<bos>', 0], ['<system>', 0], ['you', 0], ['are', 0], ['helpful', 0], ['<eot>', 0], ['<user>', 0], ['what', 0], ['is', 0], ['2+2', 0], ['?', 0], ['<eot>', 0], ['<assistant>', 0], ['2+2', 1], ['is', 1], ['4.', 1], ['<eot>', 1], ['<user>', 0], ['and', 0], ['3+3', 0], ['?', 0], ['<eot>', 0], ['<assistant>', 0], ['6.', 1], ['<eot>', 1]];
  Deck.seg('mSeg', v => {
    const only = v === '1', box = document.getElementById('mToks'); box.innerHTML = '';
    T.forEach(([t, a]) => { const s = document.createElement('span'); const on = only ? a : 1; s.textContent = t; s.style.cssText = `padding:4px 8px;border-radius:6px;background:${on ? 'var(--a)' : 'var(--panel-2)'};color:${on ? '#fff' : 'var(--muted)'}`; box.appendChild(s); });
    const n = only ? T.filter(x => x[1]).length : T.length;
    document.getElementById('mOut').innerHTML = only ? `Loss on <b>${n} of ${T.length}</b> tokens: the two answers and their end-of-turn tokens. Role tokens and user text are context only.` : `Loss on all <b>${T.length}</b> tokens: the model is also trained to predict what the user types and the template itself.`;
  });
  let seed = 3; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const LENS = [...Array(20)].map(() => Math.round(150 + rnd() * 900));
  Deck.seg('kSeg', v => {
    const s = clear(document.getElementById('kSvg')), Lr = 2048, W = 600, x0 = 40;
    let rows;
    if (v === 'pad') { const m = Math.max(...LENS); rows = LENS.map(l => [[l, m]]); }
    else { rows = []; let cur = [], used = 0; LENS.forEach(l => { if (used + l > Lr) { rows.push(cur); cur = []; used = 0; } cur.push([l]); used += l; }); rows.push(cur); }
    const width = v === 'pad' ? Math.max(...LENS) : Lr, rh = Math.min(22, 240 / rows.length);
    let real = 0, total = 0;
    rows.forEach((row, i) => {
      let x = x0; const y = 10 + i * rh;
      row.forEach(([l], j) => { svg('rect', { x, y, width: l / width * W - 1, height: rh - 3, rx: 2, style: `fill:hsl(${(i * 3 + j) * 47 % 360},55%,55%)` }, s); x += l / width * W; real += l; });
      svg('rect', { x, y, width: Math.max(0, x0 + W - x), height: rh - 3, rx: 2, style: 'fill:var(--panel-2)' }, s);
      total += width;
    });
    document.getElementById('kOut').innerHTML = `${rows.length} rows × ${width.toLocaleString()} positions: <b>${(100 * real / total).toFixed(0)}%</b> are real tokens, the rest is padding (grey) that still costs compute.`;
  });
''',
    line='SFT is next-token training on demonstrations, rendered with a chat template and with the loss only on the assistant\'s tokens, using fewer but better examples.',
    explain='Supervised fine-tuning is the first post-training step. Each conversation is rendered with a chat template into one token sequence, and the model is trained with ordinary next-token loss, but only on the assistant\'s tokens and its end-of-turn token, so it learns to answer and to stop rather than to predict users. Examples are packed into full-length rows with a document mask to avoid wasted padding. Quality matters more than quantity: Llama 2 stopped at about 27,500 carefully collected examples. SFT teaches format and style and gives the later preference stages a sensible starting point and reference model.',
    recap=[('Problem', 'base models don\'t follow turns, don\'t stop, and mimic the prompt\'s style.'), ('Core idea', 'chat template + loss on assistant tokens only (+ end-of-turn).'), ('Practice', 'pack with a document mask; a small, high-quality dataset; judge by behaviour, not validation loss.')],
)

# =============================================================== 03
DECKS['03-lora-qlora'] = dict(
    title='LoRA and QLoRA', h1='LoRA and QLoRA',
    sub='Fine-tune by training a tiny low-rank update instead of every weight, and keep the frozen base model in 4-bit NormalFloat to fit large models on one GPU.',
    prob='Full fine-tuning stores gradients and optimizer state for every parameter and produces a full model copy per task: for an 8B model that is roughly 100 GB of training memory and 16 GB per checkpoint.',
    core='<b>LoRA</b>: freeze W₀ and learn ΔW = BA of rank r (B starts at 0), then merge after training. <b>QLoRA</b>: store the frozen base in 4-bit <b>NF4</b>, dequantize on the fly, train LoRA adapters in 16-bit.',
    build=['02_lora', '03_nf4_quantization'],
    sources='Hu et al. 2021, "LoRA: Low-Rank Adaptation of Large Language Models" (§4, Fig. 1, §7); Dettmers et al. 2023, "QLoRA: Efficient Finetuning of Quantized LLMs" (§3, Appendix E NF4 values).',
    slides=[
        section('s-p1', 1, 'Where the memory goes in full fine-tuning', '''    <p class="lede">Rough training memory: BF16 weights (2 bytes per parameter), FP32 gradients (4), and Adam's two FP32 moments (8). Activations are extra. LoRA keeps the last three only for its adapters; QLoRA also shrinks the frozen weights to about 4 bits.</p>
    <div class="visual">
      <div class="seg" id="fSeg"><button data-v="8.03" class="on">8B</button><button data-v="65">65B</button></div>
      <div id="fBars" style="margin-top:12px"></div>
    </div>
    <p class="caption">Estimates from parameter counts, ignoring activations. QLoRA reports 65B fine-tuning going from more than 780 GB to under 48 GB of GPU memory.</p>'''),
        section('s-lim', 2, 'The cost of updating everything', '''    <div class="grid3">
      <div class="card d"><h3>Optimizer state for every weight</h3><p>Adam keeps two extra numbers per parameter, plus a gradient. That state is several times the size of the model itself.</p></div>
      <div class="card b"><h3>One full copy per task</h3><p>Ten fine-tuned variants of an 8B model are ten 16 GB checkpoints to store and to serve separately.</p></div>
      <div class="card c"><h3>Adapters add latency</h3><p>Earlier parameter-efficient methods inserted extra layers ("adapters") that stay in the forward pass at inference time.</p></div>
    </div>'''),
        your_turn('s-turn', 'How many trainable parameters?',
                  'A 4,096 × 4,096 projection gets a LoRA update of rank r = 8. How many trainable parameters does that add?',
                  ['16,777,216', '65,536', '32,768', '8'], 1,
                  '<b>B.</b> A is 4,096 × 8 and B is 8 × 4,096: r·(d_in + d_out) = 8 × 8,192 = <b>65,536</b>, which is 0.4% of the 16.8M entries in the full matrix.'),
        section('s-core', 4, 'Low-rank updates', '''    <div class="grid3">
      <div class="card a"><h3>Freeze, then add BA</h3><p>h = W₀x + (α/r)·BAx. W₀ is frozen. A gets a random Gaussian init and B starts at <b>zero</b>, "so ΔW = BA is zero at the beginning of training": you start exactly at the pretrained model.</p></div>
      <div class="card b"><h3>Choose where and how big</h3><p>The paper mostly adapts only W_q and W_v, and finds very small ranks (even r = 1–4) work well there. Many practitioners adapt all linear layers.</p></div>
      <div class="card e"><h3>Merge for free inference</h3><p>After training, W = W₀ + (α/r)BA is one ordinary matrix: "no additional inference latency". You can also keep W₀ shared and swap small adapters per task.</p></div>
    </div>
''' + deep('Reported results', '<p>On GPT-3 175B, LoRA "can reduce the number of trainable parameters by 10,000 times and the GPU memory requirement by 3 times", and performs on par or better than full fine-tuning in model quality on RoBERTa, DeBERTa, GPT-2 and GPT-3, with higher training throughput. The α/r scale means changing r doesn\'t require retuning the learning rate much; the paper simply sets α to the first r tried.</p>')),
        section('s-how', 5, 'LoRA parameter calculator', '''    <p class="lede">For Llama 3 8B (32 layers, d = 4,096, GQA with 1,024-wide K/V, FFN 14,336), choose the rank and which matrices get adapters.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0">
        <label class="ctl">rank r <input type="range" id="lR" min="0" max="8" step="1" value="3"> <output id="lRo"></output></label>
        <div class="seg" id="lT"><button data-v="qv" class="on">W_q, W_v (paper default)</button><button data-v="attn">all attention</button><button data-v="all">all linear layers</button></div>
      </div>
      <div class="grid3" style="margin-top:14px">
        <div class="stat"><div class="num" id="lP" style="color:var(--a)"></div><div class="lbl">trainable parameters</div></div>
        <div class="stat"><div class="num" id="lF"></div><div class="lbl">of the 8.03B base</div></div>
        <div class="stat"><div class="num" id="lS"></div><div class="lbl">adapter size (BF16)</div></div>
      </div>
      <svg id="lSvg" viewBox="0 0 660 150" style="margin-top:10px" role="img" aria-label="W0 plus BA"></svg>
    </div>'''),
        section('s-how2', 5, 'QLoRA: a 4-bit frozen base', '''    <p class="lede">The 16 NF4 levels (from the QLoRA paper) vs 16 evenly spaced INT4 levels, drawn over a normal distribution like the one pretrained weights follow. NF4 puts more levels where most weights are.</p>
    <div class="visual">
      <svg id="qSvg" viewBox="0 0 660 200" role="img" aria-label="NF4 vs INT4 levels"></svg>
      <div class="legend"><span><i style="background:var(--a)"></i>NF4 levels</span><span><i style="background:var(--b)"></i>INT4 levels (uniform)</span><span><i style="background:var(--faint)"></i>normal density</span></div>
    </div>
''' + deep('The three QLoRA ingredients', '<ul><li><b>NF4</b>: blockwise (64 weights per block) absmax-scaled 4-bit codes at normal quantiles. Notebook 03 measures lower error than uniform INT4 on Gaussian weights.</li><li><b>Double quantization</b>: quantize the per-block scales too, cutting their overhead from 0.5 to 0.127 bits per parameter, about 3 GB for a 65B model.</li><li><b>Paged optimizers</b>: page optimizer state between GPU and CPU memory to survive memory spikes.</li></ul><p>Weights are dequantized to BF16 for each matmul; gradients flow through them to the 16-bit LoRA adapters. The paper: 4-bit QLoRA with NF4 "matches 16-bit full finetuning and 16-bit LoRA finetuning performance on academic benchmarks".</p>')),
        section('s-why', 6, 'Why a low rank is enough', '''    <div class="grid2">
      <div class="card a"><h3>Updates have low intrinsic rank</h3><p>The LoRA paper's hypothesis, supported by its experiments: the change needed to adapt a pretrained model lives in a small subspace, even though the weights themselves are full rank.</p></div>
      <div class="card e"><h3>Notebook evidence</h3><p>Fitting a rank-4 update: ranks 1–3 plateau at clear error, rank ≥ 4 fits essentially perfectly. A rank above the true rank adds nothing.</p></div>
      <div class="card b"><h3>The trade-off</h3><p>Low rank limits what can change. For large shifts (new languages, lots of new knowledge), higher ranks, more target matrices, or full fine-tuning can do better.</p></div>
      <div class="card c"><h3>Serving many variants</h3><p>Because adapters are tiny, one base model can serve many fine-tunes by swapping or batching adapters, instead of loading many full copies.</p></div>
    </div>'''),
        myths('s-myth', [
            ('LoRA makes inference slower.', 'Merge W₀ + (α/r)BA after training and the model is exactly as fast as before. That is a main advantage over adapter layers.'),
            ('QLoRA trains in 4-bit.', 'Only the <b>frozen base weights</b> are stored in 4-bit. They are dequantized to BF16 for compute, and the LoRA adapters and their gradients are 16-bit.'),
            ('A bigger rank is always better.', 'Past the rank the task needs, extra rank only adds parameters; the paper found very small ranks sufficient for W_q and W_v.'),
        ]),
        check('s-check', [
            ('mcq', 'Why is B initialized to zero?', ['To save memory', 'So the model starts exactly at the pretrained weights', 'Because A is random and B must be orthogonal', 'To make merging possible'], 1, '<b>B.</b> BA = 0 at step 0, so training starts from W₀ exactly.'),
            ('open', 'Name the three techniques QLoRA combines with LoRA.', '4-bit NormalFloat (NF4) storage of the frozen base, double quantization of the scales, and paged optimizers.'),
            ('open', 'Adapters for W_q and W_v at r = 8 on Llama 3 8B: how many trainable parameters?', '32 × 8 × [(4,096 + 4,096) + (4,096 + 1,024)] = <b>3,407,872</b>, about 0.04% of 8.03B.'),
        ]),
    ],
    js=r'''
  Deck.seg('fSeg', v => {
    const P = +v, full = P * 14, lora = P * 2 + 0.004 * P * 12, q = P * (0.5 + 0.127 / 8) + 0.004 * P * 12;
    Deck.hbars(document.getElementById('fBars'), [
      { label: 'full fine-tune', value: full, color: 'var(--d)', text: Math.round(full) + ' GB' },
      { label: 'LoRA (BF16 base)', value: lora, color: 'var(--b)', text: Math.round(lora) + ' GB' },
      { label: 'QLoRA (NF4 base)', value: q, color: 'var(--a)', text: q.toFixed(1) + ' GB' }], { max: 65 * 14 });
  });
  const SHAPES = { q: [4096, 4096], k: [4096, 1024], v: [4096, 1024], o: [4096, 4096], gate: [4096, 14336], up: [4096, 14336], down: [14336, 4096] };
  const SETS = { qv: ['q', 'v'], attn: ['q', 'k', 'v', 'o'], all: Object.keys(SHAPES) };
  let set = 'qv';
  const lc = () => {
    const r = Math.pow(2, Deck.val('lR')); Deck.out('lRo', r);
    const n = 32 * SETS[set].reduce((a, k) => a + r * (SHAPES[k][0] + SHAPES[k][1]), 0);
    Deck.out('lP', n.toLocaleString()); Deck.out('lF', (100 * n / 8.03e9).toPrecision(2) + '%'); Deck.out('lS', Deck.bytes(2 * n));
    const s = clear(document.getElementById('lSvg')), d = 110, w = Math.max(3, r / 256 * d);
    svg('rect', { x: 40, y: 20, width: d, height: d, rx: 4, style: 'fill:var(--panel-2);stroke:var(--line)' }, s); svg('text', { x: 95, y: 80, 'text-anchor': 'middle', class: 't', text: 'W₀ (frozen)' }, s);
    svg('text', { x: 175, y: 82, 'text-anchor': 'middle', class: 't', style: 'font-size:20px', text: '+' }, s);
    svg('rect', { x: 210, y: 20, width: w, height: d, rx: 2, class: 'f-a' }, s); svg('text', { x: 210 + w / 2, y: 145, 'text-anchor': 'middle', class: 'tm', text: 'A' }, s);
    svg('rect', { x: 220 + w, y: 20, width: d, height: w, rx: 2, class: 'f-b' }, s); svg('text', { x: 230 + w + d, y: 20 + w / 2 + 4, class: 'tm', text: 'B' }, s);
    svg('text', { x: 400, y: 60, class: 't', text: `r = ${r}: A is d×${r}, B is ${r}×d` }, s);
    svg('text', { x: 400, y: 86, class: 'tm', text: `adapters on: ${SETS[set].map(k => 'W_' + k).join(', ')}` }, s);
  };
  Deck.bind(['lR'], lc); Deck.seg('lT', v => { set = v; lc(); });
  (() => {
    const NF4 = [-1.0, -0.6962, -0.5251, -0.3949, -0.2844, -0.1848, -0.0911, 0.0, 0.0796, 0.1609, 0.2461, 0.3379, 0.4407, 0.5626, 0.7230, 1.0];
    const s = document.getElementById('qSvg'), X = v => 40 + (v + 1) / 2 * 580;
    let p = ''; for (let v = -1; v <= 1.001; v += 0.01) p += `${X(v)},${150 - 110 * Math.exp(-((v / 0.35) ** 2) / 2)} `;
    svg('polyline', { points: p, fill: 'none', style: 'stroke:var(--faint);stroke-width:2' }, s);
    svg('line', { x1: 40, x2: 620, y1: 150, y2: 150, class: 'ln' }, s);
    NF4.forEach(v => svg('line', { x1: X(v), x2: X(v), y1: 120, y2: 150, style: 'stroke:var(--a);stroke-width:2.5' }, s));
    for (let i = 0; i < 16; i++) { const v = -1 + 2 * i / 15; svg('line', { x1: X(v), x2: X(v), y1: 155, y2: 180, style: 'stroke:var(--b);stroke-width:2.5' }, s); }
    [-1, -0.5, 0, 0.5, 1].forEach(v => svg('text', { x: X(v), y: 196, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: v }, s));
    svg('text', { x: 40, y: 20, class: 'tm', text: 'weights ÷ block absmax (values in [−1, 1])' }, s);
  })();
''',
    line='LoRA trains a rank-r update BA beside a frozen W₀ and merges it afterwards; QLoRA keeps the frozen base in 4-bit NF4 so large models fine-tune on a single GPU.',
    explain='Full fine-tuning needs gradients and Adam state for every parameter and a full model copy per task. LoRA freezes the pretrained weights and learns a low-rank update, B times A, starting from B equal to zero so training begins at the pretrained model. Because adaptation updates have low intrinsic rank, a small r works, with 10,000 times fewer trainable parameters on GPT-3, and after training the update merges into the weight with no inference cost. QLoRA additionally stores the frozen base in 4-bit NormalFloat, quantizes the scales again, and pages optimizer state, which brings 65 billion parameter fine-tuning from over 780 gigabytes to under 48.',
    recap=[('Problem', 'full fine-tuning memory ≈ 14 bytes/param plus a full copy per task.'), ('LoRA', 'W₀ + (α/r)BA, B = 0 at init, merge after: tiny trainable set, no latency.'), ('QLoRA', 'NF4 frozen base + double quantization + paged optimizers; 65B on one 48 GB GPU.')],
)

# =============================================================== 04
DECKS['04-reward-models'] = dict(
    title='Reward Models', h1='Reward models',
    sub='How human comparisons become a scalar score: the Bradley-Terry model, the pairwise loss, rankings to pairs, and the limits of any learned reward.',
    prob='"Helpful, honest, harmless" can\'t be written as a formula. RL needs a number for every sampled answer, and people can\'t label millions of samples during training.',
    core='Collect <b>comparisons</b> between answers, then train a model r(x, y) → scalar so that σ(r_w − r_l) matches how often people prefer y_w over y_l. That model scores RL samples automatically.',
    build=['04_reward_model'],
    sources='Ouyang et al. 2022 (InstructGPT §3.5, eq. 1: K = 4–9 rankings, 6B RM from the SFT model); Touvron et al. 2023 (Llama 2 §3.2.1–3.2.2: helpfulness and safety RMs, 1,418,091 Meta comparisons); Bradley & Terry 1952; Christiano et al. 2017.',
    slides=[
        section('s-p1', 1, 'Comparisons are easier than scores', '''    <p class="lede">Ask five people to score an answer from 1 to 10 and you get five different calibrations. Ask which of two answers is better and they mostly agree. The Bradley-Terry model links reward <b>differences</b> to preference probabilities. Drag the gap.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0"><label class="ctl">r(A) − r(B) <input type="range" id="bD" min="-5" max="5" step="0.1" value="1.5"> <output id="bDo"></output></label></div>
      <svg id="bSvg" viewBox="0 0 660 220" style="margin-top:10px" role="img" aria-label="Bradley-Terry curve"></svg>
      <p class="readout" id="bOut"></p>
    </div>'''),
        section('s-lim', 2, 'Why not use a hand-written reward or direct scores?', '''    <div class="grid3">
      <div class="card d"><h3>No formula for "helpful"</h3><p>Unlike a game score, quality depends on the request, the audience and subtle correctness. Any hand-written rule is easy to game.</p></div>
      <div class="card b"><h3>Absolute ratings are noisy</h3><p>Labelers disagree on what "7/10" means, and drift over time. Relative judgements are more consistent.</p></div>
      <div class="card c"><h3>Humans can't be in the loop</h3><p>PPO samples millions of responses. A learned reward model answers instantly; humans label only a fixed dataset per round.</p></div>
    </div>'''),
        your_turn('s-turn', 'Read a reward model',
                  'A reward model scores answer A at 2.0 and answer B at 0.5. Under Bradley-Terry, what is the predicted probability that a person prefers A?',
                  ['0.50', '0.75', 'about 0.82', '0.99'], 2,
                  '<b>C.</b> σ(2.0 − 0.5) = σ(1.5) = 1/(1 + e^−1.5) ≈ 0.82. Only the difference matters: scores of 102.0 and 100.5 predict exactly the same preference.'),
        section('s-core', 4, 'Architecture and loss', '''    <div class="grid3">
      <div class="card a"><h3>Model</h3><p>InstructGPT: start from the SFT model "with the final unembedding layer removed" and output one scalar for a (prompt, response) pair. They used 6B reward models; 175B RM training "could be unstable".</p></div>
      <div class="card b"><h3>Loss</h3><p>loss = −E[log σ(r(x, y_w) − r(x, y_l))]: maximize the likelihood of the observed choices under Bradley-Terry. Only differences are learned, so rewards are often normalized before RL.</p></div>
      <div class="card e"><h3>Data</h3><p>For each prompt, sample several model outputs and have labelers rank them. InstructGPT: K = 4 to 9 per prompt; Llama 2: binary comparisons with a strength label, over 1M of them.</p></div>
    </div>
    <div class="eq">loss(θ) = −1/C(K,2) · E<sub>(x, y_w, y_l)</sub> [ log σ( r<sub>θ</sub>(x, y_w) − r<sub>θ</sub>(x, y_l) ) ]   (InstructGPT eq. 1)</div>'''),
        section('s-how', 5, 'From a ranking to training pairs', '''    <p class="lede">A labeler ranks K responses. Every ordered pair becomes a comparison: K·(K−1)/2 of them. InstructGPT puts all pairs from one prompt in the <b>same batch element</b>, because they are strongly correlated and treating them as independent samples made the RM overfit.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0"><label class="ctl">K responses ranked <input type="range" id="kK" min="2" max="9" step="1" value="4"> <output id="kKo"></output></label></div>
      <svg id="kSvg" viewBox="0 0 660 230" style="margin-top:10px" role="img" aria-label="Pairs from ranking"></svg>
      <p class="readout" id="kOut"></p>
    </div>'''),
        section('s-how2', 5, 'How good can a reward model get? <span class="ill">simulation</span>', '''    <p class="lede">From notebook 04: simulated labelers choose with Bradley-Terry noise around a hidden true reward. Even the true reward function only predicts 81% of their choices, which is the ceiling. A learned RM approaches it as comparisons grow.</p>
    <div class="visual"><div id="aBars"></div></div>
''' + deep('Real reward models', '<p>Real preference data is noisy too: labelers disagree with each other, so held-out RM accuracy well below 100% is expected. Llama 2 trained <b>two</b> reward models, one for helpfulness and one for safety, because the two goals can conflict and a single model had trouble serving both.</p>')),
        section('s-why', 6, 'Why it works, and where it breaks', '''    <div class="grid2">
      <div class="card a"><h3>It generalizes the labels</h3><p>The RM learns features of good answers from tens of thousands of comparisons, then scores answers no labeler has seen.</p></div>
      <div class="card e"><h3>Comparisons carry fine signal</h3><p>Ranking 4–9 samples gives up to 36 comparisons per prompt, focused on the subtle differences between plausible answers.</p></div>
      <div class="card d"><h3>It is only a proxy</h3><p>The RM is accurate where its training data was. Push a policy far from that data and the RM's mistakes get exploited (deck 06).</p></div>
      <div class="card b"><h3>It must keep up</h3><p>As the policy improves, its outputs leave the RM's training distribution. Llama 2 and 3 collect fresh comparisons on the newest model each round.</p></div>
    </div>'''),
        myths('s-myth', [
            ('A reward model outputs a probability or a 1–10 score.', 'It outputs an unbounded scalar, identified only up to a constant: only differences between answers to the same prompt mean anything.'),
            ('A good reward model should agree with labelers 100% of the time.', 'Labelers disagree among themselves, so even the "true" reward can\'t predict every label. Accuracy has a noise ceiling.'),
            ('Once trained, the reward model can be reused for the whole project.', 'It goes stale as the policy improves. Iterated recipes retrain it on comparisons of the current model\'s outputs.'),
        ]),
        check('s-check', [
            ('mcq', 'How many pairwise comparisons does one ranking of K = 9 responses give?', ['9', '18', '36', '81'], 2, '<b>C(9,2) = 36.</b>'),
            ('open', 'Write the reward-model loss and explain why only differences are learned.', '−log σ(r(x,y_w) − r(x,y_l)). Adding the same constant to every reward leaves every difference, and therefore the loss, unchanged.'),
            ('open', 'Why did InstructGPT put all pairs from a prompt into one batch element?', 'The C(K,2) pairs share responses, so they are highly correlated. Shuffling them as independent samples caused overfitting; grouping them is also cheaper (one forward pass per response).'),
        ]),
    ],
    js=r'''
  Deck.bind(['bD'], () => {
    const d = Deck.val('bD'), p = 1 / (1 + Math.exp(-d)); Deck.out('bDo', d.toFixed(1));
    const s = clear(document.getElementById('bSvg')), X = v => 60 + (v + 5) / 10 * 560, Y = v => 190 - v * 170;
    [0, 0.5, 1].forEach(v => { svg('line', { x1: 60, x2: 620, y1: Y(v), y2: Y(v), class: 'ln' }, s); svg('text', { x: 52, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm', text: v }, s); });
    let pts = ''; for (let v = -5; v <= 5.001; v += 0.05) pts += `${X(v)},${Y(1 / (1 + Math.exp(-v)))} `;
    svg('polyline', { points: pts, fill: 'none', style: 'stroke:var(--a);stroke-width:3' }, s);
    svg('circle', { cx: X(d), cy: Y(p), r: 7, style: 'fill:var(--b)' }, s);
    svg('text', { x: 340, y: 214, 'text-anchor': 'middle', class: 'tm', text: 'reward difference r(A) − r(B)' }, s);
    document.getElementById('bOut').innerHTML = `P(A preferred) = σ(${d.toFixed(1)}) = <b>${p.toFixed(2)}</b>. Loss if the labeler chose A: −log ${p.toFixed(2)} = ${(-Math.log(p)).toFixed(2)}; if they chose B: ${(-Math.log(1 - p)).toFixed(2)}.`;
  });
  Deck.bind(['kK'], () => {
    const K = Deck.val('kK'), s = clear(document.getElementById('kSvg')); Deck.out('kKo', K);
    const pos = i => [330 + 150 * Math.cos(-Math.PI / 2 + 2 * Math.PI * i / K), 110 + 90 * Math.sin(-Math.PI / 2 + 2 * Math.PI * i / K)];
    for (let i = 0; i < K; i++) for (let j = i + 1; j < K; j++) { const [x1, y1] = pos(i), [x2, y2] = pos(j); svg('line', { x1, y1, x2, y2, style: 'stroke:var(--a);stroke-width:1.5;opacity:.6' }, s); }
    for (let i = 0; i < K; i++) { const [x, y] = pos(i); svg('circle', { cx: x, cy: y, r: 16, style: `fill:hsl(${140 - 140 * i / Math.max(1, K - 1)},55%,45%)` }, s); svg('text', { x, y: y + 5, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:700', text: '#' + (i + 1) }, s); }
    document.getElementById('kOut').innerHTML = `Ranking of ${K} (#1 best): <b>${K * (K - 1) / 2}</b> comparisons, each line a (better, worse) pair. ${K >= 4 ? 'InstructGPT used K = 4–9, so 6 to 36 pairs per prompt.' : ''}`;
  });
  Deck.hbars(document.getElementById('aBars'), [[25, 0.703], [100, 0.758], [400, 0.796], [2000, 0.812]].map(([n, a]) => ({ label: n.toLocaleString() + ' comparisons', value: a - 0.5, color: 'var(--a)', text: (100 * a).toFixed(1) + '%' })).concat([{ label: 'true reward (ceiling)', value: 0.311, color: 'var(--faint)', text: '81.1%' }]), { max: 0.35 });
''',
    line='A reward model learns a scalar score from human comparisons via the Bradley-Terry loss −log σ(r_w − r_l), giving RL an automatic but imperfect judge.',
    explain='Helpfulness has no formula, and humans can\'t score the millions of samples RL needs. So labs collect comparisons, which are more consistent than absolute ratings, often as rankings of four to nine answers per prompt, and train a model that outputs one scalar per response. The Bradley-Terry model says the probability that one answer is preferred is the sigmoid of the reward difference, so the loss is minus log sigmoid of the winner\'s score minus the loser\'s. Only differences are learned. Accuracy is capped by labeler disagreement, the model is only reliable near its training data, and it needs fresh comparisons as the policy improves.',
    recap=[('Problem', 'no formula for "good answer"; humans can\'t score every RL sample.'), ('Core idea', 'train r(x, y) on comparisons: −log σ(r_w − r_l); only differences matter.'), ('Limits', 'label noise caps accuracy; it is a proxy that goes stale as the policy moves.')],
)

# =============================================================== 05
DECKS['05-rlhf-ppo'] = dict(
    title='RLHF with PPO', h1='RLHF with PPO',
    sub='Optimizing a language model against a reward model: the KL-penalized objective, PPO\'s clipped update, the four models in memory, and the "alignment tax".',
    prob='We have a reward model. We want the policy to produce higher-scoring answers, but naive policy gradients are unstable, and maximizing an imperfect reward model without limits produces garbage that scores well.',
    core='Maximize <b>r(x, y) − β·KL(π ‖ π_SFT)</b> with <b>PPO</b>: sample answers, score them, and take several small, clipped policy-gradient steps per batch so no update moves the policy too far.',
    build=['05_ppo_toy'],
    sources='Ouyang et al. 2022 (InstructGPT §3.5 eq. 2: per-token KL penalty, PPO-ptx, value function initialized from the RM); Schulman et al. 2017, "Proximal Policy Optimization Algorithms" (eq. 7, ε = 0.2); Stiennon et al. 2020; Touvron et al. 2023 (Llama 2 §3.2.3).',
    slides=[
        section('s-p1', 1, 'Four models at once', '''    <p class="lede">A PPO step for an LLM involves four networks. Two are trained, and two are frozen but must still run a forward pass on every sample. For a 7B policy that is a lot of memory before activations.</p>
    <div class="visual">
      <svg id="fSvg" viewBox="0 0 660 230" role="img" aria-label="Four models in PPO"></svg>
      <div ''' + INFOBOX + ''' id="fInfo">Click a model.</div>
    </div>'''),
        section('s-lim', 2, 'What goes wrong with plain policy gradients', '''    <div class="grid3">
      <div class="card d"><h3>High variance</h3><p>One scalar reward for a whole answer of hundreds of tokens gives a noisy gradient. A baseline (value function) is needed to tell "better than expected" from "worse".</p></div>
      <div class="card b"><h3>Steps that are too big</h3><p>A single large update can collapse the policy (repeating one phrase, say), and on-policy data from the old policy no longer describes the new one.</p></div>
      <div class="card c"><h3>Unlimited optimization</h3><p>The reward model is wrong somewhere. Without a constraint, the policy finds those spots: odd phrasing, excessive length, flattery.</p></div>
    </div>'''),
        your_turn('s-turn', 'What does the KL term do?',
                  'RLHF maximizes r(x,y) − β·log(π_RL(y|x)/π_SFT(y|x)). What happens as β grows large?',
                  ['The policy ignores the reward model', 'The policy stays close to the SFT model and gains less reward', 'Training becomes faster', 'The reward model is updated'], 1,
                  '<b>B.</b> The penalty term, averaged over samples, is β·KL(π‖π_SFT). A large β makes drifting from the SFT model expensive, trading reward for staying where the reward model is trustworthy. The exact optimum is π* ∝ π_SFT·exp(r/β).'),
        section('s-core', 4, 'The objective and the update', '''    <div class="grid2">
      <div class="card a"><h3>What is maximized</h3><p>InstructGPT eq. 2: E[ r<sub>θ</sub>(x,y) − β·log(π<sup>RL</sup>(y|x)/π<sup>SFT</sup>(y|x)) ] + γ·E<sub>pretrain</sub>[log π<sup>RL</sup>(x)]. The KL penalty is applied per token; the γ term (PPO-ptx) mixes in pretraining gradients.</p></div>
      <div class="card b"><h3>How it is maximized (PPO)</h3><p>L<sup>CLIP</sup> = E[ min(ρ·Â, clip(ρ, 1−ε, 1+ε)·Â) ], with ρ the new/old probability ratio and ε = 0.2 in the PPO paper. Several epochs of minibatch updates per batch of samples.</p></div>
    </div>
''' + deep('Advantages for text', '<p>The reward model scores the full answer once. The per-token KL penalty gives every token a small reward too. A <b>value model</b> (InstructGPT: initialized from the RM) predicts the expected future reward at each token, and the advantage Â is how much better the actual outcome was than predicted (usually with generalized advantage estimation). GRPO (deck 08) replaces this value model with the average reward of a group of samples.</p>')),
        section('s-how', 5, 'PPO\'s clip, visualized', '''    <p class="lede">The contribution of one sample to L<sup>CLIP</sup> as the policy changes its probability (ratio ρ = π_new/π_old). For a good sample (Â &gt; 0) the gain stops growing once ρ &gt; 1+ε; for a bad one (Â &lt; 0) the gain from pushing it down stops once ρ &lt; 1−ε. Flat regions have zero gradient.</p>
    <div class="visual">
      <div class="controls" style="margin-top:0"><label class="ctl">ε <input type="range" id="cE" min="0.05" max="0.5" step="0.05" value="0.2"> <output id="cEo"></output></label><div class="seg" id="cA"><button data-v="1" class="on">Â &gt; 0 (good sample)</button><button data-v="-1">Â &lt; 0 (bad sample)</button></div></div>
      <svg id="cSvg" viewBox="0 0 660 240" style="margin-top:10px" role="img" aria-label="Clipped objective"></svg>
    </div>'''),
        section('s-how2', 5, 'β is the leash <span class="ill">toy simulation</span>', '''    <p class="lede">Notebook 05 trains a one-step "policy" over 8 responses with PPO at several β. Expected reward and KL from the reference both fall as β rises, and PPO lands on the exact optimum π* ∝ π_ref·e<sup>r/β</sup> each time.</p>
    <div class="visual"><svg id="kSvg" viewBox="0 0 660 240" role="img" aria-label="Reward and KL vs beta"></svg>
      <div class="legend"><span><i style="background:var(--a)"></i>E[reward]</span><span><i style="background:var(--d)"></i>KL(π‖π_ref)</span></div></div>'''),
        section('s-why', 6, 'Why RLHF with PPO worked', '''    <div class="grid2">
      <div class="card a"><h3>Learns from its own samples</h3><p>Online RL scores what the current policy actually writes, so it fixes the model's own failure modes, not just copies demonstrations.</p></div>
      <div class="card e"><h3>Stable enough at scale</h3><p>Clipping plus the KL leash keep updates small. InstructGPT, Llama 2-Chat (PPO after rejection-sampling rounds) and many others used it.</p></div>
      <div class="card b"><h3>The alignment tax, and PPO-ptx</h3><p>InstructGPT saw regressions on some public NLP datasets after RLHF. Mixing pretraining gradients into PPO (PPO-ptx) greatly reduced them "without compromising labeler preference scores".</p></div>
      <div class="card d"><h3>The costs</h3><p>Four models, generation inside the training loop, many sensitive hyperparameters (β, ε, learning rates, GAE settings). Hence the search for simpler methods (decks 07–08).</p></div>
    </div>'''),
        myths('s-myth', [
            ('PPO simply maximizes the reward model\'s score.', 'It maximizes reward <b>minus β·KL</b> to the SFT model. Without that term the policy would exploit the reward model.'),
            ('The value model and the reward model are the same thing.', 'The RM scores complete answers. The value model predicts expected future reward at each token to compute advantages. InstructGPT initializes the value model from the RM, but trains it separately.'),
            ('Clipping limits the size of the gradient.', 'It removes the incentive to move a sample\'s probability ratio beyond 1 ± ε in the helpful direction. Gradients from samples in the flat region are zero; others are unchanged.'),
        ]),
        check('s-check', [
            ('mcq', 'Which four models does a typical PPO-based RLHF step use?', ['Policy, reference, reward model, value model', 'Policy, teacher, student, critic', 'Encoder, decoder, RM, tokenizer', 'Only the policy'], 0, '<b>Policy</b> (trained), <b>reference/SFT</b> (frozen, for KL), <b>reward model</b> (frozen), <b>value model</b> (trained).'),
            ('open', 'What is the closed-form optimum of E[r] − β·KL(π‖π_ref)?', 'π*(y) ∝ π_ref(y)·exp(r(y)/β). Higher reward answers are up-weighted exponentially, more strongly the smaller β is. DPO is built on this formula.'),
            ('open', 'What problem does PPO-ptx address?', 'The alignment tax: RLHF degraded some benchmark performance. Mixing pretraining log-likelihood gradients into the update (γ > 0) reduced the regressions while keeping preference scores.'),
        ]),
    ],
    js=r'''
  (() => {
    const M = [['policy π (trained)', 'var(--a)', 'The model being optimized. Samples answers, then gets PPO updates. Needs gradients and optimizer state.'], ['reference π_SFT (frozen)', 'var(--faint)', 'A frozen copy of the SFT model. Its log-probs give the KL penalty that keeps the policy close.'], ['reward model (frozen)', 'var(--b)', 'Scores each complete answer with one scalar. InstructGPT used a 6B RM.'], ['value model (trained)', 'var(--c)', 'Predicts expected reward per token to compute advantages. InstructGPT initialized it from the RM. Also needs gradients and optimizer state.']];
    const s = document.getElementById('fSvg');
    M.forEach(([t, c, info], i) => {
      const x = 20 + (i % 2) * 320, y = 20 + Math.floor(i / 2) * 105, g = svg('g', { style: 'cursor:pointer' }, s);
      svg('rect', { x, y, width: 300, height: 85, rx: 12, style: `fill:${c}` }, g);
      svg('text', { x: x + 150, y: y + 50, 'text-anchor': 'middle', class: 't', style: 'fill:#fff;font-weight:700;font-size:15px', text: t }, g);
      g.addEventListener('click', () => { document.getElementById('fInfo').innerHTML = `<b>${t}</b>: ${info}`; });
    });
  })();
  let sign = 1;
  const clipDraw = () => {
    const e = Deck.val('cE'); Deck.out('cEo', e.toFixed(2));
    const s = clear(document.getElementById('cSvg')), X = r => 60 + r / 2 * 560, Y = v => 122 - v * 48;
    svg('line', { x1: 60, x2: 620, y1: Y(0), y2: Y(0), class: 'ln' }, s); svg('line', { x1: X(1), x2: X(1), y1: 20, y2: 220, class: 'ln' }, s);
    svg('rect', { x: X(1 - e), y: 22, width: X(1 + e) - X(1 - e), height: 200, style: 'fill:var(--a-soft)' }, s);
    let un = '', cl = '';
    for (let r = 0.01; r <= 2; r += 0.01) { un += `${X(r)},${Y(r * sign)} `; cl += `${X(r)},${Y(Math.min(r * sign, Math.min(Math.max(r, 1 - e), 1 + e) * sign))} `; }
    svg('polyline', { points: un, fill: 'none', style: 'stroke:var(--faint);stroke-width:2;stroke-dasharray:5 4' }, s);
    svg('polyline', { points: cl, fill: 'none', style: 'stroke:var(--a);stroke-width:3.5' }, s);
    [0, 0.5, 1, 1.5, 2].forEach(r => svg('text', { x: X(r), y: 236, 'text-anchor': 'middle', class: 'tm', style: 'font-size:11px', text: 'ρ=' + r }, s));
    svg('text', { x: 60, y: 14, class: 'tm', style: 'font-size:11px', text: 'dashed: unclipped ρ·Â   ·   solid: L_CLIP   ·   shaded: 1 ± ε' }, s);
  };
  Deck.bind(['cE'], clipDraw); Deck.seg('cA', v => { sign = +v; clipDraw(); });
  (() => {
    const B = [0.1, 0.25, 0.5, 1, 2, 5], R = [1.995, 1.891, 1.016, 0.465, 0.320, 0.248], K = [3.879, 3.398, 0.989, 0.135, 0.023, 0.005];
    const s = document.getElementById('kSvg'), X = i => 70 + i * 106, Y = v => 200 - v / 4 * 170;
    [0, 1, 2, 3, 4].forEach(v => { svg('line', { x1: 60, x2: 610, y1: Y(v), y2: Y(v), class: 'ln' }, s); svg('text', { x: 52, y: Y(v) + 4, 'text-anchor': 'end', class: 'tm', text: v }, s); });
    B.forEach((b, i) => svg('text', { x: X(i), y: 222, 'text-anchor': 'middle', class: 'tm', text: 'β=' + b }, s));
    [[R, 'var(--a)'], [K, 'var(--d)']].forEach(([v, c]) => { svg('polyline', { points: v.map((y, i) => `${X(i)},${Y(y)}`).join(' '), fill: 'none', style: `stroke:${c};stroke-width:3` }, s); v.forEach((y, i) => svg('circle', { cx: X(i), cy: Y(y), r: 5, style: `fill:${c}` }, s)); });
  })();
''',
    line='RLHF maximizes reward-model score minus β·KL to the SFT model, using PPO\'s clipped updates to stay stable, at the cost of four models and much tuning.',
    explain='Given a reward model, RLHF samples answers from the current policy, scores them, and updates the policy to raise the score while paying a per-token KL penalty for drifting from the SFT model, because the reward model is only trustworthy near its training data. PPO makes the update stable by clipping the probability ratio between new and old policy, so several gradient steps per batch can\'t move any answer\'s probability too far. A value model supplies per-token advantages. The exact optimum of reward minus beta KL is the reference policy times exp of reward over beta. InstructGPT also mixed in pretraining gradients to reduce the alignment tax.',
    recap=[('Problem', 'optimize against an imperfect RM without instability or exploitation.'), ('Core idea', 'max r − β·KL(π‖π_SFT) with PPO\'s clipped ratio (ε = 0.2).'), ('Costs', 'policy, reference, RM and value model in memory; many hyperparameters.')],
)
