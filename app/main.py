"""Application entry point for the interrogation prototype."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Import setup
# ---------------------------------------------------------------------------
# This small block lets the app work from both:
#   python -m app.main
# and:
#   python app/main.py
# A beginner-friendly project is easier to use when both commands behave.
if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

from app.interrogation_runner import InterrogationRunner


def main() -> None:
    """Start one terminal interrogation session."""

    project_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Run a local suspect interrogation session.")
    parser.add_argument(
        "--scenario",
        default=os.getenv("SCENARIO_FILE", str(project_root / "data" / "scenario" / "marcus_chen_case.json")),
        help="Scenario JSON file.",
    )
    parser.add_argument(
        "--question-bank",
        default=os.getenv(
            "QUESTION_BANK_FILE",
            str(project_root / "data" / "question_bank" / "marcus_questions.json"),
        ),
        help="Question bank JSON file.",
    )
    parser.add_argument(
        "--protocol",
        default=os.getenv("PROTOCOL_FILE"),
        help="Optional ordered protocol JSON file.",
    )
    parser.add_argument(
        "--runs-dir",
        default=os.getenv("RUNS_DIR", str(project_root / "data" / "runs")),
        help="Directory where run logs are saved.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
        help="Ollama model name.",
    )
    args = parser.parse_args()

    # -----------------------------------------------------------------------
    # Configuration
    # -----------------------------------------------------------------------
    # The model can be changed without editing code:
    #   PowerShell: $env:OLLAMA_MODEL="llama3.1:8b"
    # If the variable is not set, the project uses a sensible default.
    model_name = args.model

    runner = InterrogationRunner(
        scenario_path=Path(args.scenario),
        question_bank_path=Path(args.question_bank),
        protocol_path=Path(args.protocol) if args.protocol else None,
        runs_dir=Path(args.runs_dir),
        model_name=model_name,
    )
    runner.run()


if __name__ == "__main__":
    main()
