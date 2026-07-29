#!/usr/bin/env bash
set -eu

FRAMEWORK_DIR="${AGENT_FRAMEWORK_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
TARGET_ROOT="${AGENT_FRAMEWORK_TARGET_ROOT:-}"
BACKUP_ROOT="${AGENT_FRAMEWORK_SHARED_BACKUP_DIR:-}"

if [ -z "$TARGET_ROOT" ] || [ -z "$BACKUP_ROOT" ]; then
  echo "error: shared installer requires target root and backup directory" >&2
  exit 1
fi

case "$TARGET_ROOT" in
  /|"$HOME"|"$FRAMEWORK_DIR")
    echo "error: refusing unsafe shared target: $TARGET_ROOT" >&2
    exit 1
    ;;
esac

copied=0
replaced=0
unchanged=0

for area in kernel workflows rubrics templates docs scripts installers; do
  source_area="$FRAMEWORK_DIR/$area"
  [ -d "$source_area" ] || continue

  while IFS= read -r -d '' source_file; do
    relative="${source_file#"$FRAMEWORK_DIR"/}"
    destination="$TARGET_ROOT/$relative"

    if [ -f "$destination" ] && cmp -s "$source_file" "$destination"; then
      unchanged=$((unchanged + 1))
      continue
    fi

    mkdir -p "$(dirname "$destination")"
    if [ -e "$destination" ]; then
      backup="$BACKUP_ROOT/$relative"
      mkdir -p "$(dirname "$backup")"
      cp -p "$destination" "$backup"
      replaced=$((replaced + 1))
    fi
    cp -p "$source_file" "$destination"
    copied=$((copied + 1))
  done < <(
    find "$source_area" -type f \
      ! -name '*.pyc' \
      ! -path '*/__pycache__/*' \
      -print0
  )
done

echo "shared: copied=$copied replaced=$replaced unchanged=$unchanged target=$TARGET_ROOT"
if [ "$replaced" -gt 0 ]; then
  echo "shared backup: $BACKUP_ROOT"
fi

