"""Small Ollama HTTP client using only the Python standard library."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request


class OllamaConnectionError(RuntimeError):
    """Raised when the local Ollama server cannot complete a request."""


class OllamaClient:
    """Minimal client for Ollama's local HTTP API."""

    def __init__(self, model_name: str, base_url: str | None = None, timeout_seconds: int = 60) -> None:
        # -------------------------------------------------------------------
        # Configuration
        # -------------------------------------------------------------------
        # OLLAMA_BASE_URL lets users point the app at another local Ollama
        # server without editing code. The default is Ollama's normal port.
        self.model_name = model_name
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.timeout_seconds = timeout_seconds

    def ensure_available(self) -> None:
        """Check that Ollama is reachable and the requested model exists."""

        request = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")

        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                if response.status >= 400:
                    raise OllamaConnectionError(
                        f"Ollama responded with HTTP {response.status} at {self.base_url}."
                    )
                raw_body = response.read().decode("utf-8")
        except (urllib.error.URLError, TimeoutError) as error:
            raise OllamaConnectionError(
                f"Could not reach Ollama at {self.base_url}. Original error: {error}"
            ) from error

        try:
            parsed = json.loads(raw_body)
        except json.JSONDecodeError as error:
            raise OllamaConnectionError(f"Ollama returned invalid JSON from /api/tags: {raw_body}") from error

        model_names = {model.get("name") for model in parsed.get("models", [])}
        if self.model_name not in model_names:
            installed = ", ".join(sorted(name for name in model_names if name)) or "none"
            raise OllamaConnectionError(
                f"Model '{self.model_name}' is not installed in Ollama. "
                f"Installed models: {installed}. "
                f"Run: ollama pull {self.model_name}"
            )

    def chat(self, system_prompt: str, messages: list[dict]) -> str:
        """Send a chat request to Ollama and return the assistant content."""

        payload = {
            "model": self.model_name,
            "stream": False,
            "messages": [{"role": "system", "content": system_prompt}, *messages],
            "options": {
                "temperature": 0.4,
            },
        }

        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw_body = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise OllamaConnectionError(
                f"Ollama returned HTTP {error.code}. Response body: {body}"
            ) from error
        except (urllib.error.URLError, TimeoutError) as error:
            raise OllamaConnectionError(
                f"Ollama request failed at {self.base_url}. Original error: {error}"
            ) from error

        try:
            parsed = json.loads(raw_body)
        except json.JSONDecodeError as error:
            raise OllamaConnectionError(f"Ollama returned invalid JSON: {raw_body}") from error

        message = parsed.get("message", {})
        content = message.get("content", "").strip()
        if not content:
            raise OllamaConnectionError(f"Ollama returned an empty response: {parsed}")

        return content
