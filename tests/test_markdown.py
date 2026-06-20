from datetime import datetime, timezone

from gistory.git_reader import CommitInfo
from gistory.markdown import (
    CommitSummary,
    append_segment,
    group_by_month,
    latest_segment_end,
    mark_continued_months,
    normalize_paragraph,
    render_markdown,
    render_segment,
)


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
        CommitSummary(make_commit("def567890", "2026-05-02T10:00:00", "Refactor scoring"), "Refactored scoring."),
        CommitSummary(make_commit("abc123456", "2026-05-01T10:00:00", "Add CSV ingestion pipeline"), "Added CSV ingestion."),
        CommitSummary(make_commit("fed123456", "2026-04-01T10:00:00", "Document setup"), "Documented setup."),
    ]

    markdown = render_markdown(group_by_month(summaries))

    assert markdown.startswith("# Gistory")
    assert "## 2026-05" in markdown
    assert "Added CSV ingestion.\n\nRefactored scoring." in markdown
    assert markdown.index("- abc1234 Add CSV ingestion pipeline") < markdown.index("- def5678 Refactor scoring")
    assert "- abc1234 Add CSV ingestion pipeline" in markdown
    assert "## 2026-04" in markdown
    assert markdown.index("## 2026-04") < markdown.index("## 2026-05")


def test_render_markdown_empty_history() -> None:
    assert render_markdown([]) == "# Gistory\n\nNo commits found.\n"


def test_render_segment_adds_commit_markers() -> None:
    summaries = [
        CommitSummary(make_commit("def567890", "2026-05-02T10:00:00", "Refactor scoring"), "Refactored scoring."),
        CommitSummary(make_commit("abc123456", "2026-05-01T10:00:00", "Add CSV ingestion pipeline"), "Added CSV ingestion."),
    ]

    segment = render_segment(
        group_by_month(summaries),
        start_hash="abc1234",
        end_hash="def5678",
    )

    assert segment.startswith("<!-- gistory:segment start=abc1234 end=def5678 -->")
    assert segment.rstrip().endswith("<!-- gistory:segment-end -->")
    assert "# Gistory" not in segment


def test_render_segment_uses_explicit_git_order_over_commit_dates() -> None:
    summaries = [
        CommitSummary(make_commit("new111111", "2026-05-01T10:00:00", "Newer in Git"), "Newer change."),
        CommitSummary(make_commit("old222222", "2026-05-02T10:00:00", "Older in Git"), "Older change."),
    ]

    segment = render_segment(
        group_by_month(summaries),
        start_hash="old2222",
        end_hash="new1111",
    )

    assert segment.startswith("<!-- gistory:segment start=old2222 end=new1111 -->")


def test_latest_segment_end_reads_last_marker() -> None:
    markdown = """# Gistory

<!-- gistory:segment start=aaa1111 end=bbb2222 -->
<!-- gistory:segment-end -->

<!-- gistory:segment start=ccc3333 end=ddd4444 -->
<!-- gistory:segment-end -->
"""

    assert latest_segment_end(markdown) == "ddd4444"


def test_append_segment_preserves_existing_markdown() -> None:
    existing = "# Gistory\n\nOld text."
    segment = "<!-- gistory:segment start=aaa1111 end=bbb2222 -->\n\nNew text.\n\n<!-- gistory:segment-end -->\n"

    assert append_segment(existing, segment) == f"{existing}\n\n{segment}"


def test_normalize_paragraph_collapses_whitespace_and_preserves_punctuation() -> None:
    assert normalize_paragraph(" Added\n\nCSV ingestion ") == "Added CSV ingestion."
    assert normalize_paragraph("Kept the API stable!") == "Kept the API stable!"


def test_mark_continued_months_labels_existing_month() -> None:
    summaries = [
        CommitSummary(make_commit("abc123456", "2026-05-03T10:00:00", "Add export"), "Added export."),
        CommitSummary(make_commit("def567890", "2026-06-01T10:00:00", "Add import"), "Added import."),
    ]

    sections = mark_continued_months(group_by_month(summaries), "# Gistory\n\n## 2026-05\n")

    assert [section.title for section in sections] == ["2026-05 (continued)", "2026-06"]
