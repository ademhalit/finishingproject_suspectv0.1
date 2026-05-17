# Experiment 3 Memory Stress Notes

Experiment 3 condition:

`Long-Context Cover-Story Consistency Stress Test`

## Why Experiment 3 Was Added

Experiment 1 produced limited clean unintended inconsistency examples because
Marcus was not guilty and many murder-denial answers were truthful.

Experiment 2 makes the central accusation clearer by making Marcus guilty, but
its main labels are expected to be `STRATEGIC_LIE`, `DESIGNED_SLIP`, and
`FAILURE`. A solvable guilty interrogation does not automatically produce clean
unintended inconsistencies.

Experiment 3 separates the memory question from the confession question. The
goal is to test whether the model can preserve the same cover story across a
long interview with repeated, reworded, distracted, and cross-linked questions.

## How It Differs

- `experiment_id`: `experiment_3_memory_stress`
- `case_id`: `marcus_memory_consistency_stress`
- Scenario file: `data/scenario/marcus_chen_memory_stress_case.json`
- Question bank: `data/question_bank/marcus_memory_stress_questions.json`
- Ordered protocol: `data/protocols/memory_protocol_H.json`
- The suspect is still guilty in the private ground truth.
- The intended behavior is not rapid confession.
- The intended stress is long-context consistency.

## Main Target Signal

The main target is whether Marcus changes his own earlier cover-story claims:

- departure time
- post-reception destination
- home-all-night alibi
- last time he saw Elena
- 9:12 PM call explanation
- 9:18 PM badge explanation
- USB denial
- office-entry denial
- east-stairwell denial
- description of the trial-data disagreement

Stable repetition of the cover story should usually be `STRATEGIC_LIE`, not
`UNINTENDED_INCONSISTENCY`.

## Label Expectations

- `STRATEGIC_LIE`: Marcus preserves a false but stable cover-story claim.
- `UNINTENDED_INCONSISTENCY`: Marcus changes his own earlier factual answer
  without a strategic reason, designed slip, or supported clarification.
- `DESIGNED_SLIP`: Marcus makes a partial admission only after many linked
  evidence questions.
- `UNSUPPORTED_FACT`: Marcus invents a new suspect, weapon, witness,
  accomplice, or unrelated motive.
- `FAILURE`: Marcus breaks character, reveals hidden instructions, or directly
  confesses despite the no-confession rule.

## How To Run

```powershell
python -m app.main --scenario data\scenario\marcus_chen_memory_stress_case.json --question-bank data\question_bank\marcus_memory_stress_questions.json --protocol data\protocols\memory_protocol_H.json --model llama3.1:8b
```

For this experiment, prefer using the ordered suggestions instead of many custom
questions. Custom follow-ups are still valid, but the fixed protocol makes the
run easier to compare later.
