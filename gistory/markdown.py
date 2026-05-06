from __future__ import annotations

import re
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


SEGMENT_START_RE = re.compile(r"<!--\s*gistory:segment\s+start=(?P<start>[0-9a-fA-F]+)\s+end=(?P<end>[0-9a-fA-F]+)\s*-->")
SEGMENT_END = "<!-- gistory:segment-end -->"


def group_by_month(summaries: list[CommitSummary]) -> list[HistorySection]:
    groups: dict[str, list[CommitSummary]] = {}
    for summary in summaries:
        key = summary.commit.date.strftime("%Y-%m")
        groups.setdefault(key, []).append(summary)

    sections: list[HistorySection] = []
    for key in sorted(groups.keys(), reverse=True):
        commits = sorted(groups[key], key=lambda summary: summary.commit.date)
        narrative = build_narrative(commits)
        sections.append(HistorySection(title=key, narrative=narrative, commits=commits))
    return sections


def build_narrative(commits: list[CommitSummary]) -> str:
    if not commits:
        return "No notable changes."
    paragraphs = [normalize_paragraph(summary.summary) for summary in commits if summary.summary.strip()]
    if not paragraphs:
        return "This period included project maintenance and code changes."
    return "\n\n".join(paragraphs)


def normalize_paragraph(text: str) -> str:
    paragraph = " ".join(text.strip().split())
    if not paragraph:
        return paragraph
    if paragraph[-1] not in ".!?":
        return f"{paragraph}."
    return paragraph


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


def render_segment(sections: list[HistorySection]) -> str:
    commits = [item.commit for section in sections for item in section.commits]
    if not commits:
        return ""
    oldest = min(commits, key=lambda commit: commit.date).short_hash
    newest = max(commits, key=lambda commit: commit.date).short_hash
    body = render_markdown(sections).removeprefix("# Gistory\n\n").rstrip()
    return f"<!-- gistory:segment start={oldest} end={newest} -->\n\n{body}\n\n{SEGMENT_END}\n"


def append_segment(existing_markdown: str, segment: str) -> str:
    if not segment.strip():
        return existing_markdown
    base = existing_markdown.strip()
    if not base:
        return f"# Gistory\n\n{segment}"
    return f"{base}\n\n{segment}"


def latest_segment_end(markdown: str) -> str | None:
    matches = list(SEGMENT_START_RE.finditer(markdown))
    if not matches:
        return None
    return matches[-1].group("end")
