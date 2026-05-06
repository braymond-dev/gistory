from __future__ import annotations

from typing import Any

from gistory.git_reader import CommitInfo
from gistory.providers.base import SummaryProvider
from gistory.providers.prompts import build_commit_prompt


class VertexProvider(SummaryProvider):
    def __init__(
        self,
        model: str,
        project: str | None = None,
        location: str = "global",
        timeout: float = 120.0,
        max_tokens: int = 500,
        temperature: float = 0.2,
    ) -> None:
        self.model = model
        self.project = project
        self.location = location
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client: Any | None = None

    def summarize_commit(self, commit: CommitInfo, diff_text: str) -> str:
        try:
            response = self._vertex_client().models.generate_content(
                model=self.model,
                contents=build_commit_prompt(commit, diff_text),
                config=self._generate_config()(
                    max_output_tokens=self.max_tokens,
                    temperature=self.temperature,
                ),
            )
        except Exception as exc:
            raise RuntimeError(f"Vertex AI request failed: {exc}") from exc

        text = getattr(response, "text", None)
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("Vertex AI response did not include text")
        return text.strip()

    def _vertex_client(self) -> Any:
        if self._client is not None:
            return self._client

        try:
            from google import genai
            from google.genai.types import HttpOptions
        except ImportError as exc:
            raise RuntimeError("google-genai is required for the vertex provider") from exc

        kwargs: dict[str, Any] = {
            "vertexai": True,
            "location": self.location,
            "http_options": HttpOptions(api_version="v1", timeout=self.timeout * 1000),
        }
        if self.project:
            kwargs["project"] = self.project
        self._client = genai.Client(**kwargs)
        return self._client

    @staticmethod
    def _generate_config() -> Any:
        from google.genai.types import GenerateContentConfig

        return GenerateContentConfig
