"""Suspect-facing model logic."""

from __future__ import annotations

from app.models.ollama_client import OllamaClient
from app.prompt_builder import PromptBuilder


class SuspectAgent:
    """Turns scenario data and dialogue history into model calls."""

    def __init__(self, scenario: dict, ollama_client: OllamaClient) -> None:
        self.scenario = scenario
        self.ollama_client = ollama_client
        self.system_prompt = PromptBuilder.build_suspect_prompt(scenario)

    def answer(self, user_question: str, previous_turns: list[dict]) -> str:
        """Ask the local model for Marcus Chen's next answer."""

        # -------------------------------------------------------------------
        # Rebuild the conversation every turn
        # -------------------------------------------------------------------
        # Ollama's chat endpoint expects message history. We keep the saved
        # turn log as the source of truth and convert it into chat messages.
        messages = []
        for turn in previous_turns:
            messages.append({"role": "user", "content": turn["user_question"]})
            messages.append({"role": "assistant", "content": turn["suspect_answer"]})

        messages.append({"role": "user", "content": user_question})

        return self.ollama_client.chat(
            system_prompt=self.system_prompt,
            messages=messages,
        )
