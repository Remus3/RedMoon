---
name: reference-powershell-editions-on-legion
description: "Claude Code's PowerShell tool on Legion runs pwsh 7.6.4 Core, not powershell.exe 5.1 - probe before assuming"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 9364de1e-c901-42df-aa5e-bcb1b8e0fd25
  modified: 2026-08-01T15:41:12.137Z
---

Legion has BOTH PowerShell editions, side by side. PowerShell 7.6.4 was installed
2026-07-26 by the Riot Commander project via the MSI at machine scope. 5.1 was
untouched and stays.

    powershell.exe  ->  Windows PowerShell 5.1   (Desktop, ANSI default)
    pwsh.exe        ->  PowerShell 7.6.4         (Core, UTF-8 default)
                        C:\Program Files\PowerShell\7\pwsh.exe

**Claude Code's PowerShell tool runs pwsh 7.6.4 Core here.** Measured in-session
2026-07-26: `$PSVersionTable` returns 7.6.4 / Core and `(Get-Process -Id
$PID).Path` returns `C:\Program Files\PowerShell\7\pwsh.exe`. So `&&`, `||`,
ternary, `??`, `?.` and `ConvertFrom-Json -AsHashtable` all work directly in
agent PowerShell, with no `& pwsh -File` escape hatch needed.

Riot Commander's `POWERSHELL_7_MIGRATION.md` section 4c claims the opposite - it
says the tool invokes `powershell.exe` so agents must write 5.1-compatible
PowerShell. That claim is wrong as measured, and it SURVIVED a revision of that
doc: re-validated 2026-07-26 against an updated copy, 4c is unchanged and still
wrong. **Probe `$PSVersionTable` rather than trusting either that doc or this
entry**, since the tool's binary can change under a Claude Code upgrade.

**This machine is `DESKTOP-LCA3EBI`.** That same doc's header says
`DESKTOP-JKZECV9`, which is wrong; every other fact in it matches this box, so it
is a mis-recorded name rather than a different machine. Tailscale is not
installed and not on PATH here, so its `legion-rc` node label cannot be checked
at all.

Red Moon has ZERO PowerShell call sites to migrate: `RM-DataRefresh` executes
`pythonw.exe`, and no `.py`, `.json`, `.vbs`, `.bat` or `.cmd` in the repo
invokes powershell. Nothing to do.

**NEVER call a native Windows exe with `/flag` arguments from the Bash tool.**
Measured 2026-08-01. Git Bash MSYS path-translation rewrites a leading-slash
argument into a Windows path, so `schtasks /query /fo csv /nh` arrives as
`schtasks C:/Program Files/Git/query ...`, schtasks exits 1, and the pipeline
yields ZERO ROWS. **A tool that never ran is indistinguishable from a true
zero** - this produced a confident, wrong "RM-DataRefresh is not installed" that
contradicted the SessionStart hook. The task is installed and Ready. The same
trap applies to any `/`-flagged exe: `sc`, `reg`, `tasklist`, `taskkill /F /PID`,
`net`. Use the PowerShell tool for those, or a Python `subprocess` list (which is
what `tools/rm_facts.py` does, and why it got the right answer). Contrast with
the `_scratch/` ascii-guard probe: same failure shape, different mechanism.

**This does NOT relax the no-em-dash / 7-bit-ASCII rule.** PS7 does remove the
5.1 parse failure that `CLAUDE.md` cites as the rule's rationale, so that
rationale is now historical rather than live - measured here on a no-BOM UTF-8
`.ps1` carrying U+2014 in a double-quoted string, via `[Parser]::ParseFile`,
**5.1 reports 2 errors and 7.6.4 reports 0**. But 5.1 is still installed, the
rule is also operator style, and `tools/ascii_guard.py` plus the precommit gate
enforce it mechanically.

Related: [[reference-flashing-consoles-are-mcp-launchers]], [[user-operator-profile]]
