import subprocess
from pathlib import Path

from gistory.config import GistoryConfig
from gistory.pipeline import build_provider, generate_history, generate_history_append_only
from gistory.providers.azure import AzureProvider
from gistory.providers.bedrock import BedrockProvider
from gistory.providers.openai_compatible import OpenAICompatibleProvider
from gistory.providers.ollama import OllamaProvider
from gistory.providers.vertex import VertexProvider


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def commit_file(repo: Path, path: str, content: str, message: str) -> None:
    full_path = repo / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")
    git(repo, "add", path)
    git(repo, "commit", "-m", message)


def test_generate_history_filters_ignored_commits_and_uses_mock_provider(tmp_path: Path) -> None:
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "ada@example.com")
    git(tmp_path, "config", "user.name", "Ada Lovelace")
    commit_file(tmp_path, "dist/app.js", "compiled\n", "Build assets")
    commit_file(tmp_path, "src/app.py", "print('hello')\n", "Add app")
    config = GistoryConfig(provider="mock", ignore=["dist/**"])

    markdown = generate_history(config, repo_path=tmp_path)

    assert "# Gistory" in markdown
    assert "Add app touching src/app.py." in markdown
    assert "- " in markdown
    assert "Build assets" not in markdown


def test_generate_history_append_only_adds_only_new_segment(tmp_path: Path) -> None:
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "ada@example.com")
    git(tmp_path, "config", "user.name", "Ada Lovelace")
    commit_file(tmp_path, "src/app.py", "print('hello')\n", "Add app")
    first_hash = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    existing = (
        "# Gistory\n\n"
        f"<!-- gistory:segment start={first_hash} end={first_hash} -->\n\n"
        "## 2026-05\n\nAdd app.\n\n"
        "<!-- gistory:segment-end -->\n"
    )
    (tmp_path / "GISTORY.md").write_text(existing, encoding="utf-8")
    commit_file(tmp_path, "src/feature.py", "print('feature')\n", "Add feature")
    config = GistoryConfig(provider="mock", append_only=True)

    markdown = generate_history_append_only(config, repo_path=tmp_path)

    assert "Add app.\n\n<!-- gistory:segment-end -->" in markdown
    assert "Add feature touching src/feature.py." in markdown
    assert markdown.count("gistory:segment start=") == 2


def test_generate_history_append_only_returns_existing_when_no_new_commits(tmp_path: Path) -> None:
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "ada@example.com")
    git(tmp_path, "config", "user.name", "Ada Lovelace")
    commit_file(tmp_path, "src/app.py", "print('hello')\n", "Add app")
    head = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    existing = f"# Gistory\n\n<!-- gistory:segment start={head} end={head} -->\n\nDone.\n\n<!-- gistory:segment-end -->\n"
    (tmp_path / "GISTORY.md").write_text(existing, encoding="utf-8")
    config = GistoryConfig(provider="mock", append_only=True)

    assert generate_history_append_only(config, repo_path=tmp_path) == existing


def test_generate_history_rejects_range_and_since_together(tmp_path: Path) -> None:
    config = GistoryConfig(provider="mock")

    try:
        generate_history(config, repo_path=tmp_path, revision_range="HEAD~1..HEAD", since="30 days ago")
    except ValueError as exc:
        assert "either --range or --since" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_build_provider_passes_configured_ollama_url() -> None:
    config = GistoryConfig(
        provider="ollama",
        model="qwen3:8b",
        ollama_url="http://127.0.0.1:11434",
        ollama_timeout=123.0,
    )

    provider = build_provider(config)

    assert isinstance(provider, OllamaProvider)
    assert provider.base_url == "http://127.0.0.1:11434"
    assert provider.timeout == 123.0


def test_build_provider_supports_openai_compatible_provider() -> None:
    config = GistoryConfig(
        provider="openai-compatible",
        model="gpt-4.1-mini",
        api_base="https://example.test/v1",
        api_key_env="EXAMPLE_API_KEY",
        api_timeout=42.0,
    )

    provider = build_provider(config)

    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider.model == "gpt-4.1-mini"
    assert provider.api_base == "https://example.test/v1"
    assert provider.api_key_env == "EXAMPLE_API_KEY"
    assert provider.timeout == 42.0


def test_build_provider_supports_bedrock_provider() -> None:
    config = GistoryConfig(
        provider="bedrock",
        model="us.anthropic.claude-3-5-haiku-20241022-v1:0",
        bedrock_region="us-west-2",
        bedrock_profile="work",
        bedrock_timeout=77.0,
        bedrock_max_tokens=300,
        bedrock_temperature=0.1,
    )

    provider = build_provider(config)

    assert isinstance(provider, BedrockProvider)
    assert provider.model == "us.anthropic.claude-3-5-haiku-20241022-v1:0"
    assert provider.region == "us-west-2"
    assert provider.profile == "work"
    assert provider.timeout == 77.0
    assert provider.max_tokens == 300
    assert provider.temperature == 0.1


def test_build_provider_supports_azure_provider() -> None:
    config = GistoryConfig(
        provider="azure",
        model="my-deployment",
        azure_endpoint="https://example.services.ai.azure.com/models",
        azure_api_key_env="AZURE_KEY",
        azure_timeout=33.0,
        azure_max_tokens=250,
        azure_temperature=0.3,
    )

    provider = build_provider(config)

    assert isinstance(provider, AzureProvider)
    assert provider.model == "my-deployment"
    assert provider.endpoint == "https://example.services.ai.azure.com/models"
    assert provider.api_key_env == "AZURE_KEY"
    assert provider.timeout == 33.0
    assert provider.max_tokens == 250
    assert provider.temperature == 0.3


def test_build_provider_supports_vertex_provider() -> None:
    config = GistoryConfig(
        provider="vertex",
        model="gemini-2.5-flash",
        vertex_project="my-project",
        vertex_location="us-central1",
        vertex_timeout=44.0,
        vertex_max_tokens=350,
        vertex_temperature=0.4,
    )

    provider = build_provider(config)

    assert isinstance(provider, VertexProvider)
    assert provider.model == "gemini-2.5-flash"
    assert provider.project == "my-project"
    assert provider.location == "us-central1"
    assert provider.timeout == 44.0
    assert provider.max_tokens == 350
    assert provider.temperature == 0.4
