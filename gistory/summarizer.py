from __future__ import annotations

from dataclasses import replace

from gistory.filters import filter_paths, is_ignored
from gistory.git_reader import CommitInfo
from gistory.providers.base import SummaryProvider


MAX_DIFF_CHARS = 12_000


def truncate_text(text: str, limit: int = MAX_DIFF_CHARS) -> str:
    if len(text) <= limit:
        return text
    return f"{text[:limit]}\n\n[diff truncated: {len(text) - limit} characters omitted]"


def filter_diff_by_ignored_files(diff: str, ignore: list[str]) -> str:
    if not diff:
        return diff
    chunks = diff.split("\ndiff --git ")
    kept: list[str] = []
    for index, chunk in enumerate(chunks):
        if index == 0 and not chunk.startswith("a/"):
            if chunk.strip():
                kept.append(chunk)
            continue
        full_chunk = chunk if chunk.startswith("diff --git ") else f"diff --git {chunk}"
        first_line = full_chunk.splitlines()[0] if full_chunk.splitlines() else ""
        parts = first_line.split()
        candidate = ""
        if len(parts) >= 4 and parts[2].startswith("a/"):
            candidate = parts[2][2:]
        if candidate and is_ignored(candidate, ignore):
            continue
        kept.append(full_chunk)
    return "\n".join(part for part in kept if part.strip()).strip()


def prepare_commit_for_summary(commit: CommitInfo, ignore: list[str]) -> CommitInfo | None:
    files = filter_paths(commit.files_changed, ignore)
    if not files:
        return None
    filtered_files = len(files) != len(commit.files_changed)
    return replace(
        commit,
        files_changed=files,
        diff_summary=(
            f"{len(files)} relevant file{'s' if len(files) != 1 else ''} changed"
            if filtered_files
            else commit.diff_summary
        ),
        diff=filter_diff_by_ignored_files(commit.diff, ignore),
    )


def summarize_commit(commit: CommitInfo, provider: SummaryProvider) -> str:
    return provider.summarize_commit(commit, truncate_text(commit.diff))
