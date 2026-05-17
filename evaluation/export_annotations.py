"""Export interrogation run logs into a human annotation CSV.

This script is intentionally simple:
    - input: JSON run files saved by the terminal app
    - output: one CSV file that can be opened in Excel, Google Sheets, or VS Code

The runtime does not auto-label turns. A human annotator fills the empty
human_label and human_notes columns after reading each question/answer pair.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


LABELS = [
    "CONSISTENT_TRUTH",
    "STRATEGIC_LIE",
    "DESIGNED_SLIP",
    "UNINTENDED_INCONSISTENCY",
    "UNSUPPORTED_FACT",
    "FAILURE",
]


CSV_COLUMNS = [
    "run_id",
    "turn_id",
    "timestamp",
    "suspect_name",
    "model_name",
    "selected_question_source",
    "suggested_questions",
    "user_question",
    "suspect_answer",
    "human_label",
    "human_notes",
    "judge_label",
    "judge_confidence",
    "judge_notes",
]


def main() -> None:
    """Read run JSON files and write an annotation template."""

    parser = argparse.ArgumentParser(
        description="Export interrogation JSON logs into an annotation CSV."
    )
    parser.add_argument(
        "--runs-dir",
        default="data/runs",
        help="Directory containing saved run JSON files.",
    )
    parser.add_argument(
        "--output",
        default="data/labeled/annotation_template.csv",
        help="CSV file to create.",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Optional single run_id to export, for example 2026-05-15T12-36-23.",
    )
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    output_path = Path(args.output)

    rows = collect_rows(runs_dir=runs_dir, run_id=args.run_id)
    write_csv(output_path=output_path, rows=rows)

    print(f"Exported {len(rows)} turn(s) to {output_path}")
    print("Fill the human_label and human_notes columns during annotation.")
    print("Allowed labels: " + ", ".join(LABELS))


def collect_rows(runs_dir: Path, run_id: str | None = None) -> list[dict]:
    """Convert run JSON files into CSV row dictionaries."""

    if not runs_dir.exists():
        raise RuntimeError(f"Runs directory does not exist: {runs_dir}")

    run_files = sorted(runs_dir.glob("*.json"))
    if run_id:
        run_files = [path for path in run_files if path.stem == run_id]
        if not run_files:
            raise RuntimeError(f"No run file found for run_id: {run_id}")

    rows: list[dict] = []
    for run_path in run_files:
        run_data = load_run(run_path)
        for turn in run_data.get("turns", []):
            rows.append(build_row(run_data=run_data, turn=turn))

    return rows


def load_run(path: Path) -> dict:
    """Load one run JSON file and make sure it has the expected shape."""

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Invalid JSON in {path}: {error}") from error

    if not isinstance(data, dict):
        raise RuntimeError(f"Expected a JSON object in {path}")

    turns = data.get("turns", [])
    if not isinstance(turns, list):
        raise RuntimeError(f"Expected 'turns' to be a list in {path}")

    return data


def build_row(run_data: dict, turn: dict) -> dict:
    """Build one annotation row from one dialogue turn."""

    suggestions = turn.get("suggested_questions", [])
    if isinstance(suggestions, list):
        suggestions_text = " | ".join(str(question) for question in suggestions)
    else:
        suggestions_text = str(suggestions)

    return {
        "run_id": turn.get("run_id", run_data.get("run_id", "")),
        "turn_id": turn.get("turn_id", ""),
        "timestamp": turn.get("timestamp", ""),
        "suspect_name": turn.get("suspect_name", run_data.get("suspect_name", "")),
        "model_name": turn.get("model_name", run_data.get("model_name", "")),
        "selected_question_source": turn.get("selected_question_source", ""),
        "suggested_questions": suggestions_text,
        "user_question": turn.get("user_question", ""),
        "suspect_answer": turn.get("suspect_answer", ""),
        "human_label": "",
        "human_notes": "",
        "judge_label": "",
        "judge_confidence": "",
        "judge_notes": "",
    }


def write_csv(output_path: Path, rows: list[dict]) -> None:
    """Write rows to CSV, creating the output directory if needed."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
