from __future__ import annotations

import httpx

from gistory.git_reader import CommitInfo
from gistory.providers.base import SummaryProvider
from gistory.providers.prompts import build_commit_prompt


class OllamaProvider(SummaryProvider):
    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:11434",
        timeout: float = 60.0,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def summarize_commit(self, commit: CommitInfo, diff_text: str) -> str:
        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": build_commit_prompt(commit, diff_text), "stream": False},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc
        except ValueError as exc:
            raise RuntimeError("Ollama returned invalid JSON") from exc

        text = data.get("response")
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("Ollama response did not include a non-empty 'response' field")
        return text.strip()
