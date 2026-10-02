# System Map — what runs where, and how it connects

**Verified:** 2026-10-02 against the live machine and local sources.
**Phase 0.1 deliverable** of `PHASED_PLAN.md`. Supersedes the scattered plumbing
notes in the original `AUTOMATION_PLAN.md` §1 (full text in git history) and
answers Q3 from the plan.

## 1. Host facts

- **Ableton Live 12.1** (Suite), Build `2024-09-25_bba251b1d9`, Windows 11 Pro
  25H2. Edition confirmed via install path `C:\ProgramData\Ableton\Live 12 Suite`.
- Repo + MCP server run under **WSL2**; Ableton + the UIA layer run on **Windows**.
  WSL reaches Windows localhost via mirrored networking.

## 2. Components

### 2.1 Remote Script — the single backend
- `~/ableton-mcp-extended/AbletonMCP_Remote_Script/__init__.py` (2152 lines).
- Installed as an Ableton control surface; listens on **`localhost:9877`**.
- Framed-JSON protocol:
  request `{"type": <cmd>, "params": {...}}` → response
  `{"status": "success"|"error", "result": ..., "message": ...}`.
- **This is the only thing that touches the Live Object Model (LOM).**

### 2.2 Two front-ends share that one socket

| Front-end | Location | Role | Indexing |
|---|---|---|---|
| **MCP server** | `~/ableton-mcp-extended/MCP_Server/server.py` (2179 lines) + `plugin_aliases.py` | The `AbletonMCP` toolset (host-facing adapter) | 1-based |
| **Driver client** | `automation/lom.py` — `LomClient` | Driver's direct socket client; no MCP host needed | **0-based** (matches LOM) |

Both speak the same protocol to the same Remote Script. `automation/` can run as
a plain WSL `python3` process without OpenCode in the loop.

### 2.3 `automation/` — the actuator package

| Module | Role |
|---|---|
| `driver.py` | Unified actuator: lock, snapshot, execute, verify, log |
| `lom.py` | TCP client to the Remote Script (`:9877`) |
| `uia.py` | Subprocess bridge to Windows `python.exe` click primitives |
| `als/` | Offline `.als` channel: `read` (parse/diff), `configure` (expose params), `snapshot` (backup/restore) |
| `channels.py` | Channel-selection matrix (LOM/ALS/UIA/handoff/analysis/SDK-future) → `docs/CHANNEL_MATRIX.md` |
| `state.py` | LOM snapshot/diff + best-effort `.als` backup |
| `verify.py` | Numeric post-condition assertions (read-back) |
| `lock.py` | Single-run lock (`RUNS/.automation.lock`) |
| `log.py` | Structured JSONL run log |
| `batch.py` | Manifest batch runner with resume |
| `handoff.py` | Guided-human-step mechanism |
| `plugins.py` | External plugin discovery/resolution |
| `plugin_profiles.py` | LOM-vs-GUI plugin classification |
| `probe.py` | Live device/plugin probing → `profiles/probed/` |
| `paths.py` | WSL ↔ Windows path translation (`wslpath`) |
| `recipes/` | `import_audio`, `export_audio`, `set_tempo`, `device_report` |
| `analysis/measure.py` | LUFS / true-peak / spectrum measurement |

### 2.4 UIA layer — the reach layer
- `scripts/automate_ableton_task.py` (1885 lines), Windows `python.exe` + pywinauto.
- Wrapped by `automation/uia.py`. Used for menus, dialogs, browser drag-drop,
  plugin GUIs — anything with no LOM surface.
- `SetValue()` is permanently banned; proven path is click + type + Enter.

## 3. Provenance (Q3)

- `~/ableton-mcp-extended` origin: `github.com/uisato/ableton-mcp-extended`.
- Its README states: *"Inspired by the original ableton-mcp
  (github.com/ahujasid/ableton-mcp)"* — i.e. a **separate extended
  reimplementation**, not a git fork.
- **Implication:** we own this code outright; extending the Remote Script is
  viable with no upstream merge constraints — but also with no upstream support.

## 4. Data flow

```
OpenCode agent ──MCP──▶ MCP_Server/server.py ─┐
                                              ├─▶ :9877 Remote Script ─▶ Live 12.1 (Windows)
automation.run ──▶ automation/driver.py ──────┘         (LOM)
                        │
                        ├─▶ automation/als/ ─▶ copy/edit .als (offline; Live closed)
                        ├─▶ automation/uia.py ─▶ python.exe ─▶ pywinauto ─▶ Live UI (Windows)
                        ├─▶ automation/state.py ─▶ RUNS/ snapshots + .als backup
                        └─▶ automation/analysis ─▶ pyloudnorm/soundfile (WSL, no DAW)
```

## 5. Ports and paths

| Item | Location |
|---|---|
| Remote Script socket | `localhost:9877` |
| MCP registration | `~/.config/opencode/opencode.json` → `python .../MCP_Server/server.py` |
| Run output | `RUNS/<timestamp>_<name>/` (gitignored) |
| Probe output | `automation/profiles/probed/` |
| Local `.als` sets | `C:\Users\DELL\Jupyter_Notebooks\Learning_Mastering_in_Ableton\...` |
| Live log (ground truth) | `C:\Users\DELL\AppData\Roaming\Ableton\Live 12.1\Preferences\Log.txt` |

## 6. Still unknown / to confirm

- Whether `get_project_path` exists in the installed Remote Script (state.py
  probes for it; `ABLETON_SET_PATH` is the current fallback).
- The exact split between the MCP server's tool surface and `LomClient`'s — the
  MCP server has more tools in places (see `docs/CAPABILITY_MATRIX.md` §1), so
  the two are not 1:1.
