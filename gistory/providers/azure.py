from __future__ import annotations

import os
from typing import Any

from gistory.git_reader import CommitInfo
from gistory.providers.base import SummaryProvider
from gistory.providers.prompts import build_commit_prompt


class AzureProvider(SummaryProvider):
    def __init__(
        self,
        model: str,
        endpoint: str,
        api_key_env: str | None = None,
        timeout: float = 120.0,
        max_tokens: int = 500,
        temperature: float = 0.2,
    ) -> None:
        self.model = model
        self.endpoint = endpoint.rstrip("/")
        self.api_key_env = api_key_env
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client: Any | None = None

    def summarize_commit(self, commit: CommitInfo, diff_text: str) -> str:
        try:
            response = self._azure_client().complete(
                messages=[
                    self._system_message()("You write concise, factual project history summaries."),
                    self._user_message()(build_commit_prompt(commit, diff_text)),
                ],
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
        except Exception as exc:
            raise RuntimeError(f"Azure request failed: {exc}") from exc

        try:
            text = response.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as exc:
            raise RuntimeError("Azure response did not include message content") from exc
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("Azure response message content was empty")
        return text.strip()

    def _azure_client(self) -> Any:
        if self._client is not None:
            return self._client

        try:
            from azure.ai.inference import ChatCompletionsClient
            from azure.core.credentials import AzureKeyCredential
            from azure.identity import DefaultAzureCredential
        except ImportError as exc:
            raise RuntimeError("azure-ai-inference and azure-identity are required for the azure provider") from exc

        if self.api_key_env:
            api_key = os.getenv(self.api_key_env)
            if not api_key:
                raise RuntimeError(f"Missing API key environment variable: {self.api_key_env}")
            credential = AzureKeyCredential(api_key)
            self._client = ChatCompletionsClient(endpoint=self.endpoint, credential=credential)
        else:
            self._client = ChatCompletionsClient(
                endpoint=self.endpoint,
                credential=DefaultAzureCredential(),
                credential_scopes=["https://cognitiveservices.azure.com/.default"],
            )
        return self._client

    @staticmethod
    def _system_message() -> Any:
        from azure.ai.inference.models import SystemMessage

        return SystemMessage

    @staticmethod
    def _user_message() -> Any:
        from azure.ai.inference.models import UserMessage

        return UserMessage
