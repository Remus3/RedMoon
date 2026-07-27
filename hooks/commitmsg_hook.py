#!/usr/bin/env python3
"""git commit-msg entry point: enforce the co-author trailer policy.

Operator policy 2026-06-03: never emit the Claude co-author trailer.

The policy needs a hook rather than discipline because the default pull runs
the other way - the agent harness instructs the model to append
`Co-Authored-By: Claude ... <noreply@anthropic.com>` to every commit message.
An unenforced policy loses to a default that fires on every commit, which is
exactly what the history shows: fourteen of the thirty commits before this hook
carried the trailer, and the clean ones were clean by accident.

This strips and warns; it never blocks. A commit-msg hook that refused would
only make the operator retype the message by hand, and the trailer is cosmetic,
not a correctness gate. Compare hooks/precommit_hook.py, which does block: an
ASCII check that did not run did not pass, whereas a strip that did not run
leaves a line the operator can still remove.

Only the Claude trailer is removed. A human co-author is a true statement about
authorship and survives untouched.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

POLICY = "Operator policy 2026-06-03: never emit the Claude co-author trailer"

# A trailer line naming Claude or the anthropic.com no-reply address. Case
# insensitive because git treats trailer keys case insensitively, and the
# observed history contains both `Co-Authored-By` and `Co-authored-by`.
CLAUDE_TRAILER = re.compile(
    r"^[ \t]*co-authored-by[ \t]*:.*(?:claude|anthropic)",
    re.IGNORECASE,
)


def strip_claude_trailer(message: str) -> tuple[str, list[str]]:
    """Return the message without Claude co-author trailers, plus what was cut.

    Trailing blank lines exposed by the removal are trimmed, so stripping the
    last trailer of a message does not leave it ending in whitespace. A message
    with nothing to strip is returned byte identical - callers rely on that to
    skip the write entirely.
    """
    kept: list[str] = []
    removed: list[str] = []
    for line in message.splitlines(keepends=True):
        if CLAUDE_TRAILER.match(line):
            removed.append(line.strip())
        else:
            kept.append(line)

    if not removed:
        return message, []

    while kept and not kept[-1].strip():
        kept.pop()

    rewritten = "".join(kept)
    if rewritten and not rewritten.endswith("\n"):
        rewritten += "\n"
    return rewritten, removed


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        sys.stderr.write("commit-msg: no message file argument - nothing to do\n")
        return 0

    path = Path(args[0])
    try:
        original = path.read_text(encoding="utf-8")
    except OSError as exc:
        sys.stderr.write(f"commit-msg: cannot read {path}: {exc}\n")
        return 0

    rewritten, removed = strip_claude_trailer(original)
    if not removed:
        return 0

    # Written in place rather than through the usual temp-plus-os.replace dance:
    # git hands us a private file under .git/ and waits on our exit, so there is
    # no concurrent reader to tear.
    try:
        path.write_text(rewritten, encoding="utf-8", newline="")
    except OSError as exc:
        sys.stderr.write(f"commit-msg: cannot rewrite {path}: {exc}\n")
        return 0

    sys.stderr.write(f"commit-msg: {POLICY}\n")
    for line in removed:
        sys.stderr.write(f"  stripped: {line}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
