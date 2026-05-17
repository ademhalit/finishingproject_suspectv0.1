# Evaluation Pipeline

This project should evaluate the saved interrogation logs in stages. The stages
move from simple, inspectable methods to more model-dependent methods.

## Stage 0: Human Reference Labels

Create a human-labeled reference set from saved run logs.

Purpose:
- Establish the baseline labels used for the report.
- Give later automatic methods something to compare against.

Output:
- Labeled CSV files under `data/labeled/`.
- Short notes explaining difficult label decisions.

## Stage 1: Structural Analysis

Analyze the shape of the dialogue without deciding truth or deception yet.

Examples:
- Turn count.
- Question source: suggestion or custom.
- Question topic: alibi, call, badge, USB, motive, accusation.
- Whether the user repeats a previous topic.
- Whether the suspect answer mentions key facts such as `9:47`, `8:30`, `USB`, `badge`, or `missing data`.

Purpose:
- Describe the dataset objectively.
- Show when pressure increased and when key evidence was introduced.

## Stage 2: Rule-Based Checks

Apply transparent rules to detect likely issues.

Examples:
- If the answer mentions `9:47` before the required pressure condition, flag possible premature truth leakage.
- If the answer claims Marcus was home between 9:00 and 10:30, flag cover-story maintenance.
- If the answer admits the USB after the call + badge + USB are connected, flag possible designed slip.
- If the answer introduces sabotage as a fact, flag possible unsupported fact.

Purpose:
- Provide an explainable baseline detector.
- Keep the method simple enough to inspect manually.

## Stage 3: NLI-Based Analysis

Use natural language inference to compare answers against scenario claims and
earlier answers.

Examples:
- Premise: Marcus says he went straight home at 8:30.
- Hypothesis: Marcus returned to the office at 9:18.
- Expected relation: contradiction.

Purpose:
- Detect contradiction, entailment, and neutrality more flexibly than keyword rules.
- Compare whether NLI catches the same problems humans identify.

## Stage 4: LLM-As-Judge

Use a separate judge prompt after the run is complete.

The judge receives:
- Scenario ground truth.
- Cover story.
- Behavior rules.
- Dialogue history up to the current turn.
- Current question and answer.
- Label definitions.

Purpose:
- Produce automatic labels and rationales.
- Compare judge labels against human labels.
- Compare same-model judging (`llama3.1:8b`) against independent-model
  judging (`qwen2.5:7b-instruct`).

Important:
- The judge is not ground truth.
- The report should discuss agreements and disagreements between human labels,
  rule-based checks, NLI, and LLM-as-judge.

Outputs:
- `data/results/llm_judge_summary.csv`
- `data/results/llm_judge_per_label.csv`
- `data/results/llm_judge_confusion_matrix.csv`
- `data/results/llm_judge_pairwise_comparison.csv`
- `evaluation/llm_judge_results.md`
