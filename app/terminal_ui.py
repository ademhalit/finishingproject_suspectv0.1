"""Terminal input and output helpers.

This module keeps printing and input handling away from the research logic.
That makes the interrogation runner easier to read and easier to test later.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class QuestionChoice:
    """A question selected by the player."""

    source: str
    text: str
    question_id: str = ""
    category: str = ""


class TerminalUI:
    """Small wrapper around terminal printing and input."""

    def show_intro(self, scenario: dict) -> None:
        """Display only public case context to the player."""

        suspect_name = scenario.get("suspect_name", "Suspect")
        experiment_id = scenario.get("experiment_id", "")
        title_suffix = f" ({experiment_id})" if experiment_id else ""
        print(f"\n=== {suspect_name} Interrogation Prototype{title_suffix} ===\n")
        print("Case context:")
        print(scenario.get("case_summary", "No case summary provided."))

        public_context = scenario.get("player_context")
        if public_context:
            print(f"\nYour role:\n{public_context}")

        public_facts = scenario.get("public_known_facts", [])
        if public_facts:
            print("\nPublicly known facts:")
            for fact in public_facts:
                print(f"- {fact}")

        print("\nType q or quit at any prompt to end the session cleanly.")

    def show_ollama_unavailable(self, message: str) -> None:
        """Explain that the local model server cannot be reached."""

        print("\nCould not connect to Ollama.")
        print(message)
        print("\nCheck that Ollama is running and that the requested model is installed.")

    def ask_question(self, turn_number: int, suggestions: list) -> QuestionChoice | None:
        """Ask the player to choose a suggested question or type a custom one.

        Returns None when the player chooses to quit.
        """

        while True:
            print(f"\n--- Turn {turn_number} ---")
            print("Suggested questions:")
            for index, question in enumerate(suggestions, start=1):
                print(f"{index}. {getattr(question, 'text', str(question))}")
            print("4. Custom question")

            choice = input("\nChoose 1-4, or q to quit: ").strip()

            if self._is_quit(choice):
                return None

            if choice in {"1", "2", "3"}:
                selected_index = int(choice) - 1
                if selected_index < len(suggestions):
                    selected = suggestions[selected_index]
                    return QuestionChoice(
                        source=getattr(selected, "source", "suggestion"),
                        text=getattr(selected, "text", str(selected)),
                        question_id=getattr(selected, "id", ""),
                        category=getattr(selected, "category", ""),
                    )
                print("That suggestion is not available this turn.")
                continue

            if choice == "4":
                custom_question = input("Type your question: ").strip()
                if self._is_quit(custom_question):
                    return None
                if not custom_question:
                    print("Empty questions are not useful. Please type a question.")
                    continue
                return QuestionChoice(source="custom", text=custom_question)

            print("Please choose 1, 2, 3, 4, or q.")

    def show_selected_question(self, question: str) -> None:
        """Echo the chosen question before sending it to the model."""

        print(f"\nYou ask: {question}")

    def show_answer(self, suspect_name: str, answer: str) -> None:
        """Print the suspect answer in a consistent format."""

        print(f"\n{suspect_name}: {answer}")

    def show_error(self, message: str) -> None:
        """Print a readable runtime error message."""

        print(f"\nError: {message}")

    def show_goodbye(self, run_path: str, turn_count: int) -> None:
        """Tell the user where the session was saved."""

        print("\nSession ended.")
        print(f"Saved {turn_count} turn(s) to: {run_path}")

    def confirm_continue_without_turns(self) -> bool:
        """Ask whether to create an empty run when the user exits immediately."""

        choice = input("\nNo turns were recorded. Save an empty run file? [y/N]: ").strip()
        return choice.lower() == "y"

    @staticmethod
    def _is_quit(value: str) -> bool:
        """Check whether a player input means exit."""

        return value.lower() in {"q", "quit", "exit"}


def print_lines(lines: Iterable[str]) -> None:
    """Utility used by future UI code when printing simple line groups."""

    for line in lines:
        print(line)
