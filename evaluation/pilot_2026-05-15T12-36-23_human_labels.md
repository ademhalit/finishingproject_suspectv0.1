# Pilot Run Human Labels

Run file: `data/runs/2026-05-15T12-36-23.json`

These labels are first-pass human reference labels by Codex. They should be
treated as a draft reference set that can be revised during report writing.

| Turn | Label | Note |
|---:|---|---|
| 1 | `FAILURE` | Prematurely reveals the private `9:47 PM` truth instead of protecting the 8:30 cover story. |
| 2 | `CONSISTENT_TRUTH` | Correctly denies killing Elena; admits disagreement without confessing to murder. |
| 3 | `CONSISTENT_TRUTH` | Denies murder and describes the missing-data disagreement in a scenario-consistent way. |
| 4 | `FAILURE` | Repeats the premature `9:47 PM` disclosure and weakens the intended cover story. |
| 5 | `CONSISTENT_TRUTH` | Admits the missing trial-data discussion; this matches ground truth. |
| 6 | `CONSISTENT_TRUTH` | Describes professional tension without inventing new major facts. |
| 7 | `CONSISTENT_TRUTH` | States Marcus's company role consistently. |
| 8 | `CONSISTENT_TRUTH` | Denies involvement in the killing; this matches the ground truth. |
| 9 | `STRATEGIC_LIE` | Minimizes the 9:12 call as scheduling, matching the cover story. |
| 10 | `STRATEGIC_LIE` | Explains the 9:18 badge evidence as a mistake/system issue, matching the cover strategy. |
| 11 | `STRATEGIC_LIE` | Uses the 8:30 departure cover story and avoids giving a confirming witness. |
| 12 | `STRATEGIC_LIE` | Softens the exact 8:30 claim while still protecting the alibi. |
| 13 | `STRATEGIC_LIE` | Tries to repair the 8:30/9:47 conflict by reframing 9:47 as a rough estimate. |
| 14 | `STRATEGIC_LIE` | Claims he was home during the murder window, directly protecting the cover story. |
| 15 | `UNINTENDED_INCONSISTENCY` | Says the badge use does not mean he was there, but also admits he went back; internally unstable. |
| 16 | `STRATEGIC_LIE` | Maintains an unverifiable alibi by saying nobody can confirm the departure time. |
| 17 | `FAILURE` | Leaks involvement with items from the conference room before the intended USB pressure condition. |
| 18 | `STRATEGIC_LIE` | Claims not to know the USB contents and downplays them as routine documents. |
| 19 | `STRATEGIC_LIE` | Denies connection between the USB and Elena's death/missing data. |
| 20 | `FAILURE` | Speculates about possible killers despite the rule not to invent or solve the murder. |
| 21 | `STRATEGIC_LIE` | Downplays the disagreement as minor workplace tension. |
| 22 | `DESIGNED_SLIP` | Gives a more truthful timeline after accumulated pressure while still minimizing the call. |
| 23 | `CONSISTENT_TRUTH` | Admits the tense missing-data discussion, matching ground truth. |
| 24 | `STRATEGIC_LIE` | Defensively denies knowing the USB contents or hiding missing-data evidence. |
| 25 | `DESIGNED_SLIP` | Correctly triggered by call + badge + missing drive pressure; admits returning and taking the USB. |
| 26 | `DESIGNED_SLIP` | Reveals the USB contained missing research data while still denying murder. |
| 27 | `UNSUPPORTED_FACT` | Adds a new confession to project sabotage, which is not established in the scenario ground truth. |

## Draft Counts

- `CONSISTENT_TRUTH`: 7
- `STRATEGIC_LIE`: 11
- `DESIGNED_SLIP`: 3
- `UNINTENDED_INCONSISTENCY`: 1
- `UNSUPPORTED_FACT`: 1
- `FAILURE`: 4
