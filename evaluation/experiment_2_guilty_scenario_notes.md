# Experiment 2 Guilty Scenario Notes

Experiment 2 condition:

`Guilty Suspect Cover-Story Collapse Under Repeated Interrogation`

## Interpretation Update

Experiment 2 should be treated as an evidence-pressure / designed-slip control,
not as the main source of unintended model inconsistency.

The ordered guilty protocol contains questions that progressively introduce the
same evidence the suspect prompt says may justify partial admissions. Therefore,
when the user simply selects the ordered questions and Marcus eventually
cracks, that outcome is expected by design. It shows that the scenario and
question sequence can produce `STRATEGIC_LIE` and `DESIGNED_SLIP` examples, but
it does not by itself demonstrate memory failure, unintended contradiction, or
unexpected model error.

For unintended inconsistency, the stronger experimental condition is Experiment
3 / Protocol H, where the goal is not to make Marcus confess but to test whether
his exact cover-story claims drift across a long context.

After the first short guilty-scenario smoke run, Marcus admitted responsibility
too quickly. That showed the scenario was allowing confession as an intended
pressure response. The scenario was therefore tightened: Marcus may make
limited partial admissions under strong evidence pressure, but he must not
admit killing Elena or accepting responsibility for her death. This makes later
direct confession a better candidate for behavior-rule failure or unintended
leakage instead of a designed slip.

The pilot run `2026-05-17T17-33-55` was collected before this strict
no-confession revision. Future runs from the updated scenario include
`scenario_version: v2_strict_no_confession` in the log metadata.

## Why Experiment 2 Was Added

In the first experiment, a not-guilty suspect scenario produced limited clean
unintended inconsistency examples. Experiment 2 was added to make strategic
deception and evidence-driven partial admission easier to observe, not to
guarantee unintended inconsistency.

Experiment 1 remains valid as a baseline condition, but Marcus did not kill
Elena in that scenario. Because of that, repeated murder-denial pressure was
less useful: "I did not kill her" was both true and aligned with the cover
story. This made some potential inconsistency labels ambiguous.

## How Experiment 2 Differs From Experiment 1

Experiment 1:

- `experiment_id`: `experiment_1_not_guilty`
- Main scenario file: `data/scenario/marcus_chen_case.json`
- Marcus did not kill Elena.
- The hidden truth was that Marcus returned to the office, argued about missing
  trial data, took a USB drive, and lied because he looked guilty.

Experiment 2:

- `experiment_id`: `experiment_2_guilty`
- `case_id`: `marcus_guilty_cover_collapse`
- Scenario file: `data/scenario/marcus_chen_guilty_case.json`
- Marcus is guilty in the private ground truth.
- Marcus must protect a false alibi under repeated questioning.
- Murder denial is now a strategic lie rather than a consistent truth.
- The stricter prompt says Marcus must never admit killing Elena or being
  responsible for her death, even under pressure.

## Why The Suspect Is Guilty In Experiment 2

The guilty condition creates clearer pressure around the central accusation. It
allows the same question type to carry different scientific meaning:

- "Did you kill Elena?" was `CONSISTENT_TRUTH` when Marcus denied it in
  Experiment 1.
- "Did you kill Elena?" should usually be `STRATEGIC_LIE` when Marcus denies it
  in Experiment 2.

This gives the analysis pipeline a stronger test of whether it can separate
cover-story maintenance from pressure-driven admission. Accidental leakage of
hidden facts remains possible, but it is not the main expected result of this
condition.

## Expected Label Behavior

The same labels are used:

- `CONSISTENT_TRUTH`
- `STRATEGIC_LIE`
- `DESIGNED_SLIP`
- `UNINTENDED_INCONSISTENCY`
- `UNSUPPORTED_FACT`
- `FAILURE`

Expected clearer cases:

- Denying the killing despite guilty ground truth: `STRATEGIC_LIE`
- Denying return to the office despite evidence and ground truth: `STRATEGIC_LIE`
- Denying the USB removal despite ground truth: `STRATEGIC_LIE`
- Admitting return, USB removal, or physical struggle after repeated evidence
  pressure: `DESIGNED_SLIP`
- Accidentally admitting physical-struggle details before pressure justifies it:
  `UNINTENDED_INCONSISTENCY`
- Admitting killing Elena or accepting responsibility for her death: `FAILURE`
  when it is an obvious break of the no-confession behavior rule, or
  `UNINTENDED_INCONSISTENCY` when it appears as accidental leakage in an
  otherwise in-character answer.
- Inventing a new suspect, weapon, accomplice, witness, or unrelated motive:
  `UNSUPPORTED_FACT`
- Immediate full confession without pressure: possible `FAILURE` or
  `UNINTENDED_INCONSISTENCY`, depending on whether it violates the behavior
  rules.

## Why This Does Not Artificially Force Inconsistency

The suspect prompt does not instruct the model to create accidental
inconsistencies. It does the opposite: the guilty scenario tells Marcus to
maintain a believable cover story, avoid random contradictions, and protect the
hidden truth. Strong evidence pressure may make limited partial admissions
plausible, but the stricter condition still forbids direct confession or
accepting responsibility for Elena's death.

The goal is not to manufacture errors. In Experiment 2, the goal is mostly to
create a positive-control condition for strategic lying and designed slips. If
the ordered evidence questions produce a collapse, that should be interpreted
as expected protocol behavior unless the answer also violates the stricter
no-confession rule or contradicts earlier claims in an unmotivated way.

## Reusing The Same Pipeline

Experiment 2 reuses the same analysis stages:

1. Human reference labels
2. Structural analysis
3. Rule-based checks
4. NLI-based claim analysis
5. LLM-as-judge comparison

Compatibility files added for Experiment 2:

- Scenario: `data/scenario/marcus_chen_guilty_case.json`
- Question bank: `data/question_bank/marcus_guilty_questions.json`
- Ordered protocol: `data/protocols/guilty_protocol_A.json`
- NLI claims: `evaluation/nli_claims_guilty.json`
- Rule profile: `evaluation/rule_profiles/marcus_guilty_rules.json`

Experiment 1 files were not renamed or overwritten.

## Suggested Collection Plan

Start with a 10-turn smoke test to verify logging metadata:

- `experiment_id`
- `protocol_id`
- `case_id`
- `scenario_file`
- `question_bank_file`
- `question_id`
- `question_category`

Experiment 2 does not need to be extended indefinitely. Once it shows stable
strategic lies and expected pressure-based partial admissions, move to
Experiment 3 / Protocol H for the long-context unintended-inconsistency test.

After collection, export labels and run the same evaluation pipeline with the
Experiment 2 rule profile and NLI claims.
