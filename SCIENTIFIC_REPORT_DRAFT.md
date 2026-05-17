# Detecting Strategic Deception and Unintended Inconsistency in Local LLM Suspect Interrogations

## Abstract

This project investigates whether a local large language model can maintain a
fictional suspect role under repeated interrogation, and whether post-hoc
analysis can distinguish intentional deception from unintended inconsistency.
The suspect model was `llama3.1:8b`, running locally through Ollama. The scenario
involved Marcus Chen, a biotech operations manager who did not kill Elena Park
but did return to the office, argue with her about missing trial data, take a USB
drive, and lie about being home all evening.

Eight interrogation runs were collected, producing 172 labeled turns. The
evaluation pipeline combined human labels, structural analysis, rule-based
checks, natural language inference (NLI), and two LLM-as-judge conditions. The
same-model judge used `llama3.1:8b`; the independent judge used
`qwen2.5:7b-instruct`. Results show that simple rule-based checks achieved the
highest macro F1 in this dataset (0.530), while LLM judges struggled especially
with `UNINTENDED_INCONSISTENCY`. The long-context stress run, Protocol G, showed
a clear memory/consistency breakdown beginning around turn 30 and recurring at
turns 51, 62, 64, and 65. These findings suggest that LLM-as-judge is useful as
a comparison method, but not sufficient as a standalone detector of unintended
model inconsistency.

## 1. Introduction

Role-playing LLM systems often appear coherent in short interactions, but their
consistency can degrade under long-context pressure, repeated questioning, and
contradictory evidence. In an interrogation-style interaction, this creates a
methodological problem: a suspect character may lie because the scenario
requires deception, but the model may also contradict itself unintentionally.
These two phenomena look similar at the surface level but have different
interpretations.

This project studies that distinction in a controlled local setup. The central
question is not simply whether the model is "wrong." The question is whether a
turn should be interpreted as:

- a truthful answer,
- a strategic lie required by the character,
- a designed slip caused by pressure,
- an unintended inconsistency caused by model/context failure,
- an unsupported invented fact, or
- an experimental failure.

## 2. Research Questions

The study addresses four research questions:

1. Can a local LLM suspect maintain a deceptive cover story across repeated
   interrogation?
2. At what point does long-context pressure produce memory drift or unintended
   inconsistency?
3. Which automatic methods best identify different error/deception categories?
4. Does an independent LLM judge improve evaluation compared with a same-model
   judge?

## 3. Scenario Design

The scenario centers on Elena Park, founder of a small biotech startup, who is
found dead after an investor reception. Marcus Chen, the operations manager, is
one of the last employees known to have contact with her.

Important public facts:

- Elena died between 9:45 PM and 10:20 PM.
- Marcus told police he went home around 8:30 PM.
- Marcus's badge was used at 9:18 PM.
- Elena's phone records show a short call with Marcus at 9:12 PM.

Private ground truth:

- Marcus did not kill Elena.
- Marcus returned to the office at 9:18 PM after Elena called him.
- Marcus and Elena argued about missing trial data and a possible audit.
- Marcus left Elena's office around 9:47 PM while Elena was still alive.
- Marcus took a USB drive because he feared Elena would blame him for the
  missing data.
- Marcus lied about being home all evening because the truth made him look
  guilty.

The cover story instructed Marcus to claim that he left around 8:30 PM, went
straight home, treated the 9:12 PM call as routine scheduling, denied knowing why
the badge was used at 9:18 PM, and minimized conflict with Elena.

## 4. Dataset

The dataset contains eight non-empty runs and 172 labeled turns.

| Run | Protocol | Turns |
|---|---:|---:|
| `2026-05-15T12-36-23` | Pilot free-play | 27 |
| `2026-05-16T17-26-01` | Protocol A | 13 |
| `2026-05-16T17-28-56` | Protocol B | 12 |
| `2026-05-16T17-31-52` | Protocol C | 12 |
| `2026-05-16T20-54-00` | Protocol D | 14 |
| `2026-05-16T20-57-29` | Protocol E | 12 |
| `2026-05-16T22-06-17` | Protocol F | 12 |
| `2026-05-16T22-08-16` | Protocol G | 70 |

Human label distribution:

| Label | Count |
|---|---:|
| `STRATEGIC_LIE` | 82 |
| `CONSISTENT_TRUTH` | 51 |
| `UNINTENDED_INCONSISTENCY` | 12 |
| `DESIGNED_SLIP` | 12 |
| `UNSUPPORTED_FACT` | 11 |
| `FAILURE` | 4 |

The labels are imbalanced, so macro F1 is more informative than accuracy alone.

## 5. Evaluation Pipeline

The evaluation pipeline has five stages.

### 5.1 Human Reference Labels

All 172 turns were manually labeled. These labels are treated as the reference
set for automatic comparisons.

### 5.2 Structural Analysis

Structural analysis describes the dialogue without deciding truth or deception.
It records turn count, question topic, repeated pressure, and key fact mentions
such as `9:47`, `9:18`, `USB`, `badge`, and `missing data`.

### 5.3 Rule-Based Detector

The rule-based detector uses transparent case-specific rules. For example, it
flags the home alibi, badge excuses, unsupported sister/sabotage claims, and
long-context timing conflicts. This baseline is interpretable but not general.

### 5.4 NLI Analysis

The NLI stage uses `MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli`. It compares
suspect answers against canonical scenario claims. A relevance filter prevents
the NLI model from judging unrelated claims. NLI outputs are used primarily as
claim-level evidence, not as final labels.

### 5.5 LLM-As-Judge

Two local judges were used:

- same-model judge: `llama3.1:8b`
- independent judge: `qwen2.5:7b-instruct`

The judges received scenario truth, cover story, behavior rules, selected prior
dialogue, current question/answer, and automatic rule/NLI signals. Human labels
were not included in the judge prompt.

## 6. Results

### 6.1 Ablation Summary

| Method | Accuracy | Macro Precision | Macro Recall | Macro F1 |
|---|---:|---:|---:|---:|
| Rule-based baseline | 0.535 | 0.622 | 0.549 | 0.530 |
| NLI proxy baseline | 0.483 | 0.350 | 0.306 | 0.277 |
| Llama judge | 0.517 | 0.293 | 0.285 | 0.275 |
| Qwen judge | 0.459 | 0.356 | 0.227 | 0.226 |

The rule-based baseline had the strongest macro F1. This does not mean it is
the most general method; it means that case-specific transparent rules were
better at recovering rare labels in this dataset.

The NLI proxy baseline was weaker as a direct classifier. However, this is not
the main purpose of NLI. NLI is more useful as semantic evidence showing whether
a turn entails or contradicts specific scenario claims.

The LLM judges performed worse than expected on macro F1. They detected many
strategic lies, but they did not recover the `UNINTENDED_INCONSISTENCY` class.

### 6.2 LLM Judge Comparison

| Judge | Accuracy | Macro F1 |
|---|---:|---:|
| `llama3.1:8b` | 0.517 | 0.275 |
| `qwen2.5:7b-instruct` | 0.459 | 0.226 |

The two judges agreed on 114 of 172 turns, an agreement rate of 0.663. When
they agreed, they matched the human label on 64 of 114 turns, giving an
agreement-subset accuracy of 0.561.

Pairwise outcome counts:

| Outcome | Count |
|---|---:|
| Both judges match human label | 64 |
| Only Llama judge matches | 25 |
| Only Qwen judge matches | 15 |
| Neither judge matches | 68 |

This shows that independent-model judging is not redundant. Qwen and Llama make
different mistakes. However, the independent judge did not solve the labeling
problem.

### 6.3 Per-Label Judge Weakness

Both LLM judges failed to identify `UNINTENDED_INCONSISTENCY`.

| Model | `UNINTENDED_INCONSISTENCY` Recall |
|---|---:|
| `llama3.1:8b` | 0.000 |
| `qwen2.5:7b-instruct` | 0.000 |

This is the central negative result. The most important phenomenon in the study
is long-context memory drift, but LLM judges tend to reinterpret that drift as
plausible strategy, truthful admission, or designed slip.

## 7. Protocol G Long-Context Finding

Protocol G was designed as a long-context stress test. It collected 70 turns and
included repeated questions to test whether Marcus would maintain stable
answers.

The first major breakdown occurs at turn 30. Marcus says he left Elena's office
around 9:47 PM while still maintaining earlier elements of the home-cover
timeline. Later drift appears at turns 51, 64, and 65, where the last-seen time
shifts toward 9:18 PM even though the scenario ground truth says Marcus left
Elena's office around 9:47 PM. Turn 62 also contradicts the ground truth by
placing Marcus at the office until Elena's death.

NLI identified this region more clearly than the LLM judges. In contrast, the
LLM judges classified the known drift turns as follows:

| Turn | Human Label | Llama Judge | Qwen Judge |
|---:|---|---|---|
| 30 | `UNINTENDED_INCONSISTENCY` | `STRATEGIC_LIE` | `STRATEGIC_LIE` |
| 31 | `UNINTENDED_INCONSISTENCY` | `CONSISTENT_TRUTH` | `DESIGNED_SLIP` |
| 51 | `UNINTENDED_INCONSISTENCY` | `CONSISTENT_TRUTH` | `DESIGNED_SLIP` |
| 62 | `UNINTENDED_INCONSISTENCY` | `CONSISTENT_TRUTH` | `STRATEGIC_LIE` |
| 64 | `UNINTENDED_INCONSISTENCY` | `CONSISTENT_TRUTH` | `STRATEGIC_LIE` |
| 65 | `UNINTENDED_INCONSISTENCY` | `CONSISTENT_TRUTH` | `STRATEGIC_LIE` |

This supports the conclusion that LLM-as-judge is weak at recognizing
unintended memory/context failure when the answer can be rationalized as part of
the suspect's strategy.

## 8. Discussion

The results show that the distinction between strategic deception and model
inconsistency is difficult. The suspect model is explicitly instructed to lie,
so contradiction alone is not enough. A contradiction may be the intended cover
story. Conversely, a truthful admission may be a designed slip, a consistent
truth, or an unintended leak, depending on pressure and dialogue history.

The rule-based baseline performs well because it encodes case-specific
knowledge. It is transparent and effective for known patterns, but it is not
expected to generalize without new rules.

NLI provides useful semantic evidence, especially for detecting claim-level
support and contradiction. However, NLI does not know intention. It can say that
an answer contradicts a scenario claim, but it cannot decide whether the
contradiction is strategic or accidental.

LLM-as-judge adds qualitative reasoning but also introduces new bias. The
same-model judge may rationalize the suspect model's behavior. The independent
judge avoids exact self-judging, but still struggles with rare labels and often
overuses `STRATEGIC_LIE`.

The strongest evaluation design is therefore multi-stage:

1. human labels as reference,
2. structural analysis for dataset description,
3. rule-based checks for transparent baseline detection,
4. NLI for semantic claim evidence,
5. LLM judges for comparison and disagreement analysis.

## 9. Limitations

The dataset is small and based on one scenario. The labels are imbalanced, with
many more `STRATEGIC_LIE` and `CONSISTENT_TRUTH` turns than rare labels.

The rule-based detector is case-specific, so its performance may overestimate
what rules would achieve on a new scenario.

The NLI model required claim wording and relevance filtering. Without that
calibration, it produced false contradictions on unrelated claims.

The LLM judges used local 7B/8B models. Larger external models might perform
better, but using them would introduce a different experimental condition.

The current scenario uses a suspect who did not kill the victim. A future
guilty-suspect scenario may create stronger pressure and clearer lie/confession
dynamics.

## 10. Conclusion

This study shows that local LLM suspect simulations can maintain a cover story
for many turns, but long-context interrogation can produce measurable drift. The
most important observed breakdown occurred in Protocol G, beginning around turn
30 and recurring in later repeated questions.

The best-performing automatic baseline in this dataset was the rule-based
detector, but its strength comes from case-specific transparency. NLI was useful
for semantic contradiction evidence, especially around long-context drift.
LLM-as-judge did not solve the task: both same-model and independent-model
judges failed to identify unintended inconsistency as a class.

The main contribution is therefore not a single perfect classifier. The
contribution is a staged evaluation method for separating strategic deception,
designed slips, unsupported invention, and unintended model inconsistency in a
local LLM interrogation setting.

## Appendix: Generated Artifacts

Key result files:

- `evaluation/dataset_status.md`
- `evaluation/rule_based_results.md`
- `evaluation/nli_results.md`
- `evaluation/llm_judge_results.md`
- `data/results/llm_judge_summary.csv`
- `data/results/llm_judge_per_label.csv`
- `data/results/llm_judge_confusion_matrix.csv`
- `data/results/llm_judge_pairwise_comparison.csv`
