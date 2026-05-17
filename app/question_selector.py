"""Local suggested-question selection.

The question selector must not call a second LLM. It uses a small local
question bank and simple rules so the experiment stays reproducible.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SuggestedQuestion:
    """One suggested question plus research metadata."""

    id: str
    category: str
    text: str
    source: str = "suggestion"


class QuestionSelector:
    """Selects three local suggestions for each turn."""

    def __init__(
        self,
        questions: list[dict],
        protocol_questions: list[dict] | None = None,
        protocol_id: str | None = None,
    ) -> None:
        self.questions = [self._normalize_question(item, index) for index, item in enumerate(questions, start=1)]
        self.protocol_questions = [
            self._normalize_question(item, index, source="protocol")
            for index, item in enumerate(protocol_questions or [], start=1)
        ]
        self.protocol_id = protocol_id

    @classmethod
    def from_file(cls, path: Path, protocol_path: Path | None = None) -> "QuestionSelector":
        """Load a question bank from JSON."""

        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError as error:
            raise RuntimeError(f"Question bank not found: {path}") from error
        except json.JSONDecodeError as error:
            raise RuntimeError(f"Invalid JSON in {path}: {error}") from error

        questions = data.get("questions", [])
        if not isinstance(questions, list) or not questions:
            raise RuntimeError(f"Question bank must contain a non-empty 'questions' list: {path}")

        protocol_questions = None
        protocol_id = None
        if protocol_path is not None:
            try:
                with protocol_path.open("r", encoding="utf-8") as file:
                    protocol_data = json.load(file)
            except FileNotFoundError as error:
                raise RuntimeError(f"Protocol file not found: {protocol_path}") from error
            except json.JSONDecodeError as error:
                raise RuntimeError(f"Invalid JSON in {protocol_path}: {error}") from error

            protocol_questions = protocol_data.get("questions", [])
            if not isinstance(protocol_questions, list) or not protocol_questions:
                raise RuntimeError(f"Protocol must contain a non-empty 'questions' list: {protocol_path}")
            protocol_id = str(protocol_data.get("protocol_id", protocol_path.stem))

        return cls(questions, protocol_questions=protocol_questions, protocol_id=protocol_id)

    def select_questions(self, turn_number: int, previous_turns: list[dict]) -> list[SuggestedQuestion]:
        """Return three suggested questions using simple local rules."""

        if self.protocol_questions:
            start_index = min(turn_number - 1, len(self.protocol_questions))
            protocol_slice = [
                self._to_suggestion(item)
                for item in self.protocol_questions[start_index : start_index + 3]
            ]
            if len(protocol_slice) == 3:
                return protocol_slice
            if protocol_slice:
                fallback = self._select_from_bank(turn_number, previous_turns)
                return (protocol_slice + fallback)[:3]

        return self._select_from_bank(turn_number, previous_turns)

    def _select_from_bank(self, turn_number: int, previous_turns: list[dict]) -> list[SuggestedQuestion]:
        """Return three question-bank suggestions."""

        asked_questions = {
            turn.get("user_question", "").strip().lower()
            for turn in previous_turns
            if turn.get("user_question")
        }

        # -------------------------------------------------------------------
        # Rule 1: prefer high-priority questions that have not been asked.
        # Rule 2: rotate the list slightly by turn number for variety.
        # Rule 3: if everything was already asked, recycle the bank.
        # -------------------------------------------------------------------
        ordered = sorted(
            self.questions,
            key=lambda item: (
                item.get("priority", 100),
                item.get("category", ""),
                item.get("id", ""),
            ),
        )

        rotation = (turn_number - 1) % len(ordered)
        rotated = ordered[rotation:] + ordered[:rotation]

        unused = [
            self._to_suggestion(item)
            for item in rotated
            if item.get("question", "").strip().lower() not in asked_questions
        ]

        candidates = unused if len(unused) >= 3 else [self._to_suggestion(item) for item in rotated]
        return candidates[:3]

    @staticmethod
    def _normalize_question(item: dict, index: int, source: str = "suggestion") -> dict:
        """Normalize question-bank and protocol items into one internal shape."""

        question = str(item.get("question", "")).strip()
        if not question:
            raise RuntimeError(f"Question item {index} is missing text.")

        return {
            "id": str(item.get("id", f"q_{index:03d}")),
            "category": str(item.get("category", "")),
            "priority": int(item.get("priority", index)),
            "question": question,
            "source": source,
        }

    @staticmethod
    def _to_suggestion(item: dict) -> SuggestedQuestion:
        """Convert normalized question data to a public suggestion object."""

        return SuggestedQuestion(
            id=item.get("id", ""),
            category=item.get("category", ""),
            text=item.get("question", ""),
            source=item.get("source", "suggestion"),
        )
