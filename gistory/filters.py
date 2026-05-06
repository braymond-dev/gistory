from __future__ import annotations

from fnmatch import fnmatch
from pathlib import PurePosixPath


def is_ignored(path: str, patterns: list[str]) -> bool:
    normalized = path.replace("\\", "/").lstrip("./")
    posix_path = PurePosixPath(normalized)
    for pattern in patterns:
        normalized_pattern = pattern.replace("\\", "/").lstrip("./")
        if fnmatch(normalized, normalized_pattern):
            return True
        if posix_path.match(normalized_pattern):
            return True
        if normalized_pattern.endswith("/**"):
            prefix = normalized_pattern[:-3].rstrip("/")
            if normalized == prefix or normalized.startswith(f"{prefix}/"):
                return True
    return False


def filter_paths(paths: list[str], patterns: list[str]) -> list[str]:
    return [path for path in paths if not is_ignored(path, patterns)]
