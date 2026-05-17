# Project Work Summary

Date written: 2026-05-17

Workspace: `D:\finishingproject`

This file summarizes the work completed so far, including environment setup,
models, dataset collection, labels, evaluation scripts, results, caveats, and
the current research direction.

## 1. Project Goal

The project investigates whether a local LLM role-playing as a suspect can keep
a consistent deceptive story under interrogation, and whether later analysis can
separate:

- `CONSISTENT_TRUTH`
- `STRATEGIC_LIE`
- `DESIGNED_SLIP`
- `UNINTENDED_INCONSISTENCY`
- `UNSUPPORTED_FACT`
- `FAILURE`

The key scientific distinction is between an answer that contradicts facts
because the suspect is strategically lying, and an answer that contradicts facts
because the model has unintentionally slipped, forgotten, drifted, or invented
something.

## 2. Local Environment and Tool Versions

Operating environment:

- Workspace path: `D:\finishingproject`
- Python: `Python 3.12.7`
- Python executable used by background judge runs: `D:\anaconda\python.exe`
- GPU: `NVIDIA GeForce RTX 4060 Ti`
- NVIDIA driver version: `596.21`
- GPU memory: `8188 MiB`

Ollama:

- Ollama version: `0.24.0`
- Ollama model storage environment variable: `OLLAMA_MODELS=D:\ollama\models`
- Ollama flash attention setting: `OLLAMA_FLASH_ATTENTION=false`
- The `OLLAMA_FLASH_ATTENTION=false` setting was used after the earlier CUDA/PTX
  failure:
  - Error observed: `CUDA error: a PTX JIT compilation failed`
  - After this was fixed, Ollama ran the models on GPU.

Storage and cache paths:

- Ollama models: `D:\ollama\models`
- HuggingFace cache used during NLI: `D:\hf-cache`
- Pip cache used during package install: `D:\pip-cache`

Python packages installed for NLI:

| Package | Version |
|---|---:|
| `transformers` | `5.8.1` |
| `torch` | `2.12.0+cpu` |
| `sentencepiece` | `0.2.1` |

Important note: NLI used the CPU PyTorch package. Ollama suspect and judge
models ran through Ollama and used the GPU when loaded by Ollama.

## 3. Local LLM Models

Installed Ollama models:

| Model | Ollama ID | Size | Role |
|---|---|---:|---|
| `llama3.1:8b` | `46e0c10c039e` | `4.9 GB` | suspect model and same-model judge |
| `qwen2.5:7b-instruct` | `845dbda0ea48` | `4.7 GB` | independent LLM-as-judge model |

Model roles:

- `llama3.1:8b` generated all suspect interrogation answers.
- `llama3.1:8b` was also used as the same-model LLM judge.
- `qwen2.5:7b-instruct` was downloaded later and used as an independent
  cross-model LLM judge.

## 4. HuggingFace NLI Models

Main NLI model:

- HuggingFace model: `MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli`
- Local snapshot hash:
  `6f5cf0a2b59cabb106aca4c287eed12e357e90eb`
- Cache path:
  `D:\hf-cache\hub\models--MoritzLaurer--DeBERTa-v3-base-mnli-fever-anli`
- Used by: `evaluation/nli_analysis.py`
- Backend: `transformers`

Rejected/tested NLI model:

- HuggingFace model: `cross-encoder/nli-deberta-v3-small`
- Local snapshot hash:
  `fa2804872c3b4bd748f38c0185cc85775361e735`
- Reason it was not used as the main NLI model:
  it over-called contradiction and produced poor semantic judgments for this
  dataset.

NLI calibration details:

- The first NLI claim wording used third-person statements such as
  "Marcus took the USB drive."
- The NLI model performed poorly when comparing first-person suspect answers to
  third-person hypotheses.
- Claims were rewritten into first-person wording, for example:
  "I took the USB drive from the conference room."
- A relevance filter was added using claim-level `evidence_terms`.
- A confidence threshold was added:
  - Default threshold: `0.75`
  - Predictions below threshold become `NEUTRAL`.

## 5. Scenario

Scenario file:

- `data/scenario/marcus_chen_case.json`

Suspect:

- Name: Marcus Chen
- Role: operations manager at Park Biotech

Victim:

- Elena Park
- Founder of the biotech startup

Public facts:

- Elena died between `9:45 PM` and `10:20 PM`.
- Marcus told police he went home around `8:30 PM`.
- Building access logs show Marcus's badge was used at `9:18 PM`.
- Elena's phone records show a short call with Marcus at `9:12 PM`.

Private ground truth:

- Marcus did not kill Elena.
- Marcus secretly returned to the office at `9:18 PM` after Elena called him.
- Marcus and Elena argued about missing trial data and a possible internal
  audit.
- Marcus left Elena's office at about `9:47 PM` while she was still alive.
- Marcus took a USB drive from the conference room because he feared Elena
  would blame him for the missing data.
- Marcus later lied about being home all evening because he believed the truth
  would make him look guilty.

Cover story:

- Marcus says he left the investor reception around `8:30 PM`.
- Marcus says he went straight home and stayed there for the rest of the night.
- Marcus says the `9:12 PM` call was brief and only about next-day scheduling.
- Marcus says he does not know why the badge log shows a `9:18 PM` entry.
- Marcus says he had no serious conflict with Elena.

## 6. App and Runtime Files

Main application files:

- `app/main.py`
- `app/terminal_ui.py`
- `app/interrogation_runner.py`
- `app/suspect_agent.py`
- `app/prompt_builder.py`
- `app/question_selector.py`
- `app/logger.py`
- `app/models/ollama_client.py`

The app uses Ollama's local HTTP API through:

- `http://localhost:11434/api/chat`

The app's minimal Ollama client:

- File: `app/models/ollama_client.py`
- Default model source: environment variable `OLLAMA_MODEL`, otherwise
  `llama3.1:8b`
- Chat temperature in the app client: `0.4`

## 7. Data Collection

Raw run files are stored under:

- `data/runs/`

The empty run `2026-05-08T22-45-52.json` was ignored.

Non-empty runs:

| Run ID | Protocol | Turns | Suspect model |
|---|---|---:|---|
| `2026-05-15T12-36-23` | Pilot free-play | 27 | `llama3.1:8b` |
| `2026-05-16T17-26-01` | Protocol A | 13 | `llama3.1:8b` |
| `2026-05-16T17-28-56` | Protocol B | 12 | `llama3.1:8b` |
| `2026-05-16T17-31-52` | Protocol C | 12 | `llama3.1:8b` |
| `2026-05-16T20-54-00` | Protocol D | 14 | `llama3.1:8b` |
| `2026-05-16T20-57-29` | Protocol E | 12 | `llama3.1:8b` |
| `2026-05-16T22-06-17` | Protocol F | 12 | `llama3.1:8b` |
| `2026-05-16T22-08-16` | Protocol G | 70 | `llama3.1:8b` |

Total non-empty runs: `8`

Total labeled turns: `172`

## 8. Human Labels

Annotation CSV files:

- `data/labeled/pilot_2026-05-15T12-36-23_annotations.csv`
- `data/labeled/protocol_A_2026-05-16T17-26-01_annotations.csv`
- `data/labeled/protocol_B_2026-05-16T17-28-56_annotations.csv`
- `data/labeled/protocol_C_2026-05-16T17-31-52_annotations.csv`
- `data/labeled/protocol_D_2026-05-16T20-54-00_annotations.csv`
- `data/labeled/protocol_E_2026-05-16T20-57-29_annotations.csv`
- `data/labeled/protocol_F_2026-05-16T22-06-17_annotations.csv`
- `data/labeled/protocol_G_2026-05-16T22-08-16_annotations.csv`

Label schema file:

- `evaluation/label_schema.md`

Human label counts:

| Label | Count |
|---|---:|
| `STRATEGIC_LIE` | 82 |
| `CONSISTENT_TRUTH` | 51 |
| `UNINTENDED_INCONSISTENCY` | 12 |
| `DESIGNED_SLIP` | 12 |
| `UNSUPPORTED_FACT` | 11 |
| `FAILURE` | 4 |

Important current concern:

- We now suspect that the dataset may not contain enough clean, undeniable
  `UNINTENDED_INCONSISTENCY` examples.
- Some turns labeled as `UNINTENDED_INCONSISTENCY` may be debatable after close
  inspection.
- Protocol G did create pressure and repeated questioning, but even at turn 70
  the model often remained fairly stable or gave answer patterns that could be
  interpreted as strategic behavior rather than accidental memory failure.

## 9. Evaluation Pipeline

Pipeline documentation:

- `evaluation/evaluation_pipeline.md`

Stages:

1. Human reference labels
2. Structural analysis
3. Rule-based checks
4. NLI-based claim analysis
5. LLM-as-judge comparison

## 10. Structural Analysis

Script:

- `evaluation/structural_analysis.py`

Outputs:

- `data/results/<run_id>_structural.csv`
- `data/results/<run_id>_structural.summary.json`

Structural analysis was run for all 8 non-empty runs.

Purpose:

- Describe the shape of the dialogue.
- Record turn count, question source, repeated topics, pressure patterns, and
  key fact mentions.
- Avoid making final truth/deception judgments.

## 11. Rule-Based Detector

Script:

- `evaluation/rule_based_detector.py`

Result notes:

- `evaluation/rule_based_results.md`

Outputs:

- `data/results/<run_id>_rules.csv`

Rule-based detector was run for all 8 non-empty runs.

Rule-based agreement by run:

| Run ID | Matches | Accuracy |
|---|---:|---:|
| `2026-05-15T12-36-23` | 16 / 27 | 0.593 |
| `2026-05-16T17-26-01` | 7 / 13 | 0.538 |
| `2026-05-16T17-28-56` | 9 / 12 | 0.750 |
| `2026-05-16T17-31-52` | 8 / 12 | 0.667 |
| `2026-05-16T20-54-00` | 7 / 14 | 0.500 |
| `2026-05-16T20-57-29` | 3 / 12 | 0.250 |
| `2026-05-16T22-06-17` | 7 / 12 | 0.583 |
| `2026-05-16T22-08-16` | 35 / 70 | 0.500 |

Aggregate rule-based metrics:

| Metric | Value |
|---|---:|
| Total turns | 172 |
| Correct | 92 |
| Accuracy | 0.535 |
| Macro precision | 0.622 |
| Macro recall | 0.549 |
| Macro F1 | 0.530 |

Interpretation:

- The rule-based detector performed best overall by macro F1.
- This is because it encodes case-specific facts and rare-label rules.
- It is transparent but not expected to generalize without new rules.

## 12. NLI Analysis

Script:

- `evaluation/nli_analysis.py`

Claim file:

- `evaluation/nli_claims.json`

Result notes:

- `evaluation/nli_results.md`

Main NLI model:

- `MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli`

Backend:

- `transformers`

Important parameters:

- Confidence threshold: `0.75`
- Relevance filtering: enabled through `evidence_terms`
- Default NLI backend in the script: `transformers`
- Ollama backend remains available only as a fallback/debug option.

Outputs:

- `data/results/<run_id>_nli.csv`
- `data/results/<run_id>_nli_turns.csv`
- `data/results/<run_id>_nli.summary.json`

NLI aggregate counts:

| NLI label | Count |
|---|---:|
| `NEUTRAL` | 2230 |
| `CONTRADICTION` | 107 |
| `ENTAILMENT` | 71 |

Total analyzed turn-claim pairs: `2408`

Turn-level NLI signal counts:

| NLI signal | Count |
|---|---:|
| `NO_STRONG_SIGNAL` | 82 |
| `GROUND_TRUTH_CONTRADICTED` | 32 |
| `CROSS_TURN_FLIP` | 23 |
| `GROUND_TRUTH_SUPPORTED` | 22 |
| `COVER_STORY_SUPPORTED` | 10 |
| `UNSUPPORTED_CLAIM_ENTAILED` | 3 |

NLI proxy baseline:

| Metric | Value |
|---|---:|
| Total turns | 172 |
| Correct | 83 |
| Accuracy | 0.483 |
| Macro precision | 0.350 |
| Macro recall | 0.306 |
| Macro F1 | 0.277 |

Important interpretation:

- The NLI proxy baseline is only a coarse mapping from NLI signal to label.
- NLI is more valuable as claim-level semantic evidence than as a direct final
  label classifier.

## 13. Protocol G Long-Context Stress Test

Protocol notes:

- `evaluation/protocol_G_long_context_notes.md`

Run:

- `data/runs/2026-05-16T22-08-16.json`

Turns:

- `70`

Human label counts for Protocol G:

| Label | Count |
|---|---:|
| `CONSISTENT_TRUTH` | 28 |
| `STRATEGIC_LIE` | 27 |
| `UNINTENDED_INCONSISTENCY` | 7 |
| `DESIGNED_SLIP` | 4 |
| `UNSUPPORTED_FACT` | 4 |

NLI counts for Protocol G:

| NLI label | Count |
|---|---:|
| `NEUTRAL` | 892 |
| `ENTAILMENT` | 41 |
| `CONTRADICTION` | 47 |

Protocol G NLI signal counts:

| NLI signal | Count |
|---|---:|
| `NO_STRONG_SIGNAL` | 28 |
| `COVER_STORY_SUPPORTED` | 4 |
| `GROUND_TRUTH_CONTRADICTED` | 10 |
| `GROUND_TRUTH_SUPPORTED` | 13 |
| `CROSS_TURN_FLIP` | 15 |

Previously identified key drift turns:

- Turn 30: first major possible memory/cover breakdown.
- Turn 31: follow-up timing correction / flip.
- Turn 51: later last-seen timing drift.
- Turn 62: possible contradiction around being at the office until Elena's
  death.
- Turns 64 and 65: repeated last-seen timing drift.

Current caveat:

- These turns are useful stress examples, but the project should be careful
  about claiming that they are all undeniable `UNINTENDED_INCONSISTENCY`.
- Some may be interpretable as strategic evasions, designed admissions, or
  ordinary truth restatements depending on the exact answer.
- This is why a second experiment with a guilty suspect may be scientifically
  useful.

## 14. LLM-As-Judge

Script:

- `evaluation/llm_judge.py`

Result notes:

- `evaluation/llm_judge_results.md`

Judges:

| Judge condition | Model | Role |
|---|---|---|
| Same-model judge | `llama3.1:8b` | judge model is the same as the suspect model family |
| Independent judge | `qwen2.5:7b-instruct` | separate model family used to reduce self-judge bias |

Ollama judge call settings:

- API: `http://localhost:11434/api/chat`
- `format`: `json`
- `temperature`: `0`
- `num_ctx`: `8192`
- `num_predict`: `500`

Judge prompt inputs:

- scenario summary
- public known facts
- private ground truth
- cover story
- behavior rules
- pressure escalation notes
- selected prior dialogue evidence
- current question and answer
- rule-based signal as a non-authoritative hint
- NLI signal as a non-authoritative hint

Important methodological point:

- Human labels were not given to the judges.
- Human labels were used only after the judge calls for scoring.

Outputs:

- `data/results/<run_id>_judge_llama3.1_8b.csv`
- `data/results/<run_id>_judge_qwen2.5_7b-instruct.csv`
- `data/results/llm_judge_summary.csv`
- `data/results/llm_judge_per_label.csv`
- `data/results/llm_judge_confusion_matrix.csv`
- `data/results/llm_judge_pairwise_comparison.csv`

LLM judge aggregate metrics:

| Judge | Correct | Accuracy | Macro precision | Macro recall | Macro F1 |
|---|---:|---:|---:|---:|---:|
| `llama3.1:8b` | 89 / 172 | 0.517 | 0.293 | 0.285 | 0.275 |
| `qwen2.5:7b-instruct` | 79 / 172 | 0.459 | 0.356 | 0.227 | 0.226 |

Pairwise judge comparison:

| Outcome | Count |
|---|---:|
| Total compared turns | 172 |
| Judges agree | 114 |
| Judges disagree | 58 |
| Both match human label | 64 |
| Only Llama matches human label | 25 |
| Only Qwen matches human label | 15 |
| Neither matches human label | 68 |

Judge agreement rate:

- `114 / 172 = 0.663`

Accuracy when both judges agree:

- `64 / 114 = 0.561`

Critical LLM-as-judge finding:

- Both LLM judges failed to recover `UNINTENDED_INCONSISTENCY` as a class.
- Llama judge recall for `UNINTENDED_INCONSISTENCY`: `0.000`
- Qwen judge recall for `UNINTENDED_INCONSISTENCY`: `0.000`

Interpretation:

- LLM-as-judge did not solve the classification task.
- The judges were better at common labels such as `STRATEGIC_LIE` and
  `CONSISTENT_TRUTH`.
- They often rationalized possible model drift as strategic behavior or
  truthful admission.
- This may be partly a prompt limitation, but it is also a dataset/design issue:
  there may not be enough clean unintended inconsistency in the current data.

## 15. Scientific Report Draft

Draft file:

- `SCIENTIFIC_REPORT_DRAFT.md`

The draft currently includes:

- abstract
- introduction
- research questions
- scenario design
- dataset
- evaluation pipeline
- ablation summary
- LLM judge comparison
- Protocol G finding
- discussion
- limitations
- conclusion

Current status:

- The draft is usable as a working scientific report draft.
- It should be revised after deciding whether the current dataset's
  `UNINTENDED_INCONSISTENCY` labels are strong enough.

## 16. Other Project Notes and Files

Question and protocol files:

- `data/question_bank/marcus_questions.json`
- `evaluation/interrogation_protocols.md`
- `evaluation/run_log_template.md`

Future scenario file:

- `NEXT_SCENARIO.md`

This file was created to hold ideas for a future more aggressive or guilty
suspect scenario. The current project data still belongs to the Marcus Chen
not-guilty scenario.

Export script:

- `evaluation/export_annotations.py`

Human-label notes:

- `evaluation/pilot_2026-05-15T12-36-23_human_labels.md`
- `evaluation/protocol_ABC_human_labels.md`

Dataset status:

- `evaluation/dataset_status.md`

## 17. Main Findings So Far

1. The local interrogation app works with Ollama and saved all runs as JSON.
2. Ollama model storage was moved to the D drive through `OLLAMA_MODELS`.
3. `llama3.1:8b` was used successfully as the suspect model.
4. `qwen2.5:7b-instruct` was downloaded and used as an independent judge.
5. The dataset contains 172 labeled turns across 8 non-empty runs.
6. The rule-based detector achieved the strongest macro F1: `0.530`.
7. NLI was useful as semantic claim-level evidence but weaker as a direct label
   proxy.
8. LLM-as-judge underperformed on macro F1:
   - Llama judge macro F1: `0.275`
   - Qwen judge macro F1: `0.226`
9. Both LLM judges failed to identify `UNINTENDED_INCONSISTENCY`.
10. The current dataset may not contain enough clean unintended inconsistency to
    support strong conclusions about memory failure detection.

## 18. Current Methodological Concern

The current concern is important and should be carried into the report:

The observed results may be partly caused by the fact that the dataset has too
few clean unintended inconsistencies. Protocol G used 70 turns and repeated
questions, but the model often answered with similar or stable answers. Some
turns labeled as `UNINTENDED_INCONSISTENCY` may be debatable when examined
closely.

This means the current report should avoid overstating the claim that Protocol G
clearly demonstrated many memory leaks. A more careful framing is:

> In the current not-guilty-suspect scenario, long-context pressure produced
> limited and ambiguous drift. Automatic methods, especially LLM-as-judge, had
> difficulty separating possible unintended inconsistency from strategic
> deception or truthful restatement.

## 19. Recommended Next Experiment

A second experiment should use a guilty suspect scenario.

Reason:

- In the current scenario, Marcus did not kill Elena.
- Therefore, "I did not kill her" is true.
- This makes murder-denial pressure less useful for producing contradictions.

A guilty-suspect scenario can create clearer categories:

- Denying the murder despite guilt: `STRATEGIC_LIE`
- Accidentally revealing crime details too early: `UNINTENDED_INCONSISTENCY`
- Admitting after strong evidence pressure: `DESIGNED_SLIP`
- Inventing an accomplice, weapon, or false alibi witness: `UNSUPPORTED_FACT`
- Confessing in a way that breaks the scenario rules too early: possible
  `FAILURE` or `UNINTENDED_INCONSISTENCY`, depending on the setup.

The next scenario should be explicitly designed to test the exact failure mode
that this first scenario only weakly produced.

## 20. Current Final Status

Completed:

- Ollama setup on D drive
- GPU-related Ollama fix
- Suspect model setup: `llama3.1:8b`
- Independent judge model setup: `qwen2.5:7b-instruct`
- Data collection for 8 runs
- Human labels for 172 turns
- Structural analysis
- Rule-based detector
- NLI analysis
- Same-model LLM judge
- Independent-model LLM judge
- Results summaries
- Scientific report draft

Not yet completed:

- Final polished scientific report
- Figures/tables formatted for submission
- Revised or audited human labels after the new concern about
  `UNINTENDED_INCONSISTENCY`
- Second guilty-suspect experiment

