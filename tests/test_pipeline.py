import subprocess
from pathlib import Path

from gistory.config import GistoryConfig
from gistory.pipeline import generate_history


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


def test_generate_history_rejects_range_and_since_together(tmp_path: Path) -> None:
    config = GistoryConfig(provider="mock")

    try:
        generate_history(config, repo_path=tmp_path, revision_range="HEAD~1..HEAD", since="30 days ago")
    except ValueError as exc:
        assert "either --range or --since" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
