---
name: reference-flashing-consoles-are-mcp-launchers
description: "The console windows flashing on Legion are npx MCP launchers from concurrent Claude sessions, not Red Moon"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 6a488f8b-9a01-4c6e-9866-56227d67702a
  modified: 2026-07-26T21:19:55.979Z
---

The brief console windows the operator sees flashing on Legion are NOT Red Moon.
Measured 2026-07-26 with a 120-second `Win32_Process` poll capturing command
lines and parents.

They are `cmd.exe /d /s /c npx ...` MCP server launchers, each spawning its own
`conhost.exe` - `pathmode-mcp`, `desktop-commander`, `chrome-devtools-mcp`,
`playwright-mcp` - fired in bursts by several concurrent `claude.exe` instances,
plus other projects' `pytest` hooks running through Git Bash.

Red Moon's own hooks (`precommit_gate.py`, `pytest_guard.py`, `rm_facts.py`,
`text_first_guard.py`) all run under `pythonw.exe`, which is windowless and never
appeared in the trace as a console. The `statusLine` fix from the prior session
held and did not appear either.

The remedy is disabling unused entries under `enabledPlugins` in the user
`settings.json` (15 were enabled). Do not go hunting in the Red Moon repo for it.

Related: [[project-redmoon-ports]]
