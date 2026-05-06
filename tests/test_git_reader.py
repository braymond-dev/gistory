import subprocess
from pathlib import Path

from gistory.git_reader import GitReader


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def test_git_reader_extracts_commit_metadata_files_and_diff(tmp_path: Path) -> None:
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "ada@example.com")
    git(tmp_path, "config", "user.name", "Ada Lovelace")
    (tmp_path / "app.py").write_text("print('hello')\n", encoding="utf-8")
    git(tmp_path, "add", "app.py")
    git(tmp_path, "commit", "-m", "Add app", "-m", "Initial executable")

    commits = GitReader(tmp_path).read_commits()

    assert len(commits) == 1
    commit = commits[0]
    assert commit.author == "Ada Lovelace"
    assert commit.subject == "Add app"
    assert commit.body == "Initial executable"
    assert commit.files_changed == ["app.py"]
    assert "app.py" in commit.diff_summary
    assert "print('hello')" in commit.diff
