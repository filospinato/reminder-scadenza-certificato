#!/usr/bin/env bash
# Prepara l'ambiente di sviluppo del repository.
#
# È il punto unico da cui passano tutti gli agenti: l'hook di avvio di Claude
# Code lo richiama, Codex lo esegue nella fase di setup — l'unica in cui la rete
# è disponibile, perché la fase agente gira isolata — e una persona può
# lanciarlo a mano. Una sola procedura, tre modi di invocarla.
#
# La lista delle dipendenze resta in `pyproject.toml`: duplicarla qui farebbe
# divergere le due fonti e l'ambiente finirebbe per mentire su cosa è installato.
# Gli extra installati sono gli stessi della CI, `dev` e `google`, perché una
# verifica locale che gira su un insieme diverso non dimostra nulla.
#
# Idempotente e non interattivo: eseguirlo due volte non cambia il risultato e
# non chiede mai niente.

set -uo pipefail

radice="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$radice" || exit 1

esito=0

avviso() {
    printf 'setup: %s\n' "$1" >&2
    esito=1
}

# I mirror dei pacchetti rispondono a intermittenza e un timeout a metà lavoro
# costa più di qualche secondo di attesa qui.
installa() {
    local tentativo
    for tentativo in 1 2 3; do
        if python3 -m pip install --quiet --disable-pip-version-check \
            --root-user-action=ignore --timeout 60 --retries 5 \
            --editable '.[dev,google]'; then
            return 0
        fi
        if [ "$tentativo" -lt 3 ]; then
            printf 'setup: installazione non riuscita (tentativo %s/3), riprovo fra %ss\n' \
                "$tentativo" "$((tentativo * 5))" >&2
            sleep "$((tentativo * 5))"
        fi
    done
    return 1
}

if installa; then
    printf 'setup: dipendenze installate da pyproject.toml (extra dev, google)\n'
else
    avviso 'installazione delle dipendenze non riuscita: pytest e ruff potrebbero mancare'
fi

for comando in pytest ruff; do
    if ! command -v "$comando" >/dev/null 2>&1; then
        avviso "$comando non disponibile dopo l'installazione"
    fi
done

if [ "$esito" -eq 0 ]; then
    printf 'setup: ambiente pronto (%s)\n' "$(python3 --version)"
fi

exit "$esito"
