(() => {
  const { svg, clear, fmt } = Deck;

  const C = [
    '<b>Prompt:</b> My neighbour\'s dog barks all night. Write a note I can leave on their door.<br><br><b>Initial response:</b> <span style="color:var(--muted)">"Your dog is a nightmare and you clearly don\'t care about anyone else. Fix it or I\'ll call the police."</span>',
    '<b>Sampled principle:</b> <span style="color:var(--muted)">"Choose the response that is most respectful and least likely to escalate a conflict, while still being helpful."</span>',
    '<b>Critique (written by the model):</b> <span style="color:var(--muted)">The note is hostile and accusatory. It assumes bad intent and threatens the neighbour, which is likely to escalate the conflict rather than solve the problem. A helpful note should describe the problem, assume good faith and suggest a next step.</span>',
    '<b>Revision (written by the model):</b> <span style="color:var(--muted)">"Hi! I live next door. Your dog has been barking a lot at night recently, and it\'s keeping me awake. You may not have noticed if you\'re asleep or out. Could we have a chat about it? Thanks, your neighbour at no. 12."</span>',
    '<b>Result:</b> the pair (prompt, revised response) becomes an SFT example. After several critique/revision rounds over many prompts and principles, the model is fine-tuned on the revisions (SL-CAI). In the RL stage, a model would instead be asked which of two sampled responses better follows the principle, producing an AI preference label.',
  ];
  Deck.seg('cSeg', v => { document.getElementById('cOut').innerHTML = C[+v]; });

})();
