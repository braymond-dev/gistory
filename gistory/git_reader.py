from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


FIELD_SEPARATOR = "\x1f"
RECORD_SEPARATOR = "\x1e"


@dataclass(frozen=True)
class CommitInfo:
    hash: str
    date: datetime
    author: str
    subject: str
    body: str
    files_changed: list[str]
    diff_summary: str
    diff: str

    @property
    def short_hash(self) -> str:
        return self.hash[:7]


class GitReader:
    def __init__(self, repo_path: Path | str = ".") -> None:
        self.repo_path = Path(repo_path)

    def _git(self, args: list[str]) -> str:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("git executable was not found") from exc
        except subprocess.CalledProcessError as exc:
            message = (exc.stderr or exc.stdout or "").strip()
            raise RuntimeError(f"git {' '.join(args)} failed: {message}") from exc
        return result.stdout

    def ensure_repo(self) -> None:
        self._git(["rev-parse", "--show-toplevel"])

    def read_commits(self, revision_range: str | None = None, since: str | None = None) -> list[CommitInfo]:
        self.ensure_repo()
        log_args = [
            "log",
            "--date=iso-strict",
            f"--format={RECORD_SEPARATOR}%H{FIELD_SEPARATOR}%aI{FIELD_SEPARATOR}%an{FIELD_SEPARATOR}%s{FIELD_SEPARATOR}%b",
        ]
        if since:
            log_args.append(f"--since={since}")
        if revision_range:
            log_args.append(revision_range)

        raw_log = self._git(log_args)
        commits: list[CommitInfo] = []
        for record in raw_log.split(RECORD_SEPARATOR):
            record = record.strip("\n")
            if not record:
                continue
            parts = record.split(FIELD_SEPARATOR, 4)
            if len(parts) != 5:
                raise RuntimeError("Unable to parse git log output")
            commit_hash, date_text, author, subject, body = parts
            files_changed = self.files_changed(commit_hash)
            commits.append(
                CommitInfo(
                    hash=commit_hash,
                    date=datetime.fromisoformat(date_text),
                    author=author,
                    subject=subject,
                    body=body.strip(),
                    files_changed=files_changed,
                    diff_summary=self.diff_summary(commit_hash),
                    diff=self.diff(commit_hash),
                )
            )
        return commits

    def files_changed(self, commit_hash: str) -> list[str]:
        output = self._git(["show", "--format=", "--name-only", commit_hash])
        return [line.strip() for line in output.splitlines() if line.strip()]

    def diff_summary(self, commit_hash: str) -> str:
        return self._git(["show", "--format=", "--stat", "--summary", commit_hash]).strip()

    def diff(self, commit_hash: str) -> str:
        return self._git(["show", "--format=", "--patch", "--find-renames", commit_hash]).strip()
