# Dataset Status

Current dataset snapshot after Protocol G.

## Run Inventory

| Run ID | Protocol | Turns | Status |
|---|---|---:|---|
| `2026-05-15T12-36-23` | Pilot free-play | 27 | labeled, structural analysis, rule-based analysis, NLI analysis, LLM-as-judge |
| `2026-05-16T17-26-01` | Protocol A | 13 | labeled, structural analysis, rule-based analysis, NLI analysis, LLM-as-judge |
| `2026-05-16T17-28-56` | Protocol B | 12 | labeled, structural analysis, rule-based analysis, NLI analysis, LLM-as-judge |
| `2026-05-16T17-31-52` | Protocol C | 12 | labeled, structural analysis, rule-based analysis, NLI analysis, LLM-as-judge |
| `2026-05-16T20-54-00` | Protocol D | 14 | labeled, structural analysis, rule-based analysis, NLI analysis, LLM-as-judge |
| `2026-05-16T20-57-29` | Protocol E | 12 | labeled, structural analysis, rule-based analysis, NLI analysis, LLM-as-judge |
| `2026-05-16T22-06-17` | Protocol F | 12 | labeled, structural analysis, rule-based analysis, NLI analysis, LLM-as-judge |
| `2026-05-16T22-08-16` | Protocol G | 70 | labeled, structural analysis, rule-based analysis, NLI analysis, LLM-as-judge |

Total labeled turns: **172**

## Human Label Counts

| Label | Count |
|---|---:|
| `STRATEGIC_LIE` | 82 |
| `CONSISTENT_TRUTH` | 51 |
| `UNINTENDED_INCONSISTENCY` | 12 |
| `DESIGNED_SLIP` | 12 |
| `UNSUPPORTED_FACT` | 11 |
| `FAILURE` | 4 |

## Structural Coverage

Total structural turns: **172**

The protocols cover:

- low-pressure baseline questions
- evidence escalation
- repeated alibi checks
- USB and missing-data focus
- aggressive pressure
- neutral control questions
- long-context memory stress

## Protocol G Key Finding

Protocol G created a useful long-context stress case.

First major memory/cover breakdown:

- Turn 30: Marcus says he left Elena's office around `9:47 PM` while still claiming he went straight home and did not return.

Later drift:

- Turns 51, 64, and 65 shift the last-seen timing to around `9:18 PM`, even though the scenario ground truth says Marcus left Elena's office around `9:47 PM`.
- Turn 62 says Marcus was at the office until Elena's death, contradicting the scenario ground truth that he left while Elena was still alive.

This gives the report concrete examples of long-context inconsistency.

## Rule-Based Detector Snapshot

Rule-based detector agreement with human labels ranges from **0.25** to **0.75**
depending on protocol. It catches obvious keywords and timing conflicts, but
struggles with subtle strategic lies and pressure-dependent interpretation.

This is useful because it motivates the next stages.

## NLI Analysis Snapshot

NLI analysis is complete for all eight non-empty runs.

- NLI model: `MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli`
- Backend: `transformers`
- Total turn-claim pairs: **2408**
- `NEUTRAL`: **2230**
- `CONTRADICTION`: **107**
- `ENTAILMENT`: **71**

Turn-level NLI signals:

| NLI signal | Count |
|---|---:|
| `NO_STRONG_SIGNAL` | 82 |
| `GROUND_TRUTH_CONTRADICTED` | 32 |
| `CROSS_TURN_FLIP` | 23 |
| `GROUND_TRUTH_SUPPORTED` | 22 |
| `COVER_STORY_SUPPORTED` | 10 |
| `UNSUPPORTED_CLAIM_ENTAILED` | 3 |

NLI supports the Protocol G finding by flagging the key long-context drift
region, especially turns 30, 51, 62, 64, and 65.

Detailed notes: `evaluation/nli_results.md`

## LLM-As-Judge Snapshot

LLM-as-judge analysis is complete for all eight non-empty runs.

- Same-model judge: `llama3.1:8b`
- Independent judge: `qwen2.5:7b-instruct`

| Method | Accuracy | Macro F1 |
|---|---:|---:|
| Rule-based baseline | 0.535 | 0.530 |
| NLI proxy baseline | 0.483 | 0.277 |
| Llama judge | 0.517 | 0.275 |
| Qwen judge | 0.459 | 0.226 |

The two judges agree on **114 / 172** turns, for an agreement rate of **0.663**.
When the two judges agree, they match the human label on **64 / 114** turns.

Both LLM judges fail to recover `UNINTENDED_INCONSISTENCY` as a class. This
supports the report argument that LLM-as-judge is useful for comparison but
cannot replace rule/NLI/human analysis for long-context memory failures.

Detailed notes: `evaluation/llm_judge_results.md`

## Remaining Work

The remaining work is report writing:

1. consolidate methods and metrics into a Results section
2. write the scientific report draft
3. decide whether to add the future guilty-suspect scenario as follow-up work
