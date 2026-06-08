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

  case "$name" in
    *[!a-z0-9-]*|-*|*-|*--*)
      echo "  problem: invalid skill directory name; use kebab-case"
      problems=$((problems + 1))
      ;;
  esac

  if [ ! -f "$skill_file" ]; then
    echo "  problem: missing SKILL.md"
    problems=$((problems + 1))
    continue
  fi

  frontmatter_name="$(sed -n 's/^name:[[:space:]]*//p' "$skill_file" | head -n 1)"
  description="$(sed -n 's/^description:[[:space:]]*//p' "$skill_file" | head -n 1)"

  if [ -z "$frontmatter_name" ]; then
    echo "  problem: missing frontmatter name"
    problems=$((problems + 1))
  elif [ "$frontmatter_name" != "$name" ]; then
    echo "  problem: frontmatter name does not match directory ($frontmatter_name != $name)"
    problems=$((problems + 1))
  fi

  if [ -z "$description" ]; then
    echo "  problem: missing frontmatter description"
    problems=$((problems + 1))
  elif [ "${#description}" -gt 240 ]; then
    echo "  problem: description too long (${#description} chars, max 240)"
    problems=$((problems + 1))
  fi

  for heading in "## Objetivo" "## Workflow" "## Saida"; do
    if ! grep -Eq "^$heading" "$skill_file"; then
      echo "  problem: missing required heading prefix: $heading"
      problems=$((problems + 1))
    fi
  done

  if ! grep -Eq '^## Criterios' "$skill_file"; then
    echo "  problem: missing criteria heading"
    problems=$((problems + 1))
  fi
done

echo "problems: $problems"

if [ "$problems" -ne 0 ]; then
  exit 1
fi

echo "verification: ok"
