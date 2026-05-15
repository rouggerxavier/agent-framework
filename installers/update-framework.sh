#!/usr/bin/env bash
set -eu

FRAMEWORK_DIR="${AGENT_FRAMEWORK_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

if [ ! -d "$FRAMEWORK_DIR" ]; then
  echo "error: framework directory not found: $FRAMEWORK_DIR" >&2
  exit 1
fi

cd "$FRAMEWORK_DIR"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "git: pulling with --ff-only"
  git pull --ff-only
else
  echo "git: not a repository, skipping pull"
fi

bash "$FRAMEWORK_DIR/installers/verify-framework.sh"

echo "next: run bash $FRAMEWORK_DIR/installers/install-all.sh to sync skills"
