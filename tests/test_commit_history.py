"""The co-author policy asserted against the OUTCOME, not against the mechanism.

Operator policy 2026-06-03: never emit the Claude co-author trailer. Three
things already exist and none of them closes this:

- `hooks/commitmsg_hook.py` STRIPS AND WARNS. It never blocks, deliberately
  (see its docstring), so a message it did not see is a message it did not fix.
- `--no-verify` bypasses git hooks entirely, and CLAUDE.md itself says the hook
  is "a backstop, not a licence to emit the line".
- Nothing scans afterward, so a trailer that reached a commit stays there.

Asserting the outcome over `git log` is what survives `--no-verify`: however the
line got in, this fails once it is in the history.

TWO PROPERTIES ARE LOAD-BEARING.

The predicate is IMPORTED from the hook rather than restated. A restated literal
drifts: an earlier draft of this item named a case-sensitive `Co-Authored-By:
Claude`, which is narrower than the hook's own pattern, and a commit reading
`Co-authored-by: Fable <noreply@anthropic.com>` would have violated the policy,
been stripped by the hook, and slipped past the test meant to catch it.

The scan asserts it walked EVERY commit. A `git log` format that silently drops
merge commits or empty-body commits reports a clean zero over a partial history,
which is indistinguishable from a clean history. The count is the control.

Never assert a commit COUNT literal here. It moves every session. What is pinned
is the RELATIONSHIP between the two git calls.
"""
from __future__ import annotations

import ast
import importlib.util
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
HOOK_PATH = REPO / "hooks" / "commitmsg_hook.py"

# Record and field separators. Bodies are multi-line and may be empty, so the
# split cannot be on a newline: NUL and unit-separator cannot occur in a commit
# message, which makes the parse total rather than heuristic.
RECORD_SEP = "\x00"
FIELD_SEP = "\x1f"

# The same two separators as GIT FORMAT ESCAPES, which is not the same thing as
# the characters themselves. Interpolating a real NUL into the argument list
# fails on Windows: CreateProcess takes one command-line STRING and a NUL
# terminates it, so git received a truncated format and the walk was empty.
# Passing the escapes lets git expand them into the OUTPUT, where a NUL is fine.
LOG_FORMAT = "--format=%H%x1f%B%x00"


def _load_hook():
    """Import hooks/commitmsg_hook.py by path.

    `hooks/` carries no `__init__.py` and is not on sys.path: it is a git
    hooksPath directory, not a package, and adding one would change what git
    executes. Loading by path is what keeps the predicate single-sourced without
    restructuring the hook directory to suit a test.
    """
    spec = importlib.util.spec_from_file_location("commitmsg_hook", HOOK_PATH)
    assert spec is not None and spec.loader is not None, f"cannot load {HOOK_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CLAUDE_TRAILER = _load_hook().CLAUDE_TRAILER


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(REPO), *args],
        capture_output=True,
        text=True,
        timeout=60,
    )


def _commit_records() -> list[tuple[str, str]]:
    """Return (sha, full message body) for every commit reachable from any ref.

    `%B` is the whole message, subject and body together. `%b` is the body
    ALONE, which would miss a trailer pasted into a subject line - unlikely, but
    the cheap format is the one that cannot miss it.
    """
    result = _git("log", "--all", LOG_FORMAT)
    assert result.returncode == 0, f"git log failed: {result.stderr.strip()}"

    records: list[tuple[str, str]] = []
    for chunk in result.stdout.split(RECORD_SEP):
        if FIELD_SEP not in chunk:
            # The residue after the final separator, and nothing else. A chunk
            # with real content but no field separator would be a parse failure
            # rather than the tail, so it is asserted away instead of skipped.
            assert not chunk.strip(), f"unparseable git log chunk: {chunk!r}"
            continue
        sha, body = chunk.split(FIELD_SEP, 1)
        records.append((sha.strip(), body))
    return records


def _offending_lines(body: str) -> list[str]:
    return [line.strip() for line in body.splitlines() if CLAUDE_TRAILER.match(line)]


def test_the_scan_walks_every_commit_in_the_history():
    """The control on the scan itself.

    Without this, a format that drops merge or empty-body commits returns zero
    offenders over a partial history and reads exactly like a pass.
    """
    counted = _git("rev-list", "--all", "--count")
    assert counted.returncode == 0, f"git rev-list failed: {counted.stderr.strip()}"
    expected = int(counted.stdout.strip())
    assert expected > 0, "an empty history cannot exercise this gate"

    assert len(_commit_records()) == expected, (
        "the trailer scan did not walk every commit - a partial walk reporting "
        "zero offenders is indistinguishable from a clean history"
    )


def test_the_scan_actually_reads_message_text():
    """The liveness control, and it is not redundant with the count above.

    A walk that returns the right NUMBER of records with empty bodies scans 134
    empty strings, finds nothing, and passes - a null from an instrument that
    cannot produce a positive, which this project has recorded once already as
    the 2026-07-26 console investigation.

    The check is against HEAD's subject read through a SECOND, independent git
    format, so it fails if the body field is empty, mis-parsed, or shifted by
    one record against its sha.
    """
    subject = _git("log", "-1", "--format=%s")
    assert subject.returncode == 0, f"git log failed: {subject.stderr.strip()}"
    head_subject = subject.stdout.strip()
    assert head_subject, "HEAD has no subject line to check against"

    head_sha = _git("rev-parse", "HEAD").stdout.strip()
    bodies = {sha: body for sha, body in _commit_records()}
    assert head_sha in bodies, "the scan did not return a record for HEAD"
    assert head_subject in bodies[head_sha], (
        "the scan returned a record for HEAD whose body does not contain HEAD's "
        f"subject {head_subject!r} - the message text is not reaching the "
        "predicate, so a clean result proves nothing"
    )


def test_no_commit_in_the_history_carries_the_claude_coauthor_trailer():
    offenders: list[str] = []
    for sha, body in _commit_records():
        for line in _offending_lines(body):
            offenders.append(f"{sha[:8]}: {line}")

    assert not offenders, (
        "CLAUDE.md hard rule, operator policy 2026-06-03: never emit the Claude "
        f"co-author trailer. These commits carry it: {offenders}. The commit-msg "
        "hook strips rather than blocks and --no-verify bypasses it entirely, so "
        "these reached the history some way the hook could not see. Rewrite the "
        "message with git commit --amend, or git rebase for an older commit."
    )


# The negative control. A string built to match predicate P and then checked by
# predicate P is a tautology; what makes this a control is that these are the
# real forms the policy is about, including the two that a hand-written
# case-sensitive literal would miss.
DETECTED = (
    "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>",
    "co-authored-by: Claude <noreply@anthropic.com>",
    "Co-authored-by: Fable <noreply@anthropic.com>",
    "\tCo-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>",
    "    co-authored-by : claude",
    "Co-Authored-By: Some Assistant <bot@anthropic.com>",
)

NOT_DETECTED = (
    # The clause that stops an over-broad predicate. A human co-author is a true
    # statement about authorship and CLAUDE.md leaves it alone.
    "Co-Authored-By: Moonbeam <close.benham@gmail.com>",
    "Signed-off-by: Moonbeam <close.benham@gmail.com>",
    "docs(session): explain why Claude must not be credited as co-author",
    "Reviewed-by: Moonbeam <close.benham@gmail.com>",
)


@pytest.mark.parametrize("line", DETECTED)
def test_a_real_trailer_form_is_detected(line: str):
    assert CLAUDE_TRAILER.match(line), (
        f"the predicate misses {line!r}, so the history scan above proves nothing"
    )


@pytest.mark.parametrize("line", NOT_DETECTED)
def test_a_legitimate_line_is_not_detected(line: str):
    assert not CLAUDE_TRAILER.match(line), (
        f"the predicate over-matches {line!r} - a human co-author is a true "
        "statement about authorship and the policy does not touch it"
    )


def test_this_module_states_no_predicate_of_its_own():
    """The single-source guard, checked over the AST rather than the text.

    The whole point of importing CLAUDE_TRAILER is that the friendly path and
    this backstop cannot diverge. A future edit that quietly compiled a local
    pattern would restore exactly the drift this item exists to remove, and
    every other test here would still pass.

    Over the AST and not over the source TEXT, because a text scan for the name
    of the thing it forbids matches its own assertion and fails on a clean file
    - which it did, on the first run of this module. An AST walk does not see
    inside string literals, so the check means what it says.
    """
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))

    imports_re = any(
        (isinstance(node, ast.Import) and any(a.name == "re" for a in node.names))
        or (isinstance(node, ast.ImportFrom) and node.module == "re")
        for node in ast.walk(tree)
    )
    assert not imports_re, (
        "this module imports re, so it can compile a trailer pattern of its "
        "own - import CLAUDE_TRAILER from hooks/commitmsg_hook instead, so the "
        "hook and this scan cannot disagree about what the policy forbids"
    )
