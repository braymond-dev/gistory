from __future__ import annotations

import httpx

from gistory.git_reader import CommitInfo
from gistory.providers.base import SummaryProvider


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
        prompt = (
            "Summarize this Git commit for a project history narrative. "
            "Be concise, factual, and mention user-visible or architectural impact when clear.\n\n"
            f"Commit: {commit.short_hash} {commit.subject}\n"
            f"Author: {commit.author}\n"
            f"Date: {commit.date.isoformat()}\n"
            f"Body:\n{commit.body or '(none)'}\n\n"
            f"Files changed:\n{chr(10).join(commit.files_changed) or '(none)'}\n\n"
            f"Diff summary:\n{commit.diff_summary or '(none)'}\n\n"
            f"Diff:\n{diff_text or '(none)'}"
        )
        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
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
