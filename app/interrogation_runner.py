"""Coordinates one complete interrogation session."""

from __future__ import annotations

import json
from pathlib import Path

from app.logger import TurnLogger
from app.models.ollama_client import OllamaClient, OllamaConnectionError
from app.question_selector import QuestionSelector
from app.suspect_agent import SuspectAgent
from app.terminal_ui import TerminalUI


class InterrogationRunner:
    """Runs the turn-by-turn terminal experiment."""

    def __init__(
        self,
        scenario_path: Path,
        question_bank_path: Path,
        runs_dir: Path,
        model_name: str,
        protocol_path: Path | None = None,
    ) -> None:
        # -------------------------------------------------------------------
        # Load static experiment data
        # -------------------------------------------------------------------
        # Scenario and question bank are files so the experiment can be
        # inspected and edited without changing Python code.
        self.scenario = self._load_json(scenario_path)
        self.suspect_name = self.scenario.get("suspect_name", "Marcus Chen")
        self.scenario_path = scenario_path
        self.question_bank_path = question_bank_path
        self.protocol_path = protocol_path

        self.ui = TerminalUI()
        self.question_selector = QuestionSelector.from_file(question_bank_path, protocol_path=protocol_path)

        # -------------------------------------------------------------------
        # Build runtime services
        # -------------------------------------------------------------------
        # The Ollama client is separated from the suspect agent. Later, this
        # makes it easy to replace model serving without rewriting the app.
        self.ollama_client = OllamaClient(model_name=model_name)
        self.suspect_agent = SuspectAgent(
            scenario=self.scenario,
            ollama_client=self.ollama_client,
        )
        self.logger = TurnLogger(
            runs_dir=runs_dir,
            suspect_name=self.suspect_name,
            model_name=model_name,
            experiment_id=self.scenario.get("experiment_id", "experiment_1_not_guilty"),
            protocol_id=self.question_selector.protocol_id or self.scenario.get("protocol_id"),
            case_id=self.scenario.get("case_id", "marcus_not_guilty"),
            scenario_version=self.scenario.get("scenario_version", ""),
            scenario_file=self._display_path(scenario_path),
            question_bank_file=self._display_path(question_bank_path),
            protocol_file=self._display_path(protocol_path) if protocol_path else None,
        )

    def run(self) -> None:
        """Start and manage the terminal session."""

        self.ui.show_intro(self.scenario)

        # -------------------------------------------------------------------
        # Fail early if Ollama is not reachable
        # -------------------------------------------------------------------
        # This avoids letting the user write a question and only then discover
        # that no local model is available.
        try:
            self.ollama_client.ensure_available()
        except OllamaConnectionError as error:
            self.ui.show_ollama_unavailable(str(error))
            return

        turn_number = 1

        while True:
            suggestions = self.question_selector.select_questions(
                turn_number=turn_number,
                previous_turns=self.logger.turns,
            )

            choice = self.ui.ask_question(turn_number, suggestions)
            if choice is None:
                break

            self.ui.show_selected_question(choice.text)

            try:
                answer = self.suspect_agent.answer(
                    user_question=choice.text,
                    previous_turns=self.logger.turns,
                )
            except OllamaConnectionError as error:
                self.ui.show_error(str(error))
                self.logger.save()
                break

            self.ui.show_answer(self.suspect_name, answer)

            # ----------------------------------------------------------------
            # Save after every turn
            # ----------------------------------------------------------------
            # Saving incrementally preserves partial sessions if the terminal
            # closes or Ollama fails later in the interview.
            self.logger.add_turn(
                turn_id=turn_number,
                suggested_questions=suggestions,
                selected_question_source=choice.source,
                user_question=choice.text,
                suspect_answer=answer,
                question_id=choice.question_id,
                question_category=choice.category,
            )
            self.logger.save()

            turn_number += 1

        if self.logger.turns or self.ui.confirm_continue_without_turns():
            run_path = self.logger.save()
            self.ui.show_goodbye(str(run_path), len(self.logger.turns))
        else:
            self.ui.show_goodbye("not saved", 0)

    @staticmethod
    def _load_json(path: Path) -> dict:
        """Load a JSON object and give a clear error if the file is invalid."""

        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError as error:
            raise RuntimeError(f"Required file not found: {path}") from error
        except json.JSONDecodeError as error:
            raise RuntimeError(f"Invalid JSON in {path}: {error}") from error

        if not isinstance(data, dict):
            raise RuntimeError(f"Expected a JSON object in {path}.")

        return data

    @staticmethod
    def _display_path(path: Path) -> str:
        """Store a stable project-relative path when possible."""

        try:
            return str(path.resolve().relative_to(Path.cwd().resolve()))
        except ValueError:
            return str(path)
