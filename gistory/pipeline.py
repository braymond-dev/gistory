from __future__ import annotations

from pathlib import Path

from gistory.config import GistoryConfig
from gistory.git_reader import GitReader
from gistory.markdown import CommitSummary, group_by_month, render_markdown
from gistory.providers.base import SummaryProvider
from gistory.providers.mock import MockProvider
from gistory.providers.ollama import OllamaProvider
from gistory.summarizer import prepare_commit_for_summary, summarize_commit


def build_provider(config: GistoryConfig) -> SummaryProvider:
    if config.provider == "mock":
        return MockProvider()
    if config.provider == "ollama":
        return OllamaProvider(model=config.model)
    raise RuntimeError(f"Unsupported provider: {config.provider}")


def generate_history(
    config: GistoryConfig,
    repo_path: Path | str = ".",
    revision_range: str | None = None,
    since: str | None = None,
    provider: SummaryProvider | None = None,
) -> str:
    if revision_range and since:
        raise ValueError("Use either --range or --since, not both")

    reader = GitReader(repo_path)
    selected_provider = provider or build_provider(config)
    commit_summaries: list[CommitSummary] = []
    for commit in reader.read_commits(revision_range=revision_range, since=since):
        prepared = prepare_commit_for_summary(commit, config.ignore)
        if prepared is None:
            continue
        summary = summarize_commit(prepared, selected_provider)
        commit_summaries.append(CommitSummary(commit=prepared, summary=summary))

    sections = group_by_month(commit_summaries)
    return render_markdown(sections)


def write_history(markdown: str, output_path: Path | str) -> None:
    path = Path(output_path)
    path.write_text(markdown, encoding="utf-8")
