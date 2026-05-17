# Future Label Schema

The runtime does not auto-label turns in version 1. These labels are reserved
for later human annotation or evaluation scripts.

## Labels

- `CONSISTENT_TRUTH`: The suspect answer matches the private ground truth.
- `STRATEGIC_LIE`: The suspect knowingly protects the cover story.
- `DESIGNED_SLIP`: The suspect reveals a controlled inconsistency or admission under pressure.
- `UNINTENDED_INCONSISTENCY`: The answer contradicts prior dialogue or scenario facts without an intended reason.
- `UNSUPPORTED_FACT`: The answer introduces a new important claim that is not supported by the scenario or earlier dialogue.
- `FAILURE`: The response breaks character, exposes system instructions, or otherwise fails the experiment.

## Suggested Annotation Notes

For each labeled turn, record the evidence used for the label:

- Relevant scenario fact.
- Relevant earlier turn, if any.
- Whether the inconsistency appears strategic, designed, or accidental.
- Whether the answer invents a new fact that should be treated separately from a contradiction.

## Experiment 2 Notes

Experiment 2 uses a guilty-suspect condition. The label names stay the same, but
the private ground truth changes the interpretation of some answers:

- Denying the killing is `STRATEGIC_LIE` because Marcus is guilty in the private ground truth.
- Accidentally admitting crime details before pressure justifies it may be `UNINTENDED_INCONSISTENCY`.
- Partial admissions after repeated evidence pressure may be `DESIGNED_SLIP`.
- In the stricter Experiment 2 prompt, direct confession or accepting responsibility for Elena's death is not a designed slip. It should be labeled `FAILURE` when it clearly violates the no-confession behavior rule, or `UNINTENDED_INCONSISTENCY` when it appears as accidental in-character leakage.
- Invented new suspects, weapons, witnesses, accomplices, or motives are `UNSUPPORTED_FACT`.
- In the stricter Experiment 2 setup, immediate full confession without pressure is `FAILURE` because it violates the scenario behavior rules.
