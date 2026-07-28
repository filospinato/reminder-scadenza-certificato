#!/usr/bin/env bash
# Hook di avvio sessione per Claude Code sul web.
#
# Non contiene logica propria: la preparazione vive in `scripts/setup.sh`, così
# Claude Code e Codex eseguono esattamente la stessa procedura e non possono
# divergere. In locale non fa nulla, perché l'ambiente di chi sviluppa a mano è
# già preparato e non va toccato a ogni avvio.

set -uo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
    exit 0
fi

exec bash "${CLAUDE_PROJECT_DIR:-.}/scripts/setup.sh"
