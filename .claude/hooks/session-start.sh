#!/usr/bin/env bash
# Hook di avvio sessione per Claude Code locale e remoto.
#
# Non contiene logica propria: la preparazione vive in `scripts/setup.sh`, così
# Claude Code e Codex eseguono esattamente la stessa procedura e non possono
# divergere. La `.venv` vive nel singolo checkout, quindi anche l'esecuzione
# locale non modifica il Python globale del computer.

set -uo pipefail

output="$(bash "${CLAUDE_PROJECT_DIR:-.}/scripts/setup.sh" 2>&1)"
status=$?

if [ -n "$output" ]; then
    printf '%s\n' "$output"
fi

if [ "$status" -ne 0 ]; then
    printf '%s\n' \
        'setup: GATE BLOCCANTE — non analizzare, modificare o testare il repository'
fi
