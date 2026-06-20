from __future__ import annotations

from pathlib import Path
from time import monotonic
from typing import Optional

import typer
from pydantic import ValidationError

from gistory.config import GistoryConfig, load_config, write_default_config
from gistory.pipeline import generate_history, generate_history_document, update_history_document, write_history

app = typer.Typer(help="Generate a narrative Markdown history from Git commits.")


def format_duration(seconds: float) -> str:
    total_seconds = max(0, round(seconds))
    minutes, remaining_seconds = divmod(total_seconds, 60)
    parts: list[str] = []
    if minutes:
        parts.append(f"{minutes} min" if minutes == 1 else f"{minutes} mins")
    parts.append(f"{remaining_seconds} sec" if remaining_seconds == 1 else f"{remaining_seconds} secs")
    return " ".join(parts)


def _config_with_overrides(
    config_path: Path,
    output: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    ollama_url: Optional[str] = None,
    ollama_timeout: Optional[float] = None,
    openai_api_base: Optional[str] = None,
    openai_api_key_env: Optional[str] = None,
    openai_timeout: Optional[float] = None,
    bedrock_region: Optional[str] = None,
    bedrock_profile: Optional[str] = None,
    bedrock_timeout: Optional[float] = None,
    bedrock_max_tokens: Optional[int] = None,
    bedrock_temperature: Optional[float] = None,
    azure_endpoint: Optional[str] = None,
    azure_api_key_env: Optional[str] = None,
    azure_timeout: Optional[float] = None,
    azure_max_tokens: Optional[int] = None,
    azure_temperature: Optional[float] = None,
    vertex_project: Optional[str] = None,
    vertex_location: Optional[str] = None,
    vertex_timeout: Optional[float] = None,
    vertex_max_tokens: Optional[int] = None,
    vertex_temperature: Optional[float] = None,
) -> GistoryConfig:
    try:
        config = load_config(config_path)
        updates: dict[str, object] = {}
        if output:
            updates["output"] = output
        if provider:
            updates["provider"] = provider
        if model:
            updates["model"] = model
        if ollama_url:
            updates["ollama_url"] = ollama_url
        if ollama_timeout is not None:
            updates["ollama_timeout"] = ollama_timeout
        if openai_api_base:
            updates["openai_api_base"] = openai_api_base
        if openai_api_key_env:
            updates["openai_api_key_env"] = openai_api_key_env
        if openai_timeout is not None:
            updates["openai_timeout"] = openai_timeout
        if bedrock_region:
            updates["bedrock_region"] = bedrock_region
        if bedrock_profile:
            updates["bedrock_profile"] = bedrock_profile
        if bedrock_timeout is not None:
            updates["bedrock_timeout"] = bedrock_timeout
        if bedrock_max_tokens is not None:
            updates["bedrock_max_tokens"] = bedrock_max_tokens
        if bedrock_temperature is not None:
            updates["bedrock_temperature"] = bedrock_temperature
        if azure_endpoint:
            updates["azure_endpoint"] = azure_endpoint
        if azure_api_key_env:
            updates["azure_api_key_env"] = azure_api_key_env
        if azure_timeout is not None:
            updates["azure_timeout"] = azure_timeout
        if azure_max_tokens is not None:
            updates["azure_max_tokens"] = azure_max_tokens
        if azure_temperature is not None:
            updates["azure_temperature"] = azure_temperature
        if vertex_project:
            updates["vertex_project"] = vertex_project
        if vertex_location:
            updates["vertex_location"] = vertex_location
        if vertex_timeout is not None:
            updates["vertex_timeout"] = vertex_timeout
        if vertex_max_tokens is not None:
            updates["vertex_max_tokens"] = vertex_max_tokens
        if vertex_temperature is not None:
            updates["vertex_temperature"] = vertex_temperature
        return GistoryConfig.model_validate(config.model_dump() | updates)
    except (RuntimeError, ValidationError) as exc:
        raise typer.BadParameter(str(exc)) from exc


@app.command()
def init(
    config: Path = typer.Option(Path(".gistory.yml"), "--config", help="Path to write config."),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing config file."),
    provider: str = typer.Option("ollama", "--provider", help="Provider to configure."),
    model: Optional[str] = typer.Option(None, "--model", help="Override the provider's default model."),
) -> None:
    """Create a default .gistory.yml file."""
    try:
        write_default_config(config, overwrite=force, provider=provider, model=model)
    except (FileExistsError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Created {config}")


@app.command()
def generate(
    repo: Path = typer.Option(Path("."), "--repo", help="Path to the Git repository to read."),
    since: Optional[str] = typer.Option(None, "--since", help='Git date expression, e.g. "30 days ago".'),
    revision_range: Optional[str] = typer.Option(None, "--range", help='Git revision range, e.g. "HEAD~20..HEAD".'),
    out: Optional[str] = typer.Option(None, "--out", help="Output Markdown file."),
    fresh: bool = typer.Option(False, "--fresh", help="Rebuild marked output from the selected history."),
    provider: Optional[str] = typer.Option(None, "--provider", help="Provider name: ollama, openai-compatible, bedrock, azure, vertex, or mock."),
    model: Optional[str] = typer.Option(None, "--model", help="Provider model name."),
    ollama_url: Optional[str] = typer.Option(None, "--ollama-url", help="Ollama base URL."),
    ollama_timeout: Optional[float] = typer.Option(None, "--ollama-timeout", help="Ollama request timeout in seconds."),
    openai_api_base: Optional[str] = typer.Option(None, "--openai-api-base", help="OpenAI-compatible API base URL."),
    openai_api_key_env: Optional[str] = typer.Option(None, "--openai-api-key-env", help="Environment variable containing the OpenAI API key."),
    openai_timeout: Optional[float] = typer.Option(None, "--openai-timeout", help="OpenAI-compatible request timeout in seconds."),
    bedrock_region: Optional[str] = typer.Option(None, "--bedrock-region", help="AWS region for Bedrock Runtime."),
    bedrock_profile: Optional[str] = typer.Option(None, "--bedrock-profile", help="AWS profile name for Bedrock."),
    bedrock_timeout: Optional[float] = typer.Option(None, "--bedrock-timeout", help="Bedrock request timeout in seconds."),
    bedrock_max_tokens: Optional[int] = typer.Option(None, "--bedrock-max-tokens", help="Maximum Bedrock response tokens."),
    bedrock_temperature: Optional[float] = typer.Option(None, "--bedrock-temperature", help="Bedrock generation temperature."),
    azure_endpoint: Optional[str] = typer.Option(None, "--azure-endpoint", help="Azure AI Foundry inference endpoint."),
    azure_api_key_env: Optional[str] = typer.Option(None, "--azure-api-key-env", help="Optional Azure API key environment variable."),
    azure_timeout: Optional[float] = typer.Option(None, "--azure-timeout", help="Azure request timeout in seconds."),
    azure_max_tokens: Optional[int] = typer.Option(None, "--azure-max-tokens", help="Maximum Azure response tokens."),
    azure_temperature: Optional[float] = typer.Option(None, "--azure-temperature", help="Azure generation temperature."),
    vertex_project: Optional[str] = typer.Option(None, "--vertex-project", help="Google Cloud project for Vertex AI."),
    vertex_location: Optional[str] = typer.Option(None, "--vertex-location", help="Google Cloud location for Vertex AI."),
    vertex_timeout: Optional[float] = typer.Option(None, "--vertex-timeout", help="Vertex AI request timeout in seconds."),
    vertex_max_tokens: Optional[int] = typer.Option(None, "--vertex-max-tokens", help="Maximum Vertex AI response tokens."),
    vertex_temperature: Optional[float] = typer.Option(None, "--vertex-temperature", help="Vertex AI generation temperature."),
    config: Path = typer.Option(Path(".gistory.yml"), "--config", help="Path to config file."),
) -> None:
    """Generate a GISTORY.md file."""
    selected = _config_with_overrides(
        config,
        output=out,
        provider=provider,
        model=model,
        ollama_url=ollama_url,
        ollama_timeout=ollama_timeout,
        openai_api_base=openai_api_base,
        openai_api_key_env=openai_api_key_env,
        openai_timeout=openai_timeout,
        bedrock_region=bedrock_region,
        bedrock_profile=bedrock_profile,
        bedrock_timeout=bedrock_timeout,
        bedrock_max_tokens=bedrock_max_tokens,
        bedrock_temperature=bedrock_temperature,
        azure_endpoint=azure_endpoint,
        azure_api_key_env=azure_api_key_env,
        azure_timeout=azure_timeout,
        azure_max_tokens=azure_max_tokens,
        azure_temperature=azure_temperature,
        vertex_project=vertex_project,
        vertex_location=vertex_location,
        vertex_timeout=vertex_timeout,
        vertex_max_tokens=vertex_max_tokens,
        vertex_temperature=vertex_temperature,
    )
    try:
        started_at = monotonic()
        if fresh or revision_range or since:
            markdown = generate_history_document(
                selected,
                repo_path=repo,
                revision_range=revision_range,
                since=since,
            )
        else:
            markdown = update_history_document(selected, repo_path=repo)
        output_path = Path(selected.output)
        if not output_path.is_absolute():
            output_path = repo / output_path
        write_history(markdown, output_path)
    except (RuntimeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Wrote {selected.output} took {format_duration(monotonic() - started_at)}")


@app.command()
def explain(
    repo: Path = typer.Option(Path("."), "--repo", help="Path to the Git repository to read."),
    revision_range: str = typer.Option(..., "--range", help='Git revision range, e.g. "HEAD~10..HEAD".'),
    provider: Optional[str] = typer.Option(None, "--provider", help="Provider name: ollama, openai-compatible, bedrock, azure, vertex, or mock."),
    model: Optional[str] = typer.Option(None, "--model", help="Provider model name."),
    ollama_url: Optional[str] = typer.Option(None, "--ollama-url", help="Ollama base URL."),
    ollama_timeout: Optional[float] = typer.Option(None, "--ollama-timeout", help="Ollama request timeout in seconds."),
    openai_api_base: Optional[str] = typer.Option(None, "--openai-api-base", help="OpenAI-compatible API base URL."),
    openai_api_key_env: Optional[str] = typer.Option(None, "--openai-api-key-env", help="Environment variable containing the OpenAI API key."),
    openai_timeout: Optional[float] = typer.Option(None, "--openai-timeout", help="OpenAI-compatible request timeout in seconds."),
    bedrock_region: Optional[str] = typer.Option(None, "--bedrock-region", help="AWS region for Bedrock Runtime."),
    bedrock_profile: Optional[str] = typer.Option(None, "--bedrock-profile", help="AWS profile name for Bedrock."),
    bedrock_timeout: Optional[float] = typer.Option(None, "--bedrock-timeout", help="Bedrock request timeout in seconds."),
    bedrock_max_tokens: Optional[int] = typer.Option(None, "--bedrock-max-tokens", help="Maximum Bedrock response tokens."),
    bedrock_temperature: Optional[float] = typer.Option(None, "--bedrock-temperature", help="Bedrock generation temperature."),
    azure_endpoint: Optional[str] = typer.Option(None, "--azure-endpoint", help="Azure AI Foundry inference endpoint."),
    azure_api_key_env: Optional[str] = typer.Option(None, "--azure-api-key-env", help="Optional Azure API key environment variable."),
    azure_timeout: Optional[float] = typer.Option(None, "--azure-timeout", help="Azure request timeout in seconds."),
    azure_max_tokens: Optional[int] = typer.Option(None, "--azure-max-tokens", help="Maximum Azure response tokens."),
    azure_temperature: Optional[float] = typer.Option(None, "--azure-temperature", help="Azure generation temperature."),
    vertex_project: Optional[str] = typer.Option(None, "--vertex-project", help="Google Cloud project for Vertex AI."),
    vertex_location: Optional[str] = typer.Option(None, "--vertex-location", help="Google Cloud location for Vertex AI."),
    vertex_timeout: Optional[float] = typer.Option(None, "--vertex-timeout", help="Vertex AI request timeout in seconds."),
    vertex_max_tokens: Optional[int] = typer.Option(None, "--vertex-max-tokens", help="Maximum Vertex AI response tokens."),
    vertex_temperature: Optional[float] = typer.Option(None, "--vertex-temperature", help="Vertex AI generation temperature."),
    config: Path = typer.Option(Path(".gistory.yml"), "--config", help="Path to config file."),
) -> None:
    """Explain a commit range and print the narrative to stdout."""
    selected = _config_with_overrides(
        config,
        provider=provider,
        model=model,
        ollama_url=ollama_url,
        ollama_timeout=ollama_timeout,
        openai_api_base=openai_api_base,
        openai_api_key_env=openai_api_key_env,
        openai_timeout=openai_timeout,
        bedrock_region=bedrock_region,
        bedrock_profile=bedrock_profile,
        bedrock_timeout=bedrock_timeout,
        bedrock_max_tokens=bedrock_max_tokens,
        bedrock_temperature=bedrock_temperature,
        azure_endpoint=azure_endpoint,
        azure_api_key_env=azure_api_key_env,
        azure_timeout=azure_timeout,
        azure_max_tokens=azure_max_tokens,
        azure_temperature=azure_temperature,
        vertex_project=vertex_project,
        vertex_location=vertex_location,
        vertex_timeout=vertex_timeout,
        vertex_max_tokens=vertex_max_tokens,
        vertex_temperature=vertex_temperature,
    )
    try:
        markdown = generate_history(selected, repo_path=repo, revision_range=revision_range)
    except (RuntimeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(markdown)
