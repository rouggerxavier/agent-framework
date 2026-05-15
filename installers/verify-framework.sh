#!/usr/bin/env bash
set -eu

FRAMEWORK_DIR="${AGENT_FRAMEWORK_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
SKILLS_DIR="$FRAMEWORK_DIR/skills"

problems=0

echo "framework: $FRAMEWORK_DIR"

if [ ! -d "$SKILLS_DIR" ]; then
  echo "problem: missing skills directory: $SKILLS_DIR"
  exit 1
fi

echo "skills found:"

for skill in "$SKILLS_DIR"/*; do
  [ -d "$skill" ] || continue
  name="$(basename "$skill")"
  skill_file="$skill/SKILL.md"
  echo "- $name"

  if [ ! -f "$skill_file" ]; then
    echo "  problem: missing SKILL.md"
    problems=$((problems + 1))
    continue
  fi

  if ! grep -Eq '^name:[[:space:]]*.+' "$skill_file"; then
    echo "  problem: missing frontmatter name"
    problems=$((problems + 1))
  fi

  if ! grep -Eq '^description:[[:space:]]*.+' "$skill_file"; then
    echo "  problem: missing frontmatter description"
    problems=$((problems + 1))
  fi
done

echo "problems: $problems"

if [ "$problems" -ne 0 ]; then
  exit 1
fi

echo "verification: ok"
