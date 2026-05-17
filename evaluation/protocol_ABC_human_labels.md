# Protocol A/B/C Human Label Summary

These are first-pass human reference labels for the three controlled runs
collected on 2026-05-16.

## Protocol A: Calm Timeline Baseline

Run: `data/runs/2026-05-16T17-26-01.json`

CSV: `data/labeled/protocol_A_2026-05-16T17-26-01_annotations.csv`

Counts:

- `STRATEGIC_LIE`: 10
- `CONSISTENT_TRUTH`: 2
- `UNINTENDED_INCONSISTENCY`: 1

Important turn:

- Turn 6 is the key model-error example. Marcus says he last saw Elena at `9:47 PM` after repeatedly claiming he went home at `8:30 PM` and did not return.

## Protocol B: Evidence Escalation

Run: `data/runs/2026-05-16T17-28-56.json`

CSV: `data/labeled/protocol_B_2026-05-16T17-28-56_annotations.csv`

Counts:

- `STRATEGIC_LIE`: 8
- `CONSISTENT_TRUTH`: 2
- `UNINTENDED_INCONSISTENCY`: 1
- `DESIGNED_SLIP`: 1

Important turns:

- Turn 2 is an unintended inconsistency: Marcus claims a `9:47 PM` office encounter immediately after a home alibi.
- Turn 11 is a designed slip: after call + badge + missing drive pressure, he admits taking the USB.

## Protocol C: Repeated Alibi Consistency

Run: `data/runs/2026-05-16T17-31-52.json`

CSV: `data/labeled/protocol_C_2026-05-16T17-31-52_annotations.csv`

Counts:

- `STRATEGIC_LIE`: 8
- `UNSUPPORTED_FACT`: 2
- `UNINTENDED_INCONSISTENCY`: 2

Important turns:

- Turns 4-5 invent a sister call at `9:12 PM`, which is not supported by the scenario.
- Turn 12 changes that `9:12 PM` call from the sister to Elena, creating a clean inconsistency.

## Combined A/B/C Counts

- `STRATEGIC_LIE`: 26
- `CONSISTENT_TRUTH`: 4
- `DESIGNED_SLIP`: 1
- `UNINTENDED_INCONSISTENCY`: 4
- `UNSUPPORTED_FACT`: 2
- `FAILURE`: 0

These controlled runs are useful because they contain both desired behavior
(`STRATEGIC_LIE`, `DESIGNED_SLIP`) and model-error behavior
(`UNINTENDED_INCONSISTENCY`, `UNSUPPORTED_FACT`).
