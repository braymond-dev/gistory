import subprocess
from pathlib import Path

from typer.testing import CliRunner

from gistory.cli import app, format_duration


runner = CliRunner()


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def test_generate_repo_writes_relative_output_inside_target_repo(tmp_path: Path) -> None:
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "ada@example.com")
    git(tmp_path, "config", "user.name", "Ada Lovelace")
    (tmp_path / "app.py").write_text("print('hello')\n", encoding="utf-8")
    git(tmp_path, "add", "app.py")
    git(tmp_path, "commit", "-m", "Add app")

    result = runner.invoke(app, ["generate", "--repo", str(tmp_path), "--provider", "mock"])

    assert result.exit_code == 0
    assert "Wrote GISTORY.md took" in result.output
    assert (tmp_path / "GISTORY.md").exists()
    output = (tmp_path / "GISTORY.md").read_text(encoding="utf-8")
    assert "Add app touching app.py." in output
    assert "gistory:segment start=" in output


def test_format_duration() -> None:
    assert format_duration(0.2) == "0 secs"
    assert format_duration(1.2) == "1 sec"
    assert format_duration(65.0) == "1 min 5 secs"
    assert format_duration(245.0) == "4 mins 5 secs"


def test_init_writes_only_selected_provider_settings(tmp_path: Path) -> None:
    config_path = tmp_path / ".gistory.yml"

    result = runner.invoke(
        app,
        ["init", "--config", str(config_path), "--provider", "vertex", "--model", "gemini-test"],
    )

    assert result.exit_code == 0
    text = config_path.read_text(encoding="utf-8")
    assert "provider: vertex" in text
    assert "model: gemini-test" in text
    assert "vertex_location" in text
    assert "openai_api_base" not in text
    assert "bedrock_region" not in text
