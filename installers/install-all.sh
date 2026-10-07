#!/usr/bin/env bash
set -eu

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# HyperFrames (skills/hyperframes*): opt-out de telemetria para tudo que este instalador rodar.
# Nao persiste no shell do agente: os skills repetem as variaveis em cada comando (docs/hyperframes.md).
export HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1

bash "$SCRIPT_DIR/install-codex.sh"
bash "$SCRIPT_DIR/install-claude.sh"
bash "$SCRIPT_DIR/install-antigravity.sh"
