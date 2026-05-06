from gistory.filters import filter_paths, is_ignored


def test_is_ignored_matches_exact_and_recursive_patterns() -> None:
    patterns = ["package-lock.json", "dist/**", ".next/**"]

    assert is_ignored("package-lock.json", patterns)
    assert is_ignored("dist/app.js", patterns)
    assert is_ignored("dist/assets/app.js", patterns)
    assert is_ignored(".next/server/page.js", patterns)
    assert not is_ignored("src/app.py", patterns)


def test_filter_paths_keeps_non_ignored_files() -> None:
    paths = ["src/app.py", "dist/app.js", "README.md", "node_modules/pkg/index.js"]
    patterns = ["dist/**", "node_modules/**"]

    assert filter_paths(paths, patterns) == ["src/app.py", "README.md"]
