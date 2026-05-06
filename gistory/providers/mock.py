from __future__ import annotations

from gistory.git_reader import CommitInfo
from gistory.providers.base import SummaryProvider


class MockProvider(SummaryProvider):
    """Deterministic provider useful for tests and offline development."""

    def summarize_commit(self, commit: CommitInfo, diff_text: str) -> str:
        files = ", ".join(commit.files_changed[:3])
        suffix = f" touching {files}" if files else ""
        return f"{commit.subject}{suffix}."
