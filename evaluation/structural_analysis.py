"""Structural analysis for interrogation logs.

This is the first automatic evaluation stage. It does not decide whether Marcus
is lying or inconsistent. It only describes what appears in each turn:
topics, key evidence mentions, pressure level, and answer length.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


TOPIC_KEYWORDS = {
    "alibi": ["where were you", "9:00", "10:30", "home", "alibi"],
    "timeline": ["when", "last see", "left", "8:30", "9:47", "that day"],
    "call": ["call", "9:12"],
    "badge": ["badge", "9:18"],
    "usb": ["usb", "drive"],
    "missing_data": ["missing data", "missing records", "trial data", "research data"],
    "motive": ["arguing", "argument", "disagreement", "audit", "conflict"],
    "accusation": ["kill", "killed", "murder", "admit", "suspicious"],
    "role": ["role", "company", "operations manager"],
}


KEY_FACTS = {
    "mentions_830": ["8:30"],
    "mentions_912": ["9:12"],
    "mentions_918": ["9:18"],
    "mentions_947": ["9:47"],
    "mentions_home": ["home", "apartment"],
    "mentions_badge": ["badge"],
    "mentions_usb": ["usb", "drive"],
    "mentions_missing_data": ["missing data", "missing records", "trial data", "research data"],
    "mentions_killing_denial": ["didn't kill", "did not kill", "not a killer", "didn't hurt"],
    "mentions_sabotage": ["sabotage"],
}


CSV_COLUMNS = [
    "run_id",
    "turn_id",
    "question_topic",
    "question_pressure_level",
    "question_evidence_count",
    "answer_word_count",
    "answer_key_facts",
    "selected_question_source",
    "user_question",
]


def main() -> None:
    """Run structural analysis for one run file."""

    parser = argparse.ArgumentParser(description="Analyze dialogue structure in a run JSON file.")
    parser.add_argument(
        "--run",
        required=True,
        help="Run JSON file to analyze, for example data/runs/2026-05-15T12-36-23.json.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="CSV output path. Defaults to data/results/<run_id>_structural.csv.",
    )
    args = parser.parse_args()

    run_path = Path(args.run)
    run_data = load_run(run_path)
    run_id = run_data.get("run_id", run_path.stem)

    output_path = Path(args.output) if args.output else Path("data/results") / f"{run_id}_structural.csv"
    summary_path = output_path.with_suffix(".summary.json")

    rows = [analyze_turn(run_id, turn) for turn in run_data.get("turns", [])]
    write_csv(output_path, rows)
    write_summary(summary_path, rows)

    print(f"Wrote structural turn analysis to {output_path}")
    print(f"Wrote structural summary to {summary_path}")


def load_run(path: Path) -> dict:
    """Load a saved run JSON file."""

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise RuntimeError(f"Expected a JSON object in {path}")

    return data


def analyze_turn(run_id: str, turn: dict) -> dict:
    """Return structural features for one turn."""

    question = turn.get("user_question", "")
    answer = turn.get("suspect_answer", "")
    combined_question = question.lower()

    topic = choose_topic(combined_question)
    pressure_level = estimate_pressure(combined_question)
    evidence_count = count_evidence_mentions(combined_question)
    key_facts = find_key_facts(answer.lower())

    return {
        "run_id": run_id,
        "turn_id": turn.get("turn_id", ""),
        "question_topic": topic,
        "question_pressure_level": pressure_level,
        "question_evidence_count": evidence_count,
        "answer_word_count": len(answer.split()),
        "answer_key_facts": " | ".join(key_facts),
        "selected_question_source": turn.get("selected_question_source", ""),
        "user_question": question,
    }


def choose_topic(question: str) -> str:
    """Pick the first matching topic for a question."""

    scores: Counter[str] = Counter()
    for topic, keywords in TOPIC_KEYWORDS.items():
        for keyword in keywords:
            if keyword in question:
                scores[topic] += 1

    if not scores:
        return "other"

    return scores.most_common(1)[0][0]


def estimate_pressure(question: str) -> str:
    """Estimate how confrontational the user question is."""

    high_pressure_terms = ["admit", "kill", "killed", "suspicious", "you lied", "what are you leaving out"]
    medium_pressure_terms = ["explain", "how come", "why", "missing", "badge", "call"]

    if any(term in question for term in high_pressure_terms):
        return "high"
    if any(term in question for term in medium_pressure_terms):
        return "medium"
    return "low"


def count_evidence_mentions(question: str) -> int:
    """Count how many major evidence categories appear in the question."""

    evidence_categories = [
        ["call", "9:12"],
        ["badge", "9:18"],
        ["usb", "drive"],
        ["missing data", "missing records", "trial data"],
        ["9:47", "8:30"],
    ]

    count = 0
    for keywords in evidence_categories:
        if any(keyword in question for keyword in keywords):
            count += 1

    return count


def find_key_facts(answer: str) -> list[str]:
    """Find important evidence mentions in the suspect answer."""

    found = []
    for fact_name, keywords in KEY_FACTS.items():
        if any(keyword in answer for keyword in keywords):
            found.append(fact_name)

    return found


def write_csv(output_path: Path, rows: list[dict]) -> None:
    """Write structural features to CSV."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(summary_path: Path, rows: list[dict]) -> None:
    """Write simple aggregate counts as JSON."""

    summary = {
        "turn_count": len(rows),
        "topic_counts": dict(Counter(row["question_topic"] for row in rows)),
        "pressure_counts": dict(Counter(row["question_pressure_level"] for row in rows)),
        "question_source_counts": dict(Counter(row["selected_question_source"] for row in rows)),
        "key_fact_counts": count_key_facts(rows),
    }

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)


def count_key_facts(rows: list[dict]) -> dict:
    """Count how often each key fact appears in suspect answers."""

    counts: Counter[str] = Counter()
    for row in rows:
        for fact in row["answer_key_facts"].split(" | "):
            if fact:
                counts[fact] += 1

    return dict(counts)


if __name__ == "__main__":
    main()
