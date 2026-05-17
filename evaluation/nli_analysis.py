"""NLI-style analysis for interrogation turns.

This stage compares each suspect answer against fixed atomic claims and outputs
ENTAILMENT, CONTRADICTION, or NEUTRAL. It does not decide whether a contradiction
is strategic or accidental. That interpretation happens later by comparing NLI
signals against human labels, pressure, and dialogue history.

Claims can define evidence_terms. When enabled, the relevance filter keeps a
claim NEUTRAL unless the answer actually touches that claim's topic. This
reduces high-confidence NLI guesses on unrelated facts.

Backends:
    - transformers: uses a local HuggingFace MNLI/NLI model.
    - ollama: asks the local Ollama model to act only as an NLI classifier.
    - heuristic: lightweight keyword fallback for fast dry runs.
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


NLI_LABELS = {"ENTAILMENT", "CONTRADICTION", "NEUTRAL"}


DETAIL_COLUMNS = [
    "run_id",
    "turn_id",
    "experiment_id",
    "protocol_id",
    "case_id",
    "scenario_version",
    "claim_id",
    "claim_type",
    "claim_text",
    "nli_label",
    "nli_confidence",
    "nli_reason",
    "human_label",
    "user_question",
    "suspect_answer",
]


TURN_COLUMNS = [
    "run_id",
    "turn_id",
    "experiment_id",
    "protocol_id",
    "case_id",
    "scenario_version",
    "human_label",
    "entailed_claims",
    "contradicted_claims",
    "unsupported_entailed",
    "cross_turn_changes",
    "nli_signal",
    "user_question",
]


def main() -> None:
    """Run NLI analysis for one run or all run files."""

    parser = argparse.ArgumentParser(description="Run NLI-style claim analysis.")
    parser.add_argument("--run", default=None, help="One run JSON file to analyze.")
    parser.add_argument("--runs-dir", default="data/runs", help="Directory of run JSON files.")
    parser.add_argument("--claims", default="evaluation/nli_claims.json", help="Canonical claims JSON.")
    parser.add_argument("--labels-dir", default="data/labeled", help="Directory of human annotation CSV files.")
    parser.add_argument("--output-dir", default="data/results", help="Directory for NLI outputs.")
    parser.add_argument("--backend", choices=["transformers", "ollama", "heuristic"], default="transformers")
    parser.add_argument("--model", default=os.getenv("OLLAMA_MODEL", "llama3.1:8b"))
    parser.add_argument(
        "--nli-model",
        default=os.getenv("NLI_MODEL", "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"),
        help="HuggingFace NLI model used by the transformers backend.",
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=float(os.getenv("NLI_CONFIDENCE_THRESHOLD", "0.75")),
        help="Transformers predictions below this confidence become NEUTRAL.",
    )
    parser.add_argument("--base-url", default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    parser.add_argument("--sleep", type=float, default=0.0, help="Optional delay between Ollama calls.")
    parser.add_argument("--limit-turns", type=int, default=None, help="Debug limit per run.")
    parser.add_argument(
        "--no-relevance-filter",
        action="store_true",
        help="Disable evidence_terms filtering and classify every claim for every answer.",
    )
    args = parser.parse_args()

    claims = load_claims(Path(args.claims))
    run_paths = [Path(args.run)] if args.run else sorted(Path(args.runs_dir).glob("*.json"))
    run_paths = [path for path in run_paths if path.name != "2026-05-08T22-45-52.json"]

    backend = build_backend(args)

    for run_path in run_paths:
        run_data = load_json(run_path)
        run_id = run_data.get("run_id", run_path.stem)
        human_labels = find_human_labels(run_id=run_id, labels_dir=Path(args.labels_dir))

        turns = run_data.get("turns", [])
        if args.limit_turns is not None:
            turns = turns[: args.limit_turns]

        print(f"Analyzing {run_id}: {len(turns)} turn(s), backend={args.backend}")
        detail_rows = analyze_turns(
            run_id=run_id,
            turns=turns,
            claims=claims,
            human_labels=human_labels,
            backend=backend,
            sleep_seconds=args.sleep,
            use_relevance_filter=not args.no_relevance_filter,
        )
        turn_rows = summarize_turns(detail_rows)

        output_dir = Path(args.output_dir)
        detail_path = output_dir / f"{run_id}_nli.csv"
        turn_path = output_dir / f"{run_id}_nli_turns.csv"
        summary_path = output_dir / f"{run_id}_nli.summary.json"

        write_csv(detail_path, DETAIL_COLUMNS, detail_rows)
        write_csv(turn_path, TURN_COLUMNS, turn_rows)
        write_summary(summary_path, detail_rows, turn_rows)

        print(f"Wrote {detail_path}")
        print(f"Wrote {turn_path}")
        print(f"Wrote {summary_path}")


def load_claims(path: Path) -> list[dict]:
    """Load canonical NLI claims."""

    data = load_json(path)
    claims = data.get("claims", [])
    if not isinstance(claims, list) or not claims:
        raise RuntimeError(f"Expected non-empty 'claims' list in {path}")
    return claims


def load_json(path: Path) -> dict:
    """Load a JSON object from disk."""

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise RuntimeError(f"Expected JSON object in {path}")
    return data


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


def build_backend(args: argparse.Namespace):
    """Create the requested NLI backend."""

    if args.backend == "heuristic":
        return HeuristicNLIBackend()
    if args.backend == "transformers":
        return TransformersNLIBackend(
            model_name=args.nli_model,
            confidence_threshold=args.confidence_threshold,
        )
    return OllamaNLIBackend(model=args.model, base_url=args.base_url)


def analyze_turns(
    run_id: str,
    turns: list[dict],
    claims: list[dict],
    human_labels: dict[int, str],
    backend: Any,
    sleep_seconds: float,
    use_relevance_filter: bool,
) -> list[dict]:
    """Classify every turn answer against every canonical claim."""

    detail_rows: list[dict] = []
    for index, turn in enumerate(turns, start=1):
        answer = turn.get("suspect_answer", "")
        relevant_claims = filter_relevant_claims(answer, claims) if use_relevance_filter else claims
        relevant_claim_ids = {claim["id"] for claim in relevant_claims}
        results = backend.classify(premise=answer, claims=relevant_claims) if relevant_claims else {}
        turn_id = int(turn.get("turn_id", index))
        human_label = human_labels.get(turn_id, "")

        for claim in claims:
            if use_relevance_filter and claim["id"] not in relevant_claim_ids:
                result = normalize_result(
                    {
                        "label": "NEUTRAL",
                        "confidence": "",
                        "reason": "relevance_filter:no_matching_terms",
                    }
                )
            else:
                result = normalize_result(results.get(claim["id"], {}))
            detail_rows.append(
                {
                    "run_id": run_id,
                    "turn_id": turn_id,
                    "experiment_id": turn.get("experiment_id", ""),
                    "protocol_id": turn.get("protocol_id", ""),
                    "case_id": turn.get("case_id", ""),
                    "scenario_version": turn.get("scenario_version", ""),
                    "claim_id": claim["id"],
                    "claim_type": claim.get("claim_type", ""),
                    "claim_text": claim["text"],
                    "nli_label": result["label"],
                    "nli_confidence": result["confidence"],
                    "nli_reason": result["reason"],
                    "human_label": human_label,
                    "user_question": turn.get("user_question", ""),
                    "suspect_answer": answer,
                }
            )

        if sleep_seconds:
            time.sleep(sleep_seconds)

    return detail_rows


def filter_relevant_claims(premise: str, claims: list[dict]) -> list[dict]:
    """Keep only claims whose evidence terms appear in the answer."""

    return [claim for claim in claims if is_claim_relevant(premise, claim)]


def is_claim_relevant(premise: str, claim: dict) -> bool:
    """Return whether a claim should be checked against this answer."""

    terms = claim.get("evidence_terms", [])
    if not terms:
        return True

    text = premise.lower()
    return any(contains_evidence_term(text, str(term).lower()) for term in terms)


def contains_evidence_term(text: str, term: str) -> bool:
    """Match single-word evidence terms as words and phrases as substrings."""

    if re.fullmatch(r"[a-z0-9_]+", term):
        return bool(re.search(rf"\b{re.escape(term)}\b", text))
    return term in text


def normalize_result(result: dict) -> dict:
    """Clean one backend result."""

    label = str(result.get("label", "NEUTRAL")).upper()
    if label not in NLI_LABELS:
        label = "NEUTRAL"

    confidence = result.get("confidence", "")
    if isinstance(confidence, (int, float)):
        confidence = round(float(confidence), 3)
    else:
        confidence = ""

    return {
        "label": label,
        "confidence": confidence,
        "reason": str(result.get("reason", "")),
    }


def summarize_turns(detail_rows: list[dict]) -> list[dict]:
    """Create one summary row per turn and detect claim-level flips."""

    rows_by_turn: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for row in detail_rows:
        rows_by_turn[(row["run_id"], int(row["turn_id"]))].append(row)

    previous_labels: dict[str, str] = {}
    turn_rows: list[dict] = []

    for key in sorted(rows_by_turn, key=lambda item: (item[0], item[1])):
        run_id, turn_id = key
        rows = rows_by_turn[key]
        entailed = [row["claim_id"] for row in rows if row["nli_label"] == "ENTAILMENT"]
        contradicted = [row["claim_id"] for row in rows if row["nli_label"] == "CONTRADICTION"]
        unsupported_entailed = [
            row["claim_id"]
            for row in rows
            if row["claim_type"] in {"unsupported", "unsupported_fact"} and row["nli_label"] == "ENTAILMENT"
        ]

        changes = []
        for row in rows:
            claim_id = row["claim_id"]
            label = row["nli_label"]
            previous = previous_labels.get(claim_id)
            if previous and is_flip(previous, label):
                changes.append(f"{claim_id}:{previous}->{label}")
            if label in {"ENTAILMENT", "CONTRADICTION"}:
                previous_labels[claim_id] = label

        nli_signal = choose_signal(entailed, contradicted, unsupported_entailed, changes)
        first = rows[0]
        turn_rows.append(
            {
                "run_id": run_id,
                "turn_id": turn_id,
                "experiment_id": first.get("experiment_id", ""),
                "protocol_id": first.get("protocol_id", ""),
                "case_id": first.get("case_id", ""),
                "scenario_version": first.get("scenario_version", ""),
                "human_label": first["human_label"],
                "entailed_claims": " | ".join(entailed),
                "contradicted_claims": " | ".join(contradicted),
                "unsupported_entailed": " | ".join(unsupported_entailed),
                "cross_turn_changes": " | ".join(changes),
                "nli_signal": nli_signal,
                "user_question": first["user_question"],
            }
        )

    return turn_rows


def is_flip(previous: str, current: str) -> bool:
    """Detect a claim changing from support to contradiction or back."""

    return {previous, current} == {"ENTAILMENT", "CONTRADICTION"}


def choose_signal(
    entailed: list[str],
    contradicted: list[str],
    unsupported_entailed: list[str],
    changes: list[str],
) -> str:
    """Create a coarse turn-level NLI signal."""

    if unsupported_entailed:
        return "UNSUPPORTED_CLAIM_ENTAILED"
    if changes:
        return "CROSS_TURN_FLIP"
    if any(claim.startswith("cover_") for claim in entailed):
        return "COVER_STORY_SUPPORTED"
    if any(claim.startswith("truth_") for claim in entailed):
        return "GROUND_TRUTH_SUPPORTED"
    if any(claim.startswith("truth_") for claim in contradicted):
        return "GROUND_TRUTH_CONTRADICTED"
    return "NO_STRONG_SIGNAL"


def write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    """Write CSV rows."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(path: Path, detail_rows: list[dict], turn_rows: list[dict]) -> None:
    """Write aggregate NLI counts."""

    summary = {
        "turn_count": len(turn_rows),
        "claim_pair_count": len(detail_rows),
        "nli_label_counts": dict(Counter(row["nli_label"] for row in detail_rows)),
        "turn_signal_counts": dict(Counter(row["nli_signal"] for row in turn_rows)),
        "human_label_counts": dict(Counter(row["human_label"] for row in turn_rows if row["human_label"])),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)


class OllamaNLIBackend:
    """Ollama-backed tri-label NLI classifier."""

    def __init__(self, model: str, base_url: str) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")

    def classify(self, premise: str, claims: list[dict]) -> dict[str, dict]:
        """Classify all claims for one premise in a single Ollama call."""

        prompt = build_ollama_prompt(premise=premise, claims=claims)
        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a Natural Language Inference classifier. "
                        "You only classify the relation between a premise and each hypothesis. "
                        "Use exactly ENTAILMENT, CONTRADICTION, or NEUTRAL. "
                        "Do not judge intention, guilt, deception, or morality."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "options": {
                "temperature": 0,
                "num_predict": 1200,
            },
        }
        raw_content = self._chat(payload)
        parsed = parse_json_object(raw_content)
        results = parsed.get("results", parsed)

        output: dict[str, dict] = {}
        if isinstance(results, list):
            for item in results:
                if isinstance(item, dict) and item.get("claim_id"):
                    output[str(item["claim_id"])] = item
        elif isinstance(results, dict):
            output = {str(key): value for key, value in results.items() if isinstance(value, dict)}

        return output

    def _chat(self, payload: dict) -> str:
        """Send one chat request to Ollama."""

        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=240) as response:
                raw_body = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ollama HTTP {error.code}: {body}") from error

        data = json.loads(raw_body)
        return data.get("message", {}).get("content", "")


def build_ollama_prompt(premise: str, claims: list[dict]) -> str:
    """Build a compact NLI prompt for one answer."""

    claim_lines = "\n".join(f"- {claim['id']}: {claim['text']}" for claim in claims)
    return (
        "Premise, which is one suspect answer:\n"
        f"{premise}\n\n"
        "Hypotheses:\n"
        f"{claim_lines}\n\n"
        "Return JSON only in this shape:\n"
        "{\"results\":[{\"claim_id\":\"...\",\"label\":\"ENTAILMENT|CONTRADICTION|NEUTRAL\","
        "\"confidence\":0.0,\"reason\":\"short reason\"}]}\n"
        "Use CONTRADICTION only when the premise clearly conflicts with the hypothesis. "
        "Use ENTAILMENT only when the premise clearly supports the hypothesis. "
        "Use NEUTRAL when the premise does not decide it."
    )


def parse_json_object(text: str) -> dict:
    """Parse a JSON object, allowing small amounts of accidental wrapper text."""

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return {}

    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}

    return data if isinstance(data, dict) else {}


class HeuristicNLIBackend:
    """Fast fallback that approximates claim relations with keywords.

    This backend is only for dry runs and debugging the pipeline shape. It is
    not a replacement for the Ollama NLI backend in the report.
    """

    def classify(self, premise: str, claims: list[dict]) -> dict[str, dict]:
        text = premise.lower()
        return {claim["id"]: self.classify_claim(text, claim) for claim in claims}

    def classify_claim(self, text: str, claim: dict) -> dict:
        """Classify one claim using transparent keywords."""

        claim_id = claim["id"]
        label = "NEUTRAL"
        reason = "No heuristic evidence."

        if claim_id == "cover_home_all_night":
            if has_any(text, ["went straight home", "was at home", "stayed home", "stayed there", "my apartment"]):
                label, reason = "ENTAILMENT", "Home alibi phrase found."
            if has_any(text, ["returned to the office", "went back to the office", "back at the office"]):
                label, reason = "CONTRADICTION", "Return-to-office phrase found."
        elif claim_id == "truth_returned_918":
            if has_any(text, ["returned to the office", "went back to the office", "back at the office", "9:18"]):
                label, reason = "ENTAILMENT", "Return or 9:18 phrase found."
            if has_any(text, ["didn't go back", "did not go back", "not physically inside the office"]):
                label, reason = "CONTRADICTION", "Explicit denial of return found."
        elif claim_id == "truth_last_seen_947":
            if "9:47" in text:
                label, reason = "ENTAILMENT", "9:47 phrase found."
            if has_any(text, ["8:30 pm", "8:30"]) and "last saw" in text:
                label, reason = "CONTRADICTION", "Last-seen at 8:30 phrase found."
        elif claim_id == "truth_call_missing_data":
            if has_any(text, ["missing trial data", "missing data", "audit"]):
                label, reason = "ENTAILMENT", "Missing-data/audit phrase found."
        elif claim_id == "cover_call_scheduling":
            if has_any(text, ["scheduling", "meeting time", "next-day"]):
                label, reason = "ENTAILMENT", "Scheduling phrase found."
            if has_any(text, ["missing trial data", "audit", "confront"]):
                label, reason = "CONTRADICTION", "Call conflict phrase found."
        elif claim_id == "truth_badge_marcus":
            if has_any(text, ["my badge was used", "i was back at the office", "9:18"]):
                label, reason = "ENTAILMENT", "Badge/return phrase found."
        elif claim_id == "cover_badge_error":
            if has_any(text, ["system error", "glitch", "someone else", "borrowed my badge", "forgotten to swipe"]):
                label, reason = "ENTAILMENT", "Badge excuse phrase found."
        elif claim_id == "truth_took_usb":
            if has_any(text, ["i took the usb", "took the usb drive", "i might have taken that usb"]):
                label, reason = "ENTAILMENT", "USB admission phrase found."
            if has_any(text, ["i didn't take", "i did not take"]) and "usb" in text:
                label, reason = "CONTRADICTION", "USB denial phrase found."
        elif claim_id == "truth_usb_missing_data":
            if "usb" in text and has_any(text, ["missing trial data", "missing data", "research data"]):
                label, reason = "ENTAILMENT", "USB and missing-data phrase found."
        elif claim_id == "truth_not_killer":
            if has_any(text, ["didn't kill", "did not kill", "not a killer", "didn't hurt", "of course not"]):
                label, reason = "ENTAILMENT", "Murder denial phrase found."
        elif claim_id == "truth_argued_missing_data":
            if has_any(text, ["argued", "argument", "heated conversation", "disagreement"]) and has_any(text, ["missing data", "trial data", "audit"]):
                label, reason = "ENTAILMENT", "Argument and data/audit phrases found."
        elif claim_id == "unsupported_sabotage":
            if has_any(text, ["sabotage", "changing company data", "falsified", "cover my tracks"]):
                label, reason = "ENTAILMENT", "Unsupported sabotage phrase found."
        elif claim_id == "unsupported_sister_call":
            if "sister" in text and "9:12" in text:
                label, reason = "ENTAILMENT", "Sister and 9:12 phrase found."
        elif claim_id == "unsupported_has_usb_now":
            if has_any(text, ["i still have it", "my own device", "copy of the information"]):
                label, reason = "ENTAILMENT", "Unsupported possession/copy phrase found."

        return {"label": label, "confidence": 0.6 if label != "NEUTRAL" else 0.3, "reason": reason}


def has_any(text: str, phrases: list[str]) -> bool:
    """Return whether any phrase is in text."""

    return any(phrase in text for phrase in phrases)


class TransformersNLIBackend:
    """HuggingFace transformer NLI backend."""

    def __init__(self, model_name: str, confidence_threshold: float) -> None:
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
        except ImportError as error:
            raise RuntimeError(
                "The transformers backend requires torch and transformers. "
                "Install them or use --backend heuristic."
            ) from error

        self.torch = torch
        self.confidence_threshold = confidence_threshold
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.eval()
        self.id_to_label = self._read_label_mapping()

    def classify(self, premise: str, claims: list[dict]) -> dict[str, dict]:
        """Classify all claims for one premise using batched model inference."""

        hypotheses = [claim["text"] for claim in claims]
        premises = [premise] * len(hypotheses)
        encoded = self.tokenizer(
            premises,
            hypotheses,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )

        with self.torch.no_grad():
            logits = self.model(**encoded).logits
            probabilities = self.torch.softmax(logits, dim=-1)

        output: dict[str, dict] = {}
        for index, claim in enumerate(claims):
            probability_row = probabilities[index]
            label_id = int(self.torch.argmax(probability_row).item())
            raw_label = self.id_to_label.get(label_id, str(label_id))
            label = normalize_transformer_label(raw_label)
            confidence = float(probability_row[label_id].item())
            reason = f"transformers:{raw_label}"
            if label != "NEUTRAL" and confidence < self.confidence_threshold:
                label = "NEUTRAL"
                reason = f"{reason}; below_threshold={self.confidence_threshold}"
            output[claim["id"]] = {
                "label": label,
                "confidence": confidence,
                "reason": reason,
            }

        return output

    def _read_label_mapping(self) -> dict[int, str]:
        """Read model label names from config."""

        raw_mapping = getattr(self.model.config, "id2label", {})
        return {int(key): str(value) for key, value in raw_mapping.items()}


def normalize_transformer_label(raw_label: str) -> str:
    """Normalize model-specific NLI labels to the project label set."""

    label = raw_label.upper()
    if "ENTAIL" in label:
        return "ENTAILMENT"
    if "CONTRAD" in label:
        return "CONTRADICTION"
    if "NEUTRAL" in label:
        return "NEUTRAL"
    return "NEUTRAL"


if __name__ == "__main__":
    main()
