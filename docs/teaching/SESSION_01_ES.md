# Executive Summary: Ableton AI Coaching Framework (Session 1 PoC)

**Session Date:** August 27, 2026  
**Focus:** Proof-of-Concept (PoC) Stress-Testing — MCP Integration, Vision Sub-Agents, Spatial Reasoning, and Interactive Coaching Friction  
**Target Environment:** Ableton Live 12 Suite on Windows Host, orchestrated via OpenCode on WSL2 (`ableton-mcp-extended`, `pywinauto`, Vision Sub-Agents)

---

## 1. Executive Overview

This initial session served as an end-to-end capabilities and boundary test for an AI-driven Ableton Live tutor. Rather than proceeding straight into audio mastering curriculum, the session systematically evaluated the agent’s perceptual tools (MCP parameter/session inspection, computer-vision fallbacks, and live UI automation). 

The session successfully validated multi-modal workspace awareness and uncovered critical operational boundaries—establishing a robust **"Verify, Don't Trust"** operating framework for subsequent teaching sessions.

---

## 2. Core Capabilities Validated

| Capability | Tool / Mechanism | Result / Accuracy |
| :--- | :--- | :--- |
| **Live Session Inspection** | `ableton-mcp-extended` | Real-time tracking of track counts, track types (Audio/MIDI), clip bounds (bars 1–137), playhead position (bar-level), and transport state. |
| **Visual Workspace Classification** | `take_shot.sh` + Vision Sub-Agent | Successfully classified **Session View vs. Arrangement View** (0.98 confidence) by detecting grid-slot vs. linear timeline topology. |
| **Spatial UI Reasoning** | 4×4 Grid Partitioning | Accurately identified macro UI regions (e.g., cell D1 Info Tooltip, cell A4 transport/time ruler). |
| **Live Control Enumeration** | `dump_ableton_pywinauto.py` | Extracted live UIA element bounding rectangles directly from the Windows OS tree. |

---

## 3. Key Limitations & Failure Modes Discovered

### A. Connection Liveness & Cache Stale-State
* **The Failure:** When the learner closed Ableton mid-session, the agent continued reporting cached observations as live state twice before noticing.
* **Root Fix:** Added a mandatory **"Live-Only Reporting"** protocol in `AGENTS.md` requiring fresh MCP queries before making any live-state assertions.

### B. MCP View Blindspot
* **The Limitation:** The MCP API supports *setting* the view (`set_ableton_view`), but provides no queryable read-back to determine whether the user is looking at Session or Arrangement View.
* **Workaround:** Offloaded view detection to the vision fallback path (`take_shot.sh` + vision sub-agent).

### C. Visual Micro-OCR vs. Spatial Layout Limits
* **The Limitation:** Vision excels at layout and spatial relationships, but struggles with small, low-contrast typography (misread sample rate badge `48.0 kHz` as `80 kHz`).
* **Protocol:** Visual text/number reads (such as integrated LUFS meters) must always be treated as low-confidence and cross-checked with the learner.

### D. Coordinate Mapping & DPI-Scaling Drift
* **The Failure:** Attempting to overlay a bounding box from `pywinauto` onto a `take_shot.sh` screenshot missed the target control ("Arm Recording" on Track 2) by **~88 px vertically**, framing the wrong track.
* **Root Cause:** 
  1. `control_catalog.json` contains static control identity only—no geometry.
  2. `pywinauto` (`python.exe`) runs DPI-unaware (virtualized screen pixels), while `take_shot.sh` (PowerShell) runs DPI-aware (physical pixels), compounded by maximized-window negative border offsets.

---

## 4. Key Pedagogical & Architectural Breakthroughs

```
                       [ AGENT TOOLING ]
                 (UIA Tree / Vision Sub-Agent)
                               │
               Provides approximate UI region
                               ▼
                        [ LEARNER ]
                 Hovers mouse over target area
                               │
                    Observes tooltip text
                               ▼
                   [ ABLETON INFO VIEW ]
             Provides ground-truth confirmation
                               │
                       [ ACTION ]
                 Learner executes click
```

1. **The "Approximate Locate + Info Panel Confirm" Pattern:**
   * Pixel-precise automated coordinate clicking is brittle and dangerous.
   * **The Working Standard:** The agent provides a general spatial anchor (e.g., *"far right edge of Track 2 mixer"*), the learner hovers in that area, and the **Ableton Info View tooltip** (`"Arm Recording"`, `"Clip Overview / Zooming Hot Spot"`) provides the definitive confirmation before clicking.
2. **Anchor-Based Navigation Over Abstract Descriptions:**
   * Telling a learner to click the "beat-time ruler" causes navigation friction. Instructions must provide a visual anchor relative to an on-screen element plus the expected hover-tooltip label.

---

## 5. Governance & Artefacts Produced

* **`AGENTS.md` Updated:**
  * Added *Live-Only Reporting (Ableton Connection Liveness)* section.
  * Added *Coordinate-Space Caveat* to `take_shot.sh` tooling rules.
* **`KNOWN_ISSUES.md` Updated:**
  * Logged and resolved **Liveness Reporting** (Status: `Fixed`).
  * Logged and resolved **UIA/Screenshot DPI Coordinate Mismatch** (Status: `Fixed`).
* **`docs/poc-observations-log.md`:**
  * Captured 11 granular PoC test findings documenting framework boundaries.
* **Environment Repaired:**
  * Reinstalled Pillow under WSL `python3.12` to fix system PIL `_imaging` binary corruption.

---

## 6. Strategic Next Steps

1. **Transition to Curriculum:** With framework tooling and verification procedures established, transition into active mastering lessons on `part_01_a.wav` in Arrangement View.
2. **Core Mastering Sequence:**
   * Step 1: Track setup & gain staging.
   * Step 2: Corrective EQ via stock EQ Eight (verified via MCP numeric read-backs).
   * Step 3: Dynamic control via Glue Compressor.
   * Step 4: Loudness analysis via Youlean Loudness Meter (utilizing Vision Screenshot-and-Diagnose fallback).