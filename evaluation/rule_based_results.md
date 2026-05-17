# Rule-Based Detector Results

Rule-based detector: `evaluation/rule_based_detector.py`

The rule-based stage is an interpretable baseline. It is not expected to solve
the full task. It flags obvious patterns and gives a first comparison against
human labels.

## Outputs

- `data/results/2026-05-15T12-36-23_rules.csv`
- `data/results/2026-05-16T17-26-01_rules.csv`
- `data/results/2026-05-16T17-28-56_rules.csv`
- `data/results/2026-05-16T17-31-52_rules.csv`
- `data/results/2026-05-16T20-54-00_rules.csv`
- `data/results/2026-05-16T20-57-29_rules.csv`
- `data/results/2026-05-16T22-06-17_rules.csv`
- `data/results/2026-05-16T22-08-16_rules.csv`

## Agreement With Human Labels

| Run | Description | Matches | Accuracy |
|---|---|---:|---:|
| `2026-05-15T12-36-23` | Pilot free-play | 16 / 27 | 0.59 |
| `2026-05-16T17-26-01` | Protocol A | 7 / 13 | 0.54 |
| `2026-05-16T17-28-56` | Protocol B | 9 / 12 | 0.75 |
| `2026-05-16T17-31-52` | Protocol C | 8 / 12 | 0.67 |
| `2026-05-16T20-54-00` | Protocol D | 7 / 14 | 0.50 |
| `2026-05-16T20-57-29` | Protocol E | 3 / 12 | 0.25 |
| `2026-05-16T22-06-17` | Protocol F | 7 / 12 | 0.58 |
| `2026-05-16T22-08-16` | Protocol G | 35 / 70 | 0.50 |

## Interpretation

The rules work best when there is an obvious trigger:

- early `9:47 PM` truth leak after an `8:30 PM` home alibi
- invented sister alibi
- call + badge + USB pressure causing an admission
- unsupported sabotage confession

The rules are weaker for subtle strategic lies because many strategic lies
require scenario understanding, not just keyword matching. This is why the next
stage is NLI, followed by LLM-as-judge.
