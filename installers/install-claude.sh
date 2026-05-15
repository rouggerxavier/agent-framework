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

echo "done: copied=$copied replaced=$replaced skipped=$skipped target=$TARGET_DIR"
if [ -d "$BACKUP_DIR" ]; then
  echo "backup: previous same-name skills moved to $BACKUP_DIR"
fi
