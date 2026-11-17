#!/usr/bin/env bash
set -eu

FRAMEWORK_DIR="${AGENT_FRAMEWORK_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
SOURCE_DIR="$FRAMEWORK_DIR/skills"
TARGET_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
BACKUP_DIR="$TARGET_DIR/.agent-framework-backups/$(date +%Y%m%d-%H%M%S)-$$"

if [ ! -d "$SOURCE_DIR" ]; then
  echo "error: skills source not found: $SOURCE_DIR" >&2
  exit 1
fi

mkdir -p "$TARGET_DIR"

copied=0
replaced=0
skipped=0

for skill in "$SOURCE_DIR"/*; do
  [ -d "$skill" ] || continue
  [ -f "$skill/SKILL.md" ] || {
    echo "skip: $(basename "$skill") has no SKILL.md"
    skipped=$((skipped + 1))
    continue
  }

  name="$(basename "$skill")"
  dest="$TARGET_DIR/$name"

  case "$name" in
    ""|.|..|*/*)
      echo "skip: invalid skill name: $name"
      skipped=$((skipped + 1))
      continue
      ;;
  esac

  if [ -e "$dest" ]; then
    mkdir -p "$BACKUP_DIR"
    mv "$dest" "$BACKUP_DIR/$name"
    replaced=$((replaced + 1))
  fi

  cp -R "$skill" "$dest"
  echo "sync: $name -> $dest"
  copied=$((copied + 1))
done

AGENT_FRAMEWORK_TARGET_ROOT="$(dirname "$TARGET_DIR")" \
AGENT_FRAMEWORK_SHARED_BACKUP_DIR="$BACKUP_DIR/shared" \
  bash "$FRAMEWORK_DIR/installers/install-shared-assets.sh"

# Registers the SessionStart reminder so the router is used without being asked.
# Idempotent; AGENT_FRAMEWORK_SKIP_HOOK=1 opts out. Never fatal: skills are
# already installed by this point.
if [ "${AGENT_FRAMEWORK_SKIP_HOOK:-0}" != "1" ]; then
  CLAUDE_ROOT="$(dirname "$TARGET_DIR")"
  python3 - "$CLAUDE_ROOT/settings.json" "\"$CLAUDE_ROOT/scripts/agent-framework-session-hint\"" <<'PY' || echo "warn: could not register SessionStart hook; add it to settings.json by hand" >&2
import json, shutil, sys
from pathlib import Path

path, command = Path(sys.argv[1]), sys.argv[2]
data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
entries = data.setdefault("hooks", {}).setdefault("SessionStart", [])
if any(h.get("command") == command for e in entries for h in e.get("hooks", [])):
    print("hook: SessionStart already registered")
else:
    if path.exists():
        shutil.copy2(path, str(path) + ".agent-framework.bak")
    entries.append({"hooks": [{"type": "command", "command": command}]})
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("hook: SessionStart registered in {}".format(path))
PY
fi

echo "done: copied=$copied replaced=$replaced skipped=$skipped target=$TARGET_DIR"
if [ -d "$BACKUP_DIR" ]; then
  echo "backup: previous same-name skills moved to $BACKUP_DIR"
fi
