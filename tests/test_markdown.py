from datetime import datetime, timezone

from gistory.git_reader import CommitInfo
from gistory.markdown import CommitSummary, group_by_month, render_markdown


def make_commit(commit_hash: str, date: str, subject: str) -> CommitInfo:
    return CommitInfo(
        hash=commit_hash,
        date=datetime.fromisoformat(date).replace(tzinfo=timezone.utc),
        author="Ada",
        subject=subject,
        body="",
        files_changed=["src/app.py"],
        diff_summary="",
        diff="",
    )


def test_render_markdown_groups_by_month_with_key_commits() -> None:
    summaries = [
        CommitSummary(make_commit("abc123456", "2026-05-01T10:00:00", "Add CSV ingestion pipeline"), "Added CSV ingestion."),
        CommitSummary(make_commit("def567890", "2026-05-02T10:00:00", "Refactor scoring"), "Refactored scoring."),
        CommitSummary(make_commit("fed123456", "2026-04-01T10:00:00", "Document setup"), "Documented setup."),
    ]

    markdown = render_markdown(group_by_month(summaries))

    assert markdown.startswith("# Gistory")
    assert "## 2026-05" in markdown
    assert "Added CSV ingestion. Refactored scoring." in markdown
    assert "- abc1234 Add CSV ingestion pipeline" in markdown
    assert "## 2026-04" in markdown


def test_render_markdown_empty_history() -> None:
    assert render_markdown([]) == "# Gistory\n\nNo commits found.\n"
