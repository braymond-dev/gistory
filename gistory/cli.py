from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from pydantic import ValidationError

from gistory.config import GistoryConfig, load_config, write_default_config
from gistory.pipeline import generate_history, write_history

app = typer.Typer(help="Generate a narrative Markdown history from Git commits.")


def _config_with_overrides(
    config_path: Path,
    output: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    ollama_url: Optional[str] = None,
    ollama_timeout: Optional[float] = None,
) -> GistoryConfig:
    try:
        config = load_config(config_path)
        updates: dict[str, str] = {}
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
        return GistoryConfig.model_validate(config.model_dump() | updates)
    except (RuntimeError, ValidationError) as exc:
        raise typer.BadParameter(str(exc)) from exc


@app.command()
def init(
    config: Path = typer.Option(Path(".gistory.yml"), "--config", help="Path to write config."),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing config file."),
) -> None:
    """Create a default .gistory.yml file."""
    try:
        write_default_config(config, overwrite=force)
    except FileExistsError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Created {config}")


@app.command()
def generate(
    since: Optional[str] = typer.Option(None, "--since", help='Git date expression, e.g. "30 days ago".'),
    revision_range: Optional[str] = typer.Option(None, "--range", help='Git revision range, e.g. "HEAD~20..HEAD".'),
    out: Optional[str] = typer.Option(None, "--out", help="Output Markdown file."),
    provider: Optional[str] = typer.Option(None, "--provider", help="Provider name: ollama or mock."),
    model: Optional[str] = typer.Option(None, "--model", help="Provider model name."),
    ollama_url: Optional[str] = typer.Option(None, "--ollama-url", help="Ollama base URL."),
    ollama_timeout: Optional[float] = typer.Option(None, "--ollama-timeout", help="Ollama request timeout in seconds."),
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
    )
    try:
        markdown = generate_history(selected, revision_range=revision_range, since=since)
        write_history(markdown, selected.output)
    except (RuntimeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Wrote {selected.output}")


@app.command()
def explain(
    revision_range: str = typer.Option(..., "--range", help='Git revision range, e.g. "HEAD~10..HEAD".'),
    provider: Optional[str] = typer.Option(None, "--provider", help="Provider name: ollama or mock."),
    model: Optional[str] = typer.Option(None, "--model", help="Provider model name."),
    ollama_url: Optional[str] = typer.Option(None, "--ollama-url", help="Ollama base URL."),
    ollama_timeout: Optional[float] = typer.Option(None, "--ollama-timeout", help="Ollama request timeout in seconds."),
    config: Path = typer.Option(Path(".gistory.yml"), "--config", help="Path to config file."),
) -> None:
    """Explain a commit range and print the narrative to stdout."""
    selected = _config_with_overrides(
        config,
        provider=provider,
        model=model,
        ollama_url=ollama_url,
        ollama_timeout=ollama_timeout,
    )
    try:
        markdown = generate_history(selected, revision_range=revision_range)
    except (RuntimeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(markdown)
