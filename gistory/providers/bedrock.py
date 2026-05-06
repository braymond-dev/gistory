from __future__ import annotations

from typing import Any

from gistory.git_reader import CommitInfo
from gistory.providers.base import SummaryProvider
from gistory.providers.prompts import build_commit_prompt


class BedrockProvider(SummaryProvider):
    def __init__(
        self,
        model: str,
        region: str,
        profile: str | None = None,
        timeout: float = 120.0,
        max_tokens: int = 500,
        temperature: float = 0.2,
    ) -> None:
        self.model = model
        self.region = region
        self.profile = profile
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client: Any | None = None

    def summarize_commit(self, commit: CommitInfo, diff_text: str) -> str:
        try:
            response = self._bedrock_client().converse(
                modelId=self.model,
                system=[
                    {
                        "text": "You write concise, factual project history summaries.",
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": build_commit_prompt(commit, diff_text)}],
                    }
                ],
                inferenceConfig={
                    "maxTokens": self.max_tokens,
                    "temperature": self.temperature,
                },
            )
        except Exception as exc:
            raise RuntimeError(f"Bedrock request failed: {exc}") from exc

        text = self._extract_text(response)
        if not text:
            raise RuntimeError("Bedrock response did not include message text")
        return text

    def _bedrock_client(self) -> Any:
        if self._client is not None:
            return self._client

        try:
            import boto3
            from botocore.config import Config
        except ImportError as exc:
            raise RuntimeError("boto3 is required for the bedrock provider") from exc

        session = boto3.Session(profile_name=self.profile) if self.profile else boto3.Session()
        self._client = session.client(
            "bedrock-runtime",
            region_name=self.region,
            config=Config(read_timeout=self.timeout, connect_timeout=10),
        )
        return self._client

    @staticmethod
    def _extract_text(response: dict[str, Any]) -> str:
        content = response.get("output", {}).get("message", {}).get("content", [])
        parts = [block.get("text", "") for block in content if isinstance(block, dict)]
        return "\n".join(part.strip() for part in parts if part.strip())
