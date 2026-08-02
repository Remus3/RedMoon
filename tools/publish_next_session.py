"""Publish the next-session prompt to the operator's Desktop.

`NEXT_SESSION_PROMPT.md` is the source of truth; `Desktop/RM-NEXT-SESSION.txt`
is the copy the operator actually pastes into a cleared session. This is the
ONLY writer of that file, and the only thing in this project that writes
outside the repository at all.

Everything here is a guard, because the failure modes are silent:

- The Desktop is SHARED with two sibling projects that own `LW-` and `RC-`
  prefixed hand-offs. The target basename is a constant and is never derived
  from an argument, so a path bug cannot reach a neighbour's file.
- A truncated block is REFUSED. A stale hand-off and a truncated one both read
  as current; only one of them is missing the context that makes it useful.
- Non-ASCII is REFUSED. This is the point where the text leaves the toolchain
  for Notepad, which is exactly where the CLAUDE.md hard rule earns itself.
- The write is atomic - temp file in the destination directory, then
  `os.replace` - and is read back before it is called done. A half-written
  hand-off is indistinguishable from a complete one until it is pasted.

Usage:
    python tools/publish_next_session.py            # publish
    python tools/publish_next_session.py --check    # report drift, write nothing
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "NEXT_SESSION_PROMPT.md"

# Never derived from user input. The Desktop holds LW- and RC- prefixed
# hand-offs owned by other projects.
TARGET_NAME = "RM-NEXT-SESSION.txt"

FENCE = "```"

# The shortest hand-off ever written was several thousand bytes. Anything near
# this floor is a truncation or a stub, not a prompt.
MIN_BYTES = 2000


class Refusal(Exception):
    """A refusal to publish, carrying a machine-readable reason."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail


def extract_prompt(source_text: str) -> str:
    """Return the single fenced block of `source_text`, or refuse."""
    lines = source_text.splitlines(keepends=True)
    fences = [i for i, line in enumerate(lines) if line.rstrip("\r\n") == FENCE]

    if len(fences) < 2:
        raise Refusal("no_prompt_block", f"{SOURCE.name} has no fenced prompt block")
    if len(fences) > 2:
        raise Refusal(
            "multiple_prompt_blocks",
            f"{SOURCE.name} has {len(fences) // 2} fenced blocks; the prompt must be the only one",
        )

    block = "".join(lines[fences[0] + 1 : fences[1]])

    size = len(block.encode("ascii", errors="replace"))
    if size < MIN_BYTES:
        raise Refusal(
            "prompt_too_short",
            f"the block is {size} bytes, under the {MIN_BYTES}-byte floor - a truncated "
            "hand-off reads as current and is worse than a stale one",
        )

    offenders = sorted({ch for ch in block if ord(ch) > 127})
    if offenders:
        raise Refusal(
            "non_ascii",
            "the block carries non-ASCII characters "
            + ", ".join(f"U+{ord(ch):04X}" for ch in offenders),
        )

    return block


def target_path(desktop: Path) -> Path:
    return desktop / TARGET_NAME


def _require_desktop(desktop: Path) -> None:
    if not desktop.is_dir():
        raise Refusal("no_desktop", f"{desktop} is not a directory")


def check(source_text: str, desktop: Path) -> dict:
    """Report whether the Desktop copy matches the source. Writes nothing."""
    _require_desktop(desktop)
    block = extract_prompt(source_text)
    target = target_path(desktop)
    current = target.read_text(encoding="utf-8") if target.is_file() else None
    return {
        "ok": True,
        "in_sync": current == block,
        "present": current is not None,
        "target": str(target),
        "bytes": len(block.encode("ascii")),
    }


def publish(source_text: str, desktop: Path) -> dict:
    """Write the source's prompt block to the Desktop, atomically."""
    _require_desktop(desktop)
    block = extract_prompt(source_text)
    target = target_path(desktop)

    # Temp file in the DESTINATION directory: os.replace is only atomic within
    # a filesystem, and the Desktop need not share one with the repo.
    handle, temp_name = tempfile.mkstemp(dir=desktop, prefix=".rm-next-", suffix=".tmp")
    temp = Path(temp_name)
    try:
        with os.fdopen(handle, "w", encoding="ascii", newline="\n") as stream:
            stream.write(block)
        os.replace(temp, target)
    except BaseException:
        temp.unlink(missing_ok=True)
        raise

    written = target.read_text(encoding="utf-8")
    if written != block:
        raise Refusal("verify_failed", f"{target} does not match the source after writing")

    return {"ok": True, "target": str(target), "bytes": len(block.encode("ascii"))}


def default_desktop() -> Path:
    return Path.home() / "Desktop"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="report drift, write nothing")
    parser.add_argument("--desktop", type=Path, default=None, help="override the Desktop directory")
    args = parser.parse_args(argv)

    desktop = args.desktop or default_desktop()
    source_text = SOURCE.read_text(encoding="utf-8")

    try:
        report = check(source_text, desktop) if args.check else publish(source_text, desktop)
    except Refusal as refusal:
        print(json.dumps({"ok": False, "reason": refusal.reason, "detail": refusal.detail}))
        return 1

    print(json.dumps(report))
    return 0 if report.get("in_sync", True) else 1


if __name__ == "__main__":
    sys.exit(main())
