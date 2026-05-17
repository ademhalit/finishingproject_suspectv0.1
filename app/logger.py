"""Structured JSON logging for interrogation runs."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


class TurnLogger:
    """Stores each interrogation turn and writes the run to disk."""

    def __init__(
        self,
        runs_dir: Path,
        suspect_name: str,
        model_name: str,
        experiment_id: str = "experiment_1_not_guilty",
        protocol_id: str | None = None,
        case_id: str = "marcus_not_guilty",
        scenario_version: str = "",
        scenario_file: str = "",
        question_bank_file: str = "",
        protocol_file: str | None = None,
    ) -> None:
        self.runs_dir = runs_dir
        self.suspect_name = suspect_name
        self.model_name = model_name
        self.experiment_id = experiment_id
        self.protocol_id = protocol_id
        self.case_id = case_id
        self.scenario_version = scenario_version
        self.scenario_file = scenario_file
        self.question_bank_file = question_bank_file
        self.protocol_file = protocol_file
        self.run_id = self._make_run_id()
        self.turns: list[dict] = []
        self.notes = None

    def add_turn(
        self,
        turn_id: int,
        suggested_questions: list,
        selected_question_source: str,
        user_question: str,
        suspect_answer: str,
        question_id: str = "",
        question_category: str = "",
    ) -> None:
        """Add one turn using the research-friendly schema."""

        suggestion_texts = [
            getattr(question, "text", str(question))
            for question in suggested_questions
        ]
        suggestion_details = [
            {
                "question_id": getattr(question, "id", ""),
                "question_category": getattr(question, "category", ""),
                "question": getattr(question, "text", str(question)),
                "question_source": getattr(question, "source", "suggestion"),
            }
            for question in suggested_questions
        ]

        self.turns.append(
            {
                "run_id": self.run_id,
                "experiment_id": self.experiment_id,
                "protocol_id": self.protocol_id,
                "case_id": self.case_id,
                "scenario_version": self.scenario_version,
                "scenario_file": self.scenario_file,
                "question_bank_file": self.question_bank_file,
                "protocol_file": self.protocol_file,
                "turn_id": turn_id,
                "timestamp": self._timestamp(),
                "suspect_name": self.suspect_name,
                "suspect_model": self.model_name,
                "suggested_questions": suggestion_texts,
                "suggested_question_details": suggestion_details,
                "selected_question_source": selected_question_source,
                "question_source": selected_question_source,
                "question_category": question_category,
                "question_id": question_id,
                "question": user_question,
                "user_question": user_question,
                "suspect_answer": suspect_answer,
                "model_name": self.model_name,
                "gold_label": None,
                "notes": None,
            }
        )

    def save(self) -> Path:
        """Write the current run to a JSON file and return its path."""

        self.runs_dir.mkdir(parents=True, exist_ok=True)
        path = self.runs_dir / f"{self.run_id}.json"

        payload = {
            "run_id": self.run_id,
            "created_at": self.run_id,
            "experiment_id": self.experiment_id,
            "protocol_id": self.protocol_id,
            "case_id": self.case_id,
            "scenario_version": self.scenario_version,
            "scenario_file": self.scenario_file,
            "question_bank_file": self.question_bank_file,
            "protocol_file": self.protocol_file,
            "suspect_name": self.suspect_name,
            "suspect_model": self.model_name,
            "model_name": self.model_name,
            "turn_count": len(self.turns),
            "turns": self.turns,
            "notes": self.notes,
        }

        with path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)

        return path

    @staticmethod
    def _make_run_id() -> str:
        """Create a filename-safe timestamp ID."""

        return datetime.now().strftime("%Y-%m-%dT%H-%M-%S")

    @staticmethod
    def _timestamp() -> str:
        """Create an ISO-like timestamp for a single turn."""

        return datetime.now().isoformat(timespec="seconds")
