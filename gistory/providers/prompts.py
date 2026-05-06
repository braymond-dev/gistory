from __future__ import annotations

from gistory.git_reader import CommitInfo


def build_commit_prompt(commit: CommitInfo, diff_text: str) -> str:
    return (
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
