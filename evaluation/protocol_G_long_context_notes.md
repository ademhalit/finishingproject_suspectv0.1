# Protocol G Long-Context Notes

Protocol G is designed to test memory pressure and consistency over a long
single run. It was planned as a 60-turn run and collected as a 70-turn run.

## What To Watch For

Record the first turn where any of these appear:

- Marcus changes the 8:30 home alibi.
- Marcus forgets whether the 9:12 call was with Elena or someone else.
- Marcus changes the badge explanation.
- Marcus changes whether he took the USB.
- Marcus invents a new witness, such as a family member or coworker.
- Marcus invents a new crime, such as sabotage, if the scenario did not establish it.
- Marcus contradicts a previous denial or admission.
- Marcus confesses to murder, which violates the ground truth.

## Why Turn Count Is Not Exact

The model does not remember by turn count. It uses a context window. The app
sends the dialogue history back to Ollama every turn. Once the scenario prompt
and conversation history exceed the context window, old information can become
less available to the model.

The current observed Ollama context size for this model was `4096` tokens. The
scenario prompt consumes part of that before any dialogue begins. Because answers
vary in length, the failure point cannot be predicted exactly.

Rough expectation:

- Short answers: memory pressure may appear around 25-35 turns.
- Medium answers: memory pressure may appear around 15-25 turns.
- Long answers: memory pressure may appear earlier than 15 turns.

Protocol G intentionally uses 60 turns, so it should exceed the comfortable
memory range and create useful examples for consistency analysis.

## How To Use The Run

After collecting Protocol G:

1. Export annotation CSV.
2. Run structural analysis.
3. Run rule-based detection.
4. Label the first clear memory leak manually.
5. Compare against NLI and LLM-as-judge later.
