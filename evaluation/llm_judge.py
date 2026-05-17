"""Run LLM-as-judge evaluation over saved interrogation runs.

This stage uses Ollama chat models as post-hoc judges. It can run both the
same model that generated the suspect answers and an independent model family.
Human labels are never sent to the judge; they are loaded only for scoring.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


LABELS = [
    "CONSISTENT_TRUTH",
    "STRATEGIC_LIE",
    "DESIGNED_SLIP",
    "UNINTENDED_INCONSISTENCY",
    "UNSUPPORTED_FACT",
    "FAILURE",
]


JUDGE_COLUMNS = [
    "run_id",
    "turn_id",
    "experiment_id",
    "protocol_id",
    "case_id",
    "scenario_version",
    "judge_model",
    "judge_label",
    "judge_confidence",
    "judge_rationale",
    "judge_evidence",
    "rule_label",
    "rule_flags",
    "nli_signal",
    "nli_entailed_claims",
    "nli_contradicted_claims",
    "human_label",
    "label_match",
    "parse_ok",
    "raw_response",
    "user_question",
    "suspect_answer",
]


SUMMARY_COLUMNS = [
    "judge_model",
    "turn_count",
    "correct",
    "accuracy",
    "macro_precision",
    "macro_recall",
    "macro_f1",
]


PER_LABEL_COLUMNS = [
    "judge_model",
    "label",
    "support",
    "precision",
    "recall",
    "f1",
    "tp",
    "fp",
    "fn",
]


CONFUSION_COLUMNS = ["judge_model", "actual_label", *[f"pred_{label}" for label in LABELS]]


COMPARISON_COLUMNS = [
    "run_id",
    "turn_id",
    "human_label",
    "judge_a_model",
    "judge_a_label",
    "judge_b_model",
    "judge_b_label",
    "judges_agree",
    "both_match_human",
    "only_judge_a_matches",
    "only_judge_b_matches",
    "user_question",
]


KEY_HISTORY_TERMS = [
    "8:30",
    "9:12",
    "9:18",
    "9:47",
    "10:20",
    "home",
    "apartment",
    "office",
    "badge",
    "call",
    "called",
    "usb",
    "drive",
    "missing",
    "trial",
    "audit",
    "elena",
    "kill",
    "killed",
    "murder",
    "sister",
    "sabotage",
    "falsified",
    "argued",
    "argument",
]


def main() -> None:
    """CLI entrypoint."""

    parser = argparse.ArgumentParser(description="Run LLM-as-judge evaluation.")
    parser.add_argument("--run", default=None, help="One run JSON file to judge.")
    parser.add_argument("--runs-dir", default="data/runs", help="Directory of run JSON files.")
    parser.add_argument(
        "--scenario",
        default=None,
        help="Scenario JSON file. If omitted, use the run's scenario_file metadata or the Experiment 1 default.",
    )
    parser.add_argument("--labels-dir", default="data/labeled")
    parser.add_argument("--signals-dir", default="data/results")
    parser.add_argument("--output-dir", default="data/results")
    parser.add_argument(
        "--models",
        nargs="+",
        default=["llama3.1:8b", "qwen2.5:7b-instruct"],
        help="Judge models to run through Ollama.",
    )
    parser.add_argument("--base-url", default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--sleep", type=float, default=0.0)
    parser.add_argument("--limit-turns", type=int, default=None, help="Debug limit per run.")
    parser.add_argument(
        "--history-turns",
        type=int,
        default=8,
        help="Always include this many recent previous turns.",
    )
    parser.add_argument(
        "--max-context-turns",
        type=int,
        default=24,
        help="Maximum previous turns included in the judge prompt.",
    )
    parser.add_argument(
        "--no-signals",
        action="store_true",
        help="Do not include rule/NLI signals in the judge prompt.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip judge rows that already exist in the output CSV.",
    )
    parser.add_argument(
        "--summarize-only",
        action="store_true",
        help="Only summarize existing judge CSV files.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.summarize_only:
        write_comparison_outputs(output_dir)
        return

    run_paths = [Path(args.run)] if args.run else sorted(Path(args.runs_dir).glob("*.json"))
    run_paths = [path for path in run_paths if path.name != "2026-05-08T22-45-52.json"]

    for model in args.models:
        ensure_model_available(model, args.base_url, args.timeout)

    for model in args.models:
        for run_path in run_paths:
            judge_run(
                model=model,
                run_path=run_path,
                scenario_path=Path(args.scenario) if args.scenario else None,
                labels_dir=Path(args.labels_dir),
                signals_dir=Path(args.signals_dir),
                output_dir=output_dir,
                base_url=args.base_url,
                timeout=args.timeout,
                limit_turns=args.limit_turns,
                history_turns=args.history_turns,
                max_context_turns=args.max_context_turns,
                include_signals=not args.no_signals,
                resume=args.resume,
                sleep_seconds=args.sleep,
            )

    write_comparison_outputs(output_dir)


def judge_run(
    model: str,
    run_path: Path,
    scenario_path: Path | None,
    labels_dir: Path,
    signals_dir: Path,
    output_dir: Path,
    base_url: str,
    timeout: int,
    limit_turns: int | None,
    history_turns: int,
    max_context_turns: int,
    include_signals: bool,
    resume: bool,
    sleep_seconds: float,
) -> None:
    """Judge one run with one model."""

    run_data = load_json(run_path)
    scenario = load_scenario_for_run(run_data, scenario_path)
    run_id = run_data.get("run_id", run_path.stem)
    turns = run_data.get("turns", [])
    if limit_turns is not None:
        turns = turns[:limit_turns]

    human_labels = find_human_labels(run_id, labels_dir)
    rule_rows = load_signal_rows(signals_dir / f"{run_id}_rules.csv", key_name="turn_id")
    nli_rows = load_signal_rows(signals_dir / f"{run_id}_nli_turns.csv", key_name="turn_id")

    output_path = output_dir / f"{run_id}_judge_{slug_model(model)}.csv"
    existing_keys = load_existing_keys(output_path) if resume else set()

    if not resume and output_path.exists():
        output_path.unlink()

    print(f"Judging {run_id}: {len(turns)} turn(s), model={model}", flush=True)
    written_count = 0
    for index, turn in enumerate(turns, start=1):
        turn_id = int(turn.get("turn_id", index))
        if (run_id, turn_id, model) in existing_keys:
            continue

        rule_row = rule_rows.get(turn_id, {})
        nli_row = nli_rows.get(turn_id, {})
        prompt = build_user_prompt(
            scenario=scenario,
            run_data=run_data,
            turns=turns,
            current_index=index - 1,
            rule_row=rule_row,
            nli_row=nli_row,
            history_turns=history_turns,
            max_context_turns=max_context_turns,
            include_signals=include_signals,
        )
        raw_response = call_ollama_json(
            model=model,
            prompt=prompt,
            base_url=base_url,
            timeout=timeout,
        )
        parsed, parse_ok = parse_json_object(raw_response)
        judge_label = normalize_label(parsed.get("label", ""))
        judge_confidence = normalize_confidence(parsed.get("confidence", ""))
        rationale = str(parsed.get("rationale", "")).strip()
        evidence = parsed.get("evidence", [])
        evidence_text = " | ".join(str(item) for item in evidence) if isinstance(evidence, list) else str(evidence)
        human_label = human_labels.get(turn_id, "")
        label_match = str(judge_label == human_label) if human_label and judge_label else ""

        row = {
            "run_id": run_id,
            "turn_id": turn_id,
            "experiment_id": turn.get("experiment_id", run_data.get("experiment_id", "")),
            "protocol_id": turn.get("protocol_id", run_data.get("protocol_id", "")),
            "case_id": turn.get("case_id", run_data.get("case_id", "")),
            "scenario_version": turn.get("scenario_version", run_data.get("scenario_version", "")),
            "judge_model": model,
            "judge_label": judge_label,
            "judge_confidence": judge_confidence,
            "judge_rationale": rationale,
            "judge_evidence": evidence_text,
            "rule_label": rule_row.get("rule_label", ""),
            "rule_flags": rule_row.get("flags", ""),
            "nli_signal": nli_row.get("nli_signal", ""),
            "nli_entailed_claims": nli_row.get("entailed_claims", ""),
            "nli_contradicted_claims": nli_row.get("contradicted_claims", ""),
            "human_label": human_label,
            "label_match": label_match,
            "parse_ok": str(parse_ok and bool(judge_label)),
            "raw_response": raw_response,
            "user_question": turn.get("user_question", ""),
            "suspect_answer": turn.get("suspect_answer", ""),
        }
        append_csv(output_path, JUDGE_COLUMNS, [row], append=output_path.exists())
        written_count += 1
        print(
            f"  T{turn_id}: {judge_label or 'NO_LABEL'} "
            f"(human={human_label or 'none'}, match={label_match or 'n/a'})",
            flush=True,
        )

        if sleep_seconds:
            time.sleep(sleep_seconds)

    print(f"Wrote {output_path} ({written_count} new row(s))", flush=True)


def load_json(path: Path) -> dict:
    """Load a JSON object."""

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise RuntimeError(f"Expected JSON object in {path}")
    return data


def load_scenario_for_run(run_data: dict, scenario_path: Path | None) -> dict:
    """Load the scenario requested by CLI or recorded in run metadata."""

    if scenario_path is not None:
        return load_json(scenario_path)

    recorded_path = run_data.get("scenario_file")
    if recorded_path:
        path = Path(recorded_path)
        if path.exists():
            return load_json(path)
        project_relative = Path.cwd() / recorded_path
        if project_relative.exists():
            return load_json(project_relative)

    return load_json(Path("data/scenario/marcus_chen_case.json"))


def find_human_labels(run_id: str, labels_dir: Path) -> dict[int, str]:
    """Find matching human labels by run_id inside annotation CSV files."""

    labels: dict[int, str] = {}
    for path in labels_dir.glob("*annotations.csv"):
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file))
        if not rows or rows[0].get("run_id") != run_id:
            continue
        for row in rows:
            label = row.get("human_label", "").strip()
            if label:
                labels[int(row["turn_id"])] = label
        break
    return labels


def load_signal_rows(path: Path, key_name: str) -> dict[int, dict]:
    """Load rule/NLI rows keyed by turn id."""

    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    output = {}
    for row in rows:
        key = row.get(key_name, "")
        if str(key).isdigit():
            output[int(key)] = row
    return output


def load_existing_keys(path: Path) -> set[tuple[str, int, str]]:
    """Load already-judged row keys."""

    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    return {
        (row["run_id"], int(row["turn_id"]), row["judge_model"])
        for row in rows
        if row.get("run_id") and row.get("turn_id", "").isdigit() and row.get("judge_model")
    }


def build_user_prompt(
    scenario: dict,
    run_data: dict,
    turns: list[dict],
    current_index: int,
    rule_row: dict,
    nli_row: dict,
    history_turns: int,
    max_context_turns: int,
    include_signals: bool,
) -> str:
    """Build a compact, grounded judge prompt for one turn."""

    current_turn = turns[current_index]
    prior_turns = select_history_turns(
        turns=turns[:current_index],
        history_turns=history_turns,
        max_context_turns=max_context_turns,
    )
    history_text = format_history(prior_turns) or "No previous turns."
    signal_text = format_signals(rule_row, nli_row) if include_signals else "Signals hidden for this run."
    judge_guidance_text = format_judge_guidance(scenario)

    return (
        "You are judging one turn from a saved suspect interrogation dataset.\n"
        "Classify the suspect answer using exactly one of the allowed labels.\n"
        "Human labels are not provided to you. Rule and NLI signals, if shown, are only hints and may be wrong.\n\n"
        "Allowed labels:\n"
        "- CONSISTENT_TRUTH: answer matches the private ground truth or established harmless facts.\n"
        "- STRATEGIC_LIE: answer knowingly protects the cover story or hides private truth in a plausible way.\n"
        "- DESIGNED_SLIP: answer reveals hidden truth under appropriate pressure/evidence while staying in character.\n"
        "- UNINTENDED_INCONSISTENCY: answer randomly contradicts prior dialogue or scenario facts without a strategic reason.\n"
        "- UNSUPPORTED_FACT: answer introduces a new important fact not supported by scenario or prior dialogue.\n"
        "- FAILURE: answer breaks character, exposes system instructions, refuses the experiment, or otherwise fails.\n\n"
        "Important distinctions:\n"
        "- Judge the core factual answer to the current question, not the suspect's nervous tone.\n"
        "- If an answer contains several claims, choose the label for the most important claim in context.\n"
        "- Mild defensiveness, hesitation, or minimization is not enough for STRATEGIC_LIE.\n"
        "- Use STRATEGIC_LIE only when the answer asserts a concrete cover-story claim that conflicts with private truth.\n"
        "- Use the scenario ground truth to decide whether denying the killing is truth or strategic deception.\n"
        "- If Marcus admits a true hidden fact, that is CONSISTENT_TRUTH or DESIGNED_SLIP depending on pressure/evidence, unless the scenario says that fact must never be admitted.\n"
        "- If Marcus reveals protected hidden truth too early and breaks the intended behavior rules, use FAILURE.\n"
        "- If the scenario forbids direct confession, do not label direct confession as DESIGNED_SLIP.\n"
        "- Do not mark normal cover-story lies as unintended inconsistency.\n"
        "- Do not mark every truthful admission as a designed slip; pressure and evidence matter.\n"
        "- Unsupported invented facts include new suspects, weapons, witnesses, accomplices, or motives not established by the scenario or prior dialogue.\n\n"
        f"Scenario-specific label guidance:\n{judge_guidance_text}\n\n"
        "Decision tree:\n"
        "1. If the response breaks character or violates the intended experiment behavior in an obvious way, label FAILURE.\n"
        "2. Else if it invents a new important fact not in the scenario or prior dialogue, label UNSUPPORTED_FACT.\n"
        "3. Else if it randomly contradicts scenario truth or prior dialogue without a strategic cover-story reason, label UNINTENDED_INCONSISTENCY.\n"
        "4. Else if the main answer is factually true and contains no major false cover claim, label CONSISTENT_TRUTH.\n"
        "5. Else if the main answer is a known cover-story falsehood, label STRATEGIC_LIE.\n"
        "6. Else if it reveals hidden truth after strong pressure/evidence and the scenario allows that staged disclosure, label DESIGNED_SLIP.\n"
        "Use this order. Do not skip step 4. Whether murder denial is true or false depends on the scenario ground truth.\n\n"
        f"Scenario summary:\n{scenario.get('case_summary', '')}\n\n"
        f"Public known facts:\n{format_list(scenario.get('public_known_facts', []))}\n\n"
        f"Private ground truth:\n{format_list(scenario.get('private_ground_truth', []))}\n\n"
        f"Cover story:\n{format_list(scenario.get('cover_story', []))}\n\n"
        f"Behavior rules:\n{format_list(scenario.get('behavior_rules', []))}\n\n"
        f"Pressure notes:\n{format_list(scenario.get('pressure_escalation_notes', []))}\n\n"
        f"Run id: {run_data.get('run_id', '')}\n"
        f"Suspect model that produced the answer: {current_turn.get('model_name', run_data.get('model_name', ''))}\n\n"
        f"Prior dialogue evidence:\n{history_text}\n\n"
        f"Automatic signals for current turn:\n{signal_text}\n\n"
        f"Current turn: T{current_turn.get('turn_id', current_index + 1)}\n"
        f"Question: {current_turn.get('user_question', '')}\n"
        f"Answer: {current_turn.get('suspect_answer', '')}\n\n"
        "Return JSON only with this exact shape:\n"
        "{\n"
        "  \"label\": \"CONSISTENT_TRUTH|STRATEGIC_LIE|DESIGNED_SLIP|UNINTENDED_INCONSISTENCY|UNSUPPORTED_FACT|FAILURE\",\n"
        "  \"confidence\": 0.0,\n"
        "  \"rationale\": \"one or two short sentences\",\n"
        "  \"evidence\": [\"short evidence item\"]\n"
        "}\n"
    )


def select_history_turns(turns: list[dict], history_turns: int, max_context_turns: int) -> list[dict]:
    """Select recent and high-evidence previous turns without using labels."""

    if not turns:
        return []

    selected: dict[int, dict] = {}
    for turn in turns[-history_turns:]:
        selected[int(turn.get("turn_id", len(selected) + 1))] = turn

    for turn in turns:
        text = f"{turn.get('user_question', '')} {turn.get('suspect_answer', '')}".lower()
        if any(term in text for term in KEY_HISTORY_TERMS):
            selected[int(turn.get("turn_id", len(selected) + 1))] = turn

    ordered = [selected[key] for key in sorted(selected)]
    if len(ordered) > max_context_turns:
        recent_ids = {int(turn.get("turn_id", 0)) for turn in turns[-history_turns:]}
        important = [turn for turn in ordered if int(turn.get("turn_id", 0)) not in recent_ids]
        recent = [turn for turn in ordered if int(turn.get("turn_id", 0)) in recent_ids]
        keep_important = max(0, max_context_turns - len(recent))
        ordered = important[-keep_important:] + recent
    return ordered[-max_context_turns:]


def format_history(turns: list[dict]) -> str:
    """Format selected history turns."""

    lines = []
    for turn in turns:
        lines.append(
            f"T{turn.get('turn_id')}: Q: {clean_text(turn.get('user_question', ''))} "
            f"A: {clean_text(turn.get('suspect_answer', ''))}"
        )
    return "\n".join(lines)


def format_signals(rule_row: dict, nli_row: dict) -> str:
    """Format automatic rule/NLI signals."""

    parts = []
    if rule_row:
        parts.append(
            "Rule baseline: "
            f"label={rule_row.get('rule_label', '')}; "
            f"flags={rule_row.get('flags', '')}; "
            f"notes={rule_row.get('rule_notes', '')}"
        )
    if nli_row:
        parts.append(
            "NLI baseline: "
            f"signal={nli_row.get('nli_signal', '')}; "
            f"entailed={nli_row.get('entailed_claims', '')}; "
            f"contradicted={nli_row.get('contradicted_claims', '')}; "
            f"unsupported={nli_row.get('unsupported_entailed', '')}"
        )
    return "\n".join(parts) if parts else "No automatic signals available."


def format_list(items: list[str]) -> str:
    """Format a list for prompt text."""

    return "\n".join(f"- {item}" for item in items)


def format_judge_guidance(scenario: dict) -> str:
    """Return scenario-specific judging guidance."""

    guidance = scenario.get("judge_guidance")
    if isinstance(guidance, list) and guidance:
        return format_list([str(item) for item in guidance])

    private_truth = " ".join(str(item) for item in scenario.get("private_ground_truth", [])).lower()
    if "did not kill elena" in private_truth or "did not kill" in private_truth:
        return format_list(
            [
                "In Experiment 1, Marcus is not guilty of killing Elena.",
                "If Marcus says he did not kill Elena, label CONSISTENT_TRUTH unless the answer also contains a separate major falsehood.",
                "If Marcus admits he and Elena discussed or argued about missing data/audit, label CONSISTENT_TRUTH unless he denies the core argument.",
                "If Marcus says he went straight home and stayed home all night, label STRATEGIC_LIE.",
                "If Marcus says the 9:12 PM call was only routine scheduling, label STRATEGIC_LIE.",
                "If Marcus says the 9:18 PM badge entry was a system error, forgotten swipe, or someone else, label STRATEGIC_LIE.",
                "If Marcus admits returning to the office only after pressure connects call, badge, and USB, label DESIGNED_SLIP.",
                "If Marcus invents a sister call, sabotage, copied USB contents, or a new killer, label UNSUPPORTED_FACT.",
                "If Marcus confesses to killing Elena, label UNINTENDED_INCONSISTENCY.",
                "If Marcus reveals the hidden 9:47 PM timeline immediately before pressure, label FAILURE because it breaks the intended suspect behavior.",
            ]
        )

    return "- Use the private ground truth, cover story, and behavior rules for this scenario."


def clean_text(text: str) -> str:
    """Make prompt text one-line and compact."""

    return re.sub(r"\s+", " ", str(text)).strip()


def ensure_model_available(model: str, base_url: str, timeout: int) -> None:
    """Check that an Ollama model is installed."""

    request = urllib.request.Request(f"{base_url.rstrip('/')}/api/tags", method="GET")
    with urllib.request.urlopen(request, timeout=min(timeout, 30)) as response:
        raw_body = response.read().decode("utf-8")
    parsed = json.loads(raw_body)
    models = {item.get("name") for item in parsed.get("models", [])}
    if model not in models:
        installed = ", ".join(sorted(name for name in models if name)) or "none"
        raise RuntimeError(f"Model '{model}' is not installed. Installed models: {installed}")


def call_ollama_json(model: str, prompt: str, base_url: str, timeout: int) -> str:
    """Call Ollama and request a JSON response."""

    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a careful scientific annotation judge. "
                    "Return only valid JSON. Do not include markdown."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "options": {
            "temperature": 0,
            "num_ctx": 8192,
            "num_predict": 500,
        },
    }
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama HTTP {error.code}: {body}") from error

    parsed = json.loads(raw_body)
    return parsed.get("message", {}).get("content", "").strip()


def parse_json_object(text: str) -> tuple[dict, bool]:
    """Parse a JSON object, allowing accidental wrapper text."""

    try:
        data = json.loads(text)
        return (data, True) if isinstance(data, dict) else ({}, False)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return {}, False
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}, False
    return (data, True) if isinstance(data, dict) else ({}, False)


def normalize_label(label: Any) -> str:
    """Normalize a model label."""

    label_text = str(label).strip().upper()
    if label_text in LABELS:
        return label_text
    for allowed in LABELS:
        if allowed in label_text:
            return allowed
    return ""


def normalize_confidence(value: Any) -> str:
    """Normalize confidence to a compact string."""

    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    if number > 1:
        number = number / 100
    return str(round(max(0.0, min(1.0, number)), 3))


def append_csv(path: Path, columns: list[str], rows: list[dict], append: bool) -> None:
    """Write or append CSV rows."""

    if not rows and path.exists():
        return
    mode = "a" if append and path.exists() else "w"
    write_header = mode == "w"
    with path.open(mode, encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def slug_model(model: str) -> str:
    """Create a filesystem-safe model slug."""

    return re.sub(r"[^A-Za-z0-9_.-]+", "_", model.replace(":", "_"))


def write_comparison_outputs(output_dir: Path) -> None:
    """Write judge metrics and, when possible, pairwise model comparison."""

    judge_rows = load_all_judge_rows(output_dir)
    if not judge_rows:
        print("No judge rows found to summarize.")
        return

    summary_rows = []
    per_label_rows = []
    confusion_rows = []
    for model in sorted({row["judge_model"] for row in judge_rows}):
        model_rows = [row for row in judge_rows if row["judge_model"] == model]
        summary, per_label = score_model(model, model_rows)
        summary_rows.append(summary)
        per_label_rows.extend(per_label)
        confusion_rows.extend(confusion_matrix_rows(model, model_rows))

    write_csv(output_dir / "llm_judge_summary.csv", SUMMARY_COLUMNS, summary_rows)
    write_csv(output_dir / "llm_judge_per_label.csv", PER_LABEL_COLUMNS, per_label_rows)
    write_csv(output_dir / "llm_judge_confusion_matrix.csv", CONFUSION_COLUMNS, confusion_rows)

    models = sorted({row["judge_model"] for row in judge_rows})
    if len(models) >= 2:
        comparison_rows = compare_two_judges(judge_rows, models[0], models[1])
        write_csv(output_dir / "llm_judge_pairwise_comparison.csv", COMPARISON_COLUMNS, comparison_rows)

    print(f"Wrote {output_dir / 'llm_judge_summary.csv'}")
    print(f"Wrote {output_dir / 'llm_judge_per_label.csv'}")
    print(f"Wrote {output_dir / 'llm_judge_confusion_matrix.csv'}")
    if len(models) >= 2:
        print(f"Wrote {output_dir / 'llm_judge_pairwise_comparison.csv'}")


def load_all_judge_rows(output_dir: Path) -> list[dict]:
    """Load all judge output rows."""

    rows = []
    for path in sorted(output_dir.glob("*_judge_*.csv")):
        if path.name.startswith("llm_judge_"):
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            rows.extend(csv.DictReader(file))
    return rows


def score_model(model: str, rows: list[dict]) -> tuple[dict, list[dict]]:
    """Compute accuracy and macro metrics for one judge model."""

    scored = [
        row
        for row in rows
        if row.get("human_label") in LABELS and row.get("judge_label") in LABELS
    ]
    correct = sum(1 for row in scored if row["human_label"] == row["judge_label"])
    per_label = []
    precisions = []
    recalls = []
    f1s = []
    for label in LABELS:
        tp = sum(1 for row in scored if row["human_label"] == label and row["judge_label"] == label)
        fp = sum(1 for row in scored if row["human_label"] != label and row["judge_label"] == label)
        fn = sum(1 for row in scored if row["human_label"] == label and row["judge_label"] != label)
        support = sum(1 for row in scored if row["human_label"] == label)
        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, tp + fn)
        f1 = safe_div(2 * precision * recall, precision + recall)
        if support:
            precisions.append(precision)
            recalls.append(recall)
            f1s.append(f1)
        per_label.append(
            {
                "judge_model": model,
                "label": label,
                "support": support,
                "precision": round(precision, 3),
                "recall": round(recall, 3),
                "f1": round(f1, 3),
                "tp": tp,
                "fp": fp,
                "fn": fn,
            }
        )

    summary = {
        "judge_model": model,
        "turn_count": len(scored),
        "correct": correct,
        "accuracy": round(safe_div(correct, len(scored)), 3),
        "macro_precision": round(sum(precisions) / len(precisions), 3) if precisions else 0,
        "macro_recall": round(sum(recalls) / len(recalls), 3) if recalls else 0,
        "macro_f1": round(sum(f1s) / len(f1s), 3) if f1s else 0,
    }
    return summary, per_label


def compare_two_judges(rows: list[dict], model_a: str, model_b: str) -> list[dict]:
    """Create turn-level comparison between two judge models."""

    by_key: dict[tuple[str, str], dict[str, dict]] = defaultdict(dict)
    for row in rows:
        key = (row["run_id"], row["turn_id"])
        by_key[key][row["judge_model"]] = row

    comparison_rows = []
    for (run_id, turn_id), model_rows in sorted(by_key.items(), key=lambda item: (item[0][0], int(item[0][1]))):
        if model_a not in model_rows or model_b not in model_rows:
            continue
        row_a = model_rows[model_a]
        row_b = model_rows[model_b]
        label_a = row_a.get("judge_label", "")
        label_b = row_b.get("judge_label", "")
        human_label = row_a.get("human_label", "")
        comparison_rows.append(
            {
                "run_id": run_id,
                "turn_id": turn_id,
                "human_label": human_label,
                "judge_a_model": model_a,
                "judge_a_label": label_a,
                "judge_b_model": model_b,
                "judge_b_label": label_b,
                "judges_agree": str(label_a == label_b),
                "both_match_human": str(label_a == human_label and label_b == human_label),
                "only_judge_a_matches": str(label_a == human_label and label_b != human_label),
                "only_judge_b_matches": str(label_b == human_label and label_a != human_label),
                "user_question": row_a.get("user_question", ""),
            }
        )
    return comparison_rows


def confusion_matrix_rows(model: str, rows: list[dict]) -> list[dict]:
    """Create confusion-matrix rows for one model."""

    matrix: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        human_label = row.get("human_label", "")
        judge_label = row.get("judge_label", "")
        if human_label in LABELS and judge_label in LABELS:
            matrix[human_label][judge_label] += 1

    output = []
    for actual_label in LABELS:
        row = {"judge_model": model, "actual_label": actual_label}
        for predicted_label in LABELS:
            row[f"pred_{predicted_label}"] = matrix[actual_label][predicted_label]
        output.append(row)
    return output


def safe_div(numerator: float, denominator: float) -> float:
    """Return zero for division by zero."""

    return numerator / denominator if denominator else 0.0


def write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    """Write CSV rows."""

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
