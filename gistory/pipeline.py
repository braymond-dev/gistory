from __future__ import annotations

from pathlib import Path

from gistory.config import GistoryConfig
from gistory.git_reader import GitReader
from gistory.markdown import (
    CommitSummary,
    append_segment,
    group_by_month,
    latest_segment_end,
    mark_continued_months,
    render_markdown,
    render_segment,
)
from gistory.providers.azure import AzureProvider
from gistory.providers.bedrock import BedrockProvider
from gistory.providers.base import SummaryProvider
from gistory.providers.mock import MockProvider
from gistory.providers.openai_compatible import OpenAICompatibleProvider
from gistory.providers.ollama import OllamaProvider
from gistory.providers.vertex import VertexProvider
from gistory.summarizer import prepare_commit_for_summary, summarize_commit


def build_provider(config: GistoryConfig) -> SummaryProvider:
    if config.provider == "mock":
        return MockProvider()
    if config.provider == "ollama":
        return OllamaProvider(
            model=config.model,
            base_url=config.ollama_url,
            timeout=config.ollama_timeout,
        )
    if config.provider == "openai-compatible":
        return OpenAICompatibleProvider(
            model=config.model,
            api_base=str(config.api_base),
            api_key_env=config.api_key_env,
            timeout=config.api_timeout,
        )
    if config.provider == "bedrock":
        return BedrockProvider(
            model=config.model,
            region=config.bedrock_region,
            profile=config.bedrock_profile,
            timeout=config.bedrock_timeout,
            max_tokens=config.bedrock_max_tokens,
            temperature=config.bedrock_temperature,
        )
    if config.provider == "azure":
        return AzureProvider(
            model=config.model,
            endpoint=config.azure_endpoint,
            api_key_env=config.azure_api_key_env,
            timeout=config.azure_timeout,
            max_tokens=config.azure_max_tokens,
            temperature=config.azure_temperature,
        )
    if config.provider == "vertex":
        return VertexProvider(
            model=config.model,
            project=config.vertex_project,
            location=config.vertex_location,
            timeout=config.vertex_timeout,
            max_tokens=config.vertex_max_tokens,
            temperature=config.vertex_temperature,
        )
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

    sections = group_by_month(
        _summarize_commits(
            config,
            repo_path=repo_path,
            revision_range=revision_range,
            since=since,
            provider=provider,
        )
    )
    return render_markdown(sections)


def generate_history_append_only(
    config: GistoryConfig,
    repo_path: Path | str = ".",
    revision_range: str | None = None,
    since: str | None = None,
    provider: SummaryProvider | None = None,
) -> str:
    if revision_range or since:
        raise ValueError("Append-only mode manages the range from the existing output file")

    output_path = Path(repo_path) / config.output
    existing = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
    latest_hash = latest_segment_end(existing)
    incremental_range = f"{latest_hash}..HEAD" if latest_hash else None
    summaries = _summarize_commits(
        config,
        repo_path=repo_path,
        revision_range=incremental_range,
        provider=provider,
    )
    sections = mark_continued_months(group_by_month(summaries), existing)
    segment = render_segment(
        sections,
        start_hash=summaries[-1].commit.short_hash if summaries else None,
        end_hash=summaries[0].commit.short_hash if summaries else None,
    )
    if not segment:
        return existing if existing else "# Gistory\n\nNo commits found.\n"
    return append_segment(existing, segment)


def _summarize_commits(
    config: GistoryConfig,
    repo_path: Path | str,
    revision_range: str | None,
    since: str | None = None,
    provider: SummaryProvider | None = None,
) -> list[CommitSummary]:
    reader = GitReader(repo_path)
    selected_provider = provider or build_provider(config)
    commit_summaries: list[CommitSummary] = []
    for commit in reader.read_commits(revision_range=revision_range, since=since):
        prepared = prepare_commit_for_summary(commit, config.ignore)
        if prepared is None:
            continue
        summary = summarize_commit(prepared, selected_provider)
        commit_summaries.append(CommitSummary(commit=prepared, summary=summary))
    return commit_summaries


def write_history(markdown: str, output_path: Path | str) -> None:
    path = Path(output_path)
    path.write_text(markdown, encoding="utf-8")
