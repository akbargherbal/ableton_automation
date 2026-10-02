#!/usr/bin/env bash
# build_automation_env.sh — assemble a self-contained automation runtime folder.
#
# WHITELIST, not blacklist: only the entries below ever leave this repo.
#
# Usage:
#   ./build_automation_env.sh [target_dir]
#   target_dir defaults to a sibling folder: ../ableton-automation-runtime
#
# Point OpenCode's working directory at <target_dir>. Re-run any time the
# policy or the automation package changes — straight overwrite.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-$SCRIPT_DIR/../ableton-automation-runtime}"

FILES=(
  "docs/CAPABILITY_MATRIX.md"
  "scripts/automate_ableton_task.py"
  "scripts/dump_ableton_pywinauto.py"
  "scripts/keyboard_shortcuts.py"
  "scripts/dumps/control_catalog.json"
  "take_shot.sh"
)

OPTIONAL_FILES=(
  "docs/live12-manual-en.pdf"
)

DIRS=(
  "automation"
)

POLICY_SRC_NAME="AUTOMATION_AGENT_POLICY.md"
POLICY_DEST_NAME="AGENTS.md"

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
    echo "  skipped (optional, not present): $f"
    continue
  fi
  mkdir -p "$TARGET/$(dirname "$f")"
  cp -f "$src" "$TARGET/$f"
  echo "  copied (optional): $f"
done

for d in "${DIRS[@]}"; do
  src="$SCRIPT_DIR/$d"
  if [ ! -d "$src" ]; then
    echo "[build] FATAL: whitelisted dir missing from dev repo: $d" >&2
    exit 1
  fi
  mkdir -p "$TARGET/$d"
  # copy the package, excluding caches and transient probe output
  (cd "$SCRIPT_DIR" && find "$d" \
      -path '*/__pycache__*' -prune -o \
      -path "$d/profiles/loaded*" -prune -o \
      -type f -print) | while read -r rel; do
    mkdir -p "$TARGET/$(dirname "$rel")"
    cp -f "$SCRIPT_DIR/$rel" "$TARGET/$rel"
  done
  echo "  copied dir: $d"
done

echo "[build] done. Point OpenCode's working directory at: $TARGET"
