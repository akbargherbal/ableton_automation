#!/usr/bin/env bash
# build_mastering_env.sh — assemble a self-contained runtime folder for the
# "Mastering Suno AI Music in Ableton" course.
#
# SCOPE: the learner is a total DAW novice, not just a mastering novice —
# never used a DAW, no music theory, has never touched Ableton. This runtime
# is a hybrid:
#
#   INCLUDED  -- the click-demonstration primitives (automate_ableton_task.py
#                + its hard deps), the control_catalog.json ground-truth
#                reference (consulted on-demand/narrowly by scripts, never
#                bulk-loaded into the agent's own context), and take_shot.sh
#                for ad hoc screenshot capture.
#   EXCLUDED  -- orchestrate.sh (belongs to the sibling click-automation
#                course; this course's tutoring is live/conversational, not
#                a pre-scripted task list).
#
# WHITELIST, not blacklist: only files listed in FILES[] below ever leave
# this repo.
#
# Usage:
#   ./build_mastering_env.sh [target_dir]
#   target_dir defaults to a sibling folder: ../suno-mastering-course
#
# Point OpenCode's working directory at <target_dir> for the mastering
# course. Re-run any time SUNO_MASTERING_AGENT_POLICY.md or the whitelisted
# docs/scripts change — straight overwrite of those, but KNOWN_ISSUES.md in
# the target is never touched once it exists (it's a live session artifact
# the agent appends to, not a build output), and LABS/ / scripts/dumps/ raw
# dump files are preserved if pre-existing.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-$SCRIPT_DIR/../suno-mastering-course}"

# --- The whitelist -----------------------------------------------------
# Mastering curriculum docs/setup guide, plus the click-demonstration layer
# (minus orchestrate.sh) and the on-demand catalog reference.
FILES=(
  "docs/teaching/suno-mastering-course-breakdown.md"   # authoritative lesson spec
  "docs/teaching/suno-mastering-curriculum.md"         # leaner 6-module operating version
  # docs/opencode-ableton-mcp-setup.md deliberately NOT included: one-time
  # human setup content, not something the agent ever reads or acts on.
  "take_shot.sh"                              # ad hoc screenshot capture
                                               # (window restore/focus/maximize)
                                               # for the vision fallback
  "scripts/automate_ableton_task.py"          # click-demonstration primitives
                                               # (set_checkbox_by_id / set_slider_by_id
                                               # / set_combobox_by_id), reachable via
                                               # the fixed --task CLI and the generic
                                               # call_control()/--control path
  "scripts/dump_ableton_pywinauto.py"         # hard dep of automate_ableton_task.py
  "scripts/keyboard_shortcuts.py"             # hard dep of automate_ableton_task.py;
                                               # also the Level-2 fallback lookup --
                                               # note there is no groove_pool_toggle
                                               # entry in here at all (confirmed-crash
                                               # action, removed rather than blocked)
  "scripts/dumps/control_catalog.json"        # ground-truth "does this control
                                               # exist / is it safe" reference.
                                               # Consult narrowly/on-demand (e.g. one
                                               # grep for one device) -- never load
                                               # this whole file into the agent's own
                                               # conversation context
)
# Optional whitelist -- unlike FILES[] above, a missing entry here is a
# warning, not a FATAL. docs/live12-manual-en.pdf is local-only reference
# material (see .gitignore), so it legitimately may not exist on every dev
# checkout. Copied through when present so the mastering agent can consult
# it as ground truth per SUNO_MASTERING_AGENT_POLICY.md's tooling section.
OPTIONAL_FILES=(
  "docs/live12-manual-en.pdf"
)
POLICY_SRC_NAME="SUNO_MASTERING_AGENT_POLICY.md"
POLICY_DEST_NAME="AGENTS.md"
# Dev-name/runtime-name split, so an assistant auditing THIS dev repo must not misread the mastering
# instructions as being directed at itself. Only in the runtime folder is it
# renamed to AGENTS.md, where OpenCode auto-loads it for the agent under test.
# -------------------------------------------------------------------------

mkdir -p "$TARGET"
echo "[build] target: $TARGET"

policy_src="$SCRIPT_DIR/$POLICY_SRC_NAME"
if [ ! -f "$policy_src" ]; then
  echo "[build] FATAL: policy file missing from dev repo: $POLICY_SRC_NAME" >&2
  exit 1
fi
cp -f "$policy_src" "$TARGET/$POLICY_DEST_NAME"
echo "  copied: $POLICY_SRC_NAME -> $POLICY_DEST_NAME"

for f in "${FILES[@]}"; do
  src="$SCRIPT_DIR/$f"
  if [ ! -f "$src" ]; then
    echo "[build] FATAL: whitelisted file missing from dev repo: $f" >&2
    exit 1
  fi
  mkdir -p "$TARGET/$(dirname "$f")"
  cp -f "$src" "$TARGET/$f"
  echo "  copied: $f"
done

for f in "${OPTIONAL_FILES[@]}"; do
  src="$SCRIPT_DIR/$f"
  if [ ! -f "$src" ]; then
    echo "  skipped (not present in dev repo, optional): $f"
    continue
  fi
  mkdir -p "$TARGET/$(dirname "$f")"
  cp -f "$src" "$TARGET/$f"
  echo "  copied (optional): $f"
done

# KNOWN_ISSUES.md is a runtime session log the agent appends to live during
# sessions (see SUNO_MASTERING_AGENT_POLICY.md "Known-Issues Log"), so a
# re-run must never clobber it. Dev-repo name differs from the runtime name
# -- same construct as the POLICY_SRC_NAME/POLICY_DEST_NAME rename above --
# so this is a straight cp-with-rename, seeded once.
known_issues_target="$TARGET/KNOWN_ISSUES.md"
if [ ! -f "$known_issues_target" ]; then
  cp -f "$SCRIPT_DIR/docs/teaching/MASTERING_COURSE_KNOWN_ISSUES.md" "$known_issues_target"
  echo "  created: KNOWN_ISSUES.md (seeded from docs/teaching/MASTERING_COURSE_KNOWN_ISSUES.md)"
else
  echo "  preserved: KNOWN_ISSUES.md (existing runtime log untouched -- pull its"
  echo "             entries back into docs/teaching/MASTERING_COURSE_KNOWN_ISSUES.md by hand)"
fi

echo "[build] done. $((${#FILES[@]} + 1)) files synced."
echo "[build] take_shot.sh creates its own output directory per-call (e.g. a"
echo "        session-log folder you choose) -- nothing pre-created here."
echo "[build] Point OpenCode's working directory at: $TARGET"
