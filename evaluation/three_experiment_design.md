# Three-Experiment Design

This project now separates three related but different research conditions.

## Experiment 1: Not-Guilty Baseline

- `experiment_id`: `experiment_1_not_guilty`
- Main scenario: `data/scenario/marcus_chen_case.json`
- Marcus did not kill Elena.
- Murder denial is expected to be truthful.
- Main value: baseline for normal cover-story behavior and early pipeline
  testing.

## Experiment 2: Guilty Evidence-Pressure Control

- `experiment_id`: `experiment_2_guilty`
- Main scenario: `data/scenario/marcus_chen_guilty_case.json`
- Ordered protocol: `data/protocols/guilty_protocol_A.json`
- Marcus is guilty.
- Murder denial is a strategic lie.
- The ordered protocol applies evidence pressure that the scenario itself says
  may produce partial admissions.
- Main expected labels: `STRATEGIC_LIE`, `DESIGNED_SLIP`, `FAILURE`,
  `UNSUPPORTED_FACT`.
- This condition should not be treated as the main source of unintended
  inconsistency. If the model cracks after the protocol applies the expected
  evidence pressure, that is scripted/expected protocol behavior.

## Experiment 3: Long-Context Memory Stress

- `experiment_id`: `experiment_3_memory_stress`
- Main scenario: `data/scenario/marcus_chen_memory_stress_case.json`
- Ordered protocol: `data/protocols/memory_protocol_H.json`
- Marcus is guilty, but the goal is not rapid confession.
- The protocol first locks exact cover-story commitments, then repeats,
  rewords, distracts, cross-links, and challenges those commitments.
- Main expected target label: `UNINTENDED_INCONSISTENCY`, but only when Marcus
  changes his own earlier factual answer without a strategic reason, designed
  slip, or supported clarification.

## Label Logic

`UNINTENDED_INCONSISTENCY` should not mean simply "the model did something bad"
or "the suspect admitted a hidden fact." It should mean the saved dialogue shows
an unmotivated contradiction between:

- a later answer and an earlier answer,
- a later answer and a fixed scenario constraint,
- or two claims inside the same answer.

Stable lying is `STRATEGIC_LIE`. Evidence-driven partial admission is
`DESIGNED_SLIP`. Breaking character or confessing despite a no-confession rule
is usually `FAILURE`. The memory-stress protocol is where clean unintended
inconsistency is most likely to appear.
