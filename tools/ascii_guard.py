#!/usr/bin/env python3
"""7-bit ASCII guard for authored content (CLAUDE.md hard rule).

Windows PowerShell 5.1 ANSI-decodes a no-BOM .ps1, so a UTF-8 em-dash inside a
double-quoted string becomes a smart quote that terminates the string and
cascades into a parse failure. The rule is also standing operator style.
"""
from __future__ import annotations

import sys
from pathlib import Path

AUTHORED_SUFFIXES = frozenset(
    {".py", ".md", ".json", ".txt", ".ps1", ".bat", ".cmd", ".toml", ".ini", ".cs", ".yml"}
)

EXCLUDED_DIRS = frozenset(
    {".git", "__pycache__", ".pytest_cache", ".ruff_cache", "logs", "_scratch", "assets"}
)

# Generated or third-party trees: correctness is owned by their producer, and
# game data legitimately carries non-ASCII text.
EXCLUDED_PREFIXES = ("data/rmdata/", "ops/runtime/")


def scan_text(text: str) -> list[tuple[int, int, str]]:
    """Return (line_no, col_no, char) for every codepoint above 127, 1-indexed."""
    findings: list[tuple[int, int, str]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for col_no, char in enumerate(line, start=1):
            if ord(char) > 127:
                findings.append((line_no, col_no, char))
    return findings


def is_authored(path: Path) -> bool:
    """True when path is authored content the ASCII rule governs."""
    posix = path.as_posix()
    if any(posix.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return False
    if any(part in EXCLUDED_DIRS for part in path.parts):
        return False
    return path.suffix.lower() in AUTHORED_SUFFIXES


def scan_repo(root: Path) -> dict[str, list[tuple[int, int, str]]]:
    """Scan every authored file under root. Returns only files with findings."""
    results: dict[str, list[tuple[int, int, str]]] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if not is_authored(rel):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        findings = scan_text(text)
        if findings:
            results[rel.as_posix()] = findings
    return results


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    results = scan_repo(root)
    for rel, findings in results.items():
        for line_no, col_no, char in findings:
            print(f"{rel}:{line_no}:{col_no}: non-ascii U+{ord(char):04X}")
    return 1 if results else 0


if __name__ == "__main__":
    sys.exit(main())
