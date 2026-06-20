from __future__ import annotations

from gistory.git_reader import CommitInfo


def build_commit_prompt(commit: CommitInfo, diff_text: str) -> str:
    return (
        "Summarize this Git commit as one short paragraph for a technical blog-style project history. "
        "Write in a clear, narrative voice for engineers: factual, concrete, and readable. "
        "Mention user-visible, architectural, testing, or developer-experience impact when clear. "
        "Lead with the specific feature, fix, or decision rather than generic phrases such as "
        "'This commit', 'This update', or 'This change'. Vary sentence structure naturally across summaries. "
        "Describe only behavior implemented by the diff; distinguish examples and documentation from runtime behavior. "
        "Avoid bullet points, hype, markdown headings, and commit-hash repetition.\n\n"
        f"Commit: {commit.short_hash} {commit.subject}\n"
        f"Author: {commit.author}\n"
        f"Date: {commit.date.isoformat()}\n"
        f"Body:\n{commit.body or '(none)'}\n\n"
        f"Files changed:\n{chr(10).join(commit.files_changed) or '(none)'}\n\n"
        f"Diff summary:\n{commit.diff_summary or '(none)'}\n\n"
        f"Diff:\n{diff_text or '(none)'}"
    )
