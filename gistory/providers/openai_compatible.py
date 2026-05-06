from __future__ import annotations

import os

import httpx

from gistory.git_reader import CommitInfo
from gistory.providers.base import SummaryProvider
from gistory.providers.prompts import build_commit_prompt


class OpenAICompatibleProvider(SummaryProvider):
    def __init__(
        self,
        model: str,
        api_base: str,
        api_key_env: str = "OPENAI_API_KEY",
        timeout: float = 120.0,
    ) -> None:
        self.model = model
        self.api_base = api_base.rstrip("/")
        self.api_key_env = api_key_env
        self.timeout = timeout

    def summarize_commit(self, commit: CommitInfo, diff_text: str) -> str:
        api_key = os.getenv(self.api_key_env)
        if not api_key:
            raise RuntimeError(f"Missing API key environment variable: {self.api_key_env}")

        try:
            response = httpx.post(
                f"{self.api_base}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You write concise, factual project history summaries.",
                        },
                        {"role": "user", "content": build_commit_prompt(commit, diff_text)},
                    ],
                    "temperature": 0.2,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"OpenAI-compatible request failed: {exc}") from exc
        except ValueError as exc:
            raise RuntimeError("OpenAI-compatible provider returned invalid JSON") from exc

        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("OpenAI-compatible response did not include message content") from exc
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("OpenAI-compatible response message content was empty")
        return text.strip()
