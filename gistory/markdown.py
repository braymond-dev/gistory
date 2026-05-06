from __future__ import annotations

from dataclasses import dataclass

from gistory.git_reader import CommitInfo


@dataclass(frozen=True)
class CommitSummary:
    commit: CommitInfo
    summary: str


@dataclass(frozen=True)
class HistorySection:
    title: str
    narrative: str
    commits: list[CommitSummary]


def group_by_month(summaries: list[CommitSummary]) -> list[HistorySection]:
    groups: dict[str, list[CommitSummary]] = {}
    for summary in summaries:
        key = summary.commit.date.strftime("%Y-%m")
        groups.setdefault(key, []).append(summary)

    sections: list[HistorySection] = []
    for key in sorted(groups.keys(), reverse=True):
        commits = groups[key]
        narrative = build_narrative(commits)
        sections.append(HistorySection(title=key, narrative=narrative, commits=commits))
    return sections


def build_narrative(commits: list[CommitSummary]) -> str:
    if not commits:
        return "No notable changes."
    sentences = [summary.summary.strip().rstrip(".") for summary in commits if summary.summary.strip()]
    if not sentences:
        return "This period included project maintenance and code changes."
    return " ".join(f"{sentence}." for sentence in sentences)


def render_markdown(sections: list[HistorySection]) -> str:
    lines = ["# Gistory", ""]
    if not sections:
        lines.extend(["No commits found.", ""])
        return "\n".join(lines)

    for section in sections:
        lines.extend([f"## {section.title}", "", section.narrative.strip(), "", "### Key commits"])
        for item in section.commits:
            lines.append(f"- {item.commit.short_hash} {item.commit.subject}")
        lines.append("")
    return "\n".join(lines)
