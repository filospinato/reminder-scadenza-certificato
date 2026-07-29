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

venv="$radice/.venv"
python_venv="$venv/bin/python"
esito=0

avviso() {
    printf 'setup: %s\n' "$1" >&2
    esito=1
}

# Riporta il primo guasto trovato in `problema` invece di segnalarlo subito,
# così la stessa verifica serve sia a decidere se riparare sia a dare il verdetto.
problema=''
verifica() {
    problema=''
    if ! "$python_venv" -c 'import reminder_certificati' >/dev/null 2>&1; then
        problema='pacchetto reminder_certificati non importabile dalla .venv'
        return 1
    fi
    local comando
    for comando in pytest ruff; do
        if [ ! -x "$venv/bin/$comando" ] ||
           ! "$venv/bin/$comando" --version >/dev/null 2>&1; then
            problema="$comando non funzionante in .venv dopo l'installazione"
            return 1
        fi
    done
    return 0
}

rimuovi_flag_nascosto_macos() {
    if command -v chflags >/dev/null 2>&1 &&
       ! find "$venv" -type f -name '*.pth' \
           -exec chflags nohidden {} + 2>/dev/null; then
        avviso 'impossibile rimuovere il flag hidden macOS dalla .venv'
    fi
}

# I mirror dei pacchetti rispondono a intermittenza e un timeout a metà lavoro
# costa più di qualche secondo di attesa qui.
#
# `forzata` aggiunge --force-reinstall: è l'unico modo di riscrivere un
# eseguibile che pip considera già a posto. Serve solo alla riparazione.
installa() {
    local -a forzata=()
    if [ "${1:-}" = 'forzata' ]; then
        forzata=(--force-reinstall)
    fi

    local tentativo
    for tentativo in 1 2 3; do
        if "$python_venv" -m pip install --quiet --disable-pip-version-check \
            --root-user-action=ignore --timeout 60 --retries 5 \
            ${forzata[@]+"${forzata[@]}"} \
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

if [ -L "$venv" ]; then
    avviso 'rifiutata .venv simbolica: l’ambiente deve restare nel checkout'
elif [ ! -x "$python_venv" ] && ! python3 -m venv "$venv"; then
    avviso "creazione dell'ambiente virtuale non riuscita: $venv"
fi

if [ "$esito" -eq 0 ] && [ -x "$python_venv" ]; then
    rimuovi_flag_nascosto_macos
    if installa; then
        rimuovi_flag_nascosto_macos
        printf 'setup: dipendenze installate da pyproject.toml in .venv (extra dev, google)\n'
    else
        avviso 'installazione delle dipendenze non riuscita: pytest e ruff potrebbero mancare'
    fi

    # Uno strumento rotto ma presente lascia il requisito già soddisfatto: pip
    # non ha nulla da fare e non riscrive il file. Senza la reinstallazione
    # forzata l'ambiente resterebbe guasto a ogni esecuzione successiva.
    if [ "$esito" -eq 0 ] && ! verifica; then
        if installa forzata; then
            rimuovi_flag_nascosto_macos
            printf 'setup: ambiente riparato con una reinstallazione forzata\n'
        fi
        if ! verifica; then
            avviso "$problema"
        fi
    fi
elif [ "$esito" -eq 0 ]; then
    avviso 'python non disponibile nell’ambiente virtuale'
fi

if [ "$esito" -eq 0 ]; then
    printf 'setup: ambiente pronto (%s)\n' "$("$python_venv" --version)"
fi

exit "$esito"
