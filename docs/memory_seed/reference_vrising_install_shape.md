---
name: reference-vrising-install-shape
description: V Rising install holds two game copies plus a dedicated server; which one BepInEx targets and how to assert it
metadata:
  type: reference
---

`C:\Program Files (x86)\Steam\steamapps\common\VRising` holds THREE game trees,
probed 2026-07-26:

- Root - `VRising.exe`, `VERSION` = `VRising: v1.1.13.0-r99712-b17
  (202605251526)`. This is the pinned build and the one Steam launches.
- `v3\` - a stale full copy at `v1.0.10.4-r91333-b12`. NOT launched. BepInEx
  must never go here. This is the trap.
- `VRising_Server\` - `VRisingServer.exe`, `VERSION` = `VRisingServer:
  v1.1.13.0-r99712-b17 (202605251709)`. Same semantic build as the client,
  DIFFERENT product prefix and trailing timestamp, so any install assert must
  compare the semantic build only, never byte equality against the client line.

IL2CPP, not Mono (`GameAssembly.dll` at every root). The loader is BepInExPack
V Rising `1.733.2`, wrapping BepInEx 6.0.0 bleeding-edge `be.733` on CoreCLR
net6, extracted into a game root as `BepInEx/`, `dotnet/`, `.doorstop_version`,
`doorstop_config.ini`, `winhttp.dll`.

Launching the game creates `%USERPROFILE%\AppData\LocalLow\Stunlock Studios\
VRising\` with `Player.log`, `Settings\v4\ClientSettings.json`, `CloudSaves\`
and `ConsoleProfile\`. No save directory appears until a world is created.

See [[project-stats-require-bridge]] and [[project-vrising-build-pin]].
