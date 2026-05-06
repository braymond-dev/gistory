from __future__ import annotations

from abc import ABC, abstractmethod

from gistory.git_reader import CommitInfo


class SummaryProvider(ABC):
    """Interface for commit summary providers."""

    @abstractmethod
    def summarize_commit(self, commit: CommitInfo, diff_text: str) -> str:
        """Return a concise summary for a single commit."""
